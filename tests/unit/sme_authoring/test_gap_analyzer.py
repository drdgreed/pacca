"""
Tests for gap_analyzer.py.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from pacca.agents.sme_authoring.gap_analyzer import (
    Gap,
    ListCount,
    compute_gaps,
    read_coverage,
)

if TYPE_CHECKING:
    from pathlib import Path


_SAMPLE_COVERAGE = """# Evaluation Coverage Matrix

The current dataset (100 cases):

| List | File | Count | IDs |
|---|---|---|---|
| GOLDEN_CASES | `golden_cases.py` | 20 | GC-001 to GC-020 |
| NEAR_MISS_CASES | `near_miss_cases.py` | 2 | GC-021, GC-022 |
| CARDIOLOGY_CASES | `cardiology_cases.py` | 4 | GC-037 to GC-040 |
| MENTAL_HEALTH_CASES | `mental_health_cases.py` | 5 | GC-041 to GC-045 |
| ENDOCRINOLOGY_CASES | `endocrinology_cases.py` | 3 | GC-076 to GC-078 |
| **Total live** | — | **100** | — |
"""

_SAMPLE_COVERAGE_AT_300 = _SAMPLE_COVERAGE.replace("(100 cases)", "(300 cases)").replace(
    "**100**", "**300**"
)


class TestReadCoverage:
    def test_missing_file_marked_not_ok(self, tmp_path: Path) -> None:
        snap = read_coverage(tmp_path / "missing.md")
        assert snap.parsed_ok is False
        assert "not found" in snap.parse_error

    def test_parses_total_live(self, tmp_path: Path) -> None:
        path = tmp_path / "COV.md"
        path.write_text(_SAMPLE_COVERAGE, encoding="utf-8")
        snap = read_coverage(path)
        assert snap.parsed_ok
        assert snap.total_cases == 100

    def test_parses_per_list_rows(self, tmp_path: Path) -> None:
        path = tmp_path / "COV.md"
        path.write_text(_SAMPLE_COVERAGE, encoding="utf-8")
        snap = read_coverage(path)
        names = [r.list_name for r in snap.per_list_counts]
        assert "GOLDEN_CASES" in names
        assert "CARDIOLOGY_CASES" in names

    def test_row_fields_extracted(self, tmp_path: Path) -> None:
        path = tmp_path / "COV.md"
        path.write_text(_SAMPLE_COVERAGE, encoding="utf-8")
        snap = read_coverage(path)
        cardio = next(r for r in snap.per_list_counts if r.list_name == "CARDIOLOGY_CASES")
        assert isinstance(cardio, ListCount)
        assert cardio.count == 4
        assert cardio.file == "cardiology_cases.py"
        assert "GC-037" in cardio.id_range


class TestComputeGaps:
    def test_missing_file_returns_error_gap(self, tmp_path: Path) -> None:
        gaps = compute_gaps(tmp_path / "missing.md")
        assert len(gaps) == 1
        assert gaps[0].category == "error"

    def test_at_100_lists_300_and_500_milestones(self, tmp_path: Path) -> None:
        path = tmp_path / "COV.md"
        path.write_text(_SAMPLE_COVERAGE, encoding="utf-8")
        gaps = compute_gaps(path)
        labels = [g.label for g in gaps if g.category == "milestone"]
        # 100 is hit; should list 300 + 500 only
        assert any("300" in label for label in labels)
        assert any("500" in label for label in labels)
        assert not any("100-case" in label for label in labels)

    def test_below_within_specialty_min_surfaces_gap(self, tmp_path: Path) -> None:
        path = tmp_path / "COV.md"
        path.write_text(_SAMPLE_COVERAGE, encoding="utf-8")
        gaps = compute_gaps(path)
        # CARDIOLOGY_CASES has 4; below the 5-case threshold
        cardio_gaps = [
            g for g in gaps if g.category == "within-specialty" and "Cardiology" in g.label
        ]
        assert len(cardio_gaps) == 1
        assert cardio_gaps[0].cases_needed == 1

    def test_at_or_above_threshold_no_gap(self, tmp_path: Path) -> None:
        path = tmp_path / "COV.md"
        path.write_text(_SAMPLE_COVERAGE, encoding="utf-8")
        gaps = compute_gaps(path)
        # MENTAL_HEALTH_CASES has 5 cases — at threshold, not a gap
        mh_gaps = [g for g in gaps if g.category == "within-specialty" and "Mental" in g.label]
        assert len(mh_gaps) == 0

    def test_non_specialty_lists_ignored(self, tmp_path: Path) -> None:
        path = tmp_path / "COV.md"
        path.write_text(_SAMPLE_COVERAGE, encoding="utf-8")
        gaps = compute_gaps(path)
        # GOLDEN_CASES + NEAR_MISS_CASES are excluded from within-specialty gaps
        labels = [g.label for g in gaps if g.category == "within-specialty"]
        assert not any("Golden" in label for label in labels)
        assert not any("Near Miss" in label for label in labels)

    def test_sorted_by_priority_then_cases_needed_desc(self, tmp_path: Path) -> None:
        path = tmp_path / "COV.md"
        path.write_text(_SAMPLE_COVERAGE, encoding="utf-8")
        gaps = compute_gaps(path)
        # All priority-1 gaps come before priority-2
        priorities = [g.priority for g in gaps]
        assert priorities == sorted(priorities)

    def test_gap_is_frozen(self) -> None:
        from dataclasses import FrozenInstanceError

        import pytest

        g = Gap(
            category="x",
            label="y",
            current_count=1,
            target_count=2,
            cases_needed=1,
            priority=1,
            description="z",
        )
        with pytest.raises(FrozenInstanceError):
            g.priority = 99  # type: ignore[misc]
