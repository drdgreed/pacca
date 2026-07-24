"""
Seed the ChromaDB guideline collection (PRODUCTION_READINESS B4).

Run as an operational step after standing up a fresh store:

    make seed          # or: python -m pacca.api.seed_db

Seeding is deliberately an explicit command, not an on-startup hook: which
guidelines belong in a deployment is environment-specific, and auto-injecting
these demo rules into every environment would be wrong. `seed_database()` is
idempotent — guidelines are upserted by id, so re-running does not duplicate.
"""

from __future__ import annotations

from typing import Any

from ..config import get_logger
from ..integrations.vector_store import GuidelineRetriever

logger = get_logger(__name__)

# Synthetic demo guidelines (CPT 72148 lumbar MRI) — the pair the demo cases and
# the golden lumbar-MRI scenarios are decided against. Synthetic, no PHI.
_GUIDELINES: list[dict[str, Any]] = [
    {
        "source_id": "mri_lumbar_approved",
        "metadata": {"source_type": "CMS_GUIDELINE"},
        "text": """
        INDICATIONS FOR MRI LUMBAR SPINE (CPT 72148):
        MRI is considered medically necessary for acute lumbar pain ONLY IF accompanied by 'red flag' clinical signs.
        Red flags include:
        1) Cauda equina syndrome (saddle anesthesia, bowel/bladder incontinence).
        2) Significant, progressive motor weakness in the lower extremities.
        3) Suspected spinal infection or severe trauma.
        """,
    },
    {
        "source_id": "mri_lumbar_denied",
        "metadata": {"source_type": "CMS_GUIDELINE"},
        "text": """
        CONTRAINDICATIONS FOR MRI LUMBAR SPINE (CPT 72148):
        MRI is NOT medically necessary for routine, non-specific acute low back pain (duration less than 6 weeks) in the absence of red flag symptoms.
        Patients MUST undergo a minimum of 6 weeks of conservative therapy (Physical Therapy, NSAIDs) before imaging is approved.
        """,
    },
]


def seed_database(retriever: GuidelineRetriever | None = None) -> int:
    """
    Upsert the demo guidelines into the store. Returns the number seeded.

    Args:
        retriever: an existing retriever (tests inject one pointed at a temp dir
                   with a fake embedder); defaults to a production retriever.
    """
    rag_engine = retriever or GuidelineRetriever()
    for g in _GUIDELINES:
        rag_engine.add_guideline(
            guideline_text=g["text"],
            source_id=g["source_id"],
            metadata=g["metadata"],
        )
    count = rag_engine.guideline_count()
    logger.info("guidelines_seeded", seeded=len(_GUIDELINES), guideline_count=count)
    return len(_GUIDELINES)


if __name__ == "__main__":
    seed_database()
