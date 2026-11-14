# artscene status

Current state (Nov 13 evening): no piece has passed the blind panel. By lead order the `_PH` slots carry tracked, graded world art (not panel-passed);
see the latest entries at the bottom. Older entries below are history.

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
  paper, scene, menu-screen.

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
  the piece. Not faking a capture. Request 3 in requests/artscene.md has the ask. Skyline r2 (Gemini) not imported.
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
  stopping a pass for skyline, paper and menu-screen. No more paid calls until the slot exists (spend is wasted without the context pair).

## Nov 13: re-check after merging main (e817898a) and area/artslots (ab25ac21)
- Backdrop still draws untextured cubes (UmbrellaBackdropSubsystem.cpp:87); no T_*_PH slot exists. Skyline r2 and paper r3 cannot get a context pair.
- menu-screen: on main it has no `ui` block, so it needs a context capture too. area/artui adds ui-title/ui-pause/... elements and paints those screens
  (ground r1, ui-title round 4: reference still wins). menu-screen overlaps that lane; I am not painting it in parallel (shared spend, double work).
- Zero spend this round. Blocker for the lead, in requests/artscene.md item 3: give the backdrop a texture slot (or merge artui's `ui` elements and
  retire menu-screen). Stopping here until the slot lands.

## Nov 13: candidates moved (lead rule "Where candidates live")
- All Gemini raws, keyed cuts and round candidates moved to `pipeline/art/proof/scene/{skyline,paper}/`; `Art/Source/Scene/Paint/out/` is gone. Provenance, critic records and requests/artscene.md paths updated.
- quality_gate: sprite_check, art_inventory, art_pass_verify, art all PASS. Remaining FAILs (gdd_check, pipeline_check agent_play.py path, audio_scan) are other lanes. Still blocked on request 3 (backdrop texture slot).

