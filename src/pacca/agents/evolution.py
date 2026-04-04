"""
Policy Evolution Agent — Level 5 architecture.

This module implements PACCA's self-improvement mechanism: analyzing
patterns in human override decisions to identify whether an existing
clinical guideline should be amended.

GOVERNANCE ARCHITECTURE (added v2.2):

  The original implementation had auto_deploy=True, meaning the agent
  could directly overwrite clinical guidelines in ChromaDB at confidence
  > 0.99 with no human review. This is a regulatory liability — the FDA's
  AI/ML Software as a Medical Device (SaMD) Action Plan requires change
  control for AI-driven clinical decision support changes.

  v2.2 introduces a three-stage governance pipeline:

  Stage 1 — Proposal:    EvolutionAgent analyzes override patterns and
                          produces a PolicyProposal. The proposal is stored
                          in the database with status='pending'. Nothing is
                          deployed yet. The agent cannot deploy anything.

  Stage 2 — Review:      A human Medical Director (or designated approver)
                          reads the proposal via GET /admin/proposals.
                          They can see the full reasoning, the override
                          pattern, and the proposed amendment text.

  Stage 3 — Approval:    The approver calls POST /admin/proposals/{id}/approve
                          or POST /admin/proposals/{id}/reject.
                          Approved proposals are deployed to ChromaDB and
                          recorded in the PolicyChangeLog with the approver's
                          identity and timestamp.

  This converts EvolutionAgent from an autonomous liability into a governed
  learning system — arguably more impressive as a portfolio piece because
  it demonstrates understanding of WHY governance is necessary, not just
  that autonomous rewriting is possible.

Teaching note — why in-memory proposal store for the prototype:

  A production implementation would store proposals in the PostgreSQL
  `guidelines` table with a status column. For the portfolio prototype,
  we use an in-memory list that persists for the server lifetime. This
  is explicitly documented as a prototype limitation and the production
  path (database storage via GuidelineRepository) is noted.
"""

import time
from dataclasses import dataclass, field
from typing import Optional

from pydantic import BaseModel, Field

from .base import BaseAgent
from .prompts.templates import EVOLUTION_AGENT_SYSTEM, get_prompt_version


# =============================================================================
# Domain models for the governance pipeline
# =============================================================================

class PolicyProposal(BaseModel):
    """
    Output from the EvolutionAgent — a proposed guideline amendment.

    This replaces the original PolicyAmendment model. The key difference:
    there is NO auto_deploy field. The agent produces a proposal; humans
    deploy it. Deployment authority is removed from the agent entirely.

    Attributes:
        original_guideline_id: Which guideline is being amended
        proposed_text:         The full text of the amended guideline
        reasoning:             Why the agent believes this amendment is warranted
        override_pattern:      Summary of the human override pattern analyzed
        confidence:            Agent confidence that the amendment is appropriate
                               (0.0–1.0; even high confidence requires human approval)
        scope_boundaries:      What the amendment does NOT cover (scope limits)
        reviewer_checklist:    What a human approver should verify before deploying
    """
    original_guideline_id: str = Field(
        description="The guideline being amended (source_id in ChromaDB)"
    )
    proposed_text: str = Field(
        description="The full text of the proposed amended guideline"
    )
    reasoning: str = Field(
        description="Why this amendment is warranted based on override patterns"
    )
    override_pattern: str = Field(
        description="Summary of the human override pattern that triggered this proposal"
    )
    confidence: float = Field(
        description="Agent confidence (0.0–1.0). High confidence still requires human approval.",
        ge=0.0,
        le=1.0,
    )
    scope_boundaries: str = Field(
        description="What this amendment does NOT cover — explicit scope limits"
    )
    reviewer_checklist: list[str] = Field(
        description="What a human Medical Director should verify before approving",
        default_factory=list,
    )


@dataclass
class ProposalRecord:
    """
    A stored proposal with governance metadata.

    In production, this would be a SQLAlchemy model in the guidelines table.
    For the prototype, it is stored in an in-memory list.

    Attributes:
        proposal_id:   Unique identifier (timestamp-based for prototype)
        proposal:      The PolicyProposal from the EvolutionAgent
        status:        'pending' | 'approved' | 'rejected'
        submitted_at:  Unix timestamp when proposal was created
        reviewed_by:   Username of the approver/rejector (set on review)
        reviewed_at:   Unix timestamp when reviewed (set on review)
        review_notes:  Approver's notes (optional)
    """
    proposal_id: str
    proposal: PolicyProposal
    status: str = "pending"
    submitted_at: float = field(default_factory=time.time)
    reviewed_by: Optional[str] = None
    reviewed_at: Optional[float] = None
    review_notes: Optional[str] = None


@dataclass
class PolicyChangeLogEntry:
    """
    An immutable record of a deployed policy amendment.

    Every deployed amendment is permanently recorded here, providing
    a complete audit trail of how the guideline set evolved over time.
    This is the foundation for regulatory compliance and rollback capability.

    Attributes:
        change_id:         Unique identifier
        proposal_id:       Which proposal was deployed
        guideline_id:      Which guideline was amended
        original_text:     The guideline text BEFORE the amendment
        new_text:          The guideline text AFTER the amendment
        approved_by:       Who approved the deployment
        deployed_at:       When it was deployed
        rationale_summary: Brief summary of why the change was made
    """
    change_id: str
    proposal_id: str
    guideline_id: str
    original_text: str
    new_text: str
    approved_by: str
    deployed_at: float
    rationale_summary: str


