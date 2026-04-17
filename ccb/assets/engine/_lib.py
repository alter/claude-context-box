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


def _is_source_file(name: str) -> bool:
    return name.endswith(
        (".py", ".ts", ".tsx", ".js", ".jsx", ".go", ".rs", ".java", ".rb", ".php", ".swift", ".kt")
    )


@dataclass
class PythonExports:
    classes: list[str]
    functions: list[str]


def parse_python_exports(path: Path) -> PythonExports:
    """Best-effort parse — returns empty exports on syntax error."""
    try:
        tree = ast.parse(path.read_text(encoding="utf-8"))
    except (SyntaxError, UnicodeDecodeError):
        return PythonExports(classes=[], functions=[])
    classes: list[str] = []
    functions: list[str] = []
    for node in tree.body:
        if isinstance(node, ast.ClassDef) and not node.name.startswith("_"):
            classes.append(node.name)
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and not node.name.startswith("_"):
            functions.append(node.name)
    return PythonExports(classes=classes, functions=functions)


def python_imports(path: Path) -> list[str]:
    try:
        tree = ast.parse(path.read_text(encoding="utf-8"))
    except (SyntaxError, UnicodeDecodeError):
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


def relative(path: Path, root: Path) -> str:
    try:
        return str(path.resolve().relative_to(root))
    except ValueError:
        return str(path)


_FRONTMATTER_RE = re.compile(r"^---\n(.*?)\n---\n", re.DOTALL)


def strip_yaml_frontmatter(text: str) -> str:
    return _FRONTMATTER_RE.sub("", text, count=1)
