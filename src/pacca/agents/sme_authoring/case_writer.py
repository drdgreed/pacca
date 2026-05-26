"""
Emit GoldenCase Python source and append to a case file.

The case writer produces idiomatic Python that matches the existing
hand-authored cases. After write, the file is verified with `ast.parse`
to guarantee syntactic correctness — a corrupt write would crash the
test suite and is unacceptable.

Design:
- `format_case_as_python(case)`: pure function. Returns a Python string
  containing a single GoldenCase(...) literal. Multiline string fields
  use paren-syntax concatenation to match the existing style.
- `append_case_to_file(case, target_path, list_name)`: inserts the new
  GoldenCase literal before the closing `]` of the list. Idempotent: if
  the case_id is already in the file, raises CaseAlreadyExists rather
  than duplicating.
- `create_new_case_file(list_name, target_path, module_docstring)`:
  scaffolds a new thematic file (with imports + empty list) ready for
  the first case to be appended.

After writing, `_validate_ast(target_path)` parses the file to verify
syntactic correctness. If parsing fails, the write is rolled back.
"""

from __future__ import annotations

import ast
import textwrap
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pathlib import Path

    from pacca.agents.sme_authoring.models import CaseDraftResponse

# Width to wrap long string literals at when emitting Python source.
_WRAP_WIDTH = 68


class CaseWriterError(Exception):
    """Base class for case_writer errors."""


class CaseAlreadyExists(CaseWriterError):
    """Raised when attempting to write a case_id that already lives in the file."""


class FileSyntaxError(CaseWriterError):
    """Raised when the written file fails ast.parse — write is rolled back."""


# =============================================================================
# Formatting helpers
# =============================================================================


def _escape_for_python_string(s: str) -> str:
    """
    Escape a string for safe embedding inside a Python double-quoted string
    literal.

    Handles: backslash, double-quote, control characters. Does NOT handle
    newlines — caller is responsible for chunking on word boundaries.
    """
    return s.replace("\\", "\\\\").replace('"', '\\"')


def _wrap_long_string(value: str, indent: str) -> str:
    """
    Emit a long string value as paren-concatenated chunks.

    Example output for indent='    ' and a 200-char value:

        (
            "First chunk up to about 68 chars wide. "
            "Second chunk continues the wrap. "
            "Final chunk."
        )

    Lines are wrapped at word boundaries (via textwrap.wrap) so we never
    split words.
    """
    if not value:
        return '""'

    # Replace any internal newlines with single spaces (we don't want to
    # preserve incidental newlines that the LLM might emit; the canonical
    # representation collapses to a single logical paragraph).
    normalized = " ".join(value.split())

    chunks = textwrap.wrap(
        normalized,
        width=_WRAP_WIDTH,
        break_long_words=False,
        break_on_hyphens=False,
    )

    if len(chunks) == 1:
        return f'"{_escape_for_python_string(chunks[0])}"'

    inner_indent = indent + "    "
    lines = ["("]
    for chunk in chunks[:-1]:
        # Each chunk ends with a trailing space to preserve word separation
        # across concatenated literals.
        lines.append(f'{inner_indent}"{_escape_for_python_string(chunk)} "')
    # Final chunk has no trailing space
    lines.append(f'{inner_indent}"{_escape_for_python_string(chunks[-1])}"')
    lines.append(f"{indent})")
    return "\n".join(lines)


def _format_list_field(name: str, values: list[str], indent: str) -> str:
    """Format `name=["a", "b"]` field, wrapped if needed."""
    if not values:
        return f"{indent}{name}=[],"

    inner = ", ".join(f'"{_escape_for_python_string(v)}"' for v in values)
    one_line = f"{indent}{name}=[{inner}],"
    if len(one_line) <= 95:
        return one_line

    # Wrap one-entry-per-line
    item_indent = indent + "    "
    lines = [f"{indent}{name}=["]
    for v in values:
        lines.append(f'{item_indent}"{_escape_for_python_string(v)}",')
    lines.append(f"{indent}],")
    return "\n".join(lines)


def _format_string_field(name: str, value: str, indent: str) -> str:
    """Format `name="..."` field, wrapped via paren-syntax if long."""
    formatted_value = _wrap_long_string(value, indent)
    return f"{indent}{name}={formatted_value},"


