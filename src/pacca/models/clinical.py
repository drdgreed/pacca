"""
Clinical data models for the PACCA system.

These models represent the clinical domain entities used in
prior authorization workflows: patients, diagnoses, treatments,
and clinical evidence.
"""

from datetime import date, datetime
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field

from pacca.models.enums import (
    ClinicalSpecialty,
    EvidenceQuality,
    EvidenceSource,
    TreatmentCategory,
)


# Type aliases for clarity
ICD10Code = Annotated[str, Field(pattern=r"^[A-Z]\d{2}(\.\d{1,4})?$", examples=["C34.1", "I25.10"])]
CPTCode = Annotated[str, Field(pattern=r"^\d{5}$", examples=["99213", "27447"])]
HCPCSCode = Annotated[str, Field(pattern=r"^[A-Z]\d{4}$", examples=["J9271", "E0601"])]
NDCCode = Annotated[str, Field(pattern=r"^\d{11}$", examples=["00006494101"])]


class PatientDemographics(BaseModel):
    """Basic patient demographic information."""

    model_config = ConfigDict(frozen=True)

    patient_id: str = Field(..., description="Unique patient identifier")
    date_of_birth: date = Field(..., description="Patient date of birth")
    gender: str = Field(..., description="Patient gender (M/F/O/U)")
    zip_code: str | None = Field(None, description="Patient ZIP code (first 3 digits only for privacy)")

    @property
    def age(self) -> int:
        """Calculate patient age in years."""
        today = date.today()
        return (
            today.year
            - self.date_of_birth.year
            - ((today.month, today.day) < (self.date_of_birth.month, self.date_of_birth.day))
        )

    @property
    def is_pediatric(self) -> bool:
        """Check if patient is pediatric (under 18)."""
        return self.age < 18

    @property
    def is_geriatric(self) -> bool:
        """Check if patient is geriatric (65 or older)."""
        return self.age >= 65


class Diagnosis(BaseModel):
    """
    Medical diagnosis information.

    Represents a clinical diagnosis with ICD-10 coding and metadata.
    """

    model_config = ConfigDict(frozen=True)

    code: str = Field(..., description="ICD-10 diagnosis code", examples=["C34.1", "I25.10"])
    description: str = Field(..., description="Human-readable diagnosis description")
    is_primary: bool = Field(True, description="Whether this is the primary diagnosis")
    onset_date: date | None = Field(None, description="Date of diagnosis onset")
    clinical_status: str = Field("active", description="Clinical status (active/resolved/recurrence)")

    @property
    def code_category(self) -> str:
        """Get the ICD-10 category (first character)."""
        return self.code[0] if self.code else ""

    @property
    def is_neoplasm(self) -> bool:
        """Check if this is a neoplasm diagnosis (C00-D49)."""
        return self.code_category in ("C", "D")


class Treatment(BaseModel):
    """
    Requested treatment or service for authorization.

    Represents the specific medical service, procedure, or medication
    being requested for prior authorization.
    """

    model_config = ConfigDict(frozen=True)

    code: str = Field(..., description="Treatment code (CPT, HCPCS, or NDC)")
    code_type: str = Field(..., description="Code type: CPT, HCPCS, NDC")
    description: str = Field(..., description="Human-readable treatment description")
    category: TreatmentCategory = Field(..., description="Treatment category")

    # Dosage/quantity information
    quantity: int | None = Field(None, description="Quantity requested")
    unit: str | None = Field(None, description="Unit of measure")
    frequency: str | None = Field(None, description="Frequency of administration")
    duration_days: int | None = Field(None, description="Duration in days")

    # Cost information
    estimated_cost: float | None = Field(None, description="Estimated cost in USD")

    # Clinical details
    route_of_administration: str | None = Field(None, description="Route (oral, IV, etc.)")
    site_of_service: str | None = Field(None, description="Where service will be provided")


class MedicationHistory(BaseModel):
    """Patient's medication history relevant to the authorization."""

    model_config = ConfigDict(frozen=True)

    medication_name: str = Field(..., description="Medication name")
    ndc_code: str | None = Field(None, description="NDC code if available")
    start_date: date | None = Field(None, description="Start date")
    end_date: date | None = Field(None, description="End date if discontinued")
    dosage: str | None = Field(None, description="Dosage")
    prescriber: str | None = Field(None, description="Prescribing provider")
    reason_discontinued: str | None = Field(None, description="Reason for discontinuation")
    was_effective: bool | None = Field(None, description="Whether treatment was effective")


class LabResult(BaseModel):
    """Laboratory test result."""

    model_config = ConfigDict(frozen=True)

    test_name: str = Field(..., description="Name of the lab test")
    test_code: str | None = Field(None, description="LOINC or CPT code")
    result_value: str = Field(..., description="Result value")
    unit: str | None = Field(None, description="Unit of measure")
    reference_range: str | None = Field(None, description="Normal reference range")
    is_abnormal: bool = Field(False, description="Whether result is abnormal")
    result_date: datetime = Field(..., description="Date/time of result")


