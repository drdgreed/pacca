"""Tests for the triage output models (EvidenceOutput, ClassificationOutput) + UrgencyLevel."""

import pytest
from pydantic import ValidationError

from pacca.models import ClassificationOutput, EvidenceOutput, UrgencyLevel


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
