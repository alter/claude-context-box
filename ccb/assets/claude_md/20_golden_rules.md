## Golden rules

1. **Fix in source, not at runtime.** Runtime patches die on restart.
2. **Complete every requested task or none.** Partial work wastes time and breaks trust.
3. **Diagnose for 5 minutes before fixing.** Check permissions, env vars, running services first.
4. **Use what exists; don't create parallel solutions.** Read `services/`, `lib/`, helpers before adding new code.
5. **Right tool for the job.** HTTP for APIs, not SSH. SQL for queries, not shell loops.
6. **Update context after every meaningful change.** PROJECT.llm and CONTEXT.llm reflect reality, not wishes.
7. **No mocks in production code paths.** Test data lives in tests/ only.
8. **Test what you ship.** "Should work" means "doesn't work" until proven by an actual run.
9. **Be honest about status.** Trust outweighs the comfort of false success reports.
10. **Use ultrathink for complex tasks.** Plan, analyze, refactor, debug — all benefit from deep thinking.
11. **Fix the existing approach before switching.** It worked before; find what broke instead of starting over.
12. **Research before evaluating.** Investigate implementation details and prior art before praising or rejecting an idea.
