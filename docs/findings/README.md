# PACCA Findings

Diagnostic write-ups from live evaluation runs. Each finding is captured
when a case persistently fails or surfaces a structural issue worth recording
for future-iteration design.

The format mirrors `docs/DECISIONS.md` in spirit: one document per finding,
named by the case ID or topic, with a clear root cause, evidence, and
prescriptive next action. These are inputs to iteration planning, not
iteration manifests themselves.

## Index

- [GC-001 — Stage IIIA vs metastatic guideline mismatch in case definition](./GC-001.md) — **test-data bug**, agent caught it
- [GC-010 — Missing high-cost ($100K) escalation branch](./GC-010.md) — **agent-side bug (SEV-2)**, missing branch_2 trigger
- [GC-012 — Missing pediatric-complexity escalation branch](./GC-012.md) — **agent-side bug (SEV-2)**, same class as GC-010

## How to add a finding

1. Run the live pipeline against the case in question:
   ```bash
   set -a; source .env; set +a
   python -m tests.clinical.investigate_case <CASE_ID>
   ```
2. Read the agent rationale, judge reasoning, and case definition against each other.
3. Categorize: agent bug, test-data bug, judge bug, model issue, or expected behavior.
4. Write the finding using the four-section structure: **What we observed**,
   **Root cause**, **Evidence**, **Recommended action**.
5. Add the index line above.

## Why findings live separately from `DECISIONS.md`

`DECISIONS.md` records *what the cycle decided to ship* (per-change manifest +
verdict). Findings record *what the cycle learned about the system* —
diagnostic artifacts that may or may not result in a behavioral change. Mixing
them would dilute the methodology's audit trail. Cross-references go both
ways (DECISIONS.md cites a finding when a chg- entry is born from it; a
finding cites the chg- entry when one is opened).
