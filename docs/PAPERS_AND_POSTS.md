# Papers and Posts — Suggested Publications from the PACCA Cycle

> **Audience:** the author + collaborators considering what to write next.
> **Status:** v1.0, drafted 2026-05-25 at iter-6 open. A living idea-bank, not a commitment to write every entry.
> **Companion documents:** [`HARNESS.md`](HARNESS.md), [`DATASET_SUFFICIENCY.md`](DATASET_SUFFICIENCY.md), [`findings/H2-memory-iteration-1.md`](findings/H2-memory-iteration-1.md), [`PACCA_PRD_v2.5_Consolidated.md`](PACCA_PRD_v2.5_Consolidated.md).

## Why this document exists

The PACCA v2.3 harness-engineering cycle produced 5+ iterations of empirical lessons that are not yet in the public literature. The AHE methodology (Lin et al. 2026) provides the parent framework; PACCA's contribution is operationalizing that framework against a HIPAA-relevant clinical-AI surface and documenting what actually happened — including the failures, the wording-level fixes, and the discipline that made post-hoc storytelling impossible.

This document organizes the writeable ideas by venue and audience, with a one-paragraph thesis per item plus the supporting evidence already in the repo. The goal: anyone considering "what should I write about this work?" can scan this and pick an entry rather than starting from scratch.

## Section 1 — Academic papers (peer review, technical depth)

These are workshop / conference / journal targets. Each thesis is non-trivial and defensible from PACCA's record.

### 1.1 — "Wording matters: a sub-iteration case study on institutional-memory entries in clinical agentic systems"

- **Venue:** ML4H (Machine Learning for Health) workshop at NeurIPS, OR ICML AI for Science workshop. Backup: AMIA Annual Symposium.
- **Length:** 6–8 pages.
- **Thesis:** When AHE-style Phase H2 institutional memory encodes multiple anti-patterns in the same entry, the LLM can over-generalize from the structural pattern (multiple negatives → "this looks like denial territory") and route IN_REVIEW cases to DENIED. The fix is sub-iteration wording, not architectural change: explicit per-anti-pattern "Status: IN_REVIEW. (Not DENIED.)" disambiguation and a "Why this distinction matters" clarifying paragraph.
- **Evidence in repo:**
  - `docs/findings/H2-memory-iteration-1.md` — the GC-021 mid-iteration regression report.
  - `harness/manifests/iter-3.json` chg-2 — the predicted_fix / risk_cases / verdict trio that caught the regression in real time.
  - `docs/ITERATIONS.md` iter-3 narrative.
  - The actual wording before/after in `src/pacca/prompts/decision_agent_*.py` (or wherever the memory entry lives).
- **Why it matters:** the agentic-systems literature treats H2 as a binary "use memory or not" decision. This paper would document that *within* H2, wording-level choices have measurable behavioral consequences and need their own discipline.
- **Novelty:** the AHE paper (arXiv:2604.25850) introduces H2 but doesn't characterize sub-iteration wording effects. This paper would extend that.

### 1.2 — "Per-case regression gates compose with aggregate gates: complementary sensitivity in LLM-judge-evaluated systems"

- **Venue:** MLSys (Conference on Machine Learning and Systems), OR EMNLP industry track.
- **Length:** 6–8 pages.
- **Thesis:** The per-case regression gate (single-case score drop relative to baseline) and the aggregate-accuracy gate (binomial proportion test) detect different failure modes. The per-case gate excels at sharp single-case regressions (hallucinations, behavioral flips). The aggregate gate excels at slow distributed erosion across many cases (the Phase H2 memory-degrades-reasoning-quality failure mode). The two compose; running only aggregate misses surgical regressions; running only per-case misses erosion.
- **Evidence in repo:**
  - `tests/clinical/regression_gate.py` (iter-2 chg-2) — per-case gate implementation.
  - `tests/clinical/evaluator.py` — aggregate ≥80% gate.
  - `docs/STATISTICAL_POWER.md` § "How the per-case gate composes with aggregate" — the sensitivity-analysis cross-table.
  - `harness/manifests/iter-2.json` — the change that introduced the per-case gate, with a synthetic 5→3 case that demonstrates aggregate-undetectable per-case-detectable degradation.
