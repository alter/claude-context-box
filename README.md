# Claude Context Box

Self-maintaining project documentation for [Claude Code](https://docs.claude.com/en/docs/claude-code).
One curl command installs hooks and skills that keep `PROJECT.llm` and per-module
`CONTEXT.llm` files in sync with your code, so Claude always knows the project
architecture without re-scanning it on every session.

> **Status: 0.3.0 and later.** The previous shortcut-based line (`u` / `update`
> / `c` / `s` parsed out of CLAUDE.md) has been replaced with native Claude
> Code primitives — Skills, Hooks, and additive CLAUDE.md merging. Old
> releases are not compatible with this branch.

---

## Quick start

From inside the project ccb should manage:

```bash
cd /path/to/your/project
curl -sSL https://raw.githubusercontent.com/alter/claude-context-box/main/install.py | python3 -
.claude/bin/ccb status
```

That's it. Three lines, no further setup required. The first command does
everything — venv, hooks, skills, engine, CLAUDE.md merge, initial
PROJECT.llm + CONTEXT.llm population. The `status` call confirms it landed.

Two optional follow-ups:

```bash
.claude/bin/ccb memory init   # iterative-research memory: INDEX.md, validation
                              # protocol, experiment folders (see "Memory structure")
.claude/bin/ccb update        # manual context refresh — only needed after mass
                              # changes made OUTSIDE Claude Code (git pull, codegen);
                              # the install already populated everything, and hooks
                              # keep it fresh from here on
```

On slow filesystems (WSL `/mnt/c`, NFS) prepend `CCB_UPDATE_TIMEOUT=600` to
the install command so the initial context generation isn't cut short.

**Requires Python ≥ 3.10** — the interpreter you pipe the installer into.
ccb lives in its own isolated venv (`.claude/ccb-venv/`, created from that
interpreter), so your project's existing `.venv` is never touched and its
Python version doesn't matter. If the system `python3` is too old (or an old
project venv is activated), point the pipe at a newer one:
`curl -sSL ... | python3.11 -`.

Now open Claude Code in this project. The next section walks through what
happens.

---

## Your first session — what to expect

You open Claude Code in a project that just got ccb installed. Concretely:

1. **`SessionStart` hook fires automatically.** It reads `PROJECT.llm` (the
   architecture map ccb just generated) and the most recent daily log (empty
   on first run) and injects them into Claude's system prompt. You don't see
   this happening — Claude just knows the project from turn one.

2. **You work normally.** Ask Claude to fix a bug, add a feature, refactor.
   Every `Edit` / `Write` Claude makes is silently recorded by the
   `PostToolUse` hook into `.ccb/state.json`. Nothing visible.

3. **You close the session** (or run out of context — `PreCompact` does the
   same thing). The `SessionEnd` hook hands the list of touched files to a
   background worker that:
   - regenerates `CONTEXT.llm` for the affected modules (incremental — only
     dirs Claude actually touched, not the whole tree),
   - appends a summary entry to `.ccb/daily_log/<today>.md` (files touched,
     last assistant turn, transcript pointer),
   - if you opted into LLM summaries, also asks Haiku for a structured
     "decisions / issues / summary" extract.

4. **You open Claude Code again tomorrow.** SessionStart finds yesterday's
   daily log and injects it alongside PROJECT.llm. Claude opens the new
   session already knowing what was decided, what got fixed, what's open.

That's the loop. From here, **you almost never type a ccb command yourself.**

---

## Day-to-day — what you actually do

| When this happens | What you do | What ccb does for you |
|---|---|---|
| You start a Claude Code session | Nothing | `SessionStart` injects PROJECT.llm + last daily log; if PROJECT.llm is stale, `update.py` runs first |
| Claude edits files | Nothing | `PostToolUse` records each touched path into `.ccb/state.json` |
| Claude Code auto-compacts the context mid-session | Nothing | `PreCompact` snapshots state into the daily log so early-session decisions don't evaporate |
| You close the session | Nothing | `SessionEnd` triggers a background worker that refreshes affected `CONTEXT.llm` files and appends today's daily log |
| You start another session | Nothing | SessionStart inherits everything — Claude is up to date |
| Architecture changed materially (new top-level dirs, etc.) and you want refresh now | Type `/ccb-update` in Claude Code, or run `.claude/bin/ccb update` from the shell | Regenerates PROJECT.llm + every CONTEXT.llm. The skill also instructs Claude to re-read PROJECT.llm into the current session's context — the SessionStart hook only fires at session start, so mid-session refreshes need this manual pull. |
| You want to see what Claude knows about the project right now | Type `/ccb-status` or run `.claude/bin/ccb status` | Reports hook count, skill count, CONTEXT.llm coverage, daily-log count |
| You want a summary of decisions across many sessions | Run `.claude/bin/ccb wiki compile` (needs LLM extra installed — see Optional features) | LLM organizes daily logs into a topic-indexed wiki under `.ccb/wiki/` |
| You want to ask "what did we decide about X" without opening Claude Code | `.claude/bin/ccb wiki query "..."` | LLM answers grounded in the compiled wiki |

