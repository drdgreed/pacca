"""
Capture a per-case baseline scoreboard from a live clinical evaluation run.

Run this ONCE at the commit you want to baseline (e.g. harness-iter-1 HEAD),
with ANTHROPIC_API_KEY set. It runs all golden cases through the real PACCA
pipeline + judge, then writes {case_id: score} to a baseline file that the
per-case regression gate (regression_gate.py) compares future runs against:

    ANTHROPIC_API_KEY=... python -m tests.clinical.capture_baseline \
        --tag harness-iter-1 \
        --out tests/clinical/baselines/iter-1-baseline.json

WHY A SCRIPT, NOT A FIXTURE
---------------------------
Capturing a baseline is a deliberate, occasional act tied to a known-good
commit — not something that should happen implicitly on every test run. Keeping
it an explicit command prevents accidentally "baselining" a regression (which
would silence the very gate it feeds).

The pipeline loop below mirrors `test_full_pipeline_meets_accuracy_threshold`
in test_clinical_accuracy.py exactly, so the captured scores match what the CI
gate sees. The heavy imports (agents, Anthropic SDK) are deferred into
run_golden_dataset() so this module stays importable — and the save path stays
unit-testable — without an API key.
"""

from __future__ import annotations

import argparse
import asyncio
from pathlib import Path

from tests.clinical.regression_gate import save_baseline, scores_from_verdicts


async def run_golden_dataset() -> list:
    """
    Run every golden case through the real pipeline + judge; return verdicts.

    Faithful to the live CI test. Heavy imports are local to this function on
    purpose (see module docstring).
    """
    from pacca.agents.clinical_risk_detector import ClinicalRiskDetector
    from pacca.agents.decision import DecisionAgent, DecisionContext
    from pacca.models.clinical import ClinicalCase, EvidenceItem
    from pacca.models.enums import AuthorizationStatus, EvidenceSourceType

    from tests.clinical.evaluator import ClinicalEvaluator
    from tests.clinical.golden_cases import GOLDEN_CASES

    detector = ClinicalRiskDetector()
    agent = DecisionAgent()
    evaluator = ClinicalEvaluator()
    verdicts: list = []

    for golden in GOLDEN_CASES:
        clinical_case = ClinicalCase(
            patient_id=f"P-EVAL-{golden.case_id}",
            primary_diagnosis_code=golden.diagnosis_code,
            procedure_code=golden.procedure_code,
            evidence=[
                EvidenceItem(
                    id="e1",
                    source_type=EvidenceSourceType.CLINICAL_NOTE,
                    description=golden.clinical_notes[:200],
                    original_text=golden.clinical_notes,
                    confidence=0.9,
                )
            ],
        )

        flags = detector.evaluate(
            case=clinical_case,
            guidelines_context=golden.guidelines_context,
            prior_denial_codes=golden.prior_denial_codes,
        )

        if flags.should_pre_escalate:
            status = AuthorizationStatus.IN_REVIEW.value
            rationale = (
                f"Pre-flight escalation triggered. "
                f"Reasons: {[r.value for r in flags.reasons]}. "
                f"Details: {flags.details}"
            )
            confidence = 0.0
        else:
            try:
                ctx = DecisionContext(
                    case=clinical_case,
                    relevant_guidelines=golden.guidelines_context,
                )
                decision = await agent.run(ctx)
                status = decision.status.value
                rationale = decision.rationale
                confidence = decision.confidence_score
            except Exception as exc:  # noqa: BLE001 — capture, don't crash the run
                status = "ERROR"
                rationale = f"Agent failed: {exc!s}"
                confidence = 0.0

        verdict = await evaluator.evaluate_case(
            case=golden,
            system_decision_status=status,
            system_rationale=rationale,
            system_confidence=confidence,
        )
        verdicts.append(verdict)
        print(f"  {'PASS' if verdict.passed else 'FAIL'} {golden.case_id}: score={verdict.score}")

    return verdicts


def write_baseline_from_verdicts(verdicts, out_path: str | Path, iteration_tag: str) -> Path:
    """
    Pure, testable tail of the flow: turn verdicts into a saved scoreboard.

    Separated from run_golden_dataset() so it can be unit-tested with synthetic
    verdicts and no API key.
    """
    return save_baseline(
        scores_from_verdicts(verdicts), out_path, iteration_tag=iteration_tag
    )


async def _amain(out_path: str, tag: str) -> None:
    verdicts = await run_golden_dataset()
    path = write_baseline_from_verdicts(verdicts, out_path, tag)
    print(f"\nWrote baseline ({len(verdicts)} cases) -> {path}")


def main() -> None:
    ap = argparse.ArgumentParser(description="Capture a per-case baseline scoreboard.")
    ap.add_argument("--tag", required=True, help="harness iteration tag, e.g. harness-iter-1")
    ap.add_argument("--out", required=True, help="output path for the baseline JSON")
    args = ap.parse_args()
    asyncio.run(_amain(args.out, args.tag))


if __name__ == "__main__":
    main()
