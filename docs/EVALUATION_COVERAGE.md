# Evaluation Coverage Matrix

> **⚠️ Reconciliation note (updated 2026-07-20).** The on-disk dataset is now **105 cases** (GC-001 through GC-105, across the `tests/clinical/*_cases.py` family files — verified by unique-ID count and `TestGoldenDatasetIntegrity`). The per-cell matrix below still reflects the **33-case state**; re-baselining the matrix to 105 (mapping GC-034→GC-105 into the dimension cells) is a tracked follow-up. Until then, trust the case files as the source of truth for *which* cases exist; trust this matrix only for the *shape* of the coverage methodology. PRD-level coverage claims at 105 are in [`PACCA_PRD_v2.5_Consolidated.md`](PACCA_PRD_v2.5_Consolidated.md) § 16.6.
>
> **Companion to:** [`DATASET_SUFFICIENCY.md`](./DATASET_SUFFICIENCY.md) — this document grounds the coverage claims at the per-cell level.
> **Status:** matrix at 33-case state; on-disk dataset at 105 (production-pilot milestone crossed); per-cell re-baseline pending. Originally drafted at iter-6 open (8 expansion cases added per the iter-5 gap analysis); re-baseline when crossing 300 / 500.

## How to read this document

Each section is a *dimension* (outcome class, escalation branch, specialty, age, etc.). Each cell shows the case IDs that cover that cell. Empty cells mark gaps explicitly. A reviewer asking "where do you test X?" finds the answer by case ID and can verify the case definition in [`tests/clinical/golden_cases.py`](../tests/clinical/golden_cases.py), [`tests/clinical/near_miss_cases.py`](../tests/clinical/near_miss_cases.py), [`tests/clinical/pediatric_cases.py`](../tests/clinical/pediatric_cases.py), or [`tests/clinical/expansion_cases.py`](../tests/clinical/expansion_cases.py).

The current dataset:
- **GOLDEN_CASES:** 20 (GC-001 through GC-020)
- **NEAR_MISS_CASES:** 2 (GC-021, GC-022)
- **PEDIATRIC_CASES:** 3 (GC-023, GC-024, GC-025)
- **EXPANSION_CASES:** 8 (GC-026 through GC-033) — iter-6 gap-closure suite
- **Total live:** 33

## Dimension 1 — Outcome class × Expected branch

| Outcome class \\ Branch | branch_1_high_confidence (auto-approve) | branch_2_medical_director | branch_3_low_confidence | branch_4_experimental | branch_5_rare | branch_6_conflicting | branch_7_prior_denial | NONE |
|---|---|---|---|---|---|---|---|---|
| **AUTO_APPROVED** | GC-001, GC-002, GC-003, GC-014, GC-016, GC-020, GC-023, GC-028, GC-030, GC-031, GC-032, GC-033 | — | — | — | — | — | — | — |
| **IN_REVIEW** | — | GC-010, GC-012, GC-024, GC-025, GC-029 | GC-004, GC-005, GC-013, GC-015, GC-017, GC-021, GC-022 | — | — | — | — | — |
| **PRE_FLIGHT_ESCALATE** | — | — | — | GC-006, GC-009 | GC-007 | GC-011 | GC-008 | — |
| **DENIED** | — | — | — | — | — | — | — | GC-026, GC-027 |
| **INFORMATION_NEEDED** | — | — | GC-018, GC-019 | — | — | — | — | — |

**Gaps surfaced (iter-6 update):**
- **DENIED is now populated (was empty at iter-5).** GC-026 (proton-beam for low-risk prostate per NCCN/ASTRO) and GC-027 (cath without non-invasive workup per ACC/AHA) close the 0-DENY gap. **Next step:** grow DENY to ≥ 5 cases per `DATASET_SUFFICIENCY.md` §5 (target: criteria-not-met, contraindication, frequency-cap, prior-denial-without-new-evidence, off-label-without-evidence).
- AUTO_APPROVED × branch_2_medical_director is empty by design — these branches are mutually exclusive by policy.
- branch_4–7 each have 1–2 cases (the integrity test enforces ≥1).
- branch_3 is over-represented (7 cases) because confidence-low / ambiguous is the default escalation path.
- AUTO_APPROVED count grew from 7 → 12, IN_REVIEW grew from 11 → 12. Aggregate accuracy claims have substantially more evidence.

## Dimension 2 — Age bracket × Disease specialty

