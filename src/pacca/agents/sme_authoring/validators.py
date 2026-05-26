"""
Deterministic validators for SME-drafted clinical cases.

Each validator returns a ValidationReport with PASS / FAIL / WARN. The
agent surfaces failures verbatim to the SME so they can revise the field
and re-validate.

These validators are the operational enforcement of docs/CASE_AUTHORING_GUIDE.md
rules. They run after the LLM drafts a case and BEFORE any file write. If
any FAIL fires, the write is blocked.

Design:
- All validators are pure functions of CaseDraftResponse + optional context.
- No I/O (file reads), no LLM calls, no network. Pure CPU.
- Each validator is independently testable + reasoned about.
- The `run_all_validators` convenience function runs all six and returns
  the aggregated list.

References:
- docs/CASE_AUTHORING_GUIDE.md § 4 (PHI rule)
- docs/CASE_AUTHORING_GUIDE.md § 5 (guideline-citation rule)
- docs/CASE_AUTHORING_GUIDE.md § 6 (must_not_include semantics)
- docs/CASE_AUTHORING_GUIDE.md § 7 (outcome-branch decision tree)
"""

from __future__ import annotations

import re

from pacca.agents.sme_authoring.models import (
    CaseDraftResponse,
    ValidationOutcome,
    ValidationReport,
    ValidatorName,
)

# Explicit re-exports so __init__.py can lift these via wildcard-safe imports.
__all__ = [
    "RECOGNIZED_GUIDELINE_BODIES",
    "ValidationOutcome",
    "ValidationReport",
    "ValidatorName",
    "run_all_validators",
    "scan_for_phi",
    "validate_guideline_citation",
    "validate_judge_criteria_specificity",
    "validate_no_phi",
    "validate_outcome_branch_consistency",
    "validate_reasoning_specificity",
    "validate_schema_completeness",
]

# =============================================================================
# Recognized guideline bodies — single source of truth for the citation check.
# Mirrors docs/CASE_AUTHORING_GUIDE.md § 5 "Recognized guideline bodies" table.
# When that table is updated, this set is updated in the same PR.
# =============================================================================

RECOGNIZED_GUIDELINE_BODIES: frozenset[str] = frozenset(
    {
        # Oncology
        "NCCN",
        "ASCO",
        "ESMO",
        "CMS NCD",
        "CMS Medicare NCD",
        # Rheumatology
        "ACR",
        "EULAR",
        # Gastroenterology
        "ACG",
        "AGA",
        "ECCO",
        "ESPGHAN",
        "NASPGHAN",
        # Dermatology
        "AAD",
        "AAD-NPF",
        "EADV",
        # Pulmonology
        "ATS",
        "ERS",
        "GINA",
        "GOLD",
        "AASM",
        # Cardiology
        "ACC/AHA",
        "ACC",
        "AHA",
        "ESC",
        "HRS",
        "STS",
        "SCAI",
        # Endocrinology
        "ADA",
        "AACE",
        "ATA",
        "Endo Society",
        "Endocrine Society",
        # Neurology
        "AAN",
        "AHA/ASA",
        "MS Society",
        "AHS",
        "ILAE",
        # Surgery / Orthopedics
        "AAOS",
        "NASS",
        "ACS",
        "ASTRO",
        # Imaging
        "ACR Appropriateness",
        "AUC",
        "USPSTF",
        # Pediatrics
        "AAP",
        "AACAP",
        # Reproductive / OB
        "ACOG",
        "SMFM",
        "ASRM",
        # Hematology / transplant / behavioral
        "NHLBI",
        "ASH",
        "ASTCT",
        "ISHLT",
        "KDIGO",
        "APA",
        "WFSBP",
        "AAO",
        "FDA",  # FDA-approved label + REMS programs
        "Choosing Wisely",
        "IMDRF",
        "Renal Physicians Association",
        "SIOG",
    }
)


# =============================================================================
# Valid outcome x branch combinations — from CASE_AUTHORING_GUIDE.md § 7.
# =============================================================================

_VALID_OUTCOME_BRANCH: dict[str, frozenset[str]] = {
    # AUTO_APPROVED only fires through branch_1 (clean approve path)
    "AUTO_APPROVED": frozenset({"BRANCH_1_AUTO_APPROVE"}),
    # IN_REVIEW can fire through branch_2 (medical director) or branch_3 (low confidence)
    "IN_REVIEW": frozenset({"BRANCH_2_MEDICAL_DIRECTOR", "BRANCH_3_LOW_CONFIDENCE"}),
    # PRE_FLIGHT_ESCALATE fires through branches 4-7
    "PRE_FLIGHT_ESCALATE": frozenset(
        {
            "BRANCH_4_EXPERIMENTAL",
            "BRANCH_5_RARE",
            "BRANCH_6_CONFLICTING",
            "BRANCH_7_PRIOR_DENIAL",
        }
    ),
    # DENIED outcomes do not escalate; branch is NONE
    "DENIED": frozenset({"NONE"}),
    # INFORMATION_NEEDED routes through low-confidence branch
    "INFORMATION_NEEDED": frozenset({"BRANCH_3_LOW_CONFIDENCE"}),
}


