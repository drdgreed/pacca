# iter-0 Erratum — Trajectory Instrumentation Reconciliation

> **Purpose:** correct a spec-vs-implementation drift discovered during iter-2.
> Paste the block below into the iter-0 sections of `docs/ITERATIONS.md` and
> `docs/DECISIONS.md` (and adjust the file-reference line in `docs/EVALUATION.md`).
> Per PACCA's append-only convention in DECISIONS.md, this is recorded as a
> correction, not by editing history.

---

## What was found

The iter-0 records describe a deliverable at
`src/pacca/observability/trajectory.py` that "emits a structured JSON record
capturing input, tool calls, output, confidence, and escalation decision" per
agent step. That file and the `src/pacca/observability/` directory **do not
exist** in the repository.

What actually shipped is **OpenTelemetry span instrumentation in
`src/pacca/agents/base.py`**. Every agent LLM call opens a span and records
`llm.input_tokens`, `llm.output_tokens`, `llm.total_tokens`, and `duration_ms`
as span attributes, exported via the tracer configured in
`src/pacca/config/tracing.py`.

Two consequences for the cycle:

1. **Per-case token counts are captured**, but as span attributes in a tracing
   backend — not as the standalone per-case JSON trajectory records the docs
   describe. Reading them back for an evaluation delta requires either an
   in-memory span exporter wired into the eval harness, or reading
   `response.usage` directly in a measurement script.

2. **There is no "reasoning steps" counter.** The Decision agent
   (`DecisionAgent.run` in `src/pacca/agents/decision.py`) makes a single
   forced-tool-use call. The "evaluation framework steps" are reasoning *within*
   one rationale, not separate agent invocations. Any future verbosity claim
   must therefore be expressed as **output tokens per case** and/or
   **rationale length** — never as a count of "steps."

## Correction block to insert

> **Erratum (recorded iter-2):** The iter-0 instrumentation deliverable shipped
> as OpenTelemetry spans in `src/pacca/agents/base.py`
> (`llm.input_tokens`, `llm.output_tokens`, `llm.total_tokens`, `duration_ms`
> per call), not as a standalone `src/pacca/observability/trajectory.py`. A
> dedicated per-case trajectory-record module remains deferred. Verbosity
> metrics for later iterations are defined as output-tokens-per-case and
> rationale length, since the Decision agent issues a single forced-tool-use
> call and has no countable multi-step loop.

## Definition of done for this reconciliation

- [ ] Correction block inserted into the iter-0 section of `docs/ITERATIONS.md`.
- [ ] Correction block inserted into the iter-0 section of `docs/DECISIONS.md`.
- [ ] `docs/EVALUATION.md` "trajectory.py" reference updated to point at
      `base.py` span instrumentation (or marked deferred).
- [ ] The `find_dangling_references` doc-drift guard passes against `docs/`
      (no `src/*.py` reference resolves to a missing file).
