"""Refuse to install ccb into the ccb source repo itself."""
from __future__ import annotations

from pathlib import Path


def is_ccb_source_repo(path: Path) -> bool:
    """True when `path` looks like a checkout of the ccb source repository."""
    return (
        (path / "ccb" / "assets" / "claude_md").is_dir()
        and (path / "pyproject.toml").is_file()
        and "claude-context-box" in (path / "pyproject.toml").read_text(errors="ignore")
    )


def assert_not_source(path: Path) -> None:
    if is_ccb_source_repo(path):
        raise SystemExit(
            f"refusing to install: {path} looks like the ccb source repo. "
            "Run `ccb install` from a different project directory."
        )
