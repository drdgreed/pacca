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

## Pattern: First-line biologic DMARD for seropositive RA after conventional DMARD failure

**Headline indication:** Seropositive rheumatoid arthritis with documented
failure of 2+ conventional DMARDs (typically methotrexate plus at least
one other), moderate-to-severe disease activity, requesting first-line
biologic DMARD therapy (e.g. abatacept, adalimumab, etanercept,
infliximab, tocilizumab) per ACR 2021 guidelines.

**Required criteria — ALL must be explicitly documented:**

1. Diagnosis is rheumatoid arthritis with **seropositive markers** —
   RF (rheumatoid factor) positive AND/OR anti-CCP (anti-cyclic
   citrullinated peptide) positive, with the specific test results
   in the chart.
2. Disease activity is **moderate-to-severe**, with a specific score
   documented: DAS28 ≥ 3.2, CDAI ≥ 10, or SDAI ≥ 11. Vague language
   like "active disease" without a score is not sufficient.
3. Step therapy: failure of **2 or more conventional DMARDs**, each at
   an adequate dose for an adequate duration. The typical pattern is
   methotrexate (≥ 3 months at therapeutic dose) plus at least one
   other conventional DMARD (hydroxychloroquine, sulfasalazine, or
   leflunomide). Document the specific agents, durations, and
   reason for failure (inefficacy or intolerance).
4. Requested agent is on the **ACR-recommended biologic list for RA**
   (TNF inhibitors, abatacept, tocilizumab, rituximab, JAK inhibitors).
5. **No active uncontrolled infection** and no contraindication to
   immunosuppression (e.g. latent TB without treatment, active
   hepatitis B).

**Anti-patterns — disqualify the shortcut, require human review:**

When ANY of the following is present, the auto-approve shortcut does NOT
apply and the case **routes to IN_REVIEW for human clinical judgment** —
**NEVER to DENIED**. These are cases where a clinician must weigh the
specific context, not cases the system should reject outright.

- Only **ONE** conventional DMARD tried (or none) → insufficient step
  therapy. The patient may need a second conventional DMARD trial first,
  OR there may be a documented intolerance pattern that justifies
  earlier biologic — a human determines that. **Status: IN_REVIEW.**
  (Not DENIED.)
- **Seronegative RA** (RF and anti-CCP both negative) → different
  treatment paradigm. Combination conventional DMARDs are typically
  preferred first; biologic may still be appropriate in specific
  contexts. **Status: IN_REVIEW.** (Not DENIED.)
- **Mild disease activity** (DAS28 < 3.2, CDAI < 10, or SDAI < 11) →
  biologic generally not indicated; conventional DMARDs may be sufficient.
  **Status: IN_REVIEW.** (Not DENIED.)
- **Inadequate trial duration** on prior DMARDs (< 3 months on
  methotrexate, etc.) → cannot establish true failure. The patient may
  need to complete the trial OR there may be a tolerability issue. A
  human determines that. **Status: IN_REVIEW.** (Not DENIED.)
- **Active infection / pregnancy / live vaccine within 30 days** →
  contraindication review. **Status: IN_REVIEW.** (Not DENIED.)
- Requested agent is **not** an ACR-recommended biologic for RA →
  unusual choice requires clinical justification. **Status: IN_REVIEW.**
  (Not DENIED.)

**Why this distinction matters.** Same as the NSCLC pembrolizumab entry:
PACCA's design routes off-pattern cases to human review, not to automatic
denial. Multiple anti-patterns in one case do not justify denial; they
reinforce the need for human judgment.

**When the shortcut applies:** AUTO_APPROVE at high confidence (≥ 0.95)
**conditional on** the policy-level cost check. The rationale MUST
explicitly cite (a) seropositive status with specific markers (RF and/or
anti-CCP), (b) each conventional DMARD tried with duration and outcome,
(c) the disease-activity score, and (d) that the requested agent is
ACR-recommended for RA.

**Important interaction with policy escalation (iter-3 chg-1):** if
`ClinicalRiskDetector`'s pre-flight `high_cost_check` fires (estimated
annual cost > HIGH_COST_THRESHOLD), the case routes to IN_REVIEW
regardless of clinical eligibility. The memory does **not** override
that — it gives the agent the clinical-reasoning support to articulate
"criteria met **but cost escalates per policy**" rather than the
incorrect "criteria met → approve" (which would be the wrong outcome on
GC-010 and any future high-cost biologic case). When the pre-flight has
fired, the agent's rationale should still cite the clinical criteria as
met, then acknowledge the cost trigger.

**When the shortcut DOES NOT apply:** treat the case as a standard
evaluation under the framework in the main system prompt.

---

*This file is loaded at agent-initialization time by `_prompt_loader.py`
(see iter-2 chg-1's Jinja2 mount-point pattern). Updates here propagate
to the live agent on the next run.*
