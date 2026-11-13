#!/usr/bin/env bash
# Start (or restart) one area worker on Mac with Claude Code, in that area's worktree.
# Usage: tools/build/start_area.sh <move|keeper|health|flow|arena|enemies|progression|story> [extra instruction]
# Worktree: ../UmbrellaElla-areas/<area> on branch area/<area> (created from origin if missing). Log: ../UmbrellaElla-areas/logs/<area>.log
set -eu
A="$1"; EXTRA="${2:-}"; ROOT="$(cd "$(dirname "$0")/../.." && pwd)"; BASE="$(dirname "$ROOT")/UmbrellaElla-areas"
WT="$BASE/$A"; mkdir -p "$BASE/logs"
if [ ! -d "$WT" ]; then
  git -C "$ROOT" fetch -q origin
  if git -C "$ROOT" rev-parse -q --verify "refs/remotes/origin/area/$A" >/dev/null; then
    git -C "$ROOT" worktree add "$WT" -B "area/$A" "origin/area/$A"
  else git -C "$ROOT" worktree add "$WT" -b "area/$A" main; fi
fi
# First editor launch writes this file and test.sh fails once on the change; seed it from the main checkout.
mkdir -p "$WT/Saved/Config/MacEditor"; cp -n "$ROOT/Saved/Config/MacEditor/GameUserSettings.ini" "$WT/Saved/Config/MacEditor/" 2>/dev/null || true
PROMPT="You are the '$A' area worker for Umbrella Ella (UE 5.8.4). Your worktree is $WT on branch area/$A.
Read docs/build/worker-rules.md, then docs/build/areas/$A.md, and docs/build/areas/$A-status.md if it exists (it says
what is already done). Build your area to its definition of done: G1 Rule IDs first, then the later list.
Commit after each working slice (git -c core.hooksPath=/dev/null commit). Never push, never touch main or another lane.
Keep working until your area is done or you are truly blocked. $EXTRA"
# Model: Sonnet by default (Josh, Nov 12 evening); WORKER_MODEL overrides: claude-opus-5-5 for repeat-failure escalation,
# claude-fable-5-2 only by an explicit emergency call that is reported to Josh (worker-rules.md).
DEFAULT_MODEL=claude-sonnet-5-5   # Josh, Nov 12 evening: Sonnet by default; escalation per worker-rules.md
MODEL="${WORKER_MODEL:-$DEFAULT_MODEL}"
# Image spend (Josh Spend OK): one counter shared by every worker on this Mac, one hard total cap set by the lead.
export UE_SLOTS="${UE_SLOTS:-2}"   # workers share 2 engine slots even through a lane's older ue_slot.sh copy (the gate has its own)
export IMAGE_SPEND_FILE="$BASE/logs/image-spend.json"
[ -f "$BASE/logs/image-cap-usd.txt" ] && export IMAGE_SPEND_CAP_USD="$(cat "$BASE/logs/image-cap-usd.txt")"
export AUDIO_SPEND_FILE="$BASE/logs/audio-spend.json"
[ -f "$BASE/logs/audio-cap.txt" ] && export AUDIO_SPEND_CAP="$(cat "$BASE/logs/audio-cap.txt")"
cd "$WT"
# A new lane started from a lead brief has no area file; write it from the brief so the worker has a definition of
# done and status files that cite it resolve (pipeline_check). Committed by the worker with its first slice.
if [ ! -f "docs/build/areas/$A.md" ] && [ -n "${2:-}" ]; then
  mkdir -p docs/build/areas
  { echo "# Area: $A"; echo; echo "Started by the build lead from this brief ($(date +%Y-%m-%d)). It is the definition of done."; echo; echo "$2"; } > "docs/build/areas/$A.md"
fi
# Own session (setsid): a worker must never die with the shell, tool call or helper script that started it
# (Nov 12 20:29: ~10 workers died silently together). The exit line records how each worker ended.
export WORKER_PROMPT="$PROMPT" WORKER_MODEL_ID="$MODEL" WORKER_LOG="$BASE/logs/$A.log" WORKER_STOP="$BASE/.stop-$A"
rm -f "$BASE/.stop-$A"   # an intentional stop (lead, switch, pause) touches this file before killing; then no resume
env -u CLAUDECODE -u CLAUDE_CODE_ENTRYPOINT nohup python3 -c '
import os, signal, subprocess, sys, time
os.setsid()
for s in (signal.SIGHUP, signal.SIGINT): signal.signal(s, signal.SIG_IGN)
log = open(os.environ["WORKER_LOG"], "a")
prompt = os.environ["WORKER_PROMPT"]
for attempt in range(3):
    p = subprocess.Popen(["claude", "-p", prompt, "--permission-mode", "bypassPermissions",
                          "--disallowedTools", "Bash(git push:*)", "--model", os.environ["WORKER_MODEL_ID"]],
                         stdout=log, stderr=subprocess.STDOUT)
    rc = p.wait()
    log.write("\nWORKER_EXIT rc=%s signal=%s at %s\n" % (rc, -rc if rc < 0 else 0, time.strftime("%H:%M:%S"))); log.flush()
    # Killed from outside (SIGTERM 143 / signal) mid-work: resume once more, up to 3 runs (Nov 12: mass SIGTERM 20:29, 22:15).
    if (rc not in (143, 137) and rc >= 0) or os.path.exists(os.environ["WORKER_STOP"]):
        break
    log.write("WORKER_RESUME after outside kill (run %d)\n" % (attempt + 2)); log.flush(); time.sleep(20)
    prompt = ("Lead: your previous session was killed from outside mid-work. Resume exactly where your status file and git log "
              "say you were; commit anything finished first. Original brief follows.\n\n" + os.environ["WORKER_PROMPT"])
log.close()
' >/dev/null 2>&1 &
echo "$A worker ($MODEL) pid $! worktree $WT log $BASE/logs/$A.log"
