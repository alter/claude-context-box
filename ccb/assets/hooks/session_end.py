#!/usr/bin/env python3
"""SessionEnd hook: capture a brief session summary into the daily log.

Best-effort — the hook has a short timeout (default 1.5s, configurable via
CLAUDE_CODE_SESSIONEND_HOOKS_TIMEOUT_MS). We do the cheap work here (record
which files changed, append a log entry) and defer two slower jobs to a
background process that the hook spawns and returns from immediately:

  1. Incremental context refresh: update.py --paths <changed dirs>
  2. (phase F) LLM summary of the transcript via claude-agent-sdk

The background process gets the list of changed files via a one-shot file
written before state.json is reset.
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

    # Hand the changed-files list to the background worker via a one-shot
    # file (so it survives the state.json reset below).
    handoff = root / ".ccb" / "handoff.json"
    handoff.parent.mkdir(parents=True, exist_ok=True)
    import json as _json
    handoff.write_text(
        _json.dumps({"changed_files": changed, "transcript": transcript}),
        encoding="utf-8",
    )

    # Reset the changed-files tracker for the next session.
    state["changed_files"] = []
    state["last_session_end"] = _now_iso()
    write_state(state, root)

    # Spawn the worker: incremental context refresh + (phase F) LLM summary.
    _spawn_background_worker(root, handoff)

    write_output({})


def _spawn_background_worker(root: Path, handoff: Path) -> None:
    helper = root / ".claude" / "ccb-engine" / "capture_session.py"
    if not helper.exists():
        return
    try:
        subprocess.Popen(
            [sys.executable, str(helper), str(handoff)],
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
