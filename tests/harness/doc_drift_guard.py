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

    doc_file: str  # path of the markdown file containing the reference
    referenced_path: str  # the src/... path it points at


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
                dangling.append(DanglingReference(doc_file=str(md), referenced_path=match))
    return dangling


def format_report(dangling: list[DanglingReference]) -> str:
    """Human-readable summary for CI logs / test failure messages."""
    if not dangling:
        return "Doc-drift guard: PASSED — every src/*.py reference resolves on disk."
    lines = [f"Doc-drift guard: FAILED — {len(dangling)} dangling reference(s):"]
    for d in dangling:
        lines.append(f"    {d.doc_file} -> {d.referenced_path} (missing)")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# v2 — wider scope, more reference kinds, and escape hatches.
#
# The v1 scanner above catches `src/….py` references in docs/. v2 extends this:
#   * scope:    docs/** PLUS repo-root CLAUDE.md / README.md / CONTRIBUTING.md
#   * patterns: `src/….py` AND backticked dotted module paths like `pacca.rag.pipeline`
#               (which must resolve to a module/package under src/) — this is the class
#               that catches fictional commands such as `pacca.harness.validate_manifest`.
#   * escape hatches (for legitimately-unresolvable references — historical incident
#     notes, planned "(roadmap)" paths, illustrative examples):
#       1. any line under a heading matching Roadmap | Target architecture | Limitations
#          is exempt (gives the reconciled docs' roadmap sections a legal home);
#       2. a line carrying the inline marker `<!-- drift-guard: ignore -->` (on the same
#          line or the line immediately above) is exempt.
#
# v1 (find_dangling_references) is kept intact for tests/harness/test_iter2_hardening.py.
# ---------------------------------------------------------------------------

# Root-level docs to include beyond docs/. Kept explicit so the scanned surface is
# obvious and grows via a reviewed edit.
DEFAULT_ROOT_DOCS = ("CLAUDE.md", "README.md", "CONTRIBUTING.md")

IGNORE_MARKER = "<!-- drift-guard: ignore -->"

# Section headings whose bodies are exempt (aspirational / historical by construction).
_EXEMPT_HEADING_RE = re.compile(
    r"^#{1,6}\s+.*\b(roadmap|target architecture|limitations)\b", re.IGNORECASE
)
_ANY_HEADING_RE = re.compile(r"^#{1,6}\s+")

# Backticked dotted module path, e.g. `pacca.rag.pipeline` or `pacca.harness.validate_manifest`.
# Requires a leading `pacca` segment and at least one dot, inside backticks.
_MODULE_RE = re.compile(r"`(pacca(?:\.[A-Za-z0-9_]+)+)`")

# NOTE ON SCOPE: a broader "any backticked repo path (incl. directories) must exist"
# pattern was evaluated and deliberately excluded. It produced ~27 hits dominated by
# legitimate template placeholders (`harness/manifests/iter-N.json`, `iter-N` tags,
# `…-YYYY-Q.md`), planned-doc cross-references, and intentional "this does NOT exist"
# mentions in the reconciled docs — i.e. mostly false positives that would need
# pervasive escape-hatch annotation across canonical docs. The two patterns kept here
# (`src/….py` source files and backticked `pacca.*` modules) catch the high-value drift
# class — a doc pointing at a specific source file or importable module that is not
# there — with near-zero false positives. Broadening is a tracked follow-up if the
# placeholder-noise problem is solved first.


def _module_resolves(dotted: str, repo_root: Path) -> bool:
    """A dotted `pacca.a.b` path resolves if src/pacca/a/b.py or src/pacca/a/b/ exists.

    Trailing segments that are callables/attributes (e.g. `pacca.harness.validate_manifest`
    where validate_manifest is a function) won't resolve as a file; we accept the ref only
    if the FULL dotted path maps to a module file or package dir. That is deliberate — a
    documented `python -m pacca.harness.validate_manifest` implies an importable module.
    """
    rel = Path("src") / Path(*dotted.split("."))
    return (repo_root / rel.with_suffix(".py")).exists() or (repo_root / rel).is_dir()


def _iter_scanned_docs(
    repo_root: Path, docs_dir: Path, root_docs: tuple[str, ...], excluded: set[str]
) -> list[Path]:
    files: list[Path] = []
    for md in sorted(docs_dir.rglob("*.md")):
        if md.name not in excluded:
            files.append(md)
    for name in root_docs:
        p = repo_root / name
        if p.exists() and p.name not in excluded:
            files.append(p)
    return files


def _dangling_in_line(
    line: str, md: Path, repo_root: Path, seen: set[str]
) -> list[DanglingReference]:
    """Resolve the `src/….py` and `pacca.*` references on one (non-exempt) line."""
    out: list[DanglingReference] = []
    for path in _SRC_PATH_RE.findall(line):
        key = f"src:{path}"
        if key not in seen:
            seen.add(key)
            if not (repo_root / path).exists():
                out.append(DanglingReference(str(md), path))
    for dotted in _MODULE_RE.findall(line):
        key = f"mod:{dotted}"
        if key not in seen:
            seen.add(key)
            if not _module_resolves(dotted, repo_root):
                out.append(DanglingReference(str(md), dotted))
    return out


def _line_is_exempt(line: str, prev: str) -> bool:
    """Inline-marker escape hatch (this line or the one above)."""
    return IGNORE_MARKER in line or IGNORE_MARKER in prev


def scan_documentation(
    repo_root: str | Path,
    docs_dir: str | Path | None = None,
    root_docs: tuple[str, ...] = DEFAULT_ROOT_DOCS,
    exclude_files: tuple[str, ...] | list[str] = DEFAULT_EXCLUDED_FILES,
) -> list[DanglingReference]:
    """v2 scan: `src/….py` and backticked `pacca.*` module refs across docs/** + root docs,
    honoring the fenced-code, roadmap-section, and inline-marker escape hatches.
    """
    repo_root = Path(repo_root)
    docs_dir = Path(docs_dir) if docs_dir is not None else repo_root / "docs"
    excluded = set(exclude_files)
    dangling: list[DanglingReference] = []

    for md in _iter_scanned_docs(repo_root, docs_dir, root_docs, excluded):
        lines = md.read_text(errors="ignore").splitlines()
        exempt_section = False
        in_code_fence = False
        seen: set[str] = set()
        for i, line in enumerate(lines):
            # Fenced code blocks hold command/snippet examples — skip them wholesale.
            if line.lstrip().startswith("```"):
                in_code_fence = not in_code_fence
                continue
            if _ANY_HEADING_RE.match(line):
                exempt_section = bool(_EXEMPT_HEADING_RE.match(line))
                continue
            prev = lines[i - 1] if i > 0 else ""
            if in_code_fence or exempt_section or _line_is_exempt(line, prev):
                continue
            dangling.extend(_dangling_in_line(line, md, repo_root, seen))
    return dangling
