#!/usr/bin/env python3
"""
PACCA Demo Data Generator — v2.2.0
====================================
Generates 50 synthesized prior authorization cases covering every escalation
path in the 7-branch decision tree. Outputs:

  1. demo/cases.json        — machine-readable case data
  2. demo/demo_report.md    — human-readable walkthrough for interviews/demos
  3. demo/run_demo.py       — runnable script that executes cases through the
                               live Orchestrator (populates Langfuse with traces)

Coverage (50 cases):
  Group A — Auto-Approved (Branch 1)         15 cases  clear guideline alignment
  Group B — Human Review / Low confidence    10 cases  missing/ambiguous docs
  Group C — MD Escalation (Branch 2)          8 cases  high-cost, borderline confidence
  Group D — Experimental (Branch 4)           5 cases  CAR-T, gene therapy, trials
  Group E — Rare Condition (Branch 5)         4 cases  Gaucher, Huntington, ALS, Wilson
  Group F — Conflicting Guidelines (Branch 6) 4 cases  NCCN vs CMS contradictions
  Group G — Prior Denial (Branch 7)           4 cases  resubmissions
  Group H — Precedent-based Approval          3 cases  institutional memory learning
  Total                                       53 cases  (slight overage for coverage)

Usage:
    cd /Users/davidreed/David_Portfolio/pacca
    source venv/bin/activate
    python demo/generate_demo_data.py
"""

import json
import os
from dataclasses import asdict, dataclass, field
from typing import Optional


# ─────────────────────────────────────────────────────────────────────────────
# Data structures
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class DemoCase:
    case_id: str
    group: str                      # A-H
    title: str
    patient_id: str
    patient_age: int
    diagnosis_code: str
    diagnosis_description: str
    procedure_code: str
    procedure_description: str
    clinical_notes: str
    guidelines_context: str
    expected_branch: str            # e.g. "branch_1_auto_approve"
    expected_outcome: str           # AUTO_APPROVED | IN_REVIEW
    prior_denial_codes: list[str] = field(default_factory=list)
    estimated_cost_usd: int = 0
    demo_talking_points: str = ""


# ─────────────────────────────────────────────────────────────────────────────
# GROUP A — Clear approvals (Branch 1)
# Complete documentation, explicit guideline alignment, high confidence
# ─────────────────────────────────────────────────────────────────────────────

