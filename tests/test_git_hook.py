"""Tests for the optional ccb git pre-commit hook installer."""
from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from ccb.installer.git_hook import CCB_MARKER, install, uninstall


def _make_git_repo(tmp_path: Path) -> Path:
    subprocess.check_call(["git", "init", "-q", str(tmp_path)])
    return tmp_path


def test_install_creates_hook_in_fresh_repo(tmp_path: Path, capsys) -> None:
    _make_git_repo(tmp_path)
    rc = install(tmp_path)
    assert rc == 0
    hook = tmp_path / ".git" / "hooks" / "pre-commit"
    assert hook.exists()
    assert hook.stat().st_mode & 0o111  # executable
    body = hook.read_text()
    assert CCB_MARKER in body


def test_install_refuses_non_git_dir(tmp_path: Path, capsys) -> None:
    rc = install(tmp_path)
    assert rc == 1
    assert "not a git repo" in capsys.readouterr().out


def test_install_refuses_to_overwrite_existing_hook(tmp_path: Path, capsys) -> None:
    _make_git_repo(tmp_path)
    hook = tmp_path / ".git" / "hooks" / "pre-commit"
    hook.write_text("#!/bin/sh\n# user's own hook\nexit 0\n")
    hook.chmod(0o755)

    rc = install(tmp_path)
    assert rc == 1
    out = capsys.readouterr().out
    assert "refusing to overwrite" in out
    assert "user's own hook" in hook.read_text()


def test_install_refreshes_existing_ccb_hook(tmp_path: Path) -> None:
    _make_git_repo(tmp_path)
    install(tmp_path)
    install(tmp_path)  # second call — should not require --force
    hook = tmp_path / ".git" / "hooks" / "pre-commit"
    assert CCB_MARKER in hook.read_text()


def test_install_force_overwrites_alien_hook(tmp_path: Path) -> None:
    _make_git_repo(tmp_path)
    hook = tmp_path / ".git" / "hooks" / "pre-commit"
    hook.write_text("#!/bin/sh\n# alien hook\nexit 0\n")
    hook.chmod(0o755)
    rc = install(tmp_path, force=True)
    assert rc == 0
    assert CCB_MARKER in hook.read_text()


def test_install_yields_to_pre_commit_framework(tmp_path: Path, capsys) -> None:
    _make_git_repo(tmp_path)
    (tmp_path / ".pre-commit-config.yaml").write_text("repos: []\n")
    rc = install(tmp_path)
    assert rc == 0
    out = capsys.readouterr().out
    assert "pre-commit framework" in out
    assert not (tmp_path / ".git" / "hooks" / "pre-commit").exists()


def test_uninstall_removes_only_ccb_hook(tmp_path: Path) -> None:
    _make_git_repo(tmp_path)
    install(tmp_path)
    rc = uninstall(tmp_path)
    assert rc == 0
    assert not (tmp_path / ".git" / "hooks" / "pre-commit").exists()


def test_uninstall_leaves_user_hook_alone(tmp_path: Path, capsys) -> None:
    _make_git_repo(tmp_path)
    hook = tmp_path / ".git" / "hooks" / "pre-commit"
    hook.write_text("#!/bin/sh\nexit 0\n")
    rc = uninstall(tmp_path)
    assert rc == 1
    assert "not ccb-managed" in capsys.readouterr().out
    assert hook.exists()


def test_uninstall_noop_when_nothing_to_remove(tmp_path: Path) -> None:
    _make_git_repo(tmp_path)
    rc = uninstall(tmp_path)
    assert rc == 0
