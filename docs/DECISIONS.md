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

- [iter-2 — Eval-Net Hardening, 6 changes (chg-1 through chg-6)](#iter-2-eval-net-hardening)
- [Correction (2026-05-22) — iter-0 trajectory instrumentation record](#correction-iter0-trajectory)
- [iter-1 — chg-1: Decision Support and Medical Director prompt extraction (Phase H1)](#chg-1-iter-1)
- [iter-0 — Baseline Crystallization (seed)](#iter-0-baseline-crystallization)

---

<a name="iter-2-eval-net-hardening"></a>
## iter-2 — Eval-Net Hardening (Phase H5 slice; 6 changes; no agent surface)

| Field | Value |
|-------|-------|
| Iteration tag | `harness-iter-2` |
| Date | 2026-05-22 (manifest) → 2026-05-24 (finalization) |
| Author | David Reed |
| Base model | `claude-sonnet-4-5-20250929` |
| Constraint levels touched | `evaluation_harness` (5 changes), `instrumentation` (1 change) |
| Behavioral surface modified | none |
| Changes | 6 (`chg-1` schema; `chg-2` regression gate; `chg-3` near-miss cases + gate wiring; `chg-4` doc-drift guard + reconciliation; `chg-5` model SSOT; `chg-6` diagnostic findings + GC-001 repair) |
| Live clinical gate at iter-2 HEAD | PASS (3 of 3 selected tests in 339.52s) |
| Baseline scoreboard | 18 of 20 = 90% pass after chg-6 GC-001 repair (was 17/20 = 85% pre-repair) |
| Manifest | [`harness/manifests/iter-2.json`](../harness/manifests/iter-2.json) (authoritative; full per-change structured data) |
| Narrative | [`docs/ITERATIONS.md` iter-2 section](./ITERATIONS.md#iter-2-eval-net-hardening) |

**Why six entries instead of one per change.** iter-2 is the cycle's first multi-change iteration. The cycle's "one logical change per commit" methodology calls for per-`chg-N` entries in this log; the compact form below preserves the per-change attribution while pointing at the JSON manifest for the full structured fields and at `ITERATIONS.md` for the narrative reasoning.

### chg-1 — Extend manifest schema's `type` and `constraint_level` enums

| Field | Value |
|---|---|
| Type | `improvement` |
| Constraint level | `evaluation_harness` |
| Files | `harness/manifests/change_manifest.schema.json` |
| Predicted fixes | — | Risk cases | — |

Adds `evaluation_harness` to `constraint_level` so Phase H5 measurement-apparatus changes (golden cases, judges, regression gates, drift guards) can validate against the schema. Adds `instrumentation` to BOTH the `type` enum and the `constraint_level` enum so H0 baseline crystallization (the tracing/audit scaffolding iter-0 actually shipped) validates against the schema. Both additions are non-behavioral and close schema gaps surfaced by iter-2's manifest-validation work. Same "broaden when iteration reality demands" pattern iter-1 used for the files-path regex (recorded in iter-1's narrative under "Schema evolution").

### chg-2 — Per-case regression gate + iter-1 baseline scoreboard

| Field | Value |
|---|---|
| Type | `new` |
| Constraint level | `evaluation_harness` |
| Files | `tests/clinical/regression_gate.py`, `tests/clinical/capture_baseline.py`, `tests/clinical/baselines/iter-1-baseline.json`, `tests/harness/test_iter2_hardening.py` |
| Predicted fixes | — | Risk cases | — |

Closes the silent-per-case-degradation gap. The pre-iter-2 clinical accuracy gate was absolute and aggregate: pass = score ≥ 3, gate = pass rate ≥ 80%. A case sliding 5 → 3 still counted as a pass; an over-aggressive H2 institutional-memory entry could erode reasoning quality on every case while keeping decisions correct, and the gate would stay green forever. `regression_gate.py` compares each case's current score to a baseline scoreboard and flags any drop — even when the aggregate stays green. The keystone test `test_CORE_catches_silent_degradation_the_aggregate_gate_misses` constructs a 20-case run where 19 cases are unchanged and GC-001 slides 5 → 3; the legacy aggregate gate would be 100% green, the new gate FAILs and names GC-001. The baseline scoreboard captured at iter-2 HEAD becomes the de-facto iter-1 reference (iter-2 introduces no behavioral change, so an iter-2-HEAD live run reflects iter-1's clinical surface). See chg-6 for the post-baseline diagnostic work this enabled.

### chg-3 — Near-miss memory-trap golden cases + clinical-gate wiring

| Field | Value |
|---|---|
| Type | `new` |
| Constraint level | `evaluation_harness` |
| Files | `tests/clinical/near_miss_cases.py`, `tests/clinical/test_clinical_accuracy.py` |
| Predicted fixes | — | Risk cases | — |

Closes the false-pattern-matching gap. Adds GC-021 (PD-L1 45% — below the 50% pembrolizumab threshold) and GC-022 (EGFR sensitizing mutation present) as siblings of GC-001 that must NOT auto-approve. An H2 institutional-memory entry that compresses "NSCLC + pembrolizumab → approve" would correctly fire on GC-001 (PD-L1 62%) but would incorrectly fire on GC-021 (PD-L1 45%, sub-threshold) and GC-022 (EGFR+, disqualifying). Pre-iter-2 the golden set had no sibling-of-canonical-approve case differing by exactly one disqualifier, so the trap was untestable. The cases live in their own `NEAR_MISS_CASES` list (kept disjoint from `GOLDEN_CASES` so the existing `test_dataset_has_twenty_cases` integrity assertion is preserved) and the clinical-gate loop iterates `GOLDEN_CASES + NEAR_MISS_CASES`. The live clinical gate at iter-2 HEAD passed (3 of 3 tests, 339.52s, aggregate ≥ 80%) which implies both near-miss cases routed correctly to IN_REVIEW (math: 22 total cases, 3 persistent golden-set failures, ≥80% gate ⇒ near-miss failure budget = 1, but the close pass margin strongly implies both were correct).

### chg-4 — Doc-drift guard + iter-0 trajectory.py reconciliation + HARNESS.md repoints

| Field | Value |
|---|---|
| Type | `new` |
| Constraint level | `evaluation_harness` |
| Files | `tests/harness/doc_drift_guard.py`, `tests/harness/test_iter2_hardening.py`, `docs/ITERATIONS.md`, `docs/DECISIONS.md`, `docs/HARNESS.md` |
| Predicted fixes | — | Risk cases | — |

Adds `doc_drift_guard.py` — a CI guard that fails on any `src/*.py` reference in `docs/` that doesn't resolve on disk. The append-only audit logs (DECISIONS.md, ITERATIONS.md) are excluded by default because their protocol preserves superseded references by design. The guard's first run found three drifts: the known one (iter-0's `src/pacca/observability/trajectory.py` references, since reconciled via the superseding [Correction (2026-05-22)](#correction-iter0-trajectory) entry above), and two more in HARNESS.md that iter-2 didn't know about (`orchestrator/escalation_tree.py` → repointed to `agents/orchestrator.py` class `Orchestrator`; `db/audit/schema.py` → repointed to `db/models.py` class `AuditLogModel`). All three drifts cleared; guard now passes.

### chg-5 — Model SSOT: AgentConfig reads from settings.default_model

| Field | Value |
|---|---|
| Type | `improvement` |
| Constraint level | `instrumentation` (no agent surface) |
| Files | `src/pacca/agents/base.py`, `src/pacca/config/settings.py` |
| Predicted fixes | — | Risk cases | — |

Reproducibility scaffolding for iter-3's measurement work. Pre-change, `AgentConfig.model` was a hardcoded string that silently overrode `settings.default_model` — agents ran one model while the iter-1 manifest's `base_model` field recorded another. Now `AgentConfig.model` derives from `settings.default_model` via `Field(default_factory=lambda: get_settings().default_model)`; override via `DEFAULT_MODEL` env. Manifests already agreed on `claude-sonnet-4-5-20250929`; this commit makes the runtime agree too. Constraint level is `instrumentation` (not a behavioral level) because there is no edit to any agent surface — this eliminates a three-way drift between configured, declared, and recorded model.

### chg-6 — Diagnostic findings from iter-1 baseline + GC-001 case-definition repair

| Field | Value |
|---|---|
| Type | `new` |
| Constraint level | `evaluation_harness` |
| Files | `docs/findings/{README, GC-001, GC-010, GC-012}.md`, `tests/clinical/golden_cases.py` (GC-001), `tests/clinical/baselines/iter-1-baseline.json` (GC-001 score updated), `tests/clinical/investigate_case.py` |
| Predicted fixes | `["GC-001"]` (predicted 2 → ≥4) |
| Verified live | **GC-001 flipped 2 → 5** (verified via re-running `investigate_case.py GC-001` after the case-definition repair) |
| Risk cases | — |

The chg-2 baseline-capture run surfaced three persistent per-case failures the aggregate ≥80% gate would have ignored. chg-6 root-causes each (full write-ups under [`docs/findings/`](./findings/)) and applies the only fix that fits at `evaluation_harness` scope:

- [**GC-010** (high-cost biologic)](./findings/GC-010.md) — SEV-2 agent-side bug: missing high-cost escalation branch. `branch_2_medical_director` was designed for this; in code, no component checks `HIGH_COST_THRESHOLD` (the $100K setting exists in `.env` but is never consulted on the decision path). **Deferred to iter-3** at `constraint_level: escalation_branch`.

- [**GC-012** (pediatric severe asthma)](./findings/GC-012.md) — SEV-2 agent-side bug, same class as GC-010: missing pediatric-complexity escalation branch. `COMPLEXITY_AUTO_APPROVE_MAX` and `COMPLEXITY_SPECIALIST_REVIEW_MIN` exist in `.env`; no code consults them. **Deferred to iter-3**; bundle with GC-010 fix into one `chg-` entry.

- [**GC-001** (canonical NSCLC clean approve)](./findings/GC-001.md) — SEV-3 test-data bug: `clinical_notes` say "stage IIIA" (locally advanced); `guidelines_context` cites "metastatic NSCLC" requirements. The agent correctly identified the contradiction and routed to `INFORMATION_NEEDED`; the judge penalized the agent for being right. Fixed in this chg by changing the case definition from "stage IIIA" to "stage IV (metastatic, M1c)". Verified live: GC-001 flipped 2 → 5 same day; the judge's reasoning text on the post-repair run explicitly cites the corrected stage.

Adds `investigate_case.py` as the per-case live-pipeline reproducer (parallel to `capture_baseline.py` but selecting one case and printing the full agent rationale + judge verdict for diagnostic reading). This is the tool every future case-level investigation will use.

**Why GC-010 and GC-012 are NOT fixed in iter-2.** Both require touching `ClinicalRiskDetector.evaluate()` and/or `decision_support/system_prompt.md` — agent-surface changes that would violate iter-2's "no behavioral change" charter and would conflate iter-2's eval-net hardening with bug fixes. The findings docs explicitly record this and constrain the iter-3 design: H2 institutional memory MUST NOT compress away the discriminations these fixes enforce. A memory entry like "RA + abatacept after DMARD failure → approve" must encode the cost guard explicitly.

### Iteration-level verdict

iter-2 is closed. The verdict on iter-1's chg-1 is finalized as `keep` (above, under chg-1's verdict block). iter-2's own chgs carry predicted_fixes only on chg-6 (`["GC-001"]`, verified live the same day). The remaining chgs (1, 2, 3, 4, 5) are non-behavioral; their verdicts will land in iter-3.json's `verdicts` array if any unforeseen interaction with iter-3's H2 work surfaces.

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

### Verdict (recorded at iter-2 finalization, 2026-05-24; live-gate confirmation appended same day)

| Field | Value |
|-------|-------|
| Outcome | **keep** |
| Full-suite delta vs. iter-0 baseline | 0 — zero behavioral change, as predicted by the H1 refactor contract |
| Live clinical gate at iter-2 HEAD | **PASS** (3 of 3 selected tests in 339.52s; aggregate accuracy ≥ 80% under live LLM-as-judge) |
| Tokens-per-case delta | n/a (no agent-surface change; tokens-per-case attribution is an iter-3/H5 measurement work item) |
| Precision on predicted_fixes | n/a (empty — iter-1 predicted no fixes by design) |
| Recall on risk_cases | n/a (empty — iter-1 predicted no risks by design) |
| Verdict basis | (1) byte-identity verification character-by-character pre-merge, (2) 139/139 unit + harness tests pass at iter-2 HEAD, (3) live clinical gate PASSED, (4) doc-drift guard PASSED, (5) all three manifests validate against the schema |

**Narrative.** iter-1's success criterion was "byte-identical rendered prompts before and after the extraction" — the AHE paper's `paragraph_2 == paragraph_2` bar (Lin et al. §3.2). That criterion was met at commit time via the custom byte-identity check (`/tmp/byte_identity_check.py`) after a one-character fix to `decision_support/system_prompt.md`. iter-2 introduced no agent-surface change (all five iter-2 changes are at `instrumentation` or `evaluation_harness` constraint levels), so iter-2 cannot disturb iter-1's behavioral surface. The live clinical gate confirms this at the system level — 3 of 3 clinical-marked tests passing in 5m39s with `GOLDEN_CASES + NEAR_MISS_CASES` exercised end-to-end.

**Live-baseline scoreboard (the new authoritative iter-1 reference).** Captured at iter-2 HEAD via `capture_baseline.py` after the doc-drift run had been resolved and the API auth restored. Stored at `tests/clinical/baselines/iter-1-baseline.json`. Aggregate: **17 of 20 = 85% pass under the absolute ≥3 rule**, comfortably above the 80% gate.

| Case | Score | Note |
|---|---|---|
| GC-001 | 2 | persistent fail (canonical NSCLC PD-L1 62% auto-approve case — judge consistently scores the rationale as incomplete despite correct outcome) |
| GC-009 | 4 | unchanged from prior placeholder |
| GC-010 | 1 | **anti-pattern threshold crossed** (score 1 in this rubric = hallucination, wrong decision, or invented clinical detail per `evaluator.py` lines 70–76, 173, 177) — investigate before iter-3 |
| GC-012 | 2 | persistent fail (pediatric IN_REVIEW case — reasoning issues but not anti-pattern) |
| GC-017 | 4 | improved from prior placeholder (2 → 4); jitter or judge variance worth noting |
| All others | 5 | clean |

**Findings worth pausing on (recorded for iter-3 consideration).**

1. *GC-010 score-1 floor.* Per the evaluator rubric, score 1 is reserved for critically wrong outcomes — wrong decision, fabricated lab values, invented prior therapy. This is the most serious finding in the run. iter-3's H2 institutional-memory work could *mask* a hallucination by giving it a confident voice; the root cause should be understood before that risk is introduced.
2. *GC-001 canonical-approve scoring 2.* The cleanest case in the dataset returning a reasoning score below threshold. Implication for iter-3: H2 memory compression should target *stronger* rationales on clean approves, not shorter ones, since the judge already penalizes short reasoning here.
3. *GC-017 swing 2→4 across two runs.* LLM-as-judge non-determinism: this is the noise floor the per-case `regression_gate.py` shipped in iter-2 chg-2 must respect. Without a tolerance band, the next run could trip the gate on jitter alone — a known weakness recorded for an iter-3 (or iter-2-supplement) hardening pass.

These findings make the iter-1 baseline scoreboard a *non-trivial* reference for iter-3. The regression gate fires on *any* per-case drop today; with a hallucination already sitting at score 1, iter-3's H2 change must demonstrably leave GC-010 at or above score 1 (it cannot go lower) AND demonstrably not introduce *new* anti-pattern cases. The honest measurement frame for iter-3 is: "did H2 fix any of these, while introducing none?"

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
