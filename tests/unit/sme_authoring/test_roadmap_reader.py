"""
Tests for roadmap_reader.py — parses DATASET_GROWTH_ROADMAP.md batch specs.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from pacca.agents.sme_authoring.roadmap_reader import (
    Batch,
    BatchCase,
    get_batch,
    read_batches,
)

if TYPE_CHECKING:
    from pathlib import Path


_SAMPLE_ROADMAP = """# Dataset Growth Roadmap

Some preamble text.

## §2 — The 100-case milestone

### The 12 batches

#### Batch A — DENY expansion (3 cases) — IDs GC-034 to GC-036
**File:** `tests/clinical/denial_cases.py` (new)
- GC-034: Off-label oncology biologic without compendia support (NCCN says no)
- GC-035: PT visits exceeding annual benefit cap (frequency-cap denial)
- GC-036: Re-request after prior denial without new clinical evidence

#### Batch B — Cardiology depth (4 cases) — IDs GC-037 to GC-040
**File:** `tests/clinical/cardiology_cases.py` (new)
- GC-037: TAVR for severe symptomatic AS (clean approve per ACC/AHA)
- GC-038: AFib catheter ablation after failed AAD (clean approve)
- GC-039: ICD primary prevention with LVEF=36% (denied)
- GC-040: Statin primary prevention in 38yo with familial hypercholesterolemia

#### Batch C — Mental health depth (5 cases) — IDs GC-041 to GC-045
**File:** `tests/clinical/mental_health_cases.py` (new)
- GC-041: TMS for treatment-resistant depression
- GC-042: Esketamine intranasal for TRD

Other content between batches is ignored.

#### Batch F — At-threshold cost-boundary (3 cases) — IDs GC-055 to GC-057
**File:** extend `tests/clinical/expansion_cases.py`
- GC-055: Therapy at $99,500/year (just under)
- GC-056: Therapy at $100,500/year (just over)
- GC-057: Mixed-cost case

## §3 — The 300-case milestone

(other content)
"""


class TestReadBatches:
    def test_empty_file_returns_empty(self, tmp_path: Path) -> None:
        roadmap = tmp_path / "ROADMAP.md"
        roadmap.write_text("# Empty roadmap\nNo batches here.\n", encoding="utf-8")
        assert read_batches(roadmap) == []

    def test_missing_file_returns_empty(self, tmp_path: Path) -> None:
        assert read_batches(tmp_path / "does_not_exist.md") == []

    def test_parses_all_batches(self, tmp_path: Path) -> None:
        roadmap = tmp_path / "ROADMAP.md"
        roadmap.write_text(_SAMPLE_ROADMAP, encoding="utf-8")
        batches = read_batches(roadmap)
        ids = [b.batch_id for b in batches]
        assert ids == ["A", "B", "C", "F"]

    def test_parses_batch_metadata(self, tmp_path: Path) -> None:
        roadmap = tmp_path / "ROADMAP.md"
        roadmap.write_text(_SAMPLE_ROADMAP, encoding="utf-8")
        batches = read_batches(roadmap)

        batch_a = batches[0]
        assert isinstance(batch_a, Batch)
        assert batch_a.name == "DENY expansion"
        assert batch_a.case_count == 3
        assert batch_a.id_range == "GC-034 to GC-036"
        assert batch_a.target_file == "denial_cases.py"
        assert batch_a.is_new_file is True

    def test_parses_per_case_bullets(self, tmp_path: Path) -> None:
        roadmap = tmp_path / "ROADMAP.md"
        roadmap.write_text(_SAMPLE_ROADMAP, encoding="utf-8")
        batches = read_batches(roadmap)
        batch_a = batches[0]

        assert len(batch_a.cases) == 3
        case_ids = [c.case_id for c in batch_a.cases]
        assert case_ids == ["GC-034", "GC-035", "GC-036"]
        assert isinstance(batch_a.cases[0], BatchCase)
        assert "compendia" in batch_a.cases[0].description

    def test_strips_tests_clinical_prefix(self, tmp_path: Path) -> None:
        roadmap = tmp_path / "ROADMAP.md"
        roadmap.write_text(_SAMPLE_ROADMAP, encoding="utf-8")
        batches = read_batches(roadmap)
        # Sample writes "tests/clinical/cardiology_cases.py" — should strip
        batch_b = batches[1]
        assert batch_b.target_file == "cardiology_cases.py"

    def test_extends_existing_file_is_not_new(self, tmp_path: Path) -> None:
        roadmap = tmp_path / "ROADMAP.md"
        roadmap.write_text(_SAMPLE_ROADMAP, encoding="utf-8")
        batches = read_batches(roadmap)
        # Batch F extends expansion_cases.py
        batch_f = next(b for b in batches if b.batch_id == "F")
        assert batch_f.is_new_file is False


class TestGetBatch:
    def test_existing_batch_returns(self, tmp_path: Path) -> None:
        roadmap = tmp_path / "ROADMAP.md"
        roadmap.write_text(_SAMPLE_ROADMAP, encoding="utf-8")
        batch = get_batch("B", roadmap)
        assert batch is not None
        assert batch.name == "Cardiology depth"

    def test_case_insensitive(self, tmp_path: Path) -> None:
        roadmap = tmp_path / "ROADMAP.md"
        roadmap.write_text(_SAMPLE_ROADMAP, encoding="utf-8")
        # Lowercase should still find
        batch = get_batch("b", roadmap)
        assert batch is not None
        assert batch.batch_id == "B"

    def test_missing_batch_returns_none(self, tmp_path: Path) -> None:
        roadmap = tmp_path / "ROADMAP.md"
        roadmap.write_text(_SAMPLE_ROADMAP, encoding="utf-8")
        assert get_batch("Z", roadmap) is None
