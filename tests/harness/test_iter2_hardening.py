"""
iter-2 deliverable validation suite.

This is the meta-test for the eval-net hardening iteration. It verifies that
all THREE iter-2 deliverables were created AND that they actually work — not
just that the files exist:

  Deliverable 1 — Per-case regression gate + baseline scoreboard
                  (tests/clinical/regression_gate.py + baselines/iter-1-baseline.json)
  Deliverable 2 — Near-miss "memory-trap" golden cases
                  (tests/clinical/near_miss_cases.py)
  Deliverable 3 — Doc-drift guard + iter-0 erratum reconciliation
                  (tests/harness/doc_drift_guard.py + docs_reconciliation/ITER0_ERRATUM.md)

Run:  python -m pytest tests/harness/test_iter2_hardening.py -v
"""

from __future__ import annotations

from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]  # repo root (.../pacca)


# =============================================================================
# Deliverable 1 — Per-case regression gate
# =============================================================================
class TestDeliverable1RegressionGate:
    """The keystone: a gate that sees per-case degradation the 80% gate misses."""

    def test_module_exists_and_imports(self) -> None:
        from tests.clinical import regression_gate  # noqa: F401

    def test_baseline_scoreboard_file_exists_with_real_case_ids(self) -> None:
        from tests.clinical.golden_cases import GOLDEN_CASES
        from tests.clinical.regression_gate import load_baseline

        path = REPO_ROOT / "tests/clinical/baselines/iter-1-baseline.json"
        assert path.exists(), f"baseline scoreboard missing at {path}"

        baseline = load_baseline(path)
        golden_ids = {c.case_id for c in GOLDEN_CASES}
        assert set(baseline) == golden_ids, (
            "baseline scoreboard must cover exactly the golden case IDs"
        )

    def test_save_then_load_roundtrip(self, tmp_path: Path) -> None:
        from tests.clinical.regression_gate import load_baseline, save_baseline

        scores = {"GC-001": 5, "GC-002": 4}
        p = save_baseline(scores, tmp_path / "b.json", iteration_tag="harness-iter-1")
        assert load_baseline(p) == scores

    def test_CORE_catches_silent_degradation_the_aggregate_gate_misses(self) -> None:
        """
        THE PROOF that Gap 1 is closed.

        Construct a 20-case run where:
          - 19 cases are unchanged at their baseline,
          - GC-001 slides 5 -> 3 (still a "pass" under the absolute >=3 rule).

        The legacy aggregate gate (pass = score>=3, gate = >=80% pass) would be
        100% green here. The per-case gate must FAIL and name GC-001.
        """
        from tests.clinical.regression_gate import check_regression

        baseline = {f"GC-{i:03}": 5 for i in range(1, 21)}
        current = dict(baseline)
        current["GC-001"] = 3  # silent slide: correct decision, worse reasoning

        # Sanity: the absolute aggregate gate would NOT catch this.
        passes_absolute = sum(1 for s in current.values() if s >= 3) / len(current)
        assert passes_absolute == 1.0  # 100% — old gate sees nothing wrong

        report = check_regression(current, baseline)
        assert report.passed is False
        assert [r.case_id for r in report.regressions] == ["GC-001"]
        assert report.regressions[0].drop == 2

    def test_stable_run_passes(self) -> None:
        from tests.clinical.regression_gate import check_regression

        baseline = {"GC-001": 5, "GC-002": 4, "GC-003": 5}
        assert check_regression(dict(baseline), baseline).passed is True

    def test_missing_case_is_a_failure(self) -> None:
        from tests.clinical.regression_gate import check_regression

        baseline = {"GC-001": 5, "GC-002": 4}
        report = check_regression({"GC-001": 5}, baseline)
        assert report.passed is False
        assert report.missing == ["GC-002"]

    def test_improvement_does_not_block(self) -> None:
        from tests.clinical.regression_gate import check_regression

        baseline = {"GC-001": 4}
        report = check_regression({"GC-001": 5}, baseline)
        assert report.passed is True
        assert report.improvements and report.improvements[0].case_id == "GC-001"

    def test_verdict_adapter_is_duck_typed(self) -> None:
        from dataclasses import dataclass

        from tests.clinical.regression_gate import scores_from_verdicts

        @dataclass
        class FakeVerdict:
            case_id: str
            score: int

        verdicts = [FakeVerdict("GC-001", 5), FakeVerdict("GC-002", 3)]
        assert scores_from_verdicts(verdicts) == {"GC-001": 5, "GC-002": 3}


