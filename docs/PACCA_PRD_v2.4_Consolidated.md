# PACCA — Product Requirements Document, v2.4 Consolidated

> **Status:** Active draft, iter-6 open. Replaces [`PACCA_PRD_v2.3_Consolidated.md`](PACCA_PRD_v2.3_Consolidated.md) (a stub) by adding §15 (Harness Engineering Cycle, summarized) and §16 (Clinical Validation Strategy — the new substantive chapter).
> **Predecessor (v2.2 narrative content):** [`PACCA_PRD_Consolidated.md`](PACCA_PRD_Consolidated.md) — §1–§14 carried forward unchanged.
> **Audience:** prospective payer customers, HIPAA / SaMD reviewers, clinical-validation board members, investors evaluating production readiness, and the engineering team executing the dataset and validation roadmap.
> **Honesty disclaimer:** PACCA's current evaluation dataset is 33 cases. This document describes the *path to* HIPAA SaMD-grade clinical validation, the *current state* against that path, and the *evidence the existing dataset can defensibly support*. It does NOT claim the dataset is currently SaMD-adequate — it explicitly states that it is not, and quantifies the gap.

---

## Table of contents

- [§1–§14 — carried forward from v2.2](#§1§14--carried-forward-from-v22)
- [§15 — Harness Engineering Cycle (summarized; canonical docs cross-referenced)](#§15--harness-engineering-cycle)
- [§16 — Clinical Validation Strategy (new in v2.4)](#§16--clinical-validation-strategy)
  - §16.1 — Validation framework alignment (FDA SaMD + IMDRF)
  - §16.2 — Current evaluation surface
  - §16.3 — Dataset sufficiency — current state vs. SaMD-grade target
  - §16.4 — Statistical-power evidence
  - §16.5 — Per-case provenance and audit trail
  - §16.6 — Coverage matrix and gap analysis
  - §16.7 — Clinical-SME review process (Phase 1 + Phase 2)
  - §16.8 — Roadmap from portfolio-credible (33) to production-pilot (100) to deployment (300) to SaMD-grade (500+)
  - §16.9 — Honest assessment of claims PACCA can defend today
- [§17 — HIPAA Compliance Cross-Reference](#§17--hipaa-compliance-cross-reference)
- [§18 — Change Log](#§18--change-log)

---

## §1–§14 — Carried Forward from v2.2

Sections §1 through §14 remain unchanged from [`PACCA_PRD_Consolidated.md`](PACCA_PRD_Consolidated.md). Topics covered there:

- §1 Vision and product positioning
- §2 User personas and primary use cases
- §3 System scope (in / out)
- §4 Functional requirements (REQ-FN-001 through REQ-FN-NNN, IEEE 29148 format)
- §5 Non-functional requirements (NFR)
- §6 Data model and PHI handling
- §7 Multi-agent architecture (Clinical Risk Detector → Decision Agent → Pre-Flight Branches)
- §8 RAG layer (Phase H4 — guidelines retrieval)
- §9 Audit and observability requirements
- §10 Integration surface (FHIR, X12 278, payer APIs)
- §11 Security model (auth, authorization, secrets, key rotation)
- §12 Performance and scale targets
- §13 Acceptance criteria
- §14 Glossary

These sections are stable and not re-litigated in v2.4. The substantive additions in v2.4 are §15 (summarized; pointing to the canonical harness docs) and §16 (the clinical-validation chapter that this PRD increment exists to deliver).

---

## §15 — Harness Engineering Cycle

PACCA implements the v2.3 harness-engineering methodology described in Lin et al. (2026), *Agentic Harness Engineering* (arXiv:2604.25850). The full methodology and per-iteration record live in dedicated documents — §15 here is the index and the cross-reference policy.

### §15.1 — Canonical documents

| Document | Covers |
|---|---|
| [`HARNESS.md`](HARNESS.md) | The 11 editable harness surfaces (Phases H1–H7 plus PACCA-specific extensions: escalation branches, RAG collections, prompt registry, audit schema), the three observability pillars (logs, metrics, traces), and the three rules of engagement (one change per iteration, change-manifest contract, run-the-gate-before-merging). |
| [`harness/manifests/change_manifest.schema.json`](../harness/manifests/change_manifest.schema.json) | Machine-readable contract for every behavioral change: predicted_fix, risk_cases, verdict structure. |
| [`harness/manifests/iter-N.json`](../harness/manifests/) | Per-iteration change manifests. As of this PRD, iter-1 through iter-5 are closed and tagged; iter-6 is the current open iteration covering the dataset-expansion work this PRD increment describes. |
| [`DECISIONS.md`](DECISIONS.md) | Append-only verdict log per the runbook superseding-correction protocol. |
| [`ITERATIONS.md`](ITERATIONS.md) | Per-iteration narrative log in the format of the AHE paper's Appendix C. |
| [`RUNBOOK_iter*.md`](.) | Per-iteration runbook spec (lift the structure for any future iteration). |
| [`findings/`](findings/) | Mid-iteration investigation reports (e.g., `H2-memory-iteration-1.md` documenting the iter-3 chg-2 GC-021 regression and its wording-fix resolution). |

### §15.2 — Phases relevant to PACCA today

| Phase | Description | Status in PACCA |
|---|---|---|
| H1 | System prompt | Stable. Byte-identity check baselined at iter-1 chg-1; criterion-preservation tests added iter-3+. |
| H2 | Long-term memory (institutional memory layer) | 3 entries live: NSCLC pembrolizumab (iter-3 chg-2), RA biologic (iter-4 chg-1), asthma dupilumab (iter-5 chg-4). Each carries an explicit "Status: IN_REVIEW. (Not DENIED.)" anti-pattern routing per the iter-3 chg-2 findings. |
| H3 | Sub-agents | Not yet implemented. Roadmap item. |
| H4 | RAG / retrieval | Phase H4 RAG layer is live in `src/pacca/integrations/vector_store.py`; guideline corpus is synthesized for the test set. Production-scale guideline ingestion is roadmap. |
| H5 | Evaluation harness | Live: per-case regression gate (iter-2 chg-2), LLM-as-judge (Claude Haiku), k=2 rollouts (iter-3 chg-3), aggregate ≥80% accuracy gate. |
| H6 | Skills | Not yet implemented. AHE paper lists as future. |
| H7 | Middleware | Not yet implemented. AHE paper lists as future. |

### §15.3 — The PACCA-specific harness surfaces (beyond H1–H7)

PACCA extends the AHE framework with:

- **Escalation branches.** SS5.4 defines 7 escalation branches (branch_1 through branch_7) for the Decision Agent. Each branch has at least one validation case in the dataset (Dimension 1 of [`EVALUATION_COVERAGE.md`](EVALUATION_COVERAGE.md)).
- **Pre-flight detector.** `ClinicalRiskDetector` evaluates experimental-treatment, rare-condition, prior-denial, conflicting-guidelines, high-cost, and pediatric-complex triggers before the Decision Agent runs. Validated via the GC-006 through GC-012 case family.
- **Complexity-score model.** Integer 1–5 weighted heuristic (iter-5 chg-3) for the pediatric_complex check. Validated against GC-012, GC-023, GC-024, GC-025.
- **Hybrid structured-field + parser-fallback data path.** All clinical fields prefer the structured ClinicalCase model when populated; fall back to provider-notes parsing otherwise.
- **Prompt registry.** Versioned prompts under `src/pacca/prompts/`; byte-identity check at every iteration boundary.
- **Audit schema.** Every decision emits a structured audit trail with prompt version, retrieval hits, gate verdicts, judge score.

### §15.4 — Discipline and audit defensibility

Three rules of engagement, enforced by the runbook + branch-and-PR workflow + per-commit hook protocol:

1. **One behavioral change per iteration's chg-N entry.** No "while I'm in here" drive-by edits.
2. **Every chg-N entry has a predicted_fix and risk_cases section in the manifest.** Authored *before* the change; verdict records observed_outcome *after* the change. This protects against post-hoc storytelling.
3. **Run the full gate before merging.** Fast suite + full clinical pipeline + per-case regression gate.

Audit-trail defensibility comes from the combination of (a) append-only DECISIONS.md and ITERATIONS.md, (b) the per-iteration manifests under `harness/manifests/`, and (c) git's signed-tag history.

---

## §16 — Clinical Validation Strategy

This section is the substantive new chapter in v2.4. It exists to answer the question that a HIPAA / SaMD reviewer or a payer-customer due-diligence team will ask: **"Is your evaluation dataset adequate to defend the claims you make about your system?"**

The short answer: **PACCA's current 33-case evaluation set is portfolio-credible, production-pilot-capable on narrow scope, and explicitly not yet HIPAA SaMD-grade. The roadmap to SaMD-grade is defined in §16.8 below, with effort estimates and case-count thresholds.**

The long answer follows.

### §16.1 — Validation framework alignment (FDA SaMD + IMDRF)

PACCA's validation framework aligns to:

| Authority | Framework | PACCA's evidence document |
|---|---|---|
| FDA | *Software as a Medical Device (SaMD): Clinical Evaluation* (Dec 2017) | [`STATISTICAL_POWER.md`](STATISTICAL_POWER.md) § "FDA SaMD-grade claim alignment" |
| IMDRF | SaMD WG/N41 (2017), *Software as a Medical Device (SaMD): Clinical Evaluation* | [`STATISTICAL_POWER.md`](STATISTICAL_POWER.md) (international counterpart) |
| FDA | 21 CFR 820.30 (Design Controls) | Implicit through HARNESS.md's change-manifest + iteration-log discipline |
| HIPAA | 45 CFR 164 (Security + Privacy Rules) | [`HIPAA_COMPLIANCE.md`](HIPAA_COMPLIANCE.md) + CLAUDE.md "Never log PHI" + synthetic-only fixtures policy |
| ONC | 45 CFR 170 (Health IT certification) | Not currently pursued; relevant if PACCA enters EHR-integrated certification path |
| AMA / Specialty bodies | Specialty practice guidelines (NCCN, ACR, AAD, GINA, etc.) | [`CASE_AUTHORING_GUIDE.md`](CASE_AUTHORING_GUIDE.md) § 5 "The guideline-citation rule" |

The three-pillar SaMD framework breaks down as:

| Pillar | What it requires | PACCA's status |
|---|---|---|
| **Analytical validation — correctness** | The SaMD performs as intended on representative inputs | 33 cases across 7 escalation branches × multiple specialties; live gate 20/20 = 100% over three iterations |
| **Analytical validation — robustness** | The SaMD handles adversarial / failure-mode inputs | Named failure-mode cases: hallucination traps (GC-018, GC-019), memory traps (GC-021, GC-022), patient-preference traps (GC-005, GC-026), workup-hierarchy violations (GC-027), controlled-substance + SUD (GC-029), age-only-escalation (GC-028 must not fire), rare-prefix over-escalation (GC-030 must not fire) |
| **Analytical validation — repeatability** | The SaMD produces consistent outputs on the same input | k=2 rollouts implemented (iter-3 chg-3); k=4 recommended for SaMD-grade; LLM-as-judge variance characterized |
| **Clinical validation — agreement with experts** | The SaMD's outputs agree with clinical SME judgments | Phase 2 clinical-review board process defined in `CASE_AUTHORING_GUIDE.md` § 12; not yet operational |
| **Clinical performance — post-market** | Continuous performance evaluation in production | Pre-deployment. The architecture's audit trail and the per-case gate enable post-market instrumentation; the deployment hasn't happened. |

### §16.2 — Current evaluation surface

PACCA evaluates against a hand-crafted golden-case dataset across four files:

| File | Count | Purpose |
|---|---|---|
| `tests/clinical/golden_cases.py` (GOLDEN_CASES) | 20 | Canonical positive + negative + branch-coverage cases |
| `tests/clinical/near_miss_cases.py` (NEAR_MISS_CASES) | 2 | H2 memory-trap adversarial probes (siblings of GC-001 with one disqualifier) |
| `tests/clinical/pediatric_cases.py` (PEDIATRIC_CASES) | 3 | iter-5 chg-3 complexity-score model validation set |
| `tests/clinical/expansion_cases.py` (EXPANSION_CASES) | 8 | iter-6 gap-closure suite (DENY class, cardiology, geriatric, behavioral, hematology, transplant, neurology, OB) |
| **Total** | **33** | |

Evaluation runs through two gates:
1. **Per-case regression gate** ([`regression_gate.py`](../tests/clinical/regression_gate.py)) — iter-2 chg-2. Fires on any single-case score drop > noise_threshold relative to baseline. 100% per-case sensitivity regardless of dataset size.
2. **Aggregate ≥80% accuracy gate** ([`evaluator.py`](../tests/clinical/evaluator.py)) — the LLM-as-judge scores each case 1–5; the dataset-wide pass rate must be ≥ 80%.

The two compose: per-case dominates *detection sensitivity*; aggregate provides the single summary statistic for customer-facing reports and the SaMD claim.

### §16.3 — Dataset sufficiency — current state vs. SaMD-grade target

Per [`DATASET_SUFFICIENCY.md`](DATASET_SUFFICIENCY.md):

| Claim level | Cases required | PACCA today | Gap |
|---|---|---|---|
| Coverage floor (every gate has ≥ 1 case on each side) | ~50 | 33 | -17 |
| 20pp aggregate drop detection (smoke test) | 15–20 | 33 | met |
| 10pp aggregate drop detection (clinically meaningful) | 75–100 | 33 | -42 to -67 |
| Per-case detection on every reasoning class (3-5 per family × ~30 families) | 100–150 | 33 | -67 to -117 |
| 5pp aggregate drop detection (subtle erosion) | 200–300 | 33 | -167 to -267 |
| Production-deployment representative case mix | 300–500 | 33 | -267 to -467 |
| HIPAA / SaMD-grade clinical validation | 500+ in-house + 100/quarter clinical-review-board sample | 33 | -467 + the review-board process |

### §16.4 — Statistical-power evidence

Per [`STATISTICAL_POWER.md`](STATISTICAL_POWER.md), the binomial-CI math:

```
n ≈ ( z_α · √(p₀(1-p₀)) + z_β · √(p₁(1-p₁)) )² / (p₀-p₁)²
```

Sample sizes for PACCA's evaluation regime (baseline p₀=0.95, α=0.05, power 0.80):

| Δ (drop to detect) | n (formula) | Operational target |
|---|---|---|
| 20 pp | 13 | 20 |
| 15 pp | 23 | 30 |
| 10 pp | 43 | 100 |
| 7 pp | 75 | 150 |
| 5 pp | 150 | 200–300 |
| 3 pp | 390 | 500 |
| 2 pp | 870 | 1,000+ |

The per-case gate excels at sharp, single-case regressions; the aggregate gate excels at slow, distributed erosion. They are complementary. See `STATISTICAL_POWER.md` § "Sensitivity analysis" for the cross-table.

### §16.5 — Per-case provenance and audit trail

Per [`CASE_PROVENANCE.md`](CASE_PROVENANCE.md), each case in the dataset answers four questions:

- Case ID + file
- Clinical rationale (≤ 2 sentences)
- Named failure mode it probes (or "coverage" for routine cases)
- Iteration of origin

The 33-row provenance table is the audit-defense artifact for the question "why does this case exist?" A reviewer can scan it without reading 33 case definitions.

Failure-mode taxonomy (established and extensible):
- Coverage
- Hallucination zero-tolerance
- False pattern-matching (memory trap)
- Step-therapy enforcement
- Cross-condition memory bleed
- Test-data adequacy
- Discriminator (negative / ambiguous / positive) class
- Branch-N pre-flight
- Confidence-N boundary
- Policy-trigger override (high-cost / pediatric-complex / age-only / rare-prefix)

### §16.6 — Coverage matrix and gap analysis

Per [`EVALUATION_COVERAGE.md`](EVALUATION_COVERAGE.md), the per-dimension matrices at the 33-case state:

| Dimension | Defensible claim today | Remaining gap |
|---|---|---|
| Outcome class | All 5 outcomes represented (DENIED now populated via GC-026, GC-027) | DENY needs ≥ 5 for sufficient sample |
| Escalation branch | All 7 branches plus NONE | 3+ per branch for per-class signal |
| Specialty | 14 specialties covered | 5+ per specialty for within-specialty signal |
| Age bracket | Pediatric (4), adolescent (limited), adult (most), older adult (2), 80+ (1) | 3+ per stratum |
| Documentation completeness | Complete (across all outcomes), ambiguous, sparse + hallucination | Ambiguous DENY, graded sparseness |
| Cost tier | Under threshold (most), 2 over-threshold | At-threshold boundary cases |
| Demographics | Gender/age stated in notes | Structured fields needed for equity claims |
| Comorbidity | 0, 1, 2+ loads represented | Graded coverage for parser robustness |
| Failure mode | Every documented mode has ≥ 1 case (iter-6 added 4 new modes) | Per-mode statistical signal weak with 1–2 cases each |
| AHE harness component | H1, H2, H4, H5 covered; PACCA-specific extensions covered | H3 (sub-agent), H6 (skill), H7 (middleware) not yet implemented |

### §16.7 — Clinical-SME review process (Phase 1 + Phase 2)

Per [`CASE_AUTHORING_GUIDE.md`](CASE_AUTHORING_GUIDE.md) §§ 11–12:

**Phase 1 (per-case, pre-merge, in-house):**

Every new case requires SME concurrence on:
1. Clinical accuracy of the synthetic notes
2. Correctness of the cited guideline body and what it says
3. Correctness of expected_outcome + expected_branch
4. Appropriateness of clinical_rationale

The SME records concurrence in the PR via a "clinical-review: approved — Dr. X, MD, board-certified Y" comment. If the author is the SME, they self-attest in the PR description. In the absence of a credentialed SME for a specialty, the case lands `provisional` and gets the next Phase 2 sweep.

**Phase 2 (clinical-review board, post-100-cases, quarterly):**

- 2–3 credentialed clinicians (covering major specialties) score a random 10% stratified sample.
- Inter-rater agreement reported as Cohen's κ (target ≥ 0.80 per Landis & Koch 1977 "almost perfect" threshold).
- Cases where the board disagrees with cataloged `expected_outcome` get revision in the next iteration.
- Board reports land in `docs/findings/clinical-review-board-<date>.md`.

Phase 2 is the on-ramp to the FDA SaMD clinical-validation claim. It is **not yet operational** — it requires the dataset to cross 100 cases (current: 33) and external clinical-reviewer panel sourcing (budget: estimated $15K–$25K per quarter for 3 specialists, per `DATASET_SUFFICIENCY.md` § "Effort estimates").

### §16.8 — Roadmap from portfolio-credible (33) to SaMD-grade (500+)

| Milestone | Cases | Effort (1 FTE + 0.25 FTE clinical SME) | What it buys |
|---|---|---|---|
| **Current** | 33 | Done | Portfolio-credibility; coverage of every gate on both sides except still-thin DENY; 13 specialty families with first-case coverage; cardiology + 80+ first-touch. |
| **Production-pilot** | 100 | ~6–8 weeks | 10pp aggregate-drop detection; 3+ DENY cases; 3 cases per major specialty; demographic structured fields populated; ambiguous-tier coverage. Defensible for a single-payer pilot in a narrow specialty (e.g., "oncology biologics for a regional payer"). |
| **General payer deployment** | 300 | ~6–8 months | 5pp aggregate-drop detection; per-specialty per-class regression signal; prevalence-weighted distribution mirroring a major commercial payer's mix; demographic balance enabling equity claims. Defensible for broad-deployment-with-clinical-SME-in-the-loop. |
| **HIPAA SaMD-grade** | 500+ in-house + 100/quarter CRB sample | ~12–18 months | 3pp aggregate-drop detection; full per-specialty stratification; ongoing inter-rater κ measurement; post-market surveillance instrumentation. The bar for "this AI can make clinical recommendations that influence patient care under HIPAA SaMD." |

**Honest framing.** Each milestone is a discrete unlock of new claim-types, not a continuous-improvement-with-no-discrete-meaning. A 100-case dataset is genuinely more defensible than a 33-case dataset; the next 200 to reach 300 unlock claims the 100-case dataset cannot.

**Recommended priority order** for the next 67 cases (to reach 100) is in [`DATASET_SUFFICIENCY.md`](DATASET_SUFFICIENCY.md) § "Recommended priority order":

1. DENY-class expansion (5 cases) — close from current 2 to 5+
2. Cardiology depth (3–5 cases) — multiple sub-specialties
3. Mental health depth (3–5 cases) — beyond the single ADHD+SUD case
4. Demographic structured fields + 10 demographically-balanced cases
5. Geriatric (80+) depth (3 more cases) — beyond GC-028
6. Adult pulmonology (3 cases) — currently zero
7. At-threshold cost-boundary cases (2 cases) — currently zero
8. Ambiguous-tier completeness cases (5 cases) — currently zero
9. Specialty depth for cardiology, transplant, neurology, OB to reach 3+ each (~10 cases)
10. Graded sparse-documentation cases (3–5 cases) beyond the two hallucination traps

### §16.9 — Honest assessment of claims PACCA can defend today

| Claim | Defensible? | Evidence |
|---|---|---|
| "PACCA tests every policy gate with at least one case on each side" | Mostly. DENY now has 2 cases; the 0-DENY gap was the most embarrassing gap pre-iter-6. Still need 5+ DENY cases for sufficient sample. | EVALUATION_COVERAGE.md Dim 1 |
| "PACCA covers all 7 escalation branches" | Yes. | EVALUATION_COVERAGE.md Dim 1 |
| "PACCA tests across 14 specialty areas" | Yes, at 1–7 cases each. | EVALUATION_COVERAGE.md Dim 2 |
| "PACCA has named adversarial probes for every documented failure mode" | Yes. | EVALUATION_COVERAGE.md Dim 7 + CASE_PROVENANCE.md |
| "PACCA's per-case regression gate has 100% sensitivity on any single-case score drop ≥ 2" | Yes — mathematical guarantee, dataset-size-independent. | STATISTICAL_POWER.md § "Per-case regression-detection math" |
| "PACCA's aggregate gate catches ≥20pp drops with 80% power" | Yes — n=33 well exceeds the n=15 minimum. | STATISTICAL_POWER.md § "Sample sizes" |
| "PACCA's aggregate gate catches ≥10pp drops" | NO — n=33 is below the n=75–100 threshold. | STATISTICAL_POWER.md |
| "PACCA's aggregate gate catches ≥5pp drops (silent erosion)" | NO — n=33 is far below the n=200–300 threshold. | STATISTICAL_POWER.md |
| "PACCA's dataset is prevalence-weighted to a major payer's case mix" | NO — current distribution is convenience-sampled across observed gaps, not prevalence-weighted. | EVALUATION_COVERAGE.md gaps |
| "PACCA's dataset enables demographic equity testing" | NO — gender, ethnicity, insurance type are not structured fields on GoldenCase. | EVALUATION_COVERAGE.md Dim 5 |
| "PACCA has SaMD-grade clinical validation" | NO — current state is 33/500+; Phase 2 clinical-review board is defined but not operational. | This entire §16 |
| "PACCA has the *path* to SaMD-grade clinical validation defined" | YES — §16.8 roadmap, with effort estimates and per-milestone claim unlocks. | This document |

This honest-claim matrix is the answer to the SaMD reviewer's first question: "What can you defend?" The answer is the rows marked Yes; the rows marked NO are the explicit roadmap and the budget-justification for the next 18 months of dataset-growth work.

---

## §17 — HIPAA Compliance Cross-Reference

The clinical-validation dataset and process are governed by:

| Requirement | Policy | Document |
|---|---|---|
| Never log PHI | CLAUDE.md (project file) + structlog redaction in `src/pacca/instrumentation/tracing.py` | [`HIPAA_COMPLIANCE.md`](HIPAA_COMPLIANCE.md) |
| Synthetic data only in fixtures | CLAUDE.md + CASE_AUTHORING_GUIDE.md § 4 | [`CASE_AUTHORING_GUIDE.md`](CASE_AUTHORING_GUIDE.md) |
| Auth + input validation on every endpoint | CLAUDE.md | `HIPAA_COMPLIANCE.md` + `tests/test_api_security.py` |
| Secrets in env only | CLAUDE.md | `HIPAA_COMPLIANCE.md` + `.env.example` pattern |
| BAA-relevant logging policy | per-deployment | (operator's responsibility) |

The clinical-validation work itself does not introduce any new PHI surface — all 33 cases are synthetic per the authoring guide's § 4. The Phase 2 clinical-review board, when it activates, will need a separate BAA + access-control protocol if the board reviews any real patient data (the recommended setup is for the board to review synthetic cases only, eliminating the BAA question).

---

## §18 — Change Log

| Version | Date | Change |
|---|---|---|
| v2.2 | (predecessor) | §1–§14 narrative content; see `PACCA_PRD_Consolidated.md` |
| v2.3 stub | 2026-05-25 (initial) | Stub pointing at HARNESS.md + manifests so README links didn't 404 |
| **v2.4** | **2026-05-25 (this PRD)** | **§15 (summarized harness cycle) + §16 (Clinical Validation Strategy — substantive new chapter tying together DATASET_SUFFICIENCY, EVALUATION_COVERAGE, STATISTICAL_POWER, CASE_PROVENANCE, CASE_AUTHORING_GUIDE) + §17 (HIPAA cross-reference) + §18 (change log). Drafted as part of the iter-6 dataset-expansion work that grew the evaluation set from 25 to 33 cases.** |
| v2.5 (planned) | When dataset reaches 100 cases | Bump §16.3 / §16.6 / §16.9 with the new state; activate Phase 2 clinical-review board section as operational rather than aspirational. |

---

*This document is part of the PACCA v2.4 cycle documentation set. Last updated: 2026-05-25 (iter-6 open).*
