# Runtime-Tunable Decision Thresholds — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make PACCA's confidence-routing thresholds (and the already-config-driven high_cost / complexity thresholds) genuinely runtime-tunable by routing every consumer through one `effective_settings()` accessor that merges admin overrides over env defaults — preserving today's 0.95 / 0.90 behavior exactly.

**Architecture:** A shared override store + `effective_settings()` accessor in `config/settings.py` (merges `_runtime_overrides` over the cached `get_settings()` via `model_copy`). The orchestrator (currently hardcoded), the detector (currently reads raw `get_settings()`), and the admin `/config` handlers (currently a private store) all read/write through it. Defaults move to 0.95 / 0.90 so behavior is unchanged when no override is active.

**Tech Stack:** Python 3.11, pydantic / pydantic-settings v2, FastAPI, pytest. Reference design: `docs/RUNTIME_TUNABLE_THRESHOLDS_DESIGN.md`.

**Process:** Branch `feat/runtime-tunable-thresholds` (already created, draft PR #38). Pre-commit hooks run on every commit (no `--no-verify`). Per PACCA `CLAUDE.md`, run the `reviewer` subagent before each commit. Stage by **explicit path** — never `git add -A` (three untracked files are runbook-guarded).

**Governance note (decided during planning):** the design's "audit-trail entry" is implemented as a **structlog** record, not a DB `audit_logs` row. Reason: the admin config route is deliberately DB-session-free (its test harness mounts the router with no session/JWT — `test_config_api.py:57-71`), so adding `Depends(get_session)` would break every config test. The structlog path also fixes a real latent bug (admin currently logs structlog-style kwargs through stdlib `logging`, which raises `TypeError`). A formal DB audit row is a flagged follow-up.

---

### Task 1: Shared override store + `effective_settings()` accessor

**Files:**
- Modify: `src/pacca/config/settings.py` (add module-level store + functions, after the `Settings` class / `get_settings`)
- Test: `tests/unit/test_effective_settings.py` (create)

- [ ] **Step 1: Write the failing tests**

Create `tests/unit/test_effective_settings.py`:

```python
"""Unit tests for the shared runtime-override store + effective_settings()."""

import pytest

from pacca.config.settings import (
    active_overrides,
    apply_overrides,
    clear_all_overrides,
    effective_settings,
    get_settings,
)


@pytest.fixture(autouse=True)
def _reset_overrides():
    clear_all_overrides()
    yield
    clear_all_overrides()


def test_effective_equals_base_when_no_overrides():
    s = effective_settings()
    base = get_settings()
    assert s.auto_approve_confidence_threshold == base.auto_approve_confidence_threshold
    assert s.high_cost_threshold == base.high_cost_threshold


def test_apply_override_is_reflected():
    apply_overrides({"high_cost_threshold": 40_000})
    assert effective_settings().high_cost_threshold == 40_000
    assert "high_cost_threshold" in active_overrides()


def test_apply_override_does_not_mutate_base():
    base_before = get_settings().high_cost_threshold
    apply_overrides({"high_cost_threshold": 1})
    assert get_settings().high_cost_threshold == base_before  # cached base untouched


def test_rejects_auto_approve_not_above_escalation():
    with pytest.raises(ValueError, match="greater than|escalation band"):
        apply_overrides({"auto_approve_confidence_threshold": 0.50})  # below default escalation


def test_invalid_override_is_atomic():
    apply_overrides({"high_cost_threshold": 70_000})  # valid baseline override
    with pytest.raises(ValueError):
        apply_overrides({
            "llm_retry_max_attempts": 9,                      # valid
            "auto_approve_confidence_threshold": 0.10,        # invalid (<= escalation)
        })
    # Neither field from the failed batch applied; the earlier valid override survives.
    assert "llm_retry_max_attempts" not in active_overrides()
    assert active_overrides()["high_cost_threshold"] == 70_000


def test_clear_all_overrides_returns_cleared_keys():
    apply_overrides({"high_cost_threshold": 40_000, "demo_mode": False})
    cleared = clear_all_overrides()
    assert set(cleared) == {"high_cost_threshold", "demo_mode"}
    assert active_overrides() == {}
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/unit/test_effective_settings.py -v`
Expected: FAIL with `ImportError` (functions not defined yet).

- [ ] **Step 3: Implement the store + accessor in `config/settings.py`**

Add at module scope (after the `Settings` class and `get_settings()` definition):

```python
# ── Runtime override store (shared source of truth for tunable settings) ──────
# Set via PATCH /config, merged over the cached Settings by effective_settings().
# Cleared on restart by design (restart == reload from env). Process-local dict;
# safe under the single asyncio loop, same exposure model as before.
_runtime_overrides: dict[str, object] = {}


def effective_settings() -> "Settings":
    """get_settings() with runtime overrides applied. Cheap; call per request."""
    base = get_settings()
    if not _runtime_overrides:
        return base
    return base.model_copy(update=_runtime_overrides)


def active_overrides() -> dict[str, object]:
    """The currently-applied runtime overrides (copy)."""
    return dict(_runtime_overrides)


def clear_all_overrides() -> list[str]:
    """Drop all runtime overrides; return the field names that were cleared."""
    cleared = list(_runtime_overrides.keys())
    _runtime_overrides.clear()
    return cleared


def _validate_effective() -> None:
    """Enforce cross-field invariants on the merged effective settings."""
    s = effective_settings()
    if s.auto_approve_confidence_threshold <= s.escalation_confidence_threshold:
        raise ValueError(
            f"auto_approve_confidence_threshold ({s.auto_approve_confidence_threshold}) "
            f"must be greater than escalation_confidence_threshold "
            f"({s.escalation_confidence_threshold}). The Medical Director escalation "
            f"band would collapse to nothing."
        )
    if s.llm_retry_wait_min_seconds > s.llm_retry_wait_max_seconds:
        raise ValueError(
            f"llm_retry_wait_min_seconds ({s.llm_retry_wait_min_seconds}) must not "
            f"exceed llm_retry_wait_max_seconds ({s.llm_retry_wait_max_seconds})."
        )


def apply_overrides(updates: dict[str, object]) -> None:
    """Apply runtime overrides atomically. Validates the merged result; on failure
    no field from `updates` is applied. Raises ValueError with a readable message."""
    snapshot = dict(_runtime_overrides)
    _runtime_overrides.update(updates)
    try:
        _validate_effective()
    except ValueError:
        _runtime_overrides.clear()
        _runtime_overrides.update(snapshot)
        raise
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/unit/test_effective_settings.py -v`
Expected: PASS (6 tests).

- [ ] **Step 5: Commit**

```bash
git add src/pacca/config/settings.py tests/unit/test_effective_settings.py
git commit -m "feat(config): shared effective_settings() accessor + runtime override store"
```

---

### Task 2: Preserve-behavior defaults (0.95 / 0.90)

**Files:**
- Modify: `src/pacca/config/settings.py:106` (auto-approve default), `:112` (escalation default)
- Modify: `.env`, `.env.example`
- Test: `tests/unit/test_effective_settings.py` (append)

- [ ] **Step 1: Write the failing test**

Append to `tests/unit/test_effective_settings.py`:

```python
def test_default_confidence_thresholds_preserve_orchestrator_behavior():
    # Orchestrator historically routed at 0.95 / 0.90; defaults must match so
    # wiring it to settings is a no-op behavior change.
    fields = get_settings().__class__.model_fields
    assert fields["auto_approve_confidence_threshold"].default == 0.95
    assert fields["escalation_confidence_threshold"].default == 0.90
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/unit/test_effective_settings.py::test_default_confidence_thresholds_preserve_orchestrator_behavior -v`
Expected: FAIL (defaults are still 0.85 / 0.75).

- [ ] **Step 3: Change the defaults**

In `src/pacca/config/settings.py`, edit the two Field defaults:
- `auto_approve_confidence_threshold`: `default=0.85` → `default=0.95`
- `escalation_confidence_threshold`: `default=0.75` → `default=0.90`

In `.env` AND `.env.example` (no inline comments — PACCA rule):
- `AUTO_APPROVE_CONFIDENCE_THRESHOLD=0.85` → `AUTO_APPROVE_CONFIDENCE_THRESHOLD=0.95`
- `ESCALATION_CONFIDENCE_THRESHOLD=0.75` → `ESCALATION_CONFIDENCE_THRESHOLD=0.90`

- [ ] **Step 4: Run test + guard against stale assertions**

Run: `pytest tests/unit/test_effective_settings.py -v`
Expected: PASS.
Run: `grep -rn "0\.85\|0\.75" tests/ | grep -i "threshold\|confidence"`
Expected: no test asserts the old defaults. If any does, update it to 0.95 / 0.90 and note it in the commit.

- [ ] **Step 5: Commit**

```bash
git add src/pacca/config/settings.py .env .env.example tests/unit/test_effective_settings.py
git commit -m "feat(config): default confidence thresholds to 0.95/0.90 (preserve routing behavior)"
```

---

### Task 3: Orchestrator reads `effective_settings()` (via a pure branch helper)

**Files:**
- Modify: `src/pacca/agents/orchestrator.py` (add import + `select_confidence_branch` helper; rewrite the Branch 1–3 block `:174-218`; the MD gate `:335`)
- Test: `tests/unit/test_confidence_routing.py` (create)

- [ ] **Step 1: Write the failing tests**

Create `tests/unit/test_confidence_routing.py`:

```python
"""Pure-function tests for Tier-1 confidence branch selection (PRD §5.4)."""

import pytest

from pacca.agents.orchestrator import select_confidence_branch
from pacca.models.authorization import AuthorizationStatus


@pytest.mark.parametrize(
    "confidence,status,auto,esc,expected",
    [
        (0.96, AuthorizationStatus.AUTO_APPROVED, 0.95, 0.90, "auto_approve"),
        (0.93, AuthorizationStatus.AUTO_APPROVED, 0.95, 0.90, "medical_director"),
        (0.80, AuthorizationStatus.AUTO_APPROVED, 0.95, 0.90, "human_review"),
        # High confidence but the agent did NOT auto-approve → not Branch 1.
        (0.97, AuthorizationStatus.IN_REVIEW, 0.95, 0.90, "human_review"),
        # Tunability proof: lowering auto to 0.92 flips a 0.93 case to Branch 1.
        (0.93, AuthorizationStatus.AUTO_APPROVED, 0.92, 0.90, "auto_approve"),
    ],
)
def test_select_confidence_branch(confidence, status, auto, esc, expected):
    assert select_confidence_branch(confidence, status, auto, esc) == expected
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/unit/test_confidence_routing.py -v`
Expected: FAIL with `ImportError` (`select_confidence_branch` not defined).

- [ ] **Step 3: Add the helper + the settings import**

In `src/pacca/agents/orchestrator.py`, add to the imports block (near line 50):

```python
from ..config.settings import effective_settings
```

Add a module-level pure helper (above `class Orchestrator`):

```python
def select_confidence_branch(
    confidence: float,
    status: "AuthorizationStatus",
    auto_approve_threshold: float,
    escalation_threshold: float,
) -> str:
    """Select the Tier-1 confidence routing branch (PRD §5.4 Branches 1-3).

    Returns one of: "auto_approve", "medical_director", "human_review".
    Pure function of the agent's (confidence, status) and the effective thresholds.
    """
    if (
        confidence >= auto_approve_threshold
        and status == AuthorizationStatus.AUTO_APPROVED
    ):
        return "auto_approve"
    if escalation_threshold <= confidence < auto_approve_threshold:
        return "medical_director"
    return "human_review"
```

- [ ] **Step 4: Rewrite the Branch 1–3 block to use the helper + effective settings**

In `process_decision`, replace the existing block at `orchestrator.py:174-218` with:

```python
        # ── Tier-1 confidence routing (PRD §5.4 Branches 1-3) ──────────────────
        s = effective_settings()
        branch = select_confidence_branch(
            decision.confidence_score,
            decision.status,
            s.auto_approve_confidence_threshold,
            s.escalation_confidence_threshold,
        )

        if branch == "auto_approve":
            if audit:
                await audit.log(
                    action="escalation_auto_approved",
                    actor="orchestrator",
                    actor_type="system",
                    correlation_id=correlation_id,
                    details={
                        "escalation_reason": EscalationReason.CONFIDENCE_BELOW_THRESHOLD.value,
                        "confidence_score": decision.confidence_score,
                        "branch": "1_auto_approve",
                    },
                )
            return decision

        if branch == "medical_director":
            return await self._run_medical_director(
                context=context,
                tier1_decision=decision,
                audit=audit,
                correlation_id=correlation_id,
            )

        # branch == "human_review"
        decision.status = AuthorizationStatus.IN_REVIEW
        if audit:
            await audit.log(
                action="escalation_human_review_required",
                actor="orchestrator",
                actor_type="system",
                correlation_id=correlation_id,
                details={
                    "escalation_reason": EscalationReason.CONFIDENCE_BELOW_THRESHOLD.value,
                    "confidence_score": decision.confidence_score,
                    "threshold": s.escalation_confidence_threshold,
                    "branch": "3_low_confidence",
                },
            )
        return decision
```

- [ ] **Step 5: Wire the Medical-Director post-review gate to effective settings**

In `_run_medical_director`, change the gate at `orchestrator.py:335`:

```python
        if md_decision.confidence_score >= effective_settings().auto_approve_confidence_threshold:
            md_decision.status = AuthorizationStatus.AUTO_APPROVED
        else:
            md_decision.status = AuthorizationStatus.IN_REVIEW
```

- [ ] **Step 6: Run tests to verify they pass**

Run: `pytest tests/unit/test_confidence_routing.py -v`
Expected: PASS (5 parametrized cases).

- [ ] **Step 7: Commit**

```bash
git add src/pacca/agents/orchestrator.py tests/unit/test_confidence_routing.py
git commit -m "feat(orchestrator): route confidence Branches 1-3 via effective_settings (was hardcoded 0.95/0.90)"
```

---

### Task 4: Detector reads `effective_settings()`

**Files:**
- Modify: `src/pacca/agents/clinical_risk_detector.py:652-654` (`_check_high_cost`), `:745,760` (`_check_adult_complex`)
- Test: `tests/unit/test_escalation_high_cost_and_pediatric.py` (append)

- [ ] **Step 1: Write the failing test**

Append to `tests/unit/test_escalation_high_cost_and_pediatric.py` (the `_make_case` helper and the `EscalationReason` / `ClinicalRiskDetector` imports already exist at the top of this file):

```python
class TestHighCostThresholdIsTunable:
    def test_override_below_cost_makes_it_fire(self) -> None:
        from pacca.config.settings import apply_overrides, clear_all_overrides

        # $50k case: at the default $100k threshold it must NOT fire.
        case = _make_case("Cost $50,000.", estimated_annual_cost=50_000.0)
        assert (
            EscalationReason.HIGH_COST
            not in ClinicalRiskDetector().evaluate(case).reasons
        )
        try:
            # Override the threshold below the cost — detector must now escalate,
            # proving it reads effective_settings() rather than a static value.
            apply_overrides({"high_cost_threshold": 40_000})
            assert (
                EscalationReason.HIGH_COST
                in ClinicalRiskDetector().evaluate(case).reasons
            )
        finally:
            clear_all_overrides()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/unit/test_escalation_high_cost_and_pediatric.py::TestHighCostThresholdIsTunable -v`
Expected: FAIL (detector still reads `get_settings()`, so the override is ignored and HIGH_COST does not fire).

- [ ] **Step 3: Swap the detector's two settings reads**

In `src/pacca/agents/clinical_risk_detector.py`:
- `_check_high_cost` — change the import at `:652` and read at `:654`:
  - `from ..config.settings import get_settings` → `from ..config.settings import effective_settings`
  - `threshold = float(get_settings().high_cost_threshold)` → `threshold = float(effective_settings().high_cost_threshold)`
- `_check_adult_complex` — change the import at `:745` and read at `:760`:
  - `from ..config.settings import get_settings` → `from ..config.settings import effective_settings`
  - `threshold = int(get_settings().complexity_specialist_review_min)` → `threshold = int(effective_settings().complexity_specialist_review_min)`

(Leave `_check_pediatric_complex` unchanged — its threshold is the class constant `PEDIATRIC_COMPLEXITY_THRESHOLD = 3`, not a setting.)

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/unit/test_escalation_high_cost_and_pediatric.py -v`
Expected: PASS (existing tests + the new `TestHighCostThresholdIsTunable`).

- [ ] **Step 5: Commit**

```bash
git add src/pacca/agents/clinical_risk_detector.py tests/unit/test_escalation_high_cost_and_pediatric.py
git commit -m "feat(detector): read high_cost/complexity via effective_settings so overrides apply"
```

---

### Task 5: Admin `/config` uses the shared store + structlog governance log

**Files:**
- Modify: `src/pacca/api/routes/admin.py` (logger; remove `_config_overrides`/`_effective`; rewrite GET/PATCH/DELETE config + GET metrics to use the shared accessor; add override logging)
- Modify: `tests/unit/test_config_api.py:48-54` (fixture must clear the shared store)

- [ ] **Step 1: Update the test fixture to the shared store (and run the suite to see what breaks)**

In `tests/unit/test_config_api.py`, replace the `reset_config_overrides` fixture body:

```python
@pytest.fixture(autouse=True)
def reset_config_overrides():
    from pacca.config.settings import clear_all_overrides

    clear_all_overrides()
    yield
    clear_all_overrides()
```

Run: `pytest tests/unit/test_config_api.py -v`
Expected: FAIL — `admin.py` still defines/uses `_config_overrides`, and the broken stdlib-kwargs `logger.info(...)` raises on PATCH. (This is the RED state for the admin rewrite.)

- [ ] **Step 2: Fix the admin logger (stdlib → structlog)**

In `src/pacca/api/routes/admin.py`, replace the logging import/init:
- `import logging` → `from ...config.logging import get_logger`
- `logger = logging.getLogger(__name__)` → `logger = get_logger(__name__)`

- [ ] **Step 3: Remove the private store; import the shared accessor**

In `admin.py`:
- Delete the `_config_overrides: dict[str, Any] = {}` definition (line ~72) and the `_effective(...)` helper.
- Change `from ...config.settings import get_settings` → `from ...config.settings import effective_settings, active_overrides, apply_overrides, clear_all_overrides`. After Step 4 rewrites every handler, confirm `get_settings` is no longer referenced in this file (`grep -n get_settings src/pacca/api/routes/admin.py` → no hits) so the dropped import doesn't leave a `NameError` (the metrics handler also used it).
- Add a private response builder so GET and PATCH stay DRY:

```python
def _config_response() -> ConfigResponse:
    es = effective_settings()
    return ConfigResponse(
        auto_approve_confidence_threshold=es.auto_approve_confidence_threshold,
        escalation_confidence_threshold=es.escalation_confidence_threshold,
        high_cost_threshold=es.high_cost_threshold,
        complexity_auto_approve_max=es.complexity_auto_approve_max,
        llm_retry_max_attempts=es.llm_retry_max_attempts,
        llm_retry_wait_min_seconds=es.llm_retry_wait_min_seconds,
        llm_retry_wait_max_seconds=es.llm_retry_wait_max_seconds,
        otel_enabled=es.otel_enabled,
        otel_service_name=es.otel_service_name,
        enable_autonomous_decisions=es.enable_autonomous_decisions,
        enable_rag=es.enable_rag,
        demo_mode=es.demo_mode,
        overrides_active=list(active_overrides().keys()),
    )
```

- [ ] **Step 4: Rewrite the four handlers**

`get_config` body → `return _config_response()`.

`patch_config` body (replace the override-loop + manual validation block):

```python
    updates_dict = updates.model_dump(exclude_none=True)
    try:
        apply_overrides(updates_dict)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)
        ) from exc
    for field_name, value in updates_dict.items():
        logger.info("config_override_applied", field=field_name, new_value=value)
    return _config_response()
