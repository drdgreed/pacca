# PACCA — Prior Authorization & Care Coordination Agent Platform
## Consolidated Product Requirements Document
### Version 2.2 — Forward-Looking Production Specification

**Author:** David Reed, PhD, MBA, PMP | Executive Fellow, Wharton
**Affiliation:** Head of Career Advancement & AI/ML Delivery, Interview Kickstart
**Former:** Master Technologist (Principal/Distinguished Engineer), Hewlett-Packard
**Repository:** github.com/drdgreed/pacca
**Date:** April 2026
**Document Type:** Forward-Looking Product Specification — Production Deployment Target

---

## Table of Contents

1. Executive Summary
2. Problem Statement and Market Context
3. Product Vision and Strategic Objectives
4. What Has Been Built — v2.2.0 Prototype
5. Technical Architecture
6. AI and Multi-Agent Design
7. Retrieval-Augmented Generation Pipeline
8. Prompt Engineering and Agent Safety
9. Observability and Operational Control
10. Clinical Evaluation Framework
11. Security Architecture
12. HIPAA-Conscious Design
13. Scalability and Performance
14. Policy Evolution — Level 5 Architecture
15. Functional Requirements — Delivered and Planned
16. Technology Stack
17. Key Design Decisions
18. Demo Scenarios and Testing
19. Future Roadmap
20. Appendices

---

## 1. Executive Summary

PACCA (Prior Authorization & Care Coordination Agent Platform) is a production-targeted, multi-agent AI system that automates clinical prior authorization decisions for healthcare payers and providers. The system combines hierarchical AI agent orchestration, retrieval-augmented generation against real clinical guidelines, deterministic clinical safety escalation logic, and a complete HIPAA-conscious audit infrastructure.

The v2.2.0 prototype demonstrates the full architecture end-to-end, scoring 5.0/5.0 across eight evaluation dimensions after a structured six-week development sprint that addressed every gap identified in the v2.1 baseline evaluation.

| Evaluation Dimension | v2.1 Baseline | v2.2.0 | Delta |
|---|---|---|---|
| D1 — Agent Architecture | 4/5 | **5/5** | +1 |
| D2 — Orchestration/Escalation | 2/5 | **5/5** | +3 |
| D3 — RAG Pipeline | 4/5 | **5/5** | +1 |
| D4 — Prompt Engineering | 3/5 | **5/5** | +2 |
| D5 — Observability/Tracing | 1/5 | **5/5** | +4 |
| D6 — Evaluation Framework | 2/5 | **5/5** | +3 |
| D7 — Scalability Architecture | 2/5 | **5/5** | +3 |
| D8 — Security/HIPAA Posture | 2/5 | **5/5** | +3 |
| **Weighted Overall** | **2.70/5.0** | **5.0/5.0** | **+2.30** |

The production deployment pathway is fully specified. The engineering work is complete. The remaining gap is the compliance process: Business Associate Agreements with Anthropic and database infrastructure providers, formal HIPAA Security Risk Assessment, and enterprise authentication integration.

---

## 2. Problem Statement and Market Context

### 2.1 The Prior Authorization Bottleneck

Prior authorization is a mandatory payer review process that determines whether a proposed clinical service will be covered by insurance before it is delivered. It exists to prevent unnecessary care and control costs. In practice, the administrative burden it creates has grown to a point where it materially damages patient outcomes.

The manual prior authorization workflow at a large health system follows this timeline:

| Step | Activity | Time |
|---|---|---|
| 1 | Clinical request submission — provider initiates via EHR or fax | 5–10 min |
| 2 | Triage and routing — manual assignment to reviewer queue | 30–120 min |
| 3 | Evidence gathering — reviewer compiles EHR, labs, imaging, pharmacy | 2–6 hours |
| 4 | Clinical review — physician evaluates against medical necessity criteria | 1–2 hours |
| 5 | Decision documentation — manual entry into multiple systems | 30–60 min |
| 6 | Communication — phone or fax to requesting provider | 2–4 hours |
| 7 | Appeal management (if denied) — repeat cycle with additional evidence | 48–168 hours |

End-to-end, a single prior authorization request consumes 6–12 hours of productive clinical and administrative time in routine cases, and up to a full week when appeals are required.

### 2.2 Market Scale and Financial Impact

- **$50–100 billion** in annual administrative overhead attributable to prior authorization across U.S. healthcare
- **200 million+** prior authorization requests processed annually across U.S. health systems
- **34+ hours per week** that the average physician practice spends on prior authorization workflows
- **29% of delayed or denied authorizations** result in care delays that directly harm patient outcomes — postponed surgeries, withheld medications, disrupted care plans
- Reviewers using outdated guideline versions in **35% of cases**, contributing to inconsistent decisions
- Reviewer decision quality varies **18–35% depending on the individual**, a structural quality problem with no solution in the manual process

### 2.3 Why Agentic AI Addresses This Problem

The root causes of the prior authorization bottleneck map directly to capabilities that agentic AI can address:

**Information fragmentation (71% of bottleneck).** Clinical evidence is scattered across EHR, lab, imaging, pharmacy, and claims systems. An Evidence Aggregation Agent retrieves and synthesizes this data automatically, eliminating the 2–6 hour manual evidence gathering step.

**Inconsistent human judgment (52% of bottleneck).** Reviewer decisions vary with the individual. An AI agent evaluating the same case against the same current guidelines every time eliminates this variability for straightforward cases, routing only genuinely ambiguous cases to human reviewers.

**Static routing (40% of bottleneck).** Manual triage assigns requests to generic queues regardless of complexity or clinical risk. A Classification Agent scoring complexity and routing to the appropriate tier eliminates mis-routing and its downstream rework.

**No institutional memory (foundational limitation).** When a Medical Director makes an exception to a standard guideline and records a rationale, that knowledge currently lives in an email or a notes field. PACCA's dual-collection RAG architecture embeds override rationales into the retrieval system — future similar cases automatically surface the relevant precedent.

**Regulatory tailwinds.** The FDA relaxed clinical AI oversight in December 2025. The EU AI Act enforcement begins Q2 2026 with exemptions for clinical decision support under physician control. The market environment for deploying well-designed clinical AI has never been more favorable.

### 2.4 PACCA's Solution

PACCA automates the prior authorization workflow using a multi-agent pipeline where each agent has a defined role, defined escalation path, and operates under explicit behavioral contracts:

1. **Evidence Aggregation Agent** — synthesizes submitted clinical data into a structured narrative, identifying prior treatments, current clinical status, and medical necessity justification.
2. **Clinical Classification Agent** — scores case complexity (1–5 scale), identifies relevant medical specialty, and assesses urgency to determine routing path.
3. **Decision Support Agent (Tier 1 — Frontline Nurse)** — evaluates the case against retrieved guidelines using chain-of-thought reasoning, assessing each criterion as MET / NOT MET / UNCLEAR.
4. **Medical Director Agent (Tier 2)** — invoked for ambiguous cases; applies clinical nuance and a more conservative threshold appropriate for complex decisions.
5. **Orchestrator** — coordinates the pipeline, enforces the 7-branch escalation tree including deterministic pre-flight checks, and writes the complete audit trail.
6. **Policy Evolution Agent (Level 5)** — analyzes patterns in human override decisions and proposes governed guideline amendments, subject to Medical Director approval.

---

## 3. Product Vision and Strategic Objectives

### 3.1 Vision Statement

PACCA will be the authoritative AI platform for healthcare prior authorization decisions: faster than manual review, more consistent than human judgment on routine cases, safer than any existing automated system for high-risk and complex cases, and fully auditable to the standard required by HIPAA, FDA SaMD regulations, and CMS coverage determination requirements.

### 3.2 Strategic Objectives

**Reduce administrative cost.** Target 70–80% automation rate on routine prior authorization requests — cases with complete documentation and clear guideline alignment. Each automated case eliminates 6–12 hours of administrative time and replaces it with a sub-30-second decision.

**Improve decision quality.** Eliminate the 18–35% reviewer variability by applying current, versioned clinical guidelines consistently to every case. Human reviewers handle only cases where genuine clinical judgment is required.

**Preserve clinical safety.** Never automate decisions that a human must make. The 7-branch escalation tree encodes clinical policy as deterministic code, ensuring experimental treatments, rare conditions, conflicting guidelines, and prior denials always reach a human reviewer regardless of AI confidence level.

**Build institutional memory.** Transform Medical Director override decisions from ephemeral notes into structured, retrievable knowledge. The dual-collection RAG architecture means the system improves with every human decision, without model retraining.

**Achieve regulatory readiness.** Every design decision is made with HIPAA audit requirements, FDA SaMD Action Plan change control requirements, and CMS coverage determination standards as constraints, not afterthoughts.

### 3.3 Maturity Model Position

PACCA implements **Level 5 agentic architecture** — the highest tier on the AI Agentic Maturity Model described in Anthropic's *Levels of Agentic AI: A Practical Maturity Model for Enterprise Deployment* (2025). Level 5 is characterized by agents that can propose modifications to their own operating policies, subject to human governance controls.

The `PolicyEvolutionAgent` is PACCA's Level 5 implementation: it analyzes patterns in human override decisions, proposes specific guideline amendments, and requires Medical Director approval before any amendment is deployed. The agent can learn from experience without the system requiring model retraining, prompt modification by engineers, or any change to application code.

---

## 4. What Has Been Built — v2.2.0 Prototype

### 4.1 Architecture Overview

PACCA v2.2.0 is a fully functional full-stack application demonstrating every architectural component described in this document. The implementation flow is:

1. A provider submits a prior authorization request via React dashboard or REST API.
2. JWT authentication validates the session before any clinical data is processed.
3. The FastAPI backend retrieves relevant guidelines via semantic search against ChromaDB.
4. The Orchestrator runs pre-flight clinical risk checks (pure Python, no LLM call) to detect experimental treatments, rare conditions, conflicting guidelines, or prior denials.
5. Cases that pass pre-flight are evaluated by the Decision Support Agent against retrieved guidelines.
6. Cases with borderline confidence escalate to the Medical Director Agent for a second opinion.
7. All routing decisions and agent outputs are written to the HIPAA-conscious audit trail with correlation-ID tracing.
8. The JSON decision with rationale, confidence score, and escalation status is returned to the frontend.

### 4.2 Implemented Components

#### Backend (Python 3.11+ / FastAPI)

- **API Layer:** FastAPI with full async support, Pydantic v2 request/response models, JWT authentication, CORS configuration, and health/metrics endpoints.
- **Agent Framework:** Custom hierarchical multi-agent system with a base agent class providing retry, OTel instrumentation, and tool-use structured output. Five specialized agents with versioned prompts.
- **RAG Pipeline:** ChromaDB dual-collection architecture with 1000-character sentence-boundary-aware chunking, cosine similarity scoring, metadata filtering, and graceful fallback.
- **Orchestrator:** Full 7-branch escalation tree. Pre-flight checks run deterministically before any LLM call. Post-agent routing based on confidence thresholds.
- **Database Layer:** SQLAlchemy 2.0 async ORM with PostgreSQL 16 as production target, SQLite for development. Repository pattern decouples business logic from database engine. Alembic migration support.
- **Audit Trail:** Pre-write correlation-ID-linked audit records with start/complete pairs per agent, success/failure tracking, and token usage recording.
- **Configuration API:** Runtime-adjustable operational settings without restart. Confidence thresholds, cost thresholds, feature flags, and retry parameters all configurable via `PATCH /admin/config`.
- **Governance API:** Policy proposal store, human approval workflow, immutable change log.

#### Frontend (React 18 / TypeScript)

- Provider dashboard with real-time authorization status
- Case submission form with ICD-10 diagnosis codes, CPT/HCPCS procedure codes, clinical notes, and urgency level
- Decision display with confidence scores, reasoning chain, and escalation status
- Demo mode with 53 pre-configured clinical scenarios

#### Infrastructure

- Docker and Docker Compose for one-command deployment of 6 services (API, PostgreSQL 16, ChromaDB, Redis, Langfuse observability UI, Langfuse PostgreSQL)
- GitHub Actions CI/CD pipeline
- OpenTelemetry instrumentation with Langfuse integration for full trace visibility

### 4.3 Test Coverage

The v2.2.0 test suite contains 140 passing tests with zero failures, executing in approximately 8 seconds:

| Test File | Tests | Coverage Area |
|---|---|---|
| test_audit_trail.py | 5 | Audit wiring contracts |
| test_config_api.py | 18 | Runtime configuration API |
| test_escalation_tree.py | 24 | All 7 escalation branches + edge cases |
| test_models.py | 20 | v2.2 domain models and enums |
| test_prompt_engineering.py | 18 | Prompt registry and governance pipeline |
| test_retry_and_tracing.py | 12 | Retry logic and OTel spans |
| test_security_and_scalability.py | 20 | Auth, async session, RAG |
| test_clinical_accuracy.py (fast) | 23 | Dataset integrity, pre-flight, evaluator |
| **Total** | **140** | |

The clinical evaluation suite (LLM-as-judge, requiring API key) adds a full accuracy gate: 80% minimum accuracy across 20 golden cases, with zero-tolerance hallucination testing on sparse-documentation cases.

---

## 5. Technical Architecture

### 5.1 Component Responsibilities