# =============================================================================
# iter-3 chg-3 — Noise threshold + k=N rollouts on the regression gate
# =============================================================================
class TestIter3Chg3NoiseThreshold:
    """
    iter-3 chg-3 closes the LLM-as-judge variance false-positive class
    surfaced by iter-2's GC-017 2->4 and iter-3 chg-1's GC-005 5->2 swings
    (both with identical agent behavior across re-runs).
    """

    def test_default_strict_behavior_preserved(self) -> None:
        """Default noise_threshold=0 reproduces the iter-2 strict gate."""
        from tests.clinical.regression_gate import check_regression

        baseline = {"GC-001": 5}
        report = check_regression({"GC-001": 4}, baseline)  # one-point drop
        assert report.passed is False
        assert [r.case_id for r in report.regressions] == ["GC-001"]
        assert report.jitter == []

    def test_noise_threshold_one_suppresses_one_point_jitter(self) -> None:
        """With noise_threshold=1, a one-point drop is jitter, not regression."""
        from tests.clinical.regression_gate import check_regression

        baseline = {"GC-001": 5}
        report = check_regression({"GC-001": 4}, baseline, noise_threshold=1)
        assert report.passed is True
        assert [j.case_id for j in report.jitter] == ["GC-001"]
        assert report.regressions == []

    def test_noise_threshold_does_not_suppress_two_point_drop(self) -> None:
        """A drop larger than the noise band is still a real regression."""
        from tests.clinical.regression_gate import check_regression

        baseline = {"GC-001": 5}
        report = check_regression({"GC-001": 3}, baseline, noise_threshold=1)
        assert report.passed is False
        assert [r.case_id for r in report.regressions] == ["GC-001"]
        assert report.jitter == []

    def test_real_world_iter2_gc017_jitter_would_be_suppressed(self) -> None:
        """
        Concrete check against the iter-2 documented case.

        GC-017 was observed at score 4 in the iter-2-final baseline and
        score 2 in iter-3 chg-1's baseline-capture — a 2-point swing with
        identical agent code. noise_threshold=1 still treats this as a
        regression (correct); noise_threshold=2 suppresses it as jitter.

        The recommended production setting is noise_threshold=1: tolerate
        the +-1 swing seen on most cases, surface the +-2 swing as worth
        investigation.
        """
        from tests.clinical.regression_gate import check_regression

        baseline = {"GC-017": 4}
        # noise_threshold=1 — 4->2 is a 2-point drop, still a regression
        report = check_regression({"GC-017": 2}, baseline, noise_threshold=1)
        assert report.passed is False
        # noise_threshold=2 — 4->2 is within the (looser) noise band
        report_tolerant = check_regression({"GC-017": 2}, baseline, noise_threshold=2)
        assert report_tolerant.passed is True
        assert [j.case_id for j in report_tolerant.jitter] == ["GC-017"]

    def test_summary_reports_jitter_distinctly_from_regressions(self) -> None:
        """The summary string must surface jitter separately from regressions."""
        from tests.clinical.regression_gate import check_regression

        baseline = {"GC-001": 5, "GC-002": 5, "GC-003": 4}
        current = {"GC-001": 4, "GC-002": 5, "GC-003": 1}  # jitter + regression
        report = check_regression(current, baseline, noise_threshold=1)
        summary = report.summary()
        assert "FAILED" in summary  # GC-003 is a real regression
        assert "Regressions" in summary
        assert "GC-003" in summary
        assert "Jitter within noise tolerance" in summary
        assert "GC-001" in summary  # the jitter line


