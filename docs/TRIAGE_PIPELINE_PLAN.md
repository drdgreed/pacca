# Evidence → Classification Triage Pipeline — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Rebuild `EvidenceAggregationAgent` + `ClinicalClassificationAgent` against the current architecture and wire them into the orchestrator as advisory enrichment (after pre-flight, before Tier-1), informing the `DecisionAgent` without controlling routing.

**Architecture:** Two `BaseAgent` subclasses mirroring `DecisionAgent` (build `user_input` from `case.model_dump_json()`, call `self.execute(user_input, response_model)`); new output models in `models/triage.py`; `DecisionContext` gains optional `evidence`/`classification`; the orchestrator runs both agents best-effort (graceful degradation) and folds their outputs into the DecisionAgent prompt (None-guarded, so behavior is byte-identical when triage is absent). Reference: `docs/TRIAGE_PIPELINE_DESIGN.md`, ADR-015..019.

**Tech Stack:** Python 3.11, pydantic v2 (`StrEnum`, `BaseModel`, `model_copy`), pytest + `unittest.mock.AsyncMock`. Reuses the existing `EVIDENCE_AGENT_SYSTEM` / `CLASSIFICATION_AGENT_SYSTEM` prompt constants.

**Process:** Branch `feat/triage-pipeline` (draft PR #42). Pre-commit hooks run (no `--no-verify`); `reviewer` subagent before each commit. Stage by **explicit path** — never `git add -A`. **Note:** the existing `build_evidence_prompt` / `build_classification_prompt` builders take flat kwargs for the *obsolete* model and are NOT used — the agents build `user_input` from `case.model_dump_json()` instead (per the contract extraction). Leave those builders in place (out of scope).

---

## File structure

| File | Responsibility | Action |
|---|---|---|
| `src/pacca/models/enums.py` | Add `UrgencyLevel` | Modify |
| `src/pacca/models/triage.py` | `EvidenceOutput`, `ClassificationOutput` | **Create** |
| `src/pacca/models/__init__.py` | Export the new types | Modify |
| `src/pacca/agents/decision.py` | `DecisionContext` fields + `DecisionAgent.run()` enrichment | Modify |
| `src/pacca/agents/evidence_agent.py` | Rewrite `EvidenceAggregationAgent` | **Replace** |
| `src/pacca/agents/classification_agent.py` | Rewrite `ClinicalClassificationAgent` | **Replace** |
| `src/pacca/agents/orchestrator.py` | Instantiate + `_run_triage` + insertion | Modify |
| `src/pacca/agents/types.py` | Delete if dead | **Delete** (verify) | <!-- drift-guard: ignore -->
| `tests/unit/test_triage_models.py` | Model tests | **Create** |
| `tests/unit/test_evidence_agent.py` | Evidence agent tests | **Create** |
| `tests/unit/test_classification_agent.py` | Classification agent tests | **Create** |
| `tests/unit/test_triage_orchestration.py` | Wiring + degradation tests | **Create** |

---

### Task 1: Models foundation (`UrgencyLevel`, output models, `DecisionContext` fields)

**Files:**
- Modify: `src/pacca/models/enums.py`, `src/pacca/models/__init__.py`, `src/pacca/agents/decision.py`
- Create: `src/pacca/models/triage.py`
- Test: `tests/unit/test_triage_models.py` (create)

- [ ] **Step 1: Write the failing tests** — create `tests/unit/test_triage_models.py`:

```python
"""Tests for the triage output models + UrgencyLevel + DecisionContext extension."""

import pytest
from pydantic import ValidationError

from pacca.agents.decision import DecisionContext
from pacca.models import ClassificationOutput, EvidenceOutput, UrgencyLevel
from pacca.models.clinical import ClinicalCase


def _case() -> ClinicalCase:
    return ClinicalCase(patient_id="P-TEST", primary_diagnosis_code="C34.1", procedure_code="J9271")


def test_urgency_level_values() -> None:
    assert {u.value for u in UrgencyLevel} == {"ROUTINE", "EXPEDITED", "URGENT"}


def test_evidence_output_validates() -> None:
    ev = EvidenceOutput(
        clinical_narrative="58yo, stage IV NSCLC.", key_findings=["PD-L1 high"],
        evidence_gaps=[], confidence_score=0.9,
    )
    assert ev.clinical_narrative.startswith("58yo")
    with pytest.raises(ValidationError):
        EvidenceOutput(clinical_narrative="x", key_findings=[], evidence_gaps=[], confidence_score=1.5)


def test_classification_output_validates_and_bounds_complexity() -> None:
    cl = ClassificationOutput(
        complexity=4, complexity_factors=["comorbid"], primary_specialty="oncology",
        urgency=UrgencyLevel.EXPEDITED, routing_rationale="complex case", confidence_score=0.8,
    )
    assert cl.complexity == 4 and cl.urgency is UrgencyLevel.EXPEDITED
    with pytest.raises(ValidationError):
        ClassificationOutput(
            complexity=6, complexity_factors=[], primary_specialty="x",
            urgency=UrgencyLevel.ROUTINE, routing_rationale="y", confidence_score=0.5,
        )


def test_decision_context_carries_triage_optional() -> None:
    ctx = DecisionContext(case=_case(), relevant_guidelines="")
    assert ctx.evidence is None and ctx.classification is None
    ev = EvidenceOutput(clinical_narrative="n", key_findings=[], evidence_gaps=[], confidence_score=0.7)
    cl = ClassificationOutput(complexity=2, complexity_factors=[], primary_specialty="cardiology",
                              urgency=UrgencyLevel.ROUTINE, routing_rationale="r", confidence_score=0.7)
    enriched = ctx.model_copy(update={"evidence": ev, "classification": cl})
    assert enriched.evidence is ev and enriched.classification is cl
```

- [ ] **Step 2: Run to verify failure**

Run: `cd /Users/davidreed/David_Portfolio/pacca && python -m pytest tests/unit/test_triage_models.py -v`
Expected: FAIL — `ImportError` (`UrgencyLevel`/`EvidenceOutput`/`ClassificationOutput` not importable).

- [ ] **Step 3: Add `UrgencyLevel` to `src/pacca/models/enums.py`** (mirror the `StrEnum` pattern; place after `ComplexityLevel`):

```python
class UrgencyLevel(StrEnum):
    """Clinical urgency of a request, assessed by the classification agent."""

    ROUTINE = "ROUTINE"
    EXPEDITED = "EXPEDITED"
    URGENT = "URGENT"
```

- [ ] **Step 4: Create `src/pacca/models/triage.py`**:

```python
"""Output models for the pre-decision triage agents (Evidence + Classification).

These live in models/ (a leaf) so both decision.py's DecisionContext and the
agents can import them without a circular import.
"""

from pydantic import BaseModel, Field

from .enums import UrgencyLevel


class EvidenceOutput(BaseModel):
    """Synthesized evidence summary produced by the EvidenceAggregationAgent."""

    clinical_narrative: str
    key_findings: list[str] = Field(default_factory=list)
    evidence_gaps: list[str] = Field(default_factory=list)
    confidence_score: float = Field(ge=0.0, le=1.0)


class ClassificationOutput(BaseModel):
    """Triage classification produced by the ClinicalClassificationAgent.

    `complexity` is an integer 1-5 (consistent with the detector's
    _compute_complexity_score and the SDD) — advisory only; the detector's
    deterministic complexity remains authoritative for pre-flight gating.
    """

    complexity: int = Field(ge=1, le=5)
    complexity_factors: list[str] = Field(default_factory=list)
    primary_specialty: str
    urgency: UrgencyLevel
    routing_rationale: str
    confidence_score: float = Field(ge=0.0, le=1.0)
```

- [ ] **Step 5: Export from `src/pacca/models/__init__.py`** — add `UrgencyLevel` to the `from .enums import (...)` block, add a new import block, and extend `__all__`:

```python
from pacca.models.enums import (
    AuthorizationStatus,
    ComplexityLevel,
    EscalationReason,
    EvidenceSourceType,
    ReviewTier,
    UrgencyLevel,
)
from pacca.models.triage import (
    ClassificationOutput,
    EvidenceOutput,
)
```
And add `"UrgencyLevel"`, `"ClassificationOutput"`, `"EvidenceOutput"` to the `__all__` list.

- [ ] **Step 6: Extend `DecisionContext` in `src/pacca/agents/decision.py`** — add the import and the two optional fields:

```python
# add to imports
from ..models.triage import ClassificationOutput, EvidenceOutput

# DecisionContext body becomes:
class DecisionContext(BaseModel):
    case: ClinicalCase
    relevant_guidelines: str
    evidence: EvidenceOutput | None = None
    classification: ClassificationOutput | None = None
```

- [ ] **Step 7: Run to verify pass + no regressions**

Run: `python -m pytest tests/unit/test_triage_models.py -v` → PASS (4 tests).
Run: `python -m pytest tests/unit -q` → no new failures (existing `DecisionContext` constructions still valid — the new fields default to `None`).

- [ ] **Step 8: Commit**

```bash
git add src/pacca/models/enums.py src/pacca/models/triage.py src/pacca/models/__init__.py src/pacca/agents/decision.py tests/unit/test_triage_models.py
git commit -m "feat(models): UrgencyLevel + EvidenceOutput/ClassificationOutput + DecisionContext triage fields"
```

---

### Task 2: `EvidenceAggregationAgent` (rewrite)

**Files:**
- Replace: `src/pacca/agents/evidence_agent.py`
- Test: `tests/unit/test_evidence_agent.py` (create)

- [ ] **Step 1: Write the failing test** — create `tests/unit/test_evidence_agent.py`:

```python
"""Unit tests for the rewritten EvidenceAggregationAgent."""

from unittest.mock import AsyncMock

import pytest

from pacca.agents.decision import DecisionContext
from pacca.agents.evidence_agent import EvidenceAggregationAgent
from pacca.models import EvidenceOutput
from pacca.models.clinical import ClinicalCase


def _ctx() -> DecisionContext:
    case = ClinicalCase(patient_id="P-TEST", primary_diagnosis_code="C34.1", procedure_code="J9271")
    return DecisionContext(case=case, relevant_guidelines="")


@pytest.mark.asyncio
async def test_run_returns_evidence_output_and_passes_case_to_execute() -> None:
    agent = EvidenceAggregationAgent()
    expected = EvidenceOutput(clinical_narrative="58yo NSCLC", key_findings=["a"], evidence_gaps=[], confidence_score=0.9)
    agent.execute = AsyncMock(return_value=expected)  # type: ignore[method-assign]

    result = await agent.run(_ctx())

    assert result is expected
    kwargs = agent.execute.call_args.kwargs
    assert kwargs["response_model"] is EvidenceOutput
    assert "C34.1" in kwargs["user_input"]  # the case JSON is in the prompt


def test_agent_identity() -> None:
    agent = EvidenceAggregationAgent()
    assert agent.name == "EvidenceAggregationAgent"
    assert "Evidence" in agent.system_prompt
```

- [ ] **Step 2: Run to verify failure**

Run: `python -m pytest tests/unit/test_evidence_agent.py -v`
Expected: FAIL — current `evidence_agent.py` doesn't import (PEP-695 via `types.py`) / class shape wrong.

- [ ] **Step 3: Replace `src/pacca/agents/evidence_agent.py` entirely** with:

```python
"""Evidence Aggregation Agent — synthesizes a ClinicalCase into a structured
evidence summary used as advisory enrichment for the Decision agent.

Mirrors DecisionAgent: builds a user-turn prompt from the case JSON and calls
BaseAgent.execute() with the EvidenceOutput response model.
"""

from ..models.triage import EvidenceOutput
from .base import BaseAgent
from .decision import DecisionContext
from .prompts import EVIDENCE_AGENT_SYSTEM


class EvidenceAggregationAgent(BaseAgent):
    """Pre-decision evidence synthesis (PRD 'Evidence Aggregation')."""

    @property
    def name(self) -> str:
        return "EvidenceAggregationAgent"

    @property
    def system_prompt(self) -> str:
        return EVIDENCE_AGENT_SYSTEM

    async def run(self, context: DecisionContext) -> EvidenceOutput:
        user_input = (
            f"## Clinical Case\n"
            f"{context.case.model_dump_json(indent=2)}"
        )
        return await self.execute(user_input=user_input, response_model=EvidenceOutput)
```
(Confirm `EVIDENCE_AGENT_SYSTEM` is importable from `pacca.agents.prompts` — the contract extraction confirms it is exported there.)

- [ ] **Step 4: Run to verify pass**

Run: `python -m pytest tests/unit/test_evidence_agent.py -v` → PASS (2 tests).
Run: `python -m pytest tests/unit -q` → no new failures.

- [ ] **Step 5: Commit**

```bash
git add src/pacca/agents/evidence_agent.py tests/unit/test_evidence_agent.py
git commit -m "feat(agents): rewrite EvidenceAggregationAgent against current BaseAgent architecture"
```

---

### Task 3: `ClinicalClassificationAgent` (rewrite)

**Files:**
- Replace: `src/pacca/agents/classification_agent.py`
- Test: `tests/unit/test_classification_agent.py` (create)

- [ ] **Step 1: Write the failing test** — create `tests/unit/test_classification_agent.py`:

```python
"""Unit tests for the rewritten ClinicalClassificationAgent."""

from unittest.mock import AsyncMock

import pytest

from pacca.agents.classification_agent import ClinicalClassificationAgent
from pacca.agents.decision import DecisionContext
from pacca.models import ClassificationOutput, EvidenceOutput, UrgencyLevel
from pacca.models.clinical import ClinicalCase


def _ctx() -> DecisionContext:
    case = ClinicalCase(patient_id="P-TEST", primary_diagnosis_code="C34.1", procedure_code="J9271")
    return DecisionContext(case=case, relevant_guidelines="")


@pytest.mark.asyncio
async def test_run_returns_classification_and_includes_case_and_evidence() -> None:
    agent = ClinicalClassificationAgent()
    expected = ClassificationOutput(
        complexity=4, complexity_factors=["comorbid"], primary_specialty="oncology",
        urgency=UrgencyLevel.EXPEDITED, routing_rationale="r", confidence_score=0.8,
    )
    agent.execute = AsyncMock(return_value=expected)  # type: ignore[method-assign]
    evidence = EvidenceOutput(clinical_narrative="stage IV NSCLC narrative", key_findings=["PD-L1"], evidence_gaps=[], confidence_score=0.9)

    result = await agent.run(_ctx(), evidence)

    assert result is expected
    kwargs = agent.execute.call_args.kwargs
    assert kwargs["response_model"] is ClassificationOutput
    assert "C34.1" in kwargs["user_input"]                      # case JSON present
    assert "stage IV NSCLC narrative" in kwargs["user_input"]   # evidence narrative present


def test_agent_identity() -> None:
    agent = ClinicalClassificationAgent()
    assert agent.name == "ClinicalClassificationAgent"
    assert "Classification" in agent.system_prompt
```

- [ ] **Step 2: Run to verify failure**

Run: `python -m pytest tests/unit/test_classification_agent.py -v`
Expected: FAIL — current `classification_agent.py` doesn't import / wrong shape.

- [ ] **Step 3: Replace `src/pacca/agents/classification_agent.py` entirely** with:

```python
"""Clinical Classification Agent — the PRD 'Triage Coordinator'.

Scores complexity (1-5), identifies specialty, and assesses urgency from the
case + the upstream evidence summary. Advisory only: its output enriches the
Decision agent's context; it does not control routing. Mirrors DecisionAgent.
"""

from ..models.triage import ClassificationOutput, EvidenceOutput
from .base import BaseAgent
from .decision import DecisionContext
from .prompts import CLASSIFICATION_AGENT_SYSTEM


class ClinicalClassificationAgent(BaseAgent):
    """Pre-decision triage classification (PRD 'Clinical Classification Agent')."""

    @property
    def name(self) -> str:
        return "ClinicalClassificationAgent"

    @property
    def system_prompt(self) -> str:
        return CLASSIFICATION_AGENT_SYSTEM

    async def run(
        self, context: DecisionContext, evidence: EvidenceOutput
    ) -> ClassificationOutput:
        findings = "\n".join(f"- {f}" for f in evidence.key_findings)
        user_input = (
            f"## Clinical Case\n"
            f"{context.case.model_dump_json(indent=2)}\n\n"
            f"## Evidence Summary\n{evidence.clinical_narrative}\n\n"
            f"## Key Findings\n{findings}"
        )
        return await self.execute(user_input=user_input, response_model=ClassificationOutput)
```

- [ ] **Step 4: Run to verify pass**

Run: `python -m pytest tests/unit/test_classification_agent.py -v` → PASS (2 tests).
Run: `python -m pytest tests/unit -q` → no new failures.

- [ ] **Step 5: Commit**

```bash
git add src/pacca/agents/classification_agent.py tests/unit/test_classification_agent.py
git commit -m "feat(agents): rewrite ClinicalClassificationAgent against current BaseAgent architecture"
```

---

### Task 4: Orchestrator wiring + DecisionAgent enrichment

**Files:**
- Modify: `src/pacca/agents/orchestrator.py` (imports + `__init__` + `_run_triage` + insertion), `src/pacca/agents/decision.py` (`DecisionAgent.run()` enrichment)
- Test: `tests/unit/test_triage_orchestration.py` (create)

- [ ] **Step 1: Write the failing tests** — create `tests/unit/test_triage_orchestration.py`:

```python
"""Orchestrator wiring: triage runs + enriches; degrades gracefully on failure."""

from unittest.mock import AsyncMock

import pytest

from pacca.agents.orchestrator import Orchestrator
from pacca.agents.decision import DecisionContext
from pacca.models import ClassificationOutput, EvidenceOutput, UrgencyLevel
from pacca.models.authorization import AuthorizationDecision
from pacca.models.enums import AuthorizationStatus

# Reuse the existing escalation-tree factories so ClinicalCase / AuthorizationDecision
# are constructed exactly as the current models require (no guessing constructors).
from tests.unit.test_escalation_tree import make_case, make_decision


def _ctx() -> DecisionContext:
    return DecisionContext(case=make_case(), relevant_guidelines="")  # make_case() clears pre-flight


def _decision() -> AuthorizationDecision:
    return make_decision(status=AuthorizationStatus.AUTO_APPROVED, confidence=0.97)


def _evidence() -> EvidenceOutput:
    return EvidenceOutput(clinical_narrative="n", key_findings=[], evidence_gaps=[], confidence_score=0.9)


def _classification() -> ClassificationOutput:
    return ClassificationOutput(complexity=2, complexity_factors=[], primary_specialty="oncology",
                                urgency=UrgencyLevel.ROUTINE, routing_rationale="r", confidence_score=0.9)


@pytest.mark.asyncio
async def test_triage_runs_and_enriches_decision_context() -> None:
    orch = Orchestrator()
    orch.evidence_agent.run = AsyncMock(return_value=_evidence())            # type: ignore[method-assign]
    orch.classification_agent.run = AsyncMock(return_value=_classification())  # type: ignore[method-assign]
    orch.decision_agent.run = AsyncMock(return_value=_decision())           # type: ignore[method-assign]

    await orch.process_decision(_ctx())

    orch.evidence_agent.run.assert_awaited_once()
    orch.classification_agent.run.assert_awaited_once()
    # The decision agent received an ENRICHED context.
    passed_ctx = orch.decision_agent.run.call_args.args[0]
    assert passed_ctx.evidence is not None
    assert passed_ctx.classification is not None
    assert passed_ctx.classification.primary_specialty == "oncology"


@pytest.mark.asyncio
async def test_triage_failure_degrades_gracefully() -> None:
    orch = Orchestrator()
    orch.evidence_agent.run = AsyncMock(side_effect=RuntimeError("LLM down"))  # type: ignore[method-assign]
    orch.classification_agent.run = AsyncMock(return_value=_classification())   # type: ignore[method-assign]
    orch.decision_agent.run = AsyncMock(return_value=_decision())             # type: ignore[method-assign]

    result = await orch.process_decision(_ctx())  # must NOT raise

    assert result.status == AuthorizationStatus.AUTO_APPROVED
    passed_ctx = orch.decision_agent.run.call_args.args[0]
    assert passed_ctx.evidence is None          # un-enriched
    assert passed_ctx.classification is None
```

- [ ] **Step 2: Run to verify failure**

Run: `python -m pytest tests/unit/test_triage_orchestration.py -v`
Expected: FAIL — `Orchestrator` has no `evidence_agent`/`classification_agent` attributes; no triage runs.

- [ ] **Step 3: Wire the orchestrator** — in `src/pacca/agents/orchestrator.py`:

(a) Add imports (extend the `.decision` line is fine, or new lines):
```python
from .classification_agent import ClinicalClassificationAgent
from .evidence_agent import EvidenceAggregationAgent
```
(b) Extend `__init__`:
```python
    def __init__(self) -> None:
        self.decision_agent = DecisionAgent()
        self.medical_director_agent = MedicalDirectorAgent()
        self.risk_detector = ClinicalRiskDetector()
        self.evidence_agent = EvidenceAggregationAgent()
        self.classification_agent = ClinicalClassificationAgent()
```
(c) Add the `_run_triage` helper method on `Orchestrator`:
```python
    async def _run_triage(
        self,
        context: "DecisionContext",
        audit: AuditRepository | None,
        correlation_id: str | None,
    ) -> tuple[EvidenceOutput | None, ClassificationOutput | None]:
        """Advisory enrichment (PRD Evidence -> Classification). Best-effort:
        on any failure, returns (None, None) and the decision proceeds un-enriched."""
        try:
            if audit:
                await audit.log(action="agent_evidence_started", actor="EvidenceAggregationAgent",
                                actor_type="agent", correlation_id=correlation_id)
            evidence = await self.evidence_agent.run(context)
            if audit:
                await audit.log(action="agent_evidence_completed", actor="EvidenceAggregationAgent",
                                actor_type="agent", correlation_id=correlation_id,
                                output_summary=f"findings={len(evidence.key_findings)} conf={evidence.confidence_score:.2f}")
                await audit.log(action="agent_classification_started", actor="ClinicalClassificationAgent",
                                actor_type="agent", correlation_id=correlation_id)
            classification = await self.classification_agent.run(context, evidence)
            if audit:
                await audit.log(action="agent_classification_completed", actor="ClinicalClassificationAgent",
                                actor_type="agent", correlation_id=correlation_id,
                                output_summary=f"complexity={classification.complexity} specialty={classification.primary_specialty} urgency={classification.urgency.value}")
            return evidence, classification
        except Exception as exc:
            if audit:
                await audit.log(action="triage_enrichment_failed", actor="orchestrator",
                                actor_type="system", correlation_id=correlation_id,
                                details={"error_type": type(exc).__name__})
            return None, None
```
(d) Add the imports for the output-model types at the top of orchestrator.py:
```python
from ..models.triage import ClassificationOutput, EvidenceOutput
```
(e) Insert the triage call in `process_decision` — immediately AFTER the pre-flight `if flags.should_pre_escalate: return ...` block (around line 147) and BEFORE `tier1_start = time.time()`:
```python
        # ── Triage enrichment (advisory; PRD Evidence -> Classification) ─────────
        evidence, classification = await self._run_triage(context, audit, correlation_id)
        if evidence is not None and classification is not None:
            context = context.model_copy(
                update={"evidence": evidence, "classification": classification}
            )
```

- [ ] **Step 4: Enrich `DecisionAgent.run()`** — in `src/pacca/agents/decision.py`, replace the `user_input` construction in `DecisionAgent.run()` with a None-guarded triage prepend (byte-identical when both are None):
```python
        triage = ""
        if context.classification is not None:
            triage += f"## Triage Classification\n{context.classification.model_dump_json(indent=2)}\n\n"
        if context.evidence is not None:
            triage += f"## Evidence Summary\n{context.evidence.clinical_narrative}\n\n"
        user_input = (
            f"{triage}"
            f"## Clinical Case\n"
            f"{context.case.model_dump_json(indent=2)}\n\n"
            f"## Relevant Clinical Guidelines\n"
            f"{context.relevant_guidelines}"
        )
```
(Leave the `self.execute(...)` + `review_tier_used` lines unchanged.)

- [ ] **Step 5: Keep existing orchestrator tests offline — mock triage in their shared helper**

`tests/unit/test_escalation_tree.py` builds a real `Orchestrator` (mocking `decision_agent.run` / `medical_director_agent.run`). Now that `process_decision` runs the triage agents *first*, those tests would attempt real API calls (they'd ultimately degrade gracefully via `_run_triage`, but slowly, with retries). Update the shared `make_orchestrator_with_mocks(...)` helper to also mock the triage agents with benign outputs (add inside that helper, before it returns the orchestrator):

```python
    from pacca.models import ClassificationOutput, EvidenceOutput, UrgencyLevel
    orchestrator.evidence_agent.run = AsyncMock(  # type: ignore[method-assign]
        return_value=EvidenceOutput(clinical_narrative="", key_findings=[], evidence_gaps=[], confidence_score=0.9)
    )
    orchestrator.classification_agent.run = AsyncMock(  # type: ignore[method-assign]
        return_value=ClassificationOutput(complexity=1, complexity_factors=[], primary_specialty="general",
                                          urgency=UrgencyLevel.ROUTINE, routing_rationale="", confidence_score=0.9)
    )
```

- [ ] **Step 6: Run to verify pass + no regressions**

Run: `python -m pytest tests/unit/test_triage_orchestration.py tests/unit/test_escalation_tree.py -v` → all pass.
Run: `python -m pytest tests/unit -q` → no new failures (and no slow real-API attempts during the run).

- [ ] **Step 7: Commit**

```bash
git add src/pacca/agents/orchestrator.py src/pacca/agents/decision.py tests/unit/test_triage_orchestration.py tests/unit/test_escalation_tree.py
git commit -m "feat(orchestrator): run Evidence+Classification triage as advisory enrichment (graceful degradation)"
```

---

### Task 5: `types.py` cleanup

**Files:**
- Delete (if dead): `src/pacca/agents/types.py` <!-- drift-guard: ignore -->

- [ ] **Step 1: Verify nothing imports it**

Run: `grep -rn "agents.types\|from .types\|from \.\.agents\.types\|import types" src/ tests/ | grep -v "import typing"`
Expected: NO hits (after Tasks 2-3, the rewritten agents no longer import `AgentContext`). If there ARE hits in live code, STOP and report — apply only a minimal `Generic[T]` fix instead of deleting.

- [ ] **Step 2: Delete the dead file (only if Step 1 was clean)**

```bash
git rm src/pacca/agents/types.py
```
Also delete its stale bytecode: `rm -f src/pacca/agents/__pycache__/types.cpython-311.pyc`. <!-- drift-guard: ignore -->

- [ ] **Step 3: Verify the suite still imports + passes**

Run: `python -m pytest tests/unit -q` → no new failures (nothing imported `types.py`).

- [ ] **Step 4: Commit**

```bash
git add -u src/pacca/agents/types.py
git commit -m "chore(agents): delete dead types.py (PEP-695 syntax; unused after agent rewrites)"
```
(If Step 1 found a live importer and you applied a `Generic[T]` fix instead, stage `src/pacca/agents/types.py` by explicit path and commit `fix(agents): make types.py import on Python 3.11 (Generic[T])`.) <!-- drift-guard: ignore -->

---

### Task 6: Full-suite + golden-20 re-baseline gate

**Files:** none (verification only)

- [ ] **Step 1: Full deterministic suite**

Run: `make test`
Expected: green. Capture the passing count. Confirm no test still references the old agent shapes / `types.py`.

- [ ] **Step 2: Golden-20 live clinical gate — RE-BASELINE (not preservation)**

Run: `set -a; source .env; set +a` (sources `ANTHROPIC_API_KEY`), then `make test-clinical` (or `python -m pytest tests/clinical/test_clinical_accuracy.py -m clinical -v`).
Expected: the live pipeline now runs Evidence + Classification before the DecisionAgent on every golden case. **Score movement is expected.** Record the new distribution. The gate's pass criterion: the accuracy threshold still holds (the suite's `test_full_pipeline_meets_accuracy_threshold` passes) and zero hallucinations. If any individual golden case regresses materially, STOP and report it with the before/after — decide (adjust the triage prompt framing vs. accept) before merge.

- [ ] **Step 3: Mark PR #42 ready**

```bash
gh pr ready 42
```
Update the PR checklist (Implementation, Golden-20 re-baseline) to checked, and note the re-baseline result (old vs new distribution) in a PR comment.

---

## Out of scope (flagged)

- Full triage routing (Option C) — agents stay advisory.
- The SDD URGENT-not-standard-queue postcondition — no queue/priority concept exists yet; urgency is recorded only.
- The obsolete `build_evidence_prompt` / `build_classification_prompt` flat-arg builders — left in place, unused (a separate cleanup if desired).
