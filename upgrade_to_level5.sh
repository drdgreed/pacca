#!/bin/bash

# ==============================================================================
# PACCA LEVEL 5 UPGRADE SCRIPT
# ==============================================================================
# This script scaffolds the complete "Dark Factory" architecture.
# It creates the Agents, the Vector Store with Memory, the Policy Evolver,
# and a Rigorous Test Suite.
# ==============================================================================

echo "🚀 Initiating Level 5 Upgrade..."

# 1. SCAFFOLD DIRECTORIES
echo "📂 Creating directory structure..."
mkdir -p src/pacca/agents
mkdir -p src/pacca/integrations
mkdir -p src/pacca/models
mkdir -p src/pacca/api/routes
mkdir -p tests
touch src/pacca/__init__.py
touch src/pacca/agents/__init__.py
touch src/pacca/integrations/__init__.py
touch src/pacca/models/__init__.py
touch src/pacca/api/__init__.py
touch src/pacca/api/routes/__init__.py

# ==============================================================================
# 2. DOMAIN MODELS (The "Language")
# ==============================================================================
echo "📝 Writing Domain Models..."

cat <<EOF > src/pacca/models/enums.py
from enum import Enum

class AuthorizationStatus(str, Enum):
    PENDING = "PENDING"
    INFORMATION_NEEDED = "INFORMATION_NEEDED"
    IN_REVIEW = "IN_REVIEW"
    AUTO_APPROVED = "AUTO_APPROVED"
    DENIED = "DENIED"
    CANCELLED = "CANCELLED"

class EvidenceSourceType(str, Enum):
    LAB_RESULT = "LAB_RESULT"
    MEDICATION_HISTORY = "MEDICATION"
    CLINICAL_NOTE = "CLINICAL_NOTE"
    PATIENT_REPORTED = "PATIENT_REPORTED"

class ComplexityLevel(str, Enum):
    ROUTINE = "ROUTINE"
    INTERMEDIATE = "INTERMEDIATE"
    COMPLEX = "COMPLEX"
    CRITICAL = "CRITICAL"

class ReviewTier(str, Enum):
    AUTOMATED = "AUTOMATED"
    MEDICAL_DIRECTOR_AGENT = "MEDICAL_DIRECTOR_AGENT"
    HUMAN = "HUMAN"
EOF

cat <<EOF > src/pacca/models/clinical.py
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field
from .enums import EvidenceSourceType

class EvidenceItem(BaseModel):
    id: str
    source_type: EvidenceSourceType
    description: str
    original_text: str
    confidence: float
    timestamp: datetime = Field(default_factory=datetime.now)

class ClinicalCase(BaseModel):
    patient_id: str
    primary_diagnosis_code: str
    procedure_code: str
    evidence: List[EvidenceItem] = []
EOF

cat <<EOF > src/pacca/models/authorization.py
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field
from .enums import AuthorizationStatus, ReviewTier
from .clinical import ClinicalCase

class AuthorizationDecision(BaseModel):
    decision_id: str
    status: AuthorizationStatus
    confidence_score: float
    rationale: str
    review_tier_used: ReviewTier
    timestamp: datetime = Field(default_factory=datetime.now)

class AuthorizationRequest(BaseModel):
    request_id: str
    patient_id: str
    provider_npi: str
    clinical_case: ClinicalCase
EOF

# ==============================================================================
# 3. VECTOR STORE (The "Brain" with Memory)
# ==============================================================================
echo "🧠 Writing Vector Store Integration..."

cat <<EOF > src/pacca/integrations/vector_store.py
import chromadb
from chromadb.utils import embedding_functions
import os

