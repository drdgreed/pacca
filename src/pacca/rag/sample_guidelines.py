"""
Sample clinical guidelines for the PACCA demo system.

These are simplified versions of real clinical guidelines,
used for demonstration and testing purposes only.
"""

from datetime import date

from pacca.models import (
    ClinicalGuideline,
    ClinicalSpecialty,
    GuidelineCriterion,
    StepTherapyRequirement,
    TreatmentCategory,
)


# Oncology - Immunotherapy Guidelines
NSCLC_IMMUNOTHERAPY_GUIDELINE = ClinicalGuideline(
    guideline_id="NCCN-NSCLC-IO-2026",
    name="NCCN Guidelines: Non-Small Cell Lung Cancer Immunotherapy",
    version="2026.1",
    effective_date=date(2026, 1, 1),
    source="NCCN",
    source_url="https://www.nccn.org/guidelines",
    evidence_level="Category 1",
    specialties=[ClinicalSpecialty.ONCOLOGY, ClinicalSpecialty.PULMONOLOGY],
    treatment_categories=[TreatmentCategory.MEDICATION],
    applicable_diagnoses=["C34.0", "C34.1", "C34.2", "C34.3", "C34.8", "C34.9"],
    applicable_treatments=["J9271", "J9299", "J9228"],
    summary=(
        "Evidence-based recommendations for immunotherapy in non-small cell "
        "lung cancer, including pembrolizumab, nivolumab, and atezolizumab."
    ),
    full_text="""
# NCCN Guidelines: Immunotherapy for Non-Small Cell Lung Cancer

## Overview
Immune checkpoint inhibitors have revolutionized the treatment of advanced
non-small cell lung cancer (NSCLC). This guideline provides evidence-based
recommendations for the use of PD-1/PD-L1 inhibitors.

## First-Line Therapy Recommendations

### For PD-L1 ≥50% (TPS), No EGFR/ALK Alterations
**Category 1 Recommendations:**
- Pembrolizumab (Keytruda) monotherapy is preferred for patients with
  PD-L1 TPS ≥50% and no contraindications to immunotherapy
- Dosing: 200mg IV every 3 weeks or 400mg IV every 6 weeks
- Continue until disease progression or unacceptable toxicity

### For PD-L1 1-49% (TPS), No EGFR/ALK Alterations
**Category 1 Recommendations:**
- Pembrolizumab + platinum-based chemotherapy
- Atezolizumab + bevacizumab + chemotherapy (non-squamous)
- Nivolumab + ipilimumab + chemotherapy

## Biomarker Testing Requirements
Prior to initiating immunotherapy, the following tests are REQUIRED:
1. PD-L1 expression testing (TPS or CPS)
2. EGFR mutation testing (at minimum exons 18-21)
3. ALK rearrangement testing
4. ROS1 rearrangement testing (adenocarcinoma)

Optional but recommended:
- BRAF V600E mutation
- KRAS G12C mutation
- MET exon 14 skipping
- RET rearrangement
- NTRK fusion

## Contraindications
Immunotherapy is contraindicated in patients with:
- Active autoimmune disease requiring systemic treatment
- History of severe immune-related adverse events (Grade 4)
- Solid organ transplant recipients
- Active interstitial lung disease

## Monitoring Requirements
- Thyroid function tests every 6 weeks during treatment
- Liver function tests every 2-4 weeks initially
- Assessment for immune-related adverse events at each visit

## Prior Authorization Criteria
For prior authorization approval, the following must be documented:
1. Histologically confirmed NSCLC (adenocarcinoma, squamous, or NOS)
2. Stage III (unresectable) or Stage IV disease
3. PD-L1 testing results with TPS percentage
4. EGFR and ALK testing results (negative for targetable mutations)
5. ECOG performance status 0-2
6. No active autoimmune disease
7. Adequate organ function (labs within 14 days)
""",
    inclusion_criteria=[
        GuidelineCriterion(
            description="Histologically confirmed NSCLC",
            criterion_type="inclusion",
            required=True,
            diagnosis_codes=["C34.0", "C34.1", "C34.2", "C34.3"],
        ),
        GuidelineCriterion(
            description="PD-L1 TPS ≥50% for monotherapy",
            criterion_type="inclusion",
            required=True,
            lab_requirements=[{"test": "PD-L1 TPS", "operator": ">=", "value": 50}],
        ),
        GuidelineCriterion(
            description="EGFR/ALK negative",
            criterion_type="inclusion",
            required=True,
        ),
    ],
    exclusion_criteria=[
        GuidelineCriterion(
            description="Active autoimmune disease",
            criterion_type="exclusion",
        ),
        GuidelineCriterion(
            description="Prior solid organ transplant",
            criterion_type="exclusion",
        ),
    ],
    documentation_requirements=[
        "Pathology report confirming NSCLC",
        "PD-L1 test results",
        "EGFR/ALK mutation testing results",
        "Staging documentation (CT/PET)",
        "ECOG performance status",
    ],
)


