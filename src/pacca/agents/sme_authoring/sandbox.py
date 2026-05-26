"""
Sandbox mode + git-worktree mode for safe SME authoring.

PR-3 layers two isolation strategies on top of the PR-1 + PR-2 core:

  --sandbox      Writes generated cases to `sandbox/cases/<session_id>/`
                 instead of `tests/clinical/`. SME can experiment with
                 ZERO git state. Promotion to the real tree is explicit
                 via `promote_session(session_id)`.

  --git-worktree Auto-creates an isolated git worktree at
                 `../pacca-sme-<session_id>/` on a new branch
                 `sme-authoring/<session_id>`. All mutations happen in
                 the worktree; the main checkout is untouched.

WHY BOTH
========

- Sandbox: zero git state, lowest friction, best for "I'm experimenting
  and don't know what I want yet."
- Worktree: real git state, real PR-ready, best for "I know I want to
  merge this; just keep me isolated from main."

SECURITY / SAFETY
=================

- The sandbox directory is created with restrictive permissions (700)
  to match the SME's umask + avoid shared-filesystem leakage.
- Worktree cleanup uses `git worktree remove --force` ONLY if the
  worktree directory matches the expected `../pacca-sme-<session_id>/`
  pattern. We never blindly remove a worktree.
- If the SME's session crashed and left an orphan worktree, the next
  `pacca sme-author resume <session_id>` reattaches to it cleanly.
"""

from __future__ import annotations

import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path

# Default sandbox root (relative to the repo)
DEFAULT_SANDBOX_ROOT = Path("sandbox")
SANDBOX_CASES_DIRNAME = "cases"
SANDBOX_DOCS_DIRNAME = "docs"

# Default git-worktree branch prefix
WORKTREE_BRANCH_PREFIX = "sme-authoring/"


class SandboxError(Exception):
    """Base class for sandbox errors."""


class WorktreeError(SandboxError):
    """Raised for git-worktree-specific failures."""


@dataclass(frozen=True)
class SandboxPaths:
    """Paths within a sandbox session."""

    root: Path
    cases_dir: Path
    docs_dir: Path


def create_sandbox(
    session_id: str,
    sandbox_root: Path | None = None,
) -> SandboxPaths:
    """
    Create a sandbox session directory.

    Layout:
        <sandbox_root>/cases/<session_id>/      ← case files go here
        <sandbox_root>/docs/<session_id>/       ← companion-doc previews

    Returns:
        SandboxPaths with root, cases_dir, docs_dir.
    """
    root = (sandbox_root or DEFAULT_SANDBOX_ROOT).resolve()
    cases_dir = root / SANDBOX_CASES_DIRNAME / session_id
    docs_dir = root / SANDBOX_DOCS_DIRNAME / session_id

    cases_dir.mkdir(parents=True, exist_ok=True)
    docs_dir.mkdir(parents=True, exist_ok=True)

    # Restrict perms (mode 0o700) to avoid shared-filesystem leakage.
    # Best-effort: on systems where chmod is a no-op (Windows), this
    # silently succeeds without changing anything.
    try:
        cases_dir.chmod(0o700)
        docs_dir.chmod(0o700)
    except OSError:
        pass

    return SandboxPaths(root=root, cases_dir=cases_dir, docs_dir=docs_dir)


def sandbox_exists(
    session_id: str,
    sandbox_root: Path | None = None,
) -> bool:
    """True if the sandbox for this session has been created."""
    root = (sandbox_root or DEFAULT_SANDBOX_ROOT).resolve()
    return (root / SANDBOX_CASES_DIRNAME / session_id).exists()


def clean_sandbox(
    session_id: str,
    sandbox_root: Path | None = None,
) -> bool:
    """
    Remove the sandbox session directory.

    Returns True if something was removed, False if it didn't exist.
    """
    root = (sandbox_root or DEFAULT_SANDBOX_ROOT).resolve()
    cases_dir = root / SANDBOX_CASES_DIRNAME / session_id
    docs_dir = root / SANDBOX_DOCS_DIRNAME / session_id

    removed = False
    if cases_dir.exists():
        shutil.rmtree(cases_dir)
        removed = True
    if docs_dir.exists():
        shutil.rmtree(docs_dir)
        removed = True
    return removed


def list_sandbox_sessions(sandbox_root: Path | None = None) -> list[str]:
    """List session_ids for which a sandbox exists."""
    root = (sandbox_root or DEFAULT_SANDBOX_ROOT).resolve()
    cases_root = root / SANDBOX_CASES_DIRNAME
    if not cases_root.exists():
        return []
    return sorted(p.name for p in cases_root.iterdir() if p.is_dir())


# =============================================================================
# Git worktree mode
# =============================================================================


