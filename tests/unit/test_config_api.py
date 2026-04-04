"""
Tests for the Config API (GET/PATCH/DELETE /api/v1/admin/config).

These tests verify:
  1. GET /config returns all tunable parameters with correct values
  2. PATCH /config applies overrides immediately
  3. Overrides are reflected in subsequent GET calls
  4. Invalid threshold relationships are rejected with clear errors
  5. DELETE /config/overrides clears all overrides
  6. The metrics endpoint reflects current effective values

Teaching note — testing configuration APIs:
  Config APIs have a tricky testing property: they share state between
  tests via the module-level _config_overrides dict. We need to reset
  that dict before each test so tests don't pollute each other.

  This is done with a pytest fixture that patches _config_overrides
  to an empty dict before each test and restores it after. The fixture
  uses `autouse=True` so it runs automatically for every test in this
  module without you having to remember to include it.

Teaching note — why test configuration validation?
  The most dangerous config change in a clinical AI system is accidentally
  setting auto_approve_threshold <= escalation_threshold. This collapses
  the Medical Director escalation band to zero — no cases would ever
  escalate to Tier 2. The validation test ensures this is caught
  immediately with a clear error message rather than silently breaking
  the escalation tree.
"""

import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient


# =============================================================================
# Test setup
# =============================================================================

@pytest.fixture(autouse=True)
def reset_config_overrides():
    """
    Reset runtime config overrides before and after every test.

    This prevents test pollution: a PATCH in one test must not affect
    subsequent tests. The `autouse=True` means this runs for every
    test in this file automatically.
    """
    import pacca.api.routes.admin as admin_module
    # Clear before the test
    admin_module._config_overrides.clear()
    yield
    # Clear after the test (cleanup)
    admin_module._config_overrides.clear()


@pytest.fixture
def admin_client():
    """
    FastAPI test client for admin routes only.

    We test the router directly rather than through the full app
    to avoid needing JWT authentication in every test.
    """
    from fastapi import FastAPI
    from pacca.api.routes.admin import router

    app = FastAPI()
    app.include_router(router, prefix="/api/v1/admin")
    return TestClient(app)


# =============================================================================
# GET /config tests
# =============================================================================

class TestGetConfig:

    def test_returns_all_required_fields(self, admin_client):
        """
        GET /config must return a complete snapshot of all tunable parameters.

        A recruiter or technical reviewer opening the Swagger UI should see
        every operational knob documented and readable.
        """
        response = admin_client.get("/api/v1/admin/config")
        assert response.status_code == 200

        data = response.json()
        required_fields = [
            "auto_approve_confidence_threshold",
            "escalation_confidence_threshold",
            "high_cost_threshold",
            "complexity_auto_approve_max",
            "llm_retry_max_attempts",
            "llm_retry_wait_min_seconds",
            "llm_retry_wait_max_seconds",
            "otel_enabled",
            "enable_autonomous_decisions",
            "overrides_active",
        ]
        for field in required_fields:
            assert field in data, (
                f"GET /config response missing field '{field}'. "
                f"All tunable parameters must be visible to operators."
            )

    def test_overrides_active_empty_on_fresh_start(self, admin_client):
        """
        With no runtime overrides applied, overrides_active must be empty.
        """
        response = admin_client.get("/api/v1/admin/config")
        assert response.status_code == 200
        assert response.json()["overrides_active"] == [], (
            "No overrides should be active on a fresh config state."
        )

    def test_confidence_thresholds_are_in_valid_range(self, admin_client):
        """
        Default threshold values must satisfy the constraint:
        auto_approve > escalation (otherwise the MD escalation band is empty).
        """
        response = admin_client.get("/api/v1/admin/config")
        data = response.json()

        auto = data["auto_approve_confidence_threshold"]
        esc = data["escalation_confidence_threshold"]

        assert 0.5 <= auto <= 1.0, f"auto_approve threshold {auto} out of range"
        assert 0.3 <= esc <= 1.0, f"escalation threshold {esc} out of range"
        assert auto > esc, (
            f"auto_approve ({auto}) must be > escalation ({esc}). "
            f"If equal, the Medical Director escalation band is empty."
        )


# =============================================================================
# PATCH /config tests
# =============================================================================

