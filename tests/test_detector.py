"""Tests for ccb.installer.detector — language / package manager / venv detection."""
from __future__ import annotations

from pathlib import Path

import pytest

from ccb.installer.detector import detect


# language ---------------------------------------------------------------


def test_detects_python_via_pyproject(tmp_path: Path) -> None:
    (tmp_path / "pyproject.toml").write_text("[project]\nname='x'\n")
    info = detect(tmp_path)
    assert info.language == "python"


def test_detects_python_via_setup_py(tmp_path: Path) -> None:
    (tmp_path / "setup.py").write_text("from setuptools import setup\n")
    assert detect(tmp_path).language == "python"


def test_detects_python_via_requirements_txt(tmp_path: Path) -> None:
    (tmp_path / "requirements.txt").write_text("pytest\n")
    assert detect(tmp_path).language == "python"


def test_detects_python_via_loose_py_file(tmp_path: Path) -> None:
    (tmp_path / "main.py").write_text("print('hi')\n")
    assert detect(tmp_path).language == "python"


def test_detects_node_via_package_json(tmp_path: Path) -> None:
    (tmp_path / "package.json").write_text('{"name":"x"}\n')
    assert detect(tmp_path).language == "node"


def test_detects_go_via_go_mod(tmp_path: Path) -> None:
    (tmp_path / "go.mod").write_text("module x\n")
    assert detect(tmp_path).language == "go"


def test_detects_rust_via_cargo_toml(tmp_path: Path) -> None:
    (tmp_path / "Cargo.toml").write_text("[package]\nname='x'\n")
    assert detect(tmp_path).language == "rust"


def test_unknown_when_no_markers(tmp_path: Path) -> None:
    (tmp_path / "README.md").write_text("# my project\n")
    assert detect(tmp_path).language == "unknown"


def test_python_takes_precedence_over_loose_files(tmp_path: Path) -> None:
    """If pyproject.toml is present we use that, not the loose-file fallback."""
    (tmp_path / "pyproject.toml").write_text("[project]\nname='x'\n")
    (tmp_path / "go.mod").write_text("module x\n")  # python wins because it's earlier
    assert detect(tmp_path).language == "python"


# package manager --------------------------------------------------------


@pytest.mark.parametrize("lockfile,expected", [
    ("poetry.lock", "poetry"),
    ("Pipfile.lock", "pipenv"),
    ("uv.lock", "uv"),
    ("requirements.txt", "pip"),
])
def test_python_package_managers(tmp_path: Path, lockfile: str, expected: str) -> None:
    (tmp_path / "pyproject.toml").write_text("[project]\nname='x'\n")
    (tmp_path / lockfile).write_text("# lock\n")
    assert detect(tmp_path).package_manager == expected


def test_python_pyproject_alone_is_pip(tmp_path: Path) -> None:
    (tmp_path / "pyproject.toml").write_text("[project]\nname='x'\n")
    assert detect(tmp_path).package_manager == "pip"


def test_python_no_marker_at_all_is_none(tmp_path: Path) -> None:
    (tmp_path / "main.py").write_text("# python file but no project marker\n")
    info = detect(tmp_path)
    assert info.language == "python"
    assert info.package_manager == "none"


@pytest.mark.parametrize("lockfile,expected", [
    ("pnpm-lock.yaml", "pnpm"),
    ("yarn.lock", "yarn"),
    ("package-lock.json", "npm"),
])
def test_node_package_managers(tmp_path: Path, lockfile: str, expected: str) -> None:
    (tmp_path / "package.json").write_text('{"name":"x"}\n')
    (tmp_path / lockfile).write_text("# lock\n")
    assert detect(tmp_path).package_manager == expected


def test_node_default_npm(tmp_path: Path) -> None:
    """package.json with no lockfile defaults to npm."""
    (tmp_path / "package.json").write_text('{"name":"x"}\n')
    assert detect(tmp_path).package_manager == "npm"


def test_go_package_manager(tmp_path: Path) -> None:
    (tmp_path / "go.mod").write_text("module x\n")
    assert detect(tmp_path).package_manager == "go"


def test_rust_package_manager(tmp_path: Path) -> None:
    (tmp_path / "Cargo.toml").write_text("[package]\nname='x'\n")
    assert detect(tmp_path).package_manager == "cargo"


def test_unknown_language_no_package_manager(tmp_path: Path) -> None:
    assert detect(tmp_path).package_manager == "none"


# venv -------------------------------------------------------------------


@pytest.mark.parametrize("venv_name", [".venv", "venv", "env"])
def test_detects_unix_venv(tmp_path: Path, venv_name: str) -> None:
    (tmp_path / "pyproject.toml").write_text("[project]\nname='x'\n")
    bin_dir = tmp_path / venv_name / "bin"
    bin_dir.mkdir(parents=True)
    (bin_dir / "python").write_text("#!/usr/bin/env python3\n")
    info = detect(tmp_path)
    assert info.venv_path is not None
    assert info.venv_path.name == venv_name


def test_no_venv_returns_none(tmp_path: Path) -> None:
    (tmp_path / "pyproject.toml").write_text("[project]\nname='x'\n")
    assert detect(tmp_path).venv_path is None


def test_venv_only_for_python_projects(tmp_path: Path) -> None:
    """Even if a `.venv/bin/python` exists, non-python projects don't get a venv field."""
    (tmp_path / "package.json").write_text('{"name":"x"}\n')
    bin_dir = tmp_path / ".venv" / "bin"
    bin_dir.mkdir(parents=True)
    (bin_dir / "python").write_text("")
    assert detect(tmp_path).venv_path is None


def test_broken_venv_dir_is_skipped(tmp_path: Path) -> None:
    """A .venv/ directory without bin/python is not considered a valid venv."""
    (tmp_path / "pyproject.toml").write_text("[project]\nname='x'\n")
    (tmp_path / ".venv").mkdir()  # empty
    assert detect(tmp_path).venv_path is None


# git --------------------------------------------------------------------


def test_detects_git(tmp_path: Path) -> None:
    (tmp_path / ".git").mkdir()
    assert detect(tmp_path).has_git is True


def test_no_git(tmp_path: Path) -> None:
    assert detect(tmp_path).has_git is False


# project info dataclass -------------------------------------------------


def test_project_info_resolves_relative_paths(tmp_path: Path) -> None:
    """detect() should normalize the input path with .resolve()."""
    info = detect(tmp_path / "subdir/..")
    assert info.root == tmp_path.resolve()
