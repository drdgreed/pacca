# PACCA — Claude Code Operating Rules
Healthcare prior-authorization multi-agent platform. PHI flows through this system.
Treat every change as HIPAA-relevant.

## Engineering principles
KISS, YAGNI, DRY. Minimal code. Empirically verify before claiming done — run it, don't assert it.

## Workflow
- Plan first for any change touching >2 files, an agent's logic, a schema/migration, or any PHI handling. Write the plan, wait for approval, then code.
- Run the full suite before declaring a task done: `make test`   # <-- replace in Step 5
  Never claim tests pass without running them. Baseline is 140 passing.
- Commits run the hooks in .pre-commit-config.yaml. Do not bypass with --no-verify.

## HIPAA / safety rules (non-negotiable)
- Never log PHI: no patient names, SSN/MRN/DOB, addresses, or full request/response payloads in logs, exceptions, or print statements.
- Never put real PHI in fixtures, seeds, or committed files. Synthetic data only.
- Every new endpoint needs auth + input validation before it counts as done.
- Secrets come from env only. Never hardcode keys; never commit a .env file.

## Delegate to subagents (.claude/agents/)
- reviewer → run after any code change and before every commit. Read-only HIPAA + security review.
Use parallel subagents only for genuinely independent workstreams.

## Project facts that rarely change
- Stack: FastAPI, Claude API, ChromaDB, RAG. Multi-agent.
- .env: NO inline comments — they break Pydantic settings parsing.
- CORS_ORIGINS must be a JSON array (e.g. ["https://app.example.com"]), not a comma string.
- Requirements trace to PRD + SDD REQ-IDs (IEEE 29148). Reference REQ-IDs where relevant.