| Component | Responsibility | Production Database |
|---|---|---|
| React Frontend | Provider interface, case submission, decision display | — |
| JWT Auth | Session validation, bcrypt password hashing | PostgreSQL 16 |
| FastAPI Backend | Request routing, audit initiation, response assembly | PostgreSQL 16 |
| ChromaDB (dual-collection) | Guideline retrieval, precedent storage | ChromaDB volumes |
| Multi-Agent Orchestrator | Pipeline coordination, escalation enforcement | — (stateless) |
| Decision Support Agent | Tier 1 clinical evaluation | Claude API |
| Medical Director Agent | Tier 2 ambiguous case resolution | Claude API |
| Policy Evolution Agent | Guideline amendment proposals | ChromaDB + PostgreSQL |
| OpenTelemetry → Langfuse | Distributed tracing, agent performance visibility | Langfuse PostgreSQL |
| Audit Log | HIPAA-compliant event trail | PostgreSQL 16 (JSONB) |

### 5.2 Request Lifecycle

A complete authorization request follows this sequence:

1. **Submission:** Provider submits clinical case. Audit record written before processing begins.
2. **Pre-flight:** Orchestrator runs ClinicalRiskDetector.evaluate(). If any check fires, case routes to IN_REVIEW immediately with no LLM call.
3. **RAG retrieval:** GuidelineRetriever queries both ChromaDB collections, returns ranked context including official guidelines and applicable precedents.
4. **Tier 1 evaluation:** DecisionSupportAgent evaluates case against context. Returns confidence score and recommendation. Audit start/complete pair written.
5. **Confidence routing:**
   - confidence ≥ 0.95 and AUTO_APPROVED → return immediately (Branch 1)
   - 0.90 ≤ confidence < 0.95 → MedicalDirectorAgent (Branch 2)
   - confidence < 0.90 → IN_REVIEW (Branch 3)
6. **Tier 2 evaluation (if invoked):** MedicalDirectorAgent receives Tier 1 decision and must address the specific hesitation. Audit start/complete pair written.
7. **Final decision:** Persisted to PostgreSQL. Correlation-ID links all audit records. JSON response returned to frontend.

### 5.3 Data Model

The core domain models are:

```
ClinicalCase
  patient_id: str
  primary_diagnosis_code: str       (ICD-10)
  procedure_code: str               (CPT/HCPCS)
  evidence: List[EvidenceItem]

EvidenceItem
  id: str
  source_type: EvidenceSourceType   (LAB_RESULT | CLINICAL_NOTE | MEDICATION | PATIENT_REPORTED)
  description: str
  original_text: str
  confidence: float

AuthorizationDecision
  decision_id: str                  (UUID7 — time-sortable)
  status: AuthorizationStatus       (AUTO_APPROVED | IN_REVIEW | DENIED | PENDING)
  confidence_score: float
  rationale: str
  review_tier_used: ReviewTier      (AUTOMATED | MEDICAL_DIRECTOR_AGENT | HUMAN)
  audit_trail: List[AuditLogEntry]

AuditLogModel (PostgreSQL)
  entry_id: str                     (UUID7)
  correlation_id: str               (shared across all records for one request)
  action: str                       (structured action type)
  actor: str                        (provider NPI, agent name, or "system")
  actor_type: str                   ("provider" | "agent" | "user" | "system")
  success: bool
  error_message: str | None
  duration_ms: int
  token_usage: JSONB
  details: JSONB
  timestamp: datetime               (UTC)
```

### 5.4 Database Strategy — Development vs. Production

The entire data layer uses SQLAlchemy 2.0 async ORM with the Repository pattern. Switching between development and production databases is a single environment variable:

```bash
# Local development — zero infrastructure required
DATABASE_URL=sqlite+aiosqlite:///./pacca.db

# Production — PostgreSQL 16 full feature set
DATABASE_URL=postgresql+asyncpg://pacca:password@db:5432/pacca
```

PostgreSQL 16 is required in production for three specific capabilities that SQLite cannot provide at scale: native JSONB columns with indexed JSON-path queries for compliance reporting, row-level locking and MVCC for concurrent write safety, and managed replication for high availability. The `AuditLogModel.details` and `AuditLogModel.token_usage` fields are defined as `JSONB` in `db/models.py`, enabling queries such as:

```sql
SELECT * FROM audit_logs
WHERE details->>'confidence_score'::float < 0.85
AND details->>'agent' = 'DecisionSupportAgent'
AND timestamp > NOW() - INTERVAL '30 days';
```

---

## 6. AI and Multi-Agent Design

### 6.1 Agent Hierarchy

PACCA implements a hierarchical supervision pattern that mirrors clinical review workflows in real utilization management departments:

| Agent | Tier | Clinical Analogy | Invocation Condition |
|---|---|---|---|
| DecisionSupportAgent | 1 | Frontline UM Nurse | Every case passing pre-flight |
| MedicalDirectorAgent | 2 | Chief Medical Director | Confidence 0.90–0.95 from Tier 1 |
| EvidenceAggregationAgent | Support | Clinical Data Analyst | Pre-evaluation evidence synthesis |
| ClinicalClassificationAgent | Support | Triage Coordinator | Complexity scoring and routing |
| PolicyEvolutionAgent | Governance | Quality Improvement Lead | Periodic pattern analysis |

### 6.2 The 7-Branch Escalation Tree

The escalation tree is the system's most clinically critical component. Every branch is implemented as deterministic logic in `agents/orchestrator.py` and `agents/clinical_risk_detector.py`. No branch relies on AI reasoning — all routing decisions are pure Python conditionals that a compliance auditor can read without understanding machine learning.

**Pre-flight branches (run before any LLM call):**

| Branch | Trigger | Implementation | Clinical Rationale |
|---|---|---|---|
| 4 | Experimental treatment | Procedure code in EXPERIMENTAL_PROCEDURE_CODES frozenset, or experimental keyword in evidence text | AI confidence is unreliable on treatments with thin training data |
| 5 | Rare condition | ICD-10 code prefix matches RARE_CONDITION_ICD10_PREFIXES frozenset | Guidelines sparse or contradictory; specialist required |
| 6 | Conflicting guidelines | RAG context contains both approval and rejection language | Averaging across conflicting guidelines produces a confidently wrong answer |
| 7 | Prior denial same service | Procedure code in prior_denial_codes list | Two scenarios require human distinction: fraud vs. changed circumstances |

**Post-agent branches (run after Decision Agent):**

| Branch | Condition | Action |
|---|---|---|
| 1 | confidence ≥ 0.95 + AUTO_APPROVED | Return immediately — no human touch |
| 2 | 0.90 ≤ confidence < 0.95 | Invoke MedicalDirectorAgent |
| 2a | MD confidence ≥ 0.95 | AUTO_APPROVED |
| 2b | MD confidence < 0.95 | IN_REVIEW |
| 3 | confidence < 0.90 | IN_REVIEW |

### 6.3 The Base Agent Contract

Every agent inherits from `BaseAgent`, which enforces three invariants:

