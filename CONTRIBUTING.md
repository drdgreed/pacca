# Contributing to PACCA

Thank you for your interest in contributing. This document covers local setup, branching, and the pull-request workflow.

## Local setup

```bash
git clone https://github.com/Chaos-6/pacca.git
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
# Unit + integration
pytest

# Coverage report
pytest --cov=pacca --cov-report=html

# LLM evaluation suite (uses Claude API, costs a few cents per run)
pytest tests/eval -v
```

A change must keep the unit and integration suites green. The eval suite is run on PRs that touch agent prompts, the orchestrator, or the RAG pipeline.

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
