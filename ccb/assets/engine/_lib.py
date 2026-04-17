"""Shared helpers for ccb engine scripts.

Engine scripts run in the *target* project (installed at .claude/ccb-engine/).
They use only the standard library — no pip dependencies.
"""
from __future__ import annotations

import ast
import os
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

# Directories that never get a CONTEXT.llm and never count for architecture.
IGNORED_DIRS = frozenset(
    {
        ".git", ".hg", ".svn",
        ".venv", "venv", "env", "ENV",
        "__pycache__", ".pytest_cache", ".mypy_cache", ".ruff_cache",
        "node_modules",
        "dist", "build", ".eggs",
        ".local", ".checkpoints",
        ".ccb", ".claude", ".idea", ".vscode",
    }
)

# Files that mark a "project root" (used to detect language and PM).
LANGUAGE_MARKERS: list[tuple[str, str]] = [
    ("pyproject.toml", "python"),
    ("setup.py", "python"),
    ("requirements.txt", "python"),
    ("package.json", "node"),
    ("go.mod", "go"),
    ("Cargo.toml", "rust"),
    ("Gemfile", "ruby"),
    ("pom.xml", "java"),
    ("composer.json", "php"),
]


def project_root() -> Path:
    return Path(os.environ.get("CLAUDE_PROJECT_DIR", os.getcwd())).resolve()


def now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def detect_language(root: Path) -> str:
    for marker, lang in LANGUAGE_MARKERS:
        if (root / marker).exists():
            return lang
    return "unknown"


def detect_package_manager(root: Path) -> str:
    if (root / "poetry.lock").exists():
        return "poetry"
    if (root / "uv.lock").exists():
        return "uv"
    if (root / "Pipfile.lock").exists():
        return "pipenv"
    if (root / "pyproject.toml").exists() or (root / "requirements.txt").exists():
        return "pip"
    if (root / "pnpm-lock.yaml").exists():
        return "pnpm"
    if (root / "yarn.lock").exists():
        return "yarn"
    if (root / "package-lock.json").exists():
        return "npm"
    if (root / "go.mod").exists():
        return "go"
    if (root / "Cargo.toml").exists():
        return "cargo"
    return "none"


def iter_code_dirs(root: Path) -> list[Path]:
    """Yield directories that look like code modules (have at least one source file).

    Tolerates unreadable directories (data dirs owned by other users, broken
    symlinks, fuse mounts that are down) — they're skipped, not raised.
    """
    out: list[Path] = []
    for dirpath, dirnames, filenames in os.walk(root, onerror=lambda _e: None):
        # mutate dirnames in-place to prune the walk
        dirnames[:] = [d for d in dirnames if d not in IGNORED_DIRS and not d.startswith(".")]
        d = Path(dirpath)
        if d == root:
            continue
        if any(_is_source_file(f) for f in filenames):
            out.append(d)
    return out


def safe_iterdir(d: Path):
    """Yield entries in `d`, skipping silently on PermissionError / OSError."""
    try:
        yield from d.iterdir()
    except (PermissionError, OSError):
        return


def safe_rglob(root: Path, pattern: str = "*"):
    """Like `root.rglob(pattern)` but never raises on unreadable subtrees."""
    for dirpath, dirnames, filenames in os.walk(root, onerror=lambda _e: None):
        d = Path(dirpath)
        # match files
        for name in filenames:
            p = d / name
            if p.match(pattern):
                yield p
        # match directories themselves
        for name in dirnames:
            p = d / name
            if p.match(pattern):
                yield p


# Single source of truth for source-file extensions across the engine.
SOURCE_SUFFIXES: tuple[str, ...] = (
    ".py",
    ".ts", ".tsx", ".mts", ".cts",
    ".js", ".jsx", ".mjs", ".cjs",
    ".vue", ".svelte",
    ".go",
    ".rs",
    ".java", ".kt",
    ".rb",
    ".php",
    ".swift",
)

# Subset that the TypeScript/JavaScript parsers handle.
JS_TS_SUFFIXES: frozenset[str] = frozenset({
    ".ts", ".tsx", ".mts", ".cts",
    ".js", ".jsx", ".mjs", ".cjs",
})


def _is_source_file(name: str) -> bool:
    return name.endswith(SOURCE_SUFFIXES)


