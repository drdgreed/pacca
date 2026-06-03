"""Unit tests for the rewritten ClinicalClassificationAgent."""

from unittest.mock import AsyncMock

import pytest

from pacca.agents.classification_agent import ClinicalClassificationAgent
from pacca.agents.decision import DecisionContext
from pacca.models import ClassificationOutput, EvidenceOutput, UrgencyLevel
from pacca.models.clinical import ClinicalCase


def _ctx() -> DecisionContext:
    case = ClinicalCase(patient_id="P-TEST", primary_diagnosis_code="C34.1", procedure_code="J9271")
    return DecisionContext(case=case, relevant_guidelines="")


@pytest.mark.asyncio
async def test_run_returns_classification_and_includes_case_and_evidence() -> None:
    agent = ClinicalClassificationAgent()
    expected = ClassificationOutput(
        complexity=4,
        complexity_factors=["comorbid"],
        primary_specialty="oncology",
        urgency=UrgencyLevel.EXPEDITED,
        routing_rationale="r",
        confidence_score=0.8,
    )
    agent.execute = AsyncMock(return_value=expected)  # type: ignore[method-assign]
    evidence = EvidenceOutput(
        clinical_narrative="stage IV NSCLC narrative",
        key_findings=["PD-L1"],
        evidence_gaps=[],
        confidence_score=0.9,
    )

    result = await agent.run(_ctx(), evidence)

    assert result is expected
    kwargs = agent.execute.call_args.kwargs
    assert kwargs["response_model"] is ClassificationOutput
    assert "C34.1" in kwargs["user_input"]  # case JSON present
    assert "stage IV NSCLC narrative" in kwargs["user_input"]  # evidence narrative present


def test_agent_identity() -> None:
    agent = ClinicalClassificationAgent()
    assert agent.name == "ClinicalClassificationAgent"
    assert "Classification" in agent.system_prompt
