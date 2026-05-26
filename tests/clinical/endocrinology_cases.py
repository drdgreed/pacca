"""
Endocrinology cases — iter-6 Batch K (endo depth to 4 beyond T2DM GC-003).

  GC-076  Thyroid cancer RAI ablation per ATA              AUTO_APPROVED
  GC-077  Cushing's syndrome workup MRI (sequential)       IN_REVIEW
  GC-078  Pheochromocytoma adrenalectomy                   AUTO_APPROVED
"""

from __future__ import annotations

from tests.clinical.golden_cases import (
    EscalationBranch,
    ExpectedOutcome,
    GoldenCase,
)

ENDOCRINOLOGY_CASES: list[GoldenCase] = [
    GoldenCase(
        case_id="GC-076",
        title="Thyroid cancer RAI ablation after total thyroidectomy — clean approve per ATA",
        diagnosis_code="C73",
        diagnosis_description="Malignant neoplasm of thyroid gland",
        procedure_code="79005",
        procedure_description="Radiopharmaceutical therapy, oral (I-131 ablation)",
        clinical_notes=(
            "48-year-old female, status post total thyroidectomy 6 weeks ago "
            "for papillary thyroid carcinoma (4.2 cm primary, 5 of 12 cervical "
            "lymph nodes positive, extrathyroidal extension). Intermediate-"
            "to-high recurrence risk per ATA stratification. Stimulated "
            "thyroglobulin elevated. Endocrinology recommending I-131 RAI "
            "ablation 100 mCi following 4-week LT4 withdrawal protocol."
        ),
        guidelines_context=(
            "ATA Management Guidelines for Adult Patients with Thyroid "
            "Nodules and Differentiated Thyroid Cancer: RAI ablation is "
            "recommended for intermediate-to-high-risk DTC after total "
            "thyroidectomy. Dose 30-150 mCi based on risk. Routine "
            "coverage."
        ),
        expected_outcome=ExpectedOutcome.AUTO_APPROVED,
        expected_branch=EscalationBranch.BRANCH_1_AUTO_APPROVE,
        reasoning_must_include=["thyroid", "RAI", "ATA"],
        reasoning_must_not_include=["experimental", "denied"],
        clinical_rationale=(
            "Intermediate-to-high-risk DTC with positive nodes + ETE — clear "
            "ATA indication for adjuvant RAI. Clean approve."
        ),
        judge_scoring_criteria=(
            "Score highly if rationale cites the risk stratification and ATA guidelines."
        ),
    ),
    GoldenCase(
        case_id="GC-077",
        title="Cushing's workup adrenal MRI — IN_REVIEW (sequential workup)",
        diagnosis_code="E27.9",
        diagnosis_description="Disorder of adrenal gland, unspecified",
        procedure_code="74181",
        procedure_description="MRI abdomen without contrast",
        clinical_notes=(
            "39-year-old female with suspected Cushing's syndrome (weight "
            "gain, hypertension, glucose intolerance, easy bruising). "
            "Initial workup: late-night salivary cortisol elevated (1.2 "
            "μg/dL). 24-hour urinary free cortisol pending. Dexamethasone "
            "suppression test not yet completed. PCP requesting adrenal "
            "MRI without prior biochemical confirmation of hypercortisolism "
            "or ACTH measurement to determine ACTH-dependent vs -independent."
        ),
        guidelines_context=(
            "Endocrine Society Clinical Practice Guideline for the Diagnosis "
            "of Cushing's Syndrome: imaging follows biochemical confirmation. "
            "Sequence: (1) confirm hypercortisolism via 2-3 first-line "
            "tests (UFC, late-night salivary cortisol, 1-mg DST), (2) "
            "measure ACTH to determine dependent vs independent, (3) "
            "directed imaging (adrenal CT/MRI for ACTH-independent; pituitary "
            "MRI for ACTH-dependent). Imaging before biochemical work-up "
            "is premature."
        ),
        expected_outcome=ExpectedOutcome.IN_REVIEW,
        expected_branch=EscalationBranch.BRANCH_3_LOW_CONFIDENCE,
        reasoning_must_include=["sequential", "biochemical", "ACTH"],
        reasoning_must_not_include=["approved", "imaging first"],
        clinical_rationale=(
            "Premature imaging — biochemical workup is incomplete, ACTH not "
            "measured. Endocrine Society guideline directs to complete "
            "biochemical workup first. Request clarification rather than "
            "approve premature imaging."
        ),
        judge_scoring_criteria=(
            "Score highly if rationale identifies the missing biochemical "
            "workup and ACTH measurement and recommends completion before "
            "imaging."
        ),
    ),
    GoldenCase(
        case_id="GC-078",
        title="Pheochromocytoma laparoscopic adrenalectomy — clean approve per Endo Society",
        diagnosis_code="D35.0",
        diagnosis_description="Benign neoplasm of adrenal gland",
        procedure_code="60650",
        procedure_description="Laparoscopic adrenalectomy",
        clinical_notes=(
            "51-year-old female with biochemically confirmed pheochromocytoma "
            "(plasma metanephrines 4× upper limit; 24-hour urinary "
            "metanephrines elevated). Adrenal CT shows 4.5 cm right "
            "adrenal mass with classic imaging features. MIBG scan "
            "consistent. Pre-operative alpha-adrenergic blockade (phenoxybenzamine) "
            "× 14 days completed with orthostatic hypotension target met. "
            "Endocrine surgery recommending laparoscopic adrenalectomy."
        ),
        guidelines_context=(
            "Endocrine Society Clinical Practice Guideline for "
            "Pheochromocytoma and Paraganglioma: surgical resection is "
            "curative for unilateral disease after appropriate biochemical "
            "diagnosis, imaging localization, and pre-op alpha-blockade. "
            "Laparoscopic approach is standard for tumors < 6 cm."
        ),
        expected_outcome=ExpectedOutcome.AUTO_APPROVED,
        expected_branch=EscalationBranch.BRANCH_1_AUTO_APPROVE,
        reasoning_must_include=["pheochromocytoma", "alpha-blockade", "laparoscopic"],
        reasoning_must_not_include=["experimental", "open required"],
        clinical_rationale=(
            "Biochemically confirmed pheochromocytoma with appropriate "
            "pre-op alpha-blockade. Laparoscopic adrenalectomy is standard "
            "for < 6 cm tumors. Clean approve."
        ),
        judge_scoring_criteria=(
            "Score highly if rationale cites the biochemical confirmation, "
            "alpha-blockade, and laparoscopic indication."
        ),
    ),
]
