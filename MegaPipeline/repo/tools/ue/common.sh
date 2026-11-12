# Shared settings for the Mac scripts. Commands follow pipeline/unreal/commands-and-packaging.md; [VERIFY] on 5.8.4.
# Timeouts, dirty-tree refusal, BUILD_INFO.txt and smoke-log checks live in tools/ue_run.py (same for .ps1).
set -euo pipefail
REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
PROJECT="${PROJECT:-$REPO/UmbrellaElla.uproject}"
UE_ROOT="${UE_ROOT:-/Users/Shared/Epic Games/UE_5.8}"
UE_TIMEOUT="${UE_TIMEOUT:-7200}"   # seconds before a hung UBT/UAT/editor run is killed (exit 124)
PY="${PYTHON:-python3}"
UE_RUN=("$PY" "$REPO/tools/ue_run.py" --root "$REPO")
LOGDIR="$REPO/Saved/Logs/pipeline"
STAMP="$(date +%Y%m%d-%H%M%S)"
mkdir -p "$LOGDIR"
[ -f "$PROJECT" ] || { echo "No project at $PROJECT (Day-0 skeleton card creates it)"; exit 2; }
[ -d "$UE_ROOT/Engine" ] || { echo "UE_ROOT not found: $UE_ROOT. Set UE_ROOT to your 5.8.4 install."; exit 2; }
