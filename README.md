# PACCA — Prior Authorization & Care Coordination Agent Platform

<p align="center">
  <strong>Production-Grade Multi-Agent AI for Healthcare Prior Authorization</strong>
</p>

<p align="center">
  <a href="#architecture">Architecture</a> •
  <a href="#engineering-decisions">Engineering Decisions</a> •
  <a href="#agent-design">Agent Design</a> •
  <a href="#quick-start">Quick Start</a> •
  <a href="#demo">Demo</a> •
  <a href="#api-reference">API Reference</a> •
  <a href="#compliance">Compliance</a>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/version-2.2.0-brightgreen.svg" alt="Version 2.2.0" />
  <img src="https://img.shields.io/badge/python-3.11+-blue.svg" alt="Python 3.11+" />
  <img src="https://img.shields.io/badge/FastAPI-async-009688.svg" alt="FastAPI async" />
  <img src="https://img.shields.io/badge/Claude-API-blueviolet.svg" alt="Claude API" />
  <img src="https://img.shields.io/badge/tests-140%20passing-brightgreen.svg" alt="140 tests passing" />
  <img src="https://img.shields.io/badge/PRD%20score-5.0%2F5.0-brightgreen.svg" alt="PRD score 5.0/5.0" />
  <img src="https://img.shields.io/badge/HIPAA-audit--ready-red.svg" alt="HIPAA audit-ready" />
  <img src="https://img.shields.io/badge/license-MIT-lightgrey.svg" alt="MIT License" />
</p>

---

## What This Is

PACCA automates healthcare prior authorization using a **hierarchical multi-agent AI system**. A provider submits a clinical case; the system evaluates it against real clinical guidelines via RAG; a confidence-tiered escalation tree routes to auto-approval, Medical Director AI review, or human review; a complete HIPAA-compliant audit trail captures every decision.

**The market problem:** Prior authorization costs U.S. healthcare $50–100B annually. Providers spend 34+ hours per week on manual workflows. 29% of delayed authorizations directly impact patient outcomes.

