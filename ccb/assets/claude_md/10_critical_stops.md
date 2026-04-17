## Critical stops

When any of these triggers fires, stop and switch to the correct action before
continuing.

| Trigger | Wrong | Correct |
|---|---|---|
| ssh to API endpoint | `ssh root@host curl ...` | `curl -v http://host:8080/api` |
| edit inside container | `kubectl exec pod -- vi` | edit source, rebuild image |
| `pip install` in poetry project | `pip install requests` | `poetry add requests` |
| `permission denied` error | rewrite the auth system | `chmod +x script.sh` first |
| thinking about a rewrite | start refactoring immediately | diagnose for 5 minutes |
| writing `CONTEXT.llm` in `.venv/` | `.venv/CONTEXT.llm` (lost) | `./module/CONTEXT.llm` |
| runtime fix attempt | `kubectl exec pod -- python -c ...` | edit source, commit, rebuild |
| user gives an HTTP endpoint to test | ssh to the server | curl/httpie as an external client |

Use venv (`.venv/`, `venv/`) for **package installation** — but never put
`CONTEXT.llm` files inside it; venvs are not committed.
