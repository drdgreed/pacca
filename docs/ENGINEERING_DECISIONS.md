# Engineering Decision Record

> **What this is.** The rationale log for the engineering-approach choices made while building the **runtime-tunable decision thresholds** feature (PR #38), its follow-up fixes (PRs #39, #40), and the **Evidence → Classification triage-pipeline** design. It answers "why was this done this way?" so a future reader doesn't have to reverse-engineer the reasoning from diffs.
>
> **What this is NOT.** It is distinct from:
> - [`docs/DECISIONS.md`](./DECISIONS.md) — the harness-iteration manifest/verdict audit log (what the *harness cycle* did).
> - [`docs/AGENT_LESSONS.md`](./AGENT_LESSONS.md) — PACCA-specific gotchas the agent has hit.
> - [`docs/*_DESIGN.md`](.) — forward-looking design specs for a single change.
>
> This file is the cross-cutting **"why we chose X over Y"** record.
>
> **Format.** Each entry: **Context** (the situation/forcing function) → **Decision** → **Alternatives considered** → **Why** (rationale) → **Consequences** (what it commits us to / follow-ups). Newest workstreams last.

---

## Terms & shorthand

A few PACCA-specific terms used below, so this record stands on its own:

- **AHE** — *Agentic Harness Engineering*, the methodology PACCA's harness cycle follows (Lin et al., arXiv:2604.25850; see [`docs/ITERATIONS.md`](./ITERATIONS.md) / [`docs/HARNESS.md`](./HARNESS.md)). Core discipline: each change touches **one constraint level**, with auditable structure preferred over per-run LLM discretion.
- **golden-20** — the 20-case "golden" clinical dataset (`GOLDEN_CASES`) run end-to-end through the *real* LLM pipeline as the behavioral gate (`make test-clinical`, ~10 min, needs `ANTHROPIC_API_KEY`). The authoritative check that a routing change didn't regress clinical accuracy. Contrast `make test` — the fast deterministic suite that *deselects* these live tests.
- **Tier-1 / Branch 1-3** — the orchestrator's confidence routing (PRD §5.4): **Tier-1** is the first-line `DecisionAgent`; its confidence routes to **Branch 1** (≥ auto-approve threshold → auto-approve), **Branch 2** (escalation ≤ confidence < auto-approve → Medical Director), or **Branch 3** (< escalation → human review).
- **Scope / Approach / Option A·B·C** — local shorthand for the alternatives compared *within a single ADR*; each is spelled out in that ADR's **Alternatives** line (the labels are not global).
- **P-00x** — entries in [`docs/AGENT_LESSONS.md`](./AGENT_LESSONS.md) (PACCA-specific gotchas); referenced here, defined there.
- **py.typed cascade** — PACCA runs strict mypy on every file it touches (incl. tests), so a touched file's pre-existing type-debt surfaces and must be annotated in place. See ADR-011 / P-007.

---

## Part I — ITER-6 asset shipping

### ADR-001 · Ship the iter-6 SVG assets via squash-merge; never `git add -A`
**Context.** Four review-verified iter-6 SVGs sat on `docs/iter-6-assets` (PR #37). Three untracked files also sat in the tree (`docs/PRODUCTION_READINESS.md`, `docs/images/hero.png`, `src/pacca/_init_users.py`).
**Decision.** Squash-merge PR #37 to `main`; stage assets only; leave the three untracked files out.
**Alternatives.** Merge commit (rejected — repo convention is single-commit squashes, e.g. `(#36)`); `git add -A` (rejected, see Why).
**Why.** `RUNBOOK_iter6.md`'s "Untracked-file guard" marks all three as **NEVER commit**. `_init_users.py` is a self-described throwaday workaround carrying a dev DB credential (already public in `docker-compose.yml`, so not a new leak, but still a throwaway); `hero.png` is a placeholder (the real asset is a `dashboard-hero.png` screenshot per `docs/images/README.md`); `PRODUCTION_READINESS.md` is a draft. Squash matches the repo's PR-merge convention.
**Consequences.** The three files remain intentionally untracked. Established the discipline (later codified as P-007-adjacent practice): stage by explicit path.

---

## Part II — Runtime-tunable thresholds: design

### ADR-002 · Make thresholds *truly* runtime-tunable (Scope B), not just internally consistent
**Context.** The orchestrator hardcoded confidence thresholds (0.95/0.90) while the detector read `high_cost`/`complexity` from `settings`, and the admin `/config` override store was read by nothing in the decision path — its "changes take effect immediately" promise was false.
**Decision.** Route every threshold consumer through one accessor so admin `PATCH /config` actually changes routing (Scope B).
**Alternatives.** (A) Fix the inconsistency but keep behavior hardcoded; (C) declare routing fixed policy and remove the tunable surface. Both rejected.
**Why.** The admin API already advertises tunability and validates an escalation-band invariant; the detector's *sibling* thresholds were already config-driven. Making confidence consistent with them — and honoring the documented promise — was the coherent goal.
**Consequences.** Committed to wiring orchestrator + detector + admin to a shared store; later surfaced that *other* admin knobs were also inert (see ADR-009).

### ADR-003 · Shared `effective_settings()` accessor lives in `config/` (Approach A)
**Context.** The override store needed to be readable by the orchestrator and detector (in `agents/`) and writable by admin (in `api/routes/`).
**Decision.** Put the override store + `effective_settings()` in `config/settings.py`, beside `get_settings()`.
**Alternatives.** (B) Dependency-inject a settings snapshot threaded through call sites; (C) make `get_settings()` itself override-aware.
**Why.** **Layering.** `config/` is a leaf everything may import; having `agents/` import from `api/routes/` (where the store used to live) would invert the dependency graph. Approach A is the smallest change, preserves the existing inline-`get_settings()` read pattern, and leaves `get_settings()`'s `@lru_cache` contract untouched (C would have blended a cached singleton with mutable overrides repo-wide).
**Consequences.** One store, three readers; clean to test.

### ADR-004 · Preserve 0.95/0.90 behavior — set the *defaults* to the old hardcoded values
**Context.** Wiring the orchestrator to read settings would change behavior unless the defaults matched the old literals. `settings.py`/`.env` defaulted to 0.85/0.75 — values routing had never actually used.
**Decision.** Change the `auto_approve`/`escalation` confidence defaults to **0.95/0.90**.
**Alternatives.** Adopt the existing 0.85/0.75 as effective values.
**Why.** 0.85/0.75 were never exercised by routing, so they were *untested* — adopting them would ship an unvalidated clinical-routing change (looser auto-approve → more autonomous approvals). Preserving 0.95/0.90 kept the change behavior-neutral, the golden-20 baseline valid, and the iter-6 SVGs accurate. A deliberate re-tuning remains a separate, re-baselined decision.
**Consequences.** The change was provably behavior-neutral at defaults; the live gate was a *preservation* check (contrast ADR-019).

### ADR-005 · Governance via structlog, not a DB `audit_logs` row
**Context.** The design called for an audit-trail entry on each runtime threshold override. The admin `/config` route is deliberately DB-session-free (its test harness mounts the router with no session/JWT).
**Decision.** Record overrides via the project's structlog `get_logger` (which also fixed a latent bug), and defer a formal DB `audit_logs` row to a follow-up.
**Alternatives.** Add `Depends(get_session)` + `AuditRepository` to the route for a DB row.
**Why.** Adding a session dependency would have broken every existing config-API test; the structlog path is the design's explicitly-permitted alternative, flows to the same structured-JSON pipeline, and **fixed a real `TypeError`** (admin logged structlog-style kwargs through a stdlib `logging.getLogger` — see P-002). The HTTP boundary (`ConfigPatchRequest`) already excludes secret fields, so the override log line is safe.
**Consequences.** A DB audit row is a flagged follow-up if stronger HIPAA audit is wanted.

### ADR-006 · Spec & plan live in `docs/`, not `docs/superpowers/specs/`
**Context.** The brainstorming/writing-plans skills default to `docs/superpowers/specs|plans/`.
**Decision.** Use PACCA's `docs/*_DESIGN.md` / `docs/*_PLAN.md` convention instead.
**Why.** The iter-6 design explicitly rejected the `docs/superpowers/` path "to keep the AI-skill framework's fingerprints out of a portfolio exhibit of the AHE methodology." Honoring the project preference (skills permit this override).

---

## Part III — Runtime-tunable thresholds: implementation

### ADR-007 · Validate overrides at *write* time via `model_validate`, not `model_copy`
**Context.** `effective_settings()` first used `base.model_copy(update=overrides)`.
**Decision.** Build the merged dict and run `Settings.model_validate(merged)`; reject unknown keys explicitly.
**Why.** pydantic v2's `model_copy(update=...)` **does not run field validators** — so `apply_overrides({"high_cost_threshold": -1})` was silently accepted, and a negative cost threshold would suppress Medical-Director review (a HIPAA-relevant safety hole). `model_validate` enforces `ge`/`le`; `ValidationError` subclasses `ValueError`, so the existing atomic-rollback `except ValueError` catches it for free. `extra="ignore"` silently drops typo'd keys, so unknown keys are rejected explicitly to prevent no-op overrides.
**Consequences.** Caught in code review; the validated, atomic store is the foundation the other consumers depend on.

### ADR-008 · Extract a pure `select_confidence_branch()` helper
**Context.** The Branch 1-3 routing logic was inline in `process_decision`, coupled to agent mocking — hard to unit-test. No orchestrator test existed.
**Decision.** Extract a pure `select_confidence_branch(confidence, status, auto, esc) -> str`.
**Why.** A pure function is trivially unit-testable with the effective thresholds as parameters (including the "override flips routing" proof and exact-boundary cases), without constructing a `DecisionContext` or mocking agents. Behavior-preserving — the helper reproduces the old `if/elif/else` (including the Branch-1 `status == AUTO_APPROVED` guard).
**Consequences.** Routing is now covered by fast, deterministic tests.

### ADR-009 · "Fix all three" — wire the inert admin knobs the holistic review surfaced
**Context.** A final holistic review found the admin `/config` API advertised three knobs that were accepted/validated/logged but **inert**: the `enable_autonomous_decisions` kill switch (read nowhere), `llm_retry_*` (read once from a frozen `self._settings` snapshot), and `complexity_specialist_review_min` (the detector honored it, but `classification_agent` read raw `get_settings()` and the field wasn't even PATCHable). These were **pre-existing**, not regressions, but making *some* knobs real left the API incoherent.
**Decision.** Owner chose to fix all three in the same PR.
**Alternatives.** Defer to follow-ups; or de-advertise the inert knobs (make the API honest without wiring).
**Why.** The kill switch especially is a documented safety control ("stop all autonomous approvals during an incident") that silently did nothing — dangerous in a clinical system. The other two were the same false-promise class the feature set out to kill.
**Consequences.** Kill switch guarded in the orchestrator (behavior-neutral at default `True`); retry reads `effective_settings()` per call; `complexity_specialist_review_min` exposed in `/config`. The `classification_agent` "parity" sub-finding dissolved on investigation (see ADR-010).

---

## Part IV — Process & methodology

### ADR-010 · Revert the classification "parity" rabbit hole; ship only the real `/config` field
**Context.** A holistic review flagged `classification_agent.py` as diverging from the detector on `complexity_specialist_review_min`. The first fix attempt re-added deleted enums, added a `mypy ignore_errors` override to a production file, and relied on a stale `.pyc`.
**Decision.** Revert that attempt; investigation showed `ClinicalClassificationAgent` is dead/unwired (orchestrator never calls it; imports removed model classes; PEP-695 syntax). Ship only the genuinely valuable part — exposing the threshold in `/config`.
**Why.** "Fixing parity" in dead code is pointless, and propping it up with suppressions + a stale `.pyc` masks breakage rather than fixing it. The detector is the live consumer; the `/config` field completes *its* tunability. The dead agent is a separate decision (became the triage-pipeline build, Part V).
**Consequences.** Established that an implementer "DONE" report must survive controller scrutiny; bad commits get reverted, not patched over.

### ADR-011 · Never blanket-disable a quality gate to pass it
**Context.** Touching a file surfaced its pre-existing strict-mypy violations on commit. One attempt added `[[tool.mypy.overrides]] module = ["tests.*"] ignore_errors = true`.
**Decision.** Reject the blanket override; fix the touched file in place (return annotations; narrow per-line `# type: ignore[method-assign]` for unavoidable mock assignments).
**Why.** A `tests.*` ignore disables type-checking for the *whole* suite, erasing coverage other work earned. Suppressing a gate to pass it hides the failure. This is the established "py.typed cascade" practice — each change absorbs the type-debt of files it touches.
**Consequences.** Codified as **P-007** in `AGENT_LESSONS.md`.

### ADR-012 · Scope discipline — decline out-of-scope "must-fixes," capture as follow-ups
**Context.** Reviews surfaced real but *pre-existing*, *out-of-scope* issues (a misleading auto-approve audit reason; a negligible double `effective_settings()` call).
**Decision.** Don't fix unrelated pre-existing issues inside a scoped change; file them as follow-up chips (the audit-reason one became PR #40).
**Why.** The AHE methodology's core principle is not crossing scope/constraint boundaries within a change. Folding an unrelated fix in inflates the diff and risks the scoped change's behavior-neutrality.
**Consequences.** Clean, single-purpose PRs; a small backlog of honestly-tracked follow-ups.

### ADR-013 · Subagent-driven execution with two-stage (spec → quality) review
**Context.** A multi-task plan needed implementation without polluting the controller's context.
**Decision.** One fresh implementer subagent per task, followed by an independent **spec-compliance** review, then an independent **code-quality** review; controller synthesizes and applies scope judgment.
**Why.** Fresh, skeptical reviewers that re-derive truth from the diff catch what a self-report misses (they caught ADR-007's validation gap, ADR-010's gate erosion, ADR-009's rabbit hole). Spec-first ordering avoids polishing code that builds the wrong thing.
**Consequences.** More subagent calls, but issues caught early; the controller stays the judgment layer (declines bad reviewer "must-fixes," reverts bad implementer commits).

### ADR-014 · Branch-and-PR for *every* change, including docs; verify behavior at the *final* HEAD
**Context.** PACCA defaults to branch-and-PR (P-006). Routing changes need empirical proof, not assertion.
**Decision.** Every change (even a two-line lessons append) goes through a branch + PR. For decision-routing changes, run the live golden-20 gate (`make test-clinical`) **at the final merge HEAD**, not just an intermediate one.
**Why.** `make test` is deterministic and deselects the live LLM tests; only the live gate proves clinical-routing behavior. Verifying at an intermediate HEAD doesn't cover later commits. CLAUDE.md: "empirically verify before claiming done."
**Consequences.** Codified as **P-008**; the threshold PR ran the live gate twice (post-Task-5 and at the final HEAD).

---

## Part V — Triage pipeline (Evidence → Classification) design

### ADR-015 · Adapt the stranded agents to the *current* architecture, not resurrect the obsolete vintage
**Context.** `ClinicalClassificationAgent` (and `EvidenceAggregationAgent`, and `types.py`) are spec'd in the PRD/SDD/ARCHITECTURE but were written against an *older* architecture: a rich nested `AuthorizationRequest`, a more abstract `BaseAgent` (`_call_llm`, generics, chaining hooks), and models never built (`ClassificationResult`, `UrgencyLevel`, `AgentType`). The codebase later refactored to a simpler one (`ClinicalCase` + `BaseAgent.execute(user_input, response_model)`), leaving these agents broken.
**Decision.** **Rewrite** the agents against today's architecture (read `ClinicalCase`; subclass the real `BaseAgent`; create only the minimal missing models). Do not resurrect the old vintage.
**Why.** YAGNI. The salvageable assets are the prompts (which exist and are tested) and the contract concept; the obsolete machinery (rich request, abstract base) would be a much larger, unjustified change.
**Consequences.** "Full build" means rewrite + new minimal models + integration — a real feature, not a repair.

### ADR-016 · Advisory enrichment (Option A) — keep the LLM out of the safety-critical gate
**Context.** The detector *already* scores complexity deterministically and gates on it pre-flight; the SDD requires pre-flight to stay LLM-free. The classification agent also scores complexity (via LLM), creating overlap.
**Decision.** Run Evidence + Classification **after** the pre-flight gate, **before** Tier-1, as *advisory enrichment*: their outputs enrich the DecisionAgent's prompt + the audit trail, but routing stays owned by the existing deterministic logic. The detector's complexity remains authoritative for gating; the classification score is advisory.
**Alternatives.** (B) Classification *replaces* detector complexity — rejected: makes the deterministic safety gate depend on an LLM, violating the SDD's stated rationale. (C) Full triage routing — classification can route SPECIALIST/HUMAN directly — deferred: most orchestrator surgery + a real new failure mode (an LLM misclassification short-circuiting the decision pipeline and its human-visible rationale).
**Why.** Lowest risk, spec-aligned, preserves the "auditable structure over LLM discretion" ethos. Divergence between the two complexity scores is *expected* and documented; the detector wins for gating.
**Consequences.** The agents add context, not control.

### ADR-017 · Build both agents (full PRD flow), not classification-only
**Context.** Classification could read `ClinicalCase` directly and skip the upstream `EvidenceAggregationAgent`.
**Decision.** Owner chose to build **both** agents — the full PRD Evidence → Classification → Decision flow.
**Alternatives.** Classification only (smallest); classification + just the `types.py` syntax fix.
**Why.** Owner preference — realize the documented pipeline rather than a partial slice.
**Consequences.** Roughly double the build (evidence has its own never-built models); one spec, phased plan.

### ADR-018 · Agents use the real `BaseAgent.execute()` pattern (KISS), not the `AgentContext` chaining machinery
**Context.** `types.py`'s `AgentContext` (with `agent_outputs`, `has_run`) is "designed for chaining," but every *working* agent (`DecisionAgent`, `MedicalDirectorAgent`) instead builds a string prompt and calls `self.execute(user_input, response_model)`.
**Decision.** Both rewritten agents follow the `DecisionAgent` pattern; the orchestrator threads outputs between them; `DecisionContext` gains optional `evidence`/`classification` fields. `AgentContext` is not revived.
**Alternatives.** Fix + use `AgentContext` for chaining semantics.
**Why.** Consistency with how agents are actually built today; reviving `AgentContext` would resurrect dead machinery and require two new enums (`AgentType`, `AgentAutonomyLevel`) for no functional gain.
**Consequences.** `types.py` ends up fully unused → delete it (or minimal `Generic[T]` fix if something else imports it — to be verified during the build).

### ADR-019 · The live gate becomes a *re-baseline*, not a preservation check
**Context.** Advisory enrichment feeds the DecisionAgent new inputs (an evidence narrative + a classification), so its decisions on some golden-20 cases will likely move.
**Decision.** Treat the golden-20 live gate as a **re-baseline**: expect score movement and verify it is improvement-or-neutral, not regression.
**Why.** Unlike the threshold work (ADR-004, behavior-neutral), this is a deliberate behavioral *enhancement*. Pretending it's behavior-preserving would mis-set the success criterion.
**Consequences.** Surfaced **before** design approval; the plan's verification phase evaluates any golden-20 movement rather than asserting identity.

---

*Last updated: 2026-06-03. Maintained alongside the work it records; append a new ADR when a non-obvious engineering-approach choice is made.*
