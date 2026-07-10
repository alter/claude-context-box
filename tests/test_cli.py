"""Tests for ccb.cli — argparse dispatch.

Mocks out the actual installer functions so we only verify routing.
Catches the regression of "added a subcommand to argparse but forgot to
wire it to a handler".
"""
from __future__ import annotations

from unittest.mock import patch

import pytest

from ccb.cli import main


def test_install_dispatches_to_installer_install() -> None:
    with patch("ccb.installer.main.install", return_value=0) as mock:
        rc = main(["install", "--dir", "/tmp/x"])
    assert rc == 0
    mock.assert_called_once_with(target_dir="/tmp/x", force=False, memory=False)


def test_install_with_force() -> None:
    with patch("ccb.installer.main.install", return_value=0) as mock:
        main(["install", "--dir", "/tmp/x", "--force"])
    mock.assert_called_once_with(target_dir="/tmp/x", force=True, memory=False)


def test_install_with_memory() -> None:
    with patch("ccb.installer.main.install", return_value=0) as mock:
        main(["install", "--dir", "/tmp/x", "--memory"])
    mock.assert_called_once_with(target_dir="/tmp/x", force=False, memory=True)


def test_status_dispatches_to_installer_status() -> None:
    with patch("ccb.installer.main.status", return_value=0) as mock:
        rc = main(["status"])
    assert rc == 0
    mock.assert_called_once_with()


def test_update_dispatches_to_installer_update() -> None:
    with patch("ccb.installer.main.update", return_value=0) as mock:
        rc = main(["update"])
    assert rc == 0
    mock.assert_called_once_with()


def test_uninstall_dispatches_to_installer_uninstall() -> None:
    with patch("ccb.installer.main.uninstall", return_value=0) as mock:
        rc = main(["uninstall", "--dir", "/tmp/x"])
    assert rc == 0
    mock.assert_called_once_with(target_dir="/tmp/x")


def test_install_git_hook_dispatches() -> None:
    with patch("ccb.installer.git_hook.install", return_value=0) as mock:
        rc = main(["install-git-hook", "--dir", "/tmp/x"])
    assert rc == 0
    args, kwargs = mock.call_args
    assert str(args[0]) == "/tmp/x"
    assert kwargs == {"force": False}


def test_install_git_hook_with_force() -> None:
    with patch("ccb.installer.git_hook.install", return_value=0) as mock:
        main(["install-git-hook", "--dir", "/tmp/x", "--force"])
    _, kwargs = mock.call_args
    assert kwargs == {"force": True}


def test_uninstall_git_hook_dispatches() -> None:
    with patch("ccb.installer.git_hook.uninstall", return_value=0) as mock:
        rc = main(["uninstall-git-hook", "--dir", "/tmp/x"])
    assert rc == 0
    args, _ = mock.call_args
    assert str(args[0]) == "/tmp/x"


def test_wiki_compile_dispatches() -> None:
    with patch("ccb.installer.main.wiki", return_value=0) as mock:
        rc = main(["wiki", "compile"])
    assert rc == 0
    args, _ = mock.call_args
    assert args[0] == "compile"


def test_wiki_compile_with_since_and_dry_run() -> None:
    with patch("ccb.installer.main.wiki", return_value=0) as mock:
        main(["wiki", "compile", "--since", "7d", "--dry-run"])
    args, _ = mock.call_args
    parsed = args[1]
    assert parsed.since == "7d"
    assert parsed.dry_run is True


def test_wiki_query_dispatches() -> None:
    with patch("ccb.installer.main.wiki", return_value=0) as mock:
        rc = main(["wiki", "query", "what", "did", "we", "decide"])
    assert rc == 0
    args, _ = mock.call_args
    assert args[0] == "query"
    parsed = args[1]
    assert parsed.question == ["what", "did", "we", "decide"]


def test_memory_init_dispatches() -> None:
    with patch("ccb.installer.main.memory", return_value=0) as mock:
        rc = main(["memory", "init"])
    assert rc == 0
    args, _ = mock.call_args
    assert args[0] == "init"


def test_memory_task_dispatches() -> None:
    with patch("ccb.installer.main.memory", return_value=0) as mock:
        rc = main(["memory", "task", "books-25", "v3-500-strats"])
    assert rc == 0
    args, _ = mock.call_args
    assert args[0] == "task"
    parsed = args[1]
    assert parsed.task_name == "books-25"
    assert parsed.run_id == "v3-500-strats"


def test_memory_experiment_alias_dispatches() -> None:
    with patch("ccb.installer.main.memory", return_value=0) as mock:
        rc = main(["memory", "experiment", "books-25", "v1"])
    assert rc == 0
    args, _ = mock.call_args
    assert args[0] == "experiment"
    parsed = args[1]
    assert parsed.task_name == "books-25"
    assert parsed.run_id == "v1"


def test_memory_status_dispatches() -> None:
    with patch("ccb.installer.main.memory", return_value=0) as mock:
        rc = main(["memory", "status"])
    assert rc == 0
    args, _ = mock.call_args
    assert args[0] == "status"


def test_no_subcommand_returns_nonzero(capsys) -> None:
    """Calling without a subcommand should fail loudly, not silently."""
    with pytest.raises(SystemExit) as exc_info:
        main([])
    assert exc_info.value.code != 0


def test_unknown_subcommand_errors() -> None:
    with pytest.raises(SystemExit):
        main(["nonexistent-subcommand"])
