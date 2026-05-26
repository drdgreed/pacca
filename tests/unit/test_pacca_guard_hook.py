"""
Tests for .githooks/pacca_guard.py — the PACCA PHI guard pre-commit hook.

The hook is a standalone script under .githooks/, not a normal Python
module under src/. We load it via importlib + spec_from_file_location
to get a testable module reference.

Test strategy:
- Mock subprocess.run to return canned `git diff` output.
- Cover get_staged_files / get_staged_additions / should_skip / main.
- Verify exit codes (0 on clean, 1 on PHI, 2 on internal error).
"""

from __future__ import annotations

import importlib.util
import subprocess
from pathlib import Path
from typing import TYPE_CHECKING
from unittest.mock import patch

import pytest

if TYPE_CHECKING:
    from types import ModuleType

# Path to the hook script (relative to repo root)
_HOOK_PATH = Path(__file__).resolve().parent.parent.parent / ".githooks" / "pacca_guard.py"


@pytest.fixture
def hook() -> ModuleType:
    """Load .githooks/pacca_guard.py as a module for testing."""
    spec = importlib.util.spec_from_file_location("pacca_guard", _HOOK_PATH)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class _FakeRun:
    """Stand-in for subprocess.CompletedProcess."""

    def __init__(self, returncode: int, stdout: str = "", stderr: str = "") -> None:
        self.returncode = returncode
        self.stdout = stdout
        self.stderr = stderr


# =============================================================================
# get_staged_files
# =============================================================================


class TestGetStagedFiles:
    def test_returns_file_list(self, hook: ModuleType) -> None:
        with patch(
            "subprocess.run",
            return_value=_FakeRun(0, "src/foo.py\nsrc/bar.py\n"),
        ):
            files = hook.get_staged_files()
        assert files == ["src/foo.py", "src/bar.py"]

    def test_empty_staging_returns_empty(self, hook: ModuleType) -> None:
        with patch("subprocess.run", return_value=_FakeRun(0, "")):
            assert hook.get_staged_files() == []

    def test_git_failure_returns_empty(self, hook: ModuleType) -> None:
        with patch("subprocess.run", return_value=_FakeRun(128, "", "error")):
            assert hook.get_staged_files() == []

    def test_filters_blank_lines(self, hook: ModuleType) -> None:
        with patch(
            "subprocess.run",
            return_value=_FakeRun(0, "src/foo.py\n\nsrc/bar.py\n"),
        ):
            files = hook.get_staged_files()
        assert "" not in files
        assert files == ["src/foo.py", "src/bar.py"]


# =============================================================================
# get_staged_additions
# =============================================================================


class TestGetStagedAdditions:
    def test_extracts_added_lines(self, hook: ModuleType) -> None:
        diff_output = (
            "diff --git a/src/foo.py b/src/foo.py\n"
            "--- a/src/foo.py\n"
            "+++ b/src/foo.py\n"
            "@@ -1,2 +1,3 @@\n"
            " unchanged line\n"
            "+added line one\n"
            "+added line two\n"
            "-removed line\n"
        )
        with patch("subprocess.run", return_value=_FakeRun(0, diff_output)):
            result = hook.get_staged_additions("src/foo.py")
        # Should include only the + lines, NOT the +++ header
        assert "added line one" in result
        assert "added line two" in result
        # Should not include the diff header or unchanged/removed lines
        assert "diff --git" not in result
        assert "unchanged line" not in result
        assert "removed line" not in result

    def test_no_diff_returns_empty(self, hook: ModuleType) -> None:
        with patch("subprocess.run", return_value=_FakeRun(0, "")):
            assert hook.get_staged_additions("src/foo.py") == ""

    def test_git_failure_returns_empty(self, hook: ModuleType) -> None:
        with patch("subprocess.run", return_value=_FakeRun(1, "", "error")):
            assert hook.get_staged_additions("src/foo.py") == ""


# =============================================================================
# should_skip
# =============================================================================


class TestShouldSkip:
    @pytest.mark.parametrize(
        "path",
        [
            "tests/unit/sme_authoring/test_validators.py",
            "tests/clinical/expansion_cases.py",
            "docs/CASE_AUTHORING_GUIDE.md",
            "docs/SME_CASE_AGENT_USER_MANUAL.md",
            ".githooks/pacca_guard.py",
            "src/pacca/agents/sme_authoring/validators.py",
            ".pre-commit-config.yaml",
        ],
    )
    def test_skipped_paths(self, hook: ModuleType, path: str) -> None:
        assert hook.should_skip(path) is True

    @pytest.mark.parametrize(
        "path",
        [
            "src/pacca/cli.py",
            "src/pacca/agents/sme_authoring/agent.py",
            "src/pacca/api/routes.py",
            "Makefile",
            "pyproject.toml",
            "README.md",
        ],
    )
    def test_non_skipped_paths(self, hook: ModuleType, path: str) -> None:
        assert hook.should_skip(path) is False


# =============================================================================
# main() — end-to-end with mocked git
# =============================================================================