# Imaging - MRI Guidelines
LUMBAR_MRI_GUIDELINE = ClinicalGuideline(
    guideline_id="ACR-AC-SPINE-2026",
    name="ACR Appropriateness Criteria: Low Back Pain",
    version="2026.1",
    effective_date=date(2026, 1, 1),
    source="ACR",
    source_url="https://www.acr.org/Clinical-Resources/ACR-Appropriateness-Criteria",
    evidence_level="Evidence-based",
    specialties=[
        ClinicalSpecialty.RADIOLOGY,
        ClinicalSpecialty.ORTHOPEDICS,
        ClinicalSpecialty.NEUROLOGY,
    ],
    treatment_categories=[TreatmentCategory.IMAGING],
    applicable_diagnoses=["M54.5", "M54.4", "M54.3", "M51.16", "M51.17"],
    applicable_treatments=["72148", "72149", "72158"],
    summary=(
        "Evidence-based imaging recommendations for patients with low back pain, "
        "including appropriate use criteria for MRI of the lumbar spine."
    ),
    full_text="""
# ACR Appropriateness Criteria: Low Back Pain

## Overview
Low back pain is one of the most common reasons for physician visits. Most
cases of low back pain are self-limiting and do not require imaging. This
guideline provides criteria for appropriate imaging.

## When Imaging is NOT Indicated
MRI is NOT indicated for:
- Acute low back pain (<6 weeks) without red flags
- Non-specific low back pain responding to conservative treatment
- Chronic low back pain that is stable and manageable

## When MRI IS Indicated (Usually Appropriate)

### Red Flag Symptoms
MRI is indicated when the following are present:
- Cauda equina syndrome symptoms (saddle anesthesia, bladder dysfunction)
- Progressive neurological deficit
- Suspected spinal infection (fever + back pain)
- Suspected malignancy (history of cancer + new back pain)
- Recent significant trauma

### After Failed Conservative Treatment
MRI may be appropriate after:
- 6 weeks of conservative treatment without improvement
- Conservative treatment includes: NSAIDs, physical therapy, activity modification
- Failed conservative treatment must be documented

### Pre-surgical Planning
MRI is appropriate when:
- Surgery is being considered
- Specific surgical target needs to be identified
- Patient has radicular symptoms correlating with specific nerve root

## Documentation Requirements for Prior Authorization

### Required Documentation:
1. Duration of symptoms (>6 weeks for non-urgent)
2. Description of conservative treatments tried
3. Duration of each conservative treatment
4. Response to conservative treatment
5. Physical examination findings
6. Neurological examination (strength, reflexes, sensation)
7. Presence or absence of red flag symptoms

### Conservative Treatment Criteria:
Prior to MRI authorization (unless red flags present):
- Minimum 4-6 weeks of conservative management
- At least ONE of the following:
  - NSAIDs or other analgesics (minimum 2 weeks)
  - Physical therapy (minimum 4 sessions)
  - Chiropractic care (minimum 4 visits)
- Documentation of treatment failure or inadequate response

## MRI Protocol Recommendations
- Non-contrast MRI is usually sufficient for initial evaluation
- Contrast MRI indicated for:
  - Suspected infection
  - Post-surgical evaluation
  - Suspected tumor
  - Evaluation of enhancement patterns
""",
    inclusion_criteria=[
        GuidelineCriterion(
            description="Symptoms >6 weeks duration",
            criterion_type="inclusion",
            alternatives=["Red flag symptoms present"],
        ),
        GuidelineCriterion(
            description="Failed conservative treatment",
            criterion_type="inclusion",
            evidence_requirements=[
                "Documentation of NSAIDs trial",
                "Physical therapy notes",
            ],
        ),
    ],
    step_therapy=[
        StepTherapyRequirement(
            step_number=1,
            required_treatments=["NSAIDs", "Acetaminophen"],
            minimum_duration_days=14,
            failure_criteria="Inadequate pain relief",
            exceptions=["Red flag symptoms", "Contraindication to NSAIDs"],
        ),
        StepTherapyRequirement(
            step_number=2,
            required_treatments=["Physical therapy", "Chiropractic"],
            minimum_duration_days=28,
            documentation_required=["Therapy notes", "Progress assessment"],
            exceptions=["Red flag symptoms", "Unable to participate in therapy"],
        ),
    ],
    documentation_requirements=[
        "Symptom duration",
        "Conservative treatment history",
        "Physical examination findings",
        "Neurological examination",
        "Red flag assessment",
    ],
)


