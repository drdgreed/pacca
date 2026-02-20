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
