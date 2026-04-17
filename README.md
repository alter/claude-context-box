# Claude Context Box

Self-maintaining project documentation for [Claude Code](https://docs.claude.com/en/docs/claude-code).
One curl command installs hooks and skills that keep `PROJECT.llm` and per-module
`CONTEXT.llm` files in sync with your code, so Claude always knows the project
architecture without re-scanning it on every session.

> **Status: 0.3.0 in active development.** The previous shortcut-based release
> (`u` / `update` / `c` / `s` parsed out of CLAUDE.md) has been replaced with
> native Claude Code primitives — Skills, Hooks, and additive CLAUDE.md merging.
> Old releases are not compatible with this branch.

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

## Install

```bash
curl -sSL https://raw.githubusercontent.com/alter/claude-context-box/main/install.py | python3 -
```

The installer:

1. Refuses to run inside the ccb source repo itself (guard against accidents).
2. Detects your project's language and package manager (poetry / pip / uv /
   pnpm / npm / cargo / go).
3. Copies skills, hooks, and the engine into `.claude/`.
4. Merges `ccb` keys into `.claude/settings.json` (registers the hooks),
   preserving any user-defined hooks.
5. Inserts the ccb-managed block into `CLAUDE.md` between markers (creates the
   file if absent). Pre-existing user content is left untouched.
6. Runs an initial `update.py` so `PROJECT.llm` and `CONTEXT.llm` files are
   immediately populated.

Environment variables for non-default installs:

| Variable | Default | Purpose |
|---|---|---|
| `CCB_DIR` | `$PWD` | Target project directory |
| `CCB_REF` | `main` | Git branch / tag / commit to install |
| `CCB_FORCE` | `0` | Overwrite `.claude/{skills,hooks,ccb-engine}` instead of merging |
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
│   └── ccb-engine/                # update.py, validate.py, status.py, ...
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

## Roadmap

- **Phase F — LLM-summarized session capture.** `capture_session.py` already
  refreshes contexts; the slot for an LLM-generated decisions/issues summary
  via `claude-agent-sdk` (Haiku) is reserved but not yet wired.
- **Phase G — Wiki layer.** Optional `compile_wiki.py` that turns daily logs
  into a structured `.ccb/wiki/` (Karpathy-style "knowledge as code"), plus a
  `query_wiki.py` CLI for terminal queries without opening Claude Code.
- **Phase H — Plugin packaging.** Ship as a Claude Code plugin so the
  installation path becomes `/plugin install ccb` instead of `curl ... | python3`.

## License

MIT.
