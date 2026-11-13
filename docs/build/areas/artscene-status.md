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

## Round log, skyline (Nov 12 evening, new generator `Art/Source/Scene/build_skyline.py`; `build_scene.py` keeps paper only)
Technique change: the town is built from an architecture kit (gable and hip houses, dormers, chimneys, cresting, clock tower, cathedral with rose
window and flying buttresses, domed hall, conservatory, viaducts) as flat meshes, one mesh per ink class. Blender renders the classes as colour
channels (4 emission passes per layer); a numpy finish inside Blender turns class weights into ink: near-black walls, tiled roofs, muted amber
glass, etched frames, eave shadow, window bounce, rim light, torn rock edge. Render 8 s. Panel runner re-judges refused sessions only (format slip
or calibration miss; the tool says "judge again"), never a counted one.
- r7-r10 (old generator, commits only): panel rounds logged in art-loop.jsonl, reference pair lost every time. Abandoned.
- r12: checks PASS (art_ref 0.766). Tile 0/3, key art 0/3, bar 3/3. Gap, all critics: soft, smudged, muddy brown, weak black-to-amber contrast.
- r13 (crisp edges, darker ink): checks PASS. Tile 0/3 (gappy, bare arcades, thin etched detail), key art 1/3, bar 3/3.
- r14 (rock shelf, lit wall faces, richer viaducts, denser rows): checks PASS 0.776. Ours picked in tile 3/3, key art 2/3, bar 3/3, but only 5/9
  sessions counted (3 format slips "A: SAME" without "WINNER:", 1 calibration miss).
- r15 (torn rock edge): 9/9 counted. Tile 2/3 (loss: wavy rock band with little structure), key art 1/3 (flat cream ground, muddy rock band), bar 3/3.
- r16 (key-art style buttes with lit facets, lights clustered per house): checks PASS 0.771. Key art 3/3 ours, bar 3/3 ours, tile 2 counted wins
  and one session refused three times. Not a pass: one tile "win" has a gap text that describes the tile as the better image (the critic swapped
  X and Y in its wording), so I do not count it. Gap from that text: tile has finer etched detail and fuller lit windows; our rock band muddier.
- r17 (bigger front houses and windows, more lit windows, tighter line, cleaner rock): rendering.
- Still missing for any pass: the context pair (in-engine capture with the piece, against the key art). It needs the piece imported and on screen in a
  smoke capture; the arena/flow lanes own that. See docs/build/requests/artscene.md.

## Critic sanity (skyline)
- Passes the reference itself: not run as its own test; calibration folders (crude vs team image, crude vs shifted copy) pass 8-9 of 9 per round.
- Defect 1, packet: a transparent layer is flattened on a flat cream fill. In r12-r15 six key-art sessions named "flat cream ground, no paper grain"
  as the gap. That is the paper piece, not the skyline. Request filed (same textured ground for both sides); not worked around in the art.
- Defect 2, format: Sonnet critics often write "A: SAME | GAP" instead of "A: WINNER: SAME"; the tool refuses the session. Re-judged in a fresh session.
- Defect 3, one r16 session picked a letter that contradicts its own gap text. Treated as a loss.

## Gemini rollout (Nov 12-13): blocked on the key
- Merged main. Skyline prompt written (Art/Source/Scene/Paint/prompt.md), reviewed by a fresh Sonnet session (prompt-review.md), corrected prompt in
  Art/Source/Scene/Paint/skyline_r1.txt (466 words; 4:1, 2K, text only, green key, 1/8-height ground band, spire 70%, lit windows 1 in 6-7).
- `assetgen.py image` stops: NO KEY, GEMINI_API_KEY is not set in this shell and worker rules forbid me to read ~/.umbrella-ella.env. Zero spend.
- Next once a key reaches this shell: run the call in skyline_r1.txt, key green, resize to 3200x720, art_check/art_ref_check, blind panel; then paper and menu-screen the same way.

## Nov 13: context capture blocked (merged main ad9d6d1d)
- Followed the lead's recipe; step 1 has no target. The backdrop draws untextured cubes and no skyline/paper `_PH` texture exists, so no shot can show
  the piece. Not faking a capture. Request 3 in requests/artscene.md has the ask. Skyline r2 (Gemini) stays unshipped; `_PH` stays.
- Panel r2: pairs run but the context pair stays missing for the same reason. Cannot pass skyline, paper or menu-screen until a slot exists.
- Also committed the provenance rows for skyline r1/r2 raw images.

## Nov 13: r2 (Gemini) panel re-judged ("judge again")
- Round 14, skyline_r2_keyed.png: checks PASS (art_ref 0.781), calibration 8/9. Reference pair and quality-bar pair: reference still wins.
  Gap: lit grey-green bodies instead of near-black silhouettes; tidy regular roofline. Context pair still missing (no backdrop texture slot).
- area/artslots has no slot commit yet (only "merge artinventory"). Waiting; then merge it, import skyline_r2_keyed.png with its script, make the shot.
- Next paint: darker value structure (near-black walls, amber only in windows), ragged roofline. Needs GEMINI_API_KEY in this shell.