| Specialty \\ Age | <12 | 12–17 | 18–64 | 65–79 | 80+ |
|---|---|---|---|---|---|
| Oncology (med-onc) | — | — | GC-001 (NSCLC), GC-008 (NSCLC denied), GC-009 (oncology Phase II), GC-020 (oncological emergency), GC-021 (NSCLC near-miss), GC-022 (NSCLC near-miss), GC-033 (breast/fertility-overlap) | GC-011 (conflicting), GC-015 (incomplete) | — |
| Oncology (radiation) | — | — | GC-026 (prostate proton-beam DENIED) | — | — |
| Rheumatology / immunology | — | — | GC-010 (RA biologic high cost), GC-017 (PsA biologic) | — | — |
| Pulmonology / asthma | — | GC-012 (pediatric severe asthma) | — | — | — |
| GI / IBD | — | GC-024 (pediatric moderate Crohn's) | GC-016 (Crohn's biologic) | — | — |
| Endocrinology | — | — | GC-003 (T2DM SGLT2) | — | — |
| Cardiology | — | — | GC-027 (cath inappropriate use DENIED) | — | GC-028 (ICD per CMS NCD AUTO_APPROVED) |
| Mental health / behavioral | — | — | GC-029 (adult ADHD + SUD IN_REVIEW) | — | — |
| Orthopedics / imaging | — | — | GC-002 (lumbar MRI complete), GC-004 (lumbar MRI premature) | — | — |
| Dermatology | GC-025 (pediatric severe AD) | — | GC-005 (psoriasis step therapy not met) | — | — |
| Hematology / oncology rare | — | GC-006 (CAR-T at 19yo — boundary case) | GC-007 (Gaucher), GC-030 (sickle cell hydroxyurea) | — | — |
| Neurology | — | — | GC-032 (chronic migraine CGRP) | — | — |
| Reproductive endocrine / OB | — | — | GC-033 (fertility preservation pre-chemo) | — | — |
| Nephrology / transplant | — | — | GC-031 (post-transplant tacrolimus) | — | — |
| Confidence-boundary (non-specialty-specific) | — | — | GC-013 (borderline docs) | — | — |
| Routine refill (non-specialty-specific) | GC-023 (pediatric mild asthma) | — | — | — | — |

**Gaps surfaced (iter-6 update):**
- **Cardiology now covered (was zero):** GC-027 (DENY), GC-028 (AUTO_APP geriatric). Still need ≥ 5 cases for cardiology to claim within-specialty per-class detection.
- **Mental health now covered (was zero):** GC-029. Still need ≥ 5 cases — major depressive disorder, anxiety, psychosis, substance use disorder treatment.
- **OB/reproductive now covered (was zero):** GC-033. Still need ≥ 5 — pregnancy authorizations, contraception coverage edge cases, infertility workup outside the cancer-overlap context.
- **Transplant now covered (was zero):** GC-031. Need ≥ 5 — heart, lung, liver, marrow, plus initiation vs maintenance.
- **Neurology now covered (was zero):** GC-032. Need ≥ 5 — MS DMTs, Alzheimer's, neurodegenerative biologics, epilepsy.
- **80+ age bracket now covered (was zero):** GC-028. Need ≥ 3 more for geriatric complexity coverage.
- **Pulmonology adult: still zero.** Adult asthma / COPD biologics absent.
- **Adolescent 12–17 still minimal:** only 2 cases (GC-012, GC-024).

## Dimension 3 — Outcome × Documentation completeness

| Completeness \\ Outcome | AUTO_APPROVED | IN_REVIEW | DENIED | INFORMATION_NEEDED | PRE_FLIGHT_ESCALATE |
|---|---|---|---|---|---|
| Complete (all fields explicitly documented) | GC-001, GC-002, GC-003, GC-014, GC-016, GC-020, GC-023, GC-028, GC-030, GC-031, GC-032, GC-033 | GC-010, GC-012, GC-017, GC-024, GC-025, GC-029 | GC-026, GC-027 | — | GC-006, GC-007, GC-009, GC-011 |
| Ambiguous (some fields incomplete) | — | GC-004, GC-005, GC-013, GC-015, GC-021, GC-022 | — | — | — |
| Sparse (substantial gaps, requires INFO_NEEDED or escalation) | — | — | — | GC-018, GC-019 | GC-008 |

**Gaps surfaced (iter-6 update):**
- **DENIED now has 2 cases at "complete" tier.** Need ambiguous-tier and sparse-tier DENY cases for graded denial coverage (the criteria-not-met disposition under varying evidence quality).
- **Sparse documentation: still only 2 cases** (hallucination traps). Need graded completeness — missing one lab value, missing dose duration, missing prior-therapy details — beyond the extreme sparse-notes traps.
- **Ambiguous AUTO_APPROVED: still zero cases.** Real-world auto-approves often have minor ambiguity that the agent must reason past.

## Dimension 4 — Cost tier × Escalation outcome

