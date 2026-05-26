"""
Tests for sandbox.py — sandbox + git-worktree isolation modes.
"""

from __future__ import annotations

from typing import TYPE_CHECKING
from unittest.mock import patch

import pytest

from pacca.agents.sme_authoring.sandbox import (
    SandboxPaths,
    WorktreeError,
    WorktreeInfo,
    clean_sandbox,
    create_sandbox,
    create_worktree,
    list_sandbox_sessions,
    list_worktrees,
    remove_worktree,
    sandbox_exists,
)

if TYPE_CHECKING:
    from pathlib import Path


class _FakeRun:
    """Stand-in for subprocess.CompletedProcess."""

    def __init__(self, returncode: int, stdout: str = "", stderr: str = "") -> None:
        self.returncode = returncode
        self.stdout = stdout
        self.stderr = stderr


# =============================================================================
# Sandbox mode
# =============================================================================


class TestCreateSandbox:
    def test_creates_cases_and_docs_dirs(self, tmp_path: Path) -> None:
        paths = create_sandbox("sess-123", sandbox_root=tmp_path)
        assert paths.cases_dir.exists()
        assert paths.cases_dir.is_dir()
        assert paths.docs_dir.exists()
        assert paths.docs_dir.is_dir()

    def test_returns_sandbox_paths(self, tmp_path: Path) -> None:
        paths = create_sandbox("sess-123", sandbox_root=tmp_path)
        assert isinstance(paths, SandboxPaths)
        assert paths.cases_dir.name == "sess-123"
        assert "cases" in str(paths.cases_dir)

    def test_idempotent_create(self, tmp_path: Path) -> None:
        # Creating twice should not error
        create_sandbox("sess-123", sandbox_root=tmp_path)
        create_sandbox("sess-123", sandbox_root=tmp_path)


class TestSandboxExists:
    def test_existing_returns_true(self, tmp_path: Path) -> None:
        create_sandbox("sess-1", sandbox_root=tmp_path)
        assert sandbox_exists("sess-1", sandbox_root=tmp_path) is True

    def test_missing_returns_false(self, tmp_path: Path) -> None:
        assert sandbox_exists("never-created", sandbox_root=tmp_path) is False


class TestCleanSandbox:
    def test_clean_existing_returns_true(self, tmp_path: Path) -> None:
        create_sandbox("sess-1", sandbox_root=tmp_path)
        assert clean_sandbox("sess-1", sandbox_root=tmp_path) is True
        assert not sandbox_exists("sess-1", sandbox_root=tmp_path)

    def test_clean_missing_returns_false(self, tmp_path: Path) -> None:
        assert clean_sandbox("never-created", sandbox_root=tmp_path) is False


class TestListSandboxSessions:
    def test_empty(self, tmp_path: Path) -> None:
        assert list_sandbox_sessions(tmp_path) == []

    def test_lists_created(self, tmp_path: Path) -> None:
        create_sandbox("alpha", sandbox_root=tmp_path)
        create_sandbox("beta", sandbox_root=tmp_path)
        sessions = list_sandbox_sessions(tmp_path)
        assert "alpha" in sessions
        assert "beta" in sessions
        # Sorted alphabetically
        assert sessions == sorted(sessions)


# =============================================================================
# Worktree mode (subprocess mocked)
# =============================================================================


class TestCreateWorktree:
    def test_success_returns_info(self, tmp_path: Path) -> None:
        with patch("subprocess.run", return_value=_FakeRun(0, "ok")):
            info = create_worktree(
                "sess-1",
                repo_root=tmp_path,
                parent_dir=tmp_path.parent,
            )
        assert isinstance(info, WorktreeInfo)
        assert info.session_id == "sess-1"
        assert info.branch_name == "sme-authoring/sess-1"
        assert info.worktree_path.name == "pacca-sme-sess-1"

    def test_git_failure_raises(self, tmp_path: Path) -> None:
        with (
            patch(
                "subprocess.run",
                return_value=_FakeRun(1, "", "branch already exists"),
            ),
            pytest.raises(WorktreeError) as exc_info,
        ):
            create_worktree(
                "sess-1",
                repo_root=tmp_path,
                parent_dir=tmp_path.parent,
            )
        assert "branch already exists" in str(exc_info.value)

    def test_git_missing_raises(self, tmp_path: Path) -> None:
        with (
            patch("subprocess.run", side_effect=FileNotFoundError("git")),
            pytest.raises(WorktreeError) as exc_info,
        ):
            create_worktree(
                "sess-1",
                repo_root=tmp_path,
                parent_dir=tmp_path.parent,
            )
        assert "git" in str(exc_info.value)


class TestRemoveWorktree:
    def test_missing_path_returns_false(self, tmp_path: Path) -> None:
        # Worktree path doesn't exist → no-op returning False
        result = remove_worktree(
            "never-created",
            repo_root=tmp_path,
            parent_dir=tmp_path,
        )
        assert result is False

    def test_success_returns_true(self, tmp_path: Path) -> None:
        # Set up a fake worktree directory
        wt_path = tmp_path / "pacca-sme-sess-1"
        wt_path.mkdir()
        with patch("subprocess.run", return_value=_FakeRun(0, "ok")):
            result = remove_worktree(
                "sess-1",
                repo_root=tmp_path,
                parent_dir=tmp_path,
            )
        assert result is True

    def test_git_failure_raises(self, tmp_path: Path) -> None:
        wt_path = tmp_path / "pacca-sme-sess-1"
        wt_path.mkdir()
        with (
            patch(
                "subprocess.run",
                return_value=_FakeRun(128, "", "fatal: not a git repo"),
            ),
            pytest.raises(WorktreeError),
        ):
            remove_worktree("sess-1", repo_root=tmp_path, parent_dir=tmp_path)


class TestListWorktrees:
    def test_git_failure_returns_empty(self, tmp_path: Path) -> None:
        with patch("subprocess.run", return_value=_FakeRun(1, "", "error")):
            assert list_worktrees(tmp_path) == []

    def test_git_missing_returns_empty(self, tmp_path: Path) -> None:
        with patch("subprocess.run", side_effect=FileNotFoundError("git")):
            assert list_worktrees(tmp_path) == []

    def test_parses_sme_authoring_worktrees(self, tmp_path: Path) -> None:
        # `git worktree list --porcelain` format
        porcelain_output = """worktree /path/to/main-checkout
HEAD abc123
branch refs/heads/main

worktree /path/to/pacca-sme-sess-1
HEAD def456
branch refs/heads/sme-authoring/sess-1

worktree /path/to/other-feature
HEAD ghi789
branch refs/heads/feat/other
"""
        with patch("subprocess.run", return_value=_FakeRun(0, porcelain_output)):
            results = list_worktrees(tmp_path)
        # Only the sme-authoring/* one should be in the results
        assert "/path/to/pacca-sme-sess-1" in results
        assert "/path/to/main-checkout" not in results
        assert "/path/to/other-feature" not in results
