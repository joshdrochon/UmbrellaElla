# sndui status (area/sndui, UI sounds)

## Done: all 29 sounds pass (Nov 12 2026)
Each has one take `Audio/Source/<Id>/SW_<Id>_00.wav` and its recipe `Audio/Source/<Id>/recipe.json`.
Passed on the same bytes: blind critic (audio-critic/2, `claude -p`, Opus 5.5, packet folder only, one loop card
`SNDUI-<Id>` per piece), `audio_style_check.py check Audio/Source` (PASS files=54) and `audio_check.py --scan Audio/Source`
(no error on any sndui file; the 54 errors left are other lanes' P0 sounds with no file yet).

| tier | sounds | critic rounds |
|---|---|---|
| P0 | UiMove, UiSelect, UiBack, PauseIn, PauseOut, UiOpen, UiClose, UiTransition | 1 |
| P0 | UiSliderTick | 2 (round 1: tail cut at the file end; shorter decay, 0.2 s file) |
| P1 | SpellSelect, SpellUnavailable, SettingsSaved, BindingCaptured, BindingConflict, TutorialPrompt, TutorialStep, TutorialDone, TutorialSkip, XpGain, WeaponUnlock, UpgradePurchase, UpgradeRefund, RunStart, RunComplete | 1 |
| P1 | UiBlocked | 2 (round 1: too dark; band raised, gear click added) |
| P2 | StoryTextAppear, StoryPageReveal, SceneTransition | 1 |
| P2 | StoryAdvance | 2 (round 1: splice in the middle; rebuilt as one page gesture) |

## How they are built
Layered mixes with the audio lane's `pipeline/audio/build/regen.py` (unchanged): ElevenLabs layers (clock tick and tock,
gear click, latch, page turn, paper flick, wind breath) plus ffmpeg music-box notes (additive partials, as WandBolt and
LevelUpClock). Small room convolution reverb. Each sound has its own shape so none is mistaken for another:
move = one tick; select = one note (A6); back = tick then lower tock; pause in = ticks slowing into a muffled stop;
pause out = catch then ticks opening up; open/close = page turn (close ends on a cover thump); slider = one gear click;
transition = page turn with wind; blocked = double knock; saved = rising fifth; conflict = clashing dyad;
tutorial done / run complete = fast four-note runs; refund = unwinding clicks with a falling pair; and so on (recipes).
Level: every take is matched to active RMS -22.6 dB (± 0.6) so the `ui` family RMS rule (± 3 dB of the median) holds with
LevelUpClock (-20.3), FailSting (-21.7) and SurvivedSting (-22.4) in the same family.
Rebuild and critic commands: `docs/build/requests/sndui.md`.

## Limits of the evidence
- The critic judges spectrograms and numbers; nobody has listened to these takes.
- Critic sanity (one test): a noise-only UiSelect (band noise with a bell envelope) failed, on A6/A7 (noise floor, no
  clean partials) and on LUFS (-36.4, so the numbers failed too). The packet gives the critic the family target, not the
  single sound's event, so it cannot tell a good tick from a good bell in the wrong slot. 26 of 29 passed in round 1.
- The family ranges (attack <= 15 ms, decay_s <= 1.0) force every UI sound to open on its loudest transient and fall
  30 dB in 0.5 s. RunComplete, TutorialDone and WeaponUnlock are therefore short music-box runs (0.85 to 1.0 s), not long chimes.

## Requests (docs/build/requests/sndui.md)
recipes.py to load `Audio/Source/*/recipe.json`; regen.py trims before the lead-silence cut; home for the import script.

## Unreal assets (Nov 12 2026)
`docs/build/requests/sndui_audio_import.py` (editor exit 0) made, per sound, `Content/UmbrellaElla/Audio/<Id>/SW_<Id>_00`
and the cue `SC_<Id>` (one wave player; class SCL_UI, concurrency SCON_UI, 2D). 58 assets.
Evidence: commit=ddde118 engine=5.8.4 config=Development host=mac; build `build exit: 0 warnings: 0`;
`tools/ue/audio_dump.py` then `audio_check.py --ue-dump Saved/AudioDump.json`: no error on any sndui asset (the 8 errors
left are the old arena cue names Shot, Hit, ...). The cue is needed because the dump reports concurrency and 2D only for
cues, and the check wants them on whatever plays the sound.
Not done: nothing in game code plays these cues yet (not this lane). Not run: automation tests (no C++ changed), package, smoke.
Known warning: `SoundNodeWavePlayer.sound_wave` is deprecated in 5.8 (renamed `sound_wave_asset_ptr`); the import still works.
