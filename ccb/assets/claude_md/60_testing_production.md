## Testing and production hygiene

### Tests

- Write a test, **run it immediately**, fix until it passes — then move on.
- Never report "done" with failing tests. All pass, not most.
- A test that was never run does not exist.

### Production code

- **No mocks.** `return [{"id": 1, "name": "Test"}]` is wrong; query the real source.
- **No hardcoded secrets.** `API_KEY = "test-123"` is wrong; use `os.getenv("API_KEY")`.
- **No fixture data.** `users = ["demo@test.com"]` is wrong; fetch from the database.

### Honesty

If a blocker exists, name it and ask. Do not silently bypass:

- Wrong: "X was broken so I disabled it"
- Right: "X is broken. Fix X first, or do you authorize bypassing it?"

If you removed something, say so. If a test fails, say so. False success reports
cost more than a delayed honest one.
