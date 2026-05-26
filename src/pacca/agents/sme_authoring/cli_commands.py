"""
Click commands for the `pacca sme-author` subgroup.

PR-2 ships the `new` (interactive new-case workflow) and `validate`
(validator-only mode) subcommands. PR-3 adds `batch`, `status`,
`list-batches`, `list-gaps`. PR-4 adds documentation + the live smoke.

DESIGN
======

- The CLI is the COMPOSER: it calls the agent (PR-2), then the
  validators (PR-1), then the file_router (PR-1), then the writers
  (PR-1), then the test_runner (PR-2). On any failure, it rolls back
  and surfaces the failure to the SME.

- The CLI is INTERACTIVE: it uses click.prompt() and click.confirm()
  to walk the SME through field-by-field review of the LLM draft.
  Non-interactive use (CI, scripts) is supported via the `validate`
  subcommand and via the `--non-interactive` flag (PR-3).

- The CLI is SAFE BY DEFAULT: writes go to a sandbox (sandbox/cases/)
  unless `--commit` is explicitly passed. The PR-3 batch + worktree
  modes layer additional isolation.

PR-2 LIMITATIONS (acknowledged)
================================

- Sandbox mode flag (--sandbox / --commit) is plumbed but full
  sandbox/promotion implementation is PR-3.
- Resume mode is plumbed via session storage (PR-2's session.py) but
  the `resume` subcommand is PR-3.
- The CLI writes to the REAL case files when `--commit` is passed.
  Without `--commit`, the CLI runs through validation + drafting + draft
  display but does NOT write to disk. This safe-by-default behavior
  prevents accidental writes during exploration.
"""

from __future__ import annotations

import asyncio
import json
from datetime import UTC, datetime
from pathlib import Path

import click
import uuid_extensions

from pacca.agents.sme_authoring.agent import SMECaseAuthoringAgent
from pacca.agents.sme_authoring.case_writer import (
    CaseAlreadyExists,
    FileSyntaxError,
    append_case_to_file,
    create_new_case_file,
)
from pacca.agents.sme_authoring.coverage_updater import (
    CoverageBump,
    CoverageUpdaterError,
    bump_coverage_for_case,
)
from pacca.agents.sme_authoring.file_router import route_case
from pacca.agents.sme_authoring.id_allocator import (
    DEFAULT_CASE_DIR,
    next_id,
    release_reservation,
)
from pacca.agents.sme_authoring.models import (
    CaseDraftRequest,
    CaseDraftResponse,
    SessionState,
    SMEScenario,
    ValidationOutcome,
    ValidationReport,
)
from pacca.agents.sme_authoring.pr_template import (
    PRMetadata,
    render_pr_body,
    render_pr_title,
)
from pacca.agents.sme_authoring.provenance_writer import (
    ProvenanceRow,
    ProvenanceWriterError,
    append_provenance_row,
)
from pacca.agents.sme_authoring.session import save_session
from pacca.agents.sme_authoring.test_runner import run_integrity_tests
from pacca.agents.sme_authoring.validators import run_all_validators


@click.group(name="sme-author")
def sme_author() -> None:
    """SME Case Authoring Agent — author new golden cases for PACCA."""


# =============================================================================
# `pacca sme-author new` — interactive new-case workflow
# =============================================================================


