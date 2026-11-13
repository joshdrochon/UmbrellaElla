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
