# sndworld status (area/sndworld)

## Done (blind critic pass on the gate's model + audio_check --scan + audio_style_check on the same files)
| id | tier | file | numbers |
|---|---|---|---|
| WindZoneLoop | P0 | SW_WindZoneLoop_00.wav, 6.4 s stereo loop | centroid 1054 Hz, crest 15.4, lufs -24.1, rms -27.0, wrap 0.015 |
| GustLoop | P0 | SW_GustLoop_00.wav, 12 s stereo loop | centroid 334 Hz, crest 14.9, lufs -24.2, rms -25.5, wrap 0.000 |

## How they are built
`pipeline/audio/build/sndworld_build.py <Id>` with recipes in `sndworld_recipes.py` (new files; regen.py, recipes.py and
provenance.py are reused unedited). ElevenLabs layers, each made exactly loop-periodic (bed: tail crossfaded into head;
grid layer: hits rendered over two cycles), convolution reverb over three cycles with the middle kept, one static gain,
no fades, no loudnorm. `sndworld_build.py prov <Id> generated|placeholder "<gap>"` writes the one provenance row in place.

## Check defect found and fixed (triage, worker-rules "Repeat failures")
Round 1: the critic failed both loops only on attack_ms and decay_s ("range failure is final"). Those are one-shot
measures: `audio_style_check.applies()` never applies them to a loop, and the style check passed. The packet
(`tools/audio_loop.py`) printed every family range and every number whatever the sound's kind, and never told the critic
the sound is a loop. Verdict: check defect: packet lists ranges the measured check does not apply.
Fix: the packet lists only the ranges and numbers that apply to the kind (same `applies()` rule), and says a loop has no
onset or tail by design. Test: `tests/test_audio_loop.py::test_loop_packet_has_no_one_shot_ranges` (10 tests OK). The bar
is unchanged: no range was widened, the style check is untouched. Round 2 on the same bytes: both pass.
This edit is outside the lane (tools/); every loop in every sound lane needs it at the gate.

## Also done (commits fd01ede..161dd4c, each with blind critic pass + scan + style)
ClockTickLoop, AirMillLoop, RefugeLoop, WindBed, MillAmbience, BossApproach, RealmClocks, MusicIntro, MusicContest,
MusicDesperation. All 12 sounds have a passing take and a provenance row. Re-checked now: audio_check --scan and
audio_style_check show PASS for all 12 files.

## Left / blocked
Import into Content/UmbrellaElla/Audio/<Id>/: `pipeline/audio/build/sndworld_import.py` is written (own file, does not
touch arena_audio_import.py), but the headless run
(`ue_slot.sh UnrealEditor-Cmd <uproject> -run=pythonscript -script=... -unattended -nullrhi -nosplash -nocrashreports`)
exits 1 after shader autogen with no import log line and no assets written. Cause not found (config/plugin: the
PythonScriptPlugin may not be enabled in the .uproject, which is outside this lane). The build lead can run it, or
enable the plugin. Nothing in game code references these ids yet (the cue map is in the arena lane).
