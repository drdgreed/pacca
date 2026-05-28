"""
Mental-health cases — iter-6 Batch C (mental health depth to 6).

WHY THESE EXIST
---------------
At iter-5 close, mental health had ZERO cases. Iter-6 expansion_cases added
GC-029 (adult ADHD + concurrent SUD IN_REVIEW). This file adds 5 more to
reach 6 — within-specialty signal across treatment-resistant depression,
REMS-requiring therapies, level-of-care decisions, schizophrenia maintenance,
and adolescent psychopharmacology with safety-monitoring requirements.

  GC-041  TMS for TRD after 2 antidepressant failures   AUTO_APPROVED
  GC-042  Esketamine intranasal for TRD (REMS)          IN_REVIEW
  GC-043  Inpatient psychiatric for active SI w/ plan   AUTO_APPROVED
  GC-044  LAI antipsychotic, schizophrenia + non-adher  AUTO_APPROVED
  GC-045  Adolescent (16yo) MDD SSRI with monitoring    IN_REVIEW
"""

from __future__ import annotations

from tests.clinical.golden_cases import (
    EscalationBranch,
    ExpectedOutcome,
    GoldenCase,
)

MENTAL_HEALTH_CASES: list[GoldenCase] = [
    # ─────────────────────────────────────────────────────────────────────────
    # GC-041 — TMS for treatment-resistant depression after 2 AD failures.
    # ─────────────────────────────────────────────────────────────────────────
    GoldenCase(
        case_id="GC-041",
        title="TMS for treatment-resistant depression — clean approve after 2 AD failures",
        diagnosis_code="F33.2",
        diagnosis_description="Major depressive disorder, recurrent, severe without psychotic features",
        procedure_code="90867",
        procedure_description="Therapeutic repetitive transcranial magnetic stimulation (rTMS) treatment, initial",
        clinical_notes=(
            "47-year-old female with recurrent MDD, current episode severe. "
            "PHQ-9 score 22. Adequate trial of sertraline 200 mg x 12 weeks — "
            "minimal response (PHQ-9 reduction < 30%). Switched to venlafaxine "
            "XR 225 mg x 10 weeks — minimal response. Augmentation with "
            "bupropion 300 mg x 8 weeks — inadequate response. No psychotic "
            "features, no active SI, no contraindications (no seizure history, "
            "no metallic implants near treatment site). Psychiatrist requesting "
            "TMS course."
        ),
        guidelines_context=(
            "APA Practice Guideline for the Treatment of Patients with MDD + "
            "Clinical TMS Society Consensus Review: rTMS is appropriate for "
            "MDD after failure of ≥ 1 antidepressant in current episode; "
            "many payer policies require ≥ 2 adequate trials. Patient has "
            "exceeded both thresholds. CMS NCD recognizes TMS for treatment-"
            "resistant MDD with adequate medication-trial documentation."
        ),
        expected_outcome=ExpectedOutcome.AUTO_APPROVED,
        expected_branch=EscalationBranch.BRANCH_1_AUTO_APPROVE,
        reasoning_must_include=["TMS", "treatment-resistant", "failure"],
        reasoning_must_not_include=["experimental", "first-line"],
        clinical_rationale=(
            "Treatment-resistant MDD with two adequate antidepressant trials "
            "failed plus an augmentation failure. No contraindications. APA "
            "+ CMS NCD criteria met. Clean approve."
        ),
        judge_scoring_criteria=(
            "Score highly if rationale enumerates the antidepressant trials, "
            "the PHQ-9 severity, the absence of contraindications, and "
            "concludes auto-approval. Penalize for additional step-therapy "
            "demand (criteria are met) or for escalation."
        ),
    ),
    # ─────────────────────────────────────────────────────────────────────────
    # GC-042 — Esketamine intranasal for TRD; REMS-requiring → IN_REVIEW.
    # ─────────────────────────────────────────────────────────────────────────
    GoldenCase(
        case_id="GC-042",
        title="Esketamine intranasal for TRD — IN_REVIEW per FDA REMS + specialist requirement",
        diagnosis_code="F33.2",
        diagnosis_description="Major depressive disorder, recurrent, severe without psychotic features",
        procedure_code="S0013",
        procedure_description="Esketamine (Spravato) nasal spray, per dose",
        clinical_notes=(
            "51-year-old male with treatment-resistant MDD. Failed adequate "
            "trials of fluoxetine, duloxetine, and TMS (28-session course). "
            "PHQ-9 currently 19. No active SI but recurrent passive death-"
            "wish ideation. Psychiatrist requesting esketamine intranasal "
            "induction phase. REMS-certified clinic identified for "
            "administration. No contraindications (no recent CV event, no "
            "history of psychosis, no aneurysmal vascular disease)."
        ),
        guidelines_context=(
            "FDA-approved label (esketamine, Spravato) requires the SPRAVATO "
            "REMS program: patient may self-administer ONLY at a certified "
            "healthcare setting with monitoring × 2 hours post-dose. APA "
            "endorses use after failure of ≥ 2 antidepressants. Authorization "
            "of a new REMS-program medication requires specialist (psychiatry) "
            "involvement and verification of certified-clinic enrollment "
            "prior to first dose. Per institutional policy, esketamine "
            "initiation triggers medical-director review for REMS compliance "
            "and risk-benefit confirmation."
        ),
        expected_outcome=ExpectedOutcome.IN_REVIEW,
        expected_branch=EscalationBranch.BRANCH_2_MEDICAL_DIRECTOR,
        reasoning_must_include=["REMS", "certified", "specialist"],
        reasoning_must_not_include=["auto-approve", "routine"],
        clinical_rationale=(
            "Esketamine is REMS-required; the request triggers specialist "
            "review for REMS compliance and risk-benefit confirmation. The "
            "clinical criteria for TRD are met, but the REMS gate is "
            "process-required regardless. Not a denial — appropriate "
            "specialist review."
        ),
        judge_scoring_criteria=(
            "Score highly if rationale identifies the REMS requirement, the "
            "certified-clinic verification step, and concludes specialist "
            "review is appropriate. Penalize for auto-approval (ignores "
            "REMS), denial (clinical criteria are met), or framing as a "
            "cost-trigger (it is REMS, not cost)."
        ),
    ),
    # ─────────────────────────────────────────────────────────────────────────
    # GC-043 — Inpatient psychiatric admission for active SI with plan.
    # ─────────────────────────────────────────────────────────────────────────
    GoldenCase(
        case_id="GC-043",
        title="Inpatient psychiatric admission for active SI with plan — auto-approve",
        diagnosis_code="F32.2",
        diagnosis_description="Major depressive disorder, single episode, severe without psychotic features",
        procedure_code="0124",
        procedure_description="Acute inpatient psychiatric care, per diem",
        clinical_notes=(
            "29-year-old female presenting to ED via family. Active suicidal "
            "ideation with specific plan (overdose with stockpiled "
            "medications, intent to act within 24 hours). Recent psychosocial "
            "stressors (job loss, relationship dissolution). PHQ-9 score 24. "
            "No active substance intoxication. Family unable to provide "
            "constant supervision. Inpatient bed identified at psychiatric "
            "facility; psychiatry consulting service recommending acute "
            "inpatient admission for safety + stabilization."
        ),
        guidelines_context=(
            "APA Practice Guideline for Assessment and Treatment of Patients "
            "with Suicidal Behaviors + CMS InterQual / MCG behavioral health "
            "level-of-care criteria: active SI with specific plan and intent, "
            "absence of adequate outpatient support, meets inpatient "
            "psychiatric level-of-care criteria. Authorization is routine; "
            "delay risks patient safety."
        ),
        expected_outcome=ExpectedOutcome.AUTO_APPROVED,
        expected_branch=EscalationBranch.BRANCH_1_AUTO_APPROVE,
        reasoning_must_include=["suicidal", "plan", "inpatient"],
        reasoning_must_not_include=["outpatient", "denied", "routine outpatient"],
        clinical_rationale=(
            "Active SI with specific plan + intent + means + absence of "
            "outpatient support is the textbook indication for inpatient "
            "psychiatric admission. CMS InterQual / MCG criteria clearly met. "
            "Auto-approval is correct and time-sensitive."
        ),
        judge_scoring_criteria=(
            "Score highly if rationale identifies the active SI with plan, "
            "the absence of adequate outpatient support, and concludes "
            "auto-approval. Penalize for denial (clear safety risk), or for "
            "step-therapy demand (outpatient trial would be inappropriate "
            "given imminent risk)."
        ),
    ),
    # ─────────────────────────────────────────────────────────────────────────
    # GC-044 — Long-acting injectable antipsychotic for schizophrenia + non-adherence.
    # ─────────────────────────────────────────────────────────────────────────
    GoldenCase(
        case_id="GC-044",
        title="LAI antipsychotic for schizophrenia + documented non-adherence — clean approve",
        diagnosis_code="F20.0",
        diagnosis_description="Paranoid schizophrenia",
        procedure_code="J2426",
        procedure_description="Paliperidone palmitate (Invega Sustenna) extended-release injection",
        clinical_notes=(
            "42-year-old male with chronic paranoid schizophrenia, illness "
            "duration 18 years. Three psychiatric hospitalizations in past "
            "24 months, all triggered by medication non-adherence (per "
            "patient self-report + pharmacy refill data showing < 50% MPR "
            "on oral risperidone for the past year). Currently stabilized on "
            "oral risperidone 4 mg daily after most recent discharge. "
            "Psychiatrist transitioning to long-acting injectable paliperidone "
            "for adherence support."
        ),
        guidelines_context=(
            "APA Practice Guideline for the Treatment of Schizophrenia + "
            "WFSBP recommendations: long-acting injectable antipsychotics are "
            "recommended for patients with established non-adherence, "
            "particularly those with recent hospitalizations attributable "
            "to oral-medication interruption. Same molecule continuation "
            "(oral-to-LAI transition for the same active ingredient) is "
            "preferred to avoid cross-titration risk."
        ),
        expected_outcome=ExpectedOutcome.AUTO_APPROVED,
        expected_branch=EscalationBranch.BRANCH_1_AUTO_APPROVE,
        reasoning_must_include=["non-adherence", "long-acting", "hospitalization"],
        reasoning_must_not_include=["experimental", "first-line for new diagnosis"],
        clinical_rationale=(
            "Documented non-adherence on oral risperidone with hospitalization "
            "consequences. Same-molecule transition to LAI (paliperidone is "
            "the active metabolite of risperidone) is the evidence-based "
            "adherence intervention. Clean approve."
        ),
        judge_scoring_criteria=(
            "Score highly if rationale cites the non-adherence history, the "
            "hospitalization pattern, and the APA recommendation for LAI in "
            "this scenario. Penalize for denial or for escalation."
        ),
    ),
    # ─────────────────────────────────────────────────────────────────────────
    # GC-045 — Adolescent (16yo) MDD SSRI initiation — IN_REVIEW for monitoring.
    # ─────────────────────────────────────────────────────────────────────────
    GoldenCase(
        case_id="GC-045",
        title="Adolescent (16yo) MDD SSRI initiation — IN_REVIEW (black box + monitoring)",
        diagnosis_code="F32.1",
        diagnosis_description="Major depressive disorder, single episode, moderate",
        procedure_code="J8499",
        procedure_description="Fluoxetine 20 mg oral",
        clinical_notes=(
            "16-year-old female with new-onset moderate MDD. PHQ-A score 16. "
            "Symptoms x 4 months: anhedonia, sleep disturbance, declining "
            "academic performance, hopelessness. Denies active SI on direct "
            "questioning; passive death-wish ideation present but no plan, "
            "no intent. CBT initiated 4 weeks ago, partial response. Family "
            "support strong. Pediatric psychiatrist requesting fluoxetine "
            "20 mg daily as adjunctive pharmacotherapy. Plan: weekly "
            "follow-up x 4 weeks then biweekly per FDA suicidality-monitoring "
            "guidance."
        ),
        guidelines_context=(
            "FDA black-box warning: SSRIs in pediatric/adolescent patients "
            "carry elevated short-term suicidality risk. Fluoxetine is the "
            "only FDA-approved SSRI for adolescent MDD. AAP + AACAP guidelines "
            "support pharmacotherapy in moderate-to-severe MDD with adequate "
            "monitoring. Institutional policy: pediatric initiation of "
            "antidepressant requires specialist (pediatric psychiatry) "
            "involvement and documented safety-monitoring plan; not a denial, "
            "but a specialist-review gate."
        ),
        expected_outcome=ExpectedOutcome.IN_REVIEW,
        expected_branch=EscalationBranch.BRANCH_2_MEDICAL_DIRECTOR,
        reasoning_must_include=["pediatric", "black box", "monitoring"],
        reasoning_must_not_include=["auto-approve", "routine adult"],
        clinical_rationale=(
            "Adolescent SSRI initiation triggers institutional specialist-"
            "review gate per black-box warning + FDA safety-monitoring "
            "guidance. Not a denial — clinical criteria are met and "
            "fluoxetine is the appropriate first-line — but pediatric "
            "psychiatry oversight + documented monitoring plan is required "
            "before authorization."
        ),
        judge_scoring_criteria=(
            "Score highly if rationale identifies the pediatric age, the "
            "black-box warning, and the need for documented safety-"
            "monitoring. Penalize for auto-approval (ignores pediatric "
            "safety gate), denial (medication is appropriate), or framing "
            "as a cost trigger."
        ),
    ),
]
