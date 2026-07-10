---
name: ccb-memory
description: Scaffold or manage the memory/ structure for iterative research projects (INDEX.md entry point, validation protocol, per-iteration experiment folders). Use when the user asks to set up project memory, start a new experiment iteration, or check the memory structure.
allowed-tools: Bash({{ccb_python}} .claude/ccb-engine/memory.py:*)
---

Manage the iterative-research memory structure. Pick the operation from the
user's request:

**Initialize** (create INDEX.md, AGENTS.md, memory/ skeleton — never overwrites
existing files):

```
{{ccb_python}} .claude/ccb-engine/memory.py init
```

**Start a new experiment iteration** (creates
`memory/experiments/<range>/<version>/task-spec.md`):

```
{{ccb_python}} .claude/ccb-engine/memory.py experiment <range> <version>
```

**Status** (what exists, what's missing):

```
{{ccb_python}} .claude/ccb-engine/memory.py status
```

Present the output verbatim. After `init`, Read `INDEX.md` and
`memory/validation-protocol.md` so this session's context reflects them. After
`experiment`, open the created `task-spec.md` and help the user fill in the
pool and goal, then update `memory/current-experiment.md` and `INDEX.md`.
