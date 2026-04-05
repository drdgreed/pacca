#!/usr/bin/env python3
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

    print(f"\nRunning {len(cases)} demo cases...")
    print("=" * 60)

    for i, raw in enumerate(cases, 1):
        case_id = raw["case_id"]
        title = raw["title"][:55]
        expected = raw["expected_outcome"]

        if dry_run:
            print(f"  [{i:02d}] {case_id}: {title}")
            print(f"         Expected: {expected} | Branch: {raw['expected_branch']}")
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

    print("\n" + "=" * 60)
    print(f"Results: {passed}/{len(results)} cases matched expected outcome")
    print(f"Accuracy: {passed/len(results):.1%}")

    if failed:
        print(f"\nMismatches ({len(failed)}):")
        for r in failed:
            print(f"  {r['case_id']}: expected {r['expected']}, got {r['actual']}")

    # Save results
    results_path = Path(__file__).parent / f"results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(results_path, "w") as f:
        json.dump({
            "run_at": datetime.now().isoformat(),
            "cases_run": len(results),
            "passed": passed,
            "accuracy": passed/len(results),
            "results": results,
        }, f, indent=2)
    print(f"\nFull results saved to {results_path}")

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
