# PACCA Harness Engineering — Iteration Narratives

> **What this is:** the narrative log of PACCA's harness engineering cycle. Each iteration tag (`harness-iter-N`) gets a section structured in the format of Lin et al., *Agentic Harness Engineering* (arXiv:2604.25850, 2026), Appendix C: failure pattern → change shipped → trajectory before/after on a representative case → eval delta.
>
> **What this is for:** the engineering narrative that complements the audit log in [`DECISIONS.md`](./DECISIONS.md). DECISIONS.md is the structured record (manifest + verdict). This file is the story — what the failure looked like in the trajectory log, why we believed the chosen constraint level was right, what the passing case looked like after the fix, and what the eval delta confirmed or rejected. A reader who wants the data goes to DECISIONS.md; a reader who wants the reasoning comes here.
>
> **Reading this document:** entries are reverse-chronological after the seed (newest at top). Each iteration's narrative cites the corresponding manifest entries in DECISIONS.md and the relevant trajectory log paths. Entries are written shortly after the iteration's evaluation round completes — early enough that the engineering reasoning is fresh, late enough that the verdict is known.
>
> **Format authority:** narrative format adapted from Lin et al. (2026), Appendix C. See [`docs/HARNESS.md`](./HARNESS.md) for the methodology and [`harness/manifests/change_manifest.schema.json`](../harness/manifests/change_manifest.schema.json) for the manifest schema this narrative references.

---

## Index

