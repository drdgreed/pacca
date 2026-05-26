"""
Tests for provenance_writer.

Strategy:
- Build a minimal valid CASE_PROVENANCE.md in tmp_path.
- Test row insertion, idempotency, pipe-escaping, missing-anchor errors.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from pacca.agents.sme_authoring.provenance_writer import (
    ProvenanceRow,
    ProvenanceWriterError,
    _escape_pipe,
    append_provenance_row,
    case_id_already_in_provenance,
)

if TYPE_CHECKING:
    from pathlib import Path


_MINIMAL_PROVENANCE = """# Case Provenance — Per-Case Rationale, Failure Mode, and Iteration of Origin

> **Companion to:** [`DATASET_SUFFICIENCY.md`](./DATASET_SUFFICIENCY.md).
> **Status:** v1.0.

## Provenance table

| Case ID | File | Clinical rationale | Named failure mode | Iteration |
|---|---|---|---|---|
| GC-001 | golden_cases.py | NSCLC pembrolizumab clean approve | Coverage | iter-1 |
| GC-002 | golden_cases.py | Lumbar MRI complete documentation | Coverage | iter-1 |

## How to use this document

This is the audit trail.

---

*Last updated: 2026-05-25.*
"""


@pytest.fixture
def provenance_file(tmp_path: Path) -> Path:
    """Create a minimal CASE_PROVENANCE.md in tmp_path."""
    path = tmp_path / "CASE_PROVENANCE.md"
    path.write_text(_MINIMAL_PROVENANCE, encoding="utf-8")
    return path


# =============================================================================
# _escape_pipe
# =============================================================================


class TestEscapePipe:
    def test_no_pipe_unchanged_but_whitespace_collapsed(self) -> None:
        assert _escape_pipe("hello world") == "hello world"

    def test_pipe_escaped(self) -> None:
        assert _escape_pipe("a|b") == "a\\|b"

    def test_multiline_collapsed(self) -> None:
        assert _escape_pipe("line one\nline two") == "line one line two"

    def test_multiple_spaces_collapsed(self) -> None:
        assert _escape_pipe("a   b") == "a b"


# =============================================================================
# ProvenanceRow.render
# =============================================================================


class TestRowRender:
    def test_basic_render(self) -> None:
        row = ProvenanceRow(
            case_id="GC-101",
            file="cardiology_cases.py",
            clinical_rationale="TAVR for severe AS, intermediate STS",
            named_failure_mode="Coverage",
            iteration="iter-7",
        )
        out = row.render()
        assert out == (
            "| GC-101 | cardiology_cases.py "
            "| TAVR for severe AS, intermediate STS "
            "| Coverage | iter-7 |\n"
        )

    def test_render_escapes_pipes_in_rationale(self) -> None:
        row = ProvenanceRow(
            case_id="GC-101",
            file="cardiology_cases.py",
            clinical_rationale="LVEF >= 35% threshold | edge case",
            named_failure_mode="Coverage",
            iteration="iter-7",
        )
        out = row.render()
        assert "\\|" in out


# =============================================================================
# case_id_already_in_provenance
# =============================================================================


class TestIdLookup:
    def test_existing_id_returns_true(self, provenance_file: Path) -> None:
        assert case_id_already_in_provenance("GC-001", provenance_file) is True

    def test_missing_id_returns_false(self, provenance_file: Path) -> None:
        assert case_id_already_in_provenance("GC-999", provenance_file) is False

    def test_nonexistent_file_returns_false(self, tmp_path: Path) -> None:
        missing = tmp_path / "does_not_exist.md"
        assert case_id_already_in_provenance("GC-001", missing) is False


# =============================================================================
# append_provenance_row
# =============================================================================


class TestAppendProvenanceRow:
    def test_new_row_appended_before_how_to_use(self, provenance_file: Path) -> None:
        row = ProvenanceRow(
            case_id="GC-101",
            file="cardiology_cases.py",
            clinical_rationale="New cardiology case for testing",
            named_failure_mode="Coverage",
            iteration="iter-7",
        )
        append_provenance_row(row, provenance_file)

        text = provenance_file.read_text(encoding="utf-8")
        assert "| GC-101 |" in text
        # New row appears before the anchor
        new_row_pos = text.find("| GC-101 |")
        anchor_pos = text.find("## How to use this document")
        assert new_row_pos < anchor_pos

    def test_existing_rows_preserved(self, provenance_file: Path) -> None:
        row = ProvenanceRow(
            case_id="GC-101",
            file="cardiology_cases.py",
            clinical_rationale="New case",
            named_failure_mode="Coverage",
            iteration="iter-7",
        )
        append_provenance_row(row, provenance_file)
        text = provenance_file.read_text(encoding="utf-8")
        assert "| GC-001 |" in text
        assert "| GC-002 |" in text

    def test_duplicate_id_raises(self, provenance_file: Path) -> None:
        row = ProvenanceRow(
            case_id="GC-001",  # Already in fixture
            file="anything.py",
            clinical_rationale="duplicate attempt",
            named_failure_mode="Coverage",
            iteration="iter-7",
        )
        with pytest.raises(ProvenanceWriterError):
            append_provenance_row(row, provenance_file)

    def test_missing_anchor_raises(self, tmp_path: Path) -> None:
        bad = tmp_path / "no_anchor.md"
        bad.write_text(
            "# Provenance\n\n| Case ID | File |\n|---|---|\n| GC-001 | x |\n",
            encoding="utf-8",
        )
        row = ProvenanceRow(
            case_id="GC-101",
            file="x.py",
            clinical_rationale="test",
            named_failure_mode="Coverage",
            iteration="iter-7",
        )
        with pytest.raises(ProvenanceWriterError):
            append_provenance_row(row, bad)

    def test_missing_file_raises(self, tmp_path: Path) -> None:
        missing = tmp_path / "does_not_exist.md"
        row = ProvenanceRow(
            case_id="GC-101",
            file="x.py",
            clinical_rationale="test",
            named_failure_mode="Coverage",
            iteration="iter-7",
        )
        with pytest.raises(FileNotFoundError):
            append_provenance_row(row, missing)

    def test_idempotent_via_soft_check(self, provenance_file: Path) -> None:
        # Pattern the agent uses: check first, then append
        row = ProvenanceRow(
            case_id="GC-101",
            file="cardiology_cases.py",
            clinical_rationale="new case",
            named_failure_mode="Coverage",
            iteration="iter-7",
        )
        assert not case_id_already_in_provenance("GC-101", provenance_file)
        append_provenance_row(row, provenance_file)
        assert case_id_already_in_provenance("GC-101", provenance_file)
        # Second append blocked
        with pytest.raises(ProvenanceWriterError):
            append_provenance_row(row, provenance_file)
