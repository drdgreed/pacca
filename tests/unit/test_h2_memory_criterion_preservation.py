"""
iter-3 chg-2 — H2 institutional memory: criterion-preservation tests.

These are STRUCTURAL tests on the rendered system prompt (the output of
_prompt_loader.load_agent_prompt), not live agent calls. Their purpose is
the H2 analog of iter-1's byte-identity check:

  iter-1's check: every prompt token sent to Claude must match the
  pre-extraction f-string output exactly.

  iter-3's check: when a memory entry compresses a case class, the
  prompt MUST still expose every required criterion the un-compressed
  evaluation would have cited — explicitly — so the agent has no way
  to apply the shortcut without verifying each one.

If a future memory edit removes (or weakens) a required-criterion line,
these tests fail loudly before any live evaluation runs and before any
H2 regression can ship.

No API calls. Pure prompt-rendering assertions.
"""

from __future__ import annotations

from pacca.agents._prompt_loader import load_agent_prompt


class TestMemoryInjection:
    """Verify the memory section is rendered into the Decision agent's prompt."""

    def test_decision_support_prompt_contains_institutional_memory_section(self) -> None:
        rendered = load_agent_prompt("decision_support", "DecisionSupportAgent")
        assert "## Institutional Memory" in rendered

    def test_decision_support_memory_loads_the_nsclc_pembrolizumab_entry(self) -> None:
        rendered = load_agent_prompt("decision_support", "DecisionSupportAgent")
        assert "First-line pembrolizumab for metastatic NSCLC" in rendered

    def test_decision_support_prompt_version_bumped_to_v23(self) -> None:
        """v2.3 is the audit signal that H2 memory was active at decision time."""
        rendered = load_agent_prompt("decision_support", "DecisionSupportAgent")
        assert "Prompt version: v2.3" in rendered


class TestCriterionPreservation:
    """
    Each entry's required criteria must appear in the rendered prompt — verbatim.

    This is the H2 contract. If an edit to long_term_memory.md silently
    drops a criterion line, the agent loses the prompt-level reminder to
    verify it, and the shortcut becomes unsafe. These tests are the
    safety net against that class of edit.
    """

    def test_memory_lists_stage_metastatic_criterion(self) -> None:
        rendered = load_agent_prompt("decision_support", "DecisionSupportAgent")
        assert "Disease stage is metastatic (stage IV)" in rendered

    def test_memory_lists_pdl1_50_percent_criterion(self) -> None:
        rendered = load_agent_prompt("decision_support", "DecisionSupportAgent")
        assert "PD-L1 tumor proportion score (TPS) is **≥ 50%**" in rendered

    def test_memory_lists_no_egfr_criterion(self) -> None:
        rendered = load_agent_prompt("decision_support", "DecisionSupportAgent")
        assert "No** sensitizing EGFR mutations" in rendered

    def test_memory_lists_no_alk_criterion(self) -> None:
        rendered = load_agent_prompt("decision_support", "DecisionSupportAgent")
        assert "No** ALK rearrangements" in rendered

    def test_memory_lists_first_line_criterion(self) -> None:
        rendered = load_agent_prompt("decision_support", "DecisionSupportAgent")
        assert "No** prior systemic therapy" in rendered
        assert "first-line status" in rendered

    def test_memory_lists_ecog_criterion(self) -> None:
        rendered = load_agent_prompt("decision_support", "DecisionSupportAgent")
        assert "ECOG performance status documented" in rendered


class TestAntiPatternsPreserved:
    """
    The anti-patterns are the iter-2-finding-derived discriminations that
    catch GC-021 (PD-L1 45%) and GC-022 (EGFR+). These MUST stay in the
    memory verbatim; otherwise H2 would compress them away and the
    near-miss memory traps would auto-approve.
    """

    def test_anti_pattern_pdl1_below_threshold(self) -> None:
        rendered = load_agent_prompt("decision_support", "DecisionSupportAgent")
        assert "PD-L1 TPS **< 50%**" in rendered
        # Anti-patterns must explicitly route to IN_REVIEW (not DENIED).
        # The exact wording uses "Status: IN_REVIEW" with "(Not DENIED.)"
        # clarification — the GC-021 regression showed this distinction matters.
        assert "**Status: IN_REVIEW.**" in rendered
        assert "(Not DENIED.)" in rendered

    def test_anti_pattern_egfr_mutation(self) -> None:
        rendered = load_agent_prompt("decision_support", "DecisionSupportAgent")
        assert "EGFR sensitizing mutation present" in rendered

    def test_anti_pattern_alk_rearrangement(self) -> None:
        rendered = load_agent_prompt("decision_support", "DecisionSupportAgent")
        assert "ALK rearrangement" in rendered

    def test_anti_pattern_stage_iiia_or_earlier(self) -> None:
        rendered = load_agent_prompt("decision_support", "DecisionSupportAgent")
        assert "Stage IIIA or earlier" in rendered

    def test_anti_pattern_prior_systemic_therapy(self) -> None:
        rendered = load_agent_prompt("decision_support", "DecisionSupportAgent")
        assert "Prior systemic therapy for metastatic disease" in rendered


class TestMemoryIsSupportNotReplacement:
    """
    The H2 design constraint from iter-2/findings/GC-001.md: memory must
    encode FULL criteria sets and must instruct the agent to verify each
    one. These tests enforce that the wording in the rendered prompt is
    "support, not replacement."
    """

    def test_prompt_says_memory_is_support_not_replacement(self) -> None:
        rendered = load_agent_prompt("decision_support", "DecisionSupportAgent")
        # The "support, not replacement" phrase may be split across a line
        # break in the rendered output; assert each half independently and
        # confirm they appear in the right order, close together.
        assert "Memory is support," in rendered
        assert "not replacement" in rendered
        support_pos = rendered.index("Memory is support,")
        replace_pos = rendered.index("not replacement")
        assert replace_pos > support_pos
        assert replace_pos - support_pos < 100, (
            "Memory-as-support phrasing should appear together; "
            "found split too far apart in rendered prompt"
        )

    def test_prompt_requires_rationale_to_cite_each_criterion(self) -> None:
        rendered = load_agent_prompt("decision_support", "DecisionSupportAgent")
        # The "must STILL verify" instruction is in the system_prompt wrapper.
        assert "must STILL verify each required criterion" in rendered
        # The memory entry itself reinforces it.
        assert "Memory is the prompt for thoroughness" in rendered


class TestByteIdentityContractForAgentsWithoutMemory:
    """
    iter-1's byte-identity contract: agents whose prompts haven't been
    modified must render byte-identical output. MedicalDirectorAgent has
    no long_term_memory.md file; its rendered prompt must be unchanged
    from before iter-3 chg-2.
    """

    def test_medical_director_prompt_has_no_institutional_memory_section(self) -> None:
        rendered = load_agent_prompt("medical_director", "MedicalDirectorAgent")
        assert "## Institutional Memory" not in rendered

    def test_medical_director_prompt_has_no_nsclc_pembrolizumab_content(self) -> None:
        rendered = load_agent_prompt("medical_director", "MedicalDirectorAgent")
        assert "First-line pembrolizumab" not in rendered
        assert "PD-L1 TPS" not in rendered

    def test_medical_director_version_unchanged(self) -> None:
        """MD agent version must remain at its pre-iter-3 value."""
        rendered = load_agent_prompt("medical_director", "MedicalDirectorAgent")
        # v2.2 is the pre-iter-3 version per PROMPT_REGISTRY.
        assert "Prompt version: v2.2" in rendered
