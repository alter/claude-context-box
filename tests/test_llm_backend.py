"""Tests for the _llm.py backend abstraction.

Covers backend selection (CLI vs SDK), env-var overrides, the json
response parser, and end-to-end happy paths for both backends. Subprocess
calls are stubbed via PATH manipulation — a fake `claude` binary is
written to a temp dir and prepended to PATH for tests that need to
exercise the CLI path.
"""
from __future__ import annotations

import importlib
import os
import sys
from pathlib import Path
from textwrap import dedent

import pytest

ENGINE_DIR = Path(__file__).parent.parent / "ccb" / "assets" / "engine"
sys.path.insert(0, str(ENGINE_DIR))


@pytest.fixture(autouse=True)
def _clean_llm_module(monkeypatch):
    """Reload _llm AND `anthropic` so each test gets a clean state.

    Without this, an `import anthropic` in one test would cache the fake
    SDK module from that test's tempdir and the next test would see it
    even after monkeypatch.syspath_prepend was reverted.
    """
    for var in ("CCB_LLM_BACKEND", "CCB_LLM_MODEL", "ANTHROPIC_API_KEY"):
        monkeypatch.delenv(var, raising=False)
    for mod in ("_llm", "anthropic"):
        sys.modules.pop(mod, None)
    yield
    for mod in ("_llm", "anthropic"):
        sys.modules.pop(mod, None)


def _import_llm():
    return importlib.import_module("_llm")


def _make_fake_claude(tmp_path: Path, *, stdout: str, exit_code: int = 0) -> Path:
    """Drop a `claude` shim on a tempdir, return the PATH that includes it.

    Returned PATH includes /usr/bin + /bin so `/bin/sh` is resolvable when
    callers set `PATH` to this value (otherwise `subprocess.run([...])`
    can't find the shim's interpreter).
    """
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir(exist_ok=True)
    shim = bin_dir / "claude"
    body = dedent(f"""\
        #!/bin/sh
        cat <<'__EOF__'
        {stdout}
        __EOF__
        exit {exit_code}
    """)
    shim.write_text(body)
    shim.chmod(0o755)
    return bin_dir


def _path_with(bin_dir: Path) -> str:
    """PATH that has bin_dir first, plus the system shells dir."""
    return os.pathsep.join([str(bin_dir), "/usr/bin", "/bin"])


def _make_fake_anthropic(tmp_path: Path, *, response_text: str) -> Path:
    sitepkg = tmp_path / "fake_site"
    sitepkg.mkdir(exist_ok=True)
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


# ---- backend detection -----------------------------------------------------


