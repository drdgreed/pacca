# PACCA — Demo Script & Shot List (v1)

> **"Routine flies through. Hard cases get a human."**
>
> **Audience:** physicians and charitable-foundation members (mission- and clinically-oriented; not a deep-technical audience).
> **Target length:** ~12 minutes.
> **Narration:** neutral product/mission narrator, third person. No first-person "I built" claims.
> **Deliverable purpose:** a production-ready script to record against — screen capture of the live app + voiceover.
> **Status:** recording plan. Some flows require seeded sample data before capture (see § Recording Prerequisites). This document is the *plan*; it does not assert that every flow has been captured.

---

## Production notes

- **Both cases are synthetic golden-set cases.** Every screen showing clinical data must carry the on-screen line **"Synthetic data — no real PHI"** (matches the repo's portfolio-disclaimer posture).
- **Honesty is a feature, not a caveat to bury.** The close explicitly states pre-production status. Do not cut it.
- **Pacing:** ~145 words/minute of VO, with deliberate silent beats over on-screen actions (clicks, agent processing). Word counts below are sized for the time budget with room for those beats.
- **On-screen callouts:** short kinetic-text overlays (≤6 words) that reinforce, never duplicate, the VO. Listed per scene as `CALLOUT:`.
- **Two threads, one arc:** Act 1 = speed, Act 2 = safety, Act 3 = rigor. Act 2's escalating case is pediatric, so the trust story and the foundation's mission land in the same moment.
- **Numbers are load-bearing — read them exactly as written.** The accuracy appendix at the end gives the source of each claim so the VO is not misstated.

---

## Act 0 — Cold open: the stakes (0:00–1:15)

**Visuals:** No app yet. Black screen → clean typographic stat cards animating in over a quiet clinical-ambient bed. Then the PACCA wordmark.

**VO:**
> Every year in the United States, prior authorization sits between patients and the care their doctors have already decided they need. Providers spend more than thirty-four hours a week on it. Patients wait — two to three days on average. And by the health system's own accounting, nearly one in three of those delays directly harms the patient who's waiting.
>
> It doesn't have to work this way. Most requests are routine — they meet the guidelines cleanly, and a computer could clear them in seconds. The hard ones, the ambiguous ones, the ones where a child's treatment is on the line — those deserve a human's full attention.
>
> This is PACCA. It automates the routine, and it escalates the rest — to a person, every time. It never takes the doctor out of the loop.

| Scene | On screen | CALLOUT |
|---|---|---|
| 0.1 | Stat card: "34+ hours/week per practice" | *the paperwork tax* |
| 0.2 | Stat card: "2–3 day treatment delays" | *patients wait* |
| 0.3 | Stat card: "29% of delays directly harm care" | *one in three* |
| 0.4 | PACCA wordmark resolves; tagline fades in | *Routine flies through. Hard cases get a human.* |

**Storyboard note:** Keep it austere — no stock "doctor with tablet" footage. Typography + one restrained accent color. The 29% stat is the emotional anchor; hold it a full beat longer than the others.

---

## Act 1 — The speed win: a routine case auto-approves (1:15–3:30)

**The case (synthetic):** An adult with metastatic non–small-cell lung cancer, PD-L1 high, first-line immunotherapy request, complete and guideline-concordant documentation. The textbook "should be a yes."

**VO:**
> Here's a provider's view. A request comes in for a first-line cancer immunotherapy — the documentation is complete, and it lines up with published clinical guidelines. This is the kind of request that, done by hand, can take six to twelve hours of back-and-forth.
>
> Watch what PACCA does with it.
>
> *[submit — let the pipeline run silently for a beat]*
>
> Behind that single click, five specialized agents worked in sequence. One pulled the clinical evidence together. One classified the request and its urgency. One checked it against the actual guideline text, retrieved live — not from memory. And because everything checked out, the system returned a decision.
>
> Under thirty seconds. And notice what it gives back: not just an answer, but the reasoning, the specific guideline it relied on, and a confidence level. Nothing here is a black box — every conclusion is traceable to a source.
>
> That's the speed win. But speed is the easy part. The real question is what happens when a case *isn't* textbook.

| Scene | Screen / action | CALLOUT |
|---|---|---|
| 1.1 | Login screen → sign in (fast cut) | *Synthetic data — no real PHI* |
| 1.2 | Provider Dashboard; case A fields visible | — |
| 1.3 | Click **Submit for authorization** | — |
| 1.4 | Processing state (agents working) — hold ~3s | *5 agents, one request* |
| 1.5 | Decision result: **AUTO-APPROVED** + reasoning + guideline citation + confidence | *< 30 seconds* |
| 1.6 | Cursor traces the citation + confidence | *Every answer, traceable* |

**Storyboard note:** Do NOT speed-ramp the processing to fake sub-30s — capture it real. If real latency is longer on the demo box, state the target honestly in VO ("built for sub-30-second decisions") rather than doctoring the clock.

---

## Act 2 — The safety gate: a pediatric case escalates to a human (3:30–6:30)

**The case (synthetic):** A pediatric patient, clinically complex, high-cost therapy. The kind of case where an over-eager automated "yes" would be exactly the wrong instinct.

**VO:**
> Same provider view. This time, the patient is a child, and the request is a cell therapy — a one-time, individualized treatment for relapsed leukemia.
>
> *[submit]*
>
> Before any AI model weighs in on the answer, PACCA runs a set of deterministic safety checks — hard-coded rules, not model judgment. This request trips three of them at once. It's a cell therapy. It is extraordinarily expensive. And the patient is a child, with complex, relapsed disease. Any one of those, alone, means the same thing: this is not a decision to automate. Route it to a human.
>
> And notice — this is an entirely *appropriate* request. The escalation isn't the system catching a mistake. It's the system knowing that the highest-stakes therapy in medicine always deserves a human's eyes.
>
> *[switch to Director Queue]*
>
> This is the reviewer's side. The Medical Director sees the case, sees all three reasons it was escalated, and sees everything the agents assembled — the evidence, the classification, the draft reasoning. The machine has done the legwork. The decision belongs to the physician.
>
> *[reviewer reviews, then approves]*
>
> The Medical Director confirms this is exactly the approved, appropriate treatment for this child — and approves it. The child gets the therapy. A human simply looked first.
>
> This is the line PACCA will not cross on its own. On the routine case, it acted in seconds. On the hard case, it stopped and handed the call to a person. That boundary is deliberate, and it is permanent — the system's authority tops out below deciding a case like this alone.

| Scene | Screen / action | CALLOUT |
|---|---|---|
| 2.1 | Provider Dashboard; case B (pediatric CAR-T) fields | *Synthetic data — no real PHI* |
| 2.2 | Click **Submit for authorization** | — |
| 2.3 | Result: **ESCALATED** — three reasons stack in: cell/gene therapy · high cost · pediatric complexity (pre-flight, before AI confidence) | *Three rules. One answer: a human.* |
| 2.4 | Cut to **Director Queue**; escalated case listed | *Hard cases → a human* |
| 2.5 | Open the case: all three escalation reasons + agent-assembled evidence/reasoning | *The machine does the legwork* |
| 2.6 | Medical Director reviews, confirms on-label, **approves** | *The physician decides — and says yes* |

**Storyboard note:** This is the trust fulcrum. Linger on scene 2.3's "deterministic, before AI confidence" — that distinction (hard rule vs. model discretion) is what a skeptical physician is listening for. And because the child is the escalated case, this is also the emotional peak; let the reviewer's sign-off breathe.

---

## Act 3 — Why you can trust it: validation & the review board (6:30–10:00)

**Visuals:** SME Case Authoring / Dataset Status surfaces, then a purpose-built "validation" explainer beat.

**VO:**
> A system that makes clinical recommendations is only as trustworthy as the evidence behind it. So here's the evidence.
>
> PACCA is tested against a curated set of clinical cases — one hundred and five of them — each one authored and reviewed against real clinical guidelines. This is the dataset that catches the system when it drifts.
>
> *[Dataset Status surface]*
>
> Two gates guard every change. One flags any single case whose result gets worse — a per-case tripwire. The other requires the whole set to clear an accuracy bar before anything ships. Together they mean the system can't quietly degrade.
>
> And PACCA is honest about what that evidence does and doesn't yet prove. It maintains an explicit ledger — what the system can defend today, and what it cannot claim until the dataset grows. That honesty isn't a weakness in the pitch. For a clinical tool, it's the whole point.
>
> This is also where a review board comes in. As the dataset crosses into production-pilot scale, PACCA convenes a panel of credentialed clinicians to independently score the system's judgments — starting with pediatric cases, the ones that matter most and are hardest to get right. That board is forming now, through a charitable-foundation partnership. It is the bridge between a promising prototype and a tool a clinician could one day stand behind.
>
> Every decision, meanwhile, is grounded in retrieved guideline text and checked against explicit safety rules — so the system reasons from sources, not from a hunch.

| Scene | Screen / action | CALLOUT |
|---|---|---|
| 3.1 | SME Authoring / Dataset Status; case count visible | *105 SME-reviewed cases* |
| 3.2 | Dataset composition / status view | *Authored against real guidelines* |
| 3.3 | Explainer beat: the two gates (per-case + aggregate) | *It can't quietly degrade* |
| 3.4 | Explainer beat: honest-claims ledger (defensible today vs. roadmap) | *Honest about what it can't claim* |
| 3.5 | Explainer beat: the forming review board + pediatric focus | *A board of clinicians. Forming now.* |
| 3.6 | Brief: RAG guideline retrieval + safety rules | *Reasons from sources* |

**Storyboard note:** This act is the foundation members' segment — it answers "why should we lend our name and our clinicians to this?" Scenes 3.4 and 3.5 are the ask, softly framed. If a real screen for the honest-claims ledger or the board doesn't exist yet in the UI, render 3.3–3.5 as clean explainer slides rather than faking a screen — accuracy over polish.

---

## Act 4 — Operations at a glance (10:00–11:00)

**Visuals:** Fast, confident montage — admin/config, prompt-version history, ops metrics, audit trail. Music lifts; VO is brisk.

**VO:**
> Underneath, this is real engineering. Every prompt the agents use is versioned, so any change is traceable. Operations are measured. And every single decision leaves an audit trail — who, what, when, and why — built the way a regulated healthcare system has to be built. Nothing important happens that isn't recorded.

| Scene | Screen / action | CALLOUT |
|---|---|---|
| 4.1 | Admin: prompt versions list | *Every prompt, versioned* |
| 4.2 | Ops metrics view | *Measured, not guessed* |
| 4.3 | Audit trail entry (decision → correlation id) | *Every decision, on the record* |

**Storyboard note:** Keep this under 60 seconds. This audience doesn't need the depth — they need to *feel* that the rigor is there. Montage energy, not walkthrough.

---

## Act 5 — Close: the vision & the ask (11:00–12:00)

**Visuals:** Return to the austere typographic style of the open. The two case outcomes side by side, then the tagline, then the ask.

**VO:**
> Two requests. The routine one cleared in seconds. The hard one — the child — went straight to a physician. Both fully documented, both auditable, both grounded in real clinical evidence.
>
> A word of honesty: PACCA today is a reference architecture, built and tested on synthetic data. It is not yet cleared for real patient information — and the roadmap to get there is written down, not hand-waved.
>
> What it needs next is exactly what this room can give. For clinicians: PACCA gives you your time back without ever taking away your judgment. For a foundation: the review board — the clinicians who will vouch for how this system reasons, starting with the children's cases — is forming now, and there's a seat at that table.
>
> Because in the end, this was never about the software. It's about the one in three patients who are harmed by waiting. PACCA exists to shrink that number — carefully, and with a human always in the loop.

| Scene | Screen / action | CALLOUT |
|---|---|---|
| 5.1 | Split: "AUTO-APPROVED · <30s" / "ESCALATED · to a physician" | *Speed and safety* |
| 5.2 | Honesty line on screen | *Reference architecture · synthetic data* |
| 5.3 | The ask (physicians / foundation) | *A seat at the table* |
| 5.4 | Return to "29%" stat, now with "→ shrink it" | *Routine flies through. Hard cases get a human.* |

---

## Recording prerequisites (do these before capture)

1. **Backend + frontend running and reachable** (backend `uvicorn pacca.api.main:app --env-file .env`; frontend `npm run dev`; proxy pointed at the backend port).
2. **A registered login** (no default account ships — register one via `POST /api/v1/register/`).
3. **Case A seeded / ready to submit** — a guideline-concordant request that resolves to AUTO-APPROVED. Confirm it actually auto-approves on the demo box before recording.
4. **Case B seeded / ready to submit** — a pediatric-complex request that trips the pediatric-complex pre-flight and lands in the Director Queue. Confirm it actually escalates.
5. **Director Queue has the escalated case** visible to a Medical Director login for Act 2.
6. **Dataset Status / SME surfaces populated** enough to show the 105-case set for Act 3 (or fall back to explainer slides per the Act 3 storyboard note).
7. **Screen resolution + zoom** set for legibility on a projector (larger UI scale than a dev laptop default).

> ⚠️ **Verify each flow end-to-end before recording.** As of this script's writing, the authenticated submit → decision pipeline and the escalation → queue flow were designed but not confirmed captured on the demo machine. Record a dry run first; if any flow doesn't behave as scripted, fix the flow or adjust the VO — do not fake the result on screen.

---

## Fact-accuracy appendix (read numbers exactly; here's the basis)

| Claim in VO | Basis | Notes |
|---|---|---|
| "34+ hours/week per practice" | README "The Problem" | provider workload |
| "2–3 day treatment delays" | README "The Problem" | |
| "29% / one in three delays directly harm care" | Repo problem framing (PRD/README) | State as **% of delays that harm**, not "% of patients" |
| "six to twelve hours" manual baseline | PRD | vs. sub-30-second target |
| "five specialized agents" | EvidenceAggregation, ClinicalClassification, DecisionSupport (T1), MedicalDirector (T2), PolicyEvolution | |
| "deterministic safety checks … pediatric complexity" | 7-branch escalation tree; pre-flight fires before LLM | Say "deterministic / hard-coded," not "the model decides to be cautious" |
| "authority tops out below deciding a case like this on its own" | Autonomy posture — human-governed escalation | |
| "105 … cases, authored and reviewed against real guidelines" | 105-case golden set (GC-001–105), SME-reviewed | verified current count |
| "two gates … per-case tripwire … accuracy bar" | Dual evaluation gate: per-case regression (100% sensitivity) + aggregate ≥80% | |
| "honest ledger … defend today vs. cannot claim" | Honest-claims matrix (PRD §16.9 / v2.5) | |
| "review board … forming now … pediatric … charitable-foundation partnership" | Phase 2 CRB: **in formation** (100-case trigger crossed; operational scored sweeps at 200) | Say "forming," never "operational." Foundation is Chicago-based; name TBD |
| "reference architecture … synthetic data … not yet cleared for real patient information" | Repo portfolio disclaimer; not HIPAA-validated, no BAAs | Non-negotiable honesty line |

**Do not** state SaMD clearance, HIPAA compliance, or that the review board is operational — none are true yet, and this audience is exactly who would (rightly) hold you to it.

---

*Demo script v1 — structure approved 2026-07-20. Neutral narrator, ~12 min, synthetic-data demo of a pre-production reference architecture.*
