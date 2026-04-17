#!/usr/bin/env python3
"""Compile .ccb/daily_log/*.md into a structured wiki under .ccb/wiki/.

Karpathy-style "knowledge as code": raw daily logs are the source; the LLM
acts as the compiler; the resulting `.ccb/wiki/` is the executable index
that the user (and Claude) navigates by reading `index.md` first.

Usage:
    python3 compile_wiki.py                # compile every daily log
    python3 compile_wiki.py --since 7d     # only logs from the last N days
    python3 compile_wiki.py --dry-run      # print plan, write nothing

Needs an LLM backend — either the `claude` CLI on PATH (uses your Claude
Code subscription credentials, no extra billing) or the `anthropic` SDK
plus ANTHROPIC_API_KEY. See `_llm.py` for backend selection details.

Produces:

    .ccb/wiki/
    ├── index.md          ← top-level navigation (themes + back-references)
    └── topics/
        ├── <slug>.md     ← one article per concept extracted from the logs
        └── ...
"""
from __future__ import annotations

import argparse
import os
import re
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from _lib import now_iso, project_root  # noqa: E402
from _llm import (  # noqa: E402
    available_backends,
    call_llm,
    parse_json_response,
    setup_hint,
)

INPUT_BYTES_LIMIT = 200_000   # cap how many bytes of logs we feed the model
MAX_OUTPUT_TOKENS = 4000
LLM_TIMEOUT_SECONDS = 60


def main() -> int:
    parser = argparse.ArgumentParser(description="ccb wiki compiler")
    parser.add_argument("--since", default=None,
                        help="Only consume daily logs from the last N days (e.g. 7d, 30d)")
    parser.add_argument("--dry-run", action="store_true",
                        help="Print what would be written, don't touch disk")
    parser.add_argument("--model", default=None,
                        help="Override CCB_LLM_MODEL for this run")
    args = parser.parse_args()

    root = project_root()
    log_dir = root / ".ccb" / "daily_log"
    if not log_dir.is_dir():
        print(f"no daily logs found under {log_dir}", file=sys.stderr)
        return 1

    logs = _select_logs(log_dir, args.since)
    if not logs:
        print(f"no daily logs in window: {args.since or 'all'}", file=sys.stderr)
        return 1

    print(f"ccb wiki compile: {len(logs)} log file(s)")
    raw = _concat_logs(logs)
    print(f"  total input: {len(raw)} bytes (limit: {INPUT_BYTES_LIMIT})")

    backends = available_backends()
    if not backends:
        print(setup_hint(), file=sys.stderr)
        return 1
    print(f"  llm backend: {backends[0]}")

    plan = _ask_model_for_plan(raw, args.model)
    if plan is None:
        print("model returned no usable plan", file=sys.stderr)
        return 1

    topics = plan.get("topics") or []
    if not topics:
        print("no topics extracted from logs", file=sys.stderr)
        return 0

    if args.dry_run:
        print(f"  would write {len(topics)} topic(s):")
        for t in topics:
            print(f"    - {t.get('slug')}: {t.get('title')}")
        return 0

    wiki_dir = root / ".ccb" / "wiki"
    topics_dir = wiki_dir / "topics"
    topics_dir.mkdir(parents=True, exist_ok=True)

    written: list[tuple[str, str]] = []
    for t in topics:
        slug = _safe_slug(t.get("slug") or t.get("title") or "")
        if not slug:
            continue
        body = _render_topic(t)
        path = topics_dir / f"{slug}.md"
        path.write_text(body, encoding="utf-8")
        written.append((slug, t.get("title") or slug))
    _write_index(wiki_dir, written, plan, len(logs))

    print(f"  wrote {len(written)} topic(s) to {topics_dir.relative_to(root)}/")
    print(f"  wrote {(wiki_dir / 'index.md').relative_to(root)}")
    return 0


# ---- log selection ---------------------------------------------------------


_SINCE_RE = re.compile(r"^(\d+)\s*([dhm])$")


def _select_logs(log_dir: Path, since: str | None) -> list[Path]:
    logs = sorted(log_dir.glob("*.md"))
    if not since:
        return logs

    m = _SINCE_RE.match(since.strip())
    if not m:
        return logs
    n, unit = int(m.group(1)), m.group(2)
    delta = {"d": timedelta(days=n), "h": timedelta(hours=n), "m": timedelta(minutes=n)}[unit]
    cutoff = datetime.now(timezone.utc) - delta
    return [p for p in logs if datetime.fromtimestamp(p.stat().st_mtime, tz=timezone.utc) >= cutoff]


def _concat_logs(logs: list[Path]) -> str:
    buf: list[str] = []
    total = 0
    # Newest first — the truncation will then drop the oldest.
    for p in reversed(logs):
        text = p.read_text(encoding="utf-8", errors="ignore")
        chunk = f"\n=== {p.name} ===\n{text}\n"
        if total + len(chunk) > INPUT_BYTES_LIMIT:
            chunk = chunk[: INPUT_BYTES_LIMIT - total]
            buf.append(chunk)
            break
        buf.append(chunk)
        total += len(chunk)
    return "".join(reversed(buf))