class TestPatchConfig:

    def test_patch_updates_single_field(self, admin_client):
        """
        PATCH with one field should update only that field.
        Other fields must retain their original values.
        """
        # Get baseline
        baseline = admin_client.get("/api/v1/admin/config").json()
        original_retry = baseline["llm_retry_max_attempts"]

        # Update only retry attempts
        response = admin_client.patch(
            "/api/v1/admin/config",
            json={"llm_retry_max_attempts": 5},
        )
        assert response.status_code == 200

        updated = response.json()
        assert updated["llm_retry_max_attempts"] == 5, (
            "PATCH should update the specified field to the new value."
        )
        # All other fields should be unchanged
        assert updated["auto_approve_confidence_threshold"] == \
               baseline["auto_approve_confidence_threshold"], (
            "PATCH should not affect fields not included in the request."
        )

    def test_patch_override_reflected_in_subsequent_get(self, admin_client):
        """
        After PATCH, GET /config must return the overridden value.

        This verifies the in-memory override store is read correctly
        by the GET endpoint.
        """
        admin_client.patch(
            "/api/v1/admin/config",
            json={"high_cost_threshold": 50000},
        )
        get_response = admin_client.get("/api/v1/admin/config")
        assert get_response.json()["high_cost_threshold"] == 50000

    def test_patch_shows_overridden_fields_in_overrides_active(self, admin_client):
        """
        After PATCH, overrides_active must list the overridden field names.

        This gives operators visibility into which settings have been
        changed at runtime (vs. loaded from environment variables).
        """
        admin_client.patch(
            "/api/v1/admin/config",
            json={
                "llm_retry_max_attempts": 5,
                "enable_autonomous_decisions": False,
            },
        )
        get_response = admin_client.get("/api/v1/admin/config")
        overrides = get_response.json()["overrides_active"]

        assert "llm_retry_max_attempts" in overrides
        assert "enable_autonomous_decisions" in overrides

    def test_disable_autonomous_decisions_immediately(self, admin_client):
        """
        Setting enable_autonomous_decisions=False must take effect immediately.

        Real-world scenario: an incident is discovered and the operator
        needs to disable all autonomous approvals with one API call.
        This is the 'kill switch' test.
        """
        response = admin_client.patch(
            "/api/v1/admin/config",
            json={"enable_autonomous_decisions": False},
        )
        assert response.status_code == 200
        assert response.json()["enable_autonomous_decisions"] is False

        # Verify it persists in subsequent GET
        get_response = admin_client.get("/api/v1/admin/config")
        assert get_response.json()["enable_autonomous_decisions"] is False

    def test_patch_empty_body_changes_nothing(self, admin_client):
        """
        PATCH with an empty body (all None fields) must change nothing.
        """
        baseline = admin_client.get("/api/v1/admin/config").json()
        admin_client.patch("/api/v1/admin/config", json={})
        after = admin_client.get("/api/v1/admin/config").json()

        assert after["auto_approve_confidence_threshold"] == \
               baseline["auto_approve_confidence_threshold"]
        assert after["overrides_active"] == []


# =============================================================================
# Validation tests — rejected configurations
# =============================================================================

