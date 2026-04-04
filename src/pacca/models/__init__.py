"""
PACCA domain models — public API.

Re-exports all domain model classes so code can import from
`pacca.models` rather than from individual submodules.

Examples:
    from pacca.models import AuthorizationDecision, AuthorizationStatus
    from pacca.models import ClinicalCase, EvidenceItem
    from pacca.models.enums import EscalationReason
"""

from pacca.models.enums import (
    AuthorizationStatus,
    ComplexityLevel,
    EscalationReason,
    EvidenceSourceType,
    ReviewTier,
)
from pacca.models.clinical import (
    ClinicalCase,
    EvidenceItem,
)
from pacca.models.authorization import (
    AuditLogEntry,
    AuthorizationDecision,
    AuthorizationRequest,
)

__all__ = [
    # Enums
    "AuthorizationStatus",
    "ComplexityLevel",
    "EscalationReason",
    "EvidenceSourceType",
    "ReviewTier",
    # Clinical
    "ClinicalCase",
    "EvidenceItem",
    # Authorization
    "AuditLogEntry",
    "AuthorizationDecision",
    "AuthorizationRequest",
]
