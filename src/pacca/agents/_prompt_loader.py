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

    Returns a string byte-identical to the pre-H1 f-string output.
    """
    base_dir = Path(__file__).parent / agent_dir_name
    prompt_path = base_dir / "system_prompt.md"
    raw = prompt_path.read_text(encoding="utf-8")

    template = _jinja_env.from_string(raw)
    rendered = template.render(
        agent_identity=AGENT_IDENTITY,
        clinical_safety_guidelines=CLINICAL_SAFETY_GUIDELINES,
        output_format_instructions=OUTPUT_FORMAT_INSTRUCTIONS,
        prompt_version=PROMPT_REGISTRY[agent_registry_name]["version"],
    )

    if rendered.endswith("\n"):
        rendered = rendered[:-1]

    return rendered
