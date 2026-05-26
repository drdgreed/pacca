"""
Tests for src/pacca/api/routes/sme_authoring.py — the SME Authoring API.

Strategy:
- Use FastAPI TestClient with a valid JWT (auth_headers fixture).
- Patch SME-authoring library functions where the test needs to control
  behavior (LLM calls, integrity tests).
- Tmp-dir session storage so tests don't touch ~/.pacca/.

Covers all 11 REST endpoints. WebSocket tests live in
test_sme_authoring_websocket.py.
"""

from __future__ import annotations

from typing import TYPE_CHECKING
from unittest.mock import patch

import pytest

from pacca.agents.sme_authoring.models import (
    CaseDraftResponse,
)

if TYPE_CHECKING:
    from fastapi.testclient import TestClient


# =============================================================================
# Helpers
# =============================================================================


def _valid_scenario() -> dict:
    return {
        "description": (
            "65yo male with stage IV NSCLC PD-L1 70% requesting first-line pembrolizumab per NCCN."
        ),
        "intended_specialty": "oncology",
        "intended_outcome": "AUTO_APPROVED",
        "failure_mode_label": "Coverage",
    }


def _valid_draft_dict() -> dict:
    return {
        "case_id": "GC-101",
        "title": "Mocked NSCLC pembrolizumab case for unit testing purposes",
        "diagnosis_code": "C34.1",
        "diagnosis_description": "Malignant neoplasm of lung",
        "procedure_code": "J9271",
        "procedure_description": "Pembrolizumab injection",
        "clinical_notes": (
            "65-year-old male with stage IV NSCLC, PD-L1 70%, no EGFR/ALK. "
            "Oncology recommending first-line pembrolizumab per NCCN."
        ),
        "guidelines_context": (
            "NCCN NSCLC Guidelines: pembrolizumab monotherapy is Category 1 "
            "first-line for metastatic NSCLC with PD-L1 >= 50%."
        ),
        "expected_outcome": "AUTO_APPROVED",
        "expected_branch": "BRANCH_1_AUTO_APPROVE",
        "reasoning_must_include": ["NCCN", "PD-L1", "first-line"],
        "reasoning_must_not_include": [],
        "prior_denial_codes": [],
        "clinical_rationale": (
            "Metastatic NSCLC with high PD-L1 and no driver mutations. "
            "Pembrolizumab is NCCN Category 1. Clean auto-approval."
        ),
        "judge_scoring_criteria": (
            "Score highly if rationale cites PD-L1 percentage and the NCCN Category 1 designation."
        ),
    }


# =============================================================================
# Auth gate
# =============================================================================


class TestAuthGate:
    def test_unauthenticated_get_status_returns_401(self, client: TestClient) -> None:
        response = client.get("/api/v1/sme-authoring/status")
        assert response.status_code == 401

    def test_invalid_token_returns_401(self, client: TestClient) -> None:
        response = client.get(
            "/api/v1/sme-authoring/status",
            headers={"Authorization": "Bearer not-a-valid-jwt"},
        )
        assert response.status_code == 401


# =============================================================================
# Session CRUD
# =============================================================================


class TestSessionCreate:
    def test_create_session_returns_201(
        self,
        client: TestClient,
        auth_headers: dict[str, str],
        tmp_session_dir,
    ) -> None:
        response = client.post(
            "/api/v1/sme-authoring/sessions",
            headers=auth_headers,
            json={"scenario": _valid_scenario(), "mode": "sandbox"},
        )
        assert response.status_code == 201, response.text
        body = response.json()
        assert body["kind"] == "session"
        assert body["session"]["mode"] == "sandbox"
        assert body["session"]["scenario"]["description"].startswith("65yo male")

    def test_create_session_defaults_to_sandbox(
        self,
        client: TestClient,
        auth_headers: dict[str, str],
        tmp_session_dir,
    ) -> None:
        response = client.post(
            "/api/v1/sme-authoring/sessions",
            headers=auth_headers,
            json={"scenario": _valid_scenario()},
        )
        assert response.status_code == 201
        assert response.json()["session"]["mode"] == "sandbox"

    def test_create_session_validates_scenario_min_length(
        self,
        client: TestClient,
        auth_headers: dict[str, str],
        tmp_session_dir,
    ) -> None:
        response = client.post(
            "/api/v1/sme-authoring/sessions",
            headers=auth_headers,
            json={"scenario": {"description": "tiny"}, "mode": "sandbox"},
        )
        assert response.status_code == 422  # Pydantic validation error