| Cost tier \\ Outcome | AUTO_APPROVED | IN_REVIEW via cost | IN_REVIEW via other | DENIED | Not annotated for cost |
|---|---|---|---|---|---|
| Under threshold (<$100K/year) | GC-001, GC-002, GC-003, GC-004, GC-005, GC-013, GC-014, GC-015, GC-016, GC-017, GC-018, GC-019, GC-020, GC-023, GC-028, GC-029, GC-030, GC-031, GC-032, GC-033 | — | GC-012, GC-024, GC-025 | GC-027 | GC-006, GC-007, GC-008, GC-009, GC-011 |
| At threshold ($95K–$105K/year) | — | — | — | — | — |
| Over threshold (>$100K/year) | — | GC-010 ($288K abatacept) | — | GC-026 (proton-beam $80K-$200K depending on cycles) | — |

**Gaps surfaced (iter-6 update):**
- **At-threshold (boundary) cases: still zero.** The cost parser's behavior right at the threshold is untested. A case at $98K (just under) and $103K (just over) would exercise the parser at the decision boundary. **Highest-priority cost-related gap.**
- **Mixed cost cases:** still 0. Cases where multiple high-dollar therapies are listed but only one is the requested item. Tests parser disambiguation.
- **Over-threshold cases now: 2** (GC-010 IN_REVIEW + GC-026 DENIED at the upper estimate). Better coverage of the high-cost handling path.

## Dimension 5 — Demographics (gender, ethnicity, SES)

| Demographic dimension | Coverage today | Notes |
|---|---|---|
| **Gender** | Not a structured field on GoldenCase. Cases mention in clinical_notes: ~17 male, ~14 female, 2 unspecified across 33 cases. | Add `patient_gender: str \| None = None` to ClinicalCase + GoldenCase. Populate from existing notes. Balance future additions. |
| **Ethnicity / race** | Not tracked anywhere | Add `patient_ethnicity: str \| None = None`. Production audit requires demographic-stratified accuracy metrics (CMS Health Equity Index 2024). |
| **Insurance type** | Not tracked anywhere | Add `insurance_type: Literal["commercial", "medicare", "medicaid", "exchange"] \| None = None`. Different policies apply. GC-028 (82yo) is implicitly Medicare; GC-031 (transplant) is plausibly Medicare-disabled; GC-033 (fertility preservation) may be commercial-mandated or state-mandated. |
| **Geography / region** | Not tracked | Less critical at MVP scale; relevant for state-specific Medicaid rules. |
| **SES proxies** (zip code, etc.) | Not tracked | PHI sensitive; only synthesize, never use real codes. |

**Gap:** Demographics are the *equity-testing* dimension. Currently impossible to claim equity testing because the data doesn't exist in the case structure. Highest-leverage non-clinical addition.

## Dimension 6 — Comorbidity coverage

