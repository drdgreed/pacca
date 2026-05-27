# Engineering Runbook — Postgres Hardening

> **Status.** Queued for week 13+ of `PUSH_TO_300_PLAN.md`. Largest scope of the four runbooks; lowest time pressure (production ops, not BAA-blocking). Recommend sequencing AFTER `bedrock-routing.md` and `pgvector-migration.md` so this work consolidates the production data tier in one effort.
>
> **Goal.** Apply four production-grade Postgres patterns: (1) `pgcrypto` for column-level PHI encryption, (2) `PgBouncer` for connection pooling, (3) `pgaudit` for HIPAA-grade audit logging, (4) PITR (point-in-time recovery) backup with tested restore procedure.
>
> **Estimated effort.** ~4.5 engineering days (34 hours).
>
> **Estimated infra cost.** $10-25/month incremental (PgBouncer sidecar compute + pgaudit log retention storage).

## Pre-conditions

- [ ] Postgres host BAA signed (per `BAA_INVENTORY.md`)
- [ ] Hosting provider supports the required extensions:
  - RDS: pgcrypto + pgaudit available via parameter group; PITR included
  - Crunchy Bridge: all three plus PITR included in standard tier
  - Supabase: pgcrypto + PITR included; pgaudit in pro tier
- [ ] Application code maps PHI columns clearly (current state: ad-hoc; this runbook makes it explicit)
- [ ] Decision made about deployment target (PgBouncer sidecar vs hosted pooling service)
- [ ] Observability backend signed for log ingestion (see `BAA_INVENTORY.md`)

## Procedure

### Sub-runbook 1 — pgcrypto column-level encryption (~12 hours)

**Goal.** Encrypt PHI fields at rest such that even a database compromise doesn't reveal patient identifiers.

#### Step 1.1 — Identify PHI columns

Audit the schema for columns that contain or could contain PHI:

```sql
-- Likely candidates in PACCA:
\d authorizations           -- member_id, dob (if any)
\d audit_log                -- actor_id (if it's a member-facing actor)
\d feedback                 -- any free-text rationales
```

Document in `docs/security/phi_columns.md`. This becomes the source of truth for what gets encrypted.

#### Step 1.2 — Enable pgcrypto + add encryption key

```sql
CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- Key lives in AWS Secrets Manager, NOT in the database
-- App passes the key to pgp_sym_encrypt/decrypt at query time
```

The encryption key is a 32-byte secret stored in AWS Secrets Manager. The application reads it at startup and passes it as a query parameter, NEVER stored in Postgres.

#### Step 1.3 — Schema migration

For each PHI column, add an encrypted variant and migrate:

```sql
-- Example for member_id
ALTER TABLE authorizations ADD COLUMN member_id_encrypted bytea;
UPDATE authorizations SET member_id_encrypted = pgp_sym_encrypt(member_id, current_setting('pacca.encryption_key'));
ALTER TABLE authorizations DROP COLUMN member_id;
ALTER TABLE authorizations RENAME COLUMN member_id_encrypted TO member_id;
```

Note: `current_setting('pacca.encryption_key')` is a session-level variable set by the application on each connection.

#### Step 1.4 — App-layer integration

In SQLAlchemy models, use a TypeDecorator that transparently encrypts/decrypts:

```python
class EncryptedString(TypeDecorator):
    impl = LargeBinary

    def bind_expression(self, value):
        return func.pgp_sym_encrypt(value, func.current_setting('pacca.encryption_key'))

    def column_expression(self, column):
        return func.pgp_sym_decrypt(column, func.current_setting('pacca.encryption_key'))
```

The app reads the key from Secrets Manager at startup and sets it per connection via `SET pacca.encryption_key = 'xxx'`.

#### Step 1.5 — Test round-trip

```python
def test_phi_encryption_round_trip():
    auth = Authorization(member_id="M-12345")
    db.session.add(auth)
    db.session.commit()
    # Read back
    loaded = db.session.query(Authorization).first()
    assert loaded.member_id == "M-12345"
    # Verify ciphertext in raw query
    raw = db.session.execute("SELECT member_id FROM authorizations").first()
    assert raw[0] != b"M-12345"  # raw bytes are ciphertext
```

