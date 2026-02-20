from fastapi import APIRouter
from ...agents.evolution import EvolutionAgent
from ...integrations.vector_store import GuidelineRetriever

router = APIRouter()
evolver = EvolutionAgent()
rag = GuidelineRetriever()

@router.post("/optimize_policies")
async def run_dark_factory_optimization():
    # Level 5: Self-Optimization Mock
    # We provide 10 identical overrides to force the AI to be confident
    spine_overrides = [
        "Override: Approved MRI for 2 weeks pain due to severe motor weakness."
    ] * 10
    
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
