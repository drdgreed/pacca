"""
Clinical Risk Detector — pre-flight escalation check for the Orchestrator.

This module implements the four new escalation branches specified in PRD SS5.4:
  - Experimental treatment detection
  - Rare condition (ICD-10 prevalence) detection
  - Conflicting guidelines detection
  - Prior denial on same service detection

Architecture teaching note — why a separate class instead of putting
this logic directly in the Orchestrator?

  The Single Responsibility Principle: each class should have one reason
  to change. The Orchestrator's reason to change is "the workflow changed."
  The ClinicalRiskDetector's reason to change is "our clinical risk criteria
  changed." By separating them:

  1. You can test every detection rule in complete isolation — no mocks
     of agents or databases needed.
  2. You can update clinical criteria (e.g. add new experimental drugs to
     the list) without touching the orchestration workflow.
  3. A compliance auditor can read this file alone to understand all the
     conditions that trigger human review.

Teaching note — pure functions vs. database queries:
  Several of these checks (experimental treatment, rare conditions) use
  curated lists defined right here in the module. You might wonder: why
  not store these in the database and query them dynamically?

  Answer: configuration that affects clinical safety decisions should be
  version-controlled alongside the code that uses it. A database row can
  be changed by anyone with DB access; a Python file requires a code
  review and a deployment. For clinical escalation criteria, that friction
  is a feature, not a bug. The lists below change slowly (quarterly at
  most) and every change should be reviewed.
"""

from dataclasses import dataclass, field

from ..models.clinical import ClinicalCase
from ..models.enums import EscalationReason

# =============================================================================
# Curated clinical reference data
#
# Teaching note: These sets are the "policy" side of the system. The AI
# handles the "reasoning" side. Some decisions should not be left to
# probabilistic reasoning — they require deterministic policy enforcement.
# These sets encode that policy.
# =============================================================================

# Procedure codes for treatments that are investigational, in active clinical
# trials, or not yet standard-of-care. Sources: CMS coverage determinations,
# FDA breakthrough therapy designations, NCCN Category 2B/3 listings.
#
# This is a representative sample for the portfolio prototype. A production
# system would maintain this list in a versioned configuration store and
# update it quarterly in sync with FDA and CMS coverage decisions.
EXPERIMENTAL_PROCEDURE_CODES: frozenset[str] = frozenset(
    {
        # CAR-T cell therapies (FDA-approved for limited indications; experimental for others)
        "Q2041",  # Axicabtagene ciloleucel (Yescarta) — experimental outside approved indications
        "Q2042",  # Tisagenlecleucel (Kymriah) — experimental outside approved indications
        "Q2055",  # Lisocabtagene maraleucel (Breyanzi)
        # Gene therapies
        "J3399",  # Gene therapy — unspecified investigational
        "C9399",  # Investigational device or treatment — unspecified
        # Investigational oncology biologics
        "J9999",  # Unclassified antineoplastic drug (often used for investigational agents)
        "J3490",  # Unclassified drugs (catch-all for unlisted agents)
        # Experimental neural stimulation
        "0278T",  # Transcranial magnetic stimulation — experimental for certain indications
        "0364T",  # Vagus nerve stimulation — experimental for new indications
        # Investigational imaging
        "A9699",  # Radiopharmaceutical — investigational
        # Fecal microbiota transplantation beyond approved indications
        "G0455",  # Fecal microbiota transplantation — experimental outside C. diff indication
    }
)

# Diagnosis keyword fragments that suggest experimental treatment context.
# Used as a secondary check when procedure code is not on the list above.
EXPERIMENTAL_DIAGNOSIS_KEYWORDS: frozenset[str] = frozenset(
    {
        "investigational",
        "experimental",
        "clinical trial",
        "compassionate use",
        "expanded access",
        "off-label",
        "off label",
        "unproven",
        "not fda approved",
        "phase i",
        "phase ii",
        "phase iii",
        "phase 1",
        "phase 2",
        "phase 3",
    }
)

