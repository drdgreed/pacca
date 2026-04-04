"""
Admin routes for PACCA operator controls.

This module provides two capabilities:
  1. Configuration API — read and update operational settings at runtime
     without restarting the server (GET/PATCH /api/v1/admin/config)
  2. Policy evolution — the Level 5 autonomous guideline rewriting
     (POST /api/v1/admin/optimize_policies)

Teaching note — why a Config API matters for production systems:

  In a deployed system, you want to change a confidence threshold or
  flip a feature flag WITHOUT redeploying the server. A Config API
  makes settings visible and mutable to operators while keeping them
  version-controlled as code defaults.

  This is particularly important for clinical AI systems where:
    - Regulators may require you to LOWER the auto-approve threshold
      temporarily during an audit
    - A surge in low-quality submissions may require RAISING escalation
      sensitivity
    - You may need to disable autonomous decisions entirely with one call
      during a system incident

  The endpoints here are protected by JWT authentication (via the
  `verify_token` dependency injected in main.py). In production, you
  would add a separate ADMIN role check on top of that.

Teaching note — runtime config vs. environment variables:

  Settings are loaded from environment variables at startup via
  pydantic-settings. The Config API reads those loaded values and
  allows in-memory overrides for the current process lifetime.

  This means: a PATCH to /config takes effect immediately for all
  subsequent requests, but restarting the server resets to the
  environment variable values. For permanent changes, update the
  environment variable AND call the API.

  This is the standard pattern for production configuration management:
  environment variables are the ground truth; the API provides a
  no-restart override for operational urgency.
"""

import logging
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from ...agents.evolution import (
    EvolutionAgent,
    approve_proposal,
    get_all_proposals,
    get_change_log,
    get_pending_proposals,
    get_proposal_by_id,
    reject_proposal,
)
from ...integrations.vector_store import GuidelineRetriever
from ...config.settings import get_settings

logger = logging.getLogger(__name__)

router = APIRouter()
evolver = EvolutionAgent()
rag = GuidelineRetriever()

# In-memory override store.
# Keys match settings field names. Set via PATCH /config, read by GET /config.
# Cleared on server restart (by design — restart = reload from env vars).
_config_overrides: dict[str, Any] = {}


# =============================================================================
# Pydantic models for the Config API
# =============================================================================

class ConfigResponse(BaseModel):
    """
    Current operational configuration values.

    This is what GET /config returns — a snapshot of every tunable
    parameter with its current value, source (env var or runtime override),
    and a description of what it controls.

    Fields are grouped by functional area to make the Swagger UI readable.
    """

    # ── Clinical decision thresholds ─────────────────────────────────────────
    auto_approve_confidence_threshold: float = Field(
        description=(
            "Confidence score >= this value triggers automatic approval "
            "(no human review). Range: 0.5–1.0. Default: 0.95. "
            "Higher = safer (more cases escalate), lower = faster (more auto-approved)."
        )
    )
    escalation_confidence_threshold: float = Field(
        description=(
            "Confidence score between this and auto_approve threshold "
            "triggers Medical Director Agent escalation. Range: 0.3–1.0. "
            "Default: 0.90."
        )
    )
    high_cost_threshold: int = Field(
        description=(
            "Estimated treatment cost ($) above this value always triggers "
            "Medical Director review regardless of AI confidence. "
            "Default: 100,000."
        )
    )
    complexity_auto_approve_max: int = Field(
        description=(
            "Cases with complexity <= this value are eligible for autonomous "
            "approval (subject to confidence threshold). Range: 1–5. Default: 2."
        )
    )

    # ── Retry configuration ───────────────────────────────────────────────────
    llm_retry_max_attempts: int = Field(
        description=(
            "Maximum total LLM API call attempts (including first attempt). "
            "Retries only on transient errors: 429, 5xx, connection errors. "
            "Default: 3."
        )
    )
    llm_retry_wait_min_seconds: float = Field(
        description="Minimum wait seconds before first retry (exponential base). Default: 1.0."
    )
    llm_retry_wait_max_seconds: float = Field(
        description="Maximum wait seconds between retries (exponential cap). Default: 30.0."
    )

    # ── Observability ─────────────────────────────────────────────────────────
    otel_enabled: bool = Field(
        description=(
            "Enable OpenTelemetry span instrumentation. "
            "When true, every agent call produces a trace in Langfuse. "
            "Disable if the OTel exporter is causing latency issues."
        )
    )
    otel_service_name: str = Field(
        description="Service name reported in all OTel traces. Shown in Langfuse."
    )

    # ── Feature flags ─────────────────────────────────────────────────────────
    enable_autonomous_decisions: bool = Field(
        description=(
            "Master switch for autonomous AI approvals. "
            "When False, ALL cases route to human review regardless of confidence. "
            "Use during audits, incidents, or regulatory reviews."
        )
    )
    enable_rag: bool = Field(
        description=(
            "Enable RAG-based guideline retrieval from ChromaDB. "
            "When False, agents reason without guideline context (lower accuracy)."
        )
    )
    demo_mode: bool = Field(
        description="Load sample clinical cases and demo accounts at startup."
    )

    # ── Metadata ──────────────────────────────────────────────────────────────
    overrides_active: list[str] = Field(
        description=(
            "List of settings currently overridden at runtime via PATCH /config. "
            "These values differ from the environment variable defaults and will "
            "reset to defaults on server restart."
        )
    )