@sme_author.command(name="new")
@click.option(
    "--description",
    prompt="Scenario description (1-3 sentences in plain English)",
    help="The SME's plain-English clinical scenario.",
)
@click.option(
    "--specialty",
    default="",
    help="Optional intended specialty (e.g., 'cardiology', 'oncology').",
)
@click.option(
    "--outcome",
    type=click.Choice(
        [
            "AUTO_APPROVED",
            "IN_REVIEW",
            "DENIED",
            "PRE_FLIGHT_ESCALATE",
            "INFORMATION_NEEDED",
        ],
        case_sensitive=False,
    ),
    default="",
    help="Optional intended expected_outcome hint.",
)
@click.option(
    "--failure-mode",
    default="",
    help="Optional named failure mode (e.g., 'Coverage', 'Memory trap').",
)
@click.option(
    "--commit/--no-commit",
    default=False,
    help=(
        "If --commit, write the new case + companion docs to disk after "
        "SME approval. If --no-commit (default), drafting + validation "
        "run but no files are mutated (safe exploration mode)."
    ),
)
@click.option(
    "--case-dir",
    type=click.Path(file_okay=False, path_type=Path),
    default=None,
    help="Override case-files directory. Defaults to tests/clinical/.",
)
def new_case(
    description: str,
    specialty: str,
    outcome: str,
    failure_mode: str,
    commit: bool,
    case_dir: Path | None,
) -> None:
    """
    Interactive workflow to author a new golden case.

    Walks the SME through:
      1. Scenario description (optional --specialty/--outcome/--failure-mode hints)
      2. LLM draft (via SMECaseAuthoringAgent)
      3. Validator report (PHI, citation, schema, outcome-branch, etc.)
      4. SME attestation prompt
      5. (if --commit) file write + companion-doc updates + integrity tests
      6. PR-template preview
    """
    case_dir = case_dir or DEFAULT_CASE_DIR
    _print_mode_banner(commit)

    # Step 1: build the scenario
    scenario = SMEScenario(
        description=description,
        intended_specialty=specialty or None,
        intended_outcome=outcome.upper() if outcome else None,  # type: ignore[arg-type]
        failure_mode_label=failure_mode or None,
    )

    # Step 2: allocate ID (held in reservation until commit or release)
    allocated_id = next_id(case_dir)
    click.echo(f"\nAllocated case ID: {allocated_id}")

    # Step 3: route to the recommended file
    # We need a placeholder case to call route_case; for now we route
    # primarily off the scenario hints (the case object is mostly unused
    # at this stage since the LLM hasn't drafted yet). We'll re-route
    # after the draft if needed.
    placeholder_case = _placeholder_for_routing(allocated_id, scenario)
    routing = route_case(placeholder_case, scenario, case_dir=case_dir)
    click.echo(f"Routed to: {routing.target_file} ({routing.reason})")

    # Step 4: draft via LLM
    click.echo("\nDrafting case via Claude... (this may take 5-15 seconds)")
    try:
        draft = asyncio.run(_draft_case(scenario, allocated_id, routing.target_file))
    except Exception as exc:
        click.secho(f"\nLLM drafting failed: {exc}", fg="red", err=True)
        release_reservation(allocated_id, case_dir)
        raise click.ClickException("Aborting; reservation released.") from exc

    # Step 5: validate
    click.echo("\nValidating draft...")
    reports = run_all_validators(draft)
    _print_validator_report(reports)
    blocking = [r for r in reports if r.is_blocking]
    if blocking:
        click.secho(
            f"\n{len(blocking)} blocking failure(s). Aborting.",
            fg="red",
            err=True,
        )
        release_reservation(allocated_id, case_dir)
        raise click.ClickException("Aborting; reservation released.")

    # Step 6: preview the draft
    _print_draft_preview(draft)

    # Step 7: SME attestation
    attestation = _prompt_attestation()
    if not attestation:
        click.secho("\nNo attestation provided. Aborting.", fg="yellow")
        release_reservation(allocated_id, case_dir)
        raise click.ClickException("Aborting; reservation released.")

    # Step 8 (--commit): write to disk
    if commit:
        _commit_case(draft, routing, attestation, reports, case_dir)
    else:
        click.secho(
            "\n[NO-COMMIT MODE] No files written. Re-run with --commit to actually write the case.",
            fg="yellow",
        )
        release_reservation(allocated_id, case_dir)

    # Step 9: save session (always; the agent's audit trail)
    session_state = SessionState(
        session_id=uuid_extensions.uuid7str(),
        created_at=datetime.now(UTC),
        last_updated_at=datetime.now(UTC),
        mode="production" if commit else "sandbox",
        sme_attestation=attestation,
        scenario=scenario,
        draft=draft,
        last_validation_report=reports,
        last_step="committed" if commit else "drafted_no_commit",
    )
    session_path = save_session(session_state)
    click.echo(f"\nSession saved: {session_path}")


