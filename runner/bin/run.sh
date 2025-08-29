#!/usr/bin/env bash
set -euo pipefail

# Always run from repo root
REPO_ROOT="/Users/aman/Developer/Personal/content-writer-mcp"
# Fixed Node path you provided
NODE_BIN="/opt/homebrew/opt/node@22/bin/node"
NODE_BIN="/opt/homebrew/opt/node@22/bin/node"
export PYTHON_BIN="/Users/aman/Developer/Personal/content-creator/.venv/bin/python"

cd "$REPO_ROOT"

# Sanity check
if [[ ! -x "$NODE_BIN" ]]; then
  echo "ERROR: Node not found or not executable at: $NODE_BIN" >&2
  exit 127
fi

# Hand off to your Node runner, forwarding all args
exec "$NODE_BIN" runner/bin/run.js "$@"