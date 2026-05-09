"""
Tests for Week 5: Prompt engineering, version control, and EvolutionAgent governance.

Covers:
  1. Prompt registry completeness and version format
  2. All agents reference the registry (no hardcoded version strings)
  3. CLINICAL_SAFETY_GUIDELINES is included in all agent system prompts
  4. MedicalDirectorAgent prompt contains required structural elements
  5. EvolutionAgent produces proposals (not deployments)
  6. Governance pipeline: propose → approve → change log
  7. Governance pipeline: propose → reject → no deployment
  8. Duplicate approval is rejected
  9. Rejection is rejected if not pending

Teaching note — testing prompts:

  Prompt quality is hard to test automatically. What we CAN test:
    - Structural presence: does the prompt contain the required sections?
    - Version tracking: is every agent registered with a version?
    - Safety inclusion: does every agent have the anti-hallucination guidelines?
    - Governance contracts: does the EvolutionAgent output go to a store, not ChromaDB?

  These are necessary but not sufficient tests. The LLM-as-judge in
  tests/clinical/ tests whether the QUALITY of reasoning is correct.
  These tests ensure the STRUCTURE is correct.
"""

from unittest.mock import AsyncMock, patch

import pytest

# =============================================================================
# Prompt registry and version control tests
# =============================================================================


class TestPromptRegistry:
    """Verify the prompt version registry is complete and well-formed."""

    def test_registry_covers_all_agents(self):
        """
        Every agent class must be registered in PROMPT_REGISTRY.

        If an agent is not in the registry, its prompt version is
        'unknown' — which means it cannot be traced in audit logs.
        """
        from pacca.agents.prompts.templates import PROMPT_REGISTRY

        required_agents = {
            "DecisionSupportAgent",
            "MedicalDirectorAgent",
            "EvidenceAggregationAgent",
            "ClinicalClassificationAgent",
            "PolicyEvolutionAgent",
        }

        missing = required_agents - set(PROMPT_REGISTRY.keys())
        assert not missing, (
            f"Agents missing from PROMPT_REGISTRY: {missing}. "
            "Every agent must have a registered prompt version for audit trail."
        )

    def test_registry_versions_follow_format(self):
        """Versions must follow 'vMAJOR.MINOR' format (e.g. 'v2.1')."""
        import re

        from pacca.agents.prompts.templates import PROMPT_REGISTRY

        version_pattern = re.compile(r"^v\d+\.\d+$")
        for agent_name, entry in PROMPT_REGISTRY.items():
            version = entry.get("version", "")
            assert version_pattern.match(version), (
                f"Agent '{agent_name}' has invalid version format '{version}'. "
                f"Must match 'vX.Y' (e.g. 'v2.2')."
            )

    def test_registry_entries_have_required_fields(self):
        """Each registry entry must have version, description, and changed_in."""
        from pacca.agents.prompts.templates import PROMPT_REGISTRY

        required_fields = {"version", "description", "changed_in"}
        for agent_name, entry in PROMPT_REGISTRY.items():
            missing = required_fields - set(entry.keys())
            assert not missing, f"PROMPT_REGISTRY['{agent_name}'] missing fields: {missing}"

    def test_get_prompt_version_returns_known_agents(self):
        """get_prompt_version() must return actual version, not 'unknown'."""
        from pacca.agents.prompts.templates import get_prompt_version

        agents = [
            "DecisionSupportAgent",
            "MedicalDirectorAgent",
            "PolicyEvolutionAgent",
        ]
        for agent in agents:
            version = get_prompt_version(agent)
            assert version != "unknown", (
                f"get_prompt_version('{agent}') returned 'unknown'. "
                f"Agent must be registered in PROMPT_REGISTRY."
            )

    def test_get_prompt_version_unknown_for_unregistered(self):
        """get_prompt_version() returns 'unknown' for unregistered agents."""
        from pacca.agents.prompts.templates import get_prompt_version

        assert get_prompt_version("NonExistentAgent") == "unknown"


# =============================================================================
# Prompt content / structure tests
# =============================================================================


