# Evaluation Coverage Matrix

> **Companion to:** [`DATASET_SUFFICIENCY.md`](./DATASET_SUFFICIENCY.md), [`DATASET_GROWTH_ROADMAP.md`](./DATASET_GROWTH_ROADMAP.md), [`CASE_PROVENANCE.md`](./CASE_PROVENANCE.md).
> **Status:** v1.2 at iter-6 close (100-case state — production-pilot milestone hit). Re-baseline when the dataset crosses 100 / 300 / 500.

## How to read this document

Each section is a *dimension* (outcome class, escalation branch, specialty, age, etc.). Each cell shows the case IDs that cover that cell. Empty cells mark gaps explicitly. A reviewer asking "where do you test X?" finds the answer by case ID and verifies the case definition in the relevant `tests/clinical/*_cases.py` file. The per-case authoritative source is [`CASE_PROVENANCE.md`](./CASE_PROVENANCE.md).

The current dataset (100 cases across 17 lists):

| List | File | Count | IDs |
|---|---|---|---|
| GOLDEN_CASES | `golden_cases.py` | 20 | GC-001 to GC-020 |
| NEAR_MISS_CASES | `near_miss_cases.py` | 2 | GC-021, GC-022 |
| PEDIATRIC_CASES | `pediatric_cases.py` | 3 | GC-023 to GC-025 |
| EXPANSION_CASES | `expansion_cases.py` | 11 | GC-026 to GC-033, GC-073 to GC-075 |
| DENIAL_CASES | `denial_cases.py` | 3 | GC-034 to GC-036 |
| CARDIOLOGY_CASES | `cardiology_cases.py` | 4 | GC-037 to GC-040 |
| MENTAL_HEALTH_CASES | `mental_health_cases.py` | 5 | GC-041 to GC-045 |
| GERIATRIC_CASES | `geriatric_cases.py` | 4 | GC-046 to GC-049 |
| PULMONOLOGY_ADULT_CASES | `pulmonology_adult_cases.py` | 5 | GC-050 to GC-054 |
| AMBIGUOUS_COMPLETENESS_CASES | `ambiguous_completeness_cases.py` | 5 | GC-055 to GC-059 |
| TRANSPLANT_CASES | `transplant_cases.py` | 4 | GC-060 to GC-063 |
| NEUROLOGY_CASES | `neurology_cases.py` | 4 | GC-064 to GC-067 |
| OB_CASES | `ob_cases.py` | 5 | GC-068 to GC-072 |
| ENDOCRINOLOGY_CASES | `endocrinology_cases.py` | 3 | GC-076 to GC-078 |
| HEMATOLOGY_CASES | `hematology_cases.py` | 4 | GC-079 to GC-082 |
| ONCOLOGY_DEPTH_CASES | `oncology_depth_cases.py` | 6 | GC-083 to GC-088 |
| DEPTH_EXTENSION_CASES | `depth_extension_cases.py` | 12 | GC-089 to GC-100 |
| **Total live** | — | **100** | — |

### iter-6 close — milestone summary

**Production-pilot milestone reached.** Per `DATASET_GROWTH_ROADMAP.md` § 2 "Validation gates at 100-case milestone":

| Gate | Status |
|---|---|
| Case count = 100 | ✅ |
| `test_no_case_id_collisions_across_lists` passes | ✅ |
| `test_dataset_has_one_hundred_cases` passes | ✅ |
| `test_per_file_case_counts` passes | ✅ |
| Every Dimension-1 outcome class populated | ✅ (DENIED at 5 cases) |
| All 7 escalation branches + NONE covered | ✅ |
| 10 specialties at 5+ cases | ✅ (cardiology, MH, geriatric, pulm, transplant, neurology, OB, hematology, oncology, derm/GI via distributed depth) |
| Companion docs updated | ✅ (this PR) |
| SME Phase 1 review | Self-attested by author; CRB Phase 2 not yet operational (activates at 300) |
| Iteration manifest | (Pending iter-6 manifest finalization — separate commit) |
| Per-cell matrices below re-baselined | **PARTIAL** — high-level summary table updated; full per-cell matrix re-baseline deferred to the next iteration per the schedule below |

**Deferred to next iteration:** the per-cell matrices in Dimensions 1–8 below reflect the 33-case state at iter-6 open. Full re-baseline at the 100-case state is a mechanical exercise (read CASE_PROVENANCE.md's failure-mode column + case file's expected_outcome/expected_branch fields, populate cells) and is scheduled for the next iteration. The high-level summary table at the end of this document IS updated for the 100-case state.

---

## (The Dimension-1 through Dimension-8 matrices below reflect the 33-case state — see "iter-6 close" note above)

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

## Summary — per-dimension defensibility (iter-6 close, 100-case state)

| Dimension | Defensible claim today | Gap to next claim level |
|---|---|---|
| Outcome class | "We test all 5 outcomes; DENIED at 5 cases meets minimum sample size" ← upgraded | DENIED at ambiguous + sparse completeness tiers still missing (1-2 each, 300-case roadmap) |
| Escalation branch | "All 7 branches + NONE at ≥ 3 cases each" ← upgraded | (Sufficient for 100-milestone; 5+ per branch at 300) |
| Specialty | "14+ specialties at 1+ case; 10 specialties at 5+ cases" ← substantial upgrade | Adult pulmonology, mental health, transplant, neurology, OB, hematology now covered at depth |
| Age bracket | "Pediatric (8), adolescent (5), adult (60+), older adult (15+), 80+ (5)" ← upgraded | 80+ at 5 cases meets minimum |
| Documentation completeness | "Complete (most), ambiguous tier (5 cases new), sparse + hallucination traps (2)" ← upgraded | Graded sparseness across more specialties (300-case roadmap) |
| Cost tier | "Under-threshold + at-threshold-just-under + at-threshold-just-over + mixed-cost-parser-disambiguation + over-threshold IN_REVIEW + over-threshold DENIED" ← upgraded substantially | (Sufficient for 100-milestone) |
| Demographics | "Cases mention age and gender in notes; structured fields still absent" | Schema change required for equity claims (300-case roadmap) |
| Comorbidity | "Multi-comorbidity, geriatric polypharmacy, behavioral comorbidity all represented" ← upgraded | Graded coverage for parser robustness still iter-on-iter improvement |
| Failure mode | "Every documented mode has 1–5 named cases; 8 new modes added at iter-6" ← upgraded | Per-mode 3+ cases each becomes attainable at 300 |
| AHE component | "H1, H2, H4, H5 tested; PACCA-specific extensions tested" | H3 (sub-agent), H6 (skill), H7 (middleware) — intentionally not yet built |

## Re-baselining schedule

This document is re-baselined whenever the dataset crosses a threshold:
- **At 100 cases** (current — full per-cell re-baseline DEFERRED to next iteration; high-level summary updated): add demographic dimension rows; add per-specialty regression-signal rows
- **At 300 cases**: add prevalence-weighted distribution row; add demographic stratification rows
- **At 500 cases**: add inter-rater reliability rows (Cohen's κ per case per reviewer)

---

*This document is part of the PACCA v2.4+ harness-engineering cycle documentation set. Last updated: 2026-05-25 at iter-6 close (100-case state). Per-cell matrix re-baseline deferred to next iteration.*