GROUP_A: list[DemoCase] = [

    DemoCase(
        case_id="DEMO-A01",
        group="A",
        title="NSCLC Pembrolizumab — PD-L1 ≥50%, all criteria documented",
        patient_id="PT-10001", patient_age=58,
        diagnosis_code="C34.1",
        diagnosis_description="Non-small cell lung cancer, upper lobe",
        procedure_code="J9271",
        procedure_description="Pembrolizumab (Keytruda) injection",
        clinical_notes=(
            "58-year-old male, stage IIIA NSCLC adenocarcinoma. PD-L1 TPS 62% "
            "confirmed by validated assay (PathLab, 14 days ago). EGFR/ALK negative "
            "on molecular panel. ECOG PS 1. No prior systemic therapy. No active "
            "autoimmune disease. Requesting first-line pembrolizumab monotherapy."
        ),
        guidelines_context=(
            "NCCN NSCLC v4.2025: Pembrolizumab monotherapy Category 1 for PD-L1 "
            "TPS ≥50%, no EGFR/ALK, first-line. Evidence level IA."
        ),
        expected_branch="branch_1_auto_approve",
        expected_outcome="AUTO_APPROVED",
        estimated_cost_usd=15000,
        demo_talking_points=(
            "Showcase: all four NCCN criteria documented explicitly. Agent cites "
            "PD-L1 62%, EGFR/ALK negative, first-line status. Confidence ≥0.95 "
            "→ auto-approve with no human touch. This is the ideal case."
        ),
    ),

    DemoCase(
        case_id="DEMO-A02",
        group="A",
        title="Type 2 Diabetes + CVD — SGLT2 inhibitor, CV indication bypasses step therapy",
        patient_id="PT-10002", patient_age=63,
        diagnosis_code="E11.65",
        diagnosis_description="Type 2 diabetes mellitus with hyperglycemia",
        procedure_code="J0597",
        procedure_description="Empagliflozin (Jardiance) — SGLT2 inhibitor",
        clinical_notes=(
            "63-year-old male, T2DM with established CVD (MI 2 years ago). "
            "Metformin 1000mg BID x 18 months. HbA1c 8.4% (6 weeks ago). "
            "eGFR 68 mL/min/1.73m2. No SGLT2 contraindications. Cardiologist "
            "recommends empagliflozin for cardiovascular mortality reduction "
            "per EMPA-REG OUTCOME trial. BMI 31."
        ),
        guidelines_context=(
            "ADA 2025: SGLT2 inhibitors recommended for T2DM + established CVD "
            "regardless of HbA1c. Prior metformin NOT required when CV indication "
            "present. eGFR ≥30 required — patient eGFR 68 is adequate."
        ),
        expected_branch="branch_1_auto_approve",
        expected_outcome="AUTO_APPROVED",
        estimated_cost_usd=3600,
        demo_talking_points=(
            "Showcase: step therapy bypass. Agent must recognize CVD indication "
            "overrides metformin-first requirement. Tests nuanced guideline "
            "interpretation, not just criteria checklist matching."
        ),
    ),

    DemoCase(
        case_id="DEMO-A03",
        group="A",
        title="Lumbar MRI — foot drop, neurological emergency overrides 6-week rule",
        patient_id="PT-10003", patient_age=52,
        diagnosis_code="M54.5",
        diagnosis_description="Low back pain with radiculopathy",
        procedure_code="72148",
        procedure_description="MRI lumbar spine without contrast",
        clinical_notes=(
            "52-year-old male, back pain 3 weeks, severe L4-L5 radiculopathy. "
            "New onset foot drop developing over past 7 days. Motor strength "
            "3/5 left dorsiflexion. Conservative therapy 2 weeks. "
            "Neurological emergency: progressive motor weakness."
        ),
        guidelines_context=(
            "CMS LCD L34976: MRI requires ≥6 weeks conservative therapy. "
            "EXCEPTION: neurological red flags (progressive motor weakness, "
            "foot drop, cauda equina) override the 6-week requirement — "
            "immediate imaging indicated. "
            "PAST MEDICAL DIRECTOR DECISIONS (PRECEDENTS): "
            "Override approved: MRI for patient with 3-week history and "
            "progressive foot drop — neurological emergency exception applies."
        ),
        expected_branch="branch_1_auto_approve",
        expected_outcome="AUTO_APPROVED",
        estimated_cost_usd=1200,
        demo_talking_points=(
            "Showcase: institutional memory + exception clause. Agent must "
            "recognize foot drop as neurological red flag AND cite the precedent. "
            "Tests whether the system uses the PAST MEDICAL DIRECTOR DECISIONS "
            "section in the guidelines context."
        ),
    ),

    DemoCase(
        case_id="DEMO-A04",
        group="A",
        title="RA Biologic — 2+ DMARD failures documented, seropositive",
        patient_id="PT-10004", patient_age=48,
        diagnosis_code="M05.79",
        diagnosis_description="Rheumatoid arthritis with rheumatoid factor",
        procedure_code="J0129",
        procedure_description="Abatacept (Orencia) — biologic DMARD",
        clinical_notes=(
            "48-year-old female, seropositive RA (RF+, anti-CCP+). DAS28 5.6. "
            "Prior DMARD failures: methotrexate 25mg/week x 12 months (inadequate "
            "response), leflunomide 20mg/day x 9 months (intolerance — hepatotoxicity "
            "LFTs 4x ULN). Requesting abatacept as first biologic."
        ),
        guidelines_context=(
            "ACR RA Guidelines 2021: Biologic DMARD indicated after failure of "
            "≥2 conventional DMARDs. Seropositive RA (RF+/anti-CCP+) with DAS28 "
            ">5.1 is moderate-to-high disease activity. Both prior DMARDs failed "
            "(inadequate response + intolerance both qualify as step therapy failure)."
        ),
        expected_branch="branch_1_auto_approve",
        expected_outcome="AUTO_APPROVED",
        estimated_cost_usd=24000,
        demo_talking_points=(
            "Showcase: two types of step therapy failure. Agent must recognize "
            "both inadequate response AND intolerance as qualifying step therapy "
            "failures. Common failure mode: agents incorrectly require more DMARDs."
        ),
    ),

    DemoCase(
        case_id="DEMO-A05",
        group="A",
        title="Crohn's Disease Adalimumab — adequate step therapy, steroid-dependent",
        patient_id="PT-10005", patient_age=34,
        diagnosis_code="K50.90",
        diagnosis_description="Crohn's disease of small intestine",
        procedure_code="J0135",
        procedure_description="Adalimumab (Humira) — anti-TNF biologic",
        clinical_notes=(
            "34-year-old male, moderate-to-severe Crohn's (CDAI 285). "
            "Prior: mesalamine 6 months (inadequate), azathioprine 12 months "
            "(hepatotoxicity — LFTs 3x ULN). Steroid-dependent: prednisone "
            "8 months continuous. First biologic request."
        ),
        guidelines_context=(
            "ACG Crohn's Guidelines: Anti-TNF indicated for mod-severe Crohn's "
            "with: (1) immunomodulator failure/intolerance, OR (2) steroid "
            "dependence. Azathioprine hepatotoxicity = step therapy failure. "
            "Steroid dependence alone qualifies independently."
        ),
        expected_branch="branch_1_auto_approve",
        expected_outcome="AUTO_APPROVED",
        estimated_cost_usd=19200,
        demo_talking_points=(
            "Showcase: two independent qualifying criteria. Agent should note "
            "steroid dependence alone qualifies, PLUS azathioprine intolerance "
            "as additional supporting evidence. Robust documentation case."
        ),
    ),

    DemoCase(
        case_id="DEMO-A06",
        group="A",
        title="HER2+ Breast Cancer — trastuzumab, confirmed HER2 3+ by IHC",
        patient_id="PT-10006", patient_age=44,
        diagnosis_code="C50.912",
        diagnosis_description="Malignant neoplasm of breast, female",
        procedure_code="J9355",
        procedure_description="Trastuzumab (Herceptin) injection",
        clinical_notes=(
            "44-year-old female, HER2-positive invasive ductal carcinoma stage II. "
            "HER2 3+ by IHC confirmed (PathLab, 10 days ago). FISH amplification "
            "confirmed. ER/PR negative. ECOG PS 0. Requesting trastuzumab + "
            "pertuzumab neoadjuvant chemotherapy per NCCN Category 1."
        ),
        guidelines_context=(
            "NCCN Breast Cancer v5.2025: Trastuzumab + pertuzumab + taxane "
            "is Category 1 recommendation for HER2-positive early breast cancer. "
            "Requires HER2 overexpression confirmed by IHC 3+ or FISH amplification. "
            "Both criteria met."
        ),
        expected_branch="branch_1_auto_approve",
        expected_outcome="AUTO_APPROVED",
        estimated_cost_usd=8500,
        demo_talking_points=(
            "Classic HER2+ case. Agent must confirm both IHC 3+ and FISH "
            "amplification cited. Tests whether agent correctly applies the "
            "dual-confirmation requirement for HER2 testing."
        ),
    ),

    DemoCase(
        case_id="DEMO-A07",
        group="A",
        title="Pediatric Asthma — dupilumab add-on, eosinophilic phenotype confirmed",
        patient_id="PT-10007", patient_age=14,
        diagnosis_code="J45.51",
        diagnosis_description="Severe persistent asthma with acute exacerbation",
        procedure_code="J0222",
        procedure_description="Dupilumab (Dupixent) — IL-4/IL-13 biologic",
        clinical_notes=(
            "14-year-old male, severe persistent asthma uncontrolled on max-dose "
            "ICS/LABA (fluticasone/salmeterol) x 12 months. 3 ED visits past year. "
            "Eosinophil count 480/uL. IgE 295 IU/mL. FeNO 42 ppb. "
            "Pulmonologist requesting dupilumab add-on."
        ),
        guidelines_context=(
            "GINA/NIST: Dupilumab approved ≥12 years, severe eosinophilic asthma. "
            "Criteria: severe persistent uncontrolled on high-dose ICS, "
            "eosinophilic phenotype (eos ≥300/uL OR FeNO ≥25). "
            "Patient: eos 480 (meets threshold), FeNO 42 (meets threshold). "
            "Age 14 ≥ 12 year minimum. All criteria met."
        ),
        expected_branch="branch_1_auto_approve",
        expected_outcome="AUTO_APPROVED",
        estimated_cost_usd=38000,
        demo_talking_points=(
            "Pediatric high-cost case that still auto-approves because all criteria "
            "are explicitly documented. Contrast with DEMO-B07 where pediatric "
            "complexity triggers escalation when documentation is borderline."
        ),
    ),

    DemoCase(
        case_id="DEMO-A08",
        group="A",
        title="Oncological Emergency — leukostasis, STAT chemo authorization",
        patient_id="PT-10008", patient_age=22,
        diagnosis_code="C91.00",
        diagnosis_description="Acute lymphoblastic leukemia",
        procedure_code="J9070",
        procedure_description="Cyclophosphamide injection — hyper-CVAD induction",
        clinical_notes=(
            "22-year-old male, newly diagnosed ALL with leukostasis. WBC 188,000. "
            "Neurological symptoms: severe headache, blurred vision. ICU admission. "
            "Life-threatening emergency. Oncology requesting STAT authorization "
            "for hyper-CVAD induction chemotherapy."
        ),
        guidelines_context=(
            "NCCN ALL: Hyper-CVAD Category 1 for newly diagnosed ALL. "
            "Emergency processing: life-threatening documented emergency allows "
            "expedited/waived authorization pending retrospective review. "
            "Leukostasis with neurological symptoms = oncological emergency."
        ),
        expected_branch="branch_1_auto_approve",
        expected_outcome="AUTO_APPROVED",
        estimated_cost_usd=4200,
        demo_talking_points=(
            "Emergency override case. Agent must recognize leukostasis + WBC 188K "
            "as oncological emergency triggering expedited approval. Standard "
            "chemo (not experimental) + life-threatening = auto-approve."
        ),
    ),

    DemoCase(
        case_id="DEMO-A09",
        group="A",
        title="MS Ocrelizumab — primary progressive MS, ORATORIO trial criteria",
        patient_id="PT-10009", patient_age=41,
        diagnosis_code="G35",
        diagnosis_description="Primary progressive multiple sclerosis",
        procedure_code="J2350",
        procedure_description="Ocrelizumab (Ocrevus) — anti-CD20 biologic",
        clinical_notes=(
            "41-year-old female, primary progressive MS confirmed by McDonald 2017. "
            "EDSS 4.5. T1 gadolinium-enhancing lesion on recent MRI. No prior "
            "ocrelizumab. PPMS diagnosis 3 years ago. Ambulatory. "
            "Neurologist requesting ocrelizumab (FDA approved for PPMS)."
        ),
        guidelines_context=(
            "FDA approval 2017: Ocrelizumab is the only FDA-approved DMT for PPMS. "
            "NCCN MS guidelines: indicated for PPMS with EDSS ≤7.5, confirmed "
            "diagnosis per McDonald criteria, no active infection. "
            "All criteria met."
        ),
        expected_branch="branch_1_auto_approve",
        expected_outcome="AUTO_APPROVED",
        estimated_cost_usd=65000,
        demo_talking_points=(
            "High-cost case ($65K) that still auto-approves because it meets "
            "the specific criteria. Demonstrates the system correctly applies "
            "cost-threshold escalation only when the cost exceeds HIGH_COST_THRESHOLD."
        ),
    ),

    DemoCase(
        case_id="DEMO-A10",
        group="A",
        title="Colonoscopy screening — age 50, average risk, standard interval",
        patient_id="PT-10010", patient_age=52,
        diagnosis_code="Z12.11",
        diagnosis_description="Encounter for screening for malignant neoplasm of colon",
        procedure_code="45378",
        procedure_description="Colonoscopy, diagnostic",
        clinical_notes=(
            "52-year-old female, average colorectal cancer risk. Last colonoscopy "
            "10 years ago (normal, no polyps). Family history negative. No symptoms. "
            "Requesting standard 10-year screening colonoscopy per USPSTF guidelines."
        ),
        guidelines_context=(
            "USPSTF CRC Screening: colonoscopy every 10 years starting at 50 for "
            "average-risk adults. 10-year interval met. Patient age 52 ≥ 50. "
            "No high-risk features (no IBD, no family history). Standard coverage."
        ),
        expected_branch="branch_1_auto_approve",
        expected_outcome="AUTO_APPROVED",
        estimated_cost_usd=2800,
        demo_talking_points=(
            "Routine preventive screening — the simplest possible auto-approve. "
            "Included to show the system handles common low-complexity cases "
            "efficiently without over-escalating."
        ),
    ),

    DemoCase(
        case_id="DEMO-A11",
        group="A",
        title="T1DM Continuous Glucose Monitor — A1c above target, insulin-dependent",
        patient_id="PT-10011", patient_age=28,
        diagnosis_code="E10.9",
        diagnosis_description="Type 1 diabetes mellitus",
        procedure_code="E0787",
        procedure_description="Continuous glucose monitor (CGM) — therapeutic",
        clinical_notes=(
            "28-year-old female, T1DM x 12 years. A1c 8.1% (above 7% target). "
            "Insulin pump therapy. 3+ hypoglycemic episodes/month requiring "
            "intervention. Endocrinologist requesting CGM to improve glucose "
            "time-in-range and reduce hypoglycemia frequency."
        ),
        guidelines_context=(
            "ADA 2025: CGM indicated for T1DM on insulin with A1c above target "
            "OR recurrent hypoglycemia. Patient meets both criteria: A1c 8.1% "
            "and 3+ hypoglycemic events/month. Insurance coverage standard."
        ),
        expected_branch="branch_1_auto_approve",
        expected_outcome="AUTO_APPROVED",
        estimated_cost_usd=3200,
        demo_talking_points=(
            "Two independent qualifying criteria met: A1c above target AND "
            "recurrent hypoglycemia. Shows the system correctly recognizes "
            "when any one of multiple qualifying criteria is sufficient."
        ),
    ),

    DemoCase(
        case_id="DEMO-A12",
        group="A",
        title="Migraine Erenumab — 4+ CGRP preventives failed, chronic migraine",
        patient_id="PT-10012", patient_age=36,
        diagnosis_code="G43.909",
        diagnosis_description="Migraine, unspecified, not intractable",
        procedure_code="J3032",
        procedure_description="Erenumab (Aimovig) — CGRP antagonist",
        clinical_notes=(
            "36-year-old female, chronic migraine ≥15 days/month x 8 months. "
            "Failed 4 oral preventives: propranolol (inadequate response), "
            "topiramate (cognitive side effects), amitriptyline (weight gain, "
            "discontinued), valproate (inadequate response). Neurologist "
            "requesting erenumab."
        ),
        guidelines_context=(
            "AAN/AHS CGRP Antagonist Guidelines: Erenumab indicated after failure "
            "of ≥2 oral preventive medications. Patient failed 4 — substantially "
            "exceeds minimum requirement. Chronic migraine (≥15 days/month) "
            "confirmed ≥4 weeks. All criteria met."
        ),
        expected_branch="branch_1_auto_approve",
        expected_outcome="AUTO_APPROVED",
        estimated_cost_usd=7800,
        demo_talking_points=(
            "Step therapy clearly met — 4 failures vs. 2 required. Agent should "
            "note over-compliance with step therapy as a positive factor. "
            "Tests recognition that exceeding minimum requirements strengthens approval."
        ),
    ),

    DemoCase(
        case_id="DEMO-A13",
        group="A",
        title="Hepatitis C Sofosbuvir — genotype 1a, treatment-naive, liver fibrosis",
        patient_id="PT-10013", patient_age=47,
        diagnosis_code="B18.2",
        diagnosis_description="Chronic viral hepatitis C",
        procedure_code="S0166",
        procedure_description="Sofosbuvir/ledipasvir (Harvoni) — DAA regimen",
        clinical_notes=(
            "47-year-old male, HCV genotype 1a confirmed. Treatment-naive. "
            "Liver biopsy: Metavir F2 fibrosis (moderate). ALT 68 U/L. "
            "No cirrhosis. No HBV co-infection. HIV negative. "
            "Requesting sofosbuvir/ledipasvir 12-week course."
        ),
        guidelines_context=(
            "AASLD-IDSA HCV Guidelines: Sofosbuvir/ledipasvir 12 weeks for "
            "HCV GT1a treatment-naive, F0-F3 fibrosis. SVR12 rate >97%. "
            "Patient: GT1a confirmed, treatment-naive, F2 fibrosis. All criteria met."
        ),
        expected_branch="branch_1_auto_approve",
        expected_outcome="AUTO_APPROVED",
        estimated_cost_usd=24000,
        demo_talking_points=(
            "Standard DAA approval with strong evidence base (>97% SVR12). "
            "Shows the system confidently approves high-evidence treatments even "
            "at moderate cost when documentation is complete."
        ),
    ),

    DemoCase(
        case_id="DEMO-A14",
        group="A",
        title="COPD Tiotropium — GOLD Stage III, 2 exacerbations last year",
        patient_id="PT-10014", patient_age=67,
        diagnosis_code="J44.1",
        diagnosis_description="Chronic obstructive pulmonary disease with acute exacerbation",
        procedure_code="J7682",
        procedure_description="Tiotropium bromide (Spiriva) — LAMA inhaler",
        clinical_notes=(
            "67-year-old male, GOLD Stage III COPD. FEV1/FVC 0.58, FEV1 44% predicted. "
            "2 COPD exacerbations requiring hospitalization in past 12 months. "
            "Current: SABA PRN only. No LAMA. Pulmonologist requesting tiotropium "
            "to reduce exacerbation frequency."
        ),
        guidelines_context=(
            "GOLD 2025 Guidelines: LAMA recommended for GOLD B-D patients (≥1 "
            "exacerbation or CAT ≥10). Patient is GOLD D (FEV1 44%, 2 exacerbations). "
            "Tiotropium is Category 1A evidence for exacerbation prevention."
        ),
        expected_branch="branch_1_auto_approve",
        expected_outcome="AUTO_APPROVED",
        estimated_cost_usd=2400,
        demo_talking_points=(
            "Geriatric patient with clear clinical need. Low cost, strong evidence. "
            "Tests geriatric-appropriate recommendations without over-escalating "
            "due to patient age."
        ),
    ),

    DemoCase(
        case_id="DEMO-A15",
        group="A",
        title="Psoriatic Arthritis Adalimumab — 2 cDMARD failures, DAPSA documented",
        patient_id="PT-10015", patient_age=39,
        diagnosis_code="L40.52",
        diagnosis_description="Psoriatic arthritis, distal interphalangeal",
        procedure_code="J0129",
        procedure_description="Adalimumab (Humira) — anti-TNF for PsA",
        clinical_notes=(
            "39-year-old female, psoriatic arthritis with DIP involvement. "
            "DAPSA 32 (high disease activity). Prior: methotrexate 25mg/week x "
            "15 months (inadequate response, DAPSA improvement <50%), sulfasalazine "
            "2g/day x 9 months (GI intolerance, discontinued). "
            "Requesting adalimumab as first biologic."
        ),
        guidelines_context=(
            "ACR PsA Guidelines 2021: Biologic DMARD after failure of ≥2 "
            "conventional DMARDs (methotrexate, sulfasalazine, leflunomide). "
            "Both failures documented with adequate duration and objective endpoints. "
            "GI intolerance = valid step therapy failure."
        ),
        expected_branch="branch_1_auto_approve",
        expected_outcome="AUTO_APPROVED",
        estimated_cost_usd=21000,
        demo_talking_points=(
            "Validates the system correctly handles GI intolerance as step therapy "
            "failure in PsA — a common clinical scenario that some systems "
            "incorrectly reject as 'non-compliance'."
        ),
    ),
]