| Comorbidity load | Cases |
|---|---|
| 0 stated comorbidities | GC-001, GC-002, GC-003, GC-014, GC-016, GC-020, GC-023, GC-026, GC-027, GC-030, GC-031, GC-032, GC-033 (and most others) |
| 1 stated comorbidity | GC-013 (borderline confidence + minor comorbidity hint), GC-028 (ischemic CM + prior MI), GC-029 (ADHD + SUD-in-remission + active cannabis) |
| 2+ active comorbidities | GC-024 (Crohn's + growth delay), GC-025 (AD + atopic march), GC-010 (RA + DMARD failure history) |
| Polypharmacy-driven escalation | GC-028 (GDMT regimen has 4 drugs, but case framed as routine maintenance) |
| Geriatric multi-morbidity | GC-028 (single 80+ case; further coverage needed) |

**Gap:** The complexity-score model (iter-5 chg-3) has a "+1 for comorbidities" weight that fires on keyword matches. Without graded coverage, the parser's robustness to varied phrasing is untested.

## Dimension 7 — Adversarial / failure-mode coverage

| Failure mode | Cases that probe it |
|---|---|
| Hallucination (invented lab values) | GC-018, GC-019 (sparse-notes traps) |
| False pattern-matching (memory trap) | GC-021 (PD-L1 45% near-miss), GC-022 (EGFR+ near-miss) |
| Silent reasoning degradation (5→3 slide) | iter-2 chg-2 test_CORE_catches_silent_degradation_the_aggregate_gate_misses (synthetic; not a real case) |
| Stage / guideline mismatch (test-data inconsistency) | iter-2 chg-6 repaired GC-001 (was stage IIIA vs metastatic guideline) |
| Cost-trigger escalation override | GC-010 (memory must not override cost check; iter-3 chg-1) |
| Pediatric-complexity-trigger override | GC-012 (memory must not override pediatric_complex check; iter-5 chg-4) |
| Cross-condition memory bleed | GC-005, GC-017, GC-016 (memory entries for RA / NSCLC / asthma must not over-fire on neighboring conditions) |
| Multiple anti-pattern → wrong DENIED generalization | docs/findings/H2-memory-iteration-1.md (iter-3 chg-2 GC-021 regression; fixed by wording change) |
| Patient-preference-as-justification | GC-005 (psoriasis biologic preference cited), GC-026 (proton-beam preference cited) |
| Age-only escalation (must NOT fire) | GC-028 (geriatric clean approve — must not escalate purely on age) |
| Rare-condition-prefix over-escalation | GC-030 (sickle cell — rare-prefix should note but not override clear AAA criteria) |
| Inappropriate-use ordering (workup hierarchy) | GC-027 (cardiac cath without prior non-invasive workup) |
| Controlled-substance dispensing with concurrent SUD | GC-029 (adult ADHD + active cannabis) |

**Gap:** Most failure modes have 1-2 named cases. With more cases per mode, regression detection on that specific failure class becomes stronger. The named-mode coverage is reasonable for portfolio-stage; per-class statistical signal needs more.

## Dimension 8 — Phase H1–H7 / AHE-paper component coverage

| AHE component | PACCA validation case(s) |
|---|---|
| System prompt (Phase H1) | iter-1 chg-1 byte-identity check; all 33 cases indirectly |
| Tool description | Not separately tested (PACCA uses forced-tool-use; no tool-description variants tested) |
| Tool implementation | Not separately tested |
| Middleware | Not yet implemented in PACCA |
| Skill | Not yet implemented in PACCA |
| Sub-agent | Not yet implemented in PACCA |
| Long-term memory (Phase H2) | iter-3 chg-2 NSCLC entry; iter-4 chg-1 RA entry; iter-5 chg-4 asthma entry. Risk cases: GC-001/021/022/010/005/017/016/012/023 |
| Escalation branch (PACCA-specific) | All 7 branches covered (Dimension 1) |
| RAG collection (PACCA-specific) | Not separately tested in this dataset; coverage via guidelines_context field |
| Prompt registry (PACCA-specific) | iter-1 chg-1 byte-identity check; iter-3/4/5 version bumps |
| Audit schema (PACCA-specific) | Not in golden-case scope; covered by unit tests |
| Evaluation harness (added iter-2 chg-1) | All iter-2 chgs are at this level |
| Instrumentation (added iter-2 chg-1) | iter-0 chg-0 baseline; iter-2 chg-5 model SSOT; iter-5 chg-1 tracing.py wrap |

**Gap:** PACCA hasn't yet exercised middleware, skill, or sub-agent components. AHE paper expects all to be present at maturity. iter-6+ candidates.

## Summary — per-dimension defensibility (iter-6 update)

| Dimension | Defensible claim today | Gap to next claim level |
|---|---|---|
| Outcome class | "We test approve, in-review, deny, info-needed, and pre-flight outcomes" ← upgraded from iter-5 | DENIED has 2 cases — need 5+ for "we test denials at sufficient sample size" |
| Escalation branch | "We cover all 7 branches plus the NONE branch (for denials)" | Need 3+ per branch for per-class regression detection |
| Specialty | "We test oncology (med + radiation), cardiology, RA, IBD, asthma, derm, T2DM, hematology, neurology, transplant, reproductive endocrine, mental health, orthopedics" ← substantial upgrade | Need 5+ per specialty for within-specialty signal; pulmonology adult still absent |
| Age bracket | "We test pediatric, adolescent (limited), adult, older adult, and ≥ 80 geriatric (1 case)" ← upgraded | Need 3+ geriatric for the 80+ stratum |
| Documentation completeness | "We test complete (across all outcomes), ambiguous, and sparse + hallucination traps" | Need ambiguous DENY cases; graded sparseness |
| Cost tier | "We test under-threshold + 2 over-threshold (1 IN_REVIEW, 1 DENIED)" ← upgraded | At-threshold (boundary) untested |
| Demographics | "Cases mention age and gender in notes" | No structured fields; equity claims unsupported |
| Comorbidity | "We have 3 multi-comorbidity cases plus partial coverage of geriatric polypharmacy" | Need graded coverage for parser robustness |
| Failure mode | "Every documented mode has a named case; iter-6 added 4 new modes" ← upgraded | Per-mode statistical signal weak with 1-2 cases each |
| AHE component | "System prompt, memory, escalation, evaluation, instrumentation tested" | Middleware, skill, sub-agent untested (intentionally — not yet built) |

## Re-baselining schedule

This document is re-baselined whenever the dataset crosses a threshold:
- **At 50 cases** (next milestone — 17 more cases needed): re-fill every cell; surface remaining gaps
- **At 100 cases**: add demographic dimension rows; add per-specialty regression-signal rows
- **At 300 cases**: add prevalence-weighted distribution row; add demographic stratification rows
- **At 500 cases**: add inter-rater reliability rows (Cohen's κ per case per reviewer)

---

*This document is part of the PACCA v2.3+ harness-engineering cycle documentation set. Last updated: 2026-05-25 at iter-6 open (33-case state).*
