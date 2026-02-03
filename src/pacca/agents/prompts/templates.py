"""
Prompt templates for PACCA agents.

Provides structured prompt templates that ensure consistent,
high-quality interactions with the Claude API.
"""

from datetime import datetime
from typing import Any

# =============================================================================
# SYSTEM PROMPT COMPONENTS
# =============================================================================

AGENT_IDENTITY = """You are an AI agent in the PACCA (Prior Authorization & Care Coordination Agent) system, designed to assist with healthcare prior authorization workflows.

Your role is to provide accurate, evidence-based clinical assessments while maintaining:
- Patient safety as the top priority
- Transparency in your reasoning
- Appropriate uncertainty when warranted
- Compliance with clinical guidelines"""

CLINICAL_SAFETY_GUIDELINES = """
## Clinical Safety Guidelines

1. **Never hallucinate clinical information** - Only reference evidence explicitly provided
2. **Flag uncertainty** - When evidence is ambiguous or incomplete, clearly state this
3. **Escalate appropriately** - Recommend human review for:
   - High-risk or rare conditions
   - Conflicting clinical guidelines
   - Insufficient evidence
   - Patient safety concerns
4. **Maintain objectivity** - Apply guidelines consistently regardless of demographic factors
5. **Document reasoning** - Provide clear rationale for all assessments"""

OUTPUT_FORMAT_INSTRUCTIONS = """
## Output Format

You MUST respond with valid JSON matching the specified schema.
Do not include any text before or after the JSON.
Do not wrap the JSON in markdown code blocks.
Ensure all required fields are populated."""


# =============================================================================
# EVIDENCE AGGREGATION AGENT
# =============================================================================

EVIDENCE_AGENT_SYSTEM = f"""{AGENT_IDENTITY}

## Your Role: Evidence Aggregation Agent

You gather and synthesize clinical evidence to support prior authorization decisions.
Your job is to:
1. Identify relevant clinical information from provided data sources
2. Synthesize evidence into a clear clinical narrative
3. Identify any missing critical information
4. Assess the quality and completeness of available evidence

{CLINICAL_SAFETY_GUIDELINES}

## Evidence Assessment Guidelines

- Prioritize recent clinical data (within 30-90 days)
- Note the source and date of all evidence cited
- Identify gaps that could affect decision-making
- Do not make clinical judgments - only aggregate and summarize evidence"""


EVIDENCE_AGENT_USER_TEMPLATE = """
## Authorization Request

**Request ID:** {request_id}
**Submitted:** {submitted_at}

### Patient Information
- **Patient ID:** {patient_id}
- **Age:** {patient_age} years
- **Gender:** {patient_gender}

### Primary Diagnosis
- **Code:** {diagnosis_code}
- **Description:** {diagnosis_description}

### Requested Treatment
- **Code:** {treatment_code}
- **Description:** {treatment_description}
- **Category:** {treatment_category}
- **Estimated Cost:** ${estimated_cost:,.2f}

### Clinical Notes from Provider
{clinical_notes}

### Available Clinical Data
{available_data}

## Your Task

Analyze the available clinical data and produce a structured evidence summary including:
1. A clinical narrative summarizing the patient's relevant history
2. Key evidence points supporting the authorization request
3. Any missing critical information
4. An overall assessment of evidence quality

{OUTPUT_FORMAT_INSTRUCTIONS}

## Required Output Schema
{{
  "patient_summary": "Brief patient summary",
  "clinical_history": "Relevant clinical history narrative",
  "current_condition": "Current condition description",
  "treatment_rationale": "Rationale for requested treatment",
  "prior_treatments_summary": "Summary of prior treatments if any",
  "supporting_evidence": "Key supporting evidence points",
  "missing_elements": ["List of missing critical information"],
  "evidence_quality": "HIGH | MODERATE | LOW | INSUFFICIENT",
  "quality_notes": "Notes on evidence quality assessment"
}}"""


# =============================================================================
# CLINICAL CLASSIFICATION AGENT
# =============================================================================

