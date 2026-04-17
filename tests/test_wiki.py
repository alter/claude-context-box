"""Tests for compile_wiki.py and query_wiki.py.

Like test_llm_summary.py: anthropic is faked via PYTHONPATH so the tests
run without network or API key.
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from textwrap import dedent

ENGINE_DIR = Path(__file__).parent.parent / "ccb" / "assets" / "engine"


def _run(script: str, project_dir: Path, *, args: list[str] | None = None,
         env_extra: dict | None = None) -> subprocess.CompletedProcess:
    env = {"CLAUDE_PROJECT_DIR": str(project_dir), "PATH": ""}
    if env_extra:
        env.update(env_extra)
    cmd = [sys.executable, str(ENGINE_DIR / script), *(args or [])]
    return subprocess.run(cmd, capture_output=True, text=True, env=env, timeout=15)


def _seed_logs(project_dir: Path) -> Path:
    log_dir = project_dir / ".ccb" / "daily_log"
    log_dir.mkdir(parents=True, exist_ok=True)
    (log_dir / "2026-04-15.md").write_text(
        "## session ended\n- decided: use SQLite for v1\n- refreshed CONTEXT.llm in src/db/\n"
    )
    (log_dir / "2026-04-16.md").write_text(
        "## session ended\n- decided: JWT for auth\n- refreshed CONTEXT.llm in src/auth/\n"
    )
    return log_dir


def _install_fake_anthropic(project_dir: Path, *, response_text: str) -> Path:
    sitepkg = project_dir / "fake_site"
    sitepkg.mkdir(parents=True, exist_ok=True)
    (sitepkg / "anthropic.py").write_text(dedent(f"""\
        class _Block:
            type = "text"
            def __init__(self, text):
                self.text = text

        class _Msg:
            def __init__(self, text):
                self.content = [_Block(text)]

        class _Messages:
            def create(self, **kwargs):
                return _Msg({response_text!r})

        class Anthropic:
            messages = _Messages()
    """))
    return sitepkg


# ---- compile_wiki.py -------------------------------------------------------


def test_compile_fails_without_logs(tmp_path: Path) -> None:
    proc = _run("compile_wiki.py", tmp_path)
    assert proc.returncode == 1
    assert "no daily logs" in proc.stderr


def test_compile_fails_without_api_key(tmp_path: Path) -> None:
    _seed_logs(tmp_path)
    proc = _run("compile_wiki.py", tmp_path)
    assert proc.returncode == 1
    assert "ANTHROPIC_API_KEY" in proc.stderr


def test_compile_writes_index_and_topics(tmp_path: Path) -> None:
    _seed_logs(tmp_path)
    plan = json.dumps({
        "intro": "Project iterating on auth and db.",
        "topics": [
            {
                "slug": "authentication",
                "title": "Authentication",
                "summary": "JWT-based session handling.",
                "decisions": ["use HS256", "JWT tokens"],
                "issues": ["TODO: rate limit"],
                "modules": ["src/auth/"],
                "related": ["database"],
                "sources": ["2026-04-16.md"],
            },
            {
                "slug": "database",
                "title": "Database",
                "summary": "Persistent storage layer.",
                "decisions": ["SQLite for v1"],
                "issues": [],
                "modules": ["src/db/"],
                "related": ["authentication"],
                "sources": ["2026-04-15.md"],
            },
        ],
    })
    sitepkg = _install_fake_anthropic(tmp_path, response_text=plan)
    proc = _run("compile_wiki.py", tmp_path, env_extra={
        "ANTHROPIC_API_KEY": "x",
        "PYTHONPATH": str(sitepkg),
    })
    assert proc.returncode == 0, proc.stderr

    wiki = tmp_path / ".ccb" / "wiki"
    assert (wiki / "index.md").exists()
    assert (wiki / "topics" / "authentication.md").exists()
    assert (wiki / "topics" / "database.md").exists()

    auth = (wiki / "topics" / "authentication.md").read_text()
    assert "## Decisions" in auth
    assert "use HS256" in auth
    assert "src/auth/" in auth
    assert "[database]" in auth  # cross-link to related topic

    index = (wiki / "index.md").read_text()
    assert "Project iterating on auth and db." in index
    assert "[Authentication]" in index
    assert "[Database]" in index


def test_compile_dry_run_writes_nothing(tmp_path: Path) -> None:
    _seed_logs(tmp_path)
    plan = json.dumps({"intro": "x", "topics": [
        {"slug": "auth", "title": "Auth", "summary": "s"},
    ]})
    sitepkg = _install_fake_anthropic(tmp_path, response_text=plan)
    proc = _run("compile_wiki.py", tmp_path, args=["--dry-run"], env_extra={
        "ANTHROPIC_API_KEY": "x",
        "PYTHONPATH": str(sitepkg),
    })
    assert proc.returncode == 0
    assert "would write 1 topic" in proc.stdout
    assert not (tmp_path / ".ccb" / "wiki").exists()


def test_compile_handles_invalid_model_json(tmp_path: Path) -> None:
    _seed_logs(tmp_path)
    sitepkg = _install_fake_anthropic(tmp_path, response_text="not json")
    proc = _run("compile_wiki.py", tmp_path, env_extra={
        "ANTHROPIC_API_KEY": "x",
        "PYTHONPATH": str(sitepkg),
    })
    assert proc.returncode == 1
    assert "invalid JSON" in proc.stderr


# ---- query_wiki.py ---------------------------------------------------------


def test_query_fails_without_wiki(tmp_path: Path) -> None:
    proc = _run("query_wiki.py", tmp_path, args=["what about auth?"])
    assert proc.returncode == 1
    assert "no wiki found" in proc.stderr


def test_query_fails_without_api_key(tmp_path: Path) -> None:
    (tmp_path / ".ccb" / "wiki").mkdir(parents=True)
    (tmp_path / ".ccb" / "wiki" / "index.md").write_text("# wiki\n")
    proc = _run("query_wiki.py", tmp_path, args=["what?"])
    assert proc.returncode == 1
    assert "ANTHROPIC_API_KEY" in proc.stderr


def test_query_returns_model_answer(tmp_path: Path) -> None:
    wiki = tmp_path / ".ccb" / "wiki"
    (wiki / "topics").mkdir(parents=True)
    (wiki / "index.md").write_text("# wiki\n- [Auth](./topics/auth.md)\n")
    (wiki / "topics" / "auth.md").write_text("# Auth\n## Decisions\n- use HS256\n")
    sitepkg = _install_fake_anthropic(tmp_path, response_text="We use HS256 for JWT signing.")

    proc = _run("query_wiki.py", tmp_path, args=["how do we sign JWTs?"], env_extra={
        "ANTHROPIC_API_KEY": "x",
        "PYTHONPATH": str(sitepkg),
    })
    assert proc.returncode == 0, proc.stderr
    assert "HS256" in proc.stdout