# ─────────────────────────────────────────────────────────────────────────────
# GROUP B — Human Review / Low Confidence (Branch 3)
# Missing documentation, insufficient evidence, incomplete step therapy
# ─────────────────────────────────────────────────────────────────────────────

GROUP_B: list[DemoCase] = [

    DemoCase(
        case_id="DEMO-B01",
        group="B",
        title="NSCLC Pembrolizumab — sparse notes, PD-L1 not documented",
        patient_id="PT-20001", patient_age=61,
        diagnosis_code="C34.1",
        diagnosis_description="Non-small cell lung cancer",
        procedure_code="J9271",
        procedure_description="Pembrolizumab injection",
        clinical_notes="Patient has lung cancer. Requesting pembrolizumab.",
        guidelines_context=(
            "NCCN: Pembrolizumab requires PD-L1 TPS ≥50% confirmed by validated "
            "assay AND absence of EGFR/ALK mutations. Both must be documented."
        ),
        expected_branch="branch_3_low_confidence",
        expected_outcome="IN_REVIEW",
        estimated_cost_usd=15000,
        demo_talking_points=(
            "HALLUCINATION TRAP: agent must NOT invent PD-L1 scores or EGFR status. "
            "Notes provide zero clinical detail. Correct behavior: identify "
            "missing documentation, request specific values, return low confidence."
        ),
    ),

    DemoCase(
        case_id="DEMO-B02",
        group="B",
        title="Psoriasis Biologic — step therapy not completed, only NSAIDs tried",
        patient_id="PT-20002", patient_age=29,
        diagnosis_code="L40.0",
        diagnosis_description="Psoriasis vulgaris",
        procedure_code="J0178",
        procedure_description="Adalimumab (Humira) injection",
        clinical_notes=(
            "29-year-old female, moderate-to-severe plaque psoriasis (PASI 18). "
            "Requesting adalimumab. Patient prefers biologic over topicals. "
            "No prior systemic therapy attempted."
        ),
        guidelines_context=(
            "AAD-NPF: Biologic requires prior failure of ≥1 conventional systemic "
            "agent (methotrexate, cyclosporine, acitretin) OR ≥2 topical therapies. "
            "Patient preference alone is NOT a qualifying criterion."
        ),
        expected_branch="branch_3_low_confidence",
        expected_outcome="IN_REVIEW",
        estimated_cost_usd=18000,
        demo_talking_points=(
            "Step therapy clearly not met. Agent must correctly identify that "
            "'patient prefers biologic' is explicitly disallowed as justification. "
            "Should request documentation of conventional therapy trials."
        ),
    ),

    DemoCase(
        case_id="DEMO-B03",
        group="B",
        title="Lumbar MRI — 2 weeks symptoms, no conservative therapy",
        patient_id="PT-20003", patient_age=34,
        diagnosis_code="M54.5",
        diagnosis_description="Low back pain",
        procedure_code="72148",
        procedure_description="MRI lumbar spine without contrast",
        clinical_notes=(
            "34-year-old male, back pain onset 2 weeks ago after lifting. "
            "No prior imaging. No PT attempted. Taking OTC ibuprofen. "
            "Normal gait. No neurological symptoms. Requesting MRI to rule out "
            "'anything serious'."
        ),
        guidelines_context=(
            "CMS LCD L34976: MRI requires ≥6 weeks symptoms AND failure of "
            "conservative therapy (PT, analgesics, chiro). OR neurological "
            "red flags. Patient: 2 weeks, no conservative therapy, no red flags. "
            "None of three pathways met."
        ),
        expected_branch="branch_3_low_confidence",
        expected_outcome="IN_REVIEW",
        estimated_cost_usd=1200,
        demo_talking_points=(
            "Clear guideline non-compliance: 2 weeks vs. 6 required, no PT, "
            "no red flags. Agent should deny/request more info, NOT approve. "
            "Tests whether agent correctly applies duration requirements."
        ),
    ),

    DemoCase(
        case_id="DEMO-B04",
        group="B",
        title="Multiple Myeloma Bortezomib — incomplete submission, no staging",
        patient_id="PT-20004", patient_age=71,
        diagnosis_code="C90.00",
        diagnosis_description="Multiple myeloma",
        procedure_code="J9043",
        procedure_description="Bortezomib (Velcade) injection",
        clinical_notes="Patient has myeloma. Needs treatment.",
        guidelines_context=(
            "NCCN MM: Bortezomib requires: (1) confirmed diagnosis with M-protein, "
            "(2) ISS staging, (3) renal function (dose-adjust for CrCl <30), "
            "(4) prior treatment history (first-line vs relapsed/refractory). "
            "All four required for authorization."
        ),
        expected_branch="branch_3_low_confidence",
        expected_outcome="IN_REVIEW",
        estimated_cost_usd=8800,
        demo_talking_points=(
            "Most incomplete submission in the demo set. Agent must identify "
            "all four missing elements (M-protein, staging, renal function, "
            "treatment history) without hallucinating values."
        ),
    ),

    DemoCase(
        case_id="DEMO-B05",
        group="B",
        title="MS Alemtuzumab — documentation borderline, only 1 relapse noted",
        patient_id="PT-20005", patient_age=38,
        diagnosis_code="G35",
        diagnosis_description="Relapsing-remitting multiple sclerosis",
        procedure_code="J0202",
        procedure_description="Alemtuzumab (Lemtrada) — MS therapy",
        clinical_notes=(
            "38-year-old female, RRMS. 1 relapse last year. On interferon beta. "
            "Neurologist requesting alemtuzumab. MRI shows 'some lesion activity' "
            "(no lesion count provided). EDSS score not documented."
        ),
        guidelines_context=(
            "FDA/EMA: Alemtuzumab for active RRMS with inadequate response to "
            "≥2 prior DMTs. Active RRMS requires ≥2 relapses/year OR ≥2 new T2 "
            "lesions. Requires: relapse count, MRI lesion count, EDSS, prior DMT list."
        ),
        expected_branch="branch_3_low_confidence",
        expected_outcome="IN_REVIEW",
        estimated_cost_usd=158000,
        demo_talking_points=(
            "Multiple documentation gaps: 1 relapse vs 2 required, vague MRI "
            "('some activity'), missing EDSS, only 1 prior DMT vs 2 required. "
            "Very high cost adds urgency for complete documentation."
        ),
    ),

    DemoCase(
        case_id="DEMO-B06",
        group="B",
        title="PsA Secukinumab — only NSAIDs tried, conventional DMARD required",
        patient_id="PT-20006", patient_age=44,
        diagnosis_code="L40.52",
        diagnosis_description="Psoriatic arthritis",
        procedure_code="J1300",
        procedure_description="Secukinumab (Cosentyx) — IL-17A inhibitor",
        clinical_notes=(
            "44-year-old female, psoriatic arthritis. 3-month trial of ibuprofen. "
            "Requesting secukinumab. X-ray shows joint damage. "
            "No methotrexate or sulfasalazine trial."
        ),
        guidelines_context=(
            "ACR PsA 2021: Biologic requires prior failure of conventional DMARDs "
            "(MTX, sulfasalazine, leflunomide). NSAIDs alone are insufficient. "
            "X-ray damage does NOT override step therapy unless rapid progression "
            "documented with serial films."
        ),
        expected_branch="branch_3_low_confidence",
        expected_outcome="IN_REVIEW",
        estimated_cost_usd=26000,
        demo_talking_points=(
            "NSAIDs ≠ conventional DMARD. Common error: treating NSAID failure "
            "as step therapy completion. Agent should specify which conventional "
            "DMARDs are required (MTX, sulfasalazine, or leflunomide)."
        ),
    ),

    DemoCase(
        case_id="DEMO-B07",
        group="B",
        title="Pediatric Complex — borderline documentation with age escalation",
        patient_id="PT-20007", patient_age=8,
        diagnosis_code="K50.00",
        diagnosis_description="Crohn's disease of small intestine",
        procedure_code="J0135",
        procedure_description="Adalimumab (Humira) — pediatric IBD",
        clinical_notes=(
            "8-year-old male, pediatric Crohn's. PCDAI 35 (moderate). "
            "On mesalamine. Provider notes 'has not responded well to therapy.' "
            "No specific prior therapy duration documented."
        ),
        guidelines_context=(
            "ECCO-ESPGHAN Pediatric IBD: Biologic indicated for moderate-severe "
            "pediatric Crohn's after failure of exclusive enteral nutrition OR "
            "conventional immunomodulators (6MP, azathioprine). Specific therapy "
            "duration and objective response criteria required."
        ),
        expected_branch="branch_3_low_confidence",
        expected_outcome="IN_REVIEW",
        estimated_cost_usd=19200,
        demo_talking_points=(
            "Pediatric patient + vague step therapy documentation. 'Has not "
            "responded well' is insufficient — need specific prior therapies, "
            "durations, and objective response criteria."
        ),
    ),

    DemoCase(
        case_id="DEMO-B08",
        group="B",
        title="Hallucination trap — sparse oncology notes, must not invent labs",
        patient_id="PT-20008", patient_age=55,
        diagnosis_code="C50.911",
        diagnosis_description="Malignant neoplasm, breast",
        procedure_code="J9354",
        procedure_description="Ado-trastuzumab emtansine (Kadcyla) — HER2-ADC",
        clinical_notes="Patient has breast cancer. Requesting Kadcyla.",
        guidelines_context=(
            "NCCN: Ado-trastuzumab emtansine for HER2-positive metastatic breast "
            "cancer after prior trastuzumab and taxane. Requires: HER2 3+ or "
            "FISH amplified, prior trastuzumab + taxane documented."
        ),
        expected_branch="branch_3_low_confidence",
        expected_outcome="IN_REVIEW",
        estimated_cost_usd=12000,
        demo_talking_points=(
            "Second hallucination trap. Agent must NOT invent HER2 status, "
            "prior therapy history, or staging. Zero clinical data in notes. "
            "Only correct response: enumerate all missing required documentation."
        ),
    ),

    DemoCase(
        case_id="DEMO-B09",
        group="B",
        title="ADHD Stimulant — diagnosis not confirmed, no formal evaluation",
        patient_id="PT-20009", patient_age=32,
        diagnosis_code="F90.9",
        diagnosis_description="Attention-deficit hyperactivity disorder, unspecified",
        procedure_code="S0091",
        procedure_description="Amphetamine salts (Adderall XR) — stimulant",
        clinical_notes=(
            "32-year-old male, patient self-reports ADHD symptoms. "
            "Requesting Adderall XR. No formal neuropsychological evaluation. "
            "No prior stimulant trial documented."
        ),
        guidelines_context=(
            "AHRQ ADHD Guidelines: Stimulant authorization requires: "
            "(1) formal ADHD diagnosis by qualified clinician using DSM-5 criteria, "
            "(2) age-appropriate rating scales (Conners, ASRS), "
            "(3) assessment ruling out anxiety/mood disorders. "
            "Self-report alone insufficient."
        ),
        expected_branch="branch_3_low_confidence",
        expected_outcome="IN_REVIEW",
        estimated_cost_usd=1800,
        demo_talking_points=(
            "Self-report ≠ clinical diagnosis. Agent should identify the specific "
            "documentation required: formal evaluation, rating scales, differential "
            "diagnosis of anxiety/mood disorders."
        ),
    ),

    DemoCase(
        case_id="DEMO-B10",
        group="B",
        title="Bariatric Surgery — BMI meets threshold but comorbidity not documented",
        patient_id="PT-20010", patient_age=42,
        diagnosis_code="E66.01",
        diagnosis_description="Morbid (severe) obesity due to excess calories",
        procedure_code="43644",
        procedure_description="Laparoscopic gastric bypass (Roux-en-Y)",
        clinical_notes=(
            "42-year-old female, BMI 41. Requesting bariatric surgery. "
            "Has tried 'multiple diets.' No specific dietary program documented. "
            "Medical comorbidities not listed."
        ),
        guidelines_context=(
            "CMS Bariatric Coverage: BMI ≥40 OR BMI ≥35 with qualifying comorbidity. "
            "Requires: (1) BMI ≥40 confirmed with recent weight/height, "
            "(2) ≥6 months physician-supervised diet documented, "
            "(3) psychological clearance, (4) absence of contraindications. "
            "BMI alone insufficient without documented supervised diet program."
        ),
        expected_branch="branch_3_low_confidence",
        expected_outcome="IN_REVIEW",
        estimated_cost_usd=22000,
        demo_talking_points=(
            "BMI criterion met but mandatory 6-month supervised diet program "
            "not documented. 'Multiple diets' is not physician-supervised. "
            "Agent should cite the specific missing elements."
        ),
    ),
]


