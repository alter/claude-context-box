#!/usr/bin/env python3
"""SessionStart hook: inject project context so Claude doesn't re-scan on every open.

Steps:
  1. If PROJECT.llm is missing or older than its source files, run update.py
     synchronously to bring contexts up to date (the user might have edited
     files between sessions in another tool).
  2. Read PROJECT.llm and the most recent daily log.
  3. Return them via hookSpecificOutput.additionalContext so they land in the
     system prompt.

The synchronous update is bounded to keep session-start latency reasonable —
worst case 30 seconds, normal case milliseconds when contexts are fresh.
"""
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from _lib import ccb_dir, project_root, read_input, safe_main, write_output  # noqa: E402

UPDATE_TIMEOUT_SECONDS = 30
WALK_BUDGET_SECONDS = 2.0

# Memory-structure files (scaffolded by /ccb-memory init). Injected in this
# order — INDEX.md is the declared entry point, so it goes first.
# current-experiment.md is the pre-0.8 name of current-task.md; a project
# has one or the other, never both from a ccb scaffold.
MEMORY_FILES = (
    "INDEX.md",
    "memory/validation-protocol.md",
    "memory/current-task.md",
    "memory/current-experiment.md",
)
MEMORY_FILE_MAX_CHARS = 8000


def run() -> None:
    read_input()
    if os.environ.get("CCB_INVOKED_BY"):
        # ccb-spawned headless claude run (background summarizer) — don't
        # refresh contexts or inject them; the summarizer only needs its prompt.
        write_output({})
        return
    root = project_root()

    _refresh_if_stale(root)

    parts: list[str] = []

    for rel in MEMORY_FILES:
        p = root / rel
        if not p.is_file():
            continue
        try:
            text = p.read_text(encoding="utf-8", errors="ignore").strip()
        except OSError:
            continue
        if not text:
            continue
        if len(text) > MEMORY_FILE_MAX_CHARS:
            text = text[:MEMORY_FILE_MAX_CHARS] + "\n…(truncated — Read the file for the rest)"
        parts.append(f"### {rel}\n\n{text}")

    project_llm = root / "PROJECT.llm"
    if project_llm.exists():
        parts.append(f"### PROJECT.llm\n\n```\n{project_llm.read_text(encoding='utf-8').strip()}\n```")

    daily_dir = ccb_dir(root) / "daily_log"
    if daily_dir.is_dir():
        logs = sorted(daily_dir.glob("*.md"))
        if logs:
            latest = logs[-1]
            log_text = latest.read_text(encoding="utf-8").strip()
            if len(log_text) > MEMORY_FILE_MAX_CHARS:
                # Keep the tail — the most recent entries matter most.
                log_text = (
                    "…(truncated — Read the file for the rest)\n"
                    + log_text[-MEMORY_FILE_MAX_CHARS:]
                )
            parts.append(f"### last session log: {latest.name}\n\n{log_text}")

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


def _refresh_if_stale(root: Path) -> None:
    """Run update.py synchronously if PROJECT.llm doesn't reflect the source tree.

    OFF by default: it only guards against edits made OUTSIDE Claude Code
    between sessions (another editor, git pull, another machine), while its
    cost — a full tree walk plus a possible synchronous update — is paid on
    every session start by everyone. Changes made inside sessions are already
    tracked by the PostToolUse hook and refreshed at session end.

    Enable via `"ccb": {"auto_refresh": true}` in .claude/settings.json
    (`ccb install --auto-refresh` sets it) or the CCB_AUTO_REFRESH=1 env var.
    """
    if not _auto_refresh_enabled(root):
        return

    update_script = root / ".claude" / "ccb-engine" / "update.py"
    if not update_script.exists():
        return

    project_llm = root / "PROJECT.llm"
    if project_llm.exists() and not _is_stale(project_llm, root):
        return

    try:
        subprocess.run(
            [sys.executable, str(update_script)],
            cwd=str(root),
            capture_output=True,
            text=True,
            timeout=UPDATE_TIMEOUT_SECONDS,
        )
    except Exception:
        # safe_main will log; we still inject whatever PROJECT.llm exists.
        pass


def _auto_refresh_enabled(root: Path) -> bool:
    """Session-start refresh is opt-in; see _refresh_if_stale docstring.

    Precedence: CCB_DISABLE_AUTO_UPDATE=1 (hard off, kept for back-compat)
    > CCB_AUTO_REFRESH env > settings.json "ccb": {"auto_refresh": ...}
    > default False.
    """
    if os.environ.get("CCB_DISABLE_AUTO_UPDATE", "").lower() in {"1", "true", "yes"}:
        return False
    env = os.environ.get("CCB_AUTO_REFRESH", "").lower()
    if env in {"1", "true", "yes"}:
        return True
    if env in {"0", "false", "no"}:
        return False
    import json
    settings = root / ".claude" / "settings.json"
    try:
        data = json.loads(settings.read_text(encoding="utf-8"))
        return bool(data.get("ccb", {}).get("auto_refresh", False))
    except Exception:
        return False


def _is_stale(project_llm: Path, root: Path) -> bool:
    """True if any tracked source file is newer than PROJECT.llm.

    Uses os.walk with onerror so unreadable subtrees (data dirs owned by
    root, fuse mounts that are down, etc.) are skipped, not raised.

    The walk is time-bounded: on slow filesystems (WSL /mnt/c, network
    mounts) an unbounded walk can outlive the hook timeout, so Claude Code
    kills the hook mid-run. Past the budget we assume fresh — a fast session
    start with possibly stale context beats a cancelled hook.
    """
    import os
    import time
    deadline = time.monotonic() + WALK_BUDGET_SECONDS
    try:
        cutoff = project_llm.stat().st_mtime
    except OSError:
        return True
    skip = {".git", ".venv", "venv", "env", "__pycache__", "node_modules",
            "dist", "build", ".eggs", ".local", ".ccb", ".claude"}
    suffixes = (".py", ".ts", ".tsx", ".js", ".jsx", ".go", ".rs")
    for dirpath, dirnames, filenames in os.walk(root, onerror=lambda _e: None):
        if time.monotonic() > deadline:
            return False
        dirnames[:] = [d for d in dirnames if d not in skip and not d.startswith(".")]
        for name in filenames:
            if name.endswith(suffixes):
                try:
                    if (Path(dirpath) / name).stat().st_mtime > cutoff:
                        return True
                except OSError:
                    continue
    return False


if __name__ == "__main__":
    safe_main("session_start", run)