#### Risks for sub-runbook 1

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| Encrypted columns break ad-hoc psql queries | High | Low | Document the `pgp_sym_decrypt()` pattern in `docs/security/decrypting_phi.md`; train any human with DB access |
| Encryption key loss = data loss | Very low | Catastrophic | Key has 3-of-5 split via Shamir's Secret Sharing; key version rotation runbook; backup of encrypted key store |
| Index on encrypted column doesn't work | Certain | Medium | Indexes on encrypted columns are useless. If you need to search by `member_id`, use a deterministic hash for the search index alongside the encrypted column |

---

### Sub-runbook 2 — PgBouncer connection pooling (~6 hours)

**Goal.** Reduce per-request connection overhead under production load; protect Postgres from connection storms.

#### Step 2.1 — Deploy PgBouncer

Two options:
- **Sidecar** in the ECS task definition (preferred): PgBouncer container co-located with app container, communicates via localhost
- **Standalone service**: separate ECS task for PgBouncer, behind a service-discovery name

Sidecar is simpler ops; standalone scales independently. Pick sidecar unless you anticipate multiple app services sharing a pool.

#### Step 2.2 — Configure pooling

```ini
# pgbouncer.ini
[databases]
pacca = host=<postgres-host> dbname=pacca

[pgbouncer]
listen_port = 6432
listen_addr = 127.0.0.1  # localhost only when sidecar
pool_mode = session       # transaction mode is faster but breaks SET LOCAL + prepared statements
max_client_conn = 1000
default_pool_size = 25
```

`pool_mode = session` is the safe default for SQLAlchemy. Switch to `transaction` only after thorough testing — it WILL break prepared statements, `SET LOCAL`, and any session-state-dependent patterns.

#### Step 2.3 — SQLAlchemy connection string

```python
# old: postgresql://user:pass@db-host:5432/pacca
# new: postgresql://user:pass@localhost:6432/pacca
```

The application now talks to PgBouncer (localhost:6432), which talks to Postgres on its behalf.

#### Step 2.4 — Load test

Run a simulated production workload (~100 concurrent users, ~10 req/sec each) and verify:
- Postgres connection count stays bounded (≤ `default_pool_size` × number of pgbouncer instances)
- p95 latency unchanged or improved
- No "could not allocate connection" errors

#### Risks for sub-runbook 2

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| Transaction-mode pooling breaks SET LOCAL or prepared statements | High if transaction mode chosen | High | Start with session mode; migrate to transaction mode only after auditing all `SET LOCAL` / `PREPARE` usage |
| PgBouncer becomes single point of failure | Medium | High | Sidecar pattern fails-over with app; if standalone, run ≥ 2 instances behind a load balancer |
| Server-side prepared statements behave unexpectedly | Medium | Medium | SQLAlchemy 2.0 + asyncpg uses server-side prepared statements; pgbouncer in transaction mode breaks this. Session mode is fine |

---

### Sub-runbook 3 — pgaudit audit logging (~4 hours)

**Goal.** Capture all PHI-table writes for HIPAA audit trail; satisfy 45 CFR § 164.312(b) audit controls requirement.

#### Step 3.1 — Enable extension

```sql
CREATE EXTENSION IF NOT EXISTS pgaudit;

-- Parameter group / postgresql.conf
ALTER SYSTEM SET pgaudit.log = 'write, ddl';
ALTER SYSTEM SET pgaudit.log_catalog = off;
ALTER SYSTEM SET pgaudit.log_parameter = on;
SELECT pg_reload_conf();
```

`write, ddl` captures: INSERT, UPDATE, DELETE, plus all schema changes. Excludes SELECT (which would explode log volume) — adjust if your compliance requirements demand read-auditing.

#### Step 3.2 — Per-table audit

For high-sensitivity tables (authorizations, audit_log, anything with PHI), enable more verbose auditing:

```sql
ALTER TABLE authorizations SET (pgaudit.log = 'read, write');
```

#### Step 3.3 — Log shipping

Postgres logs include the pgaudit output. Ship to your observability backend:
- AWS RDS: enable Postgres logs export to CloudWatch
- Crunchy Bridge / Supabase: configure log syslog forwarding to your aggregator

Retention: HIPAA requires 6 years. Configure accordingly.

#### Step 3.4 — Log volume monitoring

