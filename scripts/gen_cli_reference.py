#!/usr/bin/env python3
"""Helper to generate the subcommand reference section of docs/reference/CLI_REFERENCE.md
from the live argparse setup in src/cliron_chef/cli.py.

This is OPT-IN — run it manually when you add a new subcommand or flag and want a
fresh skeleton to paste in. It does NOT auto-overwrite the human-curated doc.

Usage:
    python3 scripts/gen_cli_reference.py
    # prints generated markdown to stdout — paste into docs/reference/CLI_REFERENCE.md
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

SRC = Path(__file__).resolve().parents[1] / "src"
if SRC.is_dir() and str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))


def get_help(args_list: list[str]) -> str:
    """Run `cliron-chef <args> --help` and capture stdout."""
    result = subprocess.run(
        [sys.executable, "-m", "cliron_chef"] + args_list + ["--help"],
        capture_output=True,
        text=True,
        timeout=15,
        check=True,
    )
    return result.stdout


def get_child_commands(help_text: str) -> list[str]:
    """Parse argparse help text for a subparser `{child,command}` choices group.

    Argparse also renders option choices as braces (for example `--region {US,EU}`),
    so only accept brace groups followed by argparse's subcommand ellipsis.
    """
    import re

    for line in help_text.splitlines():
        match = re.search(r"\{([a-zA-Z0-9_, -]+)\}\s+\.\.\.\s*$", line)
        if match:
            return [part.strip() for part in match.group(1).split(",") if part.strip()]
    return []


def get_command_paths() -> list[list[str]]:
    """Discover top-level and one-level nested argparse command paths."""
    paths: list[list[str]] = []
    for sub in get_child_commands(get_help([])):
        paths.append([sub])
        for child in get_child_commands(get_help([sub])):
            paths.append([sub, child])
    return paths


def main():
    command_paths = get_command_paths()

    print("# CLI Reference (auto-generated skeleton)")
    print()
    print("This is a starting point — hand-curate explanations, examples, and cross-refs in")
    print("the real `docs/reference/CLI_REFERENCE.md`. Regenerate with `python3 scripts/gen_cli_reference.py`.")
    print()
    print("## Subcommands")
    print()

    for path in command_paths:
        command = " ".join(path)
        print(f"### `cliron-chef {command}`")
        print()
        print("```")
        help_text = get_help(path)
        print(help_text.rstrip())
        print("```")
        print()


if __name__ == "__main__":
    main()
