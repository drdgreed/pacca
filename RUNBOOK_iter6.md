# iter-6 Runbook — structlog migration + adult complexity pre-flight + adult eval cases + first deny-pattern H2 entry

The cycle's **first iteration with a DENY outcome in institutional memory** (chg-4),
sequenced behind three lower-risk changes that build the foundation for it: an
instrumentation cleanup (chg-1), a deterministic adult-complexity escalation
branch (chg-2), and the eval data that makes that branch falsifiable (chg-3).
chg-2 → chg-3 has a real data-dependency direction (the branch ships first, the
data that exercises it ships second and is validated live). chg-4 is independent
of chg-1..3 but lands last, on a proven-green suite, because its failure mode
(over-denial) is the one that actually harms patients.

**Conventions:** `$REPO=/Users/davidreed/David_Portfolio/pacca`; commands run from
repo root; **✓ Verify** lines mark per-step expected results; branch + PR
workflow per `pacca_pr_workflow.md` (branch-and-PR, never direct-to-main); the
`reviewer` subagent (`.claude/agents/`) runs read-only **before every code
commit**; commits run the `.pre-commit-config.yaml` hooks (ruff / ruff-format /
mypy / check-json / PHI-secret guard) — **never `--no-verify`**.

**Estimated time:** ~3–3.5 hours (chg-1 ~15m, chg-2 ~45m, chg-3 ~45m + live
gate, chg-4 ~60m + pre/post live capture, closure ~40m).

**Base model:** `claude-sonnet-4-5-20250929` (unchanged this iteration).

**Design decisions locked at iteration start** (each verified against the code
during planning, not assumed):

- *chg-1 (tracing.py → structlog):* `src/pacca/config/logging.py` already exposes
  `get_logger(name) -> structlog.stdlib.BoundLogger` (line 98) and the rest of
  the codebase uses it. `tracing.py` is the last stdlib-`logging` holdout; iter-5
  chg-1 left it on `logging.getLogger` + `extra={…}` as a documented stopgap with
  a breadcrumb. chg-1 finishes the migration. Manifest `type: improvement`,
  `constraint_level: instrumentation` — **mirrors iter-5 chg-1's classification
  for the same file** (the `instrumentation` *type* exists in the schema too, but
  `improvement` matches the same-file precedent).
- *chg-2 (adult complexity pre-flight):* **separate `_check_adult_complex` method
  mirroring `_check_pediatric_complex`**, not a merged `_check_complexity`. One
  named check per policy branch, 1:1 with the `EscalationReason` enum (design doc
  §"Design choice"). **No orchestrator edit.** Routing was verified to be
  *generic*: `orchestrator._handle_pre_flight_escalation` (line 222) iterates
  `flags.reasons` and routes **any** fired flag to `IN_REVIEW` /
  `ReviewTier.HUMAN` (logged `4_7_pre_flight`). There is **no
  `{EscalationReason: branch}` lookup table anywhere in `src/`** — the design
  doc's "add the routing entry … exact site to be located during implementation"
  (line 110) resolves to *nothing to wire*: adding the enum member + the check is
  self-routing. "Branch 2" is audit narrative, not control flow.
- *chg-2 threshold:* reuses the iter-5 `_compute_complexity_score` **unchanged**
  and reads `settings.complexity_specialist_review_min` (=4) — the setting that
  named itself for specialist review finally gates a deterministic check. Adult
  18–75 must reach 4 (severe +2 **and** ≥2 failures +1 **and** comorbidity +1);
  elderly >75 reach 4 on age +2 + severe +2.
