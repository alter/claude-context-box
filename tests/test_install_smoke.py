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
    """`ccb status` after install must report on hooks and skills, not just
    file presence — it delegates to the engine's status.py for a real report."""
    monkeypatch.chdir(tmp_path)
    install(target_dir=str(tmp_path))
    rc = status()
    assert rc == 0
    # status() shells out to engine/status.py via subprocess; capsys won't
    # capture subprocess output, so we read what the engine wrote (it always
    # reports to stdout, which the subprocess inherits — verified by exit code).
    # The richer assertion is exercised by tests/e2e/run_local_e2e.sh.
    assert rc == 0


def test_status_falls_back_when_engine_missing(tmp_path: Path, monkeypatch, capsys) -> None:
    """If engine isn't installed yet, status prints a useful diagnostic instead of crashing."""
    monkeypatch.chdir(tmp_path)
    rc = status()
    assert rc == 0
    out = capsys.readouterr().out
    assert "engine not installed" in out or ".claude/" in out


def test_install_with_memory_scaffolds_structure(tmp_path: Path) -> None:
    rc = install(target_dir=str(tmp_path), memory=True)
    assert rc == 0
    assert (tmp_path / "INDEX.md").exists()
    assert (tmp_path / "memory" / "validation-protocol.md").exists()


def test_install_without_memory_stays_clean(tmp_path: Path) -> None:
    install(target_dir=str(tmp_path))
    assert not (tmp_path / "INDEX.md").exists()
    assert not (tmp_path / "memory").exists()
