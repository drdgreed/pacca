# SME Case Authoring Agent — Design Document

> **For:** Engineers, architects, future contributors, and reviewers of `src/pacca/agents/sme_authoring/`.
> **Audience assumption:** Familiar with PACCA's BaseAgent + PROMPT_REGISTRY + Click + pytest patterns.
> **Companion docs:** `SME_CASE_AGENT_USER_MANUAL.md` (clinician-facing), `SME_CASE_AGENT_INSTALL.md` (IT-support-facing), `CASE_AUTHORING_GUIDE.md` (the rules the agent enforces).

---

## 1. Context

PACCA's clinical evaluation dataset hit 100 cases at iter-6 close. The 300-case (general-payer-deployment) and 500-case (HIPAA SaMD-grade) milestones per `DATASET_SUFFICIENCY.md` require authoring ~400 more cases — at the current 60–90 min/case engineer + SME authoring velocity, that's 400–600 hours of mixed engineer + clinician work.

**The bottleneck is the engineer middleware**: every case today requires a developer to translate the SME's clinical knowledge into Python, wire it into the test aggregator, update three companion docs, and run the integrity tests. SMEs (board-certified clinicians) are the scarce resource and they cannot self-serve.

**This tool eliminates the engineer middleware.** An SME runs one CLI command, describes a scenario in plain English, reviews + edits + attests, and the agent does the rest: validate, allocate ID, route to the right file, write the Python, append the provenance row, update the coverage summary, run integrity tests, render the PR.

**Intended outcome:** SME authoring throughput goes from ~3-4 cases/day with engineer support to ~6-10 cases/day SME-only.

---

## 2. Architecture

```
┌─────────────────────────────────────────────────────────────┐
│  CLINICIAN SME at the command line                          │
│  $ pacca sme-author new                                     │
└─────────────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│  src/pacca/cli.py — Click router (entry: pyproject.toml)    │
└─────────────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│  src/pacca/agents/sme_authoring/cli_commands.py             │
│    8 subcommands: new / validate / status / batch /         │
│      list-batches / list-gaps / list-sessions / resume      │
└─────────────────────────────────────────────────────────────┘
                          │
        ┌─────────────────┼──────────────────┐
        ▼                 ▼                  ▼
┌──────────────┐  ┌────────────────┐  ┌─────────────────┐
│  agent.py    │  │  validators.py │  │  id_allocator   │
│  (Claude)    │  │  6 validators  │  │  (file-locked)  │
└──────────────┘  └────────────────┘  └─────────────────┘
        │                 │                  │
        └─────────────────┼──────────────────┘
                          ▼
┌─────────────────────────────────────────────────────────────┐
│  Deterministic writers + readers                            │
│    file_router → case_writer → provenance_writer            │
│    → coverage_updater → test_runner → pr_template           │
└─────────────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│  Session state (~/.pacca/sme_authoring_sessions/)           │
│  Sandbox mode (sandbox/cases/)                              │
│  Git worktree mode (../pacca-sme-<session_id>/)             │
└─────────────────────────────────────────────────────────────┘
```

---

## 3. Module inventory (17 modules + 1 prompt file)

| Module | LOC | Responsibility |
|---|---|---|
| `cli.py` | 35 | Click root CLI; lights up `pacca` console-script entry |
| `agents/sme_authoring/__init__.py` | ~120 | Module exports |
| `agents/sme_authoring/models.py` | 190 | Pydantic data interfaces (CaseDraftRequest/Response, SMEScenario, ValidationReport, SessionState) |
| `agents/sme_authoring/validators.py` | 330 | 6 deterministic validators enforcing CASE_AUTHORING_GUIDE.md rules |
| `agents/sme_authoring/id_allocator.py` | 220 | Concurrent-safe GC-NNN allocator (POSIX lock + reservation file) |
| `agents/sme_authoring/file_router.py` | 290 | 6-step routing decision tree |
| `agents/sme_authoring/case_writer.py` | 340 | AST-validated atomic case-file mutation |
| `agents/sme_authoring/provenance_writer.py` | 120 | CASE_PROVENANCE.md row insertion |
| `agents/sme_authoring/coverage_updater.py` | 160 | EVALUATION_COVERAGE.md summary table bump |
| `agents/prompts/sme_authoring.py` | 170 | v1.0 system prompt (PROMPT_REGISTRY) |
| `agents/sme_authoring/agent.py` | 140 | `SMECaseAuthoringAgent(BaseAgent)` |
| `agents/sme_authoring/session.py` | 140 | Resumable session state persistence |
| `agents/sme_authoring/pr_template.py` | 130 | PR title + body with SME attestation |
| `agents/sme_authoring/test_runner.py` | 140 | Subprocess pytest invocation |
| `agents/sme_authoring/cli_commands.py` | 580 | 8 subcommands (new, validate, status, batch, list-*, resume) |
| `agents/sme_authoring/roadmap_reader.py` | 150 | Parse DATASET_GROWTH_ROADMAP.md batches |
| `agents/sme_authoring/gap_analyzer.py` | 180 | Compute prioritized coverage gaps |
| `agents/sme_authoring/sandbox.py` | 280 | Sandbox + git-worktree isolation |

