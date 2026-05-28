"""
Transplant cases — iter-6 Batch H (transplant depth to 5).

WHY THESE EXIST
---------------
At iter-5 close, transplant had ZERO cases. Iter-6 expansion_cases added
GC-031 (post-renal-transplant tacrolimus maintenance AUTO_APPROVED). This
file adds 4 more to reach 5 — coverage across organ types (heart, liver,
BMT, renal-rejection) and care phases (initiation, pediatric maintenance,
acute rejection).

  GC-060  Heart transplant tacrolimus initiation post-op  AUTO_APPROVED
  GC-061  Pediatric (8yo) liver transplant maintenance    IN_REVIEW
  GC-062  Allogeneic BMT conditioning regimen             IN_REVIEW
  GC-063  Renal transplant rejection — IV methylprednisolone AUTO_APPROVED
"""

from __future__ import annotations

from tests.clinical.golden_cases import (
    EscalationBranch,
    ExpectedOutcome,
    GoldenCase,
)

TRANSPLANT_CASES: list[GoldenCase] = [
    # ─────────────────────────────────────────────────────────────────────────
    # GC-060 — Heart transplant tacrolimus initiation post-op.
    # ─────────────────────────────────────────────────────────────────────────
    GoldenCase(
        case_id="GC-060",
        title="Heart transplant — tacrolimus initiation post-op per ISHLT",
        diagnosis_code="Z94.1",
        diagnosis_description="Heart transplant status",
        procedure_code="J7508",
        procedure_description="Tacrolimus (Prograf) extended release oral, per 0.1 mg",
        clinical_notes=(
            "54-year-old female, status post orthotopic heart transplant "
            "POD #8 for end-stage non-ischemic cardiomyopathy. Initiating "
            "standard maintenance immunosuppression: tacrolimus 6 mg BID "
            "(target trough 10-15 ng/mL post-op), mycophenolate mofetil "
            "1.5 g BID, prednisone 20 mg daily with planned taper. "
            "Hemodynamics stable, no rejection on protocol biopsy, no acute "
            "infection. Transplant cardiology requesting initial 30-day "
            "tacrolimus supply."
        ),
        guidelines_context=(
            "ISHLT (International Society for Heart and Lung Transplantation) "
            "Guideline for Care of Heart Transplant Recipients: tacrolimus-"
            "based triple therapy is standard maintenance regimen. Target "
            "tacrolimus trough levels are higher in first 3 months "
            "(10-15 ng/mL) and titrated down thereafter. Initial 30-day "
            "post-discharge supply is routine; no specialist re-review "
            "required when the regimen matches transplant-center protocol."
        ),
        expected_outcome=ExpectedOutcome.AUTO_APPROVED,
        expected_branch=EscalationBranch.BRANCH_1_AUTO_APPROVE,
        reasoning_must_include=["transplant", "tacrolimus", "ISHLT"],
        reasoning_must_not_include=["experimental", "denied"],
        clinical_rationale=(
            "Standard post-heart-transplant maintenance immunosuppression "
            "regimen at ISHLT-recommended doses and targets. Stable patient. "
            "Clean approve. Probes that the agent recognizes transplant-"
            "specific high target trough levels (10-15) as appropriate for "
            "the post-op phase, not over-escalation."
        ),
        judge_scoring_criteria=(
            "Score highly if rationale cites the transplant status, the "
            "ISHLT regimen, and the target trough rationale. Penalize for "
            "escalation based on procedure complexity or for denial."
        ),
    ),
    # ─────────────────────────────────────────────────────────────────────────
    # GC-061 — Pediatric liver transplant immunosuppression refill.
    # ─────────────────────────────────────────────────────────────────────────
    GoldenCase(
        case_id="GC-061",
        title="Pediatric (8yo) liver transplant tacrolimus refill — IN_REVIEW (peds + transplant)",
        diagnosis_code="Z94.4",
        diagnosis_description="Liver transplant status",
        procedure_code="J7508",
        procedure_description="Tacrolimus (Prograf) extended release oral, per 0.1 mg",
        clinical_notes=(
            "8-year-old male, status post liver transplant 18 months ago "
            "for biliary atresia. Current regimen: tacrolimus 1.5 mg BID "
            "(weight-based, target trough 4-7 ng/mL maintenance phase), "
            "low-dose prednisone. Stable graft function (AST/ALT normal, "
            "GGT normal). Annual refill request from pediatric "
            "hepatology / transplant program. Growth on target. No "
            "rejection episodes."
        ),
        guidelines_context=(
            "ESPGHAN / NASPGHAN Pediatric Liver Transplant Practice Guidance: "
            "tacrolimus is first-line maintenance in pediatric liver "
            "transplant. Pediatric dosing is weight-based with lower target "
            "troughs in maintenance phase. Institutional policy: pediatric "
            "transplant immunosuppression refills trigger specialist "
            "(pediatric transplant) review per pediatric_complex check + "
            "transplant procedure-class — both flags fire; complexity score "
            "ought to push to IN_REVIEW."
        ),
        expected_outcome=ExpectedOutcome.IN_REVIEW,
        expected_branch=EscalationBranch.BRANCH_2_MEDICAL_DIRECTOR,
        reasoning_must_include=["pediatric", "transplant", "specialist"],
        reasoning_must_not_include=["auto-approve", "routine refill"],
        clinical_rationale=(
            "Pediatric + transplant intersection — two complexity drivers. "
            "Per pediatric_complex check (iter-5 chg-3) + transplant "
            "procedure-class, the complexity-score model expects to push "
            "this to IN_REVIEW. Not a denial — refill is appropriate — but "
            "pediatric transplant oversight is policy."
        ),
        judge_scoring_criteria=(
            "Score highly if rationale identifies both the pediatric age "
            "and the transplant status as complexity drivers warranting "
            "specialist review. Penalize for auto-approval (ignores "
            "pediatric_complex), denial (refill is appropriate), or "
            "escalation framed as cost rather than complexity."
        ),
    ),
    # ─────────────────────────────────────────────────────────────────────────
    # GC-062 — Allogeneic BMT conditioning regimen.
    # ─────────────────────────────────────────────────────────────────────────
    GoldenCase(
        case_id="GC-062",
        title="Allogeneic BMT conditioning — IN_REVIEW per ASTCT (institutional protocol)",
        diagnosis_code="C92.00",
        diagnosis_description="Acute myeloblastic leukemia, not having achieved remission",
        procedure_code="38240",
        procedure_description="Hematopoietic progenitor cell transplantation, allogeneic",
        clinical_notes=(
            "47-year-old male with AML in first complete remission after "
            "induction + consolidation chemotherapy. Cytogenetics: complex "
            "karyotype (poor risk). HLA-matched unrelated donor identified. "
            "Transplant program requesting authorization for myeloablative "
            "conditioning (fludarabine + busulfan) followed by allogeneic "
            "stem cell transplant. ECOG 0. No active infection, no end-organ "
            "dysfunction. Transplant comorbidity index (HCT-CI) score 1."
        ),
        guidelines_context=(
            "ASTCT (American Society for Transplantation and Cellular "
            "Therapy) Guidelines + NCCN AML Guidelines: allogeneic stem "
            "cell transplant in CR1 is recommended for AML with adverse-"
            "risk cytogenetics. Conditioning regimen selection (myeloablative "
            "vs reduced-intensity) is institution- and patient-specific. "
            "BMT authorization requires institutional transplant-committee "
            "review and is processed via specialist (transplant medical "
            "director) approval pathway regardless of guideline alignment."
        ),
        expected_outcome=ExpectedOutcome.IN_REVIEW,
        expected_branch=EscalationBranch.BRANCH_2_MEDICAL_DIRECTOR,
        reasoning_must_include=["BMT", "transplant", "specialist"],
        reasoning_must_not_include=["auto-approve", "experimental"],
        clinical_rationale=(
            "Allogeneic BMT authorization is always specialist-routed by "
            "policy — the institutional transplant committee + medical "
            "director review the protocol and patient fitness regardless of "
            "guideline alignment. Not a denial — clinical indication is "
            "appropriate per NCCN — but specialist review is non-negotiable "
            "for this procedure class."
        ),
        judge_scoring_criteria=(
            "Score highly if rationale identifies the BMT procedure class "
            "as triggering specialist review by policy. Penalize for "
            "auto-approval (ignores policy gate) or for framing as "
            "experimental (allogeneic BMT in AML CR1 is standard of care)."
        ),
    ),
    # ─────────────────────────────────────────────────────────────────────────
    # GC-063 — Renal transplant acute rejection treatment.
    # ─────────────────────────────────────────────────────────────────────────
    GoldenCase(
        case_id="GC-063",
        title="Renal transplant — acute rejection IV methylprednisolone per KDIGO",
        diagnosis_code="T86.11",
        diagnosis_description="Kidney transplant rejection",
        procedure_code="J2920",
        procedure_description="Methylprednisolone sodium succinate injection, 40 mg",
        clinical_notes=(
            "51-year-old female, status post deceased-donor kidney transplant "
            "9 months ago. Presents with rising creatinine (1.2 → 1.9 over "
            "1 week). Allograft biopsy confirms Banff grade IIA acute "
            "T-cell-mediated rejection. No donor-specific antibodies on "
            "current testing. Transplant nephrology requesting IV "
            "methylprednisolone pulse therapy (500 mg daily × 3 days) as "
            "first-line rejection treatment."
        ),
        guidelines_context=(
            "KDIGO Clinical Practice Guideline for the Care of Kidney "
            "Transplant Recipients + AST (American Society of Transplantation) "
            "Position: first-line treatment for Banff grade IIA T-cell-"
            "mediated rejection is high-dose IV corticosteroids (typically "
            "methylprednisolone 250-500 mg daily × 3 days). Biopsy "
            "confirmation is required; antibody-mediated rejection requires "
            "different therapy."
        ),
        expected_outcome=ExpectedOutcome.AUTO_APPROVED,
        expected_branch=EscalationBranch.BRANCH_1_AUTO_APPROVE,
        reasoning_must_include=["rejection", "methylprednisolone", "KDIGO"],
        reasoning_must_not_include=["experimental", "delayed"],
        clinical_rationale=(
            "Biopsy-confirmed acute T-cell-mediated rejection in renal "
            "transplant. KDIGO first-line therapy is IV methylprednisolone "
            "pulse. Time-sensitive; clean approve."
        ),
        judge_scoring_criteria=(
            "Score highly if rationale cites the biopsy result, the Banff "
            "grade, and the KDIGO first-line therapy. Penalize for "
            "escalation (treatment is time-sensitive), denial, or "
            "step-therapy demand (corticosteroids ARE the first step)."
        ),
    ),
]
