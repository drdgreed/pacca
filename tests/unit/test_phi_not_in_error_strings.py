"""
PHI containment in database exception strings (iter-28 chg-4).

The PRD's compliance matrix maps HIPAA "Never log PHI" to "structlog redaction
in src/pacca/config/tracing.py". No such redaction exists: tracing.py implements
THREAT-03 for OTel SPANS (exception type only) and the structlog processor chain
in config/logging.py contains no redaction step at all. So every
`logger.error(..., error=str(exc))` in the codebase wrote the exception verbatim.

For SQLAlchemy that is not a hypothetical. A StatementError renders as

    (IntegrityError) ... [SQL: INSERT INTO audit_logs ...]
    [parameters: ('...clinical text...',)]

and for audit_logs those parameters are input_summary, output_summary and
details -- the clinical content of a decision. AuditRepository._persist_
independently logs exactly that on failure.

Fixed at the engine (hide_parameters=True) rather than per-handler, because the
leak is a property of the exception object: a new `except ... error=str(e)`
added later would reintroduce it. These tests pin the engine setting AND its
observable effect.
"""

from __future__ import annotations

import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine

PHI = "Patient MRN 4417, stage IV NSCLC, EGFR L858R, on osimertinib"


async def _provoke_statement_error(engine) -> str:
    """Force a UNIQUE violation on a row holding clinical text; return str(exc)."""
    async with engine.begin() as conn:
        await conn.execute(
            text("CREATE TABLE t (id INTEGER PRIMARY KEY, phi TEXT NOT NULL UNIQUE)")
        )
    async with AsyncSession(engine) as s:
        await s.execute(text("INSERT INTO t (id, phi) VALUES (1, :p)"), {"p": PHI})
        await s.commit()
        with pytest.raises(Exception) as caught:
            await s.execute(text("INSERT INTO t (id, phi) VALUES (2, :p)"), {"p": PHI})
            await s.commit()
    return str(caught.value)


class TestBoundParametersDoNotReachExceptionStrings:
    @pytest.mark.asyncio
    async def test_default_engine_leaks_phi_this_is_the_bug(self) -> None:
        """Characterisation: without hide_parameters the leak is real.

        This test documents WHY the setting is needed. If SQLAlchemy ever
        changes its default, this fails and the fix can be revisited rather
        than cargo-culted.
        """
        engine = create_async_engine("sqlite+aiosqlite:///:memory:")
        try:
            assert PHI in await _provoke_statement_error(engine)
        finally:
            await engine.dispose()

    @pytest.mark.asyncio
    async def test_hide_parameters_engine_does_not_leak_phi(self) -> None:
        engine = create_async_engine("sqlite+aiosqlite:///:memory:", hide_parameters=True)
        try:
            msg = await _provoke_statement_error(engine)
            assert PHI not in msg
            assert "MRN 4417" not in msg
            # The operator still gets a diagnosable error.
            assert "UNIQUE constraint failed" in msg
        finally:
            await engine.dispose()


class TestApplicationEngineSetsHideParameters:
    def test_get_engine_passes_hide_parameters(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Pin the real construction path, not a hand-built engine.

        A test that only builds its own engine proves SQLAlchemy works; it does
        not prove PACCA configures it. This asserts the kwarg reaches
        create_async_engine from get_engine().
        """
        import pacca.db.session as session_mod

        captured: dict[str, object] = {}

        def fake_create_async_engine(url: str, **kwargs: object):  # type: ignore[no-untyped-def]
            captured.update(kwargs)
            captured["url"] = url
            return object()

        monkeypatch.setattr(session_mod, "create_async_engine", fake_create_async_engine)
        monkeypatch.setattr(session_mod, "_engine", None)
        session_mod.get_engine()

        assert captured.get("hide_parameters") is True, (
            "get_engine() must pass hide_parameters=True; without it every "
            "error=str(exc) handler writes bound parameters (PHI) to the log."
        )
