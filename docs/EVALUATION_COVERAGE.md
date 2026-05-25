# Evaluation Coverage Matrix

> **Companion to:** [`DATASET_SUFFICIENCY.md`](./DATASET_SUFFICIENCY.md) — this document grounds the coverage claims at the per-cell level.
> **Status:** v1.0 at iter-5 close (25-case state). Re-baseline when the dataset crosses 50 / 100 / 300 / 500.

## How to read this document

Each section is a *dimension* (outcome class, escalation branch, specialty, age, etc.). Each cell shows the case IDs that cover that cell. Empty cells mark gaps explicitly. A reviewer asking "where do you test X?" finds the answer by case ID and can verify the case definition in [`tests/clinical/golden_cases.py`](../tests/clinical/golden_cases.py), [`tests/clinical/near_miss_cases.py`](../tests/clinical/near_miss_cases.py), or [`tests/clinical/pediatric_cases.py`](../tests/clinical/pediatric_cases.py).

The current dataset:
- **GOLDEN_CASES:** 20 (GC-001 through GC-020)
- **NEAR_MISS_CASES:** 2 (GC-021, GC-022)
- **PEDIATRIC_CASES:** 3 (GC-023, GC-024, GC-025)
- **Total live:** 25

## Dimension 1 — Outcome class × Expected branch

| Outcome class \\ Branch | branch_1_high_confidence (auto-approve) | branch_2_medical_director | branch_3_low_confidence | branch_4_experimental | branch_5_rare | branch_6_conflicting | branch_7_prior_denial |
|---|---|---|---|---|---|---|---|
| **AUTO_APPROVED** | GC-001, GC-002, GC-003, GC-014, GC-016, GC-020, GC-023 | — | — | — | — | — | — |
| **IN_REVIEW** | — | GC-010, GC-012, GC-024, GC-025 | GC-004, GC-005, GC-013, GC-015, GC-017, GC-021, GC-022 | — | — | — | — |
| **PRE_FLIGHT_ESCALATE** | — | — | — | GC-006, GC-009 | GC-007 | GC-011 | GC-008 |
| **DENIED** | — | — | — | — | — | — | — |
| **INFORMATION_NEEDED** | — | — | GC-018, GC-019 | — | — | — | — |

**Gaps surfaced:**
- **DENIED row is entirely empty.** Zero current cases expect a clear deny outcome. Highest-priority gap per [`DATASET_SUFFICIENCY.md`](./DATASET_SUFFICIENCY.md) §5.
- **AUTO_APPROVED × branch_2_medical_director is empty by design** — these branches are mutually exclusive by policy.
- branch_4–7 each have 1–2 cases (the integrity test enforces ≥1).
- branch_3 is over-represented (7 cases) because confidence-low / ambiguous is the default escalation path.

## Dimension 2 — Age bracket × Disease specialty

| Specialty \\ Age | <12 | 12–17 | 18–64 | 65–79 | 80+ |
|---|---|---|---|---|---|
| Oncology | GC-025 (atopic derm; pediatric not strictly oncology) | — | GC-001 (NSCLC), GC-008 (NSCLC denied), GC-009 (oncology Phase II), GC-020 (oncological emergency), GC-021 (NSCLC near-miss), GC-022 (NSCLC near-miss) | GC-011 (conflicting), GC-015 (incomplete) | — |
| Rheumatology / immunology | — | — | GC-010 (RA biologic high cost), GC-017 (PsA biologic) | — | — |
| Pulmonology / asthma | — | GC-012 (pediatric severe asthma) | — | — | — |
| GI / IBD | — | GC-024 (pediatric moderate Crohn's) | GC-016 (Crohn's biologic) | — | — |
| Endocrinology | — | — | GC-003 (T2DM SGLT2) | — | — |
| Cardiology | — | — | — | — | — |
| Mental health / psych | — | — | — | — | — |
| Orthopedics / imaging | — | — | GC-002 (lumbar MRI complete), GC-004 (lumbar MRI premature) | — | — |
| Dermatology | GC-023 (pediatric mild asthma; arguably pulm), GC-025 (severe AD) | — | GC-005 (psoriasis step therapy not met) | — | — |
| Hematology / oncology rare | — | GC-006 (CAR-T at 19yo — boundary case) | GC-007 (Gaucher) | — | — |
| Neurology | — | — | — | — | — |
| OB/GYN | — | — | — | — | — |
| Transplant | — | — | — | — | — |
| Confidence-boundary (non-specialty-specific) | — | — | GC-013 (borderline docs) | — | — |

