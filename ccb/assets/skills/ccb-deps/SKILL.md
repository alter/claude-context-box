---
name: ccb-deps
description: Show the project's module dependency graph extracted from PROJECT.llm. Use when reasoning about the impact of a change ("what depends on this?") or planning a refactor.
allowed-tools: Bash(grep:*), Bash(cat:*)
---

Print the dependency section of PROJECT.llm:

```
sed -n '/@dependency_graph/,/^@/p' PROJECT.llm | sed '$d'
```

If PROJECT.llm is missing, tell the user to run /ccb-update first.
