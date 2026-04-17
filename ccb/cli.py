"""ccb CLI — install, update, check, status."""
from __future__ import annotations

import argparse
import sys


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="ccb", description="Claude Context Box")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_install = sub.add_parser("install", help="Install ccb into target project")
    p_install.add_argument("--dir", default=".", help="Target project directory")
    p_install.add_argument("--force", action="store_true")

    sub.add_parser("status", help="Show ccb installation status in current project")
    sub.add_parser("update", help="Re-run install in current directory (idempotent)")

    p_uninstall = sub.add_parser("uninstall", help="Remove ccb block from target CLAUDE.md")
    p_uninstall.add_argument("--dir", default=".")

    p_gh = sub.add_parser(
        "install-git-hook",
        help="Install optional pre-commit hook that refreshes contexts on each commit",
    )
    p_gh.add_argument("--dir", default=".")
    p_gh.add_argument("--force", action="store_true",
                      help="Overwrite an existing non-ccb pre-commit hook")

    p_ugh = sub.add_parser(
        "uninstall-git-hook",
        help="Remove the ccb pre-commit hook (leaves non-ccb hooks alone)",
    )
    p_ugh.add_argument("--dir", default=".")

    args = parser.parse_args(argv)

    if args.cmd == "install":
        from ccb.installer.main import install
        return install(target_dir=args.dir, force=args.force)
    if args.cmd == "status":
        from ccb.installer.main import status
        return status()
    if args.cmd == "update":
        from ccb.installer.main import update
        return update()
    if args.cmd == "uninstall":
        from ccb.installer.main import uninstall
        return uninstall(target_dir=args.dir)
    if args.cmd == "install-git-hook":
        from ccb.installer.git_hook import install as install_git_hook
        from pathlib import Path as _P
        return install_git_hook(_P(args.dir), force=args.force)
    if args.cmd == "uninstall-git-hook":
        from ccb.installer.git_hook import uninstall as uninstall_git_hook
        from pathlib import Path as _P
        return uninstall_git_hook(_P(args.dir))

    parser.print_help()
    return 1


if __name__ == "__main__":
    sys.exit(main())
