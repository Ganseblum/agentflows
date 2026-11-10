#!/usr/bin/env bash
# Install the configured local source and verify its runtime payload.
# No commit, push, marketplace rebinding or global-rule update is performed.
set -euo pipefail
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
exec python3 -B "$REPO_ROOT/skills/agentflow/scripts/workflow.py" upgrade-codex --repo "$REPO_ROOT" "$@"
