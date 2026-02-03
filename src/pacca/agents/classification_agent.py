"""
Clinical Classification Agent.

Responsible for classifying authorization requests by complexity,
specialty, and urgency to determine appropriate routing and processing.
"""

from pydantic import BaseModel, Field

from pacca.agents.base import BaseAgent
from pacca.agents.prompts import CLASSIFICATION_AGENT_SYSTEM, build_classification_prompt
from pacca.agents.types import AgentContext
from pacca.config import get_logger, get_settings
from pacca.models import (
    AgentType,
    AuthorizationRequest,
    ClassificationResult,
    ClinicalSpecialty,
    ComplexityLevel,
    UrgencyLevel,
)

logger = get_logger(__name__)


class ClassificationOutput(BaseModel):
    """Structured output from Clinical Classification Agent."""

    complexity: int = Field(..., ge=1, le=5, description="Complexity level 1-5")
    complexity_factors: list[str] = Field(
        default_factory=list, description="Factors contributing to complexity"
    )
    primary_specialty: str = Field(..., description="Primary specialty for routing")
    secondary_specialties: list[str] = Field(
        default_factory=list, description="Other relevant specialties"
    )
    urgency_assessment: str = Field(..., description="Urgency level")
    routing_rationale: str = Field(..., description="Explanation for routing")
    requires_specialist_review: bool = Field(False, description="Needs specialist")
    requires_medical_director: bool = Field(False, description="Needs medical director")
    confidence_score: float = Field(..., ge=0.0, le=1.0, description="Classification confidence")