**Gaps surfaced:**
- **Cardiology: zero cases** at any age. ~10% of UM volume; priority #2 per DATASET_SUFFICIENCY.
- **Mental health: zero cases** at any age. ~8% of UM volume.
- **OB/GYN: zero cases.** Pregnancy-related authorization is a major UM category.
- **Transplant: zero cases.** Solid-organ + bone-marrow transplant PA is high-stakes and high-cost.
- **Neurology: zero cases.** MS, ALS, neurodegenerative disease biologics.
- **80+ age bracket: zero cases.** The complexity-score model's `age > 75` weight is untested.
- **Pulmonology adult: zero cases.** GC-012 (pediatric) is the only asthma case.

## Dimension 3 — Outcome × Documentation completeness

| Completeness \\ Outcome | AUTO_APPROVED | IN_REVIEW | DENIED | INFORMATION_NEEDED | PRE_FLIGHT_ESCALATE |
|---|---|---|---|---|---|
| Complete (all fields explicitly documented) | GC-001, GC-002, GC-003, GC-014, GC-016, GC-020, GC-023 | GC-010, GC-012, GC-017, GC-024, GC-025 | — | — | GC-006, GC-007, GC-009, GC-011 |
| Ambiguous (some fields incomplete) | — | GC-004, GC-005, GC-013, GC-015, GC-021, GC-022 | — | — | — |
| Sparse (substantial gaps, requires INFO_NEEDED or escalation) | — | — | — | GC-018, GC-019 | GC-008 |

**Gaps surfaced:**
- **DENIED × any completeness tier: empty.** Same gap as Dimension 1.
- **Sparse documentation: only 2 cases** (hallucination traps). Need graded completeness — e.g., missing one lab value, missing dose duration, missing prior-therapy details — beyond the extreme sparse-notes traps.
- **Ambiguous AUTO_APPROVED: zero cases.** Real-world auto-approves often have minor ambiguity that the agent must reason past.

## Dimension 4 — Cost tier × Escalation outcome

| Cost tier \\ Outcome | AUTO_APPROVED | IN_REVIEW via cost | IN_REVIEW via other | Not annotated for cost |
|---|---|---|---|---|
| Under threshold (<$100K/year) | GC-001, GC-002, GC-003, GC-004, GC-005, GC-013, GC-014, GC-015, GC-016, GC-017, GC-018, GC-019, GC-020, GC-023 | — | GC-012, GC-024, GC-025 | GC-006, GC-007, GC-008, GC-009, GC-011 |
| At threshold ($95K–$105K/year) | — | — | — | — |
| Over threshold (>$100K/year) | — | GC-010 ($288K abatacept) | — | — |

**Gaps surfaced:**
- **At-threshold (boundary) cases: zero.** The cost parser's behavior right at the threshold is untested. A case at $98K (just under) and $103K (just over) would exercise the parser at the decision boundary.
- **Mixed cost cases.** Cases where multiple high-dollar therapies are listed but only one is the requested item. Tests parser disambiguation.

## Dimension 5 — Demographics (gender, ethnicity, SES)

