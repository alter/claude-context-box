"""Detect target project layout: package manager, venv, language."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class ProjectInfo:
    root: Path
    language: str             # "python" | "node" | "go" | "rust" | "unknown"
    package_manager: str      # "poetry" | "pipenv" | "pip" | "uv" | "npm" | "pnpm" | "yarn" | "go" | "cargo" | "none"
    venv_path: Path | None    # absolute path to detected venv, or None
    has_git: bool


def detect(target_dir: Path) -> ProjectInfo:
    target_dir = target_dir.resolve()
    language = _detect_language(target_dir)
    package_manager = _detect_package_manager(target_dir, language)
    venv_path = _detect_venv(target_dir) if language == "python" else None
    has_git = (target_dir / ".git").exists()
    return ProjectInfo(
        root=target_dir,
        language=language,
        package_manager=package_manager,
        venv_path=venv_path,
        has_git=has_git,
    )


def _detect_language(d: Path) -> str:
    if (d / "pyproject.toml").exists() or (d / "setup.py").exists() or (d / "requirements.txt").exists():
        return "python"
    if (d / "package.json").exists():
        return "node"
    if (d / "go.mod").exists():
        return "go"
    if (d / "Cargo.toml").exists():
        return "rust"
    if any(d.glob("*.py")):
        return "python"
    return "unknown"


def _detect_package_manager(d: Path, language: str) -> str:
    if language == "python":
        if (d / "poetry.lock").exists():
            return "poetry"
        if (d / "Pipfile.lock").exists() or (d / "Pipfile").exists():
            return "pipenv"
        if (d / "uv.lock").exists():
            return "uv"
        if (d / "requirements.txt").exists() or (d / "pyproject.toml").exists():
            return "pip"
        return "none"
    if language == "node":
        if (d / "pnpm-lock.yaml").exists():
            return "pnpm"
        if (d / "yarn.lock").exists():
            return "yarn"
        if (d / "package-lock.json").exists():
            return "npm"
        return "npm"
    if language == "go":
        return "go"
    if language == "rust":
        return "cargo"
    return "none"


def _detect_venv(d: Path) -> Path | None:
    for name in (".venv", "venv", "env"):
        candidate = d / name
        bin_python = candidate / ("Scripts/python.exe" if (candidate / "Scripts").exists() else "bin/python")
        if bin_python.exists():
            return candidate
    return None
