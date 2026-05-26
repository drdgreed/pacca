"""
Append a row to docs/CASE_PROVENANCE.md.

Per docs/CASE_PROVENANCE.md, every case gets exactly one row in the
provenance table:

  | Case ID | File | Clinical rationale | Named failure mode | Iteration |

This module appends a new row just before the "## How to use this document"
section header. Idempotent: if the case_id is already in the table, no
duplicate row is written.

Markdown-table row format requires escaping the pipe character (`|`) in
content. We use a single-line rationale (period-stripped, pipe-escaped)
to keep the table parseable by markdown renderers.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

DEFAULT_PROVENANCE_PATH = Path("docs/CASE_PROVENANCE.md")

# Anchor used to find the insertion point. Inserts just BEFORE this line.
_INSERTION_ANCHOR = "## How to use this document"


@dataclass(frozen=True)
class ProvenanceRow:
    """A single row destined for CASE_PROVENANCE.md."""

    case_id: str
    file: str
    clinical_rationale: str
    named_failure_mode: str
    iteration: str

    def render(self) -> str:
        """Render as a markdown table row (ends with newline)."""
        return (
            f"| {self.case_id}"
            f" | {self.file}"
            f" | {_escape_pipe(self.clinical_rationale)}"
            f" | {_escape_pipe(self.named_failure_mode)}"
            f" | {self.iteration} |\n"
        )


class ProvenanceWriterError(Exception):
    """Base class for provenance_writer errors."""


def _escape_pipe(text: str) -> str:
    """
    Escape `|` for markdown-table safety, collapse whitespace to single
    spaces (so multi-line rationales render as a single row).
    """
    normalized = " ".join(text.split())
    return normalized.replace("|", "\\|")


def case_id_already_in_provenance(
    case_id: str,
    provenance_path: Path | None = None,
) -> bool:
    """
    True if the table already contains a row for case_id.

    Used by the agent for idempotency checking before append.
    """
    path = provenance_path or DEFAULT_PROVENANCE_PATH
    if not path.exists():
        return False
    text = path.read_text(encoding="utf-8")
    return f"| {case_id} |" in text or f"| {case_id} " in text


def append_provenance_row(
    row: ProvenanceRow,
    provenance_path: Path | None = None,
) -> None:
    """
    Append `row` to the provenance table.

    The new row is inserted just before the `## How to use this document`
    section header. If the case_id is already in the table, raises
    ProvenanceWriterError (caller can call `case_id_already_in_provenance`
    first to soft-check).

    Args:
        row: The row to append.
        provenance_path: Path to the provenance markdown file.

    Raises:
        FileNotFoundError if the provenance file does not exist.
        ProvenanceWriterError if the insertion anchor is missing or the
            case_id is already present.
    """
    path = provenance_path or DEFAULT_PROVENANCE_PATH
    if not path.exists():
        raise FileNotFoundError(
            f"{path} does not exist. CASE_PROVENANCE.md is created by docs PRs;"
            " ensure the project is correctly set up."
        )

    text = path.read_text(encoding="utf-8")

    if case_id_already_in_provenance(row.case_id, path):
        raise ProvenanceWriterError(
            f"case_id={row.case_id} already has a provenance row. "
            "Call case_id_already_in_provenance() to soft-check first."
        )

    anchor_pos = text.find(_INSERTION_ANCHOR)
    if anchor_pos == -1:
        raise ProvenanceWriterError(
            f"Insertion anchor '{_INSERTION_ANCHOR}' not found in {path}. "
            "Document structure may have changed."
        )

    # Walk back from anchor to the previous blank line so the new row sits
    # at the end of the table (not awkwardly attached to trailing blank lines
    # if any). We want exactly: ...row1\nrow2\n<NEW ROW>\n\n## How to use...
    # Strategy: find the last '\n' before the anchor; that's where the
    # blank-line separator starts.
    insert_pos = anchor_pos
    # Walk back to find the last non-whitespace char (end of the existing table)
    walk = insert_pos - 1
    while walk >= 0 and text[walk] in " \t\n":
        walk -= 1
    # Insert just after the end of the last table row, with a single \n separator
    table_end = walk + 1

    new_text = text[:table_end] + "\n" + row.render() + text[table_end:]

    # Atomic write
    tmp_path = path.with_suffix(path.suffix + ".tmp")
    tmp_path.write_text(new_text, encoding="utf-8")
    tmp_path.replace(path)
