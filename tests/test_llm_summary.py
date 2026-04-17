"""Tests for LLM-summarized session captures.

The anthropic SDK is mocked — these tests run without network or API key.
A separate manual smoke (documented in README) is required to verify the
real Anthropic call actually works end-to-end.
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from textwrap import dedent

ENGINE_DIR = Path(__file__).parent.parent / "ccb" / "assets" / "engine"


def _run_capture(handoff: Path | None, project_dir: Path, env_extra: dict | None = None) -> subprocess.CompletedProcess:
    """Invoke capture_session.py with controlled env."""
    env = {
        "CLAUDE_PROJECT_DIR": str(project_dir),
        "PATH": "",
    }
    if env_extra:
        env.update(env_extra)
    args = [sys.executable, str(ENGINE_DIR / "capture_session.py")]
    if handoff is not None:
        args.append(str(handoff))
    return subprocess.run(args, capture_output=True, text=True, env=env, timeout=10)


def _write_handoff(project_dir: Path, *, transcript: Path, changed: list[str] | None = None) -> Path:
    handoff = project_dir / ".ccb" / "handoff.json"
    handoff.parent.mkdir(parents=True, exist_ok=True)
    handoff.write_text(json.dumps({
        "changed_files": changed or [],
        "transcript": str(transcript),
    }))
    return handoff


def _install_fake_anthropic(project_dir: Path, *, response_text: str) -> Path:
    """Drop a stand-in `anthropic` module the worker will import in lieu of the
    real SDK. The module records that it was called by writing to a marker
    file, and returns whatever response_text we want."""
    marker = project_dir / "fake_anthropic_called.txt"
    sitepkg = project_dir / "fake_site"
    sitepkg.mkdir(parents=True, exist_ok=True)
    (sitepkg / "anthropic.py").write_text(dedent(f"""\
        from pathlib import Path

        class _Block:
            type = "text"
            def __init__(self, text):
                self.text = text

        class _Msg:
            def __init__(self, text):
                self.content = [_Block(text)]

        class _Messages:
            def create(self, **kwargs):
                Path({str(marker)!r}).write_text("called")
                return _Msg({response_text!r})

        class Anthropic:
            messages = _Messages()
    """))
    return sitepkg


# ---- skip paths --------------------------------------------------------------


def test_skipped_when_no_api_key(tmp_path: Path) -> None:
    transcript = tmp_path / "t.jsonl"
    transcript.write_text("session content")
    h = _write_handoff(tmp_path, transcript=transcript)

    proc = _run_capture(h, tmp_path)  # no ANTHROPIC_API_KEY

    assert proc.returncode == 0
    log = next((tmp_path / ".ccb" / "daily_log").glob("*.md"))
    body = log.read_text()
    # No LLM sections should appear.
    assert "#### decisions" not in body
    assert "#### summary" not in body


def test_skipped_when_disabled_via_env(tmp_path: Path) -> None:
    transcript = tmp_path / "t.jsonl"
    transcript.write_text("session content")
    h = _write_handoff(tmp_path, transcript=transcript)
    sitepkg = _install_fake_anthropic(tmp_path, response_text="{}")

    proc = _run_capture(h, tmp_path, env_extra={
        "ANTHROPIC_API_KEY": "x",
        "PYTHONPATH": str(sitepkg),
        "CCB_LLM": "0",
    })

    assert proc.returncode == 0
    assert not (tmp_path / "fake_anthropic_called.txt").exists()


def test_skipped_when_no_transcript(tmp_path: Path) -> None:
    h = _write_handoff(tmp_path, transcript=tmp_path / "missing.jsonl")
    sitepkg = _install_fake_anthropic(tmp_path, response_text='{"summary":"x"}')

    proc = _run_capture(h, tmp_path, env_extra={
        "ANTHROPIC_API_KEY": "x",
        "PYTHONPATH": str(sitepkg),
    })

    assert proc.returncode == 0
    assert not (tmp_path / "fake_anthropic_called.txt").exists()


def test_skipped_when_anthropic_not_installed(tmp_path: Path) -> None:
    transcript = tmp_path / "t.jsonl"
    transcript.write_text("content")
    h = _write_handoff(tmp_path, transcript=transcript)

    # No PYTHONPATH override → real anthropic not on sys.path.
    proc = _run_capture(h, tmp_path, env_extra={"ANTHROPIC_API_KEY": "x"})

    assert proc.returncode == 0
    log = next((tmp_path / ".ccb" / "daily_log").glob("*.md"))
    assert "#### summary" not in log.read_text()


# ---- happy path --------------------------------------------------------------


def test_writes_decisions_issues_summary_to_daily_log(tmp_path: Path) -> None:
    transcript = tmp_path / "t.jsonl"
    transcript.write_text("user: do X\nassistant: ok, did X")
    h = _write_handoff(tmp_path, transcript=transcript)

    response = json.dumps({
        "summary": "Refactored auth to use JWTs.",
        "decisions": ["use HS256", "store refresh token in httpOnly cookie"],
        "issues": ["TODO: rate limit /login"],
    })
    sitepkg = _install_fake_anthropic(tmp_path, response_text=response)

    proc = _run_capture(h, tmp_path, env_extra={
        "ANTHROPIC_API_KEY": "x",
        "PYTHONPATH": str(sitepkg),
    })

    assert proc.returncode == 0
    assert (tmp_path / "fake_anthropic_called.txt").exists(), "anthropic SDK was not called"

    log = next((tmp_path / ".ccb" / "daily_log").glob("*.md"))
    body = log.read_text()
    assert "#### summary" in body
    assert "Refactored auth to use JWTs." in body
    assert "#### decisions" in body
    assert "use HS256" in body
    assert "store refresh token in httpOnly cookie" in body
    assert "#### issues" in body
    assert "TODO: rate limit /login" in body


def test_handles_model_response_with_code_fence(tmp_path: Path) -> None:
    transcript = tmp_path / "t.jsonl"
    transcript.write_text("session")
    h = _write_handoff(tmp_path, transcript=transcript)

    fenced = '```json\n{"summary":"fenced ok","decisions":[],"issues":[]}\n```'
    sitepkg = _install_fake_anthropic(tmp_path, response_text=fenced)

    proc = _run_capture(h, tmp_path, env_extra={
        "ANTHROPIC_API_KEY": "x",
        "PYTHONPATH": str(sitepkg),
    })

    assert proc.returncode == 0
    log = next((tmp_path / ".ccb" / "daily_log").glob("*.md"))
    assert "fenced ok" in log.read_text()


def test_handles_invalid_json_silently(tmp_path: Path) -> None:
    transcript = tmp_path / "t.jsonl"
    transcript.write_text("session")
    h = _write_handoff(tmp_path, transcript=transcript)

    sitepkg = _install_fake_anthropic(tmp_path, response_text="this is not json at all")

    proc = _run_capture(h, tmp_path, env_extra={
        "ANTHROPIC_API_KEY": "x",
        "PYTHONPATH": str(sitepkg),
    })

    assert proc.returncode == 0  # never crash the user's session
    log = next((tmp_path / ".ccb" / "daily_log").glob("*.md"))
    body = log.read_text()
    assert "#### summary" not in body
