#!/usr/bin/env python3
"""ccb installer entry point.

What it does, in order:
  1. Resolves the target project (CCB_DIR or $PWD).
  2. Refuses to run inside the ccb source repo itself (guard).
  3. Fetches ccb source (git clone, falling back to tarball download).
  4. Creates an isolated virtualenv at <target>/.claude/ccb-venv/.
  5. `pip install`s ccb into that venv (no global / user-site pollution).
  6. Runs `ccb install --dir <target>` inside the venv to copy assets and
     merge CLAUDE.md / settings.json.
  7. Drops a shim at <target>/.claude/bin/ccb so the user can run `ccb` without
     activating the venv.

Usage:
    curl -sSL https://raw.githubusercontent.com/alter/claude-context-box/main/install.py | python3 -

Environment variables:
    CCB_DIR          target project directory (default: $PWD)
    CCB_REF          git ref / branch / tag of ccb to install (default: main)
    CCB_FORCE        if set to 1, recreate the venv from scratch
    CCB_REPO_URL     alternate git remote (default: github.com/alter/claude-context-box)
    CCB_TARBALL_URL  alternate tarball base URL (used as fallback)
    CCB_LLM          if set to 1, also install ccb[llm] for LLM session summaries
    CCB_MEMORY       if set to 1, also scaffold the memory/ research structure
                     (INDEX.md, validation protocol, experiment folders)
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
DEFAULT_REPO_URL = f"https://github.com/{GITHUB_REPO}.git"
DEFAULT_TARBALL_URL = f"https://codeload.github.com/{GITHUB_REPO}/tar.gz/refs/heads"


def main() -> int:
    target_dir = Path(os.environ.get("CCB_DIR", os.getcwd())).resolve()
    ref = os.environ.get("CCB_REF", DEFAULT_REF)
    force = os.environ.get("CCB_FORCE", "").lower() in {"1", "true", "yes"}
    repo_url = os.environ.get("CCB_REPO_URL", DEFAULT_REPO_URL)
    tarball_base = os.environ.get("CCB_TARBALL_URL", DEFAULT_TARBALL_URL)

    if sys.version_info < (3, 10):
        sys.stderr.write(
            f"ccb requires Python 3.10+; have {sys.version.split()[0]}\n"
        )
        return 1

    if not target_dir.exists():
        sys.stderr.write(f"target does not exist: {target_dir}\n")
        return 1

    if _is_ccb_source(target_dir):
        sys.stderr.write(
            f"refusing to install: {target_dir} looks like the ccb source repo.\n"
            "Run from a different project directory.\n"
        )
        return 1

    print(f"ccb installer")
    print(f"  target: {target_dir}")
    print(f"  source: {repo_url}@{ref}")

    with tempfile.TemporaryDirectory(prefix="ccb-install-") as tmp:
        source_root = _fetch(ref, Path(tmp), repo_url, tarball_base)
        venv_python = _setup_venv(target_dir, force=force)
        _pip_install_ccb(venv_python, source_root)
        memory = os.environ.get("CCB_MEMORY", "").lower() in {"1", "true", "yes"}
        rc = _run_ccb_install(venv_python, target_dir, force=force, memory=memory)
        if rc != 0:
            return rc
        _write_shim(target_dir, venv_python)

    print()
    print(f"ccb installed. Try:")
    print(f"  .claude/bin/ccb status")
    print(f"  (add .claude/bin to your PATH to use bare `ccb`)")
    return 0


# ---- repo fetch -------------------------------------------------------------


def _fetch(ref: str, tmp_dir: Path, repo_url: str, tarball_base: str) -> Path:
    if shutil.which("git"):
        repo_dir = tmp_dir / "repo"
        print(f"  cloning {repo_url}@{ref} ...")
        rc = subprocess.call(
            ["git", "clone", "--depth", "1", "--branch", ref, repo_url, str(repo_dir)],
            stdout=subprocess.DEVNULL,
        )
        if rc == 0:
            return repo_dir
        print("  git clone failed; falling back to tarball")

    url = f"{tarball_base}/{ref}"
    print(f"  downloading {url} ...")
    with urllib.request.urlopen(url) as resp:
        data = resp.read()
    with tarfile.open(fileobj=io.BytesIO(data), mode="r:gz") as tar:
        # Python 3.12+ supports `filter` to defend against tar slip; on older
        # versions the kwarg is silently ignored.
        try:
            tar.extractall(tmp_dir, filter="data")
        except TypeError:
            tar.extractall(tmp_dir)
    extracted = next(p for p in tmp_dir.iterdir() if p.is_dir())
    return extracted


# ---- venv setup -------------------------------------------------------------


def _setup_venv(target_dir: Path, *, force: bool) -> Path:
    """Create or reuse <target>/.claude/ccb-venv/. Returns path to venv python."""
    venv_dir = target_dir / ".claude" / "ccb-venv"
    venv_python = _venv_python_path(venv_dir)

    if venv_dir.exists() and force:
        print(f"  removing existing venv: {venv_dir}")
        shutil.rmtree(venv_dir)

    if venv_python.exists() and not _venv_has_pip(venv_python):
        # Leftover of an earlier failed run (venv created, pip bootstrap died).
        print(f"  existing venv has no pip; recreating: {venv_dir}")
        shutil.rmtree(venv_dir)

    if not venv_python.exists():
        print(f"  creating venv: {venv_dir}")
        venv_dir.parent.mkdir(parents=True, exist_ok=True)
        rc = subprocess.call([sys.executable, "-m", "venv", str(venv_dir)])
        if rc != 0:
            shutil.rmtree(venv_dir, ignore_errors=True)
            sys.stderr.write(
                "failed to create venv (see the error above).\n"
                f"interpreter used: {sys.executable}\n"
                "If this interpreter is broken (e.g. ensurepip fails), retry with\n"
                "another Python version, e.g.:\n"
                "  curl -sSL https://raw.githubusercontent.com/"
                f"{GITHUB_REPO}/main/install.py | python3.13 -\n"
            )
            sys.exit(1)
    else:
        print(f"  reusing existing venv: {venv_dir}")

    return venv_python


def _venv_has_pip(venv_python: Path) -> bool:
    return subprocess.call(
        [str(venv_python), "-m", "pip", "--version"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    ) == 0


def _venv_python_path(venv_dir: Path) -> Path:
    if os.name == "nt":
        return venv_dir / "Scripts" / "python.exe"
    return venv_dir / "bin" / "python"


def _pip_install_ccb(venv_python: Path, source_root: Path) -> None:
    extras = ""
    if os.environ.get("CCB_LLM", "").lower() in {"1", "true", "yes"}:
        extras = "[llm]"
    spec = f"{source_root}{extras}"
    print(f"  pip install ccb{extras} (into venv) ...")
    pip_cmd = [str(venv_python), "-m", "pip", "install", "--quiet",
               "--upgrade", "--disable-pip-version-check", spec]
    proc = subprocess.run(pip_cmd, capture_output=True, text=True)
    if proc.returncode != 0:
        sys.stderr.write(
            f"pip install failed:\n{proc.stderr}\n"
            "If the venv is broken, recreate it from scratch:\n"
            "  curl -sSL https://raw.githubusercontent.com/"
            f"{GITHUB_REPO}/main/install.py | CCB_FORCE=1 python3 -\n"
        )
        sys.exit(1)


# ---- run ccb install --------------------------------------------------------


def _run_ccb_install(
    venv_python: Path, target_dir: Path, *, force: bool, memory: bool = False
) -> int:
    args = [str(venv_python), "-m", "ccb", "install", "--dir", str(target_dir)]
    if force:
        args.append("--force")
    if memory:
        args.append("--memory")
    return subprocess.call(args)


# ---- shim writer -------------------------------------------------------------


def _write_shim(target_dir: Path, venv_python: Path) -> None:
    bin_dir = target_dir / ".claude" / "bin"
    bin_dir.mkdir(parents=True, exist_ok=True)
    shim = bin_dir / "ccb"
    venv_ccb = venv_python.parent / "ccb"
    if os.name == "nt":
        venv_ccb = venv_python.parent / "ccb.exe"
    shim.write_text(
        "#!/usr/bin/env bash\n"
        "# ccb shim — calls the ccb CLI installed inside .claude/ccb-venv/\n"
        f'exec "{venv_ccb}" "$@"\n',
        encoding="utf-8",
    )
    shim.chmod(0o755)


# ---- guard ------------------------------------------------------------------


def _is_ccb_source(path: Path) -> bool:
    pyproj = path / "pyproject.toml"
    return (
        (path / "ccb" / "assets" / "claude_md").is_dir()
        and pyproj.is_file()
        and "claude-context-box" in pyproj.read_text(errors="ignore")
    )


if __name__ == "__main__":
    sys.exit(main())
