#!/bin/sh
# One-command launcher: a fresh agent session for one role on one card. A human runs it, never an agent.
#   tools/start_session.sh <role> <card> [--dry-run] [extra claude args...]   e.g. tools/start_session.sh gameplay-dev UE-12
# Sets JAM_ROLE through tools/agent.sh, loads the card context, and picks the model from
# pipeline/agent-ops/model-tiers.md. The logic is in tools/start_session.py. Windows: tools\start_session.ps1.
py=$(command -v python3 || command -v python) || { echo "start_session.sh: no python3" >&2; exit 2; }
exec "$py" "$(dirname -- "$0")/start_session.py" "$@"
