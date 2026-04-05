# PACCA Demo Walkthrough — Interview & Recruiter Guide

**Version:** 2.2.0
**For:** Technical interviews, recruiter conversations, portfolio reviews

---

## The One-Paragraph Summary

PACCA is a multi-agent AI system that automates healthcare prior authorization. A provider submits a clinical case; four specialized AI agents evaluate it against real clinical guidelines retrieved from a vector database; a deterministic 7-branch escalation tree routes the case to auto-approval, a Medical Director AI agent, or a human reviewer; every decision is written to a HIPAA-conscious audit trail with correlation-ID tracing. The system learns from human override decisions without model retraining, and includes a governed policy evolution mechanism (Level 5 architecture) where AI-proposed guideline amendments require human Medical Director approval before deployment.

**What makes it non-trivial:** It does not wrap a chat API. It implements deterministic agent contracts, an anti-hallucination safety architecture, production-grade security (SECRET_KEY validation at startup, JWT auth, bcrypt), OpenTelemetry observability, a clinical evaluation framework with LLM-as-judge and a CI accuracy gate, and a 53-case synthesized demo dataset covering every system path.

---

## Scoring Context

The system was evaluated against an 8-dimension Product Requirements Document rubric before and after a 6-week development sprint:

| Dimension | Before (v2.1) | After (v2.2.0) |
|-----------|--------------|----------------|
| Agent Architecture | 4/5 | **5/5** |
| Orchestration/Escalation | 2/5 | **5/5** |
| RAG Pipeline | 4/5 | **5/5** |
| Prompt Engineering | 3/5 | **5/5** |
| Observability/Tracing | 1/5 | **5/5** |
| Evaluation Framework | 2/5 | **5/5** |
| Scalability Architecture | 2/5 | **5/5** |
| Security/HIPAA Posture | 2/5 | **5/5** |
| **Overall** | **2.70/5.0** | **5.0/5.0** |

---

## 10-Minute Interview Demo Script

### Minute 0–2: The Happy Path (show auto-approval)

Start with `DEMO-A01` — NSCLC pembrolizumab, all criteria documented.

> *"Here's the happy path. A provider submits a lung cancer case requesting pembrolizumab. The clinical notes say PD-L1 is 62%, EGFR and ALK are negative, this is first-line therapy, ECOG performance status is 1. The NCCN guidelines say pembrolizumab monotherapy is Category 1 for PD-L1 ≥50% with no EGFR/ALK. The Decision Agent checks each criterion against the notes explicitly, arrives at confidence 0.97 — above our 0.95 threshold — and the case auto-approves with no human touch."*

Key point to make: **"Every criterion is explicitly cited in the rationale. The agent doesn't say 'criteria met' — it says 'PD-L1 62% meets the ≥50% threshold, EGFR/ALK negative confirmed.' That specificity matters for compliance."**

---

### Minute 2–4: The Safety Story (pre-flight blocks LLM)

Switch to `DEMO-D01` — CAR-T therapy Q2041.

> *"Now here's what happens when a provider requests CAR-T therapy. Same oncology domain, but the system routes to human review before the LLM is ever called. The procedure code Q2041 is on our experimental treatment list. Pre-flight checks run in microseconds of pure Python — no API call, no cost. The case goes directly to human review. The rationale says exactly why."*

Key point: **"A confident AI is not the same as a correct AI. For experimental treatments, we have minimal training data and sparse guidelines. Confidence-based escalation is insufficient — we need policy-based escalation. That's what pre-flight checks implement."**

Show that neither the Decision Agent nor Medical Director Agent is called. `decision_agent.run.assert_not_called()` — this is literally a test case in the suite.

---

### Minute 4–6: The Hallucination Trap

Show `DEMO-B01` — NSCLC pembrolizumab with only "Patient has lung cancer. Requesting pembrolizumab."

> *"This is the hallucination trap. Same diagnosis, same drug as the first case — but the clinical notes provide zero detail. A less careful system would fill in the blanks. It might say 'PD-L1 TPS likely meets threshold' or invent an EGFR result. PACCA's agent correctly identifies all the missing documentation: PD-L1 not documented, EGFR/ALK status unknown, performance status missing. It routes to human review asking for those specific items. It does NOT invent values."*

Key point: **"The anti-hallucination instruction is literally in every agent's system prompt: 'Only reference evidence explicitly present in the submission. If a lab value is not in the notes — do NOT mention it.' And we have specific test cases (GC-018, GC-019 in the golden dataset) that verify this with LLM-as-judge scoring."**

---

### Minute 6–8: Institutional Memory

Show `DEMO-H01` — lumbar MRI with foot drop, 4 weeks symptoms.

