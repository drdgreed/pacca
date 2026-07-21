# CLAUDE.md — PACCA Agent Context

Project memory for any coding agent (Claude Code or otherwise) working in this repo.
Read this before making changes. It is the machine-facing counterpart to `CONTRIBUTING.md`.

> **Docs describe reality, not aspiration.** This file was reconciled against the
> working tree (2026-07-21). Where the intended design is not yet built, it is called
> out in **Limitations** or **Target architecture (roadmap)** below rather than stated
> as fact. If you find a claim here that the code contradicts, the code wins — fix the
> doc in the same PR. A doc-drift guard (`tests/harness/doc_drift_guard.py`) exists to
> catch this class of drift; wiring it into CI and widening its scope to this file is
> harness change P-1.

## What PACCA is

PACCA (Prior Authorization & Care Coordination Agent Platform) is a multi-agent AI
system that automates healthcare prior-authorization decisions. It is RAG-grounded,
harness-engineered, and observability-first. Healthcare domain: PHI handling and audit
integrity are non-negotiable, not nice-to-haves.

Stack: Python 3.12 + FastAPI (async), Pydantic v2, PostgreSQL 16 / SQLite (dev),
ChromaDB (**single** collection today — see Limitations), React 18 + Vite frontend,
OpenTelemetry spans (Langfuse export intended), Claude (`claude-sonnet-4`) with
tool-use forced for structured output.

## The one rule that governs every behavioral change

**Every change that alters agent behavior ships as a one-file diff with a recorded,
falsifiable prediction.** Behavioral = how an agent reasons, what tools it can call,
what middleware fires, or what memory context it sees. This discipline is the point of
the project; do not bypass it to "save time."

Before a behavioral change:
1. Read `docs/HARNESS.md` and identify the correct constraint level (one of the
   currently-built harness surfaces — see the PR template enum for the canonical list).
2. Make the change as a one-file diff. If multiple components are touched, use multiple
   commits — one file per commit.
3. Use the `chg-N:` commit prefix for behavioral changes (conventional commits otherwise:
   `feat:`, `fix:`, `docs:`, `refactor:`, `test:`).
4. Add a matching entry to `harness/manifests/iter-N.json` per
   `harness/manifests/change_manifest.schema.json`. Include `phi_impact` and
   `audit_relevant` fields — they are required for healthcare governance.
5. Record a verdict in `docs/DECISIONS.md` at the next evaluation round.

> **Enforcement status (interim).** The manifest discipline is currently enforced by
> **convention and review** (the PR template forces the Standard-vs-Behavioral choice),
> validated **locally**. Automated CI enforcement — a `validate-manifests` job and a
> `clinical-gate` job — is a planned change (harness change P-6), not yet wired. Until
> then, "CI validates the manifest and runs the benchmark" is **not** true; do not rely
> on CI to catch a missing manifest or a clinical regression.