In normal work: install once, open Claude Code, forget ccb exists.

---

## Slash commands inside Claude Code

The installer registers seven native skills. Type `/` in Claude Code to see them:

| Skill | What it does |
|---|---|
| `/ccb-update` | Regenerates PROJECT.llm + every CONTEXT.llm |
| `/ccb-status` | Health report (markers, hooks, skills, CONTEXT.llm coverage) |
| `/ccb-validate` | Lints contexts (missing, stale, orphan, broken refs) |
| `/ccb-cleancode` | Heuristic dead-code candidates (reports only — never deletes) |
| `/ccb-deps` | Prints the `@dependency_graph` section of PROJECT.llm |
| `/ccb-wiki` | Compile or query the daily-log wiki (requires LLM extra) |
| `/ccb-memory` | Scaffold/manage the memory/ structure for iterative research projects |

---

## CLI commands (when Claude Code isn't open)

The shim at `.claude/bin/ccb` exposes the same operations from the shell. Add
`.claude/bin` to your PATH if you want bare `ccb`:

```bash
echo 'export PATH="$PWD/.claude/bin:$PATH"' >> ~/.zshrc   # or ~/.bashrc
exec $SHELL
```

| Command | When it's useful |
|---|---|
| `ccb status` | Verify the install, debug why hooks aren't firing |
| `ccb update` | CI/CD step (`make refresh-context` before release), after `git pull`, after a mass refactor done in another tool |
| `ccb wiki compile [--since 7d] [--dry-run]` | Build the topic wiki from daily logs |
| `ccb wiki query "<question>"` | Answer a question from the wiki without opening Claude Code |
| `ccb memory init` | Scaffold INDEX.md + memory/ for iterative research projects (see Optional features) |
| `ccb memory experiment <range> <version>` | Start a new experiment iteration folder with task-spec.md |
| `ccb memory status` | Report which memory files exist |
| `ccb install --force` | Idempotent reinstall of the asset bundle (replaces ccb-owned hooks; user-defined hooks survive) |
| `ccb uninstall` | Strip the ccb block from CLAUDE.md (keeps `.claude/` so you can reinstall later) |

If you're in a CI job, the same shim works without PATH:
`/path/to/project/.claude/bin/ccb update`.

---

## Optional features

### LLM-summarized session captures

By default the SessionEnd hook records *what* changed. With this enabled, it
also asks Haiku to extract *why* — summary, decisions made, open issues — and
appends them to `.ccb/daily_log/<date>.md`. Tomorrow's SessionStart picks them
up and Claude resumes with the full reasoning, not just file diffs.

ccb tries two LLM backends, in order:

1. **`claude` CLI** (subprocess). Uses your Claude Code subscription
   credentials — no extra billing, no API key, **no setup required** if you
   already have Claude Code installed.
2. **`anthropic` Python SDK**. Requires `ANTHROPIC_API_KEY` env var.
   For headless / CI / API-only environments without a `claude` CLI on PATH.

If `claude` is on PATH, you get LLM session captures **for free** (covered by
your existing subscription). Otherwise, install the SDK and set a key:

```bash
.claude/ccb-venv/bin/pip install 'claude-context-box[llm]'
export ANTHROPIC_API_KEY=sk-ant-...   # add to your shell rc to persist
```

Or enable both at install time:

```bash
CCB_LLM=1 curl -sSL https://raw.githubusercontent.com/alter/claude-context-box/main/install.py | python3 -
```

Bounded cost (SDK path): one Haiku call per SessionEnd, transcript truncated
to 60 KB, 1000 output tokens, 30 s timeout. Single-digit cents per session.
Disable per-call with `CCB_LLM=0`. Override the model with
`CCB_LLM_MODEL=claude-sonnet-4-6` for richer summaries. Force a backend with
`CCB_LLM_BACKEND=cli` or `CCB_LLM_BACKEND=sdk`.

