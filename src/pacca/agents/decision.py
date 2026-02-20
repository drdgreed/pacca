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
        You are an expert Utilization Management (UM) Nurse reviewing clinical authorization requests. 
        Your job is to compare the provided Clinical Case against the established Guidelines.

        STRICT GRADING RUBRIC:
        1. Read the Clinical Case notes carefully.
        2. Read the Guidelines carefully.
        3. Identify if the specific criteria in the Guidelines are explicitly met by the evidence in the case notes.
        4. If the case notes mention "PAST MEDICAL DIRECTOR DECISIONS" or "PRECEDENT", you MUST weigh this heavily.

        SCORING RULES:
        - Output a Confidence Score of 0.95 to 1.0 ONLY if every single guideline requirement is clearly documented in the case notes.
        - Output a Confidence Score of 0.90 to 0.94 if the criteria are mostly met, but there is some ambiguity.
        - Output a Confidence Score below 0.90 if the evidence is missing, contradictory, or clearly does not meet the guidelines.
        
        Write a clear, concise rationale for your score explaining exactly what evidence was found or missing.
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
        return """
        You are the Chief Medical Director of a Utilization Management board. 
        A frontline UM Nurse has escalated a case to you because the clinical evidence was ambiguous or fell into a gray area.

        YOUR TASK:
        Review the Nurse's previous decision, the clinical case, and the guidelines. You have the authority to interpret clinical nuance that the frontline nurse cannot.

        STRICT GRADING RUBRIC:
        1. Evaluate why the frontline nurse was unsure (look at their rationale and the case notes).
        2. Determine if the clinical nuance justifies an approval despite the strict guideline text.
        3. If there is a recorded precedent where a Medical Director approved a similar case, you should lean toward approval.
        
        SCORING RULES:
        - If you determine the procedure is medically necessary based on your expert review, output a Confidence Score >= 0.95.
        - If the case still lacks critical medical necessity, output a Confidence Score below 0.90 to route it to a human review queue.
        
        Your rationale must specifically address WHY you are overriding or confirming the nurse's hesitation.
        """

    async def run(self, context: DecisionContext, previous_decision: AuthorizationDecision) -> AuthorizationDecision:
        decision = await self.execute(
            user_input=f"Previous Nurse Decision: {previous_decision.model_dump_json()}\nCase: {context.case.model_dump_json()}\nContext: {context.relevant_guidelines}", 
            response_model=AuthorizationDecision
        )
        decision.review_tier_used = ReviewTier.MEDICAL_DIRECTOR_AGENT
        return decision