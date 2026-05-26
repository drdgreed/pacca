"""
Unit tests for the six deterministic validators.

Test strategy: each validator has a positive case (the valid_case_draft
fixture passes), plus 2-4 mutation tests that break one field and assert
the corresponding validator fires with the expected outcome.

The run_all_validators aggregator gets its own test confirming it returns
exactly 6 reports in the correct order.
"""

from __future__ import annotations

import pytest

from pacca.agents.sme_authoring.models import (
    CaseDraftResponse,
    ValidationOutcome,
    ValidatorName,
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


def _mutate(case: CaseDraftResponse, **updates: object) -> CaseDraftResponse:
    """Return a copy of `case` with `updates` applied."""
    return case.model_copy(update=updates)


# =============================================================================
# validate_no_phi
# =============================================================================


class TestPhiScan:
    """Validator 1: PHI patterns in clinical_notes."""

    def test_clean_notes_pass(self, valid_case_draft: CaseDraftResponse) -> None:
        report = validate_no_phi(valid_case_draft)
        assert report.outcome == ValidationOutcome.PASS
        assert report.validator == ValidatorName.PHI_SCAN

    @pytest.mark.parametrize(
        "phi_phrase, expected_marker",
        [
            ("Patient SSN 123-45-6789 on file.", "SSN"),
            ("MRN: 99887766 from prior record.", "MRN"),
            ("DOB 5/4/1962 per intake form.", "DOB"),
            ("Contact patient at jdoe@example.com for follow-up.", "email"),
            ("Patient cell 415-555-1234 for callback.", "phone"),
            ("Lives at 123 Main Street, San Francisco.", "street"),
            ("Visit dated 5/4/2022 noted prior therapy.", "specific date"),
            ("Patient John Smith presented with chest pain.", "titled full name"),
        ],
    )
    def test_phi_patterns_fail(
        self,
        valid_case_draft: CaseDraftResponse,
        phi_phrase: str,
        expected_marker: str,
    ) -> None:
        # Need ≥80 chars to satisfy Pydantic min_length on clinical_notes
        notes = (
            phi_phrase + " Otherwise the case has the usual clinical descriptors with "
            "synthesized demographics and a plausible scenario."
        )
        bad_case = _mutate(valid_case_draft, clinical_notes=notes)
        report = validate_no_phi(bad_case)
        assert report.outcome == ValidationOutcome.FAIL
        assert expected_marker.lower() in report.reason.lower()
        assert report.field_path == "clinical_notes"


# =============================================================================
# validate_guideline_citation
# =============================================================================


class TestGuidelineCitation:
    """Validator 2: guidelines_context cites a recognized body."""

    def test_nccn_citation_passes(self, valid_case_draft: CaseDraftResponse) -> None:
        report = validate_guideline_citation(valid_case_draft)
        assert report.outcome == ValidationOutcome.PASS
        assert "NCCN" in report.reason

    def test_multiple_citations_listed(self, valid_case_draft: CaseDraftResponse) -> None:
        # The fixture already cites NCCN + CMS NCD
        report = validate_guideline_citation(valid_case_draft)
        assert "NCCN" in report.reason
        assert "CMS NCD" in report.reason

    def test_no_citation_fails(self, valid_case_draft: CaseDraftResponse) -> None:
        unsupported = _mutate(
            valid_case_draft,
            guidelines_context=(
                "Per institutional policy this treatment is appropriate when "
                "the local committee approves and the local pharmacy stocks "
                "the medication. No external guidelines cited."
            ),
        )
        report = validate_guideline_citation(unsupported)
        assert report.outcome == ValidationOutcome.FAIL
        assert "recognized guideline body" in report.reason

    def test_lowercase_acronym_fails(self, valid_case_draft: CaseDraftResponse) -> None:
        # Case-sensitive: lowercase mention is likely incidental
        unsupported = _mutate(
            valid_case_draft,
            guidelines_context=(
                "Some doctors refer to nccn guidelines colloquially but a "
                "proper citation uses the uppercase acronym. This text "
                "tests that lowercase mentions are not accepted as valid."
            ),
        )
        report = validate_guideline_citation(unsupported)
        assert report.outcome == ValidationOutcome.FAIL

    @pytest.mark.parametrize("body", ["NCCN", "ACR", "AAD", "GINA", "ECCO"])
    def test_all_major_specialty_bodies_recognized(self, body: str) -> None:
        # Sanity: the recognized-body table includes the bodies cited in
        # major specialty cases throughout the existing dataset.
        assert body in RECOGNIZED_GUIDELINE_BODIES


# =============================================================================
# validate_schema_completeness
# =============================================================================


class TestSchemaCompleteness:
    """Validator 3: case_id format + semantic field lengths."""

    def test_valid_case_passes(self, valid_case_draft: CaseDraftResponse) -> None:
        report = validate_schema_completeness(valid_case_draft)
        assert report.outcome == ValidationOutcome.PASS

    @pytest.mark.parametrize(
        "bad_id",
        ["GC-1", "GC-10", "G-100", "GC100", "101", "GC_101"],
    )
    def test_malformed_case_id_fails(
        self, valid_case_draft: CaseDraftResponse, bad_id: str
    ) -> None:
        # Bypass Pydantic's validation by using model_copy
        bad = _mutate(valid_case_draft, case_id=bad_id)
        report = validate_schema_completeness(bad)
        assert report.outcome == ValidationOutcome.FAIL
        assert "case_id" in (report.field_path or "")

    @pytest.mark.parametrize("valid_id", ["GC-100", "GC-101", "GC-999", "GC-1234"])
    def test_well_formed_case_ids_pass(
        self, valid_case_draft: CaseDraftResponse, valid_id: str
    ) -> None:
        good = _mutate(valid_case_draft, case_id=valid_id)
        report = validate_schema_completeness(good)
        assert report.outcome == ValidationOutcome.PASS


# =============================================================================
# validate_outcome_branch_consistency
# =============================================================================


class TestOutcomeBranchConsistency:
    """Validator 4: expected_outcome ↔ expected_branch pair validity."""

    def test_auto_approve_pair_passes(self, valid_case_draft: CaseDraftResponse) -> None:
        # Fixture is AUTO_APPROVED + BRANCH_1
        report = validate_outcome_branch_consistency(valid_case_draft)
        assert report.outcome == ValidationOutcome.PASS

    @pytest.mark.parametrize(
        "outcome, branch",
        [
            ("DENIED", "NONE"),
            ("IN_REVIEW", "BRANCH_2_MEDICAL_DIRECTOR"),
            ("IN_REVIEW", "BRANCH_3_LOW_CONFIDENCE"),
            ("PRE_FLIGHT_ESCALATE", "BRANCH_4_EXPERIMENTAL"),
            ("PRE_FLIGHT_ESCALATE", "BRANCH_5_RARE"),
            ("PRE_FLIGHT_ESCALATE", "BRANCH_6_CONFLICTING"),
            ("PRE_FLIGHT_ESCALATE", "BRANCH_7_PRIOR_DENIAL"),
            ("INFORMATION_NEEDED", "BRANCH_3_LOW_CONFIDENCE"),
        ],
    )
    def test_valid_pairs_pass(
        self,
        valid_case_draft: CaseDraftResponse,
        outcome: str,
        branch: str,
    ) -> None:
        case = _mutate(valid_case_draft, expected_outcome=outcome, expected_branch=branch)
        report = validate_outcome_branch_consistency(case)
        assert report.outcome == ValidationOutcome.PASS

    @pytest.mark.parametrize(
        "outcome, branch",
        [
            # AUTO_APPROVED with non-branch_1 → invalid
            ("AUTO_APPROVED", "BRANCH_2_MEDICAL_DIRECTOR"),
            ("AUTO_APPROVED", "NONE"),
            # DENIED with a branch → invalid (denials do not escalate)
            ("DENIED", "BRANCH_1_AUTO_APPROVE"),
            ("DENIED", "BRANCH_2_MEDICAL_DIRECTOR"),
            # PRE_FLIGHT with branch_1 or branch_2/3 → invalid
            ("PRE_FLIGHT_ESCALATE", "BRANCH_1_AUTO_APPROVE"),
            ("PRE_FLIGHT_ESCALATE", "BRANCH_2_MEDICAL_DIRECTOR"),
        ],
    )
    def test_invalid_pairs_fail(
        self,
        valid_case_draft: CaseDraftResponse,
        outcome: str,
        branch: str,
    ) -> None:
        case = _mutate(valid_case_draft, expected_outcome=outcome, expected_branch=branch)
        report = validate_outcome_branch_consistency(case)
        assert report.outcome == ValidationOutcome.FAIL

    def test_unknown_outcome_fails(self, valid_case_draft: CaseDraftResponse) -> None:
        case = _mutate(valid_case_draft, expected_outcome="MAYBE")
        report = validate_outcome_branch_consistency(case)
        assert report.outcome == ValidationOutcome.FAIL
        assert "not a recognized outcome" in report.reason


# =============================================================================
# validate_reasoning_specificity
# =============================================================================


class TestReasoningSpecificity:
    """Validator 5: reasoning_must_include is non-generic."""

    def test_specific_phrases_pass(self, valid_case_draft: CaseDraftResponse) -> None:
        report = validate_reasoning_specificity(valid_case_draft)
        assert report.outcome == ValidationOutcome.PASS

    @pytest.mark.parametrize(
        "generic_phrase",
        ["approved", "denied", "review", "appropriate", "ok"],
    )
    def test_generic_single_word_warns(
        self,
        valid_case_draft: CaseDraftResponse,
        generic_phrase: str,
    ) -> None:
        case = _mutate(valid_case_draft, reasoning_must_include=[generic_phrase])
        report = validate_reasoning_specificity(case)
        assert report.outcome == ValidationOutcome.WARN
        assert generic_phrase in report.reason

    def test_mixed_generic_and_specific_still_warns(
        self, valid_case_draft: CaseDraftResponse
    ) -> None:
        case = _mutate(
            valid_case_draft,
            reasoning_must_include=["NCCN Category 1", "approved"],
        )
        report = validate_reasoning_specificity(case)
        assert report.outcome == ValidationOutcome.WARN


# =============================================================================
# validate_judge_criteria_specificity
# =============================================================================


class TestJudgeCriteriaSpecificity:
    """Validator 6: judge_scoring_criteria is not the fallback rubric."""

    def test_specific_criteria_pass(self, valid_case_draft: CaseDraftResponse) -> None:
        report = validate_judge_criteria_specificity(valid_case_draft)
        assert report.outcome == ValidationOutcome.PASS

    @pytest.mark.parametrize(
        "generic_template",
        [
            (
                "Score highly if the rationale is correct and complete. "
                "Penalize for incorrect or incomplete reasoning."
            ),
            (
                "Evaluate the rationale for accuracy and clinical "
                "appropriateness using standard criteria."
            ),
            ("Judge based on standard criteria for clinical decision-making appropriateness."),
            ("Use default rubric to score this case from 1 through 5."),
            ("Score 1-5 based on quality of the agent's reasoning and clinical appropriateness."),
        ],
    )
    def test_generic_templates_warn(
        self,
        valid_case_draft: CaseDraftResponse,
        generic_template: str,
    ) -> None:
        case = _mutate(valid_case_draft, judge_scoring_criteria=generic_template)
        report = validate_judge_criteria_specificity(case)
        assert report.outcome == ValidationOutcome.WARN


# =============================================================================
# run_all_validators
# =============================================================================


class TestRunAllValidators:
    """The aggregator runs all six and returns them in stable order."""

    def test_returns_six_reports(self, valid_case_draft: CaseDraftResponse) -> None:
        reports = run_all_validators(valid_case_draft)
        assert len(reports) == 6

    def test_validator_order_is_stable(self, valid_case_draft: CaseDraftResponse) -> None:
        # Stability: same input → same order. Important for diff-friendly
        # output and for telemetry comparison across runs.
        reports = run_all_validators(valid_case_draft)
        names = [r.validator for r in reports]
        assert names == [
            ValidatorName.PHI_SCAN,
            ValidatorName.GUIDELINE_CITATION,
            ValidatorName.SCHEMA_COMPLETENESS,
            ValidatorName.OUTCOME_BRANCH_CONSISTENCY,
            ValidatorName.REASONING_SPECIFICITY,
            ValidatorName.JUDGE_CRITERIA_SPECIFICITY,
        ]

    def test_valid_case_no_blocking_failures(self, valid_case_draft: CaseDraftResponse) -> None:
        reports = run_all_validators(valid_case_draft)
        blocking = [r for r in reports if r.is_blocking]
        assert blocking == [], f"Valid case should have no blocking failures; got: {blocking}"

    def test_phi_failure_is_blocking_others_continue(
        self, valid_case_draft: CaseDraftResponse
    ) -> None:
        # Insert PHI into clinical_notes; verify PHI scan blocks and other
        # validators still ran (we report all six, not short-circuit on first
        # failure).
        bad = _mutate(
            valid_case_draft,
            clinical_notes=(
                "Patient SSN 111-22-3333 with stage IV NSCLC and PD-L1 high. "
                "Otherwise the case meets NCCN criteria for first-line "
                "pembrolizumab monotherapy in metastatic disease."
            ),
        )
        reports = run_all_validators(bad)
        assert len(reports) == 6

        phi = next(r for r in reports if r.validator == ValidatorName.PHI_SCAN)
        assert phi.outcome == ValidationOutcome.FAIL
        assert phi.is_blocking

        # The other validators should still have produced reports (no exception)
        guideline = next(r for r in reports if r.validator == ValidatorName.GUIDELINE_CITATION)
        assert guideline.outcome == ValidationOutcome.PASS
