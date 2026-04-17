"""Detect target project's package manager, venv, language. Phase B."""
from __future__ import annotations

from pathlib import Path


def detect(target_dir: Path) -> dict:
    raise NotImplementedError
