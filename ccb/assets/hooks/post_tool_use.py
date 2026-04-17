#!/usr/bin/env python3
"""PostToolUse hook: record which files Claude touched, for incremental updates.

Edits and writes accumulate in `.ccb/state.json`; the SessionEnd hook drains
them when the session closes. This keeps context regeneration cheap during the
session and incremental afterwards.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from _lib import project_root, read_input, read_state, safe_main, write_output, write_state  # noqa: E402

WATCHED_TOOLS = {"Edit", "Write", "MultiEdit", "NotebookEdit"}


def run() -> None:
    payload = read_input()
    tool = payload.get("tool_name") or payload.get("toolName") or ""
    if tool not in WATCHED_TOOLS:
        write_output({})
        return

    tool_input = payload.get("tool_input") or payload.get("toolInput") or {}
    file_path = tool_input.get("file_path") or tool_input.get("path") or ""
    if not file_path:
        write_output({})
        return

    root = project_root()
    rel = _to_relative(file_path, root)

    state = read_state(root)
    changed = set(state.get("changed_files", []))
    changed.add(rel)
    state["changed_files"] = sorted(changed)
    write_state(state, root)

    write_output({})


def _to_relative(file_path: str, root: Path) -> str:
    p = Path(file_path)
    try:
        return str(p.resolve().relative_to(root))
    except ValueError:
        return str(p)


if __name__ == "__main__":
    safe_main("post_tool_use", run)