- *chg-3 (adult eval cases):* **parallel `ADULT_COMPLEXITY_CASES` list in a new
  `tests/clinical/adult_complexity_cases.py`; `GOLDEN_CASES` stays at exactly
  20** (mirrors iter-5 chg-2's `pediatric_cases.py`). IDs are **GC-101 / GC-102 /
  GC-103** — the dataset is currently at exactly GC-001…GC-100, so 101–103 is the
  next free monotonic block. **No `.pre-commit-config.yaml` change:** the mypy
  hook's `additional_dependencies` are *packages* (pydantic, pytest…), not test
  modules — the design's "add the module if mypy complains" caveat does not apply
  (a mypy error here would be a real bug to fix, not a dep to add).
- *chg-4 (first deny H2 entry):* anchor `GC-034` (off-label nivolumab,
  pancreatic adeno, no NCCN compendia) — **already committed in
  `tests/clinical/denial_cases.py`** on main; chg-4 does not create it. The entry
  **inverts** the approve-entry format: anti-patterns flip **DENIED → IN_REVIEW**
  (the over-denial guard), same safety direction as the existing entries
  (everything doubtful → IN_REVIEW), opposite starting verdict.
- *chg-4 scope — the with-compendia near-miss is NOT committed.* The design's
  Scope boundary enumerates exactly **two** deliberate dataset crossings (chg-3's
  parallel list; chg-4's pre-existing GC-034 anchor). A committed near-miss case
  (a hypothetical GC-104) would be an unenumerated **third** crossing. chg-4
  therefore verifies the over-denial guard via (a) deterministic memory-text
  tests asserting each guard line + `(Not DENIED.)` is present, and (b) the
  already-committed `GC-005` (psoriasis step-therapy) staying `IN_REVIEW` live,
  plus (c) an **ephemeral, non-committed** off-label-*with*-compendia probe.
  **Committing a permanent near-miss case is flagged as a discrete owner
  decision** (Step 5g) — do not commit it without sign-off.
- *Verdict vocabulary:* the manifest schema's `verdict.outcome` enum is
  **`keep` / `improve` / `rollback`** (`change_manifest.schema.json`). The design
  doc's looser "keep/revise/drop" wording is superseded by the schema.

**Execution order:** chg-1 (instrumentation, ~zero risk — clean green baseline) →
chg-2 (adult pre-flight code + deterministic unit tests, no live data yet) →
chg-3 (adult eval cases that exercise chg-2 end-to-end on the live gate) → chg-4
(deny memory entry — highest risk, lands last on a proven-green suite; the
GC-034 pre-entry baseline is captured *before* the entry is added).

**Predicted fixes:**
- chg-1 → none. Instrumentation finish; behavior identical (structured fields go
  to the same log records via a cleaner API).
- chg-2 → none predicted to flip in the golden-20. Risk cases: the chg-3 adult
  cases (escalating must fire, boundary must not); regression watch: existing
  pediatric routing (GC-012, GC-023/024/025) untouched, and **no golden-20 adult
  case that currently auto-approves may start escalating**.
- chg-3 → none. Data + harness wiring. Risk: GC-101/GC-103 route `IN_REVIEW` via
  `ADULT_COMPLEX`; GC-102 routes `AUTO_APPROVED` (must-not-escalate guard).
- chg-4 → **unknown in advance, by design.** Whether the entry *fixes* a wrong
  baseline answer on GC-034 or merely *hardens consistency* depends on how the
  agent handles GC-034 today — captured in Step 5a *before* the entry lands, and
  reported truthfully in the manifest. Risk cases: GC-034 (must DENY with a cited
  compendia basis), GC-005 (must stay IN_REVIEW — the headline over-denial
  guard), the ephemeral with-compendia near-miss (must stay IN_REVIEW).

---

## Step 0 — Pre-flight

```bash
git rev-parse --abbrev-ref HEAD     # expect: harness/iter-6
git log --oneline main..HEAD        # expect: 1 commit — "docs(iter-6): add iter-6 design spec"
git tag --points-at $(git rev-parse main)   # informational
git tag | grep iter | sort          # expect: harness-iter-0 … harness-iter-5 (no iter-6 yet)
set -a; source .env; set +a         # ANTHROPIC_API_KEY for the live gate
```

**Capture the real baseline — do not hardcode a count.** The deterministic suite
is the merge gate; record its actual passing total at branch start:

```bash
make test 2>&1 | tail -5            # record the exact "N passed" number here: ____
```

**✓ Verify:** `make test` is fully green at branch start. Write the count into
the iter-6 manifest `summary` (Step 6) as the pre-iteration baseline — the
manifest claims a number you observed, never a number you assumed.

**Untracked-file guard.** Three untracked files must **NEVER** be committed in
this iteration. Always stage by explicit path; never `git add -A` / `git add .`:

```bash
git status --short
#  ?? docs/PRODUCTION_READINESS.md   <- do NOT commit
#  ?? docs/images/hero.png           <- do NOT commit
#  ?? src/pacca/_init_users.py       <- do NOT commit
```

---

## Step 1 — Open the draft PR

```bash
git add RUNBOOK_iter6.md
git commit -m "iter-6: add runbook (spec only)"
git push -u origin harness/iter-6
gh pr create --draft --base main --head harness/iter-6 \
    --title "iter-6: structlog migration + adult complexity pre-flight + adult eval cases + first deny H2 entry" \
    --body "Draft until 4 chgs land and verification gates green. Sequenced low→high risk: chg-1 instrumentation, chg-2 escalation_branch, chg-3 evaluation_harness, chg-4 long_term_memory (first DENY entry)."
```

---

## Step 2 — chg-1: tracing.py → structlog

Lowest-risk chg first — finishes the migration iter-5 chg-1 deferred. Touches
**one source file + one test file**.

### 2a. Write the failing test (RED)

In `tests/unit/test_retry_and_tracing.py`, add at module scope (top of file, with
the other imports) and a new test class:

```python
import logging as _stdlib_logging

from pacca.config import tracing as tracing_module


class TestTracingStructlogMigration:
    """iter-6 chg-1: tracing.py's module logger must be structlog, not stdlib."""

    def test_logger_is_structlog_not_stdlib(self) -> None:
        # RED pre-migration: tracing_module.logger is a logging.Logger.
        # GREEN post-migration: it is a structlog BoundLogger (or lazy proxy),
        # neither of which is an instance of logging.Logger.
        assert not isinstance(tracing_module.logger, _stdlib_logging.Logger)

    def test_configure_tracing_console_path_accepts_kwargs(self) -> None:
        # Exercises the structured-kwargs call sites (logger.info(event, key=val))
        # on the console path. Must not raise after the migration.
        tracing_module._tracing_configured = False
        tracing_module.configure_tracing(
            service_name="pacca-test", endpoint=None, enabled=True
        )
        tracing_module._tracing_configured = False  # reset for other tests
```

Run it — confirm RED:

```bash
python -m pytest tests/unit/test_retry_and_tracing.py::TestTracingStructlogMigration -v
```

**✓ Verify:** `test_logger_is_structlog_not_stdlib` **FAILS** (the logger is still
`logging.getLogger(__name__)`). This proves the test discriminates.

### 2b. Edit tracing.py (GREEN)

Five exact edits in `src/pacca/config/tracing.py`:

1. **Line 46** — swap the import:
   ```python
   # FROM:
   import logging
   # TO:
   from .logging import get_logger
   ```
2. **Line 58** — swap the logger factory:
   ```python
   # FROM:
   logger = logging.getLogger(__name__)
   # TO:
   logger = get_logger(__name__)
   ```
3. **Lines 113–117** — delete the iter-5 breadcrumb comment block entirely (the
   `# iter-5 chg-3: wrap structured fields in extra={} …` paragraph). It described
   the stopgap this chg removes.
4. **Line 118** — unwrap the kwargs:
   ```python
   # FROM:
   logger.info("otel_exporter_configured", extra={"endpoint": endpoint})
   # TO:
   logger.info("otel_exporter_configured", endpoint=endpoint)
   ```
5. **Lines 120–126 and line 135** — unwrap the remaining two `extra={…}` calls:
   ```python
   # FROM:
   logger.warning(
       "otel_otlp_exporter_unavailable",
       extra={
           "detail": "opentelemetry-exporter-otlp-proto-http not installed; "
           "falling back to console exporter"
       },
   )
   # TO:
   logger.warning(
       "otel_otlp_exporter_unavailable",
       detail="opentelemetry-exporter-otlp-proto-http not installed; "
       "falling back to console exporter",
   )

   # FROM:
   logger.info("otel_tracing_configured", extra={"service_name": service_name})
   # TO:
   logger.info("otel_tracing_configured", service_name=service_name)
   ```

The two `logger.debug("otel_tracing_disabled")` / `logger.debug("otel_console_exporter_configured")`
calls (lines 93, 132) take no kwargs — **leave them unchanged**.

### 2c. Verify GREEN + no stdlib-logging residue

```bash
python -m pytest tests/unit/test_retry_and_tracing.py::TestTracingStructlogMigration -v
python -m mypy src/pacca/config/tracing.py
grep -nE "import logging|logging\.(getLogger|Logger|info|warning|debug)|extra=\{" src/pacca/config/tracing.py
make test
```

**✓ Verify:**
- The new test class **PASSES**.
- mypy clean.
- The `grep` returns **nothing** — no residual stdlib-`logging` usage **and no
  leftover `extra={` wrapper** (also confirms the now-unused `import logging` is
  gone, which `ruff --exit-non-zero-on-fix` would otherwise flag at commit). Note:
  the file has **three** `extra={}` calls (lines 118 / 123 / 135), not the "4" the
  design spec states — the spec over-counts a kwarg-less `debug` call. Grepping
  the wrapper makes the exact count moot: it proves all are unwrapped.
- `make test` green at the Step 0 baseline count (no regressions; +2 new tests).

### 2d. Reviewer subagent (read-only, before commit)

Dispatch the `reviewer` subagent on the unstaged diff (HIPAA + security review).
**✓ Verify:** no PHI in logs (the structured fields are `endpoint`,
`service_name`, `detail` — all infrastructure, no patient data); no new secrets;
no behavioral regression flagged.

### 2e. Commit

```bash
git add src/pacca/config/tracing.py tests/unit/test_retry_and_tracing.py
git commit -m "chg-1: migrate tracing.py to structlog get_logger (finishes iter-5 chg-1 stopgap)"
```

---

## Step 3 — chg-2: adult complexity pre-flight check

Touches **two source files** (`enums.py`, `clinical_risk_detector.py`) + **one
test file**. **No orchestrator edit** (generic routing — see locked decisions).

### 3a. Write the failing tests (RED)

In `tests/unit/test_complexity_score_model.py`, add a new test class. It uses the
existing `_make_case(notes="", **kwargs)` helper (line 29), which passes
`patient_age` / `disease_severity` / `complexity_score` as structured
`ClinicalCase` fields — so these tests are **deterministic** (no prose-parser
dependency). Add the import of the detector instance and `EscalationReason` is
already imported (line 24):

```python
class TestAdultComplexCheck:
    """iter-6 chg-2: deterministic adult specialist-review escalation."""

    def _fire(self, **kwargs: Any) -> bool:
        from pacca.agents.clinical_risk_detector import EscalationFlags

        detector = ClinicalRiskDetector()
        flags = EscalationFlags()
        detector._check_adult_complex(_make_case(**kwargs), flags)
        return EscalationReason.ADULT_COMPLEX in flags.reasons

    def test_adult_severe_with_failures_and_comorbidity_fires_at_threshold(self) -> None:
        # adult +0, severe +2, 2 failures +1, comorbidity +1 = 4 == threshold(4)
        notes = (
            "Refractory to first agent; failed trial of second agent. "
            "Comorbid type 2 diabetes."
        )
        assert self._fire(notes=notes, patient_age=58, disease_severity="severe") is True

    def test_adult_severe_only_does_not_fire(self) -> None:
        # adult +0, severe +2 = 2 < 4 — the must-not-escalate boundary
        assert self._fire(notes="", patient_age=49, disease_severity="severe") is False

    def test_elderly_severe_fires(self) -> None:
        # age>75 +2, severe +2 = 4 == threshold
        assert self._fire(notes="", patient_age=81, disease_severity="severe") is True

    def test_pediatric_age_does_not_fire_adult_check(self) -> None:
        # age < 18 is gated out of the ADULT path (pediatric check owns it)
        assert self._fire(notes="", patient_age=10, disease_severity="severe") is False

    def test_structured_score_below_threshold_does_not_fire(self) -> None:
        # structured complexity_score=3 short-circuits the compute path; 3 < 4
        assert self._fire(notes="", patient_age=58, complexity_score=3) is False

    def test_structured_score_at_threshold_fires(self) -> None:
        assert self._fire(notes="", patient_age=58, complexity_score=4) is True

    def test_missing_age_does_not_fire(self) -> None:
        # no structured age and no parseable age → cannot confirm adult → no fire
        assert self._fire(notes="No age stated.", disease_severity="critical") is False


class TestGoldenTwentyAdultComplexRegression:
    """No golden-20 case that currently AUTO_APPROVES may start escalating
    on the new adult check (the chg-2 regression guard)."""

    def test_no_auto_approved_golden_case_newly_fires_adult_complex(self) -> None:
        from pacca.agents.clinical_risk_detector import EscalationFlags
        from tests.clinical.golden_cases import ExpectedOutcome

        detector = ClinicalRiskDetector()
        for g in GOLDEN_CASES:
            if g.expected_outcome is not ExpectedOutcome.AUTO_APPROVED:
                continue
            case = _make_case(notes=g.clinical_notes)
            flags = EscalationFlags()
            detector._check_adult_complex(case, flags)
            assert EscalationReason.ADULT_COMPLEX not in flags.reasons, (
                f"{g.case_id} auto-approves today but the adult check would "
                f"escalate it — chg-2 must not regress the golden-20."
            )
```

Run — confirm RED:

```bash
python -m pytest tests/unit/test_complexity_score_model.py::TestAdultComplexCheck -v
```

**✓ Verify:** every `TestAdultComplexCheck` test **FAILS** with
`AttributeError: 'ClinicalRiskDetector' object has no attribute '_check_adult_complex'`.
This proves the tests target the not-yet-written method.

### 3b. Add the enum member (GREEN, part 1)

In `src/pacca/models/enums.py`, insert immediately after the `PEDIATRIC_COMPLEX`
docstring (after line 119), matching the enum's house style:

```python
    ADULT_COMPLEX = "adult_complex"
    """
    Adult patient (age >= 18) whose deterministic complexity score reaches the
    specialist-review threshold (settings.complexity_specialist_review_min, =4).
    Escalated because the same policy logic that flags complex pediatric cases
    applies to complex adults — specialist review is warranted regardless of how
    confident the clinical-eligibility check is. The classification agent's
    LLM-self-assessed complexity flag remains advisory; this pre-flight is
    authoritative and reproducible.
    """
```

### 3c. Add the method + wire into evaluate() (GREEN, part 2)

In `src/pacca/agents/clinical_risk_detector.py`, add the method **immediately
after `_check_pediatric_complex`** (after line 719), mirroring it exactly. **Do
not introduce a new age constant** — reuse the existing `PEDIATRIC_AGE_CUTOFF`
(`= 18`, detector:670). The pediatric/adult boundary is one fact; one shared
constant keeps the two checks provably mutually exclusive (pediatric fires
`< cutoff`, adult fires `>= cutoff`) and unable to drift apart. The settings
import is lazy (inside the method), matching `_check_high_cost` (line 651):

```python
    # ── Branch 2: Adult complexity (iter-6 chg-2 — generalizes the score model) ─
    # Shares PEDIATRIC_AGE_CUTOFF (=18) with the pediatric check above — one
    # boundary constant, so the two age-gated checks can never drift apart.

    def _check_adult_complex(
        self,
        case: ClinicalCase,
        flags: EscalationFlags,
    ) -> None:
        """
        Escalate to specialist review when the patient is an adult (age >= 18)
        AND the complexity score reaches settings.complexity_specialist_review_min.

        Mirrors _check_pediatric_complex but for the adult population and the
        standard (higher) specialist-review threshold. Reuses the iter-5
        _compute_complexity_score unchanged — no model change — and reuses the same
        PEDIATRIC_AGE_CUTOFF boundary, so the two checks are mutually exclusive by
        construction (pediatric < 18, adult >= 18 — no double-fire, no drift).

        Data source order for the score:
          1. ClinicalCase.complexity_score (structured — preferred)
          2. Computed from case features via _compute_complexity_score
        """
        from ..config.settings import get_settings

        notes_blob = _evidence_blob(case)

        age = case.patient_age
        if age is None:
            age = _parse_age_from_notes(notes_blob)
        if age is None or age < self.PEDIATRIC_AGE_CUTOFF:
            return

        score = (
            case.complexity_score
            if case.complexity_score is not None
            else _compute_complexity_score(case)
        )
        threshold = int(get_settings().complexity_specialist_review_min)
        if score < threshold:
            return

        flags.add(
            EscalationReason.ADULT_COMPLEX,
            f"Adult patient (age {age}) with complexity score {score} >= "
            f"specialist-review threshold {threshold} — specialist review "
            f"required per policy regardless of clinical eligibility verification.",
        )
```

Wire it into `evaluate()` **immediately after** the `_check_pediatric_complex`
call at line 450:

```python
        self._check_high_cost(case, flags)
        self._check_pediatric_complex(case, flags)
        self._check_adult_complex(case, flags)   # iter-6 chg-2
```

### 3d. Verify GREEN

```bash
python -m pytest tests/unit/test_complexity_score_model.py -v
python -m mypy src/pacca/agents/clinical_risk_detector.py src/pacca/models/enums.py
make test
```

**✓ Verify:** `TestAdultComplexCheck` (7) + `TestGoldenTwentyAdultComplexRegression`
(1) all **PASS**; mypy clean; `make test` green at baseline + 8 new tests; the
existing pediatric tests are untouched.

### 3e. Reviewer subagent + commit

Dispatch the `reviewer` subagent on the diff. **✓ Verify:** PHI-clean (the flag
detail contains only age + integer score — no name/MRN/DOB); no secrets; mirrors
the established pre-flight pattern.

```bash
git add src/pacca/models/enums.py \
        src/pacca/agents/clinical_risk_detector.py \
        tests/unit/test_complexity_score_model.py
git commit -m "chg-2: add ADULT_COMPLEX pre-flight (_check_adult_complex, threshold=complexity_specialist_review_min)"
```

---

## Step 4 — chg-3: adult complexity eval cases

Creates **one new file** + wires it into the harness. **No `.pre-commit` change.**

### 4a. Create tests/clinical/adult_complexity_cases.py

Three synthetic cases (HIPAA: no real PHI). Notes are worded so the **live**
detector's parsers extract the intended signals — in particular
`_PRIOR_FAILURE_RE` (detector:295) matches `failed (trial|to|of)`, `refractory`,
`intolerance`, `inadequate response` — **not** a bare "failed X" — and
`_COMORBIDITY_HINTS` (detector:301) matches `comorbid` / `history of` /
`concurrent`. Score arithmetic is annotated per case.

```python
"""
Adult-complexity eval cases — iter-6 chg-3.

WHY THESE EXIST
---------------
chg-2 added a deterministic ADULT_COMPLEX pre-flight (age >= 18 AND complexity
score >= settings.complexity_specialist_review_min=4). A pre-flight branch with
no data behind it is an unfalsifiable assertion. These cases give the branch
real data points across its decision boundary: two that MUST escalate (one
mid-adult, one geriatric) and one that MUST NOT (the must-not-escalate guard,
mirroring iter-5's GC-023 pediatric guard).

Parallel list — GOLDEN_CASES stays at exactly 20. IDs continue the monotonic
allocation (dataset is at GC-100; these are GC-101..GC-103).

Score arithmetic (parser path; weights per _compute_complexity_score):
  GC-101  adult 58, severe(+2), >=2 failures(+1), comorbidity(+1)       = 4  FIRE
  GC-102  adult 49, severe(+2), no failures, no comorbidity             = 2  SPARE
  GC-103  elderly 81(+2), severe(+2), no failures, no comorbidity-hint  = 4  FIRE
"""

from __future__ import annotations

from tests.clinical.golden_cases import (
    EscalationBranch,
    ExpectedOutcome,
    GoldenCase,
)

ADULT_COMPLEXITY_CASES: list[GoldenCase] = [
    # ─────────────────────────────────────────────────────────────────────────
    # GC-101 — Escalating anchor. Adult, severe, refractory, comorbid; cheap drug
    # (so high_cost does NOT pre-empt) and a standard agent (not experimental).
    # ─────────────────────────────────────────────────────────────────────────
    GoldenCase(
        case_id="GC-101",
        title="Add-on spironolactone for severe treatment-resistant hypertension",
        diagnosis_code="I10",
        diagnosis_description="Essential (primary) hypertension",
        procedure_code="J0000",  # placeholder oral generic; low cost
        procedure_description="Spironolactone 25 mg oral, add-on therapy",
        clinical_notes=(
            "58-year-old male with severe treatment-resistant hypertension, "
            "office BP 168/104 despite three-drug therapy at maximally tolerated "
            "doses. Refractory to lisinopril; failed trial of amlodipine; "
            "inadequate response to hydrochlorothiazide. Comorbid type 2 diabetes "
            "mellitus and stage 3 chronic kidney disease (eGFR 52). Requesting "
            "add-on spironolactone per resistant-hypertension guidance. "
            "Spironolactone is a low-cost generic; estimated annual drug cost "
            "well under $1,000. Not investigational; standard fourth-line agent."
        ),
        guidelines_context=(
            "ACC/AHA resistant-hypertension guidance: confirmed resistant "
            "hypertension (uncontrolled on three agents including a diuretic at "
            "optimal doses) supports add-on mineralocorticoid-receptor antagonist "
            "(spironolactone) as preferred fourth-line therapy. Single "
            "authoritative source; no conflicting guideline."
        ),
        expected_outcome=ExpectedOutcome.IN_REVIEW,
        expected_branch=EscalationBranch.BRANCH_2_MEDICAL_DIRECTOR,
        reasoning_must_include=["complexity", "specialist", "severe"],
        reasoning_must_not_include=["experimental", "denied"],
        clinical_rationale=(
            "The therapy itself is guideline-concordant and low-cost — on clinical "
            "merits alone an agent might auto-approve. But the case clears the "
            "deterministic adult-complexity bar (severe + refractory + comorbid = "
            "score 4 = specialist-review threshold), so policy routes it to "
            "specialist review regardless of clinical eligibility. This is the "
            "GC-010 lesson generalized to adults: policy escalation must be "
            "deterministic, not left to the agent's confidence."
        ),
        judge_scoring_criteria=(
            "Score highly if the rationale identifies the complexity-driven "
            "specialist-review escalation (severe + refractory + comorbidity) and "
            "routes IN_REVIEW. Penalize for auto-approval (the deterministic "
            "pre-flight must win over clinical confidence) or for DENIED (nothing "
            "here warrants denial)."
        ),
    ),
    # ─────────────────────────────────────────────────────────────────────────
    # GC-102 — Must-not-escalate boundary. Adult, severe, but NO failures and NO
    # comorbidity → score 2 < 4. A clear surgical indication that should auto-
    # approve. Mirrors iter-5's GC-023 pediatric guard.
    # ─────────────────────────────────────────────────────────────────────────
    GoldenCase(
        case_id="GC-102",
        title="Laparoscopic cholecystectomy for severe acute cholecystitis",
        diagnosis_code="K81.0",
        diagnosis_description="Acute cholecystitis",
        procedure_code="47562",
        procedure_description="Laparoscopic cholecystectomy",
        clinical_notes=(
            "49-year-old female with severe acute cholecystitis: RUQ pain, "
            "Murphy's sign positive, WBC 15.2, ultrasound shows gallbladder wall "
            "thickening with pericholecystic fluid and gallstones. First "
            "presentation; no prior episodes. No other active medical problems. "
            "Requesting laparoscopic cholecystectomy within the recommended "
            "early-surgery window."
        ),
        guidelines_context=(
            "Tokyo Guidelines: early laparoscopic cholecystectomy is first-line "
            "for acute cholecystitis in an operative candidate. Clear indication; "
            "single authoritative source."
        ),
        expected_outcome=ExpectedOutcome.AUTO_APPROVED,
        expected_branch=EscalationBranch.BRANCH_1_AUTO_APPROVE,
        reasoning_must_include=["acute cholecystitis", "laparoscopic"],
        reasoning_must_not_include=["experimental", "denied", "specialist review required"],
        clinical_rationale=(
            "Severe disease, but a single severity point (score 2) is below the "
            "adult specialist-review threshold (4): no refractory failures, no "
            "comorbidity. The indication is textbook and the procedure is "
            "guideline-concordant, so the case should auto-approve. This proves "
            "the adult check does not over-escalate every severe adult case — "
            "severity alone is not enough."
        ),
        judge_scoring_criteria=(
            "Score highly for AUTO_APPROVED with a rationale citing the clear "
            "acute-cholecystitis indication. Penalize for IN_REVIEW driven by a "
            "spurious complexity escalation (severity alone must not trip the "
            "adult threshold) or for any DENIED."
        ),
    ),
    # ─────────────────────────────────────────────────────────────────────────
    # GC-103 — Geriatric escalating. Elderly(+2) + severe(+2) = 4. No failures,
    # and "secondary to CKD" is deliberately NOT a comorbidity-hint phrase, so the
    # score lands at exactly 4 (not 5). Moderate-cost agent (not high_cost).
    # ─────────────────────────────────────────────────────────────────────────
    GoldenCase(
        case_id="GC-103",
        title="Epoetin alfa for severe symptomatic anemia of chronic kidney disease",
        diagnosis_code="D63.1",
        diagnosis_description="Anemia in chronic kidney disease",
        procedure_code="J0885",
        procedure_description="Epoetin alfa injection (non-ESRD)",
        clinical_notes=(
            "81-year-old male with severe symptomatic anemia secondary to chronic "
            "kidney disease (non-dialysis). Hemoglobin 8.4 g/dL with exertional "
            "dyspnea and fatigue limiting activities of daily living. Iron studies "
            "repleted. Requesting epoetin alfa per anemia-of-CKD guidance. "
            "Estimated annual cost is moderate, below the high-cost threshold."
        ),
        guidelines_context=(
            "KDIGO anemia-in-CKD guidance: ESA therapy (epoetin alfa) is "
            "appropriate for symptomatic anemia of CKD after iron repletion, with "
            "individualized hemoglobin targets. Single authoritative source."
        ),
        expected_outcome=ExpectedOutcome.IN_REVIEW,
        expected_branch=EscalationBranch.BRANCH_2_MEDICAL_DIRECTOR,
        reasoning_must_include=["complexity", "specialist", "severe"],
        reasoning_must_not_include=["experimental", "denied"],
        clinical_rationale=(
            "Geriatric age (>75) plus severe disease reaches the adult complexity "
            "threshold (score 4) even without refractory failures or a documented "
            "comorbidity — appropriate, because age-extreme plus severe anemia in "
            "an 81-year-old genuinely warrants specialist review of the ESA "
            "risk/benefit (thrombotic risk, target individualization). Routes "
            "IN_REVIEW via the deterministic pre-flight."
        ),
        judge_scoring_criteria=(
            "Score highly for IN_REVIEW with a rationale identifying the "
            "age-extreme + severity complexity escalation. Penalize for "
            "auto-approval (geriatric severe anemia should not auto-approve on an "
            "ESA) or for DENIED."
        ),
    ),
]
```

> If a live route in 4d disagrees with the annotated score (e.g. the live age or
> severity parser does not extract a signal from the prose), **adjust the case's
> notes wording** until the parser sees it — do not change
> `_compute_complexity_score` (that model is chg-2's, frozen) and do not weaken
> the test. The score arithmetic above is the contract; the prose must satisfy it.

### 4b. Write the size test (RED)

In `tests/clinical/test_clinical_accuracy.py`, mirror
`test_expansion_dataset_has_eleven_cases` (line 146). Add inside
`TestGoldenDatasetIntegrity`:

```python
    def test_adult_complexity_dataset_has_three_cases(self) -> None:
        """
        ADULT_COMPLEXITY_CASES = 3 iter-6 chg-3 cases (GC-101 escalating,
        GC-102 must-not-escalate boundary, GC-103 geriatric escalating). Size is
        encoded so drift is caught by integrity.
        """
        assert len(ADULT_COMPLEXITY_CASES) == 3, (
            f"Expected 3 adult-complexity cases, found {len(ADULT_COMPLEXITY_CASES)}."
        )
```

Run — confirm RED (NameError, not yet imported):

```bash
python -m pytest "tests/clinical/test_clinical_accuracy.py::TestGoldenDatasetIntegrity::test_adult_complexity_dataset_has_three_cases" -v
```

**✓ Verify:** FAILS with `NameError: name 'ADULT_COMPLEXITY_CASES' is not defined`.

### 4c. Wire into the harness (GREEN)

Four edits in `tests/clinical/test_clinical_accuracy.py`:

1. **Import** — add alphabetically in the case-import block (it belongs right
   after the `ambiguous_completeness` import at line 47, keeping the block sorted):
   ```python
   from tests.clinical.adult_complexity_cases import ADULT_COMPLEXITY_CASES
   ```
2. **Registry** — add to `ALL_SUPPLEMENTARY_LISTS` (the tuple at line 81; the
   file's own comment at line 79 says "add … an entry below when a new case file
   lands"). Append after `DEPTH_EXTENSION_CASES`:
   ```python
       DEPTH_EXTENSION_CASES,
       ADULT_COMPLEXITY_CASES,
   )
   ```
3. **Cross-list collision check** — extend the line-137 expression so the new IDs
   are covered by the monotonic-uniqueness invariant:
   ```python
           c.case_id
           for c in (
               GOLDEN_CASES + NEAR_MISS_CASES + PEDIATRIC_CASES
               + EXPANSION_CASES + ADULT_COMPLEXITY_CASES
           )
   ```
4. **Live clinical gate** — extend the line-611 loop so the new cases are
   evaluated end-to-end against the live model:
   ```python
           for golden in (
               GOLDEN_CASES + NEAR_MISS_CASES + PEDIATRIC_CASES
               + EXPANSION_CASES + ADULT_COMPLEXITY_CASES
           ):
   ```
   Add a one-line comment above the loop matching the existing breadcrumb style:
   `# + ADULT_COMPLEXITY_CASES (iter-6 chg-3 — adult pre-flight validation set).`

### 4d. Verify — deterministic suite then live gate

```bash
make test                                  # deterministic: size test + collision green
set -a; source .env; set +a
python -m tests.clinical.investigate_case GC-101   # score 4 -> ADULT_COMPLEX -> IN_REVIEW
python -m tests.clinical.investigate_case GC-102   # score 2 -> no pre-flight -> AUTO_APPROVED
python -m tests.clinical.investigate_case GC-103   # score 4 -> ADULT_COMPLEX -> IN_REVIEW
```

**✓ Verify:**
- `make test` green (size + collision integrity pass; `GOLDEN_CASES` still 20).
- GC-101: pre-flight fires `adult_complex`; routed `IN_REVIEW`.
- GC-102: **no** pre-flight fires; agent reaches a decision and `AUTO_APPROVED`.
- GC-103: pre-flight fires `adult_complex`; routed `IN_REVIEW`.
- (If a route disagrees, adjust the case prose per the 4a note, re-run, repeat.)

### 4e. Confirm investigate_case resolves the new IDs

If `investigate_case GC-101` errors with "case not found," its case-aggregation
needs the new list (iter-5 chg-2 touched this file for the same reason):

```bash
grep -n "ADULT_COMPLEXITY_CASES\|ALL_CASES\|_ALL\b\|PEDIATRIC_CASES" tests/clinical/investigate_case.py
```

Add `ADULT_COMPLEXITY_CASES` to its aggregation if absent; otherwise no change.
(Stage `tests/clinical/investigate_case.py` in 4g only if you edited it.)

### 4f. Reviewer subagent

Dispatch `reviewer` on the diff. **✓ Verify:** all three cases are synthetic (no
real PHI); rationales cite guideline bodies, not patient specifics; data-only +
test-wiring change with no production-code impact.

### 4g. Commit

```bash
git add tests/clinical/adult_complexity_cases.py \
        tests/clinical/test_clinical_accuracy.py
# add tests/clinical/investigate_case.py ONLY if edited in 4e
git commit -m "chg-3: add ADULT_COMPLEXITY_CASES (GC-101/102/103) + harness wiring for chg-2"
```

---

## Step 5 — chg-4: first deny-pattern H2 memory entry (centerpiece)

Touches `long_term_memory.md` + `templates.py` (`PROMPT_REGISTRY`) + the H2 test
file. **Highest-risk change** — first DENY outcome in memory; the whole entry is
built to guard against over-denial.

### 5a. Capture the GC-034 PRE-ENTRY baseline (before any edit)

This makes the manifest's fix-vs-hardening claim honest. Record the agent's
current handling of GC-034 *without* the new memory entry:

```bash
set -a; source .env; set +a
python -m tests.clinical.investigate_case GC-034   # record status: AUTO_APPROVED / IN_REVIEW / DENIED -> ____
```

**✓ Verify:** the pre-entry status is recorded (write it down for Step 6's
manifest). If GC-034 already DENIES, chg-4 *hardens consistency*; if it does not,
chg-4 *fixes* a wrong baseline. The manifest reports whichever is true — no
"fixes X" claim is made in advance of this evidence.

### 5b. Write the failing tests (RED)

In `tests/unit/test_h2_memory_criterion_preservation.py`:

**(i) Convert the exact-version test to a floor test** (mirroring the
`is_at_least_v24` pattern at lines 201–214). Replace
`test_decision_support_prompt_version_bumped_to_v25` (lines 345–347) with:

```python
    def test_decision_support_prompt_version_is_at_least_v25(self) -> None:
        """
        v2.5+ signals the asthma (3rd) entry was active. The iter-5 chg-4 floor;
        the canonical current version is asserted by the iter-6 chg-4 test
        (test_decision_support_prompt_version_bumped_to_v26). Guards against
        accidental downgrade below v2.5.
        """
        rendered = load_agent_prompt("decision_support", "DecisionSupportAgent")
        import re

        match = re.search(r"Prompt version: v2\.(\d+)", rendered)
        assert match is not None
        minor = int(match.group(1))
        assert minor >= 5, f"prompt version v2.{minor} predates asthma entry (floor: v2.5)"
```

**(ii) Add the new canonical exact-version test + a four-entry presence test**, in
a new `TestOffLabelDenyMemoryInjection` class:

```python
class TestOffLabelDenyMemoryInjection:
    def test_decision_support_prompt_contains_deny_entry(self) -> None:
        rendered = load_agent_prompt("decision_support", "DecisionSupportAgent")
        assert "Off-label oncology biologic without NCCN compendia support" in rendered

    def test_decision_support_prompt_version_bumped_to_v26(self) -> None:
        rendered = load_agent_prompt("decision_support", "DecisionSupportAgent")
        assert "Prompt version: v2.6" in rendered

    def test_all_four_h2_entries_present(self) -> None:
        rendered = load_agent_prompt("decision_support", "DecisionSupportAgent")
        assert "First-line pembrolizumab for metastatic NSCLC" in rendered
        assert "First-line biologic DMARD for seropositive RA" in rendered
        assert "Dupilumab for severe eosinophilic asthma" in rendered
        assert "Off-label oncology biologic without NCCN compendia support" in rendered
```

**(iii) Add criterion-preservation + over-denial-guard + interaction tests**:

```python
class TestOffLabelDenyCriterionPreservation:
    """The 5 denial criteria must appear verbatim in the rendered prompt."""

    def test_lists_off_label_for_tumor_type(self) -> None:
        rendered = load_agent_prompt("decision_support", "DecisionSupportAgent")
        assert "off-label for the tumor type" in rendered.lower()

    def test_lists_no_nccn_compendia_listing(self) -> None:
        rendered = load_agent_prompt("decision_support", "DecisionSupportAgent")
        assert "NCCN Drugs & Biologics Compendium" in rendered
        assert "no Category 1, 2A, or 2B" in rendered

    def test_lists_no_tissue_agnostic_qualifier(self) -> None:
        rendered = load_agent_prompt("decision_support", "DecisionSupportAgent")
        assert "MSI-high" in rendered and "TMB-high" in rendered and "NTRK" in rendered

    def test_lists_not_trial_enrolled(self) -> None:
        rendered = load_agent_prompt("decision_support", "DecisionSupportAgent")
        assert "not enrolled in a clinical trial" in rendered.lower()

    def test_lists_cms_policy_alignment(self) -> None:
        rendered = load_agent_prompt("decision_support", "DecisionSupportAgent")
        assert "CMS" in rendered and "no compendia" in rendered.lower()


class TestOffLabelDenyOverDenialGuards:
    """The over-denial guard: each anti-pattern FLIPS deny -> IN_REVIEW, and the
    governing 'never auto-deny on doubt' rule is present. This is the safety
    property of the entire iteration."""

    def test_any_compendia_listing_flips_to_in_review(self) -> None:
        rendered = load_agent_prompt("decision_support", "DecisionSupportAgent")
        assert "any NCCN compendia listing" in rendered
        assert "(Not DENIED.)" in rendered

    def test_tissue_agnostic_marker_flips_to_in_review(self) -> None:
        rendered = load_agent_prompt("decision_support", "DecisionSupportAgent")
        assert "tissue-agnostic" in rendered.lower()

    def test_active_trial_flips_to_in_review(self) -> None:
        rendered = load_agent_prompt("decision_support", "DecisionSupportAgent")
        assert "active or pending clinical-trial enrollment" in rendered

    def test_incomplete_documentation_flips_to_in_review(self) -> None:
        rendered = load_agent_prompt("decision_support", "DecisionSupportAgent")
        assert "ambiguous or incomplete compendia documentation" in rendered

    def test_governing_rule_never_auto_deny_on_doubt(self) -> None:
        rendered = load_agent_prompt("decision_support", "DecisionSupportAgent")
        assert "Any uncertainty -> IN_REVIEW" in rendered or "Any uncertainty → IN_REVIEW" in rendered
        assert "never auto-deny on doubt" in rendered.lower()
        assert "absence of evidence is not evidence of ineligibility" in rendered.lower()

    def test_valid_denial_requires_cited_basis_and_trial_redirect(self) -> None:
        rendered = load_agent_prompt("decision_support", "DecisionSupportAgent")
        assert "cite the specific compendia-absence basis" in rendered.lower()
        assert "recommend clinical-trial enrollment" in rendered.lower()


class TestOffLabelDenyInteraction:
    def test_names_gc034_anchor(self) -> None:
        rendered = load_agent_prompt("decision_support", "DecisionSupportAgent")
        assert "GC-034" in rendered

    def test_does_not_sweep_step_therapy_into_deny(self) -> None:
        # GC-005 (psoriasis step-therapy) is explicitly NOT this pattern.
        rendered = load_agent_prompt("decision_support", "DecisionSupportAgent")
        assert "step-therapy" in rendered.lower()
        assert "is NOT this deny pattern" in rendered

    def test_does_not_override_pre_flight_checks(self) -> None:
        rendered = load_agent_prompt("decision_support", "DecisionSupportAgent")
        assert "does not override" in rendered.lower()
        assert "adult_complex" in rendered  # names the iter-6 chg-2 pre-flight
```

**(iv) Tighten the four-entry `(Not DENIED.)` count.** Update the existing
`test_every_asthma_anti_pattern_routes_to_in_review_not_denied` (lines 395–401):
the comment now reflects four entries and the deny entry's over-denial guards add
more `(Not DENIED.)` markers, so raise the floor:

```python
    def test_every_anti_pattern_routes_to_in_review_not_denied(self) -> None:
        """All H2 entries' anti-patterns say '(Not DENIED.)'. Four entries now:
        NSCLC (5) + RA (6) + asthma (5) + off-label-deny over-denial guards (5)
        = 21. The deny entry INVERTS direction (deny -> IN_REVIEW) but uses the
        same marker, so the count only grows."""
        rendered = load_agent_prompt("decision_support", "DecisionSupportAgent")
        not_denied_count = rendered.count("(Not DENIED.)")
        assert not_denied_count >= 21, (
            f"expected at least 21 (Not DENIED.) clarifications across four "
            f"H2 entries, found {not_denied_count}."
        )
```

Also update the floor-test docstrings at lines 39–46 (`is_at_least_v23`) and
201–207 (`is_at_least_v24`) to point at `bumped_to_v26` as the new canonical
version test (one-word edits — replace the referenced test name).

Run — confirm RED:

```bash
python -m pytest tests/unit/test_h2_memory_criterion_preservation.py -v -k "OffLabelDeny or bumped_to_v26 or is_at_least_v25 or routes_to_in_review"
```

**✓ Verify:** the new `TestOffLabelDeny*` tests and `bumped_to_v26` **FAIL** (the
entry and version bump don't exist yet); `is_at_least_v25` passes (v2.5 ≥ v2.5).

### 5c. Add the deny entry to long_term_memory.md (GREEN, part 1)

Append a fourth `## Pattern:` section to
`src/pacca/agents/decision_support/long_term_memory.md`, **inverting** the
approve-entry format. Use ASCII `->` (the file mixes `->`/`→`; the tests above
accept either where it matters, but match the surrounding entries' style):

```markdown
---

## Pattern: Off-label oncology biologic without NCCN compendia support

**Headline deny-class:** An off-label oncology drug requested for a tumor type
where the NCCN Drugs & Biologics Compendium lists no supported indication and no
tissue-agnostic biomarker independently qualifies it. Anchored on GC-034
(off-label nivolumab for MSI-stable pancreatic adenocarcinoma). This is the
deny-mirror of the very first memory entry (first-line pembrolizumab for NSCLC) —
same NCCN oncology body, opposite verdict.

> **This is the only entry whose shortcut outcome is DENIED.** Its failure mode —
> over-denial — is the one that harms patients. The anti-patterns below are not
> edge notes; they are the core of the entry. When in doubt, you do NOT deny.

**Required criteria for denial — ALL must be explicitly documented:**

1. The requested drug is **off-label for the tumor type** in question (not an
   approved or compendia-listed indication for this histology).
2. The **NCCN Drugs & Biologics Compendium** lists the indication at **no
   Category 1, 2A, or 2B** level (i.e., it is absent from the compendium for this
   use).
3. **No** tissue-agnostic qualifier is present that would independently justify
   coverage — specifically **no MSI-high, no TMB-high, and no NTRK fusion**
   (present *or untested* counts as "not established"; see anti-patterns).
4. The patient is **not enrolled in a clinical trial** (trial enrollment is the
   appropriate path for off-label use and changes the disposition).
5. **CMS NCD / commercial policy aligns**: the recognized compendia pathway has
   **no compendia** entry, therefore no coverage basis. State the alignment
   explicitly.

**Anti-patterns — these FLIP the outcome from DENIED to IN_REVIEW (the
over-denial guard):**

When ANY of the following is present, the deny shortcut does NOT apply and the
case **routes to IN_REVIEW for human clinical judgment** — the agent must NOT
auto-deny. The status field of your output must be `IN_REVIEW` in all such cases.

- **Any NCCN compendia listing** for the indication, even Category 2B → coverage
  basis may exist; a human weighs it. **Status: IN_REVIEW.** (Not DENIED.)
- **Any tissue-agnostic marker** — MSI-high, TMB-high, or an NTRK fusion (or a
  documented intent to test for them that is not yet resolved) → a
  histology-independent indication may apply. **Status: IN_REVIEW.** (Not DENIED.)
- **Active or pending clinical-trial enrollment**, or an expanded-access /
  compassionate-use context → the off-label question is being handled through the
  correct channel. **Status: IN_REVIEW.** (Not DENIED.)
- **Ambiguous or incomplete compendia documentation** — the record does not
  clearly establish the compendia absence → you cannot deny on an incomplete
  record. **Status: IN_REVIEW.** (Not DENIED.)
- **A plausible evolving-evidence argument** (recent practice-changing data not
  yet reflected in the compendium) → a human evaluates currency. **Status:
  IN_REVIEW.** (Not DENIED.)

**Governing rule (read this before denying):** Any uncertainty -> IN_REVIEW.
Never auto-deny on doubt. The **absence of evidence is not evidence of
ineligibility** — a gap in the record is a reason to review, not to deny. A valid
denial must (a) **cite the specific compendia-absence basis** (name the compendium
and the missing indication) AND (b) **recommend clinical-trial enrollment** as the
redirect. A denial that does neither is not a valid denial — route IN_REVIEW
instead.

**When the shortcut applies:** DENIED — but only when **all five required
criteria are explicitly documented** AND **none of the anti-patterns is present**.
The rationale MUST cite the specific compendia-absence basis by name and recommend
the trial-enrollment redirect. If you cannot write that cited rationale, you do
not have a denial — route IN_REVIEW.

**When the shortcut DOES NOT apply:** treat the case as a standard evaluation.
This entry **does not override pre-flight checks** — if any pre-flight escalation
fires (e.g. `experimental_treatment`, `high_cost`, `pediatric_complex`,
`adult_complex`, `prior_denial_same_service`), that routing wins and this entry is
moot. And note the boundary with the approve-side step-therapy pattern: a denial
for **incomplete step therapy** (e.g. GC-005, psoriasis — topical/systemic trial
not yet complete) **is NOT this deny pattern**; that is a standard step-therapy
review that routes IN_REVIEW, not an off-label-compendia denial. Do not sweep
step-therapy cases into this entry.
```

### 5d. Bump PROMPT_REGISTRY v2.5 → v2.6 (GREEN, part 2)

In `src/pacca/agents/prompts/templates.py`, the `DecisionSupportAgent` entry
(lines 51–60):

```python
    "DecisionSupportAgent": {
        "version": "v2.6",
        "description": "Frontline UM Nurse — guideline alignment + confidence scoring + institutional memory (H2, 4 entries)",
        "changed_in": "v2.6 (iter-6 chg-4): H2 memory — FIRST deny-pattern entry "
        "(off-label oncology without NCCN compendia support; GC-034 anchor) with "
        "over-denial guards (any compendia listing / tissue-agnostic biomarker / "
        "active trial / incomplete documentation each flip DENIED -> IN_REVIEW). "
        "v2.5 (iter-5 chg-4): H2 memory — third entry, dupilumab "
        # ... (keep the remainder of the existing changelog string unchanged) ...
```

Change only: `version` v2.5→v2.6; `description` "(H2, 3 entries)"→"(H2, 4
entries)"; **prepend** the v2.6 changelog sentence to the existing `changed_in`
string (do not delete the v2.5/v2.4/v2.3/v2.2 history).

### 5e. Verify GREEN

```bash
python -m pytest tests/unit/test_h2_memory_criterion_preservation.py -v
make test
```

**✓ Verify:** all H2 tests pass — the new `TestOffLabelDeny*` classes,
`bumped_to_v26`, `is_at_least_v25`, the four-entry presence test, and the
`>= 21` `(Not DENIED.)` count; `make test` green. If the count assertion is off,
**adjust the count to the observed number of guard lines, not below 21** (and only
after confirming each guard line is present and ends `(Not DENIED.)`).

### 5f. Live verification — deny correctly, guard against over-denial

```bash
set -a; source .env; set +a
python -m tests.clinical.investigate_case GC-034   # MUST be DENIED, with a cited compendia basis + trial redirect
python -m tests.clinical.investigate_case GC-005   # MUST stay IN_REVIEW (step-therapy not swept into deny)
```

**✓ Verify:** GC-034 → `DENIED` and the rationale **names the NCCN compendia
absence and recommends trial enrollment** (a bare "denied" without the cited basis
is a fail — the entry requires the cited rationale); GC-005 → `IN_REVIEW`.

**Ephemeral over-denial probe (NOT committed).** Construct a throwaway
off-label-*with*-compendia variant and confirm the guard flips it to IN_REVIEW —
without adding a case to the dataset. Use a scratch file outside the committed
case lists (e.g. a temporary `/tmp` snippet or an interactive
`investigate_case`-style call) that mirrors GC-034 but adds "**NCCN compendia
lists this indication at Category 2B**":

**✓ Verify:** the with-compendia variant routes `IN_REVIEW` (the over-denial guard
fires). Delete the scratch artifact — do **not** `git add` it.

> **Owner decision (flagged, not taken):** committing a permanent
> with-compendia near-miss case (a GC-104) would give this guard a standing
> regression test, but it is an **unenumerated third dataset crossing** beyond the
> design's Scope boundary. Leaving it ephemeral honors the locked scope. If the
> owner wants the standing guard, that is a deliberate scope expansion to approve
> separately — do not commit GC-104 in this iteration without sign-off.

### 5g. Reviewer subagent + commit

Dispatch `reviewer` on the diff. **✓ Verify:** the entry cites guideline bodies
only (no PHI); the over-denial guards are present and unambiguous; the deny
shortcut is gated behind "all five criteria documented AND no anti-pattern";
`PROMPT_REGISTRY` history preserved.

```bash
git add src/pacca/agents/decision_support/long_term_memory.md \
        src/pacca/agents/prompts/templates.py \
        tests/unit/test_h2_memory_criterion_preservation.py
git commit -m "chg-4: H2 memory — first deny-pattern entry (off-label oncology, GC-034) with over-denial guards; PROMPT_REGISTRY v2.6"
```

---

## Step 6 — Live capture iter-6 baseline + closure

### 6a. Capture the iter-6 baseline at HEAD

```bash
set -a; source .env; set +a
python -m tests.clinical.capture_baseline --rollouts 2 \
    --tag harness-iter-6 \
    --out tests/clinical/baselines/iter-6-baseline.json
```

**✓ Verify:** the 20 `GOLDEN_CASES` hold (≥ 90% aggregate; ideally the iter-5
pass rate is preserved); GC-101/GC-103 route `IN_REVIEW`, GC-102 `AUTO_APPROVED`,
GC-034 `DENIED`, GC-005 `IN_REVIEW`.

### 6b. Write the iter-6 manifest

Create `harness/manifests/iter-6.json`, mirroring `iter-5.json`'s shape
(top-level keys: `iteration`, `iteration_tag`, `iso_date`, `author`,
`base_model`, `previous_iteration_tag`, `summary`, `changes`, `verdicts`). Use the
exact enum values the schema enforces.

**`changes`** (4 entries — each with the full key set: `id`, `type`,
`description`, `files`, `failure_pattern`, `root_cause`, `evidence`,
`predicted_fixes`, `risk_cases`, `constraint_level`, `why_this_component`,
`phi_impact`, `audit_relevant`, `rollback_plan`):

| id | type | constraint_level | one-line description |
|----|------|------------------|----------------------|
| chg-1 | `improvement` | `instrumentation` | tracing.py → structlog `get_logger`; finishes iter-5 chg-1 stopgap |
| chg-2 | `new` | `escalation_branch` | `ADULT_COMPLEX` pre-flight; `_check_adult_complex` at threshold `complexity_specialist_review_min`=4 |
| chg-3 | `new` | `evaluation_harness` | `ADULT_COMPLEXITY_CASES` (GC-101/102/103); GOLDEN_CASES stays 20 |
| chg-4 | `new` | `long_term_memory` | first deny-pattern H2 entry (off-label oncology, GC-034) + over-denial guards; PROMPT_REGISTRY v2.6 |

- chg-2 `why_this_component`: deterministic policy escalation belongs in the
  pre-flight detector, not the LLM's per-run self-assessment (GC-010 lineage).
  `phi_impact: "none"`, `audit_relevant: true`, `rollback_plan: "git revert; enum
  member + method revert together; complexity_score field stays optional, no
  migration"`. **Record explicitly that no orchestrator edit was required** (the
  design's deferred routing site does not exist — routing is generic).
- chg-4 `failure_pattern` / `root_cause`: fill from the Step 5a baseline — state
  truthfully whether GC-034 already denied (then this is *hardening*) or did not
  (then this is a *fix*). `evidence`: cite the Step 5a pre-entry status and the
  Step 6a post-entry `DENIED` with cited basis. `risk_cases`: GC-034 (deny
  correctly), GC-005 (stay IN_REVIEW), synthetic with-compendia near-miss (stay
  IN_REVIEW — verified ephemerally, not committed).

**`verdicts`** (4 — on iter-5's four changes; `outcome` ∈ {`keep`,`improve`,
`rollback`}; each with `change_id`, `previous_iteration_tag:"harness-iter-5"`,
`outcome`, `verified_fixes`, `missed_fixes`, `false_predicted_fixes`,
`verified_risks`, `unforeseen_regressions`, `notes`):

| change_id | outcome | notes |
|-----------|---------|-------|
| chg-1 | `improve` | iter-5's `extra={…}` stdlib wrap held green through iter-5; iter-6 chg-1 supersedes it with structlog — intent (structured logging) preserved, mechanism improved. |
| chg-2 | `keep` | pediatric eval set reused unchanged; iter-6 chg-3 mirrors its pattern for adults. |
| chg-3 | `keep` | `_compute_complexity_score` reused **unchanged** by iter-6 chg-2's adult path — the model generalized without modification, the strongest possible "keep." |
| chg-4 | `keep` | the 3rd H2 entry (asthma) is stable; iter-6 chg-4 adds a 4th without displacing it. |

> Note: iter-5 `chg-1`/`chg-3` were themselves `type: improvement`; iter-5
> `chg-2`/`chg-4` were `type: new`. Verdicts attach to the change *id*, so all
> four iter-5 ids get a verdict here regardless of their original type.

Validate:

```bash
python -m pytest tests/harness -q          # schema + manifest validation
python -m json.tool harness/manifests/iter-6.json > /dev/null   # syntax (check-json hook also runs at commit)
```

**✓ Verify:** `tests/harness` green (iter-6.json validates against
`change_manifest.schema.json`).

### 6c. Narrative docs

- `docs/ITERATIONS.md` — insert the iter-6 narrative **after** the iter-5
  narrative and **before** the trailing "Format reference" / "On narrative
  honesty" footer, following the 6-part format (Header block / What shipped /
  Trajectory before→after / Eval delta / Verdict summary / Reflection). Include
  the honest fix-vs-hardening finding for chg-4 from Step 5a. State the
  "what success looks like for iter-6" prediction was met (or note any miss).
- `docs/DECISIONS.md` — per-chg entries (incl. the no-orchestrator-edit finding,
  the no-committed-near-miss scope call) + the iteration verdict block.

```bash
git add harness/manifests/iter-6.json docs/ITERATIONS.md docs/DECISIONS.md \
        tests/clinical/baselines/iter-6-baseline.json
git commit -m "iter-6: manifest (4 chgs + iter-5 verdicts), baseline, ITERATIONS/DECISIONS narrative"
```

### 6d. Mark ready, merge, tag

```bash
make test                                  # final green gate before merge
gh pr ready <N>
gh pr merge <N> --squash --delete-branch
git checkout main && git pull origin main
git tag -a harness-iter-6 -m "iter-6: structlog migration + adult complexity pre-flight + adult eval cases + first deny-pattern H2 entry (over-denial guarded)"
git push origin harness-iter-6
```

**✓ Verify:** `make test` green; PR squash-merged; `harness-iter-6` tag pushed;
`git tag | grep iter` now lists through `harness-iter-6`.

---

## Final checklist

- [ ] Step 0: branch is `harness/iter-6`; `make test` baseline count recorded; untracked-file guard noted (3 files NOT committed)
- [ ] Step 1: draft PR open
- [ ] Step 2: chg-1 committed (tracing.py → structlog; no stdlib-logging residue; reviewer passed)
- [ ] Step 3: chg-2 committed (`ADULT_COMPLEX` + `_check_adult_complex`; **no orchestrator edit**; golden-20 regression guard green; reviewer passed)
- [ ] Step 4: chg-3 committed (GC-101/102/103; GOLDEN_CASES still 20; live gate routes 4/2/4 correctly; reviewer passed)
- [ ] Step 5: chg-4 committed (deny H2 entry + over-denial guards; v2.6; GC-034 pre-entry baseline captured *before* edit; GC-034→DENIED with cited basis; GC-005→IN_REVIEW; ephemeral near-miss→IN_REVIEW; reviewer passed)
- [ ] Step 6: iter-6 baseline captured; manifest validates (4 chgs + 4 iter-5 verdicts); ITERATIONS/DECISIONS updated; PR merged; `harness-iter-6` tagged

**Two things this runbook deliberately does NOT do:**
1. **Commit a with-compendia near-miss case (GC-104).** The over-denial guard is
   verified by memory-text tests + the GC-005 live guard + an ephemeral probe. A
   standing near-miss regression case is a flagged owner decision, not part of
   this iteration's locked scope.
2. **Generalize complexity escalation beyond the age-gated pediatric/adult
   split.** chg-2 reuses `_compute_complexity_score` unchanged; any non-age-based
   complexity routing is a separate iteration.
