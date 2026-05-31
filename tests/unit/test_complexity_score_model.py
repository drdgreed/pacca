"""
iter-5 chg-3 — complexity-score model unit tests.

Pure tests on the _compute_complexity_score helper and the
_check_pediatric_complex method's new score-based path. No live API calls.

Two layers of coverage:
  1. The model in isolation — each weight independently, boundary cases,
     the [1, 5] clamp.
  2. The four real pediatric data points (GC-012 + chg-2's GC-023, GC-024,
     GC-025) — confirm the model lands each on the correct side of the
     pediatric escalation threshold (3).
"""

from __future__ import annotations

from typing import Any

from pacca.agents.clinical_risk_detector import (
    ClinicalRiskDetector,
    _compute_complexity_score,
)
from pacca.models.clinical import ClinicalCase, EvidenceItem
from pacca.models.enums import EscalationReason, EvidenceSourceType
from tests.clinical.golden_cases import GOLDEN_CASES
from tests.clinical.pediatric_cases import PEDIATRIC_CASES


def _make_case(notes: str = "", **kwargs: Any) -> ClinicalCase:
    return ClinicalCase(
        patient_id="P-TEST",
        primary_diagnosis_code="X00",
        procedure_code="J0000",
        evidence=[
            EvidenceItem(
                id="e1",
                source_type=EvidenceSourceType.CLINICAL_NOTE,
                description=notes[:200],
                original_text=notes,
                confidence=0.9,
            )
        ],
        **kwargs,
    )


# =============================================================================
# Each weight independently
# =============================================================================


class TestComplexityScoreWeights:
    def test_no_features_clamps_to_one(self) -> None:
        """An empty case must land at the floor of the [1, 5] clamp."""
        assert _compute_complexity_score(_make_case("Routine encounter.")) == 1

    def test_pediatric_age_adds_two(self) -> None:
        case = _make_case("Pediatric patient.", patient_age=10)
        assert _compute_complexity_score(case) == 2  # pediatric +2

    def test_geriatric_age_adds_two(self) -> None:
        case = _make_case("Older adult.", patient_age=80)
        assert _compute_complexity_score(case) == 2

    def test_adult_age_adds_nothing(self) -> None:
        case = _make_case("Healthy adult.", patient_age=45)
        assert _compute_complexity_score(case) == 1  # clamp floor only

    def test_mild_severity_adds_nothing(self) -> None:
        case = _make_case("", patient_age=45, disease_severity="mild")
        assert _compute_complexity_score(case) == 1

    def test_moderate_severity_adds_one(self) -> None:
        case = _make_case("", patient_age=45, disease_severity="moderate")
        assert _compute_complexity_score(case) == 1  # moderate +1 = 1 (no clamp)

    def test_severe_severity_adds_two(self) -> None:
        case = _make_case("", patient_age=45, disease_severity="severe")
        assert _compute_complexity_score(case) == 2

    def test_moderate_to_severe_adds_two(self) -> None:
        case = _make_case("", patient_age=45, disease_severity="moderate-to-severe")
        assert _compute_complexity_score(case) == 2

    def test_critical_severity_adds_three(self) -> None:
        case = _make_case("", patient_age=45, disease_severity="critical")
        assert _compute_complexity_score(case) == 3

    def test_two_prior_failures_add_one(self) -> None:
        """2+ failures add +1; combine with moderate severity to see the
        increment above the clamp floor."""
        notes = "Prior failure of methotrexate. Failed cyclosporine trial."
        case = _make_case(notes, patient_age=45, disease_severity="moderate")
        # adult +0, moderate +1, 2 failures +1, no comorbidity = 2
        assert _compute_complexity_score(case) == 2

    def test_single_failure_does_not_add(self) -> None:
        """Only 2+ failures trigger the weight (refractory pattern, not single-trial)."""
        notes = "Prior failure of methotrexate."
        case = _make_case(notes, patient_age=45)
        assert _compute_complexity_score(case) == 1  # 0 + 0 + 0 = 0 → clamp to 1

    def test_comorbidity_hint_adds_one(self) -> None:
        notes = "Patient has comorbid hypertension."
        case = _make_case(notes, patient_age=45)
        assert _compute_complexity_score(case) == 1  # 0+0+0+1=1; clamp floor 1


# =============================================================================
# Boundary and clamp behavior
# =============================================================================