- [iter-0 — Baseline Crystallization (seed narrative)](#iter-0-baseline-crystallization)

---

<a name="iter-0-baseline-crystallization"></a>
## iter-0 — Baseline Crystallization

**Tag:** `harness-iter-0`
**Companion tag:** `pre-ahe-baseline`
**Phase:** H0 (Baseline Crystallization)
**Date:** *(populated when shipped)*
**Eval delta:** n/a — iter-0 has no predictions to verify

### What this iteration shipped

iter-0 is the cycle's anchor. It ships no behavioral change; what it ships is the measurement infrastructure that every subsequent iteration is measured against. Specifically:

- **Trajectory instrumentation** at `src/pacca/observability/trajectory.py`. Every agent step now emits a structured JSON record capturing input, tool calls, output, confidence, and escalation decision. These records are the substrate that Phase H4's manifest verdicts and Phase H5's benchmark expansion will both consume.

- **Change manifest schema** at `harness/manifests/change_manifest.schema.json`. JSON Schema 2020-12 specification with eleven valid `constraint_level` values, healthcare-specific fields (`phi_impact`, `audit_relevant`), and a verdict sub-schema for next-iteration validation.

- **Four documentation files**: `HARNESS.md` (architectural reference), `DECISIONS.md` (this file's audit-log companion), `ITERATIONS.md` (this file), and an updated `README.md` positioning v2.3 as a methodology adoption rather than a feature drop.

The two paired tags — `harness-iter-0` and `pre-ahe-baseline` — point at the same commit. The duplication is deliberate: `harness-iter-0` is the engineering record (the iteration counter), and `pre-ahe-baseline` is the operational record (the rollback target). Different audiences look for different names, and both should find the right tag without effort.

### Why the seed is intentionally minimal

The AHE paper (Lin et al. §3.1) frames this same choice clearly: "A seed already fitted to the target benchmark would contaminate every subsequent edit's attribution, since we could not tell whether a gain came from the loop or from the seed."

PACCA's v2.2.0 is not a "minimal" harness in absolute terms — it has 5 agents, a 7-branch escalation tree, dual-collection RAG, and 140 unit tests. But for the purposes of the v2.3 cycle, v2.2.0 is the seed. The cycle does not retroactively re-attribute any v2.2.0 capability to the cycle's work. iter-0's job is to draw the line between "what existed before" and "what the cycle produced."

Operationally, this matters because the cycle's claims depend on it. When iter-3 claims that institutional memory contributed +X pp to pass@1, that claim is only credible because there is a `harness-iter-0` reference state without the institutional memory layer. The seed makes the attribution falsifiable.

### Baseline trajectory pattern

Even without a behavioral change, iter-0 captures a baseline trajectory that frames the cycle's starting point. Three observations from running the 53-case demo dataset against the v2.2.0 system, recorded immediately after tagging:

**Decision Support Agent's reasoning is mostly clean but verbose.** On Group A (auto-approve) cases, the agent typically takes 4–6 reasoning steps before finalizing a decision, even when the case clearly aligns with cited NCCN guidelines. The verbosity itself is not a failure pattern — confidence remains ≥0.95 — but it suggests an opportunity for Phase H2's institutional memory layer to encode "for clear PD-L1 ≥50% NSCLC cases with documented disease stage and PD-L1 testing date, summarize alignment to NCCN-NSCLC-PEMBRO-1L in 2 steps not 5."

**The Frontline → Medical Director handoff is occasionally lossy.** On two Group C cases (cost > $100K cases), the trajectory log shows Frontline emitting a clean rationale that Medical Director then partially restates rather than building on. Both cases pass the eval, but the redundancy is a hint that Phase H1's tool-description extraction may need to expose a structured handoff payload rather than relying on free-text rationale.

**The 7-branch escalation tree's pre-flight checks fire correctly but silently.** Group D (experimental treatment) cases are correctly routed to human review without LLM invocation, which is the design. But the trajectory log entries for these cases are sparse — they record "Branch 4 fired, routed to human" without capturing *why* the experimental treatment classifier matched. Phase H0's instrumentation enrichment plan includes adding a `pre_flight_evidence` field to these trajectory entries so a reviewer can audit the classifier's reasoning, not just its conclusion.

None of these observations are failure patterns in the manifest sense — they are not associated with failed cases. They are signals that Phase H1, H2, and H3 should pay attention to specific structural opportunities even before the full benchmark expansion in H5 makes them quantitatively actionable.

### Baseline numbers

The full numerical baseline is in [`docs/DECISIONS.md`](./DECISIONS.md#iter-0-baseline-crystallization) (iter-0 entry). The headline numbers, recorded for narrative continuity:

- **Unit tests:** 140 passing, 0 failing, ~8 seconds
- **Demo dataset:** 53 cases across 8 groups (A–H), all 7 escalation branches exercised
- **Clinical golden dataset:** 20 cases with LLM-as-judge scoring, ≥80% accuracy gate passing
- **Hallucination zero-tolerance gate:** passing on GC-018, GC-019
- **Pass@1 on unified benchmark:** to be populated after Phase H5 unifies the case sources

The "to be populated" entry is honest reporting. Phase H5 is the phase where pass@1 becomes the headline metric; until then, the cycle reports unit tests and per-source pass rates separately.

### What success looks like for iter-1

iter-1 is the first iteration that ships behavioral changes (extracted system prompts, tool descriptions, tool implementations under Phase H1). The success criterion for iter-1 is narrow and specific: full-suite reproduction of iter-0's baseline numbers with zero regression. Phase H1 is a refactor; if it produces any behavioral change, that change is a bug, not a feature.

The trickiest part of iter-1 will be the Jinja2 prompt rendering: the existing Python string prompts use f-string interpolation in places that don't translate cleanly to Jinja2 placeholders. The trajectory comparison check at iter-1's evaluation will catch any rendering discrepancy that produces a different prompt token sequence than the v2.2.0 baseline — even if the LLM happens to produce the same output.

This is why iter-1 is a conservative iteration. Phase H1 enables Phases H2 and H3 by making one-file diffs possible. The behavioral wins begin at iter-2.

### Reflection on cycle methodology

One observation worth recording at the cycle's start, as a calibration anchor for future iterations:

The AHE paper's empirical regression-blindness finding (Lin et al. §4.4.2) — that self-prediction of regressions sits at ~2x random precision while self-prediction of fixes sits at ~5x random — is the single most important calibration to internalize. Every prediction this cycle commits to in `risk_cases` should be treated as a low-confidence claim. The eval suite is the safety net. The honest verdict, including the misses, is what makes the methodology defensible.

The corollary: if the eval suite isn't catching regressions the manifest fails to predict, the eval suite is the bottleneck, not the methodology. Phase H5 exists specifically to address this. iter-0 ships with the existing eval coverage; the cycle's commitment is to expand it before iterations start producing claims that depend on it.

---

## Format reference

Each iteration's narrative section follows this structure:

1. **Header block** — tag, companion tag (if any), phase, date, eval delta
2. **What this iteration shipped** — brief summary of the changes made, with cross-references to DECISIONS.md and the manifest file
3. **Trajectory before/after** — for each major change, a representative case showing the failing trajectory pre-change and the passing trajectory post-change, in the AHE paper Appendix C three-column format
4. **Eval delta** — the numerical outcome: pass@1 change, tokens/case change, fix-precision and regression-recall against the iteration's predictions
5. **Verdict summary** — outcome verdicts on the previous iteration's predictions, with brief commentary on the misses (the misses are the most informative content)
6. **Reflection** — calibration notes for future iterations: what the cycle learned about its own prediction reliability, what the eval suite caught that the manifest didn't, what surprised the author

The reflection section is what distinguishes this log from a release-notes file. Release notes describe what shipped; reflection describes what we learned about how we ship.

## On narrative honesty

The AHE paper's case studies in Appendix C have one feature most release notes lack: they describe the failures *as failures*, including the failures that the cycle's self-attribution failed to predict. The iteration-7 narrative (Lin et al. C.1.4) is particularly clear on this — it describes a case where the iteration-6 middleware emitted the right warnings but the agent ignored them because the warnings landed in tool output rather than model context. The fix in iteration-8 was to promote the warnings to a `BeforeModelHook`. The narrative does not gloss over the iteration-6 mistake; it names it and uses it.

PACCA's iteration narratives commit to the same standard. When an iteration's verdict comes back negative, this file describes what went wrong and why the constraint level was misjudged — not as confession, but as the most useful content for the next iteration to read.

---

*This file is updated when each iteration's evaluation round completes. It is part of PACCA's harness engineering documentation set; see [`docs/HARNESS.md`](./HARNESS.md) for the methodology and [`docs/DECISIONS.md`](./DECISIONS.md) for the structured audit log.*