@dataclass(frozen=True)
class WorktreeInfo:
    """Metadata about an active SME-authoring worktree."""

    session_id: str
    worktree_path: Path
    branch_name: str


def create_worktree(
    session_id: str,
    repo_root: Path | None = None,
    parent_dir: Path | None = None,
    base_branch: str = "main",
) -> WorktreeInfo:
    """
    Create a git worktree for an SME-authoring session.

    Worktree path: parent_dir/pacca-sme-<session_id>
    Branch name:   sme-authoring/<session_id>

    Args:
        session_id: The session UUID.
        repo_root: Repo to add the worktree from. Defaults to cwd.
        parent_dir: Where to put the worktree. Defaults to repo_root.parent.
        base_branch: Branch to fork from. Defaults to 'main'.

    Returns:
        WorktreeInfo with paths + branch name.

    Raises:
        WorktreeError if `git worktree add` fails.
    """
    repo_root = (repo_root or Path.cwd()).resolve()
    parent_dir = (parent_dir or repo_root.parent).resolve()
    worktree_path = parent_dir / f"pacca-sme-{session_id}"
    branch_name = f"{WORKTREE_BRANCH_PREFIX}{session_id}"

    cmd = [
        "git",
        "worktree",
        "add",
        "-b",
        branch_name,
        str(worktree_path),
        base_branch,
    ]
    try:
        result = subprocess.run(
            cmd,
            cwd=str(repo_root),
            capture_output=True,
            text=True,
            check=False,
        )
    except FileNotFoundError as exc:
        raise WorktreeError("`git` not found on PATH; cannot create worktree.") from exc

    if result.returncode != 0:
        raise WorktreeError(
            f"git worktree add failed (exit {result.returncode}):\n"
            f"stdout: {result.stdout}\nstderr: {result.stderr}"
        )

    return WorktreeInfo(
        session_id=session_id,
        worktree_path=worktree_path,
        branch_name=branch_name,
    )


def remove_worktree(
    session_id: str,
    repo_root: Path | None = None,
    parent_dir: Path | None = None,
    force: bool = False,
) -> bool:
    """
    Remove the worktree for a session.

    Safety: only removes a worktree that matches the expected naming
    pattern (pacca-sme-<session_id>). Raises WorktreeError on any
    deviation rather than potentially blowing away unrelated state.

    Returns True if a worktree was removed, False if it didn't exist.

    Args:
        force: Pass --force to `git worktree remove`. Use only when the
            SME has confirmed they want to abandon uncommitted changes.
    """
    repo_root = (repo_root or Path.cwd()).resolve()
    parent_dir = (parent_dir or repo_root.parent).resolve()
    worktree_path = parent_dir / f"pacca-sme-{session_id}"

    if not worktree_path.exists():
        return False

    # Safety check: the path must end with our expected pattern.
    expected_suffix = f"pacca-sme-{session_id}"
    if worktree_path.name != expected_suffix:
        raise WorktreeError(
            f"Worktree path {worktree_path} does not match expected pattern "
            f"'.../{expected_suffix}'. Refusing to remove."
        )

    cmd = ["git", "worktree", "remove"]
    if force:
        cmd.append("--force")
    cmd.append(str(worktree_path))

    try:
        result = subprocess.run(
            cmd,
            cwd=str(repo_root),
            capture_output=True,
            text=True,
            check=False,
        )
    except FileNotFoundError as exc:
        raise WorktreeError("`git` not found on PATH; cannot remove worktree.") from exc

    if result.returncode != 0:
        raise WorktreeError(
            f"git worktree remove failed (exit {result.returncode}):\n"
            f"stdout: {result.stdout}\nstderr: {result.stderr}"
        )

    return True


def list_worktrees(repo_root: Path | None = None) -> list[str]:
    """
    List active SME-authoring worktrees via `git worktree list --porcelain`.

    Returns worktree paths (absolute strings) whose branch name starts
    with `sme-authoring/`. Empty list on any failure.
    """
    repo_root = (repo_root or Path.cwd()).resolve()
    try:
        result = subprocess.run(
            ["git", "worktree", "list", "--porcelain"],
            cwd=str(repo_root),
            capture_output=True,
            text=True,
            check=False,
        )
    except FileNotFoundError:
        return []

    if result.returncode != 0:
        return []

    worktrees: list[str] = []
    current_path: str | None = None
    for line in result.stdout.splitlines():
        if line.startswith("worktree "):
            current_path = line.removeprefix("worktree ").strip()
        elif line.startswith("branch ") and current_path:
            branch = line.removeprefix("branch ").strip()
            # `git worktree list --porcelain` outputs branch as refs/heads/...
            branch = branch.removeprefix("refs/heads/")
            if branch.startswith(WORKTREE_BRANCH_PREFIX):
                worktrees.append(current_path)
            current_path = None
    return worktrees
