#!/usr/bin/env python3
"""Answer a natural-language question from .ccb/wiki/ contents.

Usage:
    python3 query_wiki.py "what did we decide about auth?"

Needs an LLM backend — either the `claude` CLI on PATH (uses your Claude
Code subscription, no extra billing) or the `anthropic` SDK plus
ANTHROPIC_API_KEY. See `_llm.py` for backend selection details.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from _lib import project_root  # noqa: E402
from _llm import available_backends, call_llm, setup_hint  # noqa: E402

WIKI_BYTES_LIMIT = 100_000
MAX_OUTPUT_TOKENS = 800
LLM_TIMEOUT_SECONDS = 30


def main() -> int:
    if len(sys.argv) < 2 or not sys.argv[1].strip():
        print('usage: query_wiki.py "<question>"', file=sys.stderr)
        return 2
    question = " ".join(sys.argv[1:]).strip()

    root = project_root()
    wiki_dir = root / ".ccb" / "wiki"
    if not wiki_dir.is_dir():
        print(
            "no wiki found. Compile one first:\n"
            "  .claude/ccb-venv/bin/python .claude/ccb-engine/compile_wiki.py",
            file=sys.stderr,
        )
        return 1

    bundle = _load_wiki(wiki_dir)
    if not bundle:
        print("wiki is empty", file=sys.stderr)
        return 1

    if not available_backends():
        print(setup_hint(), file=sys.stderr)
        return 1

    answer = _ask_model(question, bundle)
    if answer is None:
        return 1
    print(answer)
    return 0


def _load_wiki(wiki_dir: Path) -> str:
    parts: list[str] = []
    total = 0
    if (wiki_dir / "index.md").exists():
        sources = [wiki_dir / "index.md"] + sorted((wiki_dir / "topics").glob("*.md"))
    else:
        sources = sorted(wiki_dir.rglob("*.md"))
    for p in sources:
        if not p.exists():
            continue
        rel = p.relative_to(wiki_dir)
        chunk = f"\n=== {rel} ===\n{p.read_text(encoding='utf-8', errors='ignore')}\n"
        if total + len(chunk) > WIKI_BYTES_LIMIT:
            break
        parts.append(chunk)
        total += len(chunk)
    return "".join(parts)


def _ask_model(question: str, wiki: str) -> str | None:
    prompt = (
        "You are answering a developer's question using ONLY the wiki articles "
        "below. Be specific. Quote exact decisions / module paths when they "
        "appear. If the wiki doesn't cover the question, say so plainly.\n\n"
        f"Question: {question}\n\n"
        "Wiki:\n"
        "---\n"
        f"{wiki}\n"
        "---\n"
    )
    return call_llm(prompt, max_tokens=MAX_OUTPUT_TOKENS, timeout=LLM_TIMEOUT_SECONDS)


if __name__ == "__main__":
    sys.exit(main())
