# iter-5 Runbook — Pediatric data + complexity-score model + asthma H2 entry + structlog cleanup

The cycle's **largest iteration by change count** (4 chgs) but each is
well-scoped. Three of the four are independent; chg-2 → chg-3 has a real
data-dependency (the complexity-score model needs the new pediatric cases
to validate against). Execution order is structured around that.

**Conventions:** `$REPO=/Users/davidreed/David_Portfolio/pacca`; commands run
from repo root; **✓ Verify** lines mark per-step expected results; branch +
PR workflow per `pacca_pr_workflow.md`.

**Estimated time:** ~2.5–3 hours (chg-1 ~15m, chg-2 ~30m + live capture,
chg-3 ~45m, chg-4 ~45m + live capture, closure ~30m).

**Design decisions locked at iteration start:**

- *chg-1 (structlog cleanup):* wrap `extra={...}` rather than adopt the
  `structlog` package. Smaller blast radius, no dependency addition. The
  iter-3 chg-1 TODO comment offered both paths; `extra={...}` is the
  minimum scope.
- *chg-2 (pediatric cases):* add as a separate `PEDIATRIC_CASES` list in
  a new `tests/clinical/pediatric_cases.py`, mirroring the iter-2 chg-3
  `NEAR_MISS_CASES` precedent. GOLDEN_CASES stays at 20; the
  `test_dataset_has_twenty_cases` integrity assertion is preserved.
- *chg-3 (complexity-score model):* integer 1-5 matching the existing
  `complexity_auto_approve_max=2`, `complexity_specialist_review_min=4`
  schema in `Settings`. Weighted-sum heuristic with per-feature clinical
  rationale, not a data-fit model — honest framing is "heuristic in
  score-model clothing" given only 4 pediatric data points. Pediatric
  threshold = 3 (one below the standard 4, with the pediatric weight
  providing the gap).
- *chg-4 (third H2 entry):* asthma dupilumab pattern. Risk cases all in
  the chg-2 expanded pediatric set + the existing GC-012.

**Execution order:** chg-1 (independent infra) → chg-2 (data prerequisite
for chg-3) → chg-3 (depends on chg-2) → chg-4 (independent behavioral).
This minimizes blast radius if anything goes wrong: chg-1 lands clean
regardless; chg-2 changes only test data; chg-3 changes one method; chg-4
is the riskiest (third H2 entry, must not interact with chg-3's new
pediatric-complex logic).

**Predicted fixes:**
- chg-1 → none. Tooling cleanup.
- chg-2 → none. Data addition.
- chg-3 → none predicted to flip; risk cases: GC-012 (must continue to
  escalate via new score model), GC-023 / GC-024 / GC-025 (chg-2's
  pediatric cases route correctly).
- chg-4 → none predicted; risk cases: GC-012 (asthma memory must not
  override pediatric_complex check), GC-023 (mild well-controlled
  asthma — memory must not override the chg-3 score's auto-approve
  pathway), GC-021 / GC-022 (NSCLC near-miss cases must still preserve
  with three H2 entries active).

---

## Step 0 — Pre-flight

```bash
git status              # On branch harness/iter-5
git log --oneline -3    # Top commit: 9e54e1d (iter-4 squash merge)
git tag --points-at HEAD~  # harness-iter-4
set -a; source .env; set +a
```

---

## Step 1 — Open the draft PR

```bash
git add RUNBOOK_iter5.md
git commit -m "iter-5: add runbook (spec only)"
git push -u origin harness/iter-5
gh pr create --draft --base main --head harness/iter-5 \
    --title "iter-5: pediatric data + complexity-score + asthma H2 + structlog cleanup" \
    --body "Draft until 4 chgs land and verification gates green."
```

---

## Step 2 — chg-1: structlog-style logger wrap (tracing.py)

Lowest-risk chg first.

### 2a. Edit tracing.py

In `src/pacca/config/tracing.py`, convert each `logger.warning(event, detail=...)`
call to `logger.warning(event, extra={"detail": ...})`. Three calls total
(per the iter-3 chg-1 TODO comment). Remove the three `# type: ignore[call-arg]`
markers.

### 2b. Verify

```bash
python -m mypy src/pacca/config/tracing.py
python -m pytest tests/unit tests/harness -q
```