class TestSessionList:
    def test_empty_list(
        self,
        client: TestClient,
        auth_headers: dict[str, str],
        tmp_session_dir,
    ) -> None:
        response = client.get("/api/v1/sme-authoring/sessions", headers=auth_headers)
        assert response.status_code == 200
        body = response.json()
        assert body["kind"] == "session_list"
        assert body["total"] == 0
        assert body["sessions"] == []

    def test_create_then_list(
        self,
        client: TestClient,
        auth_headers: dict[str, str],
        tmp_session_dir,
    ) -> None:
        client.post(
            "/api/v1/sme-authoring/sessions",
            headers=auth_headers,
            json={"scenario": _valid_scenario(), "mode": "sandbox"},
        )
        response = client.get("/api/v1/sme-authoring/sessions", headers=auth_headers)
        assert response.status_code == 200
        assert response.json()["total"] == 1


class TestSessionGet:
    def test_get_missing_returns_404(
        self,
        client: TestClient,
        auth_headers: dict[str, str],
        tmp_session_dir,
    ) -> None:
        response = client.get(
            "/api/v1/sme-authoring/sessions/does-not-exist",
            headers=auth_headers,
        )
        assert response.status_code == 404

    def test_get_existing_returns_session(
        self,
        client: TestClient,
        auth_headers: dict[str, str],
        tmp_session_dir,
    ) -> None:
        create_resp = client.post(
            "/api/v1/sme-authoring/sessions",
            headers=auth_headers,
            json={"scenario": _valid_scenario(), "mode": "sandbox"},
        )
        session_id = create_resp.json()["session"]["session_id"]
        response = client.get(f"/api/v1/sme-authoring/sessions/{session_id}", headers=auth_headers)
        assert response.status_code == 200
        assert response.json()["session"]["session_id"] == session_id


class TestSessionDelete:
    def test_delete_existing_returns_204(
        self,
        client: TestClient,
        auth_headers: dict[str, str],
        tmp_session_dir,
    ) -> None:
        create_resp = client.post(
            "/api/v1/sme-authoring/sessions",
            headers=auth_headers,
            json={"scenario": _valid_scenario(), "mode": "sandbox"},
        )
        session_id = create_resp.json()["session"]["session_id"]
        response = client.delete(
            f"/api/v1/sme-authoring/sessions/{session_id}", headers=auth_headers
        )
        assert response.status_code == 204

    def test_delete_missing_returns_404(
        self,
        client: TestClient,
        auth_headers: dict[str, str],
        tmp_session_dir,
    ) -> None:
        response = client.delete(
            "/api/v1/sme-authoring/sessions/does-not-exist",
            headers=auth_headers,
        )
        assert response.status_code == 404


# =============================================================================
# Drafting (mocked LLM)
# =============================================================================


@pytest.fixture
def mock_llm_draft():
    """Patch SMECaseAuthoringAgent.run to return a deterministic draft."""

    async def _run(self, request) -> CaseDraftResponse:
        return CaseDraftResponse(**{**_valid_draft_dict(), "case_id": request.allocated_case_id})

    with patch(
        "pacca.api.routes.sme_authoring.SMECaseAuthoringAgent.run",
        new=_run,
    ):
        yield


class TestDraft:
    def test_draft_returns_case(
        self,
        client: TestClient,
        auth_headers: dict[str, str],
        tmp_session_dir,
        mock_llm_draft,
        tmp_path,
    ) -> None:
        # Patch the case-dir + allocator state to a clean tmp_path
        with patch(
            "pacca.api.routes.sme_authoring.next_id",
            return_value="GC-101",
        ):
            create_resp = client.post(
                "/api/v1/sme-authoring/sessions",
                headers=auth_headers,
                json={"scenario": _valid_scenario(), "mode": "sandbox"},
            )
            session_id = create_resp.json()["session"]["session_id"]
            response = client.post(
                f"/api/v1/sme-authoring/sessions/{session_id}/draft",
                headers=auth_headers,
            )
        assert response.status_code == 200, response.text
        body = response.json()
        assert body["kind"] == "draft"
        assert body["allocated_case_id"] == "GC-101"
        assert body["draft"]["case_id"] == "GC-101"


# =============================================================================
# Validate
# =============================================================================


