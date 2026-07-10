#!/usr/bin/env python3
"""Scaffold and manage the memory/ structure for recurring work and large projects.

Two kinds of tasks exist. One-off work ("did it, forgot it") is already
covered by ccb's daily log + wiki — it needs no manual structure. This
layout is for the other kind: RECURRING tasks that get re-run with new
variants, options, or data, plus large projects where the whole tree must
not be held in context — INDEX.md acts as a routing table instead.

    INDEX.md                        # entry point — read first every session
    AGENTS.md                       # critical rules for any coding agent
    memory/
      validation-protocol.md        # sacred file — never violate
      current-task.md               # the active task/run
      decisions-log.md              # key decisions and insights
      pool/catalog.md               # reusable inputs recurring tasks draw from
      tasks/<task>/<run>/task-spec.md
      results/                      # cross-run comparisons, best performers
      research/                     # new theories, approaches, reference notes

Commands:
  python memory.py init                   # create missing pieces (never overwrites)
  python memory.py task <name> <run>      # new run of a recurring task
                                          #   (alias: experiment)
  python memory.py status                 # what exists, what's missing
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from _lib import now_iso, project_root, safe_iterdir  # noqa: E402


INDEX_TEMPLATE = """\
# INDEX — project state as of {date}

> Entry point and routing table. Read this file FIRST in every session —
> then read ONLY what it points to. Update it after every significant run
> and before any context compaction.

<!-- ccb:index:begin -->
_Auto-maintained by ccb — filesystem facts only. Edit OUTSIDE this block._

**Updated:** (refreshed on the next ccb update)
<!-- ccb:index:end -->

**Best results so far:**
- (none yet)

**Key insights:**
- (none yet)

**Validation protocol:** memory/validation-protocol.md (MANDATORY — follow exactly)

**Current task:** memory/current-task.md
"""

AGENTS_TEMPLATE = """\
# AGENTS.md — rules for coding agents

**CRITICAL RULES:**

1. Read INDEX.md FIRST, before any other exploration. Then read only what it
   points to — do not hold the whole project in context.
2. Before any run of a recurring task, READ memory/validation-protocol.md
   and follow it exactly.
3. This is an iterative process. Never suggest "wrapping up" or "this won't
   work" until several runs with different inputs have been tried.
4. When re-running a task, always use the LARGEST current input pool
   (see memory/pool/).
5. Record every run of a recurring task in memory/tasks/<task>/<run>/.
   One-off work does NOT need a memory entry — the session log covers it.
6. Log significant decisions and insights in memory/decisions-log.md.
7. Read only the active run's folder; for other runs use the summaries in
   memory/results/ instead of raw outputs.
8. Before context compaction or session end: update INDEX.md and
   memory/current-task.md.
"""

VALIDATION_TEMPLATE = """\
# VALIDATION PROTOCOL (MANDATORY FOR EVERY RUN)

> Sacred file. Never violate, never lose. Fill in the real steps every run
> of a recurring task must follow — preparation, checks, acceptance and
> rejection criteria.

## 1. Preparation
- ...

## 2. Execution rules
- ...

## 3. Metrics / checks (mandatory set)
- ...

## 4. Constraints
- ...

## 5. Rejection criteria
- ...

**Last updated:** {date}
**Status:** ACTIVE
"""

CURRENT_TASK_TEMPLATE = """\
# Current task

**Task:** (none active)
**Run:** (none)
**Spec:** (link to memory/tasks/<task>/<run>/task-spec.md)

## Status
- (nothing active — start one with `/ccb-memory task <name> <run>`)

## Next steps
- ...
"""

DECISIONS_TEMPLATE = """\
# Decisions log

> Append-only. One dated entry per significant decision or insight.

## {date}
- memory structure initialized
"""

POOL_TEMPLATE = """\
# Pool — reusable inputs for recurring tasks

> Whatever your tasks draw from: strategies, datasets, prompts, configs,
> test corpora. Versioned snapshots live next to this file (pool-v1.md,
> pool-v2.md, ...); when the pool grows, add a snapshot and update INDEX.md.

(empty)
"""

TASK_SPEC_TEMPLATE = """\
# Task: {task_name} — run {run_id}

**Started:** {date}
**Inputs / pool version:** (fill in)
**Previous runs:** {previous}

**Goal:**
...

**What's different in this run:**
- ...

