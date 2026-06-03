"""Tests for the triage output models + UrgencyLevel + DecisionContext extension."""

import pytest
from pydantic import ValidationError

from pacca.agents.decision import DecisionContext
from pacca.models import ClassificationOutput, EvidenceOutput, UrgencyLevel
from pacca.models.clinical import ClinicalCase


def _case() -> ClinicalCase:
    return ClinicalCase(patient_id="P-TEST", primary_diagnosis_code="C34.1", procedure_code="J9271")


def test_urgency_level_values() -> None:
    assert {u.value for u in UrgencyLevel} == {"ROUTINE", "EXPEDITED", "URGENT"}


def test_evidence_output_validates() -> None:
    ev = EvidenceOutput(
        clinical_narrative="58yo, stage IV NSCLC.",
        key_findings=["PD-L1 high"],
        evidence_gaps=[],
        confidence_score=0.9,
    )
    assert ev.clinical_narrative.startswith("58yo")
    with pytest.raises(ValidationError):
        EvidenceOutput(
            clinical_narrative="x", key_findings=[], evidence_gaps=[], confidence_score=1.5
        )


def test_classification_output_validates_and_bounds_complexity() -> None:
    cl = ClassificationOutput(
        complexity=4,
        complexity_factors=["comorbid"],
        primary_specialty="oncology",
        urgency=UrgencyLevel.EXPEDITED,
        routing_rationale="complex case",
        confidence_score=0.8,
    )
    assert cl.complexity == 4 and cl.urgency is UrgencyLevel.EXPEDITED
    with pytest.raises(ValidationError):
        ClassificationOutput(
            complexity=6,
            complexity_factors=[],
            primary_specialty="x",
            urgency=UrgencyLevel.ROUTINE,
            routing_rationale="y",
            confidence_score=0.5,
        )


def test_decision_context_carries_triage_optional() -> None:
    ctx = DecisionContext(case=_case(), relevant_guidelines="")
    assert ctx.evidence is None and ctx.classification is None
    ev = EvidenceOutput(
        clinical_narrative="n", key_findings=[], evidence_gaps=[], confidence_score=0.7
    )
    cl = ClassificationOutput(
        complexity=2,
        complexity_factors=[],
        primary_specialty="cardiology",
        urgency=UrgencyLevel.ROUTINE,
        routing_rationale="r",
        confidence_score=0.7,
    )
    enriched = ctx.model_copy(update={"evidence": ev, "classification": cl})
    assert enriched.evidence is ev and enriched.classification is cl
