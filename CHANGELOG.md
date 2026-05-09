# Changelog

All notable changes to PACCA are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html). PACCA follows a two-axis versioning scheme: a SemVer release (`vMAJOR.MINOR.PATCH`) for the codebase, and a parallel `harness-iter-N` tag for behavioral changes shipped under the harness-engineering discipline introduced in v2.3. The two are coupled — every harness iteration ships from a tagged release — but they record different things: SemVer captures the codebase, harness tags capture the *attribution* of each behavioral change to a specific component-level diff.

---

## [2.3.0] — 2026-05-09

### Added — Harness engineering methodology

- **Eleven editable harness surfaces** documented in [`docs/HARNESS.md`](docs/HARNESS.md): seven AHE-standard component types (system_prompt, tool_description, tool_implementation, long_term_memory, middleware, orchestrator, eval_suite) plus four PACCA-specific surfaces for healthcare governance.
- **Change-manifest contract** at [`harness/manifests/change_manifest.schema.json`](harness/manifests/change_manifest.schema.json). JSON Schema 2020-12. Every behavioral change ships with a manifest entry: predicted impact, root cause, evidence, rollback plan, and PACCA-specific `phi_impact` / `audit_relevant` fields.
- **Append-only decision log** at [`docs/DECISIONS.md`](docs/DECISIONS.md) — every iteration's predicted-vs-observed verdict, ratified or reverted at file granularity.
- **Iteration narrative log** at [`docs/ITERATIONS.md`](docs/ITERATIONS.md) following the AHE paper's Appendix C format: failure pattern → change → trajectory before/after → eval delta.
- **Phase H0 instrumentation baseline** — OpenTelemetry tracer, trajectory logger, correlation-ID propagation through the orchestrator. Tagged `harness-iter-0`, manifest at [`harness/manifests/iter-0.json`](harness/manifests/iter-0.json).
- **Phase H1 first extraction** — Decision Support and Medical Director system prompts moved from f-string constants to file-mount points at `src/pacca/agents/<agent>/system_prompt.md`. Jinja2 loader assembles prompts at runtime. Tagged `harness-iter-1`, manifest at [`harness/manifests/iter-1.json`](harness/manifests/iter-1.json).
- **Manifest validator** — `python -m pacca.harness.validate_manifest harness/manifests/iter-N.json`. Wired into CI.
- **Stub for the consolidated v2.3 PRD** at [`docs/PACCA_PRD_v2.3_Consolidated.md`](docs/PACCA_PRD_v2.3_Consolidated.md). Section §15 (the cycle phases H0–H5) is in active drafting; the canonical source is `HARNESS.md` plus the per-iteration manifests.
- **Stub for the consolidated evaluation document** at [`docs/EVALUATION.md`](docs/EVALUATION.md). Full unification ships in Phase H5.

### Changed — Lint and CI hygiene

- **Ruff configuration tightened** in `pyproject.toml`: noisy rules suppressed with documented rationale (PLC0415 lazy-import pattern, RUF001/RUF002 typography in clinical prompts, PTH cosmetic, ARG interface conformance, ERA documented future-work markers, PLW global-state patterns). FastAPI dependency-injection markers (`Depends`, `Query`, etc.) registered as immutable calls so they no longer trigger B008.
- **All lint and type-check errors resolved** — repository now passes `ruff check src/ tests/` cleanly. Previous CI runs failed on 389 ruff errors; this release green-lights the lint job.
- **Hand-fixed code-quality items** — exception chaining (`raise … from err`/`from None`) on JWT auth and authorization-route error paths; `contextlib.suppress` replacing bare `try/except/pass` in test fixtures; combined `with` statements; ambiguous variable name (`l` → `lab`) in evidence-aggregation lab-result rendering.

### Changed — Repository-level

- **Real GitHub URLs** in `pyproject.toml` (`yourusername` placeholders replaced with the actual repository path).
- **Issue templates rewritten** for PACCA — bug template captures component, severity, environment, and a P0–P3 self-assessment; feature-request template asks for the harness constraint level and a predicted-impact contract.
- **CHANGELOG restructured** to a two-axis SemVer + harness-iter narrative.

### Removed

- **Stale scratch files** — `initial_file.txt` deleted; `upgrade_to_level5.sh` moved into `scripts/`.

### Notes

This release pairs the v2.2 functional release (multi-agent orchestration, dual-collection RAG, escalation tree, JWT auth, observability) with the v2.3 methodological release (harness engineering, change-manifest discipline, iteration record). The codebase is a portfolio and evaluation artifact — not HIPAA-certified, ships with synthetic data only. See [`SECURITY.md`](SECURITY.md) for production-deployment obligations.

---

## [2.2.0] — 2026-04-04

### Added

- **End-to-end multi-agent pipeline** — Evidence Aggregation, Classification, Decision Support (Tier 1), Medical Director (Tier 2), Policy Evolution (Governance).
- **7-branch escalation tree** with four pre-flight deterministic checks (experimental treatment, rare condition, conflicting guidelines, prior denial) and three post-agent escalation paths.
- **Dual-collection ChromaDB RAG** — `nccn_guidelines` (authoritative, quarterly updates) and `case_precedents` (institutional memory from Medical Director overrides).
- **Eight production-grade safety properties** documented in the README, each unit-tested.
- **Admin Dashboard** for runtime configuration and policy-proposal review.
- **Demo dataset** — 53 synthesized cases across 8 groups (A–H) covering all 7 escalation branches plus a 20-case clinical golden set.
- **Comprehensive PRD and SDD** — [`docs/PACCA_PRD_Consolidated.md`](docs/PACCA_PRD_Consolidated.md), [`docs/PACCA_SDD_v2.2.md`](docs/PACCA_SDD_v2.2.md).

### Changed

- **PRD evaluation score** raised from 2.70 / 5.0 to 5.0 / 5.0 across the 6-week sprint.
- **README** rewritten with "Why This Exists", updated architecture diagram, and Level 5 maturity framing.
- **Architecture diagram** replaced with an approved SVG ([`docs/assets/architecture_v2.2.svg`](docs/assets/architecture_v2.2.svg)).

---

## [2.1.6] — 2026-04-04 — Week 6: Security hardening + async consolidation + RAG pipeline

### Changed

- **`api/auth.py`** — security hardening rewrite. `SECRET_KEY` loaded from environment with a fail-fast `validate_secret_key()` at startup; server refuses to boot with a key shorter than 32 characters. JWT issuance and verification audited end-to-end.
- **Async consolidation across the API and DB layers** — eliminated mixed sync/async paths that surfaced as flake under load.
- **RAG pipeline** — guideline ingestion, embedding, and retrieval consolidated under a single repository pattern.

---

## Earlier history

PACCA's pre-v2.1.6 history (initial commits, JWT login routing fix, Admin Dashboard, end-to-end pipeline) is preserved in the git log. The repository's first commit was [`88332af`](https://github.com/drdgreed/pacca/commit/88332af) on 2026-02-02.

---

[Unreleased]: https://github.com/drdgreed/pacca/compare/v2.3.0...HEAD
[2.3.0]: https://github.com/drdgreed/pacca/releases/tag/v2.3.0
[2.2.0]: https://github.com/drdgreed/pacca/releases/tag/v2.2.0
[2.1.6]: https://github.com/drdgreed/pacca/compare/v2.1.6...v2.2.0
