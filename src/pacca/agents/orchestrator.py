"""
Orchestration Agent.

Coordinates the multi-agent workflow for prior authorization processing,
managing state transitions, escalation logic, and human-in-the-loop gates.
"""

import asyncio
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from pacca.agents.classification_agent import ClinicalClassificationAgent
from pacca.agents.decision_agent import DecisionSupportAgent
from pacca.agents.evidence_agent import EvidenceAggregationAgent
from pacca.agents.types import AgentContext, AgentResponse
from pacca.config import get_logger, get_settings
from pacca.models import (
    AgentType,
    AuthorizationDecision,
    AuthorizationRequest,
    AuthorizationStatus,
    ClassificationResult,
    ClinicalEvidence,
    ClinicalNarrative,
    ComplexityLevel,
    DecisionOutcome,
    EscalationReason,
)

logger = get_logger(__name__)


class WorkflowState:
    """States in the authorization workflow state machine."""

    INITIALIZED = "initialized"
    GATHERING_EVIDENCE = "gathering_evidence"
    CLASSIFYING = "classifying"
    EVALUATING = "evaluating"
    PENDING_REVIEW = "pending_review"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class WorkflowResult:
    """Result of the orchestrated workflow."""

    request_id: str
    state: str
    status: AuthorizationStatus
    decision: AuthorizationDecision | None = None
    classification: ClassificationResult | None = None
    evidence: ClinicalEvidence | None = None
    narrative: ClinicalNarrative | None = None

    # Workflow metadata
    started_at: datetime = field(default_factory=datetime.utcnow)
    completed_at: datetime | None = None
    total_duration_ms: int = 0

    # Escalation
    requires_human_review: bool = False
    escalation_reasons: list[str] = field(default_factory=list)

    # Agent responses for audit
    agent_responses: dict[str, Any] = field(default_factory=dict)

    # Errors
    error: str | None = None

    def complete(self, status: AuthorizationStatus) -> None:
        """Mark workflow as complete."""
        self.completed_at = datetime.utcnow()
        self.status = status
        if self.completed_at and self.started_at:
            delta = self.completed_at - self.started_at
            self.total_duration_ms = int(delta.total_seconds() * 1000)


