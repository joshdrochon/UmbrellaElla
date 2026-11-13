# sndlaunch status (area/sndlaunch)

## How takes are built here
Recipes: `Audio/Source/<Id>/recipe.json` (same fields as the audio area's recipes). The audio area's helpers
(regen.py, critic.sh on branch `area/audio`) run unforked through a small wrapper kept outside the repo; it does
`git show area/audio:<helper>`, sets the root to this worktree and feeds it the recipe.json files. Request 2 in
docs/build/requests/sndlaunch.md asks for a `--recipe` flag so the wrapper can go.
Provenance: one row per take, inserted sorted among the Audio/ rows.
The spin-down ratchet layer is generated maths (tick rate 60/s falling exponentially, uneven gaps), written into the
recipe as an ffmpeg expression.

## Pieces
| Id | tier | audio_check --scan | audio_style_check | critic | provenance origin |
|---|---|---|---|---|---|
| KeeperYellowLaunch | P0 | pass (3 takes) | PASS | fail x9 | placeholder |

## Critic triage (Nov 12): check defect, not closed
KeeperYellowLaunch: 9 rounds, every round `style=PASS`, critic fail each time; the gap changed between rounds and rows
failed with "cannot confirm without listening". Triage, evidence and the exact changes asked for are in
docs/build/requests/sndlaunch.md section 1. Short form: the packet picture draws column stripes under 500 Hz that the
critic reads as even gear ticks, and the brief does not say the piece is the launch one-shot, so the critic asks for
launch + travel + fade in one file. A redrawn packet with the event named got a judged, concrete verdict (still fail,
one gap); the official packet then asked for the opposite. Bar not loosened; nothing in tools/ changed by me.

## Nov 12 late: takes for all 16 ids on disk
All 16 ids have 1 to 3 takes in Audio/Source/<Id>/ with recipe.json, provenance rows (origin `placeholder: audio critic fail
(critic not yet run)`), `audio_style_check` PASS and `audio_check --scan` clean for these ids (FloodShot, RearCastLaunch,
WardenShot got a 30 ms end fade for the end-click check; the cached-layer regen needs the key shell, not run).
Critic ran for ClockBeatRepeat, GustRelease, NeedleFire, StreamLoop/Release/Start, TwinStarsFire (packets in Saved/AudioLoop/SNDLAUNCH);
not recorded as passes here. Not done: critic for the rest, Unreal import (request 3). Blocked on: request 1 for owl_attack/enemy ids.

## Left
The other 15 ids; Unreal import (request 3: the import script has a fixed cue table).
