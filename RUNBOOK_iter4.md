# iter-4 Runbook — Second H2 memory entry + dead-code deletion

This is a step-by-step guide to land iter-4 in your repo. iter-4 is a
**small-but-substantive iteration**: one new H2 memory entry (RA biologic
after DMARD failure) and one long-deferred dead-code cleanup
(`decision_agent.py`, 330 lines, queued since iter-1). Both fit cleanly
into one PR and share the same risk profile (low — well-bounded changes,
both with prior design notes in place).

**Conventions used below**
- `$REPO` means `/Users/davidreed/David_Portfolio/pacca`.
- Every command is run from the repo root. Open Terminal and do this once:
  ```bash
  cd /Users/davidreed/David_Portfolio/pacca
  ```
- After most steps there's a **✓ Verify** line — an expected result.
- **Estimated time:** ~1.5–2 hours (chg-1 is ~1h including live verification,
  chg-2 is ~15m, closure docs ~30m).
- **Branch + PR workflow:** work happens on `harness/iter-4` (already created);
  the PR opens early as draft and is marked ready when verification gates
  are green.

**Scope and design decisions locked at iteration start:**

- **chg-1 (RA biologic memory entry):** follows the forward design notes
  from [`docs/findings/H2-memory-iteration-1.md`](docs/findings/H2-memory-iteration-1.md):
  explicit status routing on every anti-pattern, risk-case enumeration,
  criterion-preservation test extension, PROMPT_REGISTRY version bump.
  Entry must be RA-specific (not generic "biologic") because related
  conditions (psoriasis, Crohn's, PsA) have *different* criteria — the
  memory must not over-fire on those cases.
- **chg-2 (decision_agent.py deletion):** the 330-line dead-code file
  recorded as a deferred finding in `harness/manifests/iter-1.json` (chg-1
  `evidence` block) and re-noted in every iter narrative since. Imports
  scan confirms zero importers. Deletion is the work; verification is
  the full test suite.
- **iter-3 thread 3 (complexity-score model for pediatric_complex)** is
  **NOT in iter-4 scope.** Dataset survey showed only 1 pediatric case
  exists (GC-012). A complexity-score discriminator needs contrastive
  data; we'd need a small data-only iteration (call it iter-5) that adds
  2–3 pediatric cases (mild, moderate ambiguous, severe in different
  condition) before a score-model iteration can be empirically founded.

**Predicted_fixes for the iteration:**
- chg-1 → none predicted to flip. Risk cases: GC-010 (must stay IN_REVIEW
  via cost; memory should support the clinical reasoning, not replace it),
  GC-005 (psoriasis adalimumab — must NOT over-fire), GC-017 (PsA
  biologic — must NOT over-fire), GC-016 (Crohn's adalimumab — must NOT
  over-fire).
- chg-2 → none. Cleanup only.

---

## Step 0 — Pre-flight

```bash
git status                # On branch harness/iter-4
git log --oneline -3      # Top commit is e4791a9 (iter-3 squash merge)
git tag --points-at HEAD~ # harness-iter-3
set -a; source .env; set +a
python -c "import os; print('key set:', bool(os.environ.get('ANTHROPIC_API_KEY')))"
```

**✓ Verify:** branch is `harness/iter-4`; iter-3 tag is on the parent commit;
API key loaded.

---

## Step 1 — Open the draft PR early

```bash
git add RUNBOOK_iter4.md
git commit -m "iter-4: add runbook (spec only; no behavioral change)"
git push -u origin harness/iter-4
gh pr create --draft --base main --head harness/iter-4 \
    --title "iter-4: RA biologic H2 memory entry + decision_agent.py deletion" \
    --body "Draft until chg-1 + chg-2 land and verification gates green."
```

**✓ Verify:** PR opens as DRAFT.

---

## Step 2 — chg-2 first (cheap and unblocks): delete decision_agent.py

Doing the cleanup before the memory entry because (a) it's cheap, (b) it
de-risks chg-1 by ensuring the import graph is clean before we extend it,
and (c) iter-1 narrative explicitly endorsed bundling the deletion into
either thread.

### 2a. Confirm zero importers

```bash
grep -rn "from .decision_agent\|from pacca.agents.decision_agent\|import decision_agent" \
    --include="*.py" .
grep -rn "DecisionSupportAgent" --include="*.py" . | grep -v __pycache__
```

**✓ Verify:**
- First grep: empty (no import statements).
- Second grep: only string-literal matches in tests (e.g.
  `tests/clinical/...` expecting `name() == "DecisionSupportAgent"`).
  The actual class returning that string is `DecisionAgent` in
  `src/pacca/agents/decision.py` — those tests don't import the dead file.

### 2b. Delete the file

```bash
git rm src/pacca/agents/decision_agent.py
python -m pytest tests/unit tests/harness -q
```

**✓ Verify:** all 192 tests still pass.

### 2c. Commit chg-2

```bash
git commit -m "chg-2: delete src/pacca/agents/decision_agent.py (dead code, queued since iter-1)"
```

---

## Step 3 — chg-1: RA biologic H2 memory entry

### 3a. Add the second entry to long_term_memory.md

Append a new `## Pattern:` section to
`src/pacca/agents/decision_support/long_term_memory.md`. Use the same
five-part format the iter-3 NSCLC pembrolizumab entry established:

1. Headline indication
2. Required criteria (ALL must be explicitly documented)
3. Anti-patterns (each with explicit `**Status: IN_REVIEW.** (Not DENIED.)`)
4. When the shortcut applies (outcome + rationale-content requirement)
5. When the shortcut DOES NOT apply (fallback to standard evaluation)

Sketch of the RA entry:

```markdown
## Pattern: First-line biologic DMARD for seropositive RA after conventional DMARD failure

**Headline indication:** Seropositive rheumatoid arthritis with documented
failure of 2+ conventional DMARDs (typically methotrexate + at least one
other), moderate-to-severe disease activity, requesting first-line biologic
DMARD (e.g. abatacept, adalimumab, etanercept, infliximab, tocilizumab).

**Required criteria — ALL must be explicitly documented:**

1. Diagnosis is rheumatoid arthritis with seropositive markers:
   RF positive AND/OR anti-CCP positive, documented in the chart.
2. Disease activity is moderate-to-severe (DAS28 ≥ 3.2, or CDAI / SDAI
   equivalents documented).
3. Step therapy: failure of **2 or more** conventional DMARDs, each at
   adequate dose for adequate duration (typically methotrexate ≥ 3 months
   PLUS at least one other conventional DMARD).
4. Requested agent is on the ACR-recommended biologic list for RA.
5. No active uncontrolled infection or contraindication to immunosuppression.

**Anti-patterns — disqualify the shortcut, route to human review:**

- Only ONE conventional DMARD tried → insufficient step therapy.
  **Status: IN_REVIEW.** (Not DENIED.)
- Seronegative RA → different treatment paradigm; combination conventional
  DMARDs typically preferred first. **Status: IN_REVIEW.** (Not DENIED.)
- Mild disease activity (DAS28 < 3.2) → biologic generally not indicated.
  **Status: IN_REVIEW.** (Not DENIED.)
- Inadequate trial duration on prior DMARDs (< 3 months on methotrexate)
  → cannot establish failure. **Status: IN_REVIEW.** (Not DENIED.)
- Active infection / pregnancy / live vaccine within 30 days →
  contraindication review. **Status: IN_REVIEW.** (Not DENIED.)

**When the shortcut applies:** AUTO_APPROVE at high confidence (≥ 0.95)
*conditional on* the policy-level cost check. The rationale MUST explicitly
cite seropositive status (RF and/or anti-CCP), the specific DMARDs tried
with durations, disease activity score, and that the requested agent is
ACR-recommended for RA.

**Important interaction with policy escalation:** if the estimated annual
cost exceeds the configured HIGH_COST_THRESHOLD, `ClinicalRiskDetector`'s
pre-flight `high_cost_check` (iter-3 chg-1) will route the case to
IN_REVIEW regardless of clinical eligibility. The memory does not override
that — the memory's role is to give the agent the clinical-reasoning
support to articulate "criteria met BUT cost escalates per policy" rather
than "criteria met → approve" (which would be wrong on GC-010).

**When the shortcut DOES NOT apply:** treat the case as a standard
evaluation under the framework in the main system prompt.
```

### 3b. Bump PROMPT_REGISTRY DecisionSupportAgent v2.3 → v2.4

In `src/pacca/agents/prompts/templates.py`, update the
DecisionSupportAgent entry's `version` and `changed_in` fields. The
version bump signals via the audit log that a new memory entry was
active for any decisions made from this point forward.

### 3c. Extend the criterion-preservation tests

Add a new test class to `tests/unit/test_h2_memory_criterion_preservation.py`
covering the RA entry's required criteria and anti-patterns. Mirror the
NSCLC entry's test class structure exactly:
- `TestRABiologicMemoryInjection` — entry loads, version bumped to v2.4
- `TestRABiologicCriterionPreservation` — each required criterion present
- `TestRABiologicAntiPatternsPreserved` — each anti-pattern present with
  Status: IN_REVIEW routing
- (Don't repeat the byte-identity-for-MD-agent tests; they're already in
  the file and unchanged by adding a second entry.)

### 3d. Live verification on risk cases

```bash
set -a; source .env; set +a
python -m tests.clinical.investigate_case GC-010   # must stay IN_REVIEW via cost; memory supports the reasoning
python -m tests.clinical.investigate_case GC-005   # cross-condition: psoriasis adalimumab — must NOT auto-approve
python -m tests.clinical.investigate_case GC-017   # cross-condition: PsA biologic — must NOT auto-approve
python -m tests.clinical.investigate_case GC-016   # cross-condition: Crohn's adalimumab — currently AUTO_APPROVED; must remain so
```

**✓ Verify (the risk-case gate):**

- **GC-010 (RA abatacept, $288K cost):** `status=IN_REVIEW` via the
  `high_cost` pre-flight escalation. The agent's rationale should
  acknowledge "clinical criteria met" AND "cost threshold triggers
  escalation." Score ≥ 4. If the agent now AUTO_APPROVES because the
  memory triggered, the memory is overriding the cost guard — stop and
  weaken the memory's "when shortcut applies" clause.
- **GC-005 (psoriasis adalimumab, step therapy not met):**
  `status=IN_REVIEW`. If memory fires, it's over-firing on a different
  disease — narrow the memory's headline to RA-only.
- **GC-017 (PsA biologic, inadequate step therapy):** `status=IN_REVIEW`.
  Same risk as GC-005.
- **GC-016 (Crohn's adalimumab, adequate step therapy):**
  `status=AUTO_APPROVED`. Different disease but should still approve on
  clinical merits — memory must not interfere.

### 3e. Commit chg-1

```bash
git add src/pacca/agents/decision_support/long_term_memory.md \
        src/pacca/agents/prompts/templates.py \
        tests/unit/test_h2_memory_criterion_preservation.py
git commit -m "chg-1: H2 memory — second entry (RA biologic after DMARD failure)"
```

---

## Step 4 — Live baseline capture at iter-4 HEAD with --rollouts 2

```bash
set -a; source .env; set +a
python -m tests.clinical.capture_baseline --rollouts 2 \
    --tag harness-iter-4 \
    --out tests/clinical/baselines/iter-4-baseline.json
```

**✓ Verify:** aggregate ≥ 90% (we shouldn't regress from iter-3's 100%
but a single-case ±1 jitter is tolerated). Distributions field present
showing per-case variance.

---

## Step 5 — Cross-iteration verification

```bash
# Manifests + drift guard + suite
python -m pytest tests/unit tests/harness -q
python -c "from pathlib import Path; from tests.harness.doc_drift_guard import find_dangling_references, format_report; print(format_report(find_dangling_references('docs', '.')))"
python -c "
import json, jsonschema
schema = json.load(open('harness/manifests/change_manifest.schema.json'))
for f in ['iter-0.json', 'iter-1.json', 'iter-2.json', 'iter-3.json', 'iter-4.json']:
    inst = json.load(open(f'harness/manifests/{f}'))
    jsonschema.validate(inst, schema)
    print(f'{f}: VALID')
"
```

---

## Step 6 — Documentation + verdict

- `harness/manifests/iter-4.json` — 2 chgs + `verdicts[]` with `keep` on
  iter-3's chg-1 / chg-2 / chg-3 (each with the predicted_fixes /
  risk_cases status from the iter-3 verification).
- `docs/ITERATIONS.md` iter-4 section — narrative covering: the
  pediatric-coverage survey that scoped chg-3 out, the chg-1 memory
  entry's interaction with the iter-3 cost escalation (the cleanest
  "memory as support, not replacement" test the cycle has produced),
  the chg-2 cleanup that finally lands.
