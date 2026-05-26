"""
Tests for the PR-3 CLI subcommands:
  - status
  - list-batches
  - list-gaps
  - list-sessions
  - resume <session_id>
  - batch <BATCH_ID>

Most subcommands depend on docs files that may or may not exist in the
test environment. We patch the default paths via the unit-tested
readers' optional path arguments — accessed via monkey-patching the
module-level default constants.
"""

from __future__ import annotations

import datetime
from typing import TYPE_CHECKING
from unittest.mock import patch

from click.testing import CliRunner

from pacca.agents.sme_authoring.cli_commands import sme_author
from pacca.agents.sme_authoring.models import SessionState

if TYPE_CHECKING:
    from pathlib import Path


_SAMPLE_COVERAGE = """# Coverage

The current dataset:

| List | File | Count | IDs |
|---|---|---|---|
| GOLDEN_CASES | `golden_cases.py` | 20 | GC-001 to GC-020 |
| CARDIOLOGY_CASES | `cardiology_cases.py` | 4 | GC-037 to GC-040 |
| **Total live** | — | **100** | — |
"""

_SAMPLE_ROADMAP = """# Roadmap

#### Batch A — DENY expansion (3 cases) — IDs GC-034 to GC-036
**File:** `tests/clinical/denial_cases.py` (new)
- GC-034: Off-label oncology biologic
- GC-035: PT visits over benefit cap
- GC-036: Re-request after prior denial

#### Batch B — Cardiology depth (4 cases) — IDs GC-037 to GC-040
**File:** `tests/clinical/cardiology_cases.py` (new)
- GC-037: TAVR
"""


# =============================================================================
# status
# =============================================================================


class TestStatusCmd:
    def test_status_no_coverage_file(self, tmp_path: Path) -> None:
        # Default path won't exist in tmp env
        with patch(
            "pacca.agents.sme_authoring.gap_analyzer.DEFAULT_COVERAGE_PATH",
            tmp_path / "missing.md",
        ):
            r = CliRunner().invoke(sme_author, ["status"])
        assert r.exit_code == 0
        assert "not available" in r.output.lower() or "not found" in r.output.lower()

    def test_status_reports_total_and_per_list(self, tmp_path: Path) -> None:
        cov = tmp_path / "COV.md"
        cov.write_text(_SAMPLE_COVERAGE, encoding="utf-8")
        with patch(
            "pacca.agents.sme_authoring.gap_analyzer.DEFAULT_COVERAGE_PATH",
            cov,
        ):
            r = CliRunner().invoke(sme_author, ["status"])
        assert r.exit_code == 0, r.output
        assert "Total cases: 100" in r.output
        assert "CARDIOLOGY_CASES" in r.output
        assert "GOLDEN_CASES" in r.output

    def test_status_shows_milestone_gaps(self, tmp_path: Path) -> None:
        cov = tmp_path / "COV.md"
        cov.write_text(_SAMPLE_COVERAGE, encoding="utf-8")
        with patch(
            "pacca.agents.sme_authoring.gap_analyzer.DEFAULT_COVERAGE_PATH",
            cov,
        ):
            r = CliRunner().invoke(sme_author, ["status"])
        assert r.exit_code == 0
        # 300 and 500 milestones should appear; 100 is achieved
        assert "300" in r.output
        assert "500" in r.output


# =============================================================================
# list-batches
# =============================================================================


class TestListBatchesCmd:
    def test_no_roadmap_emits_friendly_warning(self, tmp_path: Path) -> None:
        with patch(
            "pacca.agents.sme_authoring.roadmap_reader.DEFAULT_ROADMAP_PATH",
            tmp_path / "missing.md",
        ):
            r = CliRunner().invoke(sme_author, ["list-batches"])
        assert r.exit_code == 0
        assert "No batches found" in r.output

    def test_lists_parsed_batches(self, tmp_path: Path) -> None:
        roadmap = tmp_path / "ROADMAP.md"
        roadmap.write_text(_SAMPLE_ROADMAP, encoding="utf-8")
        with patch(
            "pacca.agents.sme_authoring.roadmap_reader.DEFAULT_ROADMAP_PATH",
            roadmap,
        ):
            r = CliRunner().invoke(sme_author, ["list-batches"])
        assert r.exit_code == 0, r.output
        assert "Batch A" in r.output
        assert "DENY expansion" in r.output
        assert "Batch B" in r.output


# =============================================================================
# list-gaps
# =============================================================================