# =============================================================================
# iter-3 chg-3 — k=N rollouts in capture_baseline + save_baseline distributions
# =============================================================================
class TestIter3Chg3Rollouts:
    """
    save_baseline now accepts optional `distributions` for multi-rollout data.
    Tests are stdlib-only (no API key); cover the save/load roundtrip and the
    schema-evolution behavior.
    """

    def test_save_baseline_without_distributions_unchanged(self, tmp_path: Path) -> None:
        """Default save (no distributions) produces the iter-2 file shape."""
        import json

        from tests.clinical.regression_gate import save_baseline

        path = save_baseline(
            {"GC-001": 5, "GC-002": 4},
            tmp_path / "b.json",
            iteration_tag="harness-iter-1",
        )
        data = json.loads(path.read_text())
        assert data["iteration_tag"] == "harness-iter-1"
        assert data["scores"] == {"GC-001": 5, "GC-002": 4}
        assert "distributions" not in data  # absent when no rollouts

    def test_save_baseline_with_distributions_adds_field(self, tmp_path: Path) -> None:
        """When --rollouts > 1, the baseline file also includes distributions."""
        import json

        from tests.clinical.regression_gate import save_baseline

        path = save_baseline(
            {"GC-001": 5, "GC-002": 4},
            tmp_path / "b.json",
            iteration_tag="harness-iter-3",
            distributions={"GC-001": [5, 5], "GC-002": [4, 5]},
        )
        data = json.loads(path.read_text())
        assert data["distributions"] == {"GC-001": [5, 5], "GC-002": [4, 5]}
        # scores still present (typically the median across rollouts)
        assert data["scores"] == {"GC-001": 5, "GC-002": 4}

    def test_capture_baseline_median_helper_handles_odd_and_even_lengths(self) -> None:
        """The _median_score helper produces an int suitable for the gate."""
        from tests.clinical.capture_baseline import _median_score

        assert _median_score([5]) == 5
        assert _median_score([5, 5]) == 5
        assert _median_score([3, 5]) == 4  # statistics.median on even -> mean
        assert _median_score([1, 3, 5]) == 3
        assert _median_score([1, 2, 4, 5]) == 3  # mean of middle two (2,4)=3


# =============================================================================
# Deliverable 2 — Near-miss memory-trap golden cases
# =============================================================================
class TestDeliverable2NearMissCases:
    """Discrimination cases that catch H2 false-pattern-matching."""

    def test_module_exists_and_has_at_least_two_cases(self) -> None:
        from tests.clinical.near_miss_cases import NEAR_MISS_CASES

        assert len(NEAR_MISS_CASES) >= 2

    def test_no_near_miss_case_auto_approves(self) -> None:
        """The defining property: a near-miss must NEVER be auto-approved."""
        from tests.clinical.golden_cases import ExpectedOutcome
        from tests.clinical.near_miss_cases import NEAR_MISS_CASES

        for c in NEAR_MISS_CASES:
            assert c.expected_outcome != ExpectedOutcome.AUTO_APPROVED, (
                f"{c.case_id} is a near-miss but expects AUTO_APPROVED"
            )

    def test_ids_unique_and_disjoint_from_golden(self) -> None:
        from tests.clinical.golden_cases import GOLDEN_CASES
        from tests.clinical.near_miss_cases import NEAR_MISS_CASES

        nm_ids = [c.case_id for c in NEAR_MISS_CASES]
        assert len(nm_ids) == len(set(nm_ids)), "near-miss IDs not unique"
        golden_ids = {c.case_id for c in GOLDEN_CASES}
        assert not (set(nm_ids) & golden_ids), "near-miss IDs collide with golden IDs"

    def test_required_fields_populated(self) -> None:
        from tests.clinical.near_miss_cases import NEAR_MISS_CASES

        for c in NEAR_MISS_CASES:
            assert c.title and c.clinical_notes and c.guidelines_context
            assert c.clinical_rationale and c.judge_scoring_criteria
            assert len(c.reasoning_must_include) >= 1
            assert len(c.reasoning_must_not_include) >= 1

    def test_covers_both_intended_trap_scenarios(self) -> None:
        """One PD-L1-below-threshold trap and one EGFR-mutation trap."""
        from tests.clinical.near_miss_cases import NEAR_MISS_CASES

        blob = " ".join(
            (c.title + " " + c.clinical_notes + " " + c.guidelines_context).lower()
            for c in NEAR_MISS_CASES
        )
        assert "45%" in blob and "50%" in blob, "missing PD-L1 below-threshold trap"
        assert "egfr" in blob, "missing EGFR-mutation trap"

    def test_each_case_guards_against_memory_bleed(self) -> None:
        """Each must forbid 'auto-approved' appearing in the rationale."""
        from tests.clinical.near_miss_cases import NEAR_MISS_CASES

        for c in NEAR_MISS_CASES:
            forbidden = {s.lower() for s in c.reasoning_must_not_include}
            assert "auto-approved" in forbidden, (
                f"{c.case_id} should forbid 'auto-approved' in rationale"
            )


