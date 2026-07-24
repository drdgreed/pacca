"""
SQLAlchemy database models for the PACCA system.

These models define the database schema for persisting
authorization requests, decisions, and audit logs.
"""

from datetime import datetime
from typing import Any

from sqlalchemy import (
    JSON,
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

# Cross-dialect JSON: SQLite + asyncpg both get a sane default, while
# PostgreSQL deployments still get the indexable JSONB type.
# Replaces the previous JSONB-only annotation, which crashed at
# create_all on any SQLite-backed environment (local dev default).
_JSON_VARIANT = JSON().with_variant(JSONB(), "postgresql")


class Base(DeclarativeBase):
    """Base class for all database models."""

    type_annotation_map = {
        dict[str, Any]: _JSON_VARIANT,
    }


class AuthorizationRequestModel(Base):
    """Database model for authorization requests."""

    __tablename__ = "authorization_requests"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    request_id: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    external_reference: Mapped[str | None] = mapped_column(String(100), nullable=True)

    # Status
    status: Mapped[str] = mapped_column(String(30), index=True, default="submitted")

    # Patient info (de-identified for storage)
    patient_id: Mapped[str] = mapped_column(String(50), index=True)
    # Nullable: the minimal submission API (AuthorizationRequest + ClinicalCase)
    # does not collect gender, or descriptions/category/provider-name/payer fields.
    # Honest NULL beats fabricated audit data — see the P-4 persistence repair /
    # migration 002. Populate as upstream systems provide these fields.
    patient_age: Mapped[int | None] = mapped_column(Integer, nullable=True)
    patient_gender: Mapped[str | None] = mapped_column(String(10), nullable=True)

    # Clinical info
    primary_diagnosis_code: Mapped[str] = mapped_column(String(20), index=True)
    primary_diagnosis_description: Mapped[str | None] = mapped_column(Text, nullable=True)
    secondary_diagnoses: Mapped[dict[str, Any] | None] = mapped_column(_JSON_VARIANT, nullable=True)

    # Treatment info
    treatment_code: Mapped[str] = mapped_column(String(20), index=True)
    treatment_description: Mapped[str | None] = mapped_column(Text, nullable=True)
    treatment_category: Mapped[str | None] = mapped_column(String(30), nullable=True)
    estimated_cost: Mapped[float | None] = mapped_column(Float, nullable=True)

    # Provider and payer
    provider_id: Mapped[str] = mapped_column(String(50))
    provider_name: Mapped[str | None] = mapped_column(String(200), nullable=True)
    payer_id: Mapped[str | None] = mapped_column(String(50), index=True, nullable=True)
    payer_name: Mapped[str | None] = mapped_column(String(200), nullable=True)
    member_id: Mapped[str | None] = mapped_column(String(50), nullable=True)

    # Clinical context
    clinical_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    urgency: Mapped[str] = mapped_column(String(20), default="routine")

    # Processing metadata
    complexity: Mapped[int | None] = mapped_column(Integer, nullable=True)
    assigned_specialty: Mapped[str | None] = mapped_column(String(50), nullable=True)
    evidence_quality: Mapped[str | None] = mapped_column(String(20), nullable=True)

    # Evidence and narrative (stored as JSON)
    evidence_data: Mapped[dict[str, Any] | None] = mapped_column(_JSON_VARIANT, nullable=True)
    narrative_data: Mapped[dict[str, Any] | None] = mapped_column(_JSON_VARIANT, nullable=True)

    # Timestamps
    submitted_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), index=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), onupdate=func.now())

    # Relationships
    decision: Mapped["AuthorizationDecisionModel | None"] = relationship(
        "AuthorizationDecisionModel", back_populates="request", uselist=False
    )
    audit_logs: Mapped[list["AuditLogModel"]] = relationship(
        "AuditLogModel", back_populates="request"
    )

    def __repr__(self) -> str:
        return f"<AuthorizationRequest(request_id={self.request_id}, status={self.status})>"


class AuthorizationDecisionModel(Base):
    """Database model for authorization decisions."""

    __tablename__ = "authorization_decisions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    decision_id: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    request_id: Mapped[str] = mapped_column(
        String(50), ForeignKey("authorization_requests.request_id"), index=True
    )

    # Decision
    outcome: Mapped[str] = mapped_column(String(30), index=True)
    confidence_score: Mapped[float] = mapped_column(Float)

    # Rationale (stored as JSON)
    rationale_data: Mapped[dict[str, Any] | None] = mapped_column(_JSON_VARIANT, nullable=True)

    # Conditions
    conditions: Mapped[dict[str, Any] | None] = mapped_column(_JSON_VARIANT, nullable=True)
    required_actions: Mapped[dict[str, Any] | None] = mapped_column(_JSON_VARIANT, nullable=True)

    # Validity
    effective_date: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    expiration_date: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    authorized_quantity: Mapped[int | None] = mapped_column(Integer, nullable=True)
    authorized_duration_days: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # Processing metadata
    decided_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())
    decided_by: Mapped[str] = mapped_column(String(100), default="system")
    is_autonomous: Mapped[bool] = mapped_column(Boolean, default=True)
    was_escalated: Mapped[bool] = mapped_column(Boolean, default=False)
    escalation_reasons: Mapped[dict[str, Any] | None] = mapped_column(_JSON_VARIANT, nullable=True)

    # Token usage tracking
    total_tokens_used: Mapped[int | None] = mapped_column(Integer, nullable=True)
    processing_time_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # Relationships
    request: Mapped[AuthorizationRequestModel] = relationship(
        "AuthorizationRequestModel", back_populates="decision"
    )
    reviews: Mapped[list["HumanReviewModel"]] = relationship(
        "HumanReviewModel", back_populates="decision"
    )

    def __repr__(self) -> str:
        return f"<AuthorizationDecision(decision_id={self.decision_id}, outcome={self.outcome})>"


