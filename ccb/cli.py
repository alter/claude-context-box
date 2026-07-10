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
    p_install.add_argument(
        "--memory",
        action="store_true",
        help="Also scaffold the memory/ research structure (same as `ccb memory init`)",
    )

    sub.add_parser("status", help="Show ccb installation status in current project")
    sub.add_parser("update", help="Re-run install in current directory (idempotent)")

    p_uninstall = sub.add_parser("uninstall", help="Remove ccb block from target CLAUDE.md")
    p_uninstall.add_argument("--dir", default=".")

    p_wiki = sub.add_parser("wiki", help="Compile or query the project wiki")
    wiki_sub = p_wiki.add_subparsers(dest="wiki_cmd", required=True)
    p_wc = wiki_sub.add_parser("compile", help="Compile .ccb/daily_log/* into .ccb/wiki/")
    p_wc.add_argument("--since", default=None, help="Only logs from the last N days (e.g. 7d)")
    p_wc.add_argument("--dry-run", action="store_true")
    p_wq = wiki_sub.add_parser("query", help="Answer a question from the compiled wiki")
    p_wq.add_argument("question", nargs="+", help="The question to ask")

    p_mem = sub.add_parser(
        "memory",
        help="Scaffold/manage the memory/ structure for iterative research projects",
    )
    mem_sub = p_mem.add_subparsers(dest="memory_cmd", required=True)
    mem_sub.add_parser(
        "init", help="Create INDEX.md, AGENTS.md and memory/ skeleton (never overwrites)"
    )
    p_me = mem_sub.add_parser("experiment", help="Start a new experiment iteration folder")
    p_me.add_argument("range_name", help="Experiment range, e.g. books-25")
    p_me.add_argument("version", help="Iteration id, e.g. v3-500-strats")
    mem_sub.add_parser("status", help="Report which memory files exist")

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
        return install(target_dir=args.dir, force=args.force, memory=args.memory)
    if args.cmd == "status":
        from ccb.installer.main import status
        return status()
    if args.cmd == "update":
        from ccb.installer.main import update
        return update()
    if args.cmd == "uninstall":
        from ccb.installer.main import uninstall
        return uninstall(target_dir=args.dir)
    if args.cmd == "wiki":
        from ccb.installer.main import wiki
        return wiki(args.wiki_cmd, args)
    if args.cmd == "memory":
        from ccb.installer.main import memory
        return memory(args.memory_cmd, args)
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