## Nov 13: r2 panel re-run through the tool
- Earlier "round 14" record was a hand-typed entry; the tool-written record replaces it as evidence. Re-ran skyline_r2_keyed.png: tool logged round 15 in
  pipeline/art/critic/skyline.json (calibration 7/9, checks pass 0.781, verdict reference, two pairs short of 3 calibrated sessions, context pair missing).
  Not a pass. Waiting on area/artslots backdrop slot for the context shot.

## Nov 13: paper (Gemini, key loaded in the generating shell only)
- Prompt paper_r1.txt reviewed by a fresh session (paper-review.md), applied. r1: art_ref 0.807, screen/art checks pass. Panel (tool-written record, round 1, calibration 4/6):
  quality-bar pair ours, reference pair (star-paper tile) reference. Gap: crisp vector lines and plain white dots sit on top, flat digital weave. Context pair missing.
- r2 (prompt paper_r2.txt, hand-etched lines, soft ivory dots): art_ref 0.813 but the model painted a photographed sheet with a deckled edge, lines only at the
  borders. Ours: prompt invited "sheet"/"pressed into paper". Not panelled. Next: r3 prompt without "sheet"/"etching paper", wind lines inside the frame.
- Spend so far $7.746 of $33.82 (shared counter). Still waiting on area/artslots for the context shot; nothing ships.

## Nov 13: paper r3 (Gemini, prompt paper_r3.txt)
- Wind lines now inside the frame, soft ivory dots, no deckled edge (r2 fault was ours: prompt said "sheet"). art_ref 0.871, screen_check and art_check PASS.
- Panel (tool-written round 2): calibration 3/6, quality-bar pair ours, reference pair reference-leaning but 0/3 calibrated sessions; "judge again". Context pair missing.
- Merged main and area/artslots again: still no backdrop texture slot (grep Source for T_*_PH finds nothing). Request 3 stands; it is the only thing
  stopping a pass for skyline, paper and menu-screen. No more paid calls until the slot exists (spend is wasted without the context pair). Nothing ships; `_PH` stays.

## Nov 13: re-check after merging main (e817898a) and area/artslots (ab25ac21)
- Backdrop still draws untextured cubes (UmbrellaBackdropSubsystem.cpp:87); no T_*_PH slot exists. Skyline r2 and paper r3 cannot get a context pair.
- menu-screen: on main it has no `ui` block, so it needs a context capture too. area/artui adds ui-title/ui-pause/... elements and paints those screens
  (ground r1, ui-title round 4: reference still wins). menu-screen overlaps that lane; I am not painting it in parallel (shared spend, double work).
- Zero spend this round. Blocker for the lead, in requests/artscene.md item 3: give the backdrop a texture slot (or merge artui's `ui` elements and
  retire menu-screen). Nothing ships; every `_PH` stays. Stopping here until the slot lands.

## Nov 13: candidates moved (lead rule "Where candidates live")
- All Gemini raws, keyed cuts and round candidates moved to `pipeline/art/proof/scene/{skyline,paper}/`; `Art/Source/Scene/Paint/out/` is gone. Provenance, critic records and requests/artscene.md paths updated.
- quality_gate: sprite_check, art_inventory, art_pass_verify, art all PASS. Remaining FAILs (gdd_check, pipeline_check agent_play.py path, audio_scan) are other lanes. Still blocked on request 3 (backdrop texture slot).

## Nov 12 23:05: capture retry, still blocked (ours: none; machine)
- Merged main (2ccbebdb) and artslots. T_Skyline_PH imported locally; run_game.sh -SmokeShot ran 10 min without finishing; load average 33 -> 151
  (other lanes' captures and builds). `Flow.SmokeShotDelaySeconds` (5 s wall clock, tuning only, no command-line flag) fires before the first backdrop frame.
- Needs the lead: a `-SmokeShotDelay=` flag in SmokeHookSubsystem.cpp (not my lane) or an idle machine window. No piece can pass the context pair. Every `_PH` stays; zero spend.

## Nov 13 (re-check, main 4829fa66): still blocked, zero spend
- Merged main: nothing new for the capture. No `-SmokeShotDelay` flag in SmokeHookSubsystem; load average 49. Context pair for skyline, paper, menu-screen still impossible from this lane.
- Uncommitted and left alone: `tools/build/art_inventory.py` (scene-texture rule, outside my lane) and untracked `Content/UmbrellaElla/Art/Scene/T_Skyline_PH.uasset`. The lead decides on the inventory rule.
- Needs the lead (requests/artscene.md item 3 update): shot waits for first rendered frames or `-SmokeShotDelay=`. Every `_PH` stays.

## Nov 13 02:50: still blocked, zero spend
Merged main 4c3dea15. Capture with an ini override of the shot delay never got an engine slot in 10 min (killed). Details in requests/artscene.md item 3. Every `_PH` stays.
