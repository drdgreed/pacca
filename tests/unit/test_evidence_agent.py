"""Unit tests for the rewritten EvidenceAggregationAgent."""

from unittest.mock import AsyncMock

import pytest

from pacca.agents.decision import DecisionContext
from pacca.agents.evidence_agent import EvidenceAggregationAgent
from pacca.models import EvidenceOutput
from pacca.models.clinical import ClinicalCase


def _ctx() -> DecisionContext:
    case = ClinicalCase(patient_id="P-TEST", primary_diagnosis_code="C34.1", procedure_code="J9271")
    return DecisionContext(case=case, relevant_guidelines="")


@pytest.mark.asyncio
async def test_run_returns_evidence_output_and_passes_case_to_execute() -> None:
    agent = EvidenceAggregationAgent()
    expected = EvidenceOutput(
        clinical_narrative="58yo NSCLC", key_findings=["a"], evidence_gaps=[], confidence_score=0.9
    )
    agent.execute = AsyncMock(return_value=expected)  # type: ignore[method-assign]

    result = await agent.run(_ctx())

    assert result is expected
    kwargs = agent.execute.call_args.kwargs
    assert kwargs["response_model"] is EvidenceOutput
    assert "C34.1" in kwargs["user_input"]  # the case JSON is in the prompt


def test_agent_identity() -> None:
    agent = EvidenceAggregationAgent()
    assert agent.name == "EvidenceAggregationAgent"
    assert "Evidence" in agent.system_prompt