| Demographic dimension | Coverage today | Notes |
|---|---|---|
| **Gender** | Not a structured field on GoldenCase. Cases mention in clinical_notes: 14 male, 8 female, 3 unspecified. | Add `patient_gender: str \| None = None` to ClinicalCase + GoldenCase. Populate from existing notes. Balance future additions. |
| **Ethnicity / race** | Not tracked anywhere | Add `patient_ethnicity: str \| None = None`. Production audit requires demographic-stratified accuracy metrics (CMS Health Equity Index 2024). |
| **Insurance type** | Not tracked anywhere | Add `insurance_type: Literal["commercial", "medicare", "medicaid", "exchange"] \| None = None`. Different policies apply. |
| **Geography / region** | Not tracked | Less critical at MVP scale; relevant for state-specific Medicaid rules. |
| **SES proxies** (zip code, etc.) | Not tracked | PHI sensitive; only synthesize, never use real codes. |

**Gap:** Demographics are the *equity-testing* dimension. Currently impossible to claim equity testing because the data doesn't exist in the case structure. Highest-leverage non-clinical addition.

## Dimension 6 — Comorbidity coverage

| Comorbidity load | Cases |
|---|---|
| 0 stated comorbidities | GC-001, GC-002, GC-003, GC-014, GC-016, GC-020 (and most others) |
| 1 stated comorbidity | GC-013 (borderline confidence + minor comorbidity hint) |
| 2+ active comorbidities | GC-024 (Crohn's + growth delay), GC-025 (AD + atopic march), GC-010 (RA + DMARD failure history) |
| Polypharmacy-driven escalation | — (gap) |
| Geriatric multi-morbidity | — (gap; no 80+ cases at all) |

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

**Gap:** Most failure modes have 1-2 named cases. With more cases per mode, regression detection on that specific failure class becomes stronger. The named-mode coverage is reasonable for portfolio-stage; per-class statistical signal needs more.

## Dimension 8 — Phase H1–H7 / AHE-paper component coverage

| AHE component | PACCA validation case(s) |
|---|---|
| System prompt (Phase H1) | iter-1 chg-1 byte-identity check; all 20 GOLDEN_CASES indirectly |
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

## Summary — per-dimension defensibility

| Dimension | Defensible claim today | Gap to next claim level |
|---|---|---|
| Outcome class | "We test approve, in-review, info-needed, and pre-flight outcomes" | DENIED is empty — need 5 cases for "we test all outcomes" |
| Escalation branch | "We cover all 7 branches" | Need 3+ per branch for per-class regression detection |
| Specialty | "We test oncology, RA, IBD, asthma, derm, T2DM, lumbar MRI" | Cardiology / mental health / OB / transplant / neuro absent |
| Age bracket | "We test pediatric, adult, older adult" | 80+ untested; adolescent 12-17 minimal |
| Documentation completeness | "We test complete + sparse + hallucination traps" | Ambiguous tier underrepresented; need graded sparseness |
| Cost tier | "We test under-threshold + 1 over-threshold" | At-threshold (boundary) untested; only 1 over-threshold case |
| Demographics | "Cases mention age and gender in notes" | No structured fields; equity claims unsupported |
| Comorbidity | "We have 3 multi-comorbidity cases" | Need graded coverage for parser robustness |
| Failure mode | "Every documented mode has a named case" | Per-mode statistical signal weak with 1-2 cases each |
| AHE component | "System prompt, memory, escalation, evaluation, instrumentation tested" | Middleware, skill, sub-agent untested (intentionally — not yet built) |

## Re-baselining schedule

This document is re-baselined whenever the dataset crosses a threshold:
- **At 50 cases** (next milestone): re-fill every cell; surface remaining gaps
- **At 100 cases**: add demographic dimension rows; add per-specialty regression-signal rows
- **At 300 cases**: add prevalence-weighted distribution row; add demographic stratification rows
- **At 500 cases**: add inter-rater reliability rows (Cohen's κ per case per reviewer)

---

*This document is part of the PACCA v2.3 harness-engineering cycle documentation set. Last updated: 2026-05-25 at iter-5 close.*
