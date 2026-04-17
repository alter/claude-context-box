#!/usr/bin/env python3
"""Report on ccb installation health in the current project."""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from _lib import IGNORED_DIRS, project_root, safe_iterdir  # noqa: E402


def main() -> int:
    root = project_root()
    print(f"ccb status: {root}")

    _line("CLAUDE.md", _check_claude_md(root))
    _line("PROJECT.llm", _check_project_llm(root))
    _line(".claude/settings.json", _check_settings(root))
    _line(".claude/hooks/", _check_hooks(root))
    _line(".claude/skills/", _check_skills(root))
    _line(".ccb/daily_log/", _check_daily_log(root))
    _line(".ccb/state.json", _check_state(root))
    _line("CONTEXT.llm coverage", _check_context_coverage(root))
    return 0


def _line(label: str, value: str) -> None:
    print(f"  {label:<28} {value}")


def _check_claude_md(root: Path) -> str:
    p = root / "CLAUDE.md"
    if not p.exists():
        return "missing"
    text = p.read_text(encoding="utf-8", errors="ignore")
    has_block = "<!-- ccb:begin -->" in text and "<!-- ccb:end -->" in text
    return f"present ({len(text)} bytes, ccb block: {'yes' if has_block else 'NO'})"


def _check_project_llm(root: Path) -> str:
    p = root / "PROJECT.llm"
    if not p.exists():
        return "missing — run /ccb-update"
    age = int(time.time() - p.stat().st_mtime)
    return f"present ({_human_age(age)} old)"


def _check_settings(root: Path) -> str:
    p = root / ".claude" / "settings.json"
    if not p.exists():
        return "missing"
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return "present but invalid JSON"
    hooks = data.get("hooks") or {}
    ccb_hooks = sum(
        1
        for events in hooks.values()
        if isinstance(events, list)
        for entry in events
        if isinstance(entry, dict) and entry.get("_ccb")
    )
    return f"present ({ccb_hooks} ccb hook(s) registered)"


def _check_hooks(root: Path) -> str:
    d = root / ".claude" / "hooks"
    if not d.is_dir():
        return "missing"
    py = sorted(p.name for p in d.glob("*.py") if not p.name.startswith("_"))
    return f"{len(py)} script(s): {', '.join(py)}" if py else "empty"


def _check_skills(root: Path) -> str:
    d = root / ".claude" / "skills"
    if not d.is_dir():
        return "missing"
    skills = sorted(p.name for p in d.iterdir() if p.is_dir())
    return f"{len(skills)} skill(s): {', '.join(skills)}" if skills else "empty"


def _check_daily_log(root: Path) -> str:
    d = root / ".ccb" / "daily_log"
    if not d.is_dir():
        return "missing (not yet captured)"
    logs = sorted(d.glob("*.md"))
    if not logs:
        return "empty"
    return f"{len(logs)} entries, latest: {logs[-1].name}"


def _check_state(root: Path) -> str:
    p = root / ".ccb" / "state.json"
    if not p.exists():
        return "missing (no edits tracked yet)"
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return "present but invalid JSON"
    pending = len(data.get("changed_files") or [])
    return f"{pending} pending change(s)"


def _check_context_coverage(root: Path) -> str:
    """Walk the tree once with os.walk so unreadable subtrees are skipped, not raised."""
    import os
    code_dirs: list[Path] = []
    for dirpath, dirnames, filenames in os.walk(root, onerror=lambda _e: None):
        # prune ignored / hidden subtrees in-place
        dirnames[:] = [d for d in dirnames if d not in IGNORED_DIRS and not d.startswith(".")]
        d = Path(dirpath)
        if d == root:
            continue
        if any(name.endswith(".py") for name in filenames):
            code_dirs.append(d)
    with_ctx = sum(1 for d in code_dirs if (d / "CONTEXT.llm").exists())
    if not code_dirs:
        return "no code directories"
    pct = int(100 * with_ctx / len(code_dirs))
    return f"{with_ctx}/{len(code_dirs)} dirs ({pct}%)"


def _human_age(seconds: int) -> str:
    if seconds < 60:
        return f"{seconds}s"
    if seconds < 3600:
        return f"{seconds // 60}m"
    if seconds < 86400:
        return f"{seconds // 3600}h"
    return f"{seconds // 86400}d"


if __name__ == "__main__":
    sys.exit(main())
