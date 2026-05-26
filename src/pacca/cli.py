"""
PACCA developer-facing CLI.

This module is the entry point referenced by pyproject.toml:
    [project.scripts]
    pacca = "pacca.cli:main"

After `pip install -e .`, the `pacca` command is on PATH. Subcommands:

    pacca sme-author new       — interactive new-case workflow (LLM-drafted)
    pacca sme-author validate  — validate a CaseDraftResponse JSON file
    pacca --help               — list all subcommands

The CLI is a thin Click router. Each subgroup lives in its own module
(currently: sme_authoring/cli_commands.py). To add a new subgroup, import
its `cli` Click group and `pacca_cli.add_command(...)` it below.
"""

from __future__ import annotations

import click

from pacca.agents.sme_authoring.cli_commands import sme_author as sme_author_group


@click.group(name="pacca")
@click.version_option(version="2.4.0", prog_name="pacca")
def pacca_cli() -> None:
    """PACCA developer CLI. Subcommands organize workflows for engineers + SMEs."""


pacca_cli.add_command(sme_author_group, name="sme-author")


def main() -> None:
    """Console-script entry point used by pyproject.toml."""
    pacca_cli()


if __name__ == "__main__":
    main()