class ConfigPatchRequest(BaseModel):
    """
    Request body for PATCH /config — partial update of operational settings.

    All fields are optional. Only fields you include will be updated.
    Fields not included retain their current values.

    Example — temporarily lower auto-approve threshold during an audit:
        PATCH /api/v1/admin/config
        {"auto_approve_confidence_threshold": 0.99}

    Example — disable autonomous decisions immediately:
        PATCH /api/v1/admin/config
        {"enable_autonomous_decisions": false}

    Example — increase retries during a period of API instability:
        PATCH /api/v1/admin/config
        {"llm_retry_max_attempts": 5, "llm_retry_wait_max_seconds": 60.0}
    """
    auto_approve_confidence_threshold: float | None = Field(
        default=None, ge=0.5, le=1.0
    )
    escalation_confidence_threshold: float | None = Field(
        default=None, ge=0.3, le=1.0
    )
    high_cost_threshold: int | None = Field(
        default=None, ge=0
    )
    complexity_auto_approve_max: int | None = Field(
        default=None, ge=1, le=5
    )
    llm_retry_max_attempts: int | None = Field(
        default=None, ge=1, le=10
    )
    llm_retry_wait_min_seconds: float | None = Field(
        default=None, ge=0.1, le=10.0
    )
    llm_retry_wait_max_seconds: float | None = Field(
        default=None, ge=1.0, le=120.0
    )
    otel_enabled: bool | None = None
    enable_autonomous_decisions: bool | None = None
    enable_rag: bool | None = None
    demo_mode: bool | None = None


class ConfigResetResponse(BaseModel):
    """Response confirming all runtime overrides were cleared."""
    message: str
    cleared_overrides: list[str]


# =============================================================================
# Helper: resolve effective value (override takes precedence over env var)
# =============================================================================

def _effective(field_name: str, env_value: Any) -> Any:
    """
    Return the runtime override if set, otherwise the env-var-loaded value.

    This is how the Config API achieves 'no-restart updates': overrides
    stored in _config_overrides shadow the pydantic-settings values.
    """
    return _config_overrides.get(field_name, env_value)


# =============================================================================
# Config API endpoints
# =============================================================================