**✓ Verify:** mypy clean (no `call-arg` errors); suite 208/208 passes.

### 2c. Commit

```bash
git add src/pacca/config/tracing.py
git commit -m "chg-1: switch tracing.py to extra={...} kwargs (clears iter-3 type-ignores)"
```

---

## Step 3 — chg-2: pediatric case-set expansion

### 3a. Create tests/clinical/pediatric_cases.py

Follow the `NEAR_MISS_CASES` file structure (header docstring + module-level
list of GoldenCase instances). Three cases:

- **GC-023 — Mild pediatric asthma (well-controlled).** 10yo with mild
  intermittent asthma on low-dose ICS. PEF normal. No ED visits. Eos
  count normal. Expected outcome: AUTO_APPROVED for ICS refill (a routine
  request). expected_branch: BRANCH_1_HIGH_CONFIDENCE.

- **GC-024 — Pediatric moderate Crohn's, ambiguous case.** 16yo with
  moderate Crohn's on adequate first-line therapy. CDAI score 180
  (moderate). One immunomodulator failure documented. Requesting biologic.
  Expected outcome: IN_REVIEW (the ambiguous case — clinical criteria
  borderline; pediatric age + complexity warrants specialist review).
  expected_branch: BRANCH_2_MEDICAL_DIRECTOR.

- **GC-025 — Severe pediatric atopic dermatitis on biologic.** 9yo with
  severe refractory atopic dermatitis. Failed topical steroids x6mo,
  failed cyclosporine. EASI score 35 (severe). Requesting dupilumab.
  Expected outcome: IN_REVIEW (different disease from existing GC-012;
  confirms the pediatric_complex escalation generalizes beyond asthma).
  expected_branch: BRANCH_2_MEDICAL_DIRECTOR.

### 3b. Wire into the live gate

In `tests/clinical/test_clinical_accuracy.py`, change the gate loop from
`for golden in GOLDEN_CASES + NEAR_MISS_CASES:` to
`for golden in GOLDEN_CASES + NEAR_MISS_CASES + PEDIATRIC_CASES:`.
Add the import.

### 3c. Live verification (informational only — chg-3 will change scoring)

```bash
set -a; source .env; set +a
python -m tests.clinical.investigate_case GC-023
python -m tests.clinical.investigate_case GC-024
python -m tests.clinical.investigate_case GC-025
```

