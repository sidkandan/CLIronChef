"""Detect drift between cli.py argparse setup and docs/reference/CLI_REFERENCE.md.

This catches the documentation-vs-reality drift that Codex caught (where CLI_REFERENCE.md
documented flags like --log-file and --no-log that didn't actually exist in cli.py).

Strategy: parse the argparse setup in cli.py to get actual subcommands + long flags,
then check that each one is mentioned in CLI_REFERENCE.md. We also scan the docs for
long flag-like tokens and assert they exist in the CLI, with a tiny allowlist for
argparse's automatic `--help`.
"""
from __future__ import annotations

import re
from pathlib import Path

import pytest

CLI_REFERENCE = Path(__file__).resolve().parents[1] / "docs" / "reference" / "CLI_REFERENCE.md"


def _subcommands_from_cli_source():
    """Get the set of subcommand names by parsing cli.py.

    We parse the source rather than importing main() because argparse setup happens
    inside main() and we can't introspect the live parser after it dispatches. Pragmatic
    compromise; refactor target if cli.py grows a build_parser() helper.
    """
    from cliron_chef import cli as cli_module
    cli_source = Path(cli_module.__file__).read_text()
    subcmd_pattern = re.compile(r'sub(?:_\w+)?\.add_parser\(\s*[\'"]([\w-]+)[\'"]')
    return set(subcmd_pattern.findall(cli_source))


def _extract_flags_from_cli_source():
    """Return every long flag declared in cli.py."""
    from cliron_chef import cli as cli_module

    cli_source = Path(cli_module.__file__).read_text()
    flag_pattern = re.compile(r'add_argument\(\s*[\'"]([-]{1,2}[\w-]+)[\'"](?:\s*,\s*[\'"]([-]{1,2}[\w-]+)[\'"])?')
    long_flags = set()
    for match in flag_pattern.finditer(cli_source):
        for g in match.groups():
            if g and g.startswith("--"):
                long_flags.add(g)
    return long_flags


def _extract_long_flags_from_doc(doc: str):
    """Return every long flag-like token in CLI_REFERENCE.md."""
    return set(re.findall(r'(?<!-)--[A-Za-z][A-Za-z0-9-]*', doc))


def _doc_text():
    if not CLI_REFERENCE.is_file():
        pytest.skip("docs/reference/CLI_REFERENCE.md not found")
    return CLI_REFERENCE.read_text()


def test_every_subcommand_documented():
    """Every cliron-chef subcommand should appear in CLI_REFERENCE.md."""
    subcommands = _subcommands_from_cli_source()
    doc = _doc_text()

    missing = []
    for name in sorted(subcommands):
        if name not in doc:
            missing.append(name)
    assert not missing, (
        f"Subcommands present in cli.py but not in CLI_REFERENCE.md: {missing}. "
        "Either document them or remove from CLI."
    )


def test_every_documented_subcommand_exists():
    r"""Every subcommand documented in CLI_REFERENCE.md should exist in the CLI.

    Looks for lines starting with ``## `subcmd` `` (subcommand section headers).
    """
    doc = _doc_text()
    subcommands = _subcommands_from_cli_source()

    # Find documented subcommand headers like:  ## `cook`  or  ## `recipes list`
    header_pattern = re.compile(r'^##\s+`([\w-]+(?:\s+[\w-]+)*)`', re.MULTILINE)
    documented = set()
    for m in header_pattern.finditer(doc):
        documented.add(m.group(1).split()[0])  # take the first word (parent subcommand)

    # Some entries are aliases or composite (e.g., "recipes list" — we accept the parent)
    undocumented_in_cli = documented - subcommands - {"recipes", "modes"}  # parent commands ok
    assert not undocumented_in_cli, (
        f"Subcommands documented in CLI_REFERENCE.md but missing from cli.py: "
        f"{undocumented_in_cli}. Either implement or remove from docs."
    )


def test_every_cli_flag_documented():
    """Every long flag implemented by argparse should appear in CLI_REFERENCE.md."""
    doc = _doc_text()
    flags_in_cli = _extract_flags_from_cli_source()

    missing = sorted(flag for flag in flags_in_cli if flag not in doc)
    assert not missing, (
        f"Flags present in cli.py but not in CLI_REFERENCE.md: {missing}. "
        "Document them or remove them from the CLI."
    )


def test_no_phantom_flags_documented():
    """Every long flag mentioned in CLI_REFERENCE.md should be implemented."""
    doc = _doc_text()
    flags_in_cli = _extract_flags_from_cli_source()
    allowed_doc_only = {"--help"}  # argparse auto-adds this

    documented_flags = _extract_long_flags_from_doc(doc)
    phantom = sorted(documented_flags - flags_in_cli - allowed_doc_only)
    assert not phantom, (
        f"CLI_REFERENCE.md documents flags not implemented in cli.py: {phantom}. "
        "Remove from docs or add argparse support."
    )


def test_help_executes():
    """Smoke: `cliron-chef --help` must run without crashing."""
    import subprocess
    import sys
    result = subprocess.run(
        [sys.executable, "-m", "cliron_chef", "--help"],
        capture_output=True,
        text=True,
        timeout=15,
    )
    assert result.returncode == 0, f"--help failed: {result.stderr}"
    assert "cliron-chef" in result.stdout.lower()
