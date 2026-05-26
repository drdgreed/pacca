"""
API-layer Pydantic models for the SME Case Authoring Web UI.

These models are the wire format between the React frontend and the
FastAPI backend. They wrap the SME-authoring library's internal models
(at `src/pacca/agents/sme_authoring/models.py`) into request/response
envelopes suitable for HTTP + WebSocket transport.

DESIGN
======

- Backend internal models stay private to `pacca.agents.sme_authoring`.
- This module's models are the public API contract that the frontend
  consumes. When the internal models evolve, the wire format can stay
  stable via translation here.

- Every response includes a `kind` discriminator field to make
  TypeScript discriminated-union codegen easy in the frontend.

- WebSocket events carry their own typed envelope (`WSEvent`).
"""

from __future__ import annotations

from datetime import datetime  # noqa: TC003 — runtime-required by Pydantic
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

# Runtime-required by Pydantic (model_validate / model_dump_json):
from pacca.agents.sme_authoring.models import (  # noqa: TC001
    CaseDraftResponse,
    SessionState,
    SMEScenario,
    ValidationReport,
)

# =============================================================================
# Session — create / list / get / delete
# =============================================================================


class CreateSessionRequest(BaseModel):
    """POST /api/v1/sme-authoring/sessions request body."""

    scenario: SMEScenario
    mode: Literal["sandbox", "production"] = Field(
        default="sandbox",
        description=(
            "sandbox = drafted in sandbox/cases/ (no production write); "
            "production = commit to tests/clinical/ after attestation."
        ),
    )


class SessionResponse(BaseModel):
    """Response envelope for one session."""

    model_config = ConfigDict(frozen=False)

    kind: Literal["session"] = "session"
    session: SessionState


class SessionListResponse(BaseModel):
    """Response envelope for the session-list endpoint."""

    kind: Literal["session_list"] = "session_list"
    sessions: list[SessionState] = Field(default_factory=list)
    total: int


# =============================================================================
# Drafting — REST kick-off + WebSocket streaming
# =============================================================================


class DraftRequest(BaseModel):
    """POST /api/v1/sme-authoring/sessions/{id}/draft request body.

    Empty body — the session ID identifies the scenario + allocated_id.
    """


class DraftResponse(BaseModel):
    """
    Response from the REST `draft` endpoint.

    Returns the draft directly (buffered, no streaming). The frontend
    can ALSO subscribe to the WebSocket at `/draft-stream` for live
    typewriter-style progress; both surfaces return equivalent final
    drafts.
    """

    kind: Literal["draft"] = "draft"
    draft: CaseDraftResponse
    allocated_case_id: str
    recommended_file: str
    routing_reason: str


# =============================================================================
# Validation
# =============================================================================


class ValidateRequest(BaseModel):
    """
    POST /api/v1/sme-authoring/sessions/{id}/validate request body.

    Optional override: if provided, validates the given draft instead of
    the session's stored draft. Used when the SME has edited fields
    in the wizard and wants to re-validate before committing.
    """

    draft: CaseDraftResponse | None = None


class ValidateResponse(BaseModel):
    kind: Literal["validation"] = "validation"
    reports: list[ValidationReport]
    blocking_count: int
    warning_count: int
    pass_count: int


# =============================================================================
# Commit
# =============================================================================


class CommitRequest(BaseModel):
    """POST /api/v1/sme-authoring/sessions/{id}/commit request body."""

    sme_attestation: str = Field(
        min_length=10,
        description=(
            "SME's attestation per CASE_AUTHORING_GUIDE.md § 11. "
            "Either the generic phrase or a credentialed statement."
        ),
    )
    draft: CaseDraftResponse | None = Field(
        default=None,
        description=(
            "Override draft if SME edited fields in the wizard. If None, "
            "uses the session's stored draft."
        ),
    )
    confirm_production_write: bool = Field(
        default=False,
        description=(
            "Required True for mode=production sessions. Acts as a "
            "safety interlock against accidental writes."
        ),
    )


class CommitResponse(BaseModel):
    """Response after a successful (or failed) commit attempt."""

    kind: Literal["commit"] = "commit"
    written: bool
    target_file: str
    case_id: str
    pr_title: str
    pr_body: str
    integrity_test_passed: bool
    integrity_test_summary: str = ""


# =============================================================================
# Status / discovery — batches, gaps, dataset state
# =============================================================================


class ListCountResponse(BaseModel):
    """One row from the per-file count table."""

    list_name: str
    file: str
    count: int
    id_range: str


class StatusResponse(BaseModel):
    """Dataset-state snapshot for the dashboard."""

    kind: Literal["status"] = "status"
    total_cases: int
    per_list_counts: list[ListCountResponse]
    milestone_gaps: list[GapItem]
    coverage_parsed_ok: bool
    coverage_parse_error: str = ""


class BatchCaseItem(BaseModel):
    case_id: str
    description: str


class BatchItem(BaseModel):
    """One batch from DATASET_GROWTH_ROADMAP.md."""

    batch_id: str
    name: str
    case_count: int
    id_range: str
    target_file: str
    is_new_file: bool
    cases: list[BatchCaseItem] = Field(default_factory=list)


class BatchListResponse(BaseModel):
    kind: Literal["batch_list"] = "batch_list"
    batches: list[BatchItem]
    total: int


class BatchResponse(BaseModel):
    kind: Literal["batch"] = "batch"
    batch: BatchItem


class GapItem(BaseModel):
    """One prioritized coverage gap."""

    category: str
    label: str
    current_count: int
    target_count: int
    cases_needed: int
    priority: int
    description: str


class GapListResponse(BaseModel):
    kind: Literal["gap_list"] = "gap_list"
    gaps: list[GapItem]
    total: int


# =============================================================================
# WebSocket event envelope
# =============================================================================


class WSDeltaEvent(BaseModel):
    """Token-by-token delta from the LLM (typewriter-style streaming)."""

    type: Literal["delta"] = "delta"
    field: str  # Which field is currently being drafted (e.g., "clinical_notes")
    content: str  # Incremental text


class WSDoneEvent(BaseModel):
    """Final event when the LLM draft completes successfully."""

    type: Literal["done"] = "done"
    draft: CaseDraftResponse
    allocated_case_id: str
    recommended_file: str


class WSErrorEvent(BaseModel):
    """Sent on error; connection closes after this event."""

    type: Literal["error"] = "error"
    message: str
    recoverable: bool = False


class WSHeartbeatEvent(BaseModel):
    """Periodic heartbeat to keep the connection alive."""

    type: Literal["heartbeat"] = "heartbeat"
    timestamp: datetime


# Discriminated union for the frontend; TypeScript can codegen this.
WSEvent = WSDeltaEvent | WSDoneEvent | WSErrorEvent | WSHeartbeatEvent


# =============================================================================
# Generic error envelope (matches existing FastAPI HTTPException shape)
# =============================================================================


class ErrorResponse(BaseModel):
    """Returned on 4xx / 5xx errors (matches FastAPI HTTPException default)."""

    detail: str


# Resolve forward references
StatusResponse.model_rebuild()
