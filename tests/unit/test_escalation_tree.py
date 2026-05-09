"""
Tests for the 7-branch escalation tree — Week 2 implementation.

These tests verify every branch of PRD SS5.4. Each test is named after
the branch it covers so the test suite doubles as executable documentation
of the escalation policy.

Teaching note — test-as-specification:
  Every test here makes a claim about clinical safety behavior. If a future
  developer accidentally removes one of these escalation branches (say, by
  refactoring the orchestrator), the corresponding test will fail loudly.
  Tests are the only machine-enforceable form of specification.

  Notice what each test does NOT do:
  - It does not call the Claude API (too slow, costs money, flaky)
  - It does not write to a database (unnecessary for testing logic)
  - It does not test the agent's clinical reasoning (that's the agent's job)

  It ONLY tests whether the Orchestrator routes correctly given a specific
  input. This is called "behavior testing" — we test the observable outputs
  given controlled inputs.

Teaching note — test structure (AAA pattern):
  Every test follows Arrange / Act / Assert:
    Arrange: set up the inputs (build a ClinicalCase, configure mocks)
    Act:     call the function being tested
    Assert:  verify the output matches the expected behavior

  This structure makes tests readable as documentation. You can read any
  test here and understand the escalation rule it encodes.
"""

from unittest.mock import AsyncMock

import pytest

from pacca.agents.clinical_risk_detector import ClinicalRiskDetector
from pacca.agents.decision import DecisionContext
from pacca.agents.orchestrator import Orchestrator
from pacca.models.authorization import AuthorizationDecision
from pacca.models.clinical import ClinicalCase, EvidenceItem
from pacca.models.enums import (
    AuthorizationStatus,
    EscalationReason,
    EvidenceSourceType,
    ReviewTier,
)

# =============================================================================
# Shared fixtures
# =============================================================================


def make_case(
    procedure_code: str = "J9271",
    diagnosis_code: str = "C34.1",
    evidence_text: str = "Stage IIIA NSCLC, PD-L1 TPS >= 50%",
) -> ClinicalCase:
    """
    Build a minimal ClinicalCase for testing.

    Default values represent a routine oncology case that should NOT
    trigger any pre-flight escalation on its own.
    """
    return ClinicalCase(
        patient_id="P-TEST-001",
        primary_diagnosis_code=diagnosis_code,
        procedure_code=procedure_code,
        evidence=[
            EvidenceItem(
                id="e1",
                source_type=EvidenceSourceType.CLINICAL_NOTE,
                description=evidence_text,
                original_text=evidence_text,
                confidence=0.95,
            )
        ],
    )


def make_decision(
    status: AuthorizationStatus = AuthorizationStatus.AUTO_APPROVED,
    confidence: float = 0.97,
) -> AuthorizationDecision:
    """Build a minimal AuthorizationDecision for mock returns."""
    return AuthorizationDecision(
        decision_id="DEC-TEST-001",
        status=status,
        confidence_score=confidence,
        rationale="Test rationale.",
        review_tier_used=ReviewTier.AUTOMATED,
    )


# =============================================================================
# ClinicalRiskDetector unit tests — each detection method in isolation
# =============================================================================


