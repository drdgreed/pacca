"""
Persistent session state for SME authoring sessions.

Sessions are saved to ~/.pacca/sme_authoring_sessions/{session_id}.json
after every workflow step. An SME who quits mid-session can resume via
`pacca sme-author resume <session_id>`.

DESIGN
======

- Each session has a UUID-based session_id (uuid7 — time-sortable).
- State is the SessionState Pydantic model (defined in models.py); we
  save its JSON dump and restore via model_validate_json().
- Saves are atomic: write to tmp + rename.
- Listing sessions enumerates the directory; corrupted files surface
  with a clear error rather than crash the listing.

WHY UUID7 (NOT UUID4): same-day sessions sort by creation time, which
matters when the SME wants to find "the session I was working on this
morning."
"""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import TYPE_CHECKING

from pydantic import ValidationError

from pacca.agents.sme_authoring.models import SessionState

if TYPE_CHECKING:
    from collections.abc import Iterator

DEFAULT_SESSION_DIR = Path.home() / ".pacca" / "sme_authoring_sessions"


class SessionStorageError(Exception):
    """Base class for session-storage errors."""


def _ensure_session_dir(session_dir: Path | None = None) -> Path:
    """Create the session directory if it doesn't exist; return the path."""
    path = session_dir or DEFAULT_SESSION_DIR
    path.mkdir(parents=True, exist_ok=True)
    return path


def session_path(session_id: str, session_dir: Path | None = None) -> Path:
    """Path to the JSON file for a given session_id."""
    return _ensure_session_dir(session_dir) / f"{session_id}.json"


def save_session(
    state: SessionState,
    session_dir: Path | None = None,
) -> Path:
    """
    Atomically save SessionState to disk.

    Updates state.last_updated_at to now (UTC) before writing.

    Returns:
        The path the session was written to.
    """
    target = session_path(state.session_id, session_dir)
    state = state.model_copy(update={"last_updated_at": datetime.now(UTC)})
    tmp_path = target.with_suffix(target.suffix + ".tmp")
    tmp_path.write_text(state.model_dump_json(indent=2), encoding="utf-8")
    tmp_path.replace(target)
    return target


def load_session(
    session_id: str,
    session_dir: Path | None = None,
) -> SessionState:
    """
    Load SessionState from disk.

    Raises:
        FileNotFoundError if the session doesn't exist.
        SessionStorageError if the file exists but is corrupt or schema-
            mismatched.
    """
    path = session_path(session_id, session_dir)
    if not path.exists():
        raise FileNotFoundError(
            f"Session {session_id} not found at {path}. "
            "Use `pacca sme-author list-sessions` to see available sessions."
        )
    try:
        return SessionState.model_validate_json(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, ValidationError) as exc:
        raise SessionStorageError(
            f"Session {session_id} file is corrupt or schema-mismatched: {exc}. File path: {{path}}"
        ) from exc


def list_sessions(
    session_dir: Path | None = None,
) -> list[SessionState]:
    """
    Return all sessions in the session directory, sorted by last_updated_at
    (most-recent first).

    Corrupt sessions are silently skipped so a single bad file doesn't
    break the listing.
    """
    path = _ensure_session_dir(session_dir)
    sessions: list[SessionState] = []
    for json_file in path.glob("*.json"):
        try:
            sessions.append(SessionState.model_validate_json(json_file.read_text(encoding="utf-8")))
        except (json.JSONDecodeError, ValidationError):
            # Skip corrupt; surface via separate diagnostic command later.
            continue
    return sorted(sessions, key=lambda s: s.last_updated_at, reverse=True)


def delete_session(
    session_id: str,
    session_dir: Path | None = None,
) -> bool:
    """
    Remove a session file from disk.

    Returns True if a file was deleted; False if it didn't exist.
    """
    path = session_path(session_id, session_dir)
    if path.exists():
        path.unlink()
        return True
    return False


def iter_session_files(
    session_dir: Path | None = None,
) -> Iterator[Path]:
    """Yield every *.json session file path. Used by maintenance scripts."""
    return _ensure_session_dir(session_dir).glob("*.json")
