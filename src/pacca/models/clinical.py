from datetime import datetime

from pydantic import BaseModel, Field

from .enums import EvidenceSourceType


class EvidenceItem(BaseModel):
    id: str
    source_type: EvidenceSourceType
    description: str
    original_text: str
    confidence: float
    timestamp: datetime = Field(default_factory=datetime.now)


class ClinicalCase(BaseModel):
    patient_id: str
    primary_diagnosis_code: str
    procedure_code: str
    evidence: list[EvidenceItem] = []
    # iter-3 chg-1: structured fields for branch_2_medical_director triggers
    # (HIGH_COST and PEDIATRIC_COMPLEX). Optional — the detector reads these
    # first, falling back to parsing clinical_notes when None. This hybrid
    # keeps existing test cases working unchanged and lets upstream systems
    # populate the structured fields as they become available.
    estimated_annual_cost: float | None = None
    patient_age: int | None = None
    disease_severity: str | None = None  # e.g. "severe", "moderate-to-severe"
    # iter-5 chg-3: integer 1-5 complexity score for the pediatric_complex
    # check. Matches the Settings schema (complexity_auto_approve_max=2,
    # complexity_specialist_review_min=4). Optional — the detector computes
    # it from notes if not provided.
    complexity_score: int | None = Field(default=None, ge=1, le=5)
