import os
import sys

# 1. THE PATH HACK
# Find out exactly where this seed_db.py file lives (the 'api' folder)
current_dir = os.path.dirname(os.path.abspath(__file__))
# Navigate up three folders to your main "pacca" project root
project_root = os.path.abspath(os.path.join(current_dir, "../../.."))
# Force Python to add your project root to its search radar
sys.path.insert(0, project_root)

# 2. NOW Python can safely see the 'src' folder!
from src.pacca.integrations.vector_store import GuidelineRetriever


def seed_database():
    print("Connecting to ChromaDB...")
    rag_engine = GuidelineRetriever()

    print("Injecting Medical Guidelines...")

    # Guideline 1: Strict Approval Criteria
    rag_engine.add_guideline(
        guideline_text="""
        INDICATIONS FOR MRI LUMBAR SPINE (CPT 72148):
        MRI is considered medically necessary for acute lumbar pain ONLY IF accompanied by 'red flag' clinical signs.
        Red flags include:
        1) Cauda equina syndrome (saddle anesthesia, bowel/bladder incontinence).
        2) Significant, progressive motor weakness in the lower extremities.
        3) Suspected spinal infection or severe trauma.
        """,
        source_id="mri_lumbar_approved",
        metadata={"source_type": "CMS_GUIDELINE"},
    )

    # Guideline 2: Strict Denial Criteria
    rag_engine.add_guideline(
        guideline_text="""
        CONTRAINDICATIONS FOR MRI LUMBAR SPINE (CPT 72148):
        MRI is NOT medically necessary for routine, non-specific acute low back pain (duration less than 6 weeks) in the absence of red flag symptoms.
        Patients MUST undergo a minimum of 6 weeks of conservative therapy (Physical Therapy, NSAIDs) before imaging is approved.
        """,
        source_id="mri_lumbar_denied",
        metadata={"source_type": "CMS_GUIDELINE"},
    )

    print("Database seeded successfully! The AI now knows the rules.")


if __name__ == "__main__":
    seed_database()
