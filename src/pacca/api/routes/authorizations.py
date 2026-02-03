"""
Authorization API endpoints.

REST API for submitting and managing prior authorization requests.
"""

from datetime import date, datetime
from typing import Any

from fastapi import APIRouter, HTTPException, Query, status
from pydantic import BaseModel, Field

from pacca.agents.orchestrator import OrchestrationAgent, WorkflowResult
from pacca.api.routes.health import record_authorization_metrics
from pacca.config import get_logger
from pacca.models import (
    AuthorizationDecision,
    AuthorizationRequest,
    AuthorizationStatus,
    AuthorizationSummary,
    ClinicalSpecialty,
    ComplexityLevel,
    DecisionOutcome,
    Diagnosis,
    PatientDemographics,
    PayerInfo,
    ProviderInfo,
    Treatment,
    TreatmentCategory,
    UrgencyLevel,
)

logger = get_logger(__name__)
router = APIRouter()

# In-memory storage for MVP (would use database in production)
_authorizations: dict[str, AuthorizationRequest] = {}
_decisions: dict[str, AuthorizationDecision] = {}
_workflow_results: dict[str, WorkflowResult] = {}


# =============================================================================
# REQUEST MODELS
# =============================================================================


class PatientInput(BaseModel):
    """Patient information for authorization request."""

    id: str = Field(..., description="Patient identifier")
    date_of_birth: date = Field(..., description="Patient date of birth")
    gender: str = Field(..., description="Patient gender (M/F/O/U)")
    zip_code: str | None = Field(None, description="Patient ZIP code (first 3 digits)")


class DiagnosisInput(BaseModel):
    """Diagnosis information for authorization request."""

    code: str = Field(..., description="ICD-10 diagnosis code", examples=["C34.1"])
    description: str = Field(..., description="Diagnosis description")
    is_primary: bool = Field(True, description="Is this the primary diagnosis")
    onset_date: date | None = Field(None, description="Date of onset")


class TreatmentInput(BaseModel):
    """Treatment information for authorization request."""

    code: str = Field(..., description="Treatment code (CPT, HCPCS, NDC)")
    code_type: str = Field("HCPCS", description="Code type")
    description: str = Field(..., description="Treatment description")
    category: str = Field(..., description="Treatment category")
    quantity: int | None = Field(None, description="Quantity requested")
    estimated_cost: float | None = Field(None, description="Estimated cost in USD")


class ProviderInput(BaseModel):
    """Provider information for authorization request."""

    provider_id: str = Field(..., description="Provider NPI")
    provider_name: str = Field(..., description="Provider name")
    specialty: str | None = Field(None, description="Provider specialty")
    facility_name: str | None = Field(None, description="Facility name")


class PayerInput(BaseModel):
    """Payer information for authorization request."""

    payer_id: str = Field(..., description="Payer identifier")
    payer_name: str = Field(..., description="Payer name")
    member_id: str = Field(..., description="Member ID")
    plan_name: str | None = Field(None, description="Plan name")


class AuthorizationSubmission(BaseModel):
    """Request body for submitting a new authorization."""

    patient: PatientInput
    diagnosis: DiagnosisInput
    secondary_diagnoses: list[DiagnosisInput] = Field(default_factory=list)
    treatment: TreatmentInput
    provider: ProviderInput
    payer: PayerInput
    clinical_notes: str | None = Field(None, description="Supporting clinical notes")
    urgency: str = Field("routine", description="Request urgency level")


class HumanReviewInput(BaseModel):
    """Request body for submitting a human review decision."""

    decision: str = Field(..., description="Decision: approve, deny, approve_with_conditions")
    reviewer_id: str = Field(..., description="Reviewer identifier")
    reviewer_notes: str | None = Field(None, description="Reviewer notes")
    conditions: list[str] = Field(default_factory=list, description="Approval conditions")


# =============================================================================
# RESPONSE MODELS
# =============================================================================


class AuthorizationResponse(BaseModel):
    """Response for a single authorization."""

    request_id: str
    status: str
    submitted_at: datetime
    updated_at: datetime

    # Patient (minimal for privacy)
    patient_id: str
    patient_age: int

    # Clinical
    diagnosis_code: str
    diagnosis_description: str
    treatment_code: str
    treatment_description: str

    # Classification (if available)
    complexity: int | None = None
    specialty: str | None = None
    urgency: str

    # Decision (if available)
    decision: str | None = None
    confidence_score: float | None = None
    decision_summary: str | None = None
    conditions: list[str] = Field(default_factory=list)

    # Workflow status
    requires_human_review: bool = False
    escalation_reasons: list[str] = Field(default_factory=list)


