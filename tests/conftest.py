"""
Pytest shared configuration and fixtures for the PACCA test suite.

This conftest provides:
  - collect_ignore: excludes pre-Level 5 test files that test model/route
    APIs replaced during upgrade_to_level5.sh
  - Environment setup so tests run without a real API key or OTel collector
  - Common fixtures shared across test modules

Unit tests (tests/unit/) are self-contained — they define their own mocks.

Clinical tests (tests/clinical/) require ANTHROPIC_API_KEY and are
marked @pytest.mark.clinical to run separately from the fast suite.
"""

import os

import pytest

# =============================================================================
# Exclude pre-Level 5 test files from collection.
#
# These files test the v1 domain model layer (PatientDemographics, Diagnosis,
# TreatmentCategory, etc.) and v1 route structure that was replaced during
# the Level 5 sprint. They are preserved for reference but cannot run against
# the current v2.2 codebase without significant rework.
# =============================================================================

collect_ignore = [
    "tests/test_level5_flow.py",  # Uses 'src.pacca' import path (pre-package)
    "tests/unit/test_api.py",  # Tests v1 route structure with old fixtures
]


# =============================================================================
# Environment setup — runs before any test imports
# =============================================================================


def pytest_configure(config):
    """
    Set test-safe environment variables before any tests run.

    This runs before imports, so modules that read os.getenv() at import
    time receive safe test values rather than raising at startup.
    """
    # Prevent validate_secret_key() from raising during test collection.
    if not os.getenv("SECRET_KEY"):
        os.environ["SECRET_KEY"] = "test-secret-key-min-32-chars-for-unit-tests"

    # Disable OTel during tests — no collector running in CI.
    os.environ.setdefault("OTEL_ENABLED", "false")

    # Mark as test environment.
    # 'test' is now a valid app_env value (added to Settings Literal).
    os.environ.setdefault("APP_ENV", "test")

    # Clear the lru_cache on Settings so the test env vars above take effect.
    # Without this, a previously cached Settings instance (with APP_ENV=development)
    # would be reused and the test env vars would be ignored.
    try:
        from pacca.config.settings import get_settings

        get_settings.cache_clear()
    except Exception:
        pass  # Module not yet importable at this stage — that's fine


# =============================================================================
# Shared fixtures
# =============================================================================


@pytest.fixture
def any_authorized_user() -> str:
    """A dummy authenticated username for routes that require JWT."""
    return "test_provider"
