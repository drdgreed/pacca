<!--
  PASTE-READY ERRATUM ENTRIES — iter-0 trajectory instrumentation reconciliation
  Produced for iter-2 (harness-iter-2), 2026-05-22.

  BLOCK 1 -> paste into docs/DECISIONS.md, immediately under the "## Index" /
            top of the log (newest-first), as a superseding correction entry
            per the file's stated protocol ("corrections are made by adding a
            new entry that supersedes the prior one and citing the supersession").
  BLOCK 2 -> paste into docs/ITERATIONS.md, at the top of the
            "## iter-0 — Baseline Crystallization" section, as a dated callout.

  Also add this index line to DECISIONS.md's "## Index" list (at the top):
    - [Correction (2026-05-22) — iter-0 trajectory instrumentation record](#correction-iter0-trajectory)
-->


<!-- ============================================================ -->
<!-- BLOCK 1 — for docs/DECISIONS.md                              -->
<!-- ============================================================ -->

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


<!-- ============================================================ -->
<!-- BLOCK 2 — for docs/ITERATIONS.md (top of the iter-0 section) -->
<!-- ============================================================ -->

> **Correction (2026-05-22, recorded in iter-2).** The instrumentation described
> below as `src/pacca/observability/trajectory.py` does not exist as written.
> What shipped is OpenTelemetry span emission in `src/pacca/agents/base.py`
> (`llm.input_tokens`, `llm.output_tokens`, `llm.total_tokens`, `duration_ms`
> per call, via `src/pacca/config/tracing.py`). There is no per-step JSON
> trajectory record and no reasoning-step counter — the Decision agent makes a
> single forced-tool-use call, so verbosity is measured as output-tokens-per-case
> and rationale length, not as "steps." The "4–6 reasoning steps" observation in
> the Baseline trajectory pattern below should be read as reasoning *within one
> rationale*, not as separate agent invocations. See the superseding entry in
> [`DECISIONS.md`](./DECISIONS.md#correction-iter0-trajectory) and the drift guard
> at `tests/harness/doc_drift_guard.py`.
