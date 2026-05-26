"""
GC-NNN case-ID allocator with file-lock concurrency protection.

Per CASE_AUTHORING_GUIDE.md § 8 — case IDs are monotonically allocated
across the ENTIRE dataset (all `tests/clinical/*_cases.py` files combined).
Two SMEs running the agent simultaneously cannot collide on the next ID;
this module enforces that via a POSIX file lock on
`tests/clinical/.id_allocator.lock`.

Design:
- `find_max_existing_id(root)`: pure function, scans all *_cases.py files
  for `case_id="GC-NNN"` patterns and returns the maximum NNN found.
- `next_id(root)`: file-locked wrapper. Acquires lock, scans case files +
  the reservation file, appends new ID to the reservation file (atomic
  inside the lock), releases. The reservation persists across the gap
  between allocation and case-file write, so two concurrent callers
  cannot collide.
- `release_reservation(id, root)`: called after the case file is written
  successfully, removes the ID from the reservation file.
- `allocate_ids(root, count)`: batch allocator for `--batch` mode.

Why the reservation file: the lock CANNOT span the case-file write (that
would serialize all writes and defeat parallelism). Instead, the lock
protects the atomic operation "scan + add-to-reservations". Concurrent
callers see each other's reservations via the second scan target.
"""

from __future__ import annotations

import contextlib
import fcntl
import re
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Iterator

# Pattern that matches `case_id="GC-NNN"` in any case file.
# Robust to whitespace and trailing comma; case-insensitive on "GC" prefix
# (though the existing codebase always uses uppercase).
_CASE_ID_PATTERN = re.compile(r'case_id\s*=\s*["\']GC-(\d{1,5})["\']')

# Default directory containing the case files
DEFAULT_CASE_DIR = Path("tests/clinical")

# Lock file path (relative to case_dir)
LOCK_FILENAME = ".id_allocator.lock"

# Reservation file path (relative to case_dir). Stores allocated-but-not-
# yet-written IDs, one per line. Wiped + rebuilt periodically by external
# maintenance (orphan-cleanup).
RESERVATIONS_FILENAME = ".id_allocator.reservations"


def find_max_existing_id(case_dir: Path | None = None) -> int:
    """
    Scan every `*_cases.py` under `case_dir` for `case_id="GC-NNN"` and
    return the maximum N found.

    Returns 0 if no cases exist.

    This is a pure function: no locks, no mutations. Safe to call read-only.

    NOTE: this scans ONLY case files. It does NOT include in-flight
    reservations from the reservation file; for the full picture used by
    the allocator, see `_max_id_considering_reservations`.
    """
    case_dir = case_dir or DEFAULT_CASE_DIR
    if not case_dir.is_dir():
        return 0

    max_id = 0
    for case_file in case_dir.glob("*_cases.py"):
        try:
            text = case_file.read_text(encoding="utf-8")
        except OSError:
            continue
        for match in _CASE_ID_PATTERN.finditer(text):
            id_num = int(match.group(1))
            max_id = max(max_id, id_num)
    return max_id


def _read_reservations(case_dir: Path) -> set[int]:
    """Return the set of currently-reserved (allocated-but-not-yet-written) ID numbers."""
    res_path = case_dir / RESERVATIONS_FILENAME
    if not res_path.exists():
        return set()
    out: set[int] = set()
    for raw_line in res_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line:
            continue
        match = re.match(r"^GC-(\d+)$", line)
        if match:
            out.add(int(match.group(1)))
    return out


def _write_reservations(case_dir: Path, reservations: set[int]) -> None:
    """Atomically write the reservation file (write to tmp + rename)."""
    res_path = case_dir / RESERVATIONS_FILENAME
    tmp_path = res_path.with_suffix(res_path.suffix + ".tmp")
    body = "\n".join(f"GC-{n:03d}" for n in sorted(reservations))
    tmp_path.write_text(body + ("\n" if body else ""), encoding="utf-8")
    tmp_path.replace(res_path)


