"""Tests for ccb.installer.guard."""
from __future__ import annotations

from pathlib import Path

import pytest

from ccb.installer.guard import assert_not_source, is_ccb_source_repo


def test_guard_detects_source_repo(tmp_path: Path) -> None:
    (tmp_path / "ccb" / "assets" / "claude_md").mkdir(parents=True)
    (tmp_path / "pyproject.toml").write_text('name = "claude-context-box"\n')
    assert is_ccb_source_repo(tmp_path) is True


def test_guard_misses_random_dir(tmp_path: Path) -> None:
    assert is_ccb_source_repo(tmp_path) is False


def test_guard_misses_dir_without_marker_pyproject(tmp_path: Path) -> None:
    (tmp_path / "ccb" / "assets" / "claude_md").mkdir(parents=True)
    (tmp_path / "pyproject.toml").write_text('name = "some-other-project"\n')
    assert is_ccb_source_repo(tmp_path) is False


def test_assert_not_source_raises_in_source(tmp_path: Path) -> None:
    (tmp_path / "ccb" / "assets" / "claude_md").mkdir(parents=True)
    (tmp_path / "pyproject.toml").write_text('name = "claude-context-box"\n')
    with pytest.raises(SystemExit, match="ccb source repo"):
        assert_not_source(tmp_path)


def test_assert_not_source_silent_in_target(tmp_path: Path) -> None:
    assert_not_source(tmp_path)  # no exception