# ─────────────────────────────────────────────────────────────────────────────
# GROUP C — Medical Director Escalation (Branch 2)
# High-cost, borderline confidence 0.90-0.95, ambiguous clinical scenarios
# ─────────────────────────────────────────────────────────────────────────────

GROUP_C: list[DemoCase] = [

    DemoCase(
        case_id="DEMO-C01",
        group="C",
        title="RA Biologic — criteria met but cost $288K triggers MD review",
        patient_id="PT-30001", patient_age=55,
        diagnosis_code="M05.79",
        diagnosis_description="Rheumatoid arthritis with rheumatoid factor",
        procedure_code="J0129",
        procedure_description="Abatacept (Orencia) — biologic DMARD",
        clinical_notes=(
            "55-year-old female, seropositive RA, DAS28 5.2. Prior DMARD failures: "
            "methotrexate 12 months (inadequate), hydroxychloroquine 6 months "
            "(inadequate). Requesting abatacept. Annual cost: $24,000/infusion "
            "x 12 = $288,000."
        ),
        guidelines_context=(
            "ACR RA 2021: Biologic DMARD after ≥2 conventional DMARD failures. "
            "Abatacept is a recommended option for seropositive RA. "
            "All clinical criteria met."
        ),
        expected_branch="branch_2_medical_director",
        expected_outcome="IN_REVIEW",
        estimated_cost_usd=288000,
        demo_talking_points=(
            "Clinical criteria ARE met but $288K exceeds HIGH_COST_THRESHOLD ($100K). "
            "System should approve at the clinical level but escalate to MD for "
            "cost review. Demonstrates cost-based escalation on an otherwise "
            "approvable case."
        ),
    ),

    DemoCase(
        case_id="DEMO-C02",
        group="C",
        title="MS Natalizumab — highly active RRMS, borderline prior therapy count",
        patient_id="PT-30002", patient_age=33,
        diagnosis_code="G35",
        diagnosis_description="Relapsing-remitting multiple sclerosis",
        procedure_code="J2323",
        procedure_description="Natalizumab (Tysabri) — anti-VLA4 biologic",
        clinical_notes=(
            "33-year-old female, highly active RRMS. 2 relapses past year. "
            "1 new T1 gadolinium-enhancing lesion. EDSS 3.0. Prior DMT: interferon "
            "beta-1a x 18 months (breakthrough disease on therapy). JC antibody "
            "index 0.8 (elevated, PML risk present). Requesting natalizumab."
        ),
        guidelines_context=(
            "FDA: Natalizumab for highly active RRMS or inadequate response to "
            "other DMTs. Risk: PML (JC antibody positive = elevated risk). "
            "Guidelines recommend JC antibody index <0.9 for initial approval "
            "with risk mitigation monitoring. Index 0.8 is within range but "
            "borderline — clinical benefit vs PML risk requires MD judgment."
        ),
        expected_branch="branch_2_medical_director",
        expected_outcome="IN_REVIEW",
        estimated_cost_usd=78000,
        demo_talking_points=(
            "Clinical benefit vs. safety risk tradeoff that requires MD judgment. "
            "JC antibody 0.8 is within range but elevated — automated system "
            "should recognize this as ambiguous and escalate. Classic Branch 2 case."
        ),
    ),

    DemoCase(
        case_id="DEMO-C03",
        group="C",
        title="Pediatric Biologic — ≥12 criteria met but age requires specialist",
        patient_id="PT-30003", patient_age=13,
        diagnosis_code="M08.00",
        diagnosis_description="Unspecified juvenile idiopathic arthritis",
        procedure_code="J0129",
        procedure_description="Adalimumab (Humira) — JIA indication",
        clinical_notes=(
            "13-year-old female, polyarticular JIA, RF negative. JADAS27 16 "
            "(high disease activity). Prior: methotrexate 15mg/m2 x 12 months "
            "(inadequate response, ACR Ped response <30%). "
            "Requesting adalimumab. Weight 48kg. Age 13."
        ),
        guidelines_context=(
            "ACR JIA 2019: Biologic DMARD after ≥3 months conventional DMARD "
            "with inadequate response (ACR Ped <30%). Adalimumab approved ≥2 "
            "years for JIA. All clinical criteria met. "
            "Pediatric dosing weight-based: adalimumab 20mg q2w for <30kg, "
            "40mg q2w for ≥30kg. Patient 48kg → standard adult dose."
        ),
        expected_branch="branch_2_medical_director",
        expected_outcome="IN_REVIEW",
        estimated_cost_usd=26000,
        demo_talking_points=(
            "Pediatric patient — clinical criteria met but specialist review "
            "recommended for all pediatric biologic initiations. Demonstrates "
            "age-based escalation overlay on an otherwise approvable case."
        ),
    ),

    DemoCase(
        case_id="DEMO-C04",
        group="C",
        title="TAVR — borderline surgical risk score",
        patient_id="PT-30004", patient_age=79,
        diagnosis_code="I35.0",
        diagnosis_description="Aortic valve stenosis",
        procedure_code="33361",
        procedure_description="TAVR — transcatheter aortic valve replacement",
        clinical_notes=(
            "79-year-old male, severe aortic stenosis (AVA 0.7 cm2, mean gradient "
            "52 mmHg). STS score 4.2% (intermediate surgical risk). EF 45%. "
            "Heart team consensus recommends TAVR over SAVR. Cardiothoracic "
            "and interventional cardiology both reviewed."
        ),
        guidelines_context=(
            "ACC/AHA Valve Guidelines: TAVR for severe AS in intermediate-to-high "
            "surgical risk (STS ≥4%). Patient STS 4.2% is at the lower bound of "
            "intermediate risk. Heart team evaluation completed and documented. "
            "Cost: ~$120,000."
        ),
        expected_branch="branch_2_medical_director",
        expected_outcome="IN_REVIEW",
        estimated_cost_usd=120000,
        demo_talking_points=(
            "STS 4.2% is at the lower boundary of intermediate risk AND cost "
            ">$100K. Two escalation factors converge. Clinical criteria likely met "
            "but the edge case nature and cost warrant MD review."
        ),
    ),

    DemoCase(
        case_id="DEMO-C05",
        group="C",
        title="Spinal Cord Stimulator — failed back syndrome, 3 prior surgeries",
        patient_id="PT-30005", patient_age=54,
        diagnosis_code="M54.51",
        diagnosis_description="Vertebrogenic low back pain",
        procedure_code="63685",
        procedure_description="Spinal cord stimulator implant",
        clinical_notes=(
            "54-year-old female, failed back surgery syndrome x 8 years. 3 prior "
            "lumbar surgeries. VAS pain 8/10. Physical therapy 2 years (insufficient "
            "relief). Opioid therapy (morphine 60mg MEQ/day, stable 2 years). "
            "Pain management specialist recommends SCS trial."
        ),
        guidelines_context=(
            "CMS Coverage: SCS for failed back surgery syndrome after ≥6 months "
            "conservative therapy including PT and medication optimization. "
            "Psychological evaluation required. Trial period required before "
            "permanent implant. Cost: $65,000+ for permanent implant."
        ),
        expected_branch="branch_2_medical_director",
        expected_outcome="IN_REVIEW",
        estimated_cost_usd=65000,
        demo_talking_points=(
            "High cost + multiple prior surgeries + long opioid history creates "
            "clinical complexity warranting MD review. Conservative therapy criteria "
            "likely met but psychological evaluation documentation not mentioned."
        ),
    ),

    DemoCase(
        case_id="DEMO-C06",
        group="C",
        title="Vedolizumab for Crohn's — anti-TNF failure, cost above threshold",
        patient_id="PT-30006", patient_age=31,
        diagnosis_code="K50.90",
        diagnosis_description="Crohn's disease",
        procedure_code="J3490",
        procedure_description="Vedolizumab (Entyvio) — anti-integrin biologic",
        clinical_notes=(
            "31-year-old male, moderate Crohn's (HBI 9). Failed adalimumab "
            "(anti-drug antibodies confirmed, 14 months therapy). Prior: "
            "azathioprine intolerance. Requesting vedolizumab as second biologic."
        ),
        guidelines_context=(
            "ACG 2021: Vedolizumab indicated after anti-TNF failure or intolerance. "
            "Anti-drug antibody formation = confirmed anti-TNF failure. "
            "Annual cost vedolizumab: ~$65,000."
        ),
        expected_branch="branch_2_medical_director",
        expected_outcome="IN_REVIEW",
        estimated_cost_usd=65000,
        demo_talking_points=(
            "Second biologic after documented anti-TNF failure. Clinical criteria "
            "met but cost near threshold. Demonstrates threshold-proximate cost "
            "escalation behavior."
        ),
    ),

    DemoCase(
        case_id="DEMO-C07",
        group="C",
        title="Retinal degeneration Ranibizumab — wet AMD, high injection frequency",
        patient_id="PT-30007", patient_age=74,
        diagnosis_code="H35.32",
        diagnosis_description="Exudative age-related macular degeneration",
        procedure_code="J2778",
        procedure_description="Ranibizumab (Lucentis) — anti-VEGF injection",
        clinical_notes=(
            "74-year-old female, wet AMD both eyes. OCT: active CNV with subretinal "
            "fluid. VA: 20/80 right, 20/100 left. Prior bevacizumab inadequate "
            "(persistent fluid after 6 monthly injections). "
            "Requesting ranibizumab 0.5mg bilateral monthly x 12 months."
        ),
        guidelines_context=(
            "AAO AMD Guidelines: Anti-VEGF therapy for wet AMD with active CNV. "
            "Ranibizumab after bevacizumab failure is supported. "
            "Bilateral treatment x 12 months = ~$120,000 total annual cost."
        ),
        expected_branch="branch_2_medical_director",
        expected_outcome="IN_REVIEW",
        estimated_cost_usd=120000,
        demo_talking_points=(
            "Clinical criteria met (active CNV, prior bevacizumab failure) but "
            "bilateral treatment creates very high cumulative cost (>$100K). "
            "Demonstrates cost threshold triggering on cumulative annual cost."
        ),
    ),

    DemoCase(
        case_id="DEMO-C08",
        group="C",
        title="Immunotherapy High Cost — nivolumab + ipilimumab combination",
        patient_id="PT-30008", patient_age=62,
        diagnosis_code="C34.31",
        diagnosis_description="Malignant neoplasm of lower lobe of lung",
        procedure_code="J9299",
        procedure_description="Nivolumab + Ipilimumab combination — checkpoint inhibitors",
        clinical_notes=(
            "62-year-old male, stage IV NSCLC. TMB-high (18 mut/Mb). PD-L1 TPS 45%. "
            "EGFR/ALK/ROS1 negative. ECOG PS 1. No prior systemic therapy. "
            "Oncologist requesting nivolumab + ipilimumab combination first-line."
        ),
        guidelines_context=(
            "NCCN NSCLC v4.2025: Nivolumab + ipilimumab Category 1 for TMB-high "
            "(≥10 mut/Mb) stage IV NSCLC regardless of PD-L1. Annual combination "
            "cost: ~$280,000."
        ),
        expected_branch="branch_2_medical_director",
        expected_outcome="IN_REVIEW",
        estimated_cost_usd=280000,
        demo_talking_points=(
            "Clinical criteria clearly met (TMB-high, Category 1) but $280K cost "
            "triggers mandatory MD review. Shows that cost review doesn't mean "
            "denial — it means a senior clinician validates the treatment plan."
        ),
    ),
]


