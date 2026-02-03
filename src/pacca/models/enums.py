"""
Domain enumerations for the PACCA system.

These enums define the bounded set of values for various domain concepts
in the prior authorization workflow.
"""

from enum import Enum, auto


class AuthorizationStatus(str, Enum):
    """Status of an authorization request through its lifecycle."""

    # Initial states
    SUBMITTED = "submitted"
    VALIDATING = "validating"

    # Processing states
    EVIDENCE_GATHERING = "evidence_gathering"
    CLASSIFYING = "classifying"
    EVALUATING = "evaluating"

    # Review states
    PENDING_REVIEW = "pending_review"
    IN_REVIEW = "in_review"
    ESCALATED = "escalated"

    # Terminal states
    APPROVED = "approved"
    DENIED = "denied"
    APPROVED_WITH_CONDITIONS = "approved_with_conditions"
    WITHDRAWN = "withdrawn"
    EXPIRED = "expired"

    # Error states
    FAILED = "failed"
    INCOMPLETE = "incomplete"

    def is_terminal(self) -> bool:
        """Check if this status represents a terminal state."""
        return self in {
            AuthorizationStatus.APPROVED,
            AuthorizationStatus.DENIED,
            AuthorizationStatus.APPROVED_WITH_CONDITIONS,
            AuthorizationStatus.WITHDRAWN,
            AuthorizationStatus.EXPIRED,
            AuthorizationStatus.FAILED,
        }

    def is_processing(self) -> bool:
        """Check if this status represents an active processing state."""
        return self in {
            AuthorizationStatus.VALIDATING,
            AuthorizationStatus.EVIDENCE_GATHERING,
            AuthorizationStatus.CLASSIFYING,
            AuthorizationStatus.EVALUATING,
        }


class ComplexityLevel(int, Enum):
    """
    Complexity classification for authorization requests.

    Lower values indicate simpler cases that may be auto-approved.
    Higher values require more review and potentially specialist escalation.
    """

    ROUTINE = 1  # Standard, well-documented cases
    LOW = 2  # Minor variations from routine
    MODERATE = 3  # Requires clinical review
    HIGH = 4  # Complex cases, multiple factors
    CRITICAL = 5  # Requires specialist/medical director

    @property
    def requires_human_review(self) -> bool:
        """Check if this complexity level requires human review."""
        return self.value >= ComplexityLevel.MODERATE.value

    @property
    def requires_specialist(self) -> bool:
        """Check if this complexity level requires specialist escalation."""
        return self.value >= ComplexityLevel.CRITICAL.value


class UrgencyLevel(str, Enum):
    """Urgency classification for time-sensitive authorizations."""

    ROUTINE = "routine"  # Standard processing (24-48 hours)
    EXPEDITED = "expedited"  # Faster processing (4-24 hours)
    URGENT = "urgent"  # Same-day processing required
    EMERGENT = "emergent"  # Immediate processing (life-threatening)

    @property
    def max_hours(self) -> int:
        """Maximum hours allowed for processing at this urgency level."""
        mapping = {
            UrgencyLevel.ROUTINE: 48,
            UrgencyLevel.EXPEDITED: 24,
            UrgencyLevel.URGENT: 8,
            UrgencyLevel.EMERGENT: 1,
        }
        return mapping[self]


class ClinicalSpecialty(str, Enum):
    """Medical specialties for routing and specialist consultation."""

    GENERAL = "general"
    ONCOLOGY = "oncology"
    CARDIOLOGY = "cardiology"
    ORTHOPEDICS = "orthopedics"
    NEUROLOGY = "neurology"
    PULMONOLOGY = "pulmonology"
    GASTROENTEROLOGY = "gastroenterology"
    RHEUMATOLOGY = "rheumatology"
    ENDOCRINOLOGY = "endocrinology"
    NEPHROLOGY = "nephrology"
    HEMATOLOGY = "hematology"
    INFECTIOUS_DISEASE = "infectious_disease"
    PSYCHIATRY = "psychiatry"
    PEDIATRICS = "pediatrics"
    OBSTETRICS = "obstetrics"
    RADIOLOGY = "radiology"
    SURGERY = "surgery"
    PAIN_MANAGEMENT = "pain_management"
    PHARMACY = "pharmacy"


