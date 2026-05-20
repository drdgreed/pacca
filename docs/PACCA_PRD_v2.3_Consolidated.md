# PACCA — Product Requirements Document, v2.3 Consolidated

> **Status:** Draft — sections §1–§14 are stable from v2.2 and rendered in [`PACCA_PRD_Consolidated.md`](PACCA_PRD_Consolidated.md). Section §15 (the v2.3 harness-engineering cycle) is in active drafting; the canonical source for the cycle today is [`HARNESS.md`](HARNESS.md) plus the per-iteration manifests under [`harness/manifests/`](../harness/manifests/).
>
> This file exists so the README's references to a v2.3 consolidated PRD do not break. When §15 lands, it will replace the placeholder block below and this file will subsume `PACCA_PRD_Consolidated.md` entirely.

---

## What is here today

- **§1–§14 (v2.2 content)** — see [`PACCA_PRD_Consolidated.md`](PACCA_PRD_Consolidated.md).
- **§15 — Harness Engineering Cycle (v2.3)** — see the source documents named in the placeholder section below.
- **Architecture** — see [`ARCHITECTURE.md`](ARCHITECTURE.md).
- **HIPAA posture** — see [`HIPAA_COMPLIANCE.md`](HIPAA_COMPLIANCE.md).
- **Per-iteration record** — [`DECISIONS.md`](DECISIONS.md), [`ITERATIONS.md`](ITERATIONS.md), `harness/manifests/iter-N.json`.

## §15 — Harness Engineering Cycle (placeholder)

The full §15 will consolidate the following sources into a single specification:

| Source | Covers |
|---|---|
| [`HARNESS.md`](HARNESS.md) | The 11 editable harness surfaces, three observability pillars, three rules of engagement |
| [`harness/manifests/change_manifest.schema.json`](../harness/manifests/change_manifest.schema.json) | Machine-readable contract for every behavioral change |
| [`DECISIONS.md`](DECISIONS.md) | Append-only verdict log |
| [`ITERATIONS.md`](ITERATIONS.md) | Narrative log per iteration tag (paper Appendix C format) |

Until §15 is consolidated here, treat the four documents above as the canonical reference. The README's Harness Engineering section already cross-links them.

## Why a stub instead of the full document

This file was promised by the README in advance of consolidation so that:

1. **README links don't 404.** A live link to a stub that explains itself reads better than a broken link.
2. **The roadmap is auditable.** Anyone reading the repo can see exactly what is consolidated and what is not.
3. **The harness-engineering discipline applies to documentation too.** §15 will land as its own iteration with a manifest entry recording what changed and why.

## Roadmap to full consolidation

- [ ] Lift §15 narrative from `HARNESS.md` introduction into a §15.1 here.
- [ ] Move phase exit-criteria tables from `HARNESS.md` into §15.2.
- [ ] Inline the change-manifest schema reference as §15.3.
- [ ] Inline the DECISIONS.md / ITERATIONS.md cross-references as §15.4.
- [ ] Deprecate `PACCA_PRD_Consolidated.md` (v2.2 file) by merging its §1–§14 content here.
- [ ] Tag the consolidated PRD with the next harness iteration that delivers it.
