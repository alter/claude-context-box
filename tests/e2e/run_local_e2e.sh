#!/usr/bin/env bash
# End-to-end smoke test of the curl install flow.
#
# Simulates `curl ... install.py | python3` without pushing to a real remote:
#   - bare-clones the current source repo into a tempdir (acts as the "remote")
#   - sets up a fake target project with subdirs and existing CLAUDE.md
#   - runs install.py pointed at the local "remote" via CCB_REPO_URL
#   - asserts the install produced the expected files and preserved user content
#   - runs reinstall (idempotency check)
#   - runs uninstall and asserts user content survived
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
WORK="$(mktemp -d -t ccb-e2e.XXXXXX)"
trap 'rm -rf "$WORK"' EXIT

echo "==> work dir: $WORK"

# ---- 1. Build a local bare-git "remote" from the current source tree --------
REMOTE="$WORK/remote.git"
git clone --quiet --bare "$REPO_ROOT" "$REMOTE"
BRANCH="$(git -C "$REPO_ROOT" rev-parse --abbrev-ref HEAD)"
echo "==> built local bare remote at $REMOTE (branch: $BRANCH)"

# ---- 2. Create fake target project with subdirs and existing CLAUDE.md ------
TARGET="$WORK/hello-world"
mkdir -p "$TARGET/src/api" "$TARGET/src/db" "$TARGET/tests"
cat > "$TARGET/src/api/handler.py" <<'PY'
def hello(name: str) -> str:
    return f"hello, {name}"
PY
cat > "$TARGET/src/db/models.py" <<'PY'
class User:
    def __init__(self, name: str) -> None:
        self.name = name
PY
cat > "$TARGET/tests/test_handler.py" <<'PY'
from src.api.handler import hello
def test_hello() -> None:
    assert hello("world") == "hello, world"
PY
cat > "$TARGET/CLAUDE.md" <<'MD'
# hello-world project

USER RULE: do not delete src/db/models.py
USER RULE: tests run with `pytest tests/`
MD
cat > "$TARGET/pyproject.toml" <<'TOML'
[project]
name = "hello-world"
version = "0.1.0"
TOML
echo "==> created fake target at $TARGET"

# ---- 3. Run install.py against the local remote -----------------------------
CCB_DIR="$TARGET" \
CCB_REPO_URL="$REMOTE" \
CCB_REF="$BRANCH" \
python3 "$REPO_ROOT/install.py"

# ---- 4. Assertions ---------------------------------------------------------
fail() { echo "FAIL: $*" >&2; exit 1; }
ok()   { echo "  ok: $*"; }

echo "==> verifying install"
[ -d "$TARGET/.claude" ] || fail ".claude/ not created"
ok ".claude/ exists"

[ -f "$TARGET/.claude/settings.json" ] || fail "settings.json not created"
ok "settings.json exists"

[ -d "$TARGET/.claude/skills" ] || fail "skills/ not copied"
ok "skills/ copied"

[ -d "$TARGET/.claude/hooks" ] || fail "hooks/ not copied"
ok "hooks/ copied"

[ -d "$TARGET/.claude/ccb-engine" ] || fail "ccb-engine/ not copied"
ok "ccb-engine/ copied"

grep -q "ccb:begin" "$TARGET/CLAUDE.md" || fail "ccb begin marker missing"
grep -q "ccb:end"   "$TARGET/CLAUDE.md" || fail "ccb end marker missing"
ok "ccb markers present in CLAUDE.md"

grep -q "USER RULE: do not delete src/db/models.py" "$TARGET/CLAUDE.md" \
    || fail "user content was clobbered"
ok "existing user CLAUDE.md content preserved"

# ---- 5. Reinstall idempotency ----------------------------------------------
echo "==> reinstall (idempotency)"
CCB_DIR="$TARGET" \
CCB_REPO_URL="$REMOTE" \
CCB_REF="$BRANCH" \
python3 "$REPO_ROOT/install.py" >/dev/null

count=$(grep -c "ccb:begin" "$TARGET/CLAUDE.md")
[ "$count" = "1" ] || fail "expected 1 ccb block after reinstall, got $count"
ok "ccb block stays singleton after reinstall"

grep -q "USER RULE: tests run with" "$TARGET/CLAUDE.md" \
    || fail "user content lost on reinstall"
ok "user content preserved on reinstall"

# ---- 6. Uninstall ----------------------------------------------------------
echo "==> uninstall"
PYTHONPATH="$REPO_ROOT" python3 -m ccb uninstall --dir "$TARGET" >/dev/null
grep -q "ccb:begin" "$TARGET/CLAUDE.md" \
    && fail "ccb block still present after uninstall"
ok "ccb block removed by uninstall"

grep -q "USER RULE: do not delete" "$TARGET/CLAUDE.md" \
    || fail "user content lost on uninstall"
ok "user content survived uninstall"

echo
echo "==> ALL E2E ASSERTIONS PASSED"