**Structured output invariant.** All agents use Claude's tool-use API with `tool_choice: {type: "tool", name: "submit_result"}`. The model is forced to populate a defined Pydantic schema. Structured output is a guarantee enforced by the API, not a parsing heuristic. A response that does not populate the schema raises a `ValidationError`, not a runtime error that silently produces wrong data.

**Retry invariant.** All LLM calls are wrapped in tenacity exponential backoff with configurable parameters. Transient errors (429 rate limit, 5xx server errors, connection errors) are retried up to `llm_retry_max_attempts` times. Non-retriable errors (400 bad request, 401 authentication) fail immediately — retrying these would send the same invalid data repeatedly.

**Tracing invariant.** Every agent execution opens exactly one OpenTelemetry span covering the full call including retries. The span records agent name, model, input/output token counts, duration, and any errors. One span per agent call means Langfuse shows the total time including retries, not separate misleading spans per attempt.

### 6.4 Prompt Architecture

All five agent system prompts are assembled from shared components plus agent-specific content:

```
AGENT_IDENTITY              — who the agent is and what it must maintain
CLINICAL_SAFETY_GUIDELINES  — anti-hallucination rules, uncertainty flagging,
                              escalation triggers (applied to ALL agents)
[Agent-specific content]    — evaluation framework, scoring rubric, authority scope
OUTPUT_FORMAT_INSTRUCTIONS  — structured output enforcement
```

The `PROMPT_REGISTRY` in `agents/prompts/templates.py` tracks version, description, and change history for all five agents. Version strings are embedded in the system prompt text itself, so they flow through audit logs. When a case is reviewed weeks later, the exact prompt version that processed it is recoverable from the audit record.

---

## 7. Retrieval-Augmented Generation Pipeline

### 7.1 Dual-Collection Architecture

PACCA maintains two separate ChromaDB collections with different trust levels, update frequencies, and versioning policies:

**`nccn_guidelines` — Authoritative Clinical Guidelines**
- Sources: NCCN, CMS, AHA, ADA, ACR, and specialty societies
- Update frequency: quarterly, synchronized with guideline publication cycles
- Versioning: guidelines tagged with source, version number, and effective date
- Rollback policy: full rollback supported — old version remains available for audit

**`case_precedents` — Institutional Memory**
- Sources: Medical Director human override decisions with documented rationales
- Update frequency: continuous — every approved human override is embedded immediately
- Versioning: each precedent tagged with reviewer ID, decision date, and original case ID
- Rollback policy: individual precedents can be archived without touching the guideline collection

The collections are separate because a rollback of institutional learning must never affect authoritative guidelines, and a guideline update must never overwrite institutional precedents. This constraint cannot be reliably enforced in a single collection.

### 7.2 RAGPipeline Implementation

The `RAGPipeline` in `rag/pipeline.py` is the primary retrieval implementation:

- **Chunking:** 1000-character chunks with 200-character overlap, sentence-boundary aware. Overlap prevents clinical criteria that span sentence boundaries from being split across chunks.
- **Embedding:** ChromaDB's default embedding model (sentence-transformers). Production upgrade path: OpenAI `text-embedding-3-large` or Anthropic's embedding models for improved clinical domain performance.
- **Scoring:** Cosine similarity scoring with distance-to-similarity conversion. Minimum threshold applied to filter low-relevance results.
- **Filtering:** Metadata filtering by treatment category and specialty before scoring. Fallback retry without filter if no results meet threshold.
- **Context assembly:** Results from both collections merged, ranked by relevance, and assembled into a structured context string. A `PAST MEDICAL DIRECTOR DECISIONS (PRECEDENTS)` section is prepended when relevant precedents are found, with explicit agent instructions to weight precedents heavily.

### 7.3 Institutional Memory Mechanism

When a human reviewer overrides an AI decision:

1. The route handler calls `vector_store.add_precedent(rationale, metadata)`.
2. The rationale text is embedded and stored in `case_precedents` with metadata including: original decision ID, procedure code, diagnosis code, reviewer ID, and override direction (approved despite denial / denied despite approval).
3. Future cases with semantically similar diagnosis + procedure combinations retrieve this precedent during the RAG query phase.
4. The precedent appears in the guidelines context under `PAST MEDICAL DIRECTOR DECISIONS`, with the date and direction of the override visible to the agent.

This mechanism implements institutional learning without model retraining, without prompt modification by engineers, and without any change to application code. The system improves continuously from production use.

---

## 8. Prompt Engineering and Agent Safety

### 8.1 CLINICAL_SAFETY_GUIDELINES — Shared Baseline

Every agent's system prompt includes an identical `CLINICAL_SAFETY_GUIDELINES` block. This block enforces three universal constraints:

**Anti-hallucination.** "Only reference clinical evidence explicitly present in the submission. If a lab value, test result, diagnosis confirmation, or prior therapy history is not in the submitted notes — do NOT mention it, infer it, or assume it. State explicitly what is missing."

**Uncertainty flagging.** "When evidence is ambiguous, documentation is incomplete, or guideline criteria cannot be definitively assessed, state this clearly. A clear statement of uncertainty is clinically preferable to a confident wrong answer."

**Escalation triggers.** "Route to human review for: high-risk cases, rare conditions, conflicting evidence, experimental treatments, incomplete documentation, or any case where you are not highly confident in both the decision and the rationale."

Changes to `CLINICAL_SAFETY_GUIDELINES` propagate to all five agents simultaneously, ensuring no agent operates without the safety baseline.

### 8.2 MedicalDirectorAgent Prompt Design (v2.2)

The Medical Director Agent's v2.2 prompt was redesigned from a 2-line description to a structured 5-component specification:

1. **Identity and authority scope.** The agent is framed as "resolving Tier 1 uncertainty" — not re-evaluating from scratch. It receives the Tier 1 decision and must specifically address why the first agent was uncertain.
2. **What the agent cannot do.** Explicit prohibition: the MD Agent cannot override pre-flight escalation triggers. A case that was pre-escalated for experimental treatment stays in human review regardless of the MD Agent's confidence.
3. **4-step evaluation framework.** Read the Tier 1 decision. Identify the specific uncertainty. Evaluate whether additional guideline context resolves it. Recommend with explicit rationale addressing the hesitation.
4. **Version embedding.** The string `v2.2` appears in the prompt text itself, flowing into audit logs.
5. **CLINICAL_SAFETY_GUIDELINES block.** Applied identically to Tier 1.

### 8.3 PolicyEvolutionAgent Governance Framing (v2.2)

The v2.1 `PolicyEvolutionAgent` prompt implicitly allowed autonomous deployment of guideline amendments. The v2.2 prompt explicitly prohibits this:

- "You produce PROPOSALS, not deployments. No guideline is modified by your action."
- "Human Medical Director approval is required before any amendment is deployed."
- "You do not have direct access to ChromaDB. Your output is a structured proposal document."
- A reviewer checklist must be populated for every proposal, including the pattern evidence that motivated it, the specific guideline text being amended, and the clinical rationale.

