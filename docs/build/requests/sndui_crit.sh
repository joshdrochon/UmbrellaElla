#!/bin/bash
# crit.sh <Id>...: one blind critic round per piece (the audio lane's critic.sh), in parallel, one loop card per piece.
cd "$(git rev-parse --show-toplevel)" || exit 2
mkdir -p /tmp/sndui/crit
for id in "$@"; do
  ( python3 tools/audio_loop.py status --card SNDUI-$id >/dev/null 2>&1 || python3 tools/audio_loop.py start --card SNDUI-$id --issue 0 --ids $id --builder sndui-worker >/dev/null
    TMPDIR=/tmp/sndui/crit pipeline/audio/build/critic.sh $id SNDUI-$id > /tmp/sndui/crit/$id.out 2>&1 ) &
done
wait
for id in "$@"; do echo "== $id"; tail -12 /tmp/sndui/crit/$id.out; done
