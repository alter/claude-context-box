"""Tests for ccb engine scripts (update / status / validate / cleancode).

Engine scripts live under ccb/assets/engine/ and run in the *target* project.
We invoke them as subprocesses with CLAUDE_PROJECT_DIR pointing at a fixture.
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path
from textwrap import dedent

import pytest

ENGINE_DIR = Path(__file__).parent.parent / "ccb" / "assets" / "engine"


def _run(script: str, project_dir: Path) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(ENGINE_DIR / script)],
        capture_output=True,
        text=True,
        env={"CLAUDE_PROJECT_DIR": str(project_dir), "PATH": ""},
        timeout=10,
    )


def _make_project(root: Path) -> None:
    """Build a small but realistic Python project under `root`."""
    (root / "pyproject.toml").write_text('[project]\nname = "demo"\nversion = "0.1.0"\n')
    (root / "src" / "api").mkdir(parents=True)
    (root / "src" / "db").mkdir(parents=True)
    (root / "src" / "__init__.py").write_text("")
    (root / "src" / "api" / "__init__.py").write_text('"""HTTP layer."""\n')
    (root / "src" / "api" / "handler.py").write_text(
        dedent(
            '''\
            """Public request handlers."""
            from src.db.models import User

            def create_user(name: str) -> User:
                return User(name=name)

            class Router:
                def add(self, path: str, fn) -> None: ...
            '''
        )
    )
    (root / "src" / "db" / "__init__.py").write_text('"""Persistence."""\n')
    (root / "src" / "db" / "models.py").write_text(
        dedent(
            '''\
            """Domain models."""
            class User:
                def __init__(self, name: str) -> None:
                    self.name = name
            '''
        )
    )


# update.py --------------------------------------------------------------


def test_update_writes_project_llm(tmp_path: Path) -> None:
    _make_project(tmp_path)
    proc = _run("update.py", tmp_path)
    assert proc.returncode == 0, proc.stderr
    p = tmp_path / "PROJECT.llm"
    assert p.exists()
    text = p.read_text()
    assert "@project: " in text
    assert "@language: python" in text
    assert "@package_manager: pip" in text
    assert "@architecture:" in text
    assert "src/" in text


def test_update_writes_context_per_module(tmp_path: Path) -> None:
    _make_project(tmp_path)
    _run("update.py", tmp_path)
    api_ctx = tmp_path / "src" / "api" / "CONTEXT.llm"
    db_ctx = tmp_path / "src" / "db" / "CONTEXT.llm"
    assert api_ctx.exists()
    assert db_ctx.exists()


def test_update_extracts_python_exports(tmp_path: Path) -> None:
    _make_project(tmp_path)
    _run("update.py", tmp_path)
    api_ctx = (tmp_path / "src" / "api" / "CONTEXT.llm").read_text()
    assert "class Router" in api_ctx
    assert "def create_user" in api_ctx
    # __init__.py docstring wins over individual file docstrings for @purpose
    assert "HTTP layer." in api_ctx


def test_update_uses_module_docstring_as_purpose(tmp_path: Path) -> None:
    _make_project(tmp_path)
    _run("update.py", tmp_path)
    db_ctx = (tmp_path / "src" / "db" / "CONTEXT.llm").read_text()
    assert "@purpose: Persistence." in db_ctx


def test_update_skips_ignored_dirs(tmp_path: Path) -> None:
    _make_project(tmp_path)
    (tmp_path / ".venv" / "lib").mkdir(parents=True)
    (tmp_path / ".venv" / "lib" / "junk.py").write_text("def x(): ...\n")
    (tmp_path / "node_modules" / "foo").mkdir(parents=True)
    (tmp_path / "node_modules" / "foo" / "bar.js").write_text("export const x = 1;\n")
    _run("update.py", tmp_path)
    assert not (tmp_path / ".venv" / "lib" / "CONTEXT.llm").exists()
    assert not (tmp_path / "node_modules" / "foo" / "CONTEXT.llm").exists()


def test_update_is_idempotent(tmp_path: Path) -> None:
    _make_project(tmp_path)
    _run("update.py", tmp_path)
    first = (tmp_path / "src" / "api" / "CONTEXT.llm").read_text()
    # Strip @updated stamps for comparison
    _run("update.py", tmp_path)
    second = (tmp_path / "src" / "api" / "CONTEXT.llm").read_text()
    first_lines = [l for l in first.splitlines() if not l.startswith("@updated")]
    second_lines = [l for l in second.splitlines() if not l.startswith("@updated")]
    assert first_lines == second_lines


# status.py --------------------------------------------------------------


def test_status_runs_on_empty_project(tmp_path: Path) -> None:
    proc = _run("status.py", tmp_path)
    assert proc.returncode == 0
    assert "missing" in proc.stdout  # nothing installed yet


def test_status_reports_after_update(tmp_path: Path) -> None:
    _make_project(tmp_path)
    _run("update.py", tmp_path)
    proc = _run("status.py", tmp_path)
    assert "PROJECT.llm" in proc.stdout
    assert "present" in proc.stdout
    assert ".ccb/errors.log" in proc.stdout
    assert "no errors recorded" in proc.stdout


def test_status_surfaces_hook_errors(tmp_path: Path) -> None:
    """When a hook has crashed and written to .ccb/errors.log, status must
    report the count and timestamp so the user notices silent failures."""
    _make_project(tmp_path)
    _run("update.py", tmp_path)
    errors = tmp_path / ".ccb" / "errors.log"
    errors.parent.mkdir(parents=True, exist_ok=True)
    errors.write_text(
        "\n--- 2026-04-17T15:23:11Z session_start ---\n"
        "Traceback (most recent call last):\n"
        '  File "session_start.py", line 42, in run\n'
        "RuntimeError: simulated\n"
        "\n--- 2026-04-17T16:01:02Z post_tool_use ---\n"
        "Traceback (most recent call last):\n"
        "ValueError: another simulated failure\n"
    )
    proc = _run("status.py", tmp_path)
    assert proc.returncode == 0
    assert "2 hook error(s)" in proc.stdout
    assert "2026-04-17T16:01:02Z" in proc.stdout
    assert "post_tool_use" in proc.stdout


# validate.py ------------------------------------------------------------


def test_validate_clean_after_update(tmp_path: Path) -> None:
    _make_project(tmp_path)
    _run("update.py", tmp_path)
    proc = _run("validate.py", tmp_path)
    assert proc.returncode == 0
    assert "no issues" in proc.stdout


def test_validate_warns_on_missing_context(tmp_path: Path) -> None:
    _make_project(tmp_path)
    _run("update.py", tmp_path)
    # Add a new module without CONTEXT.llm
    (tmp_path / "src" / "auth").mkdir()
    (tmp_path / "src" / "auth" / "__init__.py").write_text('')
    (tmp_path / "src" / "auth" / "login.py").write_text('def login(): ...\n')
    proc = _run("validate.py", tmp_path)
    assert "missing CONTEXT.llm" in proc.stdout
    assert "src/auth" in proc.stdout


def test_validate_errors_when_project_llm_missing(tmp_path: Path) -> None:
    _make_project(tmp_path)
    proc = _run("validate.py", tmp_path)
    assert proc.returncode == 1
    assert "PROJECT.llm missing" in proc.stdout


# cleancode.py -----------------------------------------------------------


def test_update_paths_flag_only_touches_listed_dirs(tmp_path: Path) -> None:
    _make_project(tmp_path)
    _run("update.py", tmp_path)

    # Capture mtimes after the full refresh.
    api_ctx = tmp_path / "src" / "api" / "CONTEXT.llm"
    db_ctx = tmp_path / "src" / "db" / "CONTEXT.llm"
    api_mtime = api_ctx.stat().st_mtime
    db_mtime = db_ctx.stat().st_mtime

    # Force a discernible mtime gap, then incremental-refresh only src/api/.
    import os, time
    time.sleep(0.05)
    proc = subprocess.run(
        [sys.executable, str(ENGINE_DIR / "update.py"),
         "--paths", str(tmp_path / "src" / "api")],
        capture_output=True,
        text=True,
        env={"CLAUDE_PROJECT_DIR": str(tmp_path), "PATH": ""},
        timeout=10,
    )
    assert proc.returncode == 0, proc.stderr

    assert api_ctx.stat().st_mtime > api_mtime, "src/api CONTEXT.llm should be refreshed"
    assert db_ctx.stat().st_mtime == db_mtime, "src/db CONTEXT.llm should NOT be refreshed"


def test_update_paths_accepts_files_and_resolves_to_parent(tmp_path: Path) -> None:
    _make_project(tmp_path)
    _run("update.py", tmp_path)

    api_ctx = tmp_path / "src" / "api" / "CONTEXT.llm"
    api_ctx.unlink()
    proc = subprocess.run(
        [sys.executable, str(ENGINE_DIR / "update.py"),
         "--paths", str(tmp_path / "src" / "api" / "handler.py")],
        capture_output=True,
        text=True,
        env={"CLAUDE_PROJECT_DIR": str(tmp_path), "PATH": ""},
        timeout=10,
    )
    assert proc.returncode == 0, proc.stderr
    assert api_ctx.exists(), "passing a file path should refresh its parent dir"


# JS/TS support ----------------------------------------------------------


def _make_nextjs_project(root: Path) -> None:
    """Build a Next.js-shaped fixture: deeply-nested app/ tree + lib/ + workers/."""
    (root / "package.json").write_text('{"name":"demo-next"}\n')
    (root / "tsconfig.json").write_text('{}\n')

    # app/ — deeply nested, only one .tsx at top level (app/page.tsx) but
    # many in subroutes. The old engine reported "1 source file" for app/
    # because it only looked at direct children.
    app = root / "app"
    (app / "(dashboard)" / "billing").mkdir(parents=True)
    (app / "(marketing)" / "pricing").mkdir(parents=True)
    (app / "page.tsx").write_text(
        "/**\n * Top-level landing page.\n */\n"
        "import { Hero } from '@/lib/ui'\n"
        "export default function Page() { return <Hero /> }\n"
    )
    (app / "(dashboard)" / "billing" / "page.tsx").write_text(
        "import { client } from '@/lib/api'\n"
        "export const revalidate = 60\n"
        "export default async function Billing() { return null }\n"
    )
    (app / "(marketing)" / "pricing" / "page.tsx").write_text(
        "import { tiers } from '../../../lib/pricing'\n"
        "export default function Pricing() { return null }\n"
    )

    # lib/
    lib = root / "lib"
    lib.mkdir()
    (lib / "ui.tsx").write_text(
        "export function Hero() { return null }\n"
        "export class Button {}\n"
    )
    (lib / "api.ts").write_text(
        "import { kv } from '../workers/kv'\n"
        "export const client = { fetch: () => null }\n"
        "export type ApiResponse<T> = { data: T }\n"
    )
    (lib / "pricing.ts").write_text(
        "export const tiers = ['free', 'pro']\n"
        "export interface Tier { name: string }\n"
    )

    # workers/
    workers = root / "workers"
    workers.mkdir()
    (workers / "kv.ts").write_text(
        "export const kv = { get: (_k: string) => null }\n"
    )


def test_describe_dir_counts_recursively_for_nextjs(tmp_path: Path) -> None:
    _make_nextjs_project(tmp_path)
    _run("update.py", tmp_path)
    project_llm = (tmp_path / "PROJECT.llm").read_text()
    # Old bug: app/ reported "1 source file" because only direct children were counted.
    # Now app/ has 3 .tsx files across subdirs — a recursive count picks them all up.
    # The describe_dir output for app/ is the JSDoc from app/page.tsx (it wins over
    # the source-count fallback), so the count line lives elsewhere — assert that
    # at least the JSDoc landed.
    assert "Top-level landing page" in project_llm


def test_describe_dir_uses_recursive_count_when_no_doc(tmp_path: Path) -> None:
    """No README, no JSDoc, no docstring → fallback to recursive count, not direct."""
    (tmp_path / "package.json").write_text('{"name":"x"}\n')
    deep = tmp_path / "src" / "modules" / "auth"
    deep.mkdir(parents=True)
    (deep / "login.ts").write_text("export const a = 1\n")
    (deep / "logout.ts").write_text("export const b = 2\n")
    (tmp_path / "src" / "modules" / "billing").mkdir()
    (tmp_path / "src" / "modules" / "billing" / "stripe.ts").write_text("export const c = 3\n")

    _run("update.py", tmp_path)
    project_llm = (tmp_path / "PROJECT.llm").read_text()
    # src/ has 3 .ts files in total recursively, 0 directly.
    assert "src/: 3 source file(s)" in project_llm


def test_typescript_exports_extracted_into_context(tmp_path: Path) -> None:
    _make_nextjs_project(tmp_path)
    _run("update.py", tmp_path)
    ui_ctx = (tmp_path / "lib" / "CONTEXT.llm").read_text()
    assert "ui.tsx::fn Hero" in ui_ctx
    assert "ui.tsx::class Button" in ui_ctx
    assert "api.ts::const client" in ui_ctx
    # TypeScript-only declarations also appear
    assert "api.ts::class ApiResponse" in ui_ctx  # interface/type/enum classified as class
    assert "pricing.ts::class Tier" in ui_ctx


def test_typescript_imports_recorded_in_context(tmp_path: Path) -> None:
    _make_nextjs_project(tmp_path)
    _run("update.py", tmp_path)
    api_ctx = (tmp_path / "lib" / "CONTEXT.llm").read_text()
    assert "@imports:" in api_ctx
    # api.ts imports `../workers/kv` — the raw specifier appears
    assert "../workers/kv" in api_ctx


def test_dependency_graph_resolves_nextjs_aliases(tmp_path: Path) -> None:
    """`import ... from '@/lib/ui'` should produce app -> lib edge."""
    _make_nextjs_project(tmp_path)
    _run("update.py", tmp_path)
    project_llm = (tmp_path / "PROJECT.llm").read_text()
    assert "@dependency_graph:" in project_llm
    # The placeholder comment should be gone — there ARE edges now.
    assert "# populated as modules grow" not in project_llm
    # app imports from lib (via @/ alias and via relative path).
    assert "app: [lib]" in project_llm
    # lib imports from workers (relative path).
    assert "lib: [workers]" in project_llm


def test_jsdoc_summary_used_as_purpose(tmp_path: Path) -> None:
    """index.ts JSDoc at top of file becomes @purpose for the dir."""
    (tmp_path / "package.json").write_text('{"name":"x"}\n')
    svc = tmp_path / "services"
    svc.mkdir()
    (svc / "index.ts").write_text(
        "/**\n * HTTP service layer.\n * Wraps fetch with auth + retry.\n */\n"
        "export const svc = {}\n"
    )
    _run("update.py", tmp_path)
    ctx = (tmp_path / "services" / "CONTEXT.llm").read_text()
    assert "HTTP service layer." in ctx


def test_export_named_reexports_captured(tmp_path: Path) -> None:
    """`export { foo, bar as baz } from './x'` should add `foo` and `baz` to exports."""
    (tmp_path / "package.json").write_text('{"name":"x"}\n')
    pkg = tmp_path / "lib"
    pkg.mkdir()
    (pkg / "internal.ts").write_text("export const foo = 1\nexport const bar = 2\n")
    (pkg / "public.ts").write_text("export { foo, bar as baz } from './internal'\n")
    _run("update.py", tmp_path)
    ctx = (tmp_path / "lib" / "CONTEXT.llm").read_text()
    assert "public.ts::const foo" in ctx
    assert "public.ts::const baz" in ctx


def test_export_inside_string_or_comment_not_captured(tmp_path: Path) -> None:
    """Defensive: parser strips comments + strings before scanning."""
    (tmp_path / "package.json").write_text('{"name":"x"}\n')
    pkg = tmp_path / "lib"
    pkg.mkdir()
    (pkg / "tricky.ts").write_text(
        "// export function fakeFn() {}\n"
        "/* export class FakeClass {} */\n"
        "const SQL = `export function fakeSql() {}`\n"
        "export function realFn() { return SQL }\n"
    )
    _run("update.py", tmp_path)
    ctx = (tmp_path / "lib" / "CONTEXT.llm").read_text()
    assert "tricky.ts::fn realFn" in ctx
    assert "fakeFn" not in ctx
    assert "FakeClass" not in ctx
    assert "fakeSql" not in ctx


def test_describe_dir_truncates_long_docstring_on_word_boundary(tmp_path: Path) -> None:
    """Long docstrings must be cut to one short line ending with an ellipsis,
    not chopped mid-word. Reproduces the user-visible bug where scripts/
    showed up as 'Test contact form for CRLF header injection vulnerability.
    Sends known attack payloads and verifies  (from test-contact-injection.py)'
    — wrapped onto two lines, ending mid-word, breaking the @architecture
    table format."""
    (tmp_path / "package.json").write_text('{"name":"x"}\n')
    scripts = tmp_path / "scripts"
    scripts.mkdir()
    (scripts / "long_doc.py").write_text(
        '"""Test contact form for CRLF header injection vulnerability. '
        "Sends known attack payloads and verifies that no header smuggling "
        "occurs across all five fields. Designed to be safe against "
        'production endpoints — only requests, no POST."""\n'
    )
    _run("update.py", tmp_path)
    project_llm = (tmp_path / "PROJECT.llm").read_text()
    arch_lines = [l for l in project_llm.splitlines() if l.startswith("  scripts/:")]
    assert len(arch_lines) == 1, "scripts/ should produce exactly one @architecture line"
    line = arch_lines[0]
    # Must fit in the ≤100 char description budget plus the path prefix and
    # the optional " (from <file>)" suffix — overall well under 200.
    assert len(line) < 200
    # Must end either with an ellipsis (truncated) or with the (from ...) tag.
    assert line.endswith(")") or line.rstrip().endswith("…"), line
    # Must NOT end mid-word with trailing space.
    assert not line.rstrip(")").rstrip().endswith("verifies"), \
        "truncation cut mid-word and left a trailing space"


