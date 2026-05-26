"""
Tests for file_router.

Strategy: parametrize across the 6 routing rules + their fallbacks. Use
tmp_path for the new-file-threshold test (which scans expansion_cases.py).
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from pacca.agents.sme_authoring.file_router import (
    FILE_TO_LIST_NAME,
    SPECIALTY_TO_FILE,
    RoutingDecision,
    route_case,
)
from pacca.agents.sme_authoring.models import SMEScenario

if TYPE_CHECKING:
    from pathlib import Path

    from pacca.agents.sme_authoring.models import CaseDraftResponse


# =============================================================================
# Special-purpose routing (failure-mode-driven)
# =============================================================================


class TestFailureModeRouting:
    def test_memory_trap_routes_to_near_miss(self, valid_case_draft: CaseDraftResponse) -> None:
        scenario = SMEScenario(
            description=(
                "NSCLC near-miss with PD-L1 just below the threshold to "
                "test memory-trap discrimination."
            ),
            failure_mode_label="False pattern-matching (memory trap)",
        )
        decision = route_case(valid_case_draft, scenario)
        assert decision.target_file == "near_miss_cases.py"
        assert decision.list_name == "NEAR_MISS_CASES"
        assert not decision.is_new_file

    def test_discriminator_routes_to_pediatric(self, valid_case_draft: CaseDraftResponse) -> None:
        scenario = SMEScenario(
            description=(
                "Pediatric mild case for the complexity-score discriminator "
                "negative class to validate the score model."
            ),
            failure_mode_label="Discriminator negative class",
        )
        decision = route_case(valid_case_draft, scenario)
        assert decision.target_file == "pediatric_cases.py"

    def test_ambiguous_completeness_routes_to_own_file(
        self, valid_case_draft: CaseDraftResponse
    ) -> None:
        scenario = SMEScenario(
            description=(
                "MS DMT case with severity described qualitatively but "
                "no EDSS score documented — ambiguous completeness probe."
            ),
            failure_mode_label="Ambiguous completeness probe",
        )
        decision = route_case(valid_case_draft, scenario)
        assert decision.target_file == "ambiguous_completeness_cases.py"


# =============================================================================
# Outcome-based routing
# =============================================================================


class TestOutcomeRouting:
    def test_denied_outcome_routes_to_denial_file(
        self, valid_case_draft: CaseDraftResponse
    ) -> None:
        case = valid_case_draft.model_copy(
            update={
                "expected_outcome": "DENIED",
                "expected_branch": "NONE",
            }
        )
        decision = route_case(case)
        assert decision.target_file == "denial_cases.py"
        assert decision.list_name == "DENIAL_CASES"


# =============================================================================
# Specialty hint routing (intended_specialty wins over ICD-10)
# =============================================================================


class TestSpecialtyHintRouting:
    @pytest.mark.parametrize(
        "specialty_hint, expected_file",
        [
            ("oncology", "oncology_depth_cases.py"),
            ("cardiology", "cardiology_cases.py"),
            ("mental_health", "mental_health_cases.py"),
            ("behavioral", "mental_health_cases.py"),
            ("pulmonology", "pulmonology_adult_cases.py"),
            ("transplant", "transplant_cases.py"),
            ("neurology", "neurology_cases.py"),
            ("ob", "ob_cases.py"),
            ("OBGYN", "ob_cases.py"),  # tests case-insensitive normalization
            ("reproductive", "ob_cases.py"),
            ("endocrinology", "endocrinology_cases.py"),
            ("hematology", "hematology_cases.py"),
        ],
    )
    def test_specialty_hint_routes_correctly(
        self,
        valid_case_draft: CaseDraftResponse,
        specialty_hint: str,
        expected_file: str,
    ) -> None:
        scenario = SMEScenario(
            description="Sample scenario for routing test purposes only.",
            intended_specialty=specialty_hint,
        )
        # Use a benign diagnosis code that doesn't pre-empt the hint
        case = valid_case_draft.model_copy(update={"diagnosis_code": "R69"})
        decision = route_case(case, scenario)
        assert decision.target_file == expected_file


# =============================================================================
# ICD-10 prefix fallback (when no specialty hint)
# =============================================================================


class TestIcd10PrefixRouting:
    @pytest.mark.parametrize(
        "icd10_code, expected_file",
        [
            # Oncology — C codes
            ("C34.1", "oncology_depth_cases.py"),
            ("C50.911", "oncology_depth_cases.py"),
            # Cardiology — I codes
            ("I50.22", "cardiology_cases.py"),
            ("I48.91", "cardiology_cases.py"),
            # Pulmonology — J codes (but require adult age)
            ("J45.50", "pulmonology_adult_cases.py"),
            # Mental health — F codes
            ("F33.2", "mental_health_cases.py"),
            ("F20.0", "mental_health_cases.py"),
            # Neurology — G codes
            ("G35", "neurology_cases.py"),
            ("G43.701", "neurology_cases.py"),
            # Endocrinology — E codes (but require adult to avoid geriatric routing)
            ("E11.65", "endocrinology_cases.py"),
            # Transplant — Z94.x
            ("Z94.0", "transplant_cases.py"),
            ("Z94.1", "transplant_cases.py"),
            # Hematology — D5-D8
            ("D57.1", "hematology_cases.py"),  # sickle cell
            ("D69.3", "hematology_cases.py"),  # ITP
            # OB — O codes
            ("O09.512", "ob_cases.py"),
        ],
    )
    def test_icd10_routes_to_specialty_file(
        self,
        valid_case_draft: CaseDraftResponse,
        icd10_code: str,
        expected_file: str,
    ) -> None:
        # Provide an adult-age notes to ensure geriatric/pediatric override
        # doesn't kick in
        case = valid_case_draft.model_copy(
            update={
                "diagnosis_code": icd10_code,
                "clinical_notes": (
                    "45-year-old adult patient with a clinical scenario "
                    "described in the standard format to test ICD-10-based "
                    "routing for the specialty inferred from the prefix."
                ),
            }
        )
        decision = route_case(case)
        assert decision.target_file == expected_file


# =============================================================================
# Age-based overrides
# =============================================================================


class TestAgeOverrides:
    def test_geriatric_age_overrides_specialty(self, valid_case_draft: CaseDraftResponse) -> None:
        # 85yo with K-code (GI) should go to geriatric, NOT a GI file
        case = valid_case_draft.model_copy(
            update={
                "diagnosis_code": "K22.0",  # GI - achalasia
                "clinical_notes": (
                    "85-year-old female with achalasia presenting with "
                    "progressive dysphagia and weight loss over 6 months."
                ),
            }
        )
        decision = route_case(case)
        assert decision.target_file == "geriatric_cases.py"

    def test_geriatric_age_does_not_override_oncology(
        self, valid_case_draft: CaseDraftResponse
    ) -> None:
        # 82yo with C-code (oncology) goes to oncology, NOT geriatric
        case = valid_case_draft.model_copy(
            update={
                "diagnosis_code": "C18.7",
                "clinical_notes": (
                    "82-year-old male with stage III sigmoid colon cancer "
                    "discussing adjuvant chemotherapy options."
                ),
            }
        )
        decision = route_case(case)
        assert decision.target_file == "oncology_depth_cases.py"

    def test_geriatric_age_does_not_override_cardiology(
        self, valid_case_draft: CaseDraftResponse
    ) -> None:
        # 88yo with I-code (cardiology) goes to cardiology
        case = valid_case_draft.model_copy(
            update={
                "diagnosis_code": "I50.22",
                "clinical_notes": (
                    "88-year-old female with chronic systolic heart failure "
                    "considering device therapy after optimal medical therapy."
                ),
            }
        )
        decision = route_case(case)
        assert decision.target_file == "cardiology_cases.py"

    def test_pediatric_age_routes_to_pediatric_file(
        self, valid_case_draft: CaseDraftResponse
    ) -> None:
        case = valid_case_draft.model_copy(
            update={
                "diagnosis_code": "J45.30",
                "clinical_notes": (
                    "10-year-old female with mild persistent asthma "
                    "well-controlled on low-dose inhaled corticosteroid."
                ),
            }
        )
        decision = route_case(case)
        assert decision.target_file == "pediatric_cases.py"


# =============================================================================
# Fallback to expansion_cases.py
# =============================================================================


class TestExpansionFallback:
    def test_unknown_specialty_falls_back_to_expansion(
        self, valid_case_draft: CaseDraftResponse, tmp_path: Path
    ) -> None:
        # R69 (illness, unspecified) — no specialty mapping
        case = valid_case_draft.model_copy(
            update={
                "diagnosis_code": "R69",
                "clinical_notes": (
                    "40-year-old patient with nonspecific symptoms not "
                    "obviously tied to a recognized specialty in this test."
                ),
            }
        )
        decision = route_case(case, case_dir=tmp_path)
        assert decision.target_file == "expansion_cases.py"

    def test_specialty_with_accumulated_cases_recommends_new_file(
        self, valid_case_draft: CaseDraftResponse, tmp_path: Path
    ) -> None:
        # Simulate expansion_cases.py with 4 nephrology cases by title
        expansion_text = '"""Expansion."""\nEXPANSION_CASES = [\n'
        for i in range(4):
            expansion_text += (
                f"    GoldenCase(\n"
                f'        case_id="GC-{100 + i:03d}",\n'
                f'        title="Nephrology case {i}",\n'
                f"    ),\n"
            )
        expansion_text += "]\n"
        (tmp_path / "expansion_cases.py").write_text(expansion_text, encoding="utf-8")

        case = valid_case_draft.model_copy(
            update={"diagnosis_code": "N18.6"}  # Renal — ESRD
        )
        scenario = SMEScenario(
            description=(
                "ESRD dialysis patient requesting initial nephrology workup "
                "and consultation for renal replacement therapy planning."
            ),
            intended_specialty="nephrology",
        )
        decision = route_case(case, scenario, case_dir=tmp_path)
        assert decision.is_new_file is True
        assert decision.target_file == "nephrology_cases.py"
        assert decision.list_name == "NEPHROLOGY_CASES"


# =============================================================================
# Invariant tests on the mapping tables
# =============================================================================


class TestMappingInvariants:
    def test_every_specialty_target_is_in_file_to_list(self) -> None:
        # Every file SPECIALTY_TO_FILE points at must have a list-name mapping
        missing = [f for f in SPECIALTY_TO_FILE.values() if f not in FILE_TO_LIST_NAME]
        assert not missing, f"Missing list-name entries for: {missing}"

    def test_routing_decision_is_frozen(self) -> None:
        # RoutingDecision is a frozen dataclass; mutations should fail
        decision = RoutingDecision(
            target_file="x.py",
            list_name="X",
            is_new_file=False,
            reason="test",
        )
        with pytest.raises((AttributeError, Exception)):
            decision.target_file = "y.py"  # type: ignore[misc]