class ImagingStudy(BaseModel):
    """Imaging study information."""

    model_config = ConfigDict(frozen=True)

    study_type: str = Field(..., description="Type of imaging (MRI, CT, X-ray, etc.)")
    body_site: str = Field(..., description="Body site imaged")
    study_date: datetime = Field(..., description="Date of study")
    findings_summary: str | None = Field(None, description="Summary of findings")
    impression: str | None = Field(None, description="Radiologist impression")
    accession_number: str | None = Field(None, description="Study accession number")


class ClinicalNote(BaseModel):
    """Clinical note or documentation."""

    model_config = ConfigDict(frozen=True)

    note_type: str = Field(..., description="Type of note (progress, consultation, etc.)")
    author: str = Field(..., description="Note author/provider")
    author_specialty: ClinicalSpecialty | None = Field(None, description="Author's specialty")
    note_date: datetime = Field(..., description="Date of note")
    content: str = Field(..., description="Note content/text")


class PriorTreatment(BaseModel):
    """Record of prior treatment attempt."""

    model_config = ConfigDict(frozen=True)

    treatment_name: str = Field(..., description="Treatment name")
    treatment_code: str | None = Field(None, description="Treatment code")
    start_date: date = Field(..., description="Start date")
    end_date: date | None = Field(None, description="End date")
    outcome: str = Field(..., description="Treatment outcome")
    reason_stopped: str | None = Field(None, description="Reason treatment was stopped")
    side_effects: list[str] = Field(default_factory=list, description="Documented side effects")


class ClinicalEvidence(BaseModel):
    """
    Aggregated clinical evidence for an authorization request.

    This model represents the complete clinical picture assembled
    by the Evidence Aggregation Agent from multiple data sources.
    """

    model_config = ConfigDict(frozen=True)

    # Source tracking
    sources: list[EvidenceSource] = Field(default_factory=list, description="Data sources used")
    gathered_at: datetime = Field(..., description="When evidence was gathered")

    # Clinical history
    medication_history: list[MedicationHistory] = Field(
        default_factory=list, description="Relevant medication history"
    )
    prior_treatments: list[PriorTreatment] = Field(
        default_factory=list, description="Prior treatment attempts"
    )

    # Diagnostic data
    lab_results: list[LabResult] = Field(default_factory=list, description="Relevant lab results")
    imaging_studies: list[ImagingStudy] = Field(
        default_factory=list, description="Relevant imaging studies"
    )

    # Clinical documentation
    clinical_notes: list[ClinicalNote] = Field(
        default_factory=list, description="Relevant clinical notes"
    )

    # Comorbidities and allergies
    comorbidities: list[Diagnosis] = Field(default_factory=list, description="Comorbid conditions")
    allergies: list[str] = Field(default_factory=list, description="Documented allergies")
    contraindications: list[str] = Field(
        default_factory=list, description="Known contraindications"
    )

    # Quality assessment
    overall_quality: EvidenceQuality = Field(
        EvidenceQuality.MODERATE, description="Overall evidence quality"
    )
    missing_elements: list[str] = Field(
        default_factory=list, description="Missing evidence elements"
    )
    quality_notes: str | None = Field(None, description="Notes on evidence quality")

    @property
    def has_step_therapy_history(self) -> bool:
        """Check if there's evidence of prior treatment attempts (step therapy)."""
        return len(self.prior_treatments) > 0 or len(self.medication_history) > 0

    @property
    def has_recent_labs(self) -> bool:
        """Check if there are recent lab results (within 30 days)."""
        if not self.lab_results:
            return False
        cutoff = datetime.now().replace(tzinfo=None)
        for lab in self.lab_results:
            lab_date = lab.result_date.replace(tzinfo=None)
            if (cutoff - lab_date).days <= 30:
                return True
        return False


class ClinicalNarrative(BaseModel):
    """
    AI-generated clinical narrative summarizing the case.

    This is produced by the Evidence Aggregation Agent to provide
    a structured summary for clinical decision-making.
    """

    model_config = ConfigDict(frozen=True)

    patient_summary: str = Field(..., description="Brief patient summary")
    clinical_history: str = Field(..., description="Relevant clinical history narrative")
    current_condition: str = Field(..., description="Current condition and symptoms")
    treatment_rationale: str = Field(..., description="Rationale for requested treatment")
    prior_treatments_summary: str | None = Field(None, description="Summary of prior treatments")
    supporting_evidence: str = Field(..., description="Key supporting clinical evidence")
    contraindications_notes: str | None = Field(None, description="Any contraindication concerns")
    generated_at: datetime = Field(..., description="When narrative was generated")
