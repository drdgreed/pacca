"""
Tests for SMECaseAuthoringAgent with a mocked Anthropic client.

Strategy: patch the AsyncAnthropic client at the BaseAgent layer so the
LLM call returns a deterministic response. Verify:
  - The agent inherits BaseAgent correctly (name, system_prompt, prompt_version)
  - run() returns a CaseDraftResponse with the pre-allocated case_id echoed
  - The user input includes the SME scenario + hints
"""

from __future__ import annotations

from typing import TYPE_CHECKING
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

if TYPE_CHECKING:
    from collections.abc import Iterator

from pacca.agents.sme_authoring.agent import (
    SMECaseAuthoringAgent,
    _build_user_input,
)
from pacca.agents.sme_authoring.models import (
    CaseDraftRequest,
    CaseDraftResponse,
    SMEScenario,
)

# Pre-canned LLM response that the mock returns for every call.
_SAMPLE_LLM_DRAFT = {
    "case_id": "GC-999",  # Intentionally wrong; agent must overwrite with allocated_id
    "title": "Mocked NSCLC pembrolizumab case for unit testing",
    "diagnosis_code": "C34.1",
    "diagnosis_description": "Malignant neoplasm of upper lobe, bronchus or lung",
    "procedure_code": "J9271",
    "procedure_description": "Pembrolizumab (Keytruda) injection",
    "clinical_notes": (
        "58-year-old male with stage IV NSCLC, PD-L1 70%, no EGFR/ALK alterations. "
        "ECOG 1. Oncology recommending first-line pembrolizumab monotherapy."
    ),
    "guidelines_context": (
        "NCCN NSCLC Guidelines: pembrolizumab monotherapy is a Category 1 first-line "
        "option for metastatic NSCLC with PD-L1 >= 50% and without targetable driver."
    ),
    "expected_outcome": "AUTO_APPROVED",
    "expected_branch": "BRANCH_1_AUTO_APPROVE",
    "reasoning_must_include": ["NCCN Category 1", "PD-L1", "first-line"],
    "reasoning_must_not_include": [],
    "prior_denial_codes": [],
    "clinical_rationale": (
        "Metastatic NSCLC with high PD-L1, no driver mutations. Pembrolizumab "
        "monotherapy is Category 1. Clean auto-approval."
    ),
    "judge_scoring_criteria": (
        "Score highly if rationale cites PD-L1 percentage, the NCCN Category 1 "
        "designation, and the absence of EGFR/ALK alterations."
    ),
}


@pytest.fixture
def mock_anthropic() -> Iterator[MagicMock]:
    """
    Patch AsyncAnthropic at the BaseAgent module so the agent's API call
    returns a canned response with a tool_use content block.
    """
    # Build a mock response that mimics Anthropic's API shape
    mock_content_block = MagicMock()
    mock_content_block.type = "tool_use"
    mock_content_block.input = _SAMPLE_LLM_DRAFT

    mock_response = MagicMock()
    mock_response.content = [mock_content_block]
    mock_response.usage.input_tokens = 100
    mock_response.usage.output_tokens = 200
    mock_response.usage.cache_creation_input_tokens = 0
    mock_response.usage.cache_read_input_tokens = 0

    mock_client = MagicMock()
    mock_client.messages.create = AsyncMock(return_value=mock_response)

    with patch("pacca.agents.base.AsyncAnthropic", return_value=mock_client):
        yield mock_client


class TestAgentContract:
    def test_agent_name(self) -> None:
        agent = SMECaseAuthoringAgent()
        assert agent.name == "SMECaseAuthoringAgent"

    def test_agent_system_prompt_is_non_empty(self) -> None:
        agent = SMECaseAuthoringAgent()
        assert len(agent.system_prompt) > 100
        # Should mention key rules
        assert "PHI" in agent.system_prompt
        assert "NCCN" in agent.system_prompt
        assert "synthetic" in agent.system_prompt.lower()

    def test_prompt_version_v1_0(self) -> None:
        agent = SMECaseAuthoringAgent()
        assert agent.prompt_version == "v1.0"


