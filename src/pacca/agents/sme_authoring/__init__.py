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

from pacca.agents.sme_authoring.case_writer import (
    CaseAlreadyExists,
    CaseWriterError,
    FileSyntaxError,
    append_case_to_file,
    create_new_case_file,
    format_case_as_python,
)
from pacca.agents.sme_authoring.coverage_updater import (
    CoverageBump,
    CoverageUpdaterError,
    bump_coverage_for_case,
)
from pacca.agents.sme_authoring.file_router import (
    FILE_TO_LIST_NAME,
    SPECIALTY_TO_FILE,
    RoutingDecision,
    route_case,
)
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
    ValidatorName,
)
from pacca.agents.sme_authoring.provenance_writer import (
    ProvenanceRow,
    ProvenanceWriterError,
    append_provenance_row,
    case_id_already_in_provenance,
)
from pacca.agents.sme_authoring.validators import (
    RECOGNIZED_GUIDELINE_BODIES,
    run_all_validators,
    validate_guideline_citation,
    validate_judge_criteria_specificity,
    validate_no_phi,
    validate_outcome_branch_consistency,
    validate_reasoning_specificity,
    validate_schema_completeness,
)

__all__ = [
    # File router
    "FILE_TO_LIST_NAME",
    # Validators
    "RECOGNIZED_GUIDELINE_BODIES",
    "SPECIALTY_TO_FILE",
    # Case writer
    "CaseAlreadyExists",
    # Models
    "CaseDraftRequest",
    "CaseDraftResponse",
    "CaseWriterError",
    # Coverage updater
    "CoverageBump",
    "CoverageUpdaterError",
    "FileSyntaxError",
    # Provenance writer
    "ProvenanceRow",
    "ProvenanceWriterError",
    "RoutingDecision",
    "SMEScenario",
    "SessionState",
    "ValidationOutcome",
    "ValidationReport",
    "ValidatorName",
    # ID allocator
    "allocate_ids",
    "append_case_to_file",
    "append_provenance_row",
    "bump_coverage_for_case",
    "case_id_already_in_provenance",
    "create_new_case_file",
    "find_max_existing_id",
    "format_case_as_python",
    "next_id",
    "release_reservation",
    "route_case",
    "run_all_validators",
    "validate_guideline_citation",
    "validate_judge_criteria_specificity",
    "validate_no_phi",
    "validate_outcome_branch_consistency",
    "validate_reasoning_specificity",
    "validate_schema_completeness",
]