---

## 9. Observability and Operational Control

### 9.1 OpenTelemetry Instrumentation

Every agent execution generates exactly one OTel span. Span attributes include:

| Attribute | Value |
|---|---|
| `agent.name` | Agent class name (e.g. "DecisionSupportAgent") |
| `llm.model` | Model string (e.g. "claude-sonnet-4-20250514") |
| `llm.input_tokens` | Tokens consumed by the prompt |
| `llm.output_tokens` | Tokens in the response |
| `llm.total_tokens` | Sum |
| `duration_ms` | Wall-clock milliseconds including retries |
| `input.length_chars` | Character count of the user prompt |

Retry events are logged before each sleep interval with attempt number, wait duration, and error type. This produces a structured record of API instability patterns without requiring log parsing.

### 9.2 Langfuse Integration

Langfuse is included as a Docker Compose service. Setting `OTEL_ENDPOINT=http://localhost:4318` routes all spans automatically. The Langfuse UI at `http://localhost:3001` provides:

- Per-agent latency distributions and token usage over time
- Retry frequency broken down by agent and error type
- Full request traces with correlation-ID linkage — every audit record for one request linked to its OTel trace

### 9.3 Runtime Configuration API

All operational parameters are adjustable at runtime via `PATCH /admin/config` without server restart. This is a production safety feature: when an audit begins or an incident occurs, parameters can be adjusted in seconds:

- `enable_autonomous_decisions: false` — routes all cases to human review instantly
- `auto_approve_confidence_threshold: 0.98` — tightens the auto-approve threshold immediately
- `high_cost_threshold: 50000` — lowers the cost escalation trigger
- `otel_enabled: false` — disables tracing (e.g. during performance testing)
- `llm_retry_max_attempts: 5` — increases retries during API instability

The API validates threshold relationships on every PATCH: `auto_approve_confidence_threshold` must exceed `escalation_confidence_threshold`, or the update is rolled back with a 422 response.

---

## 10. Clinical Evaluation Framework

### 10.1 LLM-as-Judge Architecture

The clinical evaluation suite in `tests/clinical/` verifies that the system *reasons correctly*, not just that it runs. This distinction is critical: a system can pass 140 unit tests and still produce clinically dangerous reasoning. The evaluation framework addresses this directly.

The evaluator uses Claude Haiku (fast, cost-effective for bulk evaluation) as the judge. The judge receives: the original clinical case, the agent's decision, the agent's rationale, and a structured scoring rubric.

### 10.2 Scoring Rubric

| Score | Meaning |
|---|---|
| 5 | Correct decision, complete reasoning, no hallucination, explicit criterion citation |
| 4 | Correct decision, mostly complete reasoning, minor gaps |
| 3 | Correct decision, adequate but vague reasoning |
| 2 | Wrong decision OR correct decision with seriously flawed reasoning |
| 1 | Wrong decision on a clearly documented case OR any hallucination detected |

Score 1 is automatic for hallucination. Inventing a lab value, test result, or prior therapy history is a patient safety event — not a reasoning quality issue. It receives the minimum score regardless of whether the overall decision happened to be correct.

### 10.3 Golden Dataset — 20 Cases

The 20 golden cases in `tests/clinical/golden_cases.py` span eight clinical groups:

| Group | Cases | Representative scenarios |
|---|---|---|
| A: Clear approvals | 3 | NSCLC pembrolizumab (full documentation), lumbar MRI (foot drop exception), T2DM SGLT2 inhibitor (CV indication) |
| B: Clear denials | 2 | Acute LBP (2 weeks, no conservative therapy), psoriasis biologic (step therapy incomplete) |
| C: Pre-flight escalation | 4 | CAR-T therapy, Gaucher disease ERT, prior denial resubmission, Phase II clinical trial drug |
| D: MD escalation | 2 | High-cost biologic with criteria met, NCCN vs. CMS conflict |
| E: Edge cases | 4 | Pediatric biologic, borderline documentation, precedent-based override, incomplete submission |
| F: Step therapy | 2 | Crohn's biologic (adequate step therapy documented), PsA biologic (NSAID-only — insufficient) |
| G: Hallucination traps | 2 | NSCLC pembrolizumab with sparse notes ("patient has lung cancer. requesting pembrolizumab"), psoriasis with no clinical detail |
| H: Urgency override | 1 | Leukostasis / ALL — oncological emergency requiring STAT authorization |

### 10.4 CI Gate

The CI gate requires ≥80% accuracy (cases scoring ≥3) or the pipeline fails. The failure message is actionable: it identifies which cases failed, whether hallucinations were detected, and which file contains the failing cases.

The hallucination zero-tolerance test runs separately on cases GC-018 and GC-019 (the sparse-notes cases). Any hallucination in either case is an immediate test failure independent of the overall accuracy gate.

---

## 11. Security Architecture

### 11.1 Authentication and Secret Management

`SECRET_KEY` is loaded exclusively from the environment variable `SECRET_KEY`. The application calls `validate_secret_key()` during the FastAPI lifespan startup sequence. If the key is absent or shorter than 32 characters, the server refuses to start and logs the exact command to generate a valid key. This is fail-fast security: a misconfigured deployment fails loudly at startup, not silently at the first authentication request.

JWT tokens are issued with a configurable expiry (default 30 minutes via `TOKEN_EXPIRE_MINUTES`). Thirty minutes was chosen as the default because it limits the exposure window for intercepted tokens while remaining practical for active clinical sessions.

### 11.2 Password Storage

Passwords are hashed with bcrypt. `bcrypt.gensalt()` generates a unique random salt per password, preventing rainbow table attacks. `bcrypt.checkpw()` performs timing-safe comparison, preventing timing side-channel attacks. No plaintext passwords are stored anywhere in the system.

### 11.3 Route Protection

All routes touching clinical data or operational configuration require a valid JWT via `Depends(verify_token)`. The only unauthenticated routes are `POST /api/v1/login/` and `GET /health`.

### 11.4 CORS Configuration

CORS origins are parameterized and restricted to explicit lists in production. The wildcard `*` origin is never used in production configuration.

---

## 12. HIPAA-Conscious Design

This document presents HIPAA-conscious design patterns. PACCA v2.2.0 is a portfolio demonstration, not a HIPAA-certified product. See `docs/HIPAA_COMPLIANCE.md` for the complete CFR provision mapping.

### 12.1 Audit Control — 45 CFR §164.312(b)

Every authorization request generates a `correlation_id` UUID at submission. This UUID is stamped on every audit record in the request lifecycle. A compliance query for one request retrieves the complete chain:

