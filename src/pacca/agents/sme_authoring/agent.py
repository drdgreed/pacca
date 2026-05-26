"""
SMECaseAuthoringAgent — Claude-powered case drafter.

Inherits BaseAgent (src/pacca/agents/base.py) for retry, OTel tracing,
and forced-tool-use structured output. Subclass contract: name +
system_prompt + run() with a typed Pydantic input/output.

CONTRACT
========

- run(request: CaseDraftRequest) → CaseDraftResponse
- The LLM produces a CaseDraftResponse with every required field
  populated. Placeholder values ("[SME: please specify ...]") are
  permitted in scalar fields when the SME's scenario didn't provide
  enough specifics; the downstream validators flag them.
- case_id and prior_denial_codes come from the request (pre-allocated)
  and are echoed back unchanged.
- The agent does NOT call validators or write files. Composition with
  the rest of the SME-authoring pipeline (validate → route → write) is
  the CLI's job.

INTEGRATION WITH BASEAGENT
==========================

- self.execute(user_input, response_model=CaseDraftResponse) handles
  the API call, retry, tracing, and structured-output parsing.
- self.name = "SMECaseAuthoringAgent" — used in OTel spans + audit logs
- self.system_prompt = the v1.0 prompt from prompts/sme_authoring.py
- prompt_version property exposes the registered version for audit logs.

The pattern matches DecisionSupportAgent (src/pacca/agents/decision.py)
so observability + audit logs treat all agents uniformly.
"""

from __future__ import annotations

from pacca.agents.base import BaseAgent
from pacca.agents.prompts.sme_authoring import (
    SME_AUTHORING_AGENT_NAME,
    get_system_prompt,
)
from pacca.agents.prompts.templates import get_prompt_version
from pacca.agents.sme_authoring.models import (
    CaseDraftRequest,
    CaseDraftResponse,
)


class SMECaseAuthoringAgent(BaseAgent):
    """
    Drafts a CaseDraftResponse from an SME's plain-English scenario.

    Usage:
        agent = SMECaseAuthoringAgent()
        request = CaseDraftRequest(
            scenario=SMEScenario(description="65yo male with stage IV NSCLC..."),
            allocated_case_id="GC-101",
            recommended_file="oncology_depth_cases.py",
        )
        draft = await agent.run(request)
        # Pass draft through validators next.
    """

    @property
    def name(self) -> str:
        return SME_AUTHORING_AGENT_NAME

    @property
    def system_prompt(self) -> str:
        return get_system_prompt()

    @property
    def prompt_version(self) -> str:
        """Current registered prompt version (e.g., 'v1.0')."""
        return get_prompt_version(self.name)

    async def run(self, request: CaseDraftRequest) -> CaseDraftResponse:
        """
        Draft a complete GoldenCase from the SME's scenario.

        The LLM receives:
          - The SME's plain-English description + optional hints
            (intended_specialty, intended_outcome, failure_mode_label).
          - The pre-allocated case_id (must be echoed unchanged).
          - The recommended target file (informational; helps the LLM
            stay consistent with the dataset's organization).
          - The priority gap hint (if any) so the draft addresses the
            highest-value gap per EVALUATION_COVERAGE.md.

        Returns the populated CaseDraftResponse. The CLI's next step is
        to run all six validators against the draft and surface any
        FAIL/WARN to the SME for revision.
        """
        user_input = _build_user_input(request)
        draft = await self.execute(
            user_input=user_input,
            response_model=CaseDraftResponse,
        )
        # Defensively re-set the case_id in case the LLM mutated it (the
        # prompt forbids this but the validator would catch a mismatch
        # anyway; setting here makes the contract explicit).
        return draft.model_copy(update={"case_id": request.allocated_case_id})


def _build_user_input(request: CaseDraftRequest) -> str:
    """
    Render the CaseDraftRequest as the user-turn prompt sent to Claude.

    Structure:
      ## Pre-allocated metadata    (fields the LLM must echo)
      ## SME scenario              (the clinician's free-text description + hints)
      ## Gap-closure hint          (optional, from gap_analyzer)
      ## Drafting task             (concise instruction)
    """
    scenario = request.scenario
    hints: list[str] = []
    if scenario.intended_specialty:
        hints.append(f"- intended_specialty: {scenario.intended_specialty}")
    if scenario.intended_outcome:
        hints.append(f"- intended_outcome: {scenario.intended_outcome}")
    if scenario.failure_mode_label:
        hints.append(f"- failure_mode_label: {scenario.failure_mode_label}")
    hints_block = "\n".join(hints) if hints else "(no additional hints)"

    gap_block = (
        f"## Priority gap hint\n{request.priority_gap_hint}\n\n"
        if request.priority_gap_hint
        else ""
    )

    return (
        "## Pre-allocated metadata (echo unchanged)\n"
        f"- case_id: {request.allocated_case_id}\n"
        f"- recommended_file: {request.recommended_file}\n\n"
        "## SME scenario\n"
        f"{scenario.description}\n\n"
        "### SME hints\n"
        f"{hints_block}\n\n"
        f"{gap_block}"
        "## Drafting task\n"
        "Produce a complete CaseDraftResponse populating every required "
        "field per the system-prompt rules. Use synthetic data only "
        "(no PHI). Cite a recognized guideline body in guidelines_context. "
        "Ensure expected_outcome and expected_branch are consistent. Use "
        "specific clinical phrases for reasoning_must_include. Write a "
        "2-5 sentence clinical_rationale and a case-specific "
        "judge_scoring_criteria.\n"
    )
