## Context file format

ccb maintains two kinds of structured context files. They are machine-readable
and intended for LLMs, not humans.

### `PROJECT.llm` (project root, exactly one)

```
@project: <name>
@version: <semver>
@updated: <ISO-8601 timestamp>
@language: python | typescript | go | ...
@package_manager: poetry | npm | pnpm | go | ...
@architecture:
  <path>/: <one-line description>
@dependency_graph:
  <module>: [<module>, ...]
@modules_status:
  <module>: complete | in_progress | broken
@recent_changes:
  - <ISO timestamp> <path>: <what changed>
```

### `<module>/CONTEXT.llm` (one per non-trivial directory)

```
@directory: <relative path>
@updated: <ISO-8601 timestamp>
@status: complete | in_progress | broken
@purpose: <one-line description of what lives here>
@exports:
  <name>: <signature or short description>
@imports:
  <module>: [<symbol>, ...]
@invariants:
  - <constraint that must always hold>
@known_issues:
  - <file:line>: <description>
@todos:
  - <description>
```

### Forbidden zones

Never write `CONTEXT.llm` into: `.venv/`, `venv/`, `__pycache__/`, `.git/`,
`node_modules/`, `dist/`, `build/`, `.eggs/`, `.local/`, `.ccb/`.
Use venvs for package install — but the venv directory itself never holds context.