# Cardiology - Cardiac Imaging Guidelines
CARDIAC_IMAGING_GUIDELINE = ClinicalGuideline(
    guideline_id="AHA-CARDIAC-IMG-2026",
    name="AHA/ACC Appropriate Use Criteria for Cardiac Imaging",
    version="2026.1",
    effective_date=date(2026, 1, 1),
    source="AHA/ACC",
    source_url="https://www.heart.org/guidelines",
    evidence_level="Category A",
    specialties=[ClinicalSpecialty.CARDIOLOGY, ClinicalSpecialty.RADIOLOGY],
    treatment_categories=[TreatmentCategory.IMAGING],
    applicable_diagnoses=["I25.10", "I20.9", "R00.0", "R94.31"],
    applicable_treatments=["93306", "93307", "78452", "75574"],
    summary=(
        "Appropriate use criteria for cardiac imaging including echocardiography, "
        "nuclear stress testing, and cardiac CT/MRI."
    ),
    full_text="""
# AHA/ACC Appropriate Use Criteria for Cardiac Imaging

## Overview
Cardiac imaging plays a critical role in diagnosis and management of
cardiovascular disease. These criteria help ensure appropriate utilization.

## Echocardiography (TTE/TEE)

### Appropriate Indications:
- Evaluation of suspected heart failure
- Assessment of valvular heart disease
- Evaluation of pericardial disease
- Assessment after acute MI
- Evaluation of suspected endocarditis
- Pre-operative cardiac evaluation (high-risk surgery)

### Rarely Appropriate:
- Routine pre-operative evaluation (low-risk surgery, asymptomatic)
- Routine follow-up of stable, mild valvular disease
- Screening in asymptomatic patients without risk factors

## Stress Testing with Imaging

### Nuclear Stress Testing (SPECT/PET)
**Appropriate:**
- Intermediate pre-test probability of CAD
- Risk stratification after acute coronary syndrome
- Evaluation of ischemia in known CAD

**Inappropriate:**
- Low pre-test probability of CAD
- Routine screening in asymptomatic patients
- Follow-up of known CAD without change in symptoms

### Stress Echocardiography
**Appropriate:**
- Evaluation of exertional symptoms
- Pre-operative risk assessment
- Viability assessment

## Cardiac CT

### Coronary CT Angiography (CCTA)
**Appropriate:**
- Intermediate risk chest pain (acute or stable)
- Evaluation of coronary anomalies
- Pre-TAVR planning

**Inappropriate:**
- High pre-test probability (proceed to cath)
- Very low pre-test probability
- Routine screening

## Prior Authorization Requirements

### For Stress Testing:
1. Pre-test probability assessment documented
2. Symptoms or clinical indication documented
3. Baseline ECG interpretation
4. Unable to exercise (for pharmacologic stress)

### For Advanced Imaging (CT/MRI):
1. Clinical question clearly stated
2. Alternative tests considered
3. No recent similar imaging
4. Results will change management
""",
    inclusion_criteria=[
        GuidelineCriterion(
            description="Intermediate pre-test probability of CAD",
            criterion_type="inclusion",
        ),
        GuidelineCriterion(
            description="Symptoms suggestive of cardiac disease",
            criterion_type="inclusion",
        ),
    ],
    exclusion_criteria=[
        GuidelineCriterion(
            description="Very low pre-test probability",
            criterion_type="exclusion",
        ),
        GuidelineCriterion(
            description="Asymptomatic screening without risk factors",
            criterion_type="exclusion",
        ),
    ],
    documentation_requirements=[
        "Cardiac symptoms description",
        "Risk factor assessment",
        "Pre-test probability calculation",
        "Prior cardiac workup results",
    ],
)