**What makes this technically non-trivial:** The system does not wrap a chat API. It implements deterministic agent contracts, dual-collection RAG that learns from human overrides without model retraining, a 7-branch escalation tree with clinical pre-flight checks, governed policy evolution (Level 5), a prompt version registry with audit trail, LLM-as-judge clinical evaluation, and full HIPAA-conscious audit infrastructure.

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                           PACCA v2.2.0                                  │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  ┌───────────────────────────────────────────────────────────────┐     │
│  │                     React 18 Frontend                          │     │
│  │       Dashboard · Authorization List · Review Interface        │     │
│  └────────────────────────────┬──────────────────────────────────┘     │
│                               │ JWT Bearer                              │
│  ┌────────────────────────────▼──────────────────────────────────┐     │
│  │                  FastAPI Backend (async)                        │     │
│  │    /authorizations  ·  /admin  ·  /health  ·  /login          │     │
│  └─────────┬─────────────────────────────┬─────────────────────┘      │
│             │                             │                              │
│  ┌──────────▼──────────────────┐  ┌──────▼───────────────────────┐    │
│  │    Agent Orchestration      │  │         Data Layer            │    │
│  │                             │  │                               │    │
│  │  PRE-FLIGHT CHECKS          │  │  PostgreSQL 16                │    │
│  │  ├─ Experimental treatment  │  │  ├─ Authorization requests    │    │
│  │  ├─ Rare condition          │  │  ├─ Decisions + rationale     │    │
│  │  ├─ Conflicting guidelines  │  │  ├─ Audit log (JSONB)         │    │
│  │  └─ Prior denial            │  │  └─ correlation_id tracing    │    │
│  │          │                  │  │                               │    │
│  │          ▼                  │  │  ChromaDB (dual-collection)   │    │
│  │  TIER 1: Decision Agent     │  │  ├─ nccn_guidelines           │    │
│  │  (Frontline UM Nurse)       │  │  └─ case_precedents           │    │
│  │  ├─ conf ≥0.95 → APPROVE    │  │       (institutional memory)  │    │
│  │  ├─ 0.90–0.95 → Tier 2      │  │                               │    │
│  │  └─ <0.90 → HUMAN REVIEW    │  │  OpenTelemetry → Langfuse     │    │
│  │          │                  │  │  (one span per agent call)    │    │
│  │          ▼                  │  └───────────────────────────────┘    │
│  │  TIER 2: Medical Director   │                                        │
│  │  (Resolves Tier 1 ambiguity)│  ┌───────────────────────────────┐    │
│  │  ├─ conf ≥0.95 → APPROVE    │  │  Policy Evolution (Level 5)   │    │
│  │  └─ <0.95 → HUMAN REVIEW    │  │  ├─ Proposal store (pending)  │    │
│  │          │                  │  │  ├─ Human approval gate        │    │
│  │          └──────────────────┤  │  └─ Immutable change log      │    │
│  │                             │  └───────────────────────────────┘    │
│  └─────────────────────────────┘                                        │
│                                                                         │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │  Clinical Evaluation (LLM-as-Judge)                              │   │
│  │  20 golden cases · Hallucination detection · CI gate 80%        │   │
│  └─────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────┘
```

### Key architectural properties

| Property | Implementation |
|----------|---------------|
| **Deterministic escalation** | Pre-flight checks are pure Python policy rules — no LLM call occurs for experimental treatments, rare conditions, conflicting guidelines, or prior denials |
| **Zero clinical reasoning in orchestrator** | All clinical logic lives in agents and clinical_risk_detector.py — the orchestrator is testable without any API calls |
| **Correlation-ID tracing** | Every audit record for one request shares a UUID — full lifecycle queryable in one call |
| **Anti-hallucination by design** | Tool-use API forces structured output; agent prompts include explicit "never hallucinate clinical information" safety guidelines |
| **Institutional memory without retraining** | Human override decisions are embedded into ChromaDB case_precedents — future similar cases retrieve them alongside official guidelines |
| **Prompt version control** | PROMPT_REGISTRY tracks version, description, and change history for all 5 agents — versions appear in audit logs |
| **Governed AI evolution** | PolicyEvolutionAgent produces proposals requiring human Medical Director approval before deployment |
| **Clinical evaluation CI gate** | LLM-as-judge evaluator with 80% accuracy threshold blocks deployments that degrade reasoning quality |

---

## Engineering Decisions

These are deliberate architectural choices. Each trade-off is documented because a system that cannot explain its own design is a liability in a regulated environment.

### Custom Agent Framework vs. LangChain / CrewAI

**Chose:** Custom 150-line agent base class (`agents/base.py`)

Healthcare prior authorization requires deterministic escalation logic — specific clinical conditions must trigger specific routing paths regardless of LLM confidence. Framework abstractions obscure this control flow and make compliance auditing harder. Every escalation decision in PACCA is a readable `if` statement in `agents/orchestrator.py`, not a framework callback. The trade-off is maintenance ownership; the benefit is fully inspectable decision paths.

### PostgreSQL + SQLite one-line switch

**Chose:** PostgreSQL 16 (production) / SQLite (local development)

The entire data layer uses SQLAlchemy 2.0 async ORM + Repository pattern. Switching between databases is one environment variable: `DATABASE_URL`. PostgreSQL's native JSONB columns enable compliance queries like `WHERE rationale_data->>'confidence_score' < '0.85'` across thousands of audit records. SQLite works identically in development with no infrastructure required.

### Dual-Collection RAG Architecture

**Chose:** Two ChromaDB collections — `nccn_guidelines` + `case_precedents`

Clinical guidelines and institutional precedents have different trust levels and update frequencies. Separating them allows independent versioning, different relevance-weighting in prompts, and rollback of institutional learning without touching authoritative guidelines. The precedents collection implements learning without model retraining: when a Medical Director overrides an AI decision with a rationale, that rationale is embedded; future semantically similar cases retrieve it alongside official guidelines.

### Tool-Use API for Structured Output

**Chose:** Force Claude's tool-use API for all agent responses

`tool_choice: {type: "tool", name: "submit_result"}` forces the model to populate a defined JSON schema. This makes structured output a guarantee enforced by the API — not a `json.loads()` call that silently fails. Combined with Pydantic validation, every agent response is a typed Python object or a catchable exception.

### Fully Async Throughout

**Chose:** FastAPI + AsyncSession + async agent calls

Each authorization involves 2–4 Claude API calls (3–8 seconds each). A synchronous server blocks the event loop during every API call. The async architecture yields control at every `await`, allowing the server to handle concurrent requests while waiting for LLM responses.

---

## Agent Design

### The 7-Branch Escalation Tree (PRD SS5.4 — fully implemented)

```
Authorization Request Received
│
├── PRE-FLIGHT CHECKS (deterministic, no LLM call)
│   ├── Branch 4: Experimental treatment code or clinical trial keyword → IN_REVIEW
│   ├── Branch 5: Rare condition ICD-10 prefix (prevalence <1:10,000) → IN_REVIEW
│   ├── Branch 6: Conflicting guidelines from multiple sources → IN_REVIEW
│   └── Branch 7: Prior denial for same procedure code → IN_REVIEW
│
└── POST-AGENT CHECKS (after Decision Agent)
    ├── Branch 1: confidence ≥ 0.95 + AUTO_APPROVED → return immediately
    ├── Branch 2: 0.90 ≤ confidence < 0.95 → Medical Director Agent
    │   ├── MD confidence ≥ 0.95 → AUTO_APPROVED
    │   └── MD confidence < 0.95 → IN_REVIEW
    └── Branch 3: confidence < 0.90 → IN_REVIEW
