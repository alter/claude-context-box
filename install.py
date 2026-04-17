#!/usr/bin/env python3
"""
ccb installer entry point.

Usage:
    curl -sSL https://raw.githubusercontent.com/alter/claude-context-box/main/install.py | python3 -

NOTE: ccb 0.3.0 is being rewritten. Installation flow lands in Phase B.
This script is a placeholder that will clone the repo and invoke `python -m ccb install`
once the new installer is implemented.
"""
import sys


def main() -> int:
    sys.stderr.write(
        "ccb 0.3.0 is under active rewrite. Installer is not yet wired.\n"
        "Track progress at https://github.com/alter/claude-context-box\n"
    )
    return 2


if __name__ == "__main__":
    sys.exit(main())