# =============================================================================
# PHI patterns — conservative regex-based scan.
# Per CASE_AUTHORING_GUIDE.md § 4, these patterns indicate likely PHI.
# Designed for false-positive-tolerant operation: a flagged case prompts
# the SME to confirm + revise rather than auto-rejecting.
# =============================================================================

# Social Security Number: NNN-NN-NNNN
_PHI_SSN = re.compile(r"\b\d{3}-\d{2}-\d{4}\b")

# Medical Record Number: MRN followed by digits (case-insensitive)
_PHI_MRN = re.compile(r"\b(?:MRN|medical record number)[\s:#]*\d{4,}\b", re.IGNORECASE)

# Date of Birth phrasing
_PHI_DOB_PHRASE = re.compile(r"\b(?:DOB|date of birth|born on)[\s:]*\d", re.IGNORECASE)

# Email address
_PHI_EMAIL = re.compile(r"\b[\w.+-]+@[\w-]+\.[\w.-]+\b")

# US phone number (any common format)
_PHI_PHONE = re.compile(r"\b(?:\+?1[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b")

# Street address heuristic: number + street type
_PHI_STREET = re.compile(
    r"\b\d{1,5}\s+\w+\s+(?:St\b|Street\b|Ave\b|Avenue\b|Rd\b|Road\b"
    r"|Blvd\b|Boulevard\b|Ln\b|Lane\b|Dr\b|Drive\b|Ct\b|Court\b"
    r"|Pl\b|Place\b|Way\b)",
    re.IGNORECASE,
)

# Specific date with year >= 1900 (M/D/YYYY or MM/DD/YYYY)
# Used as an heuristic only — clinical-relevant dates (PRIOR THERAPY 2020-2024)
# get flagged as WARN, not FAIL. Pattern detects 4-digit year.
_PHI_SPECIFIC_DATE = re.compile(r"\b\d{1,2}/\d{1,2}/(?:19|20)\d{2}\b")

# Full name heuristic: two capitalized words ending common surname-prefix
# This is INTENTIONALLY conservative — clinician names in a case description
# would trigger this, which is the desired behavior.
_PHI_FULL_NAME = re.compile(r"\b(?:Mr|Mrs|Ms|Dr|Patient)\.?\s+[A-Z][a-z]+\s+[A-Z][a-z]+\b")


# =============================================================================
# Generic-judge-criteria patterns — sniff out fallback templates.
# =============================================================================

_GENERIC_JUDGE_PATTERNS = (
    "score highly if the rationale is correct",
    "evaluate the rationale for accuracy",
    "judge based on standard criteria",
    "use default rubric",
    "score 1-5 based on quality",
)


# =============================================================================
# Validators (each returns a single ValidationReport)
# =============================================================================


def scan_for_phi(text: str) -> list[str]:
    """
    Return a list of human-readable PHI marker names found in `text`.

    Empty list = no PHI detected. This is the public PHI-detection
    primitive — used both by `validate_no_phi` (against case
    clinical_notes) and by `.githooks/pacca_guard.py` (against any
    staged-file additions).

    Per CASE_AUTHORING_GUIDE.md § 4 — synthetic data only. Conservative
    pattern matching: false positives are preferable to false negatives
    for PHI protection.
    """
    hits: list[str] = []
    if _PHI_SSN.search(text):
        hits.append("SSN pattern (NNN-NN-NNNN)")
    if _PHI_MRN.search(text):
        hits.append("MRN reference")
    if _PHI_DOB_PHRASE.search(text):
        hits.append("DOB phrasing")
    if _PHI_EMAIL.search(text):
        hits.append("email address")
    if _PHI_PHONE.search(text):
        hits.append("phone number")
    if _PHI_STREET.search(text):
        hits.append("street address")
    if _PHI_SPECIFIC_DATE.search(text):
        hits.append("specific date (M/D/YYYY format)")
    if _PHI_FULL_NAME.search(text):
        hits.append("titled full name (Mr/Mrs/Ms/Dr/Patient + First Last)")
    return hits


