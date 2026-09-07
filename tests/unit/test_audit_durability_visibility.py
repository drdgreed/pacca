"""
Audit-write failures are visible in aggregate (iter-29).

AuditRepository still does not raise when an audit write fails -- that is a
deliberate decision recorded in AuditRepository.log's durability note, and this
change does not reverse it. What these tests pin is that the failure stops being
invisible: it increments a monotonic counter reported on /api/v1/metrics, and
marks an audit_durability check on /health.

The distinction matters for what the tests assert. There is no test here that a
request fails, because it must not. The assertions are all about detectability.
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from pacca.api.main import app
from pacca.utils import audit_durability


@pytest.fixture(autouse=True)
def _clean_counters():
    audit_durability.reset_for_tests()
    yield
    audit_durability.reset_for_tests()


class TestCounter:
    def test_starts_at_zero_and_not_degraded(self) -> None:
        snap = audit_durability.snapshot()
        assert snap.failures_total == 0
        assert snap.last_failure_at is None
        assert snap.degraded is False

    def test_counts_and_records_last_failure(self) -> None:
        audit_durability.record_audit_write_failure("decision_created")
        audit_durability.record_audit_write_failure("request_submitted")
        snap = audit_durability.snapshot()
        assert snap.failures_total == 2
        assert snap.last_failure_action == "request_submitted"
        assert snap.last_failure_at is not None
        assert snap.degraded is True

    def test_snapshot_is_immutable(self) -> None:
        """Callers get a value, not a handle on live state."""
        snap = audit_durability.snapshot()
        with pytest.raises((AttributeError, TypeError)):
            snap.failures_total = 99  # type: ignore[misc]

    def test_recording_never_raises(self) -> None:
        """It runs inside a best-effort failure branch; it must not be able to
        convert a logged failure into an unhandled exception."""
        audit_durability.record_audit_write_failure(None)
        assert audit_durability.snapshot().failures_total == 1


class TestHealthEndpoint:
    """/health on the real app -- api/main.py's, not api/routes/health.py's.

    That router is never mounted (see TestTheHealthSurfaceThatActuallyExists),
    so it is the wrong place to report anything an operator needs to see.
    """

    def test_reported_when_zero(self) -> None:
        """A signal that only appears once non-zero cannot be alerted on,
        because the alert has nothing to bind to until it is too late."""
        with TestClient(app) as client:
            body = client.get("/health").json()
        assert body["audit_durability"] == "healthy"
        assert body["audit_write_failures_total"] == 0
        assert body["audit_last_failure_at"] is None

    def test_degraded_after_a_failure(self) -> None:
        audit_durability.record_audit_write_failure("decision_created")
        with TestClient(app) as client:
            body = client.get("/health").json()
        assert body["audit_durability"] == "degraded"
        assert body["audit_write_failures_total"] == 1
        assert body["audit_last_failure_at"] is not None

    def test_status_and_code_unchanged_when_degraded(self) -> None:
        """The load-bearing assertion of this whole change.

        /health is wired to the Dockerfile healthcheck and docker-compose. If a
        failed audit write flipped `status` or the response code, a transient
        database blip would pull healthy containers out of rotation -- trading a
        compliance gap for an outage. The condition is reported in its own
        field precisely so that it can be alerted on without being acted on by
        a load balancer.
        """
        audit_durability.record_audit_write_failure("decision_created")
        with TestClient(app) as client:
            resp = client.get("/health")
        assert resp.status_code == 200
        assert resp.json()["status"] == "ok"


class TestTheHealthSurfaceThatActuallyExists:
    """api/routes/health.py is dead code -- its router is never included.

    Pinned as a fact, not as an aspiration. If someone mounts that router
    later, these fail and force a decision about the duplicate /health rather
    than letting two definitions of the same path coexist silently.
    """

    def test_unmounted_router_paths_do_not_resolve(self) -> None:
        with TestClient(app) as client:
            assert client.get("/health/live").status_code == 404
            assert client.get("/health/ready").status_code == 404
            assert client.get("/api/v1/metrics").status_code == 404

    def test_dockerfile_healthcheck_probes_a_path_that_resolves(self) -> None:
        """The Dockerfile curled /health/live, which 404s -- `curl -f` exits
        non-zero on 404, so the container healthcheck could only ever fail."""
        import re
        from pathlib import Path

        dockerfile = Path(__file__).resolve().parents[2] / "Dockerfile"
        cmd = next(
            line
            for line in dockerfile.read_text().splitlines()
            if line.strip().startswith("CMD curl")
        )
        probed = re.search(r"localhost:8000(/\S*?)\s", cmd + " ").group(1)
        with TestClient(app) as client:
            assert client.get(probed).status_code == 200, (
                f"Dockerfile HEALTHCHECK probes {probed}, which does not return 200"
            )


class TestTheCounterIsWiredToRealFailures:
    """
    The tests above prove the counter reports. These prove it is CONNECTED.

    A counter that is correct but never called is the same defect this change
    exists to fix, one level up: a signal that looks healthy because nothing
    reaches it. Both of AuditRepository's non-persisting branches are exercised
    through the real `log()` entry point.
    """

    @pytest.mark.asyncio
    async def test_unsupported_bind_increments_the_counter(self) -> None:
        """The refuse-to-write branch. From the caller's side the outcome is
        identical to a failed write -- no audit row -- so it must count."""
        from unittest.mock import MagicMock

        from pacca.db.repository import AuditRepository

        session = MagicMock()
        session.bind = object()  # not an AsyncEngine -> refused

        entry = await AuditRepository(session).log(
            action="decision_created", actor="agent", actor_type="agent"
        )

        assert entry is not None, "log() still returns its value snapshot"
        assert audit_durability.snapshot().failures_total == 1
        assert audit_durability.snapshot().last_failure_action == "decision_created"

    @pytest.mark.asyncio
    async def test_write_failure_increments_the_counter_and_does_not_raise(self) -> None:
        """The except branch. The request must still succeed -- that is the
        documented decision this change does not reverse."""
        from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine

        from pacca.db.repository import AuditRepository

        engine = create_async_engine("sqlite+aiosqlite:///:memory:")
        try:
            async with AsyncSession(engine) as session:
                # The audit table is never created, so the INSERT raises.
                entry = await AuditRepository(session).log(
                    action="request_submitted", actor="system", actor_type="system"
                )
            assert entry is not None
            assert audit_durability.snapshot().failures_total == 1
            assert audit_durability.snapshot().last_failure_action == "request_submitted"
        finally:
            await engine.dispose()