class TestClinicalRiskDetector:
    """
    Tests for each detection method in ClinicalRiskDetector.

    These test the detector in complete isolation — no Orchestrator,
    no agents, no database. Pure input-output verification.
    """

    def setup_method(self):
        self.detector = ClinicalRiskDetector()

    # ── Branch 4: Experimental treatment ─────────────────────────────────────

    def test_detects_experimental_procedure_code(self):
        """
        Branch 4: A known experimental procedure code triggers escalation.

        Real-world meaning: CAR-T cell therapies (Q2041, Q2042) are only
        FDA-approved for specific indications. Any other use is experimental
        and must not be autonomously approved.
        """
        case = make_case(procedure_code="Q2041")  # Axicabtagene (Yescarta) CAR-T
        flags = self.detector.evaluate(case)

        assert flags.should_pre_escalate, (
            "CAR-T therapy Q2041 is on the experimental procedure list "
            "and must always trigger pre-flight escalation."
        )
        assert EscalationReason.EXPERIMENTAL_TREATMENT in flags.reasons

    def test_detects_experimental_keyword_in_evidence(self):
        """
        Branch 4: Evidence text mentioning 'clinical trial' triggers escalation.

        Real-world meaning: a provider might submit a standard procedure code
        but note in clinical text that the treatment is being used in a trial.
        The keyword scan catches this case.
        """
        case = make_case(
            procedure_code="J9271",  # Standard code — not on experimental list
            evidence_text="Patient enrolled in Phase II clinical trial for combination therapy.",
        )
        flags = self.detector.evaluate(case)

        assert flags.should_pre_escalate
        assert EscalationReason.EXPERIMENTAL_TREATMENT in flags.reasons

    def test_routine_procedure_does_not_trigger_experimental(self):
        """
        Branch 4 negative test: a standard oncology procedure is not flagged.

        J9271 is Pembrolizumab (Keytruda) — FDA-approved for NSCLC.
        It should not trigger experimental treatment escalation.
        """
        case = make_case(
            procedure_code="J9271",
            evidence_text="Standard first-line pembrolizumab therapy for PD-L1 >= 50% NSCLC.",
        )
        flags = self.detector.evaluate(case)

        assert EscalationReason.EXPERIMENTAL_TREATMENT not in flags.reasons

    # ── Branch 5: Rare condition ──────────────────────────────────────────────

    def test_detects_rare_condition_by_icd10_prefix(self):
        """
        Branch 5: A Gaucher disease diagnosis code triggers escalation.

        E75.22 (Gaucher disease) starts with 'E75' which is in
        RARE_CONDITION_ICD10_PREFIXES. This is a lysosomal storage disorder
        affecting roughly 1 in 40,000 people.
        """
        case = make_case(diagnosis_code="E75.22")
        flags = self.detector.evaluate(case)

        assert flags.should_pre_escalate
        assert EscalationReason.RARE_CONDITION in flags.reasons

    def test_detects_huntington_disease(self):
        """
        Branch 5: Huntington disease (G10) is correctly flagged as rare.

        G10 is in RARE_CONDITION_ICD10_PREFIXES. Huntington affects
        roughly 1 in 10,000 people and has limited treatment options.
        """
        case = make_case(diagnosis_code="G10")
        flags = self.detector.evaluate(case)

        assert EscalationReason.RARE_CONDITION in flags.reasons

    def test_common_diagnosis_does_not_trigger_rare_condition(self):
        """
        Branch 5 negative test: common lung cancer code is not flagged.

        C34.1 (NSCLC upper lobe) is not in RARE_CONDITION_ICD10_PREFIXES.
        This is one of the most common cancer diagnoses and should not
        trigger rare condition escalation.
        """
        case = make_case(diagnosis_code="C34.1")
        flags = self.detector.evaluate(case)

        assert EscalationReason.RARE_CONDITION not in flags.reasons

    # ── Branch 6: Conflicting guidelines ─────────────────────────────────────

    def test_detects_conflicting_guidelines(self):
        """
        Branch 6: Guidelines containing both approval and conflict markers trigger escalation.

        Real-world meaning: NCCN might say 'recommended Category 1' for
        one patient profile, while CMS coverage says 'not recommended for
        patients with prior platinum failure'. Both phrases appear in the
        RAG context. A human must resolve which applies.
        """
        conflicting_context = (
            "NCCN Guideline: Pembrolizumab is recommended as Category 1 "
            "for PD-L1 >= 50% NSCLC.\n"
            "CMS Coverage Determination: Treatment is not recommended "
            "for patients with prior platinum-based chemotherapy failure "
            "without documented PD-L1 testing."
        )
        case = make_case()
        flags = self.detector.evaluate(case, guidelines_context=conflicting_context)

        assert flags.should_pre_escalate
        assert EscalationReason.CONFLICTING_GUIDELINES in flags.reasons

    def test_consistent_approval_guidelines_do_not_conflict(self):
        """
        Branch 6 negative test: guidelines that only support the treatment
        should not trigger the conflict check.
        """
        clear_context = (
            "NCCN: Pembrolizumab is recommended and strongly supported "
            "as standard of care for PD-L1 >= 50% NSCLC. "
            "Evidence-based Category 1 recommendation."
        )
        case = make_case()
        flags = self.detector.evaluate(case, guidelines_context=clear_context)

        assert EscalationReason.CONFLICTING_GUIDELINES not in flags.reasons

    def test_empty_guidelines_context_does_not_error(self):
        """
        Branch 6 edge case: empty guidelines context (no RAG results) should
        not trigger the conflict check and must not raise an exception.

        Real-world meaning: ChromaDB returned no results for this query.
        The system should degrade gracefully, not crash.
        """
        case = make_case()
        flags = self.detector.evaluate(case, guidelines_context="")

        assert EscalationReason.CONFLICTING_GUIDELINES not in flags.reasons

    # ── Branch 7: Prior denial on same service ────────────────────────────────

    def test_detects_prior_denial_same_procedure(self):
        """
        Branch 7: A prior denial for the same procedure code triggers escalation.

        Real-world meaning: this patient was previously denied Pembrolizumab
        (J9271). The same code is now being resubmitted. This must go to a
        human reviewer who can see both the original denial and the new submission.
        """
        case = make_case(procedure_code="J9271")
        flags = self.detector.evaluate(
            case,
            prior_denial_codes=["J9271", "99213"],  # J9271 is the current procedure
        )

        assert flags.should_pre_escalate
        assert EscalationReason.PRIOR_DENIAL_SAME_SERVICE in flags.reasons

    def test_prior_denial_different_procedure_does_not_trigger(self):
        """
        Branch 7 negative test: a prior denial for a DIFFERENT procedure
        should not block the current request.

        Real-world meaning: patient was previously denied an MRI (72148)
        but is now requesting Pembrolizumab (J9271). These are unrelated.
        """
        case = make_case(procedure_code="J9271")
        flags = self.detector.evaluate(
            case,
            prior_denial_codes=["72148"],  # Different procedure, different denial
        )

        assert EscalationReason.PRIOR_DENIAL_SAME_SERVICE not in flags.reasons

    def test_no_prior_denials_does_not_trigger(self):
        """
        Branch 7 edge case: no prior denial history should never trigger.
        This is the common case for new patients.
        """
        case = make_case()
        flags = self.detector.evaluate(case, prior_denial_codes=[])

        assert EscalationReason.PRIOR_DENIAL_SAME_SERVICE not in flags.reasons

    # ── Multi-flag tests ──────────────────────────────────────────────────────

    def test_multiple_flags_can_fire_simultaneously(self):
        """
        A case with multiple risk factors should trigger all applicable branches.

        Real-world meaning: a pediatric patient (handled via high-cost/complexity
        in classification) with a CAR-T therapy request AND a prior denial
        should trigger both EXPERIMENTAL_TREATMENT and PRIOR_DENIAL_SAME_SERVICE.
        This test ensures flags accumulate, not that only the first match fires.
        """
        case = make_case(
            procedure_code="Q2041",  # Experimental CAR-T therapy
            diagnosis_code="C91.0",  # Acute lymphoblastic leukemia (pediatric common)
        )
        flags = self.detector.evaluate(
            case,
            prior_denial_codes=["Q2041"],  # Also has a prior denial for same procedure
        )

        assert EscalationReason.EXPERIMENTAL_TREATMENT in flags.reasons
        assert EscalationReason.PRIOR_DENIAL_SAME_SERVICE in flags.reasons
        assert len(flags.reasons) >= 2