```
correlation_id: 550e8400-e29b-41d4-a716-446655440000

1. authorization_submitted      actor: provider NPI       success: true
2. agent_decision_started       actor: DecisionSupportAgent v2.2
3. agent_decision_completed     actor: DecisionSupportAgent duration_ms: 3420
4. escalation_auto_approved     actor: orchestrator       branch: 1_auto_approve
5. authorization_finalized      actor: system             status: AUTO_APPROVED
```

Audit records are written **before** processing begins. If the system crashes mid-processing, the record proves the request was received and processing was initiated. Without pre-write auditing, a mid-flight crash produces a PHI access event with no audit trail.

Every agent execution generates a `start` record and a `complete` record. An orphaned `start` with no matching `complete` identifies the exact agent that failed during a multi-agent trace.

### 12.2 Person Authentication — 45 CFR §164.312(d)

JWT authentication with bcrypt password hashing. Fail-fast SECRET_KEY validation at startup. 30-minute token expiry by default, configurable for stricter deployments.

### 12.3 Access Control — 45 CFR §164.312(a)(1)

JWT required on all clinical routes. Actor identity (provider NPI or username) recorded on every audit record, implementing PHI access accountability.

### 12.4 Integrity Controls — 45 CFR §164.312(c)(1)

The audit log is append-only. No route or agent implements audit record modification or deletion. The `success=False` pattern means failures are new records, not modifications to existing ones. The Policy Change Log is also append-only — a complete regulatory audit trail of every AI-proposed guideline change.

### 12.5 Minimum Necessary — 45 CFR §164.514(d)

The system captures diagnosis codes, procedure codes, clinical notes, and evidence summaries. It does not capture Social Security Numbers, financial data, or demographic information beyond what is clinically necessary. The anti-hallucination instruction in every agent prompt is also a PHI minimization control: an agent that invents clinical details would be generating false PHI records, which is both a patient safety event and a HIPAA integrity violation.

### 12.6 Production Deployment Requirements

A production deployment additionally requires:

- Business Associate Agreement with Anthropic (or on-premises model deployment)
- BAA with managed database and observability platform providers
- Encryption at rest for all datastores containing PHI
- TLS 1.2+ on all connections
- Formal HIPAA Security Risk Assessment per 45 CFR §164.308(a)(1)
- Multi-factor authentication for administrative access
- Incident response plan with 60-day breach notification procedures per 45 CFR §164.412

---

## 13. Scalability and Performance

### 13.1 Async Architecture

The system is fully asynchronous throughout. All route handlers use `AsyncSession` from `db/session.py`. All agent LLM calls use `await self.client.messages.create(...)`. No blocking I/O occurs on the event loop. This architecture allows FastAPI to handle concurrent requests while waiting for LLM responses, which take 3–8 seconds each. A synchronous architecture would serialize concurrent users; the async architecture supports hundreds of concurrent requests.

### 13.2 Connection Pooling

PostgreSQL connections are managed via a configured pool:
- `pool_size: 5` — persistent connections held open
- `max_overflow: 10` — additional connections allowed under burst load
- `pool_timeout: 30s` — maximum wait for an available connection
- `pool_pre_ping: true` — health check each connection before use

These settings activate automatically with PostgreSQL and are no-ops with SQLite.

### 13.3 Performance Targets

| Metric | Target | Current Status |
|---|---|---|
| API response (non-LLM endpoints) | < 200ms | Achieved |
| Tier 1 decision (routine case) | < 8 seconds | Dependent on Claude API latency (3–8s) |
| Tier 2 decision (complex case) | < 20 seconds | Achieved including both agent calls |
| Concurrent users (architecture target) | 500+ | Async architecture supports this; not load-tested at scale |
| Throughput | 100+ authorizations/minute | Architecture supports; dependent on Claude API rate limits |

---

## 14. Policy Evolution — Level 5 Architecture

### 14.1 Overview

The `PolicyEvolutionAgent` implements PACCA's self-improvement mechanism. It analyzes patterns in human Medical Director override decisions and proposes specific amendments to the clinical guidelines used for authorization decisions.

This is Level 5 agentic architecture: the system can propose modifications to its own operating policies. The governance pipeline ensures this capability cannot be exercised autonomously — every proposed amendment requires human Medical Director approval before deployment.

### 14.2 Three-Stage Governance Pipeline

**Stage 1 — Analysis and Proposal**

The agent is invoked via `POST /admin/optimize_policies`. It queries the case_precedents collection for patterns in human override decisions. When a recurring override pattern is detected (e.g., MRI approved in 10+ cases despite < 6 weeks conservative therapy when foot drop is present), the agent produces a `PolicyProposal` stored as `status='pending'`.

The proposal contains: the specific guideline text to be amended, the proposed replacement text, the override pattern evidence (case IDs, dates, Medical Director rationale), and a reviewer checklist.

Nothing is deployed at this stage.

**Stage 2 — Human Review**

`GET /admin/proposals` lists pending proposals. `GET /admin/proposals/{id}` returns the full proposal with override pattern evidence.

**Stage 3 — Approval or Rejection**

`POST /admin/proposals/{id}/approve` (with `reviewer_id`) deploys the amendment to the `nccn_guidelines` ChromaDB collection via `vector_store.add_guideline()` AND creates an immutable `PolicyChangeLogEntry` recording: the change ID, proposal ID, guideline ID, original text, new text, approving reviewer, deployment timestamp, and rationale summary.

`POST /admin/proposals/{id}/reject` records the rejection without modifying any guideline.

### 14.3 The Change Log

`GET /admin/change-log` returns the complete append-only history of every AI-proposed guideline change. This log is never modified. It is the regulatory audit trail required by the FDA AI/ML SaMD Action Plan for AI-driven changes to clinical decision support logic.

### 14.4 Why Governance Matters Here

An `auto_deploy=True` pattern — the v2.1 behavior — would mean the AI modifies its own clinical guidelines without human oversight. In a healthcare context this is a regulatory liability: FDA SaMD Action Plan change control requirements, CMS coverage determination integrity, and HIPAA audit requirements all demand human accountability for changes to the clinical logic used to make coverage decisions.

The three-stage governance pipeline converts the EvolutionAgent from an autonomous liability into a governed learning system. The agent contributes the pattern recognition; the human contributes the clinical judgment about whether the pattern represents sound policy.

---

## 15. Functional Requirements — Delivered and Planned

### 15.1 Delivered in v2.2.0

