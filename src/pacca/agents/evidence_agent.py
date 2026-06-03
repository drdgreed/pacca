"""Evidence Aggregation Agent — synthesizes a ClinicalCase into a structured
evidence summary used as advisory enrichment for the Decision agent.

Mirrors DecisionAgent: builds a user-turn prompt from the case JSON and calls
BaseAgent.execute() with the EvidenceOutput response model.
"""

from ..models.triage import EvidenceOutput
from .base import BaseAgent
from .decision import DecisionContext
from .prompts import EVIDENCE_AGENT_SYSTEM


class EvidenceAggregationAgent(BaseAgent):
    """Pre-decision evidence synthesis (PRD 'Evidence Aggregation')."""

    @property
    def name(self) -> str:
        return "EvidenceAggregationAgent"

    @property
    def system_prompt(self) -> str:
        return EVIDENCE_AGENT_SYSTEM

    async def run(self, context: DecisionContext) -> EvidenceOutput:
        user_input = f"## Clinical Case\n{context.case.model_dump_json(indent=2)}"
        return await self.execute(user_input=user_input, response_model=EvidenceOutput)