# =============================================================================
# Deliverable 3 — Doc-drift guard + erratum reconciliation
# =============================================================================
class TestDeliverable3DocDriftReconciliation:
    """Turns spec-vs-code drift into a test, and records the iter-0 correction."""

    def test_guard_module_exists_and_imports(self) -> None:
        from tests.harness import doc_drift_guard  # noqa: F401

    def test_erratum_artifact_exists_and_names_the_drift(self) -> None:
        path = REPO_ROOT / "docs_reconciliation/ITER0_ERRATUM.md"
        assert path.exists(), f"erratum note missing at {path}"
        text = path.read_text()
        # It must name the missing file AND the real instrumentation location.
        assert "observability/trajectory.py" in text
        assert "base.py" in text

    def test_guard_CATCHES_a_drifted_doc(self, tmp_path: Path) -> None:
        """A doc referencing a nonexistent src file must be flagged."""
        from tests.harness.doc_drift_guard import find_dangling_references

        docs = tmp_path / "docs"
        docs.mkdir()
        # Use a living-spec doc name (EVALUATION.md); the append-only logs
        # (DECISIONS.md/ITERATIONS.md) are excluded by default.
        (docs / "EVALUATION.md").write_text(
            "Instrumentation at `src/pacca/observability/trajectory.py` ships in iter-0."
        )
        # repo_root has no such file
        dangling = find_dangling_references(docs, tmp_path)
        assert any(
            d.referenced_path == "src/pacca/observability/trajectory.py" for d in dangling
        ), "guard failed to catch the known drift"

    def test_guard_excludes_append_only_logs_by_default(self, tmp_path: Path) -> None:
        """A dangling ref inside DECISIONS.md/ITERATIONS.md must be ignored."""
        from tests.harness.doc_drift_guard import find_dangling_references

        docs = tmp_path / "docs"
        docs.mkdir()
        (docs / "ITERATIONS.md").write_text(
            "Historical (superseded): `src/pacca/observability/trajectory.py`."
        )
        assert find_dangling_references(docs, tmp_path) == []

    def test_guard_PASSES_a_reconciled_doc(self, tmp_path: Path) -> None:
        """A doc referencing only files that exist must pass clean."""
        from tests.harness.doc_drift_guard import find_dangling_references

        # Create the real file the reconciled doc points at.
        (tmp_path / "src/pacca/agents").mkdir(parents=True)
        (tmp_path / "src/pacca/agents/base.py").write_text("# real file\n")

        docs = tmp_path / "docs"
        docs.mkdir()
        (docs / "EVALUATION.md").write_text(
            "Instrumentation ships as OTel spans in `src/pacca/agents/base.py`."
        )
        assert find_dangling_references(docs, tmp_path) == []


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-v"]))