# ─────────────────────────────────────────────────────────────────────────────
# GROUP D — Experimental Treatment (Branch 4)
# Pre-flight escalation — no LLM call occurs
# ─────────────────────────────────────────────────────────────────────────────

GROUP_D: list[DemoCase] = [

    DemoCase(
        case_id="DEMO-D01",
        group="D",
        title="CAR-T Yescarta — relapsed DLBCL, FDA-approved indication",
        patient_id="PT-40001", patient_age=58,
        diagnosis_code="C83.39",
        diagnosis_description="Diffuse large B-cell lymphoma",
        procedure_code="Q2041",
        procedure_description="Axicabtagene ciloleucel (Yescarta) — CAR-T therapy",
        clinical_notes=(
            "58-year-old male, relapsed/refractory DLBCL after 2 prior lines. "
            "CD19-positive. ECOG PS 1. Adequate organ function confirmed. "
            "Requesting axicabtagene ciloleucel CAR-T therapy."
        ),
        guidelines_context=(
            "FDA approval: Axicabtagene ciloleucel approved for R/R large B-cell "
            "lymphoma after ≥2 prior lines. NCCN Category 1. "
            "However, all CAR-T therapies require specialized center administration "
            "and pre-authorization review per policy."
        ),
        expected_branch="branch_4_experimental",
        expected_outcome="IN_REVIEW",
        estimated_cost_usd=450000,
        demo_talking_points=(
            "Q2041 is on EXPERIMENTAL_PROCEDURE_CODES — triggers pre-flight "
            "immediately regardless of indication. Even FDA-approved CAR-T "
            "requires human review due to cost ($450K) and specialized "
            "administration requirements. Pre-flight fires before any LLM call."
        ),
    ),

    DemoCase(
        case_id="DEMO-D02",
        group="D",
        title="Phase II Trial Drug — HER2+ mBC, investigational ADC",
        patient_id="PT-40002", patient_age=51,
        diagnosis_code="C50.911",
        diagnosis_description="Metastatic breast cancer",
        procedure_code="J9999",
        procedure_description="Unclassified antineoplastic — investigational ADC",
        clinical_notes=(
            "51-year-old female, HER2-positive metastatic breast cancer. "
            "Enrolled in Phase II clinical trial for novel antibody-drug conjugate. "
            "Requesting authorization for investigational agent as part of protocol."
        ),
        guidelines_context=(
            "Investigational agents not covered under standard formulary. "
            "Clinical trial drugs require prior authorization review per policy."
        ),
        expected_branch="branch_4_experimental",
        expected_outcome="IN_REVIEW",
        estimated_cost_usd=18000,
        demo_talking_points=(
            "Dual trigger: J9999 (unclassified antineoplastic) is on experimental "
            "code list AND 'Phase II clinical trial'/'investigational agent' appear "
            "in clinical notes. Either trigger alone would escalate — both fire."
        ),
    ),

    DemoCase(
        case_id="DEMO-D03",
        group="D",
        title="Gene Therapy — inherited retinal dystrophy",
        patient_id="PT-40003", patient_age=19,
        diagnosis_code="H35.50",
        diagnosis_description="Unspecified hereditary retinal dystrophy",
        procedure_code="J3399",
        procedure_description="Voretigene neparvovec (Luxturna) — gene therapy",
        clinical_notes=(
            "19-year-old female, biallelic RPE65 mutation-associated retinal "
            "dystrophy confirmed by genetic testing. Best-corrected visual acuity "
            "declining. Eligible for gene therapy. Requesting voretigene neparvovec."
        ),
        guidelines_context=(
            "FDA approval: Voretigene neparvovec for RPE65 mutation-associated "
            "retinal dystrophy. Requires RPE65 genetic confirmation and viable "
            "retinal cells. Single-treatment, one-time therapy."
        ),
        expected_branch="branch_4_experimental",
        expected_outcome="IN_REVIEW",
        estimated_cost_usd=850000,
        demo_talking_points=(
            "J3399 (gene therapy — unspecified investigational) triggers pre-flight. "
            "At $850K, this is the highest-cost case in the demo set. Pre-flight "
            "is particularly important for ultra-high-cost treatments."
        ),
    ),

    DemoCase(
        case_id="DEMO-D04",
        group="D",
        title="Experimental keyword — tisagenlecleucel for pediatric ALL",
        patient_id="PT-40004", patient_age=9,
        diagnosis_code="C91.00",
        diagnosis_description="Acute lymphoblastic leukemia",
        procedure_code="Q2042",
        procedure_description="Tisagenlecleucel (Kymriah) — CAR-T",
        clinical_notes=(
            "9-year-old male, relapsed B-cell ALL after 2 prior lines. "
            "CD19-positive blasts. Requesting tisagenlecleucel CAR-T therapy. "
            "FDA-approved for pediatric ALL."
        ),
        guidelines_context=(
            "FDA: Tisagenlecleucel approved for pediatric/young adult (≤25 years) "
            "B-cell ALL after ≥2 prior lines."
        ),
        expected_branch="branch_4_experimental",
        expected_outcome="IN_REVIEW",
        estimated_cost_usd=475000,
        demo_talking_points=(
            "Pediatric patient + CAR-T (Q2042) + $475K. Three risk factors "
            "converge. Pre-flight fires on procedure code alone. Demonstrates "
            "that pre-flight protects even FDA-approved treatments that require "
            "specialized oversight."
        ),
    ),

    DemoCase(
        case_id="DEMO-D05",
        group="D",
        title="Checkpoint inhibitor — off-label colon cancer use",
        patient_id="PT-40005", patient_age=67,
        diagnosis_code="C18.9",
        diagnosis_description="Malignant neoplasm of colon",
        procedure_code="J9228",
        procedure_description="Nivolumab (Opdivo) — checkpoint inhibitor",
        clinical_notes=(
            "67-year-old male, MSI-H colorectal cancer, third-line therapy. "
            "MMR deficiency confirmed. Requesting nivolumab. Clinical notes state: "
            "'Patient enrolled in investigational protocol for combination "
            "immunotherapy — off-label use under IRB approval.'"
        ),
        guidelines_context=(
            "NCCN: Nivolumab is recommended for MSI-H CRC (Category 2A). "
            "However, clinical notes indicate investigational protocol/off-label use."
        ),
        expected_branch="branch_4_experimental",
        expected_outcome="IN_REVIEW",
        estimated_cost_usd=32000,
        demo_talking_points=(
            "The approved indication (MSI-H CRC) would normally proceed to "
            "agent evaluation. But the notes mention 'investigational protocol' "
            "and 'off-label use' — experimental keyword detection fires even "
            "though the base indication is approvable."
        ),
    ),
]


# ─────────────────────────────────────────────────────────────────────────────
# GROUP E — Rare Condition (Branch 5)
# Pre-flight by ICD-10 prefix
# ─────────────────────────────────────────────────────────────────────────────

