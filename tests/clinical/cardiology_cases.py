"""
Cardiology cases — iter-6 Batch B (cardiology depth to 6).

WHY THESE EXIST
---------------
At iter-5 close, cardiology had ZERO cases. Iter-6 expansion_cases added
GC-027 (cath without non-invasive workup DENIED) and GC-028 (ICD per CMS
NCD 20.4 AUTO_APPROVED, geriatric). This file adds 4 more to reach 6 —
within-specialty signal across interventional cardiology, electrophysiology,
preventive cardiology, and threshold-boundary discrimination.

  GC-037  TAVR for severe symptomatic AS              AUTO_APPROVED
  GC-038  AFib catheter ablation after AAD failure    AUTO_APPROVED
  GC-039  ICD primary prevention, LVEF=36% (just over) DENIED
  GC-040  Statin in 38yo with familial hypercholest.  AUTO_APPROVED

GC-039 is a deliberate near-miss to GC-028 (LVEF 28%) — same procedure,
same patient archetype, one disqualifying threshold (LVEF 36% vs 35% CMS
cutoff). Tests threshold-boundary discrimination at a different surface
from GC-021 (NSCLC PD-L1 45% vs 50%).
"""

from __future__ import annotations

from tests.clinical.golden_cases import (
    EscalationBranch,
    ExpectedOutcome,
    GoldenCase,
)