# ---- LLM call --------------------------------------------------------------


def _ask_model_for_plan(raw_logs: str, model: str | None) -> dict | None:
    prompt = (
        "You are compiling a developer's coding-session daily logs into a "
        "navigable knowledge base. Read the logs and produce ONLY a JSON object "
        "matching this schema (no prose, no fences):\n\n"
        "{\n"
        '  "intro": "1-3 sentence overview of what the project has been working on",\n'
        '  "topics": [\n'
        "    {\n"
        '      "slug": "kebab-case-slug",\n'
        '      "title": "Human-readable topic name",\n'
        '      "summary": "1-2 paragraphs describing the topic",\n'
        '      "decisions": ["concrete technical decisions about this topic", ...],\n'
        '      "issues": ["unresolved issues / TODOs / risks", ...],\n'
        '      "modules": ["src/path/", ...],\n'
        '      "related": ["other-topic-slug", ...],\n'
        '      "sources": ["YYYY-MM-DD.md", ...]\n'
        "    }\n"
        "  ]\n"
        "}\n\n"
        "Rules:\n"
        " - Group multiple log entries into themes (auth, billing, db schema, etc).\n"
        " - 3-12 topics typical; skip topics with only one trivial mention.\n"
        " - 'modules' lists actual source directories the topic touches (from "
        "the 'refreshed CONTEXT.llm' lines in the logs).\n"
        " - 'related' references other topics by their slug (forms a cross-link).\n"
        " - 'sources' references the original daily-log filenames.\n\n"
        "Daily logs follow:\n"
        "---\n"
        f"{raw_logs}\n"
        "---\n"
    )

    text = call_llm(
        prompt,
        model=model,
        max_tokens=MAX_OUTPUT_TOKENS,
        timeout=LLM_TIMEOUT_SECONDS,
    )
    if text is None:
        print("LLM call returned no output", file=sys.stderr)
        return None

    data = parse_json_response(text)
    if data is None:
        print("model returned invalid JSON", file=sys.stderr)
        return None
    return data if isinstance(data, dict) else None


# ---- rendering -------------------------------------------------------------


_SLUG_RE = re.compile(r"[^a-z0-9-]+")


def _safe_slug(s: str) -> str:
    s = s.strip().lower().replace(" ", "-").replace("_", "-")
    s = _SLUG_RE.sub("", s)
    return s.strip("-")[:80]


def _render_topic(topic: dict) -> str:
    title = topic.get("title") or topic.get("slug") or "Untitled"
    parts: list[str] = [f"# {title}\n"]
    parts.append(f"_compiled: {now_iso()}_\n")

    summary = (topic.get("summary") or "").strip()
    if summary:
        parts.append(f"\n## Summary\n\n{summary}\n")

    decisions = [d for d in (topic.get("decisions") or []) if isinstance(d, str)]
    if decisions:
        parts.append("\n## Decisions\n")
        for d in decisions:
            parts.append(f"- {d.strip()}\n")

    issues = [i for i in (topic.get("issues") or []) if isinstance(i, str)]
    if issues:
        parts.append("\n## Open issues\n")
        for i in issues:
            parts.append(f"- {i.strip()}\n")

    modules = [m for m in (topic.get("modules") or []) if isinstance(m, str)]
    if modules:
        parts.append("\n## Modules touched\n")
        for m in modules:
            parts.append(f"- `{m.strip().rstrip('/')}/` (see `<repo>/{m.strip().rstrip('/')}/CONTEXT.llm`)\n")

    related = [r for r in (topic.get("related") or []) if isinstance(r, str)]
    if related:
        parts.append("\n## Related topics\n")
        for r in related:
            parts.append(f"- [{r}](./{_safe_slug(r)}.md)\n")

    sources = [s for s in (topic.get("sources") or []) if isinstance(s, str)]
    if sources:
        parts.append("\n## Sources\n")
        for s in sources:
            parts.append(f"- `.ccb/daily_log/{s.strip()}`\n")

    return "".join(parts)


def _write_index(wiki_dir: Path, written: list[tuple[str, str]], plan: dict, n_logs: int) -> None:
    intro = (plan.get("intro") or "").strip()
    parts: list[str] = ["# ccb wiki\n"]
    parts.append(f"_compiled: {now_iso()} from {n_logs} daily log(s)_\n\n")
    if intro:
        parts.append(f"{intro}\n\n")
    parts.append("## Topics\n")
    for slug, title in sorted(written, key=lambda x: x[1].lower()):
        parts.append(f"- [{title}](./topics/{slug}.md)\n")
    parts.append(
        "\n---\nThis wiki is auto-compiled from `.ccb/daily_log/`. "
        "Re-run `ccb wiki compile` after significant work to refresh it.\n"
    )
    (wiki_dir / "index.md").write_text("".join(parts), encoding="utf-8")


if __name__ == "__main__":
    sys.exit(main())
