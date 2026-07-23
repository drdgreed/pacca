# Regulatory Consultant RFP — Selection Kit

> **Purpose.** Operational guide for selecting an FDA SaMD (Software as a Medical Device) regulatory consultant. The consultant supports the 510(k) or De Novo submission required for SaMD-grade deployment per `PACCA_PRD_v2.5_Consolidated.md` § 16.
>
> **When to engage.** **6 months before the 500-case dataset milestone.** At the 3-month-to-300-case pace, that puts consultant engagement at roughly month 9-12 of the push (after 300 is hit). Don't engage earlier — you don't yet have the clinical-validation evidence package the consultant needs to scope the work.
>
> **Don't engage later.** The consultant's lead time on credentials, conflict-of-interest checks, and onboarding is 4-8 weeks. Pre-Sub meeting scheduling with FDA is another 60-90 days. Late engagement = late submission.

## Why this document exists

The FDA SaMD pathway requires regulatory expertise that engineering skill cannot substitute for. The consultant's value is not writing code — it's knowing:
- Whether 510(k) (substantial equivalence to a predicate device) or De Novo (no predicate; new device class) applies to PACCA
- How the FDA's 2023 cybersecurity premarket guidance interprets your security posture
- What clinical-validation evidence the FDA expects for an AI/ML-based SaMD (this is a moving target)
- The Q-Sub Pre-Submission meeting workflow (60-90 day lead time, structured agenda, formal FDA response)
- How to format your existing documentation (PRD, ARCHITECTURE, DECISIONS, ITERATIONS) into the FDA's expected Design History File structure (21 CFR § 820.30)

Choosing the wrong consultant burns 6-12 months of calendar and $100K-$250K in fees with no submission to show for it. Choosing the right one cuts the path to submission roughly in half.

## When you're ready to engage

You're ready when you have:

- [ ] **Dataset at 300+ cases.** Pre-Sub meetings benefit from a concrete artifact, not a roadmap.
- [ ] **CRB κ data from at least one quarter.** Per `CRB_SOURCING.md`, the κ evidence is the FDA's "how do you know your labels are right" answer.
- [ ] **`docs/PACCA_PRD_v2.5_Consolidated.md` updated** to v2.6+ reflecting the production state.
- [ ] **A target deployment partner.** Even a non-binding LOI from a payer pilot dramatically helps FDA scope. The consultant will ask "who is the intended user?" — having a real answer matters.
- [ ] **Budget approved** for at least the Pre-Sub phase ($30K-50K range).

If any of these are missing, defer engagement. Use the time to address the gap.

## Capabilities matrix — what to look for

Score each candidate 1-5 on each axis. Total / max for quick comparison.

### Substantive regulatory experience

| Capability | Why it matters | Score 1-5 |
|---|---|---|
| 510(k) submissions in clinical decision support (CDS) software | Direct precedent for your pathway | |
| De Novo submissions in AI/ML SaMD | Backup pathway if no 510(k) predicate exists | |
| AI/ML-specific pre-cert experience | FDA's AI/ML SaMD action plan is the framework you'll be navigating | |
| Familiarity with FDA's 2024 GMLP (Good Machine Learning Practice) guiding principles | Currently soft guidance; will become enforcement framework | |
| Post-market change-control experience (PCCPs — Predetermined Change Control Plans) | Critical for PACCA's harness-iteration model — the FDA needs to know how you'll update the model post-clearance | |

### Cybersecurity & privacy

| Capability | Why it matters | Score 1-5 |
|---|---|---|
| FDA 2023 premarket cybersecurity guidance experience | Strict and enforced; HIPAA compliance ≠ FDA cybersecurity compliance | |
| Threat modeling experience | Required deliverable in the submission | |
| SBOM (Software Bill of Materials) preparation | Required since 2023 | |

### Process & deliverables

| Capability | Why it matters | Score 1-5 |
|---|---|---|
| Design History File (21 CFR § 820.30) authoring | The core deliverable; must convert your existing docs to FDA format | |
| Risk Management File (ISO 14971) authoring | Required and currently does not exist in PACCA docs | |
| Pre-Sub Q-Sub meeting preparation | Structured 60-90 day process; consultant runs the agenda | |
| RFP response support (post-submission FDA questions, typically 1-3 rounds) | Adds 4-8 weeks per round to the timeline; consultant must be retained through this | |

