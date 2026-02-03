"""
Authorization data models for the PACCA system.

These models represent the core authorization workflow entities:
requests, decisions, reviews, and audit records.
"""

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, computed_field
from uuid7 import uuid7

from pacca.models.clinical import (
    ClinicalEvidence,
    ClinicalNarrative,
    Diagnosis,
    PatientDemographics,
    Treatment,
)
from pacca.models.enums import (
    AuthorizationStatus,
    ClinicalSpecialty,
    ComplexityLevel,
    DecisionOutcome,
    EscalationReason,
    ReviewerRole,
    UrgencyLevel,
)


def generate_request_id() -> str:
    """Generate a time-sortable unique request ID."""
    return f"AUTH-{uuid7()}"


class ProviderInfo(BaseModel):
    """Information about the requesting provider."""

    model_config = ConfigDict(frozen=True)

    provider_id: str = Field(..., description="Provider NPI or identifier")
    provider_name: str = Field(..., description="Provider name")
    provider_specialty: ClinicalSpecialty | None = Field(None, description="Provider specialty")
    facility_name: str | None = Field(None, description="Facility name")
    facility_id: str | None = Field(None, description="Facility identifier")
    contact_phone: str | None = Field(None, description="Contact phone number")
    contact_fax: str | None = Field(None, description="Contact fax number")


class PayerInfo(BaseModel):
    """Information about the insurance payer."""

    model_config = ConfigDict(frozen=True)

    payer_id: str = Field(..., description="Payer identifier")
    payer_name: str = Field(..., description="Payer name")
    plan_id: str | None = Field(None, description="Plan identifier")
    plan_name: str | None = Field(None, description="Plan name")
    member_id: str = Field(..., description="Member ID")
    group_number: str | None = Field(None, description="Group number")


class AuthorizationRequest(BaseModel):
    """
    A prior authorization request submitted for processing.

    This is the primary input to the PACCA system, containing all
    information needed to evaluate a prior authorization.
    """

    model_config = ConfigDict(frozen=False)  # Mutable for status updates

    # Identification
    request_id: str = Field(default_factory=generate_request_id, description="Unique request ID")
    external_reference: str | None = Field(None, description="External system reference")

    # Timestamps
    submitted_at: datetime = Field(default_factory=datetime.utcnow, description="Submission time")
    updated_at: datetime = Field(default_factory=datetime.utcnow, description="Last update time")

    # Status tracking
    status: AuthorizationStatus = Field(
        AuthorizationStatus.SUBMITTED, description="Current status"
    )

    # Clinical information
    patient: PatientDemographics = Field(..., description="Patient demographics")
    primary_diagnosis: Diagnosis = Field(..., description="Primary diagnosis")
    secondary_diagnoses: list[Diagnosis] = Field(
        default_factory=list, description="Secondary diagnoses"
    )
    requested_treatment: Treatment = Field(..., description="Requested treatment/service")

    # Provider and payer
    requesting_provider: ProviderInfo = Field(..., description="Requesting provider")
    payer: PayerInfo = Field(..., description="Insurance payer")

    # Clinical context
    clinical_notes: str | None = Field(None, description="Supporting clinical notes")
    urgency: UrgencyLevel = Field(UrgencyLevel.ROUTINE, description="Request urgency")

    # Processing metadata (populated by agents)
    evidence: ClinicalEvidence | None = Field(None, description="Gathered clinical evidence")
    narrative: ClinicalNarrative | None = Field(None, description="Generated clinical narrative")
    complexity: ComplexityLevel | None = Field(None, description="Assessed complexity")
    assigned_specialty: ClinicalSpecialty | None = Field(None, description="Assigned specialty")

    @computed_field  # type: ignore[prop-decorator]
    @property
    def days_since_submission(self) -> float:
        """Calculate days since submission."""
        delta = datetime.utcnow() - self.submitted_at
        return delta.total_seconds() / 86400

    @computed_field  # type: ignore[prop-decorator]
    @property
    def is_high_cost(self) -> bool:
        """Check if this is a high-cost authorization."""
        if self.requested_treatment.estimated_cost:
            return self.requested_treatment.estimated_cost >= 100000
        return False

    def update_status(self, new_status: AuthorizationStatus) -> None:
        """Update the request status and timestamp."""
        self.status = new_status
        self.updated_at = datetime.utcnow()


