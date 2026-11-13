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