> *"Here's the institutional memory case. The CMS rule requires 6 weeks of conservative therapy before authorizing a lumbar MRI. This patient has had only 4 weeks. Normally that would be a denial. But the clinical notes describe developing foot drop — progressive motor weakness. The guidelines context includes a section called PAST MEDICAL DIRECTOR DECISIONS that records two previous cases where Medical Directors approved MRI despite less than 6 weeks of symptoms, specifically when foot drop was present. The agent cites both the exception clause AND the precedent and approves the case."*

Key point: **"This is learning without retraining. When a Medical Director overrides an AI decision and records a rationale, that rationale is embedded into ChromaDB's case_precedents collection. Future semantically similar cases retrieve it. The model's weights don't change — the retrieval context does."**

---

### Minute 8–10: The Governance Story

Reference the admin governance API.

> *"After 10 or more Medical Director overrides for 'MRI with foot drop under 6 weeks,' the Policy Evolution Agent analyzes the pattern and proposes a guideline amendment: amend the lumbar MRI rule to add an exception for documented progressive motor weakness. The proposal is stored as pending. A human Medical Director reads it at GET /admin/proposals, confirms the clinical reasoning is sound, and approves it at POST /admin/proposals/{id}/approve. Only then does the amended guideline get deployed to ChromaDB. Every amendment — proposed, approved, and deployed — is in the immutable change log."*

Key point: **"This directly addresses FDA SaMD Action Plan requirements for AI-driven clinical decision support changes. The agent can never autonomously modify the clinical guidelines it uses to make decisions. That separation is a hard architectural property, not a policy."**

---

## Running the Demo

### Prerequisites

```bash
cd /Users/davidreed/David_Portfolio/pacca
source venv/bin/activate
export ANTHROPIC_API_KEY=sk-ant-...
```

### Option 1: Dry-run (verify setup, no API calls)

```bash
python demo/run_demo.py --dry-run
```

Prints all 53 cases with expected branches and outcomes. Use this to walk through the demo without spending API tokens.

### Option 2: Run specific groups

```bash
# Run 5 auto-approve cases (Group A)
python demo/run_demo.py --groups A --limit 5

# Run all pre-flight cases (Groups D, E, F, G)
python demo/run_demo.py --groups DEFG

# Run hallucination trap cases (Group B cases B01 and B08)
python demo/run_demo.py --groups B --limit 2
```

### Option 3: Full demo (all 53 cases)

```bash
python demo/run_demo.py
```

Results are saved to `demo/results_YYYYMMDD_HHMMSS.json`. Langfuse traces appear at http://localhost:3001 if `OTEL_ENDPOINT` is configured.

---

## The 53 Demo Cases — Summary

