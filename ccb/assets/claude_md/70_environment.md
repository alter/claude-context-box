## Environment detection

Detect the project's package manager from lockfiles and use the matching tool.
Never mix managers in the same project.

| Lockfile present | Use | Never use |
|---|---|---|
| `poetry.lock` | `poetry add`, `poetry install` | `pip install` |
| `Pipfile.lock` | `pipenv install` | `pip install`, `poetry add` |
| `uv.lock` | `uv add`, `uv sync` | `pip install` |
| `requirements.txt` only | `pip3 install -r requirements.txt` | `poetry add` |
| `pnpm-lock.yaml` | `pnpm install`, `pnpm add` | `npm install`, `yarn add` |
| `yarn.lock` | `yarn add` | `npm install`, `pnpm add` |
| `package-lock.json` | `npm install`, `npm i <pkg>` | `pnpm`, `yarn` |
| `go.mod` | `go get`, `go mod tidy` | `dep`, `glide` |
| `Cargo.toml` | `cargo add` | manually editing `Cargo.toml` |

Always use `python3` (never `python`), `pip3` (never `pip`). Inside an
activated venv, `pip` and `python` resolve correctly — but be explicit so the
intent is clear in transcripts and scripts.
