"""Evidence-grounding detector (P-5 / chg-10) — deterministic tests.

The pure function is checked directly; the orchestrator integration confirms an
ungrounded citation is a fail-closed safety short-circuit to human review BEFORE
confidence routing, with the `finding.ungrounded_evidence` audit event, and that
a grounded (or empty) citation set proceeds normally.
"""

from unittest.mock import AsyncMock

import pytest

from pacca.agents.decision import DecisionContext
from pacca.agents.evidence_grounding import unresolved_cited_evidence
from pacca.agents.orchestrator import Orchestrator
from pacca.models import ClassificationOutput, EvidenceOutput, UrgencyLevel
from pacca.models.enums import AuthorizationStatus, ReviewTier

# Reuse the model factories so ClinicalCase / AuthorizationDecision are built
# exactly as the current models require. make_case() has one EvidenceItem id="e1".
from tests.unit.test_escalation_tree import make_case, make_decision


def _decision(cited):
    d = make_decision(status=AuthorizationStatus.AUTO_APPROVED, confidence=0.97)
    d.cited_evidence_ids = cited
    return d


# ── Pure detector ─────────────────────────────────────────────────────────────


def test_unresolved_returns_ids_absent_from_submission():
    case = make_case()  # evidence: EvidenceItem(id="e1")
    d = _decision(["e1", "e99", "e99", "ghost"])
    # De-duplicated, order-preserving; "e1" resolves, the rest do not.
    assert unresolved_cited_evidence(d, case) == ["e99", "ghost"]


def test_fully_grounded_returns_empty():
    assert unresolved_cited_evidence(_decision(["e1"]), make_case()) == []


def test_empty_citations_are_grounded():
    assert unresolved_cited_evidence(_decision([]), make_case()) == []


# ── Orchestrator integration ──────────────────────────────────────────────────


class _CapturingAudit:
    def __init__(self):
        self.calls = []

    async def log(self, **kwargs):
        self.calls.append(kwargs)


def _orch(decision):
    orch = Orchestrator()
    orch.evidence_agent.run = AsyncMock(  # type: ignore[method-assign]
        return_value=EvidenceOutput(
            clinical_narrative="n", key_findings=[], evidence_gaps=[], confidence_score=0.9
        )
    )
    orch.classification_agent.run = AsyncMock(  # type: ignore[method-assign]
        return_value=ClassificationOutput(
            complexity=2,
            complexity_factors=[],
            primary_specialty="oncology",
            urgency=UrgencyLevel.ROUTINE,
            routing_rationale="r",
            confidence_score=0.9,
        )
    )
    orch.decision_agent.run = AsyncMock(return_value=decision)  # type: ignore[method-assign]
    return orch


@pytest.mark.asyncio
async def test_ungrounded_citation_forces_human_review():
    orch = _orch(_decision(["e99"]))  # e99 not in the submission
    audit = _CapturingAudit()
    result = await orch.process_decision(
        DecisionContext(case=make_case(), relevant_guidelines=""), audit=audit
    )
    # Fail-closed to human review, overriding the model's AUTO_APPROVED/0.97.
    assert result.status == AuthorizationStatus.IN_REVIEW
    assert result.review_tier_used == ReviewTier.HUMAN
    actions = [c["action"] for c in audit.calls]
    assert "finding.ungrounded_evidence" in actions
    finding = next(c for c in audit.calls if c["action"] == "finding.ungrounded_evidence")
    assert finding["details"]["unresolved_ids"] == ["e99"]
    assert finding["details"]["escalation_reason"] == "ungrounded_evidence"


@pytest.mark.asyncio
async def test_grounded_citation_proceeds_to_normal_routing():
    orch = _orch(_decision(["e1"]))  # grounded
    audit = _CapturingAudit()
    result = await orch.process_decision(
        DecisionContext(case=make_case(), relevant_guidelines=""), audit=audit
    )
    # High-confidence grounded decision is NOT forced to review by P-5.
    assert result.status == AuthorizationStatus.AUTO_APPROVED
    assert not any(c["action"] == "finding.ungrounded_evidence" for c in audit.calls)
