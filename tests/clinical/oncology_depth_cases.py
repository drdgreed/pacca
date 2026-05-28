"""
Oncology depth cases — iter-6 oncology specialty expansion to 10 cases.

WHY THESE EXIST
---------------
At iter-5 close, oncology had 7 cases (NSCLC + GC-008/009/011/015/020 +
GC-026 radiation + GC-033 breast/fertility-overlap). This file adds 6
more covering distinct cancer types, treatment modalities, and disease
phases:

  GC-083  Multiple myeloma daratumumab + lenalidomide     AUTO_APPROVED
  GC-084  Ovarian cancer PARP maintenance after platinum  AUTO_APPROVED
  GC-085  Head/neck cancer cetuximab + radiation          AUTO_APPROVED
  GC-086  Metastatic melanoma BRAF/MEK targeted therapy   AUTO_APPROVED
  GC-087  Prostate cancer abiraterone (mCRPC after ADT)   AUTO_APPROVED
  GC-088  Hepatocellular cancer atezolizumab + bevacizumab AUTO_APPROVED
"""

from __future__ import annotations

from tests.clinical.golden_cases import (
    EscalationBranch,
    ExpectedOutcome,
    GoldenCase,
)

ONCOLOGY_DEPTH_CASES: list[GoldenCase] = [
    GoldenCase(
        case_id="GC-083",
        title="Multiple myeloma — daratumumab + lenalidomide + dex per NCCN",
        diagnosis_code="C90.00",
        diagnosis_description="Multiple myeloma not having achieved remission",
        procedure_code="J9145",
        procedure_description="Daratumumab (Darzalex) injection",
        clinical_notes=(
            "63-year-old male, newly-diagnosed multiple myeloma, transplant-"
            "eligible. ISS Stage II. Cytogenetics: standard risk (no high-"
            "risk markers). ECOG 1. Hematology/oncology recommending "
            "DRd (daratumumab + lenalidomide + dexamethasone) induction "
            "with planned autologous stem cell transplant after 4 cycles."
        ),
        guidelines_context=(
            "NCCN Multiple Myeloma Guidelines: DRd is Category 1 for "
            "transplant-eligible NDMM. Quadruplet regimens (Dara-VRd) are "
            "also Category 1. Routine coverage."
        ),
        expected_outcome=ExpectedOutcome.AUTO_APPROVED,
        expected_branch=EscalationBranch.BRANCH_1_AUTO_APPROVE,
        reasoning_must_include=["myeloma", "daratumumab", "NCCN"],
        reasoning_must_not_include=["experimental"],
        clinical_rationale="NCCN Category 1 induction for NDMM. Clean approve.",
        judge_scoring_criteria="Score highly if rationale cites NCCN Category 1 for DRd.",
    ),
    GoldenCase(
        case_id="GC-084",
        title="Ovarian cancer PARP maintenance after platinum response — clean approve",
        diagnosis_code="C56.9",
        diagnosis_description="Malignant neoplasm of unspecified ovary",
        procedure_code="J8499",
        procedure_description="Olaparib (Lynparza) oral capsules",
        clinical_notes=(
            "57-year-old female with high-grade serous ovarian cancer, "
            "stage IIIC. Completed first-line carboplatin + paclitaxel with "
            "complete response. BRCA1 germline pathogenic variant confirmed. "
            "Oncologist recommending olaparib maintenance therapy."
        ),
        guidelines_context=(
            "NCCN Ovarian Cancer Guidelines + SOLO-1 / PAOLA-1 trial data: "
            "PARP inhibitor maintenance after platinum response is Category 1 "
            "for BRCA-mutated newly-diagnosed advanced ovarian cancer. "
            "Olaparib is FDA-approved for this indication."
        ),
        expected_outcome=ExpectedOutcome.AUTO_APPROVED,
        expected_branch=EscalationBranch.BRANCH_1_AUTO_APPROVE,
        reasoning_must_include=["BRCA", "PARP", "maintenance"],
        reasoning_must_not_include=["experimental"],
        clinical_rationale="BRCA+ ovarian cancer post-platinum response — clear PARP indication.",
        judge_scoring_criteria="Score highly if rationale cites BRCA status + NCCN Category 1.",
    ),
    GoldenCase(
        case_id="GC-085",
        title="Locally advanced H&N SCC — cetuximab + radiation per NCCN",
        diagnosis_code="C13.9",
        diagnosis_description="Malignant neoplasm of hypopharynx, unspecified",
        procedure_code="J9055",
        procedure_description="Cetuximab (Erbitux) injection",
        clinical_notes=(
            "67-year-old male with locally advanced (T3N2) hypopharyngeal "
            "squamous cell carcinoma. ECOG 1. Renal function impaired "
            "(eGFR 38) — cisplatin not appropriate. Oncology recommending "
            "cetuximab + concurrent radiation as bioradiotherapy alternative."
        ),
        guidelines_context=(
            "NCCN Head and Neck Cancer Guidelines: cetuximab + radiation "
            "(bioradiotherapy) is appropriate for locally advanced disease "
            "when cisplatin is contraindicated (typically renal dysfunction "
            "or hearing impairment)."
        ),
        expected_outcome=ExpectedOutcome.AUTO_APPROVED,
        expected_branch=EscalationBranch.BRANCH_1_AUTO_APPROVE,
        reasoning_must_include=["cetuximab", "cisplatin", "renal"],
        reasoning_must_not_include=["cisplatin first"],
        clinical_rationale="Locally advanced H&N with cisplatin contraindication — bioradiotherapy is NCCN-endorsed alternative.",
        judge_scoring_criteria="Score highly if rationale cites the contraindication and the bioradiotherapy alternative.",
    ),
    GoldenCase(
        case_id="GC-086",
        title="BRAF V600E metastatic melanoma — dabrafenib + trametinib per NCCN",
        diagnosis_code="C43.9",
        diagnosis_description="Malignant melanoma of skin, unspecified",
        procedure_code="J8499",
        procedure_description="Dabrafenib (Tafinlar) oral capsules",
        clinical_notes=(
            "55-year-old female with metastatic cutaneous melanoma, BRAF "
            "V600E mutation confirmed by molecular testing. LDH elevated. "
            "Symptomatic disease (visceral metastases). Oncology recommending "
            "first-line BRAF/MEK combination (dabrafenib + trametinib) for "
            "rapid response in symptomatic patient."
        ),
        guidelines_context=(
            "NCCN Cutaneous Melanoma Guidelines: BRAF/MEK combination is "
            "Category 1 for BRAF V600-mutated advanced melanoma. Preferred "
            "for rapid response in symptomatic disease; checkpoint inhibitors "
            "preferred for asymptomatic disease."
        ),
        expected_outcome=ExpectedOutcome.AUTO_APPROVED,
        expected_branch=EscalationBranch.BRANCH_1_AUTO_APPROVE,
        reasoning_must_include=["BRAF", "melanoma", "targeted"],
        reasoning_must_not_include=["experimental"],
        clinical_rationale="BRAF+ symptomatic melanoma — targeted therapy is NCCN Cat 1.",
        judge_scoring_criteria="Score highly if rationale cites BRAF status + symptom-driven choice.",
    ),
    GoldenCase(
        case_id="GC-087",
        title="mCRPC — abiraterone + prednisone per NCCN",
        diagnosis_code="C61",
        diagnosis_description="Malignant neoplasm of prostate",
        procedure_code="J8499",
        procedure_description="Abiraterone acetate (Zytiga) oral tablets",
        clinical_notes=(
            "70-year-old male with metastatic castration-resistant prostate "
            "cancer (mCRPC). PSA rising on continued ADT (leuprolide). "
            "Bone metastases on bone scan; no visceral disease. ECOG 1. "
            "No prior docetaxel. Oncology recommending abiraterone + "
            "prednisone."
        ),
        guidelines_context=(
            "NCCN Prostate Cancer Guidelines: abiraterone + prednisone is "
            "Category 1 for mCRPC. Coverage routine."
        ),
        expected_outcome=ExpectedOutcome.AUTO_APPROVED,
        expected_branch=EscalationBranch.BRANCH_1_AUTO_APPROVE,
        reasoning_must_include=["mCRPC", "abiraterone", "NCCN"],
        reasoning_must_not_include=["experimental"],
        clinical_rationale="mCRPC with PSA progression on ADT — abiraterone is NCCN Cat 1.",
        judge_scoring_criteria="Score highly if rationale cites mCRPC status + NCCN.",
    ),
    GoldenCase(
        case_id="GC-088",
        title="Hepatocellular carcinoma atezolizumab + bevacizumab per IMbrave150 / NCCN",
        diagnosis_code="C22.0",
        diagnosis_description="Liver cell carcinoma",
        procedure_code="J9022",
        procedure_description="Atezolizumab (Tecentriq) injection",
        clinical_notes=(
            "61-year-old male with advanced HCC (BCLC stage C, not amenable "
            "to locoregional therapy). Child-Pugh A liver function. EGD "
            "completed within 6 months — no varices requiring intervention. "
            "Oncology recommending atezolizumab + bevacizumab per IMbrave150 "
            "regimen."
        ),
        guidelines_context=(
            "NCCN Hepatobiliary Cancers Guidelines + AASLD HCC Guidance: "
            "atezolizumab + bevacizumab is first-line for advanced HCC with "
            "preserved liver function (Child-Pugh A). Pre-treatment EGD to "
            "exclude high-risk varices is the safety standard. Category 1 "
            "recommendation."
        ),
        expected_outcome=ExpectedOutcome.AUTO_APPROVED,
        expected_branch=EscalationBranch.BRANCH_1_AUTO_APPROVE,
        reasoning_must_include=["HCC", "atezolizumab", "Child-Pugh"],
        reasoning_must_not_include=["experimental"],
        clinical_rationale="Advanced HCC with preserved liver function and EGD safety screen — IMbrave150 regimen is Cat 1.",
        judge_scoring_criteria="Score highly if rationale cites Child-Pugh + EGD safety + NCCN.",
    ),
]
