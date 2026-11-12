#!/bin/sh
# Start any agent CLI on a card, journaled (AGENTS.md section 1). Use it for every agent, Claude Code or not.
#   tools/agent.sh <role> <card> <agent-cli> [args...]     e.g. tools/agent.sh gameplay-dev UE-12 claude
# Sets JAM_ROLE (a key of "roles" in pipeline/agent-ops/gates.json) and JAM_CARD, runs journal.py start and
# resume, runs the CLI, then writes a checkpoint that carries the next step forward and logs the session's tokens
# and cost (tools/spend_log.py; never changes the exit code). Exits with the CLI's code.
# Windows: tools\agent.ps1 (same arguments).
set -u
if [ $# -lt 3 ]; then
  echo "usage: tools/agent.sh <role> <card> <agent-cli> [args...]" >&2
  exit 2
fi
role=$1
card=$2
shift 2
root=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
py=$(command -v python3 || command -v python) || { echo "agent.sh: no python3" >&2; exit 2; }
if ! "$py" -c "import json,sys; sys.exit(0 if sys.argv[1] in json.load(open(sys.argv[2]))['roles'] else 1)" \
    "$role" "$root/pipeline/agent-ops/gates.json"; then
  echo "agent.sh: unknown role '$role'; use a key of roles in pipeline/agent-ops/gates.json" >&2
  exit 2
fi
JAM_ROLE=$role
JAM_CARD=$card
# JAM_HOST labels caps, stuck reports and journal rows; default = the hook's hash, never the raw hostname.
JAM_HOST=${JAM_HOST:-$("$py" -c "import hashlib,socket; print('host-' + hashlib.sha256(socket.gethostname().encode()).hexdigest()[:6])")}
export JAM_ROLE JAM_CARD JAM_HOST
"$py" "$root/tools/journal.py" start --role "$role" --card "$card" || exit 2
"$py" "$root/tools/journal.py" resume --card "$card"
started=$(date -u +%Y-%m-%dT%H:%M:%S)
"$@"
code=$?
"$py" "$root/tools/journal.py" checkpoint --card "$card" --note "agent CLI '$1' exited $code (tools/agent.sh)" >/dev/null
"$py" "$root/tools/spend_log.py" log --from-agent-log --since "$started" --role "$role" --card "$card" \
  --model "${JAM_MODEL:-unknown}" || true
exit $code
