# SME Case Authoring Agent — User Manual

> **For:** Board-certified clinicians authoring golden test cases for PACCA's clinical evaluation dataset.
> **Prerequisites:** None. No Python knowledge needed.
> **Time to first case:** ~15 minutes.

Welcome, doctor. This guide walks you through using `pacca sme-author` — a command-line tool that lets you author new clinical test cases for the PACCA prior-authorization platform without writing code.

Your job is the clinical thinking. The tool handles everything else: drafting, formatting, validation, file mutations, integrity tests, and PR preparation.

---

## What this tool does

You describe a clinical scenario in plain English (1–3 sentences). The tool:

1. Drafts a complete test case using Claude (the LLM)
2. Validates the draft against PACCA's authoring rules (no PHI, real guideline citation, schema-consistency, etc.)
3. Shows you the draft for review
4. Asks for your professional attestation
5. Writes the case to the right file
6. Runs the integrity tests
7. Prepares a pull-request description for your engineering team to review and merge

You stay in control: you can edit any field, abandon at any time, and the tool defaults to a "no-write" mode that lets you experiment without changing any files.

---

## Section 1 — First-time install (5 steps)

These steps assume your IT-support person has already set up Python and given you access to the PACCA repository. If not, hand them `docs/SME_CASE_AGENT_INSTALL.md` first.

