# Finding: H2 institutional memory entries require iterative refinement

**Severity:** SEV-4 (methodology data point; not a defect)
**Surfaced by:** iter-3 chg-2 live verification on GC-021
**Category:** methodology learning — memory engineering is prompt engineering
**Recommended action:** record as a constraint on all future H2 memory entries
**Related code:** `src/pacca/agents/decision_support/long_term_memory.md`, `tests/unit/test_h2_memory_criterion_preservation.py`
**Reproducer:** `python -m tests.clinical.investigate_case GC-021` at iter-3 chg-2 HEAD pre-fix vs post-fix

## What we observed

iter-3 chg-2 shipped the first Phase H2 institutional memory entry (NSCLC
pembrolizumab). The memory file's first-pass anti-pattern list followed the
iter-2-findings design constraint precisely: enumerate every disqualifying
detail, route each to IN_REVIEW. The wording for each anti-pattern was:

> - PD-L1 TPS **< 50%** → guidelines recommend combination chemo-immunotherapy,
>   not monotherapy. **Route to IN_REVIEW.**

(Plus four other anti-patterns, each ending with **Route to IN_REVIEW.**)

The unit tests passed; the rendered prompt contained every required
criterion and every anti-pattern verbatim; the criterion-preservation
contract was satisfied. Then the live verification on the three risk cases
ran:

- **GC-001** (canonical clean approve): score 5 ✓
- **GC-022** (EGFR+ near-miss): score 3, IN_REVIEW ✓
- **GC-021** (PD-L1 45% near-miss): **score 2, status DENIED** ✗

The agent's rationale identified BOTH anti-patterns (PD-L1 < 50% AND stage IIIA)
and concluded the request should be **denied** rather than escalated. Each
single anti-pattern, taken alone, would have routed to IN_REVIEW. Two
anti-patterns together generalized to DENIED.

## Root cause

The memory's first-pass wording said "Route to IN_REVIEW" five times but
never said "(Not DENIED.)" The agent appears to have read the cumulative
weight of multiple anti-patterns as evidence for a stronger negative
decision than any single one warranted. Without an explicit boundary
between IN_REVIEW and DENIED in the memory text, the boundary was inferred
from context — and the context (a case with multiple disqualifiers) tilted
the inference toward denial.

This is a category-error class PACCA's design specifically forbids: routing
off-pattern cases to automatic denial rather than human judgment. Per
`docs/HARNESS.md` and the PRD, the agent's role is to *recognize* that a
case doesn't fit the auto-approve shortcut — not to make the adjudication
call itself.

## Fix

The memory's anti-pattern list was rewritten to make the IN_REVIEW vs
DENIED distinction explicit at every anti-pattern:

> - PD-L1 TPS **< 50%** → guidelines recommend combination chemo-immunotherapy,
>   not monotherapy. The patient may still be a candidate for combination
>   therapy or for treatment with a different agent — that determination is
>   a human decision. **Status: IN_REVIEW.** (Not DENIED.)

Plus a new paragraph at the bottom of the anti-pattern list:

> **Why this distinction matters.** PACCA's design routes off-pattern cases
> to human review, not to automatic denial. The agent's role is to recognize
> that a case doesn't fit the auto-approve shortcut — NOT to make the
> adjudication call itself. Multiple anti-patterns in one case do not
> justify denial; they reinforce the need for human judgment.

Live verification after the fix: GC-021 score **2 → 5** with `correct_outcome=True`.
The judge's verdict text after the fix called out *"demonstrates genuine
case-by-case analysis rather than pattern-matching to a canonical approval
case"* — the exact behavior the H2 design contract was meant to produce.

## What this teaches the cycle

**Memory writing is closer to prompt engineering than data engineering.**
A memory entry is not a passive database row that the agent looks up; it
is a structured prompt fragment that the agent reasons over. Subtle wording
choices that would be invisible in a data context become behaviorally
significant in a prompt context. Two consequences for the methodology:

1. **The criterion-preservation test (iter-3's analog of iter-1's
   byte-identity check) is necessary but not sufficient.** It guarantees
   that every required criterion and anti-pattern is *present* in the
   rendered prompt. It does NOT guarantee the *semantics* of those entries
   are clear to the agent. Live verification on risk cases is the gate that
   catches semantic gaps.

2. **Every H2 memory entry should ship with at least one risk case verified
   live before the entry lands on main.** The risk cases for this entry
   are GC-001 (canonical), GC-021 (one-criterion miss), and GC-022 (one-criterion
   miss). Future entries need analogous risk coverage — the criterion-
   preservation test alone can pass while the entry's behavioral effect is
   wrong.

## Constraints on future H2 memory entries (recorded as forward design notes)

When adding a new memory entry:

- Each anti-pattern MUST end with an explicit status routing
  (`**Status: IN_REVIEW.**` or `**Status: AUTO_APPROVED.**`) with a
  `(Not DENIED.)` / `(Not IN_REVIEW.)` clarification when the
  decision-class boundary is ambiguous.
- Each entry MUST list its risk cases (the cases that would distinguish
  correct vs incorrect application of the shortcut) and include live
  verification on each before merging.
- The criterion-preservation test file MUST be extended with the new
  entry's criteria and anti-patterns by name.
- The PROMPT_REGISTRY version bump (e.g. v2.3 -> v2.4) signals via the
  audit log that a new memory entry was added at that decision point.

## Why this finding is SEV-4

This is not a defect. It is the cycle's first observation that H2 memory
entries are *engineered artifacts* requiring iteration based on live
behavior, not finished artifacts that can be specified once and locked in.
The runbook for iter-4 onward should reflect this: budget time for live
verification + memory wording refinement, treat the first-pass entry as
a draft, and document the wording journey in the iteration narrative.

PACCA's iter-3 chg-2 commit message and the iter-3 ITERATIONS.md narrative
both record the in-iteration refinement explicitly, so the methodology
record is honest about what the iteration learned.
