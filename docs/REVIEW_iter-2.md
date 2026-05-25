# iter-2 Review Surface

> **Retrospective review index.** iter-2's commits landed directly on `main`
> (4 commits, May 22–24, 2026) before this review surface existed. This
> document is the GitHub-native entry point for reviewing iter-2 after the
> fact: it links each artifact, each change, and each verification gate to
> its source-of-truth in the repo. Use it alongside the PR diff view for a
> file-by-file walk.

## TL;DR

- **What:** Phase H5 slice pulled forward — harden the evaluation harness *before* the first agent-behavioral iteration (iter-3 / Phase H2) lands.
- **Scope:** 6 changes, 0 agent surfaces modified.
- **Outcome:** 1 SEV-3 test-data bug fixed (verified live); 2 SEV-2 agent bugs surfaced and recorded as iter-3 design constraints; 1 LLM-as-judge variance event recorded for follow-up.
- **Baseline aggregate:** 80% → 90% from the single test-data repair.
- **Live clinical gate:** PASS (3 of 3 selected tests in 339.52s).
- **Iteration tag:** [`harness-iter-2-final`](https://github.com/drdgreed/pacca/releases/tag/harness-iter-2-final) at commit `0d3342f` (with `harness-iter-2` retained at `ca2418e` as the first-finalization anchor).

## Read order for reviewers

If you have 5 minutes:
1. This document (the index)
2. [iter-2 iteration verdict in `DECISIONS.md`](./DECISIONS.md#iter-2-eval-net-hardening)

If you have 20 minutes:
1. This document
2. [iter-2 narrative in `ITERATIONS.md`](./ITERATIONS.md#iter-2-eval-net-hardening)
3. [GC-010 finding](./findings/GC-010.md) — the most serious bug surfaced

If you're doing the full audit:
1. This document
2. [iter-2 manifest](../harness/manifests/iter-2.json) — structured per-chg fields
3. [iter-2 narrative in `ITERATIONS.md`](./ITERATIONS.md#iter-2-eval-net-hardening) — full reasoning
4. [iter-2 entries in `DECISIONS.md`](./DECISIONS.md#iter-2-eval-net-hardening) — compact per-chg audit
5. All three [case findings](./findings/) — diagnostic write-ups
6. [`RUNBOOK_iter2.md`](../RUNBOOK_iter2.md) — the runbook iter-2 executed against
7. [`tests/clinical/investigate_case.py`](../tests/clinical/investigate_case.py) — the new per-case reproducer

## Changes shipped (6 total)

| chg | Type | Constraint level | What | Source-of-truth |
|---|---|---|---|---|
| [chg-1](./DECISIONS.md#chg-1--extend-manifest-schemas-type-and-constraint_level-enums) | improvement | evaluation_harness | Extend manifest schema enums (`evaluation_harness`, `instrumentation`) so non-behavioral cycle work can validate | [`change_manifest.schema.json`](../harness/manifests/change_manifest.schema.json) |
| [chg-2](./DECISIONS.md#chg-2--per-case-regression-gate--iter-1-baseline-scoreboard) | new | evaluation_harness | Per-case regression gate + iter-1 baseline scoreboard. Catches silent per-case degradation the aggregate gate misses. | [`tests/clinical/regression_gate.py`](../tests/clinical/regression_gate.py), [`tests/clinical/capture_baseline.py`](../tests/clinical/capture_baseline.py) |
| [chg-3](./DECISIONS.md#chg-3--near-miss-memory-trap-golden-cases--clinical-gate-wiring) | new | evaluation_harness | Near-miss memory-trap golden cases (GC-021 PD-L1 45%, GC-022 EGFR+) wired into the live gate | [`tests/clinical/near_miss_cases.py`](../tests/clinical/near_miss_cases.py), [`tests/clinical/test_clinical_accuracy.py`](../tests/clinical/test_clinical_accuracy.py) |
| [chg-4](./DECISIONS.md#chg-4--doc-drift-guard--iter-0-trajectorypy-reconciliation--harnessmd-repoints) | new | evaluation_harness | Doc-drift guard + iter-0 trajectory.py reconciliation + 2 surprise HARNESS.md repoints | [`tests/harness/doc_drift_guard.py`](../tests/harness/doc_drift_guard.py) |
| [chg-5](./DECISIONS.md#chg-5--model-ssot-agentconfig-reads-from-settingsdefault_model) | improvement | instrumentation | `AgentConfig.model` derives from `settings.default_model` (single source of truth) | [`src/pacca/agents/base.py`](../src/pacca/agents/base.py), [`src/pacca/config/settings.py`](../src/pacca/config/settings.py) |
| [chg-6](./DECISIONS.md#chg-6--diagnostic-findings-from-iter-1-baseline--gc-001-case-definition-repair) | new | evaluation_harness | Diagnostic findings + GC-001 case-def repair (stage IIIA → stage IV; verified live 2 → 5) | [`docs/findings/`](./findings/), [`tests/clinical/golden_cases.py`](../tests/clinical/golden_cases.py), [`tests/clinical/investigate_case.py`](../tests/clinical/investigate_case.py) |

## Findings recorded for iter-3

Each finding is a full diagnostic write-up: what failed, the smallest reproducer, root cause, and a design constraint for the iter-3 fix.

| Finding | Severity | Category | Disposition |
|---|---|---|---|
| [GC-010 — Missing high-cost escalation branch](./findings/GC-010.md) | SEV-2 | agent-side bug | **Deferred to iter-3** at `constraint_level: escalation_branch` |
| [GC-012 — Missing pediatric-complexity escalation branch](./findings/GC-012.md) | SEV-2 | agent-side bug (same class as GC-010) | **Deferred to iter-3** — bundle with GC-010 fix |
| [GC-001 — Stage IIIA vs metastatic guideline mismatch](./findings/GC-001.md) | SEV-3 | test-data bug; agent was correct | **Fixed in chg-6** (evaluation_harness scope; verified live 2 → 5) |

One additional finding without its own document yet: **judge non-determinism** — GC-010 scored 1 in the baseline capture run and 2 in the same-day `investigate_case.py` re-run, with identical agent output both times. This is the cycle's first observed evidence of per-case LLM-as-judge variance and constrains the iter-3 noise-threshold + k=2 rollouts work for `regression_gate.py`.

## Verification gates (all green at `harness-iter-2-final` = `0d3342f`)

| Gate | Result | How to reproduce |
|---|---|---|
| Manifest schema validation | All 3 manifests VALID (`iter-0.json`, `iter-1.json`, `iter-2.json`) | `python -c "import json, jsonschema; jsonschema.validate(json.load(open('harness/manifests/iter-2.json')), json.load(open('harness/manifests/change_manifest.schema.json')))"` |
| Doc-drift guard | PASSED — every `src/*.py` reference in `docs/` resolves on disk | `python -c "from tests.harness.doc_drift_guard import find_dangling_references, format_report; print(format_report(find_dangling_references('docs', '.')))"` |
| Unit + harness suite | 139 of 139 pass in ~7s | `pytest tests/harness tests/unit -q` |
| Live clinical gate | 3 of 3 selected tests pass in 339.52s; aggregate accuracy ≥ 80% under live LLM-as-judge | `pytest tests/clinical/ -m clinical -q` (requires `ANTHROPIC_API_KEY`) |
| Live baseline scoreboard | 18 of 20 cases pass = 90% aggregate | `python -m tests.clinical.capture_baseline --tag harness-iter-1 --out tests/clinical/baselines/iter-1-baseline.json` (requires `ANTHROPIC_API_KEY`) |
| Per-case investigation | Each of GC-001, GC-010, GC-012 reproduces its finding under `investigate_case.py` | `python -m tests.clinical.investigate_case GC-010` (requires `ANTHROPIC_API_KEY`) |

## Commits anchoring this iteration

| SHA | Subject |
|---|---|
| [`35e7000`](https://github.com/drdgreed/pacca/commit/35e7000) | iter-2: harness eval-net hardening + iter-0 trajectory.py reconciliation |
| [`ca2418e`](https://github.com/drdgreed/pacca/commit/ca2418e) | iter-2 finalization: chg-3 gate wiring, chg-5 model reconciliation, iter-1 verdict |
| [`7f7da3a`](https://github.com/drdgreed/pacca/commit/7f7da3a) | iter-1 verdict: live-gate confirmation + authoritative baseline |
| [`0d3342f`](https://github.com/drdgreed/pacca/commit/0d3342f) | chg-6: diagnostic findings from iter-1 baseline + GC-001 case-def repair |

## Tags

- [`harness-iter-2`](https://github.com/drdgreed/pacca/releases/tag/harness-iter-2) → `ca2418e` — the moment iter-2 was first declared finalized
- [`harness-iter-2-final`](https://github.com/drdgreed/pacca/releases/tag/harness-iter-2-final) → `0d3342f` — the moment iter-2 was actually complete (live-gate confirmed + findings shipped + the only repair that fit at evaluation_harness scope)

Both tags exist on purpose. The distance between "we thought we were done" and "we actually were done" is itself methodological content — it records the live-gate-run + diagnostic-investigation work that closed the iteration honestly.

## iter-1 verdict, finalized here

**`keep`.** Recorded in detail at [`DECISIONS.md` § chg-1 verdict](./DECISIONS.md#verdict-recorded-at-iter-2-finalization-2026-05-24-live-gate-confirmation-appended-same-day) and in [`harness/manifests/iter-2.json` verdicts[0]](../harness/manifests/iter-2.json). Basis: byte-identity verification at commit time (per the H1 refactor contract); 139/139 unit + harness suite green at iter-2 HEAD; live clinical gate PASSED; doc-drift guard PASSED; all three manifests validate against the schema. Live-baseline scoreboard at `tests/clinical/baselines/iter-1-baseline.json` is the de-facto iter-1 reference iter-3 will regress against.

## Methodology note: why this PR is retrospective

iter-1 was reviewed via [PR #1](https://github.com/drdgreed/pacca/pull/1) following the project's branch-and-merge workflow. iter-2's commits landed directly on `main` because the iter-2 runbook prescribed `git push && git push --tags` and the runbook was followed literally. This was an oversight — for solo-author portfolio repos like PACCA, PRs are a real audit/review exhibit even when there's only one approver, and iter-1's PR-first pattern is the right default. This review surface restores the GitHub-native review affordances (PR diff view, line-level comments, the "merged" anchor) for iter-2 without rewriting history.

**Going forward,** iter-3 onward will branch first (e.g. `harness/iter-3`), commit per-`chg-N`, open the PR mid-iteration (draft until ready), merge to `main` only when CI is green and the verdict block is drafted, then tag the merge commit. Any future runbook that prescribes a different workflow will be flagged as a discrete decision for the project owner before being followed.
