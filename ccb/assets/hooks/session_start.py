#!/usr/bin/env python3
"""SessionStart hook: inject project context so Claude doesn't re-scan on every open.

Reads PROJECT.llm and the most recent daily log, returns them via
hookSpecificOutput.additionalContext so they land in the system prompt.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from _lib import ccb_dir, project_root, read_input, safe_main, write_output  # noqa: E402


def run() -> None:
    read_input()  # consume any payload Claude Code sends
    root = project_root()

    parts: list[str] = []

    project_llm = root / "PROJECT.llm"
    if project_llm.exists():
        parts.append(f"### PROJECT.llm\n\n```\n{project_llm.read_text(encoding='utf-8').strip()}\n```")

    daily_dir = ccb_dir(root) / "daily_log"
    if daily_dir.is_dir():
        logs = sorted(daily_dir.glob("*.md"))
        if logs:
            latest = logs[-1]
            parts.append(
                f"### last session log: {latest.name}\n\n{latest.read_text(encoding='utf-8').strip()}"
            )

    if not parts:
        write_output({})
        return

    body = (
        "ccb-managed project context (auto-injected at session start):\n\n"
        + "\n\n".join(parts)
    )
    write_output(
        {
            "hookSpecificOutput": {
                "hookEventName": "SessionStart",
                "additionalContext": body,
            }
        }
    )


if __name__ == "__main__":
    safe_main("session_start", run)