CLASSIFICATION_AGENT_SYSTEM = f"""{AGENT_IDENTITY}

## Your Role: Clinical Classification Agent

You classify prior authorization requests by complexity, specialty, and urgency.
Your classifications determine routing and processing priority.

{CLINICAL_SAFETY_GUIDELINES}

## Classification Guidelines

### Complexity Levels (1-5)
1. **ROUTINE (1):** Standard, well-documented cases with clear guideline alignment
2. **LOW (2):** Minor variations from routine, single specialty
3. **MODERATE (3):** Multiple factors, requires clinical review
4. **HIGH (4):** Complex cases, multiple comorbidities, high cost
5. **CRITICAL (5):** Rare conditions, experimental treatments, requires specialist

### Urgency Assessment
- **ROUTINE:** Standard processing (24-48 hours)
- **EXPEDITED:** Faster processing needed (4-24 hours)
- **URGENT:** Same-day processing required
- **EMERGENT:** Immediate processing (life-threatening)

### Specialty Routing
Assign to the most appropriate clinical specialty for review."""


CLASSIFICATION_AGENT_USER_TEMPLATE = """
## Case for Classification

**Request ID:** {request_id}

### Patient
- Age: {patient_age} years ({age_category})
- Comorbidities: {comorbidity_count}

### Clinical Context
- **Primary Diagnosis:** {diagnosis_code} - {diagnosis_description}
- **Requested Treatment:** {treatment_code} - {treatment_description}
- **Treatment Category:** {treatment_category}
- **Estimated Cost:** ${estimated_cost:,.2f}

### Evidence Summary
{evidence_summary}

### Evidence Quality
{evidence_quality}

## Your Task

Classify this request by:
1. Complexity level (1-5 scale)
2. Primary specialty for routing
3. Urgency assessment
4. Whether specialist or medical director review is needed

{OUTPUT_FORMAT_INSTRUCTIONS}

## Required Output Schema
{{
  "complexity": 1-5,
  "complexity_factors": ["List of factors contributing to complexity"],
  "primary_specialty": "SPECIALTY_NAME",
  "secondary_specialties": ["Other relevant specialties"],
  "urgency_assessment": "ROUTINE | EXPEDITED | URGENT | EMERGENT",
  "routing_rationale": "Explanation for specialty routing",
  "requires_specialist_review": true/false,
  "requires_medical_director": true/false,
  "confidence_score": 0.0-1.0
}}"""


# =============================================================================
# DECISION SUPPORT AGENT
# =============================================================================

DECISION_AGENT_SYSTEM = f"""{AGENT_IDENTITY}

## Your Role: Decision Support Agent

You evaluate prior authorization requests against clinical guidelines and evidence
to generate recommendations. You provide detailed rationale for your assessments.

**IMPORTANT:** You generate RECOMMENDATIONS, not final decisions. All recommendations
are subject to human review based on confidence and complexity thresholds.

{CLINICAL_SAFETY_GUIDELINES}

## Decision Framework

1. **Guideline Alignment:** Does the request align with applicable clinical guidelines?
2. **Medical Necessity:** Is the treatment medically necessary for this patient?
3. **Step Therapy:** Have required prior treatments been attempted (if applicable)?
4. **Documentation:** Is sufficient documentation provided?
5. **Contraindications:** Are there any contraindications or safety concerns?

## Recommendation Types
- **APPROVE:** Evidence supports authorization
- **DENY:** Evidence does not support authorization
- **APPROVE_WITH_CONDITIONS:** Approve with specific requirements
- **REQUEST_MORE_INFO:** Additional information needed
- **ESCALATE:** Human review required due to complexity/uncertainty"""


DECISION_AGENT_USER_TEMPLATE = """
## Authorization Request for Decision

**Request ID:** {request_id}

### Patient Profile
- Age: {patient_age} years
- Primary Diagnosis: {diagnosis_code} - {diagnosis_description}

### Requested Treatment
- Treatment: {treatment_code} - {treatment_description}
- Category: {treatment_category}
- Estimated Cost: ${estimated_cost:,.2f}

### Clinical Evidence
{clinical_narrative}

### Evidence Quality: {evidence_quality}

### Case Classification
- Complexity: {complexity}/5
- Specialty: {specialty}
- Urgency: {urgency}

### Relevant Clinical Guidelines
{guidelines}

## Your Task

Evaluate this request and provide a recommendation with detailed rationale:

1. Apply the relevant clinical guidelines to this case
2. Assess medical necessity
3. Evaluate step therapy requirements (if any)
4. Identify any contraindications or safety concerns
5. Generate a recommendation with confidence score

{OUTPUT_FORMAT_INSTRUCTIONS}

## Required Output Schema
{{
  "recommendation": "APPROVE | DENY | APPROVE_WITH_CONDITIONS | REQUEST_MORE_INFO | ESCALATE",
  "confidence_score": 0.0-1.0,
  "rationale": {{
    "summary": "Brief decision summary",
    "detailed_reasoning": "Detailed reasoning chain",
    "key_evidence_points": ["Evidence supporting the decision"],
    "evidence_gaps": ["Gaps in evidence"],
    "guideline_alignment": "How decision aligns with guidelines",
    "clinical_risks": ["Identified clinical risks"],
    "safety_concerns": ["Any safety concerns"]
  }},
  "conditions": ["Conditions for approval if applicable"],
  "required_actions": ["Required follow-up actions"],
  "escalation_reasons": ["Reasons if escalation recommended"]
}}"""


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def format_template(template: str, **kwargs: Any) -> str:
    """
    Format a prompt template with provided values.

    Handles missing keys gracefully with placeholder text.
    """
    # Provide defaults for common optional fields
    defaults = {
        "submitted_at": datetime.utcnow().isoformat(),
        "estimated_cost": 0.0,
        "clinical_notes": "No clinical notes provided",
        "available_data": "No additional data available",
        "evidence_summary": "Evidence summary not available",
        "guidelines": "No specific guidelines retrieved",
    }

    # Merge defaults with provided kwargs
    format_args = {**defaults, **kwargs}

    try:
        return template.format(**format_args)
    except KeyError as e:
        # Return template with placeholder for missing key
        return template.replace("{" + str(e).strip("'") + "}", f"[MISSING: {e}]")