class OrchestrationAgent:
    """
    Coordinates the multi-agent workflow for prior authorization.

    The orchestrator:
    1. Manages workflow state transitions
    2. Invokes agents in the correct sequence
    3. Handles escalation and human-in-the-loop gates
    4. Aggregates results and produces final outcomes

    Workflow Sequence:
    1. Evidence Aggregation → Gather clinical evidence
    2. Clinical Classification → Classify complexity/specialty
    3. Decision Support → Generate recommendation
    4. [If escalated] → Route to human review queue
    5. [If autonomous] → Finalize decision
    """

    def __init__(self) -> None:
        """Initialize the orchestration agent with sub-agents."""
        self.settings = get_settings()

        # Initialize sub-agents
        self.evidence_agent = EvidenceAggregationAgent()
        self.classification_agent = ClinicalClassificationAgent()
        self.decision_agent = DecisionSupportAgent()

        logger.info("orchestration_agent_initialized")

    async def process_authorization(
        self,
        request: AuthorizationRequest,
        force_escalation: bool = False,
    ) -> WorkflowResult:
        """
        Process a prior authorization request through the agent workflow.

        Args:
            request: The authorization request to process
            force_escalation: If True, always escalate to human review

        Returns:
            WorkflowResult containing decision and workflow metadata
        """
        logger.info(
            "workflow_started",
            request_id=request.request_id,
            patient_id=request.patient.patient_id,
            diagnosis=request.primary_diagnosis.code,
            treatment=request.requested_treatment.code,
        )

        # Initialize workflow result
        result = WorkflowResult(
            request_id=request.request_id,
            state=WorkflowState.INITIALIZED,
            status=AuthorizationStatus.SUBMITTED,
        )

        # Initialize context for agent chain
        context = AgentContext(
            request_id=request.request_id,
            force_escalation=force_escalation,
        )

        try:
            # Step 1: Evidence Aggregation
            result.state = WorkflowState.GATHERING_EVIDENCE
            request.update_status(AuthorizationStatus.EVIDENCE_GATHERING)

            evidence_response = await self._run_evidence_agent(request, context)
            result.agent_responses["evidence"] = evidence_response

            if not evidence_response.success:
                return self._handle_agent_failure(result, "evidence", evidence_response)

            # Store evidence outputs
            result.evidence = self.evidence_agent.to_clinical_evidence(evidence_response.output)
            result.narrative = self.evidence_agent.to_clinical_narrative(evidence_response.output)

            # Update request with evidence
            request.evidence = result.evidence
            request.narrative = result.narrative

            # Step 2: Clinical Classification
            result.state = WorkflowState.CLASSIFYING
            request.update_status(AuthorizationStatus.CLASSIFYING)

            classification_response = await self._run_classification_agent(request, context)
            result.agent_responses["classification"] = classification_response

            if not classification_response.success:
                return self._handle_agent_failure(result, "classification", classification_response)

            # Store classification results
            result.classification = self.classification_agent.to_classification_result(
                classification_response.output
            )

            # Update request with classification
            request.complexity = result.classification.complexity
            request.assigned_specialty = result.classification.primary_specialty

            # Step 3: Decision Support
            result.state = WorkflowState.EVALUATING
            request.update_status(AuthorizationStatus.EVALUATING)

            decision_response = await self._run_decision_agent(request, context)
            result.agent_responses["decision"] = decision_response

            if not decision_response.success:
                return self._handle_agent_failure(result, "decision", decision_response)

            # Determine if human review is needed
            escalation_reasons = self._collect_escalation_reasons(
                evidence_response,
                classification_response,
                decision_response,
                request,
            )

            should_escalate = (
                force_escalation
                or len(escalation_reasons) > 0
                or not self.settings.enable_autonomous_decisions
            )

            # Convert to authorization decision
            result.decision = self.decision_agent.to_authorization_decision(
                decision_response.output,
                request_id=request.request_id,
                was_escalated=should_escalate,
                escalation_reasons=[
                    EscalationReason.LOW_CONFIDENCE  # Simplified for MVP
                ]
                if should_escalate
                else [],
            )

            if should_escalate:
                # Route to human review
                result.state = WorkflowState.PENDING_REVIEW
                result.requires_human_review = True
                result.escalation_reasons = escalation_reasons
                result.complete(AuthorizationStatus.PENDING_REVIEW)

                logger.info(
                    "workflow_escalated",
                    request_id=request.request_id,
                    escalation_reasons=escalation_reasons,
                    recommendation=result.decision.outcome.value,
                )
            else:
                # Autonomous decision
                result.state = WorkflowState.COMPLETED
                final_status = self._outcome_to_status(result.decision.outcome)
                result.complete(final_status)

                logger.info(
                    "workflow_completed_autonomous",
                    request_id=request.request_id,
                    outcome=result.decision.outcome.value,
                    confidence=result.decision.confidence_score,
                    duration_ms=result.total_duration_ms,
                )

            return result

        except Exception as e:
            logger.exception(
                "workflow_failed",
                request_id=request.request_id,
                error=str(e),
            )

            result.state = WorkflowState.FAILED
            result.error = str(e)
            result.complete(AuthorizationStatus.FAILED)
            return result

    async def _run_evidence_agent(
        self,
        request: AuthorizationRequest,
        context: AgentContext,
    ) -> AgentResponse:
        """Run the evidence aggregation agent."""
        response = await self.evidence_agent.run(request, context)

        # Add output to context for next agent
        if response.success and response.output:
            context.add_agent_output(
                AgentType.EVIDENCE_AGGREGATION,
                response.output.model_dump(),
            )

        return response

    async def _run_classification_agent(
        self,
        request: AuthorizationRequest,
        context: AgentContext,
    ) -> AgentResponse:
        """Run the clinical classification agent."""
        response = await self.classification_agent.run(request, context)

        # Add output to context for next agent
        if response.success and response.output:
            context.add_agent_output(
                AgentType.CLINICAL_CLASSIFICATION,
                response.output.model_dump(),
            )

        return response

    async def _run_decision_agent(
        self,
        request: AuthorizationRequest,
        context: AgentContext,
    ) -> AgentResponse:
        """Run the decision support agent."""
        response = await self.decision_agent.run(request, context)

        # Add output to context
        if response.success and response.output:
            context.add_agent_output(
                AgentType.DECISION_SUPPORT,
                response.output.model_dump(),
            )

        return response

    def _collect_escalation_reasons(
        self,
        evidence_response: AgentResponse,
        classification_response: AgentResponse,
        decision_response: AgentResponse,
        request: AuthorizationRequest,
    ) -> list[str]:
        """Collect all escalation reasons from agents and business rules."""
        reasons = []

        # Confidence-based escalation
        min_confidence = min(
            evidence_response.confidence_score,
            classification_response.confidence_score,
            decision_response.confidence_score,
        )

        if min_confidence < self.settings.escalation_confidence_threshold:
            reasons.append(
                f"Low confidence ({min_confidence:.2f}) below threshold "
                f"({self.settings.escalation_confidence_threshold})"
            )

        # Agent-recommended escalation
        for name, response in [
            ("evidence", evidence_response),
            ("classification", classification_response),
            ("decision", decision_response),
        ]:
            if response.should_escalate:
                reasons.extend(
                    f"{name}: {r}" for r in response.escalation_reasons
                )

        # Complexity-based escalation
        if classification_response.success and classification_response.output:
            complexity = classification_response.output.complexity
            if complexity > self.settings.complexity_auto_approve_max:
                reasons.append(
                    f"Complexity ({complexity}) exceeds auto-approve threshold "
                    f"({self.settings.complexity_auto_approve_max})"
                )

        # High-cost escalation
        if request.is_high_cost:
            reasons.append(
                f"High-cost authorization (>${self.settings.high_cost_threshold:,}) "
                "requires medical director review"
            )

        # Denial escalation (denials always reviewed in this MVP)
        if decision_response.success and decision_response.output:
            if decision_response.output.recommendation.upper() == "DENY":
                reasons.append("Denial recommendations require human review")

        return reasons

    def _handle_agent_failure(
        self,
        result: WorkflowResult,
        agent_name: str,
        response: AgentResponse,
    ) -> WorkflowResult:
        """Handle agent failure and update result."""
        result.state = WorkflowState.FAILED
        result.error = f"{agent_name} agent failed: {response.error_message}"
        result.complete(AuthorizationStatus.FAILED)

        logger.error(
            "agent_failure_in_workflow",
            request_id=result.request_id,
            agent=agent_name,
            error=response.error_message,
        )

        return result

    def _outcome_to_status(self, outcome: DecisionOutcome) -> AuthorizationStatus:
        """Map decision outcome to authorization status."""
        mapping = {
            DecisionOutcome.APPROVE: AuthorizationStatus.APPROVED,
            DecisionOutcome.DENY: AuthorizationStatus.DENIED,
            DecisionOutcome.APPROVE_WITH_CONDITIONS: AuthorizationStatus.APPROVED_WITH_CONDITIONS,
            DecisionOutcome.REQUEST_MORE_INFO: AuthorizationStatus.INCOMPLETE,
            DecisionOutcome.ESCALATE: AuthorizationStatus.PENDING_REVIEW,
            DecisionOutcome.UNABLE_TO_DETERMINE: AuthorizationStatus.PENDING_REVIEW,
        }
        return mapping.get(outcome, AuthorizationStatus.PENDING_REVIEW)

    async def handle_human_review(
        self,
        request_id: str,
        reviewer_decision: DecisionOutcome,
        reviewer_notes: str | None = None,
        reviewer_id: str = "human_reviewer",
    ) -> AuthorizationDecision:
        """
        Handle human review of an escalated authorization.

        This is called when a human reviewer makes a final decision
        on an escalated case.

        Args:
            request_id: The authorization request ID
            reviewer_decision: The reviewer's decision
            reviewer_notes: Optional notes from reviewer
            reviewer_id: Identifier of the reviewer

        Returns:
            Updated AuthorizationDecision
        """
        logger.info(
            "human_review_received",
            request_id=request_id,
            reviewer_id=reviewer_id,
            decision=reviewer_decision.value,
        )

        # In a full implementation, this would:
        # 1. Load the pending decision from database
        # 2. Update with human review
        # 3. Save the final decision
        # 4. Trigger communication workflows

        # For MVP, we create a new decision reflecting the human review
        decision = AuthorizationDecision(
            request_id=request_id,
            outcome=reviewer_decision,
            confidence_score=1.0,  # Human decisions are "certain"
            rationale=None,  # Would be populated from original + reviewer notes
            decided_by=reviewer_id,
            is_autonomous=False,
            was_escalated=True,
        )

        return decision