@router.get(
    "/config",
    response_model=ConfigResponse,
    summary="Read current operational configuration",
    description=(
        "Returns all tunable operational parameters with their current effective "
        "values. Values may differ from environment variables if runtime overrides "
        "have been applied via PATCH /config."
    ),
)
async def get_config() -> ConfigResponse:
    """
    Read the current effective configuration.

    Returns every tunable parameter and its current value. The
    `overrides_active` field in the response lists which settings
    have been changed at runtime (vs. loaded from environment variables).
    """
    s = get_settings()

    return ConfigResponse(
        auto_approve_confidence_threshold=_effective(
            "auto_approve_confidence_threshold",
            s.auto_approve_confidence_threshold,
        ),
        escalation_confidence_threshold=_effective(
            "escalation_confidence_threshold",
            s.escalation_confidence_threshold,
        ),
        high_cost_threshold=_effective(
            "high_cost_threshold",
            s.high_cost_threshold,
        ),
        complexity_auto_approve_max=_effective(
            "complexity_auto_approve_max",
            s.complexity_auto_approve_max,
        ),
        llm_retry_max_attempts=_effective(
            "llm_retry_max_attempts",
            s.llm_retry_max_attempts,
        ),
        llm_retry_wait_min_seconds=_effective(
            "llm_retry_wait_min_seconds",
            s.llm_retry_wait_min_seconds,
        ),
        llm_retry_wait_max_seconds=_effective(
            "llm_retry_wait_max_seconds",
            s.llm_retry_wait_max_seconds,
        ),
        otel_enabled=_effective("otel_enabled", s.otel_enabled),
        otel_service_name=_effective("otel_service_name", s.otel_service_name),
        enable_autonomous_decisions=_effective(
            "enable_autonomous_decisions",
            s.enable_autonomous_decisions,
        ),
        enable_rag=_effective("enable_rag", s.enable_rag),
        demo_mode=_effective("demo_mode", s.demo_mode),
        overrides_active=list(_config_overrides.keys()),
    )


@router.patch(
    "/config",
    response_model=ConfigResponse,
    summary="Update operational configuration at runtime",
    description=(
        "Partially update operational settings without restarting the server. "
        "Only fields included in the request body are updated. "
        "Changes take effect immediately for all subsequent requests. "
        "Changes are reset to environment variable defaults on server restart. "
        "For permanent changes, update both the environment variable AND call this endpoint."
    ),
)
async def patch_config(updates: ConfigPatchRequest) -> ConfigResponse:
    """
    Apply runtime configuration overrides.

    Only non-None fields in the request are applied. The response returns
    the complete configuration after applying the updates, so callers
    can confirm exactly what changed.

    Validation rules enforced:
      - auto_approve threshold must be > escalation threshold
        (otherwise the escalation band collapses to nothing)
      - Cannot set retry_min > retry_max
    """
    global _config_overrides
    s = get_settings()

    # Apply updates to the override store
    for field_name, value in updates.model_dump(exclude_none=True).items():
        _config_overrides[field_name] = value
        logger.info(
            "config_override_applied",
            field=field_name,
            new_value=value,
        )

    # Validate that threshold relationships remain consistent
    effective_auto = _effective(
        "auto_approve_confidence_threshold",
        s.auto_approve_confidence_threshold,
    )
    effective_esc = _effective(
        "escalation_confidence_threshold",
        s.escalation_confidence_threshold,
    )
    if effective_auto <= effective_esc:
        # Roll back the invalid update
        for field_name in updates.model_dump(exclude_none=True):
            _config_overrides.pop(field_name, None)
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=(
                f"auto_approve_confidence_threshold ({effective_auto}) must be "
                f"greater than escalation_confidence_threshold ({effective_esc}). "
                f"The escalation band (values between the two thresholds that trigger "
                f"Medical Director review) would collapse to nothing."
            ),
        )

    effective_min = _effective("llm_retry_wait_min_seconds", s.llm_retry_wait_min_seconds)
    effective_max = _effective("llm_retry_wait_max_seconds", s.llm_retry_wait_max_seconds)
    if effective_min > effective_max:
        for field_name in updates.model_dump(exclude_none=True):
            _config_overrides.pop(field_name, None)
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=(
                f"llm_retry_wait_min_seconds ({effective_min}) cannot exceed "
                f"llm_retry_wait_max_seconds ({effective_max})."
            ),
        )

    # Return the new effective configuration
    return await get_config()


