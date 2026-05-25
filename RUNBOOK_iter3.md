# iter-3 Runbook — Phase H2 institutional memory + escalation-branch completion

This is a step-by-step guide to land iter-3 in your repo. iter-3 is the cycle's
**first behavioral-change iteration** — three changes ship that touch the agent
surface and one supports it on the eval net. The runbook codifies the design
decisions made before code was written, so the iteration's predictions can be
verified against actual outcomes.

**Conventions used below**
- `$REPO` means `/Users/davidreed/David_Portfolio/pacca`.
- Every command is run from the repo root. Open Terminal and do this once:
  ```bash
  cd /Users/davidreed/David_Portfolio/pacca
  ```
- After most steps there's a **✓ Verify** line — an expected result. If you
  don't see it, stop and check before moving on.
- **Estimated time:** ~3–5 hours (chg-1 is ~1h, chg-2 is ~1.5–2h including the
  live verification run, chg-3 is ~30m, plus ~30m for docs + verdict + tag).
- **Branch + PR workflow** (per `pacca_pr_workflow.md` memory): work happens on
  `harness/iter-3` (already created); the PR opens early as draft and is marked
  ready when verification gates are green.

**Scope and design decisions locked at the start of iter-3:**
- *chg-1 cost/age extraction:* hybrid — structured fields on `ClinicalCase` are
  the primary source; clinical_notes regex fallback when the structured field
  is `None`. Both code paths get unit-tested.
- *chg-2 H2 memory entries:* one entry — NSCLC pembrolizumab. The
  GC-001/GC-021/GC-022 sibling family validates the memory format + loader +
  criterion-preservation check on one well-understood case class. Subsequent
  iterations add entries one at a time.
- *chg-3 noise threshold:* default `drop_threshold=1` (strict) preserved;
  add a separate `noise_threshold: int = 0` parameter. Document `1` as the
  production recommendation, citing the GC-017 2→4 swing.

**Predicted fixes for the iteration:**
- chg-1 → `GC-010` flips from 1/2 to ≥3; `GC-012` flips from 2 to ≥3.
- chg-2 → none predicted to flip (memory is reasoning support, not a new
  decision rule); rather, *risk cases* GC-001 (stays at 5), GC-021 (stays
  IN_REVIEW), GC-022 (stays IN_REVIEW) must be verified non-regressed.
- chg-3 → none predicted to flip; tooling-only.

---

## Step 0 — Pre-flight

Confirm you start from the right state.

```bash
git status                # should show: On branch harness/iter-3, working tree clean (except unrelated in-flight files)
git log --oneline -3      # top commit is 0d3342f (chg-6 from iter-2)
git tag --points-at HEAD  # should show: harness-iter-2-final
```

**✓ Verify:** branch is `harness/iter-3`; HEAD has `harness-iter-2-final` tag;
unrelated in-flight files (README.md, docker-compose.yml, etc.) are still
uncommitted but not your concern — keep them out of the iter-3 PR.

Also verify the API key path is set up the safe way (`.env`, not exported):

```bash
set -a; source .env; set +a
python -c "import os; print('key set:', bool(os.environ.get('ANTHROPIC_API_KEY')))"
```

**✓ Verify:** `key set: True`.

---

## Step 1 — Open the draft PR early

The PR is a draft until all chgs land. Opening it early lets you (and any
reviewer) watch the iteration form commit-by-commit.

```bash
# After the runbook commit lands (next step), push and open the PR:
git add RUNBOOK_iter3.md
git commit -m "iter-3: add runbook (spec only; no behavioral change)"
git push -u origin harness/iter-3
gh pr create --draft --base main --head harness/iter-3 \
    --title "iter-3: H2 institutional memory + escalation-branch completion" \
    --body "$(cat <<'EOF'
## Draft — iter-3 in progress

This PR is a draft until all three changes land and the verification gates
are green. The spec is `RUNBOOK_iter3.md` (in the first commit on this branch);
the iteration manifest is `harness/manifests/iter-3.json` (added in chg-1).

**Planned changes:**
- chg-1 (escalation_branch): wire HIGH_COST and PEDIATRIC_COMPLEX into
  ClinicalRiskDetector; completes the half-built feature flagged by iter-2 chg-6.
- chg-2 (long_term_memory): Phase H2 institutional memory — first entry
  (NSCLC pembrolizumab). Loader extension + criterion-preservation tests.
- chg-3 (evaluation_harness): regression_gate noise-threshold parameter +
  k=N rollouts in capture_baseline. Closes the GC-017 jitter false-positive class.

**Predicted fixes:** GC-010 (1→≥3), GC-012 (2→≥3).
**Risk cases:** GC-001 (stays at 5), GC-021/GC-022 (stay IN_REVIEW under H2 memory).

🤖 Generated with [Claude Code](https://claude.com/claude-code)
EOF
)"
```

