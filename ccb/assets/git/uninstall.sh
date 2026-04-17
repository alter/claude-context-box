#!/usr/bin/env bash
# Remove the ccb pre-commit hook (only if it's ours).
set -euo pipefail

repo_root="$(git rev-parse --show-toplevel 2>/dev/null || true)"
if [ -z "$repo_root" ]; then
    echo "not a git repo: $(pwd)" >&2
    exit 1
fi

target="$repo_root/.git/hooks/pre-commit"
marker="# ccb pre-commit hook"

if [ ! -f "$target" ]; then
    echo "no pre-commit hook to remove"
    exit 0
fi

if ! grep -q "$marker" "$target"; then
    echo "pre-commit hook is not ccb-managed; leaving it in place: $target" >&2
    exit 1
fi

rm "$target"
echo "removed ccb pre-commit hook: $target"