@router.delete(
    "/config/overrides",
    response_model=ConfigResetResponse,
    summary="Reset all runtime configuration overrides",
    description=(
        "Clears all runtime overrides applied via PATCH /config. "
        "All settings revert to their environment variable defaults immediately. "
        "Equivalent to a soft restart for configuration purposes."
    ),
)
async def reset_config_overrides() -> ConfigResetResponse:
    """
    Clear all runtime configuration overrides.

    After this call, GET /config will return only environment variable defaults.
    No server restart required.
    """
    global _config_overrides
    cleared = list(_config_overrides.keys())
    _config_overrides.clear()

    logger.info("config_overrides_reset", cleared_count=len(cleared))

    return ConfigResetResponse(
        message=(
            f"Cleared {len(cleared)} runtime override(s). "
            "All settings now reflect environment variable defaults."
        ),
        cleared_overrides=cleared,
    )


# =============================================================================
# System metrics endpoint
# =============================================================================

class MetricsResponse(BaseModel):
    """Operational metrics snapshot."""
    config_overrides_active: int = Field(
        description="Number of settings currently overridden at runtime."
    )
    effective_auto_approve_threshold: float = Field(
        description="Current effective auto-approve confidence threshold."
    )
    effective_escalation_threshold: float = Field(
        description="Current effective Medical Director escalation threshold."
    )
    autonomous_decisions_enabled: bool = Field(
        description="Whether autonomous AI approvals are currently active."
    )
    rag_enabled: bool = Field(
        description="Whether guideline RAG retrieval is currently active."
    )
    otel_enabled: bool = Field(
        description="Whether OpenTelemetry span export is active."
    )
    langfuse_note: str = Field(
        description="Where to view traces for this service."
    )


@router.get(
    "/metrics",
    response_model=MetricsResponse,
    summary="Operational metrics and system status",
)
async def get_metrics() -> MetricsResponse:
    """
    Return a snapshot of key operational metrics and current settings.

    This endpoint is intentionally lightweight — it reads from the
    in-memory config store and requires no database queries.
    Suitable for health dashboards and status pages.
    """
    s = get_settings()
    return MetricsResponse(
        config_overrides_active=len(_config_overrides),
        effective_auto_approve_threshold=_effective(
            "auto_approve_confidence_threshold",
            s.auto_approve_confidence_threshold,
        ),
        effective_escalation_threshold=_effective(
            "escalation_confidence_threshold",
            s.escalation_confidence_threshold,
        ),
        autonomous_decisions_enabled=_effective(
            "enable_autonomous_decisions",
            s.enable_autonomous_decisions,
        ),
        rag_enabled=_effective("enable_rag", s.enable_rag),
        otel_enabled=_effective("otel_enabled", s.otel_enabled),
        langfuse_note=(
            "Traces available at http://localhost:3001 — "
            "login: admin@pacca.local / pacca_admin_dev"
        ),
    )


# =============================================================================
# Policy Evolution Governance API (Level 5)
# =============================================================================

class ProposalSummary(BaseModel):
    """Summary of a policy amendment proposal for list views."""
    proposal_id: str
    guideline_id: str
    status: str
    confidence: float
    reasoning_summary: str
    override_count: int
    submitted_at: float
    reviewed_by: Optional[str] = None


class ApprovalRequest(BaseModel):
    """Request body for approving or rejecting a proposal."""
    reviewer_id: str = Field(
        description="Username or employee ID of the Medical Director approving this amendment"
    )
    review_notes: Optional[str] = Field(
        default=None,
        description="Notes explaining the approval/rejection decision (recommended)",
    )


