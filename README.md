# PACCA — Prior Authorization & Care Coordination Agent Platform

**AI-Powered Healthcare Prior Authorization Platform with Observability-Driven Harness Engineering**

[Features](#features) • [Architecture](#architecture) • [Harness Engineering](#harness-engineering) • [Quick Start](#quick-start) • [API Docs](#api-documentation) • [Demo](#demo-scenarios)

[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.109+-green.svg)](https://fastapi.tiangolo.com/)
[![React 18](https://img.shields.io/badge/React-18+-61dafb.svg)](https://react.dev/)
[![Claude API](https://img.shields.io/badge/Claude-API-blueviolet.svg)](https://anthropic.com/)
[![Harness Iter](https://img.shields.io/badge/harness--iter-0-orange.svg)](docs/ITERATIONS.md)
[![MIT License](https://img.shields.io/badge/license-MIT-lightgrey.svg)](LICENSE)

---

## Overview

PACCA is a **secure, multi-agent AI workflow** that automates healthcare prior authorization reviews. It solves one of healthcare's most expensive bottlenecks ($50–100B annually in U.S. administrative overhead) by combining the reasoning capabilities of Large Language Models with strict deterministic grading rubrics, dual-collection vector retrieval, and a HIPAA-conscious audit infrastructure.

Unlike basic "LLM-wrapper" approaches, PACCA grounds every decision in factual medical guidelines via Retrieval-Augmented Generation, escalates to specialist tiers using a 7-branch deterministic decision tree, and — beginning with v2.3 — applies **observability-driven harness engineering** to iterate the system itself.

**v2.3 introduces a methodology, not just features.** Every behavioral change to PACCA's agent harness ships as a one-file diff with a falsifiable predicted-impact contract that the next evaluation round verifies. The methodology is adapted from Lin et al., *Agentic Harness Engineering* (arXiv:2604.25850, 2026). The repository's `docs/` folder makes the discipline auditable from outside.

### The Problem

Prior authorization is one of healthcare's most measurable failures:

- **Providers** spend 34+ hours/week per practice on prior authorization workflows
- **Patients** face treatment delays averaging 2–3 days, with 29% of delays directly harming care
- **Payers** process 200+ million requests annually, mostly manually
- **Reviewers** use outdated guideline versions in 35% of cases, with decision quality varying 18–35% by individual

### The Solution

PACCA automates the workflow using a five-agent hierarchical architecture with deterministic safety controls:

1. **Evidence Aggregation** — synthesizes scattered clinical data into coherent narratives
2. **Clinical Classification** — complexity scoring, specialty routing, urgency assessment
3. **Decision Support (Tier 1)** — guideline-based recommendations with chain-of-thought reasoning
4. **Medical Director (Tier 2)** — invoked for ambiguous cases (confidence 0.90–0.95)
5. **Policy Evolution (Governance)** — proposes amendments based on human-override patterns; deploys only with Medical Director approval

**Eight production-grade safety properties:**

- JWT-authenticated provider dashboard with bcrypt password hashing
- Dual-collection ChromaDB: official guidelines vs. institutional-memory precedents
- Chain-of-thought reasoning with anti-hallucination, uncertainty-flagging, and escalation-trigger guards on every agent
- 7-branch escalation tree (4 pre-flight + 3 post-agent) — deterministic safety logic that overrides AI confidence on experimental treatments, rare conditions, conflicting guidelines, and prior denials
- Pre-write HIPAA audit trail with correlation-ID linked event pairs
- OpenTelemetry → Langfuse distributed tracing on every agent call
- Runtime-adjustable operational parameters (confidence thresholds, retry budget, autonomy switch) without server restart
- Three-stage governance pipeline for AI-proposed guideline amendments — meets FDA SaMD change-control intent

---

## Harness Engineering

> *Beginning with v2.3, PACCA is iterated using a structured, falsifiable methodology. Every behavioral change is a one-file diff with a recorded prediction. The next evaluation round verifies the prediction. Rejected changes are reverted at file granularity.*

The methodology adapts the AHE paper's three observability pillars to a healthcare domain:

| Pillar | PACCA Implementation |
|--------|----------------------|
| **Component observability** | 11 editable harness surfaces (7 NexAU-standard + 4 PACCA-specific), each at a fixed file path with one-file-diff rollback |
| **Experience observability** | OpenTelemetry spans → Langfuse + structured trajectory logs alongside the HIPAA audit trail |
| **Decision observability** | Every change ships with a [`change_manifest`](harness/manifests/change_manifest.schema.json) entry; verdicts logged in [`DECISIONS.md`](docs/DECISIONS.md) |

### The Four Harness Engineering Documents

| Document | Purpose |
|----------|---------|
| 📐 **[`docs/HARNESS.md`](docs/HARNESS.md)** | Architectural reference. The seven AHE component types plus PACCA's four healthcare-specific harness surfaces, with rules for editing each. |
| 📋 **[`docs/DECISIONS.md`](docs/DECISIONS.md)** | Append-only log of every behavioral change with predictions and verified outcomes. The audit trail of the iteration cycle itself. |
| 📖 **[`docs/ITERATIONS.md`](docs/ITERATIONS.md)** | Narrative log per iteration tag. Format borrowed from the AHE paper's Appendix C — failure pattern → change → trajectory before/after → eval delta. |
| 🔒 **[`harness/manifests/change_manifest.schema.json`](harness/manifests/change_manifest.schema.json)** | JSON Schema 2020-12 specification for change manifests. Includes PACCA-specific fields (`phi_impact`, `audit_relevant`) tying the discipline to healthcare governance requirements. |

### v2.3 Cycle Phases

The v2.3 release commits PACCA to a six-phase cycle over 10–12 weeks. Each phase has explicit exit criteria verifiable from git history and the evaluation suite:

| Phase | Name | Weeks | Constraint Levels |
|-------|------|-------|-------------------|
| **H0** | Baseline Crystallization | 1–2 | Instrumentation only |
| **H1** | Component Decoupling | 3–4 | system_prompt, tool_description, tool_implementation |
| **H2** | Institutional Memory Layer | 5–6 | long_term_memory |
| **H3** | Cross-Step Middleware Tier | 7–8 | middleware |
| **H4** | Change Manifest Discipline | 3–10 (parallel) | Process layer |
| **H5** | Evaluation Harness Expansion | 10–12 | Eval infrastructure |

Full phase specifications, exit criteria, expected impact, and AHE paper citations are in **[the consolidated PRD §15](docs/PACCA_PRD_v2.3_Consolidated.md)**.

---

## Features

### 🤖 Multi-Agent AI System

- **Evidence Aggregation Agent**: synthesizes clinical data into coherent narratives
- **Classification Agent**: complexity scoring, specialty routing, urgency assessment
- **Decision Support Agent (Tier 1, "Frontline UM Nurse")**: evaluates clear-cut cases, auto-approves at confidence ≥ 0.95
- **Medical Director Agent (Tier 2, "Chief Medical Director")**: clinical nuance and gray areas before human routing
- **Policy Evolution Agent (Governance)**: proposes guideline amendments based on human-override patterns

### 📋 Clinical Decision Support

- RAG-powered guideline retrieval using ChromaDB dual-collection
- Evidence-based recommendations with confidence scores
- Transparent decision rationale, audit-logged
- Step therapy and prior treatment requirement support

### 👥 Human Oversight

- Configurable confidence thresholds for autonomous decisions
- 7-branch escalation tree with 4 pre-flight deterministic checks (experimental treatment, rare condition, conflicting guidelines, prior denial)
- Medical Director review interface with AI-generated case summaries
- Complete audit trail for regulatory compliance

### 📚 RAG and Institutional Memory

- **`nccn_guidelines`** — authoritative clinical guidelines (NCCN, CMS, AHA, ADA, ACR), quarterly updates, independent versioning and rollback
- **`case_precedents`** — Medical Director override decisions with documented rationales, embedded immediately, surfaced in semantically similar future cases
- v2.3+ adds per-agent `long_term_memory.md` files: human-readable, git-versioned cross-cutting clinical lessons that ride in the prompt context on every request (Phase H2)

### 🛡️ Production-Grade Safety

- **Anti-hallucination guards** on every agent ("only reference clinical evidence explicitly present in the submission")
- **Hallucination zero-tolerance tests** (GC-018, GC-019) — sparse-notes traps that fail the build on any score-1 hallucination
- **Tool-use API forced** for structured output — eliminates the most common agentic failure mode
- **Pre-write audit trail** — correlation-ID-linked event pairs flushed before any state change
- **JWT + bcrypt + fail-fast SECRET_KEY validation** — server refuses to start with weak or missing keys
- **Append-only PolicyChangeLogEntry** — immutable record of every guideline amendment, mapped to FDA SaMD Action Plan change-control requirements

### 🔧 Production-Ready Architecture

- FastAPI backend with full async support
- React 18 frontend with real-time updates
- PostgreSQL 16 for persistence, SQLite for development (one env-var switch)
- Dual-collection ChromaDB with metadata filtering
- OpenTelemetry → Langfuse distributed tracing (Docker Compose included)
- Comprehensive test coverage: 140 unit tests, 0 failures, ~8 seconds

---

## Architecture

```mermaid
graph TD
    classDef frontend fill:#61dafb,stroke:#333,stroke-width:2px,color:#000
    classDef backend fill:#009688,stroke:#333,stroke-width:2px,color:#fff
    classDef auth fill:#e91e63,stroke:#333,stroke-width:2px,color:#fff
    classDef agent fill:#ff9800,stroke:#333,stroke-width:2px,color:#fff
    classDef database fill:#607d8b,stroke:#333,stroke-width:2px,color:#fff

    React[React Frontend SPA]:::frontend
    Auth[JWT Auth Bouncer]:::auth
    API[FastAPI Backend]:::backend

    SQL[(PostgreSQL 16<br/>User Credentials & Audit)]:::database
    Chroma[(ChromaDB Dual-Collection<br/>nccn_guidelines + case_precedents)]:::database

    Orchestrator{Multi-Agent<br/>Orchestrator + 7-Branch<br/>Escalation Tree}:::agent
    Agent1[Tier 1: Frontline Nurse Agent]:::agent
    Agent2[Tier 2: Medical Director Agent]:::agent
    LLM((Claude API<br/>Sonnet 4)):::database

    React -- "POST /login" --> Auth
    Auth -- "Verify/Hash" --> SQL
    Auth -- "Returns JWT" --> React

    React -- "Submit Case + JWT" --> API
    API -- "Pre-flight checks" --> Orchestrator
    Orchestrator -- "Semantic Search" --> Chroma
    Chroma -- "Guidelines + Precedents" --> Orchestrator

    Orchestrator -- "Tier 1 Review" --> Agent1
    Agent1 -- "Evaluate" --> LLM
    Agent1 -- "Confidence 0.90-0.95" --> Orchestrator
    Orchestrator -- "Tier 2 Escalation" --> Agent2
    Agent2 -- "Evaluate Nuance" --> LLM

    Agent1 -. "Auto-Approve (>=0.95)" .-> API
    Agent2 -. "Approve / In Review" .-> API
    API -- "JSON Decision + Audit Trail" --> React
```

For the complete architecture, see [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md). For the harness layer specifically, see [`docs/HARNESS.md`](docs/HARNESS.md).

---

## Quick Start

### Prerequisites

- Python 3.12+
- Node.js 18+ (for frontend)
- Docker & Docker Compose (recommended)
- Anthropic API key

### Option 1: Docker (Recommended)

```bash
# Clone the repository
git clone https://github.com/Chaos-6/pacca.git
cd pacca

# Set up environment
cp .env.example .env
# Edit .env and add your ANTHROPIC_API_KEY

# Start all services (FastAPI, frontend, ChromaDB, PostgreSQL, Langfuse)
docker-compose up -d

# Access the application
# Frontend:    http://localhost:3000
# API:         http://localhost:8000
# API Docs:    http://localhost:8000/docs
# Langfuse:    http://localhost:3001
```

### Option 2: Local Development

```bash
# Clone and set up
git clone https://github.com/Chaos-6/pacca.git
cd pacca

# Create virtual environment
python -m venv venv
source venv/bin/activate  # or `venv\Scripts\activate` on Windows

# Install dependencies
pip install -e ".[dev]"

# Set environment variables
export ANTHROPIC_API_KEY=sk-ant-your-key-here
export DATABASE_URL=sqlite+aiosqlite:///./pacca.db
export SECRET_KEY=$(python -c 'import secrets; print(secrets.token_urlsafe(48))')

# Initialize database
python -c "import asyncio; from pacca.db import init_database; asyncio.run(init_database())"

# Start the API server
uvicorn pacca.api.main:app --reload

# In another terminal, start the frontend
cd frontend
npm install
npm run dev
```

### Running Tests

```bash
# Full unit test suite (140 tests, ~8 seconds)
pytest

# With coverage report
pytest --cov=pacca --cov-report=html

# Test categories
pytest tests/test_clinical_accuracy.py        # Clinical reasoning + LLM-as-judge
pytest tests/test_escalation_tree.py          # All 7 escalation branches
pytest tests/test_security_and_scalability.py # Auth, async, RAG

# v2.3+: harness benchmark suite (Phase H5 deliverable)
pytest tests/eval/                             # 100+ case benchmark with k=2 rollouts
```

### Validating Change Manifests (v2.3+)

```bash
# Validate a manifest against the schema before committing
python -m pacca.harness.validate_manifest harness/manifests/iter-1.json
```

---

## API Documentation

### Submit Authorization Request

```http
POST /api/v1/authorizations/
Authorization: Bearer <jwt-token>
Content-Type: application/json

{
  "patient": {
    "id": "P12345",
    "date_of_birth": "1966-05-15",
    "gender": "M"
  },
  "diagnosis": {
    "code": "C34.1",
    "description": "Malignant neoplasm of upper lobe, bronchus or lung"
  },
  "treatment": {
    "code": "J9271",
    "code_type": "HCPCS",
    "description": "Pembrolizumab injection",
    "category": "medication",
    "estimated_cost": 15000.00
  },
  "provider": {
    "provider_id": "1234567890",
    "provider_name": "Dr. Jane Smith"
  },
  "payer": {
    "payer_id": "BCBS001",
    "payer_name": "Blue Cross Blue Shield",
    "member_id": "MEM123456"
  },
  "clinical_notes": "Patient with stage IIIA NSCLC, PD-L1 TPS ≥50%...",
  "urgency": "expedited"
}
```

### Response

```json
{
  "request_id": "AUTH-01HQXYZ...",
  "status": "approved",
  "decision": "approve",
  "confidence_score": 0.92,
  "decision_summary": "Authorization approved based on NCCN guidelines...",
  "complexity": 3,
  "specialty": "oncology",
  "requires_human_review": false,
  "harness_iteration_tag": "harness-iter-0",
  "prompt_registry_versions": {
    "decision_support": "1.4.0",
    "medical_director": "1.2.0"
  }
}
```

### Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/login/` | Exchange credentials for JWT |
| POST | `/api/v1/authorizations/` | Submit authorization request |
| GET | `/api/v1/authorizations/` | List authorizations with pagination |
| GET | `/api/v1/authorizations/{id}` | Decision + full audit trail |
| GET | `/api/v1/admin/config` | Read operational configuration |
| PATCH | `/api/v1/admin/config` | Update config at runtime |
| GET | `/api/v1/admin/proposals` | Pending policy proposals |
| POST | `/api/v1/admin/proposals/{id}/approve` | Approve and deploy guideline amendment |
| GET | `/api/v1/admin/change-log` | Immutable policy change audit log |
| GET | `/api/v1/admin/harness/iterations` | v2.3+: list harness iteration tags |
| GET | `/api/v1/admin/harness/manifest/{tag}` | v2.3+: retrieve a specific iteration's manifest |
| GET | `/health` | Health check |

Full API documentation at `/docs` when running the server.

---

## Demo Scenarios

PACCA includes 53 synthesized cases across 8 groups (A–H) covering all 7 escalation branches:

| Group | Cases | Scenario |
|-------|-------|----------|
| A | 15 | Auto-approved — complete documentation, explicit guideline alignment |
| B | 10 | Human review — missing documentation, hallucination traps |
| C | 8 | MD escalation — cost > $100K or borderline confidence |
| D | 5 | Experimental treatment pre-flight — CAR-T, gene therapy |
| E | 4 | Rare condition pre-flight — Gaucher, Huntington, ALS, Wilson disease |
| F | 4 | Conflicting guidelines pre-flight — NCCN vs. CMS vs. payer LCD |
| G | 4 | Prior denial pre-flight — resubmissions, fraud patterns |
| H | 3 | Precedent-based approvals — institutional memory in action |

Plus a 20-case clinical golden dataset with LLM-as-judge scoring (Claude Haiku, 1–5 rubric) and a CI gate at ≥80% accuracy. Hallucinations score automatic 1 — there is no acceptable rate of inventing clinical data.

In v2.3 Phase H5, these case sources are unified into a single benchmark of 100+ cases with k=2 rollouts per case and pass@1 / tokens-per-case / Succ/Mtok metrics.

---

## Configuration

### Environment Variables

| Variable | Description | Default | Production |
|----------|-------------|---------|------------|
| `ANTHROPIC_API_KEY` | Claude API key | Required | Required + BAA |
| `SECRET_KEY` | JWT signing key (≥32 chars) | Required | Rotate quarterly |
| `DATABASE_URL` | Database connection | SQLite | PostgreSQL 16 |
| `TOKEN_EXPIRE_MINUTES` | JWT expiry | 30 | 15–30 |
| `AUTO_APPROVE_CONFIDENCE_THRESHOLD` | Auto-approve threshold | 0.95 | 0.95–0.98 |
| `ESCALATION_CONFIDENCE_THRESHOLD` | MD escalation threshold | 0.90 | 0.90–0.95 |
| `HIGH_COST_THRESHOLD` | Cost escalation trigger (USD) | 100000 | Per payer contract |
| `LLM_RETRY_MAX_ATTEMPTS` | Max LLM retry attempts | 3 | 3–5 |
| `ENABLE_AUTONOMOUS_DECISIONS` | Master autonomy switch | true | true (false for audit) |
| `HARNESS_ITERATION_TAG` | Active harness iteration (v2.3+) | `harness-iter-0` | Latest tagged iteration |

See [`.env.example`](.env.example) for all configuration options.

---

## Project Structure

```
pacca/
├── src/pacca/
│   ├── agents/              # Multi-agent framework
│   │   ├── decision_support/    # v2.3: per-agent component decoupling (Phase H1)
│   │   │   ├── system_prompt.md     # System prompt as standalone file
│   │   │   ├── long_term_memory.md  # v2.3: institutional memory (Phase H2)
│   │   │   ├── tool_descriptions/   # YAML schemas for tool interfaces
│   │   │   ├── tools/               # Tool implementations
│   │   │   ├── middleware/          # v2.3: cross-step hooks (Phase H3)
│   │   │   └── agent.yaml           # Component registry
│   │   ├── medical_director/    # Same layout per agent
│   │   ├── evidence_aggregation/
│   │   ├── classification/
│   │   ├── policy_evolution/
│   │   └── prompts/             # Shared PROMPT_REGISTRY
│   ├── api/                 # FastAPI application
│   ├── config/              # Settings and logging
│   ├── db/                  # Database, models, repository, migrations
│   ├── models/              # Pydantic domain models
│   ├── observability/       # v2.3: trajectory logging (Phase H0)
│   ├── orchestrator/        # 7-branch escalation tree
│   └── rag/                 # ChromaDB dual-collection pipeline
├── frontend/                # React 18 frontend
├── harness/                 # v2.3: harness engineering artifacts
│   └── manifests/               # Per-iteration change manifests + verdicts
│       ├── change_manifest.schema.json
│       ├── iter-0.json
│       └── iter-N-verdicts.json
├── tests/
│   ├── test_*.py            # 140 unit tests
│   └── eval/                # v2.3: harness benchmark (Phase H5)
├── demo/                    # 53-case synthesized demo dataset
├── docs/                    # Documentation
│   ├── ARCHITECTURE.md
│   ├── HARNESS.md           # v2.3: harness component reference
│   ├── DECISIONS.md         # v2.3: append-only change log with verdicts
│   ├── ITERATIONS.md        # v2.3: narrative log per iteration
│   ├── EVALUATION.md        # v2.3: benchmark methodology + scores
│   └── PACCA_PRD_v2.3_Consolidated.md  # Full PRD with phase specs
└── docker-compose.yml       # Full stack including Langfuse
```

---

## Technology Stack

| Layer | Technology | Notes |
|-------|------------|-------|
| **LLM** | Claude (Anthropic API), `claude-sonnet-4` | Tool-use forced for structured output |
| **Backend** | Python 3.12, FastAPI, Pydantic v2 | Fully async throughout |
| **Production DB** | PostgreSQL 16, SQLAlchemy 2.0, Alembic | JSONB compliance queries, async pool |
| **Dev DB** | SQLite (same ORM layer) | One env var to switch |
| **Vector Store** | ChromaDB 0.5+, dual-collection | Different trust levels per collection |
| **Cache** | Redis (optional) | 40–60% token reduction at scale (V2 release) |
| **Frontend** | React 18, TypeScript, Tailwind CSS | Vite build pipeline |
| **Observability** | OpenTelemetry → Langfuse 1.27+ | One span per agent call |
| **Testing** | pytest, pytest-asyncio, pytest-cov | 140 unit + benchmark suite |
| **Security** | python-jose, bcrypt | JWT + timing-safe passwords |
| **Manifest validation** | jsonschema (Draft 2020-12) | v2.3+: validates change manifests in CI |
| **CI/CD** | GitHub Actions | Includes manifest schema validation |
| **Containerization** | Docker, Docker Compose | 6 services in full stack |

---

## Documentation Map

PACCA's documentation is structured to serve four audiences: engineers, healthcare reviewers, recruiters and the agentic AI community evaluating the work, and future iterations of PACCA itself.

### Core architecture and methodology

- **[`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md)** — system architecture, component responsibilities, request lifecycle
- **[`docs/HARNESS.md`](docs/HARNESS.md)** — harness layer reference: 11 editable surfaces, three rules of engagement, three observability pillars
- **[`docs/PACCA_PRD_v2.3_Consolidated.md`](docs/PACCA_PRD_v2.3_Consolidated.md)** — full Product Requirements Document, including v2.3 harness engineering cycle phases (H0–H5)

### Iteration record (v2.3+)

- **[`docs/DECISIONS.md`](docs/DECISIONS.md)** — append-only log of every behavioral change with predictions and verdicts
- **[`docs/ITERATIONS.md`](docs/ITERATIONS.md)** — narrative log per iteration tag (paper Appendix C format)
- **[`docs/EVALUATION.md`](docs/EVALUATION.md)** — benchmark methodology, scores, regression history
- **[`CHANGELOG.md`](CHANGELOG.md)** — per-iteration changelog with eval delta and verified predictions

### Machine-readable specifications

- **[`harness/manifests/change_manifest.schema.json`](harness/manifests/change_manifest.schema.json)** — JSON Schema 2020-12 specification for change manifests
- **[`harness/manifests/iter-N.json`](harness/manifests/)** — per-iteration manifest entries
- **[`harness/manifests/iter-N-verdicts.json`](harness/manifests/)** — per-iteration verdict files (CI-generated)

---

## Contributing

Contributions are welcome. PACCA's contribution model has two paths:

### Non-behavioral changes

Refactors, documentation updates, test additions that do not change agent behavior. Standard PR workflow:

1. Fork the repository
2. Create a feature branch (`git checkout -b feat/your-feature`)
3. Commit using conventional commits (`feat:`, `fix:`, `docs:`, etc.)
4. Push and open a PR; the PR template's "non-behavioral" checkbox applies
5. CI runs the full unit test suite

### Behavioral changes (v2.3+)

Any change that modifies how an agent reasons, what tools it can call, what middleware fires, or what memory context it sees. These follow the harness engineering discipline:

1. Read [`docs/HARNESS.md`](docs/HARNESS.md) to identify the correct constraint level
2. Make the change as a one-file diff (or multiple commits, one per file, if multiple components are touched)
3. Use the `chg-N:` commit prefix
4. Add a corresponding entry to [`harness/manifests/iter-N.json`](harness/manifests/) per the [schema](harness/manifests/change_manifest.schema.json)
5. CI validates the manifest schema and runs the benchmark
6. After merge, the next evaluation round produces a verdict in [`docs/DECISIONS.md`](docs/DECISIONS.md)

The PR template enforces the choice between paths — every PR is one or the other, never ambiguous.

---

## Citation

If you reference PACCA's harness engineering implementation in academic work or production case studies, please cite:

```
Reed, D. (2026). PACCA: Prior Authorization & Care Coordination Agent Platform —
v2.3 Consolidated PRD. github.com/Chaos-6/pacca.

Methodology adapted from:
Lin, J., Liu, S., Pan, C., Lin, L., Dou, S., Huang, X., Yan, H., Han, Z., & Gui, T. (2026).
Agentic Harness Engineering: Observability-Driven Automatic Evolution of
Coding-Agent Harnesses. arXiv:2604.25850v3.
```

---

## License

MIT — see [LICENSE](LICENSE) for details.

---

## Acknowledgments

- Built with [Claude](https://anthropic.com) by Anthropic
- Methodology informed by Lin et al., *Agentic Harness Engineering* (arXiv:2604.25850, 2026)
- Clinical guidelines based on publicly available NCCN, ACR, AHA, ADA, and CMS guidance
- Inspired by real-world healthcare prior authorization challenges affecting 200+ million patients annually

---

**PACCA v2.3** — Healthcare Prior Authorization, Iterated Like Engineering
*github.com/Chaos-6/pacca | David Reed, PhD | May 2026*