class TestBuildUserInput:
    def test_includes_case_id_and_file(self) -> None:
        scenario = SMEScenario(description="Test scenario with enough length for validation.")
        request = CaseDraftRequest(
            scenario=scenario,
            allocated_case_id="GC-101",
            recommended_file="cardiology_cases.py",
        )
        user_input = _build_user_input(request)
        assert "GC-101" in user_input
        assert "cardiology_cases.py" in user_input
        assert "Test scenario" in user_input

    def test_includes_hints_when_present(self) -> None:
        scenario = SMEScenario(
            description="Test scenario with enough length for validation.",
            intended_specialty="cardiology",
            intended_outcome="AUTO_APPROVED",
            failure_mode_label="Coverage",
        )
        request = CaseDraftRequest(
            scenario=scenario,
            allocated_case_id="GC-101",
            recommended_file="cardiology_cases.py",
        )
        user_input = _build_user_input(request)
        assert "intended_specialty: cardiology" in user_input
        assert "intended_outcome: AUTO_APPROVED" in user_input
        assert "failure_mode_label: Coverage" in user_input

    def test_no_hints_section_when_absent(self) -> None:
        scenario = SMEScenario(description="Test scenario with enough length for validation.")
        request = CaseDraftRequest(
            scenario=scenario,
            allocated_case_id="GC-101",
            recommended_file="expansion_cases.py",
        )
        user_input = _build_user_input(request)
        assert "no additional hints" in user_input

    def test_priority_gap_hint_included(self) -> None:
        scenario = SMEScenario(description="Test scenario with enough length for validation.")
        request = CaseDraftRequest(
            scenario=scenario,
            allocated_case_id="GC-101",
            recommended_file="expansion_cases.py",
            priority_gap_hint="DENY-class needs 3 more cases",
        )
        user_input = _build_user_input(request)
        assert "Priority gap hint" in user_input
        assert "DENY-class needs 3 more cases" in user_input


class TestAgentRun:
    @pytest.mark.asyncio
    async def test_run_returns_case_draft_response(self, mock_anthropic: MagicMock) -> None:
        agent = SMECaseAuthoringAgent()
        request = CaseDraftRequest(
            scenario=SMEScenario(
                description=(
                    "Stage IV NSCLC, PD-L1 70%, no EGFR/ALK, requesting first-line pembrolizumab."
                )
            ),
            allocated_case_id="GC-101",
            recommended_file="oncology_depth_cases.py",
        )
        result = await agent.run(request)
        assert isinstance(result, CaseDraftResponse)
        assert result.title == _SAMPLE_LLM_DRAFT["title"]

    @pytest.mark.asyncio
    async def test_run_overwrites_case_id_with_allocated(self, mock_anthropic: MagicMock) -> None:
        """
        The LLM might (incorrectly) emit a different case_id than the
        allocated one. The agent must overwrite to ensure the allocated
        ID wins. This protects against a class of memory-trap failures.
        """
        agent = SMECaseAuthoringAgent()
        request = CaseDraftRequest(
            scenario=SMEScenario(
                description=(
                    "Stage IV NSCLC scenario with enough text content to "
                    "satisfy the description min-length validator."
                )
            ),
            allocated_case_id="GC-101",  # ← what we expect in the output
            recommended_file="oncology_depth_cases.py",
        )
        result = await agent.run(request)
        # Sample LLM draft has case_id="GC-999"; agent should overwrite to GC-101
        assert result.case_id == "GC-101"
        assert _SAMPLE_LLM_DRAFT["case_id"] != "GC-101"  # sanity

    @pytest.mark.asyncio
    async def test_run_calls_anthropic_once(self, mock_anthropic: MagicMock) -> None:
        agent = SMECaseAuthoringAgent()
        request = CaseDraftRequest(
            scenario=SMEScenario(description="Test scenario long enough for validator."),
            allocated_case_id="GC-101",
            recommended_file="expansion_cases.py",
        )
        await agent.run(request)
        mock_anthropic.messages.create.assert_called_once()
