"""Tests for ccb engine scripts (update / status / validate / cleancode).

Engine scripts live under ccb/assets/engine/ and run in the *target* project.
We invoke them as subprocesses with CLAUDE_PROJECT_DIR pointing at a fixture.
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path
from textwrap import dedent

import pytest

ENGINE_DIR = Path(__file__).parent.parent / "ccb" / "assets" / "engine"


def _run(script: str, project_dir: Path) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(ENGINE_DIR / script)],
        capture_output=True,
        text=True,
        env={"CLAUDE_PROJECT_DIR": str(project_dir), "PATH": ""},
        timeout=10,
    )


def _make_project(root: Path) -> None:
    """Build a small but realistic Python project under `root`."""
    (root / "pyproject.toml").write_text('[project]\nname = "demo"\nversion = "0.1.0"\n')
    (root / "src" / "api").mkdir(parents=True)
    (root / "src" / "db").mkdir(parents=True)
    (root / "src" / "__init__.py").write_text("")
    (root / "src" / "api" / "__init__.py").write_text('"""HTTP layer."""\n')
    (root / "src" / "api" / "handler.py").write_text(
        dedent(
            '''\
            """Public request handlers."""
            from src.db.models import User

            def create_user(name: str) -> User:
                return User(name=name)

            class Router:
                def add(self, path: str, fn) -> None: ...
            '''
        )
    )
    (root / "src" / "db" / "__init__.py").write_text('"""Persistence."""\n')
    (root / "src" / "db" / "models.py").write_text(
        dedent(
            '''\
            """Domain models."""
            class User:
                def __init__(self, name: str) -> None:
                    self.name = name
            '''
        )
    )


# update.py --------------------------------------------------------------


def test_update_writes_project_llm(tmp_path: Path) -> None:
    _make_project(tmp_path)
    proc = _run("update.py", tmp_path)
    assert proc.returncode == 0, proc.stderr
    p = tmp_path / "PROJECT.llm"
    assert p.exists()
    text = p.read_text()
    assert "@project: " in text
    assert "@language: python" in text
    assert "@package_manager: pip" in text
    assert "@architecture:" in text
    assert "src/" in text


def test_update_writes_context_per_module(tmp_path: Path) -> None:
    _make_project(tmp_path)
    _run("update.py", tmp_path)
    api_ctx = tmp_path / "src" / "api" / "CONTEXT.llm"
    db_ctx = tmp_path / "src" / "db" / "CONTEXT.llm"
    assert api_ctx.exists()
    assert db_ctx.exists()


def test_update_extracts_python_exports(tmp_path: Path) -> None:
    _make_project(tmp_path)
    _run("update.py", tmp_path)
    api_ctx = (tmp_path / "src" / "api" / "CONTEXT.llm").read_text()
    assert "class Router" in api_ctx
    assert "def create_user" in api_ctx
    # __init__.py docstring wins over individual file docstrings for @purpose
    assert "HTTP layer." in api_ctx


def test_update_uses_module_docstring_as_purpose(tmp_path: Path) -> None:
    _make_project(tmp_path)
    _run("update.py", tmp_path)
    db_ctx = (tmp_path / "src" / "db" / "CONTEXT.llm").read_text()
    assert "@purpose: Persistence." in db_ctx


def test_update_skips_ignored_dirs(tmp_path: Path) -> None:
    _make_project(tmp_path)
    (tmp_path / ".venv" / "lib").mkdir(parents=True)
    (tmp_path / ".venv" / "lib" / "junk.py").write_text("def x(): ...\n")
    (tmp_path / "node_modules" / "foo").mkdir(parents=True)
    (tmp_path / "node_modules" / "foo" / "bar.js").write_text("export const x = 1;\n")
    _run("update.py", tmp_path)
    assert not (tmp_path / ".venv" / "lib" / "CONTEXT.llm").exists()
    assert not (tmp_path / "node_modules" / "foo" / "CONTEXT.llm").exists()


def test_update_is_idempotent(tmp_path: Path) -> None:
    _make_project(tmp_path)
    _run("update.py", tmp_path)
    first = (tmp_path / "src" / "api" / "CONTEXT.llm").read_text()
    # Strip @updated stamps for comparison
    _run("update.py", tmp_path)
    second = (tmp_path / "src" / "api" / "CONTEXT.llm").read_text()
    first_lines = [l for l in first.splitlines() if not l.startswith("@updated")]
    second_lines = [l for l in second.splitlines() if not l.startswith("@updated")]
    assert first_lines == second_lines


# status.py --------------------------------------------------------------


def test_status_runs_on_empty_project(tmp_path: Path) -> None:
    proc = _run("status.py", tmp_path)
    assert proc.returncode == 0
    assert "missing" in proc.stdout  # nothing installed yet


def test_status_reports_after_update(tmp_path: Path) -> None:
    _make_project(tmp_path)
    _run("update.py", tmp_path)
    proc = _run("status.py", tmp_path)
    assert "PROJECT.llm" in proc.stdout
    assert "present" in proc.stdout
    assert ".ccb/errors.log" in proc.stdout
    assert "no errors recorded" in proc.stdout


def test_status_surfaces_hook_errors(tmp_path: Path) -> None:
    """When a hook has crashed and written to .ccb/errors.log, status must
    report the count and timestamp so the user notices silent failures."""
    _make_project(tmp_path)
    _run("update.py", tmp_path)
    errors = tmp_path / ".ccb" / "errors.log"
    errors.parent.mkdir(parents=True, exist_ok=True)
    errors.write_text(
        "\n--- 2026-04-17T15:23:11Z session_start ---\n"
        "Traceback (most recent call last):\n"
        '  File "session_start.py", line 42, in run\n'
        "RuntimeError: simulated\n"
        "\n--- 2026-04-17T16:01:02Z post_tool_use ---\n"
        "Traceback (most recent call last):\n"
        "ValueError: another simulated failure\n"
    )
    proc = _run("status.py", tmp_path)
    assert proc.returncode == 0
    assert "2 hook error(s)" in proc.stdout
    assert "2026-04-17T16:01:02Z" in proc.stdout
    assert "post_tool_use" in proc.stdout


# validate.py ------------------------------------------------------------


def test_validate_clean_after_update(tmp_path: Path) -> None:
    _make_project(tmp_path)
    _run("update.py", tmp_path)
    proc = _run("validate.py", tmp_path)
    assert proc.returncode == 0
    assert "no issues" in proc.stdout


def test_validate_warns_on_missing_context(tmp_path: Path) -> None:
    _make_project(tmp_path)
    _run("update.py", tmp_path)
    # Add a new module without CONTEXT.llm
    (tmp_path / "src" / "auth").mkdir()
    (tmp_path / "src" / "auth" / "__init__.py").write_text('')
    (tmp_path / "src" / "auth" / "login.py").write_text('def login(): ...\n')
    proc = _run("validate.py", tmp_path)
    assert "missing CONTEXT.llm" in proc.stdout
    assert "src/auth" in proc.stdout


def test_validate_errors_when_project_llm_missing(tmp_path: Path) -> None:
    _make_project(tmp_path)
    proc = _run("validate.py", tmp_path)
    assert proc.returncode == 1
    assert "PROJECT.llm missing" in proc.stdout


# cleancode.py -----------------------------------------------------------


def test_update_paths_flag_only_touches_listed_dirs(tmp_path: Path) -> None:
    _make_project(tmp_path)
    _run("update.py", tmp_path)

    # Capture mtimes after the full refresh.
    api_ctx = tmp_path / "src" / "api" / "CONTEXT.llm"
    db_ctx = tmp_path / "src" / "db" / "CONTEXT.llm"
    api_mtime = api_ctx.stat().st_mtime
    db_mtime = db_ctx.stat().st_mtime

    # Force a discernible mtime gap, then incremental-refresh only src/api/.
    import os, time
    time.sleep(0.05)
    proc = subprocess.run(
        [sys.executable, str(ENGINE_DIR / "update.py"),
         "--paths", str(tmp_path / "src" / "api")],
        capture_output=True,
        text=True,
        env={"CLAUDE_PROJECT_DIR": str(tmp_path), "PATH": ""},
        timeout=10,
    )
    assert proc.returncode == 0, proc.stderr

    assert api_ctx.stat().st_mtime > api_mtime, "src/api CONTEXT.llm should be refreshed"
    assert db_ctx.stat().st_mtime == db_mtime, "src/db CONTEXT.llm should NOT be refreshed"


def test_update_paths_accepts_files_and_resolves_to_parent(tmp_path: Path) -> None:
    _make_project(tmp_path)
    _run("update.py", tmp_path)

    api_ctx = tmp_path / "src" / "api" / "CONTEXT.llm"
    api_ctx.unlink()
    proc = subprocess.run(
        [sys.executable, str(ENGINE_DIR / "update.py"),
         "--paths", str(tmp_path / "src" / "api" / "handler.py")],
        capture_output=True,
        text=True,
        env={"CLAUDE_PROJECT_DIR": str(tmp_path), "PATH": ""},
        timeout=10,
    )
    assert proc.returncode == 0, proc.stderr
    assert api_ctx.exists(), "passing a file path should refresh its parent dir"


def test_cleancode_finds_unreferenced_function(tmp_path: Path) -> None:
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "__init__.py").write_text("")
    (tmp_path / "src" / "live.py").write_text(
        "from src.lib import used\n"
        "def main(): used()\n"
    )
    (tmp_path / "src" / "lib.py").write_text(
        "def used(): pass\n"
        "def orphaned(): pass\n"
    )
    proc = _run("cleancode.py", tmp_path)
    assert "orphaned" in proc.stdout
    assert "used" not in proc.stdout.split("orphaned")[0]  # `used` not flagged
