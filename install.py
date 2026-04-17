#!/usr/bin/env python3
"""ccb installer entry point.

Installs Claude Context Box into the current directory (or `CCB_DIR`).
Runs entirely from the standard library — no pip, no venv pollution.

    curl -sSL https://raw.githubusercontent.com/alter/claude-context-box/main/install.py | python3 -

Environment variables:
    CCB_DIR   target project directory (default: $PWD)
    CCB_REF   git ref / branch / tag of ccb to install (default: main)
    CCB_FORCE if set to 1, force overwrite of .claude/{skills,hooks,ccb-engine}
"""
from __future__ import annotations

import io
import os
import shutil
import subprocess
import sys
import tarfile
import tempfile
import urllib.request
from pathlib import Path

GITHUB_REPO = "alter/claude-context-box"
DEFAULT_REF = "main"


def main() -> int:
    target_dir = Path(os.environ.get("CCB_DIR", os.getcwd())).resolve()
    ref = os.environ.get("CCB_REF", DEFAULT_REF)
    force = os.environ.get("CCB_FORCE", "").lower() in {"1", "true", "yes"}

    if sys.version_info < (3, 10):
        sys.stderr.write(
            f"ccb requires Python 3.10+; have {sys.version.split()[0]}\n"
        )
        return 1

    print(f"ccb installer: ref={ref}  target={target_dir}")

    with tempfile.TemporaryDirectory(prefix="ccb-install-") as tmp:
        source_root = _fetch(ref, Path(tmp))
        return _run_ccb_install(source_root, target_dir, force)


def _fetch(ref: str, tmp_dir: Path) -> Path:
    """Fetch ccb source. Prefer git clone; fall back to tarball download."""
    if shutil.which("git"):
        repo_dir = tmp_dir / "repo"
        print(f"cloning github.com/{GITHUB_REPO}@{ref} ...")
        rc = subprocess.call(
            ["git", "clone", "--depth", "1", "--branch", ref,
             f"https://github.com/{GITHUB_REPO}.git", str(repo_dir)],
            stdout=subprocess.DEVNULL,
        )
        if rc == 0:
            return repo_dir
        print("git clone failed; falling back to tarball download")

    url = f"https://codeload.github.com/{GITHUB_REPO}/tar.gz/refs/heads/{ref}"
    print(f"downloading {url} ...")
    with urllib.request.urlopen(url) as resp:
        data = resp.read()
    with tarfile.open(fileobj=io.BytesIO(data), mode="r:gz") as tar:
        tar.extractall(tmp_dir)
    extracted = next(p for p in tmp_dir.iterdir() if p.is_dir())
    return extracted


def _run_ccb_install(source_root: Path, target_dir: Path, force: bool) -> int:
    cmd = [
        sys.executable, "-c",
        "import sys; sys.path.insert(0, sys.argv[1]); "
        "from ccb.cli import main; "
        "args = ['install', '--dir', sys.argv[2]] + (['--force'] if sys.argv[3] == '1' else []); "
        "sys.exit(main(args))",
        str(source_root),
        str(target_dir),
        "1" if force else "0",
    ]
    return subprocess.call(cmd)


if __name__ == "__main__":
    sys.exit(main())