class GuidelineRetriever:
    def __init__(self):
        # Use a persistent local database
        db_path = os.path.join(os.getcwd(), "pacca_db")
        self.client = chromadb.PersistentClient(path=db_path)
        self.embedding_fn = embedding_functions.DefaultEmbeddingFunction()
        
        # Collection 1: The Official Rules (NCCN/CMS)
        self.guidelines = self.client.get_or_create_collection(
            name="nccn_guidelines",
            embedding_function=self.embedding_fn
        )
        
        # Collection 2: The Institutional Memory (Human Overrides)
        self.precedents = self.client.get_or_create_collection(
            name="case_precedents",
            embedding_function=self.embedding_fn
        )

    def add_guideline(self, guideline_text: str, source_id: str, metadata: dict):
        # We assume overwrite if ID exists for simplicity
        self.guidelines.upsert(
            documents=[guideline_text],
            metadatas=[metadata],
            ids=[source_id]
        )

    def add_precedent(self, case_summary: str, rationale: str, outcome: str):
        self.precedents.add(
            documents=[f"SCENARIO: {case_summary}\nOUTCOME: {outcome}\nREASON: {rationale}"],
            metadatas=[{"type": "human_override"}],
            ids=[f"prec_{hash(case_summary)}"]
        )

    def query(self, clinical_query: str) -> str:
        # 1. Search Official Rules
        rules = self.guidelines.query(query_texts=[clinical_query], n_results=2)
        
        # 2. Search Past Decisions (Memory)
        memories = self.precedents.query(query_texts=[clinical_query], n_results=1)
        
        context = "OFFICIAL GUIDELINES:\n"
        if rules['documents']:
            for doc in rules['documents'][0]:
                context += f"- {doc}\n"
            
        if memories['documents'] and memories['documents'][0]:
            context += "\nPAST MEDICAL DIRECTOR DECISIONS (PRECEDENTS):\n"
            for doc in memories['documents'][0]:
                context += f"- {doc}\n"
                
        return context
EOF

# ==============================================================================
# 4. AGENTS (The "Nervous System")
# ==============================================================================
echo "🤖 Writing AI Agents..."

cat <<EOF > src/pacca/agents/base.py
import os
from abc import ABC, abstractmethod
from typing import Type, TypeVar
from pydantic import BaseModel
from anthropic import AsyncAnthropic

T = TypeVar("T", bound=BaseModel)

class AgentConfig(BaseModel):
    model: str = "claude-3-5-sonnet-20241022"
    temperature: float = 0.0
    max_tokens: int = 4096

class BaseAgent(ABC):
    def __init__(self, config: AgentConfig = AgentConfig()):
        self.config = config
        self.client = AsyncAnthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
        
    @property
    @abstractmethod
    def name(self) -> str: pass

    @property
    @abstractmethod
    def system_prompt(self) -> str: pass

    async def execute(self, user_input: str, response_model: Type[T]) -> T:
        messages = [{"role": "user", "content": user_input}]
        
        # Tool definition to enforce JSON structure
        tool_def = {
            "name": "submit_result",
            "description": f"Submit result for {self.name}",
            "input_schema": response_model.model_json_schema()
        }

        try:
            response = await self.client.messages.create(
                model=self.config.model,
                max_tokens=self.config.max_tokens,
                temperature=self.config.temperature,
                system=self.system_prompt,
                messages=messages,
                tools=[tool_def],
                tool_choice={"type": "tool", "name": "submit_result"}
            )

            for content in response.content:
                if content.type == "tool_use":
                    return response_model.model_validate(content.input)
            
            # Fallback (shouldn't happen with correct tool use)
            raise ValueError("Agent failed to use structured tool")
            
        except Exception as e:
            print(f"Agent {self.name} Error: {e}")
            raise e
EOF

cat <<EOF > src/pacca/agents/decision.py
from pydantic import BaseModel
from ..models.authorization import AuthorizationDecision, ReviewTier
from ..models.clinical import ClinicalCase
from .base import BaseAgent

class DecisionContext(BaseModel):
    case: ClinicalCase
    relevant_guidelines: str

class DecisionAgent(BaseAgent):
    @property
    def name(self) -> str: return "DecisionSupportAgent"

    @property
    def system_prompt(self) -> str:
        return """
        You are a Utilization Management Nurse. Compare the Clinical Case to the Guidelines.
        RULES:
        1. Approve ONLY if strict criteria are met.
        2. If 'PAST MEDICAL DIRECTOR DECISIONS' are present in context, YOU MUST FOLLOW THEM.
        3. Confidence: 1.0 = Perfect match. <0.9 = Ambiguous.
        """

    async def run(self, context: DecisionContext) -> AuthorizationDecision:
        decision = await self.execute(
            user_input=f"Case: {context.case.model_dump_json()}\nContext: {context.relevant_guidelines}", 
            response_model=AuthorizationDecision
        )
        decision.review_tier_used = ReviewTier.AUTOMATED
        return decision

