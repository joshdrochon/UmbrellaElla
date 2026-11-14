# artella status (Nov 12)

## State: no piece passes the bar. All four stay tracked `_PH` placeholders.
- Rendered with Blender 5.2.1 through `tools/assetgen.py blender --character ella` (anims Open, Attack, Close, Fall;
  IdleFloat not rendered) into `Art/Source/Ella/Raw/Ella_<Anim>_PH/` (4 frames each, 432x352). Provenance rows added (16).
- Pieces: ella-up-open (Open), ella-attack (Attack), ella-closed (Close, Fall), ella-shield: no recipe row exists
  in `characters.json` (the canopy-forward shield pose), so it is not rendered.
- Blind panel NOT run, no `.artloop.json`, nothing shipped under `Art/` or imported to Content. Reason: the stand-in rig is
  primitives (cone hat, box body, cylinder arm) against the painterly Rehearsal/Ella references and the bar-casters tier.
  Open_00 does not even show an open canopy. Running a critic on it would only record a certain fail.
- `screen_check.py` fails on a lone sprite (it measures a 16:9 gameplay frame, not a sprite), so it was not used as a sprite gate.

## Gap to the bar (what a next round must change in `stand_ins.py` build_ella)
Real silhouette: hat brim bend, long hair and scarf, layered ragged skirt, boots, two-hand grip; umbrella canopy with ribs, scalloped
edge, crown finial and diamond terminal; shading and paper-grain finish near the references. Primitives alone are unlikely to reach
"SAME" against the bar; the critic-sanity test (reference passes itself, known-bad fails) was not run.

## Next
1. Add an `ella-shield` row in characters.json (lane allows `tools/build/assets/art_ella*.py`, but characters.json is shared pipeline: request in docs/build/requests/artella.md if the lead wants it).
2. Rebuild build_ella with sculpted detail, re-render, then `art_loop.py blind/panel/verdict` per piece.


## Round log (Nov 12, afternoon)
All four pieces share one rig (`build_ella` in `pipeline/art/blender/stand_ins.py`, lead-directed edit; only that function and two new Ella-only materials changed).
| Round | Change | art_ref_check | Panel (ours vs ref / vs bar-casters) | Critic gap |
|---|---|---|---|---|
| 1 | tiered ragged skirt, hair, torn scarf, bent hat, 16-gore ribbed canopy, boots | 0.2 (min 0.398) | ref wins 3/3, bar wins/same | flat vector fill, no etched line or paper grain, grounded |
| 2 | same + lighter cloth ramp | 0.2 | ref wins 3/3, bar mostly wins | same gap |
| 3 | grain 0.38 on cloth, lighter ramp, 0.2 rad airborne lean | 0.2 | ref wins, bar wins | same gap (flat cartoon, thick uniform outlines, no grain) |
Deterministic: screen_check PASS, art_check sprite colour rules PASS, art_ref_check FAIL (0.2, no movement over 3 rounds).
Critic sanity: reasons are the same every round and match the references and GDD; the calibration folders (known SAME / known winner) were answered correctly in the 6 sessions I read; it picks the reference every time. No defect found, so the bar stands.
Also missing for any pass: the `context` pair needs an in-engine capture after import (not possible until a piece passes).

## State: STUCK (3 flat rounds, same gap, art_ref_check score not moving). All four pieces stay tracked `_PH`.
Nothing shipped under `Art/`, no `.artloop.json`, no Content import. ella-attack, ella-closed, ella-shield not paneled: same rig, same gap, a certain fail.
NEEDS HUMAN: Josh, Blender primitives with toon shading cannot reach painted-sculpt references (Rehearsal Ella, bar-casters). Choices: (a) hand-sculpted / imported model (needs a provenance-clean source), (b) an image-generation path for Ella frames (rule BG-02/ART-03 says references are not generation inputs), (c) accept `_PH` for the jam build.
Lean: (c) now, (b) only if rules allow it.

## Round 6 (Nov 12, evening): rerun on main 4ed1d35 (critic-packet fix: transparent renders on one paper ground)
Earlier rounds are invalid evidence; this is the first panel after the fix. Renders: `gp_ella.py` (Grease Pencil drawing),
`Art/Source/Ella/Raw/GP_PH/Ella_{up-open,attack,shield,closed}_GP_PH.png` (600x700). All stay tracked `_PH`.
| Piece | art_ref_check | screen/art_check | Panel (3 sessions per pair) | Critic gap |
|---|---|---|---|---|
| ella-up-open | 0.737 PASS (min 0.398) | PASS | ref wins 2/3, bar wins 2/3 | crude cartoon, blocky shapes, thick uniform outlines, no paper grain or tonal depth, mitten hands |
| ella-attack | 0.2 FAIL (min 0.448) | PASS | ref wins, bar wins | canopy detached from shaft, no two-hand grip, no gold spell, flat angular skirt |
| ella-shield | 0.624 PASS (min 0.586) | PASS | ref wins, bar wins | blocky stacked dress, stiff upright pose, wrong canopy shape, no finish |
| ella-closed | 0.2 FAIL (min 0.749) | PASS | ref wins, bar wins | reads as a grounded figure with a staff, not a closed umbrella; no airborne pose |
No piece passes. `context` pair cannot run until a piece is imported (circular: import only after a pass), so it blocks any pass today; lead should confirm how a first pass can get an in-engine capture.
Critic sanity (run before declaring stuck):
- Reference passes itself: Ella-Rising-02 as "ours" got SAME on all 3 reference-pair sessions and beat the bar image in the bar pair. OK.
- Known-bad fails: our drawings lose to the references in every round; the Roadwarden calibration folders were answered correctly (known winner Y/X, known SAME = SAME) in the sessions read.
- Self-agreement: 3 sessions per pair give the same gap each time; gaps match the references and GDD (airborne, umbrella, etched finish). Calibration scored 3/6 to 7/9, so some calibration sessions are noisy (the panel refused one round on 3/6), but no verdict contradicted the images.
- Side effect: the sanity run logged a "round 4" refused entry for ella-up-open in art-loop.jsonl; ignore it.
No defect found; the bar stands.
Concrete misses I can see in my own images: attack and closed poses are wrong in the drawing (detached canopy, staff instead of folded umbrella, grounded), and the up-open drawing still has flat tiered boxes for the dress. These are fixable drawing errors, but the finish gap (painted sculpt vs scripted strokes) is unlikely to reach SAME in this tool.

