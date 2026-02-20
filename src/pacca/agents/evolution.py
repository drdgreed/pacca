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