```

Tests: `tests/unit/test_escalation_tree.py` — 14 tests, one per branch plus edge cases. The test file is machine-readable documentation of the escalation policy.

### Prompt Engineering (v2.2)

All agent prompts use a three-component architecture:

```python
# Every agent system prompt = these three components + agent-specific content
AGENT_IDENTITY              # Who the agent is, what it maintains
CLINICAL_SAFETY_GUIDELINES  # Anti-hallucination rules (applied to ALL agents)
OUTPUT_FORMAT_INSTRUCTIONS  # Structured output enforcement
```

`PROMPT_REGISTRY` tracks every agent's version, description, and change history. The current version string is embedded in each prompt and flows through audit logs — when a case is debugged weeks later, you can identify exactly which prompt version processed it.

### Base Agent: Retry + OTel Spans

```python
# One span per agent call — timing, tokens, retries all captured
with self._tracer.start_as_current_span(f"agent.{self.name}") as span:
    response = await self._call_with_retry(user_input, tool_def)
    # span records: input_tokens, output_tokens, duration_ms

# Retry with exponential backoff — configurable via environment
@retry(
    stop=stop_after_attempt(settings.llm_retry_max_attempts),      # default: 3
    wait=wait_exponential(min=1.0, max=30.0),
    retry=retry_if_exception_type((RateLimitError, APIConnectionError, APITimeoutError)),
    reraise=True,
)
```

### Policy Evolution Agent (Level 5)

The `PolicyEvolutionAgent` analyzes patterns in human Medical Director overrides and proposes guideline amendments. Three-stage governance pipeline:

1. **Proposal** — agent produces `PolicyProposal` stored as `pending` in the proposal store
2. **Review** — human Medical Director reads the proposal via `GET /admin/proposals/{id}`
3. **Approval** — `POST /admin/proposals/{id}/approve` deploys to ChromaDB AND creates an immutable `PolicyChangeLogEntry`

Rejection writes a `rejected` record. No guidelines are ever modified without human approval. The change log is append-only — a complete regulatory audit trail of every AI-proposed guideline change.

---

## Clinical Evaluation Framework

### LLM-as-Judge

`tests/clinical/` implements a clinical accuracy evaluation suite:

- **20 golden cases** (`golden_cases.py`) — hand-crafted across all 8 clinical scenario groups (approvals, denials, pre-flight escalations, MD escalations, hallucination traps, precedent-based approvals)
- **LLM-as-judge evaluator** (`evaluator.py`) — Claude Haiku scores each agent decision 1–5 with an explicit rubric including anti-hallucination zero-tolerance criteria
- **CI gate** — accuracy must be ≥80% or the pipeline fails

```bash
# Run fast evaluation tests (no API calls)
pytest tests/clinical/test_clinical_accuracy.py -m "not clinical" -v

