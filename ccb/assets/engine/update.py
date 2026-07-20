#!/usr/bin/env python3
"""Regenerate PROJECT.llm and per-module CONTEXT.llm from the source tree.

Modes:
  python update.py                    # full refresh: PROJECT.llm + every CONTEXT.llm
  python update.py --paths a/ b/c/    # incremental: PROJECT.llm + only those dirs
                                      #   (paths can be files; their parent dir is used)
"""
from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from _lib import (  # noqa: E402
    IGNORED_DIRS,
    JS_TS_SUFFIXES,
    SOURCE_SUFFIXES,
    count_source_files,
    detect_language,
    detect_package_manager,
    imports_for_path,
    iter_code_dirs,
    now_iso,
    parse_exports_for_path,
    project_root,
    relative,
    safe_iterdir,
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
    refresh_index_block(root)

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
        return any(p.is_file() and p.suffix in SOURCE_SUFFIXES for p in d.iterdir())
    except OSError:
        return False


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
    if _write_if_changed(target, "\n".join(lines) + "\n"):
        print(f"  wrote {relative(target, root)}")


def write_context_llm(directory: Path, root: Path) -> None:
    try:
        entries = list(directory.iterdir())
    except OSError:
        return

    other_files = sorted(
        p for p in entries
        if p.is_file()
        and not p.name.startswith(".")
        and p.suffix != ".pyc"
        and p.name != "CONTEXT.llm"
    )
    source_files = [p for p in other_files if p.suffix in SOURCE_SUFFIXES]

    lines: list[str] = []
    lines.append(f"@directory: {relative(directory, root)}")
    lines.append(f"@updated: {now_iso()}")
    lines.append("@status: in_progress")
    lines.append(f"@purpose: {describe_dir(directory)}")
    lines.append("")
    lines.append("@files:")
    for p in other_files:
        lines.append(f"  {p.name}")

    if source_files:
        export_lines: list[str] = []
        import_set: set[str] = set()
        for p in source_files:
            exports = parse_exports_for_path(p)
            for c in exports.classes:
                export_lines.append(f"  {p.name}::class {c}")
            for f in exports.functions:
                kind = "def" if p.suffix == ".py" else "fn"
                export_lines.append(f"  {p.name}::{kind} {f}")
            for c in exports.constants:
                export_lines.append(f"  {p.name}::const {c}")
            for imp in imports_for_path(p):
                import_set.add(imp)

        if export_lines:
            lines.append("")
            lines.append("@exports:")
            lines.extend(export_lines)

        if import_set:
            lines.append("")
            lines.append("@imports:")
            for imp in sorted(import_set):
                lines.append(f"  {imp}")

    target = directory / "CONTEXT.llm"
    _write_if_changed(target, "\n".join(lines) + "\n")


def _write_if_changed(target: Path, text: str) -> bool:
    """Write only when content differs, ignoring volatile timestamp lines.

    Unconditional rewrites poke file watchers (dev servers, --watch test
    runners) in the source dirs after every session, and `@updated` alone
    would make the content always differ. Skipping the write also makes
    `@updated` mean "last real change", which is the useful reading.
    """
    if target.exists():
        try:
            old = target.read_text(encoding="utf-8")
        except OSError:
            old = None
        if old is not None and _stable_lines(old) == _stable_lines(text):
            return False
    target.write_text(text, encoding="utf-8")
    return True


_VOLATILE_PREFIXES = ("@updated:", "**Updated:**")


def _stable_lines(text: str) -> list[str]:
    return [
        line for line in text.splitlines()
        if not line.strip().startswith(_VOLATILE_PREFIXES)
    ]


# INDEX.md auto-maintained block ------------------------------------------
#
# INDEX.md is human/agent-owned (see memory.py) — ccb never rewrites it
# wholesale. The one exception is this marker-delimited block of
# filesystem-derived FACTS: experiment ranges, iteration counts, pools,
# latest session log. Insights and results stay outside the markers and are
# never touched. Same ownership model as the ccb block in CLAUDE.md.

INDEX_BEGIN = "<!-- ccb:index:begin -->"
INDEX_END = "<!-- ccb:index:end -->"


def refresh_index_block(root: Path) -> None:
    """Refresh the auto-generated fact block inside INDEX.md, if it exists.

    Never creates INDEX.md (that's `memory.py init`'s job) and never touches
    content outside the markers. A hand-written INDEX.md without markers gets
    the block appended at the end.
    """
    index = root / "INDEX.md"
    if not index.is_file():
        return
    try:
        text = index.read_text(encoding="utf-8")
    except OSError:
        return

    block = "\n".join([INDEX_BEGIN, *_index_facts(root), INDEX_END])

    begin = text.find(INDEX_BEGIN)
    end = text.find(INDEX_END)
    if begin != -1 and end != -1 and end >= begin:
        new_text = text[:begin] + block + text[end + len(INDEX_END):]
    else:
        new_text = text.rstrip("\n") + "\n\n" + block + "\n"

    if _stable_lines(new_text) != _stable_lines(text):
        index.write_text(new_text, encoding="utf-8")
        print(f"  refreshed {relative(index, root)} fact block")


def _index_facts(root: Path) -> list[str]:
    lines = [
        "_Auto-maintained by ccb — filesystem facts only. Edit OUTSIDE this block._",
        "",
        f"**Updated:** {now_iso()}",
    ]

    # "pool" / "tasks" are the 0.8+ names; "strategy-pool" / "experiments"
    # the pre-0.8 ones — a scaffold has one set or the other.
    pool_dir = root / "memory" / "pool"
    if not pool_dir.is_dir():
        pool_dir = root / "memory" / "strategy-pool"
    pools = sorted(p.name for p in safe_iterdir(pool_dir) if p.is_file() and p.suffix == ".md")
    if pools:
        lines.append(f"**Pool:** {', '.join(pools)}")

    tasks_root = root / "memory" / "tasks"
    if not tasks_root.is_dir():
        tasks_root = root / "memory" / "experiments"
    tasks = sorted((d for d in safe_iterdir(tasks_root) if d.is_dir()), key=lambda d: d.name)
    latest_spec: tuple[float, str] | None = None
    if tasks:
        lines.append("**Tasks:**")
        for t in tasks:
            runs = sorted((d for d in safe_iterdir(t) if d.is_dir()), key=lambda d: d.name)
            newest = ""
            for run in runs:
                spec = run / "task-spec.md"
                try:
                    mtime = spec.stat().st_mtime if spec.exists() else run.stat().st_mtime
                except OSError:
                    continue
                if latest_spec is None or mtime > latest_spec[0]:
                    latest_spec = (mtime, f"{t.name}/{run.name}")
                if not newest or mtime >= newest[0]:
                    newest = (mtime, run.name)
            detail = f", latest: {newest[1]}" if newest else ""
            lines.append(f"- {t.name}: {len(runs)} run(s){detail}")
    if latest_spec:
        rel_tasks = tasks_root.name
        lines.append(f"**Most recently active:** memory/{rel_tasks}/{latest_spec[1]}/")

    daily_dir = root / ".ccb" / "daily_log"
    logs = sorted(p.name for p in safe_iterdir(daily_dir) if p.suffix == ".md")
    if logs:
        lines.append(f"**Latest session log:** .ccb/daily_log/{logs[-1]}")

    return lines


def describe_dir(d: Path) -> str:
    """Best-effort one-line description.

    Heuristics, in order:
      - first non-empty line of <d>/README.md
      - module docstring of <d>/__init__.py (Python)
      - JSDoc summary at top of an entry-point file (Next.js page.tsx,
        layout.tsx; generic index.{ts,tsx,js,jsx}; Vite/Vue main.{ts,js})
      - first docstring of any *.py file in this dir
      - fallback: total recursive source-file count under this dir
    """
    readme = d / "README.md"
    if readme.exists():
        for line in readme.read_text(encoding="utf-8", errors="ignore").splitlines():
            line = line.strip().lstrip("#").strip()
            if line:
                return _summarize(line)

    init = d / "__init__.py"
    if init.exists():
        doc = _module_docstring(init)
        if doc:
            return _summarize(doc)

    candidates = []
    for stem in ("index", "page", "layout", "main"):
        for ext in (".ts", ".tsx", ".js", ".jsx", ".mjs", ".cjs"):
            candidates.append(d / f"{stem}{ext}")
    for c in candidates:
        if c.exists():
            doc = _js_top_doc(c)
            if doc:
                return f"{_summarize(doc)} (from {c.name})"

    for py in sorted(d.glob("*.py")):
        doc = _module_docstring(py)
        if doc:
            return f"{_summarize(doc)} (from {py.name})"

    total = count_source_files(d, recursive=True)
    return f"{total} source file(s)"


def _summarize(text: str, max_len: int = 100) -> str:
    """Reduce a multi-line / long doc to a single short line.

    Keeps only the first paragraph (until blank line), collapses internal
    whitespace, truncates on a word boundary with an ellipsis if still too
    long. Output is always single-line and ≤ max_len characters.
    """
    paragraph = text.split("\n\n", 1)[0]
    one_line = " ".join(paragraph.split())
    if len(one_line) <= max_len:
        return one_line
    cutoff = one_line.rfind(" ", 0, max_len - 1)
    if cutoff < max_len // 2:
        cutoff = max_len - 1
    return one_line[:cutoff].rstrip(" ,;:.") + "…"


def _js_top_doc(path: Path) -> str | None:
    """First /** ... */ JSDoc block at the top of a JS/TS file, if any."""
    try:
        text = path.read_text(encoding="utf-8", errors="ignore")[:2000]
    except OSError:
        return None
    import re
    m = re.match(r"\s*/\*\*(.*?)\*/", text, re.DOTALL)
    if not m:
        return None
    body = m.group(1)
    # First non-empty line, stripped of leading * and whitespace.
    for line in body.splitlines():
        line = line.strip().lstrip("*").strip()
        if line:
            return line
    return None


def _module_docstring(path: Path) -> str | None:
    try:
        import ast
        tree = ast.parse(path.read_text(encoding="utf-8"))
        return ast.get_docstring(tree)
    except Exception:
        return None


def collect_edges(root: Path) -> dict[str, set[str]]:
    """Map top-level dir → set of top-level dirs it imports from.

    Works for any language whose imports `imports_for_path` understands.
    For JS/TS we also resolve common alias prefixes (`@/foo` → `foo`,
    `~/foo` → `foo`) and walk relative imports up to find which top-level
    directory the resolved file lives in.
    """
    skip = {"venv", "env", "node_modules", "dist", "build"}
    top_dirs: set[str] = {
        p.name for p in root.iterdir()
        if p.is_dir() and not p.name.startswith(".") and p.name not in skip
    }
    if not top_dirs:
        return {}

    edges: dict[str, set[str]] = {d: set() for d in top_dirs}

    for src_dir in top_dirs:
        src_path = root / src_dir
        # Pruned walk instead of rglob("*"): nested venvs / node_modules /
        # data dumps would otherwise be enumerated file-by-file, which is
        # ruinously slow on WSL /mnt/c and network mounts.
        for dirpath, dirnames, filenames in os.walk(src_path, onerror=lambda _e: None):
            dirnames[:] = [
                d for d in dirnames if d not in IGNORED_DIRS and not d.startswith(".")
            ]
            for name in filenames:
                if not name.endswith(SOURCE_SUFFIXES):
                    continue
                f = Path(dirpath) / name
                for spec in imports_for_path(f):
                    target = _resolve_import_to_top(spec, f, root, top_dirs)
                    if target and target != src_dir:
                        edges[src_dir].add(target)
    return {k: v for k, v in edges.items() if v}


def _resolve_import_to_top(spec: str, source_file: Path, root: Path, top_dirs: set[str]) -> str | None:
    """Best-effort: turn an import specifier into the top-level dir it targets.

    Handles:
      - bare package names ("react") → returned only if the name happens to
        be a top-level dir (rare, usually means workspace package)
      - alias prefixes "@/foo/bar" / "~/foo/bar" → "foo"
      - relative paths "../../lib/x" → resolve, find top-level under root
      - absolute-ish "/lib/x" treated like relative-from-root
    """
    if not spec:
        return None
    # Strip Next.js / Vite / TS-paths style aliases.
    for prefix in ("@/", "~/", "@app/", "@/lib/", "@/app/"):
        if spec.startswith(prefix):
            head = spec[len(prefix):].split("/")[0]
            return head if head in top_dirs else None

    if spec.startswith("./") or spec.startswith("../") or spec.startswith("/"):
        try:
            base = source_file.parent if not spec.startswith("/") else root
            resolved = (base / spec).resolve()
            rel = resolved.relative_to(root)
            head = rel.parts[0] if rel.parts else ""
            return head if head in top_dirs else None
        except (ValueError, OSError):
            return None

    head = spec.split("/")[0]
    return head if head in top_dirs else None


# Backwards-compat alias for older importers (e.g. capture_session.py).
def python_imports(path: Path):  # type: ignore[no-redef]
    from _lib import python_imports as _pi
    return _pi(path)


if __name__ == "__main__":
    sys.exit(main())
