#!/usr/bin/env python3
"""Regenerate PROJECT.llm and per-module CONTEXT.llm from the source tree.

Modes:
  python update.py                    # full refresh: PROJECT.llm + every CONTEXT.llm
  python update.py --paths a/ b/c/    # incremental: PROJECT.llm + only those dirs
                                      #   (paths can be files; their parent dir is used)
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from _lib import (  # noqa: E402
    detect_language,
    detect_package_manager,
    iter_code_dirs,
    now_iso,
    parse_python_exports,
    project_root,
    python_imports,
    relative,
)


def main() -> int:
    parser = argparse.ArgumentParser(description="ccb context update")
    parser.add_argument(
        "--paths",
        nargs="+",
        default=None,
        help="Refresh CONTEXT.llm only in these dirs (or parents of these files)",
    )
    args = parser.parse_args()

    root = project_root()
    print(f"ccb update: {root}")

    write_project_llm(root)

    if args.paths:
        targets = _resolve_targets(args.paths, root)
        print(f"  incremental: refreshing {len(targets)} dir(s)")
    else:
        targets = iter_code_dirs(root)
        print(f"  full refresh: scanning {len(targets)} code dirs")

    for d in targets:
        write_context_llm(d, root)

    print("ccb update: done")
    return 0


def _resolve_targets(paths: list[str], root: Path) -> list[Path]:
    """Map an arbitrary list of paths (relative or absolute, files or dirs) to
    the unique set of directories whose CONTEXT.llm needs refreshing."""
    seen: dict[Path, None] = {}
    for p in paths:
        candidate = (root / p) if not Path(p).is_absolute() else Path(p)
        candidate = candidate.resolve()
        d = candidate if candidate.is_dir() else candidate.parent
        if not d.exists() or root not in d.parents and d != root:
            continue
        if d == root:
            # Root-level edits shouldn't write CONTEXT.llm into the project root.
            continue
        if not _has_source_file(d):
            continue
        seen[d] = None
    return list(seen.keys())


def _has_source_file(d: Path) -> bool:
    try:
        return any(_is_source_file(p) for p in d.iterdir() if p.is_file())
    except OSError:
        return False


def _is_source_file(p: Path) -> bool:
    return p.suffix in {".py", ".ts", ".tsx", ".js", ".jsx", ".go", ".rs", ".java", ".rb"}


def write_project_llm(root: Path) -> None:
    language = detect_language(root)
    pm = detect_package_manager(root)
    has_git = (root / ".git").exists()

    top_level = sorted(
        p for p in root.iterdir()
        if p.is_dir() and not p.name.startswith(".") and p.name not in {"venv", "env", "node_modules", "dist", "build"}
    )

    lines: list[str] = []
    lines.append(f"@project: {root.name}")
    lines.append(f"@updated: {now_iso()}")
    lines.append(f"@language: {language}")
    lines.append(f"@package_manager: {pm}")
    lines.append(f"@vcs: {'git' if has_git else 'none'}")
    lines.append("")
    lines.append("@architecture:")
    for d in top_level:
        purpose = describe_dir(d)
        lines.append(f"  {d.name}/: {purpose}")
    lines.append("")
    lines.append("@dependency_graph:")
    edges = collect_edges(root)
    if edges:
        for src, deps in sorted(edges.items()):
            lines.append(f"  {src}: [{', '.join(sorted(deps))}]")
    else:
        lines.append("  # populated as modules grow")

    target = root / "PROJECT.llm"
    target.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"  wrote {relative(target, root)}")


def write_context_llm(directory: Path, root: Path) -> None:
    py_files = sorted(directory.glob("*.py"))
    other_files = sorted(
        p for p in directory.iterdir()
        if p.is_file()
        and not p.name.startswith(".")
        and p.suffix not in {".pyc"}
        and p.name != "CONTEXT.llm"
    )

    lines: list[str] = []
    lines.append(f"@directory: {relative(directory, root)}")
    lines.append(f"@updated: {now_iso()}")
    lines.append(f"@status: in_progress")
    lines.append(f"@purpose: {describe_dir(directory)}")
    lines.append("")
    lines.append("@files:")
    for p in other_files:
        lines.append(f"  {p.name}")

    if py_files:
        lines.append("")
        lines.append("@exports:")
        for p in py_files:
            exports = parse_python_exports(p)
            for c in exports.classes:
                lines.append(f"  {p.name}::class {c}")
            for f in exports.functions:
                lines.append(f"  {p.name}::def {f}")

        imports: set[str] = set()
        for p in py_files:
            for imp in python_imports(p):
                imports.add(imp)
        if imports:
            lines.append("")
            lines.append("@imports:")
            for imp in sorted(imports):
                lines.append(f"  {imp}")

    target = directory / "CONTEXT.llm"
    target.write_text("\n".join(lines) + "\n", encoding="utf-8")


def describe_dir(d: Path) -> str:
    """Best-effort one-line description.

    Heuristics, in order:
      - first line of <d>/README.md
      - module docstring of <d>/__init__.py
      - first docstring of any *.py file
      - fallback: number of source files
    """
    readme = d / "README.md"
    if readme.exists():
        for line in readme.read_text(encoding="utf-8", errors="ignore").splitlines():
            line = line.strip().lstrip("#").strip()
            if line:
                return line[:120]

    init = d / "__init__.py"
    if init.exists():
        doc = _module_docstring(init)
        if doc:
            return doc[:120]

    for py in sorted(d.glob("*.py")):
        doc = _module_docstring(py)
        if doc:
            return f"{doc[:100]} (from {py.name})"

    src_files = sum(1 for p in d.iterdir() if p.is_file() and p.suffix in {".py", ".ts", ".js", ".go", ".rs"})
    return f"{src_files} source file(s)"


def _module_docstring(path: Path) -> str | None:
    try:
        import ast
        tree = ast.parse(path.read_text(encoding="utf-8"))
        return ast.get_docstring(tree)
    except Exception:
        return None


def collect_edges(root: Path) -> dict[str, set[str]]:
    """Map top-level package directory → set of top-level packages it imports."""
    top_pkgs: set[str] = {
        p.name for p in root.iterdir()
        if p.is_dir() and (p / "__init__.py").exists() and not p.name.startswith(".")
    }
    edges: dict[str, set[str]] = {pkg: set() for pkg in top_pkgs}
    for pkg in top_pkgs:
        for py in (root / pkg).rglob("*.py"):
            for imp in python_imports(py):
                if imp in top_pkgs and imp != pkg:
                    edges[pkg].add(imp)
    return {k: v for k, v in edges.items() if v}


if __name__ == "__main__":
    sys.exit(main())
