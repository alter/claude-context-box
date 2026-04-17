#!/usr/bin/env python3
"""Background session worker.

Spawned by SessionEnd / PreCompact so the slow stuff (incremental context
refresh, LLM summarization) doesn't block the hook timeout.

Reads a handoff JSON file written by the hook:
  {"changed_files": ["src/api/handler.py", ...], "transcript": "..."}

Then:
  1. Runs `update.py --paths <unique parent dirs of changed_files>` to refresh
     PROJECT.llm and the touched CONTEXT.llm files.
  2. Appends a structured entry to .ccb/daily_log/<date>.md with what got
     refreshed (and a transcript pointer).
  3. (phase F) Optionally calls claude-agent-sdk for a real LLM summary.

Failures are swallowed — never propagate back to the user's Claude Code session.
"""
from __future__ import annotations

import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from _lib import now_iso, project_root  # noqa: E402


def main() -> int:
    handoff_path = Path(sys.argv[1]) if len(sys.argv) > 1 else None
    root = project_root()

    payload: dict = {}
    if handoff_path and handoff_path.exists():
        try:
            payload = json.loads(handoff_path.read_text(encoding="utf-8"))
        except Exception:
            payload = {}
        # Consume the handoff — don't leave stale state.
        try:
            handoff_path.unlink()
        except Exception:
            pass

    changed: list[str] = payload.get("changed_files") or []
    transcript: str = payload.get("transcript") or ""

    refreshed = _refresh_contexts(root, changed)

    log_dir = root / ".ccb" / "daily_log"
    log_dir.mkdir(parents=True, exist_ok=True)
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    log = log_dir / f"{today}.md"

    with log.open("a", encoding="utf-8") as fh:
        fh.write(f"\n### background capture {now_iso()}\n")
        if refreshed:
            fh.write(f"- refreshed CONTEXT.llm in {len(refreshed)} dir(s):\n")
            for d in refreshed:
                fh.write(f"  - `{d}`\n")
        elif changed:
            fh.write("- no CONTEXT.llm refresh needed (changes outside source dirs)\n")
        if transcript and Path(transcript).exists():
            size = Path(transcript).stat().st_size
            fh.write(f"- transcript: `{transcript}` ({size} bytes)\n")
        # TODO(phase F): summarize transcript via claude-agent-sdk and append
        # a structured "## decisions" / "## issues" section here.

    return 0


def _refresh_contexts(root: Path, changed_files: list[str]) -> list[str]:
    """Run update.py --paths for unique parent directories of changed files."""
    if not changed_files:
        return []
    parents = sorted({str(Path(f).parent) for f in changed_files if f})
    update_script = root / ".claude" / "ccb-engine" / "update.py"
    if not update_script.exists():
        return []
    try:
        proc = subprocess.run(
            [sys.executable, str(update_script), "--paths", *parents],
            cwd=str(root),
            capture_output=True,
            text=True,
            timeout=60,
        )
        if proc.returncode != 0:
            return []
    except Exception:
        return []
    return parents


if __name__ == "__main__":
    sys.exit(main())
