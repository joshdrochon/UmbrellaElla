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
K="$1"; OUT="$2"; ROOT="$(cd "$(dirname "$0")/../.." && pwd)"; cd "$ROOT"
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
p = p.replace("{story_json_surfaces_deny_banned}", json.dumps({k: sj[k] for k in sj if k in ("surfaces", "deny", "banned", "banned_words")}, indent=1))
p = p.replace("{story_check_output}", (sc.stdout + sc.stderr).strip())
rows = [(r["id"], r["surface"], r["text"]) for r in csv.DictReader(open("pipeline/story/lines.csv")) if r.get("text")]
random.Random(len(rows)).shuffle(rows)
p += "\n\nLines to judge (id | surface | text), cycle=1, builder=area-worker:\n" + "\n".join(" | ".join(r) for r in rows)
open(sys.argv[1], "w").write(p)
print(len(rows))
P
  n=$(python3 -c "import csv;print(sum(1 for r in csv.DictReader(open('pipeline/story/lines.csv')) if r.get('text')))")
  [ "$n" = 0 ] && { echo "story critic: PASS (no player-facing lines in pipeline/story/lines.csv yet)"; exit 0; }
  ask "$W/packet.md" > "$OUT" 2>&1
  line=$(grep -m1 "^STORY_CRITIC:" "$OUT"); echo "$line"
  echo "$line" | grep -q "^STORY_CRITIC: PASS" && python3 tools/story_check.py --critic "$line" >/dev/null 2>&1 && exit 0
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
echo "usage: critic.sh story|encounter OUT"; exit 2
