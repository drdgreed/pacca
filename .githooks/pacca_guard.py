#!/usr/bin/env python3
"""
PACCA PHI guard — runs on every commit via .pre-commit-config.yaml.

PURPOSE
=======

Scans the LINES ADDED in the current staging for PHI patterns per
docs/CASE_AUTHORING_GUIDE.md § 4. Blocks commits that would introduce
PHI markers into PACCA's source / test / config files.

Per CLAUDE.md: "Never put real PHI in fixtures, seeds, or committed
files. Synthetic data only." This hook is the per-commit enforcement
of that rule.

DESIGN
======

- Reuses `scan_for_phi` from src/pacca/agents/sme_authoring/validators.py
  as the SSOT. When patterns are added/updated there, the hook picks
  them up automatically.

- Scans ONLY staged-diff additions, not full files. This avoids
  flagging legitimate PHI-shaped content in pre-existing files (test
  fixtures, docs that explain the patterns, etc.).

- Skips files in directories that legitimately contain PHI-shaped
  content as part of their normal operation (tests/, docs/, the hook
  itself, the validator module that defines the patterns).

- Fast: typically completes in < 50 ms on a single-file commit.

EXIT CODES
==========

  0 — no PHI detected in staged additions
  1 — PHI detected (commit blocked; stderr lists file:hits)
  2 — internal error (git command failed, etc.)

INVOCATION
==========

Configured in .pre-commit-config.yaml:

  - id: pacca-phi-secret-guard
    name: PACCA PHI / secret guard
    entry: python3 .githooks/pacca_guard.py
    language: system
    pass_filenames: false
    always_run: true
    stages: [pre-commit]

Can also be run manually:

  python3 .githooks/pacca_guard.py

…to verify the current staging area.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

# Make src/ importable. The hook runs from the repo root.
_REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_REPO_ROOT / "src"))

from pacca.agents.sme_authoring.validators import scan_for_phi

# File-path prefixes to skip. These legitimately contain PHI-shaped
# content as part of their normal operation:
#   - tests/    — test fixtures intentionally include PHI-shaped strings
#                 to verify the validators detect them
#   - docs/     — documentation explains the PHI rules with examples
#   - .githooks/ — the hook itself defines the patterns
#   - src/pacca/agents/sme_authoring/validators.py
#                — the validator module defines the regex patterns
_SKIP_PREFIXES = (
    "tests/",
    "docs/",
    ".githooks/",
    "src/pacca/agents/sme_authoring/validators.py",
    ".pre-commit-config.yaml",
)


def get_staged_files() -> list[str]:
    """
    Return the list of files staged for the current commit.

    Uses `git diff --cached --name-only --diff-filter=ACM` to get only
    Added / Copied / Modified files (excludes Deleted, since we can't
    introduce PHI by deleting content).
    """
    result = subprocess.run(
        ["git", "diff", "--cached", "--name-only", "--diff-filter=ACM"],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        return []
    return [f for f in result.stdout.splitlines() if f]


def get_staged_additions(file: str) -> str:
    """
    Return the lines ADDED to `file` in the current staging.

    Uses `git diff --cached -U0 -- <file>` to get the diff with zero
    context lines, then extracts lines starting with `+` (but not the
    `+++` file header marker).
    """
    result = subprocess.run(
        ["git", "diff", "--cached", "-U0", "--", file],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        return ""

    additions: list[str] = []
    for line in result.stdout.splitlines():
        if line.startswith("+++"):
            continue
        if line.startswith("+"):
            additions.append(line[1:])
    return "\n".join(additions)


def should_skip(file: str) -> bool:
    """True if `file` is in a directory that's intentionally PHI-shape-exempt."""
    return any(file.startswith(p) for p in _SKIP_PREFIXES)


def main() -> int:
    """Run the guard. Return exit code."""
    try:
        staged = get_staged_files()
    except (subprocess.SubprocessError, OSError) as exc:
        print(f"PACCA PHI guard: failed to list staged files: {exc}", file=sys.stderr)
        return 2

    if not staged:
        return 0

    violations: list[tuple[str, list[str]]] = []
    for file in staged:
        if should_skip(file):
            continue
        try:
            additions = get_staged_additions(file)
        except (subprocess.SubprocessError, OSError) as exc:
            print(
                f"PACCA PHI guard: failed to read diff for {file}: {exc}",
                file=sys.stderr,
            )
            return 2
        if not additions:
            continue
        hits = scan_for_phi(additions)
        if hits:
            violations.append((file, hits))

    if not violations:
        return 0

    print(
        "ERROR: PACCA PHI guard detected likely PHI in staged changes.",
        file=sys.stderr,
    )
    print(
        "Per docs/CASE_AUTHORING_GUIDE.md § 4 + CLAUDE.md, use synthetic data only.\n",
        file=sys.stderr,
    )
    for file, hits in violations:
        print(f"  {file}:", file=sys.stderr)
        for hit in hits:
            print(f"    - {hit}", file=sys.stderr)

    print(
        "\nIf the detection is a false positive, you can:\n"
        "  - Revise the lines to remove the PHI-looking pattern, OR\n"
        "  - Add the file path to _SKIP_PREFIXES in .githooks/pacca_guard.py\n"
        "    (with a comment explaining why the file is PHI-shape-exempt)",
        file=sys.stderr,
    )
    return 1


if __name__ == "__main__":
    sys.exit(main())
