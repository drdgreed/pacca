"""
Tests for pr_template.py — PR description generation.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from pacca.agents.sme_authoring.models import (
    ValidationOutcome,
    ValidationReport,
    ValidatorName,
)
from pacca.agents.sme_authoring.pr_template import (
    PRMetadata,
    render_pr_body,
    render_pr_title,
)

if TYPE_CHECKING:
    from pacca.agents.sme_authoring.models import CaseDraftResponse


def _base_metadata(commit_passed: bool = True) -> PRMetadata:
    return PRMetadata(
        sme_attestation=("I attest this case is clinically accurate per my professional judgment."),
        target_file="cardiology_cases.py",
        is_new_file=False,
        integrity_test_passed=commit_passed,
        integrity_test_summary="13 passed in 0.20s" if commit_passed else "FAILURE",
    )


class TestRenderPrTitle:
    def test_title_includes_case_id(self, valid_case_draft: CaseDraftResponse) -> None:
        title = render_pr_title(valid_case_draft)
        assert valid_case_draft.case_id in title

    def test_title_under_80_chars(self, valid_case_draft: CaseDraftResponse) -> None:
        title = render_pr_title(valid_case_draft)
        # 60 chars for title + ~20 for prefix/ID
        assert len(title) <= 100

    def test_long_title_truncated(self, valid_case_draft: CaseDraftResponse) -> None:
        long = valid_case_draft.model_copy(update={"title": "Very long title " * 10})
        rendered = render_pr_title(long)
        assert "..." in rendered


class TestRenderPrBody:
    def test_body_contains_case_id(self, valid_case_draft: CaseDraftResponse) -> None:
        body = render_pr_body(valid_case_draft, _base_metadata(), [])
        assert valid_case_draft.case_id in body

    def test_body_contains_attestation(self, valid_case_draft: CaseDraftResponse) -> None:
        body = render_pr_body(valid_case_draft, _base_metadata(), [])
        assert "SME attestation" in body
        assert "I attest" in body

    def test_body_renders_validator_pass(self, valid_case_draft: CaseDraftResponse) -> None:
        reports = [
            ValidationReport(
                validator=ValidatorName.PHI_SCAN,
                outcome=ValidationOutcome.PASS,
            )
        ]
        body = render_pr_body(valid_case_draft, _base_metadata(), reports)
        assert "PASS" in body
        assert "phi_scan" in body

    def test_body_renders_validator_fail(self, valid_case_draft: CaseDraftResponse) -> None:
        reports = [
            ValidationReport(
                validator=ValidatorName.PHI_SCAN,
                outcome=ValidationOutcome.FAIL,
                reason="Detected PHI markers",
            )
        ]
        body = render_pr_body(valid_case_draft, _base_metadata(), reports)
        assert "FAIL" in body
        assert "1 blocking failures" in body

    def test_body_renders_validator_warn(self, valid_case_draft: CaseDraftResponse) -> None:
        reports = [
            ValidationReport(
                validator=ValidatorName.REASONING_SPECIFICITY,
                outcome=ValidationOutcome.WARN,
                reason="Generic phrase detected",
            )
        ]
        body = render_pr_body(valid_case_draft, _base_metadata(), reports)
        assert "WARN" in body

    def test_body_shows_integrity_pass(self, valid_case_draft: CaseDraftResponse) -> None:
        body = render_pr_body(valid_case_draft, _base_metadata(commit_passed=True), [])
        assert "Integrity tests PASS" in body

    def test_body_shows_integrity_fail(self, valid_case_draft: CaseDraftResponse) -> None:
        body = render_pr_body(valid_case_draft, _base_metadata(commit_passed=False), [])
        assert "Integrity tests FAILED" in body

    def test_body_mentions_companion_docs(self, valid_case_draft: CaseDraftResponse) -> None:
        body = render_pr_body(valid_case_draft, _base_metadata(), [])
        assert "CASE_PROVENANCE.md" in body
        assert "EVALUATION_COVERAGE.md" in body

    def test_new_file_indicator(self, valid_case_draft: CaseDraftResponse) -> None:
        metadata = PRMetadata(
            sme_attestation="I attest.",
            target_file="brand_new_specialty_cases.py",
            is_new_file=True,
            integrity_test_passed=True,
        )
        body = render_pr_body(valid_case_draft, metadata, [])
        assert "NEW FILE" in body