class TestValidate:
    def test_validate_clean_draft(
        self,
        client: TestClient,
        auth_headers: dict[str, str],
        tmp_session_dir,
    ) -> None:
        create_resp = client.post(
            "/api/v1/sme-authoring/sessions",
            headers=auth_headers,
            json={"scenario": _valid_scenario(), "mode": "sandbox"},
        )
        session_id = create_resp.json()["session"]["session_id"]
        response = client.post(
            f"/api/v1/sme-authoring/sessions/{session_id}/validate",
            headers=auth_headers,
            json={"draft": _valid_draft_dict()},
        )
        assert response.status_code == 200
        body = response.json()
        assert body["kind"] == "validation"
        assert body["blocking_count"] == 0
        assert len(body["reports"]) == 6

    def test_validate_phi_draft_blocks(
        self,
        client: TestClient,
        auth_headers: dict[str, str],
        tmp_session_dir,
    ) -> None:
        create_resp = client.post(
            "/api/v1/sme-authoring/sessions",
            headers=auth_headers,
            json={"scenario": _valid_scenario(), "mode": "sandbox"},
        )
        session_id = create_resp.json()["session"]["session_id"]
        phi_draft = {
            **_valid_draft_dict(),
            "clinical_notes": (
                "65-year-old male SSN 123-45-6789 with stage IV NSCLC "
                "requesting first-line pembrolizumab per NCCN guidelines."
            ),
        }
        response = client.post(
            f"/api/v1/sme-authoring/sessions/{session_id}/validate",
            headers=auth_headers,
            json={"draft": phi_draft},
        )
        assert response.status_code == 200
        body = response.json()
        assert body["blocking_count"] >= 1

    def test_validate_no_draft_returns_400(
        self,
        client: TestClient,
        auth_headers: dict[str, str],
        tmp_session_dir,
    ) -> None:
        create_resp = client.post(
            "/api/v1/sme-authoring/sessions",
            headers=auth_headers,
            json={"scenario": _valid_scenario(), "mode": "sandbox"},
        )
        session_id = create_resp.json()["session"]["session_id"]
        response = client.post(
            f"/api/v1/sme-authoring/sessions/{session_id}/validate",
            headers=auth_headers,
            json={},
        )
        assert response.status_code == 400


# =============================================================================
# Commit (sandbox mode only — production mode requires real fs writes)
# =============================================================================


class TestCommit:
    def test_sandbox_commit_returns_pr_template_without_writing(
        self,
        client: TestClient,
        auth_headers: dict[str, str],
        tmp_session_dir,
    ) -> None:
        create_resp = client.post(
            "/api/v1/sme-authoring/sessions",
            headers=auth_headers,
            json={"scenario": _valid_scenario(), "mode": "sandbox"},
        )
        session_id = create_resp.json()["session"]["session_id"]
        response = client.post(
            f"/api/v1/sme-authoring/sessions/{session_id}/commit",
            headers=auth_headers,
            json={
                "sme_attestation": (
                    "I attest this case is clinically accurate per my professional judgment."
                ),
                "draft": _valid_draft_dict(),
            },
        )
        assert response.status_code == 200
        body = response.json()
        assert body["kind"] == "commit"
        assert body["written"] is False  # sandbox mode
        assert body["pr_title"]
        assert "GC-101" in body["pr_body"]

    def test_production_commit_without_confirm_returns_400(
        self,
        client: TestClient,
        auth_headers: dict[str, str],
        tmp_session_dir,
    ) -> None:
        create_resp = client.post(
            "/api/v1/sme-authoring/sessions",
            headers=auth_headers,
            json={"scenario": _valid_scenario(), "mode": "production"},
        )
        session_id = create_resp.json()["session"]["session_id"]
        response = client.post(
            f"/api/v1/sme-authoring/sessions/{session_id}/commit",
            headers=auth_headers,
            json={
                "sme_attestation": "Test attestation that is long enough.",
                "draft": _valid_draft_dict(),
            },
        )
        assert response.status_code == 400
        assert "confirm_production_write" in response.json()["detail"]


# =============================================================================
# Status / discovery
# =============================================================================


class TestStatus:
    def test_status_returns_dataset_state(
        self,
        client: TestClient,
        auth_headers: dict[str, str],
    ) -> None:
        # Status endpoint reads docs/EVALUATION_COVERAGE.md from cwd
        response = client.get("/api/v1/sme-authoring/status", headers=auth_headers)
        assert response.status_code == 200
        body = response.json()
        assert body["kind"] == "status"
        assert "total_cases" in body
        assert isinstance(body["per_list_counts"], list)


class TestBatches:
    def test_list_batches(self, client: TestClient, auth_headers: dict[str, str]) -> None:
        response = client.get("/api/v1/sme-authoring/batches", headers=auth_headers)
        assert response.status_code == 200
        body = response.json()
        assert body["kind"] == "batch_list"
        assert isinstance(body["batches"], list)

    def test_get_missing_batch_returns_404(
        self, client: TestClient, auth_headers: dict[str, str]
    ) -> None:
        response = client.get("/api/v1/sme-authoring/batches/ZZZ", headers=auth_headers)
        assert response.status_code == 404


class TestGaps:
    def test_list_gaps_default_top(self, client: TestClient, auth_headers: dict[str, str]) -> None:
        response = client.get("/api/v1/sme-authoring/gaps", headers=auth_headers)
        assert response.status_code == 200
        body = response.json()
        assert body["kind"] == "gap_list"

    def test_list_gaps_with_top_limit(
        self, client: TestClient, auth_headers: dict[str, str]
    ) -> None:
        response = client.get("/api/v1/sme-authoring/gaps?top=2", headers=auth_headers)
        assert response.status_code == 200
        body = response.json()
        assert len(body["gaps"]) <= 2
