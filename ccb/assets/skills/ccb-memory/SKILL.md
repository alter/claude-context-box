---
name: ccb-memory
description: Scaffold or manage the memory/ structure for recurring tasks and large projects (INDEX.md routing table, validation protocol, per-run task folders). Use when the user asks to set up project memory, start a new run of a recurring task, or check the memory structure.
allowed-tools: Bash({{ccb_python}} .claude/ccb-engine/memory.py:*)
---

Manage the memory structure for recurring tasks. Pick the operation from the
user's request:

**Initialize** (create INDEX.md, AGENTS.md, memory/ skeleton — never overwrites
existing files):

```
{{ccb_python}} .claude/ccb-engine/memory.py init
```

**Start a new run of a recurring task** (creates
`memory/tasks/<task>/<run>/task-spec.md`; `experiment` works as an alias):

```
{{ccb_python}} .claude/ccb-engine/memory.py task <task-name> <run-id>
```

**Status** (what exists, what's missing):

```
{{ccb_python}} .claude/ccb-engine/memory.py status
```

Present the output verbatim. After `init`, Read `INDEX.md` and
`memory/validation-protocol.md` so this session's context reflects them. After
`task`, open the created `task-spec.md` and help the user fill in the inputs
and goal, then update `memory/current-task.md` and `INDEX.md`.

Note: one-off work does not need a memory entry — the ccb session log covers
it. Create task folders only for recurring work.
