# Engineering Runbook — Embedding Model Upgrade

> **Status.** Queued for week 13 of `PUSH_TO_300_PLAN.md`, sequenced AFTER `pgvector-migration.md`. Not for execution during the push.
>
> **Goal.** Replace ChromaDB's bundled embedding model (`all-MiniLM-L6-v2`, 384-dim, general-domain) with `text-embedding-3-large` (3072-dim, much stronger general-domain, BAA-eligible via Azure OpenAI). Improves clinical retrieval quality at negligible cost.
>
> **Estimated effort.** ~2 engineering days (16 hours).
>
> **Estimated infra cost.** <$1 one-time re-embedding + ~$1-5/month ongoing. Embeddings are cheap (`text-embedding-3-large` is $0.13/1M tokens).

## Why this is sequenced after pgvector

The embedding dimensionality changes from 384 → 3072. The pgvector schema needs `vector(3072)` columns from the start. Migrating ChromaDB → pgvector with 384-dim, then upgrading to 3072-dim, would require either:
- A second schema migration (drop + recreate the `embedding` column), OR
- A second table + read-path swap

Cleaner sequence: keep ChromaDB on its 384-dim embedding during the push (no change). At week 13, migrate to pgvector with the new 3072-dim `text-embedding-3-large` embeddings in a single combined cutover. The A/B benchmark step in this runbook validates the swap.

## Alternative paths (briefly)

| Path | Pros | Cons |
|---|---|---|
| **`text-embedding-3-large` via Azure (this runbook)** | Best general-domain quality; BAA via Azure; cheap; managed service | Adds Azure as a vendor |
| `BAAI/bge-large-en-v1.5` self-hosted | No vendor lock-in; zero ongoing cost | Adds ops burden (model server uptime) |
| Keep MiniLM | Zero work | Underperforms on clinical text |
| Clinical-specific embedding (e.g., BioGPT, ClinicalBERT) | Domain-tuned | Smaller models with mixed published benchmarks; harder to get BAA-eligible managed service |

Path A (`text-embedding-3-large` via Azure) is the recommended default. If Azure BAA becomes problematic, fall back to self-hosted `bge-large-en-v1.5`.

## Pre-conditions

- [ ] `pgvector-migration.md` executed (or being executed in the same combined cutover)
- [ ] Azure subscription provisioned
- [ ] Azure OpenAI resource deployed in a region with `text-embedding-3-large` availability (currently East US, East US 2, North Central US, South Central US, West US 3)
- [ ] Azure account-level BAA signed (per `BAA_INVENTORY.md`)
- [ ] Azure OpenAI quota approved for `text-embedding-3-large` (default tier is 350K TPM, plenty for PACCA scale)

## Procedure

### Step 1 — Azure resource provisioning (~3 hours)

1. Create Azure OpenAI resource in chosen region.
2. Deploy `text-embedding-3-large` model under a deployment name (e.g., `pacca-embeddings`).
3. Generate API key + endpoint URL.
4. Store in AWS Secrets Manager (or your secrets backend) as `AZURE_OPENAI_API_KEY` and `AZURE_OPENAI_ENDPOINT`.

### Step 2 — Embedding function abstraction (~4 hours)

In `src/pacca/integrations/embeddings.py` (new file), introduce an abstraction so the rest of the code doesn't depend on a specific provider: <!-- drift-guard: ignore -->

```python
class EmbeddingProvider(Protocol):
    dimension: int
    async def embed(self, texts: list[str]) -> list[list[float]]: ...

class AzureOpenAIEmbedding(EmbeddingProvider):
    dimension = 3072
    def __init__(self):
        self._client = AsyncAzureOpenAI(
            api_key=settings.AZURE_OPENAI_API_KEY,
            azure_endpoint=settings.AZURE_OPENAI_ENDPOINT,
            api_version="2024-02-15-preview",
        )

    async def embed(self, texts):
        resp = await self._client.embeddings.create(
            input=texts,
            model="pacca-embeddings",  # deployment name
        )
        return [item.embedding for item in resp.data]

class ChromaDefaultEmbedding(EmbeddingProvider):
    dimension = 384
    # wraps the existing chromadb embedding function
```

Feature flag `EMBEDDING_PROVIDER` in settings: `azure_openai` (new) or `chroma_default` (rollback).

### Step 3 — A/B retrieval benchmark (~6 hours)