@dataclass
class Exports:
    """Per-file exports. classes/functions cover both Python and JS/TS."""
    classes: list[str]
    functions: list[str]
    constants: list[str]   # for `export const X = ...` / module-level Python assigns


# Python ----------------------------------------------------------------


def parse_python_exports(path: Path) -> Exports:
    """Best-effort parse — returns empty exports on syntax error."""
    try:
        tree = ast.parse(path.read_text(encoding="utf-8"))
    except (SyntaxError, UnicodeDecodeError, OSError):
        return Exports(classes=[], functions=[], constants=[])
    classes: list[str] = []
    functions: list[str] = []
    for node in tree.body:
        if isinstance(node, ast.ClassDef) and not node.name.startswith("_"):
            classes.append(node.name)
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and not node.name.startswith("_"):
            functions.append(node.name)
    return Exports(classes=classes, functions=functions, constants=[])


def python_imports(path: Path) -> list[str]:
    try:
        tree = ast.parse(path.read_text(encoding="utf-8"))
    except (SyntaxError, UnicodeDecodeError, OSError):
        return []
    seen: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                seen.append(alias.name.split(".")[0])
        elif isinstance(node, ast.ImportFrom) and node.module:
            seen.append(node.module.split(".")[0])
    out: list[str] = []
    for s in seen:
        if s not in out:
            out.append(s)
    return out


# JavaScript / TypeScript -----------------------------------------------
#
# We parse with regex rather than a real AST because shipping Babel/SWC/
# tree-sitter into the engine venv would be a heavyweight dependency the
# rest of ccb explicitly avoids (stdlib only). The patterns below are
# permissive — they cover ESM exports, default exports, named re-exports,
# and TypeScript-only declarations (interface/type/enum). Misses a few
# exotic forms (decorators, ambient modules) but covers >95% of real code.

_JS_LINE_COMMENT = re.compile(r"//[^\n]*")
_JS_BLOCK_COMMENT = re.compile(r"/\*.*?\*/", re.DOTALL)
_JS_STRING = re.compile(r"(?:\"(?:\\.|[^\"\\])*\"|'(?:\\.|[^'\\])*'|`(?:\\.|[^`\\])*`)")

# Match `export function name`, `export async function name`, `export default function name`
_JS_EXPORT_FUNC = re.compile(
    r"^\s*export\s+(?:default\s+)?(?:async\s+)?function\s*\*?\s*([A-Za-z_$][\w$]*)",
    re.MULTILINE,
)
# Match `export class Name`, `export default class Name`, `export abstract class Name`
_JS_EXPORT_CLASS = re.compile(
    r"^\s*export\s+(?:default\s+)?(?:abstract\s+)?class\s+([A-Za-z_$][\w$]*)",
    re.MULTILINE,
)
# Match `export const|let|var name = ...` (single declaration; tuple destructuring not handled)
_JS_EXPORT_CONST = re.compile(
    r"^\s*export\s+(?:const|let|var)\s+([A-Za-z_$][\w$]*)",
    re.MULTILINE,
)
# TypeScript-only: interface / type / enum
_TS_EXPORT_DECL = re.compile(
    r"^\s*export\s+(?:default\s+)?(?:interface|type|enum)\s+([A-Za-z_$][\w$]*)",
    re.MULTILINE,
)
# Named re-exports: `export { a, b as c, default as d } from "..."` (or without `from`)
_JS_EXPORT_NAMED = re.compile(
    r"^\s*export\s*\{([^}]+)\}",
    re.MULTILINE,
)
# `import ... from "module"` / `import "module"` / `require("module")` /
# `import("module")` — group 1 (non-empty in exactly one alternative) is the
# module specifier. The static-import body uses non-greedy `.*?` so it stops
# at the `from` keyword instead of swallowing it.
_JS_IMPORT = re.compile(
    r"""(?:
        ^\s*import\s+(?:.*?\s+from\s+)?['"]([^'"]+)['"]   # static import (named/default/side-effect)
        |
        \brequire\s*\(\s*['"]([^'"]+)['"]\s*\)            # CommonJS
        |
        \bimport\s*\(\s*['"]([^'"]+)['"]\s*\)             # dynamic import
    )""",
    re.MULTILINE | re.VERBOSE | re.DOTALL,
)