```

`reset_config_overrides` route handler (DELETE `/config/overrides`) → clear via the shared store:

```python
    cleared = clear_all_overrides()
    for field_name in cleared:
        logger.info("config_override_cleared", field=field_name)
    return {"cleared_overrides": cleared}
```

`get_metrics` (GET `/metrics`) → read `enable_autonomous_decisions` (and any other displayed setting) from `effective_settings()` instead of `_effective(...)`. Replace each `_effective("name", s.name)` with `effective_settings().name`.

- [ ] **Step 5: Run the config API suite to verify it passes**

Run: `pytest tests/unit/test_config_api.py -v`
Expected: PASS — including `test_rejects_auto_approve_below_escalation_threshold` (422 from the `apply_overrides` ValueError), `test_invalid_update_does_not_partially_apply` (atomic rollback), and `test_metrics_returns_effective_values`.

- [ ] **Step 6: Commit**

```bash
git add src/pacca/api/routes/admin.py tests/unit/test_config_api.py
git commit -m "feat(admin): config API reads/writes the shared override store; fix stdlib->structlog logging"
```

---

### Task 6: Full-suite + live clinical gate regression

**Files:** none (verification only)

- [ ] **Step 1: Run the full unit/integration suite**

Run: `make test`
Expected: green. Capture the passing count: ____ . Confirm no test asserts the old 0.85/0.75 defaults or the removed `_config_overrides` symbol.

- [ ] **Step 2: Run the live golden-20 clinical gate (the behavior-preservation proof)**

Run: `set -a; source .env; set +a` then the project's live clinical gate (e.g. `pytest tests/clinical/test_clinical_accuracy.py -v` or the documented `make` target).
Expected: golden-20 routing distribution unchanged from `main` (no override active → 0.95/0.90 identical behavior). If any golden case shifts, STOP — the defaults change was not behavior-neutral; re-check Task 2.

- [ ] **Step 3: Mark PR #38 ready**

```bash
gh pr ready 38
```

Then update the PR checklist (Implementation + tests, Golden-20 gate) to checked.

---

## Out of scope (flagged)

- A formal DB `audit_logs` row for threshold changes (vs. the structlog record implemented here) — needs a session dependency wired into the admin route + test `dependency_overrides`. Separate PR.
- `complexity_auto_approve_max` appears unread by decision logic — separate cleanup.
- The `api/database.py` SQLite-vs-Postgres `users`-table bug (the untracked `_init_users.py` workaround) — unrelated.
