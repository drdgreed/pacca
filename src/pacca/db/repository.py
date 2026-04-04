"""
Repository pattern for database operations.

Provides a clean abstraction layer between the business logic
and database operations, with async support throughout.
"""

from datetime import datetime
from typing import Any

from sqlalchemy import select, update, and_, desc
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import uuid4


def uuid7() -> str:
    """Generate a time-sortable unique ID using uuid4 as fallback.

    The uuid7 package provides true UUIDv7 (time-ordered). When unavailable,
    uuid4 (random) is used instead — functionally identical for our purposes
    since we only need globally unique IDs, not strict time ordering.
    """
    try:
        from uuid7 import uuid7 as _uuid7
        return str(_uuid7())
    except ImportError:
        return str(uuid4())


# Re-export as the same name callers expect
__all__ = ["uuid7"]

from pacca.config import get_logger
from pacca.db.models import (
    AuditLogModel,
    AuthorizationDecisionModel,
    AuthorizationRequestModel,
    GuidelineModel,
    HumanReviewModel,
)
from pacca.models.authorization import (
    AuditLogEntry,
    AuthorizationDecision,
    AuthorizationRequest,
)
from pacca.models.enums import AuthorizationStatus

logger = get_logger(__name__)


class AuthorizationRepository:
    """Repository for authorization request operations."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, request: AuthorizationRequest) -> AuthorizationRequestModel:
        """
        Create a new authorization request in the database.

        Args:
            request: The domain model to persist

        Returns:
            The created database model
        """
        db_request = AuthorizationRequestModel(
            request_id=request.request_id,
            external_reference=request.external_reference,
            status=request.status.value,
            patient_id=request.patient.patient_id,
            patient_age=request.patient.age,
            patient_gender=request.patient.gender,
            primary_diagnosis_code=request.primary_diagnosis.code,
            primary_diagnosis_description=request.primary_diagnosis.description,
            secondary_diagnoses=[d.model_dump() for d in request.secondary_diagnoses]
            if request.secondary_diagnoses
            else None,
            treatment_code=request.requested_treatment.code,
            treatment_description=request.requested_treatment.description,
            treatment_category=request.requested_treatment.category.value,
            estimated_cost=request.requested_treatment.estimated_cost,
            provider_id=request.requesting_provider.provider_id,
            provider_name=request.requesting_provider.provider_name,
            payer_id=request.payer.payer_id,
            payer_name=request.payer.payer_name,
            member_id=request.payer.member_id,
            clinical_notes=request.clinical_notes,
            urgency=request.urgency.value,
            complexity=request.complexity.value if request.complexity else None,
            assigned_specialty=request.assigned_specialty.value
            if request.assigned_specialty
            else None,
            evidence_data=request.evidence.model_dump() if request.evidence else None,
            narrative_data=request.narrative.model_dump() if request.narrative else None,
            submitted_at=request.submitted_at,
            updated_at=request.updated_at,
        )

        self.session.add(db_request)
        await self.session.flush()

        logger.info(
            "authorization_request_created",
            request_id=request.request_id,
        )

        return db_request

    async def get_by_id(self, request_id: str) -> AuthorizationRequestModel | None:
        """
        Get an authorization request by ID.

        Args:
            request_id: The unique request identifier

        Returns:
            The database model or None if not found
        """
        result = await self.session.execute(
            select(AuthorizationRequestModel).where(
                AuthorizationRequestModel.request_id == request_id
            )
        )
        return result.scalar_one_or_none()

    async def update_status(
        self,
        request_id: str,
        status: AuthorizationStatus,
        **additional_fields: Any,
    ) -> bool:
        """
        Update the status of an authorization request.

        Args:
            request_id: The request to update
            status: The new status
            **additional_fields: Additional fields to update

        Returns:
            True if updated, False if not found
        """
        update_data = {
            "status": status.value,
            "updated_at": datetime.utcnow(),
            **additional_fields,
        }

        result = await self.session.execute(
            update(AuthorizationRequestModel)
            .where(AuthorizationRequestModel.request_id == request_id)
            .values(**update_data)
        )

        if result.rowcount > 0:
            logger.info(
                "authorization_status_updated",
                request_id=request_id,
                new_status=status.value,
            )
            return True
        return False

    async def list_requests(
        self,
        status: AuthorizationStatus | None = None,
        payer_id: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[AuthorizationRequestModel]:
        """
        List authorization requests with optional filtering.

        Args:
            status: Filter by status
            payer_id: Filter by payer
            limit: Maximum results
            offset: Pagination offset

        Returns:
            List of matching requests
        """
        query = select(AuthorizationRequestModel)

        conditions = []
        if status:
            conditions.append(AuthorizationRequestModel.status == status.value)
        if payer_id:
            conditions.append(AuthorizationRequestModel.payer_id == payer_id)

        if conditions:
            query = query.where(and_(*conditions))

        query = query.order_by(desc(AuthorizationRequestModel.submitted_at))
        query = query.limit(limit).offset(offset)

        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def count_requests(
        self,
        status: AuthorizationStatus | None = None,
        payer_id: str | None = None,
    ) -> int:
        """Count authorization requests with optional filtering."""
        from sqlalchemy import func

        query = select(func.count(AuthorizationRequestModel.id))

        conditions = []
        if status:
            conditions.append(AuthorizationRequestModel.status == status.value)
        if payer_id:
            conditions.append(AuthorizationRequestModel.payer_id == payer_id)

        if conditions:
            query = query.where(and_(*conditions))

        result = await self.session.execute(query)
        return result.scalar() or 0


class DecisionRepository:
    """Repository for authorization decision operations."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(
        self,
        decision: AuthorizationDecision,
        processing_time_ms: int | None = None,
        total_tokens: int | None = None,
    ) -> AuthorizationDecisionModel:
        """
        Create a new authorization decision.

        Args:
            decision: The domain model to persist
            processing_time_ms: Time taken to process
            total_tokens: Total LLM tokens used

        Returns:
            The created database model
        """
        db_decision = AuthorizationDecisionModel(
            decision_id=decision.decision_id,
            request_id=decision.request_id,
            outcome=decision.outcome.value,
            confidence_score=decision.confidence_score,
            rationale_data=decision.rationale.model_dump() if decision.rationale else None,
            conditions=decision.conditions if decision.conditions else None,
            required_actions=decision.required_actions if decision.required_actions else None,
            effective_date=decision.effective_date,
            expiration_date=decision.expiration_date,
            authorized_quantity=decision.authorized_quantity,
            authorized_duration_days=decision.authorized_duration_days,
            decided_at=decision.decided_at,
            decided_by=decision.decided_by,
            is_autonomous=decision.is_autonomous,
            was_escalated=decision.was_escalated,
            escalation_reasons=[r.value for r in decision.escalation_reasons]
            if decision.escalation_reasons
            else None,
            processing_time_ms=processing_time_ms,
            total_tokens_used=total_tokens,
        )

        self.session.add(db_decision)
        await self.session.flush()

        logger.info(
            "authorization_decision_created",
            decision_id=decision.decision_id,
            request_id=decision.request_id,
            outcome=decision.outcome.value,
        )

        return db_decision

    async def get_by_request_id(self, request_id: str) -> AuthorizationDecisionModel | None:
        """Get decision by request ID."""
        result = await self.session.execute(
            select(AuthorizationDecisionModel).where(
                AuthorizationDecisionModel.request_id == request_id
            )
        )
        return result.scalar_one_or_none()

    async def get_by_id(self, decision_id: str) -> AuthorizationDecisionModel | None:
        """Get decision by decision ID."""
        result = await self.session.execute(
            select(AuthorizationDecisionModel).where(
                AuthorizationDecisionModel.decision_id == decision_id
            )
        )
        return result.scalar_one_or_none()