class TestListGapsCmd:
    def test_lists_gaps(self, tmp_path: Path) -> None:
        cov = tmp_path / "COV.md"
        cov.write_text(_SAMPLE_COVERAGE, encoding="utf-8")
        with patch(
            "pacca.agents.sme_authoring.gap_analyzer.DEFAULT_COVERAGE_PATH",
            cov,
        ):
            r = CliRunner().invoke(sme_author, ["list-gaps"])
        assert r.exit_code == 0, r.output
        # Should mention the within-specialty cardiology gap (4 < 5)
        assert "Cardiology" in r.output or "CARDIOLOGY" in r.output

    def test_top_flag_limits_output(self, tmp_path: Path) -> None:
        cov = tmp_path / "COV.md"
        cov.write_text(_SAMPLE_COVERAGE, encoding="utf-8")
        with patch(
            "pacca.agents.sme_authoring.gap_analyzer.DEFAULT_COVERAGE_PATH",
            cov,
        ):
            r = CliRunner().invoke(sme_author, ["list-gaps", "--top", "1"])
        assert r.exit_code == 0
        # Only the top 1 gap line should appear (heuristic: count "P1/P2/P3" markers)
        marker_count = r.output.count("\n  P")
        assert marker_count == 1


# =============================================================================
# list-sessions
# =============================================================================


class TestListSessionsCmd:
    def test_empty(self, tmp_path: Path) -> None:
        with patch(
            "pacca.agents.sme_authoring.session.DEFAULT_SESSION_DIR",
            tmp_path,
        ):
            r = CliRunner().invoke(sme_author, ["list-sessions"])
        assert r.exit_code == 0
        assert "No saved sessions" in r.output

    def test_lists_session(self, tmp_path: Path) -> None:
        from pacca.agents.sme_authoring.session import save_session

        state = SessionState(
            session_id="my-sess",
            created_at=datetime.datetime.now(datetime.UTC),
            last_updated_at=datetime.datetime.now(datetime.UTC),
            mode="sandbox",
            last_step="drafted",
        )
        save_session(state, session_dir=tmp_path)

        with patch(
            "pacca.agents.sme_authoring.session.DEFAULT_SESSION_DIR",
            tmp_path,
        ):
            r = CliRunner().invoke(sme_author, ["list-sessions"])
        assert r.exit_code == 0, r.output
        assert "my-sess" in r.output


# =============================================================================
# resume
# =============================================================================


class TestResumeCmd:
    def test_missing_session_errors(self, tmp_path: Path) -> None:
        with patch(
            "pacca.agents.sme_authoring.session.DEFAULT_SESSION_DIR",
            tmp_path,
        ):
            r = CliRunner().invoke(sme_author, ["resume", "never-existed"])
        assert r.exit_code != 0
        assert "not found" in r.output.lower()

    def test_shows_session_details(self, tmp_path: Path) -> None:
        from pacca.agents.sme_authoring.session import save_session

        state = SessionState(
            session_id="show-me",
            created_at=datetime.datetime.now(datetime.UTC),
            last_updated_at=datetime.datetime.now(datetime.UTC),
            mode="sandbox",
            sme_attestation="I attest.",
            last_step="drafted_no_commit",
        )
        save_session(state, session_dir=tmp_path)

        with patch(
            "pacca.agents.sme_authoring.session.DEFAULT_SESSION_DIR",
            tmp_path,
        ):
            r = CliRunner().invoke(sme_author, ["resume", "show-me"])
        assert r.exit_code == 0, r.output
        assert "show-me" in r.output
        assert "drafted_no_commit" in r.output
        assert "I attest" in r.output


# =============================================================================
# batch
# =============================================================================


class TestBatchCmd:
    def test_missing_batch_errors(self, tmp_path: Path) -> None:
        roadmap = tmp_path / "ROADMAP.md"
        roadmap.write_text(_SAMPLE_ROADMAP, encoding="utf-8")
        with patch(
            "pacca.agents.sme_authoring.roadmap_reader.DEFAULT_ROADMAP_PATH",
            roadmap,
        ):
            r = CliRunner().invoke(sme_author, ["batch", "Z"])
        assert r.exit_code != 0
        assert "not found" in r.output.lower()

    def test_existing_batch_shows_manifest(self, tmp_path: Path) -> None:
        roadmap = tmp_path / "ROADMAP.md"
        roadmap.write_text(_SAMPLE_ROADMAP, encoding="utf-8")
        with patch(
            "pacca.agents.sme_authoring.roadmap_reader.DEFAULT_ROADMAP_PATH",
            roadmap,
        ):
            r = CliRunner().invoke(sme_author, ["batch", "A"])
        assert r.exit_code == 0, r.output
        assert "Batch A" in r.output
        assert "DENY expansion" in r.output
        assert "GC-034" in r.output
        assert "GC-035" in r.output
        assert "GC-036" in r.output

    def test_case_insensitive(self, tmp_path: Path) -> None:
        roadmap = tmp_path / "ROADMAP.md"
        roadmap.write_text(_SAMPLE_ROADMAP, encoding="utf-8")
        with patch(
            "pacca.agents.sme_authoring.roadmap_reader.DEFAULT_ROADMAP_PATH",
            roadmap,
        ):
            r = CliRunner().invoke(sme_author, ["batch", "a"])
        assert r.exit_code == 0
        assert "Batch A" in r.output
