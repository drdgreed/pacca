"""
Tests for session.py — persistent SME-authoring session state.
"""

from __future__ import annotations

import time
from datetime import UTC, datetime
from typing import TYPE_CHECKING

import pytest

from pacca.agents.sme_authoring.models import SessionState, SMEScenario
from pacca.agents.sme_authoring.session import (
    SessionStorageError,
    delete_session,
    list_sessions,
    load_session,
    save_session,
    session_path,
)

if TYPE_CHECKING:
    from pathlib import Path


def _make_state(session_id: str = "sess-1", mode: str = "sandbox") -> SessionState:
    now = datetime.now(UTC)
    return SessionState(
        session_id=session_id,
        created_at=now,
        last_updated_at=now,
        mode=mode,  # type: ignore[arg-type]
        scenario=SMEScenario(
            description=(
                "Test scenario long enough to satisfy the minimum-length "
                "validator on the description field."
            ),
        ),
        last_step="created",
    )


class TestSavedLoad:
    def test_save_then_load_roundtrip(self, tmp_path: Path) -> None:
        state = _make_state()
        saved_path = save_session(state, session_dir=tmp_path)
        assert saved_path.exists()

        loaded = load_session(state.session_id, session_dir=tmp_path)
        assert loaded.session_id == state.session_id
        assert loaded.mode == state.mode
        assert loaded.scenario is not None
        assert state.scenario is not None
        assert loaded.scenario.description == state.scenario.description

    def test_save_updates_last_updated_at(self, tmp_path: Path) -> None:
        state = _make_state()
        original_ts = state.last_updated_at
        time.sleep(0.01)  # tiny delay to ensure timestamp moves
        save_session(state, session_dir=tmp_path)
        loaded = load_session(state.session_id, session_dir=tmp_path)
        assert loaded.last_updated_at >= original_ts

    def test_load_missing_session_raises(self, tmp_path: Path) -> None:
        with pytest.raises(FileNotFoundError):
            load_session("nonexistent", session_dir=tmp_path)

    def test_load_corrupt_session_raises(self, tmp_path: Path) -> None:
        target = session_path("corrupt", session_dir=tmp_path)
        target.write_text("not valid json", encoding="utf-8")
        with pytest.raises(SessionStorageError):
            load_session("corrupt", session_dir=tmp_path)


class TestListSessions:
    def test_empty_dir_returns_empty(self, tmp_path: Path) -> None:
        assert list_sessions(tmp_path) == []

    def test_multiple_sessions_sorted_by_recency(self, tmp_path: Path) -> None:
        old_state = _make_state(session_id="old")
        save_session(old_state, session_dir=tmp_path)

        time.sleep(0.01)
        new_state = _make_state(session_id="new")
        save_session(new_state, session_dir=tmp_path)

        sessions = list_sessions(tmp_path)
        assert len(sessions) == 2
        # Most-recent first
        assert sessions[0].session_id == "new"
        assert sessions[1].session_id == "old"

    def test_corrupt_files_silently_skipped(self, tmp_path: Path) -> None:
        save_session(_make_state(session_id="good"), session_dir=tmp_path)
        (tmp_path / "corrupt.json").write_text("garbage", encoding="utf-8")

        sessions = list_sessions(tmp_path)
        assert len(sessions) == 1
        assert sessions[0].session_id == "good"


class TestDeleteSession:
    def test_delete_existing_returns_true(self, tmp_path: Path) -> None:
        save_session(_make_state(), session_dir=tmp_path)
        assert delete_session("sess-1", session_dir=tmp_path) is True
        assert not session_path("sess-1", session_dir=tmp_path).exists()

    def test_delete_missing_returns_false(self, tmp_path: Path) -> None:
        assert delete_session("never-existed", session_dir=tmp_path) is False
