#!/usr/bin/env bash
# Blind critic sessions for gate merges (Josh, Nov 12). A fresh Claude Code session in an empty folder, given only the
# packet, so it cannot see who built what.   Usage: tools/build/critic.sh story|encounter <out-file>
#   story:     tools/story_critic_prompt.md filled with the bible, story.json and story_check output, plus every line
#              in pipeline/story/lines.csv (shuffled, ids only); needs a STORY_CRITIC: PASS line that
#              tools/story_check.py --critic accepts.
#   encounter: tools/encounter_check.py --critic-packet for each phase, with the run log $ENCOUNTER_LOG and capture
#              $ENCOUNTER_VIDEO; needs ENCOUNTER CRITIC: PASS for every phase. Until the game can write a run log (the
#              flow area's Start Game path and smoke), it prints DEFERRED and exits 0; the first gate after that runs it.
set -u
K="$1"; OUT="$2"; ROOT="$(git rev-parse --show-toplevel)"; cd "$ROOT"   # the checkout it is run in (the gate)
W=$(mktemp -d "${TMPDIR:-/tmp}/critic.XXXXXX")
ask() { (cd "$W" && env -u CLAUDECODE -u CLAUDE_CODE_ENTRYPOINT claude -p "$(cat "$1")" --permission-mode bypassPermissions \
  --disallowedTools "Bash" Edit Write --model "${CRITIC_MODEL:-claude-sonnet-5-5}") ; }
if [ "$K" = story ]; then
  python3 - "$W/packet.md" <<'P'
import csv, json, random, subprocess, sys
p = open("tools/story_critic_prompt.md").read().split("---", 1)[-1]
sj = json.load(open("pipeline/story/story.json"))
sc = subprocess.run([sys.executable, "tools/story_check.py"], capture_output=True, text=True)
p = p.replace("{story_bible}", open("pipeline/story/story-bible.md").read())
p = p.replace("{story_json_surfaces_deny_banned}", json.dumps({k: sj[k] for k in sj if k in ("surfaces", "deny", "banned", "banned_words", "length_exceptions")}, indent=1))
p = p.replace("{story_check_output}", (sc.stdout + sc.stderr).strip())
sys.path.insert(0, "tools"); import story_check
# Only lines with no passed verdict on their exact text (critic-results.csv); held lines (ship=no) never reach a player.
# A line's mode (Start Game / Director's Cut) goes with it, so a Director's-Cut-only line is not judged against Start Game (Nov 13).
rows = [(r["id"], r["surface"] + (" [" + next(p.strip()[5:] for p in (r.get("note") or "").split(";") if p.strip().startswith("mode=")) + "]" if "mode=" in (r.get("note") or "") else ""), r["text"])
        for r in story_check.lines_to_judge("pipeline/story/lines.csv", story_check.CRITIC_RESULTS)]
random.Random(len(rows)).shuffle(rows)
p += "\n\nLines to judge (id | surface | text), cycle=1, builder=area-worker:\n" + "\n".join(" | ".join(r) for r in rows)
open(sys.argv[1], "w").write(p)
print(len(rows))
P
  n=$(python3 -c "import sys; sys.path.insert(0,'tools'); import story_check as s; print(len(s.lines_to_judge('pipeline/story/lines.csv', s.CRITIC_RESULTS)))")
  [ "$n" = 0 ] && { echo "story critic: PASS (every shipped line already passed on its exact text; nothing changed to judge)"; exit 0; }
  echo "story critic: judging $n line(s) without a passed verdict on their current text"; export STORY_CRITIC_LINES=$n
  # A panel of 3 fresh sessions, all must pass (Nov 12: one session passed lines another failed on the same bible).
  : > "$OUT"; ok=1
  for i in 1 2 3; do
    ask "$W/packet.md" > "$OUT.$i" 2>&1; cat "$OUT.$i" >> "$OUT"
    line=$(grep -m1 "^STORY_CRITIC:" "$OUT.$i"); echo "critic $i: $line"
    echo "$line" | grep -q "^STORY_CRITIC: PASS" && python3 tools/story_check.py --critic "$line" >/dev/null 2>&1 || ok=0
  done
  [ $ok = 1 ] && exit 0
  echo "story critic: FAIL ($OUT)"; exit 1