GROUP_E: list[DemoCase] = [

    DemoCase(
        case_id="DEMO-E01",
        group="E",
        title="Gaucher Disease — enzyme replacement therapy initiation",
        patient_id="PT-50001", patient_age=42,
        diagnosis_code="E75.22",
        diagnosis_description="Gaucher disease type 1",
        procedure_code="J0205",
        procedure_description="Alglucerase (Ceredase) — enzyme replacement",
        clinical_notes=(
            "42-year-old female, confirmed Gaucher disease type 1 (enzyme assay + "
            "GBA gene mutation confirmed). Splenomegaly, thrombocytopenia, "
            "bone pain. Requesting ERT initiation."
        ),
        guidelines_context=(
            "ICGG Registry: ERT indicated for symptomatic Gaucher type 1 with "
            "organomegaly, cytopenias, or bone disease. All criteria met."
        ),
        expected_branch="branch_5_rare",
        expected_outcome="IN_REVIEW",
        estimated_cost_usd=350000,
        demo_talking_points=(
            "E75.22 → E75 prefix → RARE_CONDITION_ICD10_PREFIXES match. "
            "Pre-flight fires before any LLM evaluation. Specialist review "
            "required per guidelines anyway — pre-flight is clinically aligned."
        ),
    ),

    DemoCase(
        case_id="DEMO-E02",
        group="E",
        title="Huntington Disease — deutetrabenazine for chorea",
        patient_id="PT-50002", patient_age=47,
        diagnosis_code="G10",
        diagnosis_description="Huntington disease",
        procedure_code="J0791",
        procedure_description="Deutetrabenazine (Austedo) — VMAT2 inhibitor",
        clinical_notes=(
            "47-year-old male, confirmed Huntington disease (CAG repeat 42). "
            "Moderate chorea (UHDRS chorea score 14). Functional impact on ADLs. "
            "Requesting deutetrabenazine for chorea management."
        ),
        guidelines_context=(
            "FDA approval: Deutetrabenazine for Huntington chorea (adults). "
            "AAN Guidelines: VMAT2 inhibitors recommended for functional "
            "impact chorea (UHDRS ≥5). Score 14 meets threshold."
        ),
        expected_branch="branch_5_rare",
        expected_outcome="IN_REVIEW",
        estimated_cost_usd=42000,
        demo_talking_points=(
            "G10 is in RARE_CONDITION_ICD10_PREFIXES. Huntington disease has "
            "limited clinical guideline coverage — exactly the scenario where "
            "specialist review protects patients from AI overconfidence on "
            "thin training data."
        ),
    ),

    DemoCase(
        case_id="DEMO-E03",
        group="E",
        title="ALS Riluzole — confirmed MND, early disease stage",
        patient_id="PT-50003", patient_age=56,
        diagnosis_code="G12.21",
        diagnosis_description="Amyotrophic lateral sclerosis",
        procedure_code="J3490",
        procedure_description="Riluzole (Rilutek) — ALS therapy",
        clinical_notes=(
            "56-year-old male, ALS confirmed (El Escorial definite criteria). "
            "Disease duration 14 months. Limb onset. FVC 72%. "
            "Neurologist requesting riluzole to slow disease progression."
        ),
        guidelines_context=(
            "AAN ALS Practice Parameters: Riluzole is the only FDA-approved "
            "ALS disease-modifying therapy. Indicated for definite/probable "
            "ALS per El Escorial. FVC ≥60% required. Patient FVC 72% meets "
            "threshold. Early stage disease has most benefit."
        ),
        expected_branch="branch_5_rare",
        expected_outcome="IN_REVIEW",
        estimated_cost_usd=8400,
        demo_talking_points=(
            "G12.21 → G12 prefix → rare condition. ALS affects 5 in 100,000 — "
            "a prototypical rare disease. Despite clear guideline alignment, "
            "the rarity policy requires specialist review for all ALS therapies."
        ),
    ),

    DemoCase(
        case_id="DEMO-E04",
        group="E",
        title="Wilson Disease — penicillamine chelation therapy",
        patient_id="PT-50004", patient_age=24,
        diagnosis_code="E83.01",
        diagnosis_description="Wilson disease",
        procedure_code="S0151",
        procedure_description="Penicillamine (Cuprimine) — copper chelator",
        clinical_notes=(
            "24-year-old male, Wilson disease confirmed (serum ceruloplasmin "
            "<5 mg/dL, 24h urine copper 450 µg/day, KF rings present). "
            "Hepatic involvement (ALT 3x ULN). Requesting penicillamine "
            "chelation therapy."
        ),
        guidelines_context=(
            "EASL Wilson Disease Guidelines: Penicillamine first-line chelation "
            "for symptomatic Wilson. Criteria: confirmed diagnosis + organ "
            "involvement. All met. Neurological involvement absent."
        ),
        expected_branch="branch_5_rare",
        expected_outcome="IN_REVIEW",
        estimated_cost_usd=6200,
        demo_talking_points=(
            "E83.01 → E83 prefix → rare condition. Classic rare metabolic disease. "
            "At only $6,200 this would be an easy auto-approve based on cost, "
            "but rarity requires specialist oversight regardless of cost."
        ),
    ),
]


# ─────────────────────────────────────────────────────────────────────────────
# GROUP F — Conflicting Guidelines (Branch 6)
# NCCN vs CMS, ACR vs CMS, or multi-source disagreements
# ─────────────────────────────────────────────────────────────────────────────

GROUP_F: list[DemoCase] = [

    DemoCase(
        case_id="DEMO-F01",
        group="F",
        title="MSI-H CRC Nivolumab — NCCN recommends, CMS LCD restricts",
        patient_id="PT-60001", patient_age=67,
        diagnosis_code="C18.9",
        diagnosis_description="Colorectal cancer, MSI-H",
        procedure_code="J9228",
        procedure_description="Nivolumab (Opdivo)",
        clinical_notes=(
            "67-year-old male, MSI-H colorectal cancer, third-line. "
            "MMR deficiency confirmed by IHC. Prior FOLFOX + FOLFIRI. "
            "Requesting nivolumab."
        ),
        guidelines_context=(
            "NCCN Colon v2.2025: Nivolumab RECOMMENDED for MSI-H/dMMR CRC, "
            "any line. Category 2A.\n"
            "CMS LCD A57647: Checkpoint inhibitors for CRC are NOT covered as "
            "standard for third-line therapy without documented second-line "
            "checkpoint inhibitor pathway. Evidence limited for this indication."
        ),
        expected_branch="branch_6_conflicting",
        expected_outcome="IN_REVIEW",
        estimated_cost_usd=32000,
        demo_talking_points=(
            "NCCN Category 2A vs CMS non-coverage. Two authoritative sources "
            "directly contradict each other. System must detect the conflict "
            "and escalate — choosing either source autonomously would be wrong."
        ),
    ),

    DemoCase(
        case_id="DEMO-F02",
        group="F",
        title="Bariatric Surgery — ASMBS recommends, payer LCD restricts",
        patient_id="PT-60002", patient_age=45,
        diagnosis_code="E66.01",
        diagnosis_description="Morbid obesity",
        procedure_code="43644",
        procedure_description="Laparoscopic Roux-en-Y gastric bypass",
        clinical_notes=(
            "45-year-old male, BMI 38, T2DM and hypertension (comorbidities). "
            "6-month supervised diet completed (documented). Psych clearance "
            "obtained. Requesting bariatric surgery."
        ),
        guidelines_context=(
            "ASMBS Guidelines 2022: Bariatric surgery appropriate for BMI ≥35 "
            "with obesity-related comorbidity (T2DM + HTN both qualify). "
            "All documentation requirements met.\n"
            "Payer LCD 2023: BMI ≥40 required OR BMI ≥35 with single qualifying "
            "comorbidity documented with minimum 2-year treatment history. "
            "T2DM 2-year history documentation required."
        ),
        expected_branch="branch_6_conflicting",
        expected_outcome="IN_REVIEW",
        estimated_cost_usd=22000,
        demo_talking_points=(
            "ASMBS approves (BMI 38 + 2 comorbidities), payer LCD requires "
            "2-year T2DM history not documented. Surgical society guideline vs. "
            "insurance coverage policy conflict. Human must determine which "
            "standard applies for this specific payer."
        ),
    ),

    DemoCase(
        case_id="DEMO-F03",
        group="F",
        title="PCSK9 Inhibitor — AHA recommends, CMS requires prior statin failure",
        patient_id="PT-60003", patient_age=59,
        diagnosis_code="E78.5",
        diagnosis_description="Hyperlipidemia, unspecified",
        procedure_code="J3490",
        procedure_description="Evolocumab (Repatha) — PCSK9 inhibitor",
        clinical_notes=(
            "59-year-old female, familial hypercholesterolemia confirmed (LDL 320 "
            "mg/dL). Prior MI. Requesting evolocumab. On rosuvastatin 40mg. "
            "LDL remains elevated on max-statin."
        ),
        guidelines_context=(
            "AHA/ACC 2022: PCSK9 inhibitor recommended for ASCVD + LDL ≥70 on "
            "maximally tolerated statin. No prior ezetimibe required. "
            "Patient meets criteria.\n"
            "CMS LCD: PCSK9 inhibitor requires documented failure of BOTH "
            "maximally-tolerated statin AND ezetimibe before approval. "
            "Ezetimibe trial not documented in this submission."
        ),
        expected_branch="branch_6_conflicting",
        expected_outcome="IN_REVIEW",
        estimated_cost_usd=7200,
        demo_talking_points=(
            "AHA/ACC says statin alone is sufficient step therapy. CMS LCD "
            "requires statin + ezetimibe. This is a real, ongoing coverage "
            "conflict that affects millions of FH patients annually."
        ),
    ),

    DemoCase(
        case_id="DEMO-F04",
        group="F",
        title="Sacral Neuromodulation — AUA recommends, LCD requires OAB trial",
        patient_id="PT-60004", patient_age=62,
        diagnosis_code="N39.41",
        diagnosis_description="Urge incontinence",
        procedure_code="64590",
        procedure_description="Sacral neuromodulation — Interstim implant",
        clinical_notes=(
            "62-year-old female, refractory overactive bladder. Failed 3 oral "
            "anticholinergics (oxybutynin, tolterodine, mirabegron — all inadequate "
            "response or intolerance). Urologist recommending sacral neuromodulation."
        ),
        guidelines_context=(
            "AUA OAB Guidelines 2019: SNM recommended for refractory OAB after "
            "failure of behavioral therapy + ≥2 pharmacotherapy trials. "
            "Patient: 3 oral agent failures — exceeds minimum.\n"
            "Payer LCD 2022: Requires failure of BOTH oral anticholinergics AND "
            "onabotulinumtoxinA (Botox) injection therapy before SNM approval. "
            "Botox trial not documented."
        ),
        expected_branch="branch_6_conflicting",
        expected_outcome="IN_REVIEW",
        estimated_cost_usd=28000,
        demo_talking_points=(
            "AUA says 2 pharmacotherapy failures sufficient. Payer requires "
            "Botox specifically before SNM. Third therapy (Botox) not tried. "
            "Clinical society vs. payer coverage criteria conflict."
        ),
    ),
]


# ─────────────────────────────────────────────────────────────────────────────
# GROUP G — Prior Denial Same Service (Branch 7)
# Resubmissions triggering the prior denial pre-flight check
# ─────────────────────────────────────────────────────────────────────────────

