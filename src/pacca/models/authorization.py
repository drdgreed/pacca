from datetime import datetime
from uuid import uuid4

from pydantic import BaseModel, Field

from .clinical import ClinicalCase
from .enums import AuthorizationStatus, ReviewTier

# iter-5 chg-3: explicit __all__ so mypy strict mode treats ReviewTier as
# a deliberate re-export. decision.py imports ReviewTier from this module
# rather than from .enums directly, which is the project convention.
__all__ = [
    "AuditLogEntry",
    "AuthorizationDecision",
    "AuthorizationRequest",
    "AuthorizationStatus",
    "ClinicalCase",
    "DecisionDraft",
    "ReviewTier",
    "mint_decision_id",
]


def mint_decision_id() -> str:
    """
    Server-side identifier for an authorization decision.

    chg-11 (B6): ``decision_id`` used to arrive in the model's tool-use output,
    and was then written to a ``unique=True`` column. Identifiers are not a
    clinical judgement, and a model that repeats one silently cross-links two
    decisions' audit trails (``audit_logs.decision_id`` and the ``human_reviews``
    FK both reference this value). It is minted here instead.

    Standing rule: no LLM-supplied value may land in a unique, indexed, or
    foreign-keyed column.
    """
    return f"PA-{uuid4().hex[:16]}"


class AuditLogEntry(BaseModel):
    timestamp: datetime = Field(default_factory=datetime.now)
    entry_type: str
    message: str
    agent_id: str | None = None


class DecisionDraft(BaseModel):
    """
    What the LLM is asked for — clinical judgement only.

    chg-11 (B6): this is the ``response_model`` for both agent tiers, replacing
    ``AuthorizationDecision``. The difference is the point: no ``decision_id``,
    no ``review_tier_used``, no ``timestamp``, no ``audit_trail``. Those are
    facts about the *run*, which the server owns; the model contributes only the
    fields it is qualified to produce. ``model_json_schema()`` on this class is
    what becomes the forced tool schema, so anything absent here cannot be
    supplied by the model at all.
    """

    status: AuthorizationStatus
    confidence_score: float
    rationale: str
    cited_evidence_ids: list[str] = Field(default_factory=list)


class AuthorizationDecision(BaseModel):
    # Defaulted, never model-supplied — see mint_decision_id() and chg-11 (B6).
    # Explicit ids are still honoured for the deterministic escape hatches
    # (PREESC-… pre-flight escalations, SCOPE-… scope violations).
    decision_id: str = Field(default_factory=mint_decision_id)
    status: AuthorizationStatus
    confidence_score: float
    rationale: str
    review_tier_used: ReviewTier
    timestamp: datetime = Field(default_factory=datetime.now)
    # We add this field back since the AuditLogEntry exists now
    audit_trail: list[AuditLogEntry] = []
    # Evidence-grounding (P-5 / chg-10): the ids of the submission EvidenceItems
    # the decision relied on. The DecisionAgent populates it (prompt v2.7); the
    # orchestrator's grounding detector requires each id to resolve to a
    # submission EvidenceItem or forces human review. Defaulted (not required) so
    # hand-constructed decisions (pre-flight escalations, tests) still validate.
    cited_evidence_ids: list[str] = Field(default_factory=list)


class AuthorizationRequest(BaseModel):
    request_id: str
    patient_id: str
    provider_npi: str
    clinical_case: ClinicalCase
    # Audit log might be attached here in some legacy versions
    audit_log: list[AuditLogEntry] = []
