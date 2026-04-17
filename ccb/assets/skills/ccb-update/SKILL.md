---
name: ccb-update
description: Regenerate PROJECT.llm and per-module CONTEXT.llm files for the current project. Use when the architecture has changed materially (new top-level directories, new modules, removed packages) or when ccb status reports the contexts as stale.
allowed-tools: Bash({{ccb_python}} .claude/ccb-engine/update.py:*)
---

Run the ccb update engine and summarize the result:

```
{{ccb_python}} .claude/ccb-engine/update.py
```

After it finishes, briefly tell the user which files were regenerated and
mention any warnings. Do not re-read PROJECT.llm by hand — the SessionStart
hook will pick up the fresh version next session.
