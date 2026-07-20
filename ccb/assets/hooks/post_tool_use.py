#!/usr/bin/env python3
"""PostToolUse hook: record which files Claude touched, for incremental updates.

Edits and writes accumulate in `.ccb/changed_files.jsonl` (append-only — this
hook runs on EVERY edit, so it must not read-modify-rewrite anything); the
SessionEnd hook drains and dedups the file when the session closes. This keeps
context regeneration cheap during the session and incremental afterwards.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from _lib import ccb_dir, project_root, read_input, safe_main, write_output  # noqa: E402

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

    log = ccb_dir(root) / "changed_files.jsonl"
    log.parent.mkdir(parents=True, exist_ok=True)
    with log.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps({"path": rel}) + "\n")

    write_output({})


def _to_relative(file_path: str, root: Path) -> str:
    p = Path(file_path)
    try:
        return str(p.resolve().relative_to(root))
    except ValueError:
        return str(p)


if __name__ == "__main__":
    safe_main("post_tool_use", run)
