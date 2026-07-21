"""Doc-drift guard, wired into the unit suite so CI runs it on every push.

This is the CI-facing wrapper around the engine in `tests/harness/doc_drift_guard.py`
(kept there alongside the original iter-2 guard). It scans docs/** plus the repo-root
CLAUDE.md / README.md / CONTRIBUTING.md for references to source paths — `src/….py` and
backticked `pacca.*` module paths — and fails if any do not resolve on disk.

Escape hatches for legitimately-unresolvable references (historical incident notes,
planned "(roadmap)" paths, illustrative examples):
  * any line under a heading matching Roadmap / Target architecture / Limitations,
  * a line carrying `<!-- drift-guard: ignore -->` (that line or the one above),
  * anything inside a fenced code block (command/snippet examples).

If this test fails, a doc claims a code path that isn't there — fix the doc (or the
path), or, if the reference is intentional, use one of the escape hatches above.
"""
from __future__ import annotations

from pathlib import Path

from tests.harness.doc_drift_guard import format_report, scan_documentation

_REPO_ROOT = Path(__file__).resolve().parents[2]


def test_docs_have_no_dangling_source_references() -> None:
    dangling = scan_documentation(_REPO_ROOT)
    assert not dangling, format_report(dangling)