### Group A — Auto-Approved (15 cases)
All 15 cases have complete documentation and explicit guideline alignment. The agent correctly cites specific criteria for each approval. Includes:
- Standard oncology (pembrolizumab, trastuzumab, cyclophosphamide)
- Cardiology (empagliflozin for T2DM+CVD, ocrelizumab for PPMS)
- Rheumatology (abatacept for RA, adalimumab for PsA and Crohn's)
- Preventive care (colonoscopy screening, CGM for T1DM)
- Emergency (leukostasis/ALL requiring STAT authorization)
- Institutional memory (foot drop MRI override with precedent)

### Group B — Human Review / Documentation Issues (10 cases)
Cases where documentation is missing, step therapy incomplete, or the agent would need to hallucinate to approve. Includes two specific hallucination traps (B01 and B08) with sparse notes.

### Group C — Medical Director Escalation (8 cases)
Cases where clinical criteria are met but cost exceeds $100K threshold, or confidence falls in the 0.90–0.95 ambiguous zone. The MD Agent receives the Tier 1 decision and must address the specific uncertainty.

### Group D — Experimental Treatment Pre-flight (5 cases)
CAR-T therapies (Q2041, Q2042), gene therapy (J3399), unclassified antineoplastic (J9999), and a standard drug used in an investigational protocol. Pre-flight fires before any LLM call.

### Group E — Rare Condition Pre-flight (4 cases)
Gaucher disease (E75.22), Huntington disease (G10), ALS (G12.21), Wilson disease (E83.01). ICD-10 prefix matching triggers specialist review regardless of treatment cost or guideline clarity.

### Group F — Conflicting Guidelines Pre-flight (4 cases)
Real coverage conflicts: NCCN recommends vs. CMS LCD restricts. ASMBS approves vs. payer LCD requires additional step. AHA/ACC says statin alone sufficient vs. CMS LCD requires ezetimibe first.

### Group G — Prior Denial Pre-flight (4 cases)
Includes a same-day denial + resubmission (fraud pattern), a valid resubmission with corrected documentation, and a resubmission where nothing has changed.

### Group H — Precedent-Based Approvals (3 cases)
Cases where institutional memory is essential: foot drop MRI override, off-label TMB-high sarcoma (tumor-agnostic FDA approval applies), hospice morphine (CMS exception documented in precedents).

---

## Key Technical Talking Points by Audience

### For a Technical Interviewer (Staff/Principal level)

1. **Why custom framework vs LangChain?** — Compliance requires inspectable decision paths. Every escalation decision is a readable conditional in orchestrator.py, not a framework callback. You can audit the entire decision tree in 200 lines of Python.

2. **How does the test suite verify clinical reasoning?** — The fast suite (140 tests, ~8 seconds) verifies structural behavior: routing, audit wiring, config API, security. The clinical suite uses LLM-as-judge with a 20-case golden dataset and an 80% accuracy CI gate. Failing that gate means the system's reasoning quality degraded, not just that a unit test broke.

3. **What's the dual-collection RAG architecture?** — `nccn_guidelines` stores authoritative clinical guidelines. `case_precedents` stores embedded human override decisions. They have different trust levels, update frequencies, and versioning requirements. The institutional memory mechanism (precedents) implements learning without model retraining.

4. **How does the governance pipeline work?** — PolicyEvolutionAgent produces proposals. Proposals are stored as `pending`. A human approves via POST /admin/proposals/{id}/approve. Only then does ChromaDB get updated. Every change is in the immutable PolicyChangeLogEntry. The agent cannot touch ChromaDB directly.

5. **How is SECRET_KEY handled?** — `SECRET_KEY = os.getenv("SECRET_KEY", "")`. `validate_secret_key()` is called in the FastAPI lifespan — the server refuses to start if the key is missing or shorter than 32 characters. This is tested in `test_security_and_scalability.py`.

### For a Healthcare / Clinical AI Interviewer

1. **What clinical safety properties does the system have?** — Pre-flight checks enforce policy on experimental treatments and rare conditions before any AI reasoning. The anti-hallucination instructions are explicit in every agent prompt. A hallucination trap test with LLM-as-judge zero-tolerance scoring catches agents that invent clinical data.

2. **How does it handle uncertainty?** — Confidence score < 0.90 routes to human review. 0.90–0.95 routes to a second AI agent (Medical Director) that must specifically address why the first agent was uncertain. ≥0.95 auto-approves. The system is calibrated to escalate uncertainty, not paper over it.

3. **What's the HIPAA architecture?** — Pre-write audit records, correlation-ID tracing, start/complete pairs per agent, success=False for failures. See `docs/HIPAA_COMPLIANCE.md` for the full mapping to specific CFR provisions.

### For a Recruiter / Non-Technical Reader

PACCA is a complete AI system for one of healthcare's most expensive problems: the prior authorization process that adds 34+ hours per week of administrative work per physician practice. The system uses multiple AI agents working together — like a clinical team — where simpler cases are handled automatically and complex cases are escalated to more senior review (human or AI).

The important thing is what it's NOT: it's not a simple chatbot or a prompt wrapper. It implements real healthcare compliance requirements (HIPAA audit trails), real clinical safety guardrails (experimental treatment detection, hallucination prevention), and a real governance process for how the AI learns and evolves. These are the engineering details that distinguish a portfolio project that demonstrates Staff/Principal-level thinking from one that demonstrates junior-level thinking.

---

## Common Questions and Answers

**Q: Does it work? Have you run it against real cases?**
A: Yes. The 53-case demo dataset produces real Langfuse traces when run with a valid API key. The LLM-as-judge evaluation framework scores actual agent reasoning against clinical gold standards. The test suite of 140 tests verifies system behavior from unit to clinical accuracy levels.

**Q: Why healthcare? Do you have clinical background?**
A: The choice was deliberate. Healthcare AI requires solving problems that less-regulated domains don't: deterministic escalation logic, audit trail compliance, anti-hallucination at a patient safety level, and governance of AI-driven changes to clinical decision-making. These constraints produce better engineering. PACCA demonstrates Staff-level thinking precisely because the domain makes technical shortcuts dangerous.

**Q: What would it take to deploy this in production?**
A: See `docs/HIPAA_COMPLIANCE.md`. Primary requirements: BAA with Anthropic (or on-prem model), encryption at rest for all datastores, TLS for all connections, formal HIPAA risk assessment, and access management procedures. The architecture is designed for this — the `.env.example` documents the full production configuration. The engineering work is done; the compliance process would take 3–6 months.

**Q: What's the Level 5 architecture?**
A: In multi-agent AI literature, Level 5 refers to systems that can modify their own behavior over time. PACCA's Level 5 component is the PolicyEvolutionAgent: it analyzes patterns in human overrides and proposes amendments to the clinical guidelines the system uses for decisions. Unlike a self-modifying system, PACCA's Level 5 requires human approval for every proposed change — making it a governed learning system rather than an autonomous one.

---

*PACCA v2.2.0 — April 2026*
*See also: `demo/cases.json` (53 synthesized cases), `tests/clinical/golden_cases.py` (20 evaluation cases)*
