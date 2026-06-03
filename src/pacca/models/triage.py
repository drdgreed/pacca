"""Output models for the pre-decision triage agents (Evidence + Classification).

These live in models/ (a leaf) so both decision.py's DecisionContext and the
agents can import them without a circular import.
"""

from pydantic import BaseModel, Field

from .enums import UrgencyLevel


class EvidenceOutput(BaseModel):
    """Synthesized evidence summary produced by the EvidenceAggregationAgent."""

    clinical_narrative: str
    key_findings: list[str] = Field(default_factory=list)
    evidence_gaps: list[str] = Field(default_factory=list)
    confidence_score: float = Field(ge=0.0, le=1.0)


class ClassificationOutput(BaseModel):
    """Triage classification produced by the ClinicalClassificationAgent.

    `complexity` is an integer 1-5 (consistent with the detector's
    _compute_complexity_score and the SDD) — advisory only; the detector's
    deterministic complexity remains authoritative for pre-flight gating.
    """

    complexity: int = Field(ge=1, le=5)
    complexity_factors: list[str] = Field(default_factory=list)
    primary_specialty: str
    urgency: UrgencyLevel
    routing_rationale: str
    confidence_score: float = Field(ge=0.0, le=1.0)