class TestConfigValidation:

    def test_rejects_auto_approve_below_escalation_threshold(self, admin_client):
        """
        CRITICAL: auto_approve_threshold must always be > escalation_threshold.

        If auto_approve <= escalation, the Medical Director escalation band
        collapses. Cases that should go to the MD Agent would instead route
        directly to human review, bypassing the Tier 2 agent entirely.

        This is the most dangerous misconfiguration possible — it silently
        breaks the escalation tree. The API must reject it clearly.
        """
        # Get current escalation threshold
        current = admin_client.get("/api/v1/admin/config").json()
        escalation = current["escalation_confidence_threshold"]

        # Try to set auto_approve BELOW escalation — must be rejected
        response = admin_client.patch(
            "/api/v1/admin/config",
            json={"auto_approve_confidence_threshold": escalation - 0.05},
        )
        assert response.status_code == 422, (
            f"Setting auto_approve ({escalation - 0.05}) <= escalation ({escalation}) "
            f"must be rejected with 422. The escalation band would collapse to nothing."
        )
        assert "escalation band" in response.json()["detail"].lower() or \
               "greater than" in response.json()["detail"].lower(), (
            "Error message should explain the escalation band constraint."
        )

    def test_rejects_equal_thresholds(self, admin_client):
        """
        Equal auto_approve and escalation thresholds must also be rejected.
        An empty escalation band (zero-width) is as broken as an inverted one.
        """
        current = admin_client.get("/api/v1/admin/config").json()
        escalation = current["escalation_confidence_threshold"]

        response = admin_client.patch(
            "/api/v1/admin/config",
            json={"auto_approve_confidence_threshold": escalation},
        )
        assert response.status_code == 422

    def test_rejects_retry_min_above_max(self, admin_client):
        """
        llm_retry_wait_min_seconds must not exceed llm_retry_wait_max_seconds.
        """
        response = admin_client.patch(
            "/api/v1/admin/config",
            json={
                "llm_retry_wait_min_seconds": 60.0,
                "llm_retry_wait_max_seconds": 5.0,
            },
        )
        assert response.status_code == 422

    def test_invalid_update_does_not_partially_apply(self, admin_client):
        """
        If a PATCH is rejected, NONE of its fields should be applied.
        A failed update must be atomic — all or nothing.

        Without this guarantee, a rejected PATCH could leave the system
        in a partially-updated state.
        """
        # Attempt a batch update where one value is valid but the threshold
        # relationship makes the overall update invalid
        current = admin_client.get("/api/v1/admin/config").json()
        original_retry = current["llm_retry_max_attempts"]
        escalation = current["escalation_confidence_threshold"]

        admin_client.patch(
            "/api/v1/admin/config",
            json={
                "llm_retry_max_attempts": 7,                           # valid
                "auto_approve_confidence_threshold": escalation - 0.1, # invalid
            },
        )

        # The valid field (retry attempts) must NOT have been applied
        after = admin_client.get("/api/v1/admin/config").json()
        assert after["llm_retry_max_attempts"] == original_retry, (
            "When a PATCH is rejected, no fields from that request should be applied. "
            "Config updates must be atomic."
        )


# =============================================================================
# DELETE /config/overrides tests
# =============================================================================

class TestResetConfigOverrides:

    def test_reset_clears_all_overrides(self, admin_client):
        """
        DELETE /config/overrides must clear every runtime override.
        """
        # Apply several overrides
        admin_client.patch(
            "/api/v1/admin/config",
            json={
                "llm_retry_max_attempts": 5,
                "enable_autonomous_decisions": False,
                "demo_mode": False,
            },
        )

        # Confirm they're active
        before = admin_client.get("/api/v1/admin/config").json()
        assert len(before["overrides_active"]) == 3

        # Reset
        reset_response = admin_client.delete("/api/v1/admin/config/overrides")
        assert reset_response.status_code == 200

        data = reset_response.json()
        assert len(data["cleared_overrides"]) == 3

        # Confirm they're gone
        after = admin_client.get("/api/v1/admin/config").json()
        assert after["overrides_active"] == []

    def test_reset_empty_is_safe(self, admin_client):
        """
        DELETE /config/overrides on a clean state must succeed silently.
        Calling reset when there's nothing to reset must not error.
        """
        response = admin_client.delete("/api/v1/admin/config/overrides")
        assert response.status_code == 200
        assert response.json()["cleared_overrides"] == []


# =============================================================================
# Metrics endpoint tests
# =============================================================================

class TestMetricsEndpoint:

    def test_metrics_returns_effective_values(self, admin_client):
        """
        GET /metrics must reflect runtime overrides, not just env var defaults.
        """
        # Apply an override
        admin_client.patch(
            "/api/v1/admin/config",
            json={"enable_autonomous_decisions": False},
        )

        response = admin_client.get("/api/v1/admin/metrics")
        assert response.status_code == 200

        data = response.json()
        assert data["autonomous_decisions_enabled"] is False, (
            "Metrics endpoint must reflect runtime override, not env var default."
        )

    def test_metrics_includes_langfuse_note(self, admin_client):
        """
        Metrics response must include the Langfuse URL so operators know
        where to find detailed traces.
        """
        response = admin_client.get("/api/v1/admin/metrics")
        data = response.json()

        assert "langfuse_note" in data
        assert "localhost:3001" in data["langfuse_note"], (
            "Langfuse URL must be in the metrics response for operator convenience."
        )