The hook silently skips when neither backend is reachable — never breaks the
session.

### Wiki layer (Karpathy-style knowledge base)

Same LLM backend rules as above (`claude` CLI preferred → `anthropic` SDK
fallback). Turns the day-by-day log into topic-indexed articles with
cross-references. Useful after a stretch of substantial work.

```bash
.claude/bin/ccb wiki compile                # all logs
.claude/bin/ccb wiki compile --since 30d    # last 30 days only
.claude/bin/ccb wiki compile --dry-run      # preview, don't write
.claude/bin/ccb wiki query "what did we decide about auth?"
```

Output:
- `.ccb/wiki/index.md` — topic index with intro and cross-links
- `.ccb/wiki/topics/<slug>.md` — one article per concept (summary,
  decisions, open issues, modules touched, related topics, source-log refs)

### Memory structure for iterative research projects

For projects where you return to the same experiments again and again
(backtest ranges, strategy pools, model sweeps), ccb can scaffold a
memory layout that survives context compaction and session boundaries:

```
your-project/
├── INDEX.md                        # entry point — Claude reads it first, every session
├── AGENTS.md                       # critical rules for any coding agent
└── memory/
    ├── validation-protocol.md      # sacred file — read before every run, never violate
    ├── current-experiment.md       # the active iteration
    ├── decisions-log.md            # dated decisions and insights
    ├── strategy-pool/              # master list + versioned pool snapshots
    ├── experiments/<range>/<version>/task-spec.md
    ├── results/                    # comparisons, best performers
    └── research-rag/               # new theories and strategies
```

```bash
.claude/bin/ccb memory init                          # scaffold (never overwrites)
.claude/bin/ccb memory experiment books-25 v3-500    # new iteration + task-spec.md
.claude/bin/ccb memory status                        # what exists, what's missing
```

Or type `/ccb-memory` inside Claude Code.

Once `INDEX.md` and `memory/` exist:

- **SessionStart injects them.** `INDEX.md`, `memory/validation-protocol.md`,
  and `memory/current-experiment.md` go into the system prompt alongside
  PROJECT.llm (each capped at 8 KB) — Claude opens every session knowing the
  active experiment and the protocol it must follow.
- **The CLAUDE.md block enforces the workflow.** Read INDEX.md first, follow
  the validation protocol exactly, record every iteration under
  `memory/experiments/<range>/<version>/`, use the largest current pool when
  revisiting a range, and update `INDEX.md` + `current-experiment.md` before
  any compaction or session end.
- **`ccb memory experiment`** creates the iteration folder, pre-fills
  `task-spec.md`, and lists the previous versions of that range so the run
  builds on what came before.
- **INDEX.md facts stay fresh automatically.** Every engine update (install,
  stale-context SessionStart, `/ccb-update`, the SessionEnd background worker)
  rewrites the `<!-- ccb:index:begin/end -->` block inside INDEX.md with
  filesystem facts: experiment ranges with iteration counts, the most recently
  active iteration, strategy pools, the latest session log. Everything outside
  the markers — insights, best results — is yours and is never touched; those
  the agent updates per the CLAUDE.md rules.

Everything under `memory/` is plain Markdown you own and commit — ccb never
overwrites an existing file there.

### Pre-commit hook (only if you commit context files)

Default behavior: `PROJECT.llm`, `CONTEXT.llm` files, and the `.ccb/`
directory are all in `.gitignore` — local to each developer. If your team
removes them from `.gitignore` to share via git, you'll want them refreshed
and re-staged on every commit:

```bash
bash .claude/ccb-git/install.sh
```