**✓ Verify:** PR #N opens as DRAFT; description references the runbook + planned chgs.

---

## Step 2 — chg-1: escalation fixes (HIGH_COST + PEDIATRIC_COMPLEX)

The enum values already exist (`src/pacca/models/enums.py` lines 115–119).
What's missing: the check methods, the data fields they read, and the test data.

### 2a. Add optional structured fields to ClinicalCase

Open `src/pacca/models/clinical.py`. Extend `ClinicalCase` with three optional
fields. Keep them `Optional` so existing callers don't break and the parser
fallback can kick in when they're `None`.

```python
class ClinicalCase(BaseModel):
    patient_id: str
    primary_diagnosis_code: str
    procedure_code: str
    evidence: list[EvidenceItem] = []
    # iter-3 chg-1: structured fields for branch_2_medical_director triggers.
    # Optional — the detector falls back to parsing clinical_notes when None.
    estimated_annual_cost: float | None = None
    patient_age: int | None = None
    disease_severity: str | None = None  # e.g. "severe", "moderate-to-severe"
```

**✓ Verify:**

```bash
python -c "from pacca.models.clinical import ClinicalCase; c = ClinicalCase(patient_id='P1', primary_diagnosis_code='C34.1', procedure_code='J9271'); print('age:', c.patient_age, 'cost:', c.estimated_annual_cost)"
```
Both should print as `None` (defaults preserved).

### 2b. Add parser fallbacks (used when the structured field is None)

In `src/pacca/agents/clinical_risk_detector.py`, add private helper functions
near the top of the file:

```python
import re

# Matches "$288,000" / "$288K" / "288,000 dollars" / "annual cost $288,000".
# Returns the integer dollar amount, or None if no match.
_COST_RE = re.compile(
    r"\$?\s*([\d,]+)(?:\s*(?:K|k)\b|(?:\.\d+)?\s*(?:dollars?|usd)?)"
    r"|annual\s*cost\s*(?:estimated\s*at\s*)?\$?\s*([\d,]+)",
    re.IGNORECASE,
)

# Matches "55-year-old", "14 year old", "age 55", "55yo".
_AGE_RE = re.compile(
    r"(\d{1,3})[\s-]*(?:year[s]?[\s-]*old|yo\b)|age\s*[:\s]*(\d{1,3})",
    re.IGNORECASE,
)

# Severity keywords scanned in priority order.
_SEVERITY_KEYWORDS = ("severe", "moderate-to-severe", "moderate to severe", "complex", "critical")


def _parse_cost_from_notes(notes: str) -> float | None:
    """Best-effort extraction of an estimated annual cost from clinical notes."""
    # Implementation note: when multiple dollar amounts appear, prefer the LAST
    # one (often the totalled "annual cost X * 12 = $..." figure in PACCA case
    # data). Fall through to first match otherwise.
    matches = list(_COST_RE.finditer(notes))
    if not matches:
        return None
    last = matches[-1]
    raw = (last.group(1) or last.group(2) or "").replace(",", "")
    if not raw:
        return None
    try:
        value = float(raw)
    except ValueError:
        return None
    # If the original match had a K/k suffix, multiply.
    if last.group(0).rstrip().endswith(("K", "k")):
        value *= 1000
    return value


def _parse_age_from_notes(notes: str) -> int | None:
    """Best-effort extraction of patient age from clinical notes."""
    m = _AGE_RE.search(notes)
    if not m:
        return None
    raw = m.group(1) or m.group(2)
    try:
        age = int(raw)
    except (TypeError, ValueError):
        return None
    return age if 0 <= age <= 130 else None


def _parse_severity_from_notes(notes: str) -> str | None:
    """Best-effort severity detection (returns first matching keyword)."""
    lower = notes.lower()
    for kw in _SEVERITY_KEYWORDS:
        if kw in lower:
            return kw
    return None


def _evidence_blob(case: "ClinicalCase") -> str:
    """Concatenate evidence text for parser fallback. Defined once for reuse."""
    return " ".join(item.description + " " + item.original_text for item in case.evidence)
```

### 2c. Add the two new check methods

Append two private methods to the `ClinicalRiskDetector` class, structured
identically to the existing four pre-flight checks. Add them inside the
`evaluate()` method's call sequence (after the existing four).

