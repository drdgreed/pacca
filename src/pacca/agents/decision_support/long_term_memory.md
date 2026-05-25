# Decision Support Agent — Long-Term Memory

This file encodes case-pattern shortcuts learned from prior PACCA evaluations.
Entries describe COMPLETE criteria sets — never just headline indications.
When a pattern matches, the agent must STILL verify each listed criterion
against the case before applying the shortcut. Memory is reasoning **support**,
not reasoning **replacement**.

Entries follow a fixed format so the criterion-preservation discipline is
auditable:

1. **Headline indication** — one sentence naming the case class.
2. **Required criteria** — the full set that ALL must be explicitly documented.
3. **Anti-patterns** — the disqualifying details that flip the outcome.
4. **When the shortcut applies** — the outcome and the rationale-content requirement.
5. **When the shortcut DOES NOT apply** — explicit fallback to standard evaluation.

---

## Pattern: First-line pembrolizumab for metastatic NSCLC with high PD-L1

**Headline indication:** Stage IV (metastatic) non-small cell lung cancer,
first-line pembrolizumab monotherapy, per NCCN Category 1 recommendation
for PD-L1 TPS ≥ 50%.

**Required criteria — ALL must be explicitly documented:**

1. Disease stage is metastatic (stage IV) — NOT stage IIIA or earlier.
   Stage IIIA NSCLC is locally advanced and receives curative-intent
   combined-modality therapy (chemotherapy + radiation ± surgery),
   not first-line systemic monotherapy.
2. PD-L1 tumor proportion score (TPS) is **≥ 50%**, confirmed by a
   validated assay with a documented date.
3. **No** sensitizing EGFR mutations detected on molecular testing.
4. **No** ALK rearrangements detected on molecular testing.
5. **No** prior systemic therapy for metastatic disease (first-line status).
6. ECOG performance status documented (0 or 1 supports treatment tolerability).

**Anti-patterns — disqualify the shortcut, require human review:**

When ANY of the following is present, the auto-approve shortcut does NOT apply
and the case **routes to IN_REVIEW for human clinical judgment** — **NEVER to
DENIED**. These are borderline / off-pattern scenarios where a human clinician
must weigh the specific case context, not cases the system should reject
outright. The status field of your output must be `IN_REVIEW` in all such cases.

- PD-L1 TPS **< 50%** → guidelines recommend combination chemo-immunotherapy,
  not monotherapy. The patient may still be a candidate for combination
  therapy or for treatment with a different agent — that determination is
  a human decision. **Status: IN_REVIEW.** (Not DENIED.)
- EGFR sensitizing mutation present → first-line is targeted therapy
  (e.g. osimertinib), not pembrolizumab. The patient still needs treatment;
  the question is which one. **Status: IN_REVIEW.** (Not DENIED.)
- ALK rearrangement → first-line is ALK inhibitor (e.g. alectinib). Same
  pattern: alternative therapy may be appropriate. **Status: IN_REVIEW.**
  (Not DENIED.)
- Stage IIIA or earlier (locally advanced or earlier) → different treatment
  paradigm. The case may still warrant systemic therapy in specific contexts
  (e.g. unresectable disease, post-definitive-therapy progression). A human
  clinician determines that. **Status: IN_REVIEW.** (Not DENIED.)
- Prior systemic therapy for metastatic disease → not first-line, but may
  still be appropriate later-line therapy. **Status: IN_REVIEW.** (Not DENIED.)

**Why this distinction matters.** PACCA's design routes off-pattern cases
to human review, not to automatic denial. The agent's role is to recognize
that a case doesn't fit the auto-approve shortcut — NOT to make the
adjudication call itself. Multiple anti-patterns in one case do not justify
denial; they reinforce the need for human judgment.

**When the shortcut applies:** AUTO_APPROVE at high confidence (≥ 0.95).
The rationale MUST explicitly cite every required criterion above by its
specific value (e.g. "PD-L1 62%", "no EGFR", "no ALK", "stage IV", "first-line",
"ECOG 1"). Memory is the prompt for thoroughness, not the substitute for it.

**When the shortcut DOES NOT apply:** treat the case as a standard
evaluation under the framework in the main system prompt. The memory
pattern's role is to remind the agent which criteria to check explicitly —
not to skip them.

---

*This file is loaded at agent-initialization time by `_prompt_loader.py`
(see iter-2 chg-1's Jinja2 mount-point pattern). Updates here propagate
to the live agent on the next run.*
