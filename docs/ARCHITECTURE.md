# PACCA Architecture

## System Overview

PACCA (Prior Authorization & Care Coordination Agent Platform) is a multi-agent AI system designed to automate healthcare prior authorization workflows while maintaining human oversight for complex cases.

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                                 PACCA Platform                                   │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                 │
│  ┌─────────────────────────────────────────────────────────────────────────┐   │
│  │                          React Frontend (SPA)                            │   │
│  │  ┌──────────┐  ┌──────────────┐  ┌────────────┐  ┌────────────────┐    │   │
│  │  │Dashboard │  │Authorization │  │   Detail   │  │  New Request   │    │   │
│  │  │          │  │    List      │  │    View    │  │     Form       │    │   │
│  │  └──────────┘  └──────────────┘  └────────────┘  └────────────────┘    │   │
│  └─────────────────────────────────────────────────────────────────────────┘   │
│                                      │                                          │
│                                      ▼                                          │
│  ┌─────────────────────────────────────────────────────────────────────────┐   │
│  │                         FastAPI Backend (REST)                           │   │
│  │  ┌──────────────────────────────────────────────────────────────────┐   │   │
│  │  │  /api/v1/authorizations  │  /api/v1/metrics  │  /health         │   │   │
│  │  └──────────────────────────────────────────────────────────────────┘   │   │
│  └─────────────────────────────────────────────────────────────────────────┘   │
│                                      │                                          │
│                                      ▼                                          │
│  ┌─────────────────────────────────────────────────────────────────────────┐   │
│  │                     Agent Orchestration Layer                            │   │
│  │                                                                          │   │
│  │  ┌──────────────┐   ┌──────────────┐   ┌──────────────┐                │   │
│  │  │   Evidence   │   │  Clinical    │   │   Decision   │                │   │
│  │  │ Aggregation  │──▶│Classification│──▶│   Support    │                │   │
│  │  │    Agent     │   │    Agent     │   │    Agent     │                │   │
│  │  └──────────────┘   └──────────────┘   └──────────────┘                │   │
│  │         │                  │                  │                         │   │
│  │         └──────────────────┼──────────────────┘                         │   │
│  │                            ▼                                            │   │
│  │               ┌────────────────────────┐                                │   │
│  │               │    Orchestration       │                                │   │
│  │               │        Agent           │                                │   │
│  │               │  (Workflow Manager)    │                                │   │
│  │               └────────────────────────┘                                │   │
│  │                            │                                            │   │
│  └────────────────────────────┼────────────────────────────────────────────┘   │
│                               │                                                 │
│  ┌────────────────────────────┼────────────────────────────────────────────┐   │
│  │                      Data Layer                                          │   │
│  │                            │                                             │   │
│  │  ┌──────────┐  ┌──────────┴───────┐  ┌──────────┐  ┌──────────────┐   │   │
│  │  │PostgreSQL│  │    ChromaDB      │  │  Redis   │  │  Claude API  │   │   │
│  │  │          │  │  (Vector Store)  │  │ (Cache)  │  │  (Anthropic) │   │   │
│  │  │Requests  │  │   Guidelines     │  │          │  │              │   │   │
│  │  │Decisions │  │                  │  │Sessions  │  │    LLM       │   │   │
│  │  │Audit Logs│  │   RAG Search     │  │Rate Limit│  │  Reasoning   │   │   │
│  │  └──────────┘  └──────────────────┘  └──────────┘  └──────────────┘   │   │
│  └───────────────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────────────┘
```

## Component Details

### Frontend (React + TypeScript)

- **Technology**: React 18, TypeScript, Tailwind CSS, Vite
- **Components**:
  - Dashboard with real-time metrics
  - Authorization list with filtering/search
  - Detail view with AI explanation
  - Human review interface
  - New request submission form

### Backend (FastAPI)

- **Technology**: Python 3.12, FastAPI, Pydantic v2
- **Endpoints**:
  - `POST /api/v1/authorizations` - Submit new request
  - `GET /api/v1/authorizations` - List with pagination
  - `GET /api/v1/authorizations/{id}` - Get status
  - `GET /api/v1/authorizations/{id}/explain` - Get decision rationale
  - `POST /api/v1/authorizations/{id}/review` - Submit human review
  - `GET /api/v1/metrics` - System metrics
  - `GET /health` - Health check

### Agent Framework

#### Base Agent
- Abstract class with LLM integration
- Structured output parsing
- Retry logic with exponential backoff
- Confidence scoring
- Error handling

#### Evidence Aggregation Agent
- Gathers clinical data from sources
- Synthesizes clinical narrative
- Identifies missing evidence
- Assesses evidence quality

#### Clinical Classification Agent
- Complexity scoring (1-5 scale)
- Specialty routing
- Urgency assessment
- Escalation triggers

#### Decision Support Agent
- Guideline retrieval via RAG
- Medical necessity evaluation
- Recommendation generation
- Chain-of-thought rationale

#### Orchestration Agent
- Workflow state machine
- Agent coordination
- Escalation logic
- Human-in-the-loop gates

### Data Layer

#### PostgreSQL
- Authorization requests
- Decisions with rationale
- Human reviews
- Complete audit trail
- Guideline metadata

#### ChromaDB (Vector Store)
- Clinical guideline content
- Semantic search
- RAG retrieval

#### Redis (Optional)
- Session management
- Rate limiting
- Caching

## Data Flow

### Authorization Submission Flow

```
1. User submits authorization request via Frontend
   │
