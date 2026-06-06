from sqlalchemy.orm import declarative_base

# Declarative base for the auth `users` table (see api/models/user.py).
#
# There is intentionally NO standalone engine or session here. The `users`
# table is created in the application's primary database via the ASYNC engine
# (db/session.py) at startup — see the lifespan in api/main.py — so it lands in
# whatever DATABASE_URL points to (Postgres in compose, SQLite in local dev),
# the same database the /register and /login handlers query.
#
# History: this module used to define a sync engine hardcoded to
# sqlite:///./pacca.db and create the users table there. Under Postgres the
# table never existed in the DB the handlers queried, so /register and /login
# 500'd with 'relation "users" does not exist'. The sync engine + SessionLocal
# were dead code (no runtime caller) and were removed.
Base = declarative_base()
