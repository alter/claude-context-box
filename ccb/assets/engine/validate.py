#!/usr/bin/env python3
"""Lint ccb-managed context files for common drift issues."""
from __future__ import annotations

import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from _lib import IGNORED_DIRS, project_root, relative, safe_iterdir, safe_rglob  # noqa: E402

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
    for ctx in safe_rglob(root, "CONTEXT.llm"):
        if any(part in IGNORED_DIRS for part in ctx.parts):
            continue
        d = ctx.parent
        if d == root:
            continue
        if not any(_is_source_file(f) for f in safe_iterdir(d) if f.is_file()):
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
    """Walk via os.walk so unreadable subtrees are skipped, not raised."""
    import os
    out: list[Path] = []
    for dirpath, dirnames, filenames in os.walk(root, onerror=lambda _e: None):
        dirnames[:] = [d for d in dirnames if d not in IGNORED_DIRS and not d.startswith(".")]
        d = Path(dirpath)
        if d == root:
            continue
        if any(_is_source_filename(name) for name in filenames):
            out.append(d)
    return out


_SOURCE_SUFFIXES = (".py", ".ts", ".tsx", ".js", ".jsx", ".go", ".rs", ".java")


def _is_source_file(p: Path) -> bool:
    return p.suffix in _SOURCE_SUFFIXES


def _is_source_filename(name: str) -> bool:
    return name.endswith(_SOURCE_SUFFIXES)


def _is_stale(ctx: Path, dir_: Path) -> bool:
    try:
        ctx_mtime = ctx.stat().st_mtime
    except OSError:
        return False
    try:
        entries = list(dir_.iterdir())
    except (PermissionError, OSError):
        return False
    for f in entries:
        try:
            if not f.is_file():
                continue
            if _is_source_file(f) and f.stat().st_mtime > ctx_mtime:
                return True
        except OSError:
            continue
    return False


if __name__ == "__main__":
    sys.exit(main())
