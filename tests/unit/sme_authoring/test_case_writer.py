"""
Tests for case_writer.

Strategy:
- format_case_as_python: assert output parses via ast.parse + contains
  expected fields.
- append_case_to_file: write to a tmp file with a known scaffold, assert
  case appended, file still parses, case_id preserved.
- create_new_case_file: scaffold + immediately append → file parses.
- Idempotency: appending the same case twice raises CaseAlreadyExists.
- Syntax-safety: a deliberately-broken case-text triggers FileSyntaxError
  (and the file is restored).
"""

from __future__ import annotations

import ast
from typing import TYPE_CHECKING

import pytest

from pacca.agents.sme_authoring.case_writer import (
    CaseAlreadyExists,
    CaseWriterError,
    FileSyntaxError,
    _wrap_long_string,
    append_case_to_file,
    create_new_case_file,
    format_case_as_python,
)

if TYPE_CHECKING:
    from pathlib import Path

    from pacca.agents.sme_authoring.models import CaseDraftResponse


# =============================================================================
# format_case_as_python — pure function
# =============================================================================


class TestFormatCaseAsPython:
    def test_output_contains_case_id(self, valid_case_draft: CaseDraftResponse) -> None:
        text = format_case_as_python(valid_case_draft)
        assert f'case_id="{valid_case_draft.case_id}"' in text

    def test_output_contains_outcome_enum(self, valid_case_draft: CaseDraftResponse) -> None:
        text = format_case_as_python(valid_case_draft)
        assert "ExpectedOutcome.AUTO_APPROVED" in text
        assert "EscalationBranch.BRANCH_1_AUTO_APPROVE" in text

    def test_output_is_syntactically_valid_python_in_context(
        self, valid_case_draft: CaseDraftResponse
    ) -> None:
        """
        Wrap the case block in a minimal module + import preamble and
        verify ast.parse succeeds. This is the contract case_writer
        relies on: the emitted block must be drop-in-able.
        """
        case_text = format_case_as_python(valid_case_draft)
        full_module = (
            "from tests.clinical.golden_cases import (\n"
            "    EscalationBranch,\n"
            "    ExpectedOutcome,\n"
            "    GoldenCase,\n"
            ")\n\n"
            f"CASES = [\n{case_text}\n]\n"
        )
        ast.parse(full_module)

    def test_long_strings_wrapped_with_parens(self, valid_case_draft: CaseDraftResponse) -> None:
        text = format_case_as_python(valid_case_draft)
        # The fixture's clinical_notes is long enough to trigger wrapping
        assert "clinical_notes=(" in text

    def test_reasoning_must_not_include_empty_list_emitted(
        self, valid_case_draft: CaseDraftResponse
    ) -> None:
        # Fixture has empty reasoning_must_not_include
        text = format_case_as_python(valid_case_draft)
        assert "reasoning_must_not_include=[]" in text

    def test_idempotent_formatting(self, valid_case_draft: CaseDraftResponse) -> None:
        # Formatting twice yields identical output (deterministic)
        a = format_case_as_python(valid_case_draft)
        b = format_case_as_python(valid_case_draft)
        assert a == b


# =============================================================================
# _wrap_long_string helper
# =============================================================================


class TestWrapLongString:
    def test_empty_string_returns_empty_literal(self) -> None:
        assert _wrap_long_string("", "    ") == '""'

    def test_short_string_returns_single_quoted(self) -> None:
        assert _wrap_long_string("Short text.", "    ") == '"Short text."'

    def test_long_string_emits_paren_block(self) -> None:
        long = "Word " * 30  # well over the wrap width
        result = _wrap_long_string(long, "    ")
        assert result.startswith("(")
        assert result.endswith(")")
        # Multi-line
        assert "\n" in result

    def test_escapes_double_quotes(self) -> None:
        result = _wrap_long_string('She said "hello".', "    ")
        assert '\\"hello\\"' in result


# =============================================================================
# create_new_case_file
# =============================================================================


class TestCreateNewCaseFile:
    def test_creates_parseable_scaffold(self, tmp_path: Path) -> None:
        target = tmp_path / "nephrology_cases.py"
        create_new_case_file("NEPHROLOGY_CASES", target)

        assert target.exists()
        # Parses cleanly
        ast.parse(target.read_text(encoding="utf-8"))

    def test_includes_imports(self, tmp_path: Path) -> None:
        target = tmp_path / "nephrology_cases.py"
        create_new_case_file("NEPHROLOGY_CASES", target)
        text = target.read_text(encoding="utf-8")
        assert "GoldenCase" in text
        assert "EscalationBranch" in text
        assert "ExpectedOutcome" in text

    def test_includes_empty_list(self, tmp_path: Path) -> None:
        target = tmp_path / "nephrology_cases.py"
        create_new_case_file("NEPHROLOGY_CASES", target)
        text = target.read_text(encoding="utf-8")
        assert "NEPHROLOGY_CASES: list[GoldenCase] = [\n]" in text

    def test_uses_custom_docstring(self, tmp_path: Path) -> None:
        target = tmp_path / "nephrology_cases.py"
        create_new_case_file("NEPHROLOGY_CASES", target, module_docstring="My custom docstring.")
        text = target.read_text(encoding="utf-8")
        assert "My custom docstring." in text

    def test_existing_file_raises(self, tmp_path: Path) -> None:
        target = tmp_path / "nephrology_cases.py"
        target.write_text("existing content", encoding="utf-8")
        with pytest.raises(FileExistsError):
            create_new_case_file("NEPHROLOGY_CASES", target)