- `docs/DECISIONS.md` iter-4 section — per-chg compact entries +
  iteration verdict.

---

## Step 7 — Mark PR ready, merge, tag

```bash
gh pr ready <PR_NUMBER>
gh pr merge <PR_NUMBER> --squash --delete-branch
git checkout main
git pull origin main
git tag -a harness-iter-4 HEAD -m "harness-iter-4 — RA biologic H2 memory entry + decision_agent.py deletion ..."
git push origin harness-iter-4
```

---

## Final checklist

- [ ] Step 0: branch is `harness/iter-4`, iter-3 tag on parent, API key loaded
- [ ] Step 1: draft PR open
- [ ] Step 2: decision_agent.py deleted; full suite still passes
- [ ] Step 3: RA memory entry shipped; PROMPT_REGISTRY v2.4; risk cases verified live
- [ ] Step 4: iter-4 baseline captured with rollouts=2
- [ ] Step 5: all gates green
- [ ] Step 6: iter-4.json + ITERATIONS.md + DECISIONS.md updated
- [ ] Step 7: PR merged; harness-iter-4 tag pushed

**One thing this runbook does NOT do:** add new pediatric cases or fit a
complexity-score model. Per the iter-3 chg-3 deferral + iter-4 dataset
survey, the existing dataset has only 1 pediatric case (GC-012), which
is enough to justify the current keyword heuristic but not a score-based
discriminator. A small data-only iteration (iter-5 candidate) should add
2–3 pediatric cases (mild + moderate ambiguous + severe-in-different-
condition) before a complexity-score iteration can be empirically
founded.
