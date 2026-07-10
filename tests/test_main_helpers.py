"""Unit tests for ccb.installer.main helpers — _substitute_python, _compose_claude_md."""
from __future__ import annotations

from pathlib import Path

import pytest

from ccb.installer import main as installer_main


# _substitute_python -----------------------------------------------------


def test_substitute_python_replaces_placeholder(tmp_path: Path) -> None:
    f = tmp_path / "skill.md"
    f.write_text("---\nallowed-tools: Bash({{ccb_python}} run.py:*)\n---\n")
    installer_main._substitute_python(tmp_path, "/abs/path/python")
    assert "/abs/path/python" in f.read_text()
    assert "{{ccb_python}}" not in f.read_text()


def test_substitute_python_walks_subdirs(tmp_path: Path) -> None:
    (tmp_path / "ccb-update").mkdir()
    (tmp_path / "ccb-update" / "SKILL.md").write_text("Run {{ccb_python}} script.py\n")
    (tmp_path / "ccb-status").mkdir()
    (tmp_path / "ccb-status" / "SKILL.md").write_text("And {{ccb_python}} other.py\n")
    installer_main._substitute_python(tmp_path, "/x/python")
    for sub in ("ccb-update", "ccb-status"):
        assert "/x/python" in (tmp_path / sub / "SKILL.md").read_text()


def test_substitute_python_leaves_other_text_alone(tmp_path: Path) -> None:
    f = tmp_path / "skill.md"
    original = "# Skill\nDescription with {{other_var}} here.\n"
    f.write_text(original)
    installer_main._substitute_python(tmp_path, "/x/python")
    assert f.read_text() == original


def test_substitute_python_skips_binary(tmp_path: Path) -> None:
    """Binary files should be skipped silently, not raise."""
    f = tmp_path / "binary.dat"
    f.write_bytes(b"\x00\x01\x02\xff{{ccb_python}}")
    # Should not raise.
    installer_main._substitute_python(tmp_path, "/x/python")
    # Binary file is unmodified (we couldn't decode, so we don't touch it).
    assert f.read_bytes().startswith(b"\x00\x01\x02\xff")


def test_substitute_python_no_op_when_root_missing(tmp_path: Path) -> None:
    """Should silently no-op when the target root doesn't exist."""
    installer_main._substitute_python(tmp_path / "does-not-exist", "/x/python")  # no exception


# _resolve_python_token --------------------------------------------------


