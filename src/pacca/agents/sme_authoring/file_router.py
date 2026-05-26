"""
File router — decide which case file a new GoldenCase belongs in.

Per docs/CASE_AUTHORING_GUIDE.md § 9, cases are routed based on a
decision tree:

  Special-purpose cases (route by failure-mode label, not specialty):
    - failure_mode = "False pattern-matching (memory trap)"  → near_miss_cases.py
    - expected_outcome = "DENIED"                            → denial_cases.py
    - ambiguous-completeness pattern in notes                → ambiguous_completeness_cases.py
    - pediatric discriminator probe (failure_mode = "Discriminator ...")
                                                              → pediatric_cases.py

  Routine cases (route by specialty inferred from intended_specialty or ICD-10 prefix):
    - oncology     → oncology_depth_cases.py
    - cardiology   → cardiology_cases.py
    - mental_health → mental_health_cases.py
    - geriatric (>=80yo AND not in another specialty thematic) → geriatric_cases.py
    - pulmonology (adult) → pulmonology_adult_cases.py
    - transplant   → transplant_cases.py
    - neurology    → neurology_cases.py
    - ob / reproductive → ob_cases.py
    - endocrinology → endocrinology_cases.py
    - hematology   → hematology_cases.py

  Specialty-without-thematic-file (≥ 5 cases of new category warrant new file):
    - If expansion_cases.py already has ≥ 4 cases of this specialty,
      RoutingDecision recommends creating a NEW thematic file
      named `{specialty}_cases.py`.
    - Otherwise → expansion_cases.py (default for misc gap-closure).

The router is intentionally heuristic; it produces a recommendation that
the SME can override in the agent's review step.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import TYPE_CHECKING

from pacca.agents.sme_authoring.id_allocator import (
    _CASE_ID_PATTERN,
    DEFAULT_CASE_DIR,
)

if TYPE_CHECKING:
    from pathlib import Path

    from pacca.agents.sme_authoring.models import CaseDraftResponse, SMEScenario

# =============================================================================
# Specialty mappings
# =============================================================================

# Single source of truth for specialty -> thematic file mapping.
# When a new thematic file is added to tests/clinical/, add an entry here
# in the same PR.
SPECIALTY_TO_FILE: dict[str, str] = {
    "oncology": "oncology_depth_cases.py",
    "cardiology": "cardiology_cases.py",
    "mental_health": "mental_health_cases.py",
    "behavioral": "mental_health_cases.py",
    "psychiatry": "mental_health_cases.py",
    "pulmonology": "pulmonology_adult_cases.py",
    "transplant": "transplant_cases.py",
    "neurology": "neurology_cases.py",
    "ob": "ob_cases.py",
    "obgyn": "ob_cases.py",
    "ob_gyn": "ob_cases.py",
    "reproductive": "ob_cases.py",
    "endocrinology": "endocrinology_cases.py",
    "hematology": "hematology_cases.py",
    "geriatric": "geriatric_cases.py",
    "pediatric": "pediatric_cases.py",
}

# List-variable name for each thematic file.
FILE_TO_LIST_NAME: dict[str, str] = {
    "golden_cases.py": "GOLDEN_CASES",
    "near_miss_cases.py": "NEAR_MISS_CASES",
    "pediatric_cases.py": "PEDIATRIC_CASES",
    "expansion_cases.py": "EXPANSION_CASES",
    "denial_cases.py": "DENIAL_CASES",
    "cardiology_cases.py": "CARDIOLOGY_CASES",
    "mental_health_cases.py": "MENTAL_HEALTH_CASES",
    "geriatric_cases.py": "GERIATRIC_CASES",
    "pulmonology_adult_cases.py": "PULMONOLOGY_ADULT_CASES",
    "ambiguous_completeness_cases.py": "AMBIGUOUS_COMPLETENESS_CASES",
    "transplant_cases.py": "TRANSPLANT_CASES",
    "neurology_cases.py": "NEUROLOGY_CASES",
    "ob_cases.py": "OB_CASES",
    "hematology_cases.py": "HEMATOLOGY_CASES",
    "endocrinology_cases.py": "ENDOCRINOLOGY_CASES",
    "oncology_depth_cases.py": "ONCOLOGY_DEPTH_CASES",
    "depth_extension_cases.py": "DEPTH_EXTENSION_CASES",
}

# ICD-10 prefix → specialty fallback (used when intended_specialty is absent).
# First-letter-of-code is the primary signal. Z94 (transplant status) is a
# special case requiring multi-character match.
_ICD10_PREFIX_TO_SPECIALTY: dict[str, str] = {
    "C": "oncology",  # Malignant neoplasms
    "D0": "oncology",  # In-situ neoplasms (D00-D09)
    "D1": "oncology",  # Benign neoplasms (D10-D36)
    "D2": "oncology",
    "D3": "oncology",
    "D4": "oncology",  # Uncertain behavior (D37-D48)
    "D5": "hematology",  # Nutritional anemias (D50-D53)
    "D6": "hematology",  # Hemolytic anemias / aplastic (D55-D64)
    "D7": "hematology",  # Coag/platelet disorders
    "D8": "hematology",  # Immune mechanism disorders
    "E": "endocrinology",
    "F": "mental_health",
    "G": "neurology",
    "I": "cardiology",
    "J": "pulmonology",
    "K": "gastroenterology",
    "L": "dermatology",
    "M": "rheumatology_ortho",
    "N": "nephrology",
    "O": "ob",
    "P": "pediatric",
    "Z94": "transplant",
}

# Failure-mode tokens that route to special-purpose files.
_MEMORY_TRAP_TOKENS = frozenset({"false pattern", "memory trap", "near-miss", "near miss"})
_AMBIGUOUS_COMPLETENESS_TOKENS = frozenset({"ambiguous", "completeness", "graded sparseness"})
_DISCRIMINATOR_TOKENS = frozenset({"discriminator", "complexity-score"})

# Threshold: if a specialty has this many cases already in expansion_cases.py,
# recommend splitting into a new thematic file.
_NEW_FILE_THRESHOLD = 4


@dataclass(frozen=True)
class RoutingDecision:
    """
    The router's recommendation for where a case belongs.

    Attributes:
        target_file: Filename (e.g., "denial_cases.py") relative to case_dir.
        list_name: The list-variable name in the target file
            (e.g., "DENIAL_CASES").
        is_new_file: True if the target file does not yet exist and should
            be created. False if appending to an existing file.
        reason: Human-readable explanation; surfaced to the SME for review.
    """

    target_file: str
    list_name: str
    is_new_file: bool
    reason: str


# =============================================================================
# Helpers
# =============================================================================


def _normalize_specialty(s: str) -> str:
    """Normalize a specialty hint (lowercase, replace common separators)."""
    return s.lower().strip().replace("-", "_").replace(" ", "_").replace("/", "_")


def _infer_specialty_from_icd10(diagnosis_code: str) -> str | None:
    """
    Infer specialty from ICD-10 code prefix.

    Returns None if no mapping exists for the prefix.
    """
    code = diagnosis_code.upper().strip()
    if not code:
        return None

    # Z94 transplant prefix needs 3-character match
    if code.startswith("Z94"):
        return "transplant"

    # 2-char prefixes (D0-D8 disambiguation)
    if len(code) >= 2:
        prefix2 = code[:2]
        if prefix2 in _ICD10_PREFIX_TO_SPECIALTY:
            return _ICD10_PREFIX_TO_SPECIALTY[prefix2]

    # 1-char prefix fallback
    return _ICD10_PREFIX_TO_SPECIALTY.get(code[0])


def _detect_age_in_notes(clinical_notes: str) -> int | None:
    """
    Extract patient age from `NN-year-old` phrasing in clinical notes.

    Returns the age as an integer, or None if no clean match.
    """
    match = re.search(r"(\d{1,3})-year-old", clinical_notes, re.IGNORECASE)
    if not match:
        return None
    age = int(match.group(1))
    if 0 <= age <= 120:
        return age
    return None


def _count_specialty_in_expansion(specialty: str, case_dir: Path) -> int:
    """
    Heuristic count of how many cases in expansion_cases.py mention the
    given specialty in their `title` field.

    Used to decide whether a specialty has accumulated enough cases in
    expansion_cases.py to warrant promotion to a dedicated thematic file.
    """
    expansion = case_dir / "expansion_cases.py"
    if not expansion.exists():
        return 0
    text = expansion.read_text(encoding="utf-8")

    count = 0
    # Find every case_id + walk forward to its title; check if specialty
    # appears in title.
    for match in _CASE_ID_PATTERN.finditer(text):
        # Look at the next 200 chars after the match for the title field
        window = text[match.end() : match.end() + 400]
        title_match = re.search(r'title\s*=\s*["\'](.*?)["\']', window, re.DOTALL)
        if title_match and specialty.lower() in title_match.group(1).lower():
            count += 1
    return count


# =============================================================================
# Main routing function
# =============================================================================


def route_case(  # noqa: PLR0911
    case: CaseDraftResponse,
    scenario: SMEScenario | None = None,
    case_dir: Path | None = None,
) -> RoutingDecision:
    """
    Decide which case file the new case belongs in.

    Args:
        case: The drafted case to route.
        scenario: Optional SME scenario for intended_specialty + failure_mode
            hints. If None, routing falls back to ICD-10 prefix inference.
        case_dir: Directory containing the case files. Defaults to
            tests/clinical/.

    Returns:
        RoutingDecision with target_file, list_name, is_new_file, and
        reason.
    """
    case_dir = case_dir or DEFAULT_CASE_DIR

    # --- Step 1: special-purpose routing by failure-mode label ---
    failure_mode = (scenario.failure_mode_label or "").lower() if scenario else ""

    if any(tok in failure_mode for tok in _MEMORY_TRAP_TOKENS):
        return _decision_for_existing_file(
            "near_miss_cases.py",
            reason=(
                f"failure_mode '{scenario.failure_mode_label if scenario else ''}' "
                "is a memory-trap probe → near_miss_cases.py"
            ),
        )

    if any(tok in failure_mode for tok in _DISCRIMINATOR_TOKENS):
        return _decision_for_existing_file(
            "pediatric_cases.py",
            reason=("failure_mode is a complexity-score discriminator probe → pediatric_cases.py"),
        )

    if any(tok in failure_mode for tok in _AMBIGUOUS_COMPLETENESS_TOKENS):
        return _decision_for_existing_file(
            "ambiguous_completeness_cases.py",
            reason=(
                "failure_mode is an ambiguous-completeness probe → ambiguous_completeness_cases.py"
            ),
        )

    # --- Step 2: outcome-based routing ---
    if case.expected_outcome == "DENIED":
        return _decision_for_existing_file(
            "denial_cases.py",
            reason="expected_outcome=DENIED → denial_cases.py",
        )

    # --- Step 3: specialty-based routing (intended_specialty hint wins) ---
    specialty: str | None = None
    if scenario and scenario.intended_specialty:
        specialty = _normalize_specialty(scenario.intended_specialty)

    if not specialty:
        specialty = _infer_specialty_from_icd10(case.diagnosis_code)

    # --- Step 3a: age-based override (>=80 → geriatric thematic, unless
    # specialty has its own thematic file already covering this age) ---
    age = _detect_age_in_notes(case.clinical_notes)
    if age is not None and age >= 80 and specialty not in {"oncology", "cardiology"}:
        # Defer to specialty file for oncology/cardiology (those have
        # geriatric exemplars in-file); otherwise route to geriatric.
        return _decision_for_existing_file(
            "geriatric_cases.py",
            reason=(
                f"patient age {age} >= 80 with no overriding specialty file → geriatric_cases.py"
            ),
        )

    # --- Step 3b: pediatric override (age <= 17 → pediatric thematic) ---
    if age is not None and age <= 17:
        return _decision_for_existing_file(
            "pediatric_cases.py",
            reason=(f"patient age {age} <= 17 → pediatric_cases.py"),
        )

    # --- Step 4: specialty thematic file lookup ---
    if specialty and specialty in SPECIALTY_TO_FILE:
        target = SPECIALTY_TO_FILE[specialty]
        return _decision_for_existing_file(
            target,
            reason=(f"specialty='{specialty}' maps to existing thematic file → {target}"),
        )

    # --- Step 5: specialty without thematic file → expansion or new file ---
    if specialty:
        # Check if this specialty has accumulated enough cases in
        # expansion_cases to warrant a new file.
        count = _count_specialty_in_expansion(specialty, case_dir)
        if count >= _NEW_FILE_THRESHOLD:
            new_file = f"{specialty}_cases.py"
            new_list = f"{specialty.upper()}_CASES"
            return RoutingDecision(
                target_file=new_file,
                list_name=new_list,
                is_new_file=True,
                reason=(
                    f"specialty='{specialty}' has accumulated {count} cases "
                    f"in expansion_cases.py (>= threshold {_NEW_FILE_THRESHOLD}) "
                    f"→ recommend new file {new_file}"
                ),
            )

    # --- Step 6: fallback to expansion_cases.py ---
    return _decision_for_existing_file(
        "expansion_cases.py",
        reason=(
            f"no thematic file for specialty='{specialty}' "
            "and below new-file threshold → expansion_cases.py (default)"
        ),
    )


def _decision_for_existing_file(filename: str, reason: str) -> RoutingDecision:
    """Build a RoutingDecision for an existing thematic file."""
    return RoutingDecision(
        target_file=filename,
        list_name=FILE_TO_LIST_NAME[filename],
        is_new_file=False,
        reason=reason,
    )
