---
name: Bug report
about: Report a defect in PACCA's behavior
title: "[BUG] "
labels: bug
assignees: ''
---

## What is wrong

A clear, one-paragraph description of the actual behavior and the expected behavior.

## Reproduction

Minimum steps to reproduce. If the bug is in the agent layer, include the case JSON or prompt. If it is in the API or frontend, include the request/response or browser action.

```
1. ...
2. ...
3. ...
```

## Component

Which part of the system is affected (check all that apply):

- [ ] Agent reasoning (Frontline / Medical Director / Evidence / Classification / Policy Evolution)
- [ ] Orchestrator / 7-branch escalation tree
- [ ] RAG (ChromaDB collections, retrieval ranking)
- [ ] FastAPI backend / authentication
- [ ] React frontend / dashboard
- [ ] Observability (OpenTelemetry / Langfuse / trajectory logs)
- [ ] Harness manifest validation / CI
- [ ] Documentation

## Environment

- PACCA version / commit SHA: `<git rev-parse --short HEAD>`
- Python version: `3.x.x`
- OS: `<macOS / Linux / Windows>`
- Running via: `<docker compose / local venv>`
- LLM model in `.env`: `<claude-sonnet-4-… / claude-haiku-4-… / etc.>`

## Logs / output

Paste relevant tail from `pacca.log`, browser console, or pytest output. Redact any synthetic-PHI fields if the case payload would otherwise be hard to read; this repo handles only synthetic data, but please make the log useful at a glance.

```
<paste here>
```

## Severity (your assessment)

- [ ] **P0** — wrong clinical decision, hallucinated guideline citation, audit-trail gap, or auth bypass
- [ ] **P1** — broken CI, broken Quick Start, or major UX regression
- [ ] **P2** — visible but workaroundable defect
- [ ] **P3** — cosmetic / docs-only

## Suspected cause (optional)

If you've already traced this, name the file/line. Otherwise leave blank.
