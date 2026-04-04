# =============================================================================
# PACCA Makefile — developer convenience commands
#
# Usage:
#   make install      Install package + dev dependencies into current environment
#   make test         Run the fast unit test suite (no API calls, ~10 seconds)
#   make test-cov     Run unit tests with HTML coverage report
#   make test-all     Run everything except clinical (requires API key)
#   make test-clinical Run LLM-as-judge clinical evaluation (requires API key)
#   make lint         Run ruff linter
#   make typecheck    Run mypy type checker
#   make clean        Remove build artifacts and __pycache__
#
# First-time setup:
#   python -m venv venv
#   source venv/bin/activate     (Mac/Linux)
#   venv\Scripts\activate        (Windows)
#   make install
# =============================================================================

.PHONY: install test test-cov test-all test-clinical lint typecheck clean help

# ── Installation ──────────────────────────────────────────────────────────────

install:
	pip install -e ".[dev]"
	@echo "Verifying critical packages..."
	pip install uuid7 pytest-asyncio pytest-cov --quiet
	@echo "Install complete. Run 'make test' to verify."

# ── Testing ───────────────────────────────────────────────────────────────────

test:
	@echo "Running fast unit tests (no API calls)..."
	pytest tests/unit/ tests/clinical/test_clinical_accuracy.py -m "not clinical" -v

test-cov:
	@echo "Running unit tests with coverage report..."
	pytest tests/unit/ -m "not clinical" \
		--cov=pacca \
		--cov-report=html:htmlcov \
		--cov-report=term-missing \
		--cov-fail-under=80
	@echo "Coverage report: htmlcov/index.html"

test-all:
	@echo "Running all fast tests (unit + dataset integrity)..."
	pytest tests/ -m "not clinical" -v

test-clinical:
	@echo "Running full clinical evaluation (requires ANTHROPIC_API_KEY, ~3-5 minutes)..."
	@if [ -z "$$ANTHROPIC_API_KEY" ]; then \
		echo "ERROR: ANTHROPIC_API_KEY is not set. Export it before running clinical tests."; \
		exit 1; \
	fi
	pytest tests/clinical/ -m clinical -v

# ── Code quality ──────────────────────────────────────────────────────────────

lint:
	ruff check src/ tests/

typecheck:
	mypy src/pacca/

format:
	ruff format src/ tests/

# ── Utilities ─────────────────────────────────────────────────────────────────

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "htmlcov" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	@echo "Cleaned."

help:
	@echo "Available commands:"
	@echo "  make install        Install package + dev dependencies"
	@echo "  make test           Fast unit tests (no API calls)"
	@echo "  make test-cov       Unit tests + HTML coverage report"
	@echo "  make test-all       All fast tests"
	@echo "  make test-clinical  Clinical LLM evaluation (needs API key)"
	@echo "  make lint           Ruff linter"
	@echo "  make typecheck      Mypy type checker"
	@echo "  make clean          Remove build artifacts"
