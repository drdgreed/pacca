# PACCA Demo — Two Synthetic Clinical Cases (full detail)

> **Purpose:** the two case threads for the demo (`DEMO_SCRIPT_v1.md`). Case A shows the *speed win* (routine → auto-approve). Case B shows the *safety gate* (complex pediatric → human review).
>
> **⚠️ Illustrative synthetic content.** These cases are fabricated for demonstration. The clinical criteria, drug indications, codes, and costs below were checked against public FDA labels, pivotal trials, and payer/coding references (cited per case), but the *patients* are invented and carry **no real PHI**. This is **not medical advice**. A licensed clinician should review both cases before they appear in any recorded demo — see the sign-off box at the end.
>
> **Demo configuration assumption (state this if asked):** PACCA's escalation thresholds are configurable. This demo runs with `HIGH_COST_THRESHOLD = $250,000` (code default is `$100,000`) to model a payer whose policy auto-adjudicates guideline-concordant systemic therapy and reserves *cost-based* Medical-Director review for cell/gene therapies and ultra-high-cost agents. All other thresholds are defaults (`complexity_specialist_review_min = 4`; pediatric complexity threshold `= 3`; pediatric age cutoff `< 18`).

---

## Case A — "The routine one." First-line pembrolizumab for PD-L1-high metastatic NSCLC → AUTO-APPROVE

### Patient (synthetic)
- **64-year-old woman**, former smoker (30 pack-years, quit 8 years ago). ECOG performance status **1**.
- No prior systemic therapy for lung cancer. No autoimmune disease, no organ transplant, not on chronic immunosuppression (i.e., no contraindication to checkpoint inhibition).

### Diagnosis
- **Metastatic non–small-cell lung cancer, adenocarcinoma**, right upper lobe primary with contralateral lung and bone metastases. Stage **IV (cIV, M1c)**.
- **ICD-10:** `C34.11` (malignant neoplasm, upper lobe, right bronchus/lung); metastatic sites coded secondarily (e.g., `C79.51` bone).

### Biomarkers (the documentation that makes this clean)
- **PD-L1 Tumor Proportion Score (TPS) = 80%** by the **PD-L1 IHC 22C3 pharmDx** companion assay (FDA-approved test).
- **EGFR:** wild-type. **ALK:** not rearranged. **ROS1:** negative. (No actionable driver alteration — so immunotherapy, not targeted therapy, is the guideline path.)