# Run full LLM-as-judge evaluation (requires ANTHROPIC_API_KEY, ~3-5 min)
pytest tests/clinical/ -m clinical -v
```

The hallucination detection cases are the most clinically important. When clinical notes provide zero detail, the agent must enumerate missing documentation — it must not invent lab values, test results, or prior therapy history.

---

## Demo — 53 Synthesized Cases

`demo/` contains a complete demonstration dataset:

| Group | Cases | Scenario |
|-------|-------|----------|
| A | 15 | Auto-approved — clear guideline alignment |
| B | 10 | Human review — missing/ambiguous documentation |
| C | 8 | MD escalation — high-cost or borderline confidence |
| D | 5 | Experimental treatment pre-flight (Branch 4) |
| E | 4 | Rare condition pre-flight (Branch 5) |
| F | 4 | Conflicting guidelines pre-flight (Branch 6) |
| G | 4 | Prior denial pre-flight (Branch 7) |
| H | 3 | Precedent-based approvals — institutional memory |

```bash
# Generate the demo dataset
python demo/generate_demo_data.py

# Verify all 53 cases load (no API calls)
python demo/run_demo.py --dry-run

# Run 5 auto-approve cases
python demo/run_demo.py --groups A --limit 5

# Full demo — all 53 cases, populates Langfuse with traces
python demo/run_demo.py
```

See `demo/demo_report.md` for the complete interview walkthrough with per-case talking points and a 10-minute demo script.

---

## Quick Start

### Option 1: Docker (recommended — full stack)

```bash
git clone https://github.com/Chaos-6/pacca.git
cd pacca

cp .env.example .env
# Set ANTHROPIC_API_KEY and generate SECRET_KEY:
# python -c "import secrets; print(secrets.token_hex(32))"

docker-compose up -d
```

| Service | URL |
|---------|-----|
| API + Swagger | http://localhost:8000/docs |
| Langfuse observability | http://localhost:3001 (admin@pacca.local / pacca_admin_dev) |
| ChromaDB | http://localhost:8001 |

### Option 2: Local development (SQLite, zero config)

```bash
git clone https://github.com/Chaos-6/pacca.git
cd pacca

python -m venv venv && source venv/bin/activate
pip install -e ".[dev]"

cp .env.example .env
# Edit .env: set ANTHROPIC_API_KEY
# Set DATABASE_URL=sqlite+aiosqlite:///./pacca.db

uvicorn pacca.api.main:app --reload --port 8000
```

### Running Tests

```bash
# Full fast suite (140 tests, ~8 seconds, no API calls)
pytest tests/unit/ tests/clinical/test_clinical_accuracy.py -m "not clinical" -v

# With coverage report
make test-cov

# Clinical evaluation (requires API key, 3-5 minutes)
make test-clinical
```

---

## API Reference

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| `POST` | `/api/v1/login/` | None | Exchange credentials for JWT |
| `POST` | `/api/v1/authorizations/` | JWT | Submit authorization request |
| `GET` | `/api/v1/authorizations/` | JWT | List with pagination |
| `GET` | `/api/v1/authorizations/{id}` | JWT | Get decision + audit trail |
| `GET` | `/api/v1/admin/config` | JWT | Read operational configuration |
| `PATCH` | `/api/v1/admin/config` | JWT | Update config at runtime (no restart) |
| `DELETE` | `/api/v1/admin/config/overrides` | JWT | Reset overrides to env defaults |
| `GET` | `/api/v1/admin/metrics` | JWT | Operational metrics |
| `POST` | `/api/v1/admin/optimize_policies` | JWT | Trigger policy evolution proposal |
| `GET` | `/api/v1/admin/proposals` | JWT | List pending policy amendments |
| `POST` | `/api/v1/admin/proposals/{id}/approve` | JWT | Approve + deploy amendment |
| `POST` | `/api/v1/admin/proposals/{id}/reject` | JWT | Reject amendment |
| `GET` | `/api/v1/admin/change-log` | JWT | Immutable policy change audit log |
| `GET` | `/health` | None | Health check |

Full interactive docs: `http://localhost:8000/docs`

