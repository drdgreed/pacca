"""
Demo scenarios for the PACCA system.

Provides pre-configured clinical scenarios that showcase
different authorization pathways and decision types.
"""

from datetime import date, datetime, timedelta

from pacca.models import (
    AuthorizationRequest,
    ClinicalEvidence,
    Diagnosis,
    EvidenceQuality,
    EvidenceSource,
    LabResult,
    MedicationHistory,
    PatientDemographics,
    PayerInfo,
    PriorTreatment,
    ProviderInfo,
    Treatment,
    TreatmentCategory,
    UrgencyLevel,
)


def create_routine_imaging_scenario() -> AuthorizationRequest:
    """
    Scenario 1: Routine Imaging Request

    Expected outcome: AUTO-APPROVED (high confidence, low complexity)
    """
    patient = PatientDemographics(
        patient_id="DEMO-001",
        date_of_birth=date(1980, 3, 15),
        gender="F",
        zip_code="900",
    )

    diagnosis = Diagnosis(
        code="M54.5",
        description="Low back pain",
        is_primary=True,
        onset_date=date.today() - timedelta(days=45),
    )

    treatment = Treatment(
        code="72148",
        code_type="CPT",
        description="MRI lumbar spine without contrast",
        category=TreatmentCategory.IMAGING,
        quantity=1,
        estimated_cost=1200.00,
    )

    provider = ProviderInfo(
        provider_id="1234567890",
        provider_name="Dr. Sarah Johnson",
        facility_name="Community Health Center",
    )

    payer = PayerInfo(
        payer_id="BCBS001",
        payer_name="Blue Cross Blue Shield",
        member_id="DEMO123456",
        plan_name="Standard PPO",
    )

    evidence = ClinicalEvidence(
        sources=[EvidenceSource.EHR, EvidenceSource.PROVIDER_NOTES],
        gathered_at=datetime.utcnow(),
        medication_history=[
            MedicationHistory(
                medication_name="Ibuprofen 800mg",
                start_date=date.today() - timedelta(days=30),
                dosage="800mg TID",
                was_effective=False,
            ),
        ],
        prior_treatments=[
            PriorTreatment(
                treatment_name="Physical Therapy",
                start_date=date.today() - timedelta(days=60),
                end_date=date.today() - timedelta(days=30),
                outcome="Partial improvement, continued symptoms",
            ),
        ],
        overall_quality=EvidenceQuality.HIGH,
    )

    return AuthorizationRequest(
        patient=patient,
        primary_diagnosis=diagnosis,
        requested_treatment=treatment,
        requesting_provider=provider,
        payer=payer,
        clinical_notes=(
            "44-year-old female with persistent low back pain x 6 weeks. "
            "Failed conservative management including NSAIDs and physical therapy. "
            "MRI indicated to rule out disc herniation."
        ),
        urgency=UrgencyLevel.ROUTINE,
        evidence=evidence,
    )


def create_oncology_treatment_scenario() -> AuthorizationRequest:
    """
    Scenario 2: Oncology Immunotherapy Request

    Expected outcome: APPROVED WITH REVIEW (medium complexity)
    """
    patient = PatientDemographics(
        patient_id="DEMO-002",
        date_of_birth=date(1958, 8, 22),
        gender="M",
        zip_code="902",
    )

    diagnosis = Diagnosis(
        code="C34.1",
        description="Malignant neoplasm of upper lobe, bronchus or lung",
        is_primary=True,
        onset_date=date.today() - timedelta(days=60),
    )

    treatment = Treatment(
        code="J9271",
        code_type="HCPCS",
        description="Pembrolizumab (Keytruda) 200mg IV",
        category=TreatmentCategory.MEDICATION,
        quantity=6,
        estimated_cost=90000.00,
        frequency="Every 3 weeks",
        duration_days=126,
    )

    provider = ProviderInfo(
        provider_id="9876543210",
        provider_name="Dr. Michael Chen",
        facility_name="Regional Cancer Center",
    )

    payer = PayerInfo(
        payer_id="AETNA001",
        payer_name="Aetna",
        member_id="DEMO789012",
        plan_name="Premium Plus",
    )

    evidence = ClinicalEvidence(
        sources=[EvidenceSource.EHR, EvidenceSource.LAB, EvidenceSource.IMAGING],
        gathered_at=datetime.utcnow(),
        lab_results=[
            LabResult(
                test_name="PD-L1 Expression (TPS)",
                test_code="88360",
                result_value="65%",
                reference_range="<1% negative, ≥50% high",
                is_abnormal=False,
                result_date=datetime.utcnow() - timedelta(days=14),
            ),
            LabResult(
                test_name="EGFR Mutation",
                result_value="Negative",
                is_abnormal=False,
                result_date=datetime.utcnow() - timedelta(days=14),
            ),
        ],
        comorbidities=[
            Diagnosis(code="I10", description="Essential hypertension", is_primary=False),
        ],
        overall_quality=EvidenceQuality.HIGH,
    )

    return AuthorizationRequest(
        patient=patient,
        primary_diagnosis=diagnosis,
        requested_treatment=treatment,
        requesting_provider=provider,
        payer=payer,
        clinical_notes=(
            "66-year-old male with Stage IIIA NSCLC. PD-L1 TPS 65%. "
            "EGFR/ALK negative. ECOG PS 1. Requesting first-line pembrolizumab "
            "per NCCN guidelines for PD-L1 ≥50%."
        ),
        urgency=UrgencyLevel.EXPEDITED,
        evidence=evidence,
    )


