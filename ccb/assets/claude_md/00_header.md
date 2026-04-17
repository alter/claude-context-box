## ccb-managed context

This block is maintained by [Claude Context Box](https://github.com/alter/claude-context-box).
It tells Claude how the project is organized and how to keep documentation in sync.
**Do not edit between the markers** — changes will be overwritten on the next reinstall.
Add your own rules above or below the markers; ccb only owns this section.

Project context lives in:

- `PROJECT.llm` — architecture map (auto-updated by hooks)
- `<module>/CONTEXT.llm` — per-module interface contract (auto-updated)
- `.ccb/daily_log/<YYYY-MM-DD>.md` — session summaries (auto-captured)

Slash commands installed under `.claude/skills/ccb-*` cover manual operations:
`/ccb-update`, `/ccb-status`, `/ccb-validate`, `/ccb-cleancode`, `/ccb-deps`,
and `/ccb-wiki` (the last requires the optional `[llm]` extra). Lifecycle
hooks under `.claude/hooks/` keep contexts current automatically.