class ClassificationResult(BaseModel):
    """
    Result from the Clinical Classification Agent.

    Contains the complexity assessment, specialty routing,
    and urgency evaluation for a request.
    """

    model_config = ConfigDict(frozen=True)

    complexity: ComplexityLevel = Field(..., description="Assessed complexity level")
    primary_specialty: ClinicalSpecialty = Field(..., description="Primary specialty for routing")
    secondary_specialties: list[ClinicalSpecialty] = Field(
        default_factory=list, description="Secondary relevant specialties"
    )
    urgency_assessment: UrgencyLevel = Field(..., description="Urgency assessment")

    # Classification details
    complexity_factors: list[str] = Field(
        default_factory=list, description="Factors contributing to complexity"
    )
    routing_rationale: str = Field(..., description="Rationale for specialty routing")

    # Confidence
    confidence_score: float = Field(
        ..., ge=0.0, le=1.0, description="Classification confidence (0-1)"
    )

    # Flags
    requires_specialist_review: bool = Field(False, description="Needs specialist")
    requires_medical_director: bool = Field(False, description="Needs medical director")

    classified_at: datetime = Field(default_factory=datetime.utcnow)


class GuidelineMatch(BaseModel):
    """A matched clinical guideline with relevance score."""

    model_config = ConfigDict(frozen=True)

    guideline_id: str = Field(..., description="Guideline identifier")
    guideline_name: str = Field(..., description="Guideline name")
    version: str = Field(..., description="Guideline version")
    source: str = Field(..., description="Guideline source (NCCN, AHA, etc.)")

    relevance_score: float = Field(..., ge=0.0, le=1.0, description="Relevance score")
    matched_criteria: list[str] = Field(
        default_factory=list, description="Specific criteria matched"
    )
    excerpt: str | None = Field(None, description="Relevant excerpt from guideline")


class DecisionRationale(BaseModel):
    """
    Detailed rationale for an authorization decision.

    Provides transparency into the decision-making process
    including evidence citations and guideline references.
    """

    model_config = ConfigDict(frozen=True)

    summary: str = Field(..., description="Brief decision summary")
    detailed_reasoning: str = Field(..., description="Detailed reasoning chain")

    # Evidence used
    key_evidence_points: list[str] = Field(
        default_factory=list, description="Key evidence supporting decision"
    )
    evidence_gaps: list[str] = Field(default_factory=list, description="Gaps in evidence")

    # Guideline alignment
    guideline_matches: list[GuidelineMatch] = Field(
        default_factory=list, description="Matched guidelines"
    )
    guideline_conflicts: list[str] = Field(
        default_factory=list, description="Any guideline conflicts"
    )

    # Risk assessment
    clinical_risks: list[str] = Field(default_factory=list, description="Identified clinical risks")
    safety_concerns: list[str] = Field(default_factory=list, description="Safety concerns")


class AuthorizationDecision(BaseModel):
    """
    The authorization decision produced by the system.

    This represents the output of the Decision Support Agent,
    potentially modified by human review.
    """

    model_config = ConfigDict(frozen=False)

    # Identification
    decision_id: str = Field(default_factory=lambda: str(uuid7()), description="Decision ID")
    request_id: str = Field(..., description="Associated request ID")

    # Decision
    outcome: DecisionOutcome = Field(..., description="Decision outcome")
    confidence_score: float = Field(..., ge=0.0, le=1.0, description="Decision confidence")

    # Rationale
    rationale: DecisionRationale = Field(..., description="Decision rationale")

    # Conditions (for conditional approvals)
    conditions: list[str] = Field(
        default_factory=list, description="Conditions for approval"
    )
    required_actions: list[str] = Field(
        default_factory=list, description="Required follow-up actions"
    )

    # Validity
    effective_date: datetime | None = Field(None, description="When authorization is effective")
    expiration_date: datetime | None = Field(None, description="When authorization expires")
    authorized_quantity: int | None = Field(None, description="Authorized quantity")
    authorized_duration_days: int | None = Field(None, description="Authorized duration")

    # Processing metadata
    decided_at: datetime = Field(default_factory=datetime.utcnow)
    decided_by: str = Field("system", description="Decider (system or reviewer ID)")
    is_autonomous: bool = Field(True, description="Whether decided autonomously")

    # Escalation
    was_escalated: bool = Field(False, description="Whether escalated to human")
    escalation_reasons: list[EscalationReason] = Field(
        default_factory=list, description="Reasons for escalation"
    )


