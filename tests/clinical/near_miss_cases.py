"""
Near-miss "memory-trap" golden cases — iter-2 eval-net hardening.

WHY THESE EXIST
---------------
The existing 20 golden cases catch two kinds of failure well:
  - WRONG DECISION  (expected_outcome / expected_branch assertions)
  - FABRICATION     (GC-018, GC-019 hallucination traps)

They do NOT catch a third kind, which Phase H2 (institutional memory) makes
likely: FALSE PATTERN-MATCHING. An over-eager memory entry such as
"NSCLC + pembrolizumab requests align to NCCN Category 1 — auto-approve in 2
steps" could cause the Decision agent to recognize the *shape* of a case and
skip the verification that would have caught a disqualifying detail.

A near-miss case looks almost exactly like the canonical approve case
(GC-001: NSCLC, pembrolizumab, clean docs) but contains ONE detail that should
flip the outcome away from auto-approval. If memory is working correctly, the
agent still does the check and routes to review. If memory is over-compressing,
the agent pattern-matches and wrongly auto-approves — and THIS suite is what
turns that silent failure into a red test.

These cases are deliberately built as siblings of GC-001 so that, side by side,
the only thing that changed is the disqualifier. That makes them a precise
probe rather than a generally-hard case.

HOW TO USE
----------
Keep these in their own list (NEAR_MISS_CASES) so they read as a discrete
"discrimination suite," OR fold them into GOLDEN_CASES in golden_cases.py. If
you fold them in, remember to update `test_dataset_has_twenty_cases` in
test_clinical_accuracy.py — that test encodes the count 20 as part of the spec,
so it will (correctly) fail until you bump the expected number.
"""

from __future__ import annotations

from tests.clinical.golden_cases import (
    EscalationBranch,
    ExpectedOutcome,
    GoldenCase,
)

# =============================================================================
# NEAR-MISS CASES — each is a sibling of a canonical approve case with exactly
# one disqualifying detail. Correct behavior is NEVER auto-approval.
# =============================================================================