```python
    def evaluate(
        self,
        case: ClinicalCase,
        guidelines_context: str = "",
        prior_denial_codes: list[str] | None = None,
    ) -> EscalationFlags:
        flags = EscalationFlags()
        prior_denial_codes = prior_denial_codes or []

        self._check_experimental_treatment(case, flags)
        self._check_rare_condition(case, flags)
        self._check_conflicting_guidelines(case, guidelines_context, flags)
        self._check_prior_denial(case, prior_denial_codes, flags)
        # iter-3 chg-1: branch_2_medical_director triggers.
        self._check_high_cost(case, flags)
        self._check_pediatric_complex(case, flags)

        return flags

    # ── Branch 2: High-cost biologic / drug ──────────────────────────────────

    def _check_high_cost(self, case: ClinicalCase, flags: EscalationFlags) -> None:
        """
        Escalate to Medical Director when estimated annual cost exceeds
        settings.high_cost_threshold. Reads ClinicalCase.estimated_annual_cost
        first; falls back to parsing clinical_notes if the structured field is None.

        Why this lives in pre-flight: cost-based escalation is a POLICY rule,
        not a CLINICAL one. It must fire regardless of how convincing the
        clinical case is — the AHE finding on regression-blindness applies
        doubly to cost: an LLM is most confident on cases where clinical
        eligibility is unambiguous, which is exactly when it would skip the
        cost check if the rule lived in the prompt.
        """
        from ..config.settings import get_settings
        threshold = float(get_settings().high_cost_threshold)

        cost = case.estimated_annual_cost
        if cost is None:
            cost = _parse_cost_from_notes(_evidence_blob(case))
        if cost is None or cost <= threshold:
            return

        flags.add(
            EscalationReason.HIGH_COST,
            f"Estimated annual cost ${cost:,.0f} exceeds the configured "
            f"HIGH_COST_THRESHOLD of ${threshold:,.0f}. Cost-based escalation "
            f"applies regardless of clinical eligibility per policy.",
        )

    # ── Branch 2: Pediatric complexity ───────────────────────────────────────

    PEDIATRIC_AGE_CUTOFF = 18
    PEDIATRIC_SEVERITY_KEYWORDS = ("severe", "moderate-to-severe", "moderate to severe", "complex", "critical")

    def _check_pediatric_complex(self, case: ClinicalCase, flags: EscalationFlags) -> None:
        """
        Escalate to Medical Director when the patient is under 18 AND the
        disease severity is at least "moderate-to-severe" / "severe" / "complex".

        Reads ClinicalCase.patient_age and ClinicalCase.disease_severity first;
        falls back to parsing clinical_notes if either is None.

        Why both conditions: a pediatric patient with mild disease does not
        require specialist review by policy. The conservative complexity
        definition (used here because no complexity_score model exists yet)
        is satisfied by any case the clinical notes describe with "severe",
        "moderate-to-severe", "complex", or "critical" language.
        """
        notes_blob = _evidence_blob(case)

        age = case.patient_age
        if age is None:
            age = _parse_age_from_notes(notes_blob)
        if age is None or age >= self.PEDIATRIC_AGE_CUTOFF:
            return

        severity = (case.disease_severity or "").lower()
        if not severity:
            severity = _parse_severity_from_notes(notes_blob) or ""
        if not any(kw in severity for kw in self.PEDIATRIC_SEVERITY_KEYWORDS):
            return

        flags.add(
            EscalationReason.PEDIATRIC_COMPLEX,
            f"Pediatric patient (age {age}) with {severity} disease — "
            f"specialist review required per policy regardless of clinical "
            f"eligibility verification.",
        )
```

### 2d. Add unit tests for the two new checks

Create `tests/unit/test_escalation_high_cost_and_pediatric.py`. Cover both the
structured-field and parser-fallback paths, plus negative cases. (No live API
calls.)