class ChangeLogEntry(BaseModel):
    """A single entry in the policy change log."""
    change_id: str
    proposal_id: str
    guideline_id: str
    approved_by: str
    deployed_at: float
    rationale_summary: str


@router.post(
    "/optimize_policies",
    summary="Level 5: Submit policy amendment proposal",
    description=(
        "Runs the PolicyEvolutionAgent against override patterns and stores the "
        "resulting proposal as PENDING. The proposal requires human Medical Director "
        "approval via POST /admin/proposals/{id}/approve before any guideline changes "
        "take effect. No guidelines are modified by this endpoint."
    ),
)
async def run_policy_optimization():
    """
    Trigger the Level 5 policy evolution pipeline.

    Produces a governance-tracked PROPOSAL — does not deploy anything.
    The proposal is stored with status='pending' and requires human approval.
    """
    spine_overrides = [
        "Override: Approved MRI for 2 weeks pain due to severe motor weakness."
    ] * 10

    current_rule = "Indicated only after 6 weeks of conservative therapy fails."

    record = await evolver.run(
        original_guideline=current_rule,
        overrides=spine_overrides,
        guideline_id="NCCN-SPINE-LUMBAR-MRI",
    )

    logger.info(
        "policy_proposal_created",
        proposal_id=record.proposal_id,
        confidence=record.proposal.confidence,
    )

    return {
        "status": "proposal_pending",
        "proposal_id": record.proposal_id,
        "confidence": record.proposal.confidence,
        "message": (
            f"Proposal {record.proposal_id} created and stored as PENDING. "
            f"Review at GET /api/v1/admin/proposals/{record.proposal_id} and "
            f"approve via POST /api/v1/admin/proposals/{record.proposal_id}/approve."
        ),
        "proposed_text_preview": record.proposal.proposed_text[:300],
        "reviewer_checklist": record.proposal.reviewer_checklist,
    }


@router.get(
    "/proposals",
    summary="List all policy amendment proposals",
    description="Returns all proposals: pending, approved, and rejected.",
)
async def list_proposals(pending_only: bool = False):
    """List policy amendment proposals."""
    proposals = get_pending_proposals() if pending_only else get_all_proposals()

    return {
        "total": len(proposals),
        "pending": sum(1 for p in proposals if p.status == "pending"),
        "approved": sum(1 for p in proposals if p.status == "approved"),
        "rejected": sum(1 for p in proposals if p.status == "rejected"),
        "proposals": [
            {
                "proposal_id": p.proposal_id,
                "guideline_id": p.proposal.original_guideline_id,
                "status": p.status,
                "confidence": p.proposal.confidence,
                "reasoning_summary": p.proposal.reasoning[:200],
                "submitted_at": p.submitted_at,
                "reviewed_by": p.reviewed_by,
            }
            for p in proposals
        ],
    }


@router.get(
    "/proposals/{proposal_id}",
    summary="Get full proposal detail",
    description="Returns the full proposal including proposed text, reasoning, and reviewer checklist.",
)
async def get_proposal(proposal_id: str):
    """Get full detail for a specific proposal."""
    record = get_proposal_by_id(proposal_id)
    if not record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Proposal {proposal_id} not found.",
        )
    return {
        "proposal_id": record.proposal_id,
        "status": record.status,
        "submitted_at": record.submitted_at,
        "reviewed_by": record.reviewed_by,
        "reviewed_at": record.reviewed_at,
        "review_notes": record.review_notes,
        "proposal": {
            "guideline_id": record.proposal.original_guideline_id,
            "proposed_text": record.proposal.proposed_text,
            "reasoning": record.proposal.reasoning,
            "override_pattern": record.proposal.override_pattern,
            "confidence": record.proposal.confidence,
            "scope_boundaries": record.proposal.scope_boundaries,
            "reviewer_checklist": record.proposal.reviewer_checklist,
        },
    }


