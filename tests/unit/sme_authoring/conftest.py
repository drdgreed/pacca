"""
Shared fixtures for SME authoring tests.

Single source of truth for:
- valid_case_draft: a known-good CaseDraftResponse for use as a baseline
  in validator tests (each test mutates one field to trigger a failure).
- minimal_phi_case / minimal_guideline_case / etc.: focused fixtures
  per scenario.
"""

from __future__ import annotations

import pytest

from pacca.agents.sme_authoring.models import CaseDraftResponse


@pytest.fixture
def valid_case_draft() -> CaseDraftResponse:
    """
    A CaseDraftResponse that passes ALL six validators.

    Used as the baseline for failure-case tests: each test creates a
    mutated copy of this case with one field broken, then asserts the
    relevant validator fires.
    """
    return CaseDraftResponse(
        case_id="GC-101",
        title="Test case — meets all six validator criteria for baseline use",
        diagnosis_code="C34.1",
        diagnosis_description="Malignant neoplasm of upper lobe, bronchus or lung",
        procedure_code="J9271",
        procedure_description="Pembrolizumab (Keytruda) injection",
        clinical_notes=(
            "58-year-old male with stage IV non-small cell lung cancer. "
            "PD-L1 expression 62%. No EGFR or ALK alterations. ECOG 1. "
            "Oncology recommending first-line pembrolizumab monotherapy "
            "per NCCN Category 1 indication for metastatic disease."
        ),
        guidelines_context=(
            "NCCN NSCLC Guidelines: pembrolizumab monotherapy is a Category 1 "
            "first-line option for metastatic NSCLC with PD-L1 ≥ 50% and "
            "without targetable driver mutations (EGFR/ALK). CMS NCD coverage "
            "follows NCCN compendia for oncology indications."
        ),
        expected_outcome="AUTO_APPROVED",
        expected_branch="BRANCH_1_AUTO_APPROVE",
        reasoning_must_include=["NCCN Category 1", "PD-L1", "first-line"],
        reasoning_must_not_include=[],
        prior_denial_codes=[],
        clinical_rationale=(
            "Metastatic NSCLC with high PD-L1, no driver mutations, ECOG 1. "
            "Pembrolizumab monotherapy is clearly indicated per NCCN. Clean "
            "auto-approval."
        ),
        judge_scoring_criteria=(
            "Score highly if rationale cites PD-L1 percentage, the NCCN "
            "Category 1 designation, and the absence of EGFR/ALK alterations. "
            "Penalize for demanding combination chemo + IO when PD-L1 is "
            "high enough for monotherapy."
        ),
    )
