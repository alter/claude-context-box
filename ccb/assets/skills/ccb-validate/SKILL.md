---
name: ccb-validate
description: Lint the ccb-managed context files. Reports broken cross-references between CONTEXT.llm files, modules with no CONTEXT.llm, stale entries (older than the source), and orphan files. Use before committing context changes or when investigating drift.
allowed-tools: Bash(python3 .claude/ccb-engine/validate.py:*)
---

Run the ccb validator and surface the findings:

```
python3 .claude/ccb-engine/validate.py
```

If issues are reported, present them grouped by severity. Do not auto-fix —
ask the user before regenerating affected modules.