fi
if [ "$K" = encounter ]; then
  if [ -z "${ENCOUNTER_LOG:-}" ] || [ ! -f "${ENCOUNTER_LOG:-}" ]; then
    echo "encounter critic: DEFERRED (no run log yet; set ENCOUNTER_LOG and ENCOUNTER_VIDEO once the game runs)"; exit 0; fi
  python3 tools/encounter_check.py --playthrough "$ENCOUNTER_LOG" --preset GDD-SH1.0 || exit 1
  : > "$OUT"; ok=1
  for ph in wings mechanisms clock; do
    python3 tools/encounter_check.py --critic-packet "GDD-SH1.0/$ph" --log "$ENCOUNTER_LOG" --video "${ENCOUNTER_VIDEO:-none}" > "$W/packet.md"
    cp "$ENCOUNTER_LOG" "$W/"; [ -f "${ENCOUNTER_VIDEO:-}" ] && cp "$ENCOUNTER_VIDEO" "$W/"
    ask "$W/packet.md" >> "$OUT" 2>&1
    grep "^ENCOUNTER CRITIC:" "$OUT" | tail -1 | grep -q "PASS" || ok=0
  done
  grep "^ENCOUNTER CRITIC:" "$OUT"; [ $ok = 1 ] && exit 0; echo "encounter critic: FAIL ($OUT)"; exit 1
fi
if [ "$K" = audio ]; then
  # Usage: critic.sh audio OUT ID[,ID...] CARD. One blind critic session per sound id (tools/audio_loop.py round makes the
  # packet; tools/audio_critic_prompt.md is the prompt). Prints AUDIO_CRITIC: PASS|FAIL piece=<Id> gap=...; never blocks.
  IDS="$3"; CARD="$4"; : > "$OUT"
  python3 tools/audio_loop.py start --card "$CARD" --issue 0 --ids "$IDS" --builder "area-worker" >/dev/null 2>&1
  # Packets and verdicts run one at a time (they share the card's loop state); only the critic sessions run in parallel,
  # at most CRITIC_JOBS (default 4) at once (Nov 12: one gate spent 30+ min on 29 serial critics).
  ASK_AUDIO="$(cat "$ROOT/tools/audio_critic_prompt.md")

The packet for this sound is the files in the current folder. Read them (the text files and the spectrogram images)."
  for id in $(echo "$IDS" | tr ',' ' '); do
    pk=$(python3 tools/audio_loop.py round --card "$CARD" --piece "$id" 2>&1 | sed -n 's/^CRITIC PACKET: //p')
    if [ -z "$pk" ] || [ ! -d "$pk" ]; then echo "$id" >> "$W/nopacket"; continue; fi
    mkdir -p "$W/$id"; cp -R "$pk"/. "$W/$id"/
  done
  for id in $(echo "$IDS" | tr ',' ' '); do
    [ -d "$W/$id" ] || continue
    while [ "$(jobs -rp | wc -l | tr -d ' ')" -ge "${CRITIC_JOBS:-4}" ]; do sleep 2; done
    (cd "$W/$id" && env -u CLAUDECODE -u CLAUDE_CODE_ENTRYPOINT claude -p "$ASK_AUDIO" --permission-mode bypassPermissions \
      --disallowedTools "Bash" Edit Write --model "${CRITIC_MODEL:-claude-sonnet-5-5}" > reply.txt 2>&1) &
  done
  wait
  for id in $(echo "$IDS" | tr ',' ' '); do
    if [ ! -d "$W/$id" ]; then echo "AUDIO_CRITIC: FAIL piece=$id gap=no packet (round failed)" | tee -a "$OUT"; continue; fi
    D="$W/$id"
    python3 -c "import json,re,sys;t=open(sys.argv[1]).read();m=re.search(r'\{.*\}',t,re.S);json.dump(json.loads(m.group(0)),open(sys.argv[2],'w'))" "$D/reply.txt" "$D/reply.json" 2>/dev/null
    v=$(python3 -c "import json,sys;r=json.load(open(sys.argv[1]));print(r['verdict']+'|'+r.get('biggest_gap','').replace('|','/'))" "$D/reply.json" 2>/dev/null || echo "fail|critic reply unreadable")
    python3 tools/audio_loop.py verdict --card "$CARD" --piece "$id" --critic "gate-critic-$id-$$" --reply "$D/reply.json" >/dev/null 2>&1
    [ "${v%%|*}" = pass ] && echo "AUDIO_CRITIC: PASS piece=$id" | tee -a "$OUT" || echo "AUDIO_CRITIC: FAIL piece=$id gap=${v#*|}" | tee -a "$OUT"
  done
  exit 0
fi
echo "usage: critic.sh story|encounter|audio OUT"; exit 2
