"""Unit tests for the shared runtime-override store + effective_settings()."""

from collections.abc import Iterator

import pytest

from pacca.config.settings import (
    active_overrides,
    apply_overrides,
    clear_all_overrides,
    effective_settings,
    get_settings,
)


@pytest.fixture(autouse=True)
def _reset_overrides() -> Iterator[None]:
    clear_all_overrides()
    yield
    clear_all_overrides()


def test_effective_equals_base_when_no_overrides() -> None:
    s = effective_settings()
    base = get_settings()
    assert s.model_dump() == base.model_dump()


def test_apply_override_is_reflected() -> None:
    apply_overrides({"high_cost_threshold": 40_000})
    assert effective_settings().high_cost_threshold == 40_000
    assert "high_cost_threshold" in active_overrides()


def test_apply_override_does_not_mutate_base() -> None:
    base_before = get_settings().high_cost_threshold
    apply_overrides({"high_cost_threshold": 1})
    assert get_settings().high_cost_threshold == base_before  # cached base untouched


def test_rejects_auto_approve_not_above_escalation() -> None:
    # Use the real default escalation threshold (equal → must reject, not just below).
    esc = get_settings().escalation_confidence_threshold
    with pytest.raises(ValueError, match=r"greater than|escalation band"):
        apply_overrides({"auto_approve_confidence_threshold": esc})


def test_invalid_override_is_atomic() -> None:
    apply_overrides({"high_cost_threshold": 70_000})  # valid baseline override
    with pytest.raises(ValueError):
        apply_overrides(
            {
                "llm_retry_max_attempts": 9,  # valid
                "auto_approve_confidence_threshold": 0.10,  # invalid (<= escalation)
            }
        )
    # Neither field from the failed batch applied; the earlier valid override survives.
    assert "llm_retry_max_attempts" not in active_overrides()
    assert active_overrides()["high_cost_threshold"] == 70_000


def test_clear_all_overrides_returns_cleared_keys() -> None:
    apply_overrides({"high_cost_threshold": 40_000, "demo_mode": False})
    cleared = clear_all_overrides()
    assert set(cleared) == {"high_cost_threshold", "demo_mode"}
    assert active_overrides() == {}


def test_rejects_out_of_range_field_value() -> None:
    """Fix 1: model_validate enforces per-field constraints; negative cost threshold must fail."""
    with pytest.raises(ValueError):
        apply_overrides({"high_cost_threshold": -1})
    # Rollback: override must not have been applied.
    assert "high_cost_threshold" not in active_overrides()


def test_rejects_unknown_field() -> None:
    """Fix 2: unknown keys must be rejected before any mutation."""
    with pytest.raises(ValueError, match="Unknown config field"):
        apply_overrides({"totally_bogus_field": 42})
    assert active_overrides() == {}
