"""
Adult-complexity eval cases — iter-6 chg-3.

WHY THESE EXIST
---------------
chg-2 added a deterministic ADULT_COMPLEX pre-flight (age >= 18 AND complexity
score >= settings.complexity_specialist_review_min=4). A pre-flight branch with
no data behind it is an unfalsifiable assertion. These cases give the branch
real data points across its decision boundary: two that MUST escalate (one
mid-adult, one geriatric) and one that MUST NOT (the must-not-escalate guard,
mirroring iter-5's GC-023 pediatric guard).

Parallel list — GOLDEN_CASES stays at exactly 20. IDs continue the monotonic
allocation (dataset is at GC-100; these are GC-101..GC-103).

Score arithmetic (parser path; weights per _compute_complexity_score):
  GC-101  adult 58, severe(+2), >=2 failures(+1), comorbidity(+1)       = 4  FIRE
  GC-102  adult 49, severe(+2), no failures, no comorbidity             = 2  SPARE
  GC-103  elderly 81(+2), severe(+2), no failures, no comorbidity-hint  = 4  FIRE
"""

from __future__ import annotations

from tests.clinical.golden_cases import (
    EscalationBranch,
    ExpectedOutcome,
    GoldenCase,
)

ADULT_COMPLEXITY_CASES: list[GoldenCase] = [
    # ─────────────────────────────────────────────────────────────────────────
    # GC-101 — Escalating anchor. Adult, severe, refractory, comorbid; cheap drug
    # (so high_cost does NOT pre-empt) and a standard agent (not experimental).
    # ─────────────────────────────────────────────────────────────────────────
    GoldenCase(
        case_id="GC-101",
        title="Add-on spironolactone for severe treatment-resistant hypertension",
        diagnosis_code="I10",
        diagnosis_description="Essential (primary) hypertension",
        procedure_code="J0000",  # placeholder oral generic; low cost
        procedure_description="Spironolactone 25 mg oral, add-on therapy",
        clinical_notes=(
            "58-year-old male with severe treatment-resistant hypertension, "
            "office BP 168/104 despite three-drug therapy at maximally tolerated "
            "doses. Refractory to lisinopril; failed trial of amlodipine; "
            "inadequate response to hydrochlorothiazide. Comorbid type 2 diabetes "
            "mellitus and stage 3 chronic kidney disease (eGFR 52). Requesting "
            "add-on spironolactone per resistant-hypertension guidance. "
            "Spironolactone is a low-cost generic; estimated annual drug cost "
            "well under $1,000. It is an established, guideline-recommended "
            "fourth-line agent."
        ),
        guidelines_context=(
            "ACC/AHA resistant-hypertension guidance: confirmed resistant "
            "hypertension (uncontrolled on three agents including a diuretic at "
            "optimal doses) supports add-on mineralocorticoid-receptor antagonist "
            "(spironolactone) as preferred fourth-line therapy. Single "
            "authoritative source; no conflicting guideline."
        ),
        expected_outcome=ExpectedOutcome.IN_REVIEW,
        expected_branch=EscalationBranch.BRANCH_2_MEDICAL_DIRECTOR,
        reasoning_must_include=["complexity", "specialist", "severe"],
        reasoning_must_not_include=["experimental", "denied"],
        clinical_rationale=(
            "The therapy itself is guideline-concordant and low-cost — on clinical "
            "merits alone an agent might auto-approve. But the case clears the "
            "deterministic adult-complexity bar (severe + refractory + comorbid = "
            "score 4 = specialist-review threshold), so policy routes it to "
            "specialist review regardless of clinical eligibility. This is the "
            "GC-010 lesson generalized to adults: policy escalation must be "
            "deterministic, not left to the agent's confidence."
        ),
        judge_scoring_criteria=(
            "Score highly if the rationale identifies the complexity-driven "
            "specialist-review escalation (severe + refractory + comorbidity) and "
            "routes IN_REVIEW. Penalize for auto-approval (the deterministic "
            "pre-flight must win over clinical confidence) or for DENIED (nothing "
            "here warrants denial)."
        ),
    ),
    # ─────────────────────────────────────────────────────────────────────────
    # GC-102 — Must-not-escalate boundary. Adult, severe, but NO failures and NO
    # comorbidity → score 2 < 4. A clear surgical indication that should auto-
    # approve. Mirrors iter-5's GC-023 pediatric guard.
    # ─────────────────────────────────────────────────────────────────────────
    GoldenCase(
        case_id="GC-102",
        title="Laparoscopic cholecystectomy for severe acute cholecystitis",
        diagnosis_code="K81.0",
        diagnosis_description="Acute cholecystitis",
        procedure_code="47562",
        procedure_description="Laparoscopic cholecystectomy",
        clinical_notes=(
            "49-year-old female with severe acute cholecystitis: RUQ pain, "
            "Murphy's sign positive, WBC 15.2, ultrasound shows gallbladder wall "
            "thickening with pericholecystic fluid and gallstones. First "
            "presentation; no prior episodes. No other active medical problems. "
            "Requesting laparoscopic cholecystectomy within the recommended "
            "early-surgery window."
        ),
        guidelines_context=(
            "Tokyo Guidelines: early laparoscopic cholecystectomy is first-line "
            "for acute cholecystitis in an operative candidate. Clear indication; "
            "single authoritative source."
        ),
        expected_outcome=ExpectedOutcome.AUTO_APPROVED,
        expected_branch=EscalationBranch.BRANCH_1_AUTO_APPROVE,
        reasoning_must_include=["acute cholecystitis", "laparoscopic"],
        reasoning_must_not_include=["experimental", "denied", "specialist review required"],
        clinical_rationale=(
            "Severe disease, but a single severity point (score 2) is below the "
            "adult specialist-review threshold (4): no refractory failures, no "
            "comorbidity. The indication is textbook and the procedure is "
            "guideline-concordant, so the case should auto-approve. This proves "
            "the adult check does not over-escalate every severe adult case — "
            "severity alone is not enough."
        ),
        judge_scoring_criteria=(
            "Score highly for AUTO_APPROVED with a rationale citing the clear "
            "acute-cholecystitis indication. Penalize for IN_REVIEW driven by a "
            "spurious complexity escalation (severity alone must not trip the "
            "adult threshold) or for any DENIED."
        ),
    ),
    # ─────────────────────────────────────────────────────────────────────────
    # GC-103 — Geriatric escalating. Elderly(+2) + severe(+2) = 4. No failures,
    # and "secondary to CKD" is deliberately NOT a comorbidity-hint phrase, so the
    # score lands at exactly 4 (not 5). Moderate-cost agent (not high_cost).
    # ─────────────────────────────────────────────────────────────────────────
    GoldenCase(
        case_id="GC-103",
        title="Epoetin alfa for severe symptomatic anemia of chronic kidney disease",
        diagnosis_code="D63.1",
        diagnosis_description="Anemia in chronic kidney disease",
        procedure_code="J0885",
        procedure_description="Epoetin alfa injection (non-ESRD)",
        clinical_notes=(
            "81-year-old male with severe symptomatic anemia secondary to chronic "
            "kidney disease (non-dialysis). Hemoglobin 8.4 g/dL with exertional "
            "dyspnea and fatigue limiting activities of daily living. Iron studies "
            "repleted. Requesting epoetin alfa per anemia-of-CKD guidance. "
            "Estimated annual cost is moderate, below the high-cost threshold."
        ),
        guidelines_context=(
            "KDIGO anemia-in-CKD guidance: ESA therapy (epoetin alfa) is "
            "appropriate for symptomatic anemia of CKD after iron repletion, with "
            "individualized hemoglobin targets. Single authoritative source."
        ),
        expected_outcome=ExpectedOutcome.IN_REVIEW,
        expected_branch=EscalationBranch.BRANCH_2_MEDICAL_DIRECTOR,
        reasoning_must_include=["complexity", "specialist", "severe"],
        reasoning_must_not_include=["experimental", "denied"],
        clinical_rationale=(
            "Geriatric age (>75) plus severe disease reaches the adult complexity "
            "threshold (score 4) even without refractory failures or a documented "
            "comorbidity — appropriate, because age-extreme plus severe anemia in "
            "an 81-year-old genuinely warrants specialist review of the ESA "
            "risk/benefit (thrombotic risk, target individualization). Routes "
            "IN_REVIEW via the deterministic pre-flight."
        ),
        judge_scoring_criteria=(
            "Score highly for IN_REVIEW with a rationale identifying the "
            "age-extreme + severity complexity escalation. Penalize for "
            "auto-approval (geriatric severe anemia should not auto-approve on an "
            "ESA) or for DENIED."
        ),
    ),
]