Add an alert: if Postgres log volume exceeds 1 GB/day, investigate. Common causes:
- A new endpoint generating high write volume to an audited table
- A misconfigured pgaudit policy logging too aggressively
- A scan job iterating over the database

#### Risks for sub-runbook 3

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| Log volume explodes | Medium | Medium | Start with `write, ddl` (no reads); add reads only for the most sensitive tables |
| Log retention costs balloon | Low | Medium | Tier old logs to S3 Glacier ($0.001/GB/month) after 90 days hot |
| Sensitive parameter values logged | Medium | High | `pgaudit.log_parameter = on` will log bind parameters. Disable if you have queries that bind PHI without already encrypting it. Cross-check after enabling |

---

### Sub-runbook 4 — PITR backup with tested restore (~8 hours)

**Goal.** Enable point-in-time recovery so you can restore the database to any moment in the last N days, then prove the restore procedure works.

#### Step 4.1 — Enable continuous WAL archiving

Hosting-provider-specific:
- **RDS**: PITR enabled by default; configure backup retention to 35 days (max)
- **Crunchy Bridge**: PITR included; configure retention via dashboard
- **Supabase**: PITR available in Pro tier; configure via dashboard

#### Step 4.2 — Document the restore procedure

Write `docs/runbooks/postgres_pitr_restore.md` covering:
1. Identify the restore target time
2. Provision a new instance from the PITR backup at that time
3. Verify data integrity
4. Cut over application traffic
5. Decommission the old instance

Procedure varies by provider; reference the provider's runbook.

#### Step 4.3 — Quarterly restore drill

Schedule (in a calendar, not a runbook) a quarterly drill:
1. Pick a random "incident time" from the last 24 hours
2. Restore to a test instance at that time
3. Verify data matches expectations
4. Record the time-to-restore in a `docs/runbooks/restore_drill_log.md`
5. Decommission the test instance

The drill is critical. A backup you've never restored is a hypothesis, not a backup.

#### Risks for sub-runbook 4

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| Untested restore procedure fails when actually needed | Without drill: high. With quarterly drill: low | Catastrophic | Drill quarterly. No exceptions |
| PITR retention too short for compliance | Low | Medium | HIPAA doesn't mandate specific retention but recommends consistent with privacy/security risk assessment. 30-35 days is the practical norm |
| Restored database has stale encryption keys | Medium | High | Document key versioning in the restore runbook; PITR restores point-in-time including encryption-key-version metadata if you key-rotate |

## Combined acceptance criteria

- [ ] PHI columns encrypted; round-trip test passes
- [ ] Encryption key in Secrets Manager; not in Postgres
- [ ] PgBouncer deployed; under load, connection count stays bounded
- [ ] App connects via PgBouncer; no latency regression
- [ ] pgaudit logs all writes + DDL to all PHI tables; shipped to observability backend
- [ ] Log retention configured for 6 years (HIPAA)
- [ ] PITR enabled with ≥ 30-day retention
- [ ] Restore procedure documented; first quarterly drill completed
- [ ] All tests pass under the new ops layer

## Rollback per sub-runbook

| Sub-runbook | Rollback |
|---|---|
| pgcrypto | Decrypt columns in place; drop encrypted variants; remove TypeDecorator. ~4 hours of work; data is preserved |
| PgBouncer | Change SQLAlchemy connection string back to direct Postgres; remove sidecar from task definition |
| pgaudit | `ALTER SYSTEM SET pgaudit.log = '';` + reload config |
| PITR | Configuration-only change; rollback is reverting the retention setting |

## Companion docs

- [`bedrock-routing.md`](bedrock-routing.md) — LLM-layer migration (unrelated to this work)
- [`pgvector-migration.md`](pgvector-migration.md) — vector DB migration (prerequisite if you want a single combined data-tier cutover)
- [`embedding-upgrade.md`](embedding-upgrade.md) — embedding model upgrade (unrelated to this work)
- [`BAA_INVENTORY.md`](../BAA_INVENTORY.md) — Postgres host BAA status
- (future) `docs/security/phi_columns.md` — created in Step 1.1
- (future) `docs/runbooks/postgres_pitr_restore.md` — created in Step 4.2
- (future) `docs/runbooks/restore_drill_log.md` — created with first quarterly drill

---

*Last updated: 2026-05-27. Status: PLANNED, not yet executed.*
