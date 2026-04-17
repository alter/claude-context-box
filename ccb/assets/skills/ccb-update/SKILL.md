---
name: ccb-update
description: Regenerate PROJECT.llm and per-module CONTEXT.llm files for the current project. Use when the architecture has changed materially (new top-level directories, new modules, removed packages) or when ccb status reports the contexts as stale.
allowed-tools: Bash({{ccb_python}} .claude/ccb-engine/update.py:*), Read
---

Step 1 — regenerate the contexts:

```
{{ccb_python}} .claude/ccb-engine/update.py
```

Step 2 — **read the freshly-written PROJECT.llm yourself** (Read tool, full
file). The SessionStart hook only injects PROJECT.llm at the start of a new
session; in the middle of an existing session you have to pull the new
content into context manually. If the user is actively working on a specific
module, also read that module's `<module>/CONTEXT.llm`.

Step 3 — briefly tell the user what changed (new modules, removed modules,
warnings from update.py). Don't recap the entire PROJECT.llm — they can read
it themselves; just call out diffs and surprises.