### Soft criteria

| Capability | Why it matters | Score 1-5 |
|---|---|---|
| Domain familiarity with prior authorization / payer workflow | Reduces ramp-up time | |
| Communication style — clear, written, asks good questions | You'll work closely for 6-12 months | |
| References from at least 2 prior CDS-software clients within last 24 months | Recency matters; FDA guidance shifts | |

## Pricing benchmarks (2026)

| Engagement type | Typical fee | Notes |
|---|---|---|
| Initial scoping call (free) | $0 | Most reputable consultants offer 30-60 min initial scoping at no charge |
| Strategy + roadmap (1-2 weeks) | $5K-15K | One-time; consultant audits your current state and writes a recommended path |
| Pre-Sub meeting prep + facilitation | $25K-50K | Includes Q-Sub package authoring, FDA meeting attendance, post-meeting follow-up document |
| Full 510(k) submission support | $80K-200K | Includes Design History File assembly, all required documents, RFP response support |
| Full De Novo submission support | $150K-300K | More involved than 510(k); includes predicate-novelty analysis |
| Hourly engagement (for ad-hoc questions, ongoing retainer) | $250-450/hr | Senior consultants at the high end; mid-level at the low end |

**Budget framing:** at the V2+ forecast's anchor numbers ($96K-$256K consultant + $25K-$50K Pre-Sub fees), you should expect total regulatory spend of **$125K-$310K** to get the submission filed. FDA review fees are separate (~$22K for 510(k), ~$162K for De Novo as of 2026, with small-business reductions available).

## Interview rubric

Use for the 60-90 min deep-dive call after initial scoping. Score candidate on each dimension; recommend hire if total ≥ 70% of max.

### Section 1 — Pathway recommendation (15 min)

Ask the consultant to spend 10 minutes auditing what they can see of PACCA (README + PRD), then ask:

- "Based on what you've seen, do you recommend 510(k) or De Novo? Why?"
- "What predicate devices, if any, would you cite for substantial equivalence?"
- "If De Novo, what's your novelty argument?"
- "What's the biggest risk in this pathway recommendation?"

**Strong answer:** Specific predicate device names with rationale (e.g., "IDx-DR's De Novo precedent for autonomous diagnostic AI suggests..."). Acknowledges uncertainty and proposes how to resolve it (e.g., "we'd run this by the FDA in the Pre-Sub").

**Weak answer:** Generic ("we'd evaluate the options"), no specific precedents named, no risk acknowledgment.

### Section 2 — Clinical validation framework (15 min)

- "What clinical-validation evidence does the FDA expect for an AI-based prior-authorization decision support tool?"
- "How would you frame PACCA's CRB κ evidence in the submission?"
- "What's missing from PACCA's current validation that would block the submission?"

**Strong answer:** References specific FDA guidance documents (e.g., "Clinical Decision Support Software" 2022 final guidance). Identifies specific gaps with priority order. Knows the difference between analytical validation and clinical validation.

**Weak answer:** "We'd need to do clinical validation." Vague, no specifics.

### Section 3 — Cybersecurity & post-market (15 min)

- "Walk me through how you'd approach the cybersecurity premarket documentation."
- "What's your experience with PCCPs (Predetermined Change Control Plans)? PACCA's harness methodology iterates the model frequently — how do we get that through FDA?"
- "What's the post-market surveillance plan look like?"

**Strong answer:** Specific tools and frameworks (e.g., "we'd use the FDA's published cybersecurity refuse-to-accept checklist as the starting point"). Articulate on PCCPs as a vehicle for iteration. Concrete post-market plan.

**Weak answer:** Generic, no specific tools or frameworks, treats PCCPs as unfamiliar.

### Section 4 — Project management & communication (15 min)

- "Walk me through a typical timeline from contract signature to submission filed."
- "How do you communicate progress? Weekly? Async docs?"
- "What's your process when the FDA comes back with RFP questions?"
- "Reference clients we can speak with?"

**Strong answer:** Specific timeline (e.g., "8-14 months from signature to submission, broken into Pre-Sub Q1, gap-fill Q2-Q3, submission Q4"). Documented PM process. References offered without hesitation.

