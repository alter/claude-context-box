"""Unit tests for install.py — the curl entry point.

install.py lives at repo root (it has to — that's what the curl one-liner
hits) and is structured so its functions are import-able. Tests here mock
out subprocess so they're fast and don't actually clone or pip install.

Network paths and the full venv-creation flow are exercised by the e2e
suite (tests/e2e/run_*.sh). These tests cover the in-process logic that
e2e can't easily inspect.
"""
from __future__ import annotations

import importlib.util
import os
import shutil
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent


@pytest.fixture(scope="module")
def install_module():
    """Load install.py as a module."""
    spec = importlib.util.spec_from_file_location("install", REPO_ROOT / "install.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


# _is_ccb_source ---------------------------------------------------------


def test_is_source_recognizes_ccb_repo_layout(tmp_path: Path, install_module) -> None:
    (tmp_path / "ccb" / "assets" / "claude_md").mkdir(parents=True)
    (tmp_path / "pyproject.toml").write_text('name = "claude-context-box"\n')
    assert install_module._is_ccb_source(tmp_path) is True


def test_is_source_misses_random_dir(tmp_path: Path, install_module) -> None:
    assert install_module._is_ccb_source(tmp_path) is False


def test_is_source_requires_pyproject_marker(tmp_path: Path, install_module) -> None:
    (tmp_path / "ccb" / "assets" / "claude_md").mkdir(parents=True)
    (tmp_path / "pyproject.toml").write_text('name = "some-other-project"\n')
    assert install_module._is_ccb_source(tmp_path) is False


def test_is_source_no_pyproject(tmp_path: Path, install_module) -> None:
    (tmp_path / "ccb" / "assets" / "claude_md").mkdir(parents=True)
    assert install_module._is_ccb_source(tmp_path) is False


# _venv_python_path ------------------------------------------------------


def test_venv_python_path_unix(tmp_path: Path, install_module, monkeypatch) -> None:
    monkeypatch.setattr(install_module.os, "name", "posix")
    p = install_module._venv_python_path(tmp_path / ".claude" / "ccb-venv")
    assert p.parts[-3:] == ("ccb-venv", "bin", "python")


def test_venv_python_path_windows(tmp_path: Path, install_module, monkeypatch) -> None:
    monkeypatch.setattr(install_module.os, "name", "nt")
    p = install_module._venv_python_path(tmp_path / ".claude" / "ccb-venv")
    assert p.parts[-3:] == ("ccb-venv", "Scripts", "python.exe")


# _setup_venv ------------------------------------------------------------


def test_setup_venv_reuses_existing(tmp_path: Path, install_module) -> None:
    """If a working venv is already at .claude/ccb-venv/, reuse it instead of recreating."""
    venv_dir = tmp_path / ".claude" / "ccb-venv"
    bin_dir = venv_dir / "bin"
    bin_dir.mkdir(parents=True)
    fake_python = bin_dir / "python"
    fake_python.write_text("")
    fake_python.chmod(0o755)

    with patch.object(install_module.subprocess, "call") as mock_call:
        result = install_module._setup_venv(tmp_path, force=False)
        # subprocess.call should NOT have been invoked — venv was reused.
        mock_call.assert_not_called()
    assert result == fake_python


def test_setup_venv_force_recreates(tmp_path: Path, install_module) -> None:
    venv_dir = tmp_path / ".claude" / "ccb-venv"
    venv_dir.mkdir(parents=True)
    (venv_dir / "marker.txt").write_text("old")

    def fake_call(args, *a, **kw):
        # Simulate `python -m venv` succeeding by creating bin/python.
        target = Path(args[-1])
        (target / "bin").mkdir(parents=True, exist_ok=True)
        (target / "bin" / "python").touch()
        return 0

    with patch.object(install_module.subprocess, "call", side_effect=fake_call):
        install_module._setup_venv(tmp_path, force=True)

    assert not (venv_dir / "marker.txt").exists(), "force should have wiped the old venv"


def test_setup_venv_creates_when_absent(tmp_path: Path, install_module) -> None:
    def fake_call(args, *a, **kw):
        target = Path(args[-1])
        (target / "bin").mkdir(parents=True, exist_ok=True)
        (target / "bin" / "python").touch()
        return 0

    with patch.object(install_module.subprocess, "call", side_effect=fake_call) as mock_call:
        result = install_module._setup_venv(tmp_path, force=False)
        mock_call.assert_called_once()
    assert result.exists()


def test_setup_venv_exits_on_failure(tmp_path: Path, install_module) -> None:
    with patch.object(install_module.subprocess, "call", return_value=1):
        with pytest.raises(SystemExit):
            install_module._setup_venv(tmp_path, force=False)


# _pip_install_ccb -------------------------------------------------------


def test_pip_install_default_no_extras(tmp_path: Path, install_module, monkeypatch) -> None:
    monkeypatch.delenv("CCB_LLM", raising=False)
    captured = {}

    def fake_run(cmd, capture_output, text):
        captured["cmd"] = cmd
        return type("R", (), {"returncode": 0, "stderr": ""})()

    with patch.object(install_module.subprocess, "run", side_effect=fake_run):
        install_module._pip_install_ccb(tmp_path / "fake_python", tmp_path / "src")

    spec = captured["cmd"][-1]
    assert "[llm]" not in spec, "default install should not include llm extra"


def test_pip_install_with_ccb_llm_env(tmp_path: Path, install_module, monkeypatch) -> None:
    monkeypatch.setenv("CCB_LLM", "1")
    captured = {}

    def fake_run(cmd, capture_output, text):
        captured["cmd"] = cmd
        return type("R", (), {"returncode": 0, "stderr": ""})()

    with patch.object(install_module.subprocess, "run", side_effect=fake_run):
        install_module._pip_install_ccb(tmp_path / "fake_python", tmp_path / "src")

    spec = captured["cmd"][-1]
    assert spec.endswith("[llm]"), f"CCB_LLM=1 should append [llm] extra; got {spec}"


def test_pip_install_exits_on_failure(tmp_path: Path, install_module) -> None:
    fake_result = type("R", (), {"returncode": 1, "stderr": "boom"})()
    with patch.object(install_module.subprocess, "run", return_value=fake_result):
        with pytest.raises(SystemExit):
            install_module._pip_install_ccb(tmp_path / "fake_python", tmp_path / "src")


# _write_shim -------------------------------------------------------------


def test_write_shim_creates_executable(tmp_path: Path, install_module) -> None:
    venv_python = tmp_path / ".claude" / "ccb-venv" / "bin" / "python"
    venv_python.parent.mkdir(parents=True)
    venv_python.touch()

    install_module._write_shim(tmp_path, venv_python)

    shim = tmp_path / ".claude" / "bin" / "ccb"
    assert shim.exists()
    assert shim.stat().st_mode & 0o111, "shim must be executable"
    body = shim.read_text()
    assert "#!/usr/bin/env bash" in body
    assert str(venv_python.parent / "ccb") in body


# _fetch -----------------------------------------------------------------


def test_fetch_uses_git_when_available(tmp_path: Path, install_module) -> None:
    """If git is on PATH and the clone succeeds, _fetch returns the cloned dir."""
    fake_repo = tmp_path / "fake_clone"

    def fake_call(args, *a, **kw):
        if args[0] == "git" and "clone" in args:
            target = Path(args[-1])
            target.mkdir(parents=True)
            (target / "ccb").mkdir()
            (target / "marker.txt").write_text("from-git")
            return 0
        return 1

    with patch.object(install_module.shutil, "which", return_value="/usr/bin/git"):
        with patch.object(install_module.subprocess, "call", side_effect=fake_call):
            result = install_module._fetch(
                "main", tmp_path, "https://example.com/x.git", "https://example.com/tar"
            )
    assert (result / "marker.txt").read_text() == "from-git"


def test_fetch_falls_back_to_tarball_when_git_clone_fails(tmp_path: Path, install_module) -> None:
    """If git clone returns non-zero, _fetch should attempt the tarball download."""
    import io
    import tarfile

    # Build a minimal tarball in-memory.
    buf = io.BytesIO()
    with tarfile.open(fileobj=buf, mode="w:gz") as tar:
        info = tarfile.TarInfo(name="repo-from-tar/marker.txt")
        info.size = len(b"from-tar")
        tar.addfile(info, io.BytesIO(b"from-tar"))
    tarball_bytes = buf.getvalue()

    class FakeResp:
        def __init__(self, data): self._data = data
        def read(self): return self._data
        def __enter__(self): return self
        def __exit__(self, *a): pass

    with patch.object(install_module.shutil, "which", return_value="/usr/bin/git"):
        with patch.object(install_module.subprocess, "call", return_value=1):
            with patch.object(install_module.urllib.request, "urlopen",
                              return_value=FakeResp(tarball_bytes)):
                result = install_module._fetch(
                    "main", tmp_path, "https://example.com/x.git", "https://example.com/tar"
                )
    assert (result / "marker.txt").read_text() == "from-tar"
