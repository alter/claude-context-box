#!/usr/bin/env bash
# Install the optional ccb pre-commit hook.
# Run this from the target project: `bash .claude/ccb-git/install.sh`
set -euo pipefail

force=0
for arg in "$@"; do
    case "$arg" in
        --force) force=1 ;;
        -h|--help)
            echo "usage: bash .claude/ccb-git/install.sh [--force]"
            echo "  --force  replace an existing non-ccb pre-commit hook"
            exit 0 ;;
    esac
done

repo_root="$(git rev-parse --show-toplevel 2>/dev/null || true)"
if [ -z "$repo_root" ]; then
    echo "not a git repo: $(pwd)" >&2
    exit 1
fi

script_dir="$(cd "$(dirname "$0")" && pwd)"
template="$script_dir/pre-commit"

if [ ! -f "$template" ]; then
    echo "pre-commit template missing: $template" >&2
    exit 1
fi

pcc="$repo_root/.pre-commit-config.yaml"
if [ -f "$pcc" ]; then
    cat <<'YAML'
detected pre-commit framework config; ccb will not modify it.
Add this entry to .pre-commit-config.yaml by hand:

  - repo: local
    hooks:
      - id: ccb-update
        name: ccb context refresh
        entry: python3 .claude/ccb-engine/update.py --paths
        language: system
        pass_filenames: true
YAML
    exit 0
fi

target="$repo_root/.git/hooks/pre-commit"
marker="# ccb pre-commit hook"

if [ -f "$target" ]; then
    if grep -q "$marker" "$target"; then
        cp "$template" "$target"
        chmod +x "$target"
        echo "refreshed existing ccb pre-commit hook: $target"
        exit 0
    fi
    if [ "$force" -ne 1 ]; then
        echo "refusing to overwrite existing pre-commit hook at $target" >&2
        echo "Inspect it, then re-run with --force to replace." >&2
        exit 1
    fi
fi

mkdir -p "$(dirname "$target")"
cp "$template" "$target"
chmod +x "$target"
echo "installed ccb pre-commit hook: $target"