### Example Request + Response

```bash
curl -X POST http://localhost:8000/api/v1/authorizations/ \
  -H "Authorization: Bearer <jwt>" \
  -H "Content-Type: application/json" \
  -d '{
    "request_id": "AUTH-001",
    "patient_id": "P-12345",
    "provider_npi": "1234567890",
    "clinical_case": {
      "patient_id": "P-12345",
      "primary_diagnosis_code": "C34.1",
      "procedure_code": "J9271",
      "evidence": [{
        "id": "e1",
        "source_type": "CLINICAL_NOTE",
        "description": "Stage IIIA NSCLC, PD-L1 TPS 62%, EGFR/ALK negative",
        "original_text": "58-year-old male, stage IIIA NSCLC adenocarcinoma...",
        "confidence": 0.95
      }]
    }
  }'
```

```json
{
  "decision_id": "DEC-01HQXYZ",
  "status": "AUTO_APPROVED",
  "confidence_score": 0.97,
  "rationale": "NCCN Category 1: Pembrolizumab monotherapy for PD-L1 TPS ≥50% NSCLC. All criteria documented: PD-L1 62% (meets ≥50% threshold), EGFR/ALK negative, first-line, ECOG 1.",
  "review_tier_used": "AUTOMATED",
  "timestamp": "2026-04-04T18:30:00Z"
}
```

---

## Project Structure

```
pacca/
├── src/pacca/
│   ├── agents/
│   │   ├── base.py                    # ABC + retry + OTel spans
│   │   ├── orchestrator.py            # 7-branch escalation tree
│   │   ├── clinical_risk_detector.py  # Pre-flight checks (Branches 4-7)
│   │   ├── decision.py                # Tier 1 + Tier 2 agents (v2.2 prompts)
│   │   ├── evolution.py               # Level 5: PolicyEvolutionAgent + governance
│   │   └── prompts/
│   │       └── templates.py           # PROMPT_REGISTRY + versioned system prompts
│   ├── api/
│   │   ├── main.py                    # FastAPI app + async auth routes
│   │   ├── auth.py                    # SECRET_KEY from env + validate_secret_key()
│   │   └── routes/
│   │       ├── authorizations.py      # Core workflow + audit wiring
│   │       └── admin.py               # Config API + governance API
│   ├── config/
│   │   ├── settings.py                # Pydantic settings (app_env includes "test")
│   │   └── tracing.py                 # OpenTelemetry provider setup
│   ├── db/
│   │   ├── models.py                  # SQLAlchemy ORM (PostgreSQL JSONB)
│   │   ├── repository.py              # AuditRepository, AuthorizationRepository
│   │   └── session.py                 # Async engine + session factory
│   ├── integrations/
│   │   └── vector_store.py            # GuidelineRetriever → RAGPipeline (Adapter)
│   ├── rag/
│   │   └── pipeline.py                # RAGPipeline: chunking + cosine scoring
│   └── models/                        # Pydantic domain models + enums
├── tests/
│   ├── unit/
│   │   ├── test_audit_trail.py        # 5 tests — audit wiring contracts
│   │   ├── test_config_api.py         # 18 tests — runtime config API
│   │   ├── test_escalation_tree.py    # 24 tests — all 7 branches + edge cases
│   │   ├── test_models.py             # 20 tests — v2.2 domain models
│   │   ├── test_prompt_engineering.py # 18 tests — registry + governance pipeline
│   │   ├── test_retry_and_tracing.py  # 12 tests — retry logic + OTel spans
│   │   └── test_security_and_scalability.py  # 20 tests — auth + async session
│   └── clinical/
│       ├── golden_cases.py            # 20 annotated clinical evaluation cases
│       ├── evaluator.py               # LLM-as-judge + JudgeVerdict + EvaluationReport
│       └── test_clinical_accuracy.py  # 23 tests including CI gate
├── demo/
│   ├── generate_demo_data.py          # Generates cases.json + demo_report.md + run_demo.py
│   ├── cases.json                     # 53 synthesized clinical cases
│   ├── demo_report.md                 # Interview walkthrough + talking points
│   └── run_demo.py                    # Live runner (populates Langfuse traces)
├── docs/
│   ├── ARCHITECTURE.md                # Component documentation + 5 ADRs
│   ├── RELEASE_NOTES_v2.2.md          # Sprint history + final scores
│   ├── HIPAA_COMPLIANCE.md            # HIPAA-conscious design documentation
│   └── PRD_v2.2.md                    # Product Requirements Document v2.2
├── CHANGELOG.md                       # Keep-a-Changelog format
├── Makefile                           # make test, test-cov, test-clinical, install
├── docker-compose.yml                 # 6 services incl. Langfuse + PostgreSQL
└── .env.example                       # Fully annotated environment reference
```

