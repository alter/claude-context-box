"""Merge ccb-managed sections into target CLAUDE.md and .claude/settings.json.

Uses HTML comment markers so user content outside markers is preserved on reinstall.
Implementation lands in Phase B.
"""
from __future__ import annotations

from pathlib import Path

CLAUDE_MD_BEGIN = "<!-- ccb:begin -->"
CLAUDE_MD_END = "<!-- ccb:end -->"


def merge_claude_md(target_path: Path, ccb_section: str) -> None:
    raise NotImplementedError


def merge_settings_json(target_path: Path, ccb_settings: dict) -> None:
    raise NotImplementedError
