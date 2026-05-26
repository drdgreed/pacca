"""
Subprocess pytest invocation for SME-write post-flight verification.

After the case_writer + provenance_writer + coverage_updater have run,
the CLI calls run_integrity_tests() to verify the dataset still satisfies
TestGoldenDatasetIntegrity. If the run fails, the CLI rolls back the
file mutations.

This module is intentionally a thin subprocess wrapper around pytest:
- We do NOT import pytest programmatically because the tests live in
  tests/clinical/ and have their own conftest with environment setup
  (per src/pacca/conftest.py).
- Running pytest as a subprocess gives us isolation: a broken case file
  won't crash the CLI session.

USAGE
=====

    result = run_integrity_tests(repo_root)
    if not result.passed:
        rollback(...)
        show_to_sme(result.summary)
"""

from __future__ import annotations

import subprocess
from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pathlib import Path


def _to_str(maybe_bytes: bytes | str | None) -> str:
    """Decode bytes to str (best-effort UTF-8); pass str through; empty for None."""
    if maybe_bytes is None:
        return ""
    if isinstance(maybe_bytes, bytes):
        return maybe_bytes.decode("utf-8", errors="replace")
    return maybe_bytes


@dataclass(frozen=True)
class IntegrityResult:
    """Outcome of a pytest integrity-test run."""

    passed: bool
    exit_code: int
    summary: str  # stdout + stderr; suitable for SME display


# Tests to run for SME-write post-flight verification.
# These are the FAST integrity tests (no LLM, no API calls).
_INTEGRITY_TARGETS = ("tests/clinical/test_clinical_accuracy.py::TestGoldenDatasetIntegrity",)


def run_integrity_tests(
    repo_root: Path,
    targets: tuple[str, ...] = _INTEGRITY_TARGETS,
    timeout_seconds: float = 60.0,
) -> IntegrityResult:
    """
    Run the integrity-test suite as a subprocess and capture the result.

    Args:
        repo_root: Directory to run pytest from (usually the repo root).
        targets: Pytest node-id targets to run. Defaults to the fast
            integrity suite.
        timeout_seconds: Subprocess timeout; defaults to 60s (the suite
            is normally <1s so anything longer indicates a hang).

    Returns:
        IntegrityResult with passed (bool), exit_code (int), and summary
        (str — stdout + stderr).
    """
    cmd = [
        "python",
        "-m",
        "pytest",
        *targets,
        "-q",
        "--no-header",
        "-x",  # stop on first failure (faster feedback for the SME)
    ]
    try:
        completed = subprocess.run(
            cmd,
            cwd=str(repo_root),
            capture_output=True,
            text=True,
            timeout=timeout_seconds,
            check=False,
        )
    except subprocess.TimeoutExpired as exc:
        return IntegrityResult(
            passed=False,
            exit_code=-1,
            summary=(
                f"Integrity test run timed out after {timeout_seconds}s. "
                f"Partial output:\n{_to_str(exc.stdout)}\n{_to_str(exc.stderr)}"
            ),
        )

    summary = (completed.stdout or "") + (completed.stderr or "")
    return IntegrityResult(
        passed=completed.returncode == 0,
        exit_code=completed.returncode,
        summary=summary.strip(),
    )


def run_per_case_tests(
    repo_root: Path,
    case_id: str,
    timeout_seconds: float = 60.0,
) -> IntegrityResult:
    """
    Run pytest filtered to a specific case_id (-k filter).

    Used by the CLI's `validate` subcommand to spot-check a single case.
    """
    cmd = [
        "python",
        "-m",
        "pytest",
        *_INTEGRITY_TARGETS,
        "-q",
        "--no-header",
        "-k",
        case_id,
    ]
    try:
        completed = subprocess.run(
            cmd,
            cwd=str(repo_root),
            capture_output=True,
            text=True,
            timeout=timeout_seconds,
            check=False,
        )
    except subprocess.TimeoutExpired:
        return IntegrityResult(
            passed=False,
            exit_code=-1,
            summary=f"Per-case test run for {case_id} timed out.",
        )

    summary = (completed.stdout or "") + (completed.stderr or "")
    return IntegrityResult(
        passed=completed.returncode == 0,
        exit_code=completed.returncode,
        summary=summary.strip(),
    )
