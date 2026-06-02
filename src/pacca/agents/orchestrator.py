"""
Orchestrator — coordinates the multi-agent decision pipeline.

The Orchestrator is the "traffic controller" of PACCA. It decides which
agents run, in what order, and what to do with their outputs. It enforces
the full 7-branch escalation tree specified in PRD SS5.4.

Architecture teaching note — why a separate Orchestrator?
  Each agent (Decision, Medical Director) is a specialist — it knows how to
  do one thing well. The Orchestrator contains ZERO clinical reasoning. Its
  only job is workflow: call this agent, check the result, decide what to
  do next. This separation means:
    - You can change escalation rules without touching clinical prompts
    - You can add new agents (e.g. a Pharmacist Agent) by plugging them
      in here, without rewriting the decision logic
    - You can test escalation logic independently of LLM calls

The 7-branch escalation tree (PRD SS5.4 — now fully implemented):

  PRE-FLIGHT CHECKS (run before any agent call):
    Branch 4: Experimental treatment   → always route to human review
    Branch 5: Rare condition           → always route to human review
    Branch 6: Conflicting guidelines   → always route to human review
    Branch 7: Prior denial same service→ always route to human review

  POST-AGENT CHECKS (run after Decision Agent returns):
    Branch 1: confidence >= 0.95       → auto-approve
    Branch 2: 0.90 <= confidence < 0.95→ Medical Director Agent
    Branch 3: confidence < 0.90        → human review queue

  The pre-flight checks are the key architectural addition in Week 2.
  They ensure certain cases NEVER reach autonomous decision regardless of
  how confident the AI appears. This is not a limitation — it is a
  deliberate clinical safety property of the system.

Teaching note — pre-flight before post-flight:
  You might wonder: why not just run the Decision Agent on every case and
  let its confidence score drive everything? Two reasons:
  1. Efficiency: LLM calls cost money and take time. Pre-flight checks are
     pure Python — microseconds, zero cost. Why spend $0.05 on a Claude API
     call for a case we already know must go to human review?
  2. Safety: A highly confident AI is not necessarily a correct AI,
     especially on experimental treatments and rare conditions where the
     model's training data is thin. Pre-flight checks enforce policy
     regardless of AI confidence.
"""

import time

from ..config.settings import effective_settings
from ..db.repository import AuditRepository
from ..models.authorization import AuthorizationDecision, AuthorizationStatus
from ..models.enums import EscalationReason, ReviewTier
from .clinical_risk_detector import ClinicalRiskDetector, EscalationFlags
from .decision import DecisionAgent, DecisionContext, MedicalDirectorAgent


def select_confidence_branch(
    confidence: float,
    status: "AuthorizationStatus",
    auto_approve_threshold: float,
    escalation_threshold: float,
) -> str:
    """Select the Tier-1 confidence routing branch (PRD §5.4 Branches 1-3).

    Returns one of: "auto_approve", "medical_director", "human_review".
    Pure function of the agent's (confidence, status) and the effective thresholds.
    """
    if confidence >= auto_approve_threshold and status == AuthorizationStatus.AUTO_APPROVED:
        return "auto_approve"
    if escalation_threshold <= confidence < auto_approve_threshold:
        return "medical_director"
    return "human_review"


