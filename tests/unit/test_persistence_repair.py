"""Round-trip tests for the repaired persistence layer.

Before this repair, AuthorizationRepository.create / DecisionRepository.create
referenced a richer request/decision model that the current API models do not
have — they would AttributeError and were never called. These tests persist a
real request + decision against an in-memory SQLite schema (built from the
models via create_all) and read them back, proving the mapping works and that
fields the minimal API does not collect are stored as NULL, not fabricated.
"""

import pytest
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from pacca.db.models import Base
from pacca.db.repository import AuthorizationRepository, DecisionRepository
from pacca.models.authorization import AuthorizationDecision, AuthorizationRequest
from pacca.models.clinical import ClinicalCase, EvidenceItem
from pacca.models.enums import AuthorizationStatus, EvidenceSourceType, ReviewTier


@pytest.fixture
async def session():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    maker = async_sessionmaker(engine, expire_on_commit=False)
    async with maker() as s:
        yield s
    await engine.dispose()


def _request() -> AuthorizationRequest:
    return AuthorizationRequest(
        request_id="AUTH-RT-001",
        patient_id="P-RT-001",
        provider_npi="1234567890",
        clinical_case=ClinicalCase(
            patient_id="P-RT-001",
            primary_diagnosis_code="C34.1",
            procedure_code="J9271",
            patient_age=61,
            complexity_score=3,
            evidence=[
                EvidenceItem(
                    id="e1",
                    source_type=EvidenceSourceType.CLINICAL_NOTE,
                    description="Stage IIIA NSCLC",
                    original_text="Patient presents with stage IIIA NSCLC.",
                    confidence=0.95,
                )
            ],
        ),
    )


@pytest.mark.asyncio
async def test_request_round_trips_with_null_for_uncollected_fields(session):
    repo = AuthorizationRepository(session)
    await repo.create(_request())
    await session.commit()

    row = await repo.get_by_id("AUTH-RT-001")
    assert row is not None
    # Mapped from the minimal API + ClinicalCase.
    assert row.patient_id == "P-RT-001"
    assert row.patient_age == 61
    assert row.primary_diagnosis_code == "C34.1"
    assert row.treatment_code == "J9271"  # <- procedure_code
    assert row.provider_id == "1234567890"  # <- provider_npi
    assert row.complexity == 3
    assert row.evidence_data["evidence"][0]["id"] == "e1"
    # Uncollected fields are NULL (honest), not fabricated.
    assert row.patient_gender is None
    assert row.primary_diagnosis_description is None
    assert row.treatment_category is None
    assert row.provider_name is None
    assert row.payer_id is None and row.member_id is None
    # Defaults still apply.
    assert row.status == "submitted"
    assert row.urgency == "routine"


@pytest.mark.asyncio
async def test_decision_round_trips_and_derives_flags(session):
    # A request must exist first (decision.request_id FKs to it).
    await AuthorizationRepository(session).create(_request())
    decision = AuthorizationDecision(
        decision_id="DEC-RT-001",
        status=AuthorizationStatus.IN_REVIEW,
        confidence_score=0.72,
        rationale="Insufficient documentation of prior therapy.",
        review_tier_used=ReviewTier.HUMAN,
    )
    repo = DecisionRepository(session)
    await repo.create(decision, request_id="AUTH-RT-001", processing_time_ms=1234)
    await session.commit()

    row = await repo.get_by_id("DEC-RT-001")
    assert row is not None
    assert row.request_id == "AUTH-RT-001"
    assert row.outcome == "IN_REVIEW"  # <- status.value
    assert row.confidence_score == 0.72
    assert row.rationale_data == {"text": "Insufficient documentation of prior therapy."}
    assert row.decided_by == "HUMAN"  # <- review_tier_used.value
    assert row.is_autonomous is False  # HUMAN tier
    assert row.was_escalated is True  # IN_REVIEW status
    assert row.processing_time_ms == 1234
