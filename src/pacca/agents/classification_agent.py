"""Clinical Classification Agent — the PRD 'Triage Coordinator'.

Scores complexity (1-5), identifies specialty, and assesses urgency from the
case + the upstream evidence summary. Advisory only: its output enriches the
Decision agent's context; it does not control routing. Mirrors DecisionAgent.
"""

from ..models.triage import ClassificationOutput, EvidenceOutput
from .base import BaseAgent
from .decision import DecisionContext
from .prompts import CLASSIFICATION_AGENT_SYSTEM


class ClinicalClassificationAgent(BaseAgent):
    """Pre-decision triage classification (PRD 'Clinical Classification Agent')."""

    @property
    def name(self) -> str:
        return "ClinicalClassificationAgent"

    @property
    def system_prompt(self) -> str:
        return CLASSIFICATION_AGENT_SYSTEM

    async def run(self, context: DecisionContext, evidence: EvidenceOutput) -> ClassificationOutput:
        findings = "\n".join(f"- {f}" for f in evidence.key_findings)
        user_input = (
            f"## Clinical Case\n"
            f"{context.case.model_dump_json(indent=2)}\n\n"
            f"## Evidence Summary\n{evidence.clinical_narrative}\n\n"
            f"## Key Findings\n{findings}"
        )
        return await self.execute(user_input=user_input, response_model=ClassificationOutput)
