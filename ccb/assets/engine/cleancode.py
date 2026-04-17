#!/usr/bin/env python3
"""Heuristic dead-code detector for Python projects.

Flags top-level functions/classes that are defined but never referenced
elsewhere in the project. Conservative — only reports candidates, never deletes.
"""
from __future__ import annotations

import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from _lib import IGNORED_DIRS, parse_python_exports, project_root, relative, safe_rglob  # noqa: E402


def main() -> int:
    root = project_root()
    py_files = list(_iter_py(root))
    if not py_files:
        print("ccb cleancode: no .py files found")
        return 0

    # Build: name -> [(file, kind)] where it's defined
    defs: dict[str, list[tuple[Path, str]]] = defaultdict(list)
    for f in py_files:
        exp = parse_python_exports(f)
        for c in exp.classes:
            defs[c].append((f, "class"))
        for fn in exp.functions:
            defs[fn].append((f, "def"))

    # Collect all source text (cheap regex scan for usage)
    blob = "\n".join(f.read_text(encoding="utf-8", errors="ignore") for f in py_files)

    candidates: list[tuple[Path, str, str]] = []
    for name, locations in defs.items():
        if name.startswith(("test_", "_")):
            continue
        usages = blob.count(name)
        if usages <= len(locations):
            for path, kind in locations:
                candidates.append((path, kind, name))

    if not candidates:
        print("ccb cleancode: no dead-code candidates")
        return 0

    print(f"ccb cleancode: {len(candidates)} candidate(s)")
    for path, kind, name in sorted(candidates, key=lambda c: (str(c[0]), c[2])):
        print(f"  {relative(path, root):<60} {kind} {name}")
    return 0


def _iter_py(root: Path):
    for p in safe_rglob(root, "*.py"):
        try:
            if any(part in IGNORED_DIRS or part.startswith(".") for part in p.relative_to(root).parts[:-1]):
                continue
        except ValueError:
            continue
        yield p


if __name__ == "__main__":
    sys.exit(main())