# =============================================================================
# Orchestrator integration tests — full 7-branch routing
# =============================================================================


class TestOrchestratorEscalationTree:
    """
    Integration tests for the full Orchestrator escalation logic.

    These tests mock the Decision Agent and Medical Director Agent to
    isolate the Orchestrator's routing logic from actual LLM calls.
    They verify that the correct status is returned for each branch.
    """

    def make_orchestrator_with_mocks(
        self,
        tier1_confidence: float = 0.97,
        tier1_status: AuthorizationStatus = AuthorizationStatus.AUTO_APPROVED,
        tier2_confidence: float = 0.97,
    ):
        """
        Create an Orchestrator with mocked agents.

        Returns:
            Tuple of (orchestrator, mock_decision_agent, mock_md_agent)
        """
        orchestrator = Orchestrator()

        # Mock the Tier 1 agent
        orchestrator.decision_agent.run = AsyncMock(
            return_value=make_decision(
                status=tier1_status,
                confidence=tier1_confidence,
            )
        )

        # Mock the Tier 2 agent
        orchestrator.medical_director_agent.run = AsyncMock(
            return_value=make_decision(
                status=AuthorizationStatus.AUTO_APPROVED,
                confidence=tier2_confidence,
            )
        )

        return orchestrator

    # ── Branch 1: Auto-approve ────────────────────────────────────────────────

    @pytest.mark.asyncio
    async def test_branch1_high_confidence_auto_approves(self):
        """
        Branch 1: confidence >= 0.95 with AUTO_APPROVED status returns immediately.

        The Medical Director Agent must NOT be called — it would be wasteful
        and is unnecessary when the Frontline Agent is highly confident.
        """
        orchestrator = self.make_orchestrator_with_mocks(
            tier1_confidence=0.97,
            tier1_status=AuthorizationStatus.AUTO_APPROVED,
        )
        ctx = DecisionContext(case=make_case(), relevant_guidelines="NCCN guidelines support.")
        result = await orchestrator.process_decision(ctx)

        assert result.status == AuthorizationStatus.AUTO_APPROVED
        # Medical Director should NOT have been called
        orchestrator.medical_director_agent.run.assert_not_called()

    # ── Branch 2: Medical Director escalation ────────────────────────────────

    @pytest.mark.asyncio
    async def test_branch2_ambiguous_confidence_calls_medical_director(self):
        """
        Branch 2: confidence between 0.90 and 0.95 must invoke Medical Director.
        """
        orchestrator = self.make_orchestrator_with_mocks(
            tier1_confidence=0.92,  # In the 0.90-0.95 ambiguous zone
            tier1_status=AuthorizationStatus.IN_REVIEW,
            tier2_confidence=0.97,  # MD is confident → approve
        )
        ctx = DecisionContext(case=make_case(), relevant_guidelines="Some guidelines.")
        result = await orchestrator.process_decision(ctx)

        # Medical Director MUST have been called for the ambiguous case
        orchestrator.medical_director_agent.run.assert_called_once()
        assert result.status == AuthorizationStatus.AUTO_APPROVED

    @pytest.mark.asyncio
    async def test_branch2_md_low_confidence_routes_to_human_review(self):
        """
        Branch 2 variant: if the Medical Director is also uncertain (< 0.95),
        the case goes to human review — not auto-approved.
        """
        orchestrator = self.make_orchestrator_with_mocks(
            tier1_confidence=0.92,
            tier1_status=AuthorizationStatus.IN_REVIEW,
            tier2_confidence=0.88,  # MD also uncertain
        )
        # Override MD mock to return low confidence
        orchestrator.medical_director_agent.run = AsyncMock(
            return_value=make_decision(
                status=AuthorizationStatus.IN_REVIEW,
                confidence=0.88,
            )
        )
        ctx = DecisionContext(case=make_case(), relevant_guidelines="Ambiguous guidelines.")
        result = await orchestrator.process_decision(ctx)

        assert result.status == AuthorizationStatus.IN_REVIEW

    # ── Branch 3: Low confidence ──────────────────────────────────────────────

    @pytest.mark.asyncio
    async def test_branch3_low_confidence_routes_to_human_review(self):
        """
        Branch 3: confidence < 0.90 routes to human review queue.

        The Medical Director Agent must NOT be called — confidence is too
        low for even a second AI opinion to be meaningful.
        """
        orchestrator = self.make_orchestrator_with_mocks(
            tier1_confidence=0.72,  # Below the 0.90 threshold
            tier1_status=AuthorizationStatus.IN_REVIEW,
        )
        ctx = DecisionContext(case=make_case(), relevant_guidelines="Insufficient guidelines.")
        result = await orchestrator.process_decision(ctx)

        assert result.status == AuthorizationStatus.IN_REVIEW
        orchestrator.medical_director_agent.run.assert_not_called()

    # ── Branches 4-7: Pre-flight escalation ──────────────────────────────────

    @pytest.mark.asyncio
    async def test_branch4_experimental_treatment_bypasses_llm(self):
        """
        Branch 4: experimental procedure must route to IN_REVIEW without calling
        either agent. No LLM call should happen — this is a policy decision.
        """
        orchestrator = self.make_orchestrator_with_mocks()
        experimental_case = make_case(procedure_code="Q2041")  # CAR-T therapy
        ctx = DecisionContext(
            case=experimental_case,
            relevant_guidelines="CAR-T therapy guidelines.",
        )
        result = await orchestrator.process_decision(ctx)

        assert result.status == AuthorizationStatus.IN_REVIEW
        # Neither agent should have been called — pre-flight short-circuits
        orchestrator.decision_agent.run.assert_not_called()
        orchestrator.medical_director_agent.run.assert_not_called()

    @pytest.mark.asyncio
    async def test_branch5_rare_condition_bypasses_llm(self):
        """
        Branch 5: rare disease diagnosis routes to IN_REVIEW without LLM calls.
        Gaucher disease (E75.22) must not receive an autonomous AI decision.
        """
        orchestrator = self.make_orchestrator_with_mocks()
        rare_case = make_case(diagnosis_code="E75.22")  # Gaucher disease
        ctx = DecisionContext(case=rare_case, relevant_guidelines="Rare disease guidelines.")
        result = await orchestrator.process_decision(ctx)

        assert result.status == AuthorizationStatus.IN_REVIEW
        orchestrator.decision_agent.run.assert_not_called()

    @pytest.mark.asyncio
    async def test_branch6_conflicting_guidelines_bypasses_llm(self):
        """
        Branch 6: conflicting guidelines route to IN_REVIEW without LLM calls.
        """
        orchestrator = self.make_orchestrator_with_mocks()
        ctx = DecisionContext(
            case=make_case(),
            relevant_guidelines=(
                "NCCN: Treatment is recommended and evidence-based. "
                "CMS: Treatment is not recommended for this indication."
            ),
        )
        result = await orchestrator.process_decision(ctx)

        assert result.status == AuthorizationStatus.IN_REVIEW
        orchestrator.decision_agent.run.assert_not_called()

    @pytest.mark.asyncio
    async def test_branch7_prior_denial_bypasses_llm(self):
        """
        Branch 7: prior denial for same service routes to IN_REVIEW without LLM calls.
        """
        orchestrator = self.make_orchestrator_with_mocks()
        ctx = DecisionContext(case=make_case(procedure_code="J9271"), relevant_guidelines="...")
        result = await orchestrator.process_decision(
            ctx,
            prior_denial_codes=["J9271"],  # Same procedure was previously denied
        )

        assert result.status == AuthorizationStatus.IN_REVIEW
        orchestrator.decision_agent.run.assert_not_called()

    @pytest.mark.asyncio
    async def test_pre_flight_rationale_is_descriptive(self):
        """
        Pre-flight escalations must include a rationale explaining exactly
        which check triggered and why.

        Real-world meaning: the human reviewer who receives this case needs
        to know immediately what to look for. 'Routed to review' is useless.
        'Pre-flight escalation: experimental treatment — Q2041 is on the
        experimental procedure list' is actionable.
        """
        orchestrator = self.make_orchestrator_with_mocks()
        experimental_case = make_case(procedure_code="Q2041")
        ctx = DecisionContext(case=experimental_case, relevant_guidelines="...")
        result = await orchestrator.process_decision(ctx)

        assert "pre-flight" in result.rationale.lower()
        assert "Q2041" in result.rationale

    @pytest.mark.asyncio
    async def test_clean_case_proceeds_to_agent_evaluation(self):
        """
        A case with no risk flags must proceed to normal agent evaluation.

        This test verifies that the pre-flight check does NOT accidentally
        over-escalate clean cases. A standard NSCLC pembrolizumab request
        with no risk factors should reach the Decision Agent normally.
        """
        orchestrator = self.make_orchestrator_with_mocks(
            tier1_confidence=0.97,
            tier1_status=AuthorizationStatus.AUTO_APPROVED,
        )
        clean_case = make_case(
            procedure_code="J9271",  # Standard, non-experimental
            diagnosis_code="C34.1",  # Common NSCLC
            evidence_text="PD-L1 >= 50%, no prior treatment, standard of care.",
        )
        ctx = DecisionContext(
            case=clean_case,
            relevant_guidelines="NCCN: pembrolizumab recommended Category 1.",
        )
        result = await orchestrator.process_decision(ctx)

        # Decision Agent must have been called — no pre-flight triggers
        orchestrator.decision_agent.run.assert_called_once()
        assert result.status == AuthorizationStatus.AUTO_APPROVED