- **Why it matters:** the LLM-as-judge literature treats accuracy as the headline metric. Per-case gates are a contribution that the field hasn't formalized. The complementarity is the punchline.

### 1.3 — "From byte-identity checks to criterion-preservation tests: an evolution of harness-discipline tests under prompt-version churn"

- **Venue:** EASE (Evaluation and Assessment in Software Engineering), OR FSE Industry Track.
- **Length:** 4–6 pages (short paper).
- **Thesis:** Byte-identity checks (the literal text of a prompt is unchanged across iterations) are sufficient for early-stage agentic systems but become a maintenance burden once prompts churn for legitimate reasons (specialty-specific additions, model-version migrations). Criterion-preservation tests (specific behavioral invariants the prompt must satisfy, independent of wording) are the natural successor and scale better.
- **Evidence in repo:**
  - iter-1 chg-1 — byte-identity check introduced.
  - iter-3+ — criterion-preservation tests in `tests/clinical/test_*` files for memory entries, escalation thresholds, anti-pattern routing.
  - `docs/ITERATIONS.md` narrative of the evolution.
- **Why it matters:** practitioners adopting AHE-style discipline will hit this exact transition. A documented playbook saves the trial-and-error.

### 1.4 — "Heuristics in score-model clothing: when N=4 is enough data and when it isn't"

- **Venue:** Workshop on Robustness in AI for Health (ML4H workshop), OR AAAI Bridge Program.
- **Length:** 4–6 pages.
- **Thesis:** iter-5 chg-3's complexity-score model is a 1–5 weighted heuristic, not a trained model. With only 4 pediatric data points (GC-012, GC-023, GC-024, GC-025), no statistical-learning model would be defensible. The heuristic-as-score is defensible because: (a) the weights are derivable from clinical-judgment first principles rather than fit; (b) the discriminator's three-class output (clear-no / ambiguous / clear-yes) is verified against the 4 data points; (c) the model is honestly framed as a heuristic in the documentation, not as ML. The paper would argue for this framing as a transparency norm — "score model" wording often implies learned weights, which mis-leads reviewers when the weights are clinician-set.
- **Evidence in repo:**
  - `src/pacca/agents/clinical_risk_detector.py` (or wherever pediatric_complex check lives) — the score model implementation.
  - `tests/test_complexity_score_model.py` — the test surface.
  - `docs/ITERATIONS.md` iter-5 chg-3 narrative — the honest framing as a heuristic.
- **Why it matters:** the AI-in-healthcare literature has rampant inflation of "model" language for clinician-set heuristics. A transparency-first piece arguing for the honest framing would be a citable reference.

### 1.5 — "Dataset sufficiency for clinical agentic-AI evaluation: a three-framework decomposition"

- **Venue:** JAMIA (Journal of the American Medical Informatics Association), OR npj Digital Medicine.
- **Length:** 8–12 pages (full research paper).
- **Thesis:** Existing "how many evaluation cases do you need?" literature in medical AI converges on prevalence-weighted sampling (HEDIS-style). For agentic systems with discrete escalation branches and per-case regression gates, three orthogonal frameworks apply and they yield different minimum case counts: (a) per-gate coverage (gates × polarities ≈ 50), (b) statistical power for aggregate-accuracy drop detection (binomial CI; n depends on Δ), (c) real-world prevalence weighting (300+ for major payer mix). The right number is the maximum of the three.
- **Evidence in repo:**
  - `docs/DATASET_SUFFICIENCY.md` — the whole document is the source for this paper.
  - `docs/STATISTICAL_POWER.md` — the binomial-CI math.
  - `docs/EVALUATION_COVERAGE.md` — the per-cell coverage matrix.
  - `docs/CASE_PROVENANCE.md` — the per-case audit trail.