# =============================================================================
# append_case_to_file
# =============================================================================


class TestAppendCaseToFile:
    def test_append_to_empty_scaffold(
        self, valid_case_draft: CaseDraftResponse, tmp_path: Path
    ) -> None:
        target = tmp_path / "test_cases.py"
        create_new_case_file("TEST_CASES", target)
        append_case_to_file(valid_case_draft, target, "TEST_CASES")

        text = target.read_text(encoding="utf-8")
        assert f'case_id="{valid_case_draft.case_id}"' in text
        # File still parses
        ast.parse(text)

    def test_append_two_cases_in_sequence(
        self, valid_case_draft: CaseDraftResponse, tmp_path: Path
    ) -> None:
        target = tmp_path / "test_cases.py"
        create_new_case_file("TEST_CASES", target)
        append_case_to_file(valid_case_draft, target, "TEST_CASES")

        second = valid_case_draft.model_copy(update={"case_id": "GC-200"})
        append_case_to_file(second, target, "TEST_CASES")

        text = target.read_text(encoding="utf-8")
        assert 'case_id="GC-101"' in text
        assert 'case_id="GC-200"' in text
        ast.parse(text)

    def test_duplicate_case_id_raises(
        self, valid_case_draft: CaseDraftResponse, tmp_path: Path
    ) -> None:
        target = tmp_path / "test_cases.py"
        create_new_case_file("TEST_CASES", target)
        append_case_to_file(valid_case_draft, target, "TEST_CASES")

        with pytest.raises(CaseAlreadyExists):
            append_case_to_file(valid_case_draft, target, "TEST_CASES")

    def test_missing_file_raises(self, valid_case_draft: CaseDraftResponse, tmp_path: Path) -> None:
        target = tmp_path / "does_not_exist.py"
        with pytest.raises(FileNotFoundError):
            append_case_to_file(valid_case_draft, target, "TEST_CASES")

    def test_missing_list_raises(self, valid_case_draft: CaseDraftResponse, tmp_path: Path) -> None:
        target = tmp_path / "test_cases.py"
        target.write_text('"""Doc."""\n\nSOMETHING_ELSE = {}\n', encoding="utf-8")
        with pytest.raises(CaseWriterError):
            append_case_to_file(valid_case_draft, target, "TEST_CASES")

    def test_appends_before_closing_bracket_with_existing_case(
        self, valid_case_draft: CaseDraftResponse, tmp_path: Path
    ) -> None:
        # Pre-seed with one hand-crafted case (no trailing comma after the
        # closing paren of the existing case) to test the comma-insertion path
        target = tmp_path / "test_cases.py"
        target.write_text(
            (
                '"""Doc."""\n\n'
                "from tests.clinical.golden_cases import (\n"
                "    EscalationBranch,\n"
                "    ExpectedOutcome,\n"
                "    GoldenCase,\n"
                ")\n\n"
                "TEST_CASES: list[GoldenCase] = [\n"
                "    GoldenCase(\n"
                '        case_id="GC-001",\n'
                '        title="Existing",\n'
                '        diagnosis_code="X00",\n'
                '        diagnosis_description="Existing desc",\n'
                '        procedure_code="P00",\n'
                '        procedure_description="Proc desc",\n'
                '        clinical_notes="Pre-existing notes that are long enough.",\n'
                '        guidelines_context="Pre-existing guidelines context.",\n'
                "        expected_outcome=ExpectedOutcome.AUTO_APPROVED,\n"
                "        expected_branch=EscalationBranch.BRANCH_1_AUTO_APPROVE,\n"
                '        reasoning_must_include=["x"],\n'
                "    )\n"  # NOTE: no trailing comma
                "]\n"
            ),
            encoding="utf-8",
        )
        append_case_to_file(valid_case_draft, target, "TEST_CASES")
        text = target.read_text(encoding="utf-8")
        # Both cases present
        assert 'case_id="GC-001"' in text
        assert f'case_id="{valid_case_draft.case_id}"' in text
        # Still parses
        ast.parse(text)


# =============================================================================
# Syntax-error safety
# =============================================================================


class TestSyntaxErrorSafety:
    def test_validate_ast_on_malformed_file_raises(self, tmp_path: Path) -> None:
        from pacca.agents.sme_authoring.case_writer import _validate_ast

        bad = tmp_path / "broken.py"
        bad.write_text("def broken(\n", encoding="utf-8")
        with pytest.raises(FileSyntaxError):
            _validate_ast(bad)
