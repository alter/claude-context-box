"""Installer orchestration."""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import ccb
from ccb.installer.detector import detect
from ccb.installer.guard import assert_not_source, is_ccb_source_repo
from ccb.installer.merger import (
    merge_claude_md,
    merge_settings_json,
    render_claude_md_block,
    strip_claude_md,
)

ASSETS_ROOT = Path(ccb.__file__).resolve().parent / "assets"
CLAUDE_MD_DIR = ASSETS_ROOT / "claude_md"
SETTINGS_TEMPLATE = ASSETS_ROOT / "settings" / "settings.template.json"
SKILLS_DIR = ASSETS_ROOT / "skills"
HOOKS_DIR = ASSETS_ROOT / "hooks"
ENGINE_DIR = ASSETS_ROOT / "engine"

# Placeholder used in settings.template.json + SKILL.md so the installer can
# substitute the right interpreter (per-project venv if present, else python3).
PYTHON_PLACEHOLDER = "{{ccb_python}}"


def install(target_dir: str = ".", force: bool = False) -> int:
    target = Path(target_dir).resolve()
    assert_not_source(target)

    if not target.exists():
        print(f"target does not exist: {target}", file=sys.stderr)
        return 1

    info = detect(target)
    print(f"target: {target}")
    print(f"detected: {info.language} / {info.package_manager} / venv={info.venv_path}")

    claude_dir = target / ".claude"
    claude_dir.mkdir(exist_ok=True)
    _copy_dir(SKILLS_DIR, claude_dir / "skills", force=force)
    _copy_dir(HOOKS_DIR, claude_dir / "hooks", force=force)
    _copy_dir(ENGINE_DIR, claude_dir / "ccb-engine", force=force)
    _copy_dir(ASSETS_ROOT / "git", claude_dir / "ccb-git", force=force)
    _chmod_exec(claude_dir / "ccb-git" / "install.sh")
    _chmod_exec(claude_dir / "ccb-git" / "uninstall.sh")
    _chmod_exec(claude_dir / "ccb-git" / "pre-commit")

    python_token = _resolve_python_token(claude_dir)
    print(f"  hook interpreter: {python_token}")
    _substitute_python(claude_dir / "skills", python_token)

    if SETTINGS_TEMPLATE.exists():
        raw = SETTINGS_TEMPLATE.read_text(encoding="utf-8").replace(
            PYTHON_PLACEHOLDER, python_token
        )
        ccb_settings = json.loads(raw)
        outcome = merge_settings_json(claude_dir / "settings.json", ccb_settings)
        print(f".claude/settings.json: {outcome}")

    section_body = _compose_claude_md()
    if section_body:
        block = render_claude_md_block(section_body, ccb.__version__)
        outcome = merge_claude_md(target / "CLAUDE.md", block)
        print(f"CLAUDE.md: {outcome}")

    # Initial population of PROJECT.llm + CONTEXT.llm so the project has
    # something to inject the moment a Claude Code session opens.
    _run_engine_update(target)

    print(f"\nccb {ccb.__version__} installed in {target}")
    return 0


def _run_engine_update(target: Path) -> int:
    """Invoke .claude/ccb-engine/update.py against the target.

    Uses the venv python if it exists, else falls back to whatever python
    invoked ccb. Failures are reported but non-fatal (install itself succeeded).
    """
    update_script = target / ".claude" / "ccb-engine" / "update.py"
    if not update_script.exists():
        return 0

    venv_python = target / ".claude" / "ccb-venv" / (
        "Scripts/python.exe" if os.name == "nt" else "bin/python"
    )
    python_cmd = str(venv_python) if venv_python.exists() else sys.executable

    proc = subprocess.run(
        [python_cmd, str(update_script)],
        cwd=str(target),
        env={**os.environ, "CLAUDE_PROJECT_DIR": str(target)},
        capture_output=True,
        text=True,
        timeout=120,
    )
    if proc.returncode != 0:
        sys.stderr.write(
            f"ccb engine update failed (non-fatal):\n{proc.stderr}\n"
        )
        return proc.returncode
    return 0


def _resolve_python_token(claude_dir: Path) -> str:
    """Return the command Claude Code should use to run hooks/engine scripts.

    Prefers the per-project venv (`.claude/ccb-venv/bin/python`) created by
    install.py; falls back to bare `python3` so the install still works when
    someone runs `python -m ccb install` outside the curl flow.

    Returned token uses `${CLAUDE_PROJECT_DIR}` (set by Claude Code in hook
    contexts) so the project remains relocatable — moving or syncing the
    project to another machine doesn't break the hook commands.
    """
    venv_python = claude_dir / "ccb-venv" / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
    if not venv_python.exists():
        return "python3"
    if os.name == "nt":
        return r"${CLAUDE_PROJECT_DIR}\.claude\ccb-venv\Scripts\python.exe"
    return "${CLAUDE_PROJECT_DIR}/.claude/ccb-venv/bin/python"


