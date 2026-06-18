# CLAUDE.md — PACCA Agent Context

Project memory for any coding agent (Claude Code or otherwise) working in this repo.
Read this before making changes. It is the machine-facing counterpart to `CONTRIBUTING.md`.

## What PACCA is

PACCA (Prior Authorization & Care Coordination Agent Platform) is a multi-agent AI
system that automates healthcare prior-authorization decisions. It is RAG-grounded,
harness-engineered, and observability-first. Healthcare domain: PHI handling and audit
integrity are non-negotiable, not nice-to-haves.

Stack: Python 3.12 + FastAPI (async), Pydantic v2, PostgreSQL 16 / SQLite (dev),
ChromaDB dual-collection, React 18 + Vite frontend, OpenTelemetry → Langfuse,
Claude (`claude-sonnet-4`) with tool-use forced for structured output.

## The one rule that governs every behavioral change

**Every change that alters agent behavior ships as a one-file diff with a recorded,
falsifiable prediction.** Behavioral = how an agent reasons, what tools it can call,
what middleware fires, or what memory context it sees. This discipline is the point of
the project; do not bypass it to "save time."

Before a behavioral change:
1. Read `docs/HARNESS.md` and identify the correct constraint level (one of 11 editable
   harness surfaces: 7 NexAU-standard + 4 PACCA-specific).
2. Make the change as a one-file diff. If multiple components are touched, use multiple
   commits — one file per commit.
3. Use the `chg-N:` commit prefix for behavioral changes (conventional commits otherwise:
   `feat:`, `fix:`, `docs:`, `refactor:`, `test:`).
4. Add a matching entry to `harness/manifests/iter-N.json` per
   `harness/manifests/change_manifest.schema.json`. Include `phi_impact` and
   `audit_relevant` fields — they are required for healthcare governance.
5. CI validates the manifest schema and runs the benchmark. After merge, the next
   evaluation round writes a verdict to `docs/DECISIONS.md`.

Non-behavioral changes (refactors, docs, test additions that don't change behavior)
follow the standard PR flow and skip the manifest. The PR template forces the choice —
every PR is one path or the other, never ambiguous.

## Where things live (don't reorganize without reason)

- `src/pacca/agents/<agent>/` — each agent decoupled: `system_prompt.md`,
  `long_term_memory.md`, `tool_descriptions/`, `tools/`, `middleware/`, `agent.yaml`.
  Five agents: decision_support, medical_director, evidence_aggregation,
  classification, policy_evolution.
- `src/pacca/agents/prompts/` — shared `PROMPT_REGISTRY`. Prompts are versioned; the
  active versions are surfaced in API responses (`prompt_registry_versions`). Never
  hardcode a prompt at a call site — register it.
- `src/pacca/orchestrator/` — the 7-branch escalation tree (4 pre-flight deterministic
  checks + 3 post-agent). This logic OVERRIDES model confidence. Treat it as a safety
  boundary, not a suggestion.
- `src/pacca/rag/` — ChromaDB dual-collection: `nccn_guidelines` (authoritative) and
  `case_precedents` (institutional memory). Different trust levels — keep them separate.
- `src/pacca/observability/` — trajectory logging; OpenTelemetry spans → Langfuse,
  one span per agent call. Per-trace and per-span cost/token attribution flows here.
- `src/pacca/api/`, `src/pacca/db/`, `src/pacca/models/`, `src/pacca/config/` — standard.
- `harness/manifests/` — change manifests + verdicts. The decision record of iteration.
- `docs/` — `ARCHITECTURE.md`, `HARNESS.md`, `DECISIONS.md`, `ITERATIONS.md`,
  `EVALUATION.md`, consolidated PRD.

## Safety invariants — never weaken these

- **Anti-hallucination guards on every agent.** Agents may only reference clinical
  evidence explicitly present in the submission. Tests GC-018 and GC-019 fail the build
  on any score-1 hallucination. There is no acceptable hallucination rate.
- **Tool-use forced** for structured output. Don't switch an agent to free-text parsing.
- **Pre-write audit trail.** Correlation-ID-linked event pairs are flushed BEFORE any
  state change. Don't reorder writes ahead of the audit flush.
- **Fail-fast secrets.** Server refuses to start with a weak/missing `SECRET_KEY`.
- **Append-only `PolicyChangeLogEntry`.** Never mutate or delete change-log rows.

## Testing

- Full unit suite: `pytest` (140 tests, ~8s, 0 failures expected before any commit).
- Eval/benchmark: `pytest tests/eval/` (100+ cases, k=2 rollouts; Phase H5).
- Coverage: `pytest --cov=pacca --cov-report=html`.
- Manifest check before committing a behavioral change:
  `python -m pacca.harness.validate_manifest harness/manifests/iter-N.json`
- A behavioral change is not done until: unit suite green, manifest validates,
  benchmark run, prediction recorded.

## Canonical repo

`github.com/drdgreed/pacca` is canonical. If you find `Chaos-6/pacca` anywhere
(old clone URLs, citation), it is stale — update it to `drdgreed`.

## House style

- Async throughout the backend. Don't introduce blocking calls in request paths.
- Pydantic v2 models for all request/response and domain objects.
- Keep retrieval (rag), reasoning (agents), and safety (orchestrator) separable —
  a change to one should not force edits to the others.