```python
"""Unit tests for iter-3 chg-1 escalation checks."""
from pacca.agents.clinical_risk_detector import (
    ClinicalRiskDetector,
    _parse_age_from_notes,
    _parse_cost_from_notes,
    _parse_severity_from_notes,
)
from pacca.models.clinical import ClinicalCase, EvidenceItem
from pacca.models.enums import EscalationReason, EvidenceSourceType


def _make_case(notes: str = "", **kwargs) -> ClinicalCase:
    return ClinicalCase(
        patient_id="P-TEST",
        primary_diagnosis_code="X00",
        procedure_code="J0000",
        evidence=[EvidenceItem(
            id="e1", source_type=EvidenceSourceType.CLINICAL_NOTE,
            description=notes[:200], original_text=notes, confidence=0.9,
        )],
        **kwargs,
    )


class TestParsers:
    def test_cost_parser_handles_dollar_format(self):
        assert _parse_cost_from_notes("Annual cost $288,000.") == 288000
    def test_cost_parser_handles_K_suffix(self):
        assert _parse_cost_from_notes("$120K/year") == 120000
    def test_cost_parser_returns_none_when_no_match(self):
        assert _parse_cost_from_notes("Routine asthma case.") is None
    def test_age_parser_year_old(self):
        assert _parse_age_from_notes("14-year-old male with asthma") == 14
    def test_age_parser_rejects_out_of_range(self):
        assert _parse_age_from_notes("999-year-old patient") is None
    def test_severity_parser_finds_keyword(self):
        assert _parse_severity_from_notes("severe persistent asthma") == "severe"


class TestHighCostCheck:
    def test_fires_when_structured_cost_exceeds_threshold(self):
        case = _make_case(estimated_annual_cost=200_000.0)
        flags = ClinicalRiskDetector().evaluate(case)
        assert EscalationReason.HIGH_COST in flags.reasons

    def test_fires_when_notes_have_cost_and_structured_is_none(self):
        case = _make_case("Annual cost estimated at $288,000.")
        flags = ClinicalRiskDetector().evaluate(case)
        assert EscalationReason.HIGH_COST in flags.reasons

    def test_does_not_fire_below_threshold(self):
        case = _make_case(estimated_annual_cost=50_000.0)
        flags = ClinicalRiskDetector().evaluate(case)
        assert EscalationReason.HIGH_COST not in flags.reasons


class TestPediatricComplexCheck:
    def test_fires_for_severe_pediatric_with_structured_fields(self):
        case = _make_case(patient_age=14, disease_severity="severe")
        flags = ClinicalRiskDetector().evaluate(case)
        assert EscalationReason.PEDIATRIC_COMPLEX in flags.reasons

    def test_fires_for_severe_pediatric_via_notes_parsing(self):
        notes = "14-year-old male with severe persistent asthma uncontrolled on high-dose ICS."
        case = _make_case(notes)
        flags = ClinicalRiskDetector().evaluate(case)
        assert EscalationReason.PEDIATRIC_COMPLEX in flags.reasons

    def test_does_not_fire_for_adult_with_severe_disease(self):
        case = _make_case(patient_age=45, disease_severity="severe")
        flags = ClinicalRiskDetector().evaluate(case)
        assert EscalationReason.PEDIATRIC_COMPLEX not in flags.reasons

    def test_does_not_fire_for_pediatric_with_mild_disease(self):
        case = _make_case(patient_age=12, disease_severity="mild")
        flags = ClinicalRiskDetector().evaluate(case)
        assert EscalationReason.PEDIATRIC_COMPLEX not in flags.reasons
```

### 2e. Update test pipeline to pass new fields through

In `tests/clinical/test_clinical_accuracy.py` and `tests/clinical/capture_baseline.py`,
the loop that builds `ClinicalCase` from `GoldenCase` should populate the new
fields when available. Since `GoldenCase` doesn't have structured cost/age/severity,
the parser fallback in `ClinicalRiskDetector` handles it automatically.
**No change to those files is required** as long as the parsers work — but
verify by running GC-010 + GC-012 in Step 2g.

### 2f. Run the unit tests

```bash
python -m pytest tests/unit/test_escalation_high_cost_and_pediatric.py -v
```

**✓ Verify:** all 11 new tests pass.

Also run the full unit + harness suite to confirm no regressions:

```bash
python -m pytest tests/unit tests/harness -q
```

**✓ Verify:** 150 passed (139 prior + 11 new) — or however many; the count must
go UP, never down.

### 2g. Verify predicted fixes live

```bash
set -a; source .env; set +a
python -m tests.clinical.investigate_case GC-010 2>&1 | tail -20
python -m tests.clinical.investigate_case GC-012 2>&1 | tail -20
```

**✓ Verify (the predicted_fix gate):**

- **GC-010:** `status` is now `IN_REVIEW` (not `AUTO_APPROVED`); judge `score ≥ 3`;
  judge reasoning mentions the cost threshold. The pre-flight `should_pre_escalate`
  should now be `True` with `HIGH_COST` in the reasons list.
- **GC-012:** `status` is now `IN_REVIEW` (not `AUTO_APPROVED`); judge `score ≥ 3`;
  judge reasoning mentions pediatric specialist review.

