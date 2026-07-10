"""Tests for engine/memory.py — the recurring-task memory structure.

Like the other engine scripts, memory.py is not importable from the ccb
package; it runs as a subprocess with CLAUDE_PROJECT_DIR set.
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ENGINE_DIR = Path(__file__).parent.parent / "ccb" / "assets" / "engine"

KEY_FILES = (
    "INDEX.md",
    "AGENTS.md",
    "memory/validation-protocol.md",
    "memory/current-task.md",
    "memory/decisions-log.md",
    "memory/pool/catalog.md",
)
SCAFFOLD_DIRS = ("memory/tasks", "memory/results", "memory/research")


def _run_memory(args: list[str], project_dir: Path) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(ENGINE_DIR / "memory.py"), *args],
        capture_output=True,
        text=True,
        env={"CLAUDE_PROJECT_DIR": str(project_dir), "PATH": ""},
        timeout=10,
    )


# init --------------------------------------------------------------------


def test_init_scaffolds_full_structure(tmp_path: Path) -> None:
    proc = _run_memory(["init"], tmp_path)
    assert proc.returncode == 0, proc.stderr
    for rel in KEY_FILES:
        assert (tmp_path / rel).is_file(), f"missing {rel}"
    for rel in SCAFFOLD_DIRS:
        assert (tmp_path / rel).is_dir(), f"missing {rel}/"
    index = (tmp_path / "INDEX.md").read_text()
    assert "memory/validation-protocol.md" in index
    assert "<!-- ccb:index:begin -->" in index
    protocol = (tmp_path / "memory" / "validation-protocol.md").read_text()
    assert "Status:** ACTIVE" in protocol


def test_init_never_overwrites_existing_files(tmp_path: Path) -> None:
    (tmp_path / "INDEX.md").write_text("# my hand-written index\n")
    proc = _run_memory(["init"], tmp_path)
    assert proc.returncode == 0
    assert (tmp_path / "INDEX.md").read_text() == "# my hand-written index\n"
    assert "kept     INDEX.md" in proc.stdout


def test_init_is_idempotent(tmp_path: Path) -> None:
    _run_memory(["init"], tmp_path)
    proc = _run_memory(["init"], tmp_path)
    assert proc.returncode == 0
    assert "nothing to do" in proc.stdout


def test_init_respects_pre08_layout(tmp_path: Path) -> None:
    """A pre-0.8 scaffold (experiments/, strategy-pool/, current-experiment.md)
    must be recognized — init must not create parallel new-name duplicates."""
    (tmp_path / "memory" / "experiments").mkdir(parents=True)
    (tmp_path / "memory" / "strategy-pool").mkdir()
    (tmp_path / "memory" / "strategy-pool" / "all-strategies.md").write_text("# pool\n")
    (tmp_path / "memory" / "current-experiment.md").write_text("# current\n")
    proc = _run_memory(["init"], tmp_path)
    assert proc.returncode == 0
    assert not (tmp_path / "memory" / "tasks").exists()
    assert not (tmp_path / "memory" / "pool").exists()
    assert not (tmp_path / "memory" / "current-task.md").exists()


# task --------------------------------------------------------------------


def test_task_creates_spec(tmp_path: Path) -> None:
    proc = _run_memory(["task", "books-25", "v1-100-strats"], tmp_path)
    assert proc.returncode == 0, proc.stderr
    spec = tmp_path / "memory" / "tasks" / "books-25" / "v1-100-strats" / "task-spec.md"
    assert spec.is_file()
    body = spec.read_text()
    assert "books-25 — run v1-100-strats" in body
    assert "(none)" in body  # no previous runs yet


def test_task_lists_previous_runs(tmp_path: Path) -> None:
    _run_memory(["task", "books-25", "v1-100"], tmp_path)
    proc = _run_memory(["task", "books-25", "v2-300"], tmp_path)
    assert proc.returncode == 0
    spec = tmp_path / "memory" / "tasks" / "books-25" / "v2-300" / "task-spec.md"
    assert "v1-100" in spec.read_text()


def test_task_refuses_duplicate(tmp_path: Path) -> None:
    _run_memory(["task", "books-25", "v1"], tmp_path)
    proc = _run_memory(["task", "books-25", "v1"], tmp_path)
    assert proc.returncode == 1
    assert "already exists" in proc.stderr


def test_task_rejects_path_separators(tmp_path: Path) -> None:
    proc = _run_memory(["task", "books/25", "v1"], tmp_path)
    assert proc.returncode == 2
    assert not (tmp_path / "memory").exists()


def test_experiment_alias_still_works(tmp_path: Path) -> None:
    proc = _run_memory(["experiment", "books-25", "v1"], tmp_path)
    assert proc.returncode == 0
    assert (tmp_path / "memory" / "tasks" / "books-25" / "v1" / "task-spec.md").is_file()


def test_task_uses_legacy_experiments_dir_when_present(tmp_path: Path) -> None:
    (tmp_path / "memory" / "experiments").mkdir(parents=True)
    proc = _run_memory(["task", "books-25", "v1"], tmp_path)
    assert proc.returncode == 0
    assert (tmp_path / "memory" / "experiments" / "books-25" / "v1" / "task-spec.md").is_file()
    assert not (tmp_path / "memory" / "tasks").exists()


# status ------------------------------------------------------------------


def test_status_reports_missing_structure(tmp_path: Path) -> None:
    proc = _run_memory(["status"], tmp_path)
    assert proc.returncode == 0
    assert "MISSING" in proc.stdout
    assert "init" in proc.stdout


def test_status_counts_runs(tmp_path: Path) -> None:
    _run_memory(["init"], tmp_path)
    _run_memory(["task", "books-25", "v1"], tmp_path)
    _run_memory(["task", "books-25", "v2"], tmp_path)
    _run_memory(["task", "nightly-import", "2026-07-10"], tmp_path)
    proc = _run_memory(["status"], tmp_path)
    assert "tasks: 2, runs: 3" in proc.stdout


# INDEX.md auto-maintained fact block (update.py) --------------------------


def _run_update(project_dir: Path) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(ENGINE_DIR / "update.py")],
        capture_output=True,
        text=True,
        env={"CLAUDE_PROJECT_DIR": str(project_dir), "PATH": ""},
        timeout=10,
    )


def test_update_refreshes_index_fact_block(tmp_path: Path) -> None:
    _run_memory(["init"], tmp_path)
    _run_memory(["task", "books-25", "v1-100"], tmp_path)
    _run_memory(["task", "books-25", "v2-300"], tmp_path)
    proc = _run_update(tmp_path)
    assert proc.returncode == 0, proc.stderr
    index = (tmp_path / "INDEX.md").read_text()
    assert "books-25: 2 run(s)" in index
    assert "latest: v2-300" in index
    assert "Most recently active:** memory/tasks/books-25/v2-300/" in index
    # Template placeholder inside the block was replaced.
    assert "refreshed on the next ccb update" not in index


def test_update_index_block_reads_legacy_layout(tmp_path: Path) -> None:
    (tmp_path / "INDEX.md").write_text("# index\n")
    legacy = tmp_path / "memory" / "experiments" / "books-25" / "v1"
    legacy.mkdir(parents=True)
    (legacy / "task-spec.md").write_text("# spec\n")
    _run_update(tmp_path)
    index = (tmp_path / "INDEX.md").read_text()
    assert "books-25: 1 run(s)" in index
    assert "memory/experiments/books-25/v1/" in index


def test_update_preserves_content_outside_markers(tmp_path: Path) -> None:
    _run_memory(["init"], tmp_path)
    index = tmp_path / "INDEX.md"
    body = index.read_text()
    body = body.replace("- (none yet)", "- Sharpe 2.1 on books-25 v2", 1)
    index.write_text(body + "\nMY HAND-WRITTEN NOTE AT THE END\n")
    _run_update(tmp_path)
    updated = index.read_text()
    assert "Sharpe 2.1 on books-25 v2" in updated
    assert "MY HAND-WRITTEN NOTE AT THE END" in updated


def test_update_index_block_is_idempotent(tmp_path: Path) -> None:
    _run_memory(["init"], tmp_path)
    _run_update(tmp_path)
    _run_update(tmp_path)
    index = (tmp_path / "INDEX.md").read_text()
    assert index.count("<!-- ccb:index:begin -->") == 1
    assert index.count("<!-- ccb:index:end -->") == 1


def test_update_does_not_create_index(tmp_path: Path) -> None:
    (tmp_path / "pyproject.toml").write_text('[project]\nname = "demo"\n')
    proc = _run_update(tmp_path)
    assert proc.returncode == 0
    assert not (tmp_path / "INDEX.md").exists()


def test_update_appends_block_to_markerless_index(tmp_path: Path) -> None:
    (tmp_path / "INDEX.md").write_text("# my own index\nimportant notes\n")
    _run_update(tmp_path)
    index = (tmp_path / "INDEX.md").read_text()
    assert index.startswith("# my own index")
    assert "important notes" in index
    assert "<!-- ccb:index:begin -->" in index