---

## Technology Stack

| Layer | Technology | Version |
|-------|------------|---------|
| **LLM** | Claude (Anthropic API) | claude-sonnet-4 |
| **Backend** | Python, FastAPI, Pydantic v2 | 3.11+ / 0.115+ / 2.10+ |
| **Production DB** | PostgreSQL, SQLAlchemy, Alembic | 16 / 2.0 |
| **Dev DB** | SQLite (same ORM layer) | — |
| **Vector Store** | ChromaDB (dual-collection) | 0.5+ |
| **Observability** | OpenTelemetry → Langfuse | 1.27+ |
| **Retry** | Tenacity (exponential backoff) | 9.0+ |
| **Testing** | pytest, pytest-asyncio, pytest-cov | 8.3+ / 0.21+ |
| **Security** | python-jose, bcrypt | 3.3+ / 4.0+ |
| **Containers** | Docker, Docker Compose | — |

---

## Compliance

PACCA is designed with HIPAA Security Rule 164.312(b) audit control requirements in mind. See [`docs/HIPAA_COMPLIANCE.md`](docs/HIPAA_COMPLIANCE.md) for full documentation.

Key design properties:
- Audit records written **before** processing begins — a crash mid-flight still leaves evidence the request was received
- Every audit record carries a `correlation_id` UUID — full request lifecycle queryable in one call
- `start` + `complete` audit pairs per agent — orphaned `start` records pinpoint exact failure locations
- `AuditLogModel.success=False` distinguishes failures without log parsing
- `SECRET_KEY` loaded from environment, validated at startup (refuses to start if missing or < 32 chars)
- JWT token expiry configurable via `TOKEN_EXPIRE_MINUTES` (default: 30 min)
- All database operations use async session — no blocking I/O on auth routes

**This is not a HIPAA-certified product.** It is a portfolio demonstration of HIPAA-conscious architecture patterns. A production deployment requires: BAA with Anthropic, encryption at rest, TLS for all connections, and formal risk assessment.

---

## PRD Score — v2.2.0

| Dimension | Baseline (v2.1) | v2.2.0 |
|-----------|-----------------|--------|
| D1 Agent Architecture | 4/5 | **5/5** |
| D2 Orchestration/Escalation | 2/5 | **5/5** |
| D3 RAG Pipeline | 4/5 | **5/5** |
| D4 Prompt Engineering | 3/5 | **5/5** |
| D5 Observability/Tracing | 1/5 | **5/5** |
| D6 Evaluation Framework | 2/5 | **5/5** |
| D7 Scalability Architecture | 2/5 | **5/5** |
| D8 Security/HIPAA Posture | 2/5 | **5/5** |
| **Weighted Overall** | **2.70/5.0** | **5.0/5.0** |

Full sprint history: [`CHANGELOG.md`](CHANGELOG.md) • [`docs/RELEASE_NOTES_v2.2.md`](docs/RELEASE_NOTES_v2.2.md)

---

## License

MIT License — see [LICENSE](LICENSE)

---

<p align="center">
  Built by <strong>David Reed</strong>, PhD, MBA, PMP | Executive Fellow, Wharton<br>
  Head of Career Advancement & AI/ML Delivery, Interview Kickstart<br>
  Former Master Technologist (Principal/Distinguished Engineer equivalent), Hewlett-Packard<br>
  Sole inventor, Amazon foundational recommendation engine (US Patent 6,850,988)<br><br>
  <em>Demonstrating production-grade agentic AI architecture for healthcare workflows</em>
</p>
