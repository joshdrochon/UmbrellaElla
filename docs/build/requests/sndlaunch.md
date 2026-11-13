# Requests from area/sndlaunch

## 1. Audio critic packet: three defects (tools/, not my lane). Verdict of the triage: check defect.
Piece: KeeperYellowLaunch (owl_attack, one-shot). 9 official rounds, all `style=PASS`, all critic fail. The gap moved
between "add a wind-down", "remove the spike", "add a 0.5-1 s travel whirr", and rows A1/A7/A8 failed with
"cannot confirm without listening". Evidence (Saved/AudioLoop/SNDLAUNCH/KeeperYellowLaunch/round-1..9, state.json):

a. `tools/audio_style_check.py spectrogram_png`: one 1024-sample FFT (47 Hz bins) for every row. Rows under about
   500 Hz hold 1 or 2 bins, so a reverb tail draws random column stripes there. The critic reads the stripes as
   "evenly spaced gear ticks" (rounds 4, 5, 6, 8, 9) and fails A5 because "the ticks never slow". The same stripes are
   in the approved references. Test: same WAV drawn with a 4096 window below 500 Hz has no stripes.
   Change: in `spectrogram_png`, compute a second grid with `size = 4096` and use it for rows whose lower edge is
   under 500 Hz; centre each window on its column; start bins at 1 (row 0 reads the DC bin today).
b. `tools/audio_loop.py` brief (`family_text`): the family text describes three sounds (launch, travel loop, fade)
   and the brief never says which one the piece is. The critic asks for all three inside a launch one-shot.
   Change: add one line from sound-list.csv to the brief, no id: `This piece: <kind> that plays when <event>. Other
   sounds named in the family text are separate files.`
c. `tools/audio_critic_prompt.md`: rows fail with "cannot confirm from spectrograms". Josh's call, because it touches
   the bar: say what a row is when the critic cannot hear (my lean: false only when the picture or a number shows
   the fault; the measured ranges stay final).

Triage run (not recorded as a verdict): round-8 takes, packet redrawn per (a), brief line per (b), same prompt and
model. Result: fail, but every row judged, no "cannot confirm", and one concrete gap ("spring snap, then 1-3 heavy
clanks within 50-150 ms"). Round 9 was built to that gap; the official packet then asked for the opposite (a 0.5-1 s
whirr and a wind-down). So the official verdicts on owl_attack and enemy one-shots are not usable until (a) and (b)
land. No owl_attack one-shot has passed the gate-model critic on any branch (OwlBoltLaunch is a placeholder too).

## 2. regen.py: recipes outside the audio area build folder
My lane has no script folder, so my recipes are `Audio/Source/<Id>/recipe.json` and I run the audio area's regen.py
unforked from `area/audio` with a wrapper (in sndlaunch-status.md). Ask: `regen.py --recipe <json> --root <dir>` and
`provenance.py` the same, plus sorted insert. Also: an empty layer (silenceremove ate a quiet candidate) truncates
the whole take; regen should fail that candidate.

## 3. arena_audio_import.py imports a fixed cue table into /Game/UmbrellaElla/Audio
It cannot import my ids into Content/UmbrellaElla/Audio/<Id>/. Ask: take `--ids` and import every take to
`/Game/UmbrellaElla/Audio/<Id>/SW_<Id>_<NN>`.
