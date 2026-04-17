# Claude Context Box

Self-maintaining context system for Claude Code projects.

> **Status: 0.3.0 rewrite in progress.** The previous shortcut-based architecture
> (`u`/`update`/`c`/`s`) is being replaced with native Claude Code primitives:
> Skills, Hooks, and additive `CLAUDE.md` merging. Old releases are not compatible
> with this branch.

## Goal

Install with one `curl` command into any project, then run automatically:

- Reads project context (`PROJECT.llm`, `<module>/CONTEXT.llm`) on session start.
- Captures decisions and lessons after each session — no manual `update` needed.
- Updates context incrementally when files change.
- Lives alongside an existing `CLAUDE.md` instead of overwriting it.

## Architecture (target)

```
ccb/
├── cli.py                       # `ccb install`, `ccb update`, `ccb status`
├── installer/
│   ├── main.py                  # orchestration
│   ├── merger.py                # additive merge for CLAUDE.md and settings.json
│   ├── guard.py                 # refuses to install into ccb source repo
│   └── detector.py              # finds package manager, venv, framework
└── assets/                      # what gets copied/merged into the target project
    ├── claude_md/               # modular CLAUDE.md sections
    ├── skills/                  # native Claude Code skills (ccb-update, ccb-check, ...)
    ├── hooks/                   # SessionStart / SessionEnd / PreCompact / ...
    ├── engine/                  # context generation scripts
    └── settings/                # settings.json template
```

## Phases

- **Phase A — repo cleanup and scaffolding (current).** Layout, packaging, removal
  of legacy docs and dogfood artifacts.
- **Phase B — installer.** `merger.py`, `guard.py`, `install.py` wired end-to-end.
- **Phase C — assets.** Modular `CLAUDE.md`, skills, hooks, settings template,
  refactored engine.
- **Phase D — docs and tests.** README rewrite, fixture-based installer tests.

## License

MIT.