class HumanReview(BaseModel):
    """
    Human review of an authorization decision.

    Records the human reviewer's assessment, modifications,
    and final determination.
    """

    model_config = ConfigDict(frozen=True)

    review_id: str = Field(default_factory=lambda: str(uuid7()), description="Review ID")
    decision_id: str = Field(..., description="Associated decision ID")
    request_id: str = Field(..., description="Associated request ID")

    # Reviewer info
    reviewer_id: str = Field(..., description="Reviewer identifier")
    reviewer_role: ReviewerRole = Field(..., description="Reviewer's role")

    # Review details
    original_outcome: DecisionOutcome = Field(..., description="Original AI decision")
    final_outcome: DecisionOutcome = Field(..., description="Final reviewed decision")
    outcome_changed: bool = Field(False, description="Whether outcome was changed")

    # Reviewer assessment
    agrees_with_rationale: bool = Field(..., description="Agrees with AI rationale")
    reviewer_notes: str | None = Field(None, description="Reviewer notes")
    additional_rationale: str | None = Field(None, description="Additional rationale added")

    # Quality feedback
    ai_accuracy_rating: int | None = Field(
        None, ge=1, le=5, description="Rating of AI accuracy (1-5)"
    )
    feedback_tags: list[str] = Field(default_factory=list, description="Feedback tags")

    reviewed_at: datetime = Field(default_factory=datetime.utcnow)
    time_spent_seconds: int | None = Field(None, description="Time spent reviewing")


class AuditLogEntry(BaseModel):
    """
    Audit log entry for tracking all system actions.

    Provides complete traceability for compliance and debugging.
    """

    model_config = ConfigDict(frozen=True)

    entry_id: str = Field(default_factory=lambda: str(uuid7()), description="Log entry ID")
    timestamp: datetime = Field(default_factory=datetime.utcnow)

    # Context
    request_id: str | None = Field(None, description="Associated request ID")
    decision_id: str | None = Field(None, description="Associated decision ID")

    # Action details
    action: str = Field(..., description="Action performed")
    actor: str = Field(..., description="Actor (agent name, user ID, or system)")
    actor_type: str = Field(..., description="Actor type (agent, user, system)")

    # Data
    details: dict[str, Any] = Field(default_factory=dict, description="Action details")
    input_summary: str | None = Field(None, description="Summary of input")
    output_summary: str | None = Field(None, description="Summary of output")

    # Status
    success: bool = Field(True, description="Whether action succeeded")
    error_message: str | None = Field(None, description="Error message if failed")

    # Performance
    duration_ms: int | None = Field(None, description="Action duration in milliseconds")
    token_usage: dict[str, int] | None = Field(None, description="LLM token usage")


class AuthorizationSummary(BaseModel):
    """
    Summary view of an authorization for listings and dashboards.

    Provides a lightweight view without full evidence/rationale.
    """

    model_config = ConfigDict(frozen=True)

    request_id: str
    status: AuthorizationStatus
    outcome: DecisionOutcome | None = None

    # Patient (minimal)
    patient_id: str
    patient_age: int

    # Clinical (minimal)
    diagnosis_code: str
    diagnosis_description: str
    treatment_code: str
    treatment_description: str
    treatment_category: str

    # Classification
    complexity: ComplexityLevel | None = None
    urgency: UrgencyLevel
    specialty: ClinicalSpecialty | None = None

    # Timing
    submitted_at: datetime
    decided_at: datetime | None = None
    days_in_process: float

    # Flags
    is_high_cost: bool = False
    was_escalated: bool = False
    requires_review: bool = False

    @classmethod
    def from_request(
        cls,
        request: AuthorizationRequest,
        decision: AuthorizationDecision | None = None,
    ) -> "AuthorizationSummary":
        """Create a summary from a request and optional decision."""
        return cls(
            request_id=request.request_id,
            status=request.status,
            outcome=decision.outcome if decision else None,
            patient_id=request.patient.patient_id,
            patient_age=request.patient.age,
            diagnosis_code=request.primary_diagnosis.code,
            diagnosis_description=request.primary_diagnosis.description,
            treatment_code=request.requested_treatment.code,
            treatment_description=request.requested_treatment.description,
            treatment_category=request.requested_treatment.category.value,
            complexity=request.complexity,
            urgency=request.urgency,
            specialty=request.assigned_specialty,
            submitted_at=request.submitted_at,
            decided_at=decision.decided_at if decision else None,
            days_in_process=request.days_since_submission,
            is_high_cost=request.is_high_cost,
            was_escalated=decision.was_escalated if decision else False,
            requires_review=request.status
            in {AuthorizationStatus.PENDING_REVIEW, AuthorizationStatus.IN_REVIEW},
        )