class TestPromptContent:
    """Verify prompt content contains required structural elements."""

    def test_all_agent_prompts_include_safety_guidelines(self):
        """
        Every agent system prompt must include CLINICAL_SAFETY_GUIDELINES.

        The anti-hallucination instruction 'Never hallucinate clinical information'
        must be present in every agent's system prompt. This is the foundational
        patient safety requirement.
        """
        from pacca.agents.prompts.templates import (
            CLASSIFICATION_AGENT_SYSTEM,
            DECISION_AGENT_SYSTEM,
            EVIDENCE_AGENT_SYSTEM,
            EVOLUTION_AGENT_SYSTEM,
            MEDICAL_DIRECTOR_AGENT_SYSTEM,
        )

        prompts = {
            "DecisionSupportAgent": DECISION_AGENT_SYSTEM,
            "MedicalDirectorAgent": MEDICAL_DIRECTOR_AGENT_SYSTEM,
            "EvidenceAggregationAgent": EVIDENCE_AGENT_SYSTEM,
            "ClinicalClassificationAgent": CLASSIFICATION_AGENT_SYSTEM,
            "PolicyEvolutionAgent": EVOLUTION_AGENT_SYSTEM,
        }

        # The core anti-hallucination instruction must be in every prompt
        anti_hallucination_marker = "Never hallucinate clinical information"

        for agent_name, prompt in prompts.items():
            assert anti_hallucination_marker in prompt, (
                f"Agent '{agent_name}' system prompt is missing the anti-hallucination "
                f"safety guideline. Every agent must include CLINICAL_SAFETY_GUIDELINES. "
                f"This is a patient safety requirement."
            )

    def test_medical_director_prompt_addresses_tier1_uncertainty(self):
        """
        The MedicalDirectorAgent prompt must instruct the model to address
        the Tier 1 agent's specific uncertainty.

        Without this, the MD Agent tends to re-evaluate from scratch rather
        than resolving the specific ambiguity that triggered escalation.
        """
        from pacca.agents.prompts.templates import MEDICAL_DIRECTOR_AGENT_SYSTEM

        required_phrases = [
            "Tier 1",
            "uncertainty",
            "override",
        ]
        for phrase in required_phrases:
            assert phrase.lower() in MEDICAL_DIRECTOR_AGENT_SYSTEM.lower(), (
                f"MedicalDirectorAgent prompt missing '{phrase}'. "
                f"The MD prompt must frame the task as resolving Tier 1 uncertainty."
            )

    def test_medical_director_prompt_has_confidence_rubric(self):
        """
        The MD Agent prompt must include explicit confidence scoring rules.
        Without a rubric, confidence scores are inconsistent across cases.
        """
        from pacca.agents.prompts.templates import MEDICAL_DIRECTOR_AGENT_SYSTEM

        assert "0.95" in MEDICAL_DIRECTOR_AGENT_SYSTEM, (
            "MedicalDirectorAgent prompt missing confidence threshold '0.95'. "
            "The MD agent needs explicit scoring rules, not just 'high confidence'."
        )

    def test_medical_director_prompt_defines_scope_limits(self):
        """
        The MD Agent prompt must define what it does NOT have authority over.
        Without this, it may attempt to override pre-flight escalation triggers.
        """
        from pacca.agents.prompts.templates import MEDICAL_DIRECTOR_AGENT_SYSTEM

        assert "do NOT have the authority" in MEDICAL_DIRECTOR_AGENT_SYSTEM, (
            "MedicalDirectorAgent prompt must define scope limits — "
            "what the MD Agent cannot override (pre-flight triggers)."
        )

    def test_evolution_agent_prompt_prohibits_auto_deploy(self):
        """
        The EvolutionAgent prompt must state that it produces PROPOSALS,
        not deployments. The word 'deploy' or 'auto_deploy' must not
        appear in an autonomous deployment context.
        """
        from pacca.agents.prompts.templates import EVOLUTION_AGENT_SYSTEM

        assert (
            "PROPOSALS" in EVOLUTION_AGENT_SYSTEM or "proposals" in EVOLUTION_AGENT_SYSTEM.lower()
        ), "EvolutionAgent prompt must state that it produces proposals, not deployments."
        assert "human approval" in EVOLUTION_AGENT_SYSTEM.lower(), (
            "EvolutionAgent prompt must reference human approval requirement."
        )

    def test_decision_agent_prompt_includes_precedent_weighting(self):
        """
        The Decision Agent prompt must instruct the model to weigh precedents
        from the 'PAST MEDICAL DIRECTOR DECISIONS' section in guidelines.
        This is the mechanism for institutional memory to affect decisions.
        """
        from pacca.agents.prompts.templates import DECISION_AGENT_SYSTEM

        assert (
            "precedent" in DECISION_AGENT_SYSTEM.lower()
            or "PAST MEDICAL DIRECTOR" in DECISION_AGENT_SYSTEM
        ), (
            "DecisionSupportAgent prompt must reference precedent weighting. "
            "The institutional memory feature requires the agent to act on it."
        )

    def test_prompts_include_version_string(self):
        """
        Each agent prompt must embed its version string.
        This is what appears in audit logs and OTel spans.
        """
        from pacca.agents.prompts.templates import (
            DECISION_AGENT_SYSTEM,
            MEDICAL_DIRECTOR_AGENT_SYSTEM,
            PROMPT_REGISTRY,
        )

        prompts_and_agents = [
            ("DecisionSupportAgent", DECISION_AGENT_SYSTEM),
            ("MedicalDirectorAgent", MEDICAL_DIRECTOR_AGENT_SYSTEM),
        ]

        for agent_name, prompt in prompts_and_agents:
            version = PROMPT_REGISTRY[agent_name]["version"]
            assert version in prompt, (
                f"Agent '{agent_name}' system prompt does not contain its version "
                f"string '{version}'. The version must be embedded in the prompt "
                f"for audit trail purposes."
            )