def validate_no_phi(case: CaseDraftResponse) -> ValidationReport:
    """
    Scan clinical_notes (the highest-risk field) for PHI patterns.

    Per CASE_AUTHORING_GUIDE.md § 4 — synthetic data only. Conservative
    rules: any match → FAIL. SME must revise the notes to remove the PHI.

    Returns:
        ValidationReport with PASS or FAIL outcome.
    """
    hits = scan_for_phi(case.clinical_notes)

    if hits:
        return ValidationReport(
            validator=ValidatorName.PHI_SCAN,
            outcome=ValidationOutcome.FAIL,
            field_path="clinical_notes",
            reason=(
                "Detected likely PHI patterns: "
                + "; ".join(hits)
                + ". Per CASE_AUTHORING_GUIDE.md § 4, clinical_notes must "
                "be synthetic. Revise to remove specific identifiers."
            ),
        )

    return ValidationReport(
        validator=ValidatorName.PHI_SCAN,
        outcome=ValidationOutcome.PASS,
    )


def validate_guideline_citation(case: CaseDraftResponse) -> ValidationReport:
    """
    Verify guidelines_context mentions a recognized guideline body.

    Per CASE_AUTHORING_GUIDE.md § 5 — citations must reference an
    authoritative body. A case that cites only "per institutional policy"
    fails because reviewers cannot verify the citation against a public
    standard.

    Returns:
        ValidationReport with PASS, FAIL, or WARN.
    """
    text = case.guidelines_context

    # Case-sensitive match because guideline bodies are typically capitalized
    # acronyms (NCCN, ACR, etc.); a lowercase mention is more likely to be
    # incidental than an actual citation.
    matched = sorted({body for body in RECOGNIZED_GUIDELINE_BODIES if body in text})

    if matched:
        return ValidationReport(
            validator=ValidatorName.GUIDELINE_CITATION,
            outcome=ValidationOutcome.PASS,
            reason=f"Cites: {', '.join(matched)}",
        )

    return ValidationReport(
        validator=ValidatorName.GUIDELINE_CITATION,
        outcome=ValidationOutcome.FAIL,
        field_path="guidelines_context",
        reason=(
            "guidelines_context does not mention any recognized guideline "
            "body. Per CASE_AUTHORING_GUIDE.md § 5, must cite at least one "
            "of: NCCN, ACR, AAD, GINA, ECCO, ACC/AHA, etc. See the doc "
            "for the full recognized-body table."
        ),
    )


def validate_schema_completeness(case: CaseDraftResponse) -> ValidationReport:
    """
    Verify every required field is populated to a meaningful length.

    Pydantic enforces non-empty at parse time; this validator enforces
    SEMANTIC completeness (a 3-character title is technically non-empty
    but useless). Pydantic Field(min_length=...) catches most of this;
    we double-check the case_id format here.

    Returns:
        ValidationReport with PASS or FAIL.
    """
    if not re.match(r"^GC-\d{3,}$", case.case_id):
        return ValidationReport(
            validator=ValidatorName.SCHEMA_COMPLETENESS,
            outcome=ValidationOutcome.FAIL,
            field_path="case_id",
            reason=(
                f"case_id '{case.case_id}' does not match GC-NNN pattern. "
                "IDs are allocated by id_allocator; do not edit manually."
            ),
        )

    # Pydantic already enforced min_length for the major text fields; this
    # is a belt-and-suspenders check in case the model is bypassed.
    short_fields: list[str] = []
    if len(case.title) < 10:
        short_fields.append("title")
    if len(case.clinical_notes) < 80:
        short_fields.append("clinical_notes")
    if len(case.guidelines_context) < 80:
        short_fields.append("guidelines_context")
    if len(case.clinical_rationale) < 40:
        short_fields.append("clinical_rationale")
    if len(case.judge_scoring_criteria) < 40:
        short_fields.append("judge_scoring_criteria")

    if short_fields:
        return ValidationReport(
            validator=ValidatorName.SCHEMA_COMPLETENESS,
            outcome=ValidationOutcome.FAIL,
            field_path=",".join(short_fields),
            reason=(
                f"Fields below minimum semantic length: {short_fields}. "
                "Each field must convey enough detail to be auditable."
            ),
        )

    return ValidationReport(
        validator=ValidatorName.SCHEMA_COMPLETENESS,
        outcome=ValidationOutcome.PASS,
    )


