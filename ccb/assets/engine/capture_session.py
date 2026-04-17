#!/usr/bin/env python3
"""Background session worker.

Spawned by SessionEnd / PreCompact so the slow stuff (incremental context
refresh, optional LLM summarization) doesn't block the hook timeout.

Reads a handoff JSON file written by the hook:
  {"changed_files": ["src/api/handler.py", ...], "transcript": "..."}

Then:
  1. Runs `update.py --paths <unique parent dirs of changed_files>` to refresh
     PROJECT.llm and the touched CONTEXT.llm files.
  2. Appends a structured entry to .ccb/daily_log/<date>.md with what got
     refreshed (and a transcript pointer).
  3. If an LLM backend is reachable (claude CLI or anthropic SDK), asks
     Haiku to extract structured decisions / issues / summary from the
     transcript and appends those sections too. Skipped silently otherwise.

Failures are swallowed — never propagate back to the user's Claude Code session.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from _lib import now_iso, project_root  # noqa: E402
from _llm import call_llm, parse_json_response  # noqa: E402

# Cap the slice of transcript we send to Haiku — long sessions can produce
# multi-megabyte transcripts and we only need the recent decisions.
TRANSCRIPT_BYTES_LIMIT = 60_000
LLM_TIMEOUT_SECONDS = 30


def main() -> int:
    handoff_path = Path(sys.argv[1]) if len(sys.argv) > 1 else None
    root = project_root()

    payload: dict = {}
    if handoff_path and handoff_path.exists():
        try:
            payload = json.loads(handoff_path.read_text(encoding="utf-8"))
        except Exception:
            payload = {}
        try:
            handoff_path.unlink()
        except Exception:
            pass

    changed: list[str] = payload.get("changed_files") or []
    transcript: str = payload.get("transcript") or ""

    refreshed = _refresh_contexts(root, changed)
    summary = _llm_summary(transcript)

    log_dir = root / ".ccb" / "daily_log"
    log_dir.mkdir(parents=True, exist_ok=True)
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    log = log_dir / f"{today}.md"

    with log.open("a", encoding="utf-8") as fh:
        fh.write(f"\n### background capture {now_iso()}\n")
        if refreshed:
            fh.write(f"- refreshed CONTEXT.llm in {len(refreshed)} dir(s):\n")
            for d in refreshed:
                fh.write(f"  - `{d}`\n")
        elif changed:
            fh.write("- no CONTEXT.llm refresh needed (changes outside source dirs)\n")
        if transcript and Path(transcript).exists():
            size = Path(transcript).stat().st_size
            fh.write(f"- transcript: `{transcript}` ({size} bytes)\n")
        if summary:
            _write_summary(fh, summary)

    return 0


def _refresh_contexts(root: Path, changed_files: list[str]) -> list[str]:
    """Run update.py --paths for unique parent directories of changed files."""
    if not changed_files:
        return []
    parents = sorted({str(Path(f).parent) for f in changed_files if f})
    update_script = root / ".claude" / "ccb-engine" / "update.py"
    if not update_script.exists():
        return []
    try:
        proc = subprocess.run(
            [sys.executable, str(update_script), "--paths", *parents],
            cwd=str(root),
            capture_output=True,
            text=True,
            timeout=60,
        )
        if proc.returncode != 0:
            return []
    except Exception:
        return []
    return parents


# ---- LLM summary -------------------------------------------------------------


def _llm_summary(transcript_path: str) -> dict | None:
    """Best-effort transcript summarization via Haiku.

    Returns a dict with keys 'summary', 'decisions', 'issues' on success.
    Returns None if anything blocks the call (no LLM backend reachable,
    no transcript, network error, malformed JSON).

    Override the model with CCB_LLM_MODEL; disable entirely with CCB_LLM=0.
    """
    if os.environ.get("CCB_LLM", "1").lower() in {"0", "false", "no"}:
        return None
    if not transcript_path:
        return None

    transcript_file = Path(transcript_path)
    if not transcript_file.exists():
        return None

    try:
        raw = transcript_file.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return None
    if not raw.strip():
        return None
    if len(raw) > TRANSCRIPT_BYTES_LIMIT:
        # Keep the tail — recent decisions matter more than session opening.
        raw = raw[-TRANSCRIPT_BYTES_LIMIT:]

    prompt = _build_prompt(raw)
    text = call_llm(prompt, max_tokens=1000, timeout=LLM_TIMEOUT_SECONDS)
    if text is None:
        return None
    data = parse_json_response(text)
    return data if isinstance(data, dict) else None


def _build_prompt(transcript_excerpt: str) -> str:
    return (
        "You are summarizing a Claude Code coding session for a developer's "
        "long-term project memory. Output ONLY a JSON object — no prose, no "
        "code fences. Schema:\n"
        "{\n"
        '  "summary": "1-2 sentences describing what got done",\n'
        '  "decisions": ["short imperative statements of technical choices made", ...],\n'
        '  "issues": ["short imperative statements of unresolved bugs / TODOs / risks", ...]\n'
        "}\n"
        "Keep arrays under 6 items each. Skip arrays that are genuinely empty.\n\n"
        "Session transcript (most recent portion shown if truncated):\n"
        "---\n"
        f"{transcript_excerpt}\n"
        "---\n"
    )


def _write_summary(fh, summary: dict) -> None:
    s = (summary.get("summary") or "").strip()
    decisions = [d for d in (summary.get("decisions") or []) if isinstance(d, str)]
    issues = [i for i in (summary.get("issues") or []) if isinstance(i, str)]

    if s:
        fh.write(f"\n#### summary\n{s}\n")
    if decisions:
        fh.write("\n#### decisions\n")
        for d in decisions[:10]:
            fh.write(f"- {d.strip()}\n")
    if issues:
        fh.write("\n#### issues\n")
        for i in issues[:10]:
            fh.write(f"- {i.strip()}\n")


if __name__ == "__main__":
    sys.exit(main())