def format_case_as_python(case: CaseDraftResponse) -> str:
    """
    Return the GoldenCase(...) literal as a multi-line Python string.

    The output is suitable for direct insertion before the closing `]`
    of a CASES list. Indentation is 4 spaces for fields, matching the
    existing case files' convention.

    Args:
        case: The case to render.

    Returns:
        A multi-line string ending with `,\n` so that insertion before
        another list element produces a syntactically-clean result.
    """
    field_indent = "        "  # 8 spaces (2 levels)
    inner_indent = "    "  # 4 spaces (1 level)

    expected_outcome_expr = f"ExpectedOutcome.{case.expected_outcome}"
    expected_branch_expr = f"EscalationBranch.{case.expected_branch}"

    field_lines: list[str] = [
        f'{field_indent}case_id="{case.case_id}",',
        _format_string_field("title", case.title, field_indent),
        f'{field_indent}diagnosis_code="{case.diagnosis_code}",',
        _format_string_field("diagnosis_description", case.diagnosis_description, field_indent),
        f'{field_indent}procedure_code="{case.procedure_code}",',
        _format_string_field("procedure_description", case.procedure_description, field_indent),
        _format_string_field("clinical_notes", case.clinical_notes, field_indent),
        _format_string_field("guidelines_context", case.guidelines_context, field_indent),
        f"{field_indent}expected_outcome={expected_outcome_expr},",
        f"{field_indent}expected_branch={expected_branch_expr},",
        _format_list_field("reasoning_must_include", case.reasoning_must_include, field_indent),
        _format_list_field(
            "reasoning_must_not_include",
            case.reasoning_must_not_include,
            field_indent,
        ),
    ]
    if case.prior_denial_codes:
        field_lines.append(
            _format_list_field("prior_denial_codes", case.prior_denial_codes, field_indent)
        )
    field_lines.append(
        _format_string_field("clinical_rationale", case.clinical_rationale, field_indent)
    )
    field_lines.append(
        _format_string_field("judge_scoring_criteria", case.judge_scoring_criteria, field_indent)
    )

    body = "\n".join(field_lines)
    return f"{inner_indent}GoldenCase(\n{body}\n{inner_indent}),"


# =============================================================================
# File mutation
# =============================================================================


def _validate_ast(path: Path) -> None:
    """Parse the file; raise FileSyntaxError on failure."""
    try:
        ast.parse(path.read_text(encoding="utf-8"))
    except SyntaxError as exc:
        raise FileSyntaxError(f"Generated file {path} has a syntax error: {exc}") from exc


def _case_id_already_in_file(case_id: str, file_text: str) -> bool:
    """True if file_text contains `case_id="{case_id}"`."""
    needle_double = f'case_id="{case_id}"'
    needle_single = f"case_id='{case_id}'"
    return needle_double in file_text or needle_single in file_text


def create_new_case_file(
    list_name: str,
    target_path: Path,
    module_docstring: str | None = None,
) -> None:
    """
    Scaffold a new thematic case file ready for the first case to be appended.

    The file will contain: module docstring, `from __future__` import,
    GoldenCase imports, and an empty list named `list_name` ready for
    cases to be appended before the closing `]`.

    Raises:
        FileExistsError if target_path already exists.
    """
    if target_path.exists():
        raise FileExistsError(
            f"Cannot create {target_path}: file already exists. "
            "Use append_case_to_file to add cases to an existing file."
        )

    docstring = module_docstring or (
        f"{target_path.stem.replace('_', ' ').title()} — SME-authored cases."
    )
    target_path.parent.mkdir(parents=True, exist_ok=True)
    target_path.write_text(
        f'"""\n{docstring}\n"""\n\n'
        "from __future__ import annotations\n\n"
        "from tests.clinical.golden_cases import (\n"
        "    EscalationBranch,\n"
        "    ExpectedOutcome,\n"
        "    GoldenCase,\n"
        ")\n\n"
        f"{list_name}: list[GoldenCase] = [\n]\n",
        encoding="utf-8",
    )
    _validate_ast(target_path)


