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
# Model split (Josh, Nov 12): Fable for the hardest jobs (art loops, audio), Opus for the rest; WORKER_MODEL overrides.
case "$A" in art*|audio|snd*) DEFAULT_MODEL=claude-fable-5-2 ;; *) DEFAULT_MODEL=claude-opus-5-5 ;; esac
MODEL="${WORKER_MODEL:-$DEFAULT_MODEL}"
cd "$WT"
env -u CLAUDECODE -u CLAUDE_CODE_ENTRYPOINT nohup claude -p "$PROMPT" --permission-mode bypassPermissions \
  --disallowedTools "Bash(git push:*)" --model "$MODEL" >> "$BASE/logs/$A.log" 2>&1 &
echo "$A worker ($MODEL) pid $! worktree $WT log $BASE/logs/$A.log"