GROUP_G: list[DemoCase] = [

    DemoCase(
        case_id="DEMO-G01",
        group="G",
        title="Pembrolizumab resubmission — denied 30 days ago, no new documentation",
        patient_id="PT-70001", patient_age=58,
        diagnosis_code="C34.1",
        diagnosis_description="Non-small cell lung cancer",
        procedure_code="J9271",
        procedure_description="Pembrolizumab injection",
        prior_denial_codes=["J9271"],
        clinical_notes=(
            "58-year-old male, same case as prior denied request. PD-L1 TPS 62%. "
            "No change in clinical status. Provider resubmitting after denial 30 "
            "days ago. No new clinical information provided."
        ),
        guidelines_context=(
            "NCCN: Pembrolizumab Category 1 for PD-L1 ≥50% NSCLC."
        ),
        expected_branch="branch_7_prior_denial",
        expected_outcome="IN_REVIEW",
        estimated_cost_usd=15000,
        demo_talking_points=(
            "Identical resubmission 30 days after denial with no new information. "
            "Human reviewer must determine: was the original denial correct? "
            "Has anything changed? Pre-flight fires before any LLM evaluation "
            "regardless of the clinical merit."
        ),
    ),

    DemoCase(
        case_id="DEMO-G02",
        group="G",
        title="Bariatric resubmission — denied 6 months ago, now completed supervised diet",
        patient_id="PT-70002", patient_age=44,
        diagnosis_code="E66.01",
        diagnosis_description="Morbid obesity",
        procedure_code="43644",
        procedure_description="Laparoscopic gastric bypass",
        prior_denial_codes=["43644"],
        clinical_notes=(
            "44-year-old female, BMI 42. Prior denial 6 months ago for incomplete "
            "supervised diet documentation. Now has completed 6-month physician- "
            "supervised weight loss program (documented). Psych clearance obtained. "
            "Resubmitting with complete documentation."
        ),
        guidelines_context=(
            "CMS Bariatric: BMI ≥40 + 6-month supervised diet + psych clearance. "
            "Reason for prior denial: supervised diet not documented. "
            "Now documented — criteria may now be met."
        ),
        expected_branch="branch_7_prior_denial",
        expected_outcome="IN_REVIEW",
        estimated_cost_usd=22000,
        demo_talking_points=(
            "Valid resubmission — the deficiency that caused denial has been "
            "corrected. Human reviewer must confirm the new documentation "
            "is genuine and adequate. Prior denial flag protects against rapid "
            "resubmission fraud while allowing legitimate appeals."
        ),
    ),

    DemoCase(
        case_id="DEMO-G03",
        group="G",
        title="SCS resubmission — denied for missing psych eval, now obtained",
        patient_id="PT-70003", patient_age=51,
        diagnosis_code="M54.51",
        diagnosis_description="Vertebrogenic low back pain",
        procedure_code="63685",
        procedure_description="Spinal cord stimulator implant",
        prior_denial_codes=["63685"],
        clinical_notes=(
            "51-year-old male, failed back surgery syndrome. Prior SCS denial: "
            "psychological evaluation missing. Now obtained (psychologist clearance "
            "documented, no contraindications found). Resubmitting for SCS implant."
        ),
        guidelines_context=(
            "CMS: SCS requires psychological evaluation pre-approval. "
            "Prior denial reason: psych eval absent. "
            "Now provided — prior denial deficiency addressed."
        ),
        expected_branch="branch_7_prior_denial",
        expected_outcome="IN_REVIEW",
        estimated_cost_usd=65000,
        demo_talking_points=(
            "Another valid resubmission where the denial deficiency was corrected. "
            "System correctly flags for human review — reviewer can see both the "
            "original denial reason and confirm the new documentation addresses it."
        ),
    ),

    DemoCase(
        case_id="DEMO-G04",
        group="G",
        title="Rapid resubmission — same day denial and resubmit, fraud pattern",
        patient_id="PT-70004", patient_age=37,
        diagnosis_code="M54.5",
        diagnosis_description="Low back pain",
        procedure_code="72148",
        procedure_description="MRI lumbar spine",
        prior_denial_codes=["72148"],
        clinical_notes=(
            "37-year-old male, requesting MRI lumbar spine. Provider notes: "
            "'Prior authorization denied — appealing immediately.' "
            "Same-day resubmission. No new clinical information."
        ),
        guidelines_context=(
            "CMS LCD L34976: MRI requires ≥6 weeks symptoms + conservative therapy."
        ),
        expected_branch="branch_7_prior_denial",
        expected_outcome="IN_REVIEW",
        estimated_cost_usd=1200,
        demo_talking_points=(
            "Same-day denial + resubmission with no new information. This pattern "
            "is associated with prior authorization gaming. Human reviewer can "
            "evaluate whether this is a legitimate appeal or an attempt to "
            "circumvent the denial through repeated submission."
        ),
    ),
]


# ─────────────────────────────────────────────────────────────────────────────
# GROUP H — Precedent-Based Approvals
# Institutional memory influences correct approval
# ─────────────────────────────────────────────────────────────────────────────

GROUP_H: list[DemoCase] = [

    DemoCase(
        case_id="DEMO-H01",
        group="H",
        title="MRI spine — 4 weeks symptoms, foot drop precedent enables approval",
        patient_id="PT-80001", patient_age=48,
        diagnosis_code="M54.5",
        diagnosis_description="Low back pain with L5 radiculopathy",
        procedure_code="72148",
        procedure_description="MRI lumbar spine",
        clinical_notes=(
            "48-year-old male, back pain 4 weeks, severe left L5 radiculopathy. "
            "Motor weakness 4/5 left foot dorsiflexion, developing over 10 days. "
            "Conservative therapy x 3 weeks. Neurologist: 'concerning for "
            "developing foot drop — needs urgent imaging.'"
        ),
        guidelines_context=(
            "CMS LCD: MRI requires ≥6 weeks conservative therapy. "
            "EXCEPTION: neurological red flags override 6-week requirement. "
            "PAST MEDICAL DIRECTOR DECISIONS (PRECEDENTS): "
            "1. Approved MRI at 3 weeks: progressive foot drop is neurological "
            "emergency — 6-week rule overridden. "
            "2. Approved MRI at 2 weeks: motor strength 3/5 with acute decline "
            "constitutes emergency exception."
        ),
        expected_branch="branch_1_auto_approve",
        expected_outcome="AUTO_APPROVED",
        estimated_cost_usd=1200,
        demo_talking_points=(
            "Motor weakness + developing foot drop = neurological emergency. "
            "4 weeks < 6 week rule, BUT precedents confirm motor weakness "
            "overrides duration requirement. Tests whether agent correctly "
            "applies institutional memory from the precedents section."
        ),
    ),

    DemoCase(
        case_id="DEMO-H02",
        group="H",
        title="Off-label indication — precedent enables rare cancer approval",
        patient_id="PT-80002", patient_age=44,
        diagnosis_code="C49.20",
        diagnosis_description="Malignant neoplasm of connective tissue, unspecified",
        procedure_code="J9271",
        procedure_description="Pembrolizumab — off-label sarcoma use",
        clinical_notes=(
            "44-year-old female, advanced desmoplastic small round cell tumor "
            "(DSRCT), MSI-H confirmed. Tumor mutational burden 18 mut/Mb. "
            "2 prior chemotherapy regimens failed. Requesting pembrolizumab. "
            "No standard of care exists for refractory DSRCT."
        ),
        guidelines_context=(
            "NCCN Pembrolizumab: Approved for TMB-high (≥10 mut/Mb) solid "
            "tumors regardless of histology (agnostic indication). "
            "PAST MEDICAL DIRECTOR DECISIONS (PRECEDENTS): "
            "MD approved pembrolizumab for MSI-H/TMB-high sarcoma despite "
            "off-label histology — FDA tumor-agnostic approval applies."
        ),
        expected_branch="branch_1_auto_approve",
        expected_outcome="AUTO_APPROVED",
        estimated_cost_usd=15000,
        demo_talking_points=(
            "Off-label by histology but on-label by biomarker (TMB-high agnostic). "
            "Agent must reconcile the off-label diagnosis with the on-label "
            "biomarker indication, guided by the MD precedent showing this "
            "is an established approved use."
        ),
    ),

    DemoCase(
        case_id="DEMO-H03",
        group="H",
        title="Expedited authorization — palliative symptom control, end-of-life",
        patient_id="PT-80003", patient_age=71,
        diagnosis_code="C34.12",
        diagnosis_description="Malignant neoplasm of upper lobe, left bronchus",
        procedure_code="J9270",
        procedure_description="Morphine sulfate injection — palliative care",
        clinical_notes=(
            "71-year-old male, stage IV NSCLC, hospice enrolled. "
            "Severe dyspnea and pain, comfort measures only. "
            "Requesting morphine for palliative symptom control. "
            "Hospice physician certifies terminal prognosis ≤6 months."
        ),
        guidelines_context=(
            "CMS: Hospice-enrolled patients — medications for palliation of "
            "terminal illness symptoms are covered without prior authorization "
            "when hospice election documented. "
            "PAST MEDICAL DIRECTOR DECISIONS (PRECEDENTS): "
            "Expedited approval: morphine for hospice-enrolled patients "
            "bypasses standard PA process per CMS hospice benefit rules."
        ),
        expected_branch="branch_1_auto_approve",
        expected_outcome="AUTO_APPROVED",
        estimated_cost_usd=180,
        demo_talking_points=(
            "Lowest-cost case in demo set ($180). Hospice enrollment creates "
            "a CMS exception to standard PA requirements. Precedent confirms "
            "expedited approval is appropriate. Shows the system handles "
            "end-of-life care with appropriate speed and compassion."
        ),
    ),
]


# ─────────────────────────────────────────────────────────────────────────────
# Aggregate all cases
# ─────────────────────────────────────────────────────────────────────────────

ALL_CASES: list[DemoCase] = (
    GROUP_A + GROUP_B + GROUP_C + GROUP_D +
    GROUP_E + GROUP_F + GROUP_G + GROUP_H
)


def build_summary() -> dict:
    """Return distribution statistics for the demo set."""
    by_group: dict[str, int] = {}
    by_branch: dict[str, int] = {}
    by_outcome: dict[str, int] = {}
    total_cost = 0

    for case in ALL_CASES:
        by_group[case.group] = by_group.get(case.group, 0) + 1
        by_branch[case.expected_branch] = by_branch.get(case.expected_branch, 0) + 1
        by_outcome[case.expected_outcome] = by_outcome.get(case.expected_outcome, 0) + 1
        total_cost += case.estimated_cost_usd

    return {
        "total_cases": len(ALL_CASES),
        "by_group": by_group,
        "by_branch": by_branch,
        "by_outcome": by_outcome,
        "total_estimated_cost_usd": total_cost,
        "avg_cost_usd": total_cost // len(ALL_CASES),
    }


def write_cases_json(output_path: str) -> None:
    """Write all cases to a JSON file."""
    data = {
        "version": "2.2.0",
        "summary": build_summary(),
        "cases": [asdict(c) for c in ALL_CASES],
    }
    with open(output_path, "w") as f:
        json.dump(data, f, indent=2)
    print(f"  ✓ Wrote {len(ALL_CASES)} cases to {output_path}")


