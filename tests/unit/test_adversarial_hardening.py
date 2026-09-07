"""
Regression tests for the iter-28 adversarial findings.

Each class pins ONE finding and is written to fail against the pre-fix code.
Where a finding did not survive verification as originally reported, the test
pins what is actually true instead of the claim -- a test asserting a defect
that does not exist is worse than no test, because it teaches the next reader
the wrong threat model.
"""

from __future__ import annotations

import ast

import pytest
from pydantic import ValidationError

from pacca.agents.orchestrator import select_confidence_branch
from pacca.agents.sme_authoring.case_writer import _escape_for_python_string
from pacca.api.routes.admin import ApprovalRequest
from pacca.models.authorization import AuthorizationDecision, DecisionDraft, ReviewTier
from pacca.models.enums import AuthorizationStatus

# ─────────────────────────────────────────────────────────────────────────────
# Finding 1 — unbounded confidence_score
# ─────────────────────────────────────────────────────────────────────────────


class TestConfidenceScoreIsBounded:
    """
    An unbounded confidence let the model widen its own autonomy.

    select_confidence_branch grants auto-approval on `confidence >= threshold`,
    so ANY value above the threshold auto-approves and float("inf") does so
    unconditionally. Pre-fix, DecisionDraft accepted inf, nan, 1e9 and -5.0.
    """

    @pytest.mark.parametrize(
        "bad",
        [float("inf"), float("-inf"), float("nan"), 1e9, 2.0, -5.0, -0.001, 1.001],
    )
    def test_draft_rejects_out_of_range_confidence(self, bad: float) -> None:
        with pytest.raises(ValidationError):
            DecisionDraft(
                status=AuthorizationStatus.AUTO_APPROVED,
                confidence_score=bad,
                rationale="x",
            )

    @pytest.mark.parametrize("bad", [float("inf"), float("nan"), 1e9, -5.0])
    def test_persisted_decision_rejects_out_of_range_confidence(self, bad: float) -> None:
        with pytest.raises(ValidationError):
            AuthorizationDecision(
                status=AuthorizationStatus.AUTO_APPROVED,
                confidence_score=bad,
                rationale="x",
                review_tier_used=ReviewTier.AUTOMATED,
                model_id="claude-test",
                prompt_version="v1",
            )

    @pytest.mark.parametrize("good", [0.0, 0.5, 1.0])
    def test_in_range_confidence_still_accepted(self, good: float) -> None:
        """The bound must not narrow the legitimate range, endpoints included."""
        assert (
            DecisionDraft(
                status=AuthorizationStatus.AUTO_APPROVED,
                confidence_score=good,
                rationale="x",
            ).confidence_score
            == good
        )

    def test_the_routing_consequence_that_made_this_matter(self) -> None:
        """
        Why the bound is on the model and not only on the branch.

        This documents the pre-fix exploit: the routing function itself is a
        pure comparison and still says "auto_approve" for inf. It is correct
        for every value the schema can now produce -- which is the point. The
        schema is the mechanism that refuses; the branch is not.
        """
        assert (
            select_confidence_branch(float("inf"), AuthorizationStatus.AUTO_APPROVED, 0.9, 0.6)
            == "auto_approve"
        )
        # ...and the schema is now what prevents inf from ever reaching it.
        with pytest.raises(ValidationError):
            DecisionDraft(
                status=AuthorizationStatus.AUTO_APPROVED,
                confidence_score=float("inf"),
                rationale="x",
            )


# ─────────────────────────────────────────────────────────────────────────────
# Finding 2 — GOV-05, an approval attributed to nobody
# ─────────────────────────────────────────────────────────────────────────────


class TestApprovalIdentifiesAReviewer:
    """approve_proposal writes reviewer_id into the immutable change log and
    stamps it on the deployed guideline. Blank means an unattributed clinical
    policy amendment."""

    @pytest.mark.parametrize("blank", ["", " ", "   ", "\t", "\n", " \t\n "])
    def test_blank_reviewer_id_rejected(self, blank: str) -> None:
        with pytest.raises(ValidationError):
            ApprovalRequest(reviewer_id=blank)

    def test_overlong_reviewer_id_rejected_before_the_database_sees_it(self) -> None:
        """HumanReview.reviewer_id is String(50). Without max_length this
        truncates on SQLite and raises DataError on PostgreSQL -- caught in
        production, not in CI."""
        with pytest.raises(ValidationError):
            ApprovalRequest(reviewer_id="a" * 51)

    def test_reviewer_id_is_stored_stripped(self) -> None:
        assert ApprovalRequest(reviewer_id="  md.chen  ").reviewer_id == "md.chen"

    def test_real_reviewer_id_still_accepted(self) -> None:
        assert ApprovalRequest(reviewer_id="md.chen").reviewer_id == "md.chen"


# ─────────────────────────────────────────────────────────────────────────────
# Finding 3 — case_writer escaping
# ─────────────────────────────────────────────────────────────────────────────


class TestGeneratedCaseLiteralsRoundTrip:
    """
    Reported as "code injection". It is not, and the distinction is load-bearing.

    Double-quotes were already escaped, so a model-supplied value could not
    close the literal and append code. What an unescaped newline produced was a
    BROKEN literal, caught by _validate_ast, rolled back, and raised as
    FileSyntaxError. The defect was a failed authoring run, not an executed
    payload. test_quotes_cannot_close_the_literal pins the property that makes
    injection impossible, so a future refactor cannot quietly remove it.
    """

    @pytest.mark.parametrize(
        "value",
        [
            "plain",
            'has "quotes"',
            "has\\backslash",
            "has\nnewline",
            "has\rcarriage return",
            "has\ttab",
            "has\x07bell",
            "has\x00nul",
            'everything "\n\r\t\\ at once',
            "café ✓ — unicode stays intact",
        ],
    )
    def test_escaped_value_round_trips_through_a_python_literal(self, value: str) -> None:
        assert ast.literal_eval(f'"{_escape_for_python_string(value)}"') == value

    def test_quotes_cannot_close_the_literal(self) -> None:
        """The property that makes this an availability bug and not an RCE."""
        hostile = '", evil_kwarg=__import__("os").system("id"), x="'
        literal = f'"{_escape_for_python_string(hostile)}"'
        # It parses, and it parses as ONE string constant -- not as a call.
        parsed = ast.parse(literal, mode="eval")
        assert isinstance(parsed.body, ast.Constant)
        assert parsed.body.value == hostile

    def test_newline_no_longer_produces_a_multi_line_literal(self) -> None:
        """The specific pre-fix failure: the emitted source spanned two lines."""
        assert "\n" not in _escape_for_python_string("a\nb")