def validate_outcome_branch_consistency(
    case: CaseDraftResponse,
) -> ValidationReport:
    """
    Verify expected_outcome and expected_branch are a valid pair.

    Per CASE_AUTHORING_GUIDE.md § 7 — AUTO_APPROVED requires
    BRANCH_1_AUTO_APPROVE; DENIED requires NONE; PRE_FLIGHT_ESCALATE
    requires one of branches 4-7; etc.

    Returns:
        ValidationReport with PASS or FAIL.
    """
    valid_branches = _VALID_OUTCOME_BRANCH.get(case.expected_outcome)
    if valid_branches is None:
        return ValidationReport(
            validator=ValidatorName.OUTCOME_BRANCH_CONSISTENCY,
            outcome=ValidationOutcome.FAIL,
            field_path="expected_outcome",
            reason=(
                f"expected_outcome '{case.expected_outcome}' is not a "
                "recognized outcome class. Must be one of: "
                + ", ".join(sorted(_VALID_OUTCOME_BRANCH.keys()))
            ),
        )

    if case.expected_branch not in valid_branches:
        return ValidationReport(
            validator=ValidatorName.OUTCOME_BRANCH_CONSISTENCY,
            outcome=ValidationOutcome.FAIL,
            field_path="expected_branch",
            reason=(
                f"expected_outcome '{case.expected_outcome}' is incompatible "
                f"with expected_branch '{case.expected_branch}'. Valid "
                f"branches for this outcome: {sorted(valid_branches)}. "
                "See CASE_AUTHORING_GUIDE.md § 7 decision tree."
            ),
        )

    return ValidationReport(
        validator=ValidatorName.OUTCOME_BRANCH_CONSISTENCY,
        outcome=ValidationOutcome.PASS,
    )


def validate_reasoning_specificity(case: CaseDraftResponse) -> ValidationReport:
    """
    Verify reasoning_must_include has ≥ 1 phrase and is not generic.

    Pydantic enforces ≥ 1 entry; this validator catches generic phrases
    like "approved" that pass on noise. Per CASE_AUTHORING_GUIDE.md § 14
    "Anti-patterns" — generic must_include defeats the purpose.

    Returns:
        ValidationReport with PASS, WARN, or FAIL.
    """
    if not case.reasoning_must_include:
        # Pydantic should have caught this, but defensive
        return ValidationReport(
            validator=ValidatorName.REASONING_SPECIFICITY,
            outcome=ValidationOutcome.FAIL,
            field_path="reasoning_must_include",
            reason="reasoning_must_include must contain ≥ 1 phrase.",
        )

    # Flag overly generic single-word entries
    generic_words = frozenset({"approved", "denied", "review", "appropriate", "ok", "yes", "no"})
    generic_hits = [
        phrase for phrase in case.reasoning_must_include if phrase.lower().strip() in generic_words
    ]
    if generic_hits:
        return ValidationReport(
            validator=ValidatorName.REASONING_SPECIFICITY,
            outcome=ValidationOutcome.WARN,
            field_path="reasoning_must_include",
            reason=(
                f"reasoning_must_include contains generic phrases that "
                f"will pass on noise: {generic_hits}. Prefer specific "
                "clinical phrases (e.g., 'NCCN Category 1', 'LVEF ≤ 35%')."
            ),
        )

    return ValidationReport(
        validator=ValidatorName.REASONING_SPECIFICITY,
        outcome=ValidationOutcome.PASS,
    )


def validate_judge_criteria_specificity(
    case: CaseDraftResponse,
) -> ValidationReport:
    """
    Verify judge_scoring_criteria is non-generic.

    Per CASE_AUTHORING_GUIDE.md § 14 — judges default to a generic rubric
    if scoring_criteria is left as a template. Such cases produce noisier
    scores. We catch known-generic templates.

    Returns:
        ValidationReport with PASS or WARN.
    """
    normalized = " ".join(case.judge_scoring_criteria.lower().split())
    for pattern in _GENERIC_JUDGE_PATTERNS:
        if pattern in normalized:
            return ValidationReport(
                validator=ValidatorName.JUDGE_CRITERIA_SPECIFICITY,
                outcome=ValidationOutcome.WARN,
                field_path="judge_scoring_criteria",
                reason=(
                    f"judge_scoring_criteria contains a known-generic "
                    f"phrase: '{pattern}'. Rewrite to specify what the "
                    "judge should evaluate for THIS case (specific "
                    "clinical claims, citations, etc.)."
                ),
            )

    return ValidationReport(
        validator=ValidatorName.JUDGE_CRITERIA_SPECIFICITY,
        outcome=ValidationOutcome.PASS,
    )


# =============================================================================
# Aggregator
# =============================================================================


def run_all_validators(case: CaseDraftResponse) -> list[ValidationReport]:
    """
    Run every validator against the case and return all reports.

    The agent surfaces FAIL reports as blockers and WARN reports as
    advisories. The case is acceptable for write iff no report is
    `is_blocking`.

    Returns:
        List of ValidationReport, one per validator. Always 6 entries.
    """
    return [
        validate_no_phi(case),
        validate_guideline_citation(case),
        validate_schema_completeness(case),
        validate_outcome_branch_consistency(case),
        validate_reasoning_specificity(case),
        validate_judge_criteria_specificity(case),
    ]
