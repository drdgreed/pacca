"""
Geriatric cases — iter-6 Batch D (≥80 geriatric depth to 5).

WHY THESE EXIST
---------------
At iter-5 close, the ≥ 80 age stratum had ZERO cases. Iter-6 expansion_cases
added GC-028 (82yo ICD per CMS NCD AUTO_APPROVED). This file adds 4 more
to reach 5 — within-stratum signal across ophthalmology, oncology with
frailty, elective orthopedics, and renal-replacement shared-decision-making.

  GC-046  85yo cataract surgery                              AUTO_APPROVED
  GC-047  88yo adjuvant chemo, early-stage colon cancer      IN_REVIEW (frailty)
  GC-048  82yo elective total hip arthroplasty               AUTO_APPROVED
  GC-049  84yo dialysis initiation                           IN_REVIEW (GOC)

The cases test the complexity-score model's "age > 75" weight across
specialties — confirming the weight does not over-fire on routine geriatric
care (GC-046, GC-048) while properly triggering for high-stakes decisions
(GC-047, GC-049).
"""

from __future__ import annotations

from tests.clinical.golden_cases import (
    EscalationBranch,
    ExpectedOutcome,
    GoldenCase,
)

GERIATRIC_CASES: list[GoldenCase] = [
    # ─────────────────────────────────────────────────────────────────────────
    # GC-046 — Cataract surgery in 85yo, routine indication.
    # ─────────────────────────────────────────────────────────────────────────
    GoldenCase(
        case_id="GC-046",
        title="Geriatric (85yo) cataract surgery — routine indication, clean approve",
        diagnosis_code="H25.9",
        diagnosis_description="Unspecified age-related cataract",
        procedure_code="66984",
        procedure_description="Extracapsular cataract removal with intraocular lens insertion",
        clinical_notes=(
            "85-year-old female with bilateral age-related cataracts, right "
            "eye visual acuity 20/100 corrected (down from 20/40 two years "
            "ago). Patient reports falls × 2 in past 6 months, attributed in "
            "part to visual impairment. Independent in ADLs, lives alone "
            "with daughter nearby. Ophthalmologist recommending sequential "
            "cataract extraction starting with right eye. No active ocular "
            "comorbidity (no macular degeneration, no glaucoma). Pre-op "
            "clearance from PCP."
        ),
        guidelines_context=(
            "AAO Preferred Practice Pattern for Cataract in the Adult Eye: "
            "cataract surgery is indicated when visual impairment is "
            "interfering with daily activities (driving, reading, falls). "
            "20/40 or worse with documented functional impact meets criteria; "
            "20/100 with falls history clearly meets. Age alone is not an "
            "exclusion. CMS coverage routine."
        ),
        expected_outcome=ExpectedOutcome.AUTO_APPROVED,
        expected_branch=EscalationBranch.BRANCH_1_AUTO_APPROVE,
        reasoning_must_include=["cataract", "visual", "function"],
        reasoning_must_not_include=["age", "elderly", "frailty"],
        clinical_rationale=(
            "Routine geriatric cataract surgery with documented functional "
            "impact (20/100 + falls). Age alone is not an exclusion per "
            "AAO. The complexity-score model's age-weight should NOT push "
            "this to IN_REVIEW — clinical criteria are clear, no comorbidity "
            "complexity, low procedural risk."
        ),
        judge_scoring_criteria=(
            "Score highly if rationale cites the visual acuity, the falls "
            "history, and the AAO criteria. Penalize for escalation based "
            "on age alone — this is the inappropriate over-escalation "
            "failure mode this case exists to probe."
        ),
    ),
    # ─────────────────────────────────────────────────────────────────────────
    # GC-047 — 88yo adjuvant chemo for early-stage colon cancer — frailty review.
    # ─────────────────────────────────────────────────────────────────────────
    GoldenCase(
        case_id="GC-047",
        title="88yo adjuvant chemo for stage III colon cancer — IN_REVIEW for frailty",
        diagnosis_code="C18.7",
        diagnosis_description="Malignant neoplasm of sigmoid colon",
        procedure_code="J9263",
        procedure_description="Oxaliplatin injection (component of FOLFOX regimen)",
        clinical_notes=(
            "88-year-old male, status post sigmoid colectomy 4 weeks ago for "
            "stage III (T3N1) adenocarcinoma. Pathology shows 2/18 positive "
            "lymph nodes. Oncologist proposing adjuvant FOLFOX × 6 months. "
            "Geriatric assessment: G8 score 13 (impaired; threshold ≤ 14 "
            "flags vulnerability). Mild cognitive impairment, lives with "
            "spouse who serves as caregiver. ECOG 1. Comorbidities: HTN, "
            "stage 3 CKD (eGFR 42), prior MI. Patient and family expressed "
            "interest in adjuvant therapy but concerned about toxicity."
        ),
        guidelines_context=(
            "NCCN Colon Cancer Guidelines + SIOG (International Society of "
            "Geriatric Oncology) Consensus: adjuvant chemotherapy in stage "
            "III colon cancer is standard, with absolute survival benefit "
            "diminishing in patients over 80. Comprehensive geriatric "
            "assessment (CGA) is recommended before treatment decisions; "
            "abnormal G8 (≤ 14) warrants multidisciplinary review including "
            "geriatric oncology when available. Dose reduction or capecitabine "
            "monotherapy may be considered as alternatives to full-dose FOLFOX."
        ),
        expected_outcome=ExpectedOutcome.IN_REVIEW,
        expected_branch=EscalationBranch.BRANCH_2_MEDICAL_DIRECTOR,
        reasoning_must_include=["geriatric", "frailty", "G8"],
        reasoning_must_not_include=["auto-approve", "deny based on age"],
        clinical_rationale=(
            "Stage III colon cancer with established adjuvant indication, "
            "but G8 ≤ 14 indicates vulnerability and SIOG/NCCN recommend "
            "geriatric oncology review and consideration of modified regimen. "
            "Not a denial — therapy may proceed — but multidisciplinary "
            "specialist review is appropriate."
        ),
        judge_scoring_criteria=(
            "Score highly if rationale identifies the G8 score, comorbidities, "
            "and the SIOG/NCCN recommendation for geriatric oncology review. "
            "Penalize for auto-approval (ignores frailty assessment), denial "
            "(adjuvant indication is established), or escalation framed as "
            "cost or memory rather than clinical complexity."
        ),
    ),
    # ─────────────────────────────────────────────────────────────────────────
    # GC-048 — 82yo elective total hip arthroplasty per AAOS.
    # ─────────────────────────────────────────────────────────────────────────
    GoldenCase(
        case_id="GC-048",
        title="82yo elective total hip arthroplasty — clean approve per AAOS",
        diagnosis_code="M16.11",
        diagnosis_description="Unilateral primary osteoarthritis, right hip",
        procedure_code="27130",
        procedure_description="Arthroplasty, acetabular and proximal femoral prosthetic replacement",
        clinical_notes=(
            "82-year-old female with end-stage right hip osteoarthritis. "
            "HOOS score 28 (severe disability). Failed conservative management: "
            "NSAIDs (poor renal tolerance), physical therapy × 12 weeks, "
            "intra-articular corticosteroid × 2 (transient benefit only). "
            "Independent in ADLs, lives with spouse, walks with cane. "
            "Comorbidities: HTN controlled, mild CKD. ASA Physical Status 2. "
            "Orthopedic surgeon recommending elective THA. Pre-op clearance "
            "completed."
        ),
        guidelines_context=(
            "AAOS Clinical Practice Guideline for the Management of "
            "Osteoarthritis of the Hip: total hip arthroplasty is indicated "
            "for end-stage symptomatic osteoarthritis after failure of "
            "appropriate non-operative management. Age is not a contraindication "
            "in fit patients (ASA ≤ 2-3). Pre-op medical clearance documented. "
            "CMS coverage routine."
        ),
        expected_outcome=ExpectedOutcome.AUTO_APPROVED,
        expected_branch=EscalationBranch.BRANCH_1_AUTO_APPROVE,
        reasoning_must_include=["osteoarthritis", "conservative", "AAOS"],
        reasoning_must_not_include=["age", "elderly", "frailty"],
        clinical_rationale=(
            "End-stage hip OA with documented failure of conservative "
            "management, ASA 2 patient, independent in ADLs. Clean approve. "
            "Tests that the complexity-score model does not over-escalate "
            "on age alone when the rest of the case is straightforward."
        ),
        judge_scoring_criteria=(
            "Score highly if rationale cites the HOOS severity, the "
            "conservative-therapy trial, the ASA status, and the AAOS "
            "indication. Penalize for escalation purely on age."
        ),
    ),
    # ─────────────────────────────────────────────────────────────────────────
    # GC-049 — 84yo dialysis initiation — shared-decision-making review.
    # ─────────────────────────────────────────────────────────────────────────
    GoldenCase(
        case_id="GC-049",
        title="84yo dialysis initiation — IN_REVIEW for goals-of-care + shared decision-making",
        diagnosis_code="N18.6",
        diagnosis_description="End stage renal disease",
        procedure_code="90935",
        procedure_description="Hemodialysis procedure with single evaluation by physician",
        clinical_notes=(
            "84-year-old male with ESRD (eGFR 8, advancing despite "
            "conservative management). Comorbidities: ischemic cardiomyopathy "
            "(LVEF 30%), diabetic neuropathy, mild dementia (MMSE 22), "
            "moderate frailty (Clinical Frailty Scale 5). Lives in skilled "
            "nursing facility. Family meeting documented: patient expresses "
            "ambivalence between dialysis and conservative kidney management; "
            "family divided. Nephrology requesting initiation of "
            "thrice-weekly in-center hemodialysis; palliative care "
            "involvement not documented."
        ),
        guidelines_context=(
            "KDIGO ESRD Clinical Practice Guidelines + Renal Physicians "
            "Association Shared Decision-Making Guideline: dialysis initiation "
            "in patients > 80 with multiple comorbidities and limited "
            "functional reserve warrants documented shared decision-making "
            "(SDM) discussion comparing dialysis to conservative kidney "
            "management. Outcomes data show no survival benefit of dialysis "
            "over conservative management in this population in some studies; "
            "decision is preference-sensitive. Palliative care consultation "
            "recommended."
        ),
        expected_outcome=ExpectedOutcome.IN_REVIEW,
        expected_branch=EscalationBranch.BRANCH_2_MEDICAL_DIRECTOR,
        reasoning_must_include=["shared decision", "goals", "palliative"],
        reasoning_must_not_include=["auto-approve", "routine"],
        clinical_rationale=(
            "Geriatric, multi-comorbid, frail patient with ambivalence and "
            "family disagreement. KDIGO + RPA SDM Guideline directs to "
            "specialist (palliative care + nephrology + SDM process) review "
            "before dialysis initiation. Not a denial — dialysis may be the "
            "right choice — but the SDM process is required and not yet "
            "documented."
        ),
        judge_scoring_criteria=(
            "Score highly if rationale identifies the frailty, comorbidity, "
            "ambivalence, and the SDM/palliative care guideline. Penalize "
            "for auto-approval (ignores SDM), denial (dialysis may be "
            "appropriate), or escalation framed as cost."
        ),
    ),
]
