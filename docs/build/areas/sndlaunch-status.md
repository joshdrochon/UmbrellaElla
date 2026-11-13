# sndlaunch status (area/sndlaunch)

## How takes are built here
Recipes: `Audio/Source/<Id>/recipe.json` (same fields as the audio area's recipes). The audio area's helpers
(regen.py, critic.sh on branch `area/audio`) run unforked through a small wrapper kept outside the repo; it does
`git show area/audio:<helper>`, sets the root to this worktree and feeds it the recipe.json files. Request 2 in
docs/build/requests/sndlaunch.md asks for a `--recipe` flag so the wrapper can go.
Provenance: one row per take, inserted sorted among the Audio/ rows.
The spin-down ratchet layer is generated maths (tick rate 60/s falling exponentially, uneven gaps), written into the
recipe as an ffmpeg expression.

## Pieces (Nov 12, after the audio-critic/3 packet fix)
All 16 ids: 3 takes each (StreamLoop 1), `audio_check --scan` no FAIL, `audio_style_check` PASS, blind critic pass
(Saved/AudioLoop/SNDLAUNCH state: every piece `done`, last gap none), provenance origin generated/synthesized.
Reruns under the new packet: KeeperYellowLaunch passed round 10 with no change to the sound. Fixed after a real fail:
- StreamRelease: second pluck rise 0.3 ms to 2 ms (click).
- ClockBeatRepeat: one tick + low clunk per take (the cluster read as a ratchet); level lufs -17 for scan RMS.
- RearCastLaunch: two distinct strokes 450 ms apart, fade_out 0.8.
- WardenShot, FloodShot, RearCastLaunch take 00 were 0.8 s (stale build); rebuilt from cached layers at full length.
RearCastLaunch takes 00/02 reuse cached ElevenLabs candidates in other combinations: the ElevenLabs quota is
exhausted (4 credits left), so no new generation is possible until credits return.

## Left
Unreal import (request 3: arena_audio_import.py has a fixed cue table, no --ids).
Not mine: KeeperHoot has 3 provenance rows each (audio_check --scan FAIL).

## Unreal import (Nov 12, blocked, cause: env)
`Audio/Source/sndlaunch_import.py` imports all takes to `/Game/UmbrellaElla/Audio/<Id>/SW_<Id>_<NN>` (StreamLoop looping).
Run twice (`-run=pythonscript` and `-run=PythonScript`, through ue_slot.sh, UE_5.8 at /Users/Shared): the editor starts and
exits with no LogPython line and no "sndlaunch_import done"; no assets were written. Likely the Python plugin or editor
modules do not load in this worktree (not built here). Next: build lead runs the script after a build, or tells me to build.
No sound is blocked on audio quality; only the .uasset import is left.
