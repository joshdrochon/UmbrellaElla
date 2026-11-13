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

## Slice 3 (Nov 13): request 1 done, calibration measured
- Off-band now measured on source pixels, ink (L* <= 35) ignored; test `tests/test_art_judge_ink.py` (crisp ink-lined crimson passes, flood-filled teal fails). Calibrated all 26 vfx-* elements (D-new-vfx-calibration): refs pass their own element (1.0), crushed copies fail (0.2). One-image elements keep their inherited score_min.
- Re-judge clock-beat (min now 0.945): sheet3 0.2 (offband gate still fires, 0.02 before), sheet4 0.553, sheet5 0.612. The gap is now the work (shape/edge/value vs the refs), not the check.
- Open for the lead: the measured mins are 0.93-0.97 because the refs are near-identical to each other; that is a near-clone bar for new paint. If it is too tight, that is a bar decision, not mine.
- Left: repaint toward the ref silhouette and value, then the other 7 pieces. `pipeline_check` shows 2 problems from main (a missing agent play tool), not this lane.

## Slice 4 (Nov 13): blocked, calibration bar measures sheet layout
- Triage: check defect. vfx refs are whole opaque concept sheets (mask 1.0, aspect 1.34-1.49); calibrated min 0.945 is a layout match no sprite can reach. Crops of the shot score each other 0.53-0.73; clock-beat sheet5 scores 0.52-0.55 against them. Details and the exact fix: `docs/build/requests/artfx2.md` request 2.
- No paint, no spend (spend would be wasted against an unreachable bar). All 8 pieces wait for the lead to add shot crops to the vfx elements' refs and recalibrate.

## Slice 5 (Nov 13): still blocked on request 2
- Merged main (up to date, 074881e9). `references.json` on main and on artfx/artfx3/artslots still has vfx-clock-beat score_min 0.945 from whole-sheet refs; request 2 not applied. No paint, no spend.
- Left: all 8 pieces, after the lead applies request 2 (shot crops in refs, recalibrate).

## Slice 6 (Nov 13): request 2 applied, clock-beat passes the element judge, panel waits on the capture
- Merged main (crop refs and recalibration are in). `art_judge element vfx-clock-beat`: sheet3 0.2 (fail), sheet4 0.556 PASS, sheet5 0.605 PASS (min 0.546). The bar is now reachable.
- Panel round 1 on sheet4 (`pipeline/art/proof/artfx2/ClockBeat/panel1/`): 12 blind sessions prepared, stopped at "cannot judge yet: context (no in-engine capture)". Critics not run.
- Context capture not made: `import_art_candidate.py sheet5.png vfx-sheet:VFX_ClockBeat` ran 10+ min with no output (the shared Unreal slot lock was held by other workers) and was killed at the background limit. Nothing was imported; no spend this slice.
- Left: retry the import when the slot is free, capture with run_game.sh in a section where the clock beat plays, run the panel with sheet5, then the other 7 pieces with the same method (clock-beat cut script and prompt are reusable).

## Slice 7 (Nov 13): merged main, keeper-warning first draft, not passed
- Merged main (conflict in tools/assetgen.py: kept the video command; main dropped it). artslots already merged.
- Order: art-priority puts vfx-keeper-warning (18) and keeper-strike (19) above clock-beat (47), so I started keeper-warning.
- vfx-keeper-warning draft 1 (flash, $0.039, 21:9 strip, 4:1 is not offered on flash): `pipeline/art/proof/artfx2/KeeperWarning/` (prompt.txt, strip, sheet). Cut with cut_strip.py (Blender needs absolute paths).
  `art_judge element`: 0.462 vs min 0.699, closest "bar-casters". Gap: the refs (tell-ring, firing-tell crops) are soft red rings with a thin ray and an arrow; mine is a hard graphic crosshair with ink outline. Next paint: softer glowing ring plus one ray, no crosshair, no spikes.
- Clock-beat context import (sheet5 -> VFX_ClockBeat_PH) is running in the background (`../logs/artfx2-import.log`); it got an engine slot this time. Capture and panel still to do after it lands.
- Spend counter: 28.99 of 33.82. Only about 4.8 left for every lane, so paint per piece stays at one draft per round until the lead says more.
- Left: keeper-warning v2; keeper-strike; clock-beat panel after capture; clock-open, eye-exposed, recovery, departure, restoration.

## Slice 7b (Nov 13): keeper-warning draft 2
- Draft 2 (soft glowing ring + one ray, flash $0.039, `KeeperWarning/strip2.png`, `sheet2.png`): art_judge 0.568 vs min 0.699, closest is the tell-ring crop (draft 1 0.462). Better, not passed; look is glossy (no ink, no grain), so the blind critic will likely fail it.
- Clock-beat import: the editor run exited with no import and no error; `T_VFX_ClockBeat_PH.uasset` unchanged. Cause not found yet; no capture, so no panel.
- Spend 29.16 of 33.82.

## Slice 8 (Nov 13): keeper-warning draft 3, flat, stopping
- Merged main. Draft 3 (flash $0.039, grain/matte prompt `KeeperWarning/prompt.v3.txt`, sheet3): art_judge 0.515 vs min 0.699, closest bar-casters. Drafts 0.462 / 0.568 / 0.515: flat, no pass, flash does not reach the crop refs' look.
- Spend 29.29 of 33.82 (shared). Remaining about 4.5 for all lanes, so no more drafts from this lane. Pro finals need a passing draft first (`--from-draft`).
- Panel still cannot run: no in-engine capture (clock-beat import exits with no output). All 8 pieces remain `_PH`, nothing shipped.
- Left for lead: (1) why `import_art_candidate.py` exits without importing; (2) more spend or a pro-tier try for keeper-warning/strike; (3) retry-with-Opus decision for this lane per repeat-failure rule (flat 3 rounds).
