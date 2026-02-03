"""
Database module for PACCA.

Provides database models, session management, and repository pattern.
"""

from pacca.db.models import (
    AuditLogModel,
    AuthorizationDecisionModel,
    AuthorizationRequestModel,
    Base,
    GuidelineModel,
    HumanReviewModel,
)
from pacca.db.repository import (
    AuditRepository,
    AuthorizationRepository,
    DecisionRepository,
    GuidelineRepository,
)
from pacca.db.session import (
    close_database,
    get_session,
    get_session_context,
    health_check,
    init_database,
)

__all__ = [
    # Models
    "Base",
    "AuthorizationRequestModel",
    "AuthorizationDecisionModel",
    "HumanReviewModel",
    "AuditLogModel",
    "GuidelineModel",
    # Session
    "get_session",
    "get_session_context",
    "init_database",
    "close_database",
    "health_check",
    # Repositories
    "AuthorizationRepository",
    "DecisionRepository",
    "AuditRepository",
    "GuidelineRepository",
]
