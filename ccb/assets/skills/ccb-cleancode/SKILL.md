---
name: ccb-cleancode
description: Scan the project for likely dead code (unreferenced functions, unused imports, files with no inbound references). Reports candidates only — does not delete anything. Use when the user asks to clean up a module or before a refactor.
allowed-tools: Bash({{ccb_python}} .claude/ccb-engine/cleancode.py:*)
---

Run the dead-code detector:

```
{{ccb_python}} .claude/ccb-engine/cleancode.py
```

Present each candidate with: file path, what's flagged (function / import /
file), and the heuristic that flagged it. Always ask for explicit confirmation
before removing anything.