def create_incomplete_documentation_scenario() -> AuthorizationRequest:
    """
    Scenario 3: Incomplete Documentation Request

    Expected outcome: REQUEST_MORE_INFO (missing critical evidence)
    """
    patient = PatientDemographics(
        patient_id="DEMO-003",
        date_of_birth=date(1990, 4, 20),
        gender="M",
        zip_code="750",
    )

    diagnosis = Diagnosis(
        code="M79.3",
        description="Panniculitis, unspecified",
        is_primary=True,
    )

    treatment = Treatment(
        code="J1745",
        code_type="HCPCS",
        description="Infliximab (Remicade) infusion",
        category=TreatmentCategory.MEDICATION,
        quantity=6,
        estimated_cost=30000.00,
    )

    provider = ProviderInfo(
        provider_id="7777777777",
        provider_name="Dr. Robert Lee",
        facility_name="Metro Dermatology Clinic",
    )

    payer = PayerInfo(
        payer_id="CIGNA001",
        payer_name="Cigna",
        member_id="DEMO901234",
        plan_name="Open Access Plus",
    )

    evidence = ClinicalEvidence(
        sources=[EvidenceSource.PROVIDER_NOTES],
        gathered_at=datetime.utcnow(),
        overall_quality=EvidenceQuality.INSUFFICIENT,
        missing_elements=[
            "Biopsy results confirming diagnosis",
            "Prior treatment history",
            "TB screening results",
            "Hepatitis B/C screening",
        ],
    )

    return AuthorizationRequest(
        patient=patient,
        primary_diagnosis=diagnosis,
        requested_treatment=treatment,
        requesting_provider=provider,
        payer=payer,
        clinical_notes="Patient with skin condition. Requesting biologic therapy.",
        urgency=UrgencyLevel.ROUTINE,
        evidence=evidence,
    )


# Export all scenarios
DEMO_SCENARIOS = {
    "routine_imaging": {
        "name": "Routine Imaging (MRI)",
        "description": "Low-complexity imaging request with good documentation",
        "expected_outcome": "AUTO-APPROVED",
        "factory": create_routine_imaging_scenario,
    },
    "oncology_treatment": {
        "name": "Oncology Immunotherapy",
        "description": "Cancer treatment with biomarker-guided therapy",
        "expected_outcome": "APPROVED (with review)",
        "factory": create_oncology_treatment_scenario,
    },
    "incomplete_docs": {
        "name": "Incomplete Documentation",
        "description": "Request missing critical clinical evidence",
        "expected_outcome": "REQUEST_MORE_INFO",
        "factory": create_incomplete_documentation_scenario,
    },
}


def get_scenario(name: str) -> AuthorizationRequest:
    """Get a demo scenario by name."""
    if name not in DEMO_SCENARIOS:
        available = ", ".join(DEMO_SCENARIOS.keys())
        raise ValueError(f"Unknown scenario: {name}. Available: {available}")
    return DEMO_SCENARIOS[name]["factory"]()


def list_scenarios() -> list[dict]:
    """List all available demo scenarios."""
    return [
        {
            "id": key,
            "name": value["name"],
            "description": value["description"],
            "expected_outcome": value["expected_outcome"],
        }
        for key, value in DEMO_SCENARIOS.items()
    ]
