"""Shared helpers for ccb hook scripts.

Hooks must run on a stock Python 3.10+ install — no third-party imports.
They read JSON from stdin, write JSON to stdout, and exit 0 even on failure
(a crashing hook must never break the user's Claude Code session).
"""
from __future__ import annotations

import json
import os
import sys
import traceback
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def project_root() -> Path:
    """Best-effort root: $CLAUDE_PROJECT_DIR if Claude set it, else cwd."""
    return Path(os.environ.get("CLAUDE_PROJECT_DIR", os.getcwd())).resolve()


def ccb_dir(root: Path | None = None) -> Path:
    """`<project>/.ccb/` — runtime data, gitignored."""
    return (root or project_root()) / ".ccb"


def daily_log_path(root: Path | None = None, day: str | None = None) -> Path:
    day = day or datetime.now(timezone.utc).strftime("%Y-%m-%d")
    p = ccb_dir(root) / "daily_log" / f"{day}.md"
    p.parent.mkdir(parents=True, exist_ok=True)
    return p


def state_path(root: Path | None = None) -> Path:
    p = ccb_dir(root) / "state.json"
    p.parent.mkdir(parents=True, exist_ok=True)
    return p


def errors_path(root: Path | None = None) -> Path:
    p = ccb_dir(root) / "errors.log"
    p.parent.mkdir(parents=True, exist_ok=True)
    return p


def read_state(root: Path | None = None) -> dict[str, Any]:
    p = state_path(root)
    if not p.exists():
        return {}
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return {}


def write_state(state: dict[str, Any], root: Path | None = None) -> None:
    p = state_path(root)
    p.write_text(json.dumps(state, indent=2) + "\n", encoding="utf-8")


def read_input() -> dict[str, Any]:
    """Read Claude Code's hook payload from stdin. Empty payload is fine."""
    try:
        raw = sys.stdin.read()
        if not raw.strip():
            return {}
        return json.loads(raw)
    except Exception:
        return {}


def write_output(payload: dict[str, Any]) -> None:
    """Emit a JSON response on stdout."""
    json.dump(payload, sys.stdout, ensure_ascii=False)
    sys.stdout.write("\n")
    sys.stdout.flush()


def log_error(label: str, exc: BaseException, root: Path | None = None) -> None:
    try:
        with errors_path(root).open("a", encoding="utf-8") as fh:
            fh.write(f"\n--- {datetime.now(timezone.utc).isoformat()} {label} ---\n")
            fh.write("".join(traceback.format_exception(type(exc), exc, exc.__traceback__)))
    except Exception:
        # Last-ditch: never raise from a hook.
        pass


def safe_main(label: str, fn) -> None:
    """Wrap a hook entry point so any exception is logged but not raised."""
    try:
        fn()
    except SystemExit:
        raise
    except BaseException as exc:  # noqa: BLE001
        log_error(label, exc)
        # Always exit 0 — a failed hook must not block Claude Code.
        sys.exit(0)