- **Why it matters:** every agentic-AI clinical project that aims at SaMD-grade will hit this exact decomposition question. A citable reference saves each team from re-deriving it.

## Section 2 — Industry case studies and white papers

These are shorter (3–6 pages), customer-facing, and lower-bar than peer-reviewed academic work. Suitable for the project's blog, LinkedIn long-form posts, or a private "for prospective customers" PDF.

### 2.1 — "The wording fix that saved an iteration"

- **Venue:** Project blog / LinkedIn long-form.
- **Length:** 1,500–2,500 words.
- **Thesis:** Tell the GC-021 mid-iteration regression story as a narrative. The iter-3 chg-2 H2 memory entry was approved at first-pass review, deployed, and immediately regressed one case. Investigation traced to memory-wording over-generalization. Three-paragraph wording change resolved it. The post argues that this is the kind of thing every team will hit and that having a per-case regression gate (which immediately surfaces the problem) plus a runbook discipline (which makes the fix one chg-N entry rather than a panic) is what saved the iteration.
- **Evidence in repo:** Same as paper 1.1.
- **Why it matters:** practitioner audience. Demonstrates that the discipline pays off in the worst case, not just the easy case.

### 2.2 — "Why we don't claim SaMD-grade validation (yet)"

- **Venue:** Project blog / customer-facing PDF.
- **Length:** 1,500–2,500 words.
- **Thesis:** Most healthcare-AI vendors at portfolio stage either claim SaMD-grade validation without the evidence (intellectually dishonest) or refuse to talk about clinical validation at all (dodging the question). PACCA's middle path: state clearly what the 33-case dataset can defend, state clearly what it can't, publish the roadmap to SaMD-grade with effort estimates. The post argues that this honesty is a competitive advantage when customers do due diligence.
- **Evidence in repo:** `docs/PACCA_PRD_v2.5_Consolidated.md` § 16.9 (honest claims matrix), `docs/DATASET_SUFFICIENCY.md`.
- **Why it matters:** SaMD literacy is rising; customers are starting to ask the right questions. Vendors who answered honestly first will win the comparison.

### 2.3 — "Branch-and-PR discipline for AI feature work: lessons from PACCA's harness cycle"

- **Venue:** Project blog / LinkedIn long-form.
- **Length:** 1,000–1,500 words.
- **Thesis:** The conventional wisdom that AI feature work is too "exploratory" for branch-and-PR discipline is wrong. PACCA's 5+ iterations all used branch-and-PR, with each iteration's changes landing as squash-merged commits documented in append-only audit logs. The post argues that AI work benefits *more* from the discipline because the iteration's "what changed" is less mechanically obvious than for traditional code, so the audit trail is more valuable.
- **Evidence in repo:** Git history. `docs/DECISIONS.md` and `docs/ITERATIONS.md` append-only logs. The `pacca_pr_workflow.md` memory note codifying the policy.
- **Why it matters:** team-leadership audience. Cuts against the prevailing "AI is special, normal rules don't apply" narrative.

### 2.4 — "Hooks that fight you: a debugging tale of pre-commit / CI version drift"

- **Venue:** Project blog / dev-focused community (lobste.rs, HN if it pops, Programming Reddit).
- **Length:** 800–1,200 words.
- **Thesis:** Pre-commit ruff v0.8.0 vs CI's ruff v0.15.12 disagree on `assert X, msg` formatting. The disagreement creates an infinite ping-pong where local commits format one way, CI demands the other, and developers can't merge cleanly. The fix is to pin pre-commit's ruff to CI's version. The post argues for version-pinning discipline across the entire dev/CI surface, not just dependency versions.
- **Evidence in repo:** PR #8 (the fix), `.pre-commit-config.yaml`, `.github/workflows/ci.yml`.
- **Why it matters:** every team using pre-commit + CI will hit a version-drift bug eventually. A clear writeup with the symptoms + diagnosis + fix saves them debugging hours.

