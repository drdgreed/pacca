import pytest
import shutil
import os
from fastapi.testclient import TestClient
from src.pacca.api.main import app
from src.pacca.integrations.vector_store import GuidelineRetriever
# Import the modules where the global 'rag_engine' lives so we can overwrite it
from src.pacca.api.routes import authorizations, admin

# We create a specific test database path
TEST_DB_PATH = os.path.join(os.getcwd(), "test_pacca_db")

@pytest.fixture(scope="module")
def test_rag():
    """
    Creates a single RAG engine for the entire test session
    pointed at a temporary directory.
    """
    # 1. Setup: Create clean DB
    if os.path.exists(TEST_DB_PATH):
        shutil.rmtree(TEST_DB_PATH)
    
    # Initialize the Retriever with the custom path
    # We need to hack the init slightly or just rely on the fact 
    # that we can swap the client. 
    # Actually, simpler: We monkeypatch the class to use our path.
    
    # Let's just create it and manually swap the client if needed, 
    # BUT since your code hardcodes "./pacca_db", we need to be clever.
    # The cleanest way without changing source code is to change the CWD 
    # or just Mock the class.
    
    # Let's PATCH the global instances in the route files.
    # But first we need an instance that uses the test path.
    
    # Since 'GuidelineRetriever' hardcodes the path, we will subclass it for tests.
    class TestRetriever(GuidelineRetriever):
        def __init__(self):
            import chromadb
            from chromadb.utils import embedding_functions
            self.client = chromadb.PersistentClient(path=TEST_DB_PATH)
            self.embedding_fn = embedding_functions.DefaultEmbeddingFunction()
            self.guidelines = self.client.get_or_create_collection(name="nccn_guidelines", embedding_function=self.embedding_fn)
            self.precedents = self.client.get_or_create_collection(name="case_precedents", embedding_function=self.embedding_fn)

    rag = TestRetriever()
    
    # Seed it immediately
    rag.add_guideline(
        """CRITERIA FOR LUNG CANCER SCREENING (71250):
           Age 50-80 AND 20 pack-year history.""", 
        "NCCN-LUNG-001", {"specialty": "Oncology"}
    )
    rag.add_guideline(
        """CRITERIA FOR MRI LUMBAR SPINE (72148):
           Indicated only after 6 weeks of conservative therapy fails.""",
        "CMS-SPINE-002", {"specialty": "Orthopedics"}
    )
    
    yield rag
    
    # 3. Teardown
    if os.path.exists(TEST_DB_PATH):
        shutil.rmtree(TEST_DB_PATH)

@pytest.fixture(autouse=True)
def inject_rag(test_rag):
    """
    This fixture runs before EVERY test.
    It overwrites the 'rag_engine' variable in your API routes 
    with our safe 'test_rag' instance.
    """
    authorizations.rag_engine = test_rag
    admin.rag_engine = test_rag
    
    # IMPORTANT: Clear the 'Memory' collection between tests 
    # so learning tests don't pollute each other.
    try:
        test_rag.client.delete_collection("case_precedents")
    except:
        pass # Collection might not exist
    test_rag.precedents = test_rag.client.get_or_create_collection(
        name="case_precedents", 
        embedding_function=test_rag.embedding_fn
    )

client = TestClient(app)

def test_happy_path_lung_cancer():
    """Level 3 Test: Auto-Approval based on Rules"""
    payload = {
        "request_id": "test_1", "patient_id": "p1", "provider_npi": "123",
        "clinical_case": {
            "patient_id": "p1", "primary_diagnosis_code": "Lung", "procedure_code": "71250",
            "evidence": [{"id":"e1","source_type":"CLINICAL_NOTE","description":"55yo male, 30 pack year history","original_text":"...","confidence":1.0}]
        }
    }
    response = client.post("/api/v1/authorizations/", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "AUTO_APPROVED"

def test_learning_loop_spine():
    """Level 4 Test: Fail -> Teach -> Succeed"""
    # 1. Submit WEAK Case (Should Fail/Review)
    case_payload = {
        "request_id": "test_spine", "patient_id": "p2", "provider_npi": "123",
        "clinical_case": {
            "patient_id": "p2", "primary_diagnosis_code": "BackPain", "procedure_code": "72148",
            "evidence": [{"id":"e2","source_type":"CLINICAL_NOTE","description":"Patient has had back pain for 2 weeks. Requesting MRI.","original_text":"...","confidence":1.0}]
        }
    }
    
    resp1 = client.post("/api/v1/authorizations/", json=case_payload)
    assert resp1.json()["status"] == "IN_REVIEW"
    
    # 2. Teach the System (Override)
    feedback = {
        "case_summary": "MRI Spine requested for 2 weeks pain.",
        "decision": "AUTO_APPROVED",
        "rationale": "Override: Patient actually had severe motor weakness not documented in initial NLP."
    }
    client.post("/api/v1/authorizations/feedback", json=feedback)
    
    # 3. Submit SAME Case Again (Should Pass via Memory)
    resp2 = client.post("/api/v1/authorizations/", json=case_payload)
    data = resp2.json()
    assert data["status"] == "AUTO_APPROVED"
    
    rationale = data["rationale"].lower()
    assert any(x in rationale for x in ["override", "previous", "precedent", "past medical director"])

def test_dark_factory_evolution():
    """Level 5 Test: Policy Rewriting"""
    # Trigger optimization
    resp = client.post("/api/v1/admin/optimize_policies")
    data = resp.json()
    
    if data["status"] == "optimized":
        assert "weakness" in data["change"].lower()
    else:
        assert data["status"] == "proposed"
        assert "weakness" in data["proposal"]["proposed_text"].lower()
