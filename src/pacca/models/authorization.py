from datetime import datetime

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
    "ReviewTier",
]


class AuditLogEntry(BaseModel):
    timestamp: datetime = Field(default_factory=datetime.now)
    entry_type: str
    message: str
    agent_id: str | None = None


class AuthorizationDecision(BaseModel):
    decision_id: str
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
