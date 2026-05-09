"""
Evidence Aggregation Agent.

Responsible for gathering and synthesizing clinical evidence
from multiple data sources to support authorization decisions.
"""

from datetime import datetime

from pydantic import BaseModel, Field

from pacca.agents.base import BaseAgent
from pacca.agents.prompts import EVIDENCE_AGENT_SYSTEM, build_evidence_prompt
from pacca.agents.types import AgentContext
from pacca.config import get_logger
from pacca.models import (
    AgentType,
    AuthorizationRequest,
    ClinicalEvidence,
    ClinicalNarrative,
    EvidenceQuality,
    EvidenceSource,
)

logger = get_logger(__name__)


class EvidenceOutput(BaseModel):
    """Structured output from Evidence Aggregation Agent."""

    patient_summary: str = Field(..., description="Brief patient summary")
    clinical_history: str = Field(..., description="Relevant clinical history narrative")
    current_condition: str = Field(..., description="Current condition description")
    treatment_rationale: str = Field(..., description="Rationale for requested treatment")
    prior_treatments_summary: str | None = Field(None, description="Summary of prior treatments")
    supporting_evidence: str = Field(..., description="Key supporting evidence points")
    missing_elements: list[str] = Field(default_factory=list, description="Missing critical info")
    evidence_quality: str = Field(..., description="Evidence quality assessment")
    quality_notes: str | None = Field(None, description="Notes on evidence quality")