def test_resolve_python_token_uses_venv_when_present(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr(installer_main.os, "name", "posix")
    venv_python = tmp_path / "ccb-venv" / "bin" / "python"
    venv_python.parent.mkdir(parents=True)
    venv_python.touch()
    token = installer_main._resolve_python_token(tmp_path)
    assert "${CLAUDE_PROJECT_DIR}" in token
    assert ".claude/ccb-venv/bin/python" in token


def test_resolve_python_token_falls_back_to_python3(tmp_path: Path) -> None:
    assert installer_main._resolve_python_token(tmp_path) == "python3"


def test_resolve_python_token_windows_path(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr(installer_main.os, "name", "nt")
    venv_python = tmp_path / "ccb-venv" / "Scripts" / "python.exe"
    venv_python.parent.mkdir(parents=True)
    venv_python.touch()
    token = installer_main._resolve_python_token(tmp_path)
    assert "ccb-venv" in token
    assert "python.exe" in token


# _compose_claude_md -----------------------------------------------------


def test_compose_claude_md_concatenates_sorted(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr(installer_main, "CLAUDE_MD_DIR", tmp_path)
    (tmp_path / "20_b.md").write_text("BLOCK B")
    (tmp_path / "10_a.md").write_text("BLOCK A")
    (tmp_path / "00_intro.md").write_text("INTRO")

    composed = installer_main._compose_claude_md()
    # Sections appear in numeric order.
    assert composed.index("INTRO") < composed.index("BLOCK A") < composed.index("BLOCK B")


def test_compose_claude_md_skips_underscore_prefixed(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr(installer_main, "CLAUDE_MD_DIR", tmp_path)
    (tmp_path / "10_real.md").write_text("REAL")
    (tmp_path / "_legacy.md").write_text("LEGACY")
    composed = installer_main._compose_claude_md()
    assert "REAL" in composed
    assert "LEGACY" not in composed


def test_compose_claude_md_skips_non_md_files(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr(installer_main, "CLAUDE_MD_DIR", tmp_path)
    (tmp_path / "10_real.md").write_text("REAL")
    (tmp_path / "notes.txt").write_text("TXT")
    (tmp_path / "config.json").write_text('{"a": 1}')
    composed = installer_main._compose_claude_md()
    assert "REAL" in composed
    assert "TXT" not in composed
    assert "config" not in composed


def test_compose_claude_md_returns_empty_when_no_dir(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setattr(installer_main, "CLAUDE_MD_DIR", tmp_path / "nonexistent")
    assert installer_main._compose_claude_md() == ""


def test_compose_claude_md_separates_with_blank_lines(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr(installer_main, "CLAUDE_MD_DIR", tmp_path)
    (tmp_path / "10_a.md").write_text("A")
    (tmp_path / "20_b.md").write_text("B")
    composed = installer_main._compose_claude_md()
    assert "A\n\nB" in composed


# _has_ccb_block ---------------------------------------------------------


def test_has_ccb_block_true(tmp_path: Path) -> None:
    p = tmp_path / "CLAUDE.md"
    p.write_text("user\n<!-- ccb:begin -->\nx\n<!-- ccb:end -->\n")
    assert installer_main._has_ccb_block(p) is True


def test_has_ccb_block_false_when_absent(tmp_path: Path) -> None:
    p = tmp_path / "CLAUDE.md"
    p.write_text("user content only\n")
    assert installer_main._has_ccb_block(p) is False


def test_has_ccb_block_false_when_file_missing(tmp_path: Path) -> None:
    assert installer_main._has_ccb_block(tmp_path / "missing.md") is False


# wiki dispatch ----------------------------------------------------------


def test_wiki_refuses_to_run_in_source_repo(tmp_path: Path, monkeypatch, capsys) -> None:
    """If invoked inside the ccb source repo, wiki() should bail early."""
    (tmp_path / "ccb" / "assets" / "claude_md").mkdir(parents=True)
    (tmp_path / "pyproject.toml").write_text('name = "claude-context-box"\n')
    monkeypatch.chdir(tmp_path)

    class FakeArgs:
        since = None
        dry_run = False

    rc = installer_main.wiki("compile", FakeArgs())
    assert rc == 0
    assert "ccb source repo" in capsys.readouterr().out


def test_wiki_unknown_subcommand_returns_nonzero(tmp_path: Path, monkeypatch, capsys) -> None:
    monkeypatch.chdir(tmp_path)
    rc = installer_main.wiki("snorkel", object())
    assert rc == 2
    assert "unknown wiki subcommand" in capsys.readouterr().err


def test_wiki_compile_invokes_engine_with_since_and_dry_run(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    eng = tmp_path / ".claude" / "ccb-engine"
    eng.mkdir(parents=True)
    (eng / "compile_wiki.py").write_text("import sys; sys.exit(0)\n")

    captured = {}

    def fake_run(cmd, **kw):
        captured["cmd"] = cmd
        return type("R", (), {"returncode": 0})()

    class Args:
        since = "7d"
        dry_run = True

    with __import__("unittest.mock").mock.patch.object(
        installer_main.subprocess, "run", side_effect=fake_run
    ):
        rc = installer_main.wiki("compile", Args())
    assert rc == 0
    assert "--since" in captured["cmd"]
    assert "7d" in captured["cmd"]
    assert "--dry-run" in captured["cmd"]


def test_wiki_query_joins_argv_into_single_question(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    eng = tmp_path / ".claude" / "ccb-engine"
    eng.mkdir(parents=True)
    (eng / "query_wiki.py").write_text("import sys; sys.exit(0)\n")

    captured = {}

    def fake_run(cmd, **kw):
        captured["cmd"] = cmd
        return type("R", (), {"returncode": 0})()

    class Args:
        question = ["what", "did", "we", "decide"]

    with __import__("unittest.mock").mock.patch.object(
        installer_main.subprocess, "run", side_effect=fake_run
    ):
        installer_main.wiki("query", Args())
    # The question parts should be joined into a single argv element.
    assert "what did we decide" in captured["cmd"]


def test_run_engine_script_reports_missing(tmp_path: Path, capsys) -> None:
    rc = installer_main._run_engine_script(tmp_path, tmp_path / "missing.py", [])
    assert rc == 1
    assert "engine script missing" in capsys.readouterr().err


# update / status / uninstall guards -------------------------------------


def test_update_refuses_in_source_repo(tmp_path: Path, monkeypatch, capsys) -> None:
    (tmp_path / "ccb" / "assets" / "claude_md").mkdir(parents=True)
    (tmp_path / "pyproject.toml").write_text('name = "claude-context-box"\n')
    monkeypatch.chdir(tmp_path)
    rc = installer_main.update()
    assert rc == 0
    assert "ccb source repo" in capsys.readouterr().out


def test_status_refuses_in_source_repo(tmp_path: Path, monkeypatch, capsys) -> None:
    (tmp_path / "ccb" / "assets" / "claude_md").mkdir(parents=True)
    (tmp_path / "pyproject.toml").write_text('name = "claude-context-box"\n')
    monkeypatch.chdir(tmp_path)
    rc = installer_main.status()
    assert rc == 0
    assert "ccb source repo" in capsys.readouterr().out


# _run_engine_update timeout handling -------------------------------------


def test_run_engine_update_survives_timeout(tmp_path: Path, capsys) -> None:
    """A timed-out initial update must be non-fatal — the install already
    succeeded (regression: TimeoutExpired escaped and killed the installer
    on slow filesystems like WSL /mnt/c)."""
    import subprocess
    from unittest.mock import patch

    script = tmp_path / ".claude" / "ccb-engine" / "update.py"
    script.parent.mkdir(parents=True)
    script.write_text("pass\n")

    def _raise_timeout(*args, **kwargs):
        raise subprocess.TimeoutExpired(cmd="update.py", timeout=120)

    with patch.object(installer_main.subprocess, "run", side_effect=_raise_timeout):
        rc = installer_main._run_engine_update(tmp_path)
    assert rc == 1
    err = capsys.readouterr().err
    assert "timed out" in err
    assert "CCB_UPDATE_TIMEOUT" in err


def test_update_timeout_env_override(monkeypatch) -> None:
    monkeypatch.setenv("CCB_UPDATE_TIMEOUT", "600")
    assert installer_main._update_timeout() == 600


def test_update_timeout_rejects_garbage(monkeypatch) -> None:
    monkeypatch.setenv("CCB_UPDATE_TIMEOUT", "not-a-number")
    assert installer_main._update_timeout() == installer_main.DEFAULT_UPDATE_TIMEOUT
    monkeypatch.setenv("CCB_UPDATE_TIMEOUT", "-5")
    assert installer_main._update_timeout() == installer_main.DEFAULT_UPDATE_TIMEOUT


# memory dispatch ----------------------------------------------------------


def test_memory_proxies_to_engine_script(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    captured: dict = {}

    def fake_run_engine_script(target, script, args):
        captured["script"] = script.name
        captured["args"] = args
        return 0

    monkeypatch.setattr(installer_main, "_run_engine_script", fake_run_engine_script)

    class Args:
        task_name = "books-25"
        run_id = "v3-500"

    rc = installer_main.memory("experiment", Args())
    assert rc == 0
    assert captured["script"] == "memory.py"
    # The legacy "experiment" subcommand is normalized to "task".
    assert captured["args"] == ["task", "books-25", "v3-500"]


def test_memory_refuses_in_source_repo(tmp_path: Path, monkeypatch, capsys) -> None:
    (tmp_path / "ccb" / "assets" / "claude_md").mkdir(parents=True)
    (tmp_path / "pyproject.toml").write_text('name = "claude-context-box"\n')
    monkeypatch.chdir(tmp_path)
    rc = installer_main.memory("init", None)
    assert rc == 0
    assert "ccb source repo" in capsys.readouterr().out
