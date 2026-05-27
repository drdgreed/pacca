# BAA Inventory — Subcontractor Governance

> **Purpose.** Living matrix of every vendor in PACCA's production stack with Business Associate Agreement (BAA) and Data Processing Agreement (DPA) status. Required artifact for HIPAA compliance (45 CFR § 164.502(e)) and the FDA SaMD submission's "subcontractor governance" line of inquiry.
>
> **Update cadence.** When adding, changing, or removing any vendor. Quarterly review of all existing BAA expiration dates.
>
> **Owner.** Privacy Officer (currently: project owner). Assigned formally per `PACCA_PRD_v2.4_Consolidated.md` § 16.

## Status legend

| Status | Meaning |
|---|---|
| 🟢 Signed | Executed BAA on file; valid through specified date |
| 🟡 In progress | Term sheet sent or under legal review |
| 🔴 Required, not started | Vendor in production stack but no BAA conversation initiated |
| ⚪ Not required | Vendor does not process or store PHI |
| ⚫ Vendor refused | Escalation invoked; see Notes |

## Inventory

### LLM providers

| Vendor | Purpose | BAA Status | DPA Status | Last reviewed | Notes |
|---|---|---|---|---|---|
| Anthropic (direct API) | LLM inference (Claude Sonnet 4.5) for Decision Support + Medical Director agents | 🔴 Required, not started | n/a | 2026-05-27 | Two paths: (a) migrate to AWS Bedrock-routed to inherit AWS BAA; (b) negotiate direct BAA with Anthropic Enterprise tier (~6-8 weeks calendar). Path (a) is faster and consolidates BAAs. |
| AWS Bedrock | Alternative routing for Anthropic Claude | ⚪ Covered by AWS BAA | Covered by AWS BAA | — | Per [AWS HIPAA Eligible Services list](https://aws.amazon.com/compliance/hipaa-eligible-services-reference/) — Bedrock is HIPAA-eligible as of 2024. Single AWS BAA covers Bedrock, RDS, S3, ECS, Secrets Manager, CloudWatch. |
| Azure OpenAI | Embeddings (`text-embedding-3-large`) — planned upgrade from ChromaDB default | 🔴 Required (planned) | Covered by Azure BAA | — | BAA at Azure account level covers all Azure OpenAI deployments. Add only if/when the embedding upgrade ships. |
| OpenAI (direct API) | Not currently used | ⚫ N/A unless used | n/a | — | Direct OpenAI API not HIPAA-eligible. Any OpenAI model must be Azure-routed. |

### Data infrastructure

| Vendor | Purpose | BAA Status | DPA Status | Last reviewed | Notes |
|---|---|---|---|---|---|
| Postgres host (TBD: AWS RDS / Crunchy Bridge / Supabase) | Primary relational DB + pgvector retrieval (post-migration) | 🔴 Required | TBD | 2026-05-27 | All three options have HIPAA-eligible tiers. RDS preferred if AWS BAA already covers other services. |
| ChromaDB (current vector store) | Vector retrieval | ⚪ Not required (embedded local storage) | n/a | — | Migrating to pgvector eliminates this row entirely; until then, runs as a local file under `pacca_db/` — no external service. |
| AWS S3 (planned: backup storage) | PITR Postgres backups, embedding model checkpoints | ⚪ Covered by AWS BAA | Covered by AWS BAA | — | No separate BAA needed once AWS account-level BAA is signed. |

### Hosting & deployment

| Vendor | Purpose | BAA Status | DPA Status | Last reviewed | Notes |
|---|---|---|---|---|---|
| AWS (account-level master BAA) | Compute (ECS Fargate planned), storage, networking, secrets, logs | 🔴 Required | n/a | 2026-05-27 | **Single highest-leverage BAA to sign.** Unlocks Bedrock, RDS, S3, ECS, Secrets Manager, CloudWatch, ALB. Start here. |
| Docker Hub | Container image registry | ⚪ Not required | n/a | — | Images contain no PHI; build artifacts only. |
| GitHub (current: public repo) | Source code + CI | ⚪ Not required while public + synthetic-only | n/a | — | Becomes 🔴 if repo goes private with real fixtures, or if self-hosted CI runners process PHI. GitHub Enterprise offers BAA. |

### Observability & ops

| Vendor | Purpose | BAA Status | DPA Status | Last reviewed | Notes |
|---|---|---|---|---|---|
| Honeycomb / Datadog / Grafana Cloud (TBD) | OpenTelemetry trace + metric backend | 🔴 Required (planned) | TBD | — | All three offer HIPAA tiers. Selection pending. **PHI must be sanitized from span attributes** — extend `.githooks/pacca_guard.py` regex to OTel attribute serialization before sending. |
| AWS Secrets Manager (planned) | Runtime secret storage (replaces env-vars pattern) | ⚪ Covered by AWS BAA | n/a | — | — |
| AWS CloudWatch (planned) | Log aggregation | ⚪ Covered by AWS BAA | n/a | — | — |

### Clinical Review Board (activates at 200-case milestone)

| Vendor | Purpose | BAA Status | DPA Status | Last reviewed | Notes |
|---|---|---|---|---|---|
| External clinician #1 (specialty TBD) | Quarterly inter-rater κ scoring | 🔴 Required (planned, weeks 1-6 of push) | n/a | — | See [CRB_SOURCING.md](CRB_SOURCING.md) for sourcing channels + BAA template language |
| External clinician #2 (specialty TBD) | Same | 🔴 Required (planned, weeks 1-6) | n/a | — | Same |
| External clinician #3 (specialty TBD) | Same | 🔴 Required (planned, weeks 1-8) | n/a | — | Same; #3 is a "rotation" seat tied to the iteration's specialty focus |
| Review portal (TBD: REDCap / Castor EDC / spreadsheet) | Sample distribution + score collection | ⚪ Not yet selected | TBD | — | Evaluation deferred until CRB launches. Current default: CSV export per `CASE_AUTHORING_GUIDE.md` § 12. |

### Regulatory & legal

| Vendor | Purpose | BAA Status | DPA Status | Last reviewed | Notes |
|---|---|---|---|---|---|
| Regulatory consultant (TBD) | FDA SaMD pathway (510(k) or De Novo) | 🔴 Required (planned, ~6 months before 500-case milestone) | n/a | — | See [REGULATORY_RFP.md](REGULATORY_RFP.md) |
| Healthcare privacy counsel | BAA template review, breach response, HIPAA Privacy/Security Rule compliance | ⚪ Not yet engaged | n/a | — | Recommend engagement before signing first BAA. Many firms offer flat-fee initial review (~$2K-5K). |
| Cyber liability insurance | E&O + cyber liability with HIPAA rider | ⚪ Not yet bound | n/a | — | Required by most payer contracts. Typical pre-pilot milestone. |

## Escalation procedure (when a required vendor refuses BAA)

1. **Document the refusal.** Email or written response goes into the Notes column with date.
2. **Evaluate alternatives.** Is there a BAA-eligible competitor at acceptable cost / quality?
3. **Escalate to privacy counsel.** Can the vendor be retained under stricter contract terms (data residency, prohibition on PHI processing, indemnification)?
4. **Last resort: remove from the stack.** Document the architectural change in `docs/DECISIONS.md` so the audit trail captures the cause.

## Quarterly review checklist

- [ ] All 🟡 statuses resolved to 🟢 or ⚫ (decision recorded)
- [ ] All 🟢 statuses have BAA expiration date noted; renew if <90 days remaining
- [ ] New vendors since last review are tracked
- [ ] Removed vendors are archived in-place (do NOT delete rows; mark `removed YYYY-MM-DD` in Notes)
- [ ] Cross-reference with `PUSH_TO_300_PLAN.md` milestones — does any planned engineering work depend on a BAA that isn't 🟢 yet?

---

*Last updated: 2026-05-27. Format: append-only; rows are never deleted, only marked removed.*
