"""
SME Case Authoring Agent — PACCA developer tool for clinical SMEs.

This module lets a board-certified clinician (no Python knowledge required)
author new golden test cases for PACCA's clinical evaluation dataset via
the `pacca sme-author` CLI subcommand.

PR-1 (this commit): library foundation — deterministic core modules and
their unit tests. No LLM, no CLI, no agent yet. Establishes the validators,
ID allocator, file router, case writer, provenance writer, and coverage
updater that the LLM agent (PR-2) and CLI (PR-2) will compose.

See:
- docs/SME_CASE_AGENT_DESIGN.md (PR-4) for the architecture
- docs/CASE_AUTHORING_GUIDE.md for the rules the validators enforce
- /Users/davidreed/.claude/plans/mutable-tinkering-candle.md for the plan
"""

from pacca.agents.sme_authoring.id_allocator import (
    allocate_ids,
    find_max_existing_id,
    next_id,
    release_reservation,
)
from pacca.agents.sme_authoring.models import (
    CaseDraftRequest,
    CaseDraftResponse,
    SessionState,
    SMEScenario,
    ValidationOutcome,
    ValidationReport,
)
from pacca.agents.sme_authoring.validators import (
    ValidatorName,
    run_all_validators,
    validate_guideline_citation,
    validate_judge_criteria_specificity,
    validate_no_phi,
    validate_outcome_branch_consistency,
    validate_reasoning_specificity,
    validate_schema_completeness,
)

__all__ = [
    "CaseDraftRequest",
    "CaseDraftResponse",
    "SMEScenario",
    "SessionState",
    "ValidationOutcome",
    "ValidationReport",
    "ValidatorName",
    "allocate_ids",
    "find_max_existing_id",
    "next_id",
    "release_reservation",
    "run_all_validators",
    "validate_guideline_citation",
    "validate_judge_criteria_specificity",
    "validate_no_phi",
    "validate_outcome_branch_consistency",
    "validate_reasoning_specificity",
    "validate_schema_completeness",
]