class MedicalDirectorAgent(BaseAgent):
    @property
    def name(self) -> str: return "MedicalDirectorAgent"

    @property
    def system_prompt(self) -> str:
        return "You are a Medical Director. Review ambiguous cases. Approve only if >95% confident."

    async def run(self, context: DecisionContext, previous_decision: AuthorizationDecision) -> AuthorizationDecision:
        decision = await self.execute(
            user_input=f"Previous: {previous_decision.model_dump_json()}\nCase: {context.case.model_dump_json()}\nContext: {context.relevant_guidelines}", 
            response_model=AuthorizationDecision
        )
        decision.review_tier_used = ReviewTier.MEDICAL_DIRECTOR_AGENT
        return decision
EOF

cat <<EOF > src/pacca/agents/evolution.py
from pydantic import BaseModel, Field
from .base import BaseAgent

class PolicyAmendment(BaseModel):
    original_guideline_id: str
    proposed_text: str = Field(description="The new, optimized guideline text.")
    reasoning: str
    auto_deploy: bool = Field(description="True if confidence > 0.99")

class EvolutionAgent(BaseAgent):
    @property
    def name(self) -> str: return "PolicyEvolutionAgent"

    @property
    def system_prompt(self) -> str:
        return """
        You are a Clinical Process Architect.
        INPUT: Original Guideline + List of Human Overrides.
        TASK: If humans consistently approve an exception, rewrite the guideline to include it.
        """

    async def run(self, original: str, overrides: list) -> PolicyAmendment:
        return await self.execute(
            user_input=f"Original Rule: {original}\nOverrides: {overrides}", 
            response_model=PolicyAmendment
        )
EOF

cat <<EOF > src/pacca/agents/orchestrator.py
from .decision import DecisionAgent, MedicalDirectorAgent, DecisionContext
from ..models.authorization import AuthorizationDecision, AuthorizationStatus

class Orchestrator:
    def __init__(self):
        self.decision_agent = DecisionAgent()
        self.medical_director_agent = MedicalDirectorAgent()

    async def process_decision(self, context: DecisionContext) -> AuthorizationDecision:
        decision = await self.decision_agent.run(context)
        
        # Logic: If high confidence (or learnt from memory), auto-approve
        if decision.confidence_score >= 0.95 and decision.status == AuthorizationStatus.AUTO_APPROVED:
            return decision

        # Logic: Tier 2 Escalation
        elif 0.90 <= decision.confidence_score < 0.95:
            md_decision = await self.medical_director_agent.run(context, decision)
            if md_decision.confidence_score >= 0.95:
                md_decision.status = AuthorizationStatus.AUTO_APPROVED
                return md_decision
            md_decision.status = AuthorizationStatus.IN_REVIEW
            return md_decision

        else:
            decision.status = AuthorizationStatus.IN_REVIEW
            return decision
EOF

# ==============================================================================
# 5. API ROUTES (The Interface)
# ==============================================================================
echo "🌐 Writing API Routes..."

cat <<EOF > src/pacca/api/routes/authorizations.py
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from ...models.authorization import AuthorizationRequest, AuthorizationDecision
from ...agents.orchestrator import Orchestrator, DecisionContext
from ...integrations.vector_store import GuidelineRetriever

router = APIRouter()
orchestrator = Orchestrator()
rag_engine = GuidelineRetriever()

class FeedbackRequest(BaseModel):
    case_summary: str
    decision: str
    rationale: str

@router.post("/", response_model=AuthorizationDecision)
async def submit_authorization(request: AuthorizationRequest):
    try:
        case = request.clinical_case
        query = f"Guidelines for {case.primary_diagnosis_code} and {case.procedure_code}"
        
        # Level 3/4: Search Guidelines + Memory
        context_text = rag_engine.query(query)
        
        decision_ctx = DecisionContext(case=case, relevant_guidelines=context_text)
        return await orchestrator.process_decision(decision_ctx)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/feedback")
async def learn_from_feedback(feedback: FeedbackRequest):
    # Level 4: The Learning Loop
    rag_engine.add_precedent(
        case_summary=feedback.case_summary,
        rationale=feedback.rationale,
        outcome=feedback.decision
    )
    return {"status": "learned"}
EOF

cat <<EOF > src/pacca/api/routes/admin.py
from fastapi import APIRouter
from ...agents.evolution import EvolutionAgent
from ...integrations.vector_store import GuidelineRetriever

