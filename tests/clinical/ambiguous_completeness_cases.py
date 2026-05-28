"""
Ambiguous-completeness cases — iter-6 Batch G (graded sparseness to 5).

WHY THESE EXIST
---------------
At iter-5 close, the Outcome × Documentation-Completeness matrix had only
two cases at the "sparse" tier (GC-018, GC-019 hallucination traps) and
zero cases at the "ambiguous" tier. This file adds 5 cases at the ambiguous
tier — each missing ONE specific data element that would prevent automatic
decisioning, across 5 specialties.

  GC-055  Psoriasis biologic — prior therapy duration omitted     IN_REVIEW
  GC-056  MS DMT — EDSS score omitted                              IN_REVIEW
  GC-057  T2DM intensification — HbA1c date omitted                IN_REVIEW
  GC-058  Oncology 2nd-line — prior regimen response not given     IN_REVIEW
  GC-059  Migraine CGRP — prior preventives unnamed                IN_REVIEW

Each case tests the agent's recognition that "missing the specific data"
is different from "criteria explicitly not met" — the correct response is
INFORMATION_NEEDED / IN_REVIEW, not DENIED.
"""

from __future__ import annotations

from tests.clinical.golden_cases import (
    EscalationBranch,
    ExpectedOutcome,
    GoldenCase,
)

