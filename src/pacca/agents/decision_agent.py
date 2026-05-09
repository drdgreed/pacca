"""
Decision Support Agent.

Responsible for evaluating authorization requests against clinical
guidelines and generating recommendations with detailed rationale.
"""

from datetime import datetime, timedelta

from pydantic import BaseModel, Field

from pacca.agents.base import BaseAgent
from pacca.agents.prompts import DECISION_AGENT_SYSTEM, build_decision_prompt
from pacca.agents.types import AgentContext
from pacca.config import get_logger, get_settings
from pacca.models import (
    AgentType,
    AuthorizationDecision,
    AuthorizationRequest,
    DecisionOutcome,
    DecisionRationale,
    EscalationReason,
)

logger = get_logger(__name__)


class RationaleOutput(BaseModel):
    """Rationale section of decision output."""

    summary: str = Field(..., description="Brief decision summary")
    detailed_reasoning: str = Field(..., description="Detailed reasoning chain")
    key_evidence_points: list[str] = Field(default_factory=list)
    evidence_gaps: list[str] = Field(default_factory=list)
    guideline_alignment: str = Field(..., description="How decision aligns with guidelines")
    clinical_risks: list[str] = Field(default_factory=list)
    safety_concerns: list[str] = Field(default_factory=list)


class DecisionOutput(BaseModel):
    """Structured output from Decision Support Agent."""

    recommendation: str = Field(..., description="Decision recommendation")
    confidence_score: float = Field(..., ge=0.0, le=1.0)
    rationale: RationaleOutput = Field(..., description="Decision rationale")
    conditions: list[str] = Field(default_factory=list, description="Approval conditions")
    required_actions: list[str] = Field(default_factory=list, description="Required follow-up")
    escalation_reasons: list[str] = Field(default_factory=list, description="Escalation reasons")