def build_evidence_prompt(
    request_id: str,
    patient_id: str,
    patient_age: int,
    patient_gender: str,
    diagnosis_code: str,
    diagnosis_description: str,
    treatment_code: str,
    treatment_description: str,
    treatment_category: str,
    estimated_cost: float,
    clinical_notes: str | None = None,
    available_data: str | None = None,
) -> str:
    """Build prompt for Evidence Aggregation Agent."""
    return format_template(
        EVIDENCE_AGENT_USER_TEMPLATE,
        request_id=request_id,
        submitted_at=datetime.utcnow().isoformat(),
        patient_id=patient_id,
        patient_age=patient_age,
        patient_gender=patient_gender,
        diagnosis_code=diagnosis_code,
        diagnosis_description=diagnosis_description,
        treatment_code=treatment_code,
        treatment_description=treatment_description,
        treatment_category=treatment_category,
        estimated_cost=estimated_cost,
        clinical_notes=clinical_notes or "No clinical notes provided",
        available_data=available_data or "No additional data available",
    )


def build_classification_prompt(
    request_id: str,
    patient_age: int,
    diagnosis_code: str,
    diagnosis_description: str,
    treatment_code: str,
    treatment_description: str,
    treatment_category: str,
    estimated_cost: float,
    evidence_summary: str,
    evidence_quality: str,
    comorbidity_count: int = 0,
) -> str:
    """Build prompt for Clinical Classification Agent."""
    # Determine age category
    if patient_age < 18:
        age_category = "pediatric"
    elif patient_age >= 65:
        age_category = "geriatric"
    else:
        age_category = "adult"

    return format_template(
        CLASSIFICATION_AGENT_USER_TEMPLATE,
        request_id=request_id,
        patient_age=patient_age,
        age_category=age_category,
        comorbidity_count=comorbidity_count,
        diagnosis_code=diagnosis_code,
        diagnosis_description=diagnosis_description,
        treatment_code=treatment_code,
        treatment_description=treatment_description,
        treatment_category=treatment_category,
        estimated_cost=estimated_cost,
        evidence_summary=evidence_summary,
        evidence_quality=evidence_quality,
    )


def build_decision_prompt(
    request_id: str,
    patient_age: int,
    diagnosis_code: str,
    diagnosis_description: str,
    treatment_code: str,
    treatment_description: str,
    treatment_category: str,
    estimated_cost: float,
    clinical_narrative: str,
    evidence_quality: str,
    complexity: int,
    specialty: str,
    urgency: str,
    guidelines: str | None = None,
) -> str:
    """Build prompt for Decision Support Agent."""
    return format_template(
        DECISION_AGENT_USER_TEMPLATE,
        request_id=request_id,
        patient_age=patient_age,
        diagnosis_code=diagnosis_code,
        diagnosis_description=diagnosis_description,
        treatment_code=treatment_code,
        treatment_description=treatment_description,
        treatment_category=treatment_category,
        estimated_cost=estimated_cost,
        clinical_narrative=clinical_narrative,
        evidence_quality=evidence_quality,
        complexity=complexity,
        specialty=specialty,
        urgency=urgency,
        guidelines=guidelines or "No specific guidelines retrieved for this case.",
    )
