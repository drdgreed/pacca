"""
Live smoke test for the SME Case Authoring Agent.

This test runs an end-to-end round-trip against the real Anthropic API:
  1. Draft a sentinel case via SMECaseAuthoringAgent.
  2. Validate the draft against all 6 deterministic validators.
  3. Verify integrity-test pre-conditions hold.
  4. Clean up (no actual file mutations — tests cleanly without
     touching the real tests/clinical/ tree).

Marked `@pytest.mark.clinical` so it runs in the nightly CI (where
ANTHROPIC_API_KEY is available) but NOT in fast `make test` runs.

Cost: ~$0.10 per invocation. Runs nightly, not per-PR.

Purpose: catch regressions in the agent's draft format that wouldn't
show up in mocked-LLM unit tests (e.g., the LLM's schema-coercion
breaks under a new model version; the system prompt accidentally
fails to enforce a recognized guideline body; the structured tool-use
output omits a required field).

WHY THE SMOKE TEST DOES NOT MUTATE FILES
========================================

We could test the full write-to-disk pipeline by adding the sentinel
case to a temporary case file, running TestGoldenDatasetIntegrity, and
rolling back. That would test the writers too. But:

  - It requires care to roll back cleanly (a leftover sentinel
    permanently grows the dataset)
  - Integrity-test runs add ~5-10 seconds per test
  - The unit-test suite (test_case_writer / test_provenance_writer /
    test_coverage_updater) already covers the writers deterministically

So this smoke test focuses on the surface the unit tests CANNOT cover:
the LLM call itself.
"""

from __future__ import annotations

import os

import pytest

from pacca.agents.sme_authoring.agent import SMECaseAuthoringAgent
from pacca.agents.sme_authoring.models import CaseDraftRequest, SMEScenario
from pacca.agents.sme_authoring.validators import run_all_validators


@pytest.mark.clinical
@pytest.mark.asyncio
async def test_sme_agent_smoke_round_trip() -> None:
    """
    Sentinel-case draft against the real Anthropic API.

    Verifies:
      - The agent's structured tool-use call succeeds.
      - The draft has all required fields populated.
      - The PHI scan, guideline-citation, schema, and outcome-branch
        consistency validators pass on a deterministic NSCLC scenario.

    Skipped if ANTHROPIC_API_KEY is not set (so the test is safe to
    run in environments without API credentials).
    """
    if not os.getenv("ANTHROPIC_API_KEY"):
        pytest.skip("ANTHROPIC_API_KEY not set; skipping live smoke test")

    agent = SMECaseAuthoringAgent()
    request = CaseDraftRequest(
        scenario=SMEScenario(
            description=(
                "58-year-old male with stage IV metastatic NSCLC, "
                "PD-L1 high expression (70%), no EGFR or ALK alterations, "
                "ECOG 1, no prior systemic therapy, requesting first-line "
                "pembrolizumab monotherapy per NCCN."
            ),
            intended_specialty="oncology",
            intended_outcome="AUTO_APPROVED",
            failure_mode_label="Coverage",
        ),
        allocated_case_id="GC-SMOKE",
        recommended_file="oncology_depth_cases.py",
    )

    # Run the agent (real API call)
    draft = await agent.run(request)

    # Sentinel ID was preserved (the agent's defensive overwrite)
    assert draft.case_id == "GC-SMOKE"

    # Required fields populated
    assert draft.title
    assert draft.clinical_notes
    assert draft.guidelines_context
    assert draft.expected_outcome
    assert draft.expected_branch
    assert len(draft.reasoning_must_include) >= 1
    assert draft.clinical_rationale
    assert draft.judge_scoring_criteria

    # The deterministic validators should run cleanly on the draft.
    # We don't assert all PASS (the LLM may emit a generic phrase that
    # WARNs); we assert no FAIL (blocking).
    reports = run_all_validators(draft)
    blocking = [r for r in reports if r.is_blocking]
    assert not blocking, (
        f"Live LLM draft has blocking validator failures: "
        f"{[(r.validator, r.reason) for r in blocking]}"
    )


@pytest.mark.clinical
def test_sme_agent_prompt_loaded_at_v1_0() -> None:
    """
    Prompt-version drift guard.

    If a future iteration bumps the SME agent's prompt version, this
    test fails — forcing the bump to be intentional + reviewed.
    """
    agent = SMECaseAuthoringAgent()
    # v1.0 is the initial release; PR-2 chg-1
    # If you intentionally bump the prompt, update this assertion in
    # the same PR.
    assert agent.prompt_version == "v1.0", (
        f"Expected SMECaseAuthoringAgent prompt v1.0, got {agent.prompt_version}. "
        "If this is intentional, update this test in the prompt-bump PR."
    )