# =============================================================================
# EvolutionAgent governance tests
# =============================================================================


class TestEvolutionAgentGovernance:
    """
    Verify the EvolutionAgent governance pipeline works correctly.

    These tests use mocked LLM calls to test governance logic
    without making real API calls.
    """

    def make_mock_proposal(self):
        """Build a mock PolicyProposal for testing."""
        from pacca.agents.evolution import PolicyProposal

        return PolicyProposal(
            original_guideline_id="TEST-GUIDELINE-001",
            proposed_text="Amended: Allow MRI after 3 weeks if motor weakness documented.",
            reasoning="10 consistent overrides approve MRI for motor weakness < 6 weeks.",
            override_pattern="All 10 overrides: motor weakness present, approved MRI.",
            confidence=0.95,
            scope_boundaries="Only applies when motor weakness >= grade 3 is documented.",
            reviewer_checklist=[
                "Verify motor weakness grading criteria are clear",
                "Confirm this does not conflict with other LCD criteria",
            ],
        )

    def setup_method(self):
        """Clear proposal and change log stores before each test."""
        import pacca.agents.evolution as evo_module

        evo_module._proposal_store.clear()
        evo_module._change_log.clear()

    @pytest.mark.asyncio
    async def test_evolution_agent_creates_pending_proposal(self):
        """
        EvolutionAgent.run() must create a ProposalRecord with status='pending'.
        It must NOT auto-deploy anything.
        """
        from pacca.agents.evolution import EvolutionAgent, get_pending_proposals

        agent = EvolutionAgent()

        # Mock the LLM call to return our test proposal
        with patch.object(
            agent,
            "execute",
            new_callable=AsyncMock,
            return_value=self.make_mock_proposal(),
        ):
            record = await agent.run(
                original_guideline="6 weeks conservative therapy required.",
                overrides=["Override: Motor weakness approved."] * 10,
                guideline_id="TEST-001",
            )

        assert record.status == "pending", (
            "EvolutionAgent.run() must create a proposal with status='pending'. "
            "The agent cannot deploy — only human approval can change status."
        )
        pending = get_pending_proposals()
        assert len(pending) == 1
        assert pending[0].proposal_id == record.proposal_id

    @pytest.mark.asyncio
    async def test_proposal_not_deployed_until_approved(self):
        """
        Nothing should be written to ChromaDB when a proposal is created.
        ChromaDB writes only happen after explicit human approval.
        """
        from pacca.agents.evolution import EvolutionAgent

        agent = EvolutionAgent()

        with (
            patch.object(
                agent,
                "execute",
                new_callable=AsyncMock,
                return_value=self.make_mock_proposal(),
            ),
            patch("pacca.integrations.vector_store.GuidelineRetriever.add_guideline") as mock_add,
        ):
            await agent.run(
                original_guideline="6 weeks required.",
                overrides=["Override."] * 5,
            )

            (
                mock_add.assert_not_called(),
                (
                    "GuidelineRetriever.add_guideline() must NOT be called when a "
                    "proposal is created. ChromaDB writes require human approval."
                ),
            )

    def test_approve_proposal_creates_change_log_entry(self):
        """
        After approving a proposal, the change log must have one entry
        recording the approval with who approved it and when.
        """
        import pacca.agents.evolution as evo_module
        from pacca.agents.evolution import (
            ProposalRecord,
            approve_proposal,
            get_change_log,
        )

        # Manually insert a pending proposal
        proposal = self.make_mock_proposal()
        record = ProposalRecord(
            proposal_id="TEST-PROP-001",
            proposal=proposal,
            status="pending",
        )
        evo_module._proposal_store.append(record)

        # Approve it
        change_entry = approve_proposal(
            proposal_id="TEST-PROP-001",
            approved_by="dr.smith@hospital.org",
            review_notes="Reviewed and approved. Motor weakness criteria are clear.",
            original_guideline_text="6 weeks conservative therapy required.",
        )

        assert change_entry is not None, "approve_proposal() must return a change log entry."
        assert change_entry.approved_by == "dr.smith@hospital.org"
        assert change_entry.proposal_id == "TEST-PROP-001"

        # Change log must contain the entry
        log = get_change_log()
        assert len(log) == 1
        assert log[0].change_id == change_entry.change_id

    def test_approve_changes_proposal_status_to_approved(self):
        """After approval, the proposal status must be 'approved', not 'pending'."""
        import pacca.agents.evolution as evo_module
        from pacca.agents.evolution import ProposalRecord, approve_proposal, get_proposal_by_id

        proposal = self.make_mock_proposal()
        record = ProposalRecord(
            proposal_id="TEST-PROP-002",
            proposal=proposal,
            status="pending",
        )
        evo_module._proposal_store.append(record)

        approve_proposal("TEST-PROP-002", "dr.jones@hospital.org")

        updated = get_proposal_by_id("TEST-PROP-002")
        assert updated.status == "approved"
        assert updated.reviewed_by == "dr.jones@hospital.org"

    def test_reject_proposal_without_deploying(self):
        """
        Rejecting a proposal must set status='rejected' and create NO change log entry.
        """
        import pacca.agents.evolution as evo_module
        from pacca.agents.evolution import ProposalRecord, get_change_log, reject_proposal

        proposal = self.make_mock_proposal()
        record = ProposalRecord(
            proposal_id="TEST-PROP-003",
            proposal=proposal,
            status="pending",
        )
        evo_module._proposal_store.append(record)

        success = reject_proposal(
            "TEST-PROP-003",
            "dr.brown@hospital.org",
            "Insufficient pattern — only 3 consistent overrides, need 5+",
        )

        assert success is True
        assert record.status == "rejected"
        assert record.reviewed_by == "dr.brown@hospital.org"

        # Change log must be empty — rejection does not create a log entry
        assert len(get_change_log()) == 0, (
            "Rejecting a proposal must not create a change log entry. "
            "The change log only records DEPLOYED amendments."
        )

    def test_cannot_approve_already_approved_proposal(self):
        """
        Attempting to approve an already-approved proposal must fail gracefully.
        Proposals can only be approved once — double-approval is a governance error.
        """
        import pacca.agents.evolution as evo_module
        from pacca.agents.evolution import ProposalRecord, approve_proposal

        proposal = self.make_mock_proposal()
        record = ProposalRecord(
            proposal_id="TEST-PROP-004",
            proposal=proposal,
            status="approved",  # Already approved
        )
        evo_module._proposal_store.append(record)

        # Trying to approve an already-approved proposal must return None
        result = approve_proposal("TEST-PROP-004", "dr.second@hospital.org")
        assert result is None, (
            "approve_proposal() must return None for non-pending proposals. "
            "Proposals can only be approved once."
        )

    def test_cannot_reject_already_rejected_proposal(self):
        """Rejecting an already-rejected proposal must fail gracefully."""
        import pacca.agents.evolution as evo_module
        from pacca.agents.evolution import ProposalRecord, reject_proposal

        proposal = self.make_mock_proposal()
        record = ProposalRecord(
            proposal_id="TEST-PROP-005",
            proposal=proposal,
            status="rejected",
        )
        evo_module._proposal_store.append(record)

        result = reject_proposal("TEST-PROP-005", "dr.third@hospital.org")
        assert result is False

    def test_change_log_is_append_only(self):
        """
        The change log must be a permanent record.
        Multiple approvals create multiple entries — none are deleted.
        """
        import pacca.agents.evolution as evo_module
        from pacca.agents.evolution import ProposalRecord, approve_proposal, get_change_log

        # Create and approve three proposals
        for i in range(3):
            proposal = self.make_mock_proposal()
            record = ProposalRecord(
                proposal_id=f"TEST-PROP-{10 + i}",
                proposal=proposal,
                status="pending",
            )
            evo_module._proposal_store.append(record)
            approve_proposal(f"TEST-PROP-{10 + i}", f"dr.reviewer{i}@hospital.org")

        log = get_change_log()
        assert len(log) == 3, (
            f"Expected 3 change log entries, got {len(log)}. "
            "The change log must be append-only — all entries must persist."
        )
