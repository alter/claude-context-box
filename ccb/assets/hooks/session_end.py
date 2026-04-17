#!/usr/bin/env python3
"""SessionEnd hook: capture a brief session summary into the daily log.

Best-effort — the hook has a short timeout (default 1.5s, configurable via
CLAUDE_CODE_SESSIONEND_HOOKS_TIMEOUT_MS). We do the cheap work here (record
which files changed, append a stub entry) and defer LLM summarization to a
background job that the hook spawns and returns from immediately.
"""
from __future__ import annotations

import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from _lib import (  # noqa: E402
    daily_log_path,
    project_root,
    read_input,
    read_state,
    safe_main,
    write_output,
    write_state,
)


def run() -> None:
    payload = read_input()
    root = project_root()
    state = read_state(root)
    changed = sorted(set(state.get("changed_files", [])))

    git_changes = _git_short_status(root)
    transcript = payload.get("transcript_path") or ""
    last_msg = (payload.get("last_assistant_message") or "").strip()

    log = daily_log_path(root)
    with log.open("a", encoding="utf-8") as fh:
        fh.write(f"\n## session ended {_now_iso()}\n\n")
        if changed:
            fh.write(f"- files touched (PostToolUse hook): {len(changed)}\n")
            for path in changed[:30]:
                fh.write(f"  - `{path}`\n")
            if len(changed) > 30:
                fh.write(f"  - ... and {len(changed) - 30} more\n")
        if git_changes:
            fh.write(f"- git diff (working tree): {len(git_changes)} file(s)\n")
            for line in git_changes[:30]:
                fh.write(f"  - `{line}`\n")
        if transcript:
            fh.write(f"- transcript: `{transcript}`\n")
        if last_msg:
            preview = last_msg.splitlines()[0][:160]
            fh.write(f"- last assistant turn: {preview}\n")

    # Reset the changed-files tracker for the next session.
    state["changed_files"] = []
    state["last_session_end"] = _now_iso()
    write_state(state, root)

    # Spawn a no-op background placeholder. In phase D we'll have it call
    # claude-agent-sdk for a real LLM summary; for now just touch a marker file
    # so we know the slot exists.
    _spawn_background_summary(root, transcript)

    write_output({})


def _spawn_background_summary(root: Path, transcript: str) -> None:
    helper = root / ".claude" / "ccb-engine" / "capture_session.py"
    if not helper.exists():
        return
    try:
        subprocess.Popen(
            [sys.executable, str(helper), transcript],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            stdin=subprocess.DEVNULL,
            start_new_session=True,
            cwd=str(root),
            env={**os.environ, "CCB_INVOKED_BY": "session_end"},
        )
    except Exception:
        pass


def _git_short_status(root: Path) -> list[str]:
    if not (root / ".git").exists():
        return []
    try:
        out = subprocess.run(
            ["git", "status", "--short"],
            cwd=root,
            capture_output=True,
            text=True,
            timeout=2,
        )
        return [line.strip() for line in out.stdout.splitlines() if line.strip()]
    except Exception:
        return []


def _now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


if __name__ == "__main__":
    safe_main("session_end", run)
