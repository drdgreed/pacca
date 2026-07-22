"""Evidence-grounding detector (P-5 / chg-10).

Deterministic post-agent check: every evidence id the decision claims to have
relied on (``AuthorizationDecision.cited_evidence_ids``) must resolve to an
``EvidenceItem`` actually present in the submission. An id that does not resolve
means the decision may be citing fabricated or misattributed evidence, so the
orchestrator forces the run to human review — the production-path equivalent of
the GC-018/019 anti-hallucination eval gate.

Grounding is against **submission** evidence ids only. RAG chunks carry no
agent-visible ids today (the retriever hands the agent concatenated text, not
id'd chunks), so a citation cannot name a retrieved chunk and this detector does
not attempt to match them — threading RAG chunk ids is a separate future change.
Match is by identifier, never text similarity: deterministic, no second model.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pacca.models.authorization import AuthorizationDecision
    from pacca.models.clinical import ClinicalCase


def unresolved_cited_evidence(decision: AuthorizationDecision, case: ClinicalCase) -> list[str]:
    """Return the cited evidence ids that do NOT resolve to a submission EvidenceItem.

    Empty list ⇒ fully grounded. Order-preserving and de-duplicated, so the
    audit event lists each offending id once.
    """
    available = {item.id for item in case.evidence}
    seen: set[str] = set()
    unresolved: list[str] = []
    for cited_id in decision.cited_evidence_ids:
        if cited_id not in available and cited_id not in seen:
            unresolved.append(cited_id)
        seen.add(cited_id)
    return unresolved