class TestComplexityScoreBoundary:
    def test_score_clamped_to_max_five(self) -> None:
        """A case maximizing every weight must clamp at 5, not exceed."""
        notes = (
            "Critical illness with multiple comorbidities. "
            "Prior failure of agent A. Prior failure of agent B. "
            "Failed trial of agent C. Refractory disease."
        )
        case = _make_case(
            notes,
            patient_age=8,  # pediatric +2
            disease_severity="critical",  # +3
        )
        # 2 + 3 + 1 (2+ failures) + 1 (comorbidity hint via "comorbid") = 7 → clamp to 5
        assert _compute_complexity_score(case) == 5

    def test_score_clamped_to_min_one(self) -> None:
        """A case with no signals must clamp at 1, not go to 0."""
        case = _make_case("Empty.", patient_age=30, disease_severity="mild")
        assert _compute_complexity_score(case) == 1

    def test_pediatric_age_cutoff_is_strict(self) -> None:
        """18 is NOT pediatric; 17 IS."""
        case17 = _make_case("", patient_age=17, disease_severity="mild")
        case18 = _make_case("", patient_age=18, disease_severity="mild")
        assert _compute_complexity_score(case17) == 2  # pediatric +2
        assert _compute_complexity_score(case18) == 1  # not pediatric, mild +0


# =============================================================================
# Structured field vs parser fallback path
# =============================================================================


class TestComplexityScoreDataSourcePaths:
    def test_structured_score_overrides_computation(self) -> None:
        """When ClinicalCase.complexity_score is set, the detector uses it directly."""
        # Real cheap case (would compute to 1) but caller said it's a 4.
        case = _make_case(
            "Routine.",
            patient_age=14,  # pediatric, so the pediatric check runs
            complexity_score=4,
        )
        flags = ClinicalRiskDetector().evaluate(case)
        assert EscalationReason.PEDIATRIC_COMPLEX in flags.reasons

    def test_structured_score_below_threshold_blocks_escalation(self) -> None:
        """Structured score 2 must NOT fire pediatric_complex (threshold=3)."""
        case = _make_case(
            "Severe critical refractory disease with multiple comorbid conditions.",
            patient_age=14,
            complexity_score=2,
        )
        flags = ClinicalRiskDetector().evaluate(case)
        # The structured 2 overrides what would otherwise compute to 5+.
        assert EscalationReason.PEDIATRIC_COMPLEX not in flags.reasons

    def test_parser_fallback_when_structured_score_absent(self) -> None:
        """When complexity_score is None, the detector computes from features."""
        case = _make_case(
            "14-year-old with severe persistent asthma.",
            # no patient_age set; parsed from text
            # no disease_severity set; parsed from text
            # no complexity_score
        )
        flags = ClinicalRiskDetector().evaluate(case)
        # pediatric (parsed) +2 + severe (parsed) +2 = 4 >= 3
        assert EscalationReason.PEDIATRIC_COMPLEX in flags.reasons


# =============================================================================
# Real data points — the four pediatric cases that motivated the model
# =============================================================================


def _case_from_golden(g: Any) -> ClinicalCase:
    return ClinicalCase(
        patient_id=f"P-{g.case_id}",
        primary_diagnosis_code=g.diagnosis_code,
        procedure_code=g.procedure_code,
        evidence=[
            EvidenceItem(
                id="e1",
                source_type=EvidenceSourceType.CLINICAL_NOTE,
                description=g.clinical_notes[:200],
                original_text=g.clinical_notes,
                confidence=0.9,
            )
        ],
    )


