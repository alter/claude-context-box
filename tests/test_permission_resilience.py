"""Engine and hooks must never crash on unreadable directories.

Real projects often contain data dirs / fuse mounts / docker volumes that
the developer's user can't read (chmod 000, mounted root-owned, etc).
These tests put such a dir inside a fixture project and assert that every
script that scans the tree completes successfully.

Skipped on Windows (chmod 0 doesn't deny iterdir there) and when running
as root (which can read regardless of mode).
"""
from __future__ import annotations

import json
import os
import stat
import subprocess
import sys
from pathlib import Path

import pytest

ENGINE_DIR = Path(__file__).parent.parent / "ccb" / "assets" / "engine"
HOOKS_DIR = Path(__file__).parent.parent / "ccb" / "assets" / "hooks"

requires_perms = pytest.mark.skipif(
    sys.platform == "win32" or os.geteuid() == 0,
    reason="permission denial requires non-root POSIX",
)


@pytest.fixture
def project_with_unreadable_dir(tmp_path: Path):
    """A python project containing a chmod-000 subdir."""
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "__init__.py").write_text('"""src"""\n')
    (tmp_path / "src" / "main.py").write_text("def run(): ...\n")
    (tmp_path / "data").mkdir()
    locked = tmp_path / "data" / "timescale"
    locked.mkdir()
    (locked / "secret.bin").write_text("can't read me")
    locked.chmod(0)
    yield tmp_path
    # Restore mode so pytest can clean up.
    locked.chmod(stat.S_IRWXU)


def _run_engine(script: str, project_dir: Path, *, args: list[str] | None = None) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(ENGINE_DIR / script), *(args or [])],
        capture_output=True,
        text=True,
        env={"CLAUDE_PROJECT_DIR": str(project_dir), "PATH": ""},
        timeout=15,
    )


def _run_hook(script: str, project_dir: Path, *, payload: dict | None = None) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(HOOKS_DIR / script)],
        input=json.dumps(payload or {}),
        text=True,
        capture_output=True,
        env={"CLAUDE_PROJECT_DIR": str(project_dir), "PATH": ""},
        timeout=10,
    )


# ---- engine ----------------------------------------------------------------


@requires_perms
def test_update_survives_unreadable_dir(project_with_unreadable_dir: Path) -> None:
    proc = _run_engine("update.py", project_with_unreadable_dir)
    assert proc.returncode == 0, f"update.py failed:\n{proc.stderr}"
    assert (project_with_unreadable_dir / "PROJECT.llm").exists()


@requires_perms
def test_status_survives_unreadable_dir(project_with_unreadable_dir: Path) -> None:
    _run_engine("update.py", project_with_unreadable_dir)
    proc = _run_engine("status.py", project_with_unreadable_dir)
    assert proc.returncode == 0, f"status.py failed:\n{proc.stderr}"
    assert "Traceback" not in proc.stdout
    assert "Traceback" not in proc.stderr
    assert "CONTEXT.llm coverage" in proc.stdout


@requires_perms
def test_validate_survives_unreadable_dir(project_with_unreadable_dir: Path) -> None:
    _run_engine("update.py", project_with_unreadable_dir)
    proc = _run_engine("validate.py", project_with_unreadable_dir)
    assert proc.returncode == 0, f"validate.py failed:\n{proc.stderr}"
    assert "Traceback" not in proc.stdout


@requires_perms
def test_cleancode_survives_unreadable_dir(project_with_unreadable_dir: Path) -> None:
    proc = _run_engine("cleancode.py", project_with_unreadable_dir)
    assert proc.returncode == 0, f"cleancode.py failed:\n{proc.stderr}"
    assert "Traceback" not in proc.stdout


# ---- hooks -----------------------------------------------------------------


@requires_perms
def test_session_start_survives_unreadable_dir(project_with_unreadable_dir: Path) -> None:
    """SessionStart's _is_stale walks the tree to check freshness."""
    # Engine must be installed for the sync auto-update branch to run.
    eng = project_with_unreadable_dir / ".claude" / "ccb-engine"
    eng.mkdir(parents=True)
    for f in ENGINE_DIR.iterdir():
        if f.is_file():
            (eng / f.name).write_bytes(f.read_bytes())
    proc = _run_hook("session_start.py", project_with_unreadable_dir)
    assert proc.returncode == 0, f"session_start.py failed:\n{proc.stderr}"