def write_demo_report(output_path: str) -> None:
    """Write a human-readable markdown demo walkthrough."""
    summary = build_summary()

    lines = [
        "# PACCA v2.2.0 — Demo Case Walkthrough",
        "",
        "## Overview",
        "",
        f"**{summary['total_cases']} synthesized prior authorization cases** "
        f"covering all 7 escalation branches.",
        "",
        f"| Metric | Value |",
        f"|--------|-------|",
        f"| Total cases | {summary['total_cases']} |",
        f"| Total estimated cost | ${summary['total_estimated_cost_usd']:,} |",
        f"| Average case cost | ${summary['avg_cost_usd']:,} |",
        "",
        "## Distribution by Escalation Branch",
        "",
        "| Branch | Cases | Description |",
        "|--------|-------|-------------|",
    ]

    branch_descriptions = {
        "branch_1_auto_approve": "High confidence auto-approval",
        "branch_2_medical_director": "Ambiguous confidence → MD Agent",
        "branch_3_low_confidence": "Low confidence → human review",
        "branch_4_experimental": "Experimental treatment pre-flight",
        "branch_5_rare": "Rare condition pre-flight",
        "branch_6_conflicting": "Conflicting guidelines pre-flight",
        "branch_7_prior_denial": "Prior denial same service pre-flight",
    }

    for branch, count in sorted(summary["by_branch"].items()):
        desc = branch_descriptions.get(branch, branch)
        lines.append(f"| {branch} | {count} | {desc} |")

    lines += [
        "",
        "## Distribution by Outcome",
        "",
        "| Outcome | Cases |",
        "|---------|-------|",
    ]
    for outcome, count in sorted(summary["by_outcome"].items()):
        lines.append(f"| {outcome} | {count} |")

    lines += ["", "---", ""]

    group_names = {
        "A": "Group A — Auto-Approved (Branch 1)",
        "B": "Group B — Human Review / Low Confidence (Branch 3)",
        "C": "Group C — Medical Director Escalation (Branch 2)",
        "D": "Group D — Experimental Treatment (Branch 4)",
        "E": "Group E — Rare Condition (Branch 5)",
        "F": "Group F — Conflicting Guidelines (Branch 6)",
        "G": "Group G — Prior Denial (Branch 7)",
        "H": "Group H — Precedent-Based Approvals",
    }

    for group_key in "ABCDEFGH":
        group_cases = [c for c in ALL_CASES if c.group == group_key]
        if not group_cases:
            continue

        lines += [
            f"## {group_names.get(group_key, f'Group {group_key}')}",
            "",
        ]

        for case in group_cases:
            lines += [
                f"### {case.case_id}: {case.title}",
                "",
                f"- **Diagnosis:** {case.diagnosis_code} — {case.diagnosis_description}",
                f"- **Procedure:** {case.procedure_code} — {case.procedure_description}",
                f"- **Patient:** {case.patient_age}y (ID: {case.patient_id})",
                f"- **Est. Cost:** ${case.estimated_cost_usd:,}",
                f"- **Expected Branch:** `{case.expected_branch}`",
                f"- **Expected Outcome:** `{case.expected_outcome}`",
                "",
                f"**Clinical Notes:**",
                f"> {case.clinical_notes}",
                "",
                f"**Demo Talking Points:**",
                f"> {case.demo_talking_points}",
                "",
            ]
            if case.prior_denial_codes:
                lines.append(f"*Prior denial codes: {case.prior_denial_codes}*")
                lines.append("")

        lines.append("---")
        lines.append("")

    lines += [
        "## Interview / Demo Script",
        "",
        "### Opening (2 minutes)",
        "Start with DEMO-A01 (NSCLC pembrolizumab). Walk through:",
        "1. Show the clinical notes — PD-L1 62%, EGFR/ALK negative, ECOG 1",
        "2. Show the NCCN guidelines context",
        "3. Show the agent decision — confidence 0.97, AUTO_APPROVED",
        "4. Explain: 'Every criterion explicitly documented → high confidence → "
        "   auto-approve with zero human touch'",
        "",
        "### The Safety Story (3 minutes)",
        "Show DEMO-D01 (CAR-T therapy) immediately after A01:",
        "1. Same oncology domain, but Q2041 is on the experimental code list",
        "2. System routes to human review BEFORE calling the LLM",
        "3. Explain: 'Pre-flight checks enforce policy deterministically. "
        "   A confident AI is not the same as a correct AI for experimental treatments'",
        "",
        "### The Hallucination Trap (2 minutes)",
        "Show DEMO-B01 (sparse NSCLC notes):",
        "1. Notes: 'Patient has lung cancer. Requesting pembrolizumab.'",
        "2. Show the agent correctly identifying missing PD-L1, EGFR/ALK",
        "3. Explain: 'A less careful system would fill in the blanks. "
        "   PACCA only references what's actually in the submission.'",
        "",
        "### Institutional Memory (2 minutes)",
        "Show DEMO-H01 (foot drop with precedent):",
        "1. 4 weeks < 6-week CMS rule",
        "2. But foot drop = neurological emergency override in precedents",
        "3. System approves citing both the exception clause AND the precedent",
        "4. Explain: 'The system learns from past Medical Director decisions "
        "   without retraining the underlying model'",
        "",
        "### The Governance Story (2 minutes)",
        "Reference the EvolutionAgent:",
        "1. After 10+ cases approve MRI despite < 6 weeks for foot drop",
        "2. EvolutionAgent proposes a guideline amendment",
        "3. Medical Director reviews and approves the proposal",
        "4. Amendment deployed — future cases handled consistently",
        "5. Complete audit trail of who approved what and when",
        "",
        "---",
        "",
        "*Generated by demo/generate_demo_data.py — PACCA v2.2.0*",
    ]

    with open(output_path, "w") as f:
        f.write("\n".join(lines))
    print(f"  ✓ Wrote demo report to {output_path}")


def write_run_demo_script(output_path: str) -> None:
    """Write an executable script that runs cases through the live Orchestrator."""
    script = '''#!/usr/bin/env python3
"""
PACCA Live Demo Runner — v2.2.0
================================
Runs synthesized demo cases through the live Orchestrator, generating
real traces in Langfuse and producing a results summary.

Usage:
    cd /Users/davidreed/David_Portfolio/pacca
    source venv/bin/activate
    export ANTHROPIC_API_KEY=sk-ant-...
    python demo/run_demo.py [--groups ABCDEFGH] [--limit 10]

Options:
    --groups    Which case groups to run (default: all)
    --limit     Max cases to run (default: all)
    --dry-run   Print cases without running them
"""

import asyncio
import json
import os
import sys
import argparse
from pathlib import Path
from datetime import datetime

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

os.environ.setdefault("APP_ENV", "development")
os.environ.setdefault("OTEL_ENABLED", "true")

from pacca.agents.orchestrator import Orchestrator
from pacca.agents.decision import DecisionContext
from pacca.models.clinical import ClinicalCase, EvidenceItem
from pacca.models.enums import EvidenceSourceType


def load_cases(groups: str = "ABCDEFGH", limit: int = 0) -> list[dict]:
    cases_path = Path(__file__).parent / "cases.json"
    if not cases_path.exists():
        print(f"ERROR: {cases_path} not found. Run generate_demo_data.py first.")
        sys.exit(1)

    with open(cases_path) as f:
        data = json.load(f)

    cases = [c for c in data["cases"] if c["group"] in groups]
    if limit:
        cases = cases[:limit]
    return cases


def case_to_clinical(raw: dict) -> ClinicalCase:
    """Convert raw demo case dict to ClinicalCase domain model."""
    return ClinicalCase(
        patient_id=raw["patient_id"],
        primary_diagnosis_code=raw["diagnosis_code"],
        procedure_code=raw["procedure_code"],
        evidence=[
            EvidenceItem(
                id="e1",
                source_type=EvidenceSourceType.CLINICAL_NOTE,
                description=raw["clinical_notes"][:200],
                original_text=raw["clinical_notes"],
                confidence=0.9,
            )
        ],
    )


async def run_cases(cases: list[dict], dry_run: bool = False) -> dict:
    orchestrator = Orchestrator()
    results = []

    print(f"\\nRunning {len(cases)} demo cases...")
    print("=" * 60)

    for i, raw in enumerate(cases, 1):
        case_id = raw["case_id"]
        title = raw["title"][:55]
        expected = raw["expected_outcome"]

        if dry_run:
            print(f"  [{i:02d}] {case_id}: {title}")
            print(f"         Expected: {expected} | Branch: {raw[\'expected_branch\']}")
            continue

        print(f"  [{i:02d}] {case_id}: {title}...", end=" ", flush=True)

        try:
            clinical_case = case_to_clinical(raw)
            ctx = DecisionContext(
                case=clinical_case,
                relevant_guidelines=raw["guidelines_context"],
            )

            decision = await orchestrator.process_decision(
                ctx,
                prior_denial_codes=raw.get("prior_denial_codes", []),
            )

            actual = decision.status.value
            match = "✓" if actual == expected else "✗"
            confidence = f"{decision.confidence_score:.2f}" if decision.confidence_score > 0 else "N/A"

            print(f"{match} {actual} (conf: {confidence})")

            results.append({
                "case_id": case_id,
                "expected": expected,
                "actual": actual,
                "confidence": decision.confidence_score,
                "match": actual == expected,
                "rationale_preview": decision.rationale[:120],
            })

        except Exception as e:
            print(f"ERROR: {e}")
            results.append({
                "case_id": case_id,
                "expected": expected,
                "actual": "ERROR",
                "confidence": 0,
                "match": False,
                "error": str(e),
            })

    if dry_run:
        return {"dry_run": True, "cases": len(cases)}

    # Summary
    passed = sum(1 for r in results if r["match"])
    failed = [r for r in results if not r["match"]]

    print("\\n" + "=" * 60)
    print(f"Results: {passed}/{len(results)} cases matched expected outcome")
    print(f"Accuracy: {passed/len(results):.1%}")

    if failed:
        print(f"\\nMismatches ({len(failed)}):")
        for r in failed:
            print(f"  {r[\'case_id\']}: expected {r[\'expected\']}, got {r[\'actual\']}")

    # Save results
    results_path = Path(__file__).parent / f"results_{datetime.now().strftime(\'%Y%m%d_%H%M%S\')}.json"
    with open(results_path, "w") as f:
        json.dump({
            "run_at": datetime.now().isoformat(),
            "cases_run": len(results),
            "passed": passed,
            "accuracy": passed/len(results),
            "results": results,
        }, f, indent=2)
    print(f"\\nFull results saved to {results_path}")

    return {"passed": passed, "total": len(results)}


def main():
    parser = argparse.ArgumentParser(description="PACCA Demo Runner")
    parser.add_argument("--groups", default="ABCDEFGH",
                        help="Which groups to run (e.g. AB or DEFGH)")
    parser.add_argument("--limit", type=int, default=0,
                        help="Max cases to run (0 = all)")
    parser.add_argument("--dry-run", action="store_true",
                        help="Print cases without running them")
    args = parser.parse_args()

    if not args.dry_run and not os.getenv("ANTHROPIC_API_KEY"):
        print("ERROR: ANTHROPIC_API_KEY not set.")
        print("Export it: export ANTHROPIC_API_KEY=sk-ant-...")
        sys.exit(1)

    cases = load_cases(groups=args.groups, limit=args.limit)
    print(f"Loaded {len(cases)} cases from groups: {args.groups}")

    asyncio.run(run_cases(cases, dry_run=args.dry_run))


if __name__ == "__main__":
    main()
'''
    with open(output_path, "w") as f:
        f.write(script)
    os.chmod(output_path, 0o755)
    print(f"  ✓ Wrote demo runner to {output_path}")


def main():
    # Output directory is the same directory this script lives in (demo/)
    script_dir = os.path.dirname(os.path.abspath(__file__))
    demo_dir = script_dir
    os.makedirs(demo_dir, exist_ok=True)

    summary = build_summary()
    print(f"\nPACCA Demo Data Generator — v2.2.0")
    print(f"====================================")
    print(f"Total cases: {summary['total_cases']}")
    print(f"By group: {summary['by_group']}")
    print(f"By outcome: {summary['by_outcome']}")
    print(f"Total estimated cost: ${summary['total_estimated_cost_usd']:,}")
    print(f"\nWriting output files to {demo_dir}/")

    write_cases_json(os.path.join(demo_dir, "cases.json"))
    write_demo_report(os.path.join(demo_dir, "demo_report.md"))
    write_run_demo_script(os.path.join(demo_dir, "run_demo.py"))

    print(f"\nDone. Next steps:")
    print(f"  1. Review demo/demo_report.md for the interview walkthrough")
    print(f"  2. Run: python demo/run_demo.py --dry-run   (verify cases load)")
    print(f"  3. Run: python demo/run_demo.py --groups AB --limit 5   (quick test)")
    print(f"  4. Run: python demo/run_demo.py   (full demo, populates Langfuse)")


if __name__ == "__main__":
    main()
