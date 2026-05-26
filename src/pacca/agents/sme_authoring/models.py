"""
Pydantic models for the SME Case Authoring Agent.

These models are the data interfaces shared across the PR-1 deterministic
core (validators, allocator, router, writer) and will also feed the PR-2
LLM agent's structured-output contract.

Design notes:
- ValidationReport / ValidationOutcome are the central pass/fail/notes
  primitive that every validator returns. Aggregation logic lives in
  validators.run_all_validators.
- CaseDraftRequest is the SME's free-form scenario input → goes to the LLM.
- CaseDraftResponse is the LLM's structured draft → goes to the validators.
- SessionState persists across CLI invocations (resume-mid-session).
"""

from __future__ import annotations

from enum import StrEnum
from typing import TYPE_CHECKING, Literal

from pydantic import BaseModel, ConfigDict, Field

if TYPE_CHECKING:
    from datetime import datetime


class ValidationOutcome(StrEnum):
    """Three-state outcome for any single validator."""

    PASS = "pass"
    FAIL = "fail"
    WARN = "warn"  # advisory; doesn't block, but surfaces to SME


class ValidatorName(StrEnum):
    """Stable identifier for each validator. Used in reports + telemetry."""

    PHI_SCAN = "phi_scan"
    GUIDELINE_CITATION = "guideline_citation"
    SCHEMA_COMPLETENESS = "schema_completeness"
    OUTCOME_BRANCH_CONSISTENCY = "outcome_branch_consistency"
    REASONING_SPECIFICITY = "reasoning_specificity"
    JUDGE_CRITERIA_SPECIFICITY = "judge_criteria_specificity"


class ValidationReport(BaseModel):
    """
    Single-validator result.

    A case is acceptable for write iff EVERY validator returned PASS (WARN
    is advisory). The agent surfaces FAIL reasons verbatim to the SME so
    they can revise the field and re-validate.
    """

    model_config = ConfigDict(frozen=True)

    validator: ValidatorName
    outcome: ValidationOutcome
    reason: str = Field(
        default="",
        description=(
            "Human-readable explanation. Required for FAIL/WARN; empty for PASS is acceptable."
        ),
    )
    field_path: str | None = Field(
        default=None,
        description=(
            "Dotted path into the case dict where the issue lives, "
            "e.g. 'clinical_notes' or 'reasoning_must_include[0]'."
        ),
    )

    @property
    def is_blocking(self) -> bool:
        """A blocking report fails the case write."""
        return self.outcome == ValidationOutcome.FAIL


class SMEScenario(BaseModel):
    """
    Plain-English clinical scenario from the SME.

    This is what the SME types after `pacca sme-author new`. The LLM
    consumes this and produces a CaseDraftResponse.
    """

    description: str = Field(
        min_length=20,
        description=(
            "1-3 sentences in plain English. Example: "
            "'65yo male with stage IV NSCLC, PD-L1 70%, no EGFR/ALK, "
            "requesting first-line pembrolizumab.'"
        ),
    )
    intended_specialty: str | None = Field(
        default=None,
        description=(
            "Optional hint to the agent about which specialty the case "
            "belongs to (oncology, cardiology, etc.). If omitted, the "
            "LLM infers from the description."
        ),
    )
    intended_outcome: (
        Literal[
            "AUTO_APPROVED",
            "IN_REVIEW",
            "DENIED",
            "PRE_FLIGHT_ESCALATE",
            "INFORMATION_NEEDED",
        ]
        | None
    ) = Field(
        default=None,
        description=(
            "Optional hint about expected outcome. If omitted, the LLM "
            "proposes one and the SME approves/edits."
        ),
    )
    failure_mode_label: str | None = Field(
        default=None,
        description=(
            "Optional named failure mode from CASE_AUTHORING_GUIDE.md § 15 "
            "taxonomy (e.g., 'Coverage', 'Hallucination zero-tolerance', "
            "'False pattern-matching (memory trap)')."
        ),
    )


class CaseDraftResponse(BaseModel):
    """
    LLM-produced draft of a complete GoldenCase, suitable for validation.

    Mirrors the `GoldenCase` dataclass in tests/clinical/golden_cases.py
    field-for-field. After validation passes, the case_writer module emits
    the corresponding Python source.
    """

    model_config = ConfigDict(frozen=False)  # SME may edit before write

    case_id: str = Field(description="GC-NNN; allocated by id_allocator, not LLM")
    title: str = Field(min_length=10, max_length=120)
    diagnosis_code: str = Field(description="ICD-10 code")
    diagnosis_description: str = Field(min_length=5)
    procedure_code: str = Field(description="CPT / HCPCS / J-code")
    procedure_description: str = Field(min_length=5)
    clinical_notes: str = Field(
        min_length=80,
        description="3-8 sentences of synthetic provider notes. PHI-free.",
    )
    guidelines_context: str = Field(
        min_length=80,
        description="2-5 sentences citing a real authoritative guideline body.",
    )
    expected_outcome: str = Field(
        description=(
            "Must be one of: AUTO_APPROVED, IN_REVIEW, DENIED, "
            "PRE_FLIGHT_ESCALATE, INFORMATION_NEEDED"
        ),
    )
    expected_branch: str = Field(
        description=("Must be one of: BRANCH_1_AUTO_APPROVE through BRANCH_7_PRIOR_DENIAL or NONE"),
    )
    reasoning_must_include: list[str] = Field(
        min_length=1,
        description="At least 1 phrase the agent's rationale MUST contain.",
    )
    reasoning_must_not_include: list[str] = Field(
        default_factory=list,
        description=(
            "Hallucination markers. Empty for routine coverage cases; "
            "non-empty for adversarial probes."
        ),
    )
    prior_denial_codes: list[str] = Field(default_factory=list)
    clinical_rationale: str = Field(
        min_length=40,
        description=("Human-expert justification, 2-5 sentences. Period-count >= 2."),
    )
    judge_scoring_criteria: str = Field(
        min_length=40,
        description=("What the LLM-as-judge should evaluate. Non-generic; specific to this case."),
    )


class CaseDraftRequest(BaseModel):
    """
    Input bundle to the LLM agent.

    Combines the SME's scenario + repo-state context the LLM needs:
    the next available case_id, the recommended file, and any priority-
    gap signal from gap_analyzer.
    """

    scenario: SMEScenario
    allocated_case_id: str = Field(description="Pre-allocated by id_allocator (e.g., 'GC-101')")
    recommended_file: str = Field(description="Suggested target file from file_router")
    priority_gap_hint: str | None = Field(
        default=None,
        description=(
            "If gap_analyzer recommended a specific gap to close, the "
            "hint is forwarded to bias the LLM toward that gap."
        ),
    )


class SessionState(BaseModel):
    """
    Persistent SME-authoring session state.

    Saved to ~/.pacca/sme_authoring_sessions/{session_id}.json after every
    step. Used by `pacca sme-author resume <session_id>`.
    """

    session_id: str
    created_at: datetime
    last_updated_at: datetime
    mode: Literal["sandbox", "production", "git_worktree"] = "sandbox"
    sme_attestation: str | None = Field(
        default=None,
        description=("SME's typed attestation. Required before any production write."),
    )
    scenario: SMEScenario | None = None
    draft: CaseDraftResponse | None = None
    last_validation_report: list[ValidationReport] = Field(default_factory=list)
    last_step: str = Field(
        default="created",
        description=(
            "Which workflow step the session is on. Used by resume to skip already-completed steps."
        ),
    )
