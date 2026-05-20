# Contributing to PACCA

Thank you for your interest in contributing. This document covers local setup, branching, and the pull-request workflow.

## Local setup

```bash
git clone https://github.com/drdgreed/pacca.git
cd pacca

# Python environment
python -m venv venv
source venv/bin/activate                   # Windows: venv\Scripts\activate
pip install -e ".[dev]"

# Frontend
cd frontend && npm install && cd ..

# Pre-commit hooks (lint, format, basic checks)
pre-commit install

# Initialize the database
python -c "import asyncio; from pacca.db import init_database; asyncio.run(init_database())"
```

Set `ANTHROPIC_API_KEY` and any other required values in `.env` (copy `.env.example`).

## Running the system

```bash
# Backend
uvicorn pacca.api.main:app --reload

# Frontend (separate terminal)
cd frontend && npm run dev

# Or everything via Docker
docker compose up -d
```

## Tests

```bash
# Unit suite (CI-gated; 120 tests, ~7 seconds)
pytest tests/unit

# Integration + clinical-accuracy tiers (146 tests total across all tiers)
pytest tests/integration tests/clinical

# Everything
pytest

# Coverage report
pytest tests/unit --cov=pacca --cov-report=term-missing

# Manifest schema validation (run before committing any harness change)
python -m pacca.harness.validate_manifest harness/manifests/iter-N.json
```

A change must keep the unit and integration suites green. The clinical-accuracy tier (LLM-as-judge) is run on PRs that touch agent prompts, the orchestrator, or the RAG pipeline.

## Two paths: standard vs. behavioral PRs

Every PR in PACCA falls into one of two paths. The PR template enforces the choice — never ambiguous.

### Standard PRs

Refactors, documentation, infrastructure, build changes, dependency bumps, test additions that do not change agent behavior. Standard workflow:

1. Branch from `main` with a descriptive prefix (see Branching below).
2. Use conventional commit prefixes (`feat:`, `fix:`, `docs:`, `refactor:`, `test:`, `chore:`).
3. Run `ruff check src/ tests/`, `ruff format --check src/ tests/`, and `pytest tests/unit` before pushing.
4. Open a PR; tick the **Standard PR** box in the template.
5. CI runs lint, format, type-check, unit tests, Docker build, and a security scan.

### Behavioral PRs (harness-engineering discipline)

Any change that modifies how an agent reasons, what tools it can call, what middleware fires, or what memory context it sees. These follow the harness engineering discipline introduced in v2.3:

1. **Read [`docs/HARNESS.md`](docs/HARNESS.md)** to identify the correct constraint level (system_prompt, tool_description, tool_implementation, long_term_memory, middleware, orchestrator, eval_suite).
2. **Make the change as a one-file diff** (or multiple commits, one per file, if multiple components are touched).
3. **Use the `chg-N:` commit prefix.**
4. **Add a manifest entry** at `harness/manifests/iter-N.json` per the [schema](harness/manifests/change_manifest.schema.json). The manifest records: predicted impact, root cause, evidence, rollback plan, and the PACCA-specific `phi_impact` / `audit_relevant` fields.
5. **Open a PR** with the **Behavioral PR** box ticked. Fill in the manifest section.
6. CI validates the manifest schema in addition to the standard checks.
7. **After merge**, the next evaluation round produces a verdict in [`docs/DECISIONS.md`](docs/DECISIONS.md) — ratified or reverted at file granularity per the predicted-vs-observed contract you wrote in the manifest.

The goal of the discipline is *attribution*: when a behavioral metric moves, the manifest log makes it possible to identify which one-file change moved it, instead of bisecting against a wall of mixed commits.

## Branching

- Branch from `main`.
- Use a descriptive prefix: `feat/`, `fix/`, `docs/`, `refactor/`, `test/`, `chore/`.
- Example: `feat/streaming-decisions`, `fix/auth-token-expiry`.

## Commits

- Imperative mood, present tense: "Add streaming decision endpoint" not "Added".
- One logical change per commit when feasible.
- Reference issues with `Refs #123` or `Closes #123`.

## Pull requests

Before opening a PR:

1. Rebase on the latest `main`.
2. Run `pre-commit run --all-files`.
3. Run `pytest`.
4. Confirm the README and any relevant docs are updated.

Then open the PR using the template. The reviewer is looking for: a clear *what* and *why*, evidence the change was tested, and a brief note on any user-visible behavior change.

## Code style

- **Python:** Black + Ruff, configured in `pyproject.toml`. Type hints on all public functions.
- **TypeScript / React:** Prettier + ESLint, configured under `frontend/`. Functional components with hooks; no class components.
- **Naming:** module names in `snake_case`, classes in `PascalCase`, constants `UPPER_SNAKE_CASE`.
- **Tests:** every public function in `src/pacca/agents/` and `src/pacca/rag/` has at least one unit test.

## Reporting issues

Use the issue templates under `.github/ISSUE_TEMPLATE/`. For security issues, please follow [SECURITY.md](SECURITY.md) instead — do not open a public issue.

## Code of Conduct

By contributing, you agree to abide by the [Code of Conduct](CODE_OF_CONDUCT.md).
