#!/usr/bin/env bash
set -euo pipefail

ROOT="${CODEX_PROJECT_DIR:-${CLAUDE_PROJECT_DIR:-$(git rev-parse --show-toplevel 2>/dev/null || pwd)}}"
SCRIPT="$ROOT/.codestable/tools/validate-implementation-review.py"

if [[ ! -f "$SCRIPT" ]]; then
  exit 0
fi

python3 "$SCRIPT" --root "$ROOT"