class TestMain:
    def test_empty_staging_returns_zero(self, hook: ModuleType) -> None:
        with patch("subprocess.run", return_value=_FakeRun(0, "")):
            assert hook.main() == 0

    def test_clean_file_returns_zero(
        self, hook: ModuleType, capsys: pytest.CaptureFixture[str]
    ) -> None:
        # Sequence of mocked subprocess returns:
        # 1. get_staged_files → returns one file
        # 2. get_staged_additions → returns lines with no PHI
        responses = [
            _FakeRun(0, "src/myfile.py\n"),  # staged-files
            _FakeRun(
                0,
                "diff --git a/src/myfile.py b/src/myfile.py\n"
                "+++ b/src/myfile.py\n"
                "+def hello():\n"
                "+    return 'world'\n",
            ),
        ]
        with patch("subprocess.run", side_effect=responses):
            assert hook.main() == 0

    def test_phi_in_added_lines_returns_one(
        self, hook: ModuleType, capsys: pytest.CaptureFixture[str]
    ) -> None:
        responses = [
            _FakeRun(0, "src/myfile.py\n"),
            _FakeRun(
                0,
                "diff --git a/src/myfile.py b/src/myfile.py\n"
                "+++ b/src/myfile.py\n"
                "+# Patient SSN: 123-45-6789 for processing.\n",
            ),
        ]
        with patch("subprocess.run", side_effect=responses):
            exit_code = hook.main()
        assert exit_code == 1

        captured = capsys.readouterr()
        # Stderr should include the file + the SSN marker
        assert "src/myfile.py" in captured.err
        assert "SSN" in captured.err
        assert "PHI guard detected" in captured.err

    def test_skipped_file_with_phi_returns_zero(self, hook: ModuleType) -> None:
        # Test files legitimately contain PHI-shaped fixtures
        responses = [
            _FakeRun(0, "tests/unit/test_validators.py\n"),
            # get_staged_additions should NOT be called (should_skip filters)
        ]
        with patch("subprocess.run", side_effect=responses):
            assert hook.main() == 0

    def test_multiple_files_one_with_phi_returns_one(
        self, hook: ModuleType, capsys: pytest.CaptureFixture[str]
    ) -> None:
        responses = [
            _FakeRun(0, "src/clean.py\nsrc/dirty.py\n"),  # staged files
            # clean.py — no PHI
            _FakeRun(
                0,
                "+++ b/src/clean.py\n+def f(): return 1\n",
            ),
            # dirty.py — has SSN
            _FakeRun(
                0,
                "+++ b/src/dirty.py\n+SSN = '123-45-6789'\n",
            ),
        ]
        with patch("subprocess.run", side_effect=responses):
            exit_code = hook.main()
        assert exit_code == 1
        captured = capsys.readouterr()
        assert "src/dirty.py" in captured.err
        assert "src/clean.py" not in captured.err

    def test_git_failure_returns_two(
        self, hook: ModuleType, capsys: pytest.CaptureFixture[str]
    ) -> None:
        # Internal error during staged-files lookup
        with patch(
            "subprocess.run",
            side_effect=subprocess.SubprocessError("git not found"),
        ):
            exit_code = hook.main()
        assert exit_code == 2
        captured = capsys.readouterr()
        assert "failed" in captured.err.lower()


# =============================================================================
# scan_for_phi is reused (regression: validators.py exposes it publicly)
# =============================================================================


class TestScanForPhiReuse:
    def test_scan_for_phi_importable_from_validators(self) -> None:
        from pacca.agents.sme_authoring.validators import scan_for_phi

        assert callable(scan_for_phi)
        assert scan_for_phi("Patient SSN 123-45-6789") != []
        assert scan_for_phi("perfectly clean text") == []

    def test_validate_no_phi_uses_scan_for_phi(self) -> None:
        # Regression: validate_no_phi internally uses scan_for_phi.
        # If the public scan_for_phi changes, validate_no_phi sees it.
        from pacca.agents.sme_authoring.models import (
            CaseDraftResponse,
            ValidationOutcome,
        )
        from pacca.agents.sme_authoring.validators import validate_no_phi

        bad_case = CaseDraftResponse(
            case_id="GC-101",
            title="Test case with sufficient title length for validation",
            diagnosis_code="X00",
            diagnosis_description="Synthetic test diagnosis description",
            procedure_code="00000",
            procedure_description="Synthetic test procedure description",
            clinical_notes=(
                "58-year-old male with SSN 999-88-7777 and "
                "stage IV NSCLC requesting first-line therapy."
            ),
            guidelines_context=(
                "NCCN guidelines apply to this scenario; cite the recognized "
                "body to satisfy the citation validator with sufficient text."
            ),
            expected_outcome="AUTO_APPROVED",
            expected_branch="BRANCH_1_AUTO_APPROVE",
            reasoning_must_include=["NCCN"],
            clinical_rationale=(
                "Test rationale to satisfy the schema length validator. "
                "Two sentences for clinical_rationale field."
            ),
            judge_scoring_criteria=(
                "Test scoring criteria long enough to satisfy the length "
                "validator on judge_scoring_criteria."
            ),
        )
        report = validate_no_phi(bad_case)
        assert report.outcome == ValidationOutcome.FAIL
        assert "SSN" in report.reason
