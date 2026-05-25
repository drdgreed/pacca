"""
Prompt loader for file-extracted agent system prompts.

Part of the v2.3 harness engineering cycle (Phase H1: Component Decoupling).
See docs/HARNESS.md for the methodology and harness/manifests/iter-1.json
for the chg-1 manifest entry that introduced this module.
"""

from __future__ import annotations

from pathlib import Path

from jinja2 import Environment, StrictUndefined

from pacca.agents.prompts.templates import (
    AGENT_IDENTITY,
    CLINICAL_SAFETY_GUIDELINES,
    OUTPUT_FORMAT_INSTRUCTIONS,
    PROMPT_REGISTRY,
)

_jinja_env = Environment(
    undefined=StrictUndefined,
    keep_trailing_newline=True,
)


def load_agent_prompt(agent_dir_name: str, agent_registry_name: str) -> str:
    """Load and render an agent system prompt from its file mount point.

    For agents without a long_term_memory.md file, returns a string
    byte-identical to the pre-H1 f-string output (iter-1 contract preserved).

    iter-3 chg-2 (Phase H2): if the agent directory contains a
    `long_term_memory.md` file, its contents are injected as the
    `long_term_memory` Jinja variable; the system_prompt.md template's
    `{% if long_term_memory %}` guard renders the Institutional Memory
    section only when the file exists. Agents without the file (e.g.
    MedicalDirectorAgent) get an empty string and their prompt is unchanged.
    """
    base_dir = Path(__file__).parent / agent_dir_name
    prompt_path = base_dir / "system_prompt.md"
    raw = prompt_path.read_text(encoding="utf-8")

    # iter-3 chg-2: optional long-term memory injection (Phase H2).
    # Backward-compatible: agents without a memory file get an empty string.
    memory_path = base_dir / "long_term_memory.md"
    long_term_memory = memory_path.read_text(encoding="utf-8") if memory_path.exists() else ""

    template = _jinja_env.from_string(raw)
    # Jinja's render() is typed Any (no stubs); explicitly annotate as str so
    # mypy strict mode is satisfied. Surfaced after iter-3 chg-1 added py.typed
    # to the pacca package, making mypy walk transitive imports.
    rendered: str = template.render(
        agent_identity=AGENT_IDENTITY,
        clinical_safety_guidelines=CLINICAL_SAFETY_GUIDELINES,
        output_format_instructions=OUTPUT_FORMAT_INSTRUCTIONS,
        prompt_version=PROMPT_REGISTRY[agent_registry_name]["version"],
        long_term_memory=long_term_memory,
    )

    if rendered.endswith("\n"):
        rendered = rendered[:-1]

    return rendered
