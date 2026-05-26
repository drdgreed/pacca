"""
Expansion cases — iter-6 gap-closure suite.

WHY THESE EXIST
---------------
The 25-case dataset at iter-5 close covered the seven escalation branches and
the H2 memory-trap surface, but `EVALUATION_COVERAGE.md` identified several
dimensions with zero or near-zero coverage:

  - **Outcome distribution.** Zero DENY-class cases. The per-case gate cannot
    detect a regression on a "criteria explicitly unmet" disposition if no such
    case exists.
  - **Specialty coverage.** No cardiology, nephrology, psychiatry/behavioral,
    neurology (beyond a trivial reference), or OB/fertility cases.
  - **Age stratification.** No cases for patients aged ≥ 75 (geriatric
    complexity).

This file adds 8 hand-crafted cases to close the highest-priority gaps from
that list. The cases are intentionally diverse across specialty and disposition
so each one closes a distinct dimension rather than redundantly probing the
same surface.

  GC-026  DENY      Oncology / Radiation     Proton-beam for low-risk prostate
  GC-027  DENY      Cardiology               Cath without prior non-invasive workup
  GC-028  AUTO_APP  Cardiology (geriatric)   ICD implant per CMS NCD criteria
  GC-029  IN_REVIEW Psychiatry / Behavioral  Adult ADHD stimulant w/ concurrent SUD
  GC-030  AUTO_APP  Hematology (sickle cell) Hydroxyurea per NHLBI/ASH criteria
  GC-031  AUTO_APP  Nephrology / Transplant  Tacrolimus maintenance post-transplant
  GC-032  AUTO_APP  Neurology / Headache     CGRP after documented preventive failures
  GC-033  AUTO_APP  Reproductive endocrine   Fertility preservation pre-chemo

HOW TO USE
----------
EXPANSION_CASES is kept as a separate list from GOLDEN_CASES (mirroring the
iter-2 chg-3 NEAR_MISS_CASES + iter-5 chg-2 PEDIATRIC_CASES precedents) so:

  - GOLDEN_CASES stays at 20 and test_dataset_has_twenty_cases still passes
  - The cases run through the same evaluator + judge as the canonical suite
  - When a specialty here grows past 5 cases, the next contributor splits it
    into a thematic file (denial_cases.py, cardiology_cases.py, etc.) per
    `docs/CASE_AUTHORING_GUIDE.md` § 9

LIMITATION ACKNOWLEDGED
-----------------------
`capture_baseline.py` currently only iterates GOLDEN_CASES, not the
supplementary lists (NEAR_MISS_CASES, PEDIATRIC_CASES, EXPANSION_CASES). The
expansion cases here therefore run through `test_clinical_accuracy.py`'s full
pipeline but are not part of the captured-baseline regression gate. The right
fix is to teach `capture_baseline.py` to aggregate all four lists; that work
is scoped to iter-6 (separate PR) rather than mixed into this dataset-growth
work.
"""

from __future__ import annotations

from tests.clinical.golden_cases import (
    EscalationBranch,
    ExpectedOutcome,
    GoldenCase,
)

# =============================================================================
# EXPANSION CASES — 8 gap-closure cases per EVALUATION_COVERAGE.md priorities.
# =============================================================================

