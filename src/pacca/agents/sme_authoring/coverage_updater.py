"""
Targeted updates to docs/EVALUATION_COVERAGE.md.

Per the doc's own re-baselining schedule, the per-cell matrices (Dimensions
1-8) are re-baselined on milestone boundaries (100/300/500), not after
every case. This module updates ONLY the header summary table that lists
per-file counts + the "Total live" cell. The agent surfaces a note to the
SME that the per-cell matrices remain on the deferred re-baseline schedule.

The header table looks like:

  | List | File | Count | IDs |
  |---|---|---|---|
  | GOLDEN_CASES | `golden_cases.py` | 20 | GC-001 to GC-020 |
  ...
  | **Total live** | — | **100** | — |

After this module runs, the row for the affected list has its Count + IDs
bumped, and the Total live cell is incremented.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

DEFAULT_COVERAGE_PATH = Path("docs/EVALUATION_COVERAGE.md")


class CoverageUpdaterError(Exception):
    """Base class for coverage_updater errors."""


@dataclass(frozen=True)
class CoverageBump:
    """
    Spec for a single coverage-table update.

    Attributes:
        list_name: The list-variable name in the case file
            (e.g., "CARDIOLOGY_CASES"). Matches the rows of the
            per-file count table.
        file_name: Filename (e.g., "cardiology_cases.py") for the new-row
            case when the list didn't previously exist.
        new_case_id: The newly-added case ID, used to update the IDs cell.
    """

    list_name: str
    file_name: str
    new_case_id: str


def _format_id_range(min_id: str, max_id: str) -> str:
    """Format a range or single ID for the IDs cell."""
    if min_id == max_id:
        return min_id
    return f"{min_id} to {max_id}"


def _parse_id_cell(ids_cell: str) -> tuple[str | None, str | None]:
    """
    Parse the IDs cell text into (min_id, max_id) GC-NNN strings.

    Supports:
    - "GC-001 to GC-020"  → ("GC-001", "GC-020")
    - "GC-001, GC-022"    → ("GC-001", "GC-022")
    - "GC-021, GC-022"    → ("GC-021", "GC-022")
    - "GC-001"            → ("GC-001", "GC-001")
    - ""                  → (None, None)

    For lists with non-contiguous IDs, returns the min and max found.
    """
    matches = re.findall(r"GC-(\d+)", ids_cell)
    if not matches:
        return (None, None)
    nums = sorted({int(m) for m in matches})
    return (f"GC-{nums[0]:03d}", f"GC-{nums[-1]:03d}")


def bump_coverage_for_case(
    bump: CoverageBump,
    coverage_path: Path | None = None,
) -> None:
    """
    Update the per-file count table for a single new case.

    - If the list_name row exists: Count += 1, IDs range extended.
    - If not: a new row is inserted before the Total-live row.
    - Total live row is incremented by 1.

    The per-cell matrices (Dimensions 1-8) are NOT modified. The doc's
    own re-baseline schedule handles those at milestone boundaries.

    Args:
        bump: The CoverageBump describing what to update.
        coverage_path: Path to EVALUATION_COVERAGE.md.

    Raises:
        FileNotFoundError if the coverage file doesn't exist.
        CoverageUpdaterError if the expected table structure is missing.
    """
    path = coverage_path or DEFAULT_COVERAGE_PATH
    if not path.exists():
        raise FileNotFoundError(f"{path} does not exist.")

    text = path.read_text(encoding="utf-8")
    lines = text.splitlines(keepends=True)

    list_row_idx = _find_list_row(lines, bump.list_name)
    total_row_idx = _find_total_live_row(lines)

    if total_row_idx is None:
        raise CoverageUpdaterError(
            f"Could not find Total live row in {path}. Document structure may have changed."
        )

    if list_row_idx is not None:
        lines[list_row_idx] = _update_list_row(lines[list_row_idx], bump.new_case_id)
    else:
        # Insert a new row just before the Total live row
        new_row = f"| {bump.list_name} | `{bump.file_name}` | 1 | {bump.new_case_id} |\n"
        lines.insert(total_row_idx, new_row)
        total_row_idx += 1

    lines[total_row_idx] = _bump_total_live(lines[total_row_idx])

    new_text = "".join(lines)
    tmp_path = path.with_suffix(path.suffix + ".tmp")
    tmp_path.write_text(new_text, encoding="utf-8")
    tmp_path.replace(path)


def _find_list_row(lines: list[str], list_name: str) -> int | None:
    """
    Find the row index in `lines` for the given list_name.

    Looks for a markdown-table row starting with `| {list_name} |` (with
    optional whitespace around the name and pipe).
    """
    pattern = re.compile(rf"^\|\s*{re.escape(list_name)}\s*\|")
    for i, line in enumerate(lines):
        if pattern.match(line):
            return i
    return None


def _find_total_live_row(lines: list[str]) -> int | None:
    """Find the row index for the Total live cell."""
    for i, line in enumerate(lines):
        if "**Total live**" in line:
            return i
    return None


def _update_list_row(line: str, new_case_id: str) -> str:
    """
    Update a single per-file count row: bump Count, extend IDs range.

    Input row format (cells separated by pipes):
        | {list_name} | `{file}` | {count} | {ids} |

    """
    cells = [c.strip() for c in line.strip().strip("|").split("|")]
    if len(cells) < 4:
        raise CoverageUpdaterError(f"Unexpected row format: {line!r}. Expected 4 cells.")

    list_name, file_name, count_str, ids_str = cells[0], cells[1], cells[2], cells[3]

    # Parse current count (may be wrapped in ** for bold)
    count_match = re.search(r"\d+", count_str)
    if not count_match:
        raise CoverageUpdaterError(f"Could not parse count from cell: {count_str!r}")
    new_count = int(count_match.group(0)) + 1

    # Parse and extend IDs range
    min_id, max_id = _parse_id_cell(ids_str)
    new_num = int(new_case_id.removeprefix("GC-"))
    if min_id is None:
        new_ids_str = new_case_id
    else:
        cur_min_num = int(min_id.removeprefix("GC-"))
        cur_max_num = int(max_id.removeprefix("GC-")) if max_id else cur_min_num
        new_min_num = min(cur_min_num, new_num)
        new_max_num = max(cur_max_num, new_num)
        new_ids_str = _format_id_range(f"GC-{new_min_num:03d}", f"GC-{new_max_num:03d}")

    return f"| {list_name} | {file_name} | {new_count} | {new_ids_str} |\n"


def _bump_total_live(line: str) -> str:
    """Increment the **Total live** numeric cell by 1."""

    def repl(m: re.Match[str]) -> str:
        return f"**{int(m.group(1)) + 1}**"

    new_line, count = re.subn(r"\*\*(\d+)\*\*", repl, line, count=1)
    if count == 0:
        # Fallback: try without bold
        def repl_plain(m: re.Match[str]) -> str:
            return str(int(m.group(0)) + 1)

        new_line = re.sub(r"(?<=\| )\d+(?= \|)", repl_plain, line, count=1)
    return new_line
