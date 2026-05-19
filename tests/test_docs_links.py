"""Validate local Markdown links.

This protects the public-facing docs from broken links when files move or issue
templates reference docs from a different directory depth.
"""

from __future__ import annotations

import re
from pathlib import Path
from urllib.parse import unquote

ROOT = Path(__file__).resolve().parents[1]
LINK_RE = re.compile(r"\[[^\]]+\]\(([^)]+)\)")


def _markdown_files():
    skipped_parts = {".git", ".venv", "__pycache__", ".pytest_cache", ".ruff_cache"}
    for path in ROOT.rglob("*.md"):
        if skipped_parts.intersection(path.relative_to(ROOT).parts):
            continue
        yield path


def _is_external(target: str) -> bool:
    return (
        "://" in target
        or target.startswith("mailto:")
        or target.startswith("#")
    )


def test_local_markdown_links_resolve():
    missing = []
    for path in _markdown_files():
        text = path.read_text()
        for match in LINK_RE.finditer(text):
            raw_target = match.group(1).strip()
            target = unquote(raw_target.split("#", 1)[0])
            if not target or _is_external(raw_target):
                continue

            candidate = (path.parent / target).resolve()
            try:
                candidate.relative_to(ROOT)
            except ValueError:
                missing.append((path.relative_to(ROOT), raw_target, "escapes repo"))
                continue
            if not candidate.exists():
                missing.append((path.relative_to(ROOT), raw_target, "not found"))

    assert not missing, "Broken local Markdown links:\n" + "\n".join(
        f"{path}: {target} ({reason})" for path, target, reason in missing
    )
