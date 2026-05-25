# Statistical Power — Aggregate and Per-Case Regression Detection

> **Companion to:** [`DATASET_SUFFICIENCY.md`](./DATASET_SUFFICIENCY.md) — this document provides the calculations underlying the per-claim case-count thresholds.
> **Audience:** auditors, FDA SaMD reviewers, statistical-validation consultants, and contributors who need to defend the case-count numbers with explicit math.

## Two layers of regression detection

PACCA's evaluation gate operates at two layers, which compose:

| Layer | Source | What it detects | Sensitivity |
|---|---|---|---|
| **Per-case** | iter-2 chg-2 [`regression_gate.py`](../tests/clinical/regression_gate.py) | Any single-case score drop relative to baseline | 100% per-case, regardless of dataset size |
| **Aggregate** | The traditional ≥80% accuracy gate ([`evaluator.py`](../tests/clinical/evaluator.py)) | Aggregate accuracy drops below threshold | Depends on dataset size — see binomial math below |

The per-case layer dominates for *detection*. The aggregate layer matters when you need a single summary statistic to defend a claim ("aggregate accuracy did not drop by more than X percentage points") for customer-facing reports or FDA submissions.

## The binomial-CI math

The aggregate-layer gate is a hypothesis test on a binomial proportion:
- **Null hypothesis** `H₀`: accuracy is `p₀` (the baseline)
- **Alternative hypothesis** `H₁`: accuracy has degraded to `p₁` (where `p₁ < p₀`)

