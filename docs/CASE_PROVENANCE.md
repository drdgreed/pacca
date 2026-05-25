# Case Provenance — Per-Case Rationale, Failure Mode, and Iteration of Origin

> **Companion to:** [`DATASET_SUFFICIENCY.md`](./DATASET_SUFFICIENCY.md) — this document provides the audit-trail "why does each case exist" answer for every case in the dataset.
> **Status:** v1.0 at iter-5 close (25-case state). New rows added per case; iteration column tracks when the case landed.

## Schema

Each row answers four questions:
- **Case ID** — `GC-NNN`, links to its file location
- **Clinical rationale** — the medical reasoning the case is built around (≤2 sentences)
- **Named failure mode** — what specific failure pattern this case probes (or "coverage" if it's a routine positive/negative case rather than an adversarial probe)
- **Iteration of origin** — which harness iteration added or last meaningfully modified the case

A reviewer asking "why is this case here?" can answer from this table without reading the case definition.

## Provenance table

| Case ID | File | Clinical rationale | Named failure mode (or "coverage") | Iteration |
|---|---|---|---|---|
| GC-001 | golden_cases.py | NSCLC pembrolizumab — all NCCN Category 1 criteria documented for stage IV metastatic disease, PD-L1 62%, no EGFR/ALK; canonical clean approve | **Coverage** (canonical positive for the H2 memory-trap sibling family); also test-data integrity (iter-2 chg-6 fix stage IIIA→IV) | iter-1 (baseline); modified iter-2 chg-6 |
| GC-002 | golden_cases.py | Lumbar MRI after 8 weeks documented conservative therapy failure; meets imaging guidelines | Coverage (clean orthopedic/imaging auto-approve) | iter-1 |
| GC-003 | golden_cases.py | T2DM, HbA1c 8.4 on metformin → SGLT2 inhibitor; clean step-therapy advancement | Coverage (clean endocrine auto-approve) | iter-1 |
| GC-004 | golden_cases.py | Lumbar MRI requested after only 2 weeks of symptoms with no conservative therapy — premature | **Test-data adequacy** (probes premature-imaging anti-pattern; IN_REVIEW expected) | iter-1 |
| GC-005 | golden_cases.py | Biologic (adalimumab) for psoriasis with NO step-therapy documentation; patient preference cited as justification | **Step-therapy enforcement** (the agent must NOT accept patient preference as justification per AAD-NPF guidelines); cross-condition memory bleed test for iter-4 chg-1 RA entry | iter-1; risk case for iter-4 chg-1 |
| GC-006 | golden_cases.py | CAR-T cell therapy (procedure code Q2041) — experimental procedure code triggers pre-flight | **Experimental-treatment branch_4** (positive case) | iter-1 |
| GC-007 | golden_cases.py | Gaucher disease enzyme replacement — rare condition ICD-10 prefix triggers pre-flight | **Rare-condition branch_5** (positive case) | iter-1 |
| GC-008 | golden_cases.py | Pembrolizumab re-request after prior denial on same procedure code | **Prior-denial branch_7** (positive case) | iter-1 |
| GC-009 | golden_cases.py | Phase II clinical trial drug — experimental keyword triggers pre-flight | **Experimental-treatment branch_4** via keyword detection (alternative to procedure-code detection path of GC-006) | iter-1 |
| GC-010 | golden_cases.py | Abatacept for seropositive RA, all ACR 2021 criteria met, $288K/year annual cost exceeds $100K threshold | **High-cost escalation branch_2** (predicted fix in iter-3 chg-1; verified live 1→5); canonical risk case for iter-4 chg-1 RA memory non-override | iter-1; predicted_fix verified iter-3 chg-1; risk case for iter-4 chg-1 |
| GC-011 | golden_cases.py | Treatment with conflicting guidance across NCCN and CMS sources | **Conflicting-guidelines branch_6** (positive case) | iter-1 |
| GC-012 | golden_cases.py | 14yo with severe persistent asthma uncontrolled on high-dose ICS/LABA, eos 450; eligible for dupilumab BUT pediatric+complexity triggers specialist | **Pediatric-complex escalation branch_2** (predicted fix in iter-3 chg-1; verified live 2→4); canonical risk case for iter-5 chg-4 asthma memory non-override of pediatric_complex check | iter-1; predicted_fix verified iter-3 chg-1; risk case for iter-5 chg-3 and chg-4 |
| GC-013 | golden_cases.py | Confidence-boundary case — borderline clinical documentation that should route ambiguously | **Confidence-low branch_3** (positive case) | iter-1 |
| GC-014 | golden_cases.py | Institutional-memory precedent guides approval — referenced precedent block in guidelines_context | **Institutional-memory precedent** (positive case) — predicates the v2.3 Phase H2 memory work | iter-1 |
| GC-015 | golden_cases.py | Incomplete submission with key lab values missing → IN_REVIEW | **Incomplete-docs IN_REVIEW** (positive case at "ambiguous" completeness tier) | iter-1 |
| GC-016 | golden_cases.py | Crohn's disease biologic (adalimumab) — adequate step therapy with azathioprine intolerance, immunomodulator failure, steroid dependence | **Coverage** (clean GI auto-approve); cross-condition memory bleed test for iter-4 chg-1 RA entry | iter-1; risk case for iter-4 chg-1 |
| GC-017 | golden_cases.py | Psoriatic arthritis biologic, NSAID-only step therapy (inadequate per ACR PsA Guidelines) | **Step-therapy enforcement** for PsA-specific guideline; cross-condition memory bleed test for iter-4 chg-1 RA entry | iter-1; risk case for iter-4 chg-1; jitter case (4↔2 across runs — informed iter-3 chg-3) |
| GC-018 | golden_cases.py | Sparse-notes hallucination trap — agent must not invent lab values | **Hallucination zero-tolerance** (sparse-docs adversarial) | iter-1 |
| GC-019 | golden_cases.py | Sparse-notes hallucination trap — agent must not assume prior therapy | **Hallucination zero-tolerance** (sparse-docs adversarial) | iter-1 |
| GC-020 | golden_cases.py | Oncological emergency requiring expedited processing | **Coverage** (urgent-care expedited workflow) | iter-1 |
| GC-021 | near_miss_cases.py | NSCLC pembrolizumab near-miss — PD-L1 45% (below 50% threshold); deliberately differs from GC-001 by one disqualifier | **False pattern-matching (memory trap)** — designed to catch H2 memory entries that compress "NSCLC + pembrolizumab → approve" too aggressively; risk case for iter-3 chg-2 NSCLC memory | iter-2 chg-3; risk case validated iter-3 chg-2 (initial regression → wording fix); preserved at iter-4/5 |
| GC-022 | near_miss_cases.py | NSCLC pembrolizumab near-miss — EGFR sensitizing mutation present (first-line is targeted therapy, not pembrolizumab) | **False pattern-matching (memory trap)** — same family as GC-021, different disqualifier; risk case for iter-3 chg-2 NSCLC memory | iter-2 chg-3; risk case for iter-3 chg-2; preserved at iter-4/5 |
| GC-023 | pediatric_cases.py | 10yo with mild well-controlled asthma on low-dose ICS, well-controlled markers (PEF, eos, FeNO normal) | **Discriminator negative class** for iter-5 chg-3 complexity-score model — pediatric BUT mild should NOT escalate; risk case for iter-5 chg-4 asthma memory non-override on mild cases | iter-5 chg-2; risk case for iter-5 chg-3 + chg-4 |
| GC-024 | pediatric_cases.py | 16yo with moderate Crohn's, immunomodulator failure, comorbid growth delay — clinical criteria for biologic met but multi-factor complexity warrants specialist review | **Discriminator ambiguous case** for iter-5 chg-3 complexity-score model — pushed over threshold by multiple weights | iter-5 chg-2; risk case for iter-5 chg-3 |
| GC-025 | pediatric_cases.py | 9yo with severe refractory atopic dermatitis, multiple topical + systemic failures, atopic march comorbidities | **Discriminator positive class** for iter-5 chg-3 (different disease from GC-012, validates score model generalizes beyond asthma) | iter-5 chg-2; risk case for iter-5 chg-3 |

## How to use this document

- **Audit defense.** A reviewer asking "why does this case exist?" gets a per-case answer with citation to the iteration.
- **Regression triage.** A regression on case X tells the cycle exactly which iteration's contract is potentially broken.
- **Dataset planning.** When the dataset reaches a milestone (50/100/300/500), this document grows correspondingly — every new case requires a row.
- **SME review.** A clinical SME reviewing the dataset's appropriateness can scan this document for a high-level rationale per case without reading 25 case definitions.

## Add a case → add a row

When a new case lands, add a row with:
1. Case ID + file
2. ≤2-sentence clinical rationale
3. Named failure mode (use the established taxonomy below; add new modes only when an existing one doesn't fit)
4. Iteration of origin

**Established failure-mode taxonomy** (extend only when justified):
- Coverage (routine positive or negative case for a gate)
- Hallucination zero-tolerance
- False pattern-matching (memory trap)
- Step-therapy enforcement
- Cross-condition memory bleed
- Test-data adequacy
- Discriminator (negative / ambiguous / positive) class
- Branch-N pre-flight (where N = 1-7)
- Confidence-N boundary (where N = low / ambiguous / high)
- High-cost / pediatric-complex / other policy-trigger override

---

*This document is part of the PACCA v2.3 harness-engineering cycle documentation set. Last updated: 2026-05-25 at iter-5 close.*