def append_case_to_file(  # noqa: PLR0912, PLR0915
    case: CaseDraftResponse,
    target_path: Path,
    list_name: str,
) -> None:
    """
    Append a GoldenCase to the named list in target_path.

    The case is inserted just before the closing `]` of the list. After
    write, the file is parsed via `ast.parse` to verify syntactic
    correctness; if parsing fails, the original content is restored and
    FileSyntaxError is raised.

    Args:
        case: The case to append.
        target_path: Path to the case file (must exist).
        list_name: Name of the list variable (e.g., "CARDIOLOGY_CASES").

    Raises:
        FileNotFoundError: if target_path does not exist.
        CaseAlreadyExists: if case.case_id is already in the file.
        FileSyntaxError: if the resulting file fails ast.parse.
    """
    if not target_path.exists():
        raise FileNotFoundError(f"{target_path} does not exist. Use create_new_case_file first.")

    original_text = target_path.read_text(encoding="utf-8")

    if _case_id_already_in_file(case.case_id, original_text):
        raise CaseAlreadyExists(
            f"case_id={case.case_id} already lives in {target_path}. "
            "Allocate a fresh ID via id_allocator.next_id()."
        )

    new_block = format_case_as_python(case)

    # Find the list's closing `]`. Strategy: look for `{list_name}: ... = [`
    # then find the matching closing bracket. We use a simple bracket-counting
    # walk because the case files don't contain nested lists at this depth.
    list_start_marker = f"{list_name}"
    list_anchor = original_text.find(list_start_marker)
    if list_anchor == -1:
        raise CaseWriterError(
            f"Could not find list '{list_name}' in {target_path}. "
            "File may be malformed or the list_name is incorrect."
        )

    # Find the opening `[` after the anchor
    open_bracket = original_text.find("[", list_anchor)
    if open_bracket == -1:
        raise CaseWriterError(
            f"Could not find opening '[' for list '{list_name}' in {target_path}."
        )

    # Walk to find the matching closing `]` — bracket-counting, skipping
    # contents of string literals.
    depth = 1
    pos = open_bracket + 1
    in_string: str | None = None
    while pos < len(original_text) and depth > 0:
        ch = original_text[pos]

        # Track string-literal context to avoid counting brackets inside strings
        if in_string is not None:
            if ch == "\\":
                pos += 2  # skip escape sequence
                continue
            if ch == in_string:
                in_string = None
        elif ch in ('"', "'"):
            # Check for triple-quoted string
            if original_text[pos : pos + 3] in ('"""', "'''"):
                triple = original_text[pos : pos + 3]
                end_triple = original_text.find(triple, pos + 3)
                if end_triple == -1:
                    raise CaseWriterError(f"Unterminated triple-quoted string in {target_path}.")
                pos = end_triple + 3
                continue
            in_string = ch
        elif ch == "[":
            depth += 1
        elif ch == "]":
            depth -= 1
            if depth == 0:
                break
        pos += 1

    if depth != 0:
        raise CaseWriterError(
            f"Could not find matching ']' for list '{list_name}' in {target_path}."
        )

    closing_bracket = pos

    # Insert the new block just before the closing `]`. Add a newline before
    # if the previous non-whitespace char isn't a comma or `[`, to ensure
    # the new block starts on its own line.
    insertion_point = closing_bracket

    # Walk backwards to find the previous non-whitespace char
    walk = insertion_point - 1
    while walk >= 0 and original_text[walk] in " \t\n":
        walk -= 1

    # Add a comma after the previous element if it doesn't already have one
    prefix_fix = "," if walk >= 0 and original_text[walk] not in (",", "[") else ""

    new_text = (
        original_text[: walk + 1]
        + prefix_fix
        + "\n"
        + new_block
        + "\n"
        + original_text[insertion_point:]
    )

    # Write to a temp file + rename for atomicity
    tmp_path = target_path.with_suffix(target_path.suffix + ".tmp")
    tmp_path.write_text(new_text, encoding="utf-8")

    # Validate the new file
    try:
        _validate_ast(tmp_path)
    except FileSyntaxError:
        tmp_path.unlink()
        raise

    # Atomic replace
    tmp_path.replace(target_path)
