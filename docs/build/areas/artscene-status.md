# artscene status

Nothing ships. No piece has passed the blind panel, so every `_PH` stays and no `Art/Scene` image, provenance row or import script was added.

## Built (Art/Source/Scene/build_scene.py, Blender 5.2.1, `-- --piece paper|skyline --out <png>`)
- paper: 3200x1080 stained/fibrous sepia field, etched wind bands, sparkle rings. Not panel-judged yet.
  art_ref_check (card MVP 15, element paper): PASS 0.876 (min 0.5). Tile edges not seamless.
- skyline: 3200x720 gothic skyline, two layers, brick/hatch ink, gold pointed windows, Freestyle edge lines.
  art_ref_check: PASS 0.718 (min 0.527). screen_check PASS. art_check sprite colour rules: FAIL off_style 0.032 > 0.02 on round 1 (gold windows; gold was desaturated for round 2, not re-measured).
- scene, menu-screen: not started.

## Panel
- skyline round 1 (3 critics x ref, ref, quality bar): verdict=reference/quality_bar win. Gap, every critic: flat clean vector fills, no paper grain, etched line work or ink variation.
  Context pair not judged: needs an in-engine capture from the smoke.
- Round 2 added brick/hatch texture and Freestyle edges; the render still reads as clip-art. Not sent to the panel.
- Critic sanity: reasons agree across sessions and match the references; no defect suspected. Calibration was 6/9.

## Blocked / needs a decision
Procedural Blender geometry does not reach the painted/etched look of the key art, the gothic tile or the Other Realm bar. More rounds of the same approach are unlikely to pass. Options: (a) keep `_PH` for these four and ship the game with placeholders (my lean); (b) hand-sculpted/painted-in-Blender detail (grease pencil or displaced meshes with heavy texturing), many hours; (c) allow another image source for these four, which the current rule (Blender only) forbids.

## Round log, skyline (Nov 12, technique change per lead: post-etch pass, measured against the critic's named gap)
- r3 (commit "round 3"): `etch_post` in build_scene.py (numpy inside Blender): hand-jitter displacement of edges, ink-bleed ragged alpha,
  ink tone variation + fibre streaks + grain, diagonal hatching, warm rim light on roof edges, window halo. Denser blocks (24-52 px).
  art_ref_check skyline 0.719 (r2 0.718, min 0.527). screen_check PASS with `--aspect 4.444` (strip layer, not a 16:9 frame).
- r3b: roof-tile courses and stone-course line detail (lighter ink strands). art_ref_check 0.720.
- Panel r3b (9 critics, ours on transparent -> shown on black): 3 of 9 reference/bar pairs ours-or-SAME, rest lose; recurring gaps: flat fills,
  no etched line, no paper grain. Several critics called ours "thin wobbly outline on pure black".
- Critic-packet defect found: a transparent PNG is shown over black, so the ink mass vanishes and only the outline reads. The reference tile is on
  white. Fix: judge ours composited over a plain ground. My first fix attempt composited on brown by mistake (bad sed), so panel r3c is invalid
  as evidence (ours on brown, critics: "flat brown backdrop"). Next: composite on white, rerun once.
- Still not tried: Grease Pencil Line Art pass, much denser architecture (reference has ~5x the window/roof/ironwork count), painted-light pass,
  paper, scene, menu-screen. Nothing ships; `_PH` stays.

## Round log, skyline (after artfix merged: packet images flattened onto one paper ground; earlier panel rounds r3b/r3c are invalid)
- r4 panel (render = r3b look, flattened): calibration 7/9, quality_bar pair ours, reference pair reference. Gap: flat, no etched line.
- r5 (dense gabled houses, dormers, muntins, tall ground band): panel calibration 9/9, quality_bar ours/same, reference loses ours. art_check off_style 0.044 FAIL (window gold too saturated).
  Gap: fuzzy edges, blobby windows, no etched detail inside the mass.
- r6 (cleaner edges, palette gold #e9c46a-ish, etched strands survive the ink pass, stone courses): calibration 9/9, checks all PASS (art_ref 0.749),
  quality_bar pair ours, reference pair still reference. Gap: repetitive same-height gabled houses, uniform window grids, flat ground band, no clock/domes/arches.
- Next r7: architectural variety (clock tower, flying buttresses, wide manors, irregular window patterns, conservatory dome), ground-band tone.