## State: STUCK for the same reason as before (finish gap), NEEDS HUMAN unchanged. Nothing shipped, no `.artloop.json`, no Content import.
Choices for Josh: (a) provenance-clean sculpted/painted source, (b) image-generation path if rules allow, (c) keep `_PH` for the jam build.
Lean: (c).

## Round 7 (Nov 13): Gemini rollout, blocked on the key
Done: merged main; four prompts written and reviewed by a fresh Sonnet session (Art/Source/Ella/Paint/prompt.md,
prompt-review.md, assembled prompts.json, `paint.py <piece> <round>` makes one paid call). Review applied word for word
(apricot-cream outline #FFE6C4, mid-tone cloth against dark_share, hair/hat/scarf traits, SHIELD and closed poses fixed).
Ours, fixed with no spend: off_band. `tools/build/assets/art_ella_post.py` recolours the outer 4 px band to #FFF3D6;
R3 idle strip off_band 0.0855 -> 0.0092 (max 0.01). dark_share (0.52) is still above 0.45: this round's prompt targets it.
BLOCKED: GEMINI_API_KEY is not set in this worker's shell (assetgen: "NO KEY"). Worker rules forbid me to read or source
~/.umbrella-ella.env. No paid call was made; spend untouched. Needed: lead exports the key (or keychain item) for this
worker, then run `for n in up-open attack shield closed; do python3 Art/Source/Ella/Paint/paint.py $n R1; done`
(about $0.57), then clean --chroma 00FF00, art_ella_post.py, frames --cells, blind panel.

## Round 8 (Nov 13): R1 Gemini paints judged (merged artinventory; references.json 100 entries kept)
R1 paints (4 frames each, `Art/Source/Ella/Paint/R1/frames_<piece>/`), cut and post-processed; spend so far 4.00 USD of 33.82.
| Piece | art_ref_check | art_check (sprite colour rules) | Panel |
|---|---|---|---|
| ella-up-open | 0.722 PASS (min 0.398) | PASS (dark 0.44, off_band 0.008) | reference pair ours, quality-bar pair ours, calibration 6/6; only `context` missing |
| ella-attack | PASS 0.707 (frame 00) | FAIL accent_area 0.094, off_band 0.040, dark 0.466 | not run |
| ella-shield | FAIL 0.561 (min 0.586) | FAIL off_band 0.013, dark 0.53 | not run |
| ella-closed | FAIL 0.715 (min 0.749) | FAIL accent_area 0.112 | not run |
ella-up-open is the first piece to beat the bar. Blocked from shipping only by the `context` pair: it needs an in-engine capture made
after the piece is imported, and the import is gated on a pass (circular). Lead: say whether to import first as a tracked `_PH`-named
asset so the smoke can capture, or relax the order. Next: R2 paints for attack, shield, closed with prompts adjusted to the failing numbers.

## Round 9 (Nov 13): context capture attempted, blocked by a missing game-side slot
Merged main, followed "Context capture". Step 1 fails: no Ella `_PH` asset slot exists in Content and no code loads an Ella flipbook
(`IdleFlipbook` is never set; cube stand-in is what a capture shows). Needs a loader in the feedback lane: docs/build/requests/artella.md #2.
R2 paints for attack/shield/closed are cut (3 frames) but not yet judged. ella-up-open stays blocked only on `context`.

## Round 10 (Nov 13): R2 paints judged, still blocked on the Ella slot
Merged main and artslots; `FB_Ella` loader still absent from Source (request #2 open). No paint spend this round (shared counter 7.82 of 33.82).
| Piece | art_ref_check | art_check | Panel |
|---|---|---|---|
| ella-attack | PASS 0.649 (min 0.448) | PASS | reference pair: ref wins/SAME mix; calibration 3/6, panel refused (judge again) |
| ella-shield | PASS 0.588 (min 0.586) | PASS | ref wins 1 of 3 reference sessions, SAME in others; bar pair split; calibration 7/9. Gap: no pierced diamond terminal, crown finial, mask, gold magic |
| ella-closed | FAIL 0.2 (min 0.749, closest ella-freefall) | PASS | not run |
Critic noise on attack (calibration 3/6) is the critic's, not a defect found in the images; reasons match the references. Verdict: work.
Nothing shipped. Every pass is blocked anyway by the `context` pair (request #2). Next once the slot exists: import up-open as `FB_Ella_Open_PH`, capture, finish its panel.
Next paints: shield R3 (terminal, finial, mask, gold in prompt), closed R3 (airborne folded umbrella, ref check 0.2).

## Round 11 (Nov 13): re-checked after merging main, still blocked on request #2
Merged main; origin/area/artslots has nothing new. `grep -rn "Art/Ella" Source` finds no Ella loader (only VFX paths). `Content/UmbrellaElla/Art/` has only `VFX/`.
No `context` capture is possible, so no Ella piece can pass. No paint spend this round (R3 for shield/closed would not change that).
Stopped on the blocker: lead must add the `FB_Ella_<State>_PH` loader in the feedback lane (docs/build/requests/artella.md #2). Then: import ella-up-open as `FB_Ella_Open_PH`, capture, finish its panel; paint shield R3 and closed R3.

## Round 12 (Nov 13): candidates moved off Art/Source
Merged main. Per art-image-model.md "Where candidates live": Paint R1/R2 (paints, keys, posts, frames) now under
`pipeline/art/proof/artella/<piece>/<round>/`; Blender/GP/3D renders under `pipeline/art/proof/artella/raw/`. Provenance paths updated (51 rows);
`paint.py` writes to the new path. `Art/Source/Ella/Raw/Ella_*_PH` (the tracked placeholders) and the scripts stay. Blocker unchanged: request #2 (Ella slot loader).

## Preview (Nov 13): per-state looping previews for the team (candidates stay _PH, not shipped)
Script: `tools/build/assets/art_ella_preview.py` (ffmpeg; 8 FPS; left = paper tile `SKY_StarPaper_Tile.png`, right = flat dark #1c1c22; sprite scaled to 540 px high).
Candidates shown: open = up-open R1 (4 frames), attack = attack R2, shield = shield R2, closed = closed R2 (3 frames each).
Files under `pipeline/art/proof/artella/preview/<state>/` (state = open, attack, shield, closed):
`<state>_preview.gif`, `<state>_preview.mp4` (960x600), `<state>_strip.png` (all frames side by side, dark ground).
Seen in the previews: the attack frame has a cut-off fragment at its right canvas edge (frame crop), not part of the figure.
In-game capture (1280x720): see "Preview capture" below.

### Preview, registered (Nov 13): jitter fix
Script: `pipeline/art/proof/artella/register_ella.py` (pillow, numpy, scipy, ffmpeg). Anchor = bottom-centre of the lowest solid band
(4% of height) of the alpha mask, specks under 2% of the main part ignored. Each frame is scaled so mask height = strip median, then
translated so the anchor is on one pixel. Registered frames: `pipeline/art/proof/artella/registered/<state>/`; previews rewritten in
place (`preview/<state>/<state>_preview.gif`, `.mp4`, `_strip.png` = paper | dark, 8 FPS). Numbers: `registration_report.json`.
| State | max anchor offset px, before -> after | max scale drift %, before -> after |
|---|---|---|
| open | 38.5 -> 0.5 | 0.2 -> 0.0 |
| attack | 80.3 -> 0.3 | 2.6 -> 0.0 |
| shield | 180.3 -> 0.4 | 7.4 -> 0.0 |
| closed | 107.6 -> 0.6 | 0.1 -> 0.0 |
Not fixed (source cut, not registration): shield and attack cells clip the figure at the cell edge (umbrella and scarf fragments on
the left of frames 1-2). Needs a re-cut of the paint with wider cells; no paint done here.

## Round 13 (Nov 13): slot exists, context capture attempts
Merged main + artslots; the `FB_Ella`/`T_Ella_<State>` loader is now in Source (request #2 answered). Imported the registered up-open frame 00 as
`Content/UmbrellaElla/Art/Ella/T_Ella_Idle_PH` with `import_art_candidate.py ... ella-state:Idle` (import OK, still `_PH`). Build exit 0.
`run_game.sh -SmokeShot=<abs path>` runs on a machine saturated by other workers (game fps 0.1 to 0.6): three launches (240 s, 1500 s) hit the
timeout with no shot file. Note a relative -SmokeShot path wrote nothing under the worktree. Verdict: ours/env (load), not the art. A 2400 s run is queued.
ella-up-open still has only `context` missing; attack/shield/closed paints unchanged since Round 10.

## Round 14 (Nov 13 late): lane split, merged main
My pieces now: ella-up-open, ella-attack, ella-shield, ella-closed, ella-motion. Merged main: assetgen still has no tiers and the frame-based smoke shot
(screenfix) is not in yet. Spend counter 15.08 of 33.82. No paint this round: no piece can pass without `context`, and the machine load is ~31.
A context capture launch via ue_slot/run_game.sh is running (T_Ella_Idle_PH = up-open frame 00); result below if it lands.
Round 14 result: the capture landed (640x360) but shows "Preparing Shaders (3)" on black, no Ella: the time-based shot (5 s) fires before shaders finish on a loaded machine
(ours/env, not the art). Discarded, so no `context` pair. Needs the frame-based shot from screenfix. ella-up-open still blocked only on `context`.

## Round 15 (Nov 13 late): re-checked, still blocked on a reliable context capture
Merged main and artslots. The frame-based shot is still not in: `SmokeHookSubsystem.cpp:132` fires on `Elapsed >= SmokeShotDelaySeconds` (5 s, tuning), with no command-line override. Machine load ~27.
The Round 14 capture showed "Preparing Shaders" on black. No paint spend (counter unchanged, 15.08 of 33.82); a new paint could not pass without `context`.

## Round 16 (Nov 13 late): merged main and artslots, nothing new; still blocked on request #3
`SmokeHookSubsystem.cpp:132` still fires at a fixed 5 s; no `-SmokeShotDelay` override. Load ~27. No paint spend (15.08 of 33.82). Stopped on request #3.

## Round 17 (Nov 13 late): merged main and artslots, nothing new; still blocked on request #3
`SmokeHookSubsystem.cpp:132` still a fixed 5 s delay, no command-line override. Load ~25. No paint spend (15.08 of 33.82). Stopped on request #3.

## Round 18 (Nov 13 late): merged main and artslots, nothing new; still blocked on request #3
`SmokeHookSubsystem.cpp:132` still a fixed 5 s delay, no command-line override. Load ~24. No paint spend (15.08 of 33.82). Stopped on request #3.

## Round 19 (Nov 13 late): merged main and artslots, nothing new; still blocked on request #3
`SmokeHookSubsystem.cpp:132` still a fixed 5 s delay, no command-line override. Load ~24. No paint spend (15.08 of 33.82). Stopped on request #3.

## Round 20 (Nov 13 late): merged main and artslots, nothing new; still blocked on request #3
`SmokeHookSubsystem.cpp:132` still a fixed 5 s delay, no command-line override. No paint spend (15.08 of 33.82). Stopped on request #3.

## Round 21 (Nov 13 late): ini override for the shot delay works, capture window not found yet
Main and artslots: nothing new. Found a workaround for request #3 with no code change: `UmbrellaTuning` is a config class, so
`run_game.sh -SmokeShot=<abs> -SmokeQuitAfter=240 "-ini:Game:[/Script/UmbrellaElla.UmbrellaTuning]:Flow=(SmokeShotDelaySeconds=N)"` sets the delay.
N=120: shot landed (640x360) but shows the Defeat screen (Ella died while waiting, no Ella visible). N=35: queued behind the 2-slot
`ue_slot` (artslots, artenemy hold both), no log in the 30 min limit, no shot. Verdict: ours/env (load and slot wait), not the art.
Next: retry N=35..60 when a slot is free; then up-open `context` pair. No paint spend (15.08 of 33.82). Note: macOS has no `timeout`.

## Round 22 (Nov 13 late): frame-based shot is in; capture queued behind ~20 ue_slot waiters
Merged main + artslots. `-SmokeShotFrames=` exists now (request #3 answered). First capture was probably killed by another worker's `pkill -f run_game.sh`
(no log, no shot). Relaunched via ue_slot with `-SmokeShot=<abs> -SmokeShotFrames=60 -SmokeQuitAfter=20` (log /tmp/artella_cap.log); after 30+ min still waiting for a slot
(about 20 ue_slot processes queued, load ~35). Verdict: env (slot queue), not the art. No paint spend (15.08 of 33.82).
Next: when the shot lands, run the up-open panel; then paint shield R3 and closed R3.

## Round 23 (Nov 13 late): duplicate session, did nothing
Merged main + artslots (clean). Another artella session (pid 69829) is already running the ella-attack and ella-shield panels (pids 64847/64848) and the up-open capture is queued on ue_slot. A second worker would collide on the same pieces and spend. No paint (15.08 of 33.82), no panel. Resume after those finish: up-open panel on the capture, then shield R3 and closed R3.

## Round 22 (Nov 13 late): frame-based shot (screenfix merged) ran, still no usable capture
Merged main (screenfix in). Checks: ella-up-open art_ref_check PASS 0.728, ella-attack PASS 0.649 (art_check up-open PASS). Panel not run: no `context` pair.
`RUN_RES=1280x720 run_game.sh -SmokeShot=<abs> -SmokeShotFrames=60 -SmokeQuitAfter=300` waited for a slot, then wrote a 640x360 shot of "Preparing Shaders (3)" on black, no Ella
(frame 60 is before shaders finish at load ~60). Discarded. Verdict: ours/env (load), not the art. Next: retry with a larger -SmokeShotFrames (e.g. 600) when load drops.

## Round 24 (Nov 13 late): merged main, capture still queued
Merged main (artslots had nothing new). Two earlier up-open capture launches (pids 85916, 88232, from 1:15 AM) are still waiting on ue_slot; no shot file yet. Load ~29. No paint, no panel, no spend (15.08 of 33.82). Verdict: env (slot queue), not the art. Next: when the shot lands, run the up-open panel; then shield R3 and closed R3.

## Round 25 (Nov 13 late): merged main and artslots, capture still queued
Nothing new on main or artslots. The up-open capture (pid 85916, since 1:15 AM) is still waiting on ue_slot (~30 ue_slot processes, load ~25); no shot file. No paint, no panel, no spend (15.08 of 33.82). Verdict: env (slot queue), not the art. Next: when the shot lands, up-open panel; then shield R3 and closed R3.

## Round 26 (Nov 13 late): merged main, relaunched the capture with frame 600
Both queued captures used -SmokeShotFrames=60, which Round 22 showed lands on "Preparing Shaders". Killed them and queued one with -SmokeShotFrames=600 (log /tmp/artella_cap.log). Load ~28. No paint, no panel, no spend (15.08 of 33.82). Next: when the shot lands, up-open panel; then shield R3 and closed R3.

## Round 27 (Nov 13 late): the frame-600 capture landed; it has no Ella, so no panel
The Round 26 capture (pid 935, `-SmokeShotFrames=600`, 1280x720) waited for a slot and wrote `Saved/Logs/pipeline/ella-up-open-shot.png` at 03:01. Shaders are done (no "Preparing Shaders"), but the frame is black with only the HUD clock top-left: no Ella, no ground. Game log: map L_Graybox, `SMOKE_OK` fps=15.5 worst_ms=953.8, `SMOKE_EFFECTIVE outcome=fail` (Ella was hit to defeat at frame 147 of the log clock, shots and PlayerDefeated events just before the shot).
Verdict: env/ours (smoke run is a fail run on a loaded machine; Ella is defeated or off-screen at the shot), not the art. A shot with no Ella cannot be a `context` pair, so the up-open panel was not run. No paint, no spend (15.08 of 33.82). Shield R3 and closed R3 not started: they need a context pair too.
Next (needs a lane I do not own): a shot taken while Ella is alive and on screen (shot frame earlier than defeat but after shaders, or a no-damage smoke mode). I will not retry the same command.

## Round 28 (Nov 13 late): merged main, new capture at frame 250
Merged main (conflict in tools/assetgen.py, not my lane: took main's version). artslots had nothing new. Frame 60 = shaders not ready, frame 600 = after Ella's defeat, so queued one capture at `-SmokeShotFrames=250` (log /tmp/artella_cap250.log, ~16 ue_slot waiters, load ~28). No paint, no spend (15.08 of 33.82). Next: if the shot shows Ella, run the up-open panel; then shield R3 and closed R3. If Ella is still absent, the fix is a no-damage smoke flag (request for the smoke lane).

## Round 29 (Nov 13 late): merged main and artslots (nothing new); frame-250 capture still queued
The frame-250 capture (pid 30354) is waiting on ue_slot, no log or shot yet; load ~32. No paint, no panel, no spend (15.08 of 33.82). Verdict: env (slot queue), not the art. Next: if the shot shows Ella, up-open panel; then shield R3 and closed R3. If Ella is absent, request a no-damage smoke flag from the smoke lane.

## Round 30 (Nov 13 late): nothing new; frame-250 capture still queued
Main and artslots: nothing new. Capture pid 30354 still waits on ue_slot (empty log, no shot); load ~28. No paint, no panel, no spend (15.08 of 33.82). Verdict: env (slot queue), not the art. Next: if the shot shows Ella, up-open panel; then shield R3 and closed R3. If Ella is absent, request a no-damage smoke flag from the smoke lane.

## Round 31 (Nov 13 late): frame-250 shot landed, still not usable; merged screenfix fix
`ella-up-open-shot.png` (03:09) shows "Preparing Textures (1)" on black, no Ella: shot taken before textures finish under load. Discarded, no panel. Merged area/screenfix (2db3d92c); ArtSlot.cpp conflicted, took screenfix's version (not my lane). No paint, no spend (15.08 of 33.82).
Blocker: no capture with Ella on screen. Shield R3 and closed R3 need a context pair too. Next: retry capture with a later frame (e.g. 400) when load drops, or a smoke flag that waits for textures and keeps Ella alive.

## Round 32 (Nov 13 late): lead's retry at -SmokeShotFrames=3000, still "Preparing Textures (1)"
Ran once as told: `RUN_RES=1280x720 ue_slot.sh run_game.sh -SmokeShot=<abs> -SmokeShotFrames=3000 -SmokeQuitAfter=600` (load ~47). Shot written 03:46, 1280x720, again "Preparing Textures (1)" on black, no Ella. Discarded, no panel. The shot also landed within seconds of the game starting, so the frame counter or shot timing does not wait the way the flag implies. Verdict: env/smoke-shot, not the art. Not retrying.
Blocked until screenfix ships a shot that waits for texture streaming and keeps Ella alive. Then: up-open panel, shield R3, closed R3. No paint, no spend (15.08 of 33.82).

## Round 33 (Nov 13 late): merged main e99e1856 (screenfix ready-shot wait), capture relaunched
Finished the pending artslots merge (ArtSlotTests.cpp conflict, took main's version, not my lane). Main had nothing newer. Relaunched the up-open capture
with the ready-shot wait: `-SmokeShotFrames=30` counts frames after shaders, textures and a live Ella are ready (log /tmp/artella_cap_ready.log). No paint, no spend (15.08 of 33.82).
Next: if the shot shows Ella, run the up-open context pair and panel; then shield R3 and closed R3.

Round 33 result: the ready-shot capture landed (05:51, 1280x720, `-SmokeShotFrames=30`). No "Preparing" text any more, but the frame is black with only the HUD clock: no Ella, no ground, no sky.
Ready-wait passed (so shaders, textures and a live player were reported ready), yet the world draws nothing. run_game.sh keeps no game log under Saved/Logs, so I cannot see SMOKE_SHOT_READY, the map or the camera. Verdict: smoke/screenfix lane (world not rendered in the shot, or camera not on Ella), not the art.
Ask for screenfix: keep the game log from run_game.sh, and check why a ready shot shows only the HUD. Not retrying the same command. Up-open still lacks only `context`. No paint, no spend (15.08 of 33.82).

## Round 34 (Nov 13 late): merged main and artslots, nothing new; blocked on request #4
Nothing newer on main or artslots. The only capture (05:51) is HUD-only. No paint, no panel, no spend (15.08 of 33.82). Wrote request #4 (ready shot draws no world, keep the game log). Stopped: only the smoke/screenfix lane can fix it.

## Round 35 (Nov 13): merged main 642dfc82, rebuilt, frame-600 capture draws the world but Ella is not in frame
Merged main (clean), `build exit: 0` at 642dfc82. Capture `-SmokeShotFrames=600` at 1280x720 landed (07:21): world, Keeper parts, clock, shots now draw (artslots works).
Ella is not usable: at most a tiny figure at the top edge (~x255,y28) inside a dark column; the middle and bottom are empty grey. No SMOKE_VIEW line is reachable (run_game.sh keeps no game log), so `ella_in_frame=1` is unconfirmed and I treat it as 0.
No context pair, no panel, no paint, no spend (15.08 of 33.82). Shield R3 and closed R3 not started (need a context pair).
Ask (smoke/screenfix lane): keep the run_game.sh game log so SMOKE_VIEW can be read; get Ella on screen at the shot. Not retrying the same command.

## Round 36 (Nov 13): screenfix log works, Ella is in frame but tiny; up-open context pair judged and fails 2 of 3
Merged main 39c69db9, `build exit: 0`. Capture `-SmokeShotFrames=600` (1280x720), kept log `Saved/Logs/runs/run-20261113-155226-79237.log`:
`SMOKE_VIEW map=L_Graybox ... ella=1 ella_px=256,29 ella_in_frame=1 ... w=1280 h=720`. Ella is in frame, near the top edge, about 12x35 px (the Idle `_PH` flipbook).
Panel round 7 (auto crop): the locator cut the lilac placeholder blocks and Keeper parts, not Ella (critic: "X is not Ella at all"). Locator defect on a tiny figure, not the art. Also `verdict` rejected the panel
(panel.json stores an absolute `ours`, the keys a relative one); worked around in /tmp only.
Hand crop: native pixels, rect x206 y0 100x130, no upscaling. Context pair, 3 fresh sessions, calibration 6/6 valid: ours won 1, the key art won 2.
Gap: Ella is a tiny soft smudge in the game, no etched line, mask or terminal readable. Reference and quality-bar pairs: ours or SAME in most sessions, as before.
Verdict: ours/scale. At this size (12x35 px of 1280x720) no paint passes a context pair against key-art Ella. Not shipped, no import.
Shield R3 and closed R3 not painted: they would hit the same context result, so no spend (15.08 of 33.82).
Ask (lead): Ella's in-game scale (a game-side or art-slot size) or accept a context pair against a sprite-sized key-art crop; also fix `verdict` abs/relative `ours`.

## Round 37 (Nov 13): lead order, Ella as the study's small dark figure; idle imported
- Script `tools/build/assets/art_ella_silhouette.py` (numbers only, no paid call): takes the stand-in sheet the slot draws, keeps its layout
  (idle 6x4, hurt 24x1, down 6x4, same cell aspect within 0.3%), downsizes cells to 160 px tall (the slot has no mips; 654 px cells aliased),
  tones the figure into the study's dark warm range (measured on the study: darks 19,18,16, mids 44,36,31, lights 123,95,72), and adds a gold
  rim on the up-left edges and the canopy top (#E9C46A / 245,201,141). Thin hair and scarf get no rim. Transparent outside the figure.
- Idle imported into `T_Ella_Idle_PH` (LFS lock taken by this lane). Hurt and down sheets made (pipeline/art/proof/artella/silhouette/), not imported:
  the smoke shot never shows those states, so they cannot be judged in frame yet.
- Proof: pipeline/art/proof/artella/frame/idle-silhouette-proof.png (study | before | after, windowed 640x360, same build, only the sprite changed)
  and idle-silhouette-proof-zoom.png (ArenaWidth=480 at 1920x1080; its "before" is an older build, so other parts of that frame differ).
- Read: up close the figure now matches the study's Ella (dark mass, warm rim, umbrella clear). In the real 640x360 frame she still does not read:
  SMOKE_VIEW ella_px=128,15, she sits at the top edge, about 12 px tall (study scale is about 36 px at 640x360), partly behind a light-blue block
  and over a dark column. Those are camera/frame issues for visualqa, not the sprite. No spend (15.08 of 33.82).
- Next: hurt/down import once a shot can show them; re-judge idle in the frame after visualqa moves the camera.

## Lead order (recorded Nov 13 17:08, from the gate review ../logs/review-artella.txt)
Coordinator's order (Josh, 16:05): "a small Ella silhouette that reads at the Other Realm study's scale, judged in the composed frame".
This is the lead order behind the round-37 import of `T_Ella_Idle_PH`. That import is a tracked `_PH` stand-in, not a pass:
it is treated as passed only after the silhouette is judged in the composed game frame against the study with visualqa's
`tools/build/visual_qa.py` (on main). Until then it stays imported only as the `_PH` stand-in.
- Provenance row added for `Content/UmbrellaElla/Art/Ella/T_Ella_Idle_PH.uasset` (source `ella-idle_N24_grid.png`, script).
- Committed import script: `tools/build/assets/art_ella_import.py` (wraps `import_art_candidate.py`, UnrealEditor-Cmd pythonscript).
- Devlog line corrected: up close she matches the study, in the real frame she did not read yet (was overstated).

## Round 38 (Nov 13 17:20): idle judged in the composed frame; sprite cleaned up; still a _PH stand-in
- Merged main fb2f0fdb (devlog conflict: kept both lines, ours rewritten so it does not overstate). `build exit: 0` at 8b14ccb9.
- Capture: `RUN_RES=1280x720 run_game.sh -SmokeJourney=Art/Source/Ella/frame/ella_frame_journey.txt` (Start Game play + Director's Cut route, the visual_qa screens).
- Round-37 sprite in frame: body too dark for the game's near-black sky (bg behind her ~6,5,5; study's ~50), interior mottled, body rim broke into gold flecks. Umbrella read, body did not.
- Script changes (`art_ella_silhouette.py`, numbers only, no spend): body ramp re-measured on the study's Ella at full size (p10 30,25,21 / p50 62,48,38 / lit 118,88,64),
  body floor 0.3 (no black holes), interior blur 1.6 px, all-round warm edge 0.6, body rim 0.35 (canopy rim stays 0.75),
  cell 78x106 (drawn size at 1080p; was 160 px, 10x oversampled per review; aspect 0.7355 -> 0.7358). Idle re-imported via `art_ella_import.py`; hurt and down sheets regenerated, not imported.
- visual_qa.py frame (Opus judge, rubric fixed), after: dc_route FAIL 27/70, play FAIL 22/70. Ella is not in either broken list now
  (round 37's play frame listed "Ella clipped at the top edge, barely visible"). Broken items are other lanes': flat brown platform and floor bars,
  the beige light-shaft bar onto Ella, a solid red enemy rectangle, the unkeyed oversized Keeper owl, no islands.
- Verdict under the lead order: NOT passed. The composed frame fails, and Ella is about 0.6x the study's size (55 vs 92 px at 720p; request #5).
  T_Ella_Idle_PH stays imported only as the tracked _PH stand-in.
- Proof: pipeline/art/proof/artella/frame/r38-composite-dc_route.png (study | before | after; before and after are different route moments, same journey),
  r38-zoom-before-after-study.png (Ella zoomed). Judge records kept in ../logs/artella-judge-records/ (not committed: visualqa's folder).
- Spend: none this round (15.08 of 33.82). OpenRouter/fal not used: the gap was tone and noise, fixed by numbers.
- Next: re-judge when the frame's other broken items and Ella's scale are fixed; then the four state pieces (up-open, attack, shield, closed).

## Round 39 (Nov 13 20:05, lead order URGENT): approved Ella idle grid restored
- `T_Ella_Idle_PH` re-imported from `pipeline/art/proof/standins/ella-up-open/Ella_idle_N24_grid.png`; sha256 checked =
  approvals.json `ella-up-open` b128aec4 before import (`art_ella_import.py` now refuses other bytes). Same importer and settings
  as a06bcc9a (import_art_candidate.py: TC_EditorIcon, UI group, no mips, sRGB, clamp; strings identical to a06bcc9a's uasset).
  Embedded FileMD5 3cbb50e5 = md5 of the approved PNG. 6x4 layout, 2886x2616 (cell 481x654); the presenter derives the cell
  aspect from the texture (ArtSlot::CellAspect), so no code change; scale code untouched.
- The dark silhouette stays a proof file only (pipeline/art/proof/artella/silhouette/).
- Proof: pipeline/art/proof/artella/frame/r39-approved-dc_route.png and r39-approved-play.png (study | before | after, same build
  5e5ce716, only the uasset swapped, RUN_RES=1280x720 journey). After shows the approved Ella untinted.
- Capture note: without `-SmokeJourneyOut=<abs path>` the journey writes to `/joanmiguel/...` (out= path loses `/Users`), so shots
  fail to save. Not my lane (Smoke); worked around on the command line.

## Review round (Nov 13, ../logs/review-artella.txt): gate tooling in this lane, guard evidence
- Lane record: the gate tooling files `tools/build/gate.sh`, `tools/build/lane_precheck.sh`, `tools/build/gate_clean_state.sh`,
  `tools/build/gate_state_selftest.sh`, `tools/build/approved_art_guard.py` and `tests/test_approved_art_guard.py` are in this lane
  by lead order (Nov 13 ~20:05: Josh's orders for clean player state, full precheck output, and the approved-art guard). They are
  carried here because the lead cannot commit to main directly.
- Guard narrowed: `CODE_WORDS` now flags only calls / assignments that tint, recolour, hide or swap a texture or its material
  (Set{Vector,Scalar,Texture}ParameterValue*, SetMaterial*, SetTexture*, SetBrush*, SetSprite*, SetFlipbook*, SetColorAndOpacity,
  SetRenderOpacity, SetVisibility, SetHiddenInGame, SetActorHiddenInGame, *Tint*(...), *Tint*/Opacity = ...), still within 3 lines
  of the slot's texture name, visual id or piece id. New tests: plain gameplay near `T_Ella_Idle` (velocity, `bEllaVisibleToOwl`,
  `DebugColor =`) passes; `SetVectorParameterValue(TEXT("Tint"), ...)` next to `T_Ella_Idle_PH` fails.
- `art_ella_import.py`: a missing approval now stops with `no approval found for <piece> in pipeline/art/approvals.json`, not `None`.
- `T_Ella_Idle_PH` stays the approved bytes (unchanged this round).
- Not addressed this round (not in the lead's list): `lane_precheck.sh` dropped `head -N` caps (full precheck output was Josh's
  order); `gate_state_selftest.sh` default worktree path.

### Gate evidence
commit=02c32af0 base=origin/main d812ba29 host=mac (no Unreal run needed: Python only)
```
$ python3 tools/build/approved_art_guard.py check --base origin/main --head HEAD
APPROVED_ART PASS: 4 approved texture(s) guarded, none replaced, recoloured or hidden
$ python3 -m unittest tests.test_approved_art_guard
Ran 15 tests in 9.574s
OK
```

- Nov 13 21:34 (lead): gate run on dad3b703 failed at the final merge only: the main checkout held uncommitted copies of this lane's gate tooling (git refused to overwrite them). Copies removed by rename between runs (saved in the lead scratchpad); re-gating on this commit.

## Lead order (Nov 13 22:20, Josh): Keeper fight music fix, carried in this lane (the free lane the lead may use). Not art.
Causes found: (1) MusicContest/MusicDesperation had no bus event (Event Count); (2) MusicTitle was routed on ModeSelected,
which BeginRun broadcasts after Start Game has already begun the Keeper fight, so the title re-took the music; (3) the three
fight tracks were imported as `/Game/UmbrellaElla/Audio/<Id>/<Id>` (sndworld_import.py), not `SW_<Id>_00`, so LoadTakes found nothing.
Fix: `pipeline/audio/build/cue_table.py` routes (regenerated `UmbrellaCueData.h`): PhaseStarted wings/mechanisms -> MusicContest,
PhaseStarted clock -> MusicDesperation (sound-list.csv line 135 "Keeper fight music, clock"; GDD SH1.0 line 283 OWL-06 "Phase 3 clock");
MusicTitle has no bus route (launch + Title/Credits via FFlowRules::MusicFor). Cue subsystem: music changes cross-fade over 0.5 s
(audio-rules.json music.fade_s_max) on two reused components; looped music rows fall back to the `<Id>/<Id>` asset.
Tests (all PASS, 117 in Audio+Feedback+Flow+SoundLabel): UmbrellaElla.Audio.FightMusicRoutes,
.Audio.World.FightStartCrossFadesTitleToContest, .ClockPhaseSwitchesToDesperation, .CreditsAndTitleReturnToTitleMusic,
.TitleCrossFadesBackFromFightMusic. Flow lane test ModePickKeepsTitleMusicWithoutRestart updated: Start Game begins the fight,
so it now expects MusicContest with the title fading out (never restarted or doubled).
Audio log (test run, LogUmbrellaElla):
  AUDIO: music name=MusicContest from=MusicTitle take=MusicContest fade_s=0.50
  AUDIO: music name=MusicDesperation from=MusicContest take=MusicDesperation fade_s=0.50
  AUDIO: music name=MusicTitle from=MusicContest take=SW_MusicTitle_00 fade_s=0.50
Open for Josh: (a) sound-list.csv names MusicIntro for the wings phase; per the lead order the fight opens on MusicContest and
MusicIntro stays unused. (b) The three fight tracks have no record in pipeline/audio/critic (commit 161dd4c claims a pass), so
audioimport skipped them; they play from the older sndworld import. Not run: packaged/in-game listen.

## Lead order (Nov 13 23:43, coordinator for Josh): Level 07A walker test fix, carried in this free lane. Not art.
`UmbrellaElla.Level.World.RealInputWalkerAtZ450StopsAt07ALowSolid` failed on main. The game was wrong, the test right.
- Measured (test alone, main dab58cfa): solid x 11482..11674 z 367..518 is there at frame 1, but the walker (z 440..454)
  passed it, best_x 12514, CP2 at t=22.9 s. Asserted: stop at x 11464.5, cp 1.
- Bisect over main, first parent: 28656fe6 PASS, b377a494 PASS, 13534964 PASS (clean retest), 991b3eb7 FAIL (first bad),
  dd37d809 FAIL, 44a50099 FAIL. 991b3eb7 (artscene) imported `T_WorldSolids_PH`; with a picture present
  `UWorldArtSubsystem::Refresh` ran `ArtSlot::Apply` on the block's own collision mesh, which makes it a NoCollision plane.
  Not the 1.5x figure scale or camera framing.
- Fix (`Feedback/Background/WorldArtSubsystem.cpp`, d88698c3): the block keeps its box and collision (hidden), the picture
  draws on a child plane `BlockArt`. No art changed, no threshold changed.
- After: walker stops at x 11464 for t=20..60 s, block_ahead=Block, cp 1.
- `Feedback.World.ArtSlotWorldPieces` tightened (it skipped blocks already without collision): all 17 colliding blocks must
  still collide with the picture on a separate plane. Break-proven: 0/17 without the fix.
- Runs on d88698c3: Level suite PASS 30/30; full UmbrellaElla suite PASS 457/457 (the gate batch ed61ceef counted 458;
  it held commits not on main); module_check 0, manifest_check 0.
- Lane note: WorldArtSubsystem is the visuals lane (artscene); carried here by lead order.
