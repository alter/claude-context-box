#!/usr/bin/env bash
# release.sh — bump version, commit, tag, push in the right order.
#
# Why a script: tagging before the version-bump commit (or skipping the bump
# entirely) leaves git describe and ccb.__version__ disagreeing. This wraps
# the right sequence so it can't be done out of order again.
#
# Usage:
#   tools/release.sh 0.3.1
#   tools/release.sh 0.3.1 --dry-run
set -euo pipefail

if [ $# -lt 1 ]; then
    echo "usage: $0 <version> [--dry-run]" >&2
    echo "  example: $0 0.3.1" >&2
    exit 2
fi

NEW_VERSION="$1"
DRY_RUN=0
[ "${2:-}" = "--dry-run" ] && DRY_RUN=1

# Sanity: must be on main, working tree clean, all tests + e2e green.
if [ "$(git rev-parse --abbrev-ref HEAD)" != "main" ]; then
    echo "release must be cut from main; you're on $(git rev-parse --abbrev-ref HEAD)" >&2
    exit 1
fi
if [ -n "$(git status --porcelain)" ]; then
    echo "working tree must be clean; uncommitted changes:" >&2
    git status --short >&2
    exit 1
fi
if git tag -l "v$NEW_VERSION" | grep -q .; then
    echo "tag v$NEW_VERSION already exists. To replace, run:" >&2
    echo "  git tag -d v$NEW_VERSION && git push origin :refs/tags/v$NEW_VERSION" >&2
    echo "...then re-run this script. Only do that if the tag has not been" >&2
    echo "consumed by anyone (lockfiles / CI caches / dependents)." >&2
    exit 1
fi

PYPROJECT="pyproject.toml"
INIT="ccb/__init__.py"
SETTINGS="ccb/assets/settings/settings.template.json"

CURRENT_VERSION="$(grep -m1 '^version = ' "$PYPROJECT" | sed 's/.*= "\(.*\)"/\1/')"
echo "current: $CURRENT_VERSION  ->  new: $NEW_VERSION"

if [ "$DRY_RUN" -eq 1 ]; then
    echo "dry-run; no files modified, no commit, no tag."
    exit 0
fi

# Bump.
sed -i.bak "s/^version = \".*\"/version = \"$NEW_VERSION\"/" "$PYPROJECT"
sed -i.bak "s/^__version__ = \".*\"/__version__ = \"$NEW_VERSION\"/" "$INIT"
sed -i.bak "s/\"version\": \".*\"/\"version\": \"$NEW_VERSION\"/" "$SETTINGS"
rm -f "$PYPROJECT.bak" "$INIT.bak" "$SETTINGS.bak"

# Verify the bumps actually landed.
for f in "$PYPROJECT" "$INIT" "$SETTINGS"; do
    if ! grep -q "$NEW_VERSION" "$f"; then
        echo "bump did not take in $f -- check sed pattern" >&2
        exit 1
    fi
done

# Run the test suite -- never tag a broken release.
echo "running tests..."
if [ -x venv/bin/python3 ]; then
    venv/bin/python3 -m pytest tests/ --quiet >/dev/null
else
    python3 -m pytest tests/ --quiet >/dev/null
fi

# Commit + tag.
git add "$PYPROJECT" "$INIT" "$SETTINGS"
git commit -q -m "chore: bump to $NEW_VERSION"
git tag -a "v$NEW_VERSION" -m "ccb $NEW_VERSION"

cat <<EOF

released v$NEW_VERSION on $(git rev-parse --short HEAD)

push with:
  git push origin main --follow-tags
EOF
