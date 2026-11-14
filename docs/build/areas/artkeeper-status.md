# artkeeper status (piece: owl)
Builder: `tools/build/assets/art_keeper_owl.py` (Blender, side-view crownless metal Keeper: plated body, chest clock, rigid ribbed/perforated vane wings, two legs, armillary + lantern + gear on chains). Job: `pipeline/art/proof/Keeper/owl/Owl_Flap/Owl_Flap.job.json`, render: `blender -b --factory-startup -P tools/build/assets/art_keeper_owl.py -- --job <job>`.

| Round | art_ref_check | Blind panel (reference pair, critic c1) | Gap |
|---|---|---|---|
| 1 | PASS 0.704 | reference wins | flat fills, no etched lines, no paper texture, no riveted vanes |
| 2 | FAIL 0.611 (hatch too dark) then fixed | reference wins (1 sampled), quality bar: ours | same |
| 3 | PASS 0.716 (min 0.698), art_check on_palette 0.988, sprite screen_check flat/grey/outline 0 | reference wins 8 of 8 reference pairs, quality bar (bar-casters pair): ours | flat-filled at the sprite's scale: no etched ink / paper texture, riveted perforated vanes not readable |

Critic sanity: the calibration pairs in every folder behaved (SAME pair -> SAME, known-different pair -> correct winner), so the critic is not defective; the gap is the same each round because our toon render stays flat next to the painted references.

Result: owl does NOT pass the blind panel. It stays the tracked `_PH` placeholder; nothing shipped, no provenance row, no Content import. The new Blender builder and renders are committed under the lane as work in progress.
Stuck rule: critic gap unchanged 3 rounds (deterministic score best 0.716): NEEDS HUMAN: Art Director / Josh. Next step that could move it: a painted-texture pass (hand-authored etching/grain image textures or a compositor hatch layer) rather than more geometry.

## Gemini rollout, round 1 (Nov 13)
- Merged main. Prompt for a 4-pose flap grid written and reviewed by a fresh session: pipeline/art/proof/Keeper/owl/Paint/R1/{prompt.md,prompt-review.md,final_prompt.txt}. Review applied: 2x2 grid at 16:9 (a 21:9 row makes the owl too small), one hand on the clock, mechanism eyes and left/right anchors, palette hexes, no-patina bronze.
- Input is our Blender render Owl_Flap_00.png; added provenance rows for Owl_Flap_00-05 so assetgen accepts it as an in-jam input.
- BLOCKED: no paid call made. GEMINI_API_KEY is not set in this shell (tools/keys.py status), and worker rules forbid reading ~/.umbrella-ella.env. Spend so far by us: 0.
- To continue: run from a shell that has the key: python3 tools/assetgen.py image --provider gemini --aspect 16:9 --image-size 2K --input pipeline/art/proof/Keeper/owl/Owl_Flap/Owl_Flap_00.png --out pipeline/art/proof/Keeper/owl/Keeper_R1/keeper_grid.png --prompt "$(cat pipeline/art/proof/Keeper/owl/Paint/R1/final_prompt.txt)"; then cut the 2x2 cells, key green, run art_check/art_ref_check, blind panel.
- Open for Josh: GDD says each mechanism's chain runs to the head's top eye; the prompt leaves that route out.

## Gemini rollout, round 1 result (Nov 13)
- Prompt updated per Josh/lead: GDD wins, each mechanism's chain runs from its underside eye to a second eye on top of the head. Call: gemini-3-pro-image-preview 2K 16:9, cost $0.139, shared spend counter 1.781 of 33.82. Output pipeline/art/proof/Keeper/owl/Keeper_R1/keeper_grid.png (note: default model gemini-2.5-flash refuses --image-size, pass --model gemini-3-pro-image-preview).
- Look: painted etched/bronze, far closer to the references than the Blender render. Not yet judged by the panel (not cut, not keyed).
- Gaps (ours, prompt): wings read as feathered, not rigid vane plates; cage is see-through (chroma green inside would key out); rear gear hidden behind torso; chains do not all reach a top eye; cell 3 wings cover the mechanisms; black grid lines between cells; owl position drifts between cells.
- Next: round 2 prompt fixes these, then cut, key, art_check/art_ref_check, blind panel.

## Round 2 (Nov 13), cost $0.140, spent 2.091 of 33.82
- Result worse than R1. ours (prompt over-specified wings and mechanism spacing): head became a plated parrot, wings pale two-tone, mechanisms bunched at the feet, chains still not to a top eye, divider lines remain, cell 3 wings level not low.
- R3: back to the R1 prompt with only small changes (solid cage walls, no divider lines, owl-shaped head, mechanisms hang below body).

## Round 3 (Nov 13), cost $0.141, spent 2.541 of 33.82
- Best owl so far (round owl head, clock, legs, bronze palette, etched look). Gaps (model ignores placement): all three mechanisms bunch at the beak/neck instead of front / middle / rear; no top-of-head eye or chain route; wings still read feathered; divider lines remain (cropped out at cut time, ours).
- R4: explicit positions for each mechanism and chain route.

## Round 4 (Nov 13), cost $0.144, spent 3.238 of 33.82
- Big gain: riveted perforated vane wings, round owl head, clock, three mechanisms spread front/middle/rear with underside eyes. Gaps: chains do not converge on a top-of-head eye (gear chain starts at the tail, armillary chain at the brow); cell 1 wing tip touches the top edge.
- Next: cut cells (crop divider lines), key green, run art_check / art_ref_check / sprite checks, blind panel.

