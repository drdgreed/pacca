# Changelog

All notable changes to PACCA are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Planned
- FHIR R4 integration for inbound clinical data.
- Streaming decisions with progressive rationale rendering in the frontend.
- Expanded LLM evaluation suite covering specialty-specific edge cases.
- Pluggable LLM backend (currently Claude-only).

## [1.0.0] — 2026-05-07

### Added
- Multi-agent orchestration with Frontline Nurse Agent and Medical Director Agent.
- ChromaDB dual-collection RAG: official clinical guidelines + case-precedent store learned from human overrides.
- JWT-authenticated REST API (FastAPI) with bcrypt password hashing.
- React 18 + Vite + Tailwind provider dashboard.
- DeepEval-based LLM evaluation suite covering hallucination, bias, evidence-grounding, and confidence calibration.
- Three pre-configured demo scenarios (routine imaging, oncology immunotherapy, incomplete documentation).
- Docker Compose orchestration for local development.
- Alembic database migrations.
- GitHub Actions CI workflow.
- Comprehensive README, contribution guidelines, security policy, and code of conduct.

### Notes
This is a portfolio and evaluation release. The system is **not** HIPAA-certified and ships with synthetic patient data only. See [Roadmap & Limitations](README.md#roadmap--limitations) in the README.

[Unreleased]: https://github.com/Chaos-6/pacca/compare/v1.0.0...HEAD
[1.0.0]: https://github.com/Chaos-6/pacca/releases/tag/v1.0.0
