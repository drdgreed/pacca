"""Pure-function tests for Tier-1 confidence branch selection (PRD §5.4)."""

import pytest

from pacca.agents.orchestrator import select_confidence_branch
from pacca.models.authorization import AuthorizationStatus


@pytest.mark.parametrize(
    "confidence,status,auto,esc,expected",
    [
        (0.96, AuthorizationStatus.AUTO_APPROVED, 0.95, 0.90, "auto_approve"),
        (0.93, AuthorizationStatus.AUTO_APPROVED, 0.95, 0.90, "medical_director"),
        (0.80, AuthorizationStatus.AUTO_APPROVED, 0.95, 0.90, "human_review"),
        # High confidence but the agent did NOT auto-approve → not Branch 1.
        (0.97, AuthorizationStatus.IN_REVIEW, 0.95, 0.90, "human_review"),
        # Tunability proof: lowering auto to 0.92 flips a 0.93 case to Branch 1.
        (0.93, AuthorizationStatus.AUTO_APPROVED, 0.92, 0.90, "auto_approve"),
        # Exact boundaries — lock in >= auto and the inclusive lower bound of the MD band.
        (0.95, AuthorizationStatus.AUTO_APPROVED, 0.95, 0.90, "auto_approve"),
        (0.90, AuthorizationStatus.AUTO_APPROVED, 0.95, 0.90, "medical_director"),
    ],
)
def test_select_confidence_branch(
    confidence: float,
    status: AuthorizationStatus,
    auto: float,
    esc: float,
    expected: str,
) -> None:
    assert select_confidence_branch(confidence, status, auto, esc) == expected