# =============================================================================
# `pacca sme-author validate` — validator-only mode (CI-friendly)
# =============================================================================


@sme_author.command(name="validate")
@click.argument(
    "draft_path",
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
)
def validate_draft(draft_path: Path) -> None:
    """
    Validate a CaseDraftResponse JSON file against the 6 deterministic
    validators. No LLM, no file mutations. Useful for CI / scripted use.

    Exit code:
        0 — all validators PASS (WARN-only is OK)
        1 — any validator FAIL
    """
    try:
        draft = CaseDraftResponse.model_validate_json(draft_path.read_text(encoding="utf-8"))
    except Exception as exc:
        raise click.ClickException(
            f"Could not parse {draft_path} as CaseDraftResponse: {exc}"
        ) from exc

    reports = run_all_validators(draft)
    _print_validator_report(reports)
    blocking = [r for r in reports if r.is_blocking]
    if blocking:
        raise click.ClickException(f"{len(blocking)} blocking validator failure(s).")
    click.secho("All validators PASS.", fg="green")


# =============================================================================
# Helpers (private — not part of the public command surface)
# =============================================================================


def _print_mode_banner(commit: bool) -> None:
    """Print a banner showing the current mode."""
    if commit:
        click.secho(
            "\n" + "=" * 60 + "\n  COMMIT MODE — case will be written to "
            "tests/clinical/\n" + "=" * 60,
            fg="red",
            bold=True,
        )
    else:
        click.secho(
            "\n" + "=" * 60 + "\n  NO-COMMIT MODE (default) — drafting + "
            "validation only\n" + "=" * 60,
            fg="cyan",
            bold=True,
        )


def _placeholder_for_routing(allocated_id: str, scenario: SMEScenario) -> CaseDraftResponse:
    """
    Build a minimal CaseDraftResponse for routing purposes.

    The router primarily uses scenario.intended_specialty +
    case.diagnosis_code + clinical_notes (for age detection). We don't
    have those before drafting, so we use stubs; the router falls back
    to expansion_cases.py if no better signal exists. After the LLM
    drafts, the CLI can re-route if needed (PR-3 enhancement).
    """
    return CaseDraftResponse(
        case_id=allocated_id,
        title="Placeholder for routing (not the final case)",
        diagnosis_code="R69",  # Illness, unspecified — falls through to expansion
        diagnosis_description="Placeholder",
        procedure_code="00000",
        procedure_description="Placeholder",
        clinical_notes=scenario.description
        + " (Synthesized placeholder for routing; LLM will replace.)",
        guidelines_context=(
            "Placeholder for routing. Real guideline citation will be "
            "drafted by the LLM in the next step of the workflow."
        ),
        expected_outcome=scenario.intended_outcome or "AUTO_APPROVED",
        expected_branch=(
            "BRANCH_1_AUTO_APPROVE"
            if (scenario.intended_outcome or "AUTO_APPROVED") == "AUTO_APPROVED"
            else "BRANCH_3_LOW_CONFIDENCE"
        ),
        reasoning_must_include=["placeholder"],
        clinical_rationale=("Placeholder for routing. Real rationale drafted by the LLM."),
        judge_scoring_criteria=("Placeholder for routing. Real criteria drafted by the LLM."),
    )


async def _draft_case(
    scenario: SMEScenario,
    allocated_id: str,
    recommended_file: str,
) -> CaseDraftResponse:
    """Wrap the SMECaseAuthoringAgent.run() call."""
    agent = SMECaseAuthoringAgent()
    request = CaseDraftRequest(
        scenario=scenario,
        allocated_case_id=allocated_id,
        recommended_file=recommended_file,
    )
    return await agent.run(request)


