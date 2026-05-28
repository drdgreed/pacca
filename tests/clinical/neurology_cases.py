"""
Neurology cases — iter-6 Batch I (neurology depth to 5).

WHY THESE EXIST
---------------
At iter-5 close, neurology had ZERO cases. Iter-6 expansion_cases added
GC-032 (chronic migraine CGRP AUTO_APPROVED). This file adds 4 more to
reach 5 — coverage across MS DMT, novel Alzheimer's therapy with REMS,
epilepsy devices, and acute-stroke urgent workflow.

  GC-064  Ocrelizumab for relapsing MS                    AUTO_APPROVED
  GC-065  Lecanemab for early Alzheimer's (REMS + MRI)    IN_REVIEW
  GC-066  VNS for refractory focal epilepsy after AEDs    IN_REVIEW
  GC-067  IV thrombolysis for acute ischemic stroke       AUTO_APPROVED
"""

from __future__ import annotations

from tests.clinical.golden_cases import (
    EscalationBranch,
    ExpectedOutcome,
    GoldenCase,
)

NEUROLOGY_CASES: list[GoldenCase] = [
    # ─────────────────────────────────────────────────────────────────────────
    # GC-064 — Ocrelizumab for relapsing MS.
    # ─────────────────────────────────────────────────────────────────────────
    GoldenCase(
        case_id="GC-064",
        title="Ocrelizumab for relapsing MS — clean approve per AAN/MS Society",
        diagnosis_code="G35",
        diagnosis_description="Multiple sclerosis",
        procedure_code="J2350",
        procedure_description="Ocrelizumab (Ocrevus) injection",
        clinical_notes=(
            "29-year-old female with relapsing-remitting MS, diagnosed 18 "
            "months ago. Three clinical relapses in past 12 months, two "
            "with incomplete recovery. EDSS 2.5 (baseline 1.0). MRI: "
            "8 new T2 lesions and 3 enhancing lesions on recent surveillance. "
            "No prior DMT exposure. JC virus antibody status: negative. "
            "Neurologist recommending ocrelizumab as initial high-efficacy "
            "DMT given highly active disease course."
        ),
        guidelines_context=(
            "AAN Practice Guideline: Disease-Modifying Therapies for Adults "
            "with MS + National MS Society Brain Health Recommendations: "
            "high-efficacy DMTs (anti-CD20 monoclonals, including ocrelizumab "
            "and ofatumumab; or natalizumab in JCV-negative) are appropriate "
            "first-line in patients with highly active disease (≥ 2 relapses "
            "or new MRI activity in past year, with documented EDSS or MRI "
            "progression). Recent shift in MS care emphasizes early high-"
            "efficacy over escalation from platform DMTs."
        ),
        expected_outcome=ExpectedOutcome.AUTO_APPROVED,
        expected_branch=EscalationBranch.BRANCH_1_AUTO_APPROVE,
        reasoning_must_include=["MS", "relapse", "high-efficacy"],
        reasoning_must_not_include=["platform DMT first", "experimental"],
        clinical_rationale=(
            "Highly active RRMS with documented relapses, EDSS progression, "
            "MRI activity, and negative JCV — textbook indication for "
            "first-line high-efficacy DMT. AAN/NMSS criteria met. Clean "
            "approve. Tests that the agent does NOT demand platform DMT "
            "step-therapy (older guidance, now superseded)."
        ),
        judge_scoring_criteria=(
            "Score highly if rationale cites the relapse count, EDSS "
            "progression, MRI activity, and the current AAN guidance "
            "supporting first-line high-efficacy. Penalize for demanding "
            "platform DMT trial first, or for escalation."
        ),
    ),
    # ─────────────────────────────────────────────────────────────────────────
    # GC-065 — Lecanemab for early Alzheimer's; REMS + MRI monitoring.
    # ─────────────────────────────────────────────────────────────────────────
    GoldenCase(
        case_id="GC-065",
        title="Lecanemab for early Alzheimer's — IN_REVIEW per FDA REMS + MRI surveillance",
        diagnosis_code="G30.0",
        diagnosis_description="Alzheimer's disease with early onset",
        procedure_code="J0174",
        procedure_description="Lecanemab (Leqembi) injection",
        clinical_notes=(
            "68-year-old male with mild cognitive impairment due to "
            "Alzheimer's disease (CDR 0.5, MMSE 24). Amyloid PET positive. "
            "Tau PET positive. APOE genotype: heterozygous ε4 (one copy). "
            "MRI brain: no significant microhemorrhages (< 4), no "
            "superficial siderosis. No concurrent anticoagulant therapy. "
            "Neurologist requesting lecanemab biweekly infusions."
        ),
        guidelines_context=(
            "FDA-approved label + AAN Position Statement on Anti-Amyloid "
            "Therapy: lecanemab is approved for early symptomatic AD with "
            "biomarker confirmation. APOE ε4 carriers have higher ARIA "
            "(amyloid-related imaging abnormality) risk; APOE ε4 homozygotes "
            "have notably higher risk and require informed-consent "
            "documentation per FDA. REMS-like surveillance with MRI at "
            "baseline, prior to 5th, 7th, and 14th infusions. Coverage "
            "policies typically require specialist (neurology or memory "
            "clinic) oversight + documented MRI surveillance plan."
        ),
        expected_outcome=ExpectedOutcome.IN_REVIEW,
        expected_branch=EscalationBranch.BRANCH_2_MEDICAL_DIRECTOR,
        reasoning_must_include=["MRI", "ARIA", "APOE"],
        reasoning_must_not_include=["auto-approve", "routine"],
        clinical_rationale=(
            "Lecanemab requires structured MRI surveillance for ARIA, with "
            "APOE-modified risk discussion. The clinical criteria for early "
            "AD are met (amyloid +, CDR 0.5), but the FDA-mandated "
            "surveillance pathway + specialist oversight triggers IN_REVIEW. "
            "Not a denial — therapy may proceed under appropriate oversight."
        ),
        judge_scoring_criteria=(
            "Score highly if rationale identifies the ARIA risk, APOE "
            "implications, MRI surveillance requirement, and the need for "
            "specialist oversight. Penalize for auto-approval (ignores "
            "surveillance gate), denial (therapy is FDA-approved), or "
            "framing purely as a cost trigger."
        ),
    ),
    # ─────────────────────────────────────────────────────────────────────────
    # GC-066 — VNS for refractory focal epilepsy after multiple AEDs.
    # ─────────────────────────────────────────────────────────────────────────
    GoldenCase(
        case_id="GC-066",
        title="VNS for refractory focal epilepsy after 3 AED failures — IN_REVIEW per AAN",
        diagnosis_code="G40.219",
        diagnosis_description="Localization-related symptomatic epilepsy with complex partial seizures, intractable",
        procedure_code="64568",
        procedure_description="Incision for implantation of cranial nerve neurostimulator electrode array",
        clinical_notes=(
            "31-year-old male with refractory focal epilepsy x 12 years. "
            "Adequate trials of carbamazepine, lamotrigine, and levetiracetam "
            "(at maximally tolerated doses, ≥ 6 months each) — all with "
            "inadequate seizure control. Continued seizure frequency 4-6/month "
            "interfering with employment. Epilepsy monitoring unit evaluation "
            "completed: not a candidate for resective surgery (bilateral "
            "ictal onset). Neurologist + epileptologist recommending vagus "
            "nerve stimulator implantation."
        ),
        guidelines_context=(
            "AAN Practice Guideline on Vagus Nerve Stimulation + ILAE "
            "Position: VNS is appropriate adjunctive therapy for medically "
            "refractory focal epilepsy (failed ≥ 2 appropriate AEDs at "
            "adequate dose and duration) in patients not candidates for "
            "resective surgery. Implantation requires epileptologist "
            "evaluation + neurosurgical workup. Device authorization "
            "typically triggers specialist review for surgical risk-benefit."
        ),
        expected_outcome=ExpectedOutcome.IN_REVIEW,
        expected_branch=EscalationBranch.BRANCH_2_MEDICAL_DIRECTOR,
        reasoning_must_include=["VNS", "refractory", "AED"],
        reasoning_must_not_include=["auto-approve", "first-line"],
        clinical_rationale=(
            "Refractory focal epilepsy with documented multiple AED failures, "
            "EMU evaluation complete, not a surgical candidate. Clinical "
            "criteria for VNS are met, but device implantation triggers "
            "specialist (neurosurgery + epileptology) review per policy. "
            "Not a denial — VNS is appropriate — but specialist review "
            "is the surgical-procedure gate."
        ),
        judge_scoring_criteria=(
            "Score highly if rationale enumerates the AED failures, the EMU "
            "evaluation, and the AAN VNS criteria, while noting specialist "
            "review for the device implantation. Penalize for auto-approval "
            "or denial."
        ),
    ),
    # ─────────────────────────────────────────────────────────────────────────
    # GC-067 — IV thrombolysis (tPA) for acute ischemic stroke within window.
    # ─────────────────────────────────────────────────────────────────────────
    GoldenCase(
        case_id="GC-067",
        title="IV thrombolysis for acute ischemic stroke within 3-hour window — auto-approve urgent",
        diagnosis_code="I63.9",
        diagnosis_description="Cerebral infarction, unspecified",
        procedure_code="J2997",
        procedure_description="Alteplase (Activase) injection, recombinant",
        clinical_notes=(
            "58-year-old female presenting to ED 75 minutes after acute "
            "onset of left-sided hemiparesis and aphasia. NIHSS 14. "
            "Non-contrast head CT: no hemorrhage, no large established "
            "infarct (ASPECTS 9). Blood pressure 162/88 (within tPA range). "
            "INR 1.0. No anticoagulant use, no recent surgery, no recent "
            "stroke, no prior intracranial hemorrhage. Inclusion criteria "
            "met; no exclusion criteria identified. Stroke team activating "
            "IV alteplase per protocol."
        ),
        guidelines_context=(
            "AHA/ASA 2019 Guidelines for the Early Management of Acute "
            "Ischemic Stroke: IV alteplase is recommended (Class I) for "
            "eligible patients within 3 hours of symptom onset (extended to "
            "4.5 hours in select patients). Time-sensitive: every minute "
            "of delay = ~2 million neurons lost. Authorization is routine "
            "for emergent administration; delay risks patient outcome."
        ),
        expected_outcome=ExpectedOutcome.AUTO_APPROVED,
        expected_branch=EscalationBranch.BRANCH_1_AUTO_APPROVE,
        reasoning_must_include=["stroke", "alteplase", "time"],
        reasoning_must_not_include=["delayed", "specialist review required"],
        clinical_rationale=(
            "Acute ischemic stroke within the 3-hour window with all "
            "inclusion criteria met and no exclusion criteria. AHA/ASA "
            "Class I indication. Urgent — any escalation introduces "
            "outcome-relevant delay. Auto-approval is correct and "
            "time-critical."
        ),
        judge_scoring_criteria=(
            "Score highly if rationale identifies the time-from-onset, "
            "NIHSS, ASPECTS, absence of contraindications, and the "
            "time-sensitive nature. Penalize HEAVILY for any escalation "
            "or delay framing — this case exists to test that urgent "
            "pathways are NOT mis-routed."
        ),
    ),
]
