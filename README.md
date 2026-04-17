# Claude Context Box

Self-maintaining project documentation for [Claude Code](https://docs.claude.com/en/docs/claude-code).
One curl command installs hooks and skills that keep `PROJECT.llm` and per-module
`CONTEXT.llm` files in sync with your code, so Claude always knows the project
architecture without re-scanning it on every session.

> **Status: 0.3.0 in active development.** The previous shortcut-based release
> (`u` / `update` / `c` / `s` parsed out of CLAUDE.md) has been replaced with
> native Claude Code primitives — Skills, Hooks, and additive CLAUDE.md merging.
> Old releases are not compatible with this branch.

## Quick start

Step 1 — install. From inside your target project (the one ccb should manage):

```bash
cd /path/to/your/project
curl -sSL https://raw.githubusercontent.com/alter/claude-context-box/main/install.py | python3 -
```

That single command does everything: clones ccb to a tempdir, builds an
isolated venv at `.claude/ccb-venv/`, installs ccb into it, copies skills /
hooks / engine / git assets into `.claude/`, merges the ccb section into
`CLAUDE.md` (preserving your existing rules), drops a shim at
`.claude/bin/ccb`, and runs the initial engine update so `PROJECT.llm` and
per-module `CONTEXT.llm` files are populated immediately.

Step 2 — verify:

```bash
.claude/bin/ccb status
```

You should see `ccb section in CLAUDE.md: True`, `5 ccb hook(s) registered`,
`5 skill(s)` installed, and `CONTEXT.llm coverage: N/N dirs (100%)`.

Step 3 — open Claude Code in this project. The `SessionStart` hook fires
automatically and injects `PROJECT.llm` + the latest daily log into Claude's
context. There is **nothing else to type at session start** — every subsequent
session inherits state from the previous one via auto-captured daily logs.

### Optional follow-ups

Use `ccb` without typing the path each time:

```bash
echo 'export PATH="$PWD/.claude/bin:$PATH"' >> ~/.zshrc   # or ~/.bashrc
exec $SHELL                                                # reload shell
ccb status                                                 # now works bare
```

### When do you ever need to run `ccb update` by hand?

**Almost never in day-to-day Claude Code work.** The hooks already do it:

| Trigger | Who refreshes contexts |
|---|---|
| You open Claude Code and `PROJECT.llm` is older than your source tree | `SessionStart` hook (synchronous) |
| Claude finishes a session in which it edited any files | `SessionEnd` hook (background, incremental — only touched dirs) |
| Claude Code compacts the context mid-session | `PreCompact` hook (snapshot) |
| Inside a Claude Code session, you want to force a full refresh | Type `/ccb-update` (native skill) |

The bare CLI is for the cases where Claude Code isn't open at all:

```bash
.claude/bin/ccb update    # or `ccb update` if .claude/bin is on PATH
```

Real-world reasons to reach for it:

- **CI / pre-release scripts** — regenerate `PROJECT.llm` as a build step,
  e.g. `make refresh-context` before tagging a release.
- **After `git pull`** — peek at the updated `PROJECT.llm` before opening
  Claude Code.
- **Mass refactor done in another tool** — IDE-renamed everything, you want
  contexts up to date now without waiting for the next session boundary.
- **Wrapping in your own git hooks / file watchers / cron.**

Otherwise: install ccb, open Claude Code, forget it exists.

### Optional: LLM-summarized session captures

By default the `SessionEnd` hook records *what* changed (files touched,
last assistant turn). With this opt-in, it also asks Claude Haiku to extract
*why* — a 1–2 sentence summary, key technical decisions, and unresolved issues —
and appends them to `.ccb/daily_log/<date>.md`. The next `SessionStart` hook
will inject those into the new session's context.

Enable on first install:

```bash
CCB_LLM=1 curl -sSL https://raw.githubusercontent.com/alter/claude-context-box/main/install.py | python3 -
export ANTHROPIC_API_KEY=sk-ant-...   # add to your shell rc to persist
```

Or enable on an existing install:

```bash
.claude/ccb-venv/bin/pip install 'claude-context-box[llm]'
export ANTHROPIC_API_KEY=sk-ant-...
```

Costs: a Haiku call per session end, capped at 60 KB of transcript and
1000 output tokens. Single-digit cents per session at current Haiku pricing.

Disable per-invocation: `export CCB_LLM=0`. Override the model via
`CCB_LLM_MODEL=claude-sonnet-4-6` if you want richer summaries.

The hook silently skips when `ANTHROPIC_API_KEY` is unset, when the
`anthropic` SDK isn't installed, or when the API call fails — never breaks
the user's session.

### Optional: refresh contexts on every `git commit`

Only do this if you commit `PROJECT.llm` / `CONTEXT.llm` to git (i.e. you
removed them from `.gitignore` to share with your team):

```bash
bash .claude/ccb-git/install.sh
```

### Uninstall

```bash
.claude/bin/ccb uninstall                # strips ccb block from CLAUDE.md
rm -rf .claude/ccb-venv .claude/bin      # then drop the venv + shim
bash .claude/ccb-git/uninstall.sh        # if you installed the pre-commit hook
```

## What it does

- **Reads context for you on session start.** A `SessionStart` hook injects
  `PROJECT.llm` and the most recent daily log into Claude's context — Claude
  doesn't have to re-scan the tree to "remember" what the project looks like.
- **Captures decisions when the session ends.** A `SessionEnd` hook appends a
  brief summary (files touched, last assistant turn, transcript pointer) to
  `.ccb/daily_log/<date>.md`. The next session inherits it via SessionStart.
- **Survives context compaction.** A `PreCompact` hook snapshots the same
  information before Claude Code compresses the conversation, so early-session
  decisions don't evaporate.
- **Tracks what changed during the session.** A `PostToolUse` hook records
  every `Edit` / `Write` in `.ccb/state.json` so updates can be incremental.
- **Lives next to your existing CLAUDE.md.** Installer uses HTML-comment
  markers (`<!-- ccb:begin --> ... <!-- ccb:end -->`) so user content above
  and below the ccb section is preserved on every reinstall.
- **Skills replace shortcuts.** `/ccb-update`, `/ccb-status`, `/ccb-validate`,
  `/ccb-cleancode`, `/ccb-deps` are real Claude Code slash commands with
  proper `SKILL.md` frontmatter — no XML parsing, no description-prompting.

## Install — under the hood

The Quick start command above runs `install.py`, which in order:

1. Refuses to run inside the ccb source repo itself (guard against accidents).
2. Detects your project's language and package manager (poetry / pip / uv /
   pnpm / npm / cargo / go).
