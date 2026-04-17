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

# ---- 1. Build a local bare-git "remote" snapshotting the WORKING TREE -------
# We snapshot the working tree (committed + uncommitted) into a fresh bare repo
# so the test exercises whatever the developer is about to commit, not the
# stale HEAD. Using `git stash create` produces a virtual commit covering both
# tracked and untracked changes; we then push it as the remote's HEAD branch.
REMOTE="$WORK/remote.git"
BRANCH="$(git -C "$REPO_ROOT" rev-parse --abbrev-ref HEAD)"
git init --quiet --bare --initial-branch="$BRANCH" "$REMOTE"

stash_sha="$(git -C "$REPO_ROOT" stash create --include-untracked || true)"
if [ -n "$stash_sha" ]; then
    git -C "$REPO_ROOT" push --quiet "$REMOTE" "$stash_sha:refs/heads/$BRANCH"
    echo "==> snapshotted working tree (stash $stash_sha) into $REMOTE"
else
    git -C "$REPO_ROOT" push --quiet "$REMOTE" "HEAD:refs/heads/$BRANCH"
    echo "==> pushed clean HEAD into $REMOTE (no uncommitted changes)"
fi

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

# ---- 6. Engine: update.py generates context files --------------------------
echo "==> engine: update"
CLAUDE_PROJECT_DIR="$TARGET" python3 "$TARGET/.claude/ccb-engine/update.py" >/dev/null

[ -f "$TARGET/PROJECT.llm" ] || fail "PROJECT.llm not generated"
ok "PROJECT.llm generated"

grep -q "@language: python" "$TARGET/PROJECT.llm" || fail "language not detected"
ok "language correctly detected as python"

[ -f "$TARGET/src/api/CONTEXT.llm" ] || fail "src/api/CONTEXT.llm not generated"
[ -f "$TARGET/src/db/CONTEXT.llm" ]  || fail "src/db/CONTEXT.llm not generated"
ok "per-module CONTEXT.llm files generated"

grep -q "def hello" "$TARGET/src/api/CONTEXT.llm" \
    || fail "exports not extracted from src/api/handler.py"
ok "python AST exports extracted into CONTEXT.llm"

# ---- 7. Engine: status reports the install correctly -----------------------
echo "==> engine: status"
status_out=$(CLAUDE_PROJECT_DIR="$TARGET" python3 "$TARGET/.claude/ccb-engine/status.py")
echo "$status_out" | grep -q "ccb block: yes" || fail "status missed ccb block"
echo "$status_out" | grep -q "5 ccb hook(s)" || fail "status missed registered hooks"
echo "$status_out" | grep -q "5 skill(s)" || fail "status missed installed skills"
ok "status reports install correctly"

# ---- 8. Engine: validate is clean after update -----------------------------
echo "==> engine: validate"
CLAUDE_PROJECT_DIR="$TARGET" python3 "$TARGET/.claude/ccb-engine/validate.py" \
    | grep -q "no issues" || fail "validate reported issues on a fresh project"
ok "validate clean on freshly-updated project"

# ---- 9. SessionStart hook injects PROJECT.llm into context -----------------
echo "==> hook: session_start composes context"
hook_out=$(echo '{}' | CLAUDE_PROJECT_DIR="$TARGET" \
    python3 "$TARGET/.claude/hooks/session_start.py")
echo "$hook_out" | python3 -c "
import json, sys
d = json.loads(sys.stdin.read() or '{}')
ctx = d.get('hookSpecificOutput', {}).get('additionalContext', '')
assert 'PROJECT.llm' in ctx, 'session_start did not inject PROJECT.llm'
assert '@language: python' in ctx, 'session_start did not include language line'
" || fail "session_start hook output missing expected keys"
ok "session_start hook injects PROJECT.llm into additionalContext"

# ---- 10. Realistic end-of-session flow: edit → PostToolUse → SessionEnd
#         → background worker refreshes CONTEXT.llm with the new exports.
echo "==> end-of-session auto-update flow"
sleep 1.1  # mtime granularity (the engine touched CONTEXT.llm in step 6)
cat >> "$TARGET/src/api/handler.py" <<'PY'

def goodbye(name: str) -> str:
    return f"goodbye, {name}"
PY
prev_mtime=$(stat -f %m "$TARGET/src/api/CONTEXT.llm" 2>/dev/null \
    || stat -c %Y "$TARGET/src/api/CONTEXT.llm")

echo '{"tool_name":"Edit","tool_input":{"file_path":"'"$TARGET"'/src/api/handler.py"}}' \
    | CLAUDE_PROJECT_DIR="$TARGET" python3 "$TARGET/.claude/hooks/post_tool_use.py" >/dev/null
grep -q "src/api/handler.py" "$TARGET/.ccb/state.json" \
    || fail "post_tool_use did not record the edit"
ok "post_tool_use recorded the edit in .ccb/state.json"

echo '{"transcript_path":"/tmp/fake.jsonl","last_assistant_message":"added goodbye"}' \
    | CLAUDE_PROJECT_DIR="$TARGET" python3 "$TARGET/.claude/hooks/session_end.py" >/dev/null
ls "$TARGET/.ccb/daily_log/"*.md >/dev/null 2>&1 \
    || fail "session_end did not write a daily log"
grep -q "added goodbye" "$TARGET/.ccb/daily_log/"*.md \
    || fail "session_end did not record the last assistant message"
ok "session_end appended summary to daily log"

# Wait for the background worker to refresh CONTEXT.llm + verify content.
for _ in $(seq 1 100); do
    cur_mtime=$(stat -f %m "$TARGET/src/api/CONTEXT.llm" 2>/dev/null \
        || stat -c %Y "$TARGET/src/api/CONTEXT.llm")
    if [ "$cur_mtime" != "$prev_mtime" ] && grep -q "def goodbye" "$TARGET/src/api/CONTEXT.llm"; then
        break
    fi
    sleep 0.1
done
[ "$cur_mtime" != "$prev_mtime" ] \
    || fail "CONTEXT.llm not refreshed by SessionEnd background worker"
grep -q "def goodbye" "$TARGET/src/api/CONTEXT.llm" \
    || fail "refreshed CONTEXT.llm missing the new export 'goodbye'"
ok "background worker refreshed CONTEXT.llm with new exports"

# ---- 12. Optional pre-commit hook -----------------------------------------
echo "==> optional pre-commit hook"
git -C "$TARGET" init -q
git -C "$TARGET" config user.email "e2e@example.com"
git -C "$TARGET" config user.name  "E2E"

PYTHONPATH="$REPO_ROOT" python3 -m ccb install-git-hook --dir "$TARGET" >/dev/null
[ -f "$TARGET/.git/hooks/pre-commit" ] || fail "pre-commit hook not installed"
ok "pre-commit hook installed"

# Verify it runs cleanly when there are no staged changes.
git -C "$TARGET" add -A
git -C "$TARGET" commit -q -m "initial" || fail "pre-commit hook errored on first commit"
ok "pre-commit hook runs without errors on a real commit"

PYTHONPATH="$REPO_ROOT" python3 -m ccb uninstall-git-hook --dir "$TARGET" >/dev/null
[ ! -f "$TARGET/.git/hooks/pre-commit" ] || fail "pre-commit hook not removed by uninstall"
ok "pre-commit hook removable"

# ---- 13. Uninstall ---------------------------------------------------------
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