Before committing to the upgrade, prove it actually improves clinical retrieval. Run side-by-side on the 100-case benchmark:

```bash
# Generate two retrieval traces
EMBEDDING_PROVIDER=chroma_default pytest tests/clinical/ --capture-retrievals=/tmp/retrieval_old.json
EMBEDDING_PROVIDER=azure_openai pytest tests/clinical/ --capture-retrievals=/tmp/retrieval_new.json

# Compare
python scripts/compare_embeddings.py /tmp/retrieval_old.json /tmp/retrieval_new.json
```

The compare script outputs:
- **recall@k** for k ∈ {1, 3, 5, 10} — what fraction of cases had the "correct" guideline in top-k
- **MRR** (mean reciprocal rank) — average rank of the correct guideline
- **Per-case eval-score delta** — does the downstream agent decision improve when given the new retrievals?

**Acceptance gate:** recall@5 must increase by ≥ 2 absolute percentage points OR MRR must improve by ≥ 0.05 OR per-case eval score must improve by ≥ 1% with NO regression on any metric.

If the A/B fails this bar, DO NOT cut over. The embedding upgrade only justifies itself if it measurably helps. Document the negative result in `DECISIONS.md` (this is a falsifiable-prediction-rejected entry, valid harness-engineering output).

### Step 4 — Re-embedding (~2 hours of compute + babysitting)

If A/B passes:

```python
# scripts/reembed_all.py
for row in pg.execute("SELECT id, content FROM guideline_chunks"):
    new_embedding = await azure_embedding.embed([row.content])
    pg.execute("UPDATE guideline_chunks SET embedding = %s WHERE id = %s",
               [new_embedding[0], row.id])
```

Note: schema migration to `vector(3072)` happens before the re-embed. Run during low-traffic window.

Cost calc: ~3000 vectors × ~500 tokens average × $0.13/1M tokens = **$0.20 one-time**. Negligible.

### Step 5 — Tests (~3 hours)

- Update fixtures that hard-code 384-dim vectors to use 3072-dim
- Add a test that the embedding provider abstraction correctly dispatches based on feature flag
- Verify all 245 sme_authoring tests still pass

## Acceptance criteria

- [ ] A/B benchmark shows ≥ 2pp recall@5 improvement OR ≥ 0.05 MRR improvement OR ≥ 1% per-case eval score improvement
- [ ] No regression on any retrieval metric
- [ ] All vectors successfully re-embedded; row count unchanged
- [ ] All existing tests pass with `EMBEDDING_PROVIDER=azure_openai`
- [ ] p95 embedding latency < 200ms (Azure OpenAI is typically 50-100ms)

## Rollback

If retrieval quality regresses post-cutover:
1. Set `EMBEDDING_PROVIDER=chroma_default`
2. Re-embed all vectors with the old model (one-time, ~$0)
3. Schema rollback: alter column back to `vector(384)`
4. Restart workers

Because the pre-cutover A/B is mandatory and the gate is strict, this rollback should rarely be needed. The bigger risk is hitting an edge case in production retrievals that the benchmark didn't cover — monitor retrieval quality metrics for 7 days post-cutover.

## Risks

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| A/B fails to show improvement | Medium | Low | Document as a falsified hypothesis; revert. Cost: a few hours of wasted setup, nothing else |
| Azure OpenAI rate-limit hit during re-embedding | Low | Low | Default 350K TPM is plenty; throttle re-embed loop to 10K tokens/sec just in case |
| Azure region outage during cutover | Low | Medium | Don't re-embed during regional maintenance windows; check Azure status page first |
| Schema migration locks the table during re-embed | Medium | Low | Re-embed via in-place UPDATE (no lock); altering column dim from 384→3072 IS a lock — do during a maintenance window |
| Cost overruns (unlikely but possible) | Very low | Low | Set Azure OpenAI quota alerts at $50/month; PACCA's expected spend is $1-5/month |

## Companion docs

- [`pgvector-migration.md`](pgvector-migration.md) — prerequisite or same-cutover companion
- [`bedrock-routing.md`](bedrock-routing.md) — unrelated LLM-layer migration
- [`postgres-hardening.md`](postgres-hardening.md) — unrelated Postgres ops work
- [`BAA_INVENTORY.md`](../BAA_INVENTORY.md) — Azure BAA status

---

*Last updated: 2026-05-27. Status: PLANNED, not yet executed.*