2. FastAPI validates input with Pydantic
   │
3. OrchestrationAgent.process_authorization() called
   │
4. Evidence Aggregation Agent
   │  ├─ Gathers clinical data
   │  ├─ Calls Claude API for synthesis
   │  └─ Returns ClinicalEvidence + ClinicalNarrative
   │
5. Clinical Classification Agent
   │  ├─ Receives evidence context
   │  ├─ Calls Claude API for classification
   │  └─ Returns ComplexityLevel, Specialty, Urgency
   │
6. Decision Support Agent
   │  ├─ Retrieves guidelines via RAG (ChromaDB)
   │  ├─ Calls Claude API for recommendation
   │  └─ Returns DecisionOutput with rationale
   │
7. Orchestration Agent evaluates escalation
   │  ├─ Checks confidence thresholds
   │  ├─ Checks complexity thresholds
   │  ├─ Checks high-cost flags
   │  └─ Determines: autonomous vs escalated
   │
8. Decision persisted to database
   │
9. Response returned to user
```

### Human Review Flow

```
1. Case marked as "pending_review"
   │
2. Reviewer sees case in dashboard
   │
3. Reviewer examines:
   │  ├─ Clinical summary
   │  ├─ AI recommendation
   │  ├─ Escalation reasons
   │  └─ Chain-of-thought explanation
   │
4. Reviewer submits decision
   │
5. Decision updated in database
   │
6. Audit log created
```

## Workflow State Machine

```
                    ┌─────────────┐
                    │  SUBMITTED  │
                    └──────┬──────┘
                           │
                    ┌──────▼──────┐
                    │  EVIDENCE   │
                    │  GATHERING  │
                    └──────┬──────┘
                           │
                    ┌──────▼──────┐
                    │ CLASSIFYING │
                    └──────┬──────┘
                           │
                    ┌──────▼──────┐
                    │ EVALUATING  │
                    └──────┬──────┘
                           │
              ┌────────────┴────────────┐
              │                         │
       ┌──────▼──────┐          ┌──────▼──────┐
       │  COMPLETED  │          │   PENDING   │
       │ (Autonomous)│          │   REVIEW    │
       └──────┬──────┘          └──────┬──────┘
              │                        │
    ┌─────────┼─────────┐       ┌──────▼──────┐
    │         │         │       │  IN_REVIEW  │
┌───▼───┐ ┌───▼───┐ ┌───▼───┐   └──────┬──────┘
│APPROVED│ │DENIED │ │ WITH  │          │
│        │ │       │ │ CONDS │   ┌──────▼──────┐
└────────┘ └───────┘ └───────┘   │  COMPLETED  │
                                 │  (Reviewed) │
                                 └─────────────┘
```

## Security Considerations

### Data Protection
- PHI minimization (no SSN, limited demographics)
- Audit logging for all access
- Role-based access control (RBAC)
- Encryption at rest and in transit

### AI Safety
- Confidence thresholds for autonomous decisions
- Mandatory human review for denials
- Escalation for high-risk cases
- Chain-of-thought explanations for transparency

### Compliance
- HIPAA-ready architecture
- Complete audit trail
- Decision explainability
- Human oversight mechanisms

## Scalability

### Horizontal Scaling
- Stateless API servers (scale behind load balancer)
- Database connection pooling
- Redis for distributed caching
- Async processing throughout

### Performance Targets
- API response: < 200ms (excluding LLM calls)
- End-to-end authorization: < 30s
- Throughput: 100+ authorizations/minute

## Deployment Options

### Development
```bash
# Start all services
docker-compose up -d

# Run API only (with SQLite)
uvicorn pacca.api.main:app --reload
```

### Production
- Kubernetes deployment
- Managed PostgreSQL (RDS, Cloud SQL)
- Managed Redis (ElastiCache, Cloud Memorystore)
- CI/CD via GitHub Actions
