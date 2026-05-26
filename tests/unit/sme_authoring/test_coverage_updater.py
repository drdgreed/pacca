"""
Tests for coverage_updater.

Strategy:
- Build a minimal EVALUATION_COVERAGE.md in tmp_path mirroring the
  real doc's structure.
- Test bumping existing rows + adding new rows + Total live increment.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from pacca.agents.sme_authoring.coverage_updater import (
    CoverageBump,
    CoverageUpdaterError,
    _bump_total_live,
    _parse_id_cell,
    bump_coverage_for_case,
)

if TYPE_CHECKING:
    from pathlib import Path


_MINIMAL_COVERAGE = """# Evaluation Coverage Matrix

> Status: v1.2 at iter-6 close.

The current dataset (100 cases across 17 lists):

| List | File | Count | IDs |
|---|---|---|---|
| GOLDEN_CASES | `golden_cases.py` | 20 | GC-001 to GC-020 |
| NEAR_MISS_CASES | `near_miss_cases.py` | 2 | GC-021, GC-022 |
| CARDIOLOGY_CASES | `cardiology_cases.py` | 4 | GC-037 to GC-040 |
| **Total live** | — | **100** | — |

### Other content not affected

This section is below the table and should remain unchanged.
"""


@pytest.fixture
def coverage_file(tmp_path: Path) -> Path:
    """Create a minimal EVALUATION_COVERAGE.md in tmp_path."""
    path = tmp_path / "EVALUATION_COVERAGE.md"
    path.write_text(_MINIMAL_COVERAGE, encoding="utf-8")
    return path


# =============================================================================
# _parse_id_cell
# =============================================================================


class TestParseIdCell:
    def test_range_format(self) -> None:
        assert _parse_id_cell("GC-001 to GC-020") == ("GC-001", "GC-020")

    def test_comma_separated(self) -> None:
        assert _parse_id_cell("GC-021, GC-022") == ("GC-021", "GC-022")

    def test_single_id(self) -> None:
        assert _parse_id_cell("GC-100") == ("GC-100", "GC-100")

    def test_empty(self) -> None:
        assert _parse_id_cell("") == (None, None)

    def test_no_match(self) -> None:
        assert _parse_id_cell("none yet") == (None, None)


# =============================================================================
# _bump_total_live
# =============================================================================


class TestBumpTotalLive:
    def test_bumps_bold_count(self) -> None:
        line = "| **Total live** | — | **100** | — |\n"
        result = _bump_total_live(line)
        assert "**101**" in result
        assert "**100**" not in result

    def test_bumps_plain_count(self) -> None:
        line = "| **Total live** | — | 50 | — |\n"
        result = _bump_total_live(line)
        assert "51" in result


# =============================================================================
# bump_coverage_for_case
# =============================================================================


class TestBumpCoverageForCase:
    def test_existing_row_count_incremented(self, coverage_file: Path) -> None:
        bump = CoverageBump(
            list_name="CARDIOLOGY_CASES",
            file_name="cardiology_cases.py",
            new_case_id="GC-201",
        )
        bump_coverage_for_case(bump, coverage_file)
        text = coverage_file.read_text(encoding="utf-8")
        # Count 4 -> 5
        assert "| CARDIOLOGY_CASES | `cardiology_cases.py` | 5" in text

    def test_existing_row_ids_extended(self, coverage_file: Path) -> None:
        bump = CoverageBump(
            list_name="CARDIOLOGY_CASES",
            file_name="cardiology_cases.py",
            new_case_id="GC-201",
        )
        bump_coverage_for_case(bump, coverage_file)
        text = coverage_file.read_text(encoding="utf-8")
        assert "GC-037 to GC-201" in text

    def test_total_live_incremented(self, coverage_file: Path) -> None:
        bump = CoverageBump(
            list_name="CARDIOLOGY_CASES",
            file_name="cardiology_cases.py",
            new_case_id="GC-201",
        )
        bump_coverage_for_case(bump, coverage_file)
        text = coverage_file.read_text(encoding="utf-8")
        assert "**101**" in text
        assert "**100**" not in text

    def test_new_list_inserts_row(self, coverage_file: Path) -> None:
        bump = CoverageBump(
            list_name="NEPHROLOGY_CASES",
            file_name="nephrology_cases.py",
            new_case_id="GC-201",
        )
        bump_coverage_for_case(bump, coverage_file)
        text = coverage_file.read_text(encoding="utf-8")
        assert "| NEPHROLOGY_CASES | `nephrology_cases.py` | 1 | GC-201 |" in text
        # New row inserted BEFORE Total live row
        new_pos = text.find("NEPHROLOGY_CASES")
        total_pos = text.find("**Total live**")
        assert new_pos < total_pos

    def test_unchanged_content_preserved(self, coverage_file: Path) -> None:
        bump = CoverageBump(
            list_name="CARDIOLOGY_CASES",
            file_name="cardiology_cases.py",
            new_case_id="GC-201",
        )
        bump_coverage_for_case(bump, coverage_file)
        text = coverage_file.read_text(encoding="utf-8")
        assert "### Other content not affected" in text
        assert "This section is below the table" in text

    def test_missing_total_live_raises(self, tmp_path: Path) -> None:
        bad = tmp_path / "no_total.md"
        bad.write_text(
            "# Coverage\n\n| List | File | Count | IDs |\n|---|---|---|---|\n"
            "| GOLDEN_CASES | `g.py` | 20 | GC-001 to GC-020 |\n",
            encoding="utf-8",
        )
        bump = CoverageBump(list_name="X", file_name="x.py", new_case_id="GC-001")
        with pytest.raises(CoverageUpdaterError):
            bump_coverage_for_case(bump, bad)

    def test_missing_file_raises(self, tmp_path: Path) -> None:
        missing = tmp_path / "does_not_exist.md"
        bump = CoverageBump(list_name="X", file_name="x.py", new_case_id="GC-001")
        with pytest.raises(FileNotFoundError):
            bump_coverage_for_case(bump, missing)

    def test_min_id_extended_downward(self, coverage_file: Path) -> None:
        # If a new ID is LOWER than existing min, extend downward
        bump = CoverageBump(
            list_name="CARDIOLOGY_CASES",
            file_name="cardiology_cases.py",
            new_case_id="GC-010",
        )
        bump_coverage_for_case(bump, coverage_file)
        text = coverage_file.read_text(encoding="utf-8")
        assert "GC-010 to GC-040" in text
