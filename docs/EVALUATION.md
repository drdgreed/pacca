# PACCA — Evaluation Methodology

> **Status:** Draft. The current evaluation surface is real and runnable; the consolidated narrative below points to the canonical sources rather than re-stating them. A full evaluation document will land with Phase H5 (Evaluation Harness Expansion).

## What is evaluated today

| Layer | Where it lives | What it checks |
|---|---|---|
| **Unit suite** | [`tests/unit/`](../tests/unit) | 120 tests, all green. Covers escalation tree, models, retry/tracing, audit trail, prompt engineering, security/scalability, config API. Runs in ~7 seconds. |
| **Integration suite** | [`tests/integration/`](../tests/integration) | Cross-component flows including the level-5 maturity flow (`tests/test_level5_flow.py`). |
| **Clinical accuracy / LLM-as-judge** | [`tests/clinical/`](../tests/clinical) | 20-case clinical golden dataset scored 1–5 by Claude Haiku as judge. CI gate at ≥80% accuracy. Hallucinations score automatic 1 — no acceptable rate of inventing clinical data. |
| **Hallucination zero-tolerance** | `GC-018`, `GC-019` in the unit suite | Sparse-notes traps that fail the build on any score-1 hallucination. |
| **Schema validation** | Inline `jsonschema.validate(...)` against [`change_manifest.schema.json`](../harness/manifests/change_manifest.schema.json) | Every change manifest under `harness/manifests/` is validated before merge. A dedicated `pacca.harness.validate_manifest` CLI is a planned H5 deliverable; today the validation runs inline (see "Reproducing today's evaluation" below). |

## What ships in Phase H5

The README's v2.3 cycle commits PACCA to a unified benchmark in Phase H5 (weeks 10-12). When that lands, this document expands to cover:

- **Unified benchmark of 100+ cases** drawn from the existing 53-case demo dataset and the 20-case clinical golden set, plus newly synthesized cases targeting under-tested escalation paths.
- **k=2 rollouts per case** to surface non-determinism that single-run benchmarks hide.
- **Pass@1, tokens-per-case, Succ/Mtok metrics** following the AHE paper's measurement conventions.
- **Per-iteration regression history** so any iteration's benchmark delta is comparable to its predicted-impact contract in the change manifest.

## Reproducing today's evaluation

```bash
# Unit + integration (CI-gated)
pytest tests/unit tests/integration

# Clinical accuracy (uses Claude API; costs ~$0.05 per full run)
pytest tests/clinical

# Manifest validation (inline; a dedicated CLI is an H5 deliverable)
python -c "import json, jsonschema; jsonschema.validate(json.load(open('harness/manifests/iter-1.json')), json.load(open('harness/manifests/change_manifest.schema.json')))"

# Doc-drift guard (catches src/*.py references in docs that don't resolve on disk)
python -m pytest tests/harness/doc_drift_guard.py tests/harness/test_iter2_hardening.py

# Coverage report
pytest tests/unit --cov=pacca --cov-report=term-missing
```

## Reading the iteration record

For any harness iteration `harness-iter-N`:

1. Read [`harness/manifests/iter-N.json`](../harness/manifests/) for the predicted-impact contract.
2. Read [`docs/DECISIONS.md`](DECISIONS.md) for the verdict (predicted vs. observed, ratified/reverted).
3. Read [`docs/ITERATIONS.md`](ITERATIONS.md) for the narrative — failure pattern → change → trajectory before/after → eval delta.
4. Compare the manifest's `evidence` block to the iteration's CI run on GitHub Actions.

## What is NOT evaluated yet

Honesty signal: enumerated explicitly so a reader can trust the rest.

- **Production latency under load** — single-process runtime numbers exist; sustained-load benchmarks await live-demo deployment.
- **Cost-per-decision at scale** — token counts per case are recorded; aggregate $/decision projections are simulated, not measured.
- **Adversarial prompt injection** — basic guardrails are unit-tested; a dedicated red-team suite is on the roadmap (post-H5).
- **HIPAA SaMD-grade clinical validation** — the system is positioned as a portfolio artifact and not certified for real-PHI use; clinical validation by a qualified medical director is a deployment-time obligation per `SECURITY.md`.

## Why a stub instead of the full document

This file was promised by the README in advance of Phase H5. A live link to a self-explaining stub reads better than a broken link, and the harness-engineering discipline applies to documentation: H5 will land as its own iteration with its own manifest entry.
