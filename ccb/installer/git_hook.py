"""Install / remove the optional ccb git pre-commit hook.

Strategy:
  - If `.pre-commit-config.yaml` exists, append a ccb hook entry there
    (the right way for projects that use the pre-commit framework).
  - Otherwise install `.git/hooks/pre-commit` — but only if no pre-commit
    hook exists, or the existing one is already ours (idempotent reinstall).

Removal: `ccb uninstall-git-hook` strips ours back out, leaving any user
content alone.
"""
from __future__ import annotations

from pathlib import Path

import ccb

ASSETS_GIT_HOOK = Path(ccb.__file__).resolve().parent / "assets" / "git" / "pre-commit"

CCB_MARKER = "# ccb pre-commit hook"


def install(target_dir: Path, *, force: bool = False) -> int:
    target_dir = target_dir.resolve()

    git_dir = target_dir / ".git"
    if not git_dir.is_dir():
        print(f"not a git repo: {target_dir}")
        return 1

    pcc = target_dir / ".pre-commit-config.yaml"
    if pcc.exists():
        print(
            f"detected pre-commit framework config: {pcc.name}\n"
            "ccb does not auto-modify .pre-commit-config.yaml. Add this entry by hand:\n\n"
            "  - repo: local\n"
            "    hooks:\n"
            "      - id: ccb-update\n"
            "        name: ccb context refresh\n"
            "        entry: python3 .claude/ccb-engine/update.py --paths\n"
            "        language: system\n"
            "        pass_filenames: true\n"
        )
        return 0

    hooks_dir = git_dir / "hooks"
    hooks_dir.mkdir(exist_ok=True)
    target = hooks_dir / "pre-commit"

    template = ASSETS_GIT_HOOK.read_text(encoding="utf-8")

    if target.exists():
        existing = target.read_text(encoding="utf-8", errors="ignore")
        if CCB_MARKER in existing:
            target.write_text(template, encoding="utf-8")
            target.chmod(0o755)
            print(f"refreshed existing ccb pre-commit hook: {target}")
            return 0
        if not force:
            print(
                f"refusing to overwrite existing pre-commit hook at {target}\n"
                "Inspect it, then re-run with --force to replace."
            )
            return 1

    target.write_text(template, encoding="utf-8")
    target.chmod(0o755)
    print(f"installed ccb pre-commit hook: {target}")
    return 0


def uninstall(target_dir: Path) -> int:
    target_dir = target_dir.resolve()
    target = target_dir / ".git" / "hooks" / "pre-commit"
    if not target.exists():
        print("no pre-commit hook to remove")
        return 0
    existing = target.read_text(encoding="utf-8", errors="ignore")
    if CCB_MARKER not in existing:
        print(f"pre-commit hook is not ccb-managed; leaving it in place: {target}")
        return 1
    target.unlink()
    print(f"removed ccb pre-commit hook: {target}")
    return 0
