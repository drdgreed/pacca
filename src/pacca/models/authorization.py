from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field
from .enums import AuthorizationStatus, ReviewTier
from .clinical import ClinicalCase

class AuditLogEntry(BaseModel):
    timestamp: datetime = Field(default_factory=datetime.now)
    entry_type: str
    message: str
    agent_id: Optional[str] = None

class AuthorizationDecision(BaseModel):
    decision_id: str
    status: AuthorizationStatus
    confidence_score: float
    rationale: str
    review_tier_used: ReviewTier
    timestamp: datetime = Field(default_factory=datetime.now)
    # We add this field back since the AuditLogEntry exists now
    audit_trail: List[AuditLogEntry] = []

class AuthorizationRequest(BaseModel):
    request_id: str
    patient_id: str
    provider_npi: str
    clinical_case: ClinicalCase
    # Audit log might be attached here in some legacy versions
    audit_log: List[AuditLogEntry] = []
