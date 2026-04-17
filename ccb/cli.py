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

    parser.print_help()
    return 1


if __name__ == "__main__":
    sys.exit(main())