At chg-2 HEAD (still using the keyword heuristic for pediatric_complex),
expect:
- GC-023 (mild): NOT pre-flight escalated (mild severity → keyword heuristic
  doesn't fire). Agent decision likely IN_REVIEW because the routine ICS
  refill won't match any aggressive auto-approve heuristic. **Score ≥ 3
  acceptable; the chg-3 score model will improve this.**
- GC-024 (moderate Crohn's): keyword heuristic fires on "moderate" →
  PEDIATRIC_COMPLEX → IN_REVIEW. Score ≥ 4 acceptable.
- GC-025 (severe AD): keyword heuristic fires on "severe" →
  PEDIATRIC_COMPLEX → IN_REVIEW. Score ≥ 4 acceptable.

Note: chg-2 alone is data only. The score-model behavioral change is chg-3.

### 3d. Commit

```bash
git add tests/clinical/pediatric_cases.py tests/clinical/test_clinical_accuracy.py
git commit -m "chg-2: add 3 pediatric cases (PEDIATRIC_CASES) for chg-3 complexity-score model"
```

---

## Step 4 — chg-3: complexity-score model

### 4a. Add complexity_score field to ClinicalCase

In `src/pacca/models/clinical.py`, add:

```python
complexity_score: int | None = Field(default=None, ge=1, le=5)
```

### 4b. Replace _check_pediatric_complex's keyword heuristic with numeric score

In `src/pacca/agents/clinical_risk_detector.py`:

```python
# iter-5 chg-3: complexity-score model. Integer 1-5 per the existing
# Settings schema (complexity_auto_approve_max=2, complexity_specialist_review_min=4).
# Weighted-sum heuristic with per-feature clinical rationale, not a data-fit
# model — only 4 pediatric data points exist (GC-012 + chg-2's 3 new cases).
# Honest framing: this is a heuristic in score-model clothing. The defensibility
# comes from per-feature rationale + matching the integer schema, not from
# data fitting.
PEDIATRIC_COMPLEXITY_THRESHOLD = 3  # one below specialist_review_min (4)

_PRIOR_FAILURE_RE = re.compile(r"(?:prior\s+failure|failed|inadequate.*response)", re.IGNORECASE)
_COMORBIDITY_HINTS = ("comorbid", "history of", "with concurrent")


def _compute_complexity_score(case: ClinicalCase) -> int:
    """
    Compute an integer 1-5 complexity score from case features.

    Weights (each capped at the schema's 1-5 range):
      - Age extremes (< 18 or > 75): +2
      - Severity: mild +0, moderate +1, moderate-to-severe +2, severe +2,
        critical +3
      - Prior therapy failures (2+ in notes): +1
      - Multiple comorbidities: +1
    """
    notes_blob = _evidence_blob(case)
    score = 0

    # Age extremes
    age = case.patient_age
    if age is None:
        age = _parse_age_from_notes(notes_blob)
    if age is not None and (age < 18 or age > 75):
        score += 2

    # Severity
    severity = (case.disease_severity or "").lower()
    if not severity:
        severity = (_parse_severity_from_notes(notes_blob) or "").lower()
    if "critical" in severity:
        score += 3
    elif "severe" in severity or "moderate-to-severe" in severity or "moderate to severe" in severity:
        score += 2
    elif "moderate" in severity:
        score += 1
    # mild contributes 0

    # Prior failures
    failure_matches = _PRIOR_FAILURE_RE.findall(notes_blob)
    if len(failure_matches) >= 2:
        score += 1

    # Comorbidities
    if any(hint in notes_blob.lower() for hint in _COMORBIDITY_HINTS):
        score += 1

    return max(1, min(score, 5))  # clamp to schema's 1-5 range


def _check_pediatric_complex(self, case, flags):
    # Pediatric age check unchanged
    notes_blob = _evidence_blob(case)
    age = case.patient_age
    if age is None:
        age = _parse_age_from_notes(notes_blob)
    if age is None or age >= self.PEDIATRIC_AGE_CUTOFF:
        return

    # iter-5 chg-3: numeric complexity score replaces the keyword heuristic.
    score = case.complexity_score if case.complexity_score is not None else _compute_complexity_score(case)
    if score < PEDIATRIC_COMPLEXITY_THRESHOLD:
        return

    flags.add(
        EscalationReason.PEDIATRIC_COMPLEX,
        f"Pediatric patient (age {age}) with complexity score {score} >= "
        f"threshold {PEDIATRIC_COMPLEXITY_THRESHOLD} — specialist review "
        f"required per policy.",
    )
```

### 4c. Unit tests for the new model

Create `tests/unit/test_complexity_score_model.py`. Cover:
- Each weight independently (age, severity tiers, failures, comorbidities)
- Boundary cases (exactly threshold, just below, capped at 5)
- The four real data points (GC-012, GC-023, GC-024, GC-025) — assert each
  computes the expected score.

### 4d. Live verification on all 4 pediatric cases

```bash
set -a; source .env; set +a
python -m tests.clinical.investigate_case GC-012  # 14yo severe asthma — score 4-5, IN_REVIEW
python -m tests.clinical.investigate_case GC-023  # 10yo mild — score 2, AUTO_APPROVED
python -m tests.clinical.investigate_case GC-024  # 16yo moderate Crohn's, 1 failure — score 3-4, IN_REVIEW
python -m tests.clinical.investigate_case GC-025  # 9yo severe AD, failures — score 4-5, IN_REVIEW
```

**✓ Verify:** chg-2's 3 new cases route correctly under the score model:
- GC-023 NOT pediatric_complex (score < 3); should reach DecisionAgent and AUTO_APPROVED
- GC-024 / GC-025 pediatric_complex escalates (score ≥ 3); IN_REVIEW.
- GC-012 unchanged — still escalates pediatric_complex (score should compute ≥ 3).

### 4e. Commit chg-3

```bash
git add src/pacca/models/clinical.py \
        src/pacca/agents/clinical_risk_detector.py \
        tests/unit/test_complexity_score_model.py
git commit -m "chg-3: complexity-score model in pediatric_complex check"
```

---

## Step 5 — chg-4: third H2 memory entry (asthma dupilumab)

### 5a. Add the entry to long_term_memory.md

Append a third `## Pattern:` section. Mirror the structure of the iter-3
NSCLC and iter-4 RA entries:

- Headline indication: severe eosinophilic asthma on dupilumab per GINA / NIST guidelines.
- Required criteria (5): severe persistent asthma diagnosis, inadequate control on high-dose ICS / LABA, eosinophilic phenotype (eos ≥ 300/µL OR FeNO ≥ 25), age ≥ 12, no contraindication.
- Anti-patterns (5): mild / moderate asthma, insufficient ICS trial, non-eosinophilic phenotype, age < 12, active TB / contraindication. Each `**Status: IN_REVIEW.** (Not DENIED.)`.
- Cost-check + pediatric-complex check interactions documented explicitly: memory does NOT override the iter-5 chg-3 pediatric_complex check.
- When applies / when not applies sections.

### 5b. PROMPT_REGISTRY v2.4 → v2.5

In `src/pacca/agents/prompts/templates.py`.

### 5c. Extend test_h2_memory_criterion_preservation.py

Add 4 test classes for the asthma entry: injection / criterion preservation /
anti-patterns / pediatric-complex interaction. Mirror the iter-3 NSCLC and
iter-4 RA test-class structure.

### 5d. Live verification on risk cases

```bash
set -a; source .env; set +a
python -m tests.clinical.investigate_case GC-012  # canonical severe pediatric asthma — must stay IN_REVIEW
python -m tests.clinical.investigate_case GC-023  # mild pediatric — must AUTO_APPROVE; memory must not over-fire
python -m tests.clinical.investigate_case GC-021  # NSCLC near-miss — must stay IN_REVIEW with 3 entries active
python -m tests.clinical.investigate_case GC-022  # NSCLC near-miss — must stay IN_REVIEW
```

**✓ Verify:** all 4 risk cases score ≥ 4. The asthma entry must not bleed
into NSCLC memory's discriminations.

### 5e. Commit chg-4

```bash
git add src/pacca/agents/decision_support/long_term_memory.md \
        src/pacca/agents/prompts/templates.py \
        tests/unit/test_h2_memory_criterion_preservation.py
git commit -m "chg-4: H2 memory — third entry (asthma dupilumab)"
```

---

## Step 6 — Live capture iter-5 baseline + closure

### 6a. Live baseline at iter-5 HEAD with --rollouts 2

```bash
python -m tests.clinical.capture_baseline --rollouts 2 \
    --tag harness-iter-5 \
    --out tests/clinical/baselines/iter-5-baseline.json
```

**✓ Verify:** all 20 GOLDEN_CASES still pass (≥ 90% aggregate; ideally 100%
preserved from iter-4).

### 6b. Documentation

- `harness/manifests/iter-5.json` — 4 chgs + verdicts on iter-4's 2 chgs
- `docs/ITERATIONS.md` iter-5 section — narrative
- `docs/DECISIONS.md` iter-5 section — per-chg entries + iteration verdict

### 6c. Mark ready, merge, tag

```bash
gh pr ready <N>
gh pr merge <N> --squash --delete-branch
git checkout main && git pull origin main
git tag -a harness-iter-5 HEAD -m "..."
git push origin harness-iter-5
```

---

## Final checklist

- [ ] Step 0: branch is `harness/iter-5`
- [ ] Step 1: draft PR open
- [ ] Step 2: chg-1 committed (tracing.py extra={} wrap)
- [ ] Step 3: chg-2 committed (3 new pediatric cases)
- [ ] Step 4: chg-3 committed (complexity-score model; live verification on all 4 pediatric cases)
- [ ] Step 5: chg-4 committed (asthma H2 entry; risk cases preserved)
- [ ] Step 6: iter-5 baseline captured; docs updated; PR merged; tag pushed

**One thing this runbook does NOT do:** generalize the complexity-score model
beyond pediatric cases. The chg-3 implementation uses the score in
`_check_pediatric_complex` only. A non-pediatric complexity check (using the
standard `complexity_specialist_review_min=4` threshold) is a separate
iteration when a non-pediatric case justifies it.
