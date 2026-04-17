#!/usr/bin/env bash
# Run the local e2e suite inside a clean Docker container.
# Catches regressions that depend on the developer's PYTHONPATH, venv, or shell setup.
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
IMAGE="ccb-e2e:local"

echo "==> building $IMAGE"
docker build --quiet --tag "$IMAGE" --file "$REPO_ROOT/tests/e2e/Dockerfile" "$REPO_ROOT" >/dev/null
echo "==> running e2e suite in container"
docker run --rm "$IMAGE"