**Protocol compliance:** (fill in after the run)
"""

# path (relative to project root) → template. Created only if missing.
SCAFFOLD_FILES: dict[str, str] = {
    "INDEX.md": INDEX_TEMPLATE,
    "AGENTS.md": AGENTS_TEMPLATE,
    "memory/validation-protocol.md": VALIDATION_TEMPLATE,
    "memory/current-task.md": CURRENT_TASK_TEMPLATE,
    "memory/decisions-log.md": DECISIONS_TEMPLATE,
    "memory/pool/catalog.md": POOL_TEMPLATE,
}

SCAFFOLD_DIRS: tuple[str, ...] = (
    "memory/tasks",
    "memory/results",
    "memory/research",
)

# Pre-0.8 scaffolds used research-domain names. Recognized everywhere so an
# existing layout keeps working; new scaffolds use the generic names only.
LEGACY_EQUIVALENTS: dict[str, str] = {
    "memory/current-task.md": "memory/current-experiment.md",
    "memory/pool/catalog.md": "memory/strategy-pool/all-strategies.md",
    "memory/tasks": "memory/experiments",
    "memory/research": "memory/research-rag",
}

# Files whose presence defines "memory structure is initialized" for
# status reporting (here and in status.py / session_start.py).
KEY_FILES: tuple[str, ...] = (
    "INDEX.md",
    "memory/validation-protocol.md",
    "memory/current-task.md",
    "memory/decisions-log.md",
)


def _present(root: Path, rel: str) -> bool:
    """True if `rel` or its pre-0.8 legacy equivalent exists."""
    if (root / rel).exists():
        return True
    legacy = LEGACY_EQUIVALENTS.get(rel)
    return bool(legacy and (root / legacy).exists())


def tasks_dir(root: Path) -> Path:
    """The runs directory — memory/tasks/, or the legacy memory/experiments/."""
    new = root / "memory" / "tasks"
    legacy = root / "memory" / "experiments"
    return legacy if (not new.exists() and legacy.exists()) else new


def main() -> int:
    parser = argparse.ArgumentParser(description="ccb memory structure")
    sub = parser.add_subparsers(dest="cmd", required=True)
    sub.add_parser("init")
    p_task = sub.add_parser("task", aliases=["experiment"])
    p_task.add_argument("task_name")
    p_task.add_argument("run_id")
    sub.add_parser("status")
    args = parser.parse_args()

    root = project_root()
    if args.cmd == "init":
        return cmd_init(root)
    if args.cmd in ("task", "experiment"):
        return cmd_task(root, args.task_name, args.run_id)
    return cmd_status(root)


def cmd_init(root: Path) -> int:
    print(f"ccb memory init: {root}")
    date = now_iso()[:10]
    created, skipped = [], []
    for rel, template in SCAFFOLD_FILES.items():
        if _present(root, rel):
            skipped.append(rel)
            continue
        p = root / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(template.format(date=date), encoding="utf-8")
        created.append(rel)
    for rel in SCAFFOLD_DIRS:
        if _present(root, rel):
            continue
        d = root / rel
        d.mkdir(parents=True, exist_ok=True)
        (d / ".gitkeep").write_text("", encoding="utf-8")
        created.append(rel + "/")
    for rel in created:
        print(f"  created  {rel}")
    for rel in skipped:
        print(f"  kept     {rel} (already exists — never overwritten)")
    if not created:
        print("  nothing to do — structure already complete")
    return 0


def cmd_task(root: Path, task_name: str, run_id: str) -> int:
    for name in (task_name, run_id):
        if not name or "/" in name or "\\" in name or name.startswith("."):
            print(f"invalid name: {name!r} (no path separators, no leading dot)",
                  file=sys.stderr)
            return 2

    task_dir = tasks_dir(root) / task_name
    target = task_dir / run_id
    spec = target / "task-spec.md"
    if spec.exists():
        print(f"already exists: {spec.relative_to(root)}", file=sys.stderr)
        return 1

    previous = sorted(
        d.name for d in safe_iterdir(task_dir) if d.is_dir() and d.name != run_id
    ) if task_dir.is_dir() else []

    target.mkdir(parents=True, exist_ok=True)
    spec.write_text(
        TASK_SPEC_TEMPLATE.format(
            task_name=task_name,
            run_id=run_id,
            date=now_iso()[:10],
            previous=", ".join(previous) if previous else "(none)",
        ),
        encoding="utf-8",
    )
    print(f"created {spec.relative_to(root)}")
    if previous:
        print(f"  previous runs of {task_name}: {', '.join(previous)}")
    print("  next: fill in the inputs + goal, and update memory/current-task.md + INDEX.md")
    return 0


def cmd_status(root: Path) -> int:
    print(f"ccb memory status: {root}")
    for rel in (*SCAFFOLD_FILES, *SCAFFOLD_DIRS):
        state = "present" if _present(root, rel) else "MISSING"
        print(f"  {rel:<40} {state}")
    troot = tasks_dir(root)
    tasks = [d for d in safe_iterdir(troot) if d.is_dir()] if troot.is_dir() else []
    total_runs = sum(1 for t in tasks for r in safe_iterdir(t) if r.is_dir())
    print(f"  tasks: {len(tasks)}, runs: {total_runs}")
    missing = [rel for rel in KEY_FILES if not _present(root, rel)]
    if missing:
        print(f"  hint: run `memory.py init` to create: {', '.join(missing)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
