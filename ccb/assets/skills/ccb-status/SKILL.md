---
name: ccb-status
description: Show ccb installation status (presence of CLAUDE.md block, settings.json, PROJECT.llm freshness, daily-log count). Use when the user asks "is ccb installed", "what does ccb know about this project", or wants to debug why hooks aren't firing.
allowed-tools: Bash({{ccb_python}} .claude/ccb-engine/status.py:*)
---

Run the ccb status check and present the output verbatim:

```
{{ccb_python}} .claude/ccb-engine/status.py
```