class HumanReviewModel(Base):
    """Database model for human reviews of decisions."""

    __tablename__ = "human_reviews"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    review_id: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    decision_id: Mapped[str] = mapped_column(
        String(50), ForeignKey("authorization_decisions.decision_id"), index=True
    )
    request_id: Mapped[str] = mapped_column(String(50), index=True)

    # Reviewer info
    reviewer_id: Mapped[str] = mapped_column(String(50), index=True)
    reviewer_role: Mapped[str] = mapped_column(String(30))

    # Review details
    original_outcome: Mapped[str] = mapped_column(String(30))
    final_outcome: Mapped[str] = mapped_column(String(30))
    outcome_changed: Mapped[bool] = mapped_column(Boolean, default=False)

    # Assessment
    agrees_with_rationale: Mapped[bool] = mapped_column(Boolean)
    reviewer_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    additional_rationale: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Quality feedback
    ai_accuracy_rating: Mapped[int | None] = mapped_column(Integer, nullable=True)
    feedback_tags: Mapped[dict[str, Any] | None] = mapped_column(_JSON_VARIANT, nullable=True)

    # Timestamps
    reviewed_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())
    time_spent_seconds: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # Relationships
    decision: Mapped[AuthorizationDecisionModel] = relationship(
        "AuthorizationDecisionModel", back_populates="reviews"
    )

    def __repr__(self) -> str:
        return f"<HumanReview(review_id={self.review_id}, reviewer_id={self.reviewer_id})>"


class AuditLogModel(Base):
    """Database model for audit logs."""

    __tablename__ = "audit_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    entry_id: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime, default=func.now(), index=True)

    # Context
    request_id: Mapped[str | None] = mapped_column(
        String(50),
        # B3: DEFERRABLE INITIALLY DEFERRED so Postgres checks this FK at COMMIT,
        # not per-statement. The submit route writes two request_id-bearing audit
        # rows (intent.declared, authorization_submitted) BEFORE the parent
        # authorization_requests row — because intent.declared must be the first
        # audit event (pre-write-audit invariant). Deferring the check to commit
        # keeps both invariants: audit-first ordering AND referential integrity.
        ForeignKey(
            "authorization_requests.request_id",
            deferrable=True,
            initially="DEFERRED",
        ),
        nullable=True,
        index=True,
    )
    decision_id: Mapped[str | None] = mapped_column(String(50), nullable=True)
    correlation_id: Mapped[str | None] = mapped_column(String(50), nullable=True, index=True)

    # Action details
    action: Mapped[str] = mapped_column(String(100), index=True)
    actor: Mapped[str] = mapped_column(String(100))
    actor_type: Mapped[str] = mapped_column(String(30))  # agent, user, system

    # Data
    details: Mapped[dict[str, Any] | None] = mapped_column(_JSON_VARIANT, nullable=True)
    input_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    output_summary: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Status
    success: Mapped[bool] = mapped_column(Boolean, default=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Performance
    duration_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    token_usage: Mapped[dict[str, Any] | None] = mapped_column(_JSON_VARIANT, nullable=True)

    # Relationships
    request: Mapped[AuthorizationRequestModel | None] = relationship(
        "AuthorizationRequestModel", back_populates="audit_logs"
    )

    def __repr__(self) -> str:
        return f"<AuditLog(entry_id={self.entry_id}, action={self.action})>"


class GuidelineModel(Base):
    """Database model for clinical guidelines (metadata only, content in vector store)."""

    __tablename__ = "guidelines"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    guideline_id: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(500))
    version: Mapped[str] = mapped_column(String(20))

    # Source
    source: Mapped[str] = mapped_column(String(100), index=True)
    source_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    evidence_level: Mapped[str | None] = mapped_column(String(20), nullable=True)

    # Scope
    specialties: Mapped[dict[str, Any] | None] = mapped_column(_JSON_VARIANT, nullable=True)
    treatment_categories: Mapped[dict[str, Any] | None] = mapped_column(
        _JSON_VARIANT, nullable=True
    )
    applicable_diagnoses: Mapped[dict[str, Any] | None] = mapped_column(
        _JSON_VARIANT, nullable=True
    )

    # Content summary
    summary: Mapped[str] = mapped_column(Text)

    # Validity
    effective_date: Mapped[datetime] = mapped_column(DateTime)
    expiration_date: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, index=True)

    # Metadata
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), onupdate=func.now())
    tags: Mapped[dict[str, Any] | None] = mapped_column(_JSON_VARIANT, nullable=True)

    # Vector store reference
    vector_store_ids: Mapped[dict[str, Any] | None] = mapped_column(
        _JSON_VARIANT, nullable=True
    )  # IDs of chunks in vector store

    def __repr__(self) -> str:
        return f"<Guideline(guideline_id={self.guideline_id}, name={self.name})>"
