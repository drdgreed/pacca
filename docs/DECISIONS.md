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

- [iter-1 — Example: First Behavioral Change Under H1](#chg-1-iter-1)
- [iter-0 — Baseline Crystallization (seed)](#iter-0-baseline-crystallization)

---

<a name="chg-1-iter-1"></a>
## chg-1 (iter-1) — Example entry: First Behavioral Change Under Phase H1

> **Note:** this entry is a **worked example** showing the format. It will be replaced by the actual first behavioral change when Phase H1 lands. It is included here so the format is reviewable from day one and the iter-0 seed entry is not the only example a reader sees.

| Field | Value |
|-------|-------|
| Iteration tag | `harness-iter-1` |
| Date | *(populated when shipped)* |
| Author | David Reed |
| Base model | claude-sonnet-4-20250514 |
| Constraint level | `system_prompt` |
| Files | `src/pacca/agents/decision_support/system_prompt.md` (extracted from `src/pacca/agents/decision_agent.py`) |
| Type | `improvement` (refactor with no behavioral change) |

**Description.** Extract the Decision Support Agent's system prompt from the Python string literal in `decision_agent.py` into a standalone Markdown file at the canonical mount point. The Jinja2 template renderer is wired up so runtime prompt assembly is unchanged.

**Failure pattern addressed.** No failure pattern — this is a refactor enabling Phase H1's component decoupling exit criterion. Behavioral changes to the prompt would land as separate `chg-N:` commits with their own manifest entries.

**Root cause.** v2.2.0 mixes prompts, tool definitions, and tool implementations inside agent Python files, making file-level diffs of behavioral changes impossible. This refactor establishes the file boundary that subsequent behavioral changes will land against.

**Predicted fixes.** None (refactor only).

**Risk cases.** All 53 demo cases plus all 20 clinical golden cases — a Jinja2 rendering bug would silently break every case. The refactor is therefore gated on full-suite reproduction of iter-0 baseline numbers.

**Why this constraint level.** This change *creates* the system_prompt constraint level by externalizing its file. Refactor commits like this one establish constraint levels; subsequent behavioral commits exercise them.

**PHI impact.** None.

**Audit relevant.** No (no change to audit-logged behavior).

**Rollback plan.** `git revert <sha>` returns the prompt string to `decision_agent.py`. The `prompt_registry` version stays unchanged across the refactor, so no audit-log reconciliation is needed.

### Verdict (recorded after iter-2 evaluation)

*Pending — populated after iter-2's evaluation run completes. Expected fields: `outcome` (keep / improve / rollback), full-suite pass@1 delta vs. iter-0 baseline (target: zero change), tokens/case delta (target: ≤ baseline).*

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
