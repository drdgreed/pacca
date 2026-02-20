import sys
import os
sys.path.append(os.getcwd())
from src.pacca.integrations.vector_store import GuidelineRetriever

def seed():
    print("Seeding NCCN Guidelines...")
    rag = GuidelineRetriever()
    
    # 1. Lung Cancer (Happy Path)
    rag.add_guideline(
        """CRITERIA FOR LUNG CANCER SCREENING (71250):
           Age 50-80 AND 20 pack-year history.""", 
        "NCCN-LUNG-001", {"specialty": "Oncology"}
    )
    
    # 2. Spine MRI (The Edge Case)
    rag.add_guideline(
        """CRITERIA FOR MRI LUMBAR SPINE (72148):
           Indicated only after 6 weeks of conservative therapy.""",
        "CMS-SPINE-002", {"specialty": "Orthopedics"}
    )
    print("Database seeded.")

if __name__ == "__main__":
    seed()
