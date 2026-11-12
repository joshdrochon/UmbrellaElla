#!/bin/sh
# One command for the whole jam loop, Claude Code or Codex (a human runs it, never an agent):
#   tools/kickoff.sh                 no options: pipeline version, connection check, then start with the agent found
#   tools/kickoff.sh --agent codex   (or claude) to choose; --check for the check only
# Options: --check, --dry-run, --practice, --parallel N, --watch MIN, --max-cards N (KICKOFF_MAX_CARDS: stop once N
# cards merged or got blocked this run; first night: --max-cards 5), --until G1 (KICKOFF_UNTIL: only the cards on
# the G1 path, then the Mac package; stops when its smoke passes), --prompt TEXT, --prompt-file F.
# The logic is in tools/kickoff.py. Windows: tools\kickoff.ps1 (same arguments).
here=$(dirname -- "$0")
if [ ! -f "$here/kickoff.py" ]; then
  echo "kickoff: the pipeline is not installed here ($here/kickoff.py is missing). Fix: type 'git pull origin main' in the repo folder, then run tools/kickoff.sh again." >&2
  exit 2
fi
py=$(command -v python3 || command -v python)
if [ -z "$py" ] || ! "$py" -c 'import sys; sys.exit(0 if sys.version_info >= (3, 9) else 1)' 2>/dev/null; then
  echo "kickoff: Python 3.9 or newer is not installed. Install it from https://www.python.org/downloads/ then run tools/kickoff.sh again." >&2
  exit 2
fi
exec "$py" "$here/kickoff.py" "$@"