# Biologic Therapy Guidelines
RHEUMATOLOGY_BIOLOGIC_GUIDELINE = ClinicalGuideline(
    guideline_id="ACR-RA-BIO-2026",
    name="ACR Guidelines: Biologic Therapy for Rheumatoid Arthritis",
    version="2026.1",
    effective_date=date(2026, 1, 1),
    source="ACR",
    source_url="https://www.rheumatology.org/guidelines",
    evidence_level="Strong Recommendation",
    specialties=[ClinicalSpecialty.RHEUMATOLOGY],
    treatment_categories=[TreatmentCategory.MEDICATION],
    applicable_diagnoses=["M05.79", "M06.09", "M06.89"],
    applicable_treatments=["J0129", "J1745", "J0135", "J3262"],
    summary=(
        "Evidence-based recommendations for biologic DMARD therapy in "
        "rheumatoid arthritis, including step therapy requirements."
    ),
    full_text="""
# ACR Guidelines: Biologic Therapy for Rheumatoid Arthritis

## Treatment Algorithm

### First-Line Therapy
- Methotrexate (MTX) is the preferred first-line DMARD
- Dose: Start 7.5-15mg weekly, titrate to 20-25mg weekly
- Duration: Minimum 3 months at optimal dose before biologic consideration

### When to Consider Biologics
Biologic DMARDs are appropriate when:
1. Inadequate response to methotrexate (MTX) at optimal dose
2. MTX intolerance or contraindication
3. Poor prognostic features present

### Step Therapy Requirements

#### Step 1: Conventional DMARDs
- Methotrexate 15-25mg weekly for minimum 12 weeks
- OR Leflunomide 20mg daily for minimum 12 weeks
- OR Sulfasalazine + Hydroxychloroquine combination

#### Step 2: Add or Switch to Biologic
If Step 1 fails (defined as DAS28 >3.2 or continued moderate/high disease activity):
- Add TNF inhibitor (adalimumab, etanercept, infliximab, certolizumab, golimumab)
- OR Add non-TNF biologic (abatacept, rituximab, tocilizumab, sarilumab)
- OR Add JAK inhibitor (tofacitinib, baricitinib, upadacitinib)

### Pre-Treatment Screening
Before starting biologic therapy:
1. TB screening (PPD or IGRA) - REQUIRED
2. Hepatitis B and C serology - REQUIRED
3. CBC with differential
4. Liver function tests
5. Lipid panel (for JAK inhibitors)
6. Chest X-ray (if TB risk factors)

### Documentation Requirements
1. Diagnosis of RA (ACR/EULAR criteria)
2. Disease activity score (DAS28, CDAI, or SDAI)
3. Prior DMARD trials with dates, doses, and reasons for discontinuation
4. TB screening results (within 6 months)
5. Hepatitis B/C results
6. Current MTX dose (if combination therapy planned)
7. Contraindications to conventional DMARDs (if seeking first-line biologic)

### Contraindications to Biologics
- Active serious infection
- Untreated latent TB
- Active hepatitis B
- Recent live vaccine (within 4 weeks)
- Severe heart failure (NYHA class III/IV) - for TNF inhibitors
- Multiple sclerosis - for TNF inhibitors
""",
    inclusion_criteria=[
        GuidelineCriterion(
            description="Confirmed diagnosis of rheumatoid arthritis",
            criterion_type="inclusion",
            required=True,
            diagnosis_codes=["M05.79", "M06.09"],
        ),
        GuidelineCriterion(
            description="Failed conventional DMARD therapy",
            criterion_type="inclusion",
            required=True,
            alternatives=["Contraindication to conventional DMARDs"],
        ),
    ],
    step_therapy=[
        StepTherapyRequirement(
            step_number=1,
            required_treatments=["Methotrexate", "Leflunomide"],
            minimum_duration_days=84,
            failure_criteria="DAS28 >3.2 or moderate/high disease activity",
            documentation_required=[
                "Baseline DAS28 score",
                "Treatment dates and doses",
                "Follow-up disease activity assessment",
            ],
            exceptions=[
                "Hepatotoxicity from methotrexate",
                "Severe cytopenias",
                "Pregnancy planning",
            ],
        ),
    ],
    documentation_requirements=[
        "RA diagnosis (ACR/EULAR criteria documentation)",
        "Disease activity score (DAS28, CDAI, or SDAI)",
        "Prior DMARD history",
        "TB screening results",
        "Hepatitis B/C serology",
    ],
    warnings=["Screen for latent TB before initiation"],
    contraindications=["Active serious infection", "Untreated latent TB"],
)


# Export all sample guidelines
SAMPLE_GUIDELINES = [
    NSCLC_IMMUNOTHERAPY_GUIDELINE,
    LUMBAR_MRI_GUIDELINE,
    CARDIAC_IMAGING_GUIDELINE,
    RHEUMATOLOGY_BIOLOGIC_GUIDELINE,
]