| Feature | Description | Status |
|---|---|---|
| Evidence Aggregation | AI synthesizes clinical data into structured narrative | Complete |
| Clinical Classification | Complexity scoring 1–5, specialty routing, urgency | Complete |
| Guideline-Based Decision Support | RAG-powered retrieval with chain-of-thought evaluation | Complete |
| 7-Branch Escalation Tree | All branches including 4 pre-flight checks | Complete |
| Medical Director Tier 2 | Second-opinion agent for ambiguous cases | Complete |
| Confidence Scoring | Calibrated thresholds with tiered routing | Complete |
| Dual-Collection RAG | nccn_guidelines + case_precedents with institutional memory | Complete |
| PROMPT_REGISTRY | Versioned prompts for all 5 agents with audit trail integration | Complete |
| OTel Instrumentation | One span per agent call with token usage and retry events | Complete |
| Langfuse Integration | Full trace visibility via Docker Compose service | Complete |
| Clinical Evaluation Framework | 20-case golden dataset, LLM-as-judge, CI accuracy gate | Complete |
| Hallucination Zero-Tolerance Test | Separate CI gate for sparse-documentation cases | Complete |
| HIPAA Audit Trail | Pre-write records, correlation-ID, start/complete pairs | Complete |
| Runtime Config API | All operational parameters adjustable without restart | Complete |
| Policy Evolution Agent | 3-stage governance pipeline with immutable change log | Complete |
| JWT Authentication | bcrypt, fail-fast SECRET_KEY validation, 30-min expiry | Complete |
| PostgreSQL/SQLite one-line switch | Production PostgreSQL, development SQLite, same ORM | Complete |
| Docker Compose full stack | 6 services including Langfuse and PostgreSQL 16 | Complete |
| Demo Dataset | 53 synthesized cases covering all 7 escalation branches | Complete |
| 140 Unit Tests | 0 failures, ~8 seconds | Complete |

### 15.2 Deferred to Production Release

| Feature | Original Plan | Deferral Reason |
|---|---|---|
| Communication Agent | Automated provider notifications via SMS, EHR portal | Requires Twilio and EHR API partnerships |
| Appeal Automation | AI-generated appeal narratives with evidence gap analysis | Requires V1 feedback loop data volume |
| EHR Integration | Bidirectional FHIR data flow with Epic/Cerner/Athena | Requires institutional partnerships and FHIR credentials |
| OAuth 2.0 / SAML | Federated identity with institutional SSO | Enterprise infrastructure concern; JWT proves the pattern |
| Redis Caching | Semantic caching of common evidence patterns | Not needed at prototype volume; 40–60% token reduction at scale |
| Pinecone Migration | Production SaaS vector database with BAA | ChromaDB proves the architecture; Pinecone is a config change |
| Kubernetes Deployment | Auto-scaling agent workers | Docker Compose proves the containerization pattern |
| Continuous Model Validation | Drift detection beyond CI gate | Requires production traffic volume for meaningful metrics |
| MFA | Multi-factor authentication for administrative access | Required for production HIPAA compliance; not needed for prototype |

---

## 16. Technology Stack

| Layer | Technology | Version | Notes |
|---|---|---|---|
| LLM | Claude (Anthropic API) | claude-sonnet-4 | Tool-use forced for structured output |
| Backend | Python, FastAPI, Pydantic v2 | 3.11+ / 0.115+ / 2.10+ | Fully async throughout |
| Production DB | PostgreSQL, SQLAlchemy, Alembic | 16 / 2.0 | JSONB, async engine, connection pool |
| Dev DB | SQLite (same ORM layer) | — | One env var to switch |
| Vector Store | ChromaDB (dual-collection) | 0.5+ | nccn_guidelines + case_precedents |
| Observability | OpenTelemetry → Langfuse | 1.27+ | One span per agent call |
| Retry | Tenacity (exponential backoff) | 9.0+ | Configurable via settings |
| Testing | pytest, pytest-asyncio, pytest-cov | 8.3+ / 0.21+ | 140 tests, 0 failures |
| Security | python-jose, bcrypt | 3.3+ / 4.0+ | JWT + timing-safe password hashing |
| Frontend | React 18, TypeScript, Tailwind CSS, Vite | — | |
| Containers | Docker, Docker Compose | — | 6-service full stack |
| CI/CD | GitHub Actions | — | Lint → Test → Coverage |

---

## 17. Key Design Decisions

| Decision | Options Considered | Choice Made | Rationale |
|---|---|---|---|
| Agent framework | CrewAI, LangGraph, AutoGen, Custom | Custom 150-line base class | Healthcare requires deterministic escalation logic — framework abstractions obscure compliance-critical control flow |
| Vector database | Pinecone, Milvus, Weaviate, ChromaDB | ChromaDB (local) + dual-collection | Zero infrastructure for prototype; production migration path to Pinecone is a config change |
| Primary database | PostgreSQL, SQLite, MongoDB | PostgreSQL 16 (prod) / SQLite (dev) | Hard relational constraints; JSONB compliance queries; single ORM layer makes engine switch one env var |
| LLM provider | Claude only, GPT-4, Multi-model | Claude (Anthropic) | Superior clinical reasoning; BAA pathway available; native tool-use for structured output |
| Escalation design | Framework-driven, AI confidence only, Deterministic + AI | Deterministic pre-flight + confidence routing | AI confidence is not reliable for experimental/rare cases; policy must override AI judgment in these scenarios |
| Structured output | Free-form JSON parsing, Regex extraction, Tool-use API | Tool-use API forced | Makes structured output an API guarantee; eliminates the most common agentic failure mode (malformed JSON) |
| Authentication | OAuth 2.0 + SAML, JWT only | JWT + bcrypt | Proves the auth pattern; OAuth/SAML is an infrastructure concern for enterprise deployment |
| RAG strategy | Single collection, Pinecone+pgvector hybrid, Dual-collection | Dual-collection ChromaDB | Different trust levels, update frequencies, and rollback requirements for official guidelines vs. institutional precedents |
| Level 5 governance | Auto-deploy, Human approval gate, No evolution | Three-stage governance with approval gate | FDA SaMD Action Plan requires change control; auto-deploy is a regulatory liability for clinical decision logic |

---

## 18. Demo Scenarios and Testing

### 18.1 The 53-Case Synthesized Demo Dataset

`demo/cases.json` contains 53 fully synthesized clinical cases covering every escalation path in the 7-branch decision tree. Cases include complete clinical notes, procedure codes, diagnosis codes, and expected escalation branches.

| Group | Cases | Scenario |
|---|---|---|
| A | 15 | Auto-approved — complete documentation, explicit guideline alignment |
| B | 10 | Human review — missing documentation, incomplete step therapy, hallucination traps |
| C | 8 | MD escalation — cost >$100K or borderline confidence 0.90–0.95 |
| D | 5 | Experimental treatment pre-flight — CAR-T, gene therapy, clinical trial |
| E | 4 | Rare condition pre-flight — Gaucher, Huntington, ALS, Wilson disease |
| F | 4 | Conflicting guidelines pre-flight — NCCN vs. CMS vs. payer LCD |
| G | 4 | Prior denial pre-flight — resubmissions, same-day denial + refile, fraud pattern |
| H | 3 | Precedent-based approvals — institutional memory applying Medical Director overrides |

### 18.2 Running the Demo

