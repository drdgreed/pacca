# PACCA Harness Decisions Log

> **What this is:** an append-only log of every behavioral change to PACCA's agent harness, paired with the predicted impact at the time the change shipped and the verified outcome from the next evaluation round. Updated on every `chg-N:` commit.
>
> **What this is for:** three audiences. (1) Engineers reading the codebase, who want to know *why* a component exists, not just *what* it does. (2) Healthcare reviewers (audit, dispute, QA), who need traceability from a clinical decision back to the harness state that produced it. (3) Future iterations of PACCA itself, which use the verdict history to calibrate future predictions.
>
> **Reading this document:** entries are reverse-chronological (newest at top after the seed). Each entry copies the relevant `change_manifest.json` fields, then — when the next iteration's evaluation has run — adds a verdict block. Entries are never edited or deleted; corrections are made by adding a new entry that supersedes the prior one and citing the supersession.
>
> **Format authority:** entries follow the schema at [`harness/manifests/change_manifest.schema.json`](../harness/manifests/change_manifest.schema.json). The methodology is documented in [`docs/HARNESS.md`](./HARNESS.md) and the underlying paper is Lin et al., *Agentic Harness Engineering* (arXiv:2604.25850, 2026).

---

## Index

- [Correction (2026-05-22) — iter-0 trajectory instrumentation record](#correction-iter0-trajectory)
- [iter-1 — chg-1: Decision Support and Medical Director prompt extraction (Phase H1)](#chg-1-iter-1)
- [iter-0 — Baseline Crystallization (seed)](#iter-0-baseline-crystallization)

---

<a name="correction-iter0-trajectory"></a>
## Correction (2026-05-22) — iter-0 trajectory instrumentation record

| Field | Value |
|-------|-------|
| Supersedes | the iter-0 entry's references to `src/pacca/observability/trajectory.py` (Files row, baseline-metrics "Source" column, and the "Description" paragraph) |
| Date | 2026-05-22 |
| Author | David Reed |
| Iteration | recorded under iter-2 (`harness-iter-2`), chg-4 |
| Scope | documentation only; no code change |

**What the iter-0 entry claimed.** That iter-0 shipped trajectory instrumentation at `src/pacca/observability/trajectory.py`, emitting a per-step structured JSON record (input, tool calls, output, confidence, escalation decision), and that "Tokens per case (mean)" would be populated from `trajectory.py`.

**What actually shipped.** No `src/pacca/observability/` directory or `trajectory.py` file exists in the codebase. The instrumentation that shipped is **OpenTelemetry span emission in `src/pacca/agents/base.py`**: every agent LLM call opens a span recording `llm.input_tokens`, `llm.output_tokens`, `llm.total_tokens`, and `duration_ms` as span attributes, exported via the tracer configured in `src/pacca/config/tracing.py`.

**Corrected facts.**

1. The iter-0 Files row should read `src/pacca/agents/base.py` (OTel span instrumentation), not `src/pacca/observability/trajectory.py (new)`.
2. The baseline-metrics "Tokens per case (mean)" source is `base.py` span attributes (read via an in-memory span exporter or directly from `response.usage`), not `trajectory.py`.
3. There is **no per-step structured JSON trajectory record** and **no reasoning-step counter**. `DecisionAgent.run` (`src/pacca/agents/decision.py`) issues a single forced-tool-use call; the "evaluation framework steps" are reasoning *within one rationale*, not separate invocations. Any verbosity metric for later iterations is therefore defined as **output-tokens-per-case and/or rationale length**, never as a count of "steps."

**Why this supersedes rather than edits.** Per this log's protocol, the iter-0 entry is left intact; this entry is the authoritative record going forward. A dedicated per-case trajectory-record module remains deferred (candidate for the iter-3/H5 measurement work).

**Recurrence prevention.** A documentation drift guard (`tests/harness/doc_drift_guard.py`, shipped in iter-2 chg-4) now fails CI on any `src/*.py` reference in `docs/` that does not resolve on disk, so a doc can no longer claim a file that isn't there.

---

<a name="chg-1-iter-1"></a>
## chg-1 (iter-1) — Decision Support and Medical Director prompt extraction (Phase H1)

| Field | Value |
|-------|-------|
| Iteration tag | `harness-iter-1` |
| Merged commit | `a72249a` (merge of feature branch into main) |
| Date | 2026-05-04 |
| Author | David Reed |
| Base model | `claude-sonnet-4-20250514` |
| Constraint level | `system_prompt` (primary); also touched `pyproject.toml` and the manifest schema |
| Files (7) | `src/pacca/agents/_prompt_loader.py`, `src/pacca/agents/decision_support/system_prompt.md`, `src/pacca/agents/medical_director/system_prompt.md`, `src/pacca/agents/decision.py`, `pyproject.toml`, `harness/manifests/iter-1.json`, `harness/manifests/change_manifest.schema.json` |
| Type | `improvement` (refactor with no behavioral change predicted) |

**Description.** Extracted the agent-specific bodies of `DECISION_AGENT_SYSTEM` and `MEDICAL_DIRECTOR_AGENT_SYSTEM` from f-string constants in `prompts/templates.py` into file-level mount points at `src/pacca/agents/<agent>/system_prompt.md`. Added a Jinja2 loader (`_prompt_loader.py`) that assembles prompts at runtime from the .md file plus the shared components (`AGENT_IDENTITY`, `CLINICAL_SAFETY_GUIDELINES`, `OUTPUT_FORMAT_INSTRUCTIONS`) which remain canonical in `templates.py`. Wired `decision.py`'s `DecisionAgent` and `MedicalDirectorAgent` classes to use the loader. Reconciled three missing dependency declarations (`jinja2`, `python-jose`, `bcrypt`) in `pyproject.toml` after CI surfaced them. Broadened the schema's files-path pattern to allow repo-root config files after the same CI cycle revealed the iter-0 pattern was too strict.

**Failure pattern addressed.** No clinical or runtime failure pattern. This is the structural commit that establishes the file-level decoupling that Phases H2 and H3 require. The H1 success criterion is byte-identical prompt output, not a behavioral gain.

**Root cause.** Pre-H1, agent prompts lived as Python f-string constants inside `prompts/templates.py`, mixed with module-level interpolation logic. Edits to prompts produced diffs that mixed prompt-text changes with module-rendering changes. Phases H2 (Institutional Memory Layer) and H3 (Cross-Step Middleware Tier) require one-file-per-component diffs to attribute behavioral gains correctly; that attribution is impossible without H1 first.

**Predicted fixes.** None. iter-1 is a refactor; no clinical case is targeted.

**Risk cases.** None recorded in the manifest. The risk model is "any case where the rendered prompt differs by even one character from the pre-H1 baseline." This was preempted by a custom byte-identity check that compared the loader's output to the f-string output character-by-character before any runtime change. The check caught one bug — a missing blank line in the Decision Support `system_prompt.md` file — and the fix was a one-character correction. Both prompts confirmed byte-identical post-fix.

**Why this constraint level.** `system_prompt` is the level being decoupled. Tool descriptions, tool implementations, middleware, skills, and sub-agents remain unchanged. The choice to extract only system prompts in chg-1 keeps the scope narrow and makes the verification gate simple (byte-identity check on rendered prompt strings). The two collateral edits to `pyproject.toml` and the schema are not behavioral changes at the agent layer; they're correctness fixes that the chg-1 work surfaced.

**PHI impact.** None. No code path touching Protected Health Information was modified.

**Audit relevant.** No. Prompt versions tracked in `PROMPT_REGISTRY` remain unchanged across the refactor (still `v2.2`), so audit log entries from before and after this commit reconcile cleanly.

**Rollback plan.** `git revert <merge-sha>`. The orphaned `decision_agent.py` was not modified; `templates.py` was not modified beyond unused-imports cleanup. Reverting `decision.py` and removing the new directories restores the pre-H1 state exactly.

**Process notes from this iteration.** Three findings were observed during the work and recorded explicitly in the manifest. Two were deferred to future commits; one was bundled into chg-1 after CI made the case for it.

- *Deferred to chg-2:* `decision_agent.py` is dead code. Defines `DecisionSupportAgent(BaseAgent[DecisionOutput])` at line 52, but no module imports that class. The orchestrator and tests reference `decision.py`'s `DecisionAgent` instead. Deletion is queued for chg-2 with its own manifest entry.

- *Deferred indefinitely:* `decision.py` houses two tier-distinguished agents (Tier 1 Frontline Nurse, Tier 2 Medical Director) in one Python module. Both prompts were extracted to separate file mount points without restructuring the class layout. If a class-level split is later desired, that becomes its own iteration with its own attribution.

- *Originally deferred, then bundled into chg-1 after CI feedback:* `pyproject.toml` was missing declarations for `python-jose` and `bcrypt`, both of which `requirements.txt` declared. The first PR-CI run also revealed that `jinja2` (a new runtime dependency introduced by the loader in this very commit) was undeclared. All three were added to `pyproject.toml` in the same commit. The original "one logical change per commit" deferral was correct in principle but the CI run made the dependency surface visible enough that bundling all three reconciliations into chg-1 became the cleaner outcome. Methodology choice: when a constraint surfaces during execution that the original plan missed, fix it within scope rather than letting CI red ride.

- *Schema evolution:* the iter-0 schema's files-path pattern restricted entries to `^(src/pacca/|harness/|docs/|tests/)`. Adding `pyproject.toml` to the manifest's files list failed validation. The pattern was broadened to accept repo-root config files (`pyproject.toml`, `requirements*.txt`, `setup.py/cfg`, `Dockerfile`, `.gitignore`, `README.md`, `CHANGELOG.md`, `LICENSE`, `Makefile`) and CI workflows (`.github/`). Also generalized `src/pacca/` to `src/` since the project-specific prefix was unnecessary. The pattern broadening is itself in chg-1 because it was caused by chg-1.

### Verdict (recorded at iter-2 finalization, 2026-05-24)

| Field | Value |
|-------|-------|
| Outcome | **keep** |
| Full-suite delta vs. iter-0 baseline | 0 — zero behavioral change, as predicted by the H1 refactor contract |
| Tokens-per-case delta | n/a (no agent-surface change; tokens-per-case attribution is an iter-3/H5 measurement work item) |
| Precision on predicted_fixes | n/a (empty — iter-1 predicted no fixes by design) |
| Recall on risk_cases | n/a (empty — iter-1 predicted no risks by design) |
| Verdict basis | (1) byte-identity verification character-by-character pre-merge, (2) 139/139 tests pass at iter-2 HEAD (unit + harness), (3) doc-drift guard PASSED, (4) all three manifests validate against the schema |

**Narrative.** iter-1's success criterion was "byte-identical rendered prompts before and after the extraction" — the AHE paper's `paragraph_2 == paragraph_2` bar (Lin et al. §3.2). That criterion was met at commit time via the custom byte-identity check (`/tmp/byte_identity_check.py`) after a one-character fix to `decision_support/system_prompt.md`. iter-2 introduced no agent-surface change (all four iter-2 changes are at `instrumentation` or `evaluation_harness` constraint levels), so iter-2 cannot disturb iter-1's behavioral surface. The full unit + harness suite is green at iter-2 HEAD (139 passed in ~7s). All conditions stated in `RUNBOOK_iter2.md` Step 7 for verdict finalization are met.

**What this verdict does NOT cover.** The live clinical-judge gate (`pytest tests/clinical/ -m clinical`) requires an Anthropic API key and was not re-run at iter-2 HEAD. The judge's per-case scoreboard captured in `tests/clinical/baselines/iter-1-baseline.json` (4 of 20 cases at score 2 — GC-001, GC-010, GC-012, GC-017 — aggregate at the 80% floor) is the de-facto iter-1 clinical baseline that iter-3 must not regress against. iter-3 will run the live gate at its HEAD, and the per-case `regression_gate.py` shipped in iter-2 chg-2 will assert each case against this baseline.

---

<a name="iter-0-baseline-crystallization"></a>
## iter-0 — Baseline Crystallization (seed entry)

| Field | Value |
|-------|-------|
| Iteration tag | `harness-iter-0` |
| Date | *(populated when tagged)* |
| Author | David Reed |
| Base model | claude-sonnet-4-20250514 |
| Constraint level | n/a (instrumentation only; no behavioral change) |
| Files | `src/pacca/observability/trajectory.py` (new), `harness/manifests/change_manifest.schema.json` (new), `docs/HARNESS.md` (new), `docs/DECISIONS.md` (new), `docs/ITERATIONS.md` (new), `CHANGELOG.md` (new), `README.md` (updated) |
| Type | `new` (cycle initialization) |

**Description.** Establish the baseline for the v2.3 Harness Engineering Cycle. Tag the v2.2.0 state as `harness-iter-0` and `pre-ahe-baseline`. Add structured trajectory logging. Commit the change-manifest JSON Schema. Add the four documentation files (HARNESS, DECISIONS, ITERATIONS, CHANGELOG). Update README to reference the methodology and link the documentation set.

**Why no behavioral change.** Phase H0's purpose per [PRD §15](../docs/PACCA_PRD_v2.3_Consolidated.md) is to crystallize the measurement infrastructure that subsequent phases iterate against. A behavioral change in iter-0 would contaminate every subsequent attribution, since we could not tell whether a gain came from the v2.3 cycle or from edits made before the cycle formally began. The minimal seed forces every component the cycle adds to earn its place against measured rollouts — the same reasoning the AHE paper applies to its NexAU₀ seed (Lin et al. §3.1).

### Baseline metrics on harness-iter-0

These are the reference numbers every subsequent iteration is measured against. Recorded immediately after tagging.

| Metric | Value | Source |
|--------|-------|--------|
| Unit test count | 140 passing, 0 failing | `pytest tests/` |
| Unit test wall time | ~8 seconds | `pytest tests/` |
| Demo dataset cases | 53 across 8 groups (A–H) | [PRD §19](../docs/PACCA_PRD_v2.3_Consolidated.md) |
| Clinical golden cases | 20 with LLM-as-judge scoring | [PRD §10](../docs/PACCA_PRD_v2.3_Consolidated.md) |
| pass@1 on unified benchmark | *to be populated after H5 unifies the case sources* | Phase H5 deliverable |
| Tokens per case (mean) | *to be populated after H0 instrumentation captures it* | trajectory.py |
| Hallucination zero-tolerance gate | passing on GC-018, GC-019 | `tests/test_clinical_accuracy.py` |
| 7-branch escalation tree coverage | all 7 branches exercised | `tests/test_escalation_tree.py` |

### Why these baseline numbers matter

Two operational consequences flow from recording these numbers explicitly:

First, every claim of improvement in iter-1 onward is a delta against this row. Vague claims like "this iteration improved decision quality" are not admissible — claims must reference one of these metrics or a metric added by a later phase.

Second, the AHE paper's regression-blindness finding ([HARNESS.md §4 Rule 3](./HARNESS.md)) means the eval suite is the safety net against regressions the manifest fails to predict. If the eval suite isn't catching regressions, the eval suite isn't comprehensive enough — Phase H5 expands it specifically to address this.

### iter-0 manifest entry (verbatim)

The full machine-readable manifest is at [`harness/manifests/iter-0.json`](../harness/manifests/iter-0.json) and validates against the schema. The relevant fields:

```json
{
  "iteration": 0,
  "iteration_tag": "harness-iter-0",
  "iso_date": "2026-05-XX",
  "author": "David Reed",
  "base_model": "claude-sonnet-4-20250514",
  "previous_iteration_tag": null,
  "summary": "Crystallize v2.2.0 as the iteration anchor. No behavioral change. Add trajectory instrumentation, manifest schema, and the four documentation files. The minimal seed forces every component the cycle adds to earn its place against measured rollouts.",
  "changes": []
}
```

The `changes` array is empty by design. iter-0 ships infrastructure, not behavior; behavioral changes begin with iter-1's `chg-N:` commits.

### Verdict

n/a — iter-0 has no predictions to verify. The iter-1 evaluation produces baseline-reproduction confirmation only: full suite passes, no regression against the recorded numbers above.

---

## Format reference

Each entry follows this structure:

1. **Header table** — iteration tag, date, author, base model, constraint level, files touched, change type
2. **Description** — one paragraph; what changed
3. **Failure pattern addressed** — phrased as a class, not a single case
4. **Root cause** — why the failure occurs (distinct from the symptom)
5. **Predicted fixes** — case IDs expected to flip from failing to passing
6. **Risk cases** — case IDs at risk of regressing
7. **Why this constraint level** — the engineering decision is *which* level to edit; the rationale lives here
8. **PHI impact** — none / indirect / direct (PACCA-specific field)
9. **Audit relevant** — yes / no (PACCA-specific field; gates whether the change must appear in the immutable PolicyChangeLogEntry per [PRD §14](../docs/PACCA_PRD_v2.3_Consolidated.md))
10. **Rollback plan** — how to revert if the verdict rejects
11. **Verdict** — added after the next iteration's eval; `keep` / `improve` / `rollback` plus precision/recall numbers

The schema at [`harness/manifests/change_manifest.schema.json`](../harness/manifests/change_manifest.schema.json) is the authoritative specification; this prose summary is for human readers.

## On honest reporting

The AHE paper's empirical finding on self-attribution (Lin et al. §4.4.2) is that fix predictions are reliable (~5x random precision and recall) but regression predictions are barely above random (~2x). When a verdict in this document shows a missed regression, that is not a failure of the methodology — it is the methodology working as designed. The honest verdict, including the misses, is what makes the log useful.

This is also what makes the log defensible. A decision log that records only successes is a marketing document; a decision log that records the misses alongside the hits is an engineering record. PACCA's choice is the latter.

---

*This file is updated on every `chg-N:` commit and on every iteration boundary. It is part of PACCA's harness engineering documentation set; see [`docs/HARNESS.md`](./HARNESS.md) for the methodology and [`docs/ITERATIONS.md`](./ITERATIONS.md) for the narrative log.*