def _print_validator_report(reports: list[ValidationReport]) -> None:
    """Render the 6 validator outcomes to the SME."""
    click.echo("\nValidator report:")
    for r in reports:
        if r.outcome == ValidationOutcome.PASS:
            marker, fg = "  PASS", "green"
        elif r.outcome == ValidationOutcome.WARN:
            marker, fg = "  WARN", "yellow"
        else:
            marker, fg = "  FAIL", "red"
        line = f"{marker}  {r.validator.value}"
        if r.reason:
            line += f"  ({r.reason})"
        click.secho(line, fg=fg)


def _print_draft_preview(draft: CaseDraftResponse) -> None:
    """Render the LLM draft for SME review."""
    click.echo("\n" + "=" * 60)
    click.secho("  LLM DRAFT (review carefully):", bold=True)
    click.echo("=" * 60)
    click.echo(json.dumps(draft.model_dump(), indent=2))


def _prompt_attestation() -> str:
    """
    Prompt the SME for the attestation string.

    Accepted formats:
      - "I attest this case is clinically accurate per my professional judgment"
      - "Dr. <Name>, <Degree>, board-certified <Specialty>"
    """
    response: str = click.prompt(
        "\nSME attestation (per CASE_AUTHORING_GUIDE.md § 11)",
        default="",
        show_default=False,
    )
    return response.strip()


def _commit_case(
    draft: CaseDraftResponse,
    routing: object,  # RoutingDecision
    attestation: str,
    reports: list[ValidationReport],
    case_dir: Path,
) -> None:
    """Execute the file mutations + integrity tests + PR preview."""
    target_path = case_dir / routing.target_file  # type: ignore[attr-defined]

    # Create file if it's new
    if routing.is_new_file:  # type: ignore[attr-defined]
        click.echo(f"Creating new file: {target_path}")
        create_new_case_file(routing.list_name, target_path)  # type: ignore[attr-defined]

    # Append the case
    try:
        append_case_to_file(
            draft,
            target_path,
            routing.list_name,  # type: ignore[attr-defined]
        )
    except (CaseAlreadyExists, FileSyntaxError) as exc:
        raise click.ClickException(f"Write failed: {exc}") from exc

    click.secho(f"Case written to {target_path}", fg="green")

    # Update provenance + coverage
    try:
        append_provenance_row(
            ProvenanceRow(
                case_id=draft.case_id,
                file=routing.target_file,  # type: ignore[attr-defined]
                clinical_rationale=draft.clinical_rationale,
                named_failure_mode="Coverage",  # SME can override later
                iteration="iter-7",
            )
        )
        bump_coverage_for_case(
            CoverageBump(
                list_name=routing.list_name,  # type: ignore[attr-defined]
                file_name=routing.target_file,  # type: ignore[attr-defined]
                new_case_id=draft.case_id,
            )
        )
    except (ProvenanceWriterError, CoverageUpdaterError) as exc:
        click.secho(f"Companion-doc update failed: {exc}", fg="yellow", err=True)

    # Run integrity tests
    click.echo("\nRunning integrity tests...")
    result = run_integrity_tests(Path.cwd())
    if result.passed:
        click.secho("Integrity tests PASS.", fg="green")
    else:
        click.secho(
            f"Integrity tests FAILED (exit {result.exit_code}):\n{result.summary}",
            fg="red",
            err=True,
        )

    # Render PR template
    pr_metadata = PRMetadata(
        sme_attestation=attestation,
        target_file=routing.target_file,  # type: ignore[attr-defined]
        is_new_file=routing.is_new_file,  # type: ignore[attr-defined]
        integrity_test_passed=result.passed,
        integrity_test_summary=result.summary,
    )
    click.echo("\n" + "=" * 60)
    click.secho("  PR TEMPLATE:", bold=True)
    click.echo("=" * 60)
    click.echo(f"Title: {render_pr_title(draft)}\n")
    click.echo(render_pr_body(draft, pr_metadata, reports))
