# Dataset Growth Roadmap — Building and Validating Toward 100, 300, and 500 Cases

> **Companion to:** [`DATASET_SUFFICIENCY.md`](./DATASET_SUFFICIENCY.md), [`EVALUATION_COVERAGE.md`](./EVALUATION_COVERAGE.md), [`STATISTICAL_POWER.md`](./STATISTICAL_POWER.md), [`CASE_PROVENANCE.md`](./CASE_PROVENANCE.md), [`CASE_AUTHORING_GUIDE.md`](./CASE_AUTHORING_GUIDE.md), [`PACCA_PRD_v2.5_Consolidated.md`](./PACCA_PRD_v2.5_Consolidated.md) §16.
> **Audience:** maintainer + future contributors + SaMD reviewers asking "show me your plan."
> **Status:** v1.0, drafted 2026-05-25 at iter-6 mid (33-case state with 67 cases queued to reach 100).

## Purpose

`DATASET_SUFFICIENCY.md` answers *what claims the dataset can support*. `EVALUATION_COVERAGE.md` answers *what cells are filled*. This document answers the operational question those leave open: **how do you actually grow the dataset, batch by batch, in a way that meets the validation criteria at each milestone?**

Specifically, this document:

1. Defines a **case-batch methodology** — what a batch is, how to compose it, how to validate it, and what counts as exit-criteria met.
2. Enumerates the **specific case batches** (with IDs A–L for the 100-case milestone, M–Z for the 300-case milestone, AA–ZZ for 500+) and what each batch contributes.
3. Specifies the **per-milestone validation gates** — the tests and metrics that must pass before declaring the milestone met.
4. Provides **effort estimates and SME-time budgets** per milestone.
5. Records a **risk register** for the dataset-growth work.

## §1 — The case-batch methodology

A **batch** is a coherent group of 3–10 cases that shares a single named purpose. Examples:
- **Batch A — DENY expansion** (close the DENY-class statistical gap from 2 to 5)
- **Batch B — Cardiology depth** (close the within-specialty signal gap)
- **Batch G — Ambiguous-completeness graded sparseness** (close the documentation-tier coverage gap)

Each batch follows the same workflow:

```
1. STATE THE GAP.        Reference EVALUATION_COVERAGE.md cell or
                         DATASET_SUFFICIENCY.md claim level.
2. COMPOSE THE BATCH.    List the case IDs, outcomes, branches,
                         specialties, and named failure modes.
3. AUTHOR THE CASES.     Follow CASE_AUTHORING_GUIDE.md template.
                         PHI-free; cite real guidelines.
4. WIRE INTO HARNESS.    Add to test_clinical_accuracy.py
                         aggregator. Add per-list count assertion.
5. SME REVIEW (Phase 1). Per-case clinical concurrence.
6. CAPTURE BASELINE.     `python -m tests.clinical.capture_baseline
                         --rollouts 2` (once iter-6 fix lands so
                         supplementary lists are included).
7. UPDATE COMPANION DOCS. PROVENANCE row per case, COVERAGE matrix
                         cell updates, SUFFICIENCY count bump.
8. COMMIT + PR.          One PR per batch (or 2–3 batches if small).
9. VERIFY GATES.         Per-case regression gate green; aggregate
                         ≥ 80%; CI green.
10. EXIT CRITERIA.       Batch is "done" when the gap it targeted
                         is closed per the COVERAGE matrix.
```

### Per-batch quality checklist

A batch is **not done** until each case in it satisfies:

- [ ] Synthetic data only (PHI rule per `CASE_AUTHORING_GUIDE.md` § 4)
- [ ] Cites a real, currently-published clinical guideline body
- [ ] Has a defensible `expected_outcome` + `expected_branch` per the SME
- [ ] Has 1+ `reasoning_must_include` keyword
- [ ] Has 0+ `reasoning_must_not_include` if testing hallucination/anti-pattern
- [ ] Has a 2–5 sentence `clinical_rationale`
- [ ] Has explicit `judge_scoring_criteria` (not the generic fallback rubric)
- [ ] Has a row in `CASE_PROVENANCE.md`
- [ ] Has cell updates in the relevant `EVALUATION_COVERAGE.md` matrices
- [ ] Has an `__all__` export (or is in a list that's already imported by the test aggregator)

### Batch sizing

| Batch size | When to use | Pros | Cons |
|---|---|---|---|
| 3 cases | Closing a single specific gap (e.g., "at-threshold cost boundary") | Atomic; easy review | Doesn't justify a new file (per authoring guide § 9) |
| 5 cases | Standard. Closes a coherent gap with margin. | Justifies own file; coherent purpose | Standard PR size |
| 10 cases | Deep coverage of one specialty (e.g., cardiology at 100-case milestone) | Within-specialty signal; per-class detection | Larger review; SME bandwidth higher |
| 25+ cases | Avoid. Splits should happen at this size. | None. | Reviewer fatigue; correlated failures across batch |

## §2 — The 100-case milestone (next 67 cases)

The 100-case milestone unlocks (per `DATASET_SUFFICIENCY.md` claims table):

- Claim 3: "We catch aggregate accuracy drops of ≥ 10% with 80% power" (FDA SaMD "clinically meaningful" threshold)
- Claim 4 (partial): "Per-case regression detection on every reasoning class" — for the 8–10 classes that now have 3+ cases
- The "production-pilot for narrow scope" defensibility (single payer, single specialty)

### Composition target at 100

| Dimension | Target at 100 | Current at 33 | Add via batches below |
|---|---|---|---|
| DENY-class cases | 5+ | 2 (GC-026, GC-027) | Batch A (3 cases) |
| Cardiology cases | 5+ | 2 (GC-027, GC-028) | Batch B (4 cases) |
| Mental health cases | 5+ | 1 (GC-029) | Batch C (5 cases) |
| Geriatric (≥80) cases | 5+ | 1 (GC-028) | Batch D (4 cases) |
| Adult pulmonology cases | 5+ | 0 | Batch E (5 cases) |
| At-threshold cost-boundary cases | 3+ | 0 | Batch F (3 cases) |
| Ambiguous-completeness cases | 5+ | 0 | Batch G (5 cases) |
| Transplant cases | 5+ | 1 (GC-031) | Batch H (4 cases) |
| Neurology cases | 5+ | 1 (GC-032) | Batch I (4 cases) |
| OB / reproductive / pregnancy cases | 5+ | 1 (GC-033) | Batch J (5 cases) |
| Endocrine depth (beyond T2DM) | 4+ | 1 (GC-003) | Batch K (3 cases) |
| Hematology depth | 5+ | 1 (GC-030) | Batch L (4 cases) |
| Adolescent (12–17) cases | 5+ | 2 (GC-012, GC-024) | Distributed across above |
| Imaging / orthopedic depth | 5+ | 2 (GC-002, GC-004) | Distributed across above |
| Dermatology depth | 5+ | 2 (GC-005, GC-025) | Distributed across above |
| GI / IBD depth | 5+ | 2 (GC-016, GC-024) | Distributed across above |
| Rheumatology depth | 5+ | 2 (GC-010, GC-017) | (Sufficient at 100) |
| Sparse-documentation graded | 5+ | 2 (GC-018, GC-019) | Batch G partial |

**Sum:** 53 net new cases across Batches A–L. Plus 14 cases distributed for adolescent / imaging / derm / GI depth = **67 total to reach 100**.

### The 12 batches

#### Batch A — DENY expansion (3 cases) — IDs GC-034 to GC-036
**File:** `tests/clinical/denial_cases.py` (new)
- GC-034: Off-label oncology biologic without compendia support (NCCN says no)
- GC-035: PT visits exceeding annual benefit cap (frequency-cap denial)
- GC-036: Re-request after prior denial without new clinical evidence (prior-denial-without-change)

**Why these three.** Covers the three most common production deny categories beyond GC-026 (guideline-not-met-with-preference-only) and GC-027 (workup-hierarchy violation): off-label, benefit-cap, prior-denial-without-change.

#### Batch B — Cardiology depth (4 cases) — IDs GC-037 to GC-040
**File:** `tests/clinical/cardiology_cases.py` (new)
- GC-037: TAVR for severe symptomatic AS (clean approve per ACC/AHA)
- GC-038: AFib catheter ablation after failed AAD (clean approve)
- GC-039: ICD primary prevention with LVEF=36% (denied — below CMS 35% threshold)
- GC-040: Statin primary prevention in 38yo with familial hypercholesterolemia (clean approve)

**Why these four.** Plus GC-027 (DENY) and GC-028 (geriatric ICD), cardiology reaches 6 cases covering: interventional (TAVR), electrophysiology (ablation, ICD threshold-boundary), primary prevention. The ICD case at LVEF 36% is a near-miss to GC-028's LVEF 28% — exercises threshold discrimination.

#### Batch C — Mental health depth (5 cases) — IDs GC-041 to GC-045
**File:** `tests/clinical/mental_health_cases.py` (new)
- GC-041: TMS for treatment-resistant depression after 2 antidepressant failures (clean approve per APA)
- GC-042: Esketamine intranasal for TRD (IN_REVIEW — REMS + specialist)
- GC-043: Inpatient psychiatric admission for active SI with plan (auto-approve per CMS LOC criteria)
- GC-044: Long-acting injectable antipsychotic for schizophrenia + non-adherence (clean approve)
- GC-045: Adolescent (16yo) MDD SSRI (IN_REVIEW — black box + suicidality monitoring)

**Why these five.** Plus GC-029 (adult ADHD+SUD), mental health reaches 6 cases covering: TRD, REMS-requiring therapies, level-of-care decisions, schizophrenia maintenance, pediatric psychopharm.

#### Batch D — Geriatric ≥80 depth (4 cases) — IDs GC-046 to GC-049
**File:** `tests/clinical/geriatric_cases.py` (new)
- GC-046: 85yo cataract surgery (clean approve per AAO)
- GC-047: 88yo adjuvant chemo for early-stage colon cancer (IN_REVIEW — frailty assessment needed)
- GC-048: 82yo elective hip arthroplasty (clean approve per AAOS)
- GC-049: 84yo dialysis initiation for ESRD (IN_REVIEW — shared decision-making + goals-of-care)

**Why these four.** Plus GC-028 (cardiology ICD geriatric), the geriatric stratum reaches 5 cases covering: ophthalmologic, oncology with frailty, orthopedic elective, renal replacement decisions. Tests the complexity-score model's "age > 75" weight across different specialties.

#### Batch E — Adult pulmonology (5 cases) — IDs GC-050 to GC-054
**File:** `tests/clinical/pulmonology_adult_cases.py` (new)
- GC-050: Adult severe eosinophilic asthma dupilumab (clean approve per GINA + EMA label)
- GC-051: COPD escalation to triple therapy (LABA/LAMA/ICS) after exacerbation (clean approve per GOLD)
- GC-052: Pulmonary rehabilitation post-exacerbation (auto-approve per ATS)
- GC-053: CPAP initiation post-AASM-conformant sleep study (auto-approve)
- GC-054: Mepolizumab in adult severe asthma (clean approve — different biologic class from GC-050)

**Why these five.** Adult pulm was the largest specialty gap (zero coverage). Five cases give within-specialty signal across asthma biologics, COPD, OSA, pulm rehab. GC-050 vs GC-054 tests parallel-biologic-different-class discrimination.

#### Batch F — At-threshold cost-boundary (3 cases) — IDs GC-055 to GC-057
**File:** extend `tests/clinical/expansion_cases.py`
- GC-055: Therapy at $99,500/year (just under $100K) — clean approve, cost-trigger does NOT fire
- GC-056: Therapy at $100,500/year (just over) — IN_REVIEW via cost
- GC-057: Mixed-cost case ($45K for requested + $250K for unrelated mention in notes) — clean approve, parser must extract correct cost

**Why these three.** The cost parser at the threshold is currently untested. These three exercise the boundary at $99.5K, $100.5K, and the parser-disambiguation case.

#### Batch G — Ambiguous-completeness (5 cases) — IDs GC-058 to GC-062
**File:** `tests/clinical/ambiguous_completeness_cases.py` (new)
- GC-058: Adult psoriasis biologic with prior therapy listed but duration omitted — IN_REVIEW
- GC-059: Adult MS DMT with severity language present but specific EDSS score omitted — IN_REVIEW
- GC-060: T2DM intensification with HbA1c noted but date of measurement omitted — IN_REVIEW
- GC-061: Oncology second-line with prior regimen named but response not characterized — IN_REVIEW
- GC-062: Migraine CGRP with "previously tried other preventives" without naming them — IN_REVIEW

**Why these five.** Adds the missing ambiguous tier across 5 specialties. Each case has one specific data gap that would prevent automatic decisioning — tests the agent's recognition that missing data ≠ insufficient evidence to deny.

#### Batch H — Transplant depth (4 cases) — IDs GC-063 to GC-066
**File:** `tests/clinical/transplant_cases.py` (new)
- GC-063: Heart transplant tacrolimus initiation post-op (clean approve)
- GC-064: Pediatric (8yo) liver transplant immunosuppression refill (IN_REVIEW — pediatric + transplant)
- GC-065: Allogeneic bone marrow transplant conditioning regimen (IN_REVIEW per ASTCT — institutional protocol review)
- GC-066: Renal transplant rejection treatment with high-dose steroids (clean approve per KDIGO)

**Why these four.** Plus GC-031 (renal maintenance), transplant reaches 5 cases across organ types (heart, liver, BMT, renal) and care phases (initiation, maintenance, rejection treatment, pediatric).

#### Batch I — Neurology depth (4 cases) — IDs GC-067 to GC-070
**File:** `tests/clinical/neurology_cases.py` (new)
- GC-067: Ocrelizumab for relapsing MS (clean approve per AAN/MS Society)
- GC-068: Lecanemab for early Alzheimer's (IN_REVIEW per FDA REMS + MRI monitoring)
- GC-069: VNS for refractory focal epilepsy after AED failures (IN_REVIEW per AAN)
- GC-070: IV thrombolysis for acute ischemic stroke within window (auto-approve, urgent)

**Why these four.** Plus GC-032 (chronic migraine CGRP), neurology reaches 5 cases covering: MS DMT, novel Alzheimer's, epilepsy device, acute stroke (urgent-care expedited).

#### Batch J — OB / reproductive (5 cases) — IDs GC-071 to GC-075
**File:** `tests/clinical/ob_cases.py` (new)
- GC-071: First-trimester ultrasound (auto-approve per ACOG)
- GC-072: NIPT cell-free DNA screening in 38yo gravida (auto-approve per ACOG/SMFM)
- GC-073: Postpartum depression brexanolone IV infusion (IN_REVIEW per REMS)
- GC-074: Gestational diabetes insulin initiation after diet failure (clean approve per ACOG)
- GC-075: Tubal ligation post-partum (clean approve — Medicaid 30-day rule applies, documented)

**Why these five.** Plus GC-033 (fertility preservation pre-chemo), OB reaches 6 cases across: routine prenatal, prenatal screening, postpartum, gestational complication, sterilization.

#### Batch K — Endocrine depth (3 cases) — IDs GC-076 to GC-078
**File:** extend `tests/clinical/expansion_cases.py`
- GC-076: Adult thyroid cancer RAI ablation (clean approve per ATA)
- GC-077: Cushing's syndrome workup MRI (IN_REVIEW — sequential workup required)
- GC-078: Pheochromocytoma adrenalectomy (clean approve per Endo Society)

**Why these three.** Plus GC-003 (T2DM SGLT2), endocrine reaches 4 cases covering: T2DM, thyroid oncology, adrenal workup, adrenal surgery.

#### Batch L — Hematology depth (4 cases) — IDs GC-079 to GC-082
**File:** extend `tests/clinical/expansion_cases.py` or new `hematology_cases.py`
- GC-079: IV iron sucrose for severe iron-deficiency anemia after PO failure (clean approve per AGA/ASH)
- GC-080: AML 7+3 induction chemotherapy (auto-approve per NCCN)
- GC-081: ITP rituximab after steroid failure (clean approve per ASH 2019)
- GC-082: Anticoagulation reversal with PCC for warfarin-associated bleed (auto-approve, urgent)

**Why these four.** Plus GC-030 (sickle cell), hematology reaches 5 cases covering: anemia, leukemia induction, ITP biologic, urgent reversal.

### Distributed depth — Batches M to P (within-specialty depth distributed across existing files)

These don't create new files; they extend specialty depth in existing files.

- **Batch M — Adolescent depth (3 cases — distributed):** Add to existing pediatric, mental_health, or OB files: adolescent IBD, adolescent depression with school refusal, adolescent contraception. Brings adolescent (12-17) stratum from 2 to 5.
- **Batch N — Imaging depth (3 cases — extend expansion):** Knee MRI per OARSI, shoulder MRI rotator cuff, CT pulmonary angiogram for PE workup. Brings imaging from 2 to 5.
- **Batch O — Dermatology depth (3 cases — extend expansion):** Hidradenitis suppurativa adalimumab per AAD, vitiligo ruxolitinib (newer indication IN_REVIEW), severe nodular acne isotretinoin per iPLEDGE. Brings derm from 2 to 5.
- **Batch P — GI depth (3 cases — extend expansion):** Ulcerative colitis vedolizumab, eosinophilic esophagitis dupilumab IN_REVIEW, achalasia Heller myotomy. Brings GI from 2 to 5.

**Sum of M–P:** 12 cases. Plus Batches A–L (55 cases) = **67 cases to reach 100**.

### Validation gates at 100-case milestone

The dataset is **declared at 100** when:

1. ✅ Case count: `len(GOLDEN_CASES + NEAR_MISS + PEDIATRIC + EXPANSION + DENIAL + CARDIOLOGY + MENTAL_HEALTH + GERIATRIC + PULMONOLOGY_ADULT + AMBIGUOUS + TRANSPLANT + NEUROLOGY + OB) == 100`
2. ✅ Integrity tests: `test_no_case_id_collisions_across_lists` passes; per-file count assertions pass.
3. ✅ Aggregate accuracy: `pytest -m clinical` produces ≥ 95% pass rate.
4. ✅ Per-case regression gate: no case scores below its captured baseline by > 1 point.
5. ✅ Coverage matrix: every Dimension 1 row populated (DENIED ≥ 5; all branches ≥ 3).
6. ✅ SME review (Phase 1): every new case has a "clinical-review: approved" record in the PR (author-self-attestation acceptable in absence of credentialed external SME, per `CASE_AUTHORING_GUIDE.md` § 11).
7. ✅ Companion docs updated: `CASE_PROVENANCE.md` has 100 rows; `EVALUATION_COVERAGE.md` re-baselined; `DATASET_SUFFICIENCY.md` § "Where PACCA is today" updated.
8. ✅ PRD bumped: `PACCA_PRD_v2.5_Consolidated.md` drafted with the new state.
9. ✅ Iteration manifest: `harness/manifests/iter-{N}.json` records the dataset-growth iteration with predicted_fix + risk_cases + verdict.

### Metrics to report at 100

| Metric | Target | Reported in |
|---|---|---|
| Total cases | 100 | DATASET_SUFFICIENCY.md |
| Cases per outcome class | DENY ≥ 5, IN_REVIEW ≥ 25, AUTO_APPROVED ≥ 50 | EVALUATION_COVERAGE.md Dim 1 |
| Cases per escalation branch | ≥ 3 per branch (1–7); ≥ 5 in NONE | EVALUATION_COVERAGE.md Dim 1 |
| Cases per major specialty | ≥ 5 in oncology, cardiology, rheum, IBD, asthma, derm, MH, neurology, transplant, OB | EVALUATION_COVERAGE.md Dim 2 |
| Cases per age stratum | <12: 3+, 12–17: 5+, 18–64: 60+, 65–79: 10+, 80+: 5+ | EVALUATION_COVERAGE.md Dim 2 |
| Aggregate pass rate | ≥ 95% | clinical CI gate |
| Per-case noise floor | ±1 score variance at k=2 rollouts | STATISTICAL_POWER.md |
| Per-case false-positive rate | < 5% with noise_threshold=1 | regression_gate.py + judge variance |
| 10pp aggregate-drop detection power | 0.80 | STATISTICAL_POWER.md table |

## §3 — The 300-case milestone (cases 101 to 300)

The 300-case milestone unlocks:
- Claim 5: "We catch aggregate accuracy drops of ≥ 5% (subtle silent erosion)"
- Claim 6: "Statistically powered for general payer deployment with population-representative case mix"
- The "production deployment with clinical-SME-in-the-loop" defensibility

### Composition strategy: prevalence-weighted

Unlike the 100-case milestone (which closes specific coverage gaps), the 300-case milestone is **prevalence-weighted** — the distribution mirrors a typical commercial-payer claim mix.

| Specialty | Target % at 300 | Cases at 300 |
|---|---|---|
| Oncology (incl. biologics + radiation) | 25% | 75 |
| Rheumatology / immunology | 12% | 36 |
| Pulmonology (asthma + COPD + sleep) | 10% | 30 |
| Endocrinology (T2DM + thyroid + adrenal + bone) | 10% | 30 |
| Cardiology | 10% | 30 |
| Mental health / behavioral | 8% | 24 |
| GI / IBD | 8% | 24 |
| Orthopedics / imaging | 7% | 21 |
| Dermatology | 5% | 15 |
| Neurology | 3% | 9 |
| Other (transplant, OB, hematology, rare-disease) | 2% | 6 |
| **Total** | **100%** | **300** |

### The 14 batches for 100 → 300 (Batches M through Z)

- **Batch M — Oncology depth pass 1 (15 cases):** specialty-specific subtypes (multiple myeloma, ovarian, head-and-neck, GI cancers, melanoma, prostate beyond GC-026)
- **Batch N — Rheumatology depth pass 1 (12 cases):** SLE, vasculitis, AS, PsA depth, scleroderma, pediatric rheum
- **Batch O — Pulmonology depth pass 1 (10 cases):** severe asthma biologic class diversity, COPD severity stratification, ILD, sleep apnea variants
- **Batch P — Endocrinology depth pass 1 (10 cases):** T1DM, GLP-1 agonists, growth hormone, osteoporosis
- **Batch Q — Cardiology depth pass 1 (10 cases):** valvular, congenital, advanced HF (LVAD), preventive
- **Batch R — Mental health depth pass 1 (10 cases):** substance use treatment, eating disorders, OCD, PTSD
- **Batch S — GI depth pass 1 (10 cases):** UC severity stratification, CD complications, hepatitis biologics, EoE depth
- **Batch T — Orthopedic depth pass 1 (10 cases):** spinal, joint replacement, sports medicine, pediatric ortho
- **Batch U — Imaging depth pass 1 (10 cases):** advanced imaging (PET, cardiac MRI), screening protocols, urgent imaging
- **Batch V — Dermatology depth pass 1 (8 cases):** biologic class diversity, pediatric derm, skin cancer
- **Batch W — Neurology depth pass 1 (5 cases):** Parkinson's, ALS, dementia subtypes
- **Batch X — Demographic balance pass (20 cases):** redistributed across above to balance gender (≥40% each), age (>=20% in each adult bracket), insurance-type (mark Medicare/Medicaid/commercial/exchange). Requires schema change to GoldenCase.
- **Batch Y — Equity-stratified edge cases (15 cases):** cases that probe gender-specific care, race-specific dosing (e.g., warfarin in Asian populations, HLA-B*5701 in HIV), Medicaid-specific coverage rules
- **Batch Z — Rare-disease and specialty extensions (15 cases):** rare cancers, lysosomal storage diseases, primary immunodeficiencies, hemophilia, gene therapy edge cases

**Sum of M–Z:** 160 cases. Plus the 100 from milestone 1 + 40 distributed depth = 300.

### New file structure expected at 300

```
tests/clinical/
├── golden_cases.py           (20 — canonical, unchanged)
├── near_miss_cases.py        (5–10 — extended)
├── pediatric_cases.py        (15–20)
├── expansion_cases.py        (deprecated; cases migrated to thematic files)
├── denial_cases.py           (10–15)
├── cardiology_cases.py       (25–30)
├── mental_health_cases.py    (20–25)
├── geriatric_cases.py        (10–15)
├── pulmonology_cases.py      (25–30, renamed from pulmonology_adult)
├── ambiguous_completeness_cases.py (10–15)
├── transplant_cases.py       (10)
├── neurology_cases.py        (8–10)
├── ob_cases.py               (10–15)
├── oncology_cases.py         (50–75 — split from golden_cases at this point)
├── rheumatology_cases.py     (30–35)
├── endocrinology_cases.py    (25–30)
├── gi_cases.py               (20–25)
├── orthopedic_cases.py       (20)
├── dermatology_cases.py      (15)
├── hematology_cases.py       (10)
├── imaging_cases.py          (10)
├── demographic_equity_cases.py  (15–20)
└── rare_disease_cases.py     (15)
```

### Schema additions required at 300

The 300-case milestone requires adding to the `GoldenCase` and `ClinicalCase` models:

```python
patient_gender: Literal["male", "female", "non-binary", "unknown"] | None = None
patient_ethnicity: str | None = None  # free-text per CDC recommended categories
patient_age_bracket: Literal["<12", "12-17", "18-64", "65-79", "80+"] | None = None
insurance_type: Literal["commercial", "medicare", "medicaid", "exchange", "tricare", "uninsured"] | None = None
state_of_residence: str | None = None  # 2-letter; Medicaid varies by state
```

Each case re-baselined at 300 must populate these. Existing 100 cases need a back-fill pass (estimated 1 hour for 100 cases at 30 sec/case parse from clinical_notes + verification).

### Validation gates at 300

In addition to all 100-case gates:

1. ✅ Demographic distribution: gender within ±10% of payer-population norm (typically ~52% female / 48% male commercial; varies by plan)
2. ✅ Insurance-type distribution: structured field populated for ≥ 95% of cases
3. ✅ Prevalence-weighted distribution within ±5% of target % per specialty
4. ✅ Per-specialty per-class regression detection: ≥ 3 cases per (specialty × outcome) cell for the top 8 specialties
5. ✅ Aggregate pass rate: ≥ 96%
6. ✅ 5pp aggregate-drop detection power: 0.80
7. ✅ Phase 2 clinical-review board (CRB): operational. First quarterly sample (30 cases × 3 reviewers) completed. Inter-rater κ ≥ 0.70.
8. ✅ Iteration manifest discipline: every batch's chg-N entry has predicted_fix / risk_cases / verdict triple.

### Phase 2 clinical-review board (formation at 100, operational scored sweeps at 200)

Per `CASE_AUTHORING_GUIDE.md` § 12 and `PACCA_PRD_v2.5_Consolidated.md` § 16.7, the CRB activates in two stages: **formation** at the 100-case milestone (crossed — 105 as-built; board being convened) and **operational scored κ-sweeps** at the 200-case milestone. By the 300-case milestone the board is fully operational and has run at least one quarterly sweep. Once operational:

- Panel: 2–3 credentialed clinicians, covering oncology + cardiology + behavioral as the highest-volume specialties.
- Frequency: quarterly.
- Sample: 10% stratified random (30 cases at 300).
- Output: `docs/findings/clinical-review-board-{YYYY-Q}.md` per quarter.
- Disagreement protocol: cases where the panel disagrees with cataloged `expected_outcome` get revisited in the next iteration; the case is tagged `under-revision` in `CASE_PROVENANCE.md` until resolved.

Budget: estimated $15K–$25K per quarter (3 specialists × ~10 hours each × $500–$800/hr).

## §4 — The 500-case + SaMD milestone (cases 301 to 500+)

The 500-case + SaMD-grade milestone unlocks:
- Claim 7: HIPAA SaMD-grade clinical validation, audit-defensible
- "This AI can make clinical recommendations that influence patient care under HIPAA SaMD" (the highest claim level)

### Composition strategy at 500

The 300-case prevalence-weighted distribution scales linearly to 500 — 67% more cases per specialty. Plus:

| Addition | Cases |
|---|---|
| Specialty depth expansion (per top-10 specialties) | 150 |
| Adversarial / failure-mode expansion (new modes discovered in production) | 25 |
| Demographic equity expansion (race-specific dosing, gender-specific care depth) | 15 |
| Rare-disease cohort (per genomic + ICD-10 prefix coverage) | 10 |
| **Total added (300 → 500)** | **200** |

### Validation gates at 500

In addition to all 300-case gates:

1. ✅ Aggregate pass rate: ≥ 97%
2. ✅ 3pp aggregate-drop detection power: 0.80
3. ✅ Per-specialty within-cell stratification: ≥ 5 cases per (specialty × outcome × age-bracket) for the top-5 specialties
4. ✅ CRB quarterly with inter-rater κ ≥ 0.80 (Landis-Koch "almost perfect")
5. ✅ Post-market surveillance instrumentation: production decisions stream into a `post_market_decisions/` parquet store; weekly aggregation reports per `docs/findings/post-market-week-{YYYY-Www}.md`
6. ✅ External validation: a third-party clinical-AI evaluator (e.g., Coalition for Health AI; Mayo Clinic Platform; AHA Center for Health Innovation) has independently reviewed the dataset + methodology and issued a written assessment
7. ✅ Documentation completeness: every clinical claim in `PACCA_PRD_v2.6_Consolidated.md` cross-references a specific case ID or batch
8. ✅ Reproducibility: k=4 rollouts captured for the full dataset; baseline includes per-case score distributions, not just medians

### Phase 3 post-market surveillance (at 500 + deployment)

Activates when PACCA is deployed to a paying customer:

- **Instrumentation:** every production decision logs (a) input case shape, (b) decision outcome, (c) confidence score, (d) escalation branch, (e) gate-verdict trail.
- **Continuous evaluation:** synthetic shadow-run of the production case mix against the eval dataset weekly. Drift detection on aggregate pass rate (alarm at 2pp drop from rolling 4-week baseline).
- **Anomaly detection:** sudden specialty-mix shifts, branch-distribution shifts, confidence-distribution shifts.
- **Quarterly reports:** consolidated production-performance report to the customer + the regulatory file.

### Optional Phase 4: FDA SaMD De Novo or 510(k) submission

If PACCA pursues FDA clearance (not all SaMD-grade systems do — much of healthcare AI operates under "decision support" exemption today):

- **De Novo pathway:** for novel predicate. Estimated 12–18 month review.
- **510(k):** if a substantially-equivalent predicate exists. Estimated 4–6 month review.
- **Pre-submission (Q-Sub) meeting:** strongly recommended; 60–90 day FDA scheduling.

Document set required (PACCA's current artifacts map to these):

| FDA requirement | PACCA artifact |
|---|---|
| Design history file | git history + DECISIONS.md + ITERATIONS.md + manifests/ |
| Risk management file (ISO 14971) | `docs/HIPAA_COMPLIANCE.md` + risk register (this doc § 6) |
| Clinical validation report | this dataset + CRB findings + post-market data |
| Software requirements specification | PACCA_PRD_v2.X §§1–14 |
| Software design specification | ARCHITECTURE.md |
| Cybersecurity documentation | HIPAA_COMPLIANCE.md + SECURITY.md (to be authored) |

## §5 — Effort estimates and budget

| Milestone | New cases | FTE-weeks (single author + 0.25 FTE clinical SME) | FTE-weeks (clinical-writer + 0.5 FTE clinical SME) | Wall-clock (1 FTE) | Wall-clock (2 FTE) |
|---|---|---|---|---|---|
| 33 → 100 (this roadmap, near-term) | 67 | 6–8 weeks | 4–5 weeks | 1.5–2 months | 5–6 weeks |
| 100 → 300 (medium-term) | 200 | 18–24 weeks | 12–16 weeks | 4.5–6 months | 3–4 months |
| 300 → 500 (long-term) | 200 | 18–24 weeks | 12–16 weeks | 4.5–6 months | 3–4 months |
| **Total: 33 → 500** | **467** | **42–56 weeks** | **28–37 weeks** | **10–14 months** | **7–10 months** |

### Cost-per-case assumptions (calibrated against this cycle's experience)

- **Author time:** ~60–90 min per case (clinical research + writing + verification + provenance + coverage).
- **SME-review time:** ~15–20 min per case (read + concur or flag).
- **CRB time:** ~20–30 min per case sampled (3 reviewers × 10% sample → 6–9 min weighted per case in dataset).
- **Engineer wire-up:** ~5 min per case (existing pattern; new file is ~30 min one-time).

### Budget per milestone

| Milestone | Author cost ($150K FTE) | SME cost ($600K FTE @ 0.25) | CRB cost (per quarter) | Tooling cost |
|---|---|---|---|---|
| 33 → 100 | $17K–$23K | $7K–$9K | $0 (not yet active) | $0 |
| 100 → 300 | $52K–$69K | $26K–$35K | $15K–$25K × 4 quarters = $60K–$100K | $0 |
| 300 → 500 | $52K–$69K | $26K–$35K | $15K–$25K × 4 quarters = $60K–$100K | $5K–$10K (post-market surveillance store) |
| External validation (one-time) | — | — | — | $25K–$50K |

**Total cost 33 → 500:** ~$326K–$455K over 10–14 months at 1 FTE, plus $25K–$50K external validation.

This is the budget-justification number for a portfolio-stage company pursuing SaMD-grade clinical validation. Materially cheaper than (a) a real-world clinical trial (~$1M+) or (b) the absence of validation followed by a customer-discovered regression (open-ended).

## §6 — Risk register

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| **Templatized case generation** — author writes 67 cases by copy-paste-edit; cases share structural patterns that artificially correlate failures. | Medium | High | Mandatory per-case named failure mode in CASE_PROVENANCE.md; no case lands without a stated reason for existing. Anti-pattern explicitly called out in CASE_AUTHORING_GUIDE.md § 14. |
| **SME bandwidth bottleneck** — author has the cases, SME doesn't have time to review. | High at 300+ | High | Author-self-attestation acceptable at portfolio stage per CASE_AUTHORING_GUIDE.md § 11. Backfill review via CRB at quarterly cadence. |
| **CRB inter-rater disagreement** — panel doesn't agree among themselves; κ < 0.70. | Medium at first activation | Medium | Disagreement is informative; cases where the panel disagrees get a `under-revision` flag and a revision-iteration in the next harness cycle. κ < 0.70 itself becomes a finding in the CRB report. |
| **Guideline drift** — a cited guideline (NCCN, AAD, GINA) updates; existing case becomes stale. | High over 12+ months | Medium | Per-case `guideline_citation_year` field added to GoldenCase at 300-milestone schema change. Annual re-citation audit. Specific cases flagged for revision per the next iteration. |
| **PHI leak in synthetic case** — author derives a case from real patient memory and an identifier slips through. | Low | Catastrophic | CASE_AUTHORING_GUIDE.md § 4 + PR template + per-commit PHI guard hook. SME review is the human check. |
| **Capture-baseline doesn't include supplementary lists** — known limitation in `capture_baseline.py` causes new cases to not be part of the regression gate. | High (already present) | High | Scoped to iter-6 separate PR per `expansion_cases.py` docstring. Block 100-case milestone declaration on this fix. |
| **Cost overrun on CRB** — quarterly $25K × 4 = $100K underestimated; specialists charge more than expected. | Medium | Medium | Initial CRB quarter scoped at 30 cases × 3 reviewers as proof-of-process; budget revisited at 100-case mark before formal Phase 2 activation. |
| **FDA regulatory shift** — SaMD guidance updates between now and 500-case milestone; case-count thresholds change. | Medium over 12+ months | Medium | Track FDA digital-health publications. Maintain dialogue with regulatory consultant. Re-baseline `STATISTICAL_POWER.md` against current guidance annually. |
| **LLM-as-judge variance drifts** — model updates to Claude Haiku change scoring distribution. | Medium per Anthropic update | Medium | k=N rollouts (currently 2; raise to 4 at 300+); judge-model pinned in `evaluator.py`; judge-prompt versioned in prompt registry. |
| **Branch-and-PR discipline erodes under deadline pressure** — direct-to-main commits accumulate; audit chain breaks. | Medium under customer-deadline stress | High | `pacca_pr_workflow.md` memory rule + reviewer agent + commit hook reject direct-to-main pushes. |

## §7 — How this roadmap operationalizes the AHE methodology

The AHE paper (Lin et al. 2026) frames the harness cycle as iterative phases (H1–H7). This roadmap maps dataset-growth iterations to AHE phases:

| AHE phase | This roadmap's contribution |
|---|---|
| H1 (system prompt) | Unchanged by dataset growth. |
| H2 (institutional memory) | Each batch can validate that no existing H2 entry over-fires on the new cases (the "cross-condition memory bleed" failure mode in CASE_PROVENANCE.md). |
| H3 (sub-agents) | Not yet exercised. 500+ may motivate specialty-specific sub-agents. |
| H4 (RAG) | Each new specialty batch implicitly grows the RAG corpus needs; new guidelines must be added to `vector_store.py`'s seed data. |
| H5 (evaluation) | This is where dataset growth lives — every batch is an H5 evolution. |
| H6 (skills) | Not yet exercised. |
| H7 (middleware) | Not yet exercised. |

The 100/300/500 milestones map to iter-6, iter-N (where N corresponds to the 300-case batch), iter-M (the 500-case batch). Each milestone is a multi-iteration arc, not a single iteration.

## §8 — Documents this roadmap interacts with

| When a batch lands, update: | Why |
|---|---|
| `tests/clinical/{batch}_cases.py` (or extend existing) | The new cases themselves. |
| `tests/clinical/test_clinical_accuracy.py` aggregator + integrity tests | Wire up. |
| `docs/CASE_PROVENANCE.md` | Per-case row. |
| `docs/EVALUATION_COVERAGE.md` | Cell updates. |
| `docs/DATASET_SUFFICIENCY.md` "Where PACCA is today" | Count bump. |
| `harness/manifests/iter-N.json` | chg-N entry with predicted_fix + risk_cases. |
| `docs/ITERATIONS.md` | Narrative. |
| `docs/DECISIONS.md` | Verdict. |
| `docs/PACCA_PRD_vX.Y_Consolidated.md` | Bump PRD version at each milestone (100 → v2.5; 300 → v2.6; 500 → v3.0). |
| `docs/DATASET_GROWTH_ROADMAP.md` (this file) | Update §2 / §3 / §4 progress markers; tick off batch IDs. |

---

*This document is part of the PACCA v2.5+ harness-engineering cycle documentation set. Last updated: 2026-05-25 (iter-6 mid). Update sequence as batches land and milestones are hit.*
