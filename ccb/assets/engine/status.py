#!/usr/bin/env python3
"""Report on ccb installation health in the current project."""
from __future__ import annotations

import json
import re
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from _lib import IGNORED_DIRS, SOURCE_SUFFIXES, project_root, safe_iterdir  # noqa: E402


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
    _line(".ccb/errors.log", _check_errors(root))
    _line("CONTEXT.llm coverage", _check_context_coverage(root))
    _line("memory structure", _check_memory(root))
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


def _check_errors(root: Path) -> str:
    p = root / ".ccb" / "errors.log"
    if not p.exists():
        return "no errors recorded"
    try:
        text = p.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return "present but unreadable"
    headers = re.findall(r"^---\s+(\S+)\s+(\S+)\s+---$", text, flags=re.MULTILINE)
    if not headers:
        return f"present ({p.stat().st_size} bytes, no parseable entries)"
    last_ts, last_label = headers[-1]
    return f"{len(headers)} hook error(s); latest: {last_ts} ({last_label})"


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
    """Walk the tree once with os.walk so unreadable subtrees are skipped, not raised.

    Counts directories containing ANY language ccb knows about — not just
    Python. Mirrors the source-file detection used by update.py /
    iter_code_dirs so coverage figures match what /ccb-update actually walked.
    """
    import os
    code_dirs: list[Path] = []
    for dirpath, dirnames, filenames in os.walk(root, onerror=lambda _e: None):
        dirnames[:] = [d for d in dirnames if d not in IGNORED_DIRS and not d.startswith(".")]
        d = Path(dirpath)
        if d == root:
            continue
        if any(name.endswith(SOURCE_SUFFIXES) for name in filenames):
            code_dirs.append(d)
    with_ctx = sum(1 for d in code_dirs if (d / "CONTEXT.llm").exists())
    if not code_dirs:
        return "no code directories"
    pct = int(100 * with_ctx / len(code_dirs))
    return f"{with_ctx}/{len(code_dirs)} dirs ({pct}%)"


def _check_memory(root: Path) -> str:
    """Health of the memory/ structure (scaffolded by /ccb-memory init).

    Key files accept alternates: current-task.md is the 0.8+ name of the
    pre-0.8 current-experiment.md, and tasks/ of experiments/.
    """
    key = (
        ("INDEX.md",),
        ("memory/validation-protocol.md",),
        ("memory/current-task.md", "memory/current-experiment.md"),
        ("memory/decisions-log.md",),
    )
    present = [alts[0] for alts in key if any((root / a).exists() for a in alts)]
    if not present:
        return "not initialized (optional — /ccb-memory init)"
    troot = root / "memory" / "tasks"
    if not troot.is_dir():
        troot = root / "memory" / "experiments"
    tasks = [d for d in safe_iterdir(troot) if d.is_dir()] if troot.is_dir() else []
    runs = sum(1 for t in tasks for r in safe_iterdir(t) if r.is_dir())
    report = f"{len(present)}/{len(key)} key files, {len(tasks)} task(s), {runs} run(s)"
    missing = [alts[0] for alts in key if not any((root / a).exists() for a in alts)]
    if missing:
        report += f"; missing: {', '.join(missing)}"
    return report


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
