# Engineering Runbook — pgvector Migration

> **Status.** Queued for week 13 of `PUSH_TO_300_PLAN.md`. Not for execution during the push.
>
> **Goal.** Migrate vector retrieval from embedded ChromaDB to Postgres `pgvector` extension. Eliminates a service (one fewer BAA, one fewer thing to monitor), enables ACID transactions across relational + vector state, and aligns with the production AI ecosystem's consolidation pattern.
>
> **Estimated effort.** ~4 engineering days (30 hours).
>
> **Estimated infra cost.** **$0 incremental** — pgvector is a free Postgres extension and runs on the existing Postgres instance.

## Pre-conditions

- [ ] Postgres host BAA signed (per `BAA_INVENTORY.md` — AWS RDS, Crunchy Bridge, or Supabase all support pgvector)
- [ ] Postgres version ≥ 12 (PACCA already on 16, so satisfied)
- [ ] pgvector extension installed: `CREATE EXTENSION IF NOT EXISTS vector;`
- [ ] ChromaDB data still readable (don't delete `pacca_db/` until cutover passes)
- [ ] Choice of embedding model resolved: if executing `embedding-upgrade.md` first, vectors will be 3072-dim; if keeping current MiniLM, 384-dim. Schema differs accordingly.

## Schema design

```sql
CREATE TABLE guideline_chunks (
    id          uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    source_id   text NOT NULL,                    -- maps to ChromaDB's document id
    collection  text NOT NULL,                    -- 'nccn_guidelines' | 'case_precedents'
    content     text NOT NULL,
    embedding   vector(384) NOT NULL,             -- dim matches embedding model
    metadata    jsonb NOT NULL DEFAULT '{}'::jsonb,
    created_at  timestamptz NOT NULL DEFAULT now(),
    updated_at  timestamptz NOT NULL DEFAULT now()
);

-- HNSW index for ANN search (better recall than IVFFlat for sub-1M vector sets)
CREATE INDEX guideline_chunks_embedding_idx
    ON guideline_chunks
    USING hnsw (embedding vector_cosine_ops)
    WITH (m = 16, ef_construction = 64);

-- Standard btree for collection + source_id filtering
CREATE INDEX guideline_chunks_collection_source_idx
    ON guideline_chunks (collection, source_id);

CREATE INDEX guideline_chunks_metadata_idx
    ON guideline_chunks USING gin (metadata);
```

Notes:
- HNSW chosen over IVFFlat for higher recall at PACCA's scale (sub-1M vectors). IVFFlat would be more appropriate at 10M+.
- `vector_cosine_ops` matches ChromaDB's cosine-similarity scoring.
- `metadata` as JSONB enables flexible filtering without schema migration.

## Procedure

### Step 1 — Schema + index (~30 minutes)

Run the migration above. Verify with:
```sql
SELECT extname, extversion FROM pg_extension WHERE extname = 'vector';
\d guideline_chunks
```

### Step 2 — Dual-write transition layer (~6 hours)

In `src/pacca/integrations/vector_store.py`, wrap the existing class to write to BOTH Chroma and Postgres on every `add_guideline()` / `add_precedent()` call. Read path remains Chroma-only initially.

This safety net lets you migrate data without service interruption and gives you a rollback window where both stores are in sync.

```python
class DualWriteRetriever:
    def __init__(self):
        self._chroma = ChromaGuidelineRetriever()
        self._pg = PgVectorRetriever()

    def add_guideline(self, ...):
        self._chroma.add_guideline(...)
        try:
            self._pg.add_guideline(...)
        except Exception as e:
            logger.warning("pgvector_write_failed", error=str(e))
            # Chroma write succeeded; don't fail the request

    def query(self, q):
        return self._chroma.query(q)  # read still goes to Chroma
```

### Step 3 — Backfill migration script (~4 hours)

`scripts/migrate_chroma_to_pgvector.py`:

```python
# Pseudocode
for collection_name in ["nccn_guidelines", "case_precedents"]:
    collection = chroma.get_collection(collection_name)
    docs = collection.get(include=["embeddings", "metadatas", "documents"])
    for source_id, content, embedding, metadata in zip(...):
        pg.upsert(
            source_id=source_id,
            collection=collection_name,
            content=content,
            embedding=embedding,
            metadata=metadata,
        )
```

Run on a dev clone of production data first. Verify row counts match: `SELECT collection, COUNT(*) FROM guideline_chunks GROUP BY collection` should match Chroma collection sizes.

### Step 4 — Pgvector retriever implementation (~4 hours)

`src/pacca/integrations/pg_vector_store.py`: <!-- drift-guard: ignore -->

```python
class PgVectorRetriever:
    def query(self, q: str, k: int = 5, collection: str = "nccn_guidelines"):
        embedding = self._embed(q)
        rows = self._conn.execute("""
            SELECT content, metadata, 1 - (embedding <=> %s) AS similarity
            FROM guideline_chunks
            WHERE collection = %s
            ORDER BY embedding <=> %s
            LIMIT %s
        """, [embedding, collection, embedding, k])
        return [{"content": r.content, "metadata": r.metadata, "score": r.similarity}
                for r in rows]
```

Note: `<=>` is the cosine-distance operator; `1 - distance` gives similarity to match Chroma's score semantics.

### Step 5 — Retrieval benchmark (~4 hours)

Run the 100-case eval through BOTH retrievers, compare:

```bash
# Existing benchmark
pytest tests/clinical/ --retriever=chroma  # baseline
pytest tests/clinical/ --retriever=pgvector  # new

# Compare per-case retrieval recall@5 and per-case eval scores
python scripts/compare_retrievers.py --baseline=chroma_run.json --candidate=pgvector_run.json
```

**Acceptance gate:** recall@5 within ±2% of Chroma baseline AND overall eval score within ±1% of Chroma baseline. If the candidate is BETTER (which is possible — pgvector's HNSW often beats Chroma's default), proceed. If worse, debug before cutover.

### Step 6 — Read-path cutover (~2 hours)

Change `DualWriteRetriever.query()` to read from pgvector instead of Chroma. Keep dual-write active for another 7 days as a safety net.

### Step 7 — Cleanup (~2 hours, scheduled +7 days after cutover)

- Remove dual-write; pgvector becomes the sole store
- Archive `pacca_db/` directory (don't delete; keep for 90 days as rollback artifact)
- Update tests to mock pgvector instead of Chroma
- Remove ChromaDB from `pyproject.toml`

### Step 8 — Test updates (~6 hours, can run in parallel)

- Test fixtures: replace `chromadb` mocks with pgvector mocks (use pytest-postgresql or a session-scoped Docker postgres)
- Update tests that assert on Chroma-specific behavior
- Verify all 245 existing sme_authoring tests pass with pgvector backend

### Step 9 — Documentation (~2 hours)

- Update `README.md` "Technology Stack" table: ChromaDB → Postgres (pgvector)
- Update `docs/PACCA_PRD_v2.5_Consolidated.md` architecture section
- Add note to `DECISIONS.md`: this is a real iteration change with a falsifiable prediction (retrieval quality ≥ baseline)

## Acceptance criteria

- [ ] All ChromaDB data successfully migrated; row counts match
- [ ] Retrieval recall@5 within ±2% of Chroma baseline on 100-case benchmark
- [ ] Overall eval score within ±1% of Chroma baseline
- [ ] p95 query latency within +20% of Chroma baseline (pgvector should actually be faster at this scale, but allow margin)
- [ ] All existing tests pass with pgvector backend
- [ ] Dual-write removed after 7 days of stable single-source pgvector reads

## Rollback

If retrieval quality regresses after cutover:
1. Set feature flag `RETRIEVER_BACKEND=chroma` (or revert the read-path change)
2. Restart workers
3. Investigate via `compare_retrievers.py` output to identify what's different

Because dual-write was active during transition, Chroma data is current and rollback is instantaneous. The 7-day post-cutover window with dual-write still enabled is the safety net.

## Risks

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| HNSW index tuning needed | Medium | Low | Default `m=16, ef_construction=64` is good for sub-100K vectors. Tune if recall@5 dips |
| Slow query at small k due to HNSW overhead | Low | Low | If retrieval is slow at k=5, fall back to IVFFlat or no-index (linear scan is fast at <10K vectors) |
| Dual-write inconsistency window | Low | Medium | Both stores in sync after backfill; new writes go to both atomically. Async write failure to pgvector is logged but doesn't fail the request — accept eventual consistency |
| Migration script bugs corrupt pgvector data | Low | High | Run on dev clone first; verify row counts; spot-check 10 random documents; only then run on prod |
| Embedding-model swap (`embedding-upgrade.md`) collides with this work | Medium | Medium | Pick an order: do pgvector with current embedding (384-dim) first, then upgrade. OR do upgrade first and migrate with new embeddings. Don't try both simultaneously |

## Companion docs

- [`bedrock-routing.md`](bedrock-routing.md) — LLM-layer migration (independent of this)
- [`embedding-upgrade.md`](embedding-upgrade.md) — embedding model upgrade (rides on top of this; recommended sequence: pgvector first, then upgrade)
- [`postgres-hardening.md`](postgres-hardening.md) — production-grade Postgres ops (separate workstream; do after this)
- [`BAA_INVENTORY.md`](../BAA_INVENTORY.md) — Postgres host BAA status

---

*Last updated: 2026-05-27. Status: PLANNED, not yet executed.*