### 2.5 — "Audit-defensible AI development: an append-only log discipline"

- **Venue:** Project blog / compliance-focused publication (Compliance Week, Health IT News).
- **Length:** 1,500–2,000 words.
- **Thesis:** SaMD audit defense requires that "what happened" be reconstructable from sources that cannot be retroactively edited. PACCA uses three append-only artifacts: `DECISIONS.md` (verdicts), `ITERATIONS.md` (narratives), `harness/manifests/iter-N.json` (machine-readable per-change records with predicted_fix / risk_cases / verdict structure that prevents post-hoc storytelling). The post argues for this pattern as the audit-defense baseline for any AI system that might face regulatory or contractual review.
- **Evidence in repo:** All three audit artifacts. `HARNESS.md` rules-of-engagement section. The superseding-correction protocol with reified Block 1 / Block 2 corrections in `DECISIONS.md`.
- **Why it matters:** compliance audience. Maps to FDA Design Controls (21 CFR 820.30) and SOC 2 evidence requirements.

## Section 3 — LinkedIn posts (already done; extend to new lessons)

The author has been publishing per-iteration LinkedIn posts (iter-1 through iter-5). The roadmap of remaining post topics:

### 3.1 — Iter-6 closure post (when iter-6 ships)

- **Topic:** the dataset-expansion increment (25 → 33 cases) and the four companion documentation artifacts. Frame around the "what 8 cases buy you in coverage" question with the per-dimension before/after.
- **Graphic:** the EVALUATION_COVERAGE.md summary table, with iter-5 state on the left and iter-6 state on the right, highlighting the cells that newly populate (DENY × NONE branch, cardiology × 18-64, cardiology × 80+, behavioral health × 18-64, etc.).

### 3.2 — Dataset sufficiency framework post

- **Topic:** the three frameworks (coverage, power, prevalence). Sized as a 1–2 paragraph teaser pointing at the `DATASET_SUFFICIENCY.md` document.
- **Graphic:** the sample-size table from `STATISTICAL_POWER.md` (Δ vs n), with PACCA's 33 marked on the axis.

### 3.3 — Honest claims matrix post

- **Topic:** the v2.5 PRD § 16.9 "honest claims" table. Frame as "here's what we can defend, here's what we can't, here's our roadmap."
- **Graphic:** the table itself, with green ✓ / red ✗ formatting.

### 3.4 — Cycle-retrospective post

- **Topic:** lessons from 5 iterations of AHE-style harness work. The "wording matters" lesson from iter-3 chg-2; the "score model honesty" lesson from iter-5 chg-3; the "branch-and-PR pays off" lesson from the whole cycle.
- **Graphic:** a process diagram showing the iteration loop with each iteration's chg-N entries labeled.

### 3.5 — "Why we built the per-case gate" post

- **Topic:** the iter-2 chg-2 introduction of `regression_gate.py`. Frame around the silent-degradation case (5→3 score drop with aggregate accuracy unchanged) and why aggregate-only evaluation misses this class of regression.
- **Graphic:** a side-by-side: "aggregate gate says PASS" vs "per-case gate says FAIL on case X."

## Section 4 — Conference talks

These are 20–45 minute talk proposals to relevant venues.

### 4.1 — HIMSS (Healthcare Information and Management Systems Society)

- **Title:** "Audit-defensible AI prior authorization: a harness-engineering case study."
- **Audience:** payer IT, provider IT, vendor engineering, compliance officers.
- **Time:** 45 min including Q&A.
- **Sketch:** open with the cost of opaque AI in PA (denials at scale with no audit trail); introduce harness engineering as the answer; walk through PACCA's 5-iteration cycle; show the audit-defense artifacts; close with the SaMD-grade roadmap.

### 4.2 — AMIA Annual Symposium

- **Title:** "Wording matters: sub-iteration H2 memory effects in clinical agentic AI."
- **Audience:** clinical informaticians, AI-in-healthcare researchers.
- **Time:** 20 min.
- **Sketch:** academic version of post 2.1 / paper 1.1.