def test_no_backends_when_neither_available(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setenv("PATH", "")
    llm = _import_llm()
    assert llm.available_backends() == []


def test_cli_detected_when_claude_on_path(monkeypatch, tmp_path: Path) -> None:
    bin_dir = _make_fake_claude(tmp_path, stdout="ok")
    monkeypatch.setenv("PATH", _path_with(bin_dir))
    llm = _import_llm()
    assert "cli" in llm.available_backends()


def test_sdk_detected_when_key_and_module_present(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setenv("PATH", "")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "x")
    sitepkg = _make_fake_anthropic(tmp_path, response_text="x")
    monkeypatch.syspath_prepend(str(sitepkg))
    llm = _import_llm()
    assert "sdk" in llm.available_backends()


def test_sdk_skipped_when_key_missing(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setenv("PATH", "")
    sitepkg = _make_fake_anthropic(tmp_path, response_text="x")
    monkeypatch.syspath_prepend(str(sitepkg))
    # No ANTHROPIC_API_KEY set
    llm = _import_llm()
    assert "sdk" not in llm.available_backends()


def test_cli_preferred_over_sdk_in_auto_mode(monkeypatch, tmp_path: Path) -> None:
    """When both backends are available, CLI wins (subscription is free)."""
    bin_dir = _make_fake_claude(tmp_path, stdout="from-cli")
    monkeypatch.setenv("PATH", _path_with(bin_dir))
    monkeypatch.setenv("ANTHROPIC_API_KEY", "x")
    sitepkg = _make_fake_anthropic(tmp_path, response_text="from-sdk")
    monkeypatch.syspath_prepend(str(sitepkg))

    llm = _import_llm()
    out = llm.call_llm("hello")
    assert out == "from-cli", f"expected CLI backend; got {out!r}"


def test_force_sdk_via_env(monkeypatch, tmp_path: Path) -> None:
    """CCB_LLM_BACKEND=sdk overrides the default CLI preference."""
    bin_dir = _make_fake_claude(tmp_path, stdout="from-cli")
    monkeypatch.setenv("PATH", _path_with(bin_dir))
    monkeypatch.setenv("ANTHROPIC_API_KEY", "x")
    monkeypatch.setenv("CCB_LLM_BACKEND", "sdk")
    sitepkg = _make_fake_anthropic(tmp_path, response_text="from-sdk")
    monkeypatch.syspath_prepend(str(sitepkg))

    llm = _import_llm()
    out = llm.call_llm("hello")
    assert out == "from-sdk"


def test_force_cli_via_env_falls_back_when_unavailable(monkeypatch, tmp_path: Path) -> None:
    """CCB_LLM_BACKEND=cli with no claude on PATH returns None — explicit and silent."""
    monkeypatch.setenv("PATH", "")
    monkeypatch.setenv("CCB_LLM_BACKEND", "cli")
    llm = _import_llm()
    assert llm.call_llm("hello") is None


# ---- response parsing ------------------------------------------------------


def test_parse_json_plain(tmp_path: Path) -> None:
    llm = _import_llm()
    assert llm.parse_json_response('{"a": 1}') == {"a": 1}


def test_parse_json_with_fence(tmp_path: Path) -> None:
    llm = _import_llm()
    fenced = '```json\n{"a": 2}\n```'
    assert llm.parse_json_response(fenced) == {"a": 2}


def test_parse_json_with_prose_around(tmp_path: Path) -> None:
    """Tolerate leading/trailing prose: extract first {...} block."""
    llm = _import_llm()
    msg = 'Sure, here is the answer:\n\n{"x": 3}\n\nLet me know if more help.'
    assert llm.parse_json_response(msg) == {"x": 3}


def test_parse_json_empty_input(tmp_path: Path) -> None:
    llm = _import_llm()
    assert llm.parse_json_response("") is None
    assert llm.parse_json_response("not even close") is None


# ---- happy-path through the abstraction -----------------------------------


def test_call_llm_via_cli_returns_stdout(monkeypatch, tmp_path: Path) -> None:
    bin_dir = _make_fake_claude(tmp_path, stdout='{"summary": "hi"}')
    monkeypatch.setenv("PATH", _path_with(bin_dir))
    llm = _import_llm()
    out = llm.call_llm("anything")
    assert out is not None
    assert "summary" in out


def test_call_llm_via_cli_handles_nonzero_exit(monkeypatch, tmp_path: Path) -> None:
    bin_dir = _make_fake_claude(tmp_path, stdout="oops", exit_code=1)
    monkeypatch.setenv("PATH", _path_with(bin_dir))
    # No SDK fallback configured → returns None.
    llm = _import_llm()
    assert llm.call_llm("anything") is None


def test_call_llm_falls_back_to_sdk_when_cli_fails(monkeypatch, tmp_path: Path) -> None:
    """CLI exits non-zero → fall back to SDK when both are configured."""
    bin_dir = _make_fake_claude(tmp_path, stdout="", exit_code=1)
    monkeypatch.setenv("PATH", _path_with(bin_dir))
    monkeypatch.setenv("ANTHROPIC_API_KEY", "x")
    sitepkg = _make_fake_anthropic(tmp_path, response_text="from-sdk-fallback")
    monkeypatch.syspath_prepend(str(sitepkg))
    llm = _import_llm()
    out = llm.call_llm("anything")
    assert out == "from-sdk-fallback"


def test_setup_hint_mentions_both_backends() -> None:
    llm = _import_llm()
    hint = llm.setup_hint()
    assert "claude" in hint
    assert "ANTHROPIC_API_KEY" in hint
    assert "claude-context-box[llm]" in hint
