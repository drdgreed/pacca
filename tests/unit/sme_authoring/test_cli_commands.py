"""
Tests for cli_commands.py via Click's CliRunner.

Strategy:
- For `validate`: write a JSON CaseDraftResponse to tmp_path; invoke the
  command; assert exit code + output.
- For `new`: skip the live LLM test (covered by test_agent_with_mocked_llm);
  test only the safe-by-default banner + the help text.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from click.testing import CliRunner

from pacca.agents.sme_authoring.cli_commands import sme_author
from pacca.cli import pacca_cli

if TYPE_CHECKING:
    from pathlib import Path


# Sample valid CaseDraftResponse JSON used by validate tests
_VALID_DRAFT_JSON = """{
  "case_id": "GC-101",
  "title": "Test case with sufficient length to satisfy validators",
  "diagnosis_code": "C34.1",
  "diagnosis_description": "Test diagnosis description text",
  "procedure_code": "J9271",
  "procedure_description": "Test procedure description text",
  "clinical_notes": "58-year-old male with stage IV NSCLC, PD-L1 70%, no EGFR/ALK alterations. Oncology recommending pembrolizumab per NCCN Category 1.",
  "guidelines_context": "NCCN NSCLC Guidelines: pembrolizumab monotherapy is Category 1 first-line for metastatic NSCLC with PD-L1 >= 50%.",
  "expected_outcome": "AUTO_APPROVED",
  "expected_branch": "BRANCH_1_AUTO_APPROVE",
  "reasoning_must_include": ["NCCN Category 1", "PD-L1"],
  "reasoning_must_not_include": [],
  "prior_denial_codes": [],
  "clinical_rationale": "Metastatic NSCLC with high PD-L1, no driver mutations. Clear NCCN Category 1 indication.",
  "judge_scoring_criteria": "Score highly if rationale cites PD-L1 percentage and the NCCN Category 1 designation."
}
"""

# JSON with PHI inserted into clinical_notes
_PHI_DRAFT_JSON = _VALID_DRAFT_JSON.replace(
    "58-year-old male",
    "58-year-old male, SSN 123-45-6789,",
)


class TestPaccaRootCli:
    def test_pacca_help_lists_sme_author(self) -> None:
        runner = CliRunner()
        result = runner.invoke(pacca_cli, ["--help"])
        assert result.exit_code == 0
        assert "sme-author" in result.output

    def test_pacca_version(self) -> None:
        runner = CliRunner()
        result = runner.invoke(pacca_cli, ["--version"])
        assert result.exit_code == 0
        assert "pacca" in result.output


class TestSmeAuthorHelp:
    def test_subgroup_help_lists_new_and_validate(self) -> None:
        runner = CliRunner()
        result = runner.invoke(sme_author, ["--help"])
        assert result.exit_code == 0
        assert "new" in result.output
        assert "validate" in result.output

    def test_new_help_mentions_commit_flag(self) -> None:
        runner = CliRunner()
        result = runner.invoke(sme_author, ["new", "--help"])
        assert result.exit_code == 0
        assert "--commit" in result.output


class TestValidateCommand:
    def test_valid_draft_exits_zero(self, tmp_path: Path) -> None:
        draft_path = tmp_path / "draft.json"
        draft_path.write_text(_VALID_DRAFT_JSON, encoding="utf-8")
        runner = CliRunner()
        result = runner.invoke(sme_author, ["validate", str(draft_path)])
        assert result.exit_code == 0, result.output
        assert "All validators PASS" in result.output

    def test_phi_draft_exits_nonzero(self, tmp_path: Path) -> None:
        draft_path = tmp_path / "draft.json"
        draft_path.write_text(_PHI_DRAFT_JSON, encoding="utf-8")
        runner = CliRunner()
        result = runner.invoke(sme_author, ["validate", str(draft_path)])
        assert result.exit_code != 0
        assert "blocking" in result.output

    def test_missing_file_exits_nonzero(self, tmp_path: Path) -> None:
        runner = CliRunner()
        result = runner.invoke(sme_author, ["validate", str(tmp_path / "missing.json")])
        assert result.exit_code != 0

    def test_malformed_json_surfaces_error(self, tmp_path: Path) -> None:
        draft_path = tmp_path / "draft.json"
        draft_path.write_text("not valid json", encoding="utf-8")
        runner = CliRunner()
        result = runner.invoke(sme_author, ["validate", str(draft_path)])
        assert result.exit_code != 0
        assert "Could not parse" in result.output