# ICD-10 code prefixes associated with rare diseases (prevalence < 1:10,000).
# Source: NORD (National Organization for Rare Disorders), OMIM, Orphanet.
#
# ICD-10 prefixes are used rather than full codes because rare disease codes
# often have multiple specificity levels (e.g. E70.0, E70.1, E70.2...) that
# all represent the same rare condition family.
RARE_CONDITION_ICD10_PREFIXES: frozenset[str] = frozenset(
    {
        # Phenylketonuria and amino acid metabolism disorders
        "E70",
        # Gaucher disease, Fabry disease, other lysosomal storage disorders
        "E75",
        # Glycogen storage diseases (Pompe, McArdle, etc.)
        "E74",
        # Wilson disease, hemochromatosis
        "E83",
        # Huntington disease
        "G10",
        # Friedreich ataxia and spinocerebellar ataxias
        "G11",
        # Spinal muscular atrophy (SMA)
        "G12",
        # Amyotrophic lateral sclerosis (ALS) — rare but high-cost treatment
        "G12.21",
        # Myasthenia gravis — rare, complex treatment
        "G70",
        # Tuberous sclerosis
        "Q85",
        # Marfan syndrome
        "Q87.4",
        # Ehlers-Danlos syndrome
        "Q79.6",
        # Cystic fibrosis
        "J84.9",
        # Pulmonary arterial hypertension (rare forms)
        "I27.0",
        # Hereditary angioedema
        "D84.1",
        # Systemic mastocytosis
        "D47.0",
        # Aplastic anemia (severe forms)
        "D61",
        # Paroxysmal nocturnal hemoglobinuria
        "D59.5",
        # Primary immunodeficiencies
        "D80",
        "D81",
        "D82",
        "D83",
        "D84",
    }
)

# Guideline source identifiers that, when multiple are present, indicate
# a potential conflict. The detection logic checks whether the RAG context
# contains guidance from multiple sources that use different recommendation
# language (e.g. "recommended" vs "not recommended" for the same treatment).
GUIDELINE_CONFLICT_MARKERS: tuple[str, ...] = (
    "not recommended",
    "contraindicated",
    "avoid",
    "insufficient evidence",
    "conflicting evidence",
    "guideline discordant",
    "not supported",
    "evidence is limited",
)

GUIDELINE_APPROVAL_MARKERS: tuple[str, ...] = (
    "recommended",
    "indicated",
    "supported",
    "evidence-based",
    "standard of care",
    "category 1",
    "strong recommendation",
)


# =============================================================================
# Escalation flag dataclass
# =============================================================================


@dataclass
class EscalationFlags:
    """
    The result of running all pre-flight checks on a clinical case.

    Teaching note — why a dataclass instead of a dict?
      A dataclass gives you type safety and auto-completion. You can write
      flags.is_experimental and your editor knows that's a bool. With a
      dict you write flags["is_experimental"] and hope you spelled it right.

    Attributes:
        reasons:             List of EscalationReason values that fired
        should_pre_escalate: True if any check fired — shortcuts to human review
        details:             Human-readable explanation of each triggered check
    """

    reasons: list[EscalationReason] = field(default_factory=list)
    details: dict[str, str] = field(default_factory=dict)

    @property
    def should_pre_escalate(self) -> bool:
        """True if any pre-flight check triggered escalation."""
        return len(self.reasons) > 0

    def add(self, reason: EscalationReason, detail: str) -> None:
        """Record a triggered escalation reason with its explanation."""
        self.reasons.append(reason)
        self.details[reason.value] = detail


# =============================================================================
# The detector
# =============================================================================


