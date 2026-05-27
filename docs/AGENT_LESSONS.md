# Agent lessons — PACCA-specific gotchas

> **Purpose.** Repo-local catalog of mistakes the agent has made while working on PACCA, with rules to prevent recurrence. Companion to the global `~/tasks/lessons.md` (which holds cross-project process discipline).
>
> **Read this file at session start when working on PACCA.** Update after any correction that exposes a PACCA-specific gotcha.
>
> **Why a separate file from `docs/DECISIONS.md`?** DECISIONS.md records *what the system does* (architectural choices, harness iterations). This file records *what the agent gets wrong about the system* (parser quirks, stale tests, environment surprises). Two different audiences, two different append-only logs.

---

## Rendering & docs

### P-001 · GitHub mermaid parser rejects semicolons in message bodies
**Symptom.** README shows "Unable to render rich display" on a `sequenceDiagram` block. The exact error in the GitHub blob view is `Parse error on line N: ...; <text>` with a caret under the character after `;`.

**Cause.** Mermaid treats `;` as a statement terminator in message bodies. After the semicolon, the parser expects an arrow operator (`->>`, `-->>`, etc.) and instead sees a newline, breaking the block.

**Rule.** No `;` in `participant ... : <message>` bodies. Use `,` or `.` or split into two messages.

**Other GitHub-mermaid rejections worth knowing:**
- `{` and `}` in message bodies — parsed as classDef syntax. `/sessions/{id}/validate` breaks; `/sessions/id/validate` works.
- `(` and `)` in **participant aliases** — `participant V as Validators (6)` breaks. Aliases must be bare tokens or multi-word without special chars.
- `<br/>` in `Note over` blocks — flaky across mermaid versions. Keep notes on one line or use mermaid's `<br>` (no slash, sometimes works).
- Reserved keywords (`end`, `loop`, `alt`, `opt`) as participant aliases.

**Validation.** Before pushing any mermaid edit, pipe the block through `mermaid-cli`:
```bash
# extract block from README
awk '/^```mermaid/{p=1;next} /^```$/{p=0} p' file.md > /tmp/block.mmd
# validate with the same parser GitHub uses
npx -p @mermaid-js/mermaid-cli mmdc -i /tmp/block.mmd -o /tmp/test.svg
```
Exit code 0 + a generated SVG = will render on GitHub.

---

## Logging & errors

### P-002 · `pacca.config.get_logger` accepts kwargs; stdlib `logging.getLogger` does not
**Symptom.** Endpoint crashes with `Logger._log() got an unexpected keyword argument 'error'` on what looks like a normal log call.

**Cause.** PACCA's `get_logger` returns a structlog-backed `BoundLogger` that accepts `logger.warning("event", error=str(e), key=val)`. The stdlib `logging.getLogger` returns a regular `Logger` that takes positional message + format args ONLY. Any module that imports `import logging; logger = logging.getLogger(__name__)` will crash on PACCA-style structured kwargs.

**Rule.** Every PACCA module that emits logs uses:
```python
from pacca.config import get_logger
logger = get_logger(__name__)
```
Never `import logging; logger = logging.getLogger(__name__)` in PACCA code. The CI/lint config does not catch this; it's a runtime bug.

---

## Tests & CI

### P-003 · mypy flags previously-unused `# type: ignore` once you re-touch the file
**Symptom.** Pre-commit fails with `error: Unused "type: ignore" comment [unused-ignore]` on a line you didn't change.

**Cause.** mypy re-checks the whole file when you edit it. Newer mypy understands frozen-dataclass attribute assignment natively, so older `# type: ignore[misc]` comments on `g.priority = 99` (for `@dataclass(frozen=True)` test cases) are now flagged as unused.

**Rule.** When the pre-commit `mypy` step fails on a file you touched, check first if the failing line is a pre-existing `# type: ignore` that's no longer needed. If so, remove it — the fix is one line and it cleans up stale technical debt as a side benefit. Don't add `# type: ignore[unused-ignore]` to suppress; just delete the original.

### P-004 · Test environment may lack `uuid_extensions` (CI has it; local conda may not)
**Symptom.** `pytest tests/unit/sme_authoring/` fails at collection with `ModuleNotFoundError: No module named 'uuid_extensions'` on `test_cli_commands.py`, `test_cli_new_subcommands.py`, `test_agent_with_mocked_llm.py`.

**Cause.** `src/pacca/agents/sme_authoring/cli_commands.py:46` imports `uuid_extensions` (a transitive dep of Click). CI installs it via `pip install -e ".[dev]"`. Local conda env may not have it if the dev extras weren't installed.

**Rule.** When local pytest collection errors with `uuid_extensions` missing, run `python -m pip install uuid_extensions` or fall back to running the tests that don't import `cli_commands`:
```bash
pytest tests/unit/sme_authoring/ \
  --ignore=tests/unit/sme_authoring/test_agent_with_mocked_llm.py \
  --ignore=tests/unit/sme_authoring/test_cli_commands.py \
  --ignore=tests/unit/sme_authoring/test_cli_new_subcommands.py
```

### P-005 · Contract change requires broad-grep, not just edits in the file you're already in
**Symptom.** CI fails with stale-test assertions after pushing a "fix" that updated only the test file you were already editing.

**Cause.** When `read_coverage()` was changed to fall back to on-disk file counting, two test files asserted the old "no-fallback" contract: `test_cli_new_subcommands.py` (which I was editing) and `test_gap_analyzer.py` (which I forgot to grep for).

**Rule.** Before pushing a contract change, grep ALL of `tests/` for assertions about the old contract:
```bash
grep -rn 'parsed_ok is False\|"not available"\|count == 0' tests/
```
Then update or delete every match. This applies any time you change: a function's return semantics, a default value, an error condition, an output format, a public API surface.

---

## Git & PR workflow (PACCA-specific overlay on the global rule L-001)

### P-006 · PACCA defaults to branch-and-PR. No direct pushes to main.
**Pattern.** Per `~/.claude/projects/.../memory/pacca_pr_workflow.md` and CLAUDE.md, every change goes through a PR even for tiny doc fixes. The pre-commit hooks may reformat the file (ruff) — re-stage after a failed commit and re-run.

**Rule.**
1. Branch off main with a descriptive name (`fix/<thing>`, `docs/<thing>`, `feat/<thing>`).
2. Commit with a HEREDOC commit message that explains the *why*.
3. Run `git push -u origin <branch>` then `gh pr create --title "..." --body "..."`.
4. **Do not push follow-up commits to the same branch** (see global L-001). If the fix needs amending, branch off main again.
5. If a runbook prescribes direct push: flag the deviation to the user before doing it (per the saved policy).

---

## How to update this file

When the user corrects a PACCA-specific behavior (not a generic process flaw — those go in `~/tasks/lessons.md`), add a P-XXX entry with:

- **Symptom** — what the user or CI sees
- **Cause** — the underlying mechanism, in one or two sentences
- **Rule** — the actionable guard against recurrence
- Optionally: a validation snippet, a known-good code pattern, or related entries

Keep entries terse. The file is meant to be re-readable in two minutes at session start.

---

*Last updated: 2026-05-27.*
