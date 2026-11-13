# artfx2 status

## Slice 1 (Nov 13): clock-beat, 5 paints, not passed
- Merged origin/area/artfx and main. The three check defects of artfx request 5 are fixed on main (art_check --effect, calibration redraw, effect context crop), so this lane is no longer blocked by them.
- Card for `art_loop.py` is `artfx` (it lists the pieces' refs); `artfx2` has no references. Judge reads the first frame only and needs a `.sprite.json` sidecar (`{"frame_w":128,"frame_h":128}`) next to the sheet.
- vfx-clock-beat: paints in `pipeline/art/proof/artfx2/ClockBeat/` (prompt.txt, v2, v3; strips, sheets). Spend 11.03 -> 13.28 of 33.82 (1 flash draft, 3 pro). Cut script with tight key and palette snap: `pipeline/art/proof/artfx2/cut_strip.py` (env PALETTE, SNAP_T, DARK_L).
- Findings (each measured):
  - Palette: use the GDD shot colours (crimson FF3658, coral FF7848, shadow 8F173C, cream FFF5DC), not a rust red. Snapping to the effect ramp makes `art_check --effect` PASS (sheet4/sheet5).
  - Critic gaps, all rounds: no etched ink line, no paper grain, glossy. v3 prompt (ink outlines, hatching, grain, bolt-shaped frame 1) fixed the look by eye.
  - `art_ref_check` caps the score at 0.2 when the first frame's off-band share is over 0.05. Reference shots score 0.0; my v3 sheet 0.07 (ink next to crimson averages to a muddy dark red in the judge's 24x24 downscale); v2 (soft glow, sheet3) 0.02 offband and score 0.593 but fails art_check colour rules. min is 0.729, inherited from owl-bolt, not measured for this piece.
  - Verdict: work, in tension with the judge: a crisp ink outline conflicts with the offband gate, a soft glow conflicts with the critic's "no ink line". Not loosened.
- No panel pass for any piece; nothing shipped, `_PH` slots untouched.
- Left: find a frame-1 shape that keeps ink hatching but with red-only edge (ink outline in coral/crimson rim), re-run the panel; then the other 7 pieces (keeper-recovery, keeper-strike, keeper-warning, clock-open, eye-exposed, departure, restoration) with the same method. Ask the lead to calibrate score_min/detail_min for the vfx pieces (art_judge calibrate) since 0.729 is inherited from owl-bolt.

## Slice 2 (Nov 13): blocked on judge calibration
- Merged main and artslots (clean). Re-judged clock-beat sheets 3-5: 0.593 / 0.2 / 0.2 vs min 0.729, same as slice 1. No new paint, no spend.
- Verdict: check defect (uncalibrated inherited min; offband counts ink-dark pixels). Request in `docs/build/requests/artfx2.md`.
- Left: all 8 pieces, after the lead calibrates the vfx elements.
