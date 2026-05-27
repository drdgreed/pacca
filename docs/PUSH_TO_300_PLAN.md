# Push to 300 Cases — 12-Week Plan

> **Goal.** Take PACCA's clinical evaluation dataset from 100 cases to 300 cases in 12 weeks, while operationalizing the strategic-ops layer (Clinical Review Board active, BAA inventory current, regulatory consultant pipeline warmed) required for the eventual 500-case SaMD-grade milestone.
>
> **Premise.** This is an aggressive timeline. At the SME tool's measured rate of 6-10 cases/day, 67 cases/month is achievable but requires sustained focus. Parallel workstreams (CRB sourcing, BAA negotiation, optional engineering) must run alongside SME authoring, not after it.
>
> **Living document.** Update at each weekly checkpoint. The dates are aspirational anchors; the gates are the actual decision points.

## Critical insight: what dictates the pace

| Workstream | Pace constraint |
|---|---|
| SME case authoring | Project owner's available focus time. Roughly 3 cases/working day at sustained pace. |
| CRB sourcing | **8-12 weeks per panelist** from outreach to executed BAA. Must start week 1 to have a panel at week 6 (200-case CRB activation threshold). |
| BAA negotiation (AWS, observability vendor, Postgres host) | 2-6 weeks per vendor, parallelizable. Must complete before production-tier engineering begins. |
| Engineering (optional during push) | Limited by project-owner time after SME authoring. Treat as opportunistic. |
| Regulatory consultant outreach | Defer until after 300 hits (per `REGULATORY_RFP.md`). Don't burn cycles on it during the push. |

The **gating constraint is CRB sourcing**, not SME throughput. SME work can flex; CRB calendar time cannot.

## The 12-week roadmap

### Phase A — Foundation (weeks 1-2)

| Week | SME authoring | CRB sourcing | BAA | Engineering | Decision gate |
|---|---|---|---|---|---|
| 1 | 15 cases (warm-up; aim for batch A.1 of `DATASET_GROWTH_ROADMAP.md`) | **Outreach to ≥ 5 candidates** via Tier 1 channels per `CRB_SOURCING.md` | **Sign AWS account-level BAA** (single highest-leverage move per `BAA_INVENTORY.md`) | (none planned) | End of week 1: ≥ 5 CRB candidates contacted, AWS BAA in progress |
| 2 | 15 cases (total: 130) | Intake interviews (30 min each) for any candidates who responded | Begin Postgres host BAA conversation (RDS / Crunchy / Supabase selection) | (none planned) | End of week 2: ≥ 2 CRB candidates moved to BAA-sent status |

### Phase B — Velocity ramp (weeks 3-6)

