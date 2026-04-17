#!/usr/bin/env python3
"""PreCompact hook: snapshot the current session before the context is compressed.

Mirrors session_end so decisions made early in a long session survive the
auto-compaction summarization that would otherwise drop them.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from _lib import safe_main  # noqa: E402

# Reuse session_end's logic — same output format, same daily log.
from session_end import run as _session_end_run  # noqa: E402


if __name__ == "__main__":
    safe_main("pre_compact", _session_end_run)
