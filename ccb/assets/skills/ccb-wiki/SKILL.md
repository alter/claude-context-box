---
name: ccb-wiki
description: Compile .ccb/daily_log/* into a structured navigable wiki under .ccb/wiki/, or query the existing wiki by question. Use after a stretch of substantial work to produce a "what we know" reference, or when the user wants a quick answer drawn from past sessions without re-reading raw logs.
allowed-tools: Bash({{ccb_python}} .claude/ccb-engine/compile_wiki.py:*), Bash({{ccb_python}} .claude/ccb-engine/query_wiki.py:*)
---

If the user wants to **build / refresh** the wiki:

```
{{ccb_python}} .claude/ccb-engine/compile_wiki.py
```

Add `--since 7d` (or any `<N>d|h|m`) to limit the input window.
Add `--dry-run` to preview without writing.

If the user wants to **answer a question** from the wiki:

```
{{ccb_python}} .claude/ccb-engine/query_wiki.py "<their question>"
```

Both commands require the `anthropic` SDK and `ANTHROPIC_API_KEY`. If either
is missing, the script prints a clear setup hint — pass that hint back to the
user instead of guessing.