class AuthorizationListResponse(BaseModel):
    """Response for listing authorizations."""

    items: list[AuthorizationResponse]
    total: int
    page: int
    page_size: int


class ExplanationResponse(BaseModel):
    """Response for decision explanation."""

    request_id: str
    decision: str
    confidence_score: float

    # Rationale
    summary: str
    detailed_reasoning: str
    key_evidence_points: list[str]
    evidence_gaps: list[str]
    clinical_risks: list[str]
    safety_concerns: list[str]

    # Guideline alignment
    guideline_alignment: str | None = None


# =============================================================================
# ENDPOINTS
# =============================================================================


@router.post(
    "/authorizations",
    response_model=AuthorizationResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Submit Authorization Request",
    description="Submit a new prior authorization request for processing.",
)
async def submit_authorization(
    submission: AuthorizationSubmission,
) -> AuthorizationResponse:
    """
    Submit a new prior authorization request.

    The request will be processed through the agent workflow:
    1. Evidence Aggregation
    2. Clinical Classification
    3. Decision Support
    4. [If needed] Human Review Queue
    """
    logger.info(
        "authorization_submitted",
        patient_id=submission.patient.id,
        diagnosis=submission.diagnosis.code,
        treatment=submission.treatment.code,
    )

    # Convert input to domain model
    try:
        treatment_category = TreatmentCategory(submission.treatment.category.lower())
    except ValueError:
        treatment_category = TreatmentCategory.MEDICATION

    try:
        urgency = UrgencyLevel(submission.urgency.lower())
    except ValueError:
        urgency = UrgencyLevel.ROUTINE

    request = AuthorizationRequest(
        patient=PatientDemographics(
            patient_id=submission.patient.id,
            date_of_birth=submission.patient.date_of_birth,
            gender=submission.patient.gender,
            zip_code=submission.patient.zip_code,
        ),
        primary_diagnosis=Diagnosis(
            code=submission.diagnosis.code,
            description=submission.diagnosis.description,
            is_primary=True,
            onset_date=submission.diagnosis.onset_date,
        ),
        secondary_diagnoses=[
            Diagnosis(
                code=d.code,
                description=d.description,
                is_primary=False,
                onset_date=d.onset_date,
            )
            for d in submission.secondary_diagnoses
        ],
        requested_treatment=Treatment(
            code=submission.treatment.code,
            code_type=submission.treatment.code_type,
            description=submission.treatment.description,
            category=treatment_category,
            quantity=submission.treatment.quantity,
            estimated_cost=submission.treatment.estimated_cost,
        ),
        requesting_provider=ProviderInfo(
            provider_id=submission.provider.provider_id,
            provider_name=submission.provider.provider_name,
            facility_name=submission.provider.facility_name,
        ),
        payer=PayerInfo(
            payer_id=submission.payer.payer_id,
            payer_name=submission.payer.payer_name,
            member_id=submission.payer.member_id,
            plan_name=submission.payer.plan_name,
        ),
        clinical_notes=submission.clinical_notes,
        urgency=urgency,
    )

    # Store the request
    _authorizations[request.request_id] = request

    # Process through agent workflow
    orchestrator = OrchestrationAgent()
    result = await orchestrator.process_authorization(request)

    # Store the result
    _workflow_results[request.request_id] = result
    if result.decision:
        _decisions[request.request_id] = result.decision

    # Record metrics
    record_authorization_metrics(
        processing_time_ms=result.total_duration_ms,
        was_autonomous=not result.requires_human_review,
    )

    # Build response
    return _build_authorization_response(request, result)


@router.get(
    "/authorizations/{request_id}",
    response_model=AuthorizationResponse,
    summary="Get Authorization Status",
    description="Get the current status and details of an authorization request.",
)
async def get_authorization(request_id: str) -> AuthorizationResponse:
    """Get authorization by ID."""
    if request_id not in _authorizations:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Authorization {request_id} not found",
        )

    request = _authorizations[request_id]
    result = _workflow_results.get(request_id)

    return _build_authorization_response(request, result)