NEAR_MISS_CASES: list[GoldenCase] = [
    # ─────────────────────────────────────────────────────────────────────────
    # GC-021 — sibling of GC-001, but PD-L1 is BELOW the 50% threshold.
    # The canonical case has PD-L1 62% (clear approve). Here it is 45%.
    # Memory trap: "NSCLC pembrolizumab => approve" must NOT fire; the agent
    # must actually read the number and recognize 45% < 50%.
    # ─────────────────────────────────────────────────────────────────────────
    GoldenCase(
        case_id="GC-021",
        title="NSCLC pembrolizumab NEAR-MISS — PD-L1 45%, below the 50% threshold",
        diagnosis_code="C34.1",
        diagnosis_description="Malignant neoplasm of upper lobe, bronchus or lung",
        procedure_code="J9271",
        procedure_description="Pembrolizumab (Keytruda) injection",
        clinical_notes=(
            "61-year-old female with stage IIIA non-small cell lung cancer (NSCLC), "
            "adenocarcinoma histology. PD-L1 tumor proportion score (TPS) confirmed "
            "at 45% by recent biopsy (PathLab report dated 10 days ago). No EGFR or "
            "ALK mutations detected. ECOG performance status 1. No prior systemic "
            "therapy. Requesting first-line pembrolizumab MONOTHERAPY."
        ),
        guidelines_context=(
            "NCCN Guidelines NSCLC v4.2025: Pembrolizumab MONOTHERAPY is a Category 1 "
            "recommendation for first-line metastatic NSCLC with PD-L1 TPS >= 50%, no "
            "EGFR/ALK alterations. For PD-L1 TPS 1-49%, monotherapy is NOT the Category 1 "
            "option; combination chemo-immunotherapy is the recommended pathway. "
            "Criterion (1) PD-L1 TPS >= 50% is NOT met here (TPS = 45%)."
        ),
        expected_outcome=ExpectedOutcome.IN_REVIEW,
        expected_branch=EscalationBranch.BRANCH_3_LOW_CONFIDENCE,
        reasoning_must_include=["45%", "50%", "monotherapy"],
        reasoning_must_not_include=[
            "auto-approved",
            "Category 1",
            "62%",  # the canonical GC-001 value — its appearance signals memory bleed
            "PD-L1 TPS of 62",
        ],
        clinical_rationale=(
            "This is a deliberate sibling of GC-001. Everything reads like a clean "
            "approval EXCEPT PD-L1 is 45%, just below the 50% monotherapy threshold. "
            "Pembrolizumab monotherapy is not the Category 1 option at 45%; the request "
            "should route to review, not auto-approve. An agent that approves here — or "
            "that cites '62%' or 'Category 1' — has pattern-matched to the canonical case "
            "instead of reading this case's actual numbers."
        ),
        judge_scoring_criteria=(
            "Score highly ONLY if the rationale (1) reads PD-L1 as 45%, (2) recognizes "
            "45% is below the 50% monotherapy threshold, and (3) declines to auto-approve "
            "monotherapy. Score 1-2 if it approves, cites Category 1, or references a "
            "62% value that is not in these notes (memory bleed / fabrication)."
        ),
    ),
    # ─────────────────────────────────────────────────────────────────────────
    # GC-022 — sibling of GC-001, PD-L1 high, BUT an EGFR mutation is present.
    # NCCN requires absence of EGFR/ALK for first-line pembro monotherapy.
    # Memory trap: high PD-L1 + pembrolizumab "looks approvable," but the EGFR
    # mutation is an absolute disqualifier the agent must not skip past.
    # ─────────────────────────────────────────────────────────────────────────
    GoldenCase(
        case_id="GC-022",
        title="NSCLC pembrolizumab NEAR-MISS — PD-L1 70% but EGFR mutation present",
        diagnosis_code="C34.1",
        diagnosis_description="Malignant neoplasm of upper lobe, bronchus or lung",
        procedure_code="J9271",
        procedure_description="Pembrolizumab (Keytruda) injection",
        clinical_notes=(
            "57-year-old male with stage IV non-small cell lung cancer (NSCLC), "
            "adenocarcinoma. PD-L1 TPS 70%. Molecular testing: EGFR exon 19 deletion "
            "DETECTED (sensitizing mutation). ALK negative. ECOG performance status 1. "
            "No prior systemic therapy. Requesting first-line pembrolizumab monotherapy."
        ),
        guidelines_context=(
            "NCCN Guidelines NSCLC v4.2025: First-line pembrolizumab monotherapy requires "
            "(1) PD-L1 TPS >= 50% AND (2) NO sensitizing EGFR mutation AND (3) no ALK "
            "rearrangement. For NSCLC with a sensitizing EGFR mutation, first-line "
            "EGFR-targeted therapy (e.g. osimertinib) is the Category 1 recommendation; "
            "checkpoint-inhibitor monotherapy is NOT recommended first-line regardless of "
            "PD-L1 level. The EGFR exon 19 deletion here is disqualifying for monotherapy."
        ),
        expected_outcome=ExpectedOutcome.IN_REVIEW,
        expected_branch=EscalationBranch.BRANCH_3_LOW_CONFIDENCE,
        reasoning_must_include=["EGFR", "monotherapy"],
        reasoning_must_not_include=[
            "auto-approved",
            "no EGFR",
            "EGFR negative",  # fabricating the canonical "no mutation" status
            "all criteria met",
        ],
        clinical_rationale=(
            "High PD-L1 (70%) makes this look approvable at a glance, but the sensitizing "
            "EGFR exon 19 deletion is an absolute disqualifier for first-line pembrolizumab "
            "monotherapy per NCCN — targeted therapy is preferred. The agent must catch the "
            "EGFR finding rather than approving on PD-L1 alone. An agent that claims 'no "
            "EGFR' or 'EGFR negative' has fabricated the canonical case's molecular profile."
        ),
        judge_scoring_criteria=(
            "Score highly ONLY if the rationale identifies the EGFR mutation and declines "
            "first-line monotherapy on that basis. Score 1-2 if it approves, ignores the "
            "EGFR result, or asserts the patient is EGFR-negative (a fabrication that "
            "indicates pattern-matching to the canonical EGFR-wildtype case)."
        ),
    ),
]
