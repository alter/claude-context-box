## Pre-response validation

Before sending a response that claims work is complete, verify each item:

- [ ] Modified source files, not running processes
- [ ] Changes will survive a restart
- [ ] All requested tasks completed (not a subset)
- [ ] All tests pass (not most)
- [ ] No mocks or hardcoded test data in production paths
- [ ] PROJECT.llm and relevant CONTEXT.llm updated
- [ ] Used ultrathink for genuinely complex sections
- [ ] Honest about state — no "should work", no silent skips

If any item fails, fix it before responding rather than acknowledging it after.
