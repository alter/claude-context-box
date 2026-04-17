#!/usr/bin/env python3
"""InstructionsLoaded hook: warn if PROJECT.llm is stale at the start of a session."""
from __future__ import annotations

import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from _lib import project_root, read_input, safe_main, write_output  # noqa: E402

STALE_AFTER_SECONDS = 7 * 24 * 3600  # 7 days


def run() -> None:
    read_input()
    root = project_root()
    p = root / "PROJECT.llm"
    if not p.exists():
        write_output(
            {
                "systemMessage": (
                    "PROJECT.llm is missing. Run /ccb-update to generate it from the "
                    "current source tree."
                )
            }
        )
        return

    age = time.time() - p.stat().st_mtime
    if age > STALE_AFTER_SECONDS:
        days = int(age // 86400)
        write_output(
            {
                "systemMessage": (
                    f"PROJECT.llm is {days} days old. Consider running /ccb-update."
                )
            }
        )
        return

    write_output({})


if __name__ == "__main__":
    safe_main("instructions_loaded", run)
