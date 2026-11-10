#!/usr/bin/env bash
# Honor the configured local/Git marketplace; verify installed bytes separately
# from new-session loading. No commit, push or source rebinding is performed.
set -euo pipefail
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
exec python3 -B "$REPO_ROOT/skills/agentflow/scripts/workflow.py" upgrade-zcode --repo "$REPO_ROOT" "$@"
