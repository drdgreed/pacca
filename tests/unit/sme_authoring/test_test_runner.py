"""
Tests for test_runner.py — pytest subprocess invocation.

We test the subprocess wrapper using a controlled stub command rather
than running real pytest (which would be slow + brittle in CI).
"""

from __future__ import annotations

import subprocess
from typing import TYPE_CHECKING
from unittest.mock import patch

import pytest

from pacca.agents.sme_authoring.test_runner import (
    IntegrityResult,
    run_integrity_tests,
    run_per_case_tests,
)

if TYPE_CHECKING:
    from pathlib import Path


class _FakeCompleted:
    """Stand-in for subprocess.CompletedProcess used by patch."""

    def __init__(self, returncode: int, stdout: str = "", stderr: str = "") -> None:
        self.returncode = returncode
        self.stdout = stdout
        self.stderr = stderr


class TestRunIntegrityTests:
    def test_zero_exit_returns_passed(self, tmp_path: Path) -> None:
        with patch(
            "subprocess.run",
            return_value=_FakeCompleted(0, "all tests passed", ""),
        ):
            result = run_integrity_tests(tmp_path)
        assert result.passed is True
        assert result.exit_code == 0
        assert "all tests passed" in result.summary

    def test_nonzero_exit_returns_failed(self, tmp_path: Path) -> None:
        with patch(
            "subprocess.run",
            return_value=_FakeCompleted(1, "test failed", "error context"),
        ):
            result = run_integrity_tests(tmp_path)
        assert result.passed is False
        assert result.exit_code == 1
        assert "test failed" in result.summary
        assert "error context" in result.summary

    def test_timeout_returns_failed_result(self, tmp_path: Path) -> None:
        with patch(
            "subprocess.run",
            side_effect=subprocess.TimeoutExpired(
                cmd="pytest", timeout=60.0, output="partial output"
            ),
        ):
            result = run_integrity_tests(tmp_path, timeout_seconds=60.0)
        assert result.passed is False
        assert result.exit_code == -1
        assert "timed out" in result.summary

    def test_summary_strips_whitespace(self, tmp_path: Path) -> None:
        with patch(
            "subprocess.run",
            return_value=_FakeCompleted(0, "\n\nclean output\n\n", ""),
        ):
            result = run_integrity_tests(tmp_path)
        assert result.summary == "clean output"


class TestRunPerCaseTests:
    def test_filters_by_case_id(self, tmp_path: Path) -> None:
        with patch("subprocess.run", return_value=_FakeCompleted(0)) as mock_run:
            run_per_case_tests(tmp_path, "GC-101")
        # The -k filter argument should include the case_id
        call_args = mock_run.call_args
        cmd = call_args[0][0]
        assert "-k" in cmd
        assert "GC-101" in cmd

    def test_passed_propagates(self, tmp_path: Path) -> None:
        with patch("subprocess.run", return_value=_FakeCompleted(0, "ok")):
            result = run_per_case_tests(tmp_path, "GC-101")
        assert result.passed is True


class TestIntegrityResultDataclass:
    def test_is_frozen(self) -> None:
        from dataclasses import FrozenInstanceError

        result = IntegrityResult(passed=True, exit_code=0, summary="")
        with pytest.raises(FrozenInstanceError):
            result.passed = False  # type: ignore[misc]