def _strip_js_comments(text: str) -> str:
    """Remove only comments — leaves string literals intact.

    Used for import scanning, where the module specifier IS a string literal
    that we need to keep readable.
    """
    text = _JS_LINE_COMMENT.sub("", text)
    return _JS_BLOCK_COMMENT.sub("", text)


def _strip_js_comments_and_strings(text: str) -> str:
    """Remove comments AND zero out string literals.

    Used for export scanning so things like `const SQL = "export class Fake {}"`
    don't get misread as exports. Side effect: unusable for import scanning
    because module specifiers ARE strings — use _strip_js_comments instead.
    """
    text = _strip_js_comments(text)
    return _JS_STRING.sub('""', text)


def parse_js_exports(path: Path) -> Exports:
    """Regex-based exports for .js/.jsx/.ts/.tsx/.mjs/.cjs/.mts/.cts.

    Misses: TypeScript decorators applied to exported items, ambient
    `declare module {}` blocks, namespace exports. Catches the 95% case.
    """
    try:
        raw = path.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return Exports(classes=[], functions=[], constants=[])
    text = _strip_js_comments_and_strings(raw)

    functions = list(dict.fromkeys(_JS_EXPORT_FUNC.findall(text)))
    classes = list(dict.fromkeys(_JS_EXPORT_CLASS.findall(text) + _TS_EXPORT_DECL.findall(text)))
    constants = list(dict.fromkeys(_JS_EXPORT_CONST.findall(text)))

    # Named re-exports: pull out individual names. `default as foo` → keep `foo`,
    # `bar as baz` → keep `baz`, plain `bar` → keep `bar`.
    for group in _JS_EXPORT_NAMED.findall(text):
        for token in group.split(","):
            token = token.strip()
            if not token:
                continue
            # strip optional `<name> as <alias>`
            parts = [t.strip() for t in token.split(" as ")]
            name = parts[-1]
            if name and name not in functions and name not in classes and name not in constants:
                constants.append(name)

    return Exports(classes=classes, functions=functions, constants=constants)


def js_imports(path: Path) -> list[str]:
    """Yield the raw module specifiers a JS/TS file imports.

    Returns specifiers as written: `react`, `@/lib/foo`, `./bar`, `../../baz`.
    Caller decides what to do with relative vs package vs alias paths.
    """
    try:
        raw = path.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return []
    # Strip only comments — keep string literals so the regex can capture
    # the module specifier inside them.
    text = _strip_js_comments(raw)
    seen: list[str] = []
    for m in _JS_IMPORT.findall(text):
        # m is a 3-tuple from the alternation, exactly one element non-empty.
        spec = next((g for g in m if g), "")
        if spec and spec not in seen:
            seen.append(spec)
    return seen


# Polymorphic dispatch ---------------------------------------------------


def parse_exports_for_path(path: Path) -> Exports:
    if path.suffix == ".py":
        return parse_python_exports(path)
    if path.suffix in JS_TS_SUFFIXES:
        return parse_js_exports(path)
    return Exports(classes=[], functions=[], constants=[])


def imports_for_path(path: Path) -> list[str]:
    if path.suffix == ".py":
        return python_imports(path)
    if path.suffix in JS_TS_SUFFIXES:
        return js_imports(path)
    return []


def count_source_files(d: Path, recursive: bool = True) -> int:
    """Count source files in a directory. Recursive walk skips IGNORED_DIRS."""
    if not d.exists():
        return 0
    if not recursive:
        try:
            return sum(
                1 for p in d.iterdir()
                if p.is_file() and p.suffix in SOURCE_SUFFIXES
            )
        except OSError:
            return 0
    total = 0
    for dirpath, dirnames, filenames in os.walk(d, onerror=lambda _e: None):
        dirnames[:] = [x for x in dirnames if x not in IGNORED_DIRS and not x.startswith(".")]
        for name in filenames:
            if name.endswith(SOURCE_SUFFIXES):
                total += 1
    return total


# Backwards-compatible alias used by older imports.
PythonExports = Exports


def relative(path: Path, root: Path) -> str:
    try:
        return str(path.resolve().relative_to(root))
    except ValueError:
        return str(path)


_FRONTMATTER_RE = re.compile(r"^---\n(.*?)\n---\n", re.DOTALL)


def strip_yaml_frontmatter(text: str) -> str:
    return _FRONTMATTER_RE.sub("", text, count=1)