3. Clones the ccb source into a tempdir.
4. Creates an isolated venv at `.claude/ccb-venv/` and `pip install`s ccb into
   it (no global / user-site pollution).
5. Copies skills, hooks, engine, and git assets into `.claude/`.
6. Merges `ccb` keys into `.claude/settings.json` (registers the hooks),
   preserving any user-defined hooks. Hook commands point at the venv
   python via `${CLAUDE_PROJECT_DIR}` so the project remains relocatable.
7. Inserts the ccb-managed block into `CLAUDE.md` between markers (creates
   the file if absent). Pre-existing user content is left untouched.
8. Runs the engine update so `PROJECT.llm` + every `CONTEXT.llm` are
   populated immediately.
9. Drops a shim at `.claude/bin/ccb` so the user can run `ccb` without
   activating the venv.

Environment variables for non-default installs:

| Variable | Default | Purpose |
|---|---|---|
| `CCB_DIR` | `$PWD` | Target project directory |
| `CCB_REF` | `main` | Git branch / tag / commit to install |
| `CCB_FORCE` | `0` | Recreate `.claude/ccb-venv/` from scratch |
| `CCB_REPO_URL` | `https://github.com/alter/claude-context-box.git` | Alternate source (used by tests, mirrors, forks) |

## How automatic context maintenance works