If either case still auto-approves: stop. The parser fallback or the threshold
check missed something. Don't proceed to chg-2 until chg-1 is verified.

### 2h. Update the baseline scoreboard

```bash
python -m tests.clinical.capture_baseline --tag harness-iter-3-chg1 \
    --out tests/clinical/baselines/iter-3-chg1-baseline.json
```

**✓ Verify:** GC-010 now scores ≥3 (was 1); GC-012 now scores ≥3 (was 2);
no other case regressed (the iter-2 `regression_gate.py` should pass against
the iter-1 baseline). Aggregate accuracy should move 18/20 → 20/20 (or
19/20 if one case has jitter that didn't recover).

### 2i. Commit chg-1

```bash
git add src/pacca/models/clinical.py \
        src/pacca/agents/clinical_risk_detector.py \
        tests/unit/test_escalation_high_cost_and_pediatric.py \
        tests/clinical/baselines/iter-3-chg1-baseline.json
git commit -m "chg-1: wire HIGH_COST + PEDIATRIC_COMPLEX into ClinicalRiskDetector"
```

The iter-3 manifest is added at Step 6 (along with the verdicts on chg-2 / chg-3).
For per-chg manifest entries, draft them inline as you commit but consolidate the
JSON at iteration close.

---

## Step 3 — chg-2: Phase H2 institutional memory (one entry)

The cycle's first behavioral-change iteration at the long_term_memory constraint
level. Per the iter-1/iter-2 design constraints in `docs/findings/GC-001.md`,
the memory entry must encode the FULL set of criteria for its shortcut — not
just the headline indication — so it doesn't compress away the discriminations
that catch GC-021 (PD-L1 45%) and GC-022 (EGFR+).

### 3a. Create the memory file

Create `src/pacca/agents/decision_support/long_term_memory.md`:

```markdown
# Decision Support Agent — Long-Term Memory

This file encodes case-pattern shortcuts learned from prior PACCA evaluations.
Entries describe COMPLETE criteria sets — never just headline indications.
When a pattern matches, the agent must STILL verify each listed criterion
against the case before applying the shortcut.

---

## Pattern: First-line pembrolizumab for metastatic NSCLC with high PD-L1

**Headline indication:** Stage IV (metastatic) non-small cell lung cancer,
first-line pembrolizumab monotherapy, per NCCN Category 1 recommendation
for PD-L1 TPS ≥ 50%.

**Required criteria — ALL must be explicitly documented:**
1. Disease stage is metastatic (stage IV) — NOT stage IIIA or earlier. Stage
   IIIA NSCLC is locally advanced and receives curative-intent combined-
   modality therapy, not first-line systemic monotherapy.
2. PD-L1 tumor proportion score (TPS) is **≥ 50%**, confirmed by validated
   assay with a date.
3. No sensitizing EGFR mutations detected on molecular testing.
4. No ALK rearrangements detected on molecular testing.
5. No prior systemic therapy for metastatic disease (first-line).
6. ECOG performance status documented (0 or 1 supports treatment tolerability).

**Anti-patterns — explicitly NOT this shortcut:**
- PD-L1 TPS < 50% → guidelines recommend combination chemo-immunotherapy,
  not monotherapy. Route to IN_REVIEW.
- EGFR sensitizing mutation present → first-line is targeted therapy (e.g.
  osimertinib), not pembrolizumab. Route to IN_REVIEW.
- ALK rearrangement → first-line is ALK inhibitor (e.g. alectinib). Route
  to IN_REVIEW.
- Stage IIIA or earlier → different treatment paradigm. Route to IN_REVIEW.

**When the shortcut applies:** AUTO_APPROVE with high confidence (≥0.95) AND
the rationale must explicitly cite every required criterion above by value
(e.g. "PD-L1 62%", "no EGFR", "stage IV").

**When the shortcut DOES NOT apply:** treat the case as a standard evaluation
under the framework above. Memory is reasoning *support*, not reasoning
*replacement*.
```

### 3b. Extend the prompt loader to inject memory

Open `src/pacca/agents/_prompt_loader.py`. Add memory injection:

```python
def load_agent_prompt(agent_dir_name: str, agent_registry_name: str) -> str:
    base_dir = Path(__file__).parent / agent_dir_name
    prompt_path = base_dir / "system_prompt.md"
    raw = prompt_path.read_text(encoding="utf-8")

    # iter-3 chg-2: optionally inject long-term memory if a memory file exists.
    # Backward-compatible: agents without a memory file get an empty string,
    # preserving iter-1's byte-identity contract for agents that don't opt in.
    memory_path = base_dir / "long_term_memory.md"
    long_term_memory = memory_path.read_text(encoding="utf-8") if memory_path.exists() else ""

    template = _jinja_env.from_string(raw)
    rendered = template.render(
        agent_identity=AGENT_IDENTITY,
        clinical_safety_guidelines=CLINICAL_SAFETY_GUIDELINES,
        output_format_instructions=OUTPUT_FORMAT_INSTRUCTIONS,
        prompt_version=PROMPT_REGISTRY[agent_registry_name]["version"],
        long_term_memory=long_term_memory,
    )

    if rendered.endswith("\n"):
        rendered = rendered[:-1]

    return rendered
```

### 3c. Inject the memory section into the Decision agent's system prompt

Edit `src/pacca/agents/decision_support/system_prompt.md`. Add an "Institutional
Memory" section between the Evaluation Framework and the Confidence Scoring Rules
— the loader will inject the memory content here. If the file is absent (as in
the MedicalDirectorAgent), the variable renders empty and the structure is
unchanged.

Insert this immediately after the "5. **Precedents:**" line and before
"## Confidence Scoring Rules":

```markdown
{% if long_term_memory %}

## Institutional Memory

The following case-pattern shortcuts are codified from prior PACCA
evaluations. Apply them as REASONING SUPPORT: when a pattern matches,
you must STILL verify each required criterion against the case before
applying the shortcut. When required criteria are not all met, treat
the case as a standard evaluation under the framework above. Memory
is support, not replacement.

{{ long_term_memory }}
{% endif %}
```

The `{% if long_term_memory %}` guard means the section disappears entirely
when no memory file is present, preserving iter-1's byte-identity contract
for the MedicalDirectorAgent.

Bump the `DecisionSupportAgent` entry in `src/pacca/agents/prompts/templates.py`
PROMPT_REGISTRY from `v2.2` to `v2.3`. The version bump is recorded in the
prompt and signals (via the audit log) that institutional memory was active
for any decisions made from this point forward.

### 3d. Criterion-preservation tests

Create `tests/unit/test_h2_memory_criterion_preservation.py`. These are
*structural* tests on the prompt loader output, not live agent calls — they
verify that the memory content makes it through the loader correctly and that
the absent-file path leaves the prompt unchanged.

```python
"""iter-3 chg-2 H2 institutional memory — structural tests on prompt loader."""
from pathlib import Path
from pacca.agents._prompt_loader import load_agent_prompt


class TestMemoryInjection:
    def test_decision_support_prompt_contains_memory_section(self):
        rendered = load_agent_prompt("decision_support", "DecisionSupportAgent")
        assert "## Institutional Memory" in rendered
        assert "First-line pembrolizumab for metastatic NSCLC" in rendered

    def test_decision_support_memory_lists_all_required_criteria(self):
        rendered = load_agent_prompt("decision_support", "DecisionSupportAgent")
        # Each required criterion must be present in the rendered prompt.
        # This is the "criterion preservation" check at the prompt level —
        # an analog to iter-1's byte-identity check, scoped to H2's contract.
        for criterion in ("stage IV", "PD-L1", "≥ 50%", "EGFR", "ALK",
                          "first-line", "ECOG"):
            assert criterion in rendered, f"missing required criterion: {criterion}"

    def test_medical_director_prompt_unchanged_no_memory_file(self):
        # MedicalDirectorAgent has no long_term_memory.md; the Institutional
        # Memory section must be absent (iter-1 byte-identity contract).
        rendered = load_agent_prompt("medical_director", "MedicalDirectorAgent")
        assert "## Institutional Memory" not in rendered
        assert "First-line pembrolizumab" not in rendered

    def test_memory_anti_patterns_are_explicit(self):
        rendered = load_agent_prompt("decision_support", "DecisionSupportAgent")
        # The memory MUST encode the discriminations that catch GC-021/GC-022,
        # otherwise H2 could compress them away.
        assert "PD-L1 TPS < 50%" in rendered
        assert "EGFR sensitizing mutation" in rendered
```

### 3e. Live verification — risk cases

```bash
set -a; source .env; set +a
python -m tests.clinical.investigate_case GC-001  # canonical case — should still score 5
python -m tests.clinical.investigate_case GC-021  # near-miss PD-L1 45% — must NOT auto-approve
python -m tests.clinical.investigate_case GC-022  # near-miss EGFR+ — must NOT auto-approve
```

**✓ Verify (the risk-case gate):**

- **GC-001:** `status=AUTO_APPROVED`; score ≥4 (was 5 at iter-2 close).
  Rationale should mention "memory" or cite the institutional-memory pattern
  explicitly. If score drops to 2 or below, memory is REPLACING reasoning
  instead of supporting it — stop and fix the prompt wording.
- **GC-021 (PD-L1 45%):** `status=IN_REVIEW`; rationale cites the
  sub-50% PD-L1 anti-pattern from memory. If `AUTO_APPROVED`, the memory is
  compressing away the discrimination — stop.
- **GC-022 (EGFR+):** `status=IN_REVIEW`; rationale cites the EGFR
  anti-pattern from memory. If `AUTO_APPROVED`, same failure as GC-021.

### 3f. Commit chg-2

```bash
git add src/pacca/agents/decision_support/long_term_memory.md \
        src/pacca/agents/_prompt_loader.py \
        src/pacca/agents/decision_support/system_prompt.md \
        src/pacca/agents/prompts/templates.py \
        tests/unit/test_h2_memory_criterion_preservation.py
git commit -m "chg-2: H2 institutional memory — first entry (NSCLC pembrolizumab)"
```

---

## Step 4 — chg-3: regression_gate noise-threshold + k=N rollouts

### 4a. Extend `check_regression` with noise_threshold

Modify `tests/clinical/regression_gate.py`. Add a `noise_threshold` parameter
(default 0 = strict) and a `jitter` field on the report.

```python
def check_regression(
    current: dict[str, int],
    baseline: dict[str, int],
    *,
    drop_threshold: int = REGRESSION_DROP_THRESHOLD,
    noise_threshold: int = 0,
) -> RegressionReport:
    """
    ... (existing docstring) ...

    iter-3 chg-3: noise_threshold suppresses regressions whose drop is
    <= noise_threshold (treated as judge jitter). Default 0 preserves the
    iter-2 strict behavior. Production usage should set noise_threshold=1
    given the observed GC-017 2 -> 4 swing across same-state runs.
    """
    report = RegressionReport()
    for case_id, base_score in baseline.items():
        if case_id not in current:
            report.missing.append(case_id)
            continue
        cur_score = current[case_id]
        delta = base_score - cur_score
        if delta >= drop_threshold and delta > noise_threshold:
            report.regressions.append(CaseRegression(case_id, base_score, cur_score))
        elif delta > 0 and delta <= noise_threshold:
            report.jitter.append(CaseRegression(case_id, base_score, cur_score))
        elif cur_score > base_score:
            report.improvements.append(CaseRegression(case_id, base_score, cur_score))
    # ... rest unchanged ...
```

Add `jitter: list[CaseRegression] = field(default_factory=list)` to
`RegressionReport`. Extend `summary()` to surface jitter when present.

### 4b. Add k=N rollouts to capture_baseline.py

Add a `--rollouts N` CLI flag (default 1). When N > 1, each case runs N times
and stores the median score plus the full distribution.

The baseline file schema extends to optionally include distributions:

```json
{
  "iteration_tag": "...",
  "scores": {"GC-001": 5, ...},
  "distributions": {"GC-001": [5, 5], ...}  // optional, present only when --rollouts > 1
}
```

`save_baseline` accepts an optional `distributions` argument; `load_baseline`
returns it if present.

### 4c. Unit tests for the new behavior

Extend `tests/harness/test_iter2_hardening.py`:

```python
def test_noise_threshold_suppresses_one_point_jitter(self):
    from tests.clinical.regression_gate import check_regression
    baseline = {"GC-001": 5}
    current = {"GC-001": 4}  # one-point drop = jitter
    report = check_regression(current, baseline, noise_threshold=1)
    assert report.passed is True
    assert [r.case_id for r in report.jitter] == ["GC-001"]
    assert not report.regressions

def test_noise_threshold_does_not_suppress_two_point_drop(self):
    from tests.clinical.regression_gate import check_regression
    baseline = {"GC-001": 5}
    current = {"GC-001": 3}  # two-point drop = real regression
    report = check_regression(current, baseline, noise_threshold=1)
    assert report.passed is False
    assert [r.case_id for r in report.regressions] == ["GC-001"]
```

### 4d. Run the suite

```bash
python -m pytest tests/harness tests/unit -q
```

**✓ Verify:** all tests pass (count: ~150 + new chg-3 tests).

### 4e. Re-capture baseline with k=2 rollouts (live)

```bash
set -a; source .env; set +a
python -m tests.clinical.capture_baseline --rollouts 2 --tag harness-iter-3 \
    --out tests/clinical/baselines/iter-3-baseline.json
```

This double-runs each case and stores both median scores and distributions.
The distributions reveal the judge's variance per case.

### 4f. Commit chg-3

```bash
git add tests/clinical/regression_gate.py \
        tests/clinical/capture_baseline.py \
        tests/clinical/baselines/iter-3-baseline.json \
        tests/harness/test_iter2_hardening.py
git commit -m "chg-3: regression_gate noise_threshold + capture_baseline --rollouts"
```

---

## Step 5 — Cross-iteration verification

After all three chgs land, run every gate one more time:

```bash
# 5a. Full unit + harness suite
python -m pytest tests/unit tests/harness -q

# 5b. Live clinical gate (the full clinical run with GOLDEN + NEAR_MISS cases)
python -m pytest tests/clinical/ -m clinical -q

# 5c. Doc-drift guard
python -c "from pathlib import Path; from tests.harness.doc_drift_guard import find_dangling_references, format_report; print(format_report(find_dangling_references('docs', '.')))"

# 5d. Manifest validation
python -c "
import json, jsonschema
schema = json.load(open('harness/manifests/change_manifest.schema.json'))
for f in ['iter-0.json', 'iter-1.json', 'iter-2.json', 'iter-3.json']:
    inst = json.load(open(f'harness/manifests/{f}'))
    jsonschema.validate(inst, schema)
    print(f'{f}: VALID')
"
```

**✓ Verify (the iteration close gate):**
- Unit + harness suite: green; total count strictly greater than iter-2's 139.
- Live clinical gate: PASS (3 of 3 tests). GC-021/GC-022 routes preserved.
- Doc-drift guard: PASSED.
- All four manifests validate.

---

## Step 6 — Documentation + verdict

### 6a. Write iter-3 narrative in ITERATIONS.md

Add a new section at the top of `docs/ITERATIONS.md` (newest-first) with the
structure used for iter-2: what shipped, the design choices, the verdict on
iter-2's predictions, what success looks like for iter-4.

### 6b. Add iter-3 entries to DECISIONS.md

Add per-chg entries (chg-1, chg-2, chg-3) using the compact format from iter-2.
Each gets a table + a description + the verdict (when written; verdicts on
chg-2/chg-3's risk cases land in iter-4's `verdicts` array).

### 6c. Create harness/manifests/iter-3.json

Full structured manifest with three changes and the verdicts array pointing
back at iter-2's chgs 2 / 3 / 4 / 5 / 6 (whichever ones have outcomes worth
recording from iter-3's evidence).

### 6d. Update REVIEW_iter-2.md / create REVIEW_iter-3.md (optional)

If the PR-review surface pattern earned its keep in iter-2, repeat it for
iter-3. Otherwise skip.

---

## Step 7 — Mark PR ready, merge, tag

```bash
# 7a. Mark PR ready
gh pr ready <PR_NUMBER>

# 7b. Merge (squash recommended to keep main's log tight)
gh pr merge <PR_NUMBER> --squash --delete-branch

# 7c. Tag the merge commit
git checkout main
git pull origin main
git tag -a harness-iter-3 HEAD -m "harness-iter-3 — H2 institutional memory + escalation-branch completion ..."
git push origin harness-iter-3

# 7d. If live-gate confirmation lands later (as in iter-2's pattern), add harness-iter-3-final
```

---

## Final checklist

- [ ] Step 0: branch is `harness/iter-3`, HEAD at iter-2-final
- [ ] Step 1: draft PR open
- [ ] Step 2: chg-1 committed; GC-010 + GC-012 verified flipped (≥3)
- [ ] Step 3: chg-2 committed; GC-001 stays ≥4; GC-021/022 stay IN_REVIEW
- [ ] Step 4: chg-3 committed; noise_threshold tests pass; iter-3 baseline captured with --rollouts=2
- [ ] Step 5: all gates green
- [ ] Step 6: iter-3.json, ITERATIONS.md, DECISIONS.md updated
- [ ] Step 7: PR merged; harness-iter-3 tag pushed

**One thing this runbook does NOT do:** introduce a complexity-score model.
The pediatric_complex check uses a keyword heuristic on `disease_severity`.
A real complexity score (`COMPLEXITY_AUTO_APPROVE_MAX`, `COMPLEXITY_SPECIALIST_REVIEW_MIN`)
is its own iteration, justified by a second pediatric case that the heuristic
can't classify. Defer until that case exists.