## Round 4 deterministic checks (Nov 13) and triage
- Cut cells (ffmpeg crop, divider lines gone), keyed with assetgen clean (enclosed-key warnings are the real gaps between chains and mechanisms). Best cell art_ref_check owl 0.629 (min 0.698); detail 0.76 (floor 0.301) fine; edges 0.95; silhouette IoU 0.52.
- Triage: check is sound (reference vs itself = 1.0). Failing term is value: our dark-pixel share 0.75 vs reference 0.30. Verdict: ours (prompt asked for #3A2C25/#1D1713 metal, too dark). R5 lightens metal to mid-tone bronze and keeps ink near black.

## Round 5 (Nov 13), cost $0.141, spent 4.000 of 33.82
- Prompt: R4 with lighter bronze/pewter metal (pipeline/art/proof/Keeper/owl/Paint/R5). Cut (crop 6px off divider lines), keyed.
- art_ref_check owl: PASS 0.819 (cell 3; cells 0-2: 0.795/0.816/0.625; min 0.698). Value term fixed: the R4 triage was right (ours: too dark).
- Quick blind pair (reference, seed 5, cell 3): reference wins; calibration pairs correct. Quality-bar pair: a calibration/off-subject pair swallowed the verdict, one pair SAME. Full panel not run: it needs an in-engine capture and this piece still fails on look, so no point spending 18 sessions.
- Gaps (ours, prompt): wings feathered again (R4 had vane plates), head reads parrot/plated, mechanisms clump near the legs, no top-eye chain route, one stray chain loop. Model drifts on wing structure between runs with the same words.
- R6: R4 wing wording back, keep R5 palette, shorter mechanism block, no chain over the back.

## Round 6 (Nov 13), cost $0.140, spent 4.420 of 33.82
- Prompt: R5 + "fan of rigid blades, no feathers" wings, straight chains from one top point, flat facial disc. Model painted a muted green background (#5CB36A, not #00FF00); keyed with --chroma 5CB36A --hue-tol 30 (ours: prompt, fine, keys clean).
- art_ref_check owl: PASS 0.799 (cell 1; others 0.773/0.783/0.778).
- Quick blind (cell 1): quality-bar pair: OURS wins. Reference pair: reference wins, gap "ours is an organic feathered owl with flesh and plumage, not the fabricated metal Keeper". Calibration pairs correct.
- Look: rigid perforated vane wings and three spread mechanisms now right. Gap (ours, prompt): head/body drawn as a real barn owl (feathers, flesh face, fur-like breast); chains go up off the cell, not to a top eye.
- R7: body, head, face and breast all riveted metal plates, metal beak, glass eyes, no feather or skin texture.

## Round 7 (Nov 13), cost $0.141, spent 5.323 of 33.82
- Prompt: all-metal body/head/face/beak, glass eyes, no feather or skin. Painted grid has a green-to-white gradient background (top row did not key; bottom cells keyed clean with --chroma 00FF00 --hue-tol 40).
- Look: head now bolted metal plates, rigid vane wings, three spread mechanisms. Gaps (ours, prompt): head still reads parrot-like, chains do not reach a top eye, armillary hangs lower than the others.
- art_ref_check owl: PASS 0.705 (cell 3; cells 2 0.625; top cells unkeyed). Min 0.698, thin margin.
- Next: in-engine context capture per art-image-model.md, then full blind panel on cell 3.

## Blocked (Nov 13): context capture
- Merged main and followed art-image-model.md "Context capture". Step 1 cannot be done: no owl `_PH` asset exists under Content/UmbrellaElla/Art (VFX only) and the game draws the Keeper from cube meshes, loading no owl texture. A capture would not show the candidate, so the context pair cannot be made honestly. Request written: docs/build/requests/artkeeper.md.
- Ready when the slot exists: R7 keyed_3 (art_ref_check 0.705), reference and quality-bar pairs can be run now; remaining gaps are prompt-side (parrot-like head, chains to a top eye).

## Round 7 full blind panel (Nov 13, cell 3, keyed_3.png)
- 27 fresh critic sessions (24 reference, 3 quality-bar), calibration 21/27 sessions counted. Verdict: reference wins, quality bar wins. Context pair not run (no Keeper slot yet).
- Gap (critic, ours): feathered/organic head, mechanisms hang from a tangled chain instead of three separate body eyes, haloed cutout edges, flat unarticulated wing vanes.
- Deterministic: art_ref_check PASS 0.705, screen_check PASS, art_check FAIL off_band 0.0129 > 0.01 (halo/despill, ours: keying).
- Triage: work, not a check defect (gaps match R6/R7 notes; calibration pairs behaved). Next R8: fix keying halo, head/chain wording in the prompt.

## Round 8 (Nov 13): painted, panel run
- Painted R8 (owl head, straight chains, even green), keyed, graded sat 0.7. Best cell graded_1: art_ref_check PASS 0.717 (min 0.698), art_check PASS, screen_check PASS (flat/grey/outline 0).
- Blind panel (24 fresh sessions, 8 reference pairs + quality bar, 3 each): verdict reference. Calibration counted 16/27 sessions; reference pairs 1-2 of 3 calibrated each. Critic gaps (ours): wings and plumage still read organic/feathered, one wing visible, head small and glossy. Calibration (SAME and known-different folders) behaved in the sessions that counted, so not a critic defect.
- Context pair still missing: no Keeper `_PH` slot yet (docs/build/requests/artkeeper.md; artslots merge has none).
- Next R9: wing wording as rigid blades with visible joint spars, matte etched finish (less gloss), two wings visible.

## Rounds 9 and 10 (Nov 13), cost $0.141 + $0.142, spent 8.102 of 33.82
- R9 (rigid chisel-tip blades, matte finish): wings now read as rigid blades, but the model turned the owl to face the camera with ear tufts and set the cylinder under the feet. Ours (prompt): the wing rewrite shifted pose. Not cut or judged.
- R10 (R8 grid as the pose input + R9 wing wording): model copied the R8 pose almost unchanged (top-right cell has the broad rigid fan wing, others as R8). Cut and keyed: art_ref_check 0.693 / 0.700 / 0.658 / 0.702 (min 0.698). Same look as R8, so no new panel run (R8 panel already measured that look: reference wins).
- Verdict: the look has plateaued at the R8 level; remaining panel gaps (organic/feathered read, single clear wing, small glossy head) have not moved by prompt wording across R6-R10. Owl stays the tracked `_PH`; nothing shipped.
- Blocker for the lead: (1) no Keeper `_PH` slot, so the context pair cannot be made (docs/build/requests/artkeeper.md); (2) panel calibration counts only 16/27 sessions, so even a good round would stay "missing" until the critic sessions calibrate more reliably: lead to check the calibration folders (not loosening the bar). 
NEEDS HUMAN: Art Director / Josh: decide whether the Blender articulated route (rigid parts, Blender-rendered vanes with painted texture) should take over, since pure painting has plateaued 3 rounds.

## Candidates moved (Nov 13)
Per art-image-model.md "Where candidates live": every raw paint, keyed cut, round prompt and the Blender Owl_Flap render/job now sit under pipeline/art/proof/Keeper/owl/ (Keeper_R*, Paint/R*, Owl_Flap). Provenance, critic/owl.json, job.json and the builder docstring updated. Art/Source/Keeper holds only the tracked keeper_idle_PH placeholder. pipeline_check: only 2 unrelated agent_play.py problems (not mine); submission_check assets PASS.

## Nov 13 session: context capture attempt
- Merged main + artslots. Slot T_Keeper_Owl now exists. Imported R10 keyed_3 as Content/UmbrellaElla/Art/Keeper/T_Keeper_Owl_PH.uasset (stays _PH), build exit 0.
- Capture run: black frame with HUD only (no Keeper fight started by the smoke run; relative -SmokeShot path lands in the engine folder). Both written in docs/build/requests/artkeeper.md. Context pair still cannot be made.
- No new paint round: R6-R10 plateaued at the same panel gap (organic/feathered read, one wing); spend stays 10.89 of 33.82 (shared). The open decision is unchanged: Blender articulated route vs more paint.
- Owl stays tracked _PH; nothing shipped.
NEEDS HUMAN: Josh / lead: smoke switch to start the Keeper fight (request 1), and the Blender-vs-paint decision.

## Nov 13 later session: still blocked (no new paint, spend unchanged)
- Merged main and area/artslots. Rechecked: Source still has no -SmokeKeeper/-SmokeSection/-SmokeMap handling and a relative -SmokeShot path still resolves into the engine folder, so the in-engine context pair cannot be made (docs/build/requests/artkeeper.md items 1 and 2, both outside my lane).
- Paint plateaued R6-R10 at the same panel gap; another round would cost money without moving it, so none was run.
- Owl stays tracked _PH; nothing shipped.
NEEDS HUMAN: lead: (1) smoke switch to start the Keeper fight, (2) ProjectDir-relative -SmokeShot path, (3) Blender-articulated vs paint decision.

## Nov 12 session: still blocked (no new paint, spend unchanged)
- Merged main (artslots already in). Source still has no -SmokeKeeper/-SmokeSection handling and -SmokeShot is still not ProjectDir-relative, so the context pair cannot be made (docs/build/requests/artkeeper.md items 1-2). Paint plateaued R6-R10; no round run.
- Owl stays tracked _PH; nothing shipped.
NEEDS HUMAN: lead: smoke switch to start the Keeper fight, ProjectDir-relative -SmokeShot, Blender-vs-paint decision.

## Nov 12 later session: still blocked (no new paint, spend unchanged)
- Merged main and artslots: both already in. Source still has no -SmokeKeeper/-SmokeSection handling (only tools/ scripts mention it), so the context pair cannot be made (docs/build/requests/artkeeper.md items 1-2). Paint plateaued R6-R10; no round run.
- Owl stays tracked _PH; nothing shipped.
NEEDS HUMAN: lead: smoke switch to start the Keeper fight, ProjectDir-relative -SmokeShot, Blender-vs-paint decision.

## Nov 12 session (lane now owl, keeper-wing, keeper-talon): blocked, no paint run
- Merged main (already in). No GEMINI_API_KEY in this session (tools/keys.py status: missing; keychain empty), so no image call is possible; spend unchanged at 11.10 of 33.82.
- Context capture still blocked: SmokeHookSubsystem has no -SmokeKeeper/-SmokeSection/-SmokeMap and relative -SmokeShot still lands in the engine folder (docs/build/requests/artkeeper.md 1-2; the frame-based smoke shot from screenfix is not on main). assetgen has no tiers yet.
- keeper-wing and keeper-talon: no work started (no prompt, no prompt-review.md); both need the fresh-session prompt review before the first paid call.
NEEDS HUMAN: lead: set GEMINI_API_KEY for this worker, land the screenfix smoke shot, then restart.

## Nov 13 later session 2: still blocked (no new paint, spend unchanged)
- Merged main (art_loop change) and artslots (already in). GEMINI_API_KEY present. Source still has no -SmokeKeeper/-SmokeSection/-SmokeMap handling and relative -SmokeShot is still not ProjectDir-relative (docs/build/requests/artkeeper.md 1-2). Paint plateaued R6-R10; no round run.
- Owl stays tracked _PH; nothing shipped.
NEEDS HUMAN: lead: smoke switch to start the Keeper fight, ProjectDir-relative -SmokeShot, Blender-vs-paint decision.

## Nov 13 session 3: still blocked (no new paint, spend unchanged)
- Merged main and area/artslots: both already in. Source still has no -SmokeKeeper/-SmokeSection handling and relative -SmokeShot is still not ProjectDir-relative (requests items 1-2), so the context pair cannot be made and no round can pass. Paint plateaued R6-R10; a new round would repeat R8-R10.
- Owl stays tracked _PH; nothing shipped.
NEEDS HUMAN: lead: smoke switch to start the Keeper fight, ProjectDir-relative -SmokeShot, Blender-vs-paint decision.

## Nov 13 session 4: still blocked (no new paint, spend unchanged)
- Merged main and area/artslots: both already in. Source still has no -SmokeKeeper/-SmokeSection/-SmokeMap handling (grep empty), so the context pair cannot be made (docs/build/requests/artkeeper.md items 1-2). Paint plateaued R6-R10; no round run.
- Owl stays tracked _PH; nothing shipped.
NEEDS HUMAN: lead: smoke switch to start the Keeper fight, ProjectDir-relative -SmokeShot, Blender-vs-paint decision.

## Nov 13 session 5: still blocked (no new paint, spend unchanged)
- Merged main (one conflict in tools/build/art_inventory.py, kept both rule sets) and area/artslots (already in). Source still has no -SmokeKeeper/-SmokeSection/-SmokeMap handling (grep empty), so the context pair cannot be made (docs/build/requests/artkeeper.md items 1-2). Paint plateaued R6-R10; no round run.
- Owl stays tracked _PH; nothing shipped.
NEEDS HUMAN: lead: smoke switch to start the Keeper fight, ProjectDir-relative -SmokeShot, Blender-vs-paint decision.

## Nov 13 session 6: still blocked (no new paint, spend unchanged)
- Merged main and area/artslots. Source still has no -SmokeKeeper/-SmokeSection/-SmokeMap (grep empty), so the context pair cannot be made (requests items 1-2). Owl paint plateaued R6-R10.
- Set base: owl, base_mode: reuse in references.json for keeper-clock, -talon, -wing, -mech-front/-middle/-mech-rear, -damage, -departure (art_pass_verify base_link check PASS). They are judged on what differs only once the owl base has a verified pass; none can be painted usefully before that.
NEEDS HUMAN: lead: smoke switch to start the Keeper fight, ProjectDir-relative -SmokeShot, Blender-vs-paint decision.

## Nov 13 session 7: still blocked (no new paint, spend unchanged)
- Merged main and area/artslots: both already in. Source still has no -SmokeKeeper/-SmokeSection/-SmokeMap handling (grep empty), so the context pair cannot be made (docs/build/requests/artkeeper.md items 1-2). Owl paint plateaued R6-R10; no round run.
NEEDS HUMAN: lead: smoke switch to start the Keeper fight, ProjectDir-relative -SmokeShot, Blender-vs-paint decision.

## Nov 13 session 8: still blocked (no new paint, spend unchanged)
- Main and area/artslots already in. Source still has no -SmokeKeeper/-SmokeSection/-SmokeMap handling (grep empty), so the context pair cannot be made (docs/build/requests/artkeeper.md items 1-2). Owl paint plateaued R6-R10; no round run.
NEEDS HUMAN: lead: smoke switch to start the Keeper fight, ProjectDir-relative -SmokeShot, Blender-vs-paint decision.

## Nov 13 session 9: still blocked (no new paint, spend unchanged)
- Main and area/artslots already in. Source still has no -SmokeKeeper/-SmokeSection/-SmokeMap handling (grep empty), so the context pair cannot be made (docs/build/requests/artkeeper.md items 1-2). Owl paint plateaued R6-R10; no round run.
NEEDS HUMAN: lead: smoke switch to start the Keeper fight, ProjectDir-relative -SmokeShot, Blender-vs-paint decision.

## Nov 13 session 10: still blocked (no new paint, spend unchanged)
- Main and area/artslots already in. Source still has no -SmokeKeeper/-SmokeSection/-SmokeMap handling, and -SmokeShot is still not ProjectDir-relative (docs/build/requests/artkeeper.md items 1-2), so the context pair cannot be made. Owl paint plateaued R6-R10; no round run.
NEEDS HUMAN: lead: smoke switch to start the Keeper fight, ProjectDir-relative -SmokeShot, Blender-vs-paint decision.

## Nov 13 session 11: still blocked (no new paint, spend unchanged)
- Main and area/artslots already in. Source still has no -SmokeKeeper/-SmokeSection/-SmokeMap handling (only a doc mention in the header), -SmokeShot not ProjectDir-relative (requests items 1-2). Owl paint plateaued R6-R10; no round run.
NEEDS HUMAN: lead: smoke switch to start the Keeper fight, ProjectDir-relative -SmokeShot, Blender-vs-paint decision.

## Nov 13 session 12: still blocked (no new paint, spend unchanged)
- Main and area/artslots already in. Source still has no -SmokeKeeper/-SmokeSection/-SmokeMap handling (header doc mention only), -SmokeShot not ProjectDir-relative (requests items 1-2). Owl paint plateaued R6-R10; no round run.
NEEDS HUMAN: lead: smoke switch to start the Keeper fight, ProjectDir-relative -SmokeShot, Blender-vs-paint decision.

## Nov 13 session 13: context capture works now; panel fails on the capture, not the paint
- Merged main. -SmokeKeeper and ProjectDir-relative -SmokeShot are in. Build exit 0. Capture: `RUN_RES=1280x720 tools/build/run_game.sh -SmokeKeeper -SmokeShot=Saved/Logs/pipeline/owl-shot.png -SmokeQuitAfter=15` shows the Keeper sprite (R8 graded_1 imported to T_Keeper_Owl_PH), but a flat lilac cube (the game's old body mesh) is drawn over its torso/head, plus a grey gradient bar and a pale rectangle.
- Round on R10 keyed_3 (card artkeeper, run by the artkeeper2 session): verdict reference, context pair lost with gaps "purple placeholder block, no owl"; quality_bar pair: ours; art_check FAIL off_style 0.045 (R10 keyed_3 saturation, ours: grade it like R8 graded_1); calibration 30/40.
- My own run on R8 graded_1 duplicated that one and was killed at the 2 h background limit with no output; not restarted.
- Triage: context pair failure is "ours/source": the capture hides the owl behind the cube. Needs the keeper lane to stop drawing the cube mesh when T_Keeper_Owl(_PH) loads (docs/build/requests/artkeeper.md item 3). Until then no round can pass the context pair, so more paid paint is wasted. Spend unchanged.
NEEDS HUMAN: lead: hide the Keeper cube meshes when the owl slot texture loads (request 3).

## Nov 13 session 14: blocked on request 3, no spend
- Merged origin/main (523292da): only art_loop tooling changed; KeeperOfTime/KeeperPresenter still draw the cube over the sprite. Wrote the exact 3-step diff in docs/build/requests/artkeeper.md (Update 4). Paint is not the gap, so no paid round run (spend unchanged).
NEEDS HUMAN: lead: apply request 3 (hide stand-in cubes when the owl slot draws); then artkeeper re-captures and runs the owl panel at once (R8 graded_1 is ready).

## Nov 13 session 15: still blocked on request 3, no spend
- Merged main (already in) and area/artslots. KeeperOfTime.cpp:107 still SetVisibility(true) on the cube parts; no bArtReplacesStandIn. Exact diff is in docs/build/requests/artkeeper.md Update 4. No paid round run.
NEEDS HUMAN: lead: apply request 3; then artkeeper re-captures and runs the owl panel (R8 graded_1 ready).

## Nov 13 session 16 (Opus, lead order: Keeper cream box + lilac square): done
- Merged origin/main (262 behind; main kept outside the Keeper files).
- Cubes: `AUmbrellaArena::SetKeeperArtShown` hides the arena's graybox KeeperStandIn (survives BuildPlaceholders); `UKeeperPresenterSubsystem::SyncArenaStandIn` (every Tick + after each draw) hides it while any Keeper slot draws and shows it when none does. KeeperOfTime body cubes (wings, clock, 3 mechanisms) stay hidden under the body sprite or their own layer (`MarkPartArtDrawn`). Attack cues (eye, chain head, talon tip, gust, telegraph) still show: they are state telegraphs with no slot art.
- Test `UmbrellaElla.Feedback.World.KeeperStandInHiddenUnderArt`: break-checked (hide removed in PlaceVisual and SetKeeperArtShown -> FAIL, 7 assertions "cube N hidden under the body art", "arena keeper square hidden while Keeper art draws"; restored -> PASS).
- Paper keyed: talon, wing and front mechanism stand-ins were RGB on cream paper (each drew a paper box). `tools/build/assets/art_keeper_talon_key.py` (Blender numpy, border flood fill; numbers only) writes `move_final2_keyed.png` beside each source; reimported T_Keeper_Talon_PH / Wing_PH / MechFront_PH with `import_art_candidate.py` (chmod u+w first, no LFS lock taken: workers do not reach the remote). Test `UmbrellaElla.Feedback.KeeperPaperStandInsHaveAlpha` (corners clear, >50 % clear, >10 % opaque) PASS.
- Capture: `tools/build/run_game.sh -SmokeKeeper -SmokeShot=pipeline/art/proof/artkeeper/keeper-nocube.png -SmokeQuitAfter=20` (640x360 windowed): frame_check PASS, SMOKE_SCENE keeper=1. `python3 tools/build/assets/art_keeper_box_check.py`: screenfix b2-ella-1280.png FAIL (lilac 0.442, cream 0.356); ours PASS (lilac 0.000, cream 0.040: backdrop clouds at the box top).
- Left: the stand-ins are still unpassed _PH art (owl panel next); the front-mechanism picture's right edge is a straight frame cut.

## Nov 13 session 17 (Opus, lead order after review of 73c2ef68): state cues kept under the art
- Merged origin/main (11 commits, clean).
- Review item 1 (state cues): the slot art is static, so it shows only each part's default state. `AKeeperOfTime::PlaceVisual` now takes `bStateCue`: a covered cube still shows while its part is broken (wings, front/middle/rear) or the clock is open. Default states (wings alive, clock closed, mechanisms alive) stay hidden under the art.
- Found while testing: `PlaceVisual` set the cube colour on `Color`, but the flat unlit stand-in material reads `Tint`, so every Keeper cube was lilac whatever its state (no broken/open colour ever showed, art or not). It now sets `Tint` too. This also changes the no-art look: cubes show KeeperLook state colours instead of all lilac.
- Test `UmbrellaElla.Feedback.World.KeeperStateCuesShowUnderArt`: under the body art, default parts hidden; broken wing, open clock and broken front mechanism visible; wing tint = KeeperLook::Broken, clock tint = KeeperLook::ClockOpen. Break-checked twice: cue removed -> FAIL (3 assertions: wing, clock, front cue); Tint line removed -> FAIL (2 colour assertions); restored -> PASS.
- Minor items: arena square syncs on Keeper spawn, draw and destroy (`AddOnActorDestroyedHandler`), and in Tick only when art presence changed (no TActorIterator per frame). `SyncPartCover` (presenter Tick) sets each part's cover from the art that exists now, so a destroyed part layer clears its cover and its cube shows (asserted in KeeperStandInHiddenUnderArt). `FindPart` ignores a destroyed layer waiting for GC; `ShowPartArt` moves such a stale one aside before reusing the name. Provenance rows for the three keyed stand-ins now name the tool (Blender 5.2.1 numpy script) and input image.
- Lane grant line added to docs/build/areas/artkeeper.md (lead order item 2).
- Build exit 0. Tests: UmbrellaElla.Keeper 44/44, UmbrellaElla.Feedback 45/45, UmbrellaElla.Arena 3/3 PASS.
- Capture (640x360 windowed, -SmokeKeeper, Wings phase start): frame_check PASS; art_keeper_box_check PASS lilac 0.000, cream 0.040. No kept cube shows in this capture (default states). When a cue shows in play it is part-sized and in its state colour (dark grey broken, yellow open clock), not the full lilac body square.

## Nov 13 session 18 (Opus, lead order ~17:40: Keeper idle the way Ella's idle was made)
- Still (OpenRouter, owl piece $0.515 of the near-bar 1.00 cap): prompt reviewed by a fresh session (keeper-idle/prompt-review.md); 5 flash drafts (draft5: art_check PASS, art_ref_check PASS), Pro final1 (art_ref_check 0.707, min 0.698; two clock hands) and an edit pass final2 (one hand). One failed draft call kept its cost ($0.039, OpenRouter returned no image).
- Video: fal Veo 3.1 Fast, keeper-idle.mp4, $0.60 (piece keeper-idle-video): slow wing beat, clock and mechanisms move.
- Cut: video_to_strip.py (24 of a 45-frame loop, fps 6.4, loops=true). Its lowest-band registration moved the whole body up to 55 px (the lowest pixels are mechanisms in one frame, a wing tip in the next), so `tools/build/assets/art_keeper_grid.py` re-cuts with one fixed crop (locked camera keeps the clip's own bob). Grid 5664x2488, 6x4 cells of 944x622. `art_keeper_grade.py --clamp-hue --chroma-floor 4`: olive bronze and the pink despill fringe moved into the gold/rust band.
- Checks on grid cells: art_check PASS (off_band was 0.040). art_ref_check FAIL 0.620-0.647 < 0.698 (Veo darkened the still: dark share 0.51 -> 0.63). sprite_check FAIL on every cell only for dark_share 0.55-0.57 < 0.6 (silhouette); fringe/halo/border 0. Triage (not re-graded): the two checks pull opposite ways on darkness (art_ref_check reference 0.30, sprite_check silhouette >= 0.60); needs the lead's call, logged here, no check loosened. Owl stays a tracked _PH.
- Import: standins.json keeper:body-hover-flap -> pipeline/art/proof/standins/owl/Keeper_idle_N24_grid.png (replaces Keeper_R7 keyed_3), catalog row 6x4 (art_slots check PASS), T_Keeper_Owl_PH reimported (chmod u+w; no LFS lock, workers do not reach the remote).
- KeeperPresenterSubsystem (lead grant): plays the grid (row 0 ping-pong: M_ArtSlot samples only the top row, request Update 5); unpassed _PH part stand-ins no longer layer over body art (they hid the new owl completely: front-facing owl square, talons, wing); the body draws at its cell aspect with the 6-unit width (was squashed into a square). In uncooked -game runs the texture still compiles at spawn and GetSizeX/Y report a square placeholder (VQDUMP half=(300,0,450)); editor builds read the source size (now half=(300,0,198)). ArtSlot::CellAspect (shared) has the same issue for Ella; not touched.
- Tests: KeeperIdleFrameLoops, KeeperPartStandInsYieldToBody (break-checked: 2 assertions fail without the rule), KeeperBodyKeepsCellAspect (break-checked: 1.0 vs 2.0 without it), ArtSlotKeeperParts updated to the new rule; KeeperStateCuesShowUnderArt PASS. Feedback+Keeper 98/98 PASS.
- Frame (visual_qa.py frame --screen keeper): Director's Cut before 20, after 26; Start Game (-SmokeKeeper) after 26. No Keeper item left in "broken" (before: "Keeper sprite on a visible rectangle"). Remaining broken items are other lanes: ground bar and block, tether pole, no wind ribbons, Ella at the top edge. small_figures 3 -> 4. Composite: pipeline/art/proof/artkeeper/frame/keeper-composite-dc.png; devlog line added.
- Left: the in-engine wing highlights read pinker than the file (engine side; the art carries no pink after the grade). Choice for the lead: hiding unpassed part stand-ins under body art (default taken) vs keeping them.

## Nov 13 session 19 (Opus, lead fast-track 18:35: owner-approved owl in)
- Restored the owner-approved grid (082c95a0 bytes, LFS oid 8bb4d531, approvals.json keeper-idle on main 8c5ded33) in fixed/ and standins/owl/, and T_Keeper_Owl_PH from 082c95a0 (imported from those bytes, oid 0ccd23fb). standins.json sha and provenance row back to 8bb4d531. Code edits from 069f8ad3 kept (body cell aspect: needed so the owl is not squashed; state cues untouched).
- Merged origin/main. Build exit 0, warnings 0. Feedback+Keeper 100/100 PASS, incl. KeeperStateCuesShowUnderArt and KeeperStandInHiddenUnderArt.
- Capture 1280x720 windowed -SmokeKeeper: frame_check PASS, owl drawn, no cube. pipeline/art/proof/artkeeper/frame/keeper-after-approved.png; composite keeper-composite-approved.png (study | before dc | after). Devlog line added.
- module_check: 2 -> 0 (0.01f -> UmbrellaKeeperPresenterConst::MinBodyAspect; PartPictureYieldsToBody -> ShouldPartPictureYieldToBody).
- Follow-up (needs a new owner approval): pink wing-rim cleanup, re-graded sheet 5f61cf17 (art_keeper_grade.py --chroma-floor 4), in 069f8ad3 history.

## Nov 13 session 20 (Opus, lead fix order after review HOLD of 34f3bdde)
- Merged origin/main 8c5ded33: already up to date. Build exit 0, warnings 0 (commit 34f3bdde).
- (1) `python3 tools/build/visual_qa.py run --out pipeline/qa/visual/artkeeper-34f3bdde --main-sha 8c5ded33` (launches through ue_slot.sh itself), on 34f3bdde:
  `VISUAL_QA FAIL play=35/70 dc_route=24/70 keeper=26/70 broken=8 baseline=none failed=play,dc_route,keeper`
  No baseline for main 8c5ded33 exists (../logs/visual-baseline/ is empty), so "worse than main" cannot be measured; I did not create one (lead's gate step). Broken items, none in the Keeper lane: thin full-height white vertical line (play, keeper), no wind ribbons (play), flat brown ground bars + block step (dc_route, keeper), cream clock-face backdrop and no floating islands (dc_route). Keeper screen 26/70 matches session 18/19's own frame score (26). No Keeper item listed as broken.
- (2) Part readability: pipeline/qa/visual/artkeeper-34f3bdde/vq_keeper.png (gameplay, -SmokeJourney visual_qa) and keeper-parts-readability-3x.png (owl crop, 3x). Readable in the body art: two wings, central clock, three distinct hanging mechanisms (gear ball, cage, ring), talons. Default-state cube cues stay hidden under the art; broken/open cues show (KeeperStateCuesShowUnderArt). Part pictures stay hidden under body art (not re-enabled: the parts read in the body art itself). Gap for the lead: owl faces left, so the front (head-side) mechanism is the gear ball and the ring hangs at the rear; OWL-08 says front is the armillary/ring. Owner-approved art, not changed here.
- (3) The shipped Keeper idle is a 6-frame ping-pong of row 0 of the 6x4 grid (M_ArtSlot samples only the top row) until docs/build/requests/artkeeper.md Update 5 lands (lead assigns it); then UmbrellaKeeperPresenterConst::IdlePlayback flips to AllCells.
- (4) KeeperPresenterSubsystem.cpp: comment cites UE 5.8.4 Engine/Classes/Engine/Texture.h for UTexture::Source, FTextureSource::IsValid and GetSizeX/GetSizeY (comment only, no code change).
- Not swapped: pink-rim sheet 5f61cf17 (needs Josh's approval). approvals.json untouched.

## Nov 13 session 21 (Opus, lead order ~20:30: owl sharper in the raw video than in the grid and in game)
- Merged origin/main (ebda6e47). Approved grid 8bb4d531 and approvals.json untouched; T_Keeper_Owl_PH left as it was (mip tests reverted with git checkout).
- Tool: `tools/build/assets/art_keeper_sharpness.py` (ffmpeg + numpy; run with Blender's python -I). Sharpness = mean luma gradient on the inner figure. `art_keeper_texdump.py` prints the texture and render settings (read-only commandlet).
- (a) key: 0 partial-alpha px on 6683 edge px (hard cut, no feather); the cut eats 2 px (chroma_key grow=2: the cream outline); edge band 0.98 of raw.
- (b) grade: 3.9 % of solid px changed, mean 0.19/255; inner sharpness cell/raw 0.9997.
- (c) resample: 1.000 source px per cell px (registration RMS 0.15 at 944 px vs 39-40 at +-12 px); ffmpeg lanczos at 720 vs plain decode: max diff 0. Note: the sidecar crop [50,18] is relative to video_to_strip's own --crop; the cell sits at (230,28) in the frame.
- (d) in-game texture: BGRA8 uncompressed (TC_EDITOR_ICON), sRGB, no mips, UI group (filter aniso, MaxLODSize 16384), never stream, LOD bias 0, 5664x2488 full size. Render: TSR (r.AntiAliasingMethod 4), screen percentage auto.
  Screen scale: owl cell drawn 378-384 px wide at 1280x720 (SMOKE_DRAW px=753..1131) = 2.48 texels per screen px; 568 px at 1920x1080 = 1.66. The raw video shows the same cell at 944 px.
  In-game sharpness vs ideal lanczos at the same size (1280x720): base 0.73 / 0.76 / 0.75 (3 runs); AA off 1.09 (blur 1.005, aliased); FXAA 0.84; TAA 0.65; tone mapper off 0.67; r.Tonemapper.Sharpen 0.5 / 1 / 2: 0.92 / 0.97 / 1.11. 1920x1080: base 0.57, r.ScreenPercentage 100 0.66, + Sharpen 1 0.79.
  Mips (in my lane): simple average 0.68, sharpen5 0.74, sharpen10 0.77 / 0.83 / 0.77: no gain past run-to-run noise, +33 % memory. Not shipped.
- Verdict: the art pipeline costs nothing; the softness is the screen size (2.48x smaller than the video) and TSR (0.75). No fix in this lane; options for the TD/lead in docs/build/requests/artkeeper.md Update 6. No grid change needed, so no new grid prepared.
- Side-by-side: pipeline/qa/visual/owl-sharpness/owl-sharpness-side-by-side.png (raw | keyed | in-game before | in-game after PREVIEW with r.Tonemapper.Sharpen 1, runtime only) + README + json.
- No test added: no code fix shipped; the tool needs numpy, which the repo's python lacks.

## Nov 13 session 22 (Opus, lead order 21:42: Keeper wing-gust warning made like the owl)
- Merged origin/main (already up to date at 13534964).
- Clip: input = approved idle grid cell 0 (oid 8bb4d531) at 80 % on #00FF00 (`art_keeper_wing_gust.py input`). Prompt reviewed by a fresh session (wing-gust/prompt-review.md, applied whole). fal Veo 3.1 Fast i2v, piece keeper-wing-gust-video, $0.60 (assetgen: "spent=$12.000 of $74.84"). No Gemini/OpenRouter still needed.
- Cut: video_to_strip.py keyed 48 frames at 12 fps. Veo raised the wings far past the asked 30 degrees: frames 7-22 clip the top edge, 24-28 the left, 33-38 the bottom. A second take would pass the 1 USD per-piece video cap, so only unclipped frames are used: gather 0-6, flap 23/29/31/32, recover 39/42/46. One fixed crop [6,18,986,700], one row of 14 cells (M_ArtSlot reads the top row), no upscale; `art_keeper_grade.py --clamp-hue` (same grade as the approved grid). Clip frame 0 registers on the input within 2-4 px. Imported as T_Keeper_WingGust_PH (stays _PH).
- For Josh's approval (not gated until then; approvals.json untouched): pipeline/art/proof/artkeeper/wing-gust/frames/ (14 cells), wing-gust-side-by-side.png (approved idle | cells 3, 6, 7, 8, 9, 12). Gap: the flap frames hide the hanging mechanisms behind the wing and the despill leaves the same faint pink wing tips as the approved idle.
- Code (lead grant files): `AKeeperOfTime::WingGustCellFor` gathers over 70 % of the 1.1 s warning, flaps through the launch (+0.25 s) and recovers over 0.45 s, then idle; gated on OWL_15. `GustStrokes` draws #555e60 ribbons in code: 4 thin wavy strands draw out along the locked lane toward -X during the warning, then 5 thick strands with heads at the hit front's leading edge while the gust travels. The flat telegraph box and the flat gust cube are never shown for the gust (other telegraphs unchanged). Found while there: the old gust box was drawn from BandZ to BandZ+120 while the hit band is BandZ +-60; the ribbons are centred on BandZ. `UKeeperPresenterSubsystem` draws the clip as its own layer placed so the clip owl lands on the idle owl (body hidden while the cue plays, idle grid untouched); workbench `-SmokeKeeperCueShot=<png> [-SmokeKeeperCueCell=n]` captures at a cue cell.
- Timing unchanged: warning 1.1 s, band 120 (asserted).
- Tests: UmbrellaElla.Keeper.WingGust.CueFollowsTheWarning (model warning measured 1.1 s, gather then flap on launch), .RibbonsShowDirectionAndFront (in band, heads lead -X, thick head, thin tail, wavy), .WarningDrawsRibbonsNotABox (no box/cube, #555e60, cleared when the wings break), Feedback.World.KeeperWingGustPlaysOverBody. Keeper+Feedback 104/104 PASS. Break-check: old box back -> FAIL "no flat telegraph box for the gust". Build exit 0, warnings 0; module_check 0.
- visual_qa frame --screen keeper (1280x720, -SmokeKeeper): before (main's look, temporary patch for this capture only) 30, broken "solid salmon-pink rectangle bar". After, first ribbon try: 27/29, "ruled straight grey lines with an arrow glyph", "partial ring" -> redrawn as tapered wavy strands. After: gather 38, flap 39, travelling 32. Remaining broken items are not this lane: the full-height tether line (also in before) and, while the gust travels, the "stray ornate scroll sprite" = the existing VFX_Gust sheet drawn by the VFX director.
- Proof: wing-gust/capture/before-cell5.png, after-cell5/9/12.png, wing-gust-composite.png (study | before | after), wing-gust-before-after.png; devlog line added.
- Left for the lead: VFX_Gust scroll sprite (VFX lane) reads as misplaced next to the ribbons; Josh's approval of the clip.