---

## 4. Key design decisions

### 4.1 — LLM-drafted + SME-edited (vs structured form, vs hybrid)

**Chosen:** LLM-drafted + SME-edited.

**Why not structured form (no LLM):** SMEs are time-constrained. Making them type 3–8 sentences of `clinical_notes` from scratch + draft the `clinical_rationale` + draft the `judge_scoring_criteria` is friction. The LLM saves 30+ minutes per case.

**Why not pure-LLM (no SME edit):** LLMs hallucinate clinical detail. The SME's professional judgment is the safety surface. Edit-after-LLM-draft puts the SME's expertise where it matters most.

**Risk mitigation:** Deterministic validators run AFTER the LLM draft (PHI scan, guideline-body check, schema, outcome-branch consistency, reasoning specificity, judge-criteria specificity). The SME's edits + the validators together defend against LLM error.

### 4.2 — Inherit BaseAgent (vs standalone agent)

**Chosen:** `SMECaseAuthoringAgent(BaseAgent)`.

**Why:** PACCA already has retry (tenacity), OTel tracing, forced-tool-use structured output, and prompt-versioning baked into `BaseAgent`. Inheriting gets all four for free + makes the new agent observable alongside DecisionSupportAgent etc.

**Trade-off:** The base class is for production runtime agents; using it for a dev tool means the dev-tool agent shares the same Anthropic API key + tracing config as production. Not a problem in practice — the dev tool is opt-in and the spans are tagged `agent.smecaseauthoringagent` (lowercased, per BaseAgent's span naming convention).

### 4.3 — Module location: `src/pacca/agents/sme_authoring/` (vs `tools/`)

**Chosen:** `src/pacca/agents/sme_authoring/`.

**Why:** The existing convention is everything under `src/pacca/`. `tools/` doesn't exist in the repo. Creating it would establish a parallel layout that violates KISS.

**Implication:** The SME tool is shipped with the production package. `pip install pacca` puts the `pacca` CLI on PATH regardless of whether the user is a developer or an SME. This is fine — the SME workflow doesn't accidentally trigger production code paths (CLI subcommands are an explicit opt-in).

### 4.4 — Click (vs Typer vs argparse)

**Chosen:** Click 8.1+.

**Why:** Mature, widely-used, good UX. Typer is sugar-coated Click — same underlying machinery, no real win. argparse is too low-level for nested subcommands with rich prompting.

**Trade-off:** Click's decorator-heavy API trips mypy's `disallow_untyped_decorators` strict-mode check. Mitigation: per-module mypy override for `cli.py` + `cli_commands.py` (pyproject.toml). Other modules keep strict enforcement.

### 4.5 — Sandbox + git-worktree dual-mode

**Chosen:** Both, with sandbox as the default for first-time users.

**Why:**
- **Sandbox:** zero git state, lowest friction. Best for "I'm experimenting and don't know what I want yet." Writes go to `sandbox/cases/<session_id>/`.
- **Git worktree:** real git state, PR-ready. Best for "I know I want to merge this; just isolate me from main." Auto-creates `../pacca-sme-<session_id>/` on branch `sme-authoring/<session_id>`.

**v1.0 status:** Sandbox + worktree infrastructure landed in PR-3. Full --commit routing to sandbox (vs real tree) is queued for v1.1.

### 4.6 — Concurrency: file-lock + reservation file

**Chosen:** POSIX advisory file lock (`fcntl.LOCK_EX`) on `.id_allocator.lock` + reservation file `.id_allocator.reservations` in `tests/clinical/`.

**Why:** Two SMEs running `pacca sme-author new` simultaneously cannot collide on `GC-NNN`. The first design (lock-around-scan-only) had a TOCTOU bug — caught by the 10-thread test in `test_id_allocator.py`. The reservation-file pattern moves the in-flight tracking into the lock-protected operation, so concurrent allocations see each other's pending IDs.

**Trade-off:** Reservations need explicit release on write success / failure. The `next_id()` → `append_case_to_file()` → `release_reservation()` sequence is enforced by the CLI but a script that calls `next_id()` and crashes leaves an orphan reservation. Manual cleanup: delete `.id_allocator.reservations`.

### 4.7 — Per-cell coverage matrix update: NOT done at write time

**Chosen:** Update only the summary table (per-file counts + Total live) at write time. Per-cell matrices (Dimensions 1–8) re-baselined on milestone boundaries (100/300/500) per `EVALUATION_COVERAGE.md`'s own schedule.

**Why:** Re-deriving the per-cell matrices for every case write is expensive + error-prone. The doc itself acknowledges this is a milestone-boundary exercise. Doing it at write time would create churn in the markdown without buying signal.

**Implication:** SMEs (and reviewers) see the summary table reflect every case immediately. The per-cell matrices remain accurate at the last milestone re-baseline (currently iter-6, 100 cases).

---

## 5. Integration with PACCA infrastructure

| PACCA component | How the SME tool integrates |
|---|---|
| `src/pacca/agents/base.py::BaseAgent` | `SMECaseAuthoringAgent` inherits; gets retry + tracing + structured output |
| `src/pacca/config/tracing.py::get_tracer` | OTel spans named `agent.smecaseauthoringagent.*` |
| `src/pacca/agents/prompts/templates.py::PROMPT_REGISTRY` | New entry: `SMECaseAuthoringAgent v1.0` |
| `tests/clinical/test_clinical_accuracy.py::TestGoldenDatasetIntegrity` | Agent invokes via subprocess after every write; rolls back on failure |
| `pyproject.toml [project.scripts] pacca` | Wired by `src/pacca/cli.py:main()` |
| `docs/CASE_AUTHORING_GUIDE.md` | The validators are the operational enforcement of every rule in this doc |
| `docs/DATASET_GROWTH_ROADMAP.md` | `roadmap_reader` parses for `batch` subcommand |
| `docs/EVALUATION_COVERAGE.md` | `gap_analyzer` reads summary table for `list-gaps` + `status` |
| `docs/CASE_PROVENANCE.md` | `provenance_writer` appends rows |
| `docs/DATASET_SUFFICIENCY.md` | `status` reports claim-state |
| `docs/STATISTICAL_POWER.md` | `status` reports current per-Δ detection power (future) |

---

## 6. Acceptance criteria (the tool's contract)

A case generated by the tool satisfies ALL of:

1. **Schema completeness** — every GoldenCase field populated.
2. **Case-ID uniqueness** — globally monotonic across all 17 case files; allocator-file-locked.
3. **No PHI** — regex + heuristic scan for SSN, MRN, DOB phrasing, email, phone, street address, specific dates, titled full names.
4. **Guideline citation present** — at least one body from `CASE_AUTHORING_GUIDE.md § 5` (NCCN, ACR, AAD, etc.).
5. **Outcome ↔ branch consistency** — AUTO_APPROVED→branch_1, DENIED→NONE, IN_REVIEW→branch_2/3, PRE_FLIGHT→branches 4-7.
6. **Reasoning specificity** — ≥ 1 specific phrase in `reasoning_must_include`; generic phrases like "approved" trigger WARN.
7. **Judge criteria specificity** — non-generic; known-fallback templates trigger WARN.
8. **SME attestation** — explicit attestation string provided.
9. **Integrity tests pass post-write** — pytest TestGoldenDatasetIntegrity passes; failures roll back.

---

## 7. Testing strategy

### Three layers of regression detection

| Layer | What it catches | Where |
|---|---|---|
| **L1: Internal regression** | Agent code changes that break validators / writers / router | `tests/unit/sme_authoring/` (275 tests) |
| **L2: Per-case integrity** | A bad case write breaks dataset structure | `test_runner.run_integrity_tests()` invoked after every write |
| **L3: Dataset-wide regression** | A new case alters scoring of OTHER cases (H2 memory dynamics) | `tests/clinical/regression_gate.py` (pre-existing PACCA gate) |

### Test patterns

- **Validators:** table-driven parametrized tests, ≥ 4 cases per validator.
- **ID allocator:** 10-thread concurrent test verifies lock + reservation correctness.
- **Case writer:** AST validation of every generated file; idempotency check.
- **CLI:** Click `CliRunner` with stdin / captured output.
- **Agent:** mocked `AsyncAnthropic` returns canned `tool_use` response.

### Live smoke test

`tests/clinical/sme_authoring_smoke_test.py` (marked `@pytest.mark.clinical`):
1. Generate `GC-SENTINEL-<uuid>` via the real Anthropic API.
2. Validate → write to a tmp_path-scoped case dir → run integrity tests.
3. Assert integrity passes.
4. Roll back.

Cost: ~$0.10 per CI run. Runs nightly, not per-PR.

---

## 8. Risk register

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| LLM hallucinates clinical detail or wrong guideline citation | High | High | Deterministic validators run AFTER LLM draft; SME edit prompt for each field reinforces SME review. |
| SME accidentally writes to production without `--sandbox` | Medium | High | Default-to-no-commit (the most conservative path). Production write requires explicit `--commit` flag + attestation. Banner shown at session start. |
| Two SMEs collide on next `GC-NNN` | Low | Medium | File-lock + reservation file. 10-thread concurrent test enforces correctness. |
| Agent crashes mid-session, leaves partial mutation | Medium | High | All file mutations atomic (write tmp + rename). Session state checkpointed at every step. Resume detects + offers to roll back. |
| Pre-commit hook reformats agent-generated code in ways that break it | Medium | Low | Generated code passes `ast.parse`; ruff version is pinned in pre-commit. |
| API key absent | High at first install | Low | `pacca sme-author --help` exit-code 0 even without key. Other commands give a clear "set ANTHROPIC_API_KEY then retry" error. |
| Per-cell coverage matrix re-baseline never gets done | Medium over time | Medium | Cited limitation already documented in `EVALUATION_COVERAGE.md`'s own re-baseline schedule. Scheduled for separate iteration. |
| LLM model drift changes case-drafting style | Medium per Anthropic update | Low | Prompt versioned in `PROMPT_REGISTRY`. K=N rollouts on drafting (future). |
| SME types into the wrong terminal (production vs sandbox) | Medium | High | `pacca sme-author` prints which mode is active in big text at session start. Confirmation prompt before any production write. |
| Roadmap doc lives on parallel PR branch (PR #9), not main | High (transient) | Low | `roadmap_reader.read_batches()` returns empty list when file is missing. CLI surfaces friendly "no batches found" message. Tool fully functional without docs branch merged. |

---

## 9. Out of scope

The following are intentionally NOT in this design:

- **Web UI.** CLI is the deliverable. Web UI is a separate effort.
- **Auto-merge of PRs.** Agent generates the PR description but never merges. Human reviewer always in the loop.
- **Multi-SME real-time collaboration.** Each SME session is independent.
- **Phase 2 clinical-review-board orchestration.** That activates at the 300-case milestone and is a separate workflow.
- **FDA submission packaging.** Activates at the 500-case milestone per `DATASET_GROWTH_ROADMAP.md` § 4.4.
- **Multi-language support.** English only for v1.0.
- **PHI re-identification testing.** The PHI scan is intentionally conservative (catch + warn) rather than ML-based re-identification.

---

## 10. Future work

| Feature | When |
|---|---|
| Full sandbox-mode write routing (`--commit` to `sandbox/cases/`) | v1.1 |
| Interactive resume (continue drafting from last step) | v1.1 |
| `--draft-all` for batch mode (iterate slots automatically) | v1.1 |
| `pacca sme-author promote <session_id>` to lift sandbox → real tree | v1.2 |
| K=N rollouts on drafting (median of N drafts) | v1.2 |
| Field-by-field edit UI (skip the JSON preview, edit each field inline) | v2.0 |
| Web UI (separate effort) | TBD |
| FDA SaMD packaging workflow | At 500-case milestone |

---

*Last updated: 2026-05-25 (iter-7 close — SMECaseAuthoringAgent v1.0).*
