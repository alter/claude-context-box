#!/usr/bin/env python3
"""Lint ccb-managed context files for common drift issues."""
from __future__ import annotations

import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from _lib import IGNORED_DIRS, project_root, relative  # noqa: E402

STALE_AFTER_SECONDS = 7 * 24 * 3600


def main() -> int:
    root = project_root()
    issues: list[tuple[str, str]] = []

    project_llm = root / "PROJECT.llm"
    if not project_llm.exists():
        issues.append(("error", "PROJECT.llm missing — run /ccb-update"))

    code_dirs = _code_dirs(root)
    for d in code_dirs:
        ctx = d / "CONTEXT.llm"
        if not ctx.exists():
            issues.append(("warn", f"missing CONTEXT.llm: {relative(d, root)}/"))
            continue
        if _is_stale(ctx, d):
            issues.append(("warn", f"stale CONTEXT.llm: {relative(d, root)}/ (older than its source)"))

    # Orphan CONTEXT.llm — files in directories with no source.
    for ctx in root.rglob("CONTEXT.llm"):
        if any(part in IGNORED_DIRS for part in ctx.parts):
            continue
        d = ctx.parent
        if d == root:
            continue
        if not any(_is_source_file(f) for f in d.iterdir() if f.is_file()):
            issues.append(("warn", f"orphan CONTEXT.llm: {relative(ctx, root)} (no source files)"))

    if not issues:
        print("ccb validate: no issues")
        return 0

    errors = [i for i in issues if i[0] == "error"]
    warns = [i for i in issues if i[0] == "warn"]
    print(f"ccb validate: {len(errors)} error(s), {len(warns)} warning(s)")
    for sev, msg in issues:
        print(f"  [{sev}] {msg}")
    return 1 if errors else 0


def _code_dirs(root: Path) -> list[Path]:
    out: list[Path] = []
    for sub in root.rglob("*"):
        if not sub.is_dir():
            continue
        rel_parts = sub.relative_to(root).parts
        if any(part in IGNORED_DIRS or part.startswith(".") for part in rel_parts):
            continue
        if any(_is_source_file(f) for f in sub.iterdir() if f.is_file()):
            out.append(sub)
    return out


def _is_source_file(p: Path) -> bool:
    return p.suffix in {".py", ".ts", ".tsx", ".js", ".jsx", ".go", ".rs", ".java"}


def _is_stale(ctx: Path, dir_: Path) -> bool:
    ctx_mtime = ctx.stat().st_mtime
    for f in dir_.iterdir():
        if f.is_file() and _is_source_file(f) and f.stat().st_mtime > ctx_mtime:
            return True
    return False


if __name__ == "__main__":
    sys.exit(main())
