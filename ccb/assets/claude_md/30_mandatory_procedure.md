## Mandatory procedure for code changes

For any non-trivial code modification, work through these steps in order. The
hooks installed by ccb pre-load steps 1–3 into your context at session start —
you don't need to re-read those files manually.

1. **Read `PROJECT.llm`** to understand the architecture and tech stack.
2. **Locate the target module** that owns the change.
3. **Read that module's `CONTEXT.llm`** to understand its interface and invariants.
4. **Plan with ultrathink.** Consider impact on dependents, tests, and contracts.
5. **Analyze with ultrathink.** Trace the actual code flow involved.
6. **Make the smallest possible change.** Preserve unaffected behavior.
7. **Verify with ultrathink.** Run the relevant tests; reason about edge cases.
8. **Update contexts.** The `SessionEnd` hook captures most of this automatically;
   manual `/ccb-update` is only needed when interfaces change mid-session.
