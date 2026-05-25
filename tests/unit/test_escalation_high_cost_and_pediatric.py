"""
Unit tests for iter-3 chg-1 escalation checks:
  - _check_high_cost          (EscalationReason.HIGH_COST)
  - _check_pediatric_complex  (EscalationReason.PEDIATRIC_COMPLEX)

Also tests the parser fallbacks (cost / age / severity) directly, so a future
golden-case wording change doesn't silently defeat the structured-field-first
hybrid path.

No live API calls; pure dataclass / regex tests.
"""

from __future__ import annotations

from typing import Any

from pacca.agents.clinical_risk_detector import (
    ClinicalRiskDetector,
    _parse_age_from_notes,
    _parse_cost_from_notes,
    _parse_severity_from_notes,
)
from pacca.models.clinical import ClinicalCase, EvidenceItem
from pacca.models.enums import EscalationReason, EvidenceSourceType


def _make_case(notes: str = "", **kwargs: Any) -> ClinicalCase:
    """Convenience: build a ClinicalCase with one evidence item from a notes string."""
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
# Parser tests — these are the contract between "messy clinical prose" and
# "structured detector input." If a future golden-case wording breaks one of
# these, the parser needs updating before the detector can be trusted on it.
# =============================================================================


class TestCostParser:
    def test_simple_dollar_amount(self) -> None:
        assert _parse_cost_from_notes("Annual cost $50,000.") == 50_000

    def test_returns_max_when_multiple_amounts(self) -> None:
        """The per-infusion-times-12 pattern from GC-010 must return the totalled value."""
        notes = "$24,000/infusion x 12 = $288,000."
        assert _parse_cost_from_notes(notes) == 288_000

    def test_handles_K_suffix(self) -> None:
        assert _parse_cost_from_notes("$120K/year") == 120_000

    def test_returns_none_when_no_amount(self) -> None:
        assert _parse_cost_from_notes("Routine asthma case, no cost mentioned.") is None

    def test_handles_decimal(self) -> None:
        assert _parse_cost_from_notes("Cost: $12,500.50") == 12_500.50


class TestAgeParser:
    def test_year_old_hyphenated(self) -> None:
        assert _parse_age_from_notes("14-year-old male with asthma") == 14

    def test_year_old_spaced(self) -> None:
        assert _parse_age_from_notes("55 year old female") == 55

    def test_yo_abbreviation(self) -> None:
        assert _parse_age_from_notes("Pt is 67yo with COPD") == 67

    def test_age_colon_form(self) -> None:
        assert _parse_age_from_notes("Age: 42, no comorbidities") == 42

    def test_rejects_out_of_range_high(self) -> None:
        assert _parse_age_from_notes("999-year-old patient") is None

    def test_returns_none_when_no_age(self) -> None:
        assert _parse_age_from_notes("Asthma case, prior failures.") is None


class TestSeverityParser:
    def test_finds_severe(self) -> None:
        assert _parse_severity_from_notes("severe persistent asthma") == "severe"

    def test_finds_moderate_to_severe_hyphenated(self) -> None:
        assert _parse_severity_from_notes("moderate-to-severe RA") == "moderate-to-severe"

    def test_prefers_longer_phrase(self) -> None:
        # "moderate-to-severe" must match before bare "severe" — longer keywords first.
        result = _parse_severity_from_notes("moderate-to-severe disease activity")
        assert result == "moderate-to-severe"

    def test_returns_none_when_no_keyword(self) -> None:
        assert _parse_severity_from_notes("Mild intermittent asthma, well-controlled.") is None


# =============================================================================
# HIGH_COST check — structured field path + parser fallback path + negatives
# =============================================================================