AMBIGUOUS_COMPLETENESS_CASES: list[GoldenCase] = [
    # ─────────────────────────────────────────────────────────────────────────
    # GC-055 — Psoriasis biologic, missing prior-therapy duration.
    # ─────────────────────────────────────────────────────────────────────────
    GoldenCase(
        case_id="GC-055",
        title="Psoriasis biologic — prior MTX duration omitted, IN_REVIEW",
        diagnosis_code="L40.0",
        diagnosis_description="Psoriasis vulgaris",
        procedure_code="J3357",
        procedure_description="Ustekinumab (Stelara) injection",
        clinical_notes=(
            "44-year-old male with moderate-to-severe plaque psoriasis "
            "(BSA 12%, PASI 18). Prior methotrexate trial completed; duration "
            "and dose not specified in submitted documentation. Patient "
            "reports topical therapy 'did not help.' Dermatologist requesting "
            "ustekinumab. No mention of phototherapy or cyclosporine trial. "
            "No contraindications noted."
        ),
        guidelines_context=(
            "AAD-NPF Guidelines for Plaque Psoriasis: biologic step-up "
            "requires documented inadequate response or contraindication "
            "to at least one conventional systemic agent (methotrexate, "
            "cyclosporine, acitretin, or apremilast). Adequate trial of "
            "methotrexate is defined as ≥ 15 mg/week × ≥ 12 weeks. Without "
            "documented dose and duration, eligibility cannot be confirmed."
        ),
        expected_outcome=ExpectedOutcome.IN_REVIEW,
        expected_branch=EscalationBranch.BRANCH_3_LOW_CONFIDENCE,
        reasoning_must_include=["methotrexate", "duration", "dose"],
        reasoning_must_not_include=["criteria met", "deny based on no MTX"],
        clinical_rationale=(
            "Ambiguous documentation: methotrexate trial is mentioned but "
            "duration and dose are missing. Cannot confirm adequacy without "
            "this data. Not a denial (MTX may well have been adequate) — "
            "INFORMATION_NEEDED / IN_REVIEW pending clarification."
        ),
        judge_scoring_criteria=(
            "Score highly if rationale identifies the missing duration/dose "
            "data and requests clarification rather than denying outright. "
            "Penalize for auto-approval (cannot confirm step therapy), "
            "denial (over-assumes inadequacy), or hallucinating a duration."
        ),
    ),
    # ─────────────────────────────────────────────────────────────────────────
    # GC-056 — MS DMT, severity language present but EDSS not given.
    # ─────────────────────────────────────────────────────────────────────────
    GoldenCase(
        case_id="GC-056",
        title="MS DMT — severity described qualitatively but EDSS omitted, IN_REVIEW",
        diagnosis_code="G35",
        diagnosis_description="Multiple sclerosis",
        procedure_code="J2350",
        procedure_description="Ocrelizumab (Ocrevus) injection",
        clinical_notes=(
            "34-year-old female with relapsing-remitting MS, diagnosed 2 "
            "years ago. Two clinical relapses in past 12 months. MRI shows "
            "'multiple T2 hyperintense lesions with new enhancement.' "
            "Neurologist describes disease as 'moderately active.' EDSS "
            "score not stated in submitted documentation. Currently on "
            "no DMT. Requesting ocrelizumab as initial DMT."
        ),
        guidelines_context=(
            "AAN Practice Guideline + MS Society Recommendations: high-"
            "efficacy DMTs (ocrelizumab, ofatumumab, natalizumab) are "
            "first-line for highly active MS. Activity is defined by relapse "
            "frequency (≥ 2 in past year), new MRI lesions, AND/OR EDSS "
            "progression. Documentation typically requires explicit EDSS "
            "score (baseline + current) to support 'highly active' "
            "characterization."
        ),
        expected_outcome=ExpectedOutcome.IN_REVIEW,
        expected_branch=EscalationBranch.BRANCH_3_LOW_CONFIDENCE,
        reasoning_must_include=["EDSS", "MS", "severity"],
        reasoning_must_not_include=["meets criteria", "approved without EDSS"],
        clinical_rationale=(
            "Relapse count and MRI findings support high-efficacy DMT "
            "consideration, but the EDSS score is conventionally documented "
            "and is missing. Request clarification of baseline + current "
            "EDSS rather than approving on the qualitative description."
        ),
        judge_scoring_criteria=(
            "Score highly if rationale identifies the missing EDSS and "
            "requests it. Penalize for auto-approval (qualitative 'moderately "
            "active' is not sufficient), or for hallucinating an EDSS value."
        ),
    ),
    # ─────────────────────────────────────────────────────────────────────────
    # GC-057 — T2DM intensification, HbA1c noted but date omitted.
    # ─────────────────────────────────────────────────────────────────────────
    GoldenCase(
        case_id="GC-057",
        title="T2DM SGLT2 inhibitor — HbA1c 8.6 but measurement date missing, IN_REVIEW",
        diagnosis_code="E11.65",
        diagnosis_description="Type 2 diabetes mellitus with hyperglycemia",
        procedure_code="J8499",
        procedure_description="Empagliflozin 25 mg oral",
        clinical_notes=(
            "56-year-old male with T2DM. On metformin 1000 mg BID + "
            "glipizide 10 mg BID. HbA1c documented as 8.6 — date of "
            "measurement not specified in submitted notes. eGFR 68 (no "
            "renal contraindication). No CV disease documented. PCP "
            "requesting empagliflozin add-on for glycemic control."
        ),
        guidelines_context=(
            "ADA Standards of Care: glycemic intensification is appropriate "
            "when HbA1c remains above individualized target despite current "
            "therapy. HbA1c measurement must be recent (within 90 days) to "
            "guide therapy changes; older values may not reflect current "
            "control. SGLT2 inhibitors are appropriate add-ons; eGFR > 30 "
            "required for empagliflozin initiation."
        ),
        expected_outcome=ExpectedOutcome.IN_REVIEW,
        expected_branch=EscalationBranch.BRANCH_3_LOW_CONFIDENCE,
        reasoning_must_include=["HbA1c", "date", "recent"],
        reasoning_must_not_include=["meets criteria", "approved"],
        clinical_rationale=(
            "HbA1c value (8.6) would justify intensification if recent, but "
            "the measurement date is missing. ADA expects measurement within "
            "90 days to guide therapy. Request the measurement date."
        ),
        judge_scoring_criteria=(
            "Score highly if rationale flags the missing measurement date "
            "and requests it. Penalize for auto-approval on the assumption "
            "the value is current, or for outright denial."
        ),
    ),
    # ─────────────────────────────────────────────────────────────────────────
    # GC-058 — Oncology 2nd-line, prior regimen named but response missing.
    # ─────────────────────────────────────────────────────────────────────────
    GoldenCase(
        case_id="GC-058",
        title="Oncology 2nd-line — prior regimen named but response not characterized, IN_REVIEW",
        diagnosis_code="C18.7",
        diagnosis_description="Malignant neoplasm of sigmoid colon",
        procedure_code="J9035",
        procedure_description="Bevacizumab (Avastin) injection",
        clinical_notes=(
            "62-year-old male with metastatic colon cancer. Prior first-line "
            "FOLFOX completed; response not characterized in submitted "
            "documentation (no statement of CR, PR, SD, or PD; no imaging "
            "report cited). Oncologist requesting second-line FOLFIRI + "
            "bevacizumab. Patient ECOG 1, no contraindications to bevacizumab "
            "(no recent surgery, no uncontrolled HTN, no bleeding)."
        ),
        guidelines_context=(
            "NCCN Colon Cancer Guidelines: second-line therapy selection "
            "depends on first-line response — patients with progression on "
            "FOLFOX move to FOLFIRI (with or without bevacizumab); patients "
            "who responded to FOLFOX and then progressed after a treatment "
            "holiday may benefit from FOLFOX re-challenge. Response "
            "characterization is essential to inform regimen choice."
        ),
        expected_outcome=ExpectedOutcome.IN_REVIEW,
        expected_branch=EscalationBranch.BRANCH_3_LOW_CONFIDENCE,
        reasoning_must_include=["first-line", "response", "progression"],
        reasoning_must_not_include=["meets criteria without response data"],
        clinical_rationale=(
            "Second-line regimen selection requires first-line response "
            "characterization. Missing this data point. Request: was the "
            "patient progressing on FOLFOX, or progressing after a "
            "treatment holiday? Critical for regimen selection."
        ),
        judge_scoring_criteria=(
            "Score highly if rationale identifies the missing response "
            "characterization and requests it. Penalize for auto-approval "
            "(regimen choice is not fully informed) or denial."
        ),
    ),
    # ─────────────────────────────────────────────────────────────────────────
    # GC-059 — Migraine CGRP, prior preventives mentioned but unnamed.
    # ─────────────────────────────────────────────────────────────────────────
    GoldenCase(
        case_id="GC-059",
        title="Migraine CGRP — 'previously tried other preventives' unnamed, IN_REVIEW",
        diagnosis_code="G43.709",
        diagnosis_description="Chronic migraine without aura, not intractable, without status migrainosus",
        procedure_code="J3590",
        procedure_description="Fremanezumab (Ajovy) injection",
        clinical_notes=(
            "42-year-old female with chronic migraine, 16 headache days "
            "per month. MIDAS score 24. Documentation states 'patient has "
            "tried multiple preventive therapies in the past without "
            "success' — specific medications, doses, and durations not "
            "named. No contraindications documented. Neurologist requesting "
            "fremanezumab quarterly dosing."
        ),
        guidelines_context=(
            "AAN / AHS 2019 Consensus on CGRP-targeted Therapies: CGRP "
            "monoclonals require documented failure of ≥ 2 categories of "
            "established preventive therapy at adequate dose and duration. "
            "Acceptable categories include beta-blockers, TCAs, "
            "antiepileptics (topiramate, valproate), and "
            "onabotulinumtoxinA. Naming the specific agents, doses, and "
            "durations is the documentation standard."
        ),
        expected_outcome=ExpectedOutcome.IN_REVIEW,
        expected_branch=EscalationBranch.BRANCH_3_LOW_CONFIDENCE,
        reasoning_must_include=["preventive", "documented", "specific"],
        reasoning_must_not_include=["meets criteria without naming", "auto-approve"],
        clinical_rationale=(
            "CGRP eligibility hinges on ≥ 2 specific documented preventive "
            "failures. 'Tried multiple preventives without success' is "
            "insufficient documentation. Request: name the agents, doses, "
            "and durations."
        ),
        judge_scoring_criteria=(
            "Score highly if rationale identifies the unnamed preventives "
            "as the gap and requests specifics. Penalize for auto-approval "
            "(criteria can't be confirmed), or for denial without giving the "
            "provider a chance to document."
        ),
    ),
]
