"""
Read DATASET_GROWTH_ROADMAP.md and extract batch specs.

Batches in the roadmap look like:

    #### Batch A — DENY expansion (3 cases) — IDs GC-034 to GC-036
    **File:** `tests/clinical/denial_cases.py` (new)
    - GC-034: Off-label oncology biologic without compendia support (NCCN says no)
    - GC-035: PT visits exceeding annual benefit cap (frequency-cap denial)
    - GC-036: Re-request after prior denial without new clinical evidence

This module parses each `#### Batch <ID> —` header + the following block to
produce a list of Batch dataclasses. The CLI uses this to:
  - List available batches (`pacca sme-author list-batches`)
  - Drive batch-mode authoring (`pacca sme-author batch <ID>`)

ROBUSTNESS
==========

The parser is tolerant of:
- Missing file → returns empty list (the SME's repo may pre-date the
  roadmap, or the docs branch may not be merged yet).
- Partial sections → batches without case bullets are still surfaced
  with whatever metadata can be extracted.
- Format drift → we fail-open (return what we parsed) rather than
  raise; the SME sees what's parseable and the CLI surfaces a warning.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

DEFAULT_ROADMAP_PATH = Path("docs/DATASET_GROWTH_ROADMAP.md")


# Regex for the batch header line, e.g.:
#   #### Batch A — DENY expansion (3 cases) — IDs GC-034 to GC-036
# The em-dash and en-dash variants are both accepted.
# `case_count` and `id_range` are optional (graceful when missing).
_BATCH_HEADER_RE = re.compile(
    r"^####\s+Batch\s+(?P<batch_id>[A-Z]+)\s*[—\-–]\s*"
    r"(?P<name>[^\(\n]+?)"
    r"(?:\s*\((?P<case_count>\d+)\s+cases?\))?"
    r"(?:\s*[—\-–]\s*IDs?\s+(?P<id_range>GC-\d+(?:\s+to\s+GC-\d+)?(?:,\s+GC-\d+)*))?"
    r"\s*$",
    re.MULTILINE,
)

# Regex for the `**File:** `...`` line
_BATCH_FILE_RE = re.compile(
    r"^\*\*File:\*\*\s*`(?P<file>[^`]+)`(?:\s*\((?P<status>new)\))?",
    re.MULTILINE,
)

# Regex for per-case bullets, e.g.:
#   - GC-034: Off-label oncology biologic without compendia support
_BATCH_CASE_BULLET_RE = re.compile(
    r"^\s*-\s+(?P<case_id>GC-\d+):\s*(?P<description>.+?)\s*$",
    re.MULTILINE,
)


@dataclass(frozen=True)
class BatchCase:
    """One case slot within a batch."""

    case_id: str
    description: str


@dataclass(frozen=True)
class Batch:
    """
    A roadmap batch — a coherent group of N cases sharing a single
    named purpose.

    Attributes:
        batch_id: Single-letter identifier ("A", "B", ...).
        name: Human-readable name ("DENY expansion", "Cardiology depth").
        case_count: Number of cases in the batch (may be 0 if unparsed).
        id_range: Raw ID-range string from the header ("GC-034 to GC-036").
        target_file: Filename + sandbox indicator ("denial_cases.py").
        is_new_file: True if the target file is to be created (vs extended).
        cases: Per-case slots within the batch.
    """

    batch_id: str
    name: str
    case_count: int
    id_range: str
    target_file: str
    is_new_file: bool
    cases: list[BatchCase] = field(default_factory=list)


class RoadmapReaderError(Exception):
    """Raised on unrecoverable parse failure."""


def read_batches(roadmap_path: Path | None = None) -> list[Batch]:
    """
    Parse the roadmap and return every batch found.

    Returns an empty list if the file is missing (the CLI surfaces a
    friendly message; this is not an error condition for repos that
    don't yet have the roadmap doc).
    """
    path = roadmap_path or DEFAULT_ROADMAP_PATH
    if not path.exists():
        return []

    text = path.read_text(encoding="utf-8")
    return _parse_batches(text)


def get_batch(batch_id: str, roadmap_path: Path | None = None) -> Batch | None:
    """
    Look up a batch by single-letter ID. Returns None if not found.
    """
    for batch in read_batches(roadmap_path):
        if batch.batch_id == batch_id.upper().strip():
            return batch
    return None


def _parse_batches(text: str) -> list[Batch]:
    """
    Walk the roadmap text + extract every Batch.

    Strategy: find each `#### Batch <ID> —` header, slice the text from
    that header to the next `####` header (or end of file), and parse
    the file + cases from that slice.
    """
    headers = list(_BATCH_HEADER_RE.finditer(text))
    if not headers:
        return []

    batches: list[Batch] = []
    for i, header_match in enumerate(headers):
        start = header_match.end()
        end = headers[i + 1].start() if i + 1 < len(headers) else len(text)
        section = text[start:end]

        batch_id = header_match.group("batch_id")
        name = header_match.group("name").strip()
        case_count_str = header_match.group("case_count")
        case_count = int(case_count_str) if case_count_str else 0
        id_range = header_match.group("id_range") or ""

        # Parse the file line + cases from the section
        file_match = _BATCH_FILE_RE.search(section)
        target_file = ""
        is_new_file = False
        if file_match:
            target_file = file_match.group("file")
            # Strip leading tests/clinical/ if present so target_file is
            # just the base filename (matches FILE_TO_LIST_NAME keys)
            target_file = target_file.removeprefix("tests/clinical/")
            is_new_file = file_match.group("status") == "new"

        cases = [
            BatchCase(case_id=m.group("case_id"), description=m.group("description"))
            for m in _BATCH_CASE_BULLET_RE.finditer(section)
        ]

        batches.append(
            Batch(
                batch_id=batch_id,
                name=name,
                case_count=case_count or len(cases),
                id_range=id_range,
                target_file=target_file,
                is_new_file=is_new_file,
                cases=cases,
            )
        )

    return batches