class DecisionSupportAgent(BaseAgent[DecisionOutput]):
    """
    Agent responsible for generating authorization recommendations.

    This agent:
    1. Evaluates the request against clinical guidelines
    2. Assesses medical necessity
    3. Checks step therapy requirements
    4. Identifies contraindications and safety concerns
    5. Generates a recommendation with detailed rationale

    IMPORTANT: This agent generates RECOMMENDATIONS, not final decisions.
    All recommendations are subject to human review based on configuration.
    """

    @property
    def agent_type(self) -> AgentType:
        return AgentType.DECISION_SUPPORT

    @property
    def output_model(self) -> type[DecisionOutput]:
        return DecisionOutput

    @property
    def system_prompt(self) -> str:
        return DECISION_AGENT_SYSTEM

    async def execute(
        self,
        request: AuthorizationRequest,
        context: AgentContext,
    ) -> DecisionOutput:
        """
        Execute decision support for the authorization request.

        Args:
            request: The authorization request
            context: Execution context with evidence and classification

        Returns:
            DecisionOutput with recommendation and rationale
        """
        logger.info(
            "decision_support_started",
            request_id=request.request_id,
            treatment=request.requested_treatment.code,
        )

        # Get outputs from previous agents
        evidence_output = context.get_agent_output(AgentType.EVIDENCE_AGGREGATION)
        classification_output = context.get_agent_output(AgentType.CLINICAL_CLASSIFICATION)

        # Extract relevant information
        if evidence_output:
            clinical_narrative = self._build_narrative(evidence_output)
            evidence_quality = evidence_output.get("evidence_quality", "MODERATE")
        else:
            clinical_narrative = request.clinical_notes or "No clinical narrative available"
            evidence_quality = "MODERATE"

        if classification_output:
            complexity = classification_output.get("complexity", 3)
            specialty = classification_output.get("primary_specialty", "GENERAL")
            urgency = classification_output.get("urgency_assessment", "ROUTINE")
        else:
            complexity = 3
            specialty = "GENERAL"
            urgency = "ROUTINE"

        # Get relevant guidelines (in production, this would use RAG)
        guidelines = await self._retrieve_guidelines(request)

        # Build the prompt
        prompt = build_decision_prompt(
            request_id=request.request_id,
            patient_age=request.patient.age,
            diagnosis_code=request.primary_diagnosis.code,
            diagnosis_description=request.primary_diagnosis.description,
            treatment_code=request.requested_treatment.code,
            treatment_description=request.requested_treatment.description,
            treatment_category=request.requested_treatment.category.value,
            estimated_cost=request.requested_treatment.estimated_cost or 0.0,
            clinical_narrative=clinical_narrative,
            evidence_quality=evidence_quality,
            complexity=complexity,
            specialty=specialty,
            urgency=urgency,
            guidelines=guidelines,
        )

        # Call LLM
        response = await self._call_llm(
            messages=[{"role": "user", "content": prompt}],
            temperature=0.0,
        )

        # Parse structured output
        output = await self._parse_structured_output(response)

        logger.info(
            "decision_support_completed",
            request_id=request.request_id,
            recommendation=output.recommendation,
            confidence=output.confidence_score,
            has_conditions=len(output.conditions) > 0,
        )

        return output

    def _build_narrative(self, evidence_output: dict) -> str:
        """Build clinical narrative from evidence output."""
        parts = []

        if patient_summary := evidence_output.get("patient_summary"):
            parts.append(f"**Patient Summary:** {patient_summary}")

        if clinical_history := evidence_output.get("clinical_history"):
            parts.append(f"**Clinical History:** {clinical_history}")

        if current_condition := evidence_output.get("current_condition"):
            parts.append(f"**Current Condition:** {current_condition}")

        if treatment_rationale := evidence_output.get("treatment_rationale"):
            parts.append(f"**Treatment Rationale:** {treatment_rationale}")

        if supporting_evidence := evidence_output.get("supporting_evidence"):
            parts.append(f"**Supporting Evidence:** {supporting_evidence}")

        return "\n\n".join(parts) if parts else "No clinical narrative available"

    async def _retrieve_guidelines(self, request: AuthorizationRequest) -> str:
        """
        Retrieve relevant clinical guidelines for the request.

        In production, this would use RAG to search a vector database
        of clinical guidelines. For MVP, we return mock guidelines.
        """
        # Record this as a tool call for observability
        self._record_tool_call(
            tool_name="retrieve_guidelines",
            tool_input={
                "diagnosis": request.primary_diagnosis.code,
                "treatment": request.requested_treatment.code,
                "category": request.requested_treatment.category.value,
            },
            tool_output="Mock guidelines retrieved",
            success=True,
        )

        # MVP: Return basic guideline structure
        # In production, this would be real guideline content from RAG
        diagnosis_code = request.primary_diagnosis.code
        treatment_category = request.requested_treatment.category.value

        guidelines = f"""
## Applicable Clinical Guidelines

### Medical Necessity Criteria
For {treatment_category} treatments related to diagnosis {diagnosis_code}:

1. **Documentation Requirements:**
   - Confirmed diagnosis with supporting clinical evidence
   - Treatment plan from qualified provider
   - Relevant lab results and imaging (if applicable)

2. **Step Therapy (if applicable):**
   - First-line treatments should be attempted unless contraindicated
   - Documentation of treatment failure or intolerance required for advanced therapies

3. **Coverage Criteria:**
   - Treatment must be FDA-approved for the indicated condition
   - Dosing must align with approved labeling or evidence-based protocols
   - Duration of authorization based on clinical guidelines

4. **Special Considerations:**
   - Pediatric patients may have different criteria
   - Geriatric patients require assessment of contraindications
   - High-cost treatments (>${get_settings().high_cost_threshold:,}) require medical director review

*Note: These are generalized guidelines. Specific payer policies may vary.*
"""
        return guidelines

    async def calculate_confidence(
        self,
        output: DecisionOutput,
        context: AgentContext,
    ) -> float:
        """Use the confidence score from the LLM output."""
        return output.confidence_score

    async def should_escalate(
        self,
        output: DecisionOutput,
        confidence: float,
        context: AgentContext,
    ) -> tuple[bool, list[str]]:
        """Determine escalation based on decision output."""
        should_escalate, reasons = await super().should_escalate(output, confidence, context)

        # Escalate if the agent itself recommends escalation
        if output.recommendation.upper() == "ESCALATE":
            should_escalate = True
            reasons.extend(output.escalation_reasons)

        # Escalate if there are safety concerns
        if output.rationale.safety_concerns:
            should_escalate = True
            reasons.append(f"Safety concerns identified: {output.rationale.safety_concerns}")

        # Escalate denials for additional review (optional, configurable)
        get_settings()
        if output.recommendation.upper() == "DENY" and confidence < 0.9:
            should_escalate = True
            reasons.append("Denial recommendation requires human verification")

        return should_escalate, reasons

    async def get_next_agent(
        self,
        output: DecisionOutput,
        context: AgentContext,
    ) -> AgentType | None:
        """Decision agent is the last in the main chain."""
        # Orchestration agent handles what happens next
        return AgentType.ORCHESTRATION

    def to_authorization_decision(
        self,
        output: DecisionOutput,
        request_id: str,
        was_escalated: bool = False,
        escalation_reasons: list[EscalationReason] | None = None,
    ) -> AuthorizationDecision:
        """Convert agent output to AuthorizationDecision model."""
        # Map recommendation string to enum
        recommendation_map = {
            "APPROVE": DecisionOutcome.APPROVE,
            "DENY": DecisionOutcome.DENY,
            "APPROVE_WITH_CONDITIONS": DecisionOutcome.APPROVE_WITH_CONDITIONS,
            "REQUEST_MORE_INFO": DecisionOutcome.REQUEST_MORE_INFO,
            "ESCALATE": DecisionOutcome.ESCALATE,
        }

        outcome = recommendation_map.get(
            output.recommendation.upper(),
            DecisionOutcome.UNABLE_TO_DETERMINE,
        )

        # Build rationale
        rationale = DecisionRationale(
            summary=output.rationale.summary,
            detailed_reasoning=output.rationale.detailed_reasoning,
            key_evidence_points=output.rationale.key_evidence_points,
            evidence_gaps=output.rationale.evidence_gaps,
            clinical_risks=output.rationale.clinical_risks,
            safety_concerns=output.rationale.safety_concerns,
        )

        # Calculate authorization validity period
        effective_date = datetime.utcnow()
        expiration_date = effective_date + timedelta(days=90)  # Standard 90-day authorization

        return AuthorizationDecision(
            request_id=request_id,
            outcome=outcome,
            confidence_score=output.confidence_score,
            rationale=rationale,
            conditions=output.conditions,
            required_actions=output.required_actions,
            effective_date=effective_date if outcome == DecisionOutcome.APPROVE else None,
            expiration_date=expiration_date if outcome == DecisionOutcome.APPROVE else None,
            decided_by="decision_support_agent",
            is_autonomous=not was_escalated,
            was_escalated=was_escalated,
            escalation_reasons=escalation_reasons or [],
        )
