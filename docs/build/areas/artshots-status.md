# artshots status (worker, 12 Nov)

Nothing ships yet. Every piece is still a tracked `_PH` (no `.artloop.json`, no provenance row, no import script).

## What exists
- `tools/build/assets/art_shots.py <piece> --scale N --out-dir Art/Source/<Asset>/Raw/StillN` renders a piece through
  Blender with the shared planner (look, palette). `art_shots_blender.py` holds my builders (shared `stand_ins.py` untouched):
  `shot_red`, `shot_gold`, `burst_red`, `wind_lines`, `wind_zone`; palette-exact graded layers, per-pixel grain,
  engraved hatch, geometry ink outline (Freestyle off: its AA edges blow `off_style`).
- Renders: `Art/Source/{OwlBolt,WandShot,BoltHit,WindLines,WindZone}/Raw/Still*/`.

## Deterministic checks (art_check sprite rules, screen_check, art_ref_check)
| piece | result | note |
|---|---|---|
| owl-bolt | PASS (score 0.744 / min 0.729, off_style 0.019) | 4x render (640x320); at 1x the AA edges fail off_style |
| wand-shot | PASS (0.698 / 0.334) | same builder, gold family |
| bolt-hit | FAIL | detail 0.32 < detail_min 0.362 (score capped to 0.2); lifting detail with grain/ink lines pushes off_style past 0.02 |
| wind-lines | FAIL | art_check passes; ref score 0.2 (detail 0.24 < 0.408) |
| wind-zone | FAIL | art_check passes; detail 0.09 < detail_min 0.421 |

## Blind panel (owl-bolt, rounds 1 to 5, `art_loop.py panel`, 12 Sonnet critics per round)
Round 1 rust-cross placeholder look; 2 pixel blob; 3 to 5 palette-exact vector with hatch and grain. Calibration 10 to 11/12.
Verdict each round: reference still wins in most sessions. Same gap every round: "flat vector fills, no etched line or paper
texture, serrated head not one sharp point, tail too long / loose squares". Progress: critics stopped calling it a blob and
started picking ours over the old rust needle. Not yet unanimous ours/SAME, so no pass.

## Blockers
1. `context` pair: the panel needs an in-engine capture made after the piece (import, then smoke screenshot). No piece can
   pass without it; that needs the build lead's package/smoke. Import script not written until a piece clears the other pairs.
2. Calibration (for the lead, not loosened): wind-zone `detail_min` 0.421 is above its only reference's own detail (0.099), and
   wind-lines/wind-zone `score_min` are "not measurable" defaults (0.582) that a stroke sprite cannot reach by shape alone.
   Suggest re-measuring those two elements. Critic itself looks sane (rust needle is picked against, calibration 10/12).

## Next
owl-bolt: single sharper head (one point, not stacked teeth), shorter tail, visible etched interior line work; re-run panel.
Then bolt-hit detail, then wind pieces once their calibration is fixed.
