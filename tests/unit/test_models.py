"""
Unit tests for data models.
"""

from datetime import date, datetime

import pytest

from pacca.models import (
    AuthorizationRequest,
    AuthorizationStatus,
    ComplexityLevel,
    Diagnosis,
    PatientDemographics,
    Treatment,
    TreatmentCategory,
    UrgencyLevel,
)


class TestPatientDemographics:
    """Tests for PatientDemographics model."""

    def test_age_calculation(self):
        """Test that age is calculated correctly."""
        # Patient born 30 years ago
        birth_date = date(date.today().year - 30, 1, 1)
        patient = PatientDemographics(
            patient_id="P001",
            date_of_birth=birth_date,
            gender="M",
        )
        assert patient.age == 30

    def test_pediatric_flag(self):
        """Test pediatric flag for patients under 18."""
        # Child patient
        birth_date = date(date.today().year - 10, 1, 1)
        child = PatientDemographics(
            patient_id="P002",
            date_of_birth=birth_date,
            gender="F",
        )
        assert child.is_pediatric is True
        assert child.is_geriatric is False

    def test_geriatric_flag(self):
        """Test geriatric flag for patients 65+."""
        birth_date = date(date.today().year - 70, 1, 1)
        senior = PatientDemographics(
            patient_id="P003",
            date_of_birth=birth_date,
            gender="M",
        )
        assert senior.is_geriatric is True
        assert senior.is_pediatric is False


class TestDiagnosis:
    """Tests for Diagnosis model."""

    def test_code_category(self):
        """Test ICD-10 code category extraction."""
        diagnosis = Diagnosis(
            code="C34.1",
            description="Lung cancer",
        )
        assert diagnosis.code_category == "C"

    def test_neoplasm_detection(self):
        """Test neoplasm diagnosis detection."""
        cancer = Diagnosis(code="C34.1", description="Lung cancer")
        benign = Diagnosis(code="D12.0", description="Benign neoplasm")
        other = Diagnosis(code="I25.10", description="Heart disease")

        assert cancer.is_neoplasm is True
        assert benign.is_neoplasm is True
        assert other.is_neoplasm is False


class TestTreatment:
    """Tests for Treatment model."""

    def test_treatment_creation(self):
        """Test treatment model creation."""
        treatment = Treatment(
            code="J9271",
            code_type="HCPCS",
            description="Pembrolizumab",
            category=TreatmentCategory.MEDICATION,
            estimated_cost=15000.00,
        )

        assert treatment.code == "J9271"
        assert treatment.category == TreatmentCategory.MEDICATION
        assert treatment.estimated_cost == 15000.00


class TestAuthorizationStatus:
    """Tests for AuthorizationStatus enum."""

    def test_terminal_states(self):
        """Test terminal state detection."""
        assert AuthorizationStatus.APPROVED.is_terminal() is True
        assert AuthorizationStatus.DENIED.is_terminal() is True
        assert AuthorizationStatus.WITHDRAWN.is_terminal() is True
        assert AuthorizationStatus.PENDING_REVIEW.is_terminal() is False
        assert AuthorizationStatus.EVALUATING.is_terminal() is False

    def test_processing_states(self):
        """Test processing state detection."""
        assert AuthorizationStatus.EVALUATING.is_processing() is True
        assert AuthorizationStatus.CLASSIFYING.is_processing() is True
        assert AuthorizationStatus.APPROVED.is_processing() is False


class TestComplexityLevel:
    """Tests for ComplexityLevel enum."""

    def test_human_review_requirement(self):
        """Test human review requirement by complexity."""
        assert ComplexityLevel.ROUTINE.requires_human_review is False
        assert ComplexityLevel.LOW.requires_human_review is False
        assert ComplexityLevel.MODERATE.requires_human_review is True
        assert ComplexityLevel.HIGH.requires_human_review is True
        assert ComplexityLevel.CRITICAL.requires_human_review is True

    def test_specialist_requirement(self):
        """Test specialist requirement by complexity."""
        assert ComplexityLevel.ROUTINE.requires_specialist is False
        assert ComplexityLevel.HIGH.requires_specialist is False
        assert ComplexityLevel.CRITICAL.requires_specialist is True


class TestUrgencyLevel:
    """Tests for UrgencyLevel enum."""

    def test_max_hours(self):
        """Test max processing hours by urgency."""
        assert UrgencyLevel.ROUTINE.max_hours == 48
        assert UrgencyLevel.EXPEDITED.max_hours == 24
        assert UrgencyLevel.URGENT.max_hours == 8
        assert UrgencyLevel.EMERGENT.max_hours == 1


class TestAuthorizationRequest:
    """Tests for AuthorizationRequest model."""

    def test_request_creation(self, sample_authorization_request):
        """Test authorization request creation."""
        request = sample_authorization_request
        assert request.request_id.startswith("AUTH-")
        assert request.status == AuthorizationStatus.SUBMITTED

    def test_high_cost_detection(
        self,
        sample_patient,
        sample_diagnosis,
        sample_provider,
        sample_payer,
    ):
        """Test high-cost authorization detection."""
        # Low cost treatment
        low_cost = Treatment(
            code="99213",
            code_type="CPT",
            description="Office visit",
            category=TreatmentCategory.PROCEDURE,
            estimated_cost=150.00,
        )

        # High cost treatment
        high_cost = Treatment(
            code="33361",
            code_type="CPT",
            description="TAVR procedure",
            category=TreatmentCategory.PROCEDURE,
            estimated_cost=150000.00,
        )

        low_cost_request = AuthorizationRequest(
            patient=sample_patient,
            primary_diagnosis=sample_diagnosis,
            requested_treatment=low_cost,
            requesting_provider=sample_provider,
            payer=sample_payer,
        )

        high_cost_request = AuthorizationRequest(
            patient=sample_patient,
            primary_diagnosis=sample_diagnosis,
            requested_treatment=high_cost,
            requesting_provider=sample_provider,
            payer=sample_payer,
        )

        assert low_cost_request.is_high_cost is False
        assert high_cost_request.is_high_cost is True

    def test_status_update(self, sample_authorization_request):
        """Test status update functionality."""
        request = sample_authorization_request
        original_updated_at = request.updated_at

        # Small delay to ensure timestamp changes
        import time
        time.sleep(0.01)

        request.update_status(AuthorizationStatus.EVALUATING)

        assert request.status == AuthorizationStatus.EVALUATING
        assert request.updated_at > original_updated_at