| When | What happens | Hook |
|---|---|---|
| Session starts | If `PROJECT.llm` is missing or older than the source tree, `update.py` runs synchronously. Then `PROJECT.llm` + the latest daily log are injected into the system prompt. | `SessionStart` |
| Claude edits a file | The file path is appended to `.ccb/state.json`. | `PostToolUse` |
| Claude Code compresses the context | A snapshot is written to `.ccb/daily_log/<date>.md`. | `PreCompact` |
| Session ends | The change list is handed off to a background worker that refreshes the affected `CONTEXT.llm` files (incremental — only touched dirs) and appends a summary to today's daily log. | `SessionEnd` |
| `CLAUDE.md` / `.claude/rules/*.md` reload | If `PROJECT.llm` is missing or >7 days old, a `systemMessage` warning is emitted. | `InstructionsLoaded` |

You can opt out of the synchronous SessionStart refresh on huge repos:
`export CCB_DISABLE_AUTO_UPDATE=1`.

## Manual escape hatches

Lifecycle is automatic — there's nothing to type at session start. You only
invoke the skills manually when you want to override the defaults.

| Slash command | What it runs |
|---|---|
| `/ccb-update` | Regenerates `PROJECT.llm` + every `CONTEXT.llm` |
| `/ccb-status` | Reports markers, registered hooks, daily-log count, CONTEXT.llm coverage |
| `/ccb-validate` | Lints contexts (missing, stale, orphan, broken refs) |
| `/ccb-cleancode` | Heuristic dead-code candidates (reports only — never deletes) |
| `/ccb-deps` | Prints the `@dependency_graph` section of `PROJECT.llm` |

CLI equivalents (handy in scripts and CI):

```bash
ccb status
ccb update
ccb uninstall --dir /path/to/project
ccb install-git-hook --dir .       # optional pre-commit integration (below)
ccb uninstall-git-hook --dir .
```

## Optional: pre-commit integration

By default, ccb refreshes contexts on session boundaries. If your team commits
`PROJECT.llm` / `CONTEXT.llm` files into git (i.e. you removed them from
`.gitignore`), you may also want them refreshed and re-staged on every commit:

```bash
ccb install-git-hook
```

What it does:

- If `.pre-commit-config.yaml` exists, prints the snippet to add to that
  config and does nothing else (don't fight the [pre-commit framework](https://pre-commit.com/)).
- Otherwise installs `.git/hooks/pre-commit` — but **only if no pre-commit
  hook already exists**. Use `--force` to replace a non-ccb hook.
- The hook runs `update.py --paths <staged dirs>` and re-stages only the
  context files that git already tracks. Untracked context files stay
  untracked (it never starts checking in files you didn't choose to commit).

Remove with `ccb uninstall-git-hook` (refuses to remove a non-ccb hook).

## What lives where in the target project

```
your-project/
├── CLAUDE.md                      # your existing rules + ccb block between markers
├── PROJECT.llm                    # architecture map (auto-regenerated)
├── <module>/
│   └── CONTEXT.llm                # per-module interface (auto-regenerated)
├── .claude/
│   ├── settings.json              # hook registrations under "_ccb": true
│   ├── hooks/                     # session_start.py, session_end.py, ...
│   ├── skills/                    # ccb-update/, ccb-status/, ...
│   ├── ccb-engine/                # update.py, validate.py, status.py, ...
│   └── ccb-git/                   # install.sh, uninstall.sh, pre-commit template
└── .ccb/                          # runtime data (gitignored)
    ├── daily_log/<YYYY-MM-DD>.md  # auto-captured session summaries
    ├── state.json                 # files touched in current session
    └── errors.log                 # captured hook exceptions (never user-facing)
```

## Why this and not the old `u` / `update` shortcuts

- **Hooks vs shortcuts.** Lifecycle hooks run automatically — the old approach
  relied on the user remembering to type `u`. With ccb 0.3.0, context refreshes
  on session boundaries with no human in the loop.
- **Skills vs XML.** Native Claude Code skills with frontmatter don't depend
  on Claude correctly parsing `<executable_shortcuts>` blocks — they appear in
  the slash-command menu and have proper `allowed-tools` scoping.
- **Additive merge vs overwrite.** The previous `merge_claude_md` used regex
  on emoji headings; ccb 0.3.0 uses unambiguous HTML-comment markers that
  survive arbitrary user edits outside them.
- **Stdlib only.** Hooks, engine, and installer all use the standard library —
  no pip dependencies in the target project, no venv pollution, nothing extra
  for the user to install.

## Source repo layout (for contributors)

```
claude-context-box/
├── install.py                     # curl entry — clones repo, runs ccb.cli install
├── pyproject.toml                 # hatchling build, ccb = ccb.cli:main
├── ccb/
│   ├── cli.py                     # `ccb {install,status,update,uninstall}`
│   ├── installer/
│   │   ├── main.py                # orchestration
│   │   ├── merger.py              # additive CLAUDE.md / settings.json merge
│   │   ├── guard.py               # refuses to install into ccb source repo
│   │   └── detector.py            # language / package manager / venv probe
│   └── assets/                    # everything that gets copied into the target
│       ├── claude_md/             # numbered modular sections
│       ├── skills/                # SKILL.md files
│       ├── hooks/                 # python hook scripts
│       ├── settings/              # settings.json template
│       └── engine/                # update / status / validate / cleancode
└── tests/
    ├── test_*.py                  # unit / merger / guard / hooks / engine
    └── e2e/
        ├── run_local_e2e.sh       # full install → update → status → uninstall
        ├── run_docker_e2e.sh      # same, in python:3.11-slim
        └── Dockerfile
```

Run the suite:

```bash
python3 -m pytest tests/         # unit + integration
bash tests/e2e/run_local_e2e.sh  # end-to-end against a local bare clone
bash tests/e2e/run_docker_e2e.sh # same but in a clean container
```

### Optional: wiki layer (Karpathy-style knowledge base)

Daily logs accumulate raw session-by-session events; the wiki turns them into
a topic-organized knowledge base with cross-references. Same dependency as
Phase F (`anthropic` SDK + `ANTHROPIC_API_KEY`).

**Compile** the wiki from your daily logs:

```bash
.claude/bin/ccb wiki compile                # all logs
.claude/bin/ccb wiki compile --since 30d    # last 30 days only
.claude/bin/ccb wiki compile --dry-run      # preview without writing
```

Or invoke `/ccb-wiki` from inside Claude Code.

Output: `.ccb/wiki/index.md` (topic index with cross-links) +
`.ccb/wiki/topics/<slug>.md` (one article per concept extracted from the
logs, each with summary / decisions / open issues / modules touched / related
topics / source-log references).

**Query** the wiki without opening Claude Code:

```bash
.claude/bin/ccb wiki query "what did we decide about auth?"
.claude/bin/ccb wiki query "any open issues with the rate limiter?"
```

The CLI loads the wiki, asks Haiku to answer grounded in those documents,
and prints the response. Useful in shell sessions, scripts, or as a sanity
check before opening a long-form Claude Code session.

## Roadmap

The 0.3.0 architecture is feature-complete for the goals it set out to meet
(self-maintaining context with native Claude Code primitives). Future work
is iterative — sharper heuristics in the engine, richer SessionEnd capture,
better cross-language support — not new architecture.

Out of scope: Claude Code plugin packaging. The plugin format manages
skills / hooks via symlinks but cannot do the `CLAUDE.md` merge, venv setup,
or initial engine population that ccb relies on — distributing as a plugin
would deliver only a degraded subset (skills only). Curl install stays.

## License

MIT.
