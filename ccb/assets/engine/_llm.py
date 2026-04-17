"""LLM backend abstraction for ccb engine scripts.

Two backends, tried in order:

  1. `claude` CLI (subprocess) — uses the user's Claude Code subscription
     credentials. No extra billing, no API key needed. This is the default
     for subscription users (Pro/Max/Team) which is the majority of Claude
     Code installs.

  2. `anthropic` Python SDK — direct API access, requires
     ANTHROPIC_API_KEY env var. For users on standalone pay-as-you-go API
     billing or for headless CI environments without a Claude Code session.

Auto-detect at call time:
  - `CCB_LLM_BACKEND=cli`  → force CLI
  - `CCB_LLM_BACKEND=sdk`  → force SDK
  - unset / `auto`         → CLI if `claude` in PATH, else SDK if key+module

Returns the model's full text response, or None if no backend works.
Never raises — engine scripts must keep running even if the LLM is
unreachable.
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from typing import Literal

DEFAULT_MODEL = "claude-haiku-4-5"
DEFAULT_TIMEOUT = 60
DEFAULT_MAX_TOKENS = 1000

Backend = Literal["cli", "sdk"]


def call_llm(
    prompt: str,
    *,
    model: str | None = None,
    max_tokens: int = DEFAULT_MAX_TOKENS,
    timeout: int = DEFAULT_TIMEOUT,
) -> str | None:
    """Send `prompt` to the LLM, return the text response or None on failure.

    Backend selection follows the docstring at module top.
    """
    model = model or os.environ.get("CCB_LLM_MODEL", DEFAULT_MODEL)
    backend = _select_backend()

    if backend == "cli":
        out = _via_cli(prompt, model=model, timeout=timeout)
        if out is not None:
            return out
        # CLI was preferred but failed → fall back to SDK if available.
        if _sdk_available():
            return _via_sdk(prompt, model=model, max_tokens=max_tokens, timeout=timeout)
        return None

    if backend == "sdk":
        return _via_sdk(prompt, model=model, max_tokens=max_tokens, timeout=timeout)

    return None


def available_backends() -> list[Backend]:
    """List backends usable right now. Useful for status / error messages."""
    out: list[Backend] = []
    if _cli_available():
        out.append("cli")
    if _sdk_available():
        out.append("sdk")
    return out


def setup_hint() -> str:
    """One-paragraph hint to print when no backend works."""
    return (
        "ccb LLM features need one of:\n"
        "  • the `claude` CLI on PATH (uses your Claude Code subscription — free for Pro/Max/Team)\n"
        "  • OR `ANTHROPIC_API_KEY` set + the `anthropic` SDK installed\n"
        "      .claude/ccb-venv/bin/pip install 'claude-context-box[llm]'\n"
        "      export ANTHROPIC_API_KEY=sk-ant-..."
    )


# ---- backend selection ------------------------------------------------------


def _select_backend() -> Backend | None:
    forced = os.environ.get("CCB_LLM_BACKEND", "auto").lower()
    if forced == "cli":
        return "cli" if _cli_available() else None
    if forced == "sdk":
        return "sdk" if _sdk_available() else None
    # auto: prefer subscription-backed CLI when available, otherwise SDK.
    if _cli_available():
        return "cli"
    if _sdk_available():
        return "sdk"
    return None


def _cli_available() -> bool:
    return shutil.which("claude") is not None


def _sdk_available() -> bool:
    if not os.environ.get("ANTHROPIC_API_KEY"):
        return False
    try:
        import anthropic  # noqa: F401
    except ImportError:
        return False
    return True


# ---- backends ---------------------------------------------------------------


def _via_cli(prompt: str, *, model: str, timeout: int) -> str | None:
    """Invoke the `claude` CLI in print mode and return its stdout.

    `claude -p "<prompt>"` runs a one-shot non-interactive query against
    the user's authenticated session. Output is the model's text response.
    """
    cmd = ["claude", "-p", prompt, "--model", model]
    try:
        proc = subprocess.run(
            cmd, capture_output=True, text=True, timeout=timeout, check=False
        )
    except (subprocess.TimeoutExpired, OSError):
        return None
    if proc.returncode != 0:
        sys.stderr.write(
            f"claude CLI exited {proc.returncode}: {proc.stderr.strip()[:200]}\n"
        )
        return None
    text = proc.stdout.strip()
    return text or None


def _via_sdk(prompt: str, *, model: str, max_tokens: int, timeout: int) -> str | None:
    try:
        import anthropic  # type: ignore
    except ImportError:
        return None
    try:
        client = anthropic.Anthropic()
        msg = client.messages.create(
            model=model,
            max_tokens=max_tokens,
            timeout=timeout,
            messages=[{"role": "user", "content": prompt}],
        )
    except Exception as exc:  # noqa: BLE001
        sys.stderr.write(f"anthropic SDK call failed: {exc}\n")
        return None
    try:
        return "".join(
            b.text for b in msg.content if getattr(b, "type", None) == "text"
        ).strip() or None
    except Exception:
        return None


# ---- response parsing helpers ----------------------------------------------


def parse_json_response(text: str) -> dict | list | None:
    """Tolerate ```json fences and stray prose around the JSON block."""
    if not text:
        return None
    s = text.strip()
    if s.startswith("```"):
        # ```json\n{...}\n```
        s = s.strip("`")
        s = s.removeprefix("json").strip()
        # In case there's still a trailing fence after stripping leading
        if s.endswith("```"):
            s = s.removesuffix("```").strip()
    try:
        return json.loads(s)
    except json.JSONDecodeError:
        # Last resort: find the first {…} or [...] block and try just that.
        for opener, closer in (("{", "}"), ("[", "]")):
            i = s.find(opener)
            j = s.rfind(closer)
            if 0 <= i < j:
                try:
                    return json.loads(s[i:j + 1])
                except json.JSONDecodeError:
                    continue
        return None
