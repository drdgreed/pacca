"""Orchestrator wiring: triage runs + enriches; degrades gracefully on failure."""

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
async def test_triage_runs_and_enriches_decision_context() -> None:
    orch = Orchestrator()
    orch.evidence_agent.run = AsyncMock(return_value=_evidence())  # type: ignore[method-assign]
    orch.classification_agent.run = AsyncMock(return_value=_classification())  # type: ignore[method-assign]
    orch.decision_agent.run = AsyncMock(return_value=_decision())  # type: ignore[method-assign]

    await orch.process_decision(_ctx())

    orch.evidence_agent.run.assert_awaited_once()
    orch.classification_agent.run.assert_awaited_once()
    passed_ctx = orch.decision_agent.run.call_args.args[0]
    assert passed_ctx.evidence is not None
    assert passed_ctx.classification is not None
    assert passed_ctx.classification.primary_specialty == "oncology"


@pytest.mark.asyncio
async def test_triage_failure_degrades_gracefully() -> None:
    orch = Orchestrator()
    orch.evidence_agent.run = AsyncMock(side_effect=RuntimeError("LLM down"))  # type: ignore[method-assign]
    orch.classification_agent.run = AsyncMock(return_value=_classification())  # type: ignore[method-assign]
    orch.decision_agent.run = AsyncMock(return_value=_decision())  # type: ignore[method-assign]

    result = await orch.process_decision(_ctx())  # must NOT raise

    assert result.status == AuthorizationStatus.AUTO_APPROVED
    passed_ctx = orch.decision_agent.run.call_args.args[0]
    assert passed_ctx.evidence is None
    assert passed_ctx.classification is None
