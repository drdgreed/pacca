"""
Pytest configuration and shared fixtures.
"""

from datetime import date, datetime
from typing import Generator
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from pacca.api.main import app
from pacca.models import (
    AuthorizationRequest,
    AuthorizationStatus,
    Diagnosis,
    PatientDemographics,
    PayerInfo,
    ProviderInfo,
    Treatment,
    TreatmentCategory,
    UrgencyLevel,
)


@pytest.fixture
def client() -> Generator[TestClient, None, None]:
    """Create a test client for the FastAPI application."""
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def sample_patient() -> PatientDemographics:
    """Create a sample patient for testing."""
    return PatientDemographics(
        patient_id="P12345",
        date_of_birth=date(1966, 5, 15),  # 58 years old
        gender="M",
        zip_code="902",
    )


@pytest.fixture
def sample_diagnosis() -> Diagnosis:
    """Create a sample diagnosis for testing."""
    return Diagnosis(
        code="C34.1",
        description="Malignant neoplasm of upper lobe, bronchus or lung",
        is_primary=True,
        onset_date=date(2025, 10, 1),
    )


@pytest.fixture
def sample_treatment() -> Treatment:
    """Create a sample treatment for testing."""
    return Treatment(
        code="J9271",
        code_type="HCPCS",
        description="Pembrolizumab injection",
        category=TreatmentCategory.MEDICATION,
        quantity=1,
        estimated_cost=15000.00,
    )


@pytest.fixture
def sample_provider() -> ProviderInfo:
    """Create a sample provider for testing."""
    return ProviderInfo(
        provider_id="1234567890",
        provider_name="Dr. Jane Smith",
        facility_name="City Medical Center",
    )


@pytest.fixture
def sample_payer() -> PayerInfo:
    """Create a sample payer for testing."""
    return PayerInfo(
        payer_id="BCBS001",
        payer_name="Blue Cross Blue Shield",
        member_id="MEM123456",
        plan_name="Gold PPO",
    )


@pytest.fixture
def sample_authorization_request(
    sample_patient: PatientDemographics,
    sample_diagnosis: Diagnosis,
    sample_treatment: Treatment,
    sample_provider: ProviderInfo,
    sample_payer: PayerInfo,
) -> AuthorizationRequest:
    """Create a sample authorization request for testing."""
    return AuthorizationRequest(
        patient=sample_patient,
        primary_diagnosis=sample_diagnosis,
        secondary_diagnoses=[],
        requested_treatment=sample_treatment,
        requesting_provider=sample_provider,
        payer=sample_payer,
        clinical_notes="Patient with stage IIIA NSCLC, PD-L1 TPS ≥50%, ECOG PS 1.",
        urgency=UrgencyLevel.ROUTINE,
    )


@pytest.fixture
def mock_anthropic_client():
    """Mock the Anthropic client for testing without API calls."""
    with patch("pacca.agents.base.anthropic.Anthropic") as mock:
        client_instance = MagicMock()
        mock.return_value = client_instance

        # Mock the messages.create response
        mock_response = MagicMock()
        mock_response.content = [
            MagicMock(type="text", text='{"test": "response"}')
        ]
        mock_response.usage = MagicMock(input_tokens=100, output_tokens=50)

        client_instance.messages.create.return_value = mock_response

        yield client_instance


@pytest.fixture
def authorization_submission_data() -> dict:
    """Create sample authorization submission data for API testing."""
    return {
        "patient": {
            "id": "P12345",
            "date_of_birth": "1966-05-15",
            "gender": "M",
            "zip_code": "902",
        },
        "diagnosis": {
            "code": "C34.1",
            "description": "Malignant neoplasm of upper lobe, bronchus or lung",
            "is_primary": True,
        },
        "treatment": {
            "code": "J9271",
            "code_type": "HCPCS",
            "description": "Pembrolizumab injection",
            "category": "medication",
            "estimated_cost": 15000.00,
        },
        "provider": {
            "provider_id": "1234567890",
            "provider_name": "Dr. Jane Smith",
            "facility_name": "City Medical Center",
        },
        "payer": {
            "payer_id": "BCBS001",
            "payer_name": "Blue Cross Blue Shield",
            "member_id": "MEM123456",
        },
        "clinical_notes": "Patient with stage IIIA NSCLC, PD-L1 TPS ≥50%.",
        "urgency": "routine",
    }