| Week | SME authoring | CRB sourcing | BAA | Engineering | Decision gate |
|---|---|---|---|---|---|
| 3 | 17 cases (total: 147) | BAA negotiation with first 2-3 candidates | Postgres host BAA in legal review | (none planned) | Mid-week 3 checkpoint: at 80%+ of plan? If not, re-pace. |
| 4 | 17 cases (total: 164) | Continue BAA negotiation | AWS BAA signed; Postgres BAA in legal | **OPTIONAL:** kick off Bedrock-routed Claude migration (~2.5 days, blocks Anthropic BAA need) | End of week 4: ≥ 1 CRB BAA close to execution? |
| 5 | 17 cases (total: 181) | First panelist onboarding + scoring rubric calibration | Observability vendor selection (Honeycomb / Datadog / Grafana) + BAA conversation | Bedrock migration finishing or pgvector migration starting (per `BAA_INVENTORY.md` consolidation rationale) | End of week 5: production stack BAA situation green or amber? |
| 6 | 19 cases (total: 200) — **200-case CRB activation milestone** | **First CRB quarterly cycle begins** (assuming ≥ 2 panelists active) | Observability vendor BAA execution | Postgres hardening planning (don't start work until BAAs signed) | **Decision gate: is CRB active?** If not, defer milestone-claim and adjust plan. |

### Phase C — Hardening + push (weeks 7-12)

| Week | SME authoring | CRB sourcing | BAA | Engineering | Decision gate |
|---|---|---|---|---|---|
| 7 | 17 cases (total: 217) | First CRB cycle in progress (4-8 hours of scoring per panelist over 2-3 weeks) | Final BAA cleanup | pgvector migration (~4 days) if not already done | — |
| 8 | 17 cases (total: 234) | Continue CRB cycle 1 | All required BAAs signed | Embedding upgrade (~2 days) if A/B benchmark passes | — |
| 9 | 17 cases (total: 251) | CRB cycle 1 wrap-up + κ calculation + findings doc draft | — | Postgres hardening (~4.5 days) — pgcrypto, PgBouncer, pgaudit, PITR | End of week 9: κ ≥ 0.80? If not, surface the disagreements; defer the SaMD-grade claim. |
| 10 | 17 cases (total: 268) | Publish `docs/findings/clinical-review-board-2026-Q3.md` | — | Postgres hardening continuing | — |
| 11 | 17 cases (total: 285) | CRB cycle 2 sample preparation | — | Engineering finalization + smoke tests | — |
| 12 | 15 cases (total: 300) — **300-case general-payer-deployment milestone** | CRB cycle 2 begins | — | Final integration testing | **Decision gate: is dataset at 300 with κ ≥ 0.80 from cycle 1?** If yes: ready for first payer pilot conversation. |

### Daily / weekly cadence

| Frequency | Activity |
|---|---|
| Daily | 3-4 cases authored via SME tool. Aim for completion before end of day so you don't carry "case debt" into the next day. |
| Weekly (Monday) | Re-read this plan. Update last week's "actual cases" column (add below) vs. plan. Adjust the current week if behind. |
| Weekly (Friday) | Cross-reference `BAA_INVENTORY.md` quarterly review checklist items that came due this week. |
| Bi-weekly | Open a small (~10 LOC) update PR to this plan with the actual-vs-plan delta. Treat the plan as a versioned artifact, not a static doc. |

### Actual cases by week (update as you go)

| Week | Planned cumulative | Actual cumulative | Notes |
|---|---|---|---|
| 1 | 115 | — | |
| 2 | 130 | — | |
| 3 | 147 | — | |
| 4 | 164 | — | |
| 5 | 181 | — | |
| 6 | 200 | — | |
| 7 | 217 | — | |
| 8 | 234 | — | |
| 9 | 251 | — | |
| 10 | 268 | — | |
| 11 | 285 | — | |
| 12 | 300 | — | |

## Critical path

```
[Week 1: CRB outreach + AWS BAA] → [Week 2-5: CRB BAA negotiation] → [Week 6: CRB active]
                                                                          ↓
[Weeks 1-12: SME authoring at 17/week]  ──────────────────────────→  [Week 12: 300 cases]
                                                                          ↓
[Week 6-9: CRB cycle 1] → [Week 9: findings doc + κ] → [Week 12: ready for payer pilot]
```

If any of these break:

- **CRB sourcing slips** (e.g., zero panelists by week 4): the 200-case CRB activation slides; consider lowering the threshold target to 150 cases for cycle 1, or accept a 16-week timeline.
- **SME authoring slips** (e.g., < 14 cases/week sustained): re-pace to 16 weeks. Don't compromise case quality to hit the calendar.
- **BAA stalls** on a critical vendor: invoke the escalation procedure in `BAA_INVENTORY.md`. If AWS BAA stalls, the entire Bedrock + RDS + S3 stack is blocked — switch deployment target to GCP or Azure as backup.

## Decision gates

These are explicit "stop and re-plan" checkpoints, not soft reviews. At each gate, the answer must be unambiguous before proceeding.

### Gate 1 — End of week 2: foundation gate

**Pass criteria:**
- ≥ 5 CRB candidates contacted, ≥ 2 with intake interview scheduled
- AWS BAA conversation started
- Cases on plan (≥ 130)

**Fail action:** Extend Phase A by 1-2 weeks. Re-evaluate Phase B + C timing.

### Gate 2 — End of week 6: CRB activation gate

**Pass criteria:**
- 200 cases authored
- ≥ 2 CRB panelists with signed BAA, scoring rubric calibration complete, ready for cycle 1
- AWS BAA signed; ≥ 1 other production-tier BAA signed

**Fail action:** If CRB not active, defer the 200-case milestone claim. Continue authoring toward 300, run cycle 1 retroactively when CRB activates. Do NOT manufacture a CRB result.

### Gate 3 — End of week 9: κ gate

**Pass criteria:**
- 251 cases authored
- CRB cycle 1 findings document drafted
- Cohen's κ ≥ 0.80 panelist-to-system; inter-panelist κ ≥ 0.70

**Fail action:** If κ < 0.80, this is a **signal worth investigating, not a failure to hide**. Identify which cases the panel disagrees on. Per `CASE_AUTHORING_GUIDE.md` § 12.4, mark those cases `provisional` in `CASE_PROVENANCE.md` and queue for revision in the next iteration. Continue the plan; SaMD-grade claim defers but the project doesn't stall.

### Gate 4 — End of week 12: 300-case milestone

**Pass criteria:**
- 300 cases authored
- Cycle 1 findings published
- Production-tier BAAs current
- Engineering hardening complete OR explicitly deferred with rationale

**Pass action:** Ready for first payer pilot conversation. Begin `REGULATORY_RFP.md` consultant outreach (6-month lead to the eventual 500 milestone).

**Fail action:** Re-pace. The milestone moves; nothing else has to.

## Risk register

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| CRB sourcing yields < 2 active panelists by week 6 | Medium | High | Tier 1 channels are highest-yield; cast widely in week 1. Fallback to locum agency (Tier 2) by week 3 if Tier 1 not converting. |
| Project owner burns out on sustained 17-case/week pace | Medium | High | Build in a buffer week at week 4 (reduced to 12 cases) if signal of fatigue appears. Sustainability > velocity. |
| Engineering work compresses SME authoring time | High if engineering is attempted during push | Medium | Don't make engineering required-path. The pgvector + Bedrock + Postgres-hardening work can defer to weeks 13-16 without impacting 300-case milestone. |
| CRB κ < 0.80 on cycle 1 | Medium | Medium | This is INFORMATIVE, not a failure. The disagreements identify where the dataset has ambiguity. Use as input to next iteration, not as cause for panic. |
| AWS / Postgres BAA stalls in vendor legal review | Medium | High | Engage privacy counsel in week 1 to pre-review the standard BAA templates AWS and major Postgres hosts publish. Most BAA stalls are about novel terms the vendor won't change. |
| Payer pilot conversation surfaces architecture requirements that invalidate the chosen tech stack | Low | High | Don't over-commit to architectural decisions before the pilot conversation. Defer engineering hardening if pilot conversation is imminent. |

## Re-pace contingencies

If you need to slow down (which is fine — the goal is reaching 300 with quality, not hitting an arbitrary date):

| Original | Re-pace option A (16 weeks) | Re-pace option B (20 weeks) |
|---|---|---|
| 17 cases/week | 13 cases/week | 10 cases/week |
| CRB active week 6 | CRB active week 8 | CRB active week 10 |
| 300 cases week 12 | 300 cases week 16 | 300 cases week 20 |
| Payer pilot conversation week 12 | Same week 16 | Same week 20 |

Re-pace is the right move if any of:
- SME authoring quality (rubric pass rate) drops below 95%
- CRB sourcing yields < 2 panelists by week 4
- Project owner reports sustained fatigue or competing priorities

## What's deliberately out of scope for this 12 weeks

- **Regulatory consultant engagement** — deferred per `REGULATORY_RFP.md`. Consultant outreach starts at the END of this push, not during.
- **FDA Pre-Sub meeting preparation** — too early; requires the CRB κ data + 500-case dataset.
- **First payer pilot integration** (FHIR, X12 278) — conversation can start at week 12, integration work happens in a subsequent push.
- **Multi-region deployment, K8s migration, multi-tenant SSO** — defer until informed by payer pilot.
- **Web UI v1.2 features** (quick-draft mode, multi-SME collab) — not needed for the push; SME tool at v1.0 is sufficient.

## Companion documents

- [`docs/CRB_SOURCING.md`](CRB_SOURCING.md) — operational playbook for the CRB-sourcing workstream
- [`docs/REGULATORY_RFP.md`](REGULATORY_RFP.md) — consultant selection kit (for week 12 onward)
- [`docs/BAA_INVENTORY.md`](BAA_INVENTORY.md) — vendor BAA tracker (update weekly during this push)
- [`docs/CASE_AUTHORING_GUIDE.md`](CASE_AUTHORING_GUIDE.md) — the SME authoring rules
- [`docs/DATASET_GROWTH_ROADMAP.md`](DATASET_GROWTH_ROADMAP.md) — batch composition for the 100→300 cases (already authored)
- [`docs/EVALUATION_COVERAGE.md`](EVALUATION_COVERAGE.md) — coverage matrix; update at each 50-case checkpoint

---

*Last updated: 2026-05-27. Format: weekly amendments via small PRs; never rewrite, always append.*
