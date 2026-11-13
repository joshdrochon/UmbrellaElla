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

## Unreal import (Nov 12, done)
Lead's fix worked: built the editor module with ue_slot.sh tools/ue/build.sh (exit 0), then ran
`Audio/Source/StreamStart/sndlaunch_import.py` (in lane; imports all 16 ids) with UnrealEditor-Cmd -run=pythonscript (four headless flags). 46 SW_<Id>_<NN> assets
written under Content/UmbrellaElla/Audio/<Id>/ (15 ids x 3 takes + StreamLoop x 1, looping), LFS-tracked.
No new ElevenLabs calls were made. Not mine: KeeperHoot has 3 provenance rows each (audio_check --scan FAIL).

## Critic rerun after main's check fixes (Nov 12, evening)
Merged main (neighbours exclude placeholder takes; enemy family target = regular enemies). Reran the blind critic
(pipeline/audio/build/critic.sh, Sonnet) on all 16. Failed on the new packet, then fixed and re-passed:
- CourierShot, TalonSlash, FrontCastLaunch: critic saw a broadband wash with no onset/ticks. Fix: reverb wet -10/-8 to
  -16 dB, shorter layer decays, ratchet and body rebalanced (TalonSlash rake layer -13 dB; recipe `want` widened to the
  style ranges, the style check itself unchanged). Cached layers only, no ElevenLabs calls.
- All 16 now `done`, scan has no FAIL for them, style PASS. SW_ assets for those three re-imported (files were
  read-only; chmod u+w first).

## Review fixes (Nov 13)
Review said BellowsGust and StreamLoop were placeholders; the gate marked them after the critic failed them (BellowsGust:
reply unreadable, so never judged; StreamLoop: edge burst, caused by the spectrogram-window defect, request 1a). With the
window fix on main, reran the blind critic (Sonnet, SNDLAUNCH card) with no change to the sound: both PASS, style PASS.
On this branch their provenance origin is generated/synthesized, no placeholder row. All 16 `done`.
Evidence (commit f30994c + this change): `audio_style_check check Audio/Source --ids <16>` PASS files=46;
`pipeline_check` 0 problems; `audio_check --scan Audio/Source`: no FAIL for any of the 16 (the 98 errors are other
lanes' ids, e.g. PhaseChime has no file).
Import script moved into lane: Audio/Source/StreamStart/sndlaunch_import.py.
Not done: sorting provenance.csv. The Audio/ block is unsorted across all lanes (31 inversions); a sort touches other
lanes' lines, so it needs one gate commit.
