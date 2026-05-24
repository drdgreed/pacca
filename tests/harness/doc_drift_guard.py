"""
Documentation drift guard — iter-2 eval-net hardening.

WHY THIS EXISTS
---------------
iter-0's records (ITERATIONS.md, DECISIONS.md, EVALUATION.md) describe an
instrumentation deliverable at `src/pacca/observability/trajectory.py`. That
file and that directory do not exist in the codebase. The instrumentation that
actually shipped is OpenTelemetry span emission inside `src/pacca/agents/base.py`
(per-call llm.input_tokens / llm.output_tokens / duration_ms).

A doc that points at code which isn't there is exactly the spec-vs-implementation
drift PACCA's own SDD evaluation lens treats as a defect. This module turns that
class of defect into a test: it scans documentation for source-file references
and flags any that do not resolve on disk. Run it in CI and the docs can never
again claim a file that isn't there without turning a build red.

It is intentionally narrow: it only checks references that look like Python
source paths under `src/` (the place real drift lives), so it won't trip over
prose, URLs, or aspirational future paths written outside backticks.

NOTE ON APPEND-ONLY LOGS
------------------------
DECISIONS.md and ITERATIONS.md are append-only audit logs whose protocol is
"never edit; correct by superseding." They therefore intentionally retain
outdated references (with a correction appended elsewhere), so scanning them
would produce permanent false positives. They are excluded by default; pass a
different `exclude_files` to override.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

# Append-only audit logs that legitimately preserve superseded references.
DEFAULT_EXCLUDED_FILES = ("DECISIONS.md", "ITERATIONS.md")

# Match source-file paths like  src/pacca/observability/trajectory.py
# Anchored on a `src/` segment and ending in `.py`. Allows letters, digits,
# underscores, hyphens, dots and slashes in between.
_SRC_PATH_RE = re.compile(r"src/[A-Za-z0-9_./-]+\.py")


@dataclass
class DanglingReference:
    """A documented source path that does not exist on disk."""

    doc_file: str          # path of the markdown file containing the reference
    referenced_path: str   # the src/... path it points at


def find_dangling_references(
    docs_dir: str | Path,
    repo_root: str | Path,
    exclude_files: tuple[str, ...] | list[str] = DEFAULT_EXCLUDED_FILES,
) -> list[DanglingReference]:
    """
    Scan every .md file under `docs_dir` for `src/....py` references and return
    those that do not resolve under `repo_root`.

    Args:
        docs_dir:      Directory of markdown docs to scan (e.g. <repo>/docs).
        repo_root:     Repository root used to resolve referenced paths.
        exclude_files: Filenames to skip (matched on the file's name, not path).
                       Defaults to the append-only audit logs, which preserve
                       superseded references by design.

    Returns:
        A list of DanglingReference, one per (doc, missing path) pair.
        De-duplicated within a single doc file.
    """
    docs_dir = Path(docs_dir)
    repo_root = Path(repo_root)
    excluded = set(exclude_files)
    dangling: list[DanglingReference] = []

    for md in sorted(docs_dir.rglob("*.md")):
        if md.name in excluded:
            continue
        text = md.read_text(errors="ignore")
        seen: set[str] = set()
        for match in _SRC_PATH_RE.findall(text):
            if match in seen:
                continue
            seen.add(match)
            if not (repo_root / match).exists():
                dangling.append(
                    DanglingReference(doc_file=str(md), referenced_path=match)
                )
    return dangling


def format_report(dangling: list[DanglingReference]) -> str:
    """Human-readable summary for CI logs / test failure messages."""
    if not dangling:
        return "Doc-drift guard: PASSED — every src/*.py reference resolves on disk."
    lines = [f"Doc-drift guard: FAILED — {len(dangling)} dangling reference(s):"]
    for d in dangling:
        lines.append(f"    {d.doc_file} -> {d.referenced_path} (missing)")
    return "\n".join(lines)