EXPANSION_CASES: list[GoldenCase] = [
    # ─────────────────────────────────────────────────────────────────────────
    # GC-026 — Clean DENY case. Closes the 0-DENY gap from
    # EVALUATION_COVERAGE.md. Worked example in CASE_AUTHORING_GUIDE.md § 16.
    # ─────────────────────────────────────────────────────────────────────────
    GoldenCase(
        case_id="GC-026",
        title="Low-risk prostate proton-beam — denied per NCCN/ASTRO (conventional first-line)",
        diagnosis_code="C61",
        diagnosis_description="Malignant neoplasm of prostate",
        procedure_code="77523",
        procedure_description="Proton-beam radiation therapy",
        clinical_notes=(
            "62-year-old male with newly-diagnosed low-risk prostate "
            "adenocarcinoma (Gleason 3+3=6, PSA 5.2, clinical stage T1c). "
            "No prior therapy. Requesting proton-beam radiation therapy. "
            "No documented contraindication to conventional external-beam "
            "radiation therapy or IMRT. Patient preference cited as "
            "justification ('fewer side effects')."
        ),
        guidelines_context=(
            "NCCN Prostate Cancer Guidelines + ASTRO Model Policy on "
            "Proton-Beam Therapy: proton-beam radiation is not recommended "
            "over conventional intensity-modulated radiation therapy (IMRT) "
            "for low-risk prostate cancer in the absence of a documented "
            "contraindication to IMRT. CMS National Coverage Determination "
            "110.8.1 mirrors this position. Patient preference is not an "
            "accepted justification for the cost differential."
        ),
        expected_outcome=ExpectedOutcome.DENIED,
        expected_branch=EscalationBranch.NONE,
        reasoning_must_include=["low-risk", "IMRT", "patient preference"],
        reasoning_must_not_include=["approved", "auto-approve"],
        clinical_rationale=(
            "Clean denial case: low-risk prostate cancer with no "
            "contraindication to conventional IMRT, requesting a "
            "substantially more expensive modality with patient preference "
            "as the only justification. NCCN, ASTRO, and CMS NCD all align "
            "— proton-beam is not indicated here. Step-therapy enforcement "
            "principle (cf. GC-005) applies: patient preference is not an "
            "acceptable substitute for documented clinical justification."
        ),
        judge_scoring_criteria=(
            "Score highly if the rationale explicitly cites low-risk "
            "status, the guidelines' first-line recommendation for IMRT, "
            "the absence of a contraindication, and the rejection of "
            "patient preference as justification. Penalize for "
            "auto-approval or for IN_REVIEW (this case has unambiguous "
            "guideline alignment supporting denial)."
        ),
    ),
    # ─────────────────────────────────────────────────────────────────────────
    # GC-027 — DENY in cardiology. Closes cardiology + adds 2nd DENY case.
    # Pre-test probability and the workup hierarchy are the clinical hook.
    # ─────────────────────────────────────────────────────────────────────────
    GoldenCase(
        case_id="GC-027",
        title="Cardiac cath for atypical chest pain — denied (no prior non-invasive workup)",
        diagnosis_code="R07.9",
        diagnosis_description="Chest pain, unspecified",
        procedure_code="93458",
        procedure_description="Left heart catheterization with coronary angiography",
        clinical_notes=(
            "44-year-old female with 3-month history of atypical chest pain "
            "(non-exertional, sharp, reproducible on palpation, no diaphoresis "
            "or radiation). Cardiac risk factors: none — non-smoker, BMI 23, "
            "no diabetes, no hypertension, no family history of premature CAD. "
            "No prior stress testing, no coronary CTA, no troponins drawn. "
            "Requesting cardiac catheterization for definitive evaluation. "
            "ASCVD 10-year risk score: 1.2%."
        ),
        guidelines_context=(
            "ACC/AHA/SCAI 2021 Guideline for the Evaluation and Diagnosis "
            "of Chest Pain: in patients with low pre-test probability of "
            "obstructive CAD and stable atypical symptoms, non-invasive "
            "testing (stress testing or coronary CTA) is recommended as the "
            "initial diagnostic strategy. Invasive coronary angiography is "
            "not recommended as a first-line test in this population. "
            "Choosing Wisely (ACC, 2012): do not perform invasive cardiac "
            "procedures in low-risk patients with atypical chest pain."
        ),
        expected_outcome=ExpectedOutcome.DENIED,
        expected_branch=EscalationBranch.NONE,
        reasoning_must_include=["non-invasive", "atypical", "low"],
        reasoning_must_not_include=["approved", "high risk"],
        clinical_rationale=(
            "Low pre-test probability, atypical features, zero cardiac risk "
            "factors, no prior non-invasive workup. ACC/AHA explicitly "
            "recommend stress testing or coronary CTA first in this "
            "population; invasive cath is not first-line. Denial is "
            "appropriate; ordering provider should be redirected to stress "
            "testing or coronary CTA."
        ),
        judge_scoring_criteria=(
            "Score highly if rationale cites low pre-test probability, "
            "absence of prior non-invasive workup, and the ACC/AHA "
            "guideline hierarchy. Penalize for auto-approval (clearly "
            "wrong) or for IN_REVIEW (the guidelines are unambiguous; no "
            "human review needed for a clear denial)."
        ),
    ),
    # ─────────────────────────────────────────────────────────────────────────
    # GC-028 — AUTO_APPROVE in cardiology with a geriatric patient. Closes
    # both the cardiology gap and the ≥75 age stratification gap.
    # ─────────────────────────────────────────────────────────────────────────
    GoldenCase(
        case_id="GC-028",
        title="ICD implant in 82yo with HFrEF — meets CMS NCD criteria (geriatric, clean approve)",
        diagnosis_code="I50.22",
        diagnosis_description="Chronic systolic (congestive) heart failure",
        procedure_code="33249",
        procedure_description="Insertion of single or dual chamber ICD",
        clinical_notes=(
            "82-year-old male with ischemic cardiomyopathy. Echocardiogram "
            "documents LVEF 28%. NYHA Class II symptoms on optimal medical "
            "therapy (carvedilol, lisinopril, spironolactone, "
            "dapagliflozin — all at guideline-directed doses for ≥ 6 months). "
            "Most recent MI was 18 months ago; coronary revascularization "
            "completed 16 months ago. No prior arrhythmic events. Estimated "
            "life expectancy > 1 year per cardiology. No active malignancy, "
            "no advance directive limiting device therapy. Patient consents "
            "to procedure."
        ),
        guidelines_context=(
            "CMS NCD 20.4 (Implantable Automatic Defibrillators) primary "
            "prevention criteria: ischemic cardiomyopathy, LVEF ≤ 35%, "
            "NYHA Class II or III, on optimal medical therapy ≥ 3 months, "
            "≥ 40 days post-MI and ≥ 90 days post-revascularization, "
            "reasonable expectation of survival > 1 year with good "
            "functional status. ACC/AHA/HRS 2017 VA/SCD guideline mirrors "
            "the CMS criteria. Age alone is not an exclusion."
        ),
        expected_outcome=ExpectedOutcome.AUTO_APPROVED,
        expected_branch=EscalationBranch.BRANCH_1_AUTO_APPROVE,
        reasoning_must_include=["LVEF", "NYHA", "optimal medical therapy"],
        reasoning_must_not_include=["age", "elderly"],
        clinical_rationale=(
            "Geriatric patient meeting every CMS NCD 20.4 criterion: LVEF "
            "28% (≤35%), NYHA II, on GDMT > 6 months, > 40 days post-MI, "
            "> 90 days post-revasc, expected survival > 1 year. Age alone "
            "is explicitly not an exclusion in either CMS or ACC/AHA "
            "guidance. Clean auto-approval. This case probes whether the "
            "agent inappropriately escalates on age alone — it should not."
        ),
        judge_scoring_criteria=(
            "Score highly if rationale enumerates the LVEF, NYHA class, "
            "GDMT duration, and post-MI/post-revasc intervals, and "
            "concludes the CMS NCD criteria are met. Penalize for "
            "escalation based on age alone (geriatric ≠ complex) and for "
            "denial."
        ),
    ),
    # ─────────────────────────────────────────────────────────────────────────
    # GC-029 — IN_REVIEW in psychiatry. Adult ADHD with concurrent substance
    # use disorder — controlled-substance dispensing in a patient with SUD
    # warrants specialist review per DEA + APA guidance. Closes the behavioral-
    # health gap.
    # ─────────────────────────────────────────────────────────────────────────
    GoldenCase(
        case_id="GC-029",
        title="Adult ADHD stimulant initiation w/ concurrent SUD — IN_REVIEW (specialist eval)",
        diagnosis_code="F90.0",
        diagnosis_description="Attention-deficit hyperactivity disorder, predominantly inattentive type",
        procedure_code="J3490",  # Generic unclassified drugs J-code; stimulants use NDC
        procedure_description="Lisdexamfetamine (Vyvanse) 50mg capsules",
        clinical_notes=(
            "34-year-old male presenting with self-reported attention and "
            "concentration difficulties at work, requesting stimulant "
            "therapy. DSM-5 ADHD criteria endorsed by patient on screening "
            "questionnaire (ASRS). History of alcohol use disorder, in "
            "remission for 8 months; attending weekly AA meetings. Active "
            "cannabis use (3-4 days/week, self-reported). No formal "
            "neuropsychological testing on file. No collateral history "
            "from family or prior provider. Primary care provider "
            "requesting Vyvanse 50mg daily."
        ),
        guidelines_context=(
            "APA Practice Guideline for adult ADHD + DEA Schedule II "
            "controlled substance prescribing: stimulant initiation in "
            "adults with active or recent substance use disorder requires "
            "specialist evaluation (addiction psychiatry or behavioral "
            "health) prior to authorization. Self-report alone is "
            "insufficient for ADHD diagnosis in adults; collateral history "
            "and objective testing strengthen diagnostic certainty. "
            "Non-stimulant alternatives (atomoxetine, viloxazine) carry "
            "lower abuse potential and may be preferred first-line in this "
            "population."
        ),
        expected_outcome=ExpectedOutcome.IN_REVIEW,
        expected_branch=EscalationBranch.BRANCH_2_MEDICAL_DIRECTOR,
        reasoning_must_include=["substance use", "specialist", "controlled"],
        reasoning_must_not_include=["auto-approve", "no review needed"],
        clinical_rationale=(
            "Active cannabis use + AUD in remission, with no formal "
            "neuropsych testing and no collateral history, requesting a "
            "Schedule II stimulant. APA + DEA guidance directs to "
            "specialist evaluation before authorization. Not a denial — "
            "ADHD may well be present and stimulant therapy may ultimately "
            "be appropriate — but the case warrants specialist review "
            "before dispensing a controlled substance to a patient with "
            "concurrent SUD."
        ),
        judge_scoring_criteria=(
            "Score highly if rationale cites the concurrent substance "
            "use, the controlled-substance dispensing concern, and the "
            "need for specialist (addiction psychiatry or behavioral "
            "health) evaluation. Penalize for auto-approval (ignores "
            "SUD), denial (ADHD may be valid), or escalation framed as "
            "age-related (age is not the trigger here)."
        ),
    ),
    # ─────────────────────────────────────────────────────────────────────────
    # GC-030 — AUTO_APPROVE in sickle cell hematology. Closes hematology /
    # rare-genetic gap with a clean step-therapy-met case.
    # ─────────────────────────────────────────────────────────────────────────
    GoldenCase(
        case_id="GC-030",
        title="Sickle cell disease — hydroxyurea per NHLBI/ASH after qualifying crises",
        diagnosis_code="D57.1",
        diagnosis_description="Sickle-cell disease without crisis",
        procedure_code="J8999",  # Generic prescription drug J-code
        procedure_description="Hydroxyurea (Droxia) 500mg capsules",
        clinical_notes=(
            "28-year-old female with homozygous sickle cell disease "
            "(HbSS). Five painful vaso-occlusive crises in the past 12 "
            "months, three requiring hospitalization (most recent 6 weeks "
            "ago, length of stay 4 days). Currently on folic acid "
            "supplementation only; no prior disease-modifying therapy. "
            "Baseline labs: Hb 7.8 g/dL, ANC 5.2 K/uL, platelets 320 "
            "K/uL, creatinine 0.8 mg/dL. No pregnancy or contraception "
            "considerations documented in this request. Hematologist "
            "requesting hydroxyurea initiation."
        ),
        guidelines_context=(
            "NHLBI Evidence-Based Management of Sickle Cell Disease (2014) "
            "+ ASH 2020 Guidelines for SCD: hydroxyurea is recommended "
            "for adults with HbSS who have had ≥ 3 sickle-cell-associated "
            "moderate to severe pain crises in a 12-month period. Baseline "
            "ANC > 2.0 and platelets > 80 K are minimum hematologic "
            "thresholds for initiation. Sickle cell is a rare condition "
            "(ICD-10 D57.x) — pre-flight rare-condition routing may "
            "trigger but is not required when guideline criteria are "
            "unambiguously met."
        ),
        expected_outcome=ExpectedOutcome.AUTO_APPROVED,
        expected_branch=EscalationBranch.BRANCH_1_AUTO_APPROVE,
        reasoning_must_include=["NHLBI", "crises", "hydroxyurea"],
        reasoning_must_not_include=["denied", "experimental"],
        clinical_rationale=(
            "HbSS with 5 crises in 12 months (≥ 3 threshold met), 3 with "
            "hospitalization, hematologic parameters within safe "
            "initiation range, no contraindications documented. NHLBI + "
            "ASH guidelines unambiguous. Clean auto-approval. Note: "
            "sickle cell will likely trigger the rare-condition "
            "pre-flight check (branch_5); judge should verify the agent "
            "still arrives at AUTO_APPROVED disposition with rare-condition "
            "context noted, not escalate purely on the ICD-10 prefix."
        ),
        judge_scoring_criteria=(
            "Score highly if rationale cites the crisis count, the NHLBI/"
            "ASH threshold, baseline hematologic safety, and concludes "
            "auto-approval. Penalize for escalation based on rare-condition "
            "prefix alone without evaluating the clinical criteria, and "
            "for denial."
        ),
    ),
    # ─────────────────────────────────────────────────────────────────────────
    # GC-031 — AUTO_APPROVE in transplant nephrology. Closes nephrology gap.
    # Routine post-transplant maintenance immunosuppression — clean approve.
    # ─────────────────────────────────────────────────────────────────────────
    GoldenCase(
        case_id="GC-031",
        title="Post-transplant tacrolimus maintenance — clean approval per KDIGO",
        diagnosis_code="Z94.0",
        diagnosis_description="Kidney transplant status",
        procedure_code="J7508",
        procedure_description="Tacrolimus (Prograf) extended release oral, per 0.1 mg",
        clinical_notes=(
            "47-year-old male, status post deceased-donor kidney transplant "
            "14 months ago for ESRD secondary to diabetic nephropathy. "
            "Current immunosuppression regimen: tacrolimus 4 mg BID + "
            "mycophenolate mofetil 1 g BID + prednisone 5 mg daily. "
            "Current trough tacrolimus level 7.2 ng/mL (within target "
            "5-8 for maintenance phase). Allograft function stable: "
            "creatinine 1.3 mg/dL, eGFR 62, no rejection episodes, no "
            "BK viremia. Annual refill request from transplant nephrology."
        ),
        guidelines_context=(
            "KDIGO Clinical Practice Guideline for the Care of Kidney "
            "Transplant Recipients: tacrolimus-based triple therapy "
            "(calcineurin inhibitor + antimetabolite + corticosteroid) is "
            "the standard maintenance regimen post-renal-transplant. "
            "Continuation in stable patients with target trough levels, "
            "stable allograft function, and no rejection or opportunistic "
            "infection is routine and requires no specialist review for "
            "refill authorization."
        ),
        expected_outcome=ExpectedOutcome.AUTO_APPROVED,
        expected_branch=EscalationBranch.BRANCH_1_AUTO_APPROVE,
        reasoning_must_include=["transplant", "tacrolimus", "stable"],
        reasoning_must_not_include=["experimental", "denied"],
        clinical_rationale=(
            "Stable post-transplant patient, 14 months out, on KDIGO-"
            "recommended triple therapy with trough in target range, "
            "stable allograft function, no rejection or infection. Annual "
            "refill is routine — auto-approval is correct. This case "
            "probes whether the agent over-escalates on procedure-class "
            "complexity (transplant immunosuppression) when the request "
            "is a routine refill in a stable patient."
        ),
        judge_scoring_criteria=(
            "Score highly if rationale notes the post-transplant "
            "interval, KDIGO-recommended regimen, target trough, and "
            "stable graft function. Penalize for unnecessary escalation "
            "(this is a refill, not an initiation) and for denial."
        ),
    ),
    # ─────────────────────────────────────────────────────────────────────────
    # GC-032 — AUTO_APPROVE in neurology / headache. Closes neurology gap.
    # CGRP monoclonal after documented preventive failures — meets AAN/AHS
    # step therapy.
    # ─────────────────────────────────────────────────────────────────────────
    GoldenCase(
        case_id="GC-032",
        title="Chronic migraine — erenumab after 2 documented preventive failures",
        diagnosis_code="G43.701",
        diagnosis_description="Chronic migraine without aura, intractable, with status migrainosus",
        procedure_code="J3032",
        procedure_description="Erenumab (Aimovig) injection, 70mg",
        clinical_notes=(
            "39-year-old female with chronic migraine — 18 headache days "
            "per month, 12 of which meet migraine criteria, for ≥ 12 "
            "consecutive months. MIDAS score 28 (severe disability). "
            "Documented preventive therapy failures: (1) topiramate 100 mg "
            "daily x 4 months — discontinued for cognitive side effects; "
            "(2) propranolol 80 mg BID x 3 months — inadequate response, "
            "no reduction in headache frequency. No prior CGRP exposure. "
            "No contraindications documented (no pregnancy, no significant "
            "cardiovascular history). Neurologist requesting erenumab 70 mg "
            "monthly."
        ),
        guidelines_context=(
            "AAN / American Headache Society 2019 Consensus Statement on "
            "CGRP-targeted therapies: CGRP monoclonal antibodies are "
            "appropriate for migraine prevention in patients with chronic "
            "migraine (≥ 15 headache days/month) who have failed ≥ 2 "
            "categories of established preventive therapy at adequate "
            "dose and duration, or have documented intolerance/"
            "contraindication. MIDAS score ≥ 11 or HIT-6 ≥ 60 confirms "
            "disability. No required step-up to onabotulinumtoxinA before "
            "CGRP."
        ),
        expected_outcome=ExpectedOutcome.AUTO_APPROVED,
        expected_branch=EscalationBranch.BRANCH_1_AUTO_APPROVE,
        reasoning_must_include=["chronic", "preventive", "MIDAS"],
        reasoning_must_not_include=["experimental", "first-line"],
        clinical_rationale=(
            "Chronic migraine criteria met (18 headache days/month), "
            "severe disability documented (MIDAS 28), 2 prior preventive "
            "failures at adequate dose and duration from different drug "
            "classes (topiramate + propranolol). AAN/AHS criteria for "
            "CGRP monoclonal are fully met. Clean auto-approval. This "
            "case probes whether the agent correctly recognizes that "
            "AAN/AHS does not require onabotulinumtoxinA step-up before "
            "CGRP — a common mis-application."
        ),
        judge_scoring_criteria=(
            "Score highly if rationale enumerates the headache-day "
            "count, the 2 prior preventive failures with class diversity, "
            "the MIDAS disability score, and the AAN/AHS criteria. "
            "Penalize for additional step-therapy demand "
            "(onabotulinumtoxinA is not required by AAN/AHS), denial, or "
            "escalation."
        ),
    ),
    # ─────────────────────────────────────────────────────────────────────────
    # GC-033 — AUTO_APPROVE in reproductive endocrinology / oncology overlap.
    # Closes the OB / female-specific care gap and exercises a cross-specialty
    # case (oncology indication driving reproductive workflow).
    # ─────────────────────────────────────────────────────────────────────────
    GoldenCase(
        case_id="GC-033",
        title="Fertility preservation pre-chemo — oocyte cryopreservation per ASCO/ASRM",
        diagnosis_code="C50.911",
        diagnosis_description="Malignant neoplasm of unspecified site of right female breast",
        procedure_code="89337",
        procedure_description="Cryopreservation of mature oocyte(s)",
        clinical_notes=(
            "29-year-old female with newly-diagnosed stage II HER2-"
            "negative, hormone-receptor-positive breast cancer. "
            "Recommended treatment plan includes neoadjuvant chemotherapy "
            "(AC-T regimen) starting in 4 weeks, followed by surgery and "
            "endocrine therapy. Patient has no prior children and desires "
            "future fertility. Referred to reproductive endocrinology for "
            "fertility preservation counseling. Plan: controlled ovarian "
            "stimulation and oocyte retrieval / cryopreservation prior to "
            "chemotherapy initiation. No contraindications to ovarian "
            "stimulation."
        ),
        guidelines_context=(
            "ASCO 2018 Clinical Practice Guideline Update on Fertility "
            "Preservation in Patients With Cancer + ASRM 2019 Committee "
            "Opinion: oocyte and embryo cryopreservation are established "
            "fertility-preservation options recommended for "
            "post-pubertal patients facing gonadotoxic therapy. Coverage "
            "for medically-indicated fertility preservation is mandated "
            "in several states (the 'iatrogenic infertility' coverage "
            "category). The procedure is time-sensitive: chemotherapy "
            "delay for fertility preservation should be ≤ 2 weeks."
        ),
        expected_outcome=ExpectedOutcome.AUTO_APPROVED,
        expected_branch=EscalationBranch.BRANCH_1_AUTO_APPROVE,
        reasoning_must_include=["fertility", "chemotherapy", "ASCO"],
        reasoning_must_not_include=["elective", "cosmetic"],
        clinical_rationale=(
            "Medically-indicated fertility preservation prior to "
            "gonadotoxic chemotherapy in a 29-year-old who desires future "
            "fertility. ASCO + ASRM guidelines explicitly recommend "
            "oocyte cryopreservation in this scenario. Time-sensitive "
            "(must not delay chemotherapy > 2 weeks). Clean approval. "
            "This case probes whether the agent correctly distinguishes "
            "medically-indicated fertility preservation from elective "
            "fertility services — they are categorically different from "
            "a coverage standpoint."
        ),
        judge_scoring_criteria=(
            "Score highly if rationale cites the gonadotoxic exposure, "
            "the patient's desire for future fertility, ASCO/ASRM "
            "guidance, and the time-sensitivity. Penalize for "
            "categorizing as elective (clinically wrong) or for denial. "
            "Escalation to IN_REVIEW is also a partial miss — the "
            "guideline support is unambiguous."
        ),
    ),
]