@router.post(
    "/proposals/{proposal_id}/approve",
    summary="Approve and deploy a policy amendment",
    description=(
        "Approves the proposal and deploys the amended guideline to ChromaDB. "
        "This is the human approval gate — no guideline changes occur without this call. "
        "The deployment is permanently recorded in the policy change log."
    ),
)
async def approve_policy_proposal(
    proposal_id: str,
    request: ApprovalRequest,
):
    """
    Approve a pending proposal and deploy the amendment.

    This endpoint:
      1. Records the approval in the proposal store
      2. Deploys the amended guideline to ChromaDB
      3. Creates an immutable entry in the policy change log
    """
    record = get_proposal_by_id(proposal_id)
    if not record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Proposal {proposal_id} not found.",
        )
    if record.status != "pending":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Proposal {proposal_id} is already {record.status}. Only pending proposals can be approved.",
        )

    # Record the approval and get the change log entry
    change_entry = approve_proposal(
        proposal_id=proposal_id,
        approved_by=request.reviewer_id,
        review_notes=request.review_notes,
        original_guideline_text=(
            f"Original guideline: {record.proposal.original_guideline_id}"
        ),
    )

    if not change_entry:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to record approval.",
        )

    # Deploy to ChromaDB
    rag.add_guideline(
        guideline_text=record.proposal.proposed_text,
        source_id=record.proposal.original_guideline_id,
        metadata={
            "source": "AI_EVOLUTION_APPROVED",
            "change_id": change_entry.change_id,
            "approved_by": request.reviewer_id,
            "proposal_id": proposal_id,
        },
    )

    logger.info(
        "policy_amendment_deployed",
        proposal_id=proposal_id,
        change_id=change_entry.change_id,
        guideline_id=record.proposal.original_guideline_id,
        approved_by=request.reviewer_id,
    )

    return {
        "status": "deployed",
        "change_id": change_entry.change_id,
        "proposal_id": proposal_id,
        "guideline_id": record.proposal.original_guideline_id,
        "approved_by": request.reviewer_id,
        "message": (
            f"Amendment deployed to ChromaDB. Change recorded as {change_entry.change_id}. "
            f"Full change log available at GET /api/v1/admin/change-log."
        ),
    }


@router.post(
    "/proposals/{proposal_id}/reject",
    summary="Reject a policy amendment proposal",
    description="Rejects the proposal without deploying anything. The proposal is permanently recorded as rejected.",
)
async def reject_policy_proposal(
    proposal_id: str,
    request: ApprovalRequest,
):
    """Reject a pending proposal without deploying it."""
    record = get_proposal_by_id(proposal_id)
    if not record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Proposal {proposal_id} not found.",
        )
    if record.status != "pending":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Proposal {proposal_id} is already {record.status}.",
        )

    success = reject_proposal(
        proposal_id=proposal_id,
        rejected_by=request.reviewer_id,
        review_notes=request.review_notes,
    )

    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to record rejection.",
        )

    logger.info(
        "policy_proposal_rejected",
        proposal_id=proposal_id,
        rejected_by=request.reviewer_id,
    )

    return {
        "status": "rejected",
        "proposal_id": proposal_id,
        "rejected_by": request.reviewer_id,
        "message": "Proposal rejected. No guidelines were modified.",
    }


@router.get(
    "/change-log",
    summary="Policy change audit log",
    description=(
        "Returns the complete immutable log of all deployed policy amendments. "
        "This is the regulatory audit trail for AI-driven guideline changes. "
        "Entries are append-only — no amendments are ever deleted from this log."
    ),
)
async def get_policy_change_log():
    """Return the complete policy change log."""
    log = get_change_log()
    return {
        "total_changes": len(log),
        "changes": [
            {
                "change_id": e.change_id,
                "proposal_id": e.proposal_id,
                "guideline_id": e.guideline_id,
                "approved_by": e.approved_by,
                "deployed_at": e.deployed_at,
                "rationale_summary": e.rationale_summary,
            }
            for e in log
        ],
    }
