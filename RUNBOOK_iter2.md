# iter-2 Runbook — finishing the eval-net hardening pass

This is a step-by-step guide to land iter-2 in your repo. It assumes you have the
files from this conversation downloaded (default: `~/Downloads`) and that your repo
is at `/Users/davidreed/David_Portfolio/pacca`.

**Conventions used below**
- `$REPO` means `/Users/davidreed/David_Portfolio/pacca`.
- Every command is run from the repo root unless stated. Open Terminal and do this once:
  ```bash
  cd /Users/davidreed/David_Portfolio/pacca
  ```
- After most steps there's a **✓ Verify** line — an expected result. If you don't see
  it, stop and check before moving on.
- Estimated time: ~25–40 min, most of it the live baseline run in Step 3.

**Order matters.** Step 2 (model) comes before Step 3 (baseline) on purpose: the
baseline is only meaningful for the exact model that produced it.

---

## Step 0 — Put the files in the repo

You downloaded these files from the chat. This script copies each to its correct
place and creates the one new folder/package. Paste the whole block:

```bash
cd /Users/davidreed/David_Portfolio/pacca
SRC=~/Downloads   # change if your downloads land elsewhere

# new test packages / folders
mkdir -p tests/harness tests/clinical/baselines docs_reconciliation harness/manifests
touch tests/harness/__init__.py

# Deliverable code (tests/clinical)
cp "$SRC/regression_gate.py"        tests/clinical/regression_gate.py
cp "$SRC/capture_baseline.py"       tests/clinical/capture_baseline.py
cp "$SRC/near_miss_cases.py"        tests/clinical/near_miss_cases.py
cp "$SRC/iter-1-baseline.json"      tests/clinical/baselines/iter-1-baseline.json   # placeholder; regenerated in Step 3

# Deliverable code (tests/harness)
cp "$SRC/doc_drift_guard.py"        tests/harness/doc_drift_guard.py
cp "$SRC/test_iter2_hardening.py"   tests/harness/test_iter2_hardening.py

# Manifests (overwrites schema + iter-1 with the fixed/patched versions)
cp "$SRC/change_manifest.schema.json" harness/manifests/change_manifest.schema.json
cp "$SRC/iter-2.json"                 harness/manifests/iter-2.json
cp "$SRC/iter-1.json"                 harness/manifests/iter-1.json

# Reconciliation notes
cp "$SRC/ITER0_ERRATUM.md"          docs_reconciliation/ITER0_ERRATUM.md
cp "$SRC/ITER0_ERRATUM_ENTRIES.md"  docs_reconciliation/ITER0_ERRATUM_ENTRIES.md

echo "Placement done."
```

**✓ Verify:**
```bash
ls tests/clinical/regression_gate.py tests/clinical/near_miss_cases.py \
   tests/harness/doc_drift_guard.py tests/harness/test_iter2_hardening.py \
   harness/manifests/iter-2.json
```
All five paths should print with no "No such file" error.

---

## Step 1 — Verify placement with the acceptance test

This runs the iter-2 validation suite I wrote. It proves the regression gate, the
near-miss cases, and the drift guard are all present and working.

```bash
python -m pytest tests/harness/test_iter2_hardening.py -v
```