class ClinicalRiskDetector:
    """
    Evaluates a clinical case for pre-flight escalation triggers.

    This class implements the 4 new PRD SS5.4 escalation branches:
      check_experimental_treatment()  → Branch 4
      check_rare_condition()          → Branch 5
      check_conflicting_guidelines()  → Branch 6
      check_prior_denial()            → Branch 7

    Each method is a pure function: same input always produces same output,
    no side effects, no database calls. This makes them trivially testable.

    Usage:
        detector = ClinicalRiskDetector()
        flags = detector.evaluate(case, guidelines_context, prior_denials)
        if flags.should_pre_escalate:
            # Route directly to human review with flags.reasons recorded
    """

    def evaluate(
        self,
        case: ClinicalCase,
        guidelines_context: str = "",
        prior_denial_codes: list[str] | None = None,
    ) -> EscalationFlags:
        """
        Run all pre-flight checks on a case and return the combined result.

        This is the single entry point for the Orchestrator. It runs all
        four checks and aggregates their results into one EscalationFlags
        object. Multiple checks can fire simultaneously — for example, a
        rare condition treated with an experimental drug triggers both
        RARE_CONDITION and EXPERIMENTAL_TREATMENT.

        Args:
            case:                The clinical case being evaluated
            guidelines_context:  The raw text returned by the RAG pipeline —
                                 used to detect guideline conflicts
            prior_denial_codes:  List of procedure codes that have been
                                 previously denied for this patient

        Returns:
            EscalationFlags with all triggered reasons and their explanations
        """
        flags = EscalationFlags()
        prior_denial_codes = prior_denial_codes or []

        # Run each check and collect any triggered flags
        self._check_experimental_treatment(case, flags)
        self._check_rare_condition(case, flags)
        self._check_conflicting_guidelines(case, guidelines_context, flags)
        self._check_prior_denial(case, prior_denial_codes, flags)

        return flags

    # ── Branch 4: Experimental treatment ─────────────────────────────────────

    def _check_experimental_treatment(
        self,
        case: ClinicalCase,
        flags: EscalationFlags,
    ) -> None:
        """
        Detect whether the requested procedure is experimental or investigational.

        Two detection strategies, applied in order:
          1. Exact match against EXPERIMENTAL_PROCEDURE_CODES — the most
             reliable signal; procedure codes are authoritative identifiers
          2. Keyword scan of evidence text — catches cases where the provider
             notes explicitly mention investigational or trial status

        Teaching note — defense in depth:
          Using two strategies means neither a missing code nor missing keywords
          alone defeats the check. A real UM system might add a third strategy:
          querying the FDA clinical trials registry API. That would be a
          production enhancement, and is the right pattern for Week 5.
        """
        procedure = case.procedure_code.upper().strip()

        # Strategy 1: exact procedure code match
        if procedure in EXPERIMENTAL_PROCEDURE_CODES:
            flags.add(
                EscalationReason.EXPERIMENTAL_TREATMENT,
                f"Procedure code {procedure} is on the experimental treatment list. "
                f"No autonomous AI decision appropriate — requires human review.",
            )
            return  # No need to scan keywords if code already matched

        # Strategy 2: keyword scan across all evidence text
        all_evidence_text = " ".join(
            item.description.lower() + " " + item.original_text.lower() for item in case.evidence
        )
        matched_keywords = [kw for kw in EXPERIMENTAL_DIAGNOSIS_KEYWORDS if kw in all_evidence_text]
        if matched_keywords:
            flags.add(
                EscalationReason.EXPERIMENTAL_TREATMENT,
                f"Evidence text contains experimental treatment indicators: "
                f"{', '.join(matched_keywords[:3])}. Requires human review.",
            )

    # ── Branch 5: Rare condition ──────────────────────────────────────────────

    def _check_rare_condition(
        self,
        case: ClinicalCase,
        flags: EscalationFlags,
    ) -> None:
        """
        Detect whether the primary diagnosis is a rare condition.

        Matching strategy: prefix matching on ICD-10 code.

        Teaching note — why prefix matching?
          ICD-10 codes are hierarchical. "E70" means "Disorders of aromatic
          amino-acid metabolism." "E70.0" is phenylketonuria specifically.
          "E70.1" is tyrosinemia. All E70.x codes represent rare metabolic
          disorders. Matching on the prefix catches all specificity levels
          in a single check, which is more maintainable than listing every
          possible E70.x code.

          The trade-off: a prefix check could catch a non-rare condition if
          a rare prefix is more specific than expected. In practice, the
          prefixes in RARE_CONDITION_ICD10_PREFIXES were chosen to correspond
          to disease families that are uniformly rare. Any false positive
          (a non-rare condition escalated to human review) is acceptable —
          it's a conservative error. A false negative (a rare condition not
          escalated) would be a patient safety issue.
        """
        diagnosis_code = case.primary_diagnosis_code.upper().strip()

        for prefix in RARE_CONDITION_ICD10_PREFIXES:
            if diagnosis_code.startswith(prefix):
                flags.add(
                    EscalationReason.RARE_CONDITION,
                    f"Diagnosis code {diagnosis_code} matches rare condition prefix "
                    f"'{prefix}'. Population prevalence < 1:10,000. Clinical guidelines "
                    f"may be sparse or contradictory — requires specialist review.",
                )
                return  # One match is sufficient

    # ── Branch 6: Conflicting guidelines ─────────────────────────────────────

    def _check_conflicting_guidelines(
        self,
        case: ClinicalCase,
        guidelines_context: str,
        flags: EscalationFlags,
    ) -> None:
        """
        Detect whether the retrieved guidelines contain conflicting recommendations.

        Strategy: check whether the guidelines context contains both approval
        language AND rejection/caution language for the same case. If both
        are present, the guidelines conflict and a human must weigh them.

        Teaching note — this is a heuristic, not a certainty:
          The keyword check is a signal, not a guarantee. "Not recommended
          for patients under 18" in a guideline about an adult patient is
          a false positive — the restriction doesn't apply. A production
          system would use a more sophisticated NLP approach (e.g. sentence-
          level sentiment analysis, or structured extraction of guideline
          recommendations). For this portfolio project, the heuristic
          approach demonstrates the pattern and the intent. The important
          engineering principle is that the Orchestrator is structured to
          receive this signal; upgrading the detection algorithm is a
          localized change to this one function.

          False positives (unnecessary human review) are acceptable.
          False negatives (missed conflicts reaching autonomous decisions) are not.
        """
        if not guidelines_context:
            return

        context_lower = guidelines_context.lower()

        has_approval = any(m in context_lower for m in GUIDELINE_APPROVAL_MARKERS)
        has_rejection = any(m in context_lower for m in GUIDELINE_CONFLICT_MARKERS)

        if has_approval and has_rejection:
            matched_rejections = [m for m in GUIDELINE_CONFLICT_MARKERS if m in context_lower]
            flags.add(
                EscalationReason.CONFLICTING_GUIDELINES,
                f"Retrieved guidelines contain both approval and rejection language. "
                f"Conflict indicators: {', '.join(matched_rejections[:2])}. "
                f"Human review required to weigh guidelines against patient context.",
            )

    # ── Branch 7: Prior denial on same service ────────────────────────────────

    def _check_prior_denial(
        self,
        case: ClinicalCase,
        prior_denial_codes: list[str],
        flags: EscalationFlags,
    ) -> None:
        """
        Detect whether this patient has a prior denial for the same procedure.

        Strategy: exact match of current procedure code against the list of
        procedure codes previously denied for this patient.

        Teaching note — where does prior_denial_codes come from?
          In this prototype, the Orchestrator passes an empty list by default.
          In a production system, the route handler would query the
          AuthorizationRepository for prior decisions matching this patient ID
          and procedure code with status=DENIED, then pass those codes here.

          That query is the right place to add this: in the route, before
          calling process_decision(), something like:
            prior_denials = await auth_repo.get_denied_procedure_codes(
                patient_id=request.patient_id
            )
          This is a straightforward extension to AuthorizationRepository
          and is designed as a Week 3 enhancement.

          The important point is that the Orchestrator and ClinicalRiskDetector
          are already structured to receive and act on this information — the
          interface is ready even if the data source is not yet wired.
        """
        procedure = case.procedure_code.upper().strip()
        normalized_denials = [code.upper().strip() for code in prior_denial_codes]

        if procedure in normalized_denials:
            flags.add(
                EscalationReason.PRIOR_DENIAL_SAME_SERVICE,
                f"Patient has a prior denial record for procedure {procedure}. "
                f"Human review required to determine if circumstances have changed "
                f"or whether this is a repeat claim.",
            )