class TestHighCostCheck:
    def test_fires_when_structured_cost_exceeds_threshold(self) -> None:
        # Structured field wins; parser fallback should not be needed.
        case = _make_case("No cost mentioned.", estimated_annual_cost=200_000.0)
        flags = ClinicalRiskDetector().evaluate(case)
        assert EscalationReason.HIGH_COST in flags.reasons

    def test_fires_when_notes_have_cost_and_structured_is_none(self) -> None:
        # Parser fallback path — exactly the GC-010 case in production.
        case = _make_case("Annual cost estimated at $24,000/infusion x 12 = $288,000.")
        flags = ClinicalRiskDetector().evaluate(case)
        assert EscalationReason.HIGH_COST in flags.reasons

    def test_does_not_fire_below_threshold(self) -> None:
        case = _make_case("Routine asthma, cost $5,000.", estimated_annual_cost=5_000.0)
        flags = ClinicalRiskDetector().evaluate(case)
        assert EscalationReason.HIGH_COST not in flags.reasons

    def test_does_not_fire_when_no_cost_anywhere(self) -> None:
        # Negative case: GC-001-style — no cost in notes, no structured field.
        case = _make_case("58-year-old male, stage IV NSCLC, requesting pembrolizumab.")
        flags = ClinicalRiskDetector().evaluate(case)
        assert EscalationReason.HIGH_COST not in flags.reasons


# =============================================================================
# PEDIATRIC_COMPLEX check — structured field path + parser fallback path + negatives
# =============================================================================


class TestPediatricComplexCheck:
    def test_fires_for_severe_pediatric_with_structured_fields(self) -> None:
        case = _make_case(
            "Pediatric patient, severe disease.",
            patient_age=14,
            disease_severity="severe",
        )
        flags = ClinicalRiskDetector().evaluate(case)
        assert EscalationReason.PEDIATRIC_COMPLEX in flags.reasons

    def test_fires_for_severe_pediatric_via_notes_parsing(self) -> None:
        # Parser fallback path — exactly the GC-012 case in production.
        notes = (
            "14-year-old male with severe persistent asthma uncontrolled on "
            "high-dose ICS. 3 ED visits in past year."
        )
        case = _make_case(notes)
        flags = ClinicalRiskDetector().evaluate(case)
        assert EscalationReason.PEDIATRIC_COMPLEX in flags.reasons

    def test_does_not_fire_for_adult_with_severe_disease(self) -> None:
        # Age guard: a 45-year-old with severe disease is NOT pediatric.
        case = _make_case(
            "45-year-old male with severe disease.",
            patient_age=45,
            disease_severity="severe",
        )
        flags = ClinicalRiskDetector().evaluate(case)
        assert EscalationReason.PEDIATRIC_COMPLEX not in flags.reasons

    def test_does_not_fire_for_pediatric_with_mild_disease(self) -> None:
        # Severity guard: a 12-year-old with MILD disease is NOT escalated.
        case = _make_case(
            "12-year-old with mild asthma.",
            patient_age=12,
            disease_severity="mild",
        )
        flags = ClinicalRiskDetector().evaluate(case)
        assert EscalationReason.PEDIATRIC_COMPLEX not in flags.reasons

    def test_does_not_fire_for_18_year_old(self) -> None:
        # Boundary: cutoff is < 18 (strict), so 18 is NOT pediatric.
        case = _make_case(
            "18-year-old with severe disease.",
            patient_age=18,
            disease_severity="severe",
        )
        flags = ClinicalRiskDetector().evaluate(case)
        assert EscalationReason.PEDIATRIC_COMPLEX not in flags.reasons


# =============================================================================
# Integration — confirm the two new checks don't break the existing 4 pre-flights
# =============================================================================


class TestNoRegressionOnExistingChecks:
    def test_experimental_treatment_still_fires(self) -> None:
        # CAR-T procedure code — should still trigger EXPERIMENTAL_TREATMENT.
        case = ClinicalCase(
            patient_id="P",
            primary_diagnosis_code="C83.30",
            procedure_code="Q2041",
            evidence=[
                EvidenceItem(
                    id="e1",
                    source_type=EvidenceSourceType.CLINICAL_NOTE,
                    description="DLBCL",
                    original_text="DLBCL pt",
                    confidence=0.9,
                )
            ],
        )
        flags = ClinicalRiskDetector().evaluate(case)
        assert EscalationReason.EXPERIMENTAL_TREATMENT in flags.reasons

    def test_clean_adult_case_pre_flights_clean(self) -> None:
        # GC-001-style: no triggers expected.
        case = _make_case("58-year-old male, stage IV NSCLC, requesting pembrolizumab.")
        flags = ClinicalRiskDetector().evaluate(case)
        assert flags.should_pre_escalate is False
