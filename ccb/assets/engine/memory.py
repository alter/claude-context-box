#!/usr/bin/env python3
"""Scaffold and manage the memory/ structure for iterative research projects.

The layout keeps context, a validation protocol, and iteration history across
many returns to the same experiment ranges (see README "Memory structure"):

    INDEX.md                        # entry point — read first every session
    AGENTS.md                       # critical rules for any coding agent
    memory/
      validation-protocol.md        # sacred file — never violate
      current-experiment.md         # the active iteration
      decisions-log.md              # key decisions and insights
      strategy-pool/all-strategies.md
      experiments/<range>/<version>/task-spec.md
      results/
      research-rag/

Commands:
  python memory.py init                          # create missing pieces (never overwrites)
  python memory.py experiment <range> <version>  # new iteration folder + task-spec.md
  python memory.py status                        # what exists, what's missing
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from _lib import now_iso, project_root, safe_iterdir  # noqa: E402


INDEX_TEMPLATE = """\
# INDEX — project state as of {date}

> Entry point. Read this file FIRST in every session. Update it after every
> significant run and before any context compaction.

<!-- ccb:index:begin -->
_Auto-maintained by ccb — filesystem facts only. Edit OUTSIDE this block._

**Updated:** (refreshed on the next ccb update)
<!-- ccb:index:end -->

**Current strategy pool:** (none yet — see memory/strategy-pool/)

**Best results so far:**
- (none yet)

**Key insights:**
- (none yet)

**Validation protocol:** memory/validation-protocol.md (MANDATORY — follow exactly)

**Current experiment:** memory/current-experiment.md
"""

AGENTS_TEMPLATE = """\
# AGENTS.md — rules for coding agents

**CRITICAL RULES:**

1. Before any backtest, generation, or analysis, READ memory/validation-protocol.md
   and follow it exactly.
2. This is an iterative research process. Never suggest "wrapping up" or "this
   won't work" until several passes with different strategy pools have run.
3. When returning to a previous experiment range, always use the LARGEST
   current strategy pool.
4. Record every iteration in memory/experiments/<range>/<version>/.
5. Log significant decisions and insights in memory/decisions-log.md.
6. Before context compaction or session end: update INDEX.md and
   memory/current-experiment.md.
"""

VALIDATION_TEMPLATE = """\
# VALIDATION PROTOCOL (MANDATORY FOR EVERY EXPERIMENT)

> Sacred file. Never violate, never lose. Fill in your real steps below.

## 1. Data Preparation
- ...

## 2. IS / OOS / Forward Split
- ...

## 3. Metrics (mandatory set)
- ...

## 4. Risk & Portfolio Rules
- ...

## 5. Rejection Criteria
- ...

**Last updated:** {date}
**Status:** ACTIVE
"""

CURRENT_EXPERIMENT_TEMPLATE = """\
# Current experiment

**Started:** (not started)
**Range:** (none)
**Pool:** (none)
**Spec:** (link to memory/experiments/<range>/<version>/task-spec.md)

## Status
- (nothing active — start one with `/ccb-memory experiment <range> <version>`)

## Next steps
- ...
"""

DECISIONS_TEMPLATE = """\
# Decisions log

> Append-only. One dated entry per significant decision or insight.

## {date}
- memory structure initialized
"""

ALL_STRATEGIES_TEMPLATE = """\
# Strategy pool — all strategies

> Master list. Versioned snapshots live next to this file as pool-vN-<size>.md.
> When the pool grows, create a new pool-vN file and update INDEX.md.

(empty)
"""

TASK_SPEC_TEMPLATE = """\
# Task: {range_name} — {version}

**Started:** {date}
**Pool used:** (fill in, e.g. pool-v3-500)
**Previous versions:** {previous}

**Goal:**
...

**What's different in this run:**
- ...

