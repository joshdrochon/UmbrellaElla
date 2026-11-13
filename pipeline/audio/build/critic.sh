#!/bin/bash
# critic.sh <piece> [card]  : new round, fresh blind critic session on a copy of the packet, record the verdict.
# Same session set-up as the gate (tools/build/critic.sh audio): same prompt, same model, so the two agree.
set -u
PIECE=$1; CARD=${2:-AUDIO-1}
cd "$(dirname "$0")/../../.." || exit 2
ROOT=$(pwd)
T=${TMPDIR:-/tmp}
python3 tools/audio_loop.py round --card "$CARD" --piece "$PIECE" > "$T/round_$PIECE.txt" 2>&1
grep -E "style=|FAIL " "$T/round_$PIECE.txt" | tail -6
PKT=$(sed -n 's/^CRITIC PACKET: //p' "$T/round_$PIECE.txt" | tail -1)
[ -d "$PKT" ] || { echo "no packet"; tail -5 "$T/round_$PIECE.txt"; exit 2; }
D=$(mktemp -d "$T/acritic.XXXXXX"); cp -R "$PKT"/. "$D"/
SID=critic-$PIECE-$(date +%s)-$RANDOM
(cd "$D" && env -u CLAUDECODE -u CLAUDE_CODE_ENTRYPOINT claude -p "$(cat "$ROOT/tools/audio_critic_prompt.md")

The packet for this sound is the files in the current folder. Read them (the text files and the spectrogram images)." \
  --permission-mode bypassPermissions --disallowedTools "Bash" Edit Write --model "${CRITIC_MODEL:-claude-opus-5-5}") > "$D/reply.txt" 2>&1
python3 -c "import json,re,sys;t=open(sys.argv[1]).read();m=re.search(r'\{.*\}',t,re.S);json.dump(json.loads(m.group(0)),open(sys.argv[2],'w'))" "$D/reply.txt" "$D/reply.json" \
  || { echo "bad reply:"; head -c 600 "$D/reply.txt"; exit 2; }
python3 tools/audio_loop.py verdict --card "$CARD" --piece "$PIECE" --critic "$SID" --reply "$D/reply.json"
python3 -c "import json,sys;r=json.load(open(sys.argv[1]));print(r['verdict'],'|',r['biggest_gap'],'|',r['basis']);[print(k,v[0],v[1][:220]) for k,v in r['rows'].items() if not v[0]]" "$D/reply.json"