class EvidenceAggregationAgent(BaseAgent[EvidenceOutput]):
    """
    Agent responsible for gathering and synthesizing clinical evidence.

    This agent:
    1. Retrieves clinical data from available sources (EHR, labs, imaging, etc.)
    2. Synthesizes the data into a coherent clinical narrative
    3. Identifies gaps in the available evidence
    4. Assesses overall evidence quality

    In the MVP, this agent works with mock/demo data. In production,
    it would integrate with real EHR systems via FHIR APIs.
    """

    @property
    def agent_type(self) -> AgentType:
        return AgentType.EVIDENCE_AGGREGATION

    @property
    def output_model(self) -> type[EvidenceOutput]:
        return EvidenceOutput

    @property
    def system_prompt(self) -> str:
        return EVIDENCE_AGENT_SYSTEM

    async def execute(
        self,
        request: AuthorizationRequest,
        context: AgentContext,
    ) -> EvidenceOutput:
        """
        Execute evidence aggregation for the authorization request.

        Args:
            request: The authorization request
            context: Execution context

        Returns:
            EvidenceOutput with synthesized clinical evidence
        """
        logger.info(
            "evidence_aggregation_started",
            request_id=request.request_id,
            patient_id=request.patient.patient_id,
        )

        # In production, this would query real data sources
        # For MVP, we work with the data provided in the request
        available_data = await self._gather_available_data(request)

        # Build the prompt
        prompt = build_evidence_prompt(
            request_id=request.request_id,
            patient_id=request.patient.patient_id,
            patient_age=request.patient.age,
            patient_gender=request.patient.gender,
            diagnosis_code=request.primary_diagnosis.code,
            diagnosis_description=request.primary_diagnosis.description,
            treatment_code=request.requested_treatment.code,
            treatment_description=request.requested_treatment.description,
            treatment_category=request.requested_treatment.category.value,
            estimated_cost=request.requested_treatment.estimated_cost or 0.0,
            clinical_notes=request.clinical_notes,
            available_data=available_data,
        )

        # Call LLM
        response = await self._call_llm(
            messages=[{"role": "user", "content": prompt}],
            temperature=0.0,  # We want consistent, factual output
        )

        # Parse structured output
        output = await self._parse_structured_output(response)

        logger.info(
            "evidence_aggregation_completed",
            request_id=request.request_id,
            evidence_quality=output.evidence_quality,
            missing_count=len(output.missing_elements),
        )

        return output

    async def _gather_available_data(self, request: AuthorizationRequest) -> str:
        """
        Gather available clinical data for the request.

        In production, this would make API calls to:
        - EHR systems (FHIR)
        - Lab systems
        - Imaging archives
        - Pharmacy systems
        - Claims data

        For MVP, we format the data already available in the request.
        """
        data_sections = []

        # Format existing evidence if available
        if request.evidence:
            evidence = request.evidence

            if evidence.medication_history:
                meds = "\n".join(
                    f"  - {m.medication_name}: {m.start_date} to {m.end_date or 'present'}"
                    for m in evidence.medication_history
                )
                data_sections.append(f"**Medication History:**\n{meds}")

            if evidence.lab_results:
                labs = "\n".join(
                    f"  - {lab.test_name}: {lab.result_value} {lab.unit or ''} "
                    f"({'ABNORMAL' if lab.is_abnormal else 'normal'}) - {lab.result_date.date()}"
                    for lab in evidence.lab_results
                )
                data_sections.append(f"**Recent Lab Results:**\n{labs}")

            if evidence.imaging_studies:
                imaging = "\n".join(
                    f"  - {i.study_type} of {i.body_site} ({i.study_date.date()}): "
                    f"{i.findings_summary or 'No summary'}"
                    for i in evidence.imaging_studies
                )
                data_sections.append(f"**Imaging Studies:**\n{imaging}")

            if evidence.prior_treatments:
                treatments = "\n".join(
                    f"  - {t.treatment_name}: {t.outcome} ({t.start_date} to {t.end_date})"
                    for t in evidence.prior_treatments
                )
                data_sections.append(f"**Prior Treatments:**\n{treatments}")

            if evidence.comorbidities:
                comorbidities = ", ".join(
                    f"{c.code} ({c.description})" for c in evidence.comorbidities
                )
                data_sections.append(f"**Comorbidities:** {comorbidities}")

            if evidence.allergies:
                data_sections.append(f"**Allergies:** {', '.join(evidence.allergies)}")

            if evidence.contraindications:
                data_sections.append(
                    f"**Contraindications:** {', '.join(evidence.contraindications)}"
                )

        # Add secondary diagnoses
        if request.secondary_diagnoses:
            secondary = ", ".join(
                f"{d.code} ({d.description})" for d in request.secondary_diagnoses
            )
            data_sections.append(f"**Secondary Diagnoses:** {secondary}")

        if not data_sections:
            return "Limited clinical data available. Primary information from provider notes only."

        return "\n\n".join(data_sections)

    async def calculate_confidence(
        self,
        output: EvidenceOutput,
        context: AgentContext,
    ) -> float:
        """Calculate confidence based on evidence quality and completeness."""
        # Base confidence on evidence quality
        quality_scores = {
            "HIGH": 0.95,
            "MODERATE": 0.80,
            "LOW": 0.60,
            "INSUFFICIENT": 0.40,
        }

        base_confidence = quality_scores.get(output.evidence_quality.upper(), 0.70)

        # Reduce confidence for missing elements
        missing_penalty = min(len(output.missing_elements) * 0.05, 0.25)

        return max(0.3, base_confidence - missing_penalty)

    async def get_next_agent(
        self,
        output: EvidenceOutput,
        context: AgentContext,
    ) -> AgentType | None:
        """Evidence agent is followed by Classification agent."""
        return AgentType.CLINICAL_CLASSIFICATION

    def to_clinical_evidence(self, output: EvidenceOutput) -> ClinicalEvidence:
        """Convert agent output to ClinicalEvidence model."""
        quality_map = {
            "HIGH": EvidenceQuality.HIGH,
            "MODERATE": EvidenceQuality.MODERATE,
            "LOW": EvidenceQuality.LOW,
            "INSUFFICIENT": EvidenceQuality.INSUFFICIENT,
        }

        return ClinicalEvidence(
            sources=[EvidenceSource.PROVIDER_NOTES],  # MVP: minimal sources
            gathered_at=datetime.utcnow(),
            overall_quality=quality_map.get(
                output.evidence_quality.upper(), EvidenceQuality.MODERATE
            ),
            missing_elements=output.missing_elements,
            quality_notes=output.quality_notes,
        )

    def to_clinical_narrative(self, output: EvidenceOutput) -> ClinicalNarrative:
        """Convert agent output to ClinicalNarrative model."""
        return ClinicalNarrative(
            patient_summary=output.patient_summary,
            clinical_history=output.clinical_history,
            current_condition=output.current_condition,
            treatment_rationale=output.treatment_rationale,
            prior_treatments_summary=output.prior_treatments_summary,
            supporting_evidence=output.supporting_evidence,
            generated_at=datetime.utcnow(),
        )
