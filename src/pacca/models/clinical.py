from datetime import datetime
from typing import List, Optional
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
    evidence: List[EvidenceItem] = []