For a one-sided test with significance `α` (false-positive rate — flagging a regression when there isn't one) and power `1-β` (true-positive rate — catching a real regression):

```
n ≈ ( z_α · √(p₀ · (1 - p₀))  +  z_β · √(p₁ · (1 - p₁)) )²  /  (p₀ - p₁)²
```

Where:
- `z_α` = one-sided critical value at significance `α` (e.g., 1.645 for α=0.05)
- `z_β` = one-sided critical value at the power level (e.g., 0.842 for 80% power, β=0.20)

This is the **normal approximation** to the binomial. It degrades when `n` is very small (<30) or when `p` is near 0 or 1. PACCA's evaluation runs are typically in the `p ≈ 0.80–0.95` range, well within the approximation's accuracy.

## Sample sizes for PACCA's evaluation regime

**Assumptions:**
- Baseline accuracy `p₀ = 0.95` (PACCA's current cycle has held aggregate at 100% across iter-3/4/5, but 95% is the realistic floor for a production claim that accounts for LLM-as-judge variance)
- Two-tail considerations: we only care about *drops* (one-sided test), since improvements don't need a regression flag
- α = 0.05 (5% false-positive rate — the gate flags a regression that isn't there 5% of the time)
- Power 1-β = 0.80 (we catch a real regression 80% of the time)

| Δ (drop to detect) | `p₁` | n (per the formula) | Operational target |
|---|---|---|---|
| 20 pp | 0.75 | **13** | 20 (safety margin) |
| 15 pp | 0.80 | **23** | 30 |
| 10 pp | 0.85 | **43** | 100 |
| 7 pp | 0.88 | **75** | 150 |
| 5 pp | 0.90 | **150** | 200–300 |
| 3 pp | 0.92 | **390** | 500 |
| 2 pp | 0.93 | **870** | 1,000+ |

### Derivation of the n=43 case (10pp drop)

Step by step:
```
α = 0.05   →   z_α = 1.645
β = 0.20   →   z_β = 0.842
p₀ = 0.95
p₁ = 0.85
p₀ - p₁ = 0.10

Variance terms:
  √(p₀ · (1 - p₀))  =  √(0.95 · 0.05)  =  √0.0475  =  0.218
  √(p₁ · (1 - p₁))  =  √(0.85 · 0.15)  =  √0.1275  =  0.357

Numerator:
  (z_α · 0.218  +  z_β · 0.357)²
  = (1.645 · 0.218  +  0.842 · 0.357)²
  = (0.358  +  0.301)²
  = 0.659²
  = 0.434

Denominator:
  (p₀ - p₁)²  =  0.10²  =  0.01

n = 0.434 / 0.01 = 43.4 → 44 (round up)
```

Add safety margin and per-specialty stratification (4-8 specialties at PACCA's coverage) → **operational target 100**.

### Why operational targets exceed the formula

The raw formula gives the minimum n for the assumed `p₀` and `p₁`. Real-world deployment requires:

1. **Per-specialty stratification.** If you want to detect a 10pp drop in any specialty (not just aggregate), each specialty needs the per-stratum n. With 8 major specialties, that's 8 × 43 = 344 minimum for full per-specialty detection at 10pp.

2. **Safety margin for boundary effects.** The normal approximation degrades near the boundary. Doubling the formula's n for safety is standard.

3. **Continuity correction.** The Yates continuity correction adds 1/(2(p₀-p₁)) to the formula's n. At Δ=0.10, that's +5 cases. At Δ=0.05, +10.

4. **LLM-as-judge variance.** The iter-3 chg-3 work established that the judge produces ±1-2 score variance on same-state runs. Effective `p` has its own variance that further inflates required n.

**Practical rule:** double the formula's `n` for production targets, triple for SaMD-grade claims.

## How the per-case gate composes with aggregate

The iter-2 chg-2 per-case regression gate fires on **any** single-case score drop relative to baseline. With the iter-3 chg-3 noise threshold (default 0, recommended production value 1), it tolerates ±1 point of judge jitter while still catching ±2+ regressions.

**Sensitivity analysis:**

| Scenario | Per-case gate fires | Aggregate gate fires (if n=25) | Aggregate gate fires (if n=100) | Aggregate gate fires (if n=300) |
|---|---|---|---|---|
| 1 case drops 5→2 (95% → 91%) | YES | No (within noise) | No (within power for 10pp) | Marginal (50% power for 4pp) |
| 3 cases drop 5→3 (95% → 83%) | YES | YES (clear) | YES (clear) | YES (clear) |
| 10 cases drop 5→3 in 100-case set (95% → 85%) | YES | n/a | YES (80% power) | YES (>99% power) |
| Single hallucination-class regression on 1 case | YES | No | No | No |
| Slow erosion: every case drops by 0.5 on average | NO (drops < noise threshold) | YES if aggregate drops >threshold | YES with more cases | YES with more cases |

**Key observation:** the per-case gate excels at sharp, single-case regressions (hallucinations, behavioral flips). The aggregate gate excels at slow, distributed erosion across many cases (the H2-memory-degrades-reasoning-quality failure mode). They are complementary.

## Per-case regression-detection math (formal)

Given a baseline scoreboard `B = {case_id: score_baseline}` and a current run scoreboard `C = {case_id: score_current}`, the gate fires if:

```
∃ case_id ∈ B : (B[case_id] - C[case_id]) > noise_threshold
   ∧ (B[case_id] - C[case_id]) ≥ drop_threshold
```

Where `noise_threshold` (default 0) and `drop_threshold` (default 1) are parameters. With `noise_threshold = 1` (production recommended) and `drop_threshold = 1`, the gate fires on any drop of 2 or more points on any single case.

**Per-case false-positive rate:**
The per-case gate flags genuine `δ ≥ 2` drops with 100% sensitivity. Its false-positive rate depends on the judge's per-case score variance distribution:

| Per-case score variance (σ) | False-positive rate (per case, per run) | Per-run false-positive rate (n=100, noise_threshold=1) |
|---|---|---|
| 0 (deterministic judge) | 0% | 0% |
| 1.0 (±1 score swing common) | ~16% (assuming normal) | ~100% (one of 100 will swing ≥2) |
| 0.5 (well-behaved judge) | ~5% | ~99% |
| 0.3 (very tight judge) | ~0.3% | ~26% |

**Practical implication:** at n=100 with a judge that has ±1 score variance, the gate fires on noise alone with high probability. This is why `noise_threshold = 1` is the production-recommended setting — it filters out the ±1 jitter that's noise, leaving the gate to flag ±2+ which are likely real regressions.

**The k=2 rollouts feature** (iter-3 chg-3 `capture_baseline.py --rollouts N`) reduces effective `σ` by averaging k samples per case. At k=2, σ_effective ≈ σ_single / √2 ≈ 0.5σ. With k=4, σ_effective ≈ 0.5σ. This is how PACCA achieves zero jitter in current 2-rollout captures (the median of 2 same-state scores filters single-roll noise).

## FDA SaMD-grade claim alignment

Per FDA's *Software as a Medical Device: Clinical Evaluation* (2017) and the IMDRF SaMD WG/N41 framework, the analytical-validation pillar requires demonstrating that the SaMD performs as intended on representative inputs.

PACCA's claims map to FDA's framework as:

| FDA claim type | PACCA's evidence | Case count required | Where PACCA is |
|---|---|---|---|
| Analytical validation — correctness | Per-gate coverage matrix (`EVALUATION_COVERAGE.md`) | ≥50 (Framework 1) | 25, below |
| Analytical validation — robustness | Adversarial / failure-mode cases (hallucination traps, near-miss, memory-trap, sparse-docs) | ≥30 (per major failure mode × 5) | ~10 named cases across modes |
| Analytical validation — repeatability | k=2+ rollouts, distribution captured | k=2 done (iter-3 chg-3); k=4+ recommended for SaMD | k=2 minimum implemented |
| Clinical validation — agreement with experts | Independent clinical-review-board scoring | 100/quarter at Cohen's κ ≥ 0.80 | Not yet implemented |
| Clinical performance — post-market | Production deployment + feedback loop | Continuous | N/A — pre-deployment |

The path to SaMD-grade:
1. Grow the in-house dataset to 500 cases per the priority order in [`DATASET_SUFFICIENCY.md`](./DATASET_SUFFICIENCY.md)
2. Run capture_baseline with --rollouts 4 to validate repeatability claims
3. Establish a clinical-review-board sampling process (separately budgeted; typically external)
4. After production deployment, instrument for continuous performance evaluation

## References

| Source | Use |
|---|---|
| Casagrande, Pike & Smith (1978), *An Improved Approximate Formula for Calculating Sample Sizes for Comparing Two Binomial Distributions* | The continuity-corrected formula used in the per-line calculations. |
| Fleiss, Levin & Paik (2003), *Statistical Methods for Rates and Proportions, 3rd ed.* | Standard reference for binomial test sample-size formulas. |
| FDA, *Software as a Medical Device (SaMD): Clinical Evaluation* (Dec 2017) | The three-pillar framework cited above. |
| IMDRF SaMD WG/N41 (2017), *Software as a Medical Device (SaMD): Clinical Evaluation* | International counterpart. |
| Cohen (1960), *A coefficient of agreement for nominal scales* | Cohen's κ inter-rater reliability metric. |
| Landis & Koch (1977), *The measurement of observer agreement for categorical data* | The κ interpretation thresholds (≥0.80 = "almost perfect" agreement). |

---

*This document is part of the PACCA v2.3 harness-engineering cycle documentation set. Last updated: 2026-05-25.*
