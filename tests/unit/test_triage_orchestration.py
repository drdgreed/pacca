"""Orchestrator wiring: triage runs for audit/routing but does NOT enrich the
Tier-1 decision (ADR-020); degrades gracefully on failure."""

from unittest.mock import AsyncMock

import pytest

from pacca.agents.decision import DecisionContext
from pacca.agents.orchestrator import Orchestrator
from pacca.models import ClassificationOutput, EvidenceOutput, UrgencyLevel
from pacca.models.authorization import AuthorizationDecision
from pacca.models.enums import AuthorizationStatus

# Reuse the existing escalation-tree factories so ClinicalCase / AuthorizationDecision
# are constructed exactly as the current models require (no guessing constructors).
from tests.unit.test_escalation_tree import make_case, make_decision


def _ctx() -> DecisionContext:
    return DecisionContext(
        case=make_case(), relevant_guidelines=""
    )  # make_case() clears pre-flight


def _decision() -> AuthorizationDecision:
    return make_decision(status=AuthorizationStatus.AUTO_APPROVED, confidence=0.97)


def _evidence() -> EvidenceOutput:
    return EvidenceOutput(
        clinical_narrative="n", key_findings=[], evidence_gaps=[], confidence_score=0.9
    )


def _classification() -> ClassificationOutput:
    return ClassificationOutput(
        complexity=2,
        complexity_factors=[],
        primary_specialty="oncology",
        urgency=UrgencyLevel.ROUTINE,
        routing_rationale="r",
        confidence_score=0.9,
    )


@pytest.mark.asyncio
async def test_triage_runs_but_does_not_enrich_the_decision() -> None:
    """Decouple guard (ADR-020): triage still runs — its output feeds the audit
    trail and routing/queue — but the Tier-1 DecisionAgent must receive the
    ORIGINAL, un-enriched context. Locks in the GC-020 fix: routing-severity
    signals must not bias the approve/escalate decision."""
    orch = Orchestrator()
    orch.evidence_agent.run = AsyncMock(return_value=_evidence())  # type: ignore[method-assign]
    orch.classification_agent.run = AsyncMock(return_value=_classification())  # type: ignore[method-assign]
    orch.decision_agent.run = AsyncMock(return_value=_decision())  # type: ignore[method-assign]

    ctx = _ctx()
    await orch.process_decision(ctx)

    # Triage ran (captured in the audit trail / available for routing)...
    orch.evidence_agent.run.assert_awaited_once()
    orch.classification_agent.run.assert_awaited_once()
    # ...but the DecisionAgent got the original context object — no enrichment.
    passed_ctx = orch.decision_agent.run.call_args.args[0]
    assert passed_ctx is ctx


@pytest.mark.asyncio
async def test_triage_failure_does_not_break_the_decision() -> None:
    orch = Orchestrator()
    orch.evidence_agent.run = AsyncMock(side_effect=RuntimeError("LLM down"))  # type: ignore[method-assign]
    orch.classification_agent.run = AsyncMock(return_value=_classification())  # type: ignore[method-assign]
    orch.decision_agent.run = AsyncMock(return_value=_decision())  # type: ignore[method-assign]

    result = await orch.process_decision(_ctx())  # must NOT raise

    # The decision proceeds normally even when triage errors out.
    assert result.status == AuthorizationStatus.AUTO_APPROVED
    orch.decision_agent.run.assert_awaited_once()