**Weak answer:** Vague timelines. No documented process. References "can be provided after we sign."

### Section 5 — Pricing & engagement structure (15 min)

- Get a written quote for the proposed scope
- Ask about pricing model: flat fee, hourly, milestones, retainer + variable?
- Ask about scope changes: what triggers a change order?
- Ask about RFP response: included in the original quote, or separate engagement?
- Ask about termination: what happens to your DHF if you part ways mid-engagement?

**Strong answer:** Written quote in 5 business days. Milestone-based pricing with clear deliverables. RFP response scoped explicitly. Clean termination terms (DHF stays with you).

**Weak answer:** "We'll work it out." Hourly-only with no cap. RFP response is a separate engagement. Termination terms favor the consultant.

## Red-flag checklist

Any of these is a serious concern. Two or more is a hard pass.

- 🚩 Never personally worked on a CDS-software submission (only experience is medical-device hardware)
- 🚩 Cannot name 2+ recent (≤ 24 months) AI/ML SaMD precedents
- 🚩 Quotes vague pricing (range > 3x; "depends on scope" without follow-up)
- 🚩 No published thought leadership (blog posts, webinars, conference talks) in the last 18 months — suggests not actively engaged with current FDA guidance
- 🚩 References from clients are >3 years old or all in unrelated device classes
- 🚩 Insists on hourly billing with no scope cap
- 🚩 Will not let you speak with the actual consultant who'd do the work (sales rep handoff)
- 🚩 Does not have errors & omissions insurance ($1M+ minimum)
- 🚩 Refuses to discuss prior submissions that did NOT clear (everyone has them; refusal signals defensiveness)

## Sample SOW outline

Standard scope decomposition. Use as template when requesting quotes.

```
1. Phase 0 — Strategy + Roadmap (1-2 weeks, $5K-15K)
   - Audit of current PACCA documentation
   - Pathway recommendation (510(k) vs De Novo) with rationale
   - Gap analysis: what's missing from FDA submission readiness
   - Recommended workplan with milestones

2. Phase 1 — Pre-Sub Q-Sub (3-4 months, $25K-50K)
   - Q-Sub package authoring
   - FDA meeting attendance + facilitation
   - Post-meeting follow-up document
   - Identification of items to address before formal submission

3. Phase 2 — Submission Package Authoring (6-9 months, $80K-200K for 510(k))
   - Design History File assembly per 21 CFR § 820.30
   - Risk Management File per ISO 14971
   - Cybersecurity documentation per 2023 FDA guidance
   - Clinical validation report
   - Software lifecycle (SDLC) documentation
   - eCopy submission formatting
   - Filing with FDA

4. Phase 3 — Post-Submission RFP Response (estimated, 4-8 weeks per round, hourly)
   - Response to FDA questions (typically 1-3 rounds)
   - Supplementary document authoring
   - Re-submission as needed

5. Optional: Phase 4 — Post-Market Surveillance Plan + Annual Reports (retainer)
   - Ongoing PCCP execution
   - Annual reporting per 21 CFR § 814.84
```

## Vendor refusal procedure

If after interviewing 3-5 candidates you cannot find one that scores adequately on the rubric:

1. **Re-scope.** Are you trying to engage at the wrong scale? Initial scoping calls are usually free; consider engaging two consultants for Phase 0 only, compare their roadmaps, then pick for Phase 1+.
2. **Adjust budget.** The mid-tier ($100K-150K consultants) often outperform either the cheap ($50K) or the elite ($300K+) options for early-stage AI SaMD.
3. **Re-evaluate timing.** If no consultant will engage at your current evidence level, you're not ready. Defer 3-6 months and re-source after gaining the missing artifacts.

## Documentation outputs

When consultant engagement begins, capture these as part of the project history:

- `docs/regulatory/Q0_consultant_selection.md` — which candidates were considered, scoring matrix, decision rationale
- `docs/regulatory/Q1_pre_sub_package.md` — Q-Sub agenda + FDA response
- `docs/regulatory/Q2_gap_remediation.md` — items addressed between Pre-Sub and formal submission
- `docs/regulatory/submission_artifacts/` — final submission package (or pointers to where it lives; some artifacts can't be public)

---

*Last updated: 2026-05-27.*
