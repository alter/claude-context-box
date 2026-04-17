"""Additive merge for target CLAUDE.md and .claude/settings.json.

Both merges use marker conventions so ccb owns only its own slice and the
user's surrounding content (or unrelated settings) is preserved on reinstall.

CLAUDE.md
---------
ccb manages a single block delimited by HTML comment markers. Anything outside
the markers is left untouched.

    <!-- ccb:begin -->
    ... auto-managed content ...
    <!-- ccb:end -->

settings.json
-------------
ccb owns one top-level key: "ccb". Hooks contributed by ccb are appended to
existing arrays under "hooks" but each ccb-owned hook entry carries
`"_ccb": true` so reinstall can identify and replace prior versions without
touching user-defined hooks.
"""
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

CLAUDE_MD_BEGIN = "<!-- ccb:begin -->"
CLAUDE_MD_END = "<!-- ccb:end -->"
_BLOCK_RE = re.compile(
    re.escape(CLAUDE_MD_BEGIN) + r".*?" + re.escape(CLAUDE_MD_END),
    re.DOTALL,
)

# .gitignore uses hash comments for markers (HTML comments would be literal lines).
GITIGNORE_BEGIN = "# ccb:begin"
GITIGNORE_END = "# ccb:end"
_GITIGNORE_BLOCK_RE = re.compile(
    re.escape(GITIGNORE_BEGIN) + r".*?" + re.escape(GITIGNORE_END),
    re.DOTALL,
)

# Paths ccb writes to the target that should never be committed.
GITIGNORE_PATTERNS: tuple[str, ...] = (
    ".claude/ccb-venv/",
    ".ccb/",
    "PROJECT.llm",
    "**/CONTEXT.llm",
)


def render_claude_md_block(section_body: str, version: str) -> str:
    """Wrap an asset body in begin/end markers with a version stamp."""
    return (
        f"{CLAUDE_MD_BEGIN}\n"
        f"<!-- ccb version: {version} — do not edit between markers; "
        f"changes will be overwritten on reinstall -->\n\n"
        f"{section_body.rstrip()}\n\n"
        f"{CLAUDE_MD_END}"
    )


def merge_claude_md(target_path: Path, ccb_block: str) -> str:
    """Insert or replace the ccb block in target CLAUDE.md.

    Returns one of: "created", "replaced", "appended".
    """
    if not target_path.exists():
        target_path.write_text(ccb_block + "\n", encoding="utf-8")
        return "created"

    existing = target_path.read_text(encoding="utf-8")
    if _BLOCK_RE.search(existing):
        new = _BLOCK_RE.sub(lambda _m: ccb_block, existing, count=1)
        target_path.write_text(new, encoding="utf-8")
        return "replaced"

    sep = "" if existing.endswith("\n\n") else ("\n" if existing.endswith("\n") else "\n\n")
    target_path.write_text(existing + sep + ccb_block + "\n", encoding="utf-8")
    return "appended"


def strip_claude_md(target_path: Path) -> bool:
    """Remove the ccb block from target CLAUDE.md. Returns True if removed."""
    if not target_path.exists():
        return False
    existing = target_path.read_text(encoding="utf-8")
    if not _BLOCK_RE.search(existing):
        return False
    new = _BLOCK_RE.sub("", existing, count=1).rstrip() + "\n"
    target_path.write_text(new, encoding="utf-8")
    return True


def render_gitignore_block(version: str) -> str:
    """Wrap ccb gitignore patterns in begin/end markers with a version stamp."""
    body = "\n".join(GITIGNORE_PATTERNS)
    return (
        f"{GITIGNORE_BEGIN}\n"
        f"# ccb runtime artifacts (managed by claude-context-box {version}; "
        f"do not edit between markers)\n"
        f"{body}\n"
        f"{GITIGNORE_END}"
    )


def merge_gitignore(target_path: Path, ccb_block: str) -> str:
    """Insert or replace the ccb block in target .gitignore.

    Returns one of: "created", "replaced", "appended", "patterns-already-listed".
    The last status indicates the project author already explicitly listed
    every ccb path outside of any ccb markers — we leave them alone instead
    of forcing a duplicate block.
    """
    if not target_path.exists():
        target_path.write_text(ccb_block + "\n", encoding="utf-8")
        return "created"

    existing = target_path.read_text(encoding="utf-8")
    if _GITIGNORE_BLOCK_RE.search(existing):
        new = _GITIGNORE_BLOCK_RE.sub(lambda _m: ccb_block, existing, count=1)
        target_path.write_text(new, encoding="utf-8")
        return "replaced"

    # Heuristic: if every pattern ccb owns already appears in .gitignore as a
    # standalone line, the user has manually listed them — don't append.
    existing_lines = {line.strip() for line in existing.splitlines()}
    if all(p in existing_lines for p in GITIGNORE_PATTERNS):
        return "patterns-already-listed"

    sep = "" if existing.endswith("\n\n") else ("\n" if existing.endswith("\n") else "\n\n")
    target_path.write_text(existing + sep + ccb_block + "\n", encoding="utf-8")
    return "appended"


def strip_gitignore(target_path: Path) -> bool:
    """Remove the ccb block from target .gitignore. Returns True if removed."""
    if not target_path.exists():
        return False
    existing = target_path.read_text(encoding="utf-8")
    if not _GITIGNORE_BLOCK_RE.search(existing):
        return False
    new = _GITIGNORE_BLOCK_RE.sub("", existing, count=1).rstrip() + "\n"
    target_path.write_text(new, encoding="utf-8")
    return True


def merge_settings_json(target_path: Path, ccb_settings: dict[str, Any]) -> str:
    """Merge ccb-owned keys into .claude/settings.json without clobbering user keys.

    Strategy:
      - Top-level "ccb" key: replaced wholesale (ccb owns it).
      - Top-level "hooks" key: ccb-owned entries (marked with "_ccb": True)
        are removed and re-added; user entries are preserved untouched.

    Returns one of: "created", "merged".
    """
    if not target_path.exists():
        target_path.parent.mkdir(parents=True, exist_ok=True)
        target_path.write_text(json.dumps(ccb_settings, indent=2) + "\n", encoding="utf-8")
        return "created"

    try:
        existing = json.loads(target_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise SystemExit(f"settings.json is not valid JSON: {target_path} ({exc})")

    if not isinstance(existing, dict):
        raise SystemExit(f"settings.json must be a JSON object: {target_path}")

    if "ccb" in ccb_settings:
        existing["ccb"] = ccb_settings["ccb"]

    if "hooks" in ccb_settings:
        existing_hooks = existing.get("hooks") or {}
        if not isinstance(existing_hooks, dict):
            raise SystemExit("settings.json 'hooks' must be a JSON object")
        for event, entries in ccb_settings["hooks"].items():
            user_entries = [
                e for e in (existing_hooks.get(event) or []) if not _is_ccb_owned(e)
            ]
            existing_hooks[event] = user_entries + list(entries)
        existing["hooks"] = existing_hooks

    target_path.write_text(json.dumps(existing, indent=2) + "\n", encoding="utf-8")
    return "merged"


def _is_ccb_owned(entry: Any) -> bool:
    return isinstance(entry, dict) and entry.get("_ccb") is True
