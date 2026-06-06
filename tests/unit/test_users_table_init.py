"""Regression: the auth `users` table is created in the SAME async database the
/register and /login handlers query — not a separate, hardcoded sync SQLite engine.

History: main.py used to create `users` via api/database.py's sync SQLite engine.
In local SQLite dev both engines point at ./pacca.db so it worked, but under
Postgres they diverge — `users` was created in SQLite while the handlers queried
Postgres, so /register and /login 500'd with 'relation "users" does not exist'.
The fix creates the table via the async engine (get_engine) at startup.
"""

import inspect


def test_users_table_created_in_same_async_db_not_separate_sqlite() -> None:
    import pacca.api.database as db_module
    import pacca.api.main as main_module

    lifespan_src = inspect.getsource(main_module.lifespan)
    assert "create_all" in lifespan_src, "lifespan must create the users table"
    assert "sync_engine" not in lifespan_src, (
        "users table must NOT be created on the legacy sync SQLite engine; "
        "create it via the async engine (get_engine) so it lands in the "
        "configured database (Postgres in compose, SQLite in dev)."
    )
    # api/database.py must no longer define a standalone (SQLite) engine or sync
    # session — only the declarative Base remains.
    assert not hasattr(db_module, "engine"), (
        "api/database.py must not define a standalone sync SQLite engine."
    )
    assert not hasattr(db_module, "SessionLocal"), (
        "api/database.py must not define a sync SessionLocal."
    )
