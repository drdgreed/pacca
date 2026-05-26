"""
Shared fixtures for API-layer unit tests.

- `client` — FastAPI TestClient with auth bypassed via dependency override.
- `auth_headers` — JWT Authorization header for endpoints that don't use
  the override (e.g., when we want to test the real auth dependency).
- `tmp_session_dir` — isolated session storage for SME-authoring tests.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import TYPE_CHECKING

import pytest
from fastapi.testclient import TestClient
from jose import jwt

from pacca.api.auth import ALGORITHM, SECRET_KEY
from pacca.api.main import app

if TYPE_CHECKING:
    from pathlib import Path


@pytest.fixture
def client() -> TestClient:
    """TestClient with the full app — auth is NOT overridden."""
    return TestClient(app)


@pytest.fixture
def auth_headers() -> dict[str, str]:
    """Valid JWT Authorization headers for a test user."""
    expires = datetime.now(UTC) + timedelta(minutes=30)
    payload = {"sub": "test-user", "exp": expires}
    token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def tmp_session_dir(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """
    Redirect SME-authoring session storage to a tmp dir.

    Patches DEFAULT_SESSION_DIR + session_path so the test doesn't touch
    ~/.pacca/sme_authoring_sessions/.
    """
    session_dir = tmp_path / "sessions"
    session_dir.mkdir()
    monkeypatch.setattr("pacca.agents.sme_authoring.session.DEFAULT_SESSION_DIR", session_dir)
    return session_dir