CARDIOLOGY_CASES: list[GoldenCase] = [
    # ─────────────────────────────────────────────────────────────────────────
    # GC-037 — TAVR for severe symptomatic AS, intermediate-risk per STS.
    # ─────────────────────────────────────────────────────────────────────────
    GoldenCase(
        case_id="GC-037",
        title="TAVR for severe symptomatic AS — intermediate STS risk, clean approve",
        diagnosis_code="I35.0",
        diagnosis_description="Nonrheumatic aortic (valve) stenosis",
        procedure_code="33361",
        procedure_description="Transcatheter aortic valve replacement (TAVR), femoral approach",
        clinical_notes=(
            "76-year-old male with severe symptomatic aortic stenosis "
            "(aortic valve area 0.7 cm², mean gradient 48 mmHg, peak velocity "
            "4.4 m/s). NYHA III symptoms (exertional dyspnea, near-syncope). "
            "STS-PROM score 6.2% (intermediate surgical risk). Heart-team "
            "evaluation completed, multidisciplinary recommendation for TAVR "
            "over surgical AVR. Coronary angiography shows no significant CAD. "
            "Femoral access suitable on CT angio. Frailty assessment: not frail."
        ),
        guidelines_context=(
            "ACC/AHA/STS 2020 Guideline for the Management of Patients With "
            "Valvular Heart Disease: TAVR is recommended (Class I) for severe "
            "symptomatic AS in patients with intermediate or high surgical "
            "risk per STS-PROM. Heart-team consensus required and documented. "
            "CMS NCD 20.32 covers TAVR for symptomatic severe AS with heart-"
            "team participation. Intermediate-risk patients age ≥ 65 with "
            "femoral access are appropriate for transfemoral TAVR."
        ),
        expected_outcome=ExpectedOutcome.AUTO_APPROVED,
        expected_branch=EscalationBranch.BRANCH_1_AUTO_APPROVE,
        reasoning_must_include=["TAVR", "heart team", "STS"],
        reasoning_must_not_include=["surgical AVR only", "experimental"],
        clinical_rationale=(
            "Severe symptomatic AS with documented intermediate STS risk and "
            "heart-team consensus. Class I ACC/AHA recommendation. CMS NCD "
            "20.32 criteria met. Clean approve."
        ),
        judge_scoring_criteria=(
            "Score highly if rationale cites the AS severity (AVA, mean "
            "gradient), STS-PROM, heart-team documentation, and the Class I "
            "indication. Penalize for denying or escalating when the "
            "guideline criteria are unambiguously met."
        ),
    ),
    # ─────────────────────────────────────────────────────────────────────────
    # GC-038 — AFib catheter ablation after documented AAD failure.
    # ─────────────────────────────────────────────────────────────────────────
    GoldenCase(
        case_id="GC-038",
        title="AFib catheter ablation after failure of class III antiarrhythmic",
        diagnosis_code="I48.91",
        diagnosis_description="Unspecified atrial fibrillation",
        procedure_code="93656",
        procedure_description="Catheter ablation, atrial fibrillation by pulmonary vein isolation",
        clinical_notes=(
            "58-year-old female with symptomatic paroxysmal atrial fibrillation. "
            "12-month trial of flecainide (Class IC) discontinued for "
            "intolerable side effects. Subsequent 6-month trial of sotalol "
            "(Class III) — inadequate rhythm control with ongoing symptomatic "
            "episodes documented on monitoring. Adequate anticoagulation on "
            "apixaban. CHA₂DS₂-VASc 2. Echocardiogram: normal LV function, no "
            "structural disease, left atrial diameter 4.2 cm. Electrophysiology "
            "consult recommends pulmonary vein isolation."
        ),
        guidelines_context=(
            "ACC/AHA/HRS 2019 Focused Update on AFib: catheter ablation for "
            "rhythm control is reasonable (Class I or IIa depending on "
            "subgroup) for symptomatic paroxysmal AFib after failure of at "
            "least one Class I or III antiarrhythmic. Two-drug failure (one "
            "intolerance + one inefficacy) clearly establishes ablation "
            "eligibility. CMS coverage routine."
        ),
        expected_outcome=ExpectedOutcome.AUTO_APPROVED,
        expected_branch=EscalationBranch.BRANCH_1_AUTO_APPROVE,
        reasoning_must_include=["antiarrhythmic", "failure", "ablation"],
        reasoning_must_not_include=["first-line", "experimental"],
        clinical_rationale=(
            "Symptomatic paroxysmal AFib with documented failure of two "
            "antiarrhythmic agents (one intolerance, one inefficacy). Adequate "
            "anticoagulation. ACC/AHA Class I or IIa indication. Clean approve."
        ),
        judge_scoring_criteria=(
            "Score highly if rationale cites the two-drug failure history, "
            "anticoagulation status, and the ACC/AHA guideline criteria. "
            "Penalize for additional step-therapy demand (two drugs already "
            "failed), or for escalation purely on age."
        ),
    ),
    # ─────────────────────────────────────────────────────────────────────────
    # GC-039 — ICD primary prevention denied: LVEF=36% just over CMS cutoff.
    # Near-miss sibling of GC-028 (LVEF 28% approved).
    # ─────────────────────────────────────────────────────────────────────────
    GoldenCase(
        case_id="GC-039",
        title="ICD denied — LVEF 36% above CMS NCD 20.4 35% cutoff (near-miss to GC-028)",
        diagnosis_code="I50.22",
        diagnosis_description="Chronic systolic (congestive) heart failure",
        procedure_code="33249",
        procedure_description="Insertion of single or dual chamber ICD",
        clinical_notes=(
            "66-year-old male with ischemic cardiomyopathy. Most recent "
            "echocardiogram documents LVEF 36% (two prior echos at 38% and "
            "37% over the past year). NYHA Class II symptoms on optimal "
            "medical therapy x 8 months. MI 12 months ago, revascularization "
            "completed 10 months ago. No syncope, no documented sustained VT, "
            "no prior arrhythmic events. Cardiologist requesting primary-"
            "prevention ICD citing borderline EF and ischemic substrate."
        ),
        guidelines_context=(
            "CMS NCD 20.4 (Implantable Automatic Defibrillators): primary "
            "prevention ICD requires LVEF ≤ 35%, NYHA Class II or III, "
            "ischemic etiology with ≥ 40 days post-MI and ≥ 90 days post-"
            "revascularization, on optimal medical therapy ≥ 3 months. LVEF "
            "is the gating numerical threshold; 36% does NOT meet criterion. "
            "ACC/AHA/HRS 2017 SCD guideline mirrors the CMS cutoff. "
            "Cardiomyopathy with borderline EF without documented sustained "
            "arrhythmia is not an indication."
        ),
        expected_outcome=ExpectedOutcome.DENIED,
        expected_branch=EscalationBranch.NONE,
        reasoning_must_include=["LVEF", "35%", "threshold"],
        reasoning_must_not_include=["meets criteria", "approved"],
        clinical_rationale=(
            "Near-miss sibling of GC-028 (LVEF 28%, approved). LVEF 36% is "
            "above the CMS NCD 20.4 cutoff of 35%; no documented sustained "
            "arrhythmia provides an alternate path. Denial is correct. "
            "Probes whether the agent reads the LVEF number against the "
            "explicit threshold rather than pattern-matching on the ICD-"
            "request shape."
        ),
        judge_scoring_criteria=(
            "Score highly if rationale extracts the LVEF (36%), compares "
            "against the CMS 35% cutoff, and concludes denial. Penalize "
            "for auto-approval (the H2 memory entry for ICD primary prev "
            "could fire on the shape and miss the number) or for IN_REVIEW "
            "(the cutoff is unambiguous)."
        ),
    ),
    # ─────────────────────────────────────────────────────────────────────────
    # GC-040 — Statin for primary prevention in young adult with FH.
    # ─────────────────────────────────────────────────────────────────────────
    GoldenCase(
        case_id="GC-040",
        title="Statin in 38yo with familial hypercholesterolemia — primary prevention approve",
        diagnosis_code="E78.01",
        diagnosis_description="Familial hypercholesterolemia",
        procedure_code="J8499",
        procedure_description="Atorvastatin 40 mg oral",
        clinical_notes=(
            "38-year-old male with heterozygous familial hypercholesterolemia "
            "confirmed by genetic testing (LDLR pathogenic variant). Pre-"
            "treatment LDL-C 248 mg/dL. Family history: father MI age 42, "
            "brother MI age 39. No tobacco, BMI 24, BP normal, no diabetes. "
            "10-year ASCVD risk score does not apply (FH is an exemption). "
            "Lipid clinic requesting atorvastatin 40 mg as first-line statin "
            "with eventual addition of ezetimibe if LDL > 70 after titration."
        ),
        guidelines_context=(
            "ACC/AHA 2018 Cholesterol Guideline + AHA/NLA FH Guidelines: "
            "patients with familial hypercholesterolemia (LDL-C ≥ 190 mg/dL "
            "at baseline OR genetic confirmation) qualify for high-intensity "
            "statin therapy regardless of 10-year ASCVD risk score. Age-based "
            "ASCVD risk thresholds do NOT apply to FH; primary prevention "
            "is indicated as soon as diagnosed."
        ),
        expected_outcome=ExpectedOutcome.AUTO_APPROVED,
        expected_branch=EscalationBranch.BRANCH_1_AUTO_APPROVE,
        reasoning_must_include=["familial", "LDL", "high-intensity"],
        reasoning_must_not_include=["risk score insufficient", "elderly"],
        clinical_rationale=(
            "Genetically-confirmed FH with strong family history and very "
            "elevated baseline LDL. High-intensity statin is first-line; "
            "age and ASCVD calculator do not apply. Clean approve. Probes "
            "that the agent recognizes the FH exemption to age-based ASCVD "
            "thresholds — a common mis-application."
        ),
        judge_scoring_criteria=(
            "Score highly if rationale cites the FH diagnosis, the baseline "
            "LDL, family history, and the ACC/AHA exemption from age-based "
            "ASCVD thresholds. Penalize for denying based on young age (a "
            "frequent mis-application of preventive guidelines) or for "
            "escalating."
        ),
    ),
]
