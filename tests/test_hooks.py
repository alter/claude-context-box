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


def test_session_start_auto_refresh_when_project_llm_missing(tmp_path: Path) -> None:
    """SessionStart should run update.py synchronously if PROJECT.llm is absent."""
    # Lay out a minimal target that mirrors a real install.
    engine_dst = tmp_path / ".claude" / "ccb-engine"
    engine_dst.mkdir(parents=True)
    engine_src = Path(__file__).parent.parent / "ccb" / "assets" / "engine"
    for f in engine_src.iterdir():
        if f.is_file():
            (engine_dst / f.name).write_bytes(f.read_bytes())

    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "__init__.py").write_text('"""Demo."""\n')
    (tmp_path / "src" / "foo.py").write_text("def bar(): ...\n")

    out = _run_hook("session_start.py", {}, tmp_path)
    assert (tmp_path / "PROJECT.llm").exists(), "session_start should auto-create PROJECT.llm"
    ctx = out["hookSpecificOutput"]["additionalContext"]
    assert "PROJECT.llm" in ctx


def test_session_start_survives_failing_engine_update(tmp_path: Path) -> None:
    """If the synchronous auto-refresh crashes, SessionStart still inject
    whatever PROJECT.llm exists — it must never break the user's session."""
    # Engine script that exits 1 — simulates a buggy update.py
    eng = tmp_path / ".claude" / "ccb-engine"
    eng.mkdir(parents=True)
    (eng / "update.py").write_text(
        "import sys\nsys.stderr.write('simulated crash\\n')\nsys.exit(1)\n"
    )
    # PROJECT.llm exists from a previous good run.
    (tmp_path / "PROJECT.llm").write_text("@project: x\n@stale: yes\n")
    # And a source file newer than PROJECT.llm so _is_stale triggers update.
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "main.py").write_text("def hi(): pass\n")
    import os, time
    time.sleep(0.05)
    os.utime(tmp_path / "src" / "main.py", None)

    out = _run_hook("session_start.py", {}, tmp_path)
    # Hook still injects PROJECT.llm even though update.py failed.
    ctx = out["hookSpecificOutput"]["additionalContext"]
    assert "@project: x" in ctx


def test_session_start_respects_disable_auto_update_env(tmp_path: Path) -> None:
    """CCB_DISABLE_AUTO_UPDATE=1 should skip the synchronous refresh entirely."""
    eng = tmp_path / ".claude" / "ccb-engine"
    eng.mkdir(parents=True)
    marker = tmp_path / "engine_was_called.txt"
    (eng / "update.py").write_text(
        f"from pathlib import Path\nPath({str(marker)!r}).write_text('called')\n"
    )
    (tmp_path / "PROJECT.llm").write_text("@project: y\n")
    # Make a stale source file so the staleness check would fire if not disabled.
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "main.py").write_text("def x(): pass\n")
    import os, time
    time.sleep(0.05)
    os.utime(tmp_path / "src" / "main.py", None)

    proc = subprocess.run(
        [sys.executable, str(HOOKS_DIR / "session_start.py")],
        input="{}",
        text=True,
        capture_output=True,
        env={
            "CLAUDE_PROJECT_DIR": str(tmp_path),
            "CCB_DISABLE_AUTO_UPDATE": "1",
            "PATH": "",
        },
        timeout=5,
    )
    assert proc.returncode == 0
    assert not marker.exists(), "engine update should have been skipped"


def test_pre_compact_writes_summary_to_daily_log(tmp_path: Path) -> None:
    """PreCompact should snapshot session state into the daily log so early-
    session decisions don't evaporate during context compaction."""
    state = tmp_path / ".ccb" / "state.json"
    state.parent.mkdir(parents=True)
    state.write_text(json.dumps({"changed_files": ["src/auth.py", "src/db.py"]}))

    out = _run_hook(
        "pre_compact.py",
        {"transcript_path": "/tmp/x", "last_assistant_message": "halfway through refactor"},
        tmp_path,
    )

    assert out == {}
    logs = list((tmp_path / ".ccb" / "daily_log").glob("*.md"))
    assert len(logs) == 1
    body = logs[0].read_text()
    assert "src/auth.py" in body
    assert "src/db.py" in body
    assert "halfway through refactor" in body


def test_session_end_writes_handoff_and_spawns_worker(tmp_path: Path) -> None:
    """SessionEnd records changed files via a handoff JSON for the background worker."""
    state = tmp_path / ".ccb" / "state.json"
    state.parent.mkdir(parents=True)
    state.write_text(json.dumps({"changed_files": ["src/api/handler.py"]}))

    # Provide a fake worker that records its argv into a marker file so we can
    # verify SessionEnd actually invoked it with the handoff path.
    engine_dir = tmp_path / ".claude" / "ccb-engine"
    engine_dir.mkdir(parents=True)
    marker = tmp_path / "worker-was-called.txt"
    (engine_dir / "capture_session.py").write_text(
        "import sys, pathlib\n"
        f"pathlib.Path(r'{marker}').write_text('|'.join(sys.argv[1:]))\n"
    )

    _run_hook(
        "session_end.py",
        {"transcript_path": "/tmp/x", "last_assistant_message": "done"},
        tmp_path,
    )

    # Background spawn is async — give it a moment to write the marker.
    import time
    deadline = time.time() + 2
    while not marker.exists() and time.time() < deadline:
        time.sleep(0.05)
    assert marker.exists(), "SessionEnd did not spawn the background worker"
    handoff_path = marker.read_text()
    # The handoff file is consumed by the worker, but the path passed in must
    # have pointed at .ccb/handoff.json.
    assert ".ccb" in handoff_path and "handoff.json" in handoff_path


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