class AuditRepository:
    """Repository for audit log operations."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def log(
        self,
        action: str,
        actor: str,
        actor_type: str,
        request_id: str | None = None,
        decision_id: str | None = None,
        correlation_id: str | None = None,
        details: dict[str, Any] | None = None,
        input_summary: str | None = None,
        output_summary: str | None = None,
        success: bool = True,
        error_message: str | None = None,
        duration_ms: int | None = None,
        token_usage: dict[str, int] | None = None,
    ) -> AuditLogModel:
        """
        Create an audit log entry.

        Args:
            action: The action performed
            actor: Who performed the action
            actor_type: Type of actor (agent, user, system)
            request_id: Related request ID
            decision_id: Related decision ID
            correlation_id: Correlation ID for tracing
            details: Additional details
            input_summary: Summary of input
            output_summary: Summary of output
            success: Whether action succeeded
            error_message: Error message if failed
            duration_ms: Duration in milliseconds
            token_usage: LLM token usage

        Returns:
            The created audit log entry
        """
        entry = AuditLogModel(
            entry_id=str(uuid7()),
            request_id=request_id,
            decision_id=decision_id,
            correlation_id=correlation_id,
            action=action,
            actor=actor,
            actor_type=actor_type,
            details=details,
            input_summary=input_summary,
            output_summary=output_summary,
            success=success,
            error_message=error_message,
            duration_ms=duration_ms,
            token_usage=token_usage,
        )

        self.session.add(entry)
        await self.session.flush()

        return entry

    async def get_by_request_id(
        self,
        request_id: str,
        limit: int = 100,
    ) -> list[AuditLogModel]:
        """Get audit logs for a request."""
        result = await self.session.execute(
            select(AuditLogModel)
            .where(AuditLogModel.request_id == request_id)
            .order_by(desc(AuditLogModel.timestamp))
            .limit(limit)
        )
        return list(result.scalars().all())


class GuidelineRepository:
    """Repository for clinical guideline operations."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(
        self,
        guideline_id: str,
        name: str,
        version: str,
        source: str,
        summary: str,
        effective_date: datetime,
        **kwargs: Any,
    ) -> GuidelineModel:
        """Create a new guideline record."""
        guideline = GuidelineModel(
            guideline_id=guideline_id,
            name=name,
            version=version,
            source=source,
            summary=summary,
            effective_date=effective_date,
            **kwargs,
        )

        self.session.add(guideline)
        await self.session.flush()

        return guideline

    async def get_by_id(self, guideline_id: str) -> GuidelineModel | None:
        """Get guideline by ID."""
        result = await self.session.execute(
            select(GuidelineModel).where(GuidelineModel.guideline_id == guideline_id)
        )
        return result.scalar_one_or_none()

    async def list_active(
        self,
        specialty: str | None = None,
        limit: int = 100,
    ) -> list[GuidelineModel]:
        """List active guidelines, optionally filtered by specialty."""
        query = select(GuidelineModel).where(GuidelineModel.is_active == True)

        # Note: specialty filtering would require JSONB contains operator
        # For simplicity, filtering by specialty is left for the application layer

        query = query.order_by(GuidelineModel.name).limit(limit)

        result = await self.session.execute(query)
        return list(result.scalars().all())
