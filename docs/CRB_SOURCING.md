# Clinical Review Board (CRB) — Sourcing Playbook

> **Purpose.** Operational guide for sourcing the external Clinical Review Board specified in `CASE_AUTHORING_GUIDE.md` § 12 and `PACCA_PRD_v2.5_Consolidated.md` § 16.7. The CRB has a **two-stage** activation: **formation** begins at the **100-case milestone** (crossed — 105 as-built; the board is currently being convened) and **operational scored sweeps** begin at the **200-case dataset milestone** — roughly week 6 of the 3-month push to 300 cases. From the 200-case operational stage forward the board provides quarterly inter-rater agreement (Cohen's κ) evidence that gates the SaMD-grade claim at 500.
>
> **Audience.** Project owner doing the recruiting. Companion to `REGULATORY_RFP.md` (consultant-sourcing) and `BAA_INVENTORY.md` (vendor tracker).
>
> **Critical path.** Credentialing + BAA execution averages **8-12 weeks per panelist**. To have a board active by week 6, outreach starts in **week 1**. Treat this as the gating constraint for the 300-case push.

## Why this document exists

A Clinical Review Board is the only credible answer to the FDA SaMD question "how do you know your dataset's labeled outcomes are clinically correct?" In-house SMEs can label cases, but their labels are by definition the system's own definition of truth. The CRB provides **independent verification** — board-certified specialists, blinded to the system's labels, score a random stratified sample each quarter. The output is Cohen's κ between the CRB and the cataloged outcomes, with a target of κ ≥ 0.80 for SaMD-grade defensibility.

Recruiting the wrong panel is worse than no panel. A panel whose specialties don't match the dataset distribution will produce κ scores that are statistically valid but clinically meaningless. The right panel has **specialty representation proportional to the dataset's case mix** plus enough rotation to avoid review fatigue.

## Required panel composition

Per `CASE_AUTHORING_GUIDE.md` § 12.2:

- **2-3 specialists per quarter** review the same stratified random sample
- **At least one specialist matching the dataset's top specialty** (currently oncology + cardiology dominate; check `EVALUATION_COVERAGE.md` quarterly)
- **One rotating "outside" reviewer** drawn from a different specialty each quarter — catches cases that should escalate cross-specialty
- **Board certification required** in the specialty they're reviewing
- **No active employment relationship** with the project owner (independence requirement)
- **Active clinical practice within the last 24 months** (currency requirement)

Panel rotation: each panelist serves up to 4 consecutive quarters, then a mandatory 2-quarter break. Prevents reviewer drift toward the system's biases. Plan for 4-6 panelists on retainer to support a 3-person quarterly rotation.

## Sourcing channels — ranked by yield

### Tier 1: Highest-yield, lowest-risk

**1. Specialty society directories.**
- American College of Cardiology (ACC): [member directory](https://www.acc.org/membership)
- American Society of Clinical Oncology (ASCO): member portal
- American College of Radiology (ACR), American Academy of Dermatology (AAD), etc.

Members are board-certified by definition; many have AI/clinical-decision-support consulting profiles. Reach via society's "consultants & speakers" listing if available.

**2. Academic department directories.**
- Search "department of [specialty]" at AAMC member medical schools
- Look for **associate professors or higher** with publications in clinical informatics, evidence-based medicine, or guideline development
- Faculty in academic medicine have institutional BAA infrastructure (their employer signs); easier than solo practitioners

**3. KOL (Key Opinion Leader) networks via existing relationships.**
- Ask any clinical advisor or board member if they have credentialed colleagues
- Warm intros convert 5-10x better than cold outreach
- Existing PACCA advisors, project-owner medical school connections, etc.

### Tier 2: Medium-yield, may add friction

**4. Locum tenens agencies with consulting divisions.**
- Weatherby Healthcare, CompHealth, Staff Care — primarily place physicians for locum shifts, but most have consulting branches
- They handle credentialing + BAA + payment infrastructure; markup is ~20-30%
- Useful if recruiting velocity matters more than per-hour cost

**5. Expert witness directories.**
- ABMS-certified expert witness networks (board-certification verified)
- Already comfortable with BAA / NDA paperwork
- Slightly higher hourly rates ($400-600/hr typical)

**6. LinkedIn Sales Navigator search.**
- Filter: title contains "MD" OR "DO" + specialty + 10+ years experience + currently in active clinical role
- High volume, low conversion; useful as a backup when Tier 1 / Tier 2 falls short

### Tier 3: Last resort

**7. Cold-call clinical practices.**
- Volume game; expect <2% response rate
- Only useful if all other channels have been exhausted
- Avoid if at all possible — high opportunity cost for both sides

## Compensation benchmarks (2026)

Per-hour rates for clinical review work, sourced from expert-witness rate cards + industry surveys:

| Specialty | Range ($/hr) | Mid-point | Notes |
|---|---|---|---|
| Cardiology | $400-600 | $500 | Procedure-heavy specialty; CT surgery on the higher end |
| Oncology (medical) | $450-650 | $550 | Sub-specialty premium (GI, GU, breast, heme) typically $50-100 above generalist |
| Surgical oncology | $500-700 | $600 | Highest among oncology |
| Mental health (psychiatry) | $300-450 | $375 | Lower volume of complex review per hour, so per-case faster |
| Endocrinology | $350-500 | $425 | — |
| Rheumatology | $350-500 | $425 | — |
| Pediatrics (general) | $300-450 | $375 | Pediatric subspecialties (cards, onc, neuro) match adult subspecialty rates |
| Primary care (FM/IM) | $250-400 | $325 | Useful for the "outside reviewer" rotation seat |

Quarterly budget at the median panel (2-3 specialists, 4-8 hours each per quarter):
- 2 specialists × 6 hr × $500 = **$6,000/quarter** (minimum viable)
- 3 specialists × 8 hr × $500 = **$12,000/quarter** (full panel, mid-range specialties)
- 3 specialists × 8 hr × $600 = **$14,400/quarter** (premium specialties)

Annual: **$24K-58K** depending on panel size and specialty mix. Conservative budget for `PUSH_TO_300_PLAN.md`: $15K-25K/quarter as cited in the V2+ forecast.

## BAA template language (key clauses)

The BAA must, at minimum, address:

1. **Permitted uses of PHI.** The CRB reviewer may access synthetic case data only for the purpose of inter-rater scoring. They may NOT use the data for publication, teaching, or any other purpose without separate written consent.

2. **Subcontractors.** The reviewer may not delegate review work to associates, residents, or other clinicians not specifically named in this BAA.

3. **Data return / destruction.** All sample materials returned or destroyed within 30 days of quarterly cycle close.

4. **Breach notification.** Reviewer must notify within 24 hours of any suspected unauthorized disclosure.

5. **Termination.** Either party may terminate with 30 days' notice; obligations survive for the duration of any PHI access already granted.

6. **Audit rights.** PACCA owner may audit reviewer's data handling practices on reasonable notice.

7. **Indemnification.** Reviewer indemnifies PACCA for any breach caused by reviewer's negligence; PACCA indemnifies reviewer for breach in PACCA's transmission of the data.

> **Important.** Even though PACCA's review data is synthetic by design (per `CLAUDE.md` HIPAA rules), the BAA framing is still required because (a) it's the FDA's expected artifact for subcontractor governance, and (b) it future-proofs the panel for the eventuality of payer-data review work. Synthetic data today; the BAA structure must support real-PHI review tomorrow.

Engage privacy counsel for template drafting (see `BAA_INVENTORY.md` regulatory section). Budget ~$2K-5K flat fee for initial template; subsequent panelist BAAs are mostly cut-paste of the same template.

## Intake interview script

Use for first conversation after a candidate expresses interest. ~30 minutes; rule out fast, ramp in fast.

### Section 1 — Credentials verification (5 min)

- [ ] Board certification in [specialty]? Year obtained, year of last MOC?
- [ ] State medical license — active, no public actions?
- [ ] Active clinical practice within the last 24 months — what setting, what volume?
- [ ] No prior employment, consulting, or equity relationship with PACCA, project owner, or any payer/PBM whose decisions PACCA references?

### Section 2 — Experience in clinical decision support / AI (10 min)

- [ ] Familiar with prior authorization workflows? On which side (provider, payer, IDN)?
- [ ] Any prior experience reviewing clinical AI outputs? Examples?
- [ ] Comfort with the concept of "synthetic clinical cases" — i.e., scenarios not drawn from a single real patient?
- [ ] Familiar with NCCN / ACC / specialty-specific guideline structure?

### Section 3 — Workflow logistics (10 min)

- [ ] Available 4-8 hours per quarter for the next 12 months? Cadence flexibility?
- [ ] Comfortable with structured scoring rubric vs. free-text review? (PACCA uses both)
- [ ] Comfortable with blinded review (you see the case + the system's outcome label, but not the rationale; your job is to independently judge correctness)?
- [ ] Comfortable with the BAA terms (briefly summarize key clauses)?

### Section 4 — Red flags (5 min)

Any "yes" here is a hard stop:
- Active litigation as plaintiff or defendant in any medical AI case
- Equity or board position in a competing clinical-decision-support company
- Recent (within 24 months) public disciplinary action
- Unwillingness to sign standard BAA + conflict-of-interest disclosure

## Recruitment timeline (8-12 weeks per panelist)

| Week | Activity | Owner |
|---|---|---|
| 1 | Outreach (channel-specific: society directory query, academic email, KOL intro request) | Project owner |
| 2-3 | Initial response + scheduling intake call | Project owner |
| 3-4 | Intake interview (30 min) + reference check | Project owner |
| 4-5 | BAA + COI disclosure sent | Privacy counsel |
| 5-7 | BAA negotiation / review by panelist's counsel | Both parties |
| 7-8 | BAA execution | Both parties |
| 8-10 | Onboarding: read CASE_AUTHORING_GUIDE, sample-review walkthrough, scoring rubric calibration on 2-3 retired cases | Project owner |
| 10-12 | First quarterly review cycle begins | Panelist |

**Critical-path implication for the 300-case push.** To have a 2-3 person panel reviewing the first quarterly sample at week 6 (200-case milestone), outreach to **at least 5 candidates** starts in **week 1**. Expect a 40-60% conversion rate from outreach to executed BAA. Five outreach → 2-3 active panelists is the planning ratio.

## First-quarter logistics

When the panel is active (target: week 6-8 of the push):

1. **Stratified random sample.** Select 10% of the dataset (at 200 cases: 20 cases). Stratification dimensions per `EVALUATION_COVERAGE.md`: outcome class (APPROVE / DENY / IN_REVIEW), specialty, age stratum.
2. **Blinded distribution.** Each panelist receives the cases + system's outcome label, but NOT the system's confidence score or rationale. Sample format: CSV export per `CASE_AUTHORING_GUIDE.md` § 12 (until a managed review portal is selected).
3. **Score collection.** Panelist marks each case as "agree" / "disagree" / "uncertain" with optional free-text rationale.
4. **Aggregation.** Cohen's κ computed between each panelist and the cataloged outcomes, plus inter-panelist κ. Target: κ ≥ 0.80 panelist-to-system; inter-panelist κ ≥ 0.70.
5. **Disagreement triage.** Cases flagged by ≥1 panelist go into the case-revision queue. Per `CASE_AUTHORING_GUIDE.md` § 12.4, these get marked `provisional` in `CASE_PROVENANCE.md` and re-reviewed in the next iteration.
6. **Findings document.** Write `docs/findings/clinical-review-board-YYYY-Q.md` summarizing κ scores, flagged cases, and revision recommendations. This becomes part of the FDA submission package.

## Anti-patterns to avoid

- **Recruiting "friends of the project."** A panelist who is already enthusiastic about PACCA introduces systematic bias toward the system's labels. The point is independent verification, not enthusiastic validation.
- **Over-relying on one specialty.** A panel that's all cardiology produces κ scores that don't generalize to the dataset's distribution.
- **Skipping calibration.** Without a 2-3 case calibration round on retired cases, panelists score with different rubric interpretations and inter-panelist κ drops.
- **Letting panelist tenure extend past 4 quarters.** Long tenure → drift toward system biases. Rotation is non-optional.

---

*Last updated: 2026-05-27.*