# =============================================================================
# In-memory governance stores
# Production path: replace with SQLAlchemy models in db/repository.py
# =============================================================================

_proposal_store: list[ProposalRecord] = []
_change_log: list[PolicyChangeLogEntry] = []


def get_all_proposals() -> list[ProposalRecord]:
    """Return all proposals (pending, approved, rejected)."""
    return list(_proposal_store)


def get_pending_proposals() -> list[ProposalRecord]:
    """Return proposals awaiting human review."""
    return [p for p in _proposal_store if p.status == "pending"]


def get_proposal_by_id(proposal_id: str) -> Optional[ProposalRecord]:
    """Return a specific proposal by ID."""
    return next((p for p in _proposal_store if p.proposal_id == proposal_id), None)


def get_change_log() -> list[PolicyChangeLogEntry]:
    """Return the complete immutable change log of all deployed amendments."""
    return list(_change_log)


# =============================================================================
# The EvolutionAgent
# =============================================================================

class EvolutionAgent(BaseAgent):
    """
    Level 5 Policy Evolution Agent.

    Analyzes human override patterns to identify guideline amendment
    opportunities. Produces PROPOSALS that require human approval before
    any deployment occurs.

    This agent deliberately has NO deployment capability. It cannot
    write to ChromaDB. It can only produce a structured proposal that
    goes through the governance pipeline.

    Prompt version: see PROMPT_REGISTRY['PolicyEvolutionAgent']
    """

    @property
    def name(self) -> str:
        return "PolicyEvolutionAgent"

    @property
    def system_prompt(self) -> str:
        return EVOLUTION_AGENT_SYSTEM

    @property
    def prompt_version(self) -> str:
        return get_prompt_version(self.name)

    async def run(
        self,
        original_guideline: str,
        overrides: list[str],
        guideline_id: str = "UNKNOWN",
    ) -> ProposalRecord:
        """
        Analyze override patterns and produce a governance-tracked proposal.

        This method:
          1. Calls the EvolutionAgent LLM to analyze the pattern
          2. Wraps the result in a ProposalRecord with status='pending'
          3. Stores it in the in-memory proposal store
          4. Returns the stored record (NOT a deployment)

        The proposal requires human approval via the admin API before
        any guideline changes take effect.

        Args:
            original_guideline: The current guideline text
            overrides:          List of human override decisions with rationales
            guideline_id:       Identifier of the guideline being analyzed

        Returns:
            ProposalRecord with status='pending' — awaiting human review
        """
        user_input = (
            f"## Guideline Under Analysis\n"
            f"ID: {guideline_id}\n"
            f"Current Text: {original_guideline}\n\n"
            f"## Human Override Pattern ({len(overrides)} cases)\n"
            + "\n".join(f"- {o}" for o in overrides)
        )

        proposal = await self.execute(
            user_input=user_input,
            response_model=PolicyProposal,
        )
        # Ensure the guideline ID is set even if the model didn't populate it
        if proposal.original_guideline_id == "UNKNOWN" or not proposal.original_guideline_id:
            proposal = proposal.model_copy(
                update={"original_guideline_id": guideline_id}
            )

        # Store with governance metadata — status starts as 'pending'
        proposal_id = f"PROP-{int(time.time())}"
        record = ProposalRecord(
            proposal_id=proposal_id,
            proposal=proposal,
            status="pending",
        )
        _proposal_store.append(record)

        return record


# =============================================================================
# Governance functions — called by the admin API endpoints
# =============================================================================

def approve_proposal(
    proposal_id: str,
    approved_by: str,
    review_notes: Optional[str] = None,
    original_guideline_text: str = "",
) -> Optional[PolicyChangeLogEntry]:
    """
    Approve a pending proposal and record it in the change log.

    This is the deployment gate. Only after this function is called
    does the amendment become eligible for deployment to ChromaDB.
    The actual ChromaDB write happens in the admin route after calling this.

    Args:
        proposal_id:             The proposal to approve
        approved_by:             Username/ID of the approving Medical Director
        review_notes:            Optional notes from the reviewer
        original_guideline_text: The current guideline text (for the change log)

    Returns:
        PolicyChangeLogEntry if approved successfully, None if not found
    """
    record = get_proposal_by_id(proposal_id)
    if not record or record.status != "pending":
        return None

    # Update the proposal record
    record.status = "approved"
    record.reviewed_by = approved_by
    record.reviewed_at = time.time()
    record.review_notes = review_notes

    # Create an immutable change log entry
    change_id = f"CHANGE-{int(time.time())}"
    log_entry = PolicyChangeLogEntry(
        change_id=change_id,
        proposal_id=proposal_id,
        guideline_id=record.proposal.original_guideline_id,
        original_text=original_guideline_text,
        new_text=record.proposal.proposed_text,
        approved_by=approved_by,
        deployed_at=time.time(),
        rationale_summary=record.proposal.reasoning[:500],
    )
    _change_log.append(log_entry)

    return log_entry


def reject_proposal(
    proposal_id: str,
    rejected_by: str,
    review_notes: Optional[str] = None,
) -> bool:
    """
    Reject a pending proposal without deploying it.

    Args:
        proposal_id:  The proposal to reject
        rejected_by:  Username/ID of the reviewer
        review_notes: Reason for rejection (recommended)

    Returns:
        True if rejected successfully, False if not found or not pending
    """
    record = get_proposal_by_id(proposal_id)
    if not record or record.status != "pending":
        return False

    record.status = "rejected"
    record.reviewed_by = rejected_by
    record.reviewed_at = time.time()
    record.review_notes = review_notes
    return True
