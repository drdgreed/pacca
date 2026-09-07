# Session handoff — 2026-09-07

Work is **parked**, not blocked. `main` is green, nothing is in flight, and every
branch this session created has been merged and can be deleted.

This file exists so the next session does not have to re-derive what was learned
here — several of the findings below were expensive to establish and two of them
overturned things the repository previously asserted about itself.

---

## 1. Resume here

```bash
git fetch origin && git checkout main && git reset --hard origin/main   # f45fdaf
python -m pacca.harness.validate_manifest --all                          # expect 30 valid
pytest tests/ -m "not clinical and not holdout" -q                       # expect 1186 passed
```

The top open item is **§5.1 (judge parse failures)**. It is the only one that
changes what an existing number *means*, so it should go first.

---

## 2. What shipped

Five PRs, all merged. `main` moved `dc05a68 → f45fdaf`.

| PR | Iter | What |
|---|---|---|
| [#100](https://github.com/drdgreed/pacca/pull/100) | — | Baseline capture covered 20 of the 42 cases the gate scores. Fixed; `holdout.IN_SAMPLE_CASES` is now the single definition. |
| [#101](https://github.com/drdgreed/pacca/pull/101) | 27 | Adopted the first baseline over all 42 cases, and retired the variance attribution it disproved. |
| [#102](https://github.com/drdgreed/pacca/pull/102) | 28 | Four adversarial findings: unbounded confidence, blank `reviewer_id`, PHI in exception strings, control-char escaping. |
| [#103](https://github.com/drdgreed/pacca/pull/103) | 29 | Audit-write failures made visible without being made fatal; Dockerfile healthcheck fixed. |
| [astro#12](https://github.com/drdgreed/drdavidreed-astro/pull/12) | — | Portfolio card `whitepaper-3` updated with the findings. |

---

## 3. The through-line

Every finding this session was a variant of one thing: **a mechanism that looked
like it was working because nothing could tell you it wasn't.**

- A regression gate that had never been called outside its own unit tests.
- A baseline covering less than half the cases it was compared against, with the
  shortfall reported as `new_cases` — a bucket that reads like routine housekeeping.
- A compliance control (structlog PHI redaction) named in the PRD that **does not
  exist in the codebase**.
- A container healthcheck probing a 404, so it could only ever fail.
- A confidence gate whose input was unbounded, so the model could widen its own
  autonomy by returning a number.

The sharpest instance, worth carrying forward as a general lesson:

> **An incomplete evaluation set does not merely measure less — it measures
> *easier*, and reports the difference as good news.**

Fixing the 20→42 coverage gap did not just add cases. It revised published
numbers: judge self-disagreement went from a measured **0%** to **7.1%**, and max
end-to-end spread from **1** to **3**. The original 20 were not a random subset;
they were the stable ones. GC-001 through GC-020 moved on only 1 of 20 in the
wider run.

---

## 4. Reference numbers

Baseline `tests/clinical/baselines/iter-27-baseline.json` — run
[34070093157](https://github.com/drdgreed/pacca/actions/runs/34070093157) on `main` at `c1e150d`.

**Judge-only** (42 cases × 2 re-scores of frozen text): disagreement 7.1%,
band-crossing 7.1%, fabrication disagreement 0.0%, max spread **2**.

**End-to-end** (42 cases × 5 rollouts): 6 of 42 moved, max spread **3**.

```
GC-012 [4,4,5,4,4]   GC-019 [5,5,5,5,4]   GC-021 [5,5,5,2,5]
GC-022 [3,3,3,3,2]   GC-024 [3,2,4,2,3]   GC-075 [1,2,2,1,1]
```

Median accuracy **38/42 = 90.5%**; failing at median: **GC-027, GC-029, GC-034, GC-075**.
Three cases (GC-021, GC-022, GC-024) cross the pass mark between rollouts on
identical inputs.

**Live gate runs since adoption** — all report-only on the regression gate:

| PR | Accuracy | Per-case regression report |
|---|---|---|
| #101 | 37/42 (88.1%) | `Jitter within noise tolerance (1): GC-024 3->2` |
| #102 | 38/42 (90.5%) | `No per-case movement versus baseline.` |
| #103 | 38/42 (90.5%) | `Jitter within noise tolerance (1): GC-034 2->1` ← *a parse failure, see §5.1* |

---

## 5. Open items, ranked

### 5.1 Judge JSON parse failures are scored as clinical failures — START HERE

Found in #103's gate run. Two instances in one run:

```
GC-034 (score 1): Judge response could not be parsed: Extra data: line 11 column 1 (char 1154)
[error] judge_json_parse_failed  case_id=GC-019  error='Extra data: line 7 column 1 (char 955)'
```

A parse failure is scored **1** — the lowest clinical score — rather than raised
as a harness error. Consequences:

1. **The accuracy metric conflates two things.** "The system reasoned badly" and
   "we could not read the judge's reply" both land as a failing case. 90.5% is
   doing double duty as a clinical measure and a parser success rate.
2. **The regression tolerance launders it.** `GC-034 2->1` was absorbed as
   "jitter within noise tolerance (1)" and the gate reported PASSED. The
   tolerance did exactly what it is specified to do and hid a harness bug it was
   never meant to cover.
3. **It may contaminate the iter-27 variance numbers.** `GC-021 [5,5,5,2,5]` and
   `GC-024 [3,2,4,2,3]` are precisely the shape a sporadic unparseable verdict
   produces. **This has not been checked.**

**First step, and it is cheap:** pull the logs of run 34070093157 and grep for
`judge_json_parse_failed` / `could not be parsed`. If the low draws on GC-021 and
GC-024 correlate with parse failures, the measured "agent variance" is partly a
parser bug and §4's numbers need revising *again*.

**Then:** distinguish a parse failure from a score in `tests/clinical/evaluator.py`
— retry once, and fail the harness rather than the case. This changes what the
accuracy number means, so it warrants its own manifest entry and gate run.

### 5.2 `noise_threshold=1` is measurably too small

`measure_judge_noise`'s own stated rule — *a threshold at or below the max judge
spread cannot separate a regression from the judge rescoring identical text* —
now condemns the configured value: max judge spread is **2**, max end-to-end is **3**.

It stays at 1 **only because the gate is report-only**. Before enforcing, decide
between a larger threshold, medians over rollouts, or both. Note §5.1 may change
the inputs to this decision.

### 5.3 `api/routes/health.py` is dead code

Its router is never passed to `include_router`, so `/health/live`, `/health/ready`
and `/api/v1/metrics` do not resolve. The `/health` that answers is defined
directly in `api/main.py`.

Deliberately **not** mounted in #103, because that router defines a colliding
`/health` and an **unauthenticated** `/api/v1/metrics`. Decide: mount it (with
those two problems resolved), or delete it. Leaving it is the worst option — it
reads as a working metrics surface.

`tests/unit/test_audit_durability_visibility.py::TestTheHealthSurfaceThatActuallyExists`
pins the current 404s, so whoever mounts it will be forced to confront the collision.

### 5.4 Fail-closed on audit-write failure

Still open, deliberately. #103 implemented the middle option (visibility) without
reversing the documented decision that an audit-write problem must never turn a
working request into a 500.

`GET /health` now reports `audit_write_failures_total`. **After a few weeks of
real traffic that counter tells you how often fail-closed would have fired** —
which converts this from an argument into a measurement. Revisit then.

### 5.5 Two stale open PRs from an earlier session

Both branch from `db47a5d`/`37cabf1`; `main` is now ~15 commits ahead, so both
are probably conflicted.

- **[#86](https://github.com/drdgreed/pacca/pull/86)** `fix/gc-027-preflight-expectation` — changes GC-027 to expect
  `PRE_FLIGHT_ESCALATE`. **Directly relevant:** GC-027 is one of the four cases
  failing at median today, with an outcome mismatch. This PR may already be the
  fix for a current failure. Read it before touching GC-027.
- **[#88](https://github.com/drdgreed/pacca/pull/88)** `docs/enforce-decisions-log` — adds a coverage test requiring a
  `DECISIONS.md` section per manifest. If merged, it will demand entries for
  iters 25–29, which this session did not write.

Three dependabot PRs (#89, #90, #91) are frontend-only and independent.

### 5.6 Smaller, carried from earlier

- SDD v3.0 is not under `docs/`, so v3.0 requirement IDs do not resolve against code.
- `docs/STATISTICAL_POWER.md` claims 100% per-case sensitivity, which §4 contradicts.
- The PRD compliance matrix still names a structlog redaction control that does not
  exist. #102 fixed the *leak* at the engine (`hide_parameters=True`); the **claim**
  is still wrong and should be corrected or the control built.
- `DECISIONS.md` / `ITERATIONS.md` narrative entries for iters 25–29 were not written.

---

## 6. Operational notes

**Worktrees are gone.** This session used ~12 (`/home/user/pacca-*`); the container
is ephemeral. Everything is on `origin`. All branches this session created are
merged and safe to delete:

```
chg/adopt-iter27-baseline  chg/iter27-adopt-baseline
chg/iter28-adversarial-fixes  chg/iter29-audit-failure-visibility
```

**The clinical gate** fires on any `chg-` commit subject, on changes to
`src/pacca/(agents|rag)/` or `config/settings.py`, and on manual dispatch. It runs
42 live cases and takes **~11 minutes**. It is opt-in by the `ANTHROPIC_API_KEY`
secret and inert without it.

**`variance.yml`** is manual-only and expensive: at 42 cases with `judge_runs=2,
rollouts=5` it takes **~43 minutes** and roughly **550 API calls** (~$5–15 on
Sonnet 4.5). It writes its baseline as an **artifact, never a commit** — adopting
a baseline is a deliberate act, and auto-committing would let a regression baseline
itself into legitimacy.

**Artifacts cannot be downloaded from an agent session** — the GitHub REST API is
blocked; only the MCP server works, and it has no artifact-download tool. Baseline
numbers had to be transcribed from job logs. If you do that again, verify the way
#101 did: assert the case set equals `IN_SAMPLE_CASES`, assert a uniform rollout
count, and recompute every median from its own distribution before writing the file.

---

## 7. Corrections made this session

Recorded so they are not re-derived wrongly. Each is now fixed in the code or its
comments.

1. **"Judge variance is 0, so run-to-run movement is the agent's."** Measured at 20
   cases × 3; false at 42 × 2, where the judge disagrees with itself 7.1% of the
   time. Four files asserted this and were corrected in #101.
2. **"`case_writer` has a code-injection hole with silently discarded cases."**
   Neither half held. Quotes were already escaped — an injected payload parses to a
   single `ast.Constant`, not a `Call` (there is now a test pinning that) — and the
   route raises 409 rather than discarding. The real defect was availability.
3. **"Audit writes swallow failures"** — real behaviour, but a *documented decision*,
   not an oversight. Do not reverse it without deciding to; see §5.4.
4. **The six baselines `iter-1`…`iter-6`** all entered in the repository's initial
   import commit. Whether they were captured or reconstructed **cannot be determined**
   from history. Do not assert either.

---

## 8. If resuming with a fresh agent

Point it at this file first, then `docs/HARNESS.md` and `CLAUDE.md`. The
conventions that matter most here:

- Behavioral changes need a manifest at `harness/manifests/iter-N.json`; at
  iteration ≥ 18 an `improvement` or `rollback` requires a **measured** `baseline`
  object — a reproduction, not an assertion. The validator enforces this.
- Commit subjects starting `chg-` fire the clinical gate. Use it when a change
  warrants a live run; do not use it to kick CI.
- Verify that a new guard *discriminates* — revert the fix and watch the test fail —
  before claiming it protects anything. Every guard added this session was checked
  this way, and one (#100's) was rewritten after failing against its own subject.