| Step | What to type | What you'll see |
|---|---|---|
| 1 | `cd path/to/pacca` | (a prompt showing you're in the repo) |
| 2 | `pip install -e ".[dev]"` | A long list of packages installing |
| 3 | `pacca --version` | `pacca, version 2.4.0` |
| 4 | `export ANTHROPIC_API_KEY=sk-ant-...` | (no output; your API key is set for this terminal session) |
| 5 | `pacca sme-author --help` | A list of subcommands |

If step 3 fails with `pacca: command not found`, your IT-support person needs to re-run the install. If step 5 shows the subcommands list, you're ready.

---

## Section 2 — Add your first case (15 minutes)

### 2.1 — Check the current state

```bash
pacca sme-author status
```

You'll see something like:

```
Total cases: 100

Per-list counts:
  GOLDEN_CASES                          20  GC-001 to GC-020
  NEAR_MISS_CASES                        2  GC-021, GC-022
  CARDIOLOGY_CASES                       4  GC-037 to GC-040
  ...

Next milestones:
  300-case general-payer-deployment milestone   200 cases needed
  500-case HIPAA SaMD-grade milestone           400 cases needed
```

This tells you the dataset is at 100 cases. The "Next milestones" line shows what remains.

### 2.2 — Find the highest-priority gap

```bash
pacca sme-author list-gaps --top 5
```

You'll see the top 5 gaps with cases-needed counts:

```
Top 5 gaps:

  P1  [milestone        ] 300-case general-payer-deployment        (need 200 more)
        Dataset at 100; need 200 more cases to reach 300.
  P1  [milestone        ] 500-case HIPAA SaMD-grade                (need 400 more)
        Dataset at 100; need 400 more cases to reach 500.
  P2  [within-specialty ] Cardiology                                (need 1 more)
        Specialty 'CARDIOLOGY_CASES' has 4 cases; need 1 more for...
```

Pick the gap you're best positioned to address with your clinical expertise.

### 2.3 — Start the workflow

```bash
pacca sme-author new
```

You'll see a banner:

```
============================================================
  NO-COMMIT MODE (default) — drafting + validation only
============================================================

Scenario description (1-3 sentences in plain English):
```

Type your scenario in plain English. Example:

> 67-year-old male with metastatic prostate cancer progressing on androgen deprivation. PSA rising; bone metastases on scan. Requesting abiraterone with prednisone per NCCN.

The tool will:
1. Allocate the next case ID (`GC-101`).
2. Route to a thematic file (e.g., `oncology_depth_cases.py`).
3. Call Claude to draft a complete case.
4. Run 6 validators (PHI scan, guideline citation, schema, outcome-branch consistency, reasoning specificity, judge-criteria specificity).
5. Show you the draft.

### 2.4 — Review the draft

The tool prints the draft as JSON. Read carefully:

```json
{
  "case_id": "GC-101",
  "title": "mCRPC abiraterone + prednisone per NCCN Cat 1",
  "diagnosis_code": "C61",
  "clinical_notes": "67-year-old male with metastatic castration-resistant ...",
  "guidelines_context": "NCCN Prostate Cancer Guidelines: abiraterone + prednisone is ...",
  "expected_outcome": "AUTO_APPROVED",
  ...
}
```

**Things to check:**
- Is the `clinical_notes` clinically accurate? (Drug doses, staging, lab interpretations.)
- Is the `guidelines_context` citation correct? (Real body, current recommendation.)
- Is `expected_outcome` what you'd recommend?
- Does `reasoning_must_include` capture the key clinical claims a reasoner should make?

If anything is wrong, abort (Ctrl-C) and re-run with a more specific scenario description.

### 2.5 — Provide your attestation

The tool prompts:

```
SME attestation (per CASE_AUTHORING_GUIDE.md § 11):
```

Type either:

```
I attest this case is clinically accurate per my professional judgment
```

or

```
Dr. Jane Doe, MD, board-certified medical oncology
```

This goes into the PR description as your professional review record. Audit trail purposes.

### 2.6 — Decide: commit or not?

In `--no-commit` mode (default), no files are written. The tool ends with:

```
[NO-COMMIT MODE] No files written. Re-run with --commit to actually
write the case.
```

When you're ready to write the case for real:

```bash
pacca sme-author new --commit
```

This time, after attestation, the tool will:
1. Write the case to the target file
2. Add a row to `docs/CASE_PROVENANCE.md`
3. Update the summary table in `docs/EVALUATION_COVERAGE.md`
4. Run the integrity tests (`pytest TestGoldenDatasetIntegrity`)
5. Render the PR description

You'll see something like:

```
Case written to tests/clinical/oncology_depth_cases.py

Running integrity tests...
Integrity tests PASS.

============================================================
  PR TEMPLATE:
============================================================
Title: sme-cases: add GC-101 — mCRPC abiraterone + prednisone per NCCN Cat 1

## Summary
...
```

Copy the PR title + body and hand to your engineering team to create the pull request on GitHub. They'll review and merge.

---

## Section 3 — Add a batch (1 hour)

A **batch** is a coherent group of 3–10 cases sharing a single purpose. Roadmap batches are pre-planned in `docs/DATASET_GROWTH_ROADMAP.md`.

### 3.1 — Browse the roadmap

```bash
pacca sme-author list-batches
```

You'll see every batch from the roadmap:

```
Available batches (16):

  Batch A   DENY expansion             (3 cases)   → denial_cases.py [NEW FILE]
  Batch B   Cardiology depth           (4 cases)   → cardiology_cases.py [NEW FILE]
  Batch C   Mental health depth        (5 cases)   → mental_health_cases.py [NEW FILE]
  ...
```

### 3.2 — Inspect a specific batch

```bash
pacca sme-author batch B
```

Shows the batch's planned case slots:

```
Batch B: Cardiology depth
  Target file: cardiology_cases.py (NEW)
  ID range:    GC-037 to GC-040
  Case count:  4

Case slots:
  GC-037  TAVR for severe symptomatic AS (clean approve per ACC/AHA)
  GC-038  AFib catheter ablation after failed AAD (clean approve)
  GC-039  ICD primary prevention with LVEF=36% (denied)
  GC-040  Statin primary prevention in 38yo with familial hypercholesterolemia
```

### 3.3 — Author each slot

For each slot, use the description as your scenario when running `pacca sme-author new`. For example, for `GC-037`:

```bash
pacca sme-author new --commit \
  --description "76yo male with severe symptomatic aortic stenosis (AVA 0.7 cm², mean gradient 48 mmHg, NYHA III, STS-PROM 6.2%). Heart team consensus for TAVR. Femoral access suitable." \
  --specialty cardiology \
  --outcome AUTO_APPROVED
```

Work through each slot. Plan ~10–15 minutes per case.

---

## Section 4 — What to do if the agent suggests something clinically wrong

You are the clinical authority. **Never accept a case you believe is wrong.**

If the LLM's draft has a clinical error:
1. **Abort the session** (Ctrl-C).
2. **Re-run with a more specific scenario description** — include the specific clinical detail the LLM got wrong, e.g., "PD-L1 70% — do NOT recommend combination chemo; monotherapy is Category 1."
3. **Or use field-by-field manual entry** (planned for v1.1; for now, abort + redraft).

If the LLM cites a wrong guideline body:
1. Abort.
2. Re-run with `--description "... per <correct guideline body name>"`.

If the LLM fabricates a lab value:
1. Abort.
2. Add the lab value (or "lab not specified") explicitly to your scenario description.
3. The PHI scan and reasoning_must_not_include validators help catch these, but your eyes are the final check.

---

## Section 5 — How to attest your review

The SME attestation prompt accepts two formats:

**Format 1 — generic attestation statement:**
```
I attest this case is clinically accurate per my professional judgment
```

**Format 2 — credentialed statement (preferred for audit):**
```
Dr. Jane Doe, MD, board-certified <Specialty>, <Institution>, <Date>
```

Format 2 is preferred because it embeds your credentials in the PR description, satisfying the Phase 1 review requirement from `docs/CASE_AUTHORING_GUIDE.md` § 11.

If you'd rather not embed your name in PRs (privacy preference), use Format 1 and have your engineering team add a private credential attestation note to the case-tracking system.

---

## Section 6 — How to flag a case as provisional

If you're uncertain about a clinical detail and want to land the case for Phase 2 (clinical-review board) sweep later:

1. Author the case as normal.
2. In your attestation, write: `Provisional — clinical-review-board sweep requested. <reason>`.
3. The PR description will include this verbatim. The engineering team will tag the case `provisional` in `CASE_PROVENANCE.md` until the next CRB review.

Provisional cases still count toward the dataset's total. They are flagged for revision in the next iteration.

---

## Section 7 — Resuming an interrupted session

Every session is saved to `~/.pacca/sme_authoring_sessions/` after every step. If your terminal crashed, your laptop slept, or you abandoned mid-session:

```bash
pacca sme-author list-sessions
```

Shows your saved sessions with timestamps:

```
Saved sessions (3):

  06a1505d-b94f-7fc9...  [sandbox  ] step=drafted               updated=2026-05-25 14:32:11 UTC
      Stage IV NSCLC PD-L1 70% requesting first-line pembrolizumab...
```

To inspect a session:

```bash
pacca sme-author resume 06a1505d-b94f-7fc9...
```

You'll see the session state (scenario, draft, attestation, last step). **PR-4 ships read-only display**; full interactive continuation will come in a future release. For now, use the displayed state as context and re-run `pacca sme-author new` to start fresh.

---

## Section 8 — Troubleshooting

### "Allocated case ID GC-101 but ID is wrong"

The tool allocates IDs monotonically. If you see a gap or unexpected number, run `pacca sme-author status` to see the current state. The next ID will always be max-existing + 1.

### "ANTHROPIC_API_KEY environment variable not set"

```bash
export ANTHROPIC_API_KEY=sk-ant-...
```

Use the API key your team gave you. Don't put the key into any committed file.

### "LLM drafting failed: <error>"

Usually a transient API issue. Re-run. If it persists, check:
- Network connectivity
- API key validity (`echo $ANTHROPIC_API_KEY` should show your key)
- API rate limits (the tool retries 3 times automatically)

### "Validator FAILED: PHI scan detected likely PHI"

The LLM accidentally included a PHI-looking pattern. Common causes:
- Specific dates ("5/4/2024") — re-run with "12 weeks ago" framing in your scenario.
- Capitalized names ("Mr. Smith") — re-run with "the patient" framing.
- SSN-like numbers — should never happen; abort and report to engineering.

### "Validator FAILED: guideline body not recognized"

The LLM cited a non-recognized body (or paraphrased one). Re-run with the specific recognized body name in your scenario description, e.g., "per NCCN" not "per oncology guidelines".

### "Integrity tests FAILED after write"

The case write produced a file the test suite doesn't accept. The tool should have rolled back automatically. Check `git status` — there should be no staged/unstaged changes. If there are, run `git restore <file>` to revert.

### "I want to undo a case I just committed"

```bash
git restore tests/clinical/<file>
git restore docs/CASE_PROVENANCE.md
git restore docs/EVALUATION_COVERAGE.md
```

The `next_id` allocator will skip the released ID on its next call.

---

## Section 9 — Glossary

**Case ID (GC-NNN):** Unique identifier for a golden test case. Monotonically allocated across all case files. E.g., `GC-101`.

**Expected outcome:** What PACCA SHOULD decide for this case. One of: `AUTO_APPROVED`, `IN_REVIEW`, `DENIED`, `PRE_FLIGHT_ESCALATE`, `INFORMATION_NEEDED`.

**Expected branch:** Which of PACCA's 7 escalation branches should fire. Branches 1–7 mirror SS5.4 of the PRD.

**Failure mode:** A named pattern this case probes. E.g., `Coverage` (routine case), `Hallucination zero-tolerance` (sparse-notes trap), `False pattern-matching (memory trap)` (near-miss to a known approve case).

**Validator:** A deterministic check the tool runs against the draft. The 6 validators: PHI scan, guideline citation, schema completeness, outcome-branch consistency, reasoning specificity, judge criteria specificity.

**Integrity test:** `pytest TestGoldenDatasetIntegrity` — runs after every write. Verifies case count, cross-file ID uniqueness, per-file counts, etc.

**Sandbox mode (`--sandbox`):** Writes go to `sandbox/cases/` instead of `tests/clinical/`. Zero git state. (Full implementation in a future release.)

**Worktree mode (`--git-worktree`):** Auto-creates an isolated git worktree at `../pacca-sme-<session_id>/`. PR-ready isolation. (Full implementation in a future release.)

**Phase 1 review (per `CASE_AUTHORING_GUIDE.md` § 11):** SME concurrence on each new case at PR time. Required for every case. Embedded in the PR description via your attestation.

**Phase 2 review (per `CASE_AUTHORING_GUIDE.md` § 12):** Quarterly clinical-review-board (CRB) sample. Activates at the 300-case milestone. Independent of the per-case Phase 1 review.

---

## Section 10 — Where to get help

| Question | Where |
|---|---|
| "How do I install?" | `docs/SME_CASE_AGENT_INSTALL.md` |
| "How does this work under the hood?" | `docs/SME_CASE_AGENT_DESIGN.md` |
| "What are the authoring rules?" | `docs/CASE_AUTHORING_GUIDE.md` |
| "What's the dataset trajectory?" | `docs/DATASET_SUFFICIENCY.md` + `docs/DATASET_GROWTH_ROADMAP.md` |
| "Why does PACCA have these gates?" | `docs/EVALUATION_COVERAGE.md` |
| "The tool crashed" | File a GitHub issue with the session_id (from `~/.pacca/sme_authoring_sessions/`); include the redacted stack trace. |
| "I have a clinical question about a guideline" | Ask your specialty colleague; the tool's LLM is NOT a clinical authority. |

---

---

## Section 11 — The Web UI

> **For clinicians who prefer a browser to a terminal.** Same agent, same validators, same audit trail — different surface.

If your team has deployed the Web UI (PR #13–#17, v1.1+), point your browser at the URL your IT person sent you (something like `https://sme.example.com/sme-author`) and sign in with the username + password they gave you.

### What's different from the CLI

| | CLI (`pacca sme-author new`) | Web UI |
|---|---|---|
| **Where you work** | Your terminal | Any laptop with a browser |
| **What you type** | Same plain English | Same plain English |
| **What it does** | Same agent, same validators | Same agent, same validators |
| **What you get** | Same PR description, same case file | Same PR description, same case file |
| **Where state lives** | `~/.pacca/sme_authoring_sessions/` on your machine | Server-side; visible from any browser you sign into |

You don't have to choose. Both surfaces stay supported. Some clinicians prefer the terminal for batch work; others prefer the browser for a single case. They share the same backend, so a case authored in either surface lands in the same audit trail.

### Tour — what each page does

When you sign in, you land on the **Dashboard**. From the top nav:

- **Dashboard** — your "where am I" home. Total cases, recent sessions, top-priority gaps.
- **New case** — the 6-step wizard. The main work surface.
- **Sessions** — every session you (or anyone on the team) has started. Filter by mode; click any row to see the detail.
- **Batches** — the planned batches from the roadmap, with progress bars.
- **Gaps** — the prioritized coverage gaps the analyzer has identified.
- **Status** — full dataset snapshot with milestone progress (production-pilot at 100, general-payer at 300, SaMD-grade at 500).

### The 6-step wizard — what to expect

Open **New case**. The wizard walks you through six steps, each on its own page.

1. **Scenario.** Type 1–3 sentences in plain English. Same prompt as the CLI's first question. Optional hints (specialty + intended outcome) bias the agent's draft but are NOT required.
   - **A client-side PHI scan runs as you type.** If you accidentally paste real patient data (or anything that looks like an SSN, MRN, DOB, full name, phone number, etc.), the page surfaces a warning and blocks the Continue button until you either remove the pattern or check "I confirm this is a false positive (synthetic data only)."
   - The default is **Sandbox mode**. Drafts go to `sandbox/cases/` and never touch production. To commit to `tests/clinical/`, switch to **Production mode** on this same page.

2. **Drafting.** The agent calls the LLM. You see the draft appear **token by token, field by field**, with a blinking cursor on whichever field is currently being written. If the streaming connection drops, the page silently falls back to a buffered draft (you'll see "WebSocket unavailable — using buffered REST drafting…").

3. **Review.** Every field of the agent's draft, editable inline. Change anything that's clinically off. If you edit, the next step (Validation) re-runs automatically — you don't have to remember.

4. **Validation.** The same 6 deterministic validators that run in the CLI: PHI scan, guideline citation, schema completeness, outcome ↔ branch consistency, reasoning specificity, judge criteria specificity. Each shows pass / warn / fail with the reason. Any FAIL blocks the next step until you step back and fix it.

5. **Attestation.** Type your attestation — either the generic phrase or a credentialed statement (see Section 5). The page tells you live which format it recognized.

6. **Commit.** A summary of everything (mode, target file, allocated case ID, validation counts). If you chose Production mode, the page demands an explicit "I confirm this case should be written to production now" checkbox before the Commit button enables. After commit, you see the PR title + body with **copy-to-clipboard** buttons — paste these directly into `gh pr create` or the GitHub web UI.

You can step backward at any time — the wizard preserves your in-progress state. Click any visited step in the indicator at the top to jump back.

### What the Web UI does NOT do (yet)

- **Resume mid-wizard after a browser refresh.** In v1.1, refreshing the page restarts the wizard. The session record IS preserved on the server (you can find it in the Sessions list), but the wizard itself doesn't re-hydrate. v1.2 will fix this.
- **Author directly from a gap.** Gaps list shows priority + counts; the "Author from this gap" link takes you to the wizard but doesn't pre-fill the failure-mode hint. v1.2 will wire this.
- **Multi-clinician simultaneous editing.** Each session is single-author. Concurrent sessions don't conflict on case IDs (the server reserves IDs as it issues them) but two clinicians can't co-edit one draft.

### HIPAA awareness for browser use

The Web UI was designed with the synthetic-only rule in mind, but browsers add a few risks the terminal doesn't:

- **Don't open the surface on a shared / public computer.** Sign out when you step away. Logout actively clears all local storage in the browser tab.
- **Don't screenshot the wizard for non-PACCA people.** Even though the cases are synthetic, the synthetic clinical notes can look very real.
- **Check the URL bar.** The Dashboard URL is `…/sme-author`. The wizard is `…/sme-author/new`. Sessions are `…/sme-author/sessions/<short-id>` — those short IDs are safe to share with PACCA teammates.
- **If you paste something that looks PHI-shaped** the page will warn you before any data leaves the browser. If you confirm and continue anyway, the backend's canonical PHI scan runs again before the case is written. Three layers of defense; trust the first.

### When to use which

- **Authoring a single case:** Web UI is faster. Less switching between terminal panes.
- **Authoring a batch of 10+ cases:** CLI is faster. You can script the scenario inputs from a CSV.
- **Triaging existing sessions:** Web UI. The Sessions page is far easier than `pacca sme-author list-sessions`.
- **Reviewing a batch's progress:** Web UI. The Batches page shows everything at a glance.
- **Working offline / on a plane:** CLI. The Web UI needs a network connection to the backend.
- **Demoing the tool to a non-engineer:** Web UI. Always.

---

*Last updated: 2026-05-26 (PR #17 close — SME Web UI v1.1).*
