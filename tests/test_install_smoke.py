"""End-to-end smoke test: install ccb into a fresh fake project."""
from __future__ import annotations

import json
from pathlib import Path

from ccb.installer.main import install, status, uninstall
from ccb.installer.merger import CLAUDE_MD_BEGIN, CLAUDE_MD_END


def test_install_into_empty_project(tmp_path: Path, capsys) -> None:
    rc = install(target_dir=str(tmp_path))
    assert rc == 0

    claude_md = tmp_path / "CLAUDE.md"
    settings = tmp_path / ".claude" / "settings.json"

    assert claude_md.exists()
    assert CLAUDE_MD_BEGIN in claude_md.read_text()
    assert CLAUDE_MD_END in claude_md.read_text()

    assert settings.exists()
    data = json.loads(settings.read_text())
    assert data["ccb"]["managed"] is True


def test_install_preserves_existing_claude_md(tmp_path: Path) -> None:
    user_text = "# my project\n\nuser instructions here\n"
    (tmp_path / "CLAUDE.md").write_text(user_text)

    install(target_dir=str(tmp_path))

    content = (tmp_path / "CLAUDE.md").read_text()
    assert "user instructions here" in content
    assert CLAUDE_MD_BEGIN in content


def test_reinstall_is_idempotent(tmp_path: Path) -> None:
    install(target_dir=str(tmp_path))
    first = (tmp_path / "CLAUDE.md").read_text()
    install(target_dir=str(tmp_path))
    second = (tmp_path / "CLAUDE.md").read_text()
    assert first == second


def test_uninstall_strips_block_only(tmp_path: Path) -> None:
    user_text = "# my project\n\nuser stuff\n"
    (tmp_path / "CLAUDE.md").write_text(user_text)
    install(target_dir=str(tmp_path))
    uninstall(target_dir=str(tmp_path))
    final = (tmp_path / "CLAUDE.md").read_text()
    assert "user stuff" in final
    assert CLAUDE_MD_BEGIN not in final


def test_status_runs(tmp_path: Path, monkeypatch, capsys) -> None:
    monkeypatch.chdir(tmp_path)
    install(target_dir=str(tmp_path))
    rc = status()
    assert rc == 0
    out = capsys.readouterr().out
    assert "CLAUDE.md: present" in out
    assert "settings.json: present" in out
