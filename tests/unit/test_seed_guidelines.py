"""
Guideline seeding — PRODUCTION_READINESS B4.

B4's live crash is gone (the retriever uses idempotent get_or_create_collection
and the B5 structlog fix made the fallback non-fatal). What remained: nothing
seeds the guideline collections, there was no `make seed`, and no test asserted
the collections are ever populated — so a fresh deployment silently serves
*empty* guideline context and the agent decides ungrounded, with no signal.

These tests pin the seeding path: a fresh store starts empty, `seed_database`
populates it, and re-running is idempotent (upsert, not duplicate).

Hermetic by design: a fake embedding function is injected so the test never
downloads ChromaDB's ~80MB default model — important because `pytest tests/unit`
runs in CI with `-x`.
"""

from __future__ import annotations

import numpy as np
from chromadb import EmbeddingFunction

from pacca.api.seed_db import seed_database
from pacca.integrations.vector_store import GuidelineRetriever


class _FakeEmbedding(EmbeddingFunction):
    """Deterministic, offline stand-in for the default MiniLM embedder."""

    def __init__(self) -> None:  # chromadb 1.5+ requires an explicit __init__
        pass

    @staticmethod
    def name() -> str:
        return "fake-test-embedding"

    def __call__(self, input: list[str]) -> list[np.ndarray]:
        return [np.array([float(len(t) % 7), 1.0, 2.0, 3.0], dtype=np.float32) for t in input]


def _retriever(tmp_path: object) -> GuidelineRetriever:
    return GuidelineRetriever(db_path=str(tmp_path), embedding_function=_FakeEmbedding())


def test_fresh_store_starts_empty(tmp_path: object) -> None:
    assert _retriever(tmp_path).guideline_count() == 0


def test_seed_database_populates_the_guidelines_collection(tmp_path: object) -> None:
    retriever = _retriever(tmp_path)
    count = seed_database(retriever=retriever)
    assert count == retriever.guideline_count()
    assert retriever.guideline_count() > 0, "seeding left the guidelines collection empty (B4)"


def test_seeding_is_idempotent(tmp_path: object) -> None:
    retriever = _retriever(tmp_path)
    first = seed_database(retriever=retriever)
    seed_database(retriever=retriever)  # re-run must not duplicate (upsert by id)
    assert retriever.guideline_count() == first
