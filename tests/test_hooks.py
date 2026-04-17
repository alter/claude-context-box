"""Tests for ccb lifecycle hooks.

Hooks live under ccb/assets/hooks/ and are not part of the importable ccb
package, so they're invoked as subprocesses with stdin/stdout JSON, the same
way Claude Code calls them.
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

HOOKS_DIR = Path(__file__).parent.parent / "ccb" / "assets" / "hooks"


def _run_hook(name: str, payload: dict | None, project_dir: Path) -> dict:
    """Invoke a hook script as Claude Code would; return its parsed stdout."""
    proc = subprocess.run(
        [sys.executable, str(HOOKS_DIR / name)],
        input=json.dumps(payload or {}),
        text=True,
        capture_output=True,
        env={"CLAUDE_PROJECT_DIR": str(project_dir), "PATH": ""},
        timeout=5,
    )
    assert proc.returncode == 0, f"hook crashed: {proc.stderr}"
    return json.loads(proc.stdout) if proc.stdout.strip() else {}


# session_start ----------------------------------------------------------


def test_session_start_silent_when_no_context(tmp_path: Path) -> None:
    out = _run_hook("session_start.py", {}, tmp_path)
    assert out == {}


def test_session_start_includes_project_llm(tmp_path: Path) -> None:
    (tmp_path / "PROJECT.llm").write_text("@project: foo\n@version: 1.0\n")
    out = _run_hook("session_start.py", {}, tmp_path)
    ctx = out["hookSpecificOutput"]["additionalContext"]
    assert "@project: foo" in ctx
    assert "PROJECT.llm" in ctx


def test_session_start_includes_latest_daily_log(tmp_path: Path) -> None:
    log_dir = tmp_path / ".ccb" / "daily_log"
    log_dir.mkdir(parents=True)
    (log_dir / "2026-01-01.md").write_text("# old log\n")
    (log_dir / "2026-04-17.md").write_text("# latest log\ndecision: use SQLite\n")
    out = _run_hook("session_start.py", {}, tmp_path)
    ctx = out["hookSpecificOutput"]["additionalContext"]
    assert "use SQLite" in ctx
    assert "old log" not in ctx  # only the latest log is injected


# post_tool_use ----------------------------------------------------------


def test_post_tool_use_records_edit(tmp_path: Path) -> None:
    target = tmp_path / "src" / "foo.py"
    target.parent.mkdir(parents=True)
    target.write_text("x")
    _run_hook(
        "post_tool_use.py",
        {"tool_name": "Edit", "tool_input": {"file_path": str(target)}},
        tmp_path,
    )
    state = json.loads((tmp_path / ".ccb" / "state.json").read_text())
    assert state["changed_files"] == ["src/foo.py"]


def test_post_tool_use_ignores_read(tmp_path: Path) -> None:
    _run_hook(
        "post_tool_use.py",
        {"tool_name": "Read", "tool_input": {"file_path": "/tmp/x"}},
        tmp_path,
    )
    assert not (tmp_path / ".ccb" / "state.json").exists()


def test_post_tool_use_dedupes(tmp_path: Path) -> None:
    target = tmp_path / "a.py"
    target.write_text("x")
    for _ in range(3):
        _run_hook(
            "post_tool_use.py",
            {"tool_name": "Write", "tool_input": {"file_path": str(target)}},
            tmp_path,
        )
    state = json.loads((tmp_path / ".ccb" / "state.json").read_text())
    assert state["changed_files"] == ["a.py"]


# session_end ------------------------------------------------------------


def test_session_end_drains_state_into_daily_log(tmp_path: Path) -> None:
    state_file = tmp_path / ".ccb" / "state.json"
    state_file.parent.mkdir(parents=True)
    state_file.write_text(json.dumps({"changed_files": ["a.py", "b.py"]}))

    _run_hook(
        "session_end.py",
        {"transcript_path": "/tmp/fake.jsonl", "last_assistant_message": "shipped feature X"},
        tmp_path,
    )

    logs = list((tmp_path / ".ccb" / "daily_log").glob("*.md"))
    assert len(logs) == 1
    body = logs[0].read_text()
    assert "a.py" in body
    assert "b.py" in body
    assert "shipped feature X" in body

    new_state = json.loads(state_file.read_text())
    assert new_state["changed_files"] == []
    assert "last_session_end" in new_state


# instructions_loaded ---------------------------------------------------


def test_instructions_loaded_warns_when_project_llm_missing(tmp_path: Path) -> None:
    out = _run_hook("instructions_loaded.py", {}, tmp_path)
    assert "PROJECT.llm is missing" in out["systemMessage"]


def test_instructions_loaded_silent_when_fresh(tmp_path: Path) -> None:
    (tmp_path / "PROJECT.llm").write_text("@project: foo\n")
    out = _run_hook("instructions_loaded.py", {}, tmp_path)
    assert out == {}


# safety net -------------------------------------------------------------


@pytest.mark.parametrize(
    "hook",
    ["session_start.py", "session_end.py", "pre_compact.py", "post_tool_use.py", "instructions_loaded.py"],
)
def test_hook_survives_malformed_input(hook: str, tmp_path: Path) -> None:
    """A hook must never crash Claude Code, even given garbage input."""
    proc = subprocess.run(
        [sys.executable, str(HOOKS_DIR / hook)],
        input="this is not json",
        text=True,
        capture_output=True,
        env={"CLAUDE_PROJECT_DIR": str(tmp_path), "PATH": ""},
        timeout=5,
    )
    assert proc.returncode == 0