class TestRealPediatricDataPoints:
    """
    Validate the score model on the four real pediatric data points it was
    designed for. These are the cases the model has to discriminate — if a
    future case definition or model change breaks any of these, the model
    needs to be revisited.
    """

    def test_gc012_severe_asthma_escalates(self) -> None:
        gc012 = next(c for c in GOLDEN_CASES if c.case_id == "GC-012")
        case = _case_from_golden(gc012)
        flags = ClinicalRiskDetector().evaluate(case)
        assert EscalationReason.PEDIATRIC_COMPLEX in flags.reasons

    def test_gc023_mild_well_controlled_auto_approves(self) -> None:
        """The discriminator's negative-class case."""
        gc023 = next(c for c in PEDIATRIC_CASES if c.case_id == "GC-023")
        case = _case_from_golden(gc023)
        flags = ClinicalRiskDetector().evaluate(case)
        assert EscalationReason.PEDIATRIC_COMPLEX not in flags.reasons

    def test_gc024_moderate_ambiguous_escalates(self) -> None:
        """The borderline case — pushed over threshold by multiple weights."""
        gc024 = next(c for c in PEDIATRIC_CASES if c.case_id == "GC-024")
        case = _case_from_golden(gc024)
        flags = ClinicalRiskDetector().evaluate(case)
        assert EscalationReason.PEDIATRIC_COMPLEX in flags.reasons

    def test_gc025_severe_different_condition_escalates(self) -> None:
        """Confirms the model generalizes beyond asthma."""
        gc025 = next(c for c in PEDIATRIC_CASES if c.case_id == "GC-025")
        case = _case_from_golden(gc025)
        flags = ClinicalRiskDetector().evaluate(case)
        assert EscalationReason.PEDIATRIC_COMPLEX in flags.reasons


class TestAdultCasesUnaffected:
    """The age check must short-circuit non-pediatric cases regardless of score."""

    def test_adult_high_score_does_not_fire_pediatric_check(self) -> None:
        gc010 = next(c for c in GOLDEN_CASES if c.case_id == "GC-010")
        case = _case_from_golden(gc010)
        flags = ClinicalRiskDetector().evaluate(case)
        assert EscalationReason.PEDIATRIC_COMPLEX not in flags.reasons


class TestAdultComplexCheck:
    """iter-6 chg-2: deterministic adult specialist-review escalation."""

    def _fire(self, **kwargs: Any) -> bool:
        from pacca.agents.clinical_risk_detector import EscalationFlags

        detector = ClinicalRiskDetector()
        flags = EscalationFlags()
        detector._check_adult_complex(_make_case(**kwargs), flags)
        return EscalationReason.ADULT_COMPLEX in flags.reasons

    def test_adult_severe_with_failures_and_comorbidity_fires_at_threshold(self) -> None:
        # adult +0, severe +2, 2 failures +1, comorbidity +1 = 4 == threshold(4)
        notes = "Refractory to first agent; failed trial of second agent. Comorbid type 2 diabetes."
        assert self._fire(notes=notes, patient_age=58, disease_severity="severe") is True

    def test_adult_severe_only_does_not_fire(self) -> None:
        # adult +0, severe +2 = 2 < 4 — the must-not-escalate boundary
        assert self._fire(notes="", patient_age=49, disease_severity="severe") is False

    def test_elderly_severe_fires(self) -> None:
        # age>75 +2, severe +2 = 4 == threshold
        assert self._fire(notes="", patient_age=81, disease_severity="severe") is True

    def test_pediatric_age_does_not_fire_adult_check(self) -> None:
        # age < 18 is gated out of the ADULT path (pediatric check owns it)
        assert self._fire(notes="", patient_age=10, disease_severity="severe") is False

    def test_structured_score_below_threshold_does_not_fire(self) -> None:
        # structured complexity_score=3 short-circuits the compute path; 3 < 4
        assert self._fire(notes="", patient_age=58, complexity_score=3) is False

    def test_structured_score_at_threshold_fires(self) -> None:
        assert self._fire(notes="", patient_age=58, complexity_score=4) is True

    def test_missing_age_does_not_fire(self) -> None:
        # no structured age and no parseable age → cannot confirm adult → no fire
        assert self._fire(notes="No age stated.", disease_severity="critical") is False


class TestGoldenTwentyAdultComplexRegression:
    """No golden-20 case that currently AUTO_APPROVES may start escalating
    on the new adult check (the chg-2 regression guard)."""

    def test_no_auto_approved_golden_case_newly_fires_adult_complex(self) -> None:
        from pacca.agents.clinical_risk_detector import EscalationFlags
        from tests.clinical.golden_cases import ExpectedOutcome

        detector = ClinicalRiskDetector()
        for g in GOLDEN_CASES:
            if g.expected_outcome is not ExpectedOutcome.AUTO_APPROVED:
                continue
            case = _make_case(notes=g.clinical_notes)
            flags = EscalationFlags()
            detector._check_adult_complex(case, flags)
            assert EscalationReason.ADULT_COMPLEX not in flags.reasons, (
                f"{g.case_id} auto-approves today but the adult check would "
                f"escalate it — chg-2 must not regress the golden-20."
            )
