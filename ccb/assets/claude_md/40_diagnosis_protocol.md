## Diagnosis protocol

Before any fix, spend up to 5 minutes gathering evidence. Most "broken" systems
fail one of these cheap checks:

| Command | Detects |
|---|---|
| `ls -la <file>` | Wrong permissions (`chmod +x` fixes ~50% of "won't run") |
| `echo $VAR` | Missing or empty environment variables |
| `which python3` | Wrong interpreter (system vs venv) |
| `ps aux \| grep <service>` | Service crashed or never started |
| `lsof -i :<port>` | Port held by another process |
| `pip3 list \| grep <pkg>` | Dependency not installed |
| `git diff HEAD~1` | Recent change introducing the regression |

Form a hypothesis from the evidence, then try the cheapest fix first
(chmod, export, restart). Code changes come last, after simple fixes fail.