@router.get(
    "/authorizations",
    response_model=AuthorizationListResponse,
    summary="List Authorizations",
    description="List authorization requests with optional filtering.",
)
async def list_authorizations(
    status_filter: str | None = Query(None, alias="status"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
) -> AuthorizationListResponse:
    """List authorizations with pagination."""
    items = list(_authorizations.values())

    # Apply status filter
    if status_filter:
        items = [r for r in items if r.status.value == status_filter]

    # Sort by submission time (newest first)
    items.sort(key=lambda r: r.submitted_at, reverse=True)

    # Paginate
    total = len(items)
    start = (page - 1) * page_size
    end = start + page_size
    page_items = items[start:end]

    # Build responses
    responses = []
    for request in page_items:
        result = _workflow_results.get(request.request_id)
        responses.append(_build_authorization_response(request, result))

    return AuthorizationListResponse(
        items=responses,
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get(
    "/authorizations/{request_id}/explain",
    response_model=ExplanationResponse,
    summary="Get Decision Explanation",
    description="Get detailed explanation of the authorization decision.",
)
async def get_explanation(request_id: str) -> ExplanationResponse:
    """Get decision explanation with chain-of-thought reasoning."""
    if request_id not in _authorizations:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Authorization {request_id} not found",
        )

    decision = _decisions.get(request_id)
    if not decision:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No decision found for authorization {request_id}",
        )

    if not decision.rationale:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No explanation available for authorization {request_id}",
        )

    return ExplanationResponse(
        request_id=request_id,
        decision=decision.outcome.value,
        confidence_score=decision.confidence_score,
        summary=decision.rationale.summary,
        detailed_reasoning=decision.rationale.detailed_reasoning,
        key_evidence_points=decision.rationale.key_evidence_points,
        evidence_gaps=decision.rationale.evidence_gaps,
        clinical_risks=decision.rationale.clinical_risks,
        safety_concerns=decision.rationale.safety_concerns,
    )


@router.post(
    "/authorizations/{request_id}/review",
    response_model=AuthorizationResponse,
    summary="Submit Human Review",
    description="Submit a human reviewer's decision for an escalated authorization.",
)
async def submit_review(
    request_id: str,
    review: HumanReviewInput,
) -> AuthorizationResponse:
    """Submit human review decision for an escalated case."""
    if request_id not in _authorizations:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Authorization {request_id} not found",
        )

    request = _authorizations[request_id]
    result = _workflow_results.get(request_id)

    if not result or not result.requires_human_review:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Authorization {request_id} does not require human review",
        )

    # Map decision string to enum
    decision_map = {
        "approve": DecisionOutcome.APPROVE,
        "deny": DecisionOutcome.DENY,
        "approve_with_conditions": DecisionOutcome.APPROVE_WITH_CONDITIONS,
    }

    outcome = decision_map.get(review.decision.lower())
    if not outcome:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid decision: {review.decision}",
        )

    # Process human review
    orchestrator = OrchestrationAgent()
    decision = await orchestrator.handle_human_review(
        request_id=request_id,
        reviewer_decision=outcome,
        reviewer_notes=review.reviewer_notes,
        reviewer_id=review.reviewer_id,
    )

    # Update stored data
    _decisions[request_id] = decision

    # Update workflow result
    result.decision = decision
    result.requires_human_review = False
    result.state = "completed"

    # Update request status
    status_map = {
        DecisionOutcome.APPROVE: AuthorizationStatus.APPROVED,
        DecisionOutcome.DENY: AuthorizationStatus.DENIED,
        DecisionOutcome.APPROVE_WITH_CONDITIONS: AuthorizationStatus.APPROVED_WITH_CONDITIONS,
    }
    request.update_status(status_map.get(outcome, AuthorizationStatus.APPROVED))

    logger.info(
        "human_review_completed",
        request_id=request_id,
        reviewer_id=review.reviewer_id,
        decision=outcome.value,
    )

    return _build_authorization_response(request, result)


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================


def _build_authorization_response(
    request: AuthorizationRequest,
    result: WorkflowResult | None,
) -> AuthorizationResponse:
    """Build API response from domain models."""
    decision = result.decision if result else None
    classification = result.classification if result else None

    return AuthorizationResponse(
        request_id=request.request_id,
        status=request.status.value,
        submitted_at=request.submitted_at,
        updated_at=request.updated_at,
        patient_id=request.patient.patient_id,
        patient_age=request.patient.age,
        diagnosis_code=request.primary_diagnosis.code,
        diagnosis_description=request.primary_diagnosis.description,
        treatment_code=request.requested_treatment.code,
        treatment_description=request.requested_treatment.description,
        complexity=classification.complexity.value if classification else None,
        specialty=classification.primary_specialty.value if classification else None,
        urgency=request.urgency.value,
        decision=decision.outcome.value if decision else None,
        confidence_score=decision.confidence_score if decision else None,
        decision_summary=decision.rationale.summary if decision and decision.rationale else None,
        conditions=decision.conditions if decision else [],
        requires_human_review=result.requires_human_review if result else False,
        escalation_reasons=result.escalation_reasons if result else [],
    )