class DecisionOutcome(str, Enum):
    """Possible outcomes from the decision support agent."""

    APPROVE = "approve"
    DENY = "deny"
    APPROVE_WITH_CONDITIONS = "approve_with_conditions"
    REQUEST_MORE_INFO = "request_more_info"
    ESCALATE = "escalate"
    UNABLE_TO_DETERMINE = "unable_to_determine"


class EvidenceSource(str, Enum):
    """Sources of clinical evidence."""

    EHR = "ehr"  # Electronic Health Record
    LAB = "lab"  # Laboratory results
    IMAGING = "imaging"  # Radiology/imaging
    PHARMACY = "pharmacy"  # Medication history
    CLAIMS = "claims"  # Historical claims data
    PROVIDER_NOTES = "provider_notes"  # Clinical notes
    EXTERNAL = "external"  # External records
    PATIENT_REPORTED = "patient_reported"  # Patient-provided info
    GUIDELINE = "guideline"  # Clinical guidelines


class EvidenceQuality(str, Enum):
    """Quality assessment of clinical evidence."""

    HIGH = "high"  # Recent, complete, verified
    MODERATE = "moderate"  # Some gaps or older data
    LOW = "low"  # Significant gaps or unverified
    INSUFFICIENT = "insufficient"  # Not enough for decision


class AgentType(str, Enum):
    """Types of agents in the PACCA system."""

    EVIDENCE_AGGREGATION = "evidence_aggregation"
    CLINICAL_CLASSIFICATION = "clinical_classification"
    DECISION_SUPPORT = "decision_support"
    ORCHESTRATION = "orchestration"
    COMMUNICATION = "communication"


class AgentAutonomyLevel(str, Enum):
    """
    Autonomy levels for agent decision-making.

    Maps to the staged autonomy model from the PRD.
    """

    SHADOW = "shadow"  # Generates recommendations, no action
    SUPERVISED = "supervised"  # Recommends, human decides
    SEMI_AUTONOMOUS = "semi_autonomous"  # Acts within boundaries
    AUTONOMOUS = "autonomous"  # Full decision authority


class ReviewerRole(str, Enum):
    """Roles of human reviewers in the authorization process."""

    CLINICAL_REVIEWER = "clinical_reviewer"
    SENIOR_REVIEWER = "senior_reviewer"
    MEDICAL_DIRECTOR = "medical_director"
    SPECIALIST = "specialist"
    PHARMACIST = "pharmacist"


class EscalationReason(str, Enum):
    """Reasons for escalating a case to human review."""

    LOW_CONFIDENCE = "low_confidence"
    HIGH_COMPLEXITY = "high_complexity"
    HIGH_COST = "high_cost"
    RARE_CONDITION = "rare_condition"
    SAFETY_CONCERN = "safety_concern"
    MISSING_EVIDENCE = "missing_evidence"
    GUIDELINE_CONFLICT = "guideline_conflict"
    POLICY_EXCEPTION = "policy_exception"
    PATIENT_REQUEST = "patient_request"
    PROVIDER_REQUEST = "provider_request"
    EXPERIMENTAL_TREATMENT = "experimental_treatment"
    PEDIATRIC_CASE = "pediatric_case"
    PREGNANCY_RELATED = "pregnancy_related"


class TreatmentCategory(str, Enum):
    """Categories of medical treatments for authorization."""

    MEDICATION = "medication"
    PROCEDURE = "procedure"
    IMAGING = "imaging"
    LAB_TEST = "lab_test"
    DURABLE_MEDICAL_EQUIPMENT = "dme"
    HOME_HEALTH = "home_health"
    REHABILITATION = "rehabilitation"
    MENTAL_HEALTH = "mental_health"
    SUBSTANCE_ABUSE = "substance_abuse"
    TRANSPLANT = "transplant"
    CLINICAL_TRIAL = "clinical_trial"
