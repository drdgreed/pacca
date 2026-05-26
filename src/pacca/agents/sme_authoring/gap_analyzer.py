"""
Parse EVALUATION_COVERAGE.md and compute prioritized gaps.

Produces a list of Gap dataclasses that the CLI surfaces via
`pacca sme-author list-gaps` and references in `status`. Gaps include:
- Outcome class with < N cases
- Specialty with < N cases
- Age stratum with < N cases
- Distance-to-milestone summary

DESIGN
======

The analyzer reads the per-file count table at the top of
EVALUATION_COVERAGE.md (`| List | File | Count | IDs |`) and applies
heuristics to produce a "next-priority" gap list. It does NOT re-derive
the per-cell matrices (those are on a separate re-baseline schedule per
the doc).

The CLI uses this to:
  - `list-gaps`: enumerate the top-N gaps with cases-needed counts.
  - `status`: report distance to 100 / 300 / 500 milestones.

ROBUSTNESS
==========

- Missing file → returns a single Gap saying "EVALUATION_COVERAGE.md
  not found; cannot compute gaps." This is the right behavior for early
  repo setup.
- Format drift → fail-open: surface what's parseable; warn on the rest.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

DEFAULT_COVERAGE_PATH = Path("docs/EVALUATION_COVERAGE.md")

# Milestones from DATASET_SUFFICIENCY.md
_MILESTONES = (
    (100, "production-pilot"),
    (300, "general-payer-deployment"),
    (500, "HIPAA SaMD-grade"),
)

# Minimum count per list for a "within-specialty signal" claim.
# Aligned with DATASET_SUFFICIENCY.md claim 4 (3-5 cases per family).
_WITHIN_SPECIALTY_MIN = 5

# Sentinel filenames that don't represent specialties.
_NON_SPECIALTY_LISTS = frozenset(
    {
        "GOLDEN_CASES",
        "NEAR_MISS_CASES",
        "EXPANSION_CASES",
        "PEDIATRIC_CASES",
        "DEPTH_EXTENSION_CASES",
        "AMBIGUOUS_COMPLETENESS_CASES",
    }
)


@dataclass(frozen=True)
class ListCount:
    """One row from the per-file count table."""

    list_name: str
    file: str
    count: int
    id_range: str


@dataclass(frozen=True)
class Gap:
    """
    A single coverage gap with priority + remedy guidance.

    Attributes:
        category: 'milestone', 'within-specialty', 'outcome-class', etc.
        label: Human-readable name ('DENY class', 'Cardiology', 'production-pilot milestone').
        current_count: Cases currently covering this dimension.
        target_count: Cases needed for the gap to close.
        cases_needed: max(0, target - current).
        priority: 1-3 (1 = highest). Heuristic ordering signal.
        description: One-sentence remedy guidance for the SME.
    """

    category: str
    label: str
    current_count: int
    target_count: int
    cases_needed: int
    priority: int
    description: str


@dataclass(frozen=True)
class CoverageSnapshot:
    """The dataset's current state, as read from EVALUATION_COVERAGE.md."""

    total_cases: int
    per_list_counts: list[ListCount] = field(default_factory=list)
    parsed_ok: bool = True
    parse_error: str = ""


def read_coverage(coverage_path: Path | None = None) -> CoverageSnapshot:
    """Parse EVALUATION_COVERAGE.md into a CoverageSnapshot."""
    path = coverage_path or DEFAULT_COVERAGE_PATH
    if not path.exists():
        return CoverageSnapshot(
            total_cases=0,
            parsed_ok=False,
            parse_error=f"{path} not found",
        )

    text = path.read_text(encoding="utf-8")
    rows = _parse_per_list_table(text)
    total = _parse_total_live(text) or sum(r.count for r in rows)

    return CoverageSnapshot(total_cases=total, per_list_counts=rows)


def compute_gaps(coverage_path: Path | None = None) -> list[Gap]:
    """
    Compute the prioritized gap list.

    Returns gaps sorted by (priority asc, cases_needed desc) — the SME
    sees the most-impactful gap first.
    """
    snapshot = read_coverage(coverage_path)
    if not snapshot.parsed_ok:
        return [
            Gap(
                category="error",
                label="Coverage file missing",
                current_count=0,
                target_count=0,
                cases_needed=0,
                priority=1,
                description=(
                    f"{snapshot.parse_error}. Cannot compute gaps. "
                    "Ensure the docs branch is checked out / merged."
                ),
            )
        ]

    gaps: list[Gap] = []

    # Milestone gaps
    for target, name in _MILESTONES:
        if snapshot.total_cases < target:
            gaps.append(
                Gap(
                    category="milestone",
                    label=f"{target}-case {name} milestone",
                    current_count=snapshot.total_cases,
                    target_count=target,
                    cases_needed=target - snapshot.total_cases,
                    priority=1 if target == 100 else (2 if target == 300 else 3),
                    description=(
                        f"Dataset at {snapshot.total_cases}; need "
                        f"{target - snapshot.total_cases} more cases to reach "
                        f"{target} ({name})."
                    ),
                )
            )

    # Within-specialty gaps
    for row in snapshot.per_list_counts:
        if row.list_name in _NON_SPECIALTY_LISTS:
            continue
        if row.count >= _WITHIN_SPECIALTY_MIN:
            continue
        gaps.append(
            Gap(
                category="within-specialty",
                label=row.list_name.replace("_CASES", "").replace("_", " ").title(),
                current_count=row.count,
                target_count=_WITHIN_SPECIALTY_MIN,
                cases_needed=_WITHIN_SPECIALTY_MIN - row.count,
                priority=2,
                description=(
                    f"Specialty '{row.list_name}' has {row.count} cases; "
                    f"need {_WITHIN_SPECIALTY_MIN - row.count} more for "
                    "within-specialty per-class regression signal."
                ),
            )
        )

    # Sort: priority asc (1 first), then cases_needed desc (biggest gap first)
    gaps.sort(key=lambda g: (g.priority, -g.cases_needed))
    return gaps


# =============================================================================
# Parsers
# =============================================================================


_LIST_ROW_RE = re.compile(
    # Match: | LIST_NAME | `file.py` | count | ids |
    # The count may be bold (**N**) or plain (N).
    r"^\|\s*(?P<list_name>[A-Z_]+)\s*"
    r"\|\s*`(?P<file>[^`]+)`\s*"
    r"\|\s*\*?\*?(?P<count>\d+)\*?\*?\s*"
    r"\|\s*(?P<ids>[^|]*?)\s*\|",
    re.MULTILINE,
)

_TOTAL_LIVE_RE = re.compile(
    r"\|\s*\*\*Total live\*\*\s*\|\s*[^|]*\|\s*\*\*(\d+)\*\*",
)


def _parse_per_list_table(text: str) -> list[ListCount]:
    """Extract per-file count rows from the markdown table."""
    rows = []
    for match in _LIST_ROW_RE.finditer(text):
        rows.append(
            ListCount(
                list_name=match.group("list_name"),
                file=match.group("file"),
                count=int(match.group("count")),
                id_range=match.group("ids").strip(),
            )
        )
    return rows


def _parse_total_live(text: str) -> int | None:
    """Extract the **Total live** count if present."""
    match = _TOTAL_LIVE_RE.search(text)
    return int(match.group(1)) if match else None
