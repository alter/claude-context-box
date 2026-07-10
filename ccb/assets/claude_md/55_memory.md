## Memory structure (recurring tasks, large projects)

These rules apply ONLY when `INDEX.md` and `memory/` exist in the project root
(scaffold them with `/ccb-memory init`):

1. Read `INDEX.md` FIRST, before any other exploration. It is a routing
   table — read only what it points to; do not hold the whole project in
   context.
2. `memory/validation-protocol.md` is inviolable. Read it before any run of
   a recurring task and follow it exactly.
3. Distinguish task kinds. One-off work ("did it, forgot it") needs NO memory
   entry — the ccb session log captures it automatically. Only recurring
   tasks — re-run with new variants, options, or data — get a folder under
   `memory/tasks/<task>/<run>/` (`/ccb-memory task <name> <run>` creates it).
4. This is an iterative process. Never suggest "wrapping up" or "this won't
   work" until several runs with different inputs have been tried.
5. When re-running a task, always use the LARGEST current input pool
   (see `memory/pool/`).
6. Read only the active run's folder. For other runs use the summaries in
   `memory/results/` — never pull their raw outputs into context.
7. Log significant decisions in `memory/decisions-log.md`.
8. After every significant run, and BEFORE any context compaction or session
   end: update `INDEX.md` and `memory/current-task.md` so nothing is lost
   between sessions. The `<!-- ccb:index:begin/end -->` block in INDEX.md is
   auto-maintained by ccb — update the human-owned parts (best results, key
   insights) OUTSIDE the markers, and never edit inside them.
