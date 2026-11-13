#!/bin/sh
# Resume one area of the build from its branch, on your own machine (a human runs it, never an agent):
#   tools/area.sh                  HANDOFF.md and every area's branch
#   tools/area.sh <name>           check out area/<name>, merge main in, guard the lane, start your agent with the brief
#   tools/area.sh <name> --done    merge main in, check the lane, merge the area into main, print the push command
# Options: --agent claude|codex|none, --prompt. The logic is in tools/area.py. Windows: tools\area.ps1 (same arguments).
here=$(dirname -- "$0")
if [ ! -f "$here/area.py" ]; then
  echo "area: tools/area.py is missing here. Fix: type 'git pull origin main' in the repo folder, then run tools/area.sh again." >&2
  exit 2
fi
py=$(command -v python3 || command -v python)
if [ -z "$py" ] || ! "$py" -c 'import sys; sys.exit(0 if sys.version_info >= (3, 9) else 1)' 2>/dev/null; then
  echo "area: Python 3.9 or newer is not installed. Install it from https://www.python.org/downloads/ then run tools/area.sh again." >&2
  exit 2
fi
exec "$py" "$here/area.py" "$@"
