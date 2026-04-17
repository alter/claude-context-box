#!/usr/bin/env python3
"""Background session-summary worker.

Spawned by the SessionEnd / PreCompact hook so summarization doesn't block the
hook timeout. For now it appends a minimal record to the daily log; phase D
upgrades it to call claude-agent-sdk for an LLM summary of the transcript.
"""
from __future__ import annotations

import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from _lib import now_iso, project_root  # noqa: E402


def main() -> int:
    transcript_path = sys.argv[1] if len(sys.argv) > 1 else ""
    root = project_root()

    log_dir = root / ".ccb" / "daily_log"
    log_dir.mkdir(parents=True, exist_ok=True)
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    log = log_dir / f"{today}.md"

    with log.open("a", encoding="utf-8") as fh:
        fh.write(f"\n### background capture {now_iso()}\n")
        if transcript_path and Path(transcript_path).exists():
            size = Path(transcript_path).stat().st_size
            fh.write(f"- transcript: `{transcript_path}` ({size} bytes)\n")
            # TODO(phase D): summarize via claude-agent-sdk and write structured
            # decisions/issues sections here.
        else:
            fh.write("- no transcript available\n")

    return 0


if __name__ == "__main__":
    sys.exit(main())