**✓ Verify:** `19 passed`. (If imports fail, confirm `tests/harness/__init__.py`
exists and that you're running from the repo root.)

---

## Step 2 — Resolve the model (do this BEFORE the baseline)

Goal: make one model string the single source of truth and have all three places
agree (manifest, `settings.py`, `AgentConfig`). Right now `AgentConfig` silently
overrides settings, so the agents actually run `claude-sonnet-4-5-20250929` while
the records say `claude-sonnet-4-20250514`.

**2a. Pick the model string you want to tune against.** Either is fine; pick one and
be consistent. If you've been running real evals recently, you've been on
`claude-sonnet-4-5-20250929`, so the least-surprising choice is to standardize on
that. Call your choice `<MODEL>` below.

**2b. Make `AgentConfig` read from settings (one source of truth).** Open
`src/pacca/agents/base.py`. Change the import and the `AgentConfig` class:

Find:
```python
from pydantic import BaseModel
```
Change to:
```python
from pydantic import BaseModel, Field
```

Find:
```python
class AgentConfig(BaseModel):
    model: str = "claude-sonnet-4-5-20250929"
    temperature: float = 0.0
    max_tokens: int = 4096
```
Change to:
```python
class AgentConfig(BaseModel):
    # Single source of truth: settings.default_model (override via env DEFAULT_MODEL).
    model: str = Field(default_factory=lambda: get_settings().default_model)
    temperature: float = 0.0
    max_tokens: int = 4096
```
(`get_settings` is already imported at the top of `base.py`, so no other import is needed.)

**2c. Set the chosen string in `settings.py`.** Open `src/pacca/config/settings.py`,
find `default_model`, and set its default to `<MODEL>`:
```python
    default_model: str = Field(
        default="<MODEL>",
        description="Default Claude model for agents",
    )
```

**2d. Make the manifests agree.** In `harness/manifests/iter-1.json` and
`harness/manifests/iter-2.json`, set `"base_model": "<MODEL>"`.

**✓ Verify:** quick sanity check that the running model now equals settings:
```bash
python -c "from pacca.agents.base import AgentConfig; from pacca.config.settings import get_settings; \
print('AgentConfig:', AgentConfig().model); print('settings  :', get_settings().default_model)"
```
Both lines should print the same `<MODEL>`.

---

## Step 3 — Capture the real baseline scoreboard

This runs all 20 golden cases through the live pipeline + judge and writes the real
per-case scores (replacing my placeholder). It makes real API calls (~40 calls, a
few minutes, a few cents).

```bash
# Make your API key available to the shell (the agent client reads os.environ):
export ANTHROPIC_API_KEY="sk-ant-...your key..."
# (or, if it lives in your .env:  set -a; source src/pacca/.env; set +a )

python -m tests.clinical.capture_baseline \
    --tag harness-iter-1 \
    --out tests/clinical/baselines/iter-1-baseline.json
```
(The `--tag harness-iter-1` records that these scores represent the pre-H2
behavioral state — iter-2 changes nothing behavioral, so scores captured now are
that baseline. The file keeps its `iter-1-baseline.json` name.)

**✓ Verify:** you see 20 lines like `PASS GC-001: score=5`, then
`Wrote baseline (20 cases) -> tests/clinical/baselines/iter-1-baseline.json`.
Open the file and confirm real scores. If many cases FAIL, that's a finding worth
pausing on — tell me and we'll look before going further.

---

## Step 4 — Reconcile the docs + run the drift guard

**4a. Paste the erratum blocks.** Open `docs_reconciliation/ITER0_ERRATUM_ENTRIES.md`
and follow its header comments:
- Paste **Block 1** into `docs/DECISIONS.md` near the top (newest-first), and add the
  one index line it gives you to the `## Index` list.
- Paste **Block 2** into `docs/ITERATIONS.md` at the top of the
  `## iter-0 — Baseline Crystallization` section.

**4b. Fix the one *living-spec* reference.** Your append-only logs keep their old
`trajectory.py` references on purpose (the erratum supersedes them). But
`docs/EVALUATION.md` is a living spec — find any `src/pacca/observability/trajectory.py`
reference there and change it to describe the real instrumentation (OTel spans in
`src/pacca/agents/base.py`) or mark it deferred. To find every reference:
```bash
grep -rn "observability/trajectory.py" docs/
```

**4c. Run the drift guard against your real docs** (it skips the append-only logs):
```bash
python -c "from tests.harness.doc_drift_guard import find_dangling_references, format_report; \
print(format_report(find_dangling_references('docs', '.')))"
```
**✓ Verify:** `Doc-drift guard: PASSED`. If it still lists `EVALUATION.md`, you
missed a reference there — fix and re-run.

---

## Step 5 — Wire the near-miss cases into the live gate

So GC-021/022 actually run (and get judged) in your clinical gate. Open
`tests/clinical/test_clinical_accuracy.py`.

Add this import near the other `from tests.clinical...` imports:
```python
from tests.clinical.near_miss_cases import NEAR_MISS_CASES
```

In `test_full_pipeline_meets_accuracy_threshold`, find the gate loop:
```python
        for golden in GOLDEN_CASES:
```
Change it to:
```python
        for golden in GOLDEN_CASES + NEAR_MISS_CASES:
```
That's the only behavioral edit. (Leave `GOLDEN_CASES` at 20 and leave the
`== 20` integrity assertions alone — the near-miss cases run as a separate
concatenated set, protected by the accuracy gate's correct-outcome check.)

---

## Step 6 — Run the full suite

```bash
# Fast tests (no API calls):
python -m pytest tests/ -m "not clinical" -q

# The live clinical gate (real API calls; needs ANTHROPIC_API_KEY from Step 3):
python -m pytest tests/clinical/ -m clinical -q
```
**✓ Verify:** fast tests green; clinical gate passes (≥80%), and GC-021/022 show as
passing (the agent routes them to IN_REVIEW, not auto-approve). If GC-021/022 fail
now, that's a *pre-existing* discrimination weakness the new cases just exposed —
worth a look before iter-3.

---

## Step 7 — Commit per change, tag, and finalize the iter-1 verdict

Methodology: one commit per change, prefixed `chg-N:`, then tag the iteration.

```bash
# chg-1: schema extension
git add harness/manifests/change_manifest.schema.json
git commit -m "chg-1: add evaluation_harness constraint level to manifest schema"

# chg-2: regression gate + baseline + acceptance test
git add tests/clinical/regression_gate.py tests/clinical/capture_baseline.py \
        tests/clinical/baselines/iter-1-baseline.json tests/harness/
git commit -m "chg-2: add per-case regression gate, baseline scoreboard, validation suite"

# chg-3: near-miss cases + gate wiring
git add tests/clinical/near_miss_cases.py tests/clinical/test_clinical_accuracy.py
git commit -m "chg-3: add near-miss memory-trap golden cases; run them in the clinical gate"

# chg-4: doc-drift guard + erratum reconciliation + model reconciliation
git add tests/harness/doc_drift_guard.py docs/ docs_reconciliation/ \
        src/pacca/agents/base.py src/pacca/config/settings.py harness/manifests/iter-1.json
git commit -m "chg-4: doc-drift guard; reconcile iter-0 trajectory record and base_model"

# the manifest for the whole iteration
git add harness/manifests/iter-2.json
git commit -m "iter-2: eval-net hardening manifest"

# tag the iteration
git tag harness-iter-2
```

**Finalize the iter-1 verdict.** Now that the full suite is green at iter-2 HEAD with
zero behavioral change, the draft `keep` verdict is confirmed:
- In `harness/manifests/iter-2.json`, edit the `verdicts[0].notes` to drop the
  "DRAFT… confirm by running" caveat and state it's confirmed (suite green at
  iter-2 HEAD, zero behavioral delta).
- In `docs/DECISIONS.md`, replace the chg-1 *"Verdict (recorded after iter-2
  evaluation) — Pending…"* block with the `keep` verdict (outcome: keep; full suite
  green; zero behavioral delta vs. iter-0).

Then push (and the tag):
```bash
git push && git push --tags
```

---

## Final checklist

- [ ] Step 0: files placed; Step 1 acceptance test = 19 passed
- [ ] Step 2: AgentConfig/settings/manifests all show the same `<MODEL>`
- [ ] Step 3: real baseline written (20 real scores)
- [ ] Step 4: erratum pasted; `EVALUATION.md` fixed; drift guard PASSED
- [ ] Step 5: near-miss wired into the gate loop
- [ ] Step 6: fast tests green; clinical gate green; GC-021/022 pass
- [ ] Step 7: 5 commits, `harness-iter-2` tag, iter-1 verdict finalized, pushed

**One thing this runbook does NOT do:** wire the regression gate's `check_regression`
into the live gate as an assertion (so a future run is auto-compared to the
baseline). That belongs with iter-3's H2 change, where it first earns its keep —
ping me when you're there and I'll add it.