Non-behavioral changes (refactors, docs, test additions that don't change behavior)
follow the standard PR flow and skip the manifest. The PR template forces the choice —
every PR is one path or the other, never ambiguous.

## Where things live (don't reorganize without reason)

- `src/pacca/agents/` — the agents. **As built**, two agents have their own directory:
  `decision_support/` (`system_prompt.md` + `long_term_memory.md`) and `medical_director/`
  (`system_prompt.md`). The other three are flat modules: `evidence_agent.py`,
  `classification_agent.py`, and `evolution.py`. Wiring is by direct
  Python import, not an `agent.yaml` loader. The per-agent seven-component layout
  (`tool_descriptions/`, `tools/`, `middleware/`, `agent.yaml`) is **roadmap** — see below.
- `src/pacca/agents/prompts/templates.py` — shared `PROMPT_REGISTRY`. Prompts are
  versioned (`v{MAJOR}.{MINOR}`, surfaced to audit logs and OTel spans). Register a
  prompt; don't hardcode one at a call site.
- `src/pacca/agents/orchestrator.py` (class `Orchestrator`) — the 7-branch escalation
  tree (4 pre-flight deterministic checks + 3 post-agent). This logic OVERRIDES model
  confidence. Treat it as a safety boundary, not a suggestion.
- `src/pacca/rag/pipeline.py` — `GuidelineVectorStore`, a **single**-collection ChromaDB
  store (default `clinical_guidelines`). Dual-collection (`nccn_guidelines` +
  `case_precedents`) is roadmap. **Note:** `rag/pipeline.py` currently does not import
  cleanly (a chain of stale references in `models/guidelines.py`); the RAG pipeline is
  effectively dead code pending a revival pass (see Limitations).
- Span emission lives in `src/pacca/agents/base.py` + `src/pacca/config/tracing.py`
  (one span per agent call). There is **no** `src/pacca/observability/` package.
- `src/pacca/api/`, `src/pacca/db/`, `src/pacca/models/`, `src/pacca/config/` — standard.
- `.githooks/pacca_guard.py` — the **PHI/secret pre-commit guard** (wired via
  `.pre-commit-config.yaml`, reusing `sme_authoring/validators.py` as SSOT, tested in
  `tests/unit/test_pacca_guard_hook.py`). This is PACCA's strongest existing example of a
  deterministic commit-time gate — the pattern to imitate when adding enforcement.
- `harness/manifests/` — change manifests + verdicts. The decision record of iteration.
- `docs/` — `ARCHITECTURE.md`, `HARNESS.md`, `DECISIONS.md`, `ITERATIONS.md`,
  `EVALUATION.md`, consolidated PRD.

## Safety invariants — never weaken these

- **Anti-hallucination guards.** Agents may only reference clinical evidence explicitly
  present in the submission. Golden cases **GC-018** and **GC-019** (in
  `tests/clinical/golden_cases.py`) assert zero score-1 hallucination. **Caveat:** the
  clinical suite is not in CI yet (see Limitations), so today these fail a *local
  clinical run* (`make test-clinical`), not the build. Making them build-blocking is P-6.
- **Tool-use forced** for structured output. Don't switch an agent to free-text parsing.
- **Pre-write audit trail.** Correlation-ID-linked event pairs (`AuditLogModel` carries
  `correlation_id`) are flushed BEFORE any state change; `tests/unit/test_audit_trail.py`
  guards the ordering. Don't reorder writes ahead of the audit flush.
- **Append-only policy change log.** The intent is that policy changes are never mutated
  or deleted. **As built** this is a prototype: `PolicyChangeLogEntry` (in
  `agents/evolution.py`) is an in-memory dataclass list, not a DB table
  (see Limitations). Preserve the append-only *contract* in code; the durable-persistence
  piece is roadmap.

## Testing

Use the Makefile targets (they encode the correct markers):

- **Deterministic suite (routine):** `make test` — runs `pytest tests/unit/` plus the
  non-clinical part of the clinical accuracy test, with `-m "not clinical"`. Fast (~25s).
  Run before every commit; expect 0 failures. (Sizes drift — `pytest --collect-only -q`
  reports the current count rather than a number baked into this doc.)
- **Everything non-clinical:** `make test-all` (`pytest tests/ -m "not clinical"`).
- **Coverage:** `make test-cov`.
- **Clinical / LLM-as-judge gate:** `make test-clinical` (`pytest tests/clinical/ -m clinical`).
  Makes real Claude calls (~3–5 min); requires `ANTHROPIC_API_KEY` in the shell env —
  source it from the gitignored `.env`, never hardcode or print it. This is the golden-set
  accuracy gate (incl. GC-018/019); run it at the final merge HEAD for any behavior change.

> **Do not infer clinical accuracy from `make test`.** The deterministic suite deselects
> the live LLM tests — they cover different things (see `docs/AGENT_LESSONS.md` P-008).
>
> A manifest-validation CLI (`python -m pacca.harness.validate_manifest …`) is referenced
> by the harness workflow but **not yet implemented** — it lands as harness change P-2.
> Until then there is no manifest-lint command; validate against the schema by inspection.

## Limitations (what the design intends but the code does not yet do)

- **No middleware layer** and **no `agent.yaml` loader** — agents are wired by direct
  Python import. The seven-component per-agent harness layout is roadmap.
- **Single RAG collection.** The dual-collection design (`nccn_guidelines` /
  `case_precedents`) is not built; the existing `rag/pipeline.py` does not import cleanly
  and is effectively dead code (stale `uuid7` / missing-enum references in
  `models/guidelines.py`). Reviving or removing it is a tracked follow-up.
- **Clinical suite not in CI.** `ci.yml` runs ruff, mypy, `pytest tests/unit`, coverage,
  Docker build, bandit/safety — **no** manifest validation, benchmark, or doc-drift step.
  Those are harness change P-6.
- **No SECRET_KEY fail-fast.** `config/settings.py` ships a weak default `secret_key`
  (and a placeholder `anthropic_api_key`) with **no** startup validator rejecting weak or
  missing values. The server will start with insecure defaults. Add a fail-fast validator
  before relying on the earlier "refuses to start" behavior.
- **Policy change log is in-memory.** See the safety-invariants note above.

## Target architecture (roadmap)

These are the intended end-states, moved here so they are not mistaken for current fact:

- **Seven-component per-agent layout** (NexAU-style): each agent as
  `system_prompt.md` + `long_term_memory.md` + `tool_descriptions/*.tool.yaml` +
  `tools/*.py` + `middleware/*.py` + `skills/<name>/SKILL.md` +
  `sub_agents/<name>/agent.yaml`, declared in a per-agent `agent.yaml` loaded by a
  framework. Rationale: file-level component decoupling + one-file-diff rollback.
- **Dual-collection RAG:** separate `nccn_guidelines` (authoritative) and
  `case_precedents` (institutional memory) stores, kept apart for their different trust
  levels.
- **CI enforcement (P-6):** `validate-manifests` + `clinical-gate` jobs that make the
  manifest and GC-018/019 gates build-blocking.

## Canonical repo

`github.com/drdgreed/pacca` is canonical. If you find `Chaos-6/pacca` anywhere
(old clone URLs, citation), it is stale — update it to `drdgreed`.

## House style

- Async throughout the backend. Don't introduce blocking calls in request paths.
- Pydantic v2 models for all request/response and domain objects.
- Keep retrieval (rag), reasoning (agents), and safety (orchestrator) separable —
  a change to one should not force edits to the others.
- Logging: `from pacca.config import get_logger` (structlog-backed) — never
  `logging.getLogger` (see `docs/AGENT_LESSONS.md` P-002).
