"""
Tests for id_allocator.

Strategy:
- Use tmp_path fixtures to create isolated case-file directories.
- Test against synthetic cases-files with known max IDs.
- Test concurrent allocation via threading to verify lock correctness.
"""

from __future__ import annotations

import threading
from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    from pathlib import Path

from pacca.agents.sme_authoring.id_allocator import (
    allocate_ids,
    find_max_existing_id,
    next_id,
    release_reservation,
)


def _write_case_file(case_dir: Path, name: str, ids: list[int]) -> None:
    """Helper: write a minimal *_cases.py file with the given case IDs."""
    body = "\n".join(f'    case_id="GC-{i:03d}",' for i in ids)
    case_dir.joinpath(name).write_text(
        f'"""Synthetic test case file."""\n\nCASES = [\n{body}\n]\n',
        encoding="utf-8",
    )


class TestFindMaxExistingId:
    def test_empty_dir_returns_zero(self, tmp_path: Path) -> None:
        assert find_max_existing_id(tmp_path) == 0

    def test_nonexistent_dir_returns_zero(self, tmp_path: Path) -> None:
        missing = tmp_path / "does_not_exist"
        assert find_max_existing_id(missing) == 0

    def test_single_file_returns_max(self, tmp_path: Path) -> None:
        _write_case_file(tmp_path, "golden_cases.py", [1, 2, 3, 5])
        assert find_max_existing_id(tmp_path) == 5

    def test_multiple_files_returns_global_max(self, tmp_path: Path) -> None:
        _write_case_file(tmp_path, "golden_cases.py", [1, 2, 3])
        _write_case_file(tmp_path, "expansion_cases.py", [50, 51, 52])
        _write_case_file(tmp_path, "denial_cases.py", [33, 34])
        assert find_max_existing_id(tmp_path) == 52

    def test_ignores_non_cases_files(self, tmp_path: Path) -> None:
        # A test file that LOOKS like it has IDs but doesn't end in _cases.py
        tmp_path.joinpath("conftest.py").write_text('case_id="GC-999"', encoding="utf-8")
        _write_case_file(tmp_path, "golden_cases.py", [1, 2, 3])
        assert find_max_existing_id(tmp_path) == 3

    def test_sparse_ids_returns_max(self, tmp_path: Path) -> None:
        # Per CASE_AUTHORING_GUIDE.md § 8, IDs may be sparse if cases are
        # retired. Allocator returns max, not count.
        _write_case_file(tmp_path, "golden_cases.py", [1, 5, 17, 42])
        assert find_max_existing_id(tmp_path) == 42

    def test_handles_4_digit_ids(self, tmp_path: Path) -> None:
        _write_case_file(tmp_path, "golden_cases.py", [999, 1000, 1001])
        assert find_max_existing_id(tmp_path) == 1001


class TestNextId:
    def test_empty_dir_returns_gc_001(self, tmp_path: Path) -> None:
        assert next_id(tmp_path) == "GC-001"

    def test_after_100_returns_101(self, tmp_path: Path) -> None:
        _write_case_file(tmp_path, "golden_cases.py", list(range(1, 101)))
        assert next_id(tmp_path) == "GC-101"

    def test_creates_lock_file(self, tmp_path: Path) -> None:
        next_id(tmp_path)
        assert (tmp_path / ".id_allocator.lock").exists()

    def test_does_not_mutate_case_files(self, tmp_path: Path) -> None:
        _write_case_file(tmp_path, "golden_cases.py", [1, 2, 3])
        original_contents = (tmp_path / "golden_cases.py").read_text(encoding="utf-8")
        next_id(tmp_path)
        assert (tmp_path / "golden_cases.py").read_text(encoding="utf-8") == original_contents

    def test_zero_padded_to_three_digits(self, tmp_path: Path) -> None:
        # New allocator should produce GC-001, not GC-1
        assert next_id(tmp_path) == "GC-001"
        _write_case_file(tmp_path, "golden_cases.py", [8])
        assert next_id(tmp_path) == "GC-009"


class TestAllocateIds:
    def test_count_one_equivalent_to_next_id(self, tmp_path: Path) -> None:
        ids = allocate_ids(1, tmp_path)
        assert ids == ["GC-001"]

    def test_count_five_returns_consecutive(self, tmp_path: Path) -> None:
        _write_case_file(tmp_path, "golden_cases.py", [10])
        assert allocate_ids(5, tmp_path) == [
            "GC-011",
            "GC-012",
            "GC-013",
            "GC-014",
            "GC-015",
        ]

    def test_zero_count_raises(self, tmp_path: Path) -> None:
        with pytest.raises(ValueError):
            allocate_ids(0, tmp_path)

    def test_negative_count_raises(self, tmp_path: Path) -> None:
        with pytest.raises(ValueError):
            allocate_ids(-1, tmp_path)


class TestConcurrentAllocation:
    """
    Lock + reservation correctness: N threads racing on next_id() must
    produce N unique IDs. The reservation file persists the allocation
    across the gap between scan and case-file write, so concurrent
    callers see each other's pending allocations.
    """

    def test_ten_threads_no_collisions(self, tmp_path: Path) -> None:
        results: list[str] = []
        results_lock = threading.Lock()

        def worker() -> None:
            allocated = next_id(tmp_path)
            with results_lock:
                results.append(allocated)

        threads = [threading.Thread(target=worker) for _ in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        # All 10 IDs unique
        assert len(set(results)) == 10, f"Collisions: {results}"
        # All allocated IDs are in the expected range
        for allocated in results:
            n = int(allocated.removeprefix("GC-"))
            assert 1 <= n <= 10


class TestReservationLifecycle:
    """
    Reservation file is the in-flight tracker. Once a case file contains
    the ID, the reservation can be released; the allocator's next scan
    sees the case file and continues from there.
    """

    def test_reservation_persists_across_calls(self, tmp_path: Path) -> None:
        first = next_id(tmp_path)
        assert first == "GC-001"
        # Without releasing or writing the case file, the next allocation
        # should still see the reservation and increment.
        second = next_id(tmp_path)
        assert second == "GC-002"

    def test_release_frees_id_for_reuse(self, tmp_path: Path) -> None:
        # Allocate, then release WITHOUT writing the case file. The next
        # allocation reuses the freed ID since there's no case file or
        # remaining reservation occupying it.
        first = next_id(tmp_path)
        release_reservation(first, tmp_path)
        second = next_id(tmp_path)
        assert second == first

    def test_release_invalid_format_raises(self, tmp_path: Path) -> None:
        with pytest.raises(ValueError):
            release_reservation("invalid-id", tmp_path)

    def test_release_unknown_id_is_noop(self, tmp_path: Path) -> None:
        # Releasing an ID never reserved should silently succeed.
        release_reservation("GC-999", tmp_path)

    def test_allocate_ids_reserves_all(self, tmp_path: Path) -> None:
        # After batch allocation, a subsequent next_id() must see all
        # reservations and increment past them.
        batch = allocate_ids(5, tmp_path)
        assert batch == [f"GC-{i:03d}" for i in range(1, 6)]
        single = next_id(tmp_path)
        assert single == "GC-006"

    def test_case_file_supersedes_reservation(self, tmp_path: Path) -> None:
        # If the case file already contains the ID, releasing the
        # reservation does not reduce the max — the case file is the
        # authoritative record.
        allocated = next_id(tmp_path)
        _write_case_file(tmp_path, "test_cases.py", [1])
        release_reservation(allocated, tmp_path)
        # Next allocation must increment past 1, not return 1
        next_alloc = next_id(tmp_path)
        assert next_alloc == "GC-002"