**Validation Protocol Compliance:** (fill in after the run)
"""

# path (relative to project root) → template. Created only if missing.
SCAFFOLD_FILES: dict[str, str] = {
    "INDEX.md": INDEX_TEMPLATE,
    "AGENTS.md": AGENTS_TEMPLATE,
    "memory/validation-protocol.md": VALIDATION_TEMPLATE,
    "memory/current-experiment.md": CURRENT_EXPERIMENT_TEMPLATE,
    "memory/decisions-log.md": DECISIONS_TEMPLATE,
    "memory/strategy-pool/all-strategies.md": ALL_STRATEGIES_TEMPLATE,
}

SCAFFOLD_DIRS: tuple[str, ...] = (
    "memory/experiments",
    "memory/results",
    "memory/research-rag",
)

# Files whose presence defines "memory structure is initialized" for
# status reporting (here and in status.py / session_start.py).
KEY_FILES: tuple[str, ...] = (
    "INDEX.md",
    "memory/validation-protocol.md",
    "memory/current-experiment.md",
    "memory/decisions-log.md",
)


def main() -> int:
    parser = argparse.ArgumentParser(description="ccb memory structure")
    sub = parser.add_subparsers(dest="cmd", required=True)
    sub.add_parser("init")
    p_exp = sub.add_parser("experiment")
    p_exp.add_argument("range_name")
    p_exp.add_argument("version")
    sub.add_parser("status")
    args = parser.parse_args()

    root = project_root()
    if args.cmd == "init":
        return cmd_init(root)
    if args.cmd == "experiment":
        return cmd_experiment(root, args.range_name, args.version)
    return cmd_status(root)


def cmd_init(root: Path) -> int:
    print(f"ccb memory init: {root}")
    date = now_iso()[:10]
    created, skipped = [], []
    for rel, template in SCAFFOLD_FILES.items():
        p = root / rel
        if p.exists():
            skipped.append(rel)
            continue
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(template.format(date=date), encoding="utf-8")
        created.append(rel)
    for rel in SCAFFOLD_DIRS:
        d = root / rel
        if not d.exists():
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


def cmd_experiment(root: Path, range_name: str, version: str) -> int:
    for name in (range_name, version):
        if not name or "/" in name or "\\" in name or name.startswith("."):
            print(f"invalid name: {name!r} (no path separators, no leading dot)",
                  file=sys.stderr)
            return 2

    range_dir = root / "memory" / "experiments" / range_name
    target = range_dir / version
    spec = target / "task-spec.md"
    if spec.exists():
        print(f"already exists: {spec.relative_to(root)}", file=sys.stderr)
        return 1

    previous = sorted(
        d.name for d in safe_iterdir(range_dir) if d.is_dir() and d.name != version
    ) if range_dir.is_dir() else []

    target.mkdir(parents=True, exist_ok=True)
    spec.write_text(
        TASK_SPEC_TEMPLATE.format(
            range_name=range_name,
            version=version,
            date=now_iso()[:10],
            previous=", ".join(previous) if previous else "(none)",
        ),
        encoding="utf-8",
    )
    print(f"created {spec.relative_to(root)}")
    if previous:
        print(f"  previous versions in {range_name}: {', '.join(previous)}")
    print("  next: fill in the pool + goal, and update memory/current-experiment.md + INDEX.md")
    return 0


def cmd_status(root: Path) -> int:
    print(f"ccb memory status: {root}")
    for rel in (*SCAFFOLD_FILES, *SCAFFOLD_DIRS):
        p = root / rel
        state = "present" if p.exists() else "MISSING"
        print(f"  {rel:<40} {state}")
    exp_root = root / "memory" / "experiments"
    ranges = [d for d in safe_iterdir(exp_root) if d.is_dir()] if exp_root.is_dir() else []
    total_iters = sum(
        1 for r in ranges for v in safe_iterdir(r) if v.is_dir()
    )
    print(f"  experiment ranges: {len(ranges)}, iterations: {total_iters}")
    missing = [rel for rel in KEY_FILES if not (root / rel).exists()]
    if missing:
        print(f"  hint: run `memory.py init` to create: {', '.join(missing)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