class Orchestrator:
    """
    Coordinates the full 7-branch prior authorization decision pipeline.

    Responsibilities:
      - Run pre-flight clinical risk checks (Branches 4-7)
      - Run the Frontline Decision Agent on cases that pass pre-flight
      - Apply confidence thresholds (Branches 1-3)
      - Escalate to Medical Director Agent when confidence is ambiguous
      - Route to human review queue when required
      - Write per-agent audit records for observability and HIPAA compliance

    The Orchestrator is intentionally thin on clinical reasoning — it only
    applies policy rules. All clinical judgment lives in the agents.
    """

    def __init__(self) -> None:
        self.decision_agent = DecisionAgent()
        self.medical_director_agent = MedicalDirectorAgent()
        # ClinicalRiskDetector is a stateless utility — safe to instantiate once
        self.risk_detector = ClinicalRiskDetector()

    async def process_decision(
        self,
        context: DecisionContext,
        audit: AuditRepository | None = None,
        correlation_id: str | None = None,
        prior_denial_codes: list[str] | None = None,
    ) -> AuthorizationDecision:
        """
        Run the full 7-branch decision pipeline for a prior authorization request.

        Args:
            context:             The clinical case + retrieved guidelines
            audit:               AuditRepository for writing event records.
                                 Optional so the Orchestrator can be called
                                 from tests or scripts without a database.
            correlation_id:      UUID shared across all audit records for this
                                 request. Pass the same ID used in the route.
            prior_denial_codes:  Procedure codes previously denied for this
                                 patient. Used for Branch 7 (prior denial check).
                                 Defaults to empty list if not provided.

        Returns:
            AuthorizationDecision with final status, confidence, and rationale
        """
        prior_denial_codes = prior_denial_codes or []

        # ═════════════════════════════════════════════════════════════════════
        # PRE-FLIGHT: Branches 4-7 — run BEFORE any LLM call
        # ═════════════════════════════════════════════════════════════════════
        #
        # Teaching note: these checks are deterministic policy rules. They
        # do not involve any AI reasoning. A case that triggers a pre-flight
        # flag goes directly to the human review queue — the LLM is never
        # consulted. This is intentional: for these case types, AI confidence
        # is not a reliable signal.

        flags = self.risk_detector.evaluate(
            case=context.case,
            guidelines_context=context.relevant_guidelines,
            prior_denial_codes=prior_denial_codes,
        )

        if flags.should_pre_escalate:
            return await self._handle_pre_flight_escalation(
                context=context,
                flags=flags,
                audit=audit,
                correlation_id=correlation_id,
            )

        # ═════════════════════════════════════════════════════════════════════
        # TIER 1: Decision Agent (Branch evaluation: 1, 2, or 3)
        # ═════════════════════════════════════════════════════════════════════
        #
        # Teaching note: every agent call is wrapped in a start/complete
        # audit pair. This pattern gives you:
        #   - Proof that the agent was called (start record)
        #   - Proof of what it returned and how long it took (complete record)
        # An orphaned "started" record with no "completed" pair tells you
        # exactly where a failure occurred — invaluable for debugging.

        tier1_start = time.time()

        if audit:
            await audit.log(
                action="agent_decision_started",
                actor="DecisionSupportAgent",
                actor_type="agent",
                correlation_id=correlation_id,
                input_summary=(
                    f"Diagnosis: {context.case.primary_diagnosis_code} | "
                    f"Procedure: {context.case.procedure_code}"
                ),
            )

        decision = await self.decision_agent.run(context)
        tier1_ms = int((time.time() - tier1_start) * 1000)

        if audit:
            await audit.log(
                action="agent_decision_completed",
                actor="DecisionSupportAgent",
                actor_type="agent",
                correlation_id=correlation_id,
                duration_ms=tier1_ms,
                output_summary=(
                    f"Status: {decision.status.value} | Confidence: {decision.confidence_score:.2f}"
                ),
                details={
                    "confidence_score": decision.confidence_score,
                    "status": decision.status.value,
                    "review_tier": decision.review_tier_used.value,
                },
            )

        # ── Tier-1 confidence routing (PRD §5.4 Branches 1-3) ──────────────────
        s = effective_settings()
        branch = select_confidence_branch(
            decision.confidence_score,
            decision.status,
            s.auto_approve_confidence_threshold,
            s.escalation_confidence_threshold,
        )

        if branch == "auto_approve":
            if audit:
                await audit.log(
                    action="escalation_auto_approved",
                    actor="orchestrator",
                    actor_type="system",
                    correlation_id=correlation_id,
                    details={
                        "escalation_reason": EscalationReason.CONFIDENCE_BELOW_THRESHOLD.value,
                        "confidence_score": decision.confidence_score,
                        "branch": "1_auto_approve",
                    },
                )
            return decision

        if branch == "medical_director":
            return await self._run_medical_director(
                context=context,
                tier1_decision=decision,
                audit=audit,
                correlation_id=correlation_id,
            )

        # branch == "human_review"
        decision.status = AuthorizationStatus.IN_REVIEW
        if audit:
            await audit.log(
                action="escalation_human_review_required",
                actor="orchestrator",
                actor_type="system",
                correlation_id=correlation_id,
                details={
                    "escalation_reason": EscalationReason.CONFIDENCE_BELOW_THRESHOLD.value,
                    "confidence_score": decision.confidence_score,
                    "threshold": s.escalation_confidence_threshold,
                    "branch": "3_low_confidence",
                },
            )
        return decision

    # ── Helper: Pre-flight escalation handler ────────────────────────────────

    async def _handle_pre_flight_escalation(
        self,
        context: DecisionContext,
        flags: EscalationFlags,
        audit: AuditRepository | None,
        correlation_id: str | None,
    ) -> AuthorizationDecision:
        """
        Handle a case that triggered one or more pre-flight risk checks.

        Creates a decision record that routes directly to human review,
        with all triggered escalation reasons recorded in the audit log.
        This decision is NOT produced by an LLM — it is a policy decision
        by the Orchestrator.

        The decision's rationale explains exactly why it was pre-escalated,
        so the human reviewer immediately knows what to focus on.
        """
        # Build a clear rationale from all triggered flags
        reasons_text = "; ".join(
            f"{reason.value}: {detail}"
            for reason, detail in zip(flags.reasons, flags.details.values(), strict=False)
        )

        # Construct the decision as a policy outcome, not an AI outcome
        decision = AuthorizationDecision(
            decision_id=f"PREESC-{context.case.procedure_code}-{int(time.time())}",
            status=AuthorizationStatus.IN_REVIEW,
            confidence_score=0.0,  # Not applicable — this is a policy decision
            rationale=(
                f"Pre-flight escalation triggered by clinical risk checks. "
                f"Case routed directly to human review without AI evaluation. "
                f"Triggered checks: {reasons_text}"
            ),
            review_tier_used=ReviewTier.HUMAN,
        )

        if audit:
            await audit.log(
                action="escalation_pre_flight_triggered",
                actor="orchestrator",
                actor_type="system",
                correlation_id=correlation_id,
                output_summary=(
                    f"Pre-flight escalation: {len(flags.reasons)} trigger(s) fired. "
                    f"Reasons: {[r.value for r in flags.reasons]}"
                ),
                details={
                    "escalation_reasons": [r.value for r in flags.reasons],
                    "escalation_details": flags.details,
                    "branch": "4_7_pre_flight",
                    "llm_consulted": False,
                },
            )

        return decision

    # ── Helper: Medical Director Agent (Branch 2) ─────────────────────────────

    async def _run_medical_director(
        self,
        context: DecisionContext,
        tier1_decision: AuthorizationDecision,
        audit: AuditRepository | None,
        correlation_id: str | None,
    ) -> AuthorizationDecision:
        """
        Run the Tier 2 Medical Director Agent for ambiguous cases.

        The Medical Director Agent receives both the original case AND the
        Tier 1 decision so it can evaluate exactly why the Frontline Agent
        was uncertain. This is different from just running a second
        independent evaluation — it is a supervised second opinion.
        """
        tier2_start = time.time()

        if audit:
            await audit.log(
                action="agent_medical_director_started",
                actor="MedicalDirectorAgent",
                actor_type="agent",
                correlation_id=correlation_id,
                input_summary=(
                    f"Escalating from Tier 1. "
                    f"Tier 1 confidence: {tier1_decision.confidence_score:.2f}"
                ),
                details={
                    "branch": "2_medical_director",
                    "tier1_confidence": tier1_decision.confidence_score,
                    "tier1_status": tier1_decision.status.value,
                },
            )

        md_decision = await self.medical_director_agent.run(context, tier1_decision)
        tier2_ms = int((time.time() - tier2_start) * 1000)

        if audit:
            await audit.log(
                action="agent_medical_director_completed",
                actor="MedicalDirectorAgent",
                actor_type="agent",
                correlation_id=correlation_id,
                duration_ms=tier2_ms,
                output_summary=(
                    f"Status: {md_decision.status.value} | "
                    f"Confidence: {md_decision.confidence_score:.2f}"
                ),
                details={
                    "confidence_score": md_decision.confidence_score,
                    "status": md_decision.status.value,
                },
            )

        if md_decision.confidence_score >= effective_settings().auto_approve_confidence_threshold:
            md_decision.status = AuthorizationStatus.AUTO_APPROVED
        else:
            md_decision.status = AuthorizationStatus.IN_REVIEW

        return md_decision
