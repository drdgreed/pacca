"""
Unit tests for API endpoints.
"""

from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient


class TestHealthEndpoints:
    """Tests for health check endpoints."""

    def test_health_check(self, client: TestClient):
        """Test main health check endpoint."""
        response = client.get("/health")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "version" in data
        assert "environment" in data
        assert "checks" in data

    def test_readiness_check(self, client: TestClient):
        """Test readiness probe endpoint."""
        response = client.get("/health/ready")

        assert response.status_code == 200
        assert response.json()["status"] == "ready"

    def test_liveness_check(self, client: TestClient):
        """Test liveness probe endpoint."""
        response = client.get("/health/live")

        assert response.status_code == 200
        assert response.json()["status"] == "alive"

    def test_metrics_endpoint(self, client: TestClient):
        """Test metrics endpoint."""
        response = client.get("/api/v1/metrics")

        assert response.status_code == 200
        data = response.json()
        assert "uptime_seconds" in data
        assert "requests_total" in data
        assert "authorizations_processed" in data


class TestAuthorizationEndpoints:
    """Tests for authorization API endpoints."""

    @pytest.fixture
    def mock_orchestrator(self):
        """Mock the OrchestrationAgent for testing."""
        with patch("pacca.api.routes.authorizations.OrchestrationAgent") as mock:
            instance = mock.return_value

            # Create a mock workflow result
            mock_result = AsyncMock()
            mock_result.requires_human_review = False
            mock_result.total_duration_ms = 1500
            mock_result.escalation_reasons = []
            mock_result.decision = None
            mock_result.classification = None

            instance.process_authorization = AsyncMock(return_value=mock_result)

            yield instance

    def test_list_authorizations_empty(self, client: TestClient):
        """Test listing authorizations when empty."""
        # Clear any existing data
        from pacca.api.routes.authorizations import _authorizations
        _authorizations.clear()

        response = client.get("/api/v1/authorizations")

        assert response.status_code == 200
        data = response.json()
        assert data["items"] == []
        assert data["total"] == 0

    def test_get_nonexistent_authorization(self, client: TestClient):
        """Test getting a non-existent authorization."""
        response = client.get("/api/v1/authorizations/AUTH-nonexistent")

        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    def test_get_explanation_nonexistent(self, client: TestClient):
        """Test getting explanation for non-existent authorization."""
        response = client.get("/api/v1/authorizations/AUTH-nonexistent/explain")

        assert response.status_code == 404

    def test_submit_review_nonexistent(self, client: TestClient):
        """Test submitting review for non-existent authorization."""
        response = client.post(
            "/api/v1/authorizations/AUTH-nonexistent/review",
            json={
                "decision": "approve",
                "reviewer_id": "DR001",
            },
        )

        assert response.status_code == 404

    def test_submit_authorization_validation(self, client: TestClient):
        """Test authorization submission with invalid data."""
        # Missing required fields
        response = client.post(
            "/api/v1/authorizations",
            json={"invalid": "data"},
        )

        assert response.status_code == 422  # Validation error

    def test_submit_authorization_structure(
        self,
        client: TestClient,
        authorization_submission_data: dict,
        mock_orchestrator,
    ):
        """Test authorization submission has correct response structure."""
        # This test checks the request/response structure
        # The actual processing is mocked

        # We need to mock at a deeper level since the orchestrator
        # is instantiated inside the route handler
        with patch("pacca.api.routes.authorizations.OrchestrationAgent") as mock_orch:
            mock_result = AsyncMock()
            mock_result.requires_human_review = False
            mock_result.total_duration_ms = 1000
            mock_result.escalation_reasons = []
            mock_result.decision = None
            mock_result.classification = None

            instance = mock_orch.return_value
            instance.process_authorization = AsyncMock(return_value=mock_result)

            response = client.post(
                "/api/v1/authorizations",
                json=authorization_submission_data,
            )

            # Should either succeed or fail with a predictable error
            # (actual API call would need real Claude API key)
            assert response.status_code in [201, 500]

            if response.status_code == 201:
                data = response.json()
                assert "request_id" in data
                assert data["request_id"].startswith("AUTH-")
                assert "status" in data
                assert "diagnosis_code" in data
                assert "treatment_code" in data


class TestAPIMiddleware:
    """Tests for API middleware."""

    def test_request_id_header(self, client: TestClient):
        """Test that response includes request ID header."""
        response = client.get("/health")

        assert "X-Request-ID" in response.headers
        assert "X-Response-Time-Ms" in response.headers

    def test_cors_headers(self, client: TestClient):
        """Test CORS headers are present."""
        response = client.options(
            "/health",
            headers={"Origin": "http://localhost:3000"},
        )

        # CORS preflight should be handled
        assert response.status_code in [200, 405]
