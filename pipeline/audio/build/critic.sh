#!/bin/bash
# critic.sh <piece> [card]  : new round, fresh blind critic session in the packet folder, record verdict.
set -u
PIECE=$1; CARD=${2:-AUDIO-1}
cd "$(dirname "$0")/../../.." || exit 2
python3 tools/audio_loop.py round --card "$CARD" --piece "$PIECE" > /tmp/round_$PIECE.txt 2>&1
cat /tmp/round_$PIECE.txt | grep -E "style=|FAIL " | tail -6
PKT=$(grep -o '/.*packet' /tmp/round_$PIECE.txt | tail -1)
[ -d "$PKT" ] || { echo "no packet"; exit 2; }
RD=$(dirname "$PKT")
SID=critic-$PIECE-$(date +%s)-$RANDOM
( cd "$PKT" && claude -p "Read brief.md in this folder and follow it exactly. Reply with only the JSON object." \
    --disallowedTools Bash Edit Write --model ${CRITIC_MODEL:-sonnet} --output-format text > "$RD/reply.txt" 2> "$RD/err.txt" )
python3 - "$RD/reply.txt" "$RD/reply.json" <<'P'
import sys,re,json
t=open(sys.argv[1]).read()
m=re.search(r'\{.*\}',t,re.S)
json.dump(json.loads(m.group(0)),open(sys.argv[2],'w'))
P
[ $? = 0 ] || { echo "bad reply:"; head -c 600 "$RD/reply.txt"; exit 2; }
python3 tools/audio_loop.py verdict --card "$CARD" --piece "$PIECE" --critic "$SID" --reply "$RD/reply.json"
python3 -c "import json;r=json.load(open('$RD/reply.json'));print(r['verdict'],'|',r['biggest_gap'],'|',r['basis']);[print(k,v[0],v[1][:140]) for k,v in r['rows'].items() if not v[0]]"
