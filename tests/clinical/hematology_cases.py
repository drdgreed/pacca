"""
Hematology cases — iter-6 Batch L (hematology depth to 5).

WHY THESE EXIST
---------------
Iter-6 expansion_cases added GC-030 (sickle cell hydroxyurea). This file
adds 4 more to reach 5 hematology cases covering: deficiency-anemia,
acute leukemia induction, ITP biologic, urgent anticoagulation reversal.

  GC-079  IV iron sucrose for severe IDA after PO failure  AUTO_APPROVED
  GC-080  AML 7+3 induction chemotherapy                   AUTO_APPROVED
  GC-081  ITP rituximab after steroid failure              AUTO_APPROVED
  GC-082  Warfarin-associated bleed reversal with PCC      AUTO_APPROVED (urgent)
"""

from __future__ import annotations

from tests.clinical.golden_cases import (
    EscalationBranch,
    ExpectedOutcome,
    GoldenCase,
)

HEMATOLOGY_CASES: list[GoldenCase] = [
    GoldenCase(
        case_id="GC-079",
        title="IV iron sucrose for severe IDA after PO iron failure — clean approve",
        diagnosis_code="D50.9",
        diagnosis_description="Iron deficiency anemia, unspecified",
        procedure_code="J1756",
        procedure_description="Iron sucrose injection, 1 mg",
        clinical_notes=(
            "44-year-old female with severe iron-deficiency anemia (Hb 7.8, "
            "ferritin 4, TSAT 3%). 12-week trial of oral ferrous sulfate "
            "325 mg TID — discontinued for intractable GI side effects and "
            "minimal Hb response (Hb increased only 0.4 g/dL). Etiology: "
            "heavy menstrual bleeding (gynecology workup underway). "
            "Hematology requesting IV iron sucrose (1000 mg total dose split)."
        ),
        guidelines_context=(
            "AGA + ASH Guidelines: IV iron is appropriate when PO iron is "
            "ineffective, not tolerated, or inadequate to meet replacement "
            "needs. Severe symptomatic anemia (Hb < 9) supports IV. "
            "Iron sucrose is well-established with no test-dose requirement. "
            "CMS coverage routine."
        ),
        expected_outcome=ExpectedOutcome.AUTO_APPROVED,
        expected_branch=EscalationBranch.BRANCH_1_AUTO_APPROVE,
        reasoning_must_include=["iron", "PO", "failure"],
        reasoning_must_not_include=["experimental", "denied"],
        clinical_rationale=(
            "Severe IDA with documented PO iron intolerance + minimal "
            "response. AGA/ASH criteria for IV iron clearly met."
        ),
        judge_scoring_criteria=(
            "Score highly if rationale cites the severity, the PO failure, "
            "and the AGA/ASH criteria. Penalize for demanding additional "
            "PO trial."
        ),
    ),
    GoldenCase(
        case_id="GC-080",
        title="AML 7+3 induction chemotherapy — auto-approve per NCCN",
        diagnosis_code="C92.00",
        diagnosis_description="Acute myeloblastic leukemia, not having achieved remission",
        procedure_code="J9000",
        procedure_description="Doxorubicin HCl injection (component of 7+3 induction)",
        clinical_notes=(
            "52-year-old male, newly diagnosed AML with intermediate-risk "
            "cytogenetics (normal karyotype, NPM1+ FLT3-). ECOG 1. No "
            "significant comorbidities. Hematology/oncology recommending "
            "standard 7+3 induction (cytarabine continuous infusion × 7 "
            "days + idarubicin × 3 days). Bone marrow biopsy pre-treatment "
            "documented. Transplant consultation initiated for post-remission "
            "planning."
        ),
        guidelines_context=(
            "NCCN AML Guidelines: standard induction for fit adults with "
            "newly-diagnosed non-APL AML is '7+3' (cytarabine + anthracycline). "
            "Category 1 recommendation for intermediate-risk cytogenetics in "
            "patients ≤ 60. CMS coverage routine."
        ),
        expected_outcome=ExpectedOutcome.AUTO_APPROVED,
        expected_branch=EscalationBranch.BRANCH_1_AUTO_APPROVE,
        reasoning_must_include=["AML", "induction", "NCCN"],
        reasoning_must_not_include=["experimental", "delayed"],
        clinical_rationale=(
            "Newly-diagnosed AML in a fit adult — 7+3 is NCCN Category 1 "
            "first-line induction. Time-sensitive; clean approve."
        ),
        judge_scoring_criteria=(
            "Score highly if rationale cites the diagnosis, cytogenetics "
            "risk, fitness, and NCCN Category 1. Penalize for escalation "
            "(time-sensitive) or denial."
        ),
    ),
    GoldenCase(
        case_id="GC-081",
        title="ITP rituximab after corticosteroid failure — clean approve per ASH 2019",
        diagnosis_code="D69.3",
        diagnosis_description="Immune thrombocytopenic purpura",
        procedure_code="J9312",
        procedure_description="Rituximab (Rituxan) injection",
        clinical_notes=(
            "38-year-old female with chronic ITP (platelet count 18 K/uL). "
            "Failed adequate trial of prednisone 1 mg/kg/day × 6 weeks (no "
            "durable response after taper). Failed 3-day IVIG (transient "
            "response only). Bleeding symptoms: easy bruising, occasional "
            "epistaxis. Hematology requesting rituximab as second-line "
            "ITP therapy."
        ),
        guidelines_context=(
            "ASH 2019 Guidelines for ITP: in adults with ITP and platelet "
            "count < 30 K/uL who have failed corticosteroids, rituximab is "
            "an appropriate second-line option (alongside TPO-RAs and "
            "splenectomy). Choice typically driven by patient preference, "
            "comorbidity, and reproductive plans."
        ),
        expected_outcome=ExpectedOutcome.AUTO_APPROVED,
        expected_branch=EscalationBranch.BRANCH_1_AUTO_APPROVE,
        reasoning_must_include=["ITP", "rituximab", "second-line"],
        reasoning_must_not_include=["first-line", "experimental"],
        clinical_rationale=(
            "Chronic ITP with documented steroid + IVIG failure; rituximab "
            "is ASH-endorsed second-line. Clean approve."
        ),
        judge_scoring_criteria=(
            "Score highly if rationale cites the platelet count, prior "
            "therapy failures, and ASH 2019 second-line endorsement. "
            "Penalize for demanding splenectomy first."
        ),
    ),
    GoldenCase(
        case_id="GC-082",
        title="Warfarin-associated intracranial bleed — PCC reversal (auto-approve urgent)",
        diagnosis_code="T45.515A",
        diagnosis_description="Adverse effect of anticoagulants, initial encounter",
        procedure_code="J7168",
        procedure_description="Prothrombin complex concentrate, 4-factor (Kcentra)",
        clinical_notes=(
            "72-year-old female on warfarin for AFib presents to ED with "
            "spontaneous intracerebral hemorrhage. CT confirms 18 mL "
            "intraparenchymal hematoma. INR on arrival 3.8. Vitamin K "
            "10 mg IV given; ED + neurosurgery requesting 4-factor PCC "
            "(Kcentra) 50 IU/kg for immediate anticoagulation reversal."
        ),
        guidelines_context=(
            "AHA/ASA + Neurocritical Care Society Guideline for Reversal of "
            "Antithrombotics in Intracranial Hemorrhage: 4-factor PCC is "
            "recommended over FFP for warfarin reversal in ICH (faster onset, "
            "less volume, more reliable INR correction). Vitamin K + PCC "
            "combination is standard. Time-sensitive — every minute of "
            "anticoagulation extends bleed."
        ),
        expected_outcome=ExpectedOutcome.AUTO_APPROVED,
        expected_branch=EscalationBranch.BRANCH_1_AUTO_APPROVE,
        reasoning_must_include=["ICH", "warfarin", "reversal"],
        reasoning_must_not_include=["delayed", "FFP first"],
        clinical_rationale=(
            "Active intracranial hemorrhage on warfarin — PCC reversal is "
            "AHA/ASA-recommended, time-critical. Any escalation introduces "
            "outcome-relevant delay."
        ),
        judge_scoring_criteria=(
            "Score highly if rationale identifies the active bleed, the "
            "AHA/ASA PCC recommendation, and the time-sensitivity. Penalize "
            "HEAVILY for any escalation or delay framing."
        ),
    ),
]