### 4.3 — ML4H (Machine Learning for Health) workshop at NeurIPS

- **Title:** "Per-case regression gates: surgical detection in LLM-judge evaluation."
- **Audience:** ML researchers building clinical-AI evaluation systems.
- **Time:** 15 min lightning talk + poster.
- **Sketch:** academic version of paper 1.2.

### 4.4 — FAccT (Fairness, Accountability, Transparency)

- **Title:** "Honest claim matrices: a transparency primitive for AI-in-healthcare vendors."
- **Audience:** AI ethics + policy.
- **Time:** 20 min.
- **Sketch:** academic version of post 2.2 + the broader argument for vendor honesty as a transparency primitive.

### 4.5 — Strange Loop / Papers We Love

- **Title:** "Operationalizing the Agentic Harness Engineering paper: a 5-iteration field report."
- **Audience:** generalist software-engineering audience.
- **Time:** 30 min.
- **Sketch:** the technical-architecture version of the cycle retrospective, oriented toward engineers considering AHE adoption.

## Section 5 — Open-source contributions

Beyond writing, the cycle produced reusable artifacts that could be extracted to OSS:

| Artifact | OSS target |
|---|---|
| `regression_gate.py` (per-case + aggregate) | Standalone PyPI package `llm-eval-gate` or similar |
| Change-manifest schema (`change_manifest.schema.json`) | JSON Schema gallery + AHE-paper companion repo |
| Append-only DECISIONS.md / ITERATIONS.md pattern | A `cookiecutter-harness-discipline` template repo |
| Case-authoring guide template | A `cookiecutter-clinical-eval-dataset` template repo |
| Pre-commit + CI ruff version-alignment guard | A standalone pre-commit hook |

These would expand the addressable audience for the writing in §§ 1–4 by giving readers a tool to adopt, not just an idea to consider.

## Section 6 — Sequencing recommendation

If the author has limited writing bandwidth, the recommended order is:

1. **Post 2.2 — "Why we don't claim SaMD-grade validation (yet)"** — highest immediate-value differentiation against competitors; sized as a long blog post; uses material already drafted in the v2.5 PRD.
2. **Post 3.1 — Iter-6 closure LinkedIn post** — preserves the per-iteration cadence the author has established.
3. **Paper 1.5 — Dataset sufficiency JAMIA paper** — highest academic-citation potential; document is already drafted as `DATASET_SUFFICIENCY.md`.
4. **Post 2.1 — "The wording fix that saved an iteration"** — narrative-driven; broad practitioner appeal; cross-pollinates into the paper 1.1 academic version.
5. **Paper 1.2 — Per-case gates compose with aggregate** — strongest technical contribution; broad ML-systems audience.
6. **Talk 4.1 — HIMSS** — biggest stage; gives the work a market platform.
7. Everything else as bandwidth allows.

## Section 7 — What NOT to write

Some things look writable but probably aren't worth the bandwidth:

- **"Why we chose Claude over GPT" — no.** The model choice is largely contingent on the author's API access and pricing at the time. The lessons learned generalize across models; a model-comparison piece would date quickly and provide thin signal.
- **"PACCA achieves 100% accuracy on the clinical gate" — no.** Aggregate accuracy on a 33-case dataset is not a defensible claim per `STATISTICAL_POWER.md`; trumpeting it would undermine the credibility built up by the rest of the work.
- **"A complete tutorial on building a clinical-AI system" — no.** Too broad; would dilute into how-to material. The narrower wordings ("the wording fix," "the per-case gate") have stronger thesis-per-word density.
- **A reply piece to any specific competitor — no.** The honest-claims-matrix framing speaks for itself; ad-hominem-adjacent comparisons would weaken the principled position.

---

*This document is part of the PACCA v2.5 cycle documentation set. Last updated: 2026-05-25 (iter-6 open). Update sequence recommendations as the publishing landscape and the project's state evolve.*
