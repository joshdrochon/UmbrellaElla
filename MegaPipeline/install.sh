#!/usr/bin/env bash
# Installs or updates the Umbrella Ella pipeline from MegaPipeline/repo/ into the repo root (a human runs it).
#   bash MegaPipeline/install.sh                    # install, dry run: lists what would be copied and every conflict
#   bash MegaPipeline/install.sh --apply            # install: copies every file that does not already exist
#   bash MegaPipeline/install.sh --update           # update, dry run: one line per change, nothing written
#   bash MegaPipeline/install.sh --update --apply   # update: replaces pipeline files, backs up what it replaces
# Install never overwrites. Update replaces only pipeline files (MegaPipeline/manifest.json) that still hold a
# version the pipeline shipped; it never touches Source/, Content/, Config/, the GDD or the team's own files.
# Windows: powershell -File MegaPipeline\install.ps1 (same options). The logic is in MegaPipeline/install.py.
set -euo pipefail
here="$(cd "$(dirname "$0")" && pwd)"
py=$(command -v python3 || command -v python || true)
if [ -z "$py" ]; then
  echo "install: Python 3 is not installed. Install it from https://www.python.org/downloads/ then run this again." >&2
  exit 2
fi
exec "$py" "$here/install.py" "$@"
