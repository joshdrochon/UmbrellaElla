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