class ClinicalClassificationAgent(BaseAgent[ClassificationOutput]):
    """
    Agent responsible for classifying prior authorization requests.

    This agent:
    1. Assesses case complexity (1-5 scale)
    2. Determines appropriate clinical specialty for routing
    3. Evaluates urgency level
    4. Identifies if specialist or medical director review is needed

    Classification determines how requests are processed and routed.
    """

    @property
    def agent_type(self) -> AgentType:
        return AgentType.CLINICAL_CLASSIFICATION

    @property
    def output_model(self) -> type[ClassificationOutput]:
        return ClassificationOutput

    @property
    def system_prompt(self) -> str:
        return CLASSIFICATION_AGENT_SYSTEM

    async def execute(
        self,
        request: AuthorizationRequest,
        context: AgentContext,
    ) -> ClassificationOutput:
        """
        Execute classification for the authorization request.

        Args:
            request: The authorization request
            context: Execution context with evidence from previous agent

        Returns:
            ClassificationOutput with complexity, specialty, and urgency
        """
        logger.info(
            "classification_started",
            request_id=request.request_id,
            diagnosis=request.primary_diagnosis.code,
        )

        # Get evidence summary from previous agent
        evidence_output = context.get_agent_output(AgentType.EVIDENCE_AGGREGATION)
        if evidence_output:
            evidence_summary = evidence_output.get("supporting_evidence", "No evidence summary")
            evidence_quality = evidence_output.get("evidence_quality", "MODERATE")
        else:
            evidence_summary = request.clinical_notes or "No clinical summary available"
            evidence_quality = "MODERATE"

        # Count comorbidities
        comorbidity_count = 0
        if request.evidence and request.evidence.comorbidities:
            comorbidity_count = len(request.evidence.comorbidities)
        comorbidity_count += len(request.secondary_diagnoses)

        # Build the prompt
        prompt = build_classification_prompt(
            request_id=request.request_id,
            patient_age=request.patient.age,
            diagnosis_code=request.primary_diagnosis.code,
            diagnosis_description=request.primary_diagnosis.description,
            treatment_code=request.requested_treatment.code,
            treatment_description=request.requested_treatment.description,
            treatment_category=request.requested_treatment.category.value,
            estimated_cost=request.requested_treatment.estimated_cost or 0.0,
            evidence_summary=evidence_summary,
            evidence_quality=evidence_quality,
            comorbidity_count=comorbidity_count,
        )

        # Call LLM
        response = await self._call_llm(
            messages=[{"role": "user", "content": prompt}],
            temperature=0.0,
        )

        # Parse structured output
        output = await self._parse_structured_output(response)

        # Apply business rules for additional escalation triggers
        output = await self._apply_escalation_rules(output, request)

        logger.info(
            "classification_completed",
            request_id=request.request_id,
            complexity=output.complexity,
            specialty=output.primary_specialty,
            urgency=output.urgency_assessment,
            requires_specialist=output.requires_specialist_review,
        )

        return output

    async def _apply_escalation_rules(
        self,
        output: ClassificationOutput,
        request: AuthorizationRequest,
    ) -> ClassificationOutput:
        """
        Apply business rules that may override or enhance classification.

        These rules ensure certain conditions always trigger appropriate review.
        """
        settings = get_settings()

        # High-cost cases always need medical director review
        if request.is_high_cost:
            output = ClassificationOutput(
                **{
                    **output.model_dump(),
                    "requires_medical_director": True,
                    "complexity_factors": [
                        *output.complexity_factors,
                        f"High cost authorization (>${settings.high_cost_threshold:,})",
                    ],
                }
            )

        # Pediatric cases may need specialist review
        if request.patient.is_pediatric and output.complexity >= 3:
            output = ClassificationOutput(
                **{
                    **output.model_dump(),
                    "requires_specialist_review": True,
                    "complexity_factors": [
                        *output.complexity_factors,
                        "Pediatric patient with moderate+ complexity",
                    ],
                }
            )

        # Very high complexity always needs specialist
        if output.complexity >= settings.complexity_specialist_review_min:
            output = ClassificationOutput(
                **{
                    **output.model_dump(),
                    "requires_specialist_review": True,
                }
            )

        return output

    async def calculate_confidence(
        self,
        output: ClassificationOutput,
        context: AgentContext,
    ) -> float:
        """Use the confidence score from the LLM output."""
        return output.confidence_score

    async def should_escalate(
        self,
        output: ClassificationOutput,
        confidence: float,
        context: AgentContext,
    ) -> tuple[bool, list[str]]:
        """Determine escalation based on classification results."""
        should_escalate, reasons = await super().should_escalate(
            output, confidence, context
        )

        # Add classification-specific escalation reasons
        if output.requires_specialist_review:
            should_escalate = True
            reasons.append("Specialist review required based on classification")

        if output.requires_medical_director:
            should_escalate = True
            reasons.append("Medical director review required")

        return should_escalate, reasons

    async def get_next_agent(
        self,
        output: ClassificationOutput,
        context: AgentContext,
    ) -> AgentType | None:
        """Classification agent is followed by Decision Support agent."""
        return AgentType.DECISION_SUPPORT

    def to_classification_result(self, output: ClassificationOutput) -> ClassificationResult:
        """Convert agent output to ClassificationResult model."""
        # Map specialty string to enum
        try:
            primary_specialty = ClinicalSpecialty(output.primary_specialty.lower())
        except ValueError:
            primary_specialty = ClinicalSpecialty.GENERAL

        secondary_specialties = []
        for spec in output.secondary_specialties:
            try:
                secondary_specialties.append(ClinicalSpecialty(spec.lower()))
            except ValueError:
                pass

        # Map urgency string to enum
        try:
            urgency = UrgencyLevel(output.urgency_assessment.lower())
        except ValueError:
            urgency = UrgencyLevel.ROUTINE

        return ClassificationResult(
            complexity=ComplexityLevel(output.complexity),
            primary_specialty=primary_specialty,
            secondary_specialties=secondary_specialties,
            urgency_assessment=urgency,
            complexity_factors=output.complexity_factors,
            routing_rationale=output.routing_rationale,
            confidence_score=output.confidence_score,
            requires_specialist_review=output.requires_specialist_review,
            requires_medical_director=output.requires_medical_director,
        )