def _substitute_python(root: Path, python_token: str) -> None:
    """Replace PYTHON_PLACEHOLDER in any text file under `root`."""
    if not root.exists():
        return
    for p in root.rglob("*"):
        if not p.is_file():
            continue
        try:
            text = p.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        if PYTHON_PLACEHOLDER in text:
            p.write_text(text.replace(PYTHON_PLACEHOLDER, python_token), encoding="utf-8")


def status() -> int:
    target = Path.cwd()
    if is_ccb_source_repo(target):
        print(f"this is the ccb source repo, not a target install: {target}")
        return 0

    claude_dir = target / ".claude"
    claude_md = target / "CLAUDE.md"
    settings = claude_dir / "settings.json"
    print(f"target: {target}")
    print(f"  .claude/: {'present' if claude_dir.exists() else 'missing'}")
    print(f"  CLAUDE.md: {'present' if claude_md.exists() else 'missing'}")
    print(f"  settings.json: {'present' if settings.exists() else 'missing'}")
    print(f"  ccb section in CLAUDE.md: {_has_ccb_block(claude_md)}")
    return 0


def update() -> int:
    """Regenerate PROJECT.llm and per-module CONTEXT.llm in the current dir.

    Equivalent to invoking the /ccb-update skill from inside Claude Code.
    For an idempotent reinstall of assets, run `ccb install` instead.
    """
    target = Path.cwd().resolve()
    if is_ccb_source_repo(target):
        print(f"this is the ccb source repo, not a target install: {target}")
        return 0
    rc = _run_engine_update(target)
    if rc == 0:
        print("ccb update: done")
    return rc


def wiki(subcmd: str, args) -> int:
    """`ccb wiki compile` / `ccb wiki query` — proxies to engine scripts."""
    target = Path.cwd().resolve()
    if is_ccb_source_repo(target):
        print(f"this is the ccb source repo, not a target install: {target}")
        return 0

    engine_dir = target / ".claude" / "ccb-engine"
    if subcmd == "compile":
        script = engine_dir / "compile_wiki.py"
        extra: list[str] = []
        if getattr(args, "since", None):
            extra += ["--since", args.since]
        if getattr(args, "dry_run", False):
            extra += ["--dry-run"]
        return _run_engine_script(target, script, extra)
    if subcmd == "query":
        script = engine_dir / "query_wiki.py"
        question = " ".join(args.question) if isinstance(args.question, list) else str(args.question)
        return _run_engine_script(target, script, [question])
    print(f"unknown wiki subcommand: {subcmd}", file=sys.stderr)
    return 2


def _run_engine_script(target: Path, script: Path, args: list[str]) -> int:
    if not script.exists():
        print(f"engine script missing: {script}", file=sys.stderr)
        return 1
    venv_python = target / ".claude" / "ccb-venv" / (
        "Scripts/python.exe" if os.name == "nt" else "bin/python"
    )
    python_cmd = str(venv_python) if venv_python.exists() else sys.executable
    proc = subprocess.run(
        [python_cmd, str(script), *args],
        cwd=str(target),
        env={**os.environ, "CLAUDE_PROJECT_DIR": str(target)},
    )
    return proc.returncode


def uninstall(target_dir: str = ".") -> int:
    target = Path(target_dir).resolve()
    assert_not_source(target)
    removed = strip_claude_md(target / "CLAUDE.md")
    print(f"CLAUDE.md ccb block: {'removed' if removed else 'not present'}")
    print("note: .claude/ contents (skills, hooks, engine) left in place — remove manually if desired")
    return 0


def _copy_dir(src: Path, dst: Path, *, force: bool) -> None:
    if not src.exists():
        return
    if dst.exists():
        if force:
            shutil.rmtree(dst)
        else:
            shutil.copytree(src, dst, dirs_exist_ok=True)
            return
    shutil.copytree(src, dst)


def _chmod_exec(p: Path) -> None:
    if p.exists():
        mode = p.stat().st_mode
        p.chmod(mode | 0o111)


def _compose_claude_md() -> str:
    if not CLAUDE_MD_DIR.exists():
        return ""
    parts: list[str] = []
    for path in sorted(CLAUDE_MD_DIR.glob("*.md")):
        if path.name.startswith("_"):
            continue
        parts.append(path.read_text(encoding="utf-8").rstrip())
    return "\n\n".join(parts)


def _has_ccb_block(path: Path) -> bool:
    if not path.exists():
        return False
    content = path.read_text(encoding="utf-8", errors="ignore")
    from ccb.installer.merger import CLAUDE_MD_BEGIN, CLAUDE_MD_END
    return CLAUDE_MD_BEGIN in content and CLAUDE_MD_END in content
