"""
Tests for src/pacca/api/websockets/draft_stream.py.

Uses FastAPI TestClient's WebSocket support. Mocks the LLM agent so
tests are hermetic + fast.

Covers:
- Auth-first-message protocol
- Session-not-found close (4404)
- Successful draft round-trip (`done` event)
- LLM failure (`error` event + close)
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import TYPE_CHECKING
from unittest.mock import patch

import pytest
from jose import jwt
from starlette.testclient import WebSocketTestSession  # noqa: F401 — type hint

from pacca.agents.sme_authoring.models import CaseDraftResponse
from pacca.api.auth import ALGORITHM, SECRET_KEY

if TYPE_CHECKING:
    from fastapi.testclient import TestClient

    pass


def _make_token(sub: str = "test-user") -> str:
    """Build a valid JWT for the auth-first-message."""
    payload = {
        "sub": sub,
        "exp": datetime.now(UTC) + timedelta(minutes=5),
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def _valid_draft() -> CaseDraftResponse:
    return CaseDraftResponse(
        case_id="GC-101",
        title="Mocked draft from WebSocket test fixture for assertion purposes",
        diagnosis_code="C34.1",
        diagnosis_description="Malignant neoplasm of lung",
        procedure_code="J9271",
        procedure_description="Pembrolizumab injection",
        clinical_notes=(
            "65-year-old male with stage IV NSCLC, PD-L1 70%, no EGFR/ALK. "
            "Oncology recommending first-line pembrolizumab per NCCN."
        ),
        guidelines_context=(
            "NCCN NSCLC Guidelines: pembrolizumab monotherapy is Category 1 "
            "first-line for metastatic NSCLC with PD-L1 >= 50%."
        ),
        expected_outcome="AUTO_APPROVED",
        expected_branch="BRANCH_1_AUTO_APPROVE",
        reasoning_must_include=["NCCN", "PD-L1"],
        clinical_rationale=("Metastatic NSCLC with high PD-L1, NCCN Category 1. Clean approve."),
        judge_scoring_criteria=("Score highly if rationale cites PD-L1 + NCCN Category 1."),
    )


@pytest.fixture
def session_id(client: TestClient, auth_headers, tmp_session_dir) -> str:
    """Create a session via the REST API + return its ID."""
    resp = client.post(
        "/api/v1/sme-authoring/sessions",
        headers=auth_headers,
        json={
            "scenario": {
                "description": (
                    "65yo male with stage IV NSCLC requesting first-line pembrolizumab per NCCN."
                ),
            },
            "mode": "sandbox",
        },
    )
    return resp.json()["session"]["session_id"]


# =============================================================================
# Auth protocol
# =============================================================================


class TestAuthProtocol:
    def test_missing_first_message_closes_4401(
        self,
        client: TestClient,
        session_id: str,
    ) -> None:
        url = f"/api/v1/sme-authoring/sessions/{session_id}/draft-stream"
        # Connect + immediately close without sending auth
        with client.websocket_connect(url) as ws:
            # Server should emit an error event then close
            event = ws.receive_json()
            assert event["type"] == "error"
            assert "auth" in event["message"].lower()

    def test_invalid_token_closes_4401(
        self,
        client: TestClient,
        session_id: str,
    ) -> None:
        url = f"/api/v1/sme-authoring/sessions/{session_id}/draft-stream"
        with client.websocket_connect(url) as ws:
            ws.send_json({"type": "auth", "token": "not-a-real-jwt"})
            event = ws.receive_json()
            assert event["type"] == "error"
            assert "invalid" in event["message"].lower() or "jwt" in event["message"].lower()


# =============================================================================
# Session-not-found
# =============================================================================


class TestSessionLookup:
    def test_nonexistent_session_closes_4404(
        self,
        client: TestClient,
        tmp_session_dir,
    ) -> None:
        url = "/api/v1/sme-authoring/sessions/does-not-exist/draft-stream"
        with client.websocket_connect(url) as ws:
            ws.send_json({"type": "auth", "token": _make_token()})
            event = ws.receive_json()
            assert event["type"] == "error"
            assert "not found" in event["message"].lower()


# =============================================================================
# Successful draft round-trip
# =============================================================================


class TestSuccessfulDraft:
    def test_draft_emits_done_event(
        self,
        client: TestClient,
        session_id: str,
    ) -> None:
        url = f"/api/v1/sme-authoring/sessions/{session_id}/draft-stream"

        async def _mock_run(self, request):
            return _valid_draft().model_copy(update={"case_id": request.allocated_case_id})

        with (
            patch(
                "pacca.api.websockets.draft_stream.SMECaseAuthoringAgent.run",
                new=_mock_run,
            ),
            patch(
                "pacca.api.websockets.draft_stream.next_id",
                return_value="GC-200",
            ),
            client.websocket_connect(url) as ws,
        ):
            ws.send_json({"type": "auth", "token": _make_token()})
            event = ws.receive_json()
            assert event["type"] == "done"
            assert event["allocated_case_id"] == "GC-200"
            assert event["draft"]["case_id"] == "GC-200"


# =============================================================================
# LLM failure path
# =============================================================================


class TestLLMFailure:
    def test_llm_error_emits_error_event(
        self,
        client: TestClient,
        session_id: str,
    ) -> None:
        url = f"/api/v1/sme-authoring/sessions/{session_id}/draft-stream"

        async def _failing_run(self, request):
            raise RuntimeError("simulated LLM API failure")

        with (
            patch(
                "pacca.api.websockets.draft_stream.SMECaseAuthoringAgent.run",
                new=_failing_run,
            ),
            patch(
                "pacca.api.websockets.draft_stream.next_id",
                return_value="GC-300",
            ),
            client.websocket_connect(url) as ws,
        ):
            ws.send_json({"type": "auth", "token": _make_token()})
            event = ws.receive_json()
            assert event["type"] == "error"
            assert "simulated LLM API failure" in event["message"]
            assert event["recoverable"] is True