## Nov 12 23:05: capture retry, still blocked (ours: none; machine)
- Merged main (2ccbebdb) and artslots. T_Skyline_PH imported locally; run_game.sh -SmokeShot ran 10 min without finishing; load average 33 -> 151
  (other lanes' captures and builds). `Flow.SmokeShotDelaySeconds` (5 s wall clock, tuning only, no command-line flag) fires before the first backdrop frame.
- Needs the lead: a `-SmokeShotDelay=` flag in SmokeHookSubsystem.cpp (not my lane) or an idle machine window. No piece can pass the context pair. (zero spend)

## Nov 13 (re-check, main 4829fa66): still blocked, zero spend
- Merged main: nothing new for the capture. No `-SmokeShotDelay` flag in SmokeHookSubsystem; load average 49. Context pair for skyline, paper, menu-screen still impossible from this lane.
- Uncommitted and left alone: `tools/build/art_inventory.py` (scene-texture rule, outside my lane) and untracked `Content/UmbrellaElla/Art/Scene/T_Skyline_PH.uasset`. The lead decides on the inventory rule.
- Needs the lead (requests/artscene.md item 3 update): shot waits for first rendered frames or `-SmokeShotDelay=`.

## Nov 13 02:50: still blocked, zero spend
Merged main 4c3dea15. Capture with an ini override of the shot delay never got an engine slot in 10 min (killed). Details in requests/artscene.md item 3.

## Nov 13 (main 4e1e6aff merged): still blocked, zero spend
No `-SmokeShotDelay=` flag yet, load average 45. Context pair for skyline, paper, menu-screen still needs a capture with the shot delay raised or an idle machine. Request 3 stands.

## Nov 13: skyline r3 repainted with the shared style block (main 3e2c0b2a merged)
- Prompt skyline_r3.txt (= r2 text; assetgen appends the style block). Gemini 3.1 flash draft, $0.101, shared spend now $29.88 of $33.82. Keyed with art_scene_key.py, 3200x720.
- Checks PASS (art_ref 0.802, screen_check, art_check). Panel round 16, calibration 7/9: reference and quality-bar pairs still reference.
  Gap: mid-tone brick and dome shading dilute the near-black silhouette; ground band is a flat black slab (no rock edge/texture); little rust/gold accent.
- Context pair still missing (no `-SmokeShotDelay=`, load average 66). Not passable either way. Paper and menu-screen not repainted: only about $3.9 of cap left,
  and without the context capture a repaint cannot pass. Next paint (if the lead wants it): darker flat silhouette, textured ground band, rust accent in the prompt.
- Tool defect (ours, tools/art_loop.py, not my lane): `panel` stores `ours` as an absolute path when --ours is absolute-resolved, then `verdict` refuses
  ("every folder of one panel judges the same file"). Worked around by hand-editing the temp panel.json to the relative path. Fix: store the relative path.

## Nov 13 (Opus, lead order): the study's world, round 1 (all tracked `_PH`, not panel-passed)
- Target: bar-other-realm as the whole frame. Prompts in Art/Source/Scene/Paint/world/ (fresh-session review applied: prompt-review.md).
  OpenRouter only: 7 flash drafts + 1 Pro (start-end r2) = $0.414. Post: tools/build/assets/art_scene_world.py (key off the sampled green,
  grade to study numbers, place in the panel rows the camera sees: 5%..50% of a 4800x2400 panel), art_scene_void.py (void tile, flecks),
  art_scene_import.py (one editor launch for many slots).
- Slots now: Sky=void tile; bg:atmosphere=flecks + clock-rim ridges (BG-05 order: clocks behind land); FarLand=distant island chain;
  bg:land=three islands + arch; Base=faint low haze (Base sits in front of FarLand/land, so it must stay see-through);
  NearArchitecture=barn + ring-wheel windmill island; bg:start-end (arena + route ends)=study-like void with the big island (Pro r2);
  world:solids=drippy island slab on every ledge; world:refuge=island with an umbrella-rib gazebo and a gold lantern.
- Emptied (transparent): bg:clocks (rims moved to atmosphere), ClockWaterWind, bg:water. The study has no clock face or water pipes; GDD BG-03
  still lists water and clock pieces, so these come back as faint layers if the lead wants them. Decision for the lead/Josh.
- Proof: pipeline/art/proof/artscene/world-r1-{arena,route-cp1,route-start}.png (study | before | after). LFS locks held on all T_Bg*/Paper/Skyline _PH.
- Gaps vs study: the floor is still a flat cream bar (Floor has no art slot: code, not my lane); wind zones and the refuge stand-in square
  are other lanes' visuals; islands from flash drafts have a slightly cartoon edge; ledges stretch one picture (8-15:1). Next: Pro passes for
  skyline/land/solids, a floor slot request, then visualqa's frame check once its visual_qa tool is on main.
- Pro passes (Nov 13): skyline r5 and bg-land r6 painted ($0.277) but not imported: land r6 cuts its big island at the canvas edge, skyline r5
  crowds both ends (seam when repeated). The flash versions stay. world-solids Pro refused by the draft guard (art_ref_check 0.485 < 0.527).
- Check triage (for the lead): `tools/art_check.py` FAILS the study itself (paper_texture 0.227 < 0.38, dark_share 0.80 > 0.45); it is tuned to
  the key art, so it cannot judge "match the Other Realm study". Verdict: check/target conflict, not loosened; visualqa's frame check should own it.
- near grade keeps 85% chroma (100% put the solids' rim at off_style 0.037 > 0.02; 85% measures 0.004).
- OpenRouter spend this session: $0.691 (10 calls). Pre-check PASS at c6ad170c.
- Nov 13 17:25, after merging main 570ca482: visualqa's BackdropDim (x0.055 on all backdrop art) turns the graded scene black (arena p50 luma 0,
  study 35). Request 5 in docs/build/requests/artscene.md; proof world-r1-after-dim.png. Also removed an old out-of-lane art_inventory.py
  edit from this branch (back to main's). Pre-check PASS at 001d90e7. Next once request 5 lands: recapture, then Pro passes where the
  frame shows the gap (route islands, refuge).

## Nov 13 17:45 (Opus, lead order): floating-island platforms r2 (tracked `_PH`, not panel-passed)
- Study read: flat dusty crust with a lit front lip and gold rim, top-lit; underside streams down in swept wax-like sheets breaking into specks.
  New prompts world-solids_r2/r3 (ledge) and world-solids-block_r1/r2 (block), fresh-session review applied (prompt-review-islands.md).
- Green ground made the model paint grass on the tops (keys out). Ours: green invites grass. Fix: magenta ground + magenta key in
  art_scene_world.py (ground hue sampled from the border; despill pink to brown).
- Ledge r3b imported to T_WorldSolids_PH: art_ref_check PASS 0.575 (min 0.527; r1 was FAIL 0.485). Block r2: PASS 0.571, waits for a slot
  (request 6: blocks/columns are 0.7-2.7:1, the 8:1 ledge picture squashes about 10x on them).
- In game: BackdropDim also darkens the ledges, so a fresh capture is near-black (Saved/Journey-r2). Judged on the pre-dim r1 frame and
  the keyed pieces on the study's void: pipeline/art/proof/artscene/islands-r2.png. Recapture once request 5 lands.
- OpenRouter spend this round: 5 flash drafts, $0.195 (world-solids $0.117 + 0.173 earlier, world-solids-block $0.078).
- Distant islands (FarLand) r6: few big islands at different depths with the study's swept sheets and speck spray (r4 was a regular row of
  same-size icons). Model drew a black frame (cropped off before keying); windmill is still a classic X-sail, not the ring wheel. art_ref_check
  PASS 0.563 (r4 0.553, min 0.527). Imported to T_Skyline_PH. Composite pipeline/art/proof/artscene/skyline-r6.png (study | pre-dim arena | piece on the void).
  Invisible in game until request 5 lands. $0.039.

## Nov 13 evening (Opus, lead restart after the Mac reboot): gate items from review-artscene
- (1) BG-03/05/06 kept by Josh's decision (docs/decisions.md D-new-study-vs-bg-layers, DECIDED Nov 13 Josh): T_BgClock_PH = two ash-blue dial
  ghosts with separate hands; T_BgWater_PH = two dim silver-grey falls cut into spill source / falling middle / pool / sea landing (masked parts);
  T_BgClockWaterWind_PH = faint wind ribbon (entry/straight/bend/exit) + small clock + thin fall. Built by tools/build/assets/art_scene_clockwater.py
  from 4 flash drafts (dial, hands, water, wind: $0.156). Every part is its own PNG next to the layer. Depth order: request 7 (visuals lane).
- (2) provenance rows added for bg-start-end/world_r2_post, world-solids/world_r3_post, skyline/skyline_r3_keyed, the artscene/*.png proofs and every new part.
- (3) BG-02: art_scene_world.py repeatN cross-fades the ends (TILE_FADE 0.12). Seam check tools/build/assets/art_scene_seam.py, test tests/test_art_scene_seam.py (8 PASS).
  Measured (join score vs the picture's own interior p90): skyline r6 0.840 vs 0.412 FAIL -> r7 0.091 vs 0.363 PASS (T_Skyline_PH);
  bg-clock rims r3 0.712 vs 0.420 FAIL -> r4 0.187 vs 0.419 PASS (in T_BgAtmosphere_PH).
- Whole-frame proof (visual_qa.py capture, 1280x720, real window): pipeline/art/proof/artscene/bg-layers-r1-{dc_route,play,keeper}.png = study | before (tip cc398b0f textures) | after.
  Route frame now shows two faint dial ghosts with hands above the land and a dim fall by the barn; play/keeper frames unchanged in look (layers sit outside their view).

## Nov 13 night (Opus, lead order): gate 3dfc4e2d visual_qa defects
- (3) keeper "wind as thick brown dripping bands": not the wind presenter (its ribbons are flat-colour planes, ArtSlot::SetFlatUnlit). The two
  wavy dripping clock-rim bands were painted into bg:start-end (world_r2_post). New tools/build/assets/art_scene_unband.py paints them out
  (per-column tone blend, grain, windmill ink kept, barn glow toned down) -> world_r2d_post.png -> T_BgStartEnd_PH.
- (1) dc_route dark rectangle: art_scene_world.py haze fade was inverted (full alpha on the TOP row: hard edge). Fixed (haze_envelope), alpha 0.45 -> 0.30,
  fades at both ends -> bg-base/world_r1b_post.png -> T_BgBase_PH.
- (2) dc_route grey blocks: the water falls' sea landing (side fade ran before the crop: square sides, cut bottom). art_scene_clockwater.py edge_fade
  after the crop + bottom fade; water/clock/cww alphas lowered -> T_BgWater_PH, T_BgClock_PH, T_BgClockWaterWind_PH (r1c).
- Gate runs (visual_qa.py run --gate --main-sha ebda6e47, through ue_slot), precheck PASS on each:
  - a2bc7f3d: FAIL play=42 dc_route=43 keeper=37 (bands/rectangle/grey blocks gone; new: unband step + crosshatch edge, dial ghosts, thin fall) -> fixed in 70610a55.
  - 70610a55: FAIL play=43 dc_route=45 keeper=36 broken=8, keeper PASS (only: faint streaks above the windmill, mine -> fixed in c5492f1a; vertical wind lines).
  - c5492f1a: `VISUAL_QA GATE FAIL play=42/70 dc_route=42/70 keeper=37/70 broken=10 baseline=ebda6e4752b4 failed=play,dc_route`
    Items left, none from artscene art: play "no wind ribbons visible anywhere"; dc_route "straight vertical light lines ... not flowing wind"
    (UWindPresenterSubsystem updraft ribbons; main draws them too, they only show now that the backdrop is dark) and "no red enemy shot streaks,
    gold shots in square-ish glow halos" (shot VFX). The judge's art items differ run to run on the same frames (shots/wind lists change), so part is noise.
- Blocked for a PASS on other lanes: wind presenter (ribbon shape/visibility) and shot VFX. Not mine to edit. Stopping here.
- Merged main d812ba29 (visualqa 68c07ec4) -> 2726d06c: build exit 0, PRECHECK PASS sha=2726d06c. Gate:
  `VISUAL_QA GATE FAIL play=42/70 dc_route=39/70 keeper=36/70 broken=9 baseline=ebda6e4752b4 failed=dc_route,keeper` (play now PASS).
  Items: keeper "long straight vertical line to the hanging girl" (her rope: main's keeper frame has the same line); dc_route shots (VFX lane)
  and "short flat dark bars at the far left edges" (route floor slabs, ~40:1, drawn as thin bars; same in every earlier run, flagged only now).
  Triage for the lead: four runs, no artscene item repeats; the remaining items differ run to run on the same art (judge noise against a
  single-run baseline) or are other lanes' (rope, wind ribbons, shot VFX, floor shape). Stopping.

## Nov 13 21:05 (Opus, lead order 20:57): gate 0f6dc79e dc_route "two blue circle outlines ... look like debug gizmos"
- Top centre ring = my small dial ghost (T_BgClock_PH): the glass was faded to 0.35 so only the bright rim showed, a thin ring at any alpha.
  Top left ring = the HUD's own arc around the HUD clock (still there with T_BgClock_PH changed; my large dial sits off-frame there). Not artscene.
- Fix (art_scene_clockwater.py clock, r1d): full painted face (FACE_GHOST 1.0), outer edge feathered (EDGE_SOFT 0.90, bottom rim and drips kept),
  grade 0.165/0.04 -> 0.21/0.09 so numerals, ticks and glass streak read. Re-imported T_BgClock_PH. Dropping was not an option:
  D-new-study-vs-bg-layers (DECIDED, Josh) says the clock layer is never transparent.
- Whole frame: pipeline/art/proof/artscene/dials-r1d-dc_route.png (study | gate 0f6dc79e | after; visual_qa.py capture, 1280x720).
  After: one dim painted dial with numerals and hand at top centre, no outline ring. Not judged (no spend); the gate judges it.

## Nov 13 21:40 (Opus, lead order 21:26): gate 400e00bc dc_route "flat solid slate-blue disc (clock) that reads as a plain circle"
- Cause: r1d's full face was one even ash-blue fill. Fix (art_scene_clockwater.py r1e): clock/hand grade near the void (0.15/0.06, alpha 0.30),
  warm ash grey like the study's far clock arcs (not blue), edge feather from 0.78, and fog: 3-octave value noise times a fade toward the
  lower right (haze(), applied after the hands so they sit in the same fog). Re-imported T_BgClock_PH from clock_r1e_post.png.
  T_BgClockWaterWind_PH not rebuilt (its small clock was not flagged).
- Whole frame: pipeline/art/proof/artscene/dials-r1e-dc_route.png (study | r1d | r1e). After: no disc; the dial is lost in the haze.
- Merged main 294963a8 first. Gate on the working tree (through ue_slot, logs/artscene-gate-r1e.log):
  `VISUAL_QA GATE PASS play=42,45/70 dc_route=43,42/70 keeper=42,37/70 broken=10,9 baseline=294963a82c9b recheck=1`; no clock/disc item.