def _max_id_considering_reservations(case_dir: Path) -> int:
    """Max of (case-files max ID, reservations max ID)."""
    files_max = find_max_existing_id(case_dir)
    reservations = _read_reservations(case_dir)
    res_max = max(reservations) if reservations else 0
    return max(files_max, res_max)


@contextlib.contextmanager
def _exclusive_lock(lock_path: Path) -> Iterator[None]:
    """
    Acquire an exclusive POSIX advisory lock on `lock_path` for the
    duration of the context.

    Creates the lock file if it doesn't exist. The lock is released
    automatically on context exit, including on exception.
    """
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    lock_path.touch(exist_ok=True)

    with lock_path.open("r+", encoding="utf-8") as lock_file:
        try:
            fcntl.flock(lock_file.fileno(), fcntl.LOCK_EX)
            yield
        finally:
            fcntl.flock(lock_file.fileno(), fcntl.LOCK_UN)


def next_id(case_dir: Path | None = None) -> str:
    """
    Allocate the next monotonic GC-NNN case ID and reserve it.

    Acquires a file lock, scans case files AND the reservation file,
    appends the new ID to the reservation file inside the lock, releases.
    The reservation persists across the gap between allocation and case-
    file write, so two concurrent callers cannot collide.

    Callers MUST call `release_reservation(allocated_id)` after the case
    file is written successfully, OR call it from an exception handler
    to release the ID if the write fails.

    Returns:
        Newly-allocated case ID string in GC-NNN format. Numeric part
        is zero-padded to ≥ 3 digits to match existing convention.
    """
    case_dir = case_dir or DEFAULT_CASE_DIR
    lock_path = case_dir / LOCK_FILENAME

    with _exclusive_lock(lock_path):
        current_max = _max_id_considering_reservations(case_dir)
        new_id_num = current_max + 1
        reservations = _read_reservations(case_dir)
        reservations.add(new_id_num)
        _write_reservations(case_dir, reservations)
        return f"GC-{new_id_num:03d}"


def allocate_ids(count: int, case_dir: Path | None = None) -> list[str]:
    """
    Allocate `count` consecutive GC-NNN IDs in one lock-held operation.

    Used by `--batch` mode where the SME plans to write N cases as a unit.
    Reserves all IDs immediately so the SME sees stable IDs across the
    drafting session, even if another agent runs in parallel.

    Args:
        count: Number of IDs to allocate. Must be ≥ 1.

    Returns:
        List of `count` allocated GC-NNN strings in increasing order.

    Raises:
        ValueError if count < 1.
    """
    if count < 1:
        raise ValueError(f"count must be >= 1, got {count}")

    case_dir = case_dir or DEFAULT_CASE_DIR
    lock_path = case_dir / LOCK_FILENAME

    with _exclusive_lock(lock_path):
        current_max = _max_id_considering_reservations(case_dir)
        new_ids = [current_max + i + 1 for i in range(count)]
        reservations = _read_reservations(case_dir)
        reservations.update(new_ids)
        _write_reservations(case_dir, reservations)
        return [f"GC-{n:03d}" for n in new_ids]


def release_reservation(allocated_id: str, case_dir: Path | None = None) -> None:
    """
    Release a previously-reserved ID.

    Called after the case file is successfully written (the case's
    presence in the file serves as the persistent record; the
    reservation file is just the in-flight tracker).

    Also called on write failure to allow the next allocator call to
    reuse the ID. Silently no-ops if the ID is not currently reserved.
    """
    case_dir = case_dir or DEFAULT_CASE_DIR
    lock_path = case_dir / LOCK_FILENAME

    match = re.match(r"^GC-(\d+)$", allocated_id)
    if not match:
        raise ValueError(f"Invalid allocated_id format: {allocated_id!r}")
    n = int(match.group(1))

    with _exclusive_lock(lock_path):
        reservations = _read_reservations(case_dir)
        reservations.discard(n)
        _write_reservations(case_dir, reservations)