router = APIRouter()
evolver = EvolutionAgent()
rag = GuidelineRetriever()

@router.post("/optimize_policies")
async def run_dark_factory_optimization():
    # Level 5: Self-Optimization Mock
    # In real life, we would fetch these from the DB
    spine_overrides = [
        "Override: Approved MRI for 2 weeks pain due to severe motor weakness.",
        "Override: Approved MRI for 2 weeks pain due to severe motor weakness.",
        "Override: Approved MRI for 2 weeks pain due to severe motor weakness."
    ]
    current_rule = "Indicated only after 6 weeks of conservative therapy fails."
    
    amendment = await evolver.run(current_rule, spine_overrides)
    
    if amendment.auto_deploy:
        rag.add_guideline(
            guideline_text=amendment.proposed_text,
            source_id="NCCN-SPINE-AI-OPTIMIZED",
            metadata={"source": "AI_EVOLUTION"}
        )
        return {"status": "optimized", "change": amendment.proposed_text}
    return {"status": "proposed", "proposal": amendment}
EOF

cat <<EOF > src/pacca/api/main.py
from fastapi import FastAPI
from .routes import authorizations, admin

app = FastAPI(title="PACCA Level 5")
app.include_router(authorizations.router, prefix="/api/v1/authorizations")
app.include_router(admin.router, prefix="/api/v1/admin")

@app.get("/health")
async def health(): return {"status": "ok"}
EOF

# ==============================================================================
# 6. SEED DATA & TESTS
# ==============================================================================
echo "🌱 Creating Seed Script..."

cat <<EOF > seed_data.py
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
EOF

echo "🧪 Creating Rigorous Test Suite..."

cat <<EOF > tests/test_level5_flow.py
import pytest
import asyncio
from fastapi.testclient import TestClient
from src.pacca.api.main import app
from src.pacca.integrations.vector_store import GuidelineRetriever

client = TestClient(app)

# Helper to reset DB
@pytest.fixture(autouse=True)
def setup_db():
    import seed_data
    seed_data.seed()

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
    assert "NCCN-LUNG" in data["rationale"] or "Age 50-80" in data["rationale"]

def test_learning_loop_spine():
    """Level 4 Test: Fail -> Teach -> Succeed"""
    
    # 1. Submit Case (Should Fail/Review because only 2 weeks pain)
    case_payload = {
        "request_id": "test_spine", "patient_id": "p2", "provider_npi": "123",
        "clinical_case": {
            "patient_id": "p2", "primary_diagnosis_code": "BackPain", "procedure_code": "72148",
            "evidence": [{"id":"e2","source_type":"CLINICAL_NOTE","description":"Severe motor weakness. Pain for 2 weeks.","original_text":"...","confidence":1.0}]
        }
    }
    
    resp1 = client.post("/api/v1/authorizations/", json=case_payload)
    # Expect IN_REVIEW because 2 weeks < 6 weeks rule
    assert resp1.json()["status"] == "IN_REVIEW"
    
    # 2. Teach the System (Override)
    feedback = {
        "case_summary": "MRI Spine requested for 2 weeks pain but severe motor weakness present.",
        "decision": "AUTO_APPROVED",
        "rationale": "Override: Severe motor weakness requires immediate imaging."
    }
    client.post("/api/v1/authorizations/feedback", json=feedback)
    
    # 3. Submit SAME Case Again (Should Pass via Memory)
    resp2 = client.post("/api/v1/authorizations/", json=case_payload)
    assert resp2.json()["status"] == "AUTO_APPROVED"
    assert "Override" in resp2.json()["rationale"]

def test_dark_factory_evolution():
    """Level 5 Test: Policy Rewriting"""
    # Trigger optimization
    resp = client.post("/api/v1/admin/optimize_policies")
    data = resp.json()
    
    assert data["status"] == "optimized"
    # The new rule should mention 'weakness' or 'exception'
    assert "weakness" in data["change"].lower()
    
    # Verify the vector store was actually updated
    rag = GuidelineRetriever()
    results = rag.guidelines.get(ids=["NCCN-SPINE-AI-OPTIMIZED"])
    assert len(results['documents']) > 0
    print(f"New Rule: {results['documents'][0]}")

EOF

echo "✅ Upgrade Complete. Ready to deploy."
EOF