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
    "AuditLogModel",
    "AuditRepository",
    "AuthorizationDecisionModel",
    # Repositories
    "AuthorizationRepository",
    "AuthorizationRequestModel",
    # Models
    "Base",
    "DecisionRepository",
    "GuidelineModel",
    "GuidelineRepository",
    "HumanReviewModel",
    "close_database",
    # Session
    "get_session",
    "get_session_context",
    "health_check",
    "init_database",
]