```bash
# Verify all 53 cases load correctly (no API calls)
python demo/run_demo.py --dry-run

# Run 5 auto-approve cases
python demo/run_demo.py --groups A --limit 5

# Run all pre-flight cases to see zero-LLM routing in action
python demo/run_demo.py --groups DEFG

# Full demo — all 53 cases, populates Langfuse with real traces
python demo/run_demo.py
```

See `demo/demo_report.md` for the complete 10-minute interview demo script with per-case talking points for technical, clinical, and recruiter audiences.

---

## 19. Future Roadmap

### V2 — Enterprise Integration (6–12 months post-production)

1. **EHR Integration.** Bidirectional FHIR data flow with Epic, Cerner, and Athena. Automated evidence gathering from EHR replaces manual submission. The Evidence Aggregation Agent retrieves lab results, imaging reports, and medication history directly.
2. **Communication Agent.** Automated provider notifications via EHR messaging, SMS, and payer portal. Replaces phone and fax communication for routine decisions.
3. **Appeal Automation.** AI-generated appeal narratives incorporating evidence gap analysis from the original denial. Requires 6–12 months of production feedback loop data to train effectively.
4. **OAuth 2.0 / SAML.** Federated identity with institutional SSO providers. Standard enterprise requirement.
5. **Redis Caching.** Semantic caching of common evidence patterns and guideline retrieval results. Expected 40–60% reduction in LLM token consumption for high-volume deployments.

### V3 — Platform Scale (12–24 months)

6. **Kubernetes Deployment.** Auto-scaling agent workers with load-balanced request distribution. Target: 10,000+ authorizations per day.
7. **A2A Protocol Integration.** Agent-to-agent communication enabling cross-organizational authorization workflows — payer and provider systems communicating directly through PACCA agents.
8. **Domain-Specific Model Optimization.** Fine-tuned models using accumulated authorization decision data. Expected improvement in clinical reasoning quality on complex cases.
9. **Continuous Model Validation.** Langfuse-based drift detection comparing current model performance against the golden dataset on a rolling basis. Automated alerts when accuracy degrades below threshold.
10. **Multi-Payer Coverage Database.** Comprehensive database of payer-specific coverage policies and LCDs, maintained via automated ingestion of CMS coverage determination updates.

---

## 20. Appendices

### Appendix A — Environment Configuration Reference

| Variable | Description | Default | Production |
|---|---|---|---|
| `ANTHROPIC_API_KEY` | Claude API key | Required | Required + BAA |
| `SECRET_KEY` | JWT signing key (≥32 chars) | Required | Rotate quarterly |
| `DATABASE_URL` | Database connection | SQLite | PostgreSQL 16 |
| `TOKEN_EXPIRE_MINUTES` | JWT expiry | 30 | 15–30 |
| `AUTO_APPROVE_CONFIDENCE_THRESHOLD` | Auto-approve threshold | 0.95 | 0.95–0.98 |
| `ESCALATION_CONFIDENCE_THRESHOLD` | MD escalation threshold | 0.90 | 0.90–0.95 |
| `HIGH_COST_THRESHOLD` | Cost escalation trigger (USD) | 100000 | Set per payer contract |
| `LLM_RETRY_MAX_ATTEMPTS` | Max LLM retry attempts | 3 | 3–5 |
| `OTEL_ENDPOINT` | OTel collector URL | None | Langfuse or Jaeger |
| `ENABLE_AUTONOMOUS_DECISIONS` | Master autonomy switch | true | true (can be false for audit) |
| `CORS_ORIGINS` | Allowed frontend origins | localhost | Production domain only |

### Appendix B — API Reference

| Method | Endpoint | Auth | Description |
|---|---|---|---|
| POST | `/api/v1/login/` | None | Exchange credentials for JWT |
| POST | `/api/v1/authorizations/` | JWT | Submit authorization request |
| GET | `/api/v1/authorizations/` | JWT | List with pagination |
| GET | `/api/v1/authorizations/{id}` | JWT | Decision + full audit trail |
| GET | `/api/v1/admin/config` | JWT | Read operational configuration |
| PATCH | `/api/v1/admin/config` | JWT | Update config at runtime |
| DELETE | `/api/v1/admin/config/overrides` | JWT | Reset to env defaults |
| GET | `/api/v1/admin/metrics` | JWT | Operational metrics + Langfuse link |
| POST | `/api/v1/admin/optimize_policies` | JWT | Trigger policy evolution analysis |
| GET | `/api/v1/admin/proposals` | JWT | List pending policy proposals |
| GET | `/api/v1/admin/proposals/{id}` | JWT | Full proposal with reviewer checklist |
| POST | `/api/v1/admin/proposals/{id}/approve` | JWT | Approve and deploy amendment |
| POST | `/api/v1/admin/proposals/{id}/reject` | JWT | Reject proposal |
| GET | `/api/v1/admin/change-log` | JWT | Immutable policy change audit log |
| GET | `/health` | None | Health check |

### Appendix C — Repository Layout

```
pacca/
├── src/pacca/
│   ├── agents/
│   │   ├── base.py                    # ABC + retry + OTel spans
│   │   ├── orchestrator.py            # 7-branch escalation tree
│   │   ├── clinical_risk_detector.py  # Pre-flight checks (Branches 4–7)
│   │   ├── decision.py                # Tier 1 + Tier 2 agents
│   │   ├── evolution.py               # PolicyEvolutionAgent + governance
│   │   └── prompts/templates.py       # PROMPT_REGISTRY + versioned prompts
│   ├── api/
│   │   ├── auth.py                    # SECRET_KEY + validate_secret_key()
│   │   ├── main.py                    # FastAPI app + lifespan startup
│   │   └── routes/
│   │       ├── authorizations.py      # Core workflow + audit wiring
│   │       └── admin.py               # Config API + governance API
│   ├── config/
│   │   ├── settings.py                # Pydantic settings
│   │   └── tracing.py                 # OTel provider setup
│   ├── db/
│   │   ├── models.py                  # SQLAlchemy ORM (PostgreSQL JSONB)
│   │   ├── repository.py              # AuditRepository, AuthorizationRepository
│   │   └── session.py                 # Async engine + connection pool
│   ├── integrations/vector_store.py   # GuidelineRetriever → RAGPipeline (Adapter)
│   ├── rag/pipeline.py                # RAGPipeline: chunking + cosine scoring
│   └── models/                        # Pydantic domain models + enums
├── tests/unit/                        # 140 fast tests (no API calls)
├── tests/clinical/                    # 20-case golden dataset + LLM-as-judge
├── demo/                              # 53 synthesized cases + runner
└── docs/                              # Architecture + HIPAA + SDD + this document
```

---

*PACCA v2.2.0 — April 2026*
*github.com/drdgreed/pacca*
*Author: David Reed, PhD | david.reed@interviewkickstart.com*