### Requested therapy
- **Pembrolizumab (KEYTRUDA) monotherapy**, **200 mg IV every 3 weeks** (label-alternative: 400 mg IV every 6 weeks), first-line, up to 35 cycles.
- **HCPCS:** `J9271`. **Estimated annual cost:** ~**$190,000** (under the demo's $250k cost-review threshold).

### Why it's guideline-concordant (auto-approvable)
First-line single-agent pembrolizumab is a standard-of-care, category-1 option for metastatic NSCLC with **PD-L1 TPS ≥ 50%** and **no EGFR/ALK** alteration — the population and result of the **KEYNOTE-024** trial (5-yr OS ~31.9% vs 16.3% for chemotherapy). This patient meets every criterion: correct histology, stage IV, TPS well above the 50% bar, no driver mutation, ECOG 0–1, no immunotherapy contraindication, complete documentation.

### Expected PACCA behavior → **AUTO-APPROVED**
Deterministic pre-flight checks (all must be clear for auto-adjudication):

| Pre-flight branch | Fires? | Why |
|---|---|---|
| Experimental treatment | No | `J9271` is a standard, FDA-approved agent — not in the experimental-code set |
| Rare condition | No | NSCLC (`C34.*`) is common; not a rare-disease ICD-10 prefix |
| Conflicting guidelines | No | Single clear guideline path; PD-L1-high + driver-negative = immunotherapy |
| Prior denial | No | No prior denial on record |
| High-cost | No | ~$190k < $250k demo threshold |
| Pediatric / adult complexity | No | Adult; single diagnosis, good PS, complete docs → complexity score below the specialist-review threshold |

With no pre-flight trigger, the agent pipeline (Evidence Aggregation → Clinical Classification → Decision Support, Tier 1) evaluates guideline concordance, cites the retrieved guideline text, and returns **AUTO-APPROVED with high confidence** — target **< 30 seconds**, versus a 6–12 hour manual review.

---

## Case B — "The hard one." Pediatric CD19 CAR-T for relapsed/refractory B-ALL → ESCALATE → human approves

### Patient (synthetic)
- **8-year-old child.** B-cell precursor acute lymphoblastic leukemia, **second relapse** after multi-agent chemotherapy and a prior allogeneic stem-cell transplant. Currently in morphologic relapse with CD19-positive disease confirmed by flow cytometry.
- Adequate organ function and performance status for cell therapy per the treating center; caregiver consented.

### Diagnosis
- **B-cell precursor acute lymphoblastic leukemia, in relapse.**
- **ICD-10:** `C91.02` (acute lymphoblastic leukemia, B-cell type, **in relapse**).

### Requested therapy
- **Tisagenlecleucel (KYMRIAH)** — a one-time autologous **anti-CD19 CAR-T** cell infusion, preceded by leukapheresis, several weeks of individualized manufacturing, and lymphodepleting chemotherapy.
- **HCPCS:** `Q2042`. **Cost:** **$475,000** for the infusion (≈ **$547,000** estimated year-one total with apheresis, lymphodepletion, admission, and CRS/neurotoxicity management).

### Why it's *appropriate* care — but still deserves a human
Tisagenlecleucel is **FDA-approved (2017)** for patients **up to age 25** with B-cell precursor ALL that is **refractory or in second-or-later relapse** — which this child meets on-label. So this is not a bad request. It is a **high-stakes, high-complexity** one: a $475k one-time cell therapy in a child, with a real risk of severe cytokine-release syndrome (grade ≥3 CRS ~23%) and neurotoxicity, dependent on manufacturing logistics. This is precisely the request a payer should **not** let a machine auto-decide.

### Expected PACCA behavior → **ESCALATE (three independent triggers) → Medical Director → APPROVE**
Deterministic pre-flight — **any one** trigger routes to human review; this case trips **three**:

| Pre-flight branch | Fires? | Why |
|---|---|---|
| **Experimental treatment** | **Yes** | `Q2042` is in PACCA's `EXPERIMENTAL_PROCEDURE_CODES` (CAR-T therapies are flagged for conservative human review) |
| **High-cost** | **Yes** | $475k **>** $250k demo threshold (and > $100k default) — cost-based escalation fires *regardless of clinical merit*, by policy |
| **Pediatric complexity** | **Yes** | Age 8 (< 18) with a complexity score ≥ 3 (pediatric weight + relapsed/high-severity disease) |
| Rare condition | No | Pediatric ALL is not coded as an ultra-rare prefix here |
| Prior denial | No | None on record |

The request routes to the **Medical Director queue**. The reviewer sees the assembled evidence, the agents' reasoning, and **every escalation reason**. The physician confirms the therapy is **on-label and appropriate** for this relapse setting and **approves** it — the child gets the treatment, *after* a human has looked.

**The narrative point:** the escalation is not the system catching a *bad* request — it's the system knowing that the highest-stakes therapy in medicine always deserves a human's eyes. Three separate deterministic rules independently reached the same conclusion: *don't automate this one.* And the human said yes.

> **On the "experimental" flag (be ready for this question):** Kymriah is FDA-approved for exactly this indication, so flagging it "experimental" is deliberately conservative — PACCA routes *all* CAR-T to human review rather than trying to adjudicate on-label vs. off-label autonomously. The Medical Director makes that determination. If a clinician viewer objects that on-label CAR-T shouldn't read as "experimental," that's a fair note to fold into how the escalation reason is *labeled* on screen (e.g., "cell/gene therapy — mandatory specialist review") without changing the safe behavior.

---

## Side-by-side (for the Act 5 split screen)

| | Case A | Case B |
|---|---|---|
| Patient | 64 yo, metastatic NSCLC | 8 yo, relapsed/refractory B-ALL |
| Therapy | Pembrolizumab 200 mg Q3W (`J9271`) | Tisagenlecleucel CAR-T (`Q2042`) |
| Guideline basis | KEYNOTE-024; PD-L1 TPS ≥50%, driver-negative | FDA label: ≤25 yr, ≥2nd relapse/refractory |
| Cost (annual/one-time) | ~$190k | $475k (~$547k yr-1) |
| Pre-flight triggers | None | Experimental + High-cost + Pediatric-complex |
| Outcome | **AUTO-APPROVED, < 30 s** | **ESCALATED → Medical Director → approved** |
| What it proves | Speed + transparency | Safety + human-in-the-loop |

---

## Clinician sign-off (complete before recording)

- [ ] Case A is a fair representation of a **clean, guideline-concordant** first-line pembrolizumab approval (histology, TPS ≥50%, driver-negative, ECOG, no contraindication).
- [ ] Case B is a fair representation of an **on-label, appropriate** pediatric CAR-T request that *should* receive specialist review.
- [ ] The on-screen escalation-reason labels are clinically defensible (see the "experimental" note above).
- [ ] Reviewer name / credentials: ______________________  Date: __________

---

## Sources

- KEYNOTE-024 5-year outcomes (first-line pembrolizumab vs chemo, PD-L1 TPS ≥50%): [Annals of Oncology](https://www.annalsofoncology.org/article/S0923-7534(20)42366-X/fulltext) · [J Clin Oncol](https://ascopubs.org/doi/10.1200/JCO.21.00174)
- FDA — first-line pembrolizumab NSCLC indication & PD-L1 22C3 testing: [fda.gov](https://www.fda.gov/drugs/fda-expands-pembrolizumab-indication-first-line-treatment-nsclc-tps-1)
- FDA — tisagenlecleucel (Kymriah) approval for pediatric/young-adult r/r B-ALL (≤25 yr, ≥2nd relapse/refractory): [fda.gov](https://www.fda.gov/drugs/resources-information-approved-drugs/fda-approves-tisagenlecleucel-b-cell-all-and-tocilizumab-cytokine-release-syndrome) · [Novartis](https://www.novartis.com/news/media-releases/novartis-receives-first-ever-fda-approval-car-t-cell-therapy-kymriahtm-ctl019-children-and-young-adults-b-cell-all-refractory-or-has-relapsed-least-twice)
- Kymriah pricing ($475k infusion; ~$547k yr-1 total; CRS rates): [OncLive](https://www.onclive.com/view/novartis-sets-a-price-of-475000-for-car-tcell-therapy)
- ICD-10 references (`C34.11`, `C91.02`): [icd10data C34](https://www.icd10data.com/ICD10CM/Codes/C00-D49/C30-C39/C34-) · [AAPC C34](https://www.aapc.com/codes/icd-10-codes/C34)

*Cases v1 — researched 2026-07-20 against public labels/trials/coding refs. Costs and criteria are point-in-time; confirm current NCCN/FDA/payer policy before any real use.*
