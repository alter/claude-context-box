## Memory structure (iterative research projects)

These rules apply ONLY when `INDEX.md` and `memory/` exist in the project root
(scaffold them with `/ccb-memory init`):

1. Read `INDEX.md` FIRST, before any other exploration. It is the entry point.
2. `memory/validation-protocol.md` is inviolable. Read it before any backtest,
   generation, or analysis, and follow it exactly.
3. This is an iterative research process. Never suggest "wrapping up" or
   "this won't work" until several passes with different pools have run.
4. When returning to a previous experiment range, always use the LARGEST
   current strategy pool (see `memory/strategy-pool/`).
5. Record every iteration in `memory/experiments/<range>/<version>/`
   (`/ccb-memory experiment <range> <version>` creates the folder and
   `task-spec.md`). Log significant decisions in `memory/decisions-log.md`.
6. After every significant run, and BEFORE any context compaction or session
   end: update `INDEX.md` and `memory/current-experiment.md` so nothing is
   lost between sessions. The `<!-- ccb:index:begin/end -->` block in INDEX.md
   is auto-maintained by ccb — update the human-owned parts (best results,
   key insights) OUTSIDE the markers, and never edit inside them.