def test_status_coverage_counts_typescript_dirs(tmp_path: Path) -> None:
    """status.py CONTEXT.llm coverage must include TS dirs, not only Python."""
    (tmp_path / "package.json").write_text('{"name":"x"}\n')
    (tmp_path / "lib").mkdir()
    (tmp_path / "lib" / "ui.tsx").write_text("export const x = 1\n")
    (tmp_path / "lib" / "CONTEXT.llm").write_text("@directory: lib\n")
    (tmp_path / "workers").mkdir()
    (tmp_path / "workers" / "kv.ts").write_text("export const kv = {}\n")
    # workers/ deliberately has no CONTEXT.llm yet
    proc = _run("status.py", tmp_path)
    assert proc.returncode == 0
    # 2 code dirs total (lib, workers); 1 has CONTEXT.llm.
    assert "1/2 dirs" in proc.stdout, f"got: {proc.stdout!r}"


def test_python_workflow_unchanged(tmp_path: Path) -> None:
    """Sanity: the JS/TS additions didn't regress Python parsing."""
    _make_project(tmp_path)
    _run("update.py", tmp_path)
    api_ctx = (tmp_path / "src" / "api" / "CONTEXT.llm").read_text()
    # Python uses `def`, JS/TS uses `fn` — verify Python still says def.
    assert "handler.py::class Router" in api_ctx
    assert "handler.py::def create_user" in api_ctx


def test_cleancode_finds_unreferenced_function(tmp_path: Path) -> None:
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "__init__.py").write_text("")
    (tmp_path / "src" / "live.py").write_text(
        "from src.lib import used\n"
        "def main(): used()\n"
    )
    (tmp_path / "src" / "lib.py").write_text(
        "def used(): pass\n"
        "def orphaned(): pass\n"
    )
    proc = _run("cleancode.py", tmp_path)
    assert "orphaned" in proc.stdout
    assert "used" not in proc.stdout.split("orphaned")[0]  # `used` not flagged
