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

## Left
The other 15 ids; Unreal import (request 3: the import script has a fixed cue table).
