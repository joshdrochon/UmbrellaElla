# sndtele status (Nov 12)
Done: all 19 sounds have takes in Audio/Source/<Id>/ and SoundWave assets in Content/UmbrellaElla/Audio/<Id>/.
audio_style_check PASS (44 files); provenance rows present.
Blocked (cause: check defect): the blind critic packet never names the sound's event or kind (loop vs one-shot), so the
critic fails takes for the wrong reasons (see docs/build/requests/sndtele.md, change to tools/audio_loop.py). main does
not have event_text yet. Until the build lead applies it, every take stays a tracked placeholder
("placeholder: audio critic fail").
Next: after the request lands, run audio_loop round + fresh-session critic per piece, P0 first; flip provenance origin
on each pass.
Not mine, left uncommitted: tools/ue/smoke.sh, tools/ue_run.py (other lane's edits in this worktree).

## Update (after audio-critic/3, event named; ElevenLabs out of credits, synth only)
Pass (blind critic + audio_check + style): all 19 except below. Latest passes this round: TalonWarning, CourierWarning, FloodStiltMove (rebuilt from synth; provenance generated).
Tracked placeholders:
- BellowsWarning: critic A5 failed 4 rounds on the same gap (reads as a wind swell next to the wind family's gust whooshes). Triage: possibly a
  family-target/neighbour defect (wind target has no telegraph kind); work side tried: one 650 ms swell, rising narrow whistle, valve knock, open tail.
  Needs fresh takes or a telegraph line in the wind family target.
- WardenMove: blocked on request 2 in docs/build/requests/sndtele.md (style.json `enemy` target describes only the owl's projectiles).

## Update (wind family target now describes the bellows warning, main fff114d)
BellowsWarning passes: blind critic round 8 (fresh session, A1-A8 true, same take as before, no new ElevenLabs), style PASS, provenance generated.
Round 1-7 failure was a check defect (wind target never described a warning). Still blocked: WardenMove (request 2).

## Update (main critic fixes merged)
WardenMove passes: blind critic round 1 (fresh session, A1-A8 true), style PASS, provenance generated. All 19 sounds now pass; no tracked placeholders left in this lane.
