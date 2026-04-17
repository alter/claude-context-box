#!/usr/bin/env python3
"""Answer a natural-language question from .ccb/wiki/ contents.

Usage:
    python3 query_wiki.py "what did we decide about auth?"

Requires the `anthropic` SDK + ANTHROPIC_API_KEY (the same dependency as
compile_wiki.py). Loads index.md and every topic article, asks the model to
answer the question grounded in those documents, and prints the response to
stdout. No state is written.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from _lib import project_root  # noqa: E402

QUERY_MODEL = "claude-haiku-4-5"
WIKI_BYTES_LIMIT = 100_000
MAX_OUTPUT_TOKENS = 800
LLM_TIMEOUT_SECONDS = 30


def main() -> int:
    if len(sys.argv) < 2 or not sys.argv[1].strip():
        print("usage: query_wiki.py \"<question>\"", file=sys.stderr)
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

    if not _llm_available():
        print(
            "query requires the anthropic SDK and ANTHROPIC_API_KEY.\n"
            "  install: .claude/ccb-venv/bin/pip install 'claude-context-box[llm]'\n"
            "  then:    export ANTHROPIC_API_KEY=sk-ant-...",
            file=sys.stderr,
        )
        return 1

    answer = _ask_model(question, bundle, os.environ.get("CCB_LLM_MODEL", QUERY_MODEL))
    if answer is None:
        return 1
    print(answer)
    return 0


def _load_wiki(wiki_dir: Path) -> str:
    parts: list[str] = []
    total = 0
    for p in [wiki_dir / "index.md"] + sorted((wiki_dir / "topics").glob("*.md")) if (wiki_dir / "index.md").exists() else sorted(wiki_dir.rglob("*.md")):
        if not p.exists():
            continue
        rel = p.relative_to(wiki_dir)
        chunk = f"\n=== {rel} ===\n{p.read_text(encoding='utf-8', errors='ignore')}\n"
        if total + len(chunk) > WIKI_BYTES_LIMIT:
            break
        parts.append(chunk)
        total += len(chunk)
    return "".join(parts)


def _llm_available() -> bool:
    if not os.environ.get("ANTHROPIC_API_KEY"):
        return False
    try:
        import anthropic  # noqa: F401
    except ImportError:
        return False
    return True


def _ask_model(question: str, wiki: str, model: str) -> str | None:
    import anthropic  # type: ignore

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

    try:
        client = anthropic.Anthropic()
        msg = client.messages.create(
            model=model,
            max_tokens=MAX_OUTPUT_TOKENS,
            timeout=LLM_TIMEOUT_SECONDS,
            messages=[{"role": "user", "content": prompt}],
        )
    except Exception as exc:  # noqa: BLE001
        print(f"anthropic call failed: {exc}", file=sys.stderr)
        return None

    try:
        return "".join(
            b.text for b in msg.content if getattr(b, "type", None) == "text"
        ).strip()
    except Exception:
        return None


if __name__ == "__main__":
    sys.exit(main())
