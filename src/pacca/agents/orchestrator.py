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