Behavior:
- If `.pre-commit-config.yaml` exists, prints the snippet to add to it
  manually (don't fight the [pre-commit framework](https://pre-commit.com/)).
- Otherwise installs `.git/hooks/pre-commit` — but **refuses to overwrite an
  existing non-ccb hook** unless you pass `--force`.
- The hook re-stages only context files git already tracks. Untracked
  context files stay untracked.

Remove with `bash .claude/ccb-git/uninstall.sh` (refuses to remove a non-ccb
hook).

---

## Reference

### What lives where in the target project

```
your-project/
├── CLAUDE.md                      # your existing rules + ccb block between markers
├── PROJECT.llm                    # architecture map (auto-regenerated)
├── <module>/
│   └── CONTEXT.llm                # per-module interface (auto-regenerated)
├── .claude/
│   ├── settings.json              # hook registrations under "_ccb": true
│   ├── ccb-venv/                  # isolated venv with the ccb package
│   ├── bin/ccb                    # shim → ccb-venv's ccb entry point
│   ├── hooks/                     # session_start.py, session_end.py, ...
│   ├── skills/                    # ccb-update/, ccb-status/, ccb-wiki/, ...
│   ├── ccb-engine/                # update.py, validate.py, status.py, ...
│   └── ccb-git/                   # install.sh, uninstall.sh, pre-commit template
└── .ccb/                          # runtime data (gitignored)
    ├── daily_log/<YYYY-MM-DD>.md  # auto-captured session summaries
    ├── wiki/                      # compiled topic wiki (after `ccb wiki compile`)
    ├── state.json                 # files touched in current session
    ├── handoff.json               # one-shot file SessionEnd → background worker
    └── errors.log                 # captured hook exceptions (never user-facing)
```

### How Claude actually reads the context

There is one strong injection mechanism and two weak signals:

1. **`SessionStart` hook (strong).** When you open a new Claude Code session,
   the hook reads PROJECT.llm + the latest daily log and returns them via
   `hookSpecificOutput.additionalContext`. Claude Code injects that into
   the system prompt — Claude knows the project from turn one. Fires **only
   on session start**, not on any in-session event.
2. **CLAUDE.md mentions PROJECT.llm (weak).** The ccb block points Claude
   at PROJECT.llm and `<module>/CONTEXT.llm`, but Claude doesn't read them
   automatically — only if it decides it needs to (via the Read tool).
3. **`InstructionsLoaded` hook (advisory).** Warns via `systemMessage` if
   PROJECT.llm is missing or >7 days old. Doesn't inject content.

**Mid-session refreshes:** when you type `/ccb-update` in the middle of an
existing session, the file on disk gets refreshed but the *injected* copy
in Claude's system prompt is still the version from session start. The
`/ccb-update` skill closes that gap by instructing Claude to Read the
freshly-written PROJECT.llm into the current turn's context. Without that
explicit re-read, mid-session updates only land in the *next* session.

### Lifecycle hooks

| Hook | Trigger | Action |
|---|---|---|
| `SessionStart` | New Claude Code session opens | If PROJECT.llm is stale, run engine update synchronously. Then inject PROJECT.llm + latest daily log into the system prompt. |
| `PostToolUse` | After every Edit/Write/MultiEdit/NotebookEdit | Append touched file path to `.ccb/state.json` |
| `PreCompact` | Before Claude Code compresses context | Snapshot state into today's daily log |
| `SessionEnd` | Session closes | Hand off to background worker → incremental engine refresh + daily-log entry + (opt-in) LLM summary |
| `InstructionsLoaded` | CLAUDE.md / `.claude/rules/*.md` loaded | Warn via `systemMessage` if PROJECT.llm is missing or >7 days old |

Opt out of the synchronous SessionStart refresh on huge repos:
`export CCB_DISABLE_AUTO_UPDATE=1`.

### Install env vars

| Variable | Default | Purpose |
|---|---|---|
| `CCB_DIR` | `$PWD` | Target project directory |
| `CCB_REF` | `main` | Git branch / tag / commit to install |
| `CCB_FORCE` | `0` | Recreate `.claude/ccb-venv/` from scratch |
| `CCB_LLM` | `0` | Also install `ccb[llm]` for LLM session summaries |
| `CCB_LLM_MODEL` | `claude-haiku-4-5` | Override the model used by Phase F + wiki |
| `CCB_REPO_URL` | `https://github.com/alter/claude-context-box.git` | Alternate source (forks, mirrors) |
| `CCB_TARBALL_URL` | `https://codeload.github.com/alter/claude-context-box/tar.gz/refs/heads` | Tarball fallback if git unavailable |
| `CCB_DISABLE_AUTO_UPDATE` | `0` | Skip the synchronous SessionStart refresh |
| `CCB_UPDATE_TIMEOUT` | `120` | Seconds before the initial engine update is abandoned (non-fatal). Raise on slow filesystems — WSL `/mnt/c`, NFS, huge monorepos |
| `ANTHROPIC_API_KEY` | unset | Required for opt-in LLM features (Phase F + wiki) |

### What `install.py` does, step by step

1. Refuses to run inside the ccb source repo itself (guard against accidents).
2. Detects your project's language and package manager
   (poetry / pip / uv / pnpm / npm / cargo / go).
3. Clones the ccb source into a tempdir.
4. Creates `.claude/ccb-venv/` and `pip install`s ccb into it
   (no global / user-site pollution).
5. Copies skills, hooks, engine, and git assets into `.claude/`.
6. Merges `ccb` keys into `.claude/settings.json` — preserves user-defined
   hooks; ccb-owned hooks (marked `_ccb: true`) replace prior versions.
   Hook commands point at the venv python via `${CLAUDE_PROJECT_DIR}` so
   the project remains relocatable.
7. Inserts the ccb-managed block into `CLAUDE.md` between
   `<!-- ccb:begin -->` / `<!-- ccb:end -->` markers. Pre-existing user
   content above and below the markers is left untouched.
8. Runs the engine update so PROJECT.llm + every CONTEXT.llm are populated
   immediately.
9. Drops a shim at `.claude/bin/ccb` so the user can run `ccb` without
   activating the venv.

### Uninstall

```bash
.claude/bin/ccb uninstall                # strips ccb block from CLAUDE.md
rm -rf .claude/ccb-venv .claude/bin      # drop the venv + shim
rm -rf .claude/{hooks,skills,ccb-engine,ccb-git}   # drop the assets
rm -rf .ccb                              # drop runtime data (or keep it as a record)
bash .claude/ccb-git/uninstall.sh        # if you installed the pre-commit hook
```

---

## FAQ

### What about MCP Memory Service?

Old ccb releases (≤ 0.2.x) shipped an installer for
[doobidoo/mcp-memory-service](https://github.com/doobidoo/mcp-memory-service)
and a set of `/memory-*` slash commands. **0.3.0 deliberately drops that
integration.** ccb does not install, configure, or interact with MCP Memory
in any way.

Why dropped:

- **Karpathy's premise holds.** His original post (the inspiration for the
  wiki layer here) shows that flat markdown + LLM grounding handles 100+
  articles / 500K words without RAG. ccb's `compile_wiki.py` /
  `query_wiki.py` cover the same ground at zero setup cost.
- **Install footprint.** MCP Memory needs `sentence-transformers`,
  `sqlite-vec`, and often a C++ toolchain (Xcode CLT / build-essential / VS
  Build Tools). ccb's value proposition is one curl + stdlib only — adding
  MCP would break the three-line Quick start.
- **Per-project vs cross-project.** 0.3.0 keeps everything inside the
  project (PROJECT.llm, .ccb/, venv) so it travels with the repo. MCP
  Memory is a long-running global server — a different model.
- **Claude Code already has auto-memory.** Since v2.1.59 Claude Code
  records "useful context" automatically, exposed via `/memory`. Layering a
  third memory store (Claude's auto-memory + ccb daily logs + MCP) just
  creates three sources of truth.
- **Old installer was overstepping.** The previous ccb tried to manage MCP
  as if it were a ccb feature; in practice it was a third-party server with
  its own lifecycle and failure modes. That coupling was the wrong scope.

What ccb gives you instead, mapped to MCP Memory's pitch:

| MCP Memory feature | ccb 0.3.0 equivalent |
|---|---|
| Persistent storage between sessions | `.ccb/daily_log/<date>.md` (auto-captured by SessionEnd) |
| Semantic search across stored memories | `ccb wiki query "..."` (Haiku grounded in `.ccb/wiki/`) |
| Memory consolidation / dream-style summarization | `ccb wiki compile` (re-extracts topics from current daily logs) |
| `/memory-*` slash commands | `/ccb-status`, `/ccb-update`, `/ccb-wiki` |

If you actually want MCP Memory in addition to ccb, install it as a
standalone Claude Code MCP server (`claude mcp add memory …`) — the two
don't conflict. ccb just won't do it for you.

## Why hooks/skills, not shortcuts

- **Hooks vs shortcuts.** Lifecycle hooks run automatically — the old approach
  relied on the user remembering to type `u`. With ccb 0.3.0, context refreshes
  on session boundaries with no human in the loop.
- **Skills vs XML.** Native Claude Code skills with frontmatter don't depend
  on Claude correctly parsing `<executable_shortcuts>` blocks — they appear in
  the slash-command menu and have proper `allowed-tools` scoping.
- **Additive merge vs overwrite.** The previous merge_claude_md used regex
  on emoji headings; ccb 0.3.0 uses unambiguous HTML-comment markers that
  survive arbitrary user edits outside them.
- **Per-project venv vs global pip.** No pollution of the user's site-packages,
  no PATH conflicts, clean uninstall is `rm -rf .claude/ccb-venv`.

---

## For contributors

```
claude-context-box/
├── install.py                     # curl entry — clones repo, runs ccb.cli install
├── pyproject.toml                 # setuptools, ccb = ccb.cli:main, [llm] extra
├── ccb/
│   ├── cli.py                     # `ccb {install,status,update,uninstall,wiki,...}`
│   ├── installer/
│   │   ├── main.py                # orchestration
│   │   ├── merger.py              # additive CLAUDE.md / settings.json merge
│   │   ├── guard.py               # refuses to install into ccb source repo
│   │   ├── detector.py            # language / package manager / venv probe
│   │   └── git_hook.py            # optional pre-commit hook installer (Python)
│   └── assets/                    # everything that gets copied into the target
│       ├── claude_md/             # numbered modular sections (00..80)
│       ├── skills/                # SKILL.md files
│       ├── hooks/                 # python hook scripts (stdlib only)
│       ├── settings/              # settings.json template
│       ├── engine/                # update / status / validate / cleancode / wiki
│       └── git/                   # install.sh / uninstall.sh / pre-commit template
└── tests/
    ├── test_*.py                  # unit / merger / guard / hooks / engine / wiki / llm
    └── e2e/
        ├── run_local_e2e.sh       # full install → update → ... against a local bare clone
        ├── run_docker_e2e.sh      # same in python:3.11-slim
        ├── run_real_curl.sh       # real curl-from-github e2e (run after pushing)
        └── Dockerfile
```

Run the suite:

```bash
python3 -m pytest tests/                                  # 180 unit + integration
python3 -m pytest tests/ --cov=ccb --cov-report=term      # with coverage report
bash tests/e2e/run_local_e2e.sh                           # local end-to-end
bash tests/e2e/run_docker_e2e.sh                          # same, in a clean container
bash tests/e2e/run_real_curl.sh                           # real github.com curl flow
```

Current coverage: **96% line coverage** of the importable ccb package.
Uncovered lines are subprocess fallback paths and the `if __name__ ==
"__main__"` guards. Engine and hook scripts under `ccb/assets/` are not
counted in line coverage (they're shipped to the target as-is and exercised
through subprocess + e2e), but each has its own dedicated test file:

| File | Tests |
|---|---|
| `tests/test_merger.py` | 20 — CLAUDE.md / settings.json / .gitignore additive merging |
| `tests/test_detector.py` | 31 — language / package manager / venv detection |
| `tests/test_install_py.py` | 16 — install.py: guard, venv setup, pip, shim, fetch + tarball fallback |
| `tests/test_main_helpers.py` | 24 — _substitute_python, _compose_claude_md, wiki dispatch, source-repo guards |
| `tests/test_cli.py` | 13 — argparse subcommand dispatch (all `ccb …` verbs) |
| `tests/test_hooks.py` | 19 — every lifecycle hook + auto-refresh recovery + PreCompact |
| `tests/test_engine.py` | 15 — update / status / validate / cleancode |
| `tests/test_install_smoke.py` | 6 — full install / reinstall / uninstall in-process |
| `tests/test_git_hook.py` | 9 — pre-commit hook installer |
| `tests/test_guard.py` | 5 — source-repo detection |
| `tests/test_llm_summary.py` | 7 — capture_session.py with anthropic SDK mocked |
| `tests/test_wiki.py` | 11 — compile_wiki.py + query_wiki.py, including 200 KB truncation |
| `tests/test_permission_resilience.py` | 5 — every scanner survives chmod-000 dirs |

LLM features (Phase F + wiki) are tested via a faked anthropic SDK injected
through PYTHONPATH — the suite runs without network or API key. Real Anthropic
calls require a manual smoke against `.claude/bin/ccb wiki compile` with
`ANTHROPIC_API_KEY` set.

---

## Roadmap

The 0.3.0 architecture is feature-complete for its goals (self-maintaining
context with native Claude Code primitives). Future work is iterative —
sharper engine heuristics, richer SessionEnd capture, better cross-language
support — not new architecture.

Out of scope: Claude Code plugin packaging. The plugin format manages
skills / hooks via symlinks but cannot do the CLAUDE.md merge, venv setup,
or initial engine population that ccb relies on. Distributing as a plugin
would deliver only a degraded subset (skills only). Curl install stays the
primary path.

---

## License

MIT.
