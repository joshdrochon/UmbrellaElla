# artfx status

## Slice 1 (Nov 12): VFX wiring, light policy, light shaft, placeholder sheets
Lane note: the brief's `Feedback/VFX/**` is the existing `Feedback/Vfx/` folder (case-insensitive disk). See `docs/build/requests/artfx.md`.

### Built (code)
| Rule ID | What | Where | Tests |
|---|---|---|---|
| VFX-02 | 48 effects in one table, each with its sheet, layer, timing and light; sheets imported as textures and shown on a camera-facing quad through `M_VFX_Sheet_PH`; a stand-in shape when a sheet is missing | `Feedback/Vfx/VfxCatalog`, `VfxSheetVisual`, `Art/Source/VFX/import_vfx.py` | `Feedback.VfxCatalogRules` |
| VFX-03 | Small Blasts release/travel/impact/fade; Streamed Blast startup/sustain (sized to the beam hitbox)/contact/stop; Twin Stars two release anchors and two heads; Needle channel/pulse/sliver/pierce and protected contact. Driven by the bus (`ProjectileSpawned`, `ProjectileContact`, `UmbrellaConfigChanged`) and the live beam actor | `UUmbrellaVfxDirectorSubsystem` | `Feedback.World.VfxWeaponWiring` |
| VFX-05 | Warning/strike/recovery for talon and the three casts; gust warning/release/travel/expiry; clock double beat (one per beat), opening/cover; part hit/break; stun, slow, exposed eye, blackout, restoration; departure. Read from the fight model each step, anchored on the model's head/claw/gust/clock positions. Safe pause and recovery start no damage-looking effect | `KeeperVfxRules`, director | `Feedback.VfxKeeperRules`, `Feedback.World.VfxKeeperWiring` |
| VFX-07, VFX-08 | Per-effect additive light overlay (sprites stay unlit) plus an unshadowed point light; local radius, effect colour, fades and leaves with the effect; on/off switch. This is the default of the open row D-new-sh10-vfx-lighting; the decision is still open | `VfxLightPolicy`, director | `Feedback.VfxLightAndShaftRules`, `Feedback.World.VfxIlluminationOnOff` |
| NAR-05 | Light shaft through Ella's position; umbra under the open umbrella follows her; folding closes the gap in 0.15 s and light passes below her. Looks only | `LightShaftRules`, director | `Feedback.VfxLightAndShaftRules`, `Feedback.World.VfxLightShaftAndUmbra` |
| VFX-11 | Acceptance in tests: each event shows its effect once, at its anchor, stops on retry/defeat/phase start; no double with the shared subsystem; concurrency cap and flash gap | all of the above | the five tests above |

No gameplay timing, collision or state is written by any of it (tests check the shot velocity, Ella's and the Keeper's position stay untouched).

### Art (all tracked `_PH`, nothing shipped)
- 28 sheets (8 x 1 cells of 128), Blender 5.2.1, `Art/Source/VFX/vfx_sheets.py` -> `Art/Source/VFX/Raw/*_PH.png`, imported to
  `Content/UmbrellaElla/Art/VFX/T_VFX_*_PH` with `M_VFX_Sheet_PH` and `M_VFX_Spill_PH`. Provenance: 28 rows, origin `placeholder`.
- No art loop pass exists for any sheet. `pipeline/art/references.json` has no judge element for these effects (request 4), so the
  official panel cannot open for them.
- Blind critic probe (one fresh Sonnet session per pair, Twin Star head against the `wand-shot` element, which describes the same gold star head):
  | Round | Change | Reference pair | Quality-bar pair | Calibration folders |
  |---|---|---|---|---|
  | 1 | flat emissive shapes, soft glow | reference wins: "soft airbrushed glow, no ink silhouette, etched line or paper grain" | not run | 2/2 right |
  | 2 | ink outline behind each shape, hatching engraved as ink, paper grain, no glow disc | ours wins | ours wins | 4/4 right |
  Round 2 is 1 session per pair, not a panel, so it is not a pass. The quality-bar reason faulted the bar image for being a concept
  sheet with a wand, which is a content reason, not a finish reason: I do not count that pair.
  The ink outline + engraved hatch + grain recipe is what moved the reference pair; it may help the artshots lane.

### Not done / not run
- VFX-11 evidence the GDD asks for and this lane could not produce: gameplay-scale screenshots or video, the illumination on/off
  capture, performance profile on target hardware, editable-source change -> reimport test on a device. Headless runs are `-nullrhi`.
- Sheet orientation on the quad (not mirrored, upright) is checked only by a rotation test, not by eye in a rendered frame.
- Art loop pass for any sheet (blocked by request 4 and by the `context` pair needing an in-engine capture).
- VFX-10 numerical budgets stay OPEN in the GDD; the cap (40 live effects) and flash gap (0.34 s) are this build's values.
- Reduced-flash toggle is not wired from Settings to the director (request 2).
- Blackout veil opacity (0.55) is my value; the GDD gives none.

## Slice 2 (Nov 13): first Gemini-painted effect, Twin Star head (VFX-03)
- Prompt reviewed by a fresh Art Director session before the call (`Art/Source/VFX/Paint/TwinStarHead/prompt-review.md`); its corrected block is `prompt.final.txt`. Applied: side view, head plus short tail, 8-point faceted star, named palette colours, shell/shadow, no rotation. One call, 3 Pro 21:9 2K, $0.14 (shared counter 1.81 of 33.82).
- Cut: clean + frames (4 frames, spread 16.8% by design: frame 2 is the bright, larger beat). `art_ref_check` wand-shot PASS 0.53-0.63 (min 0.334).
- art_check colour rules FAIL on a single frame (off_band 0.24, on_palette 0.62, accent_area): these are full-frame rules, and bronze/amber shading counts as off-band. Same rule/style disagreement imagegen logged. Not fixed here.
- Blind probe, 1 fresh Sonnet session per pair, not a panel: reference pair ours wins (calibration 2/2 right); quality-bar pair ours wins but that session missed calibration A, so it does not count. No motion or context pair run, so no pass. Not shipped: stays a `_PH` slot, no `.artloop.json`.
- Ours vs model: panel-coloured green boxes appeared behind each cell (prompt said "green identical in every cell"; model drew darker cell panels). The HSV key removed them, but drop that sentence next time. Glow on frames 2 and 4 spills onto the panel; keyed edge looks clean.
- Left: panel of 3 per pair, motion pair, in-engine context capture; paint release/impact/fade and Keeper warning/strike with the same method; import to `Content/.../Art/VFX` only after a pass.

## Slice 3 (Nov 13): blocked, no new paint
- Merged main (d3cf6ee5). Re-checked request 4: `pipeline/art/references.json` still has no judge element for the VFX pieces, and `art_loop.py pieces --card artfx` lists none. `wand-shot` belongs to the artshots lane (card 0.10b).
- So no blind panel can open for any artfx piece and nothing can ship. More Gemini calls would only add `_PH` candidates that cannot pass, so I made none (spend stays 1.81 of 33.82).
- Verdict: "check/source gap, not the work". Needs the lead to add elements (spell-small-blasts, spell-stream, spell-twin-stars, spell-needle, keeper-warning, keeper-strike, clock-beat, light-shaft) with refs and calibration, or to rule that artshots' `wand-shot` pass covers the four spell heads.
- Once that lands: paint release/impact/fade and Keeper warning/strike with the Twin Star method (drop "green identical in every cell" from the prompt), run a panel of 3 per pair plus motion and in-engine context pairs.

## Slice 4 (Nov 13): inventory merged, refs wired, second painted candidate
- Merged `origin/area/artinventory`: the 26 `vfx-*` judge elements are in `pipeline/art/references.json`. They still did not list for `artfx` (`art_loop.py pieces` reads the references' `cards`), so I added `artfx` to the `cards` of the 19 refs those elements use (additions only). `art_loop.py pieces --card artfx` now lists all 26 `vfx-*` pieces (plus other lanes' elements that share those refs).
- Gold impact (`vfx-gold-impact`): prompt reviewed by a fresh Art Director session (`Art/Source/VFX/Paint/GoldImpact/prompt-review.md`, `prompt.final.txt`), one 3 Pro 21:9 2K call, $0.139 (shared counter 4.14 of 33.82). Raw `Raw/strip.png`, keyed `keyed.png`.
- Verdict on the output, "ours: prompt": the word "cell" made the model draw dark panel boxes with black borders again (second time); the key leaves the 1 px borders, and frame 2 reaches across its box. Next prompt: no "cells" or "gaps": ask for four bursts on one flat green field, spaced by a stated fraction of width, and cut frames by fixed geometry.
- Not judged, not shipped: no panel run. Reason: every full round needs the `context` pair (an in-engine capture newer than the piece, `Saved/Logs/pipeline/*-shot.png`), and this lane has no rendered capture (headless `-nullrhi`). Without it `verdict` reports "reference" by rule, so no piece can pass from here. Needs the lead or QA to produce a smoke capture after the sheets are imported.
- Spend stays tiny; I made no further calls because more candidates cannot pass without the capture.

## Slice 5 (Nov 13): own in-engine capture, prompt fix, painted gold impact v2, full panel round
- Merged main (art-image-model "Context capture"). Prompt fixed as the lead said (no "cells"/"gaps": four bursts on one flat green field, centres at 1/8, 3/8, 5/8, 7/8 of the width): `Art/Source/VFX/Paint/GoldImpact/prompt.v2.txt`. One 3 Pro 21:9 2K call, $0.140 (shared counter 4.56 of 33.82). Result: clean bursts on flat green, no dark boxes ("ours: prompt" is fixed).
- Cut by fixed geometry (`Art/Source/VFX/Paint/cut_strip.py`, Blender): key, four bursts split at the emptiest columns near 1/4, 1/2, 3/4, one common scale, centred in 128 px cells, each frame doubled to 8 cells. `Paint/GoldImpact/sheet.png`; provenance row added. Installed in the `_PH` slot (`Raw/VFX_GoldImpact_PH.png`, reimported `T_VFX_GoldImpact_PH`; stays a tracked `_PH`).
- In-engine capture: new `-VfxDemo=<EffectKey>` flag in the director (replays the effect beside Ella; art capture only) writes a scene-only shot to `Saved/Screenshots`. The smoke `-SmokeShot` window read-back is black for the 3D scene on this Mac (only the Slate UI), and the run needs `-SmokeQuitAfter=90` (frames run at about 0.1-0.5 fps while shaders compile, so game time is slow). Command: `tools/build/run_game.sh /Game/UmbrellaElla/Maps/L_Graybox -VfxDemo=SmallBlastImpact -SmokeQuitAfter=90`, then copy `Saved/Screenshots/MacEditor/ScreenShot.png` to `Saved/Logs/pipeline/vfx-gold-impact-shot.png`. The capture shows the burst at game scale.
- Panel round on sheet.png (9 fresh Sonnet sessions): verdict=reference, calibration 3/9, score 0.526 (art_ref_check PASS, screen_check PASS), art_check colour rules FAIL (on_palette 0.55, off_style 0.32, off_band 0.15), no pass.
- Triage: not the sheet alone. (1) art_check's colour rules are full-frame rules; they fail any gold sprite with bronze/amber shading (same defect as Slice 2). (2) Critic sessions miss calibration folder C (a clearly different pair) and answer SAME: 3/9 calibrated. (3) The context pair puts a near-black graybox capture against the key art, so it judges the scene, not the burst. Verdict: "check defect", needs the lead (a calibrated-session count, a sprite colour rule that reads the effect only, a context pair for effects). Not loosened by me.
- Left: same method for the other 25 `vfx-*` pieces; none is run, because each would stop at the same three checks.

## Slice 6 (Nov 13): merged main, still blocked
- Merged main (b43ca5ae). Only change touching art_loop was the UI-screen context rule; the three check defects in Slice 5 are unchanged. Written up as request 5 in `docs/build/requests/artfx.md`. No paint, spend stays 4.56 of 33.82.

## Slice 7 (Nov 13): merged main and origin/area/artslots, still blocked
- Re-checked the three defects of request 5 on main: `art_check.py` still has no sprite/effect colour mode, `art_loop.py` still counts only fully calibrated sessions with no re-draw, and the context pair is unchanged for effects. artslots brought nothing for them.
- No paint, spend stays 4.56 of 33.82. Blocker is only the lead's: request 5 in `docs/build/requests/artfx.md`.

## Slice 8 (Nov 13): merged main and artslots (both up to date), still blocked
- Main (e90abdd5) has not moved since slice 7. `art_check.py` has no sprite/effect mode, `art_loop.py` has no re-draw for uncalibrated sessions, the context pair is unchanged. Request 5 stands. No paint, spend stays 4.56 of 33.82.

## Slice 9 (Nov 13): candidates moved to pipeline/art/proof/artfx
- Per art-image-model "Where candidates live": `Art/Source/VFX/Paint/*` (TwinStarHead, GoldImpact, cut_strip.py) is now `pipeline/art/proof/artfx/`. Provenance, request 5 and the critic json paths updated. Earlier slice text above keeps the old paths.
- `VFX_GoldImpact_PH.png` and `T_VFX_GoldImpact_PH.uasset` restored to the generated placeholder (the painted sheet is a candidate, not shipped). `Art/Source/VFX` now holds only tracked `_PH` sheets.
- Merged main. Still blocked on request 5; no paint.

## Review fix (Nov 13, review-artfx round 1)
- Reverted the `cards` additions in `pipeline/art/references.json` (outside the lane); the exact diff is request 6 in `docs/build/requests/artfx.md`. The slice 4 line above describing the edit as done is superseded.
- `-VfxDemo` is compiled out of shipping builds (`#if !UE_BUILD_SHIPPING`, header and cpp), `StepDemo` returns early with no key, and its timer is wall time. Rule test `UmbrellaElla.Feedback.VfxDemoRules`.
- Not run: UE build and the new test (the lead's slot).

## Review fix round 2 (Nov 13)
- Lead ruling: the `cards` additions in `pipeline/art/references.json` (19 refs, additions only) are in-lane per `docs/build/art-image-model.md` "Shared references" on main. Restored; request 6 withdrawn. `art_loop.py pieces --card artfx` lists the 26 `vfx-*` pieces again.
- Demo test `UmbrellaElla.Feedback.VfxDemoRules` kept (uses `FName(TEXT(...))`); `StepDemo` early-returns with no key and times on wall time.
- Ran: build exit 0, `UmbrellaElla.Feedback` 30/30 PASS, module_check 0 problems. Demo timer uses `FApp::GetCurrentTime()` (wall time, non-shipping art capture only) because rule N flags `FPlatformTime`.

## Slice 10 (Nov 13): check defects fixed on main; gold impact re-run, still no pass
- Merged main and artslots. Request 5's three defects are fixed on main (effect colour mode, redraw of uncalibrated sessions, cropped context pair). Request 5 is closed.
- Colour: `pipeline/art/proof/artfx/snap_palette.py` snaps each opaque pixel of a painted sheet to the nearest effect-palette colour (our post-process, alpha kept). `GoldImpact/sheet.snap.png`: `art_check --effect` PASS (on_palette 1.0, off_style 0, off_band 0); the raw sheet failed (0.73 / 0.18 / 0.018). art_ref_check 0.527 PASS, screen_check PASS.
- Capture: `-VfxDemo` (non-shipping) now hides Ella and the Keeper stand-ins and puts a paper-coloured backdrop behind the effect, so the piece locator no longer picks their black. Command adds `RUN_RES=1920x1080`. The star shows at game scale (about 40 px) on paper when the shot lands on its bright frames.
- Panel on the snapped sheet (3 sessions per pair, calibration 9/9): reference pair ours; quality-bar pair flipped between rounds (round 3 ours, rounds 4-6 reference: "thin uniform spikes, little ink weight, no value structure, sticker-like"); context pair reference in rounds 4-6 because the capture is timing-dependent (round 5 showed only a black dot, round 6 only the faded last frame).
- Verdicts: context capture "ours: capture timing" (the shot fires once the effect is live, on wall time, but game time crawls); quality bar "work" (the painted burst is thin: next paint asks for heavier ink silhouette and value steps).
- Next: pin the demo to one frame (hold frame 3 for the shot), repaint gold impact with a heavier etched look (one call, prompt reviewed by a fresh Art Director session), rerun. Spend stays 4.56 of 33.82. `VFX_GoldImpact_PH` stays the generated placeholder; nothing shipped.
- Ran: build exit 0, `UmbrellaElla.Feedback` 35/35 PASS, module_check 0 problems.

## Slice 11 (Nov 13): split lane (10 pieces), flash drafts for all of them, import queued
- Lane now: vfx-gold-fade, gold-impact, gust, gust-puff, light-shaft, light-spill, umbra, blackout, blocked, slow. Merged main.
- Demo capture holds one sheet cell (`DemoHoldFrame`, non-shipping) so the shot cannot land on a faded frame. Build exit 0.
- Prompts reviewed by fresh sessions before any call (`prompt-review*.md` next to each). Drafts on `gemini-3.1-flash-image-preview` 1K (about $0.067 each, 11 calls, no 3-pro yet). Spend counter 17.26 of 33.82 at last call (shared).
- Sprite pieces (strip on green, `cut_strip.py`, `snap_palette.py`): GoldImpact v3 (heavier ink, value steps: a clear step up from v2), GoldFade, GustPuff, Gust, Blocked. `art_check --effect` PASS on all five.
- Veil pieces (2 x 2 grid on flat black or white, new `cut_veil.py`: brightness or darkness becomes alpha): LightShaft, Umbra, Blackout, Slow, LightSpill. `art_check --effect` PASS (after palette snap for the light ones). Light shaft needed a second draw (frames drifted); fixed with a "same place in every panel" sentence.
- Light spill has no texture slot (it is the `M_VFX_Spill_PH` material), so it has a candidate image but no in-engine slot yet; wiring it needs an `import_vfx.py` change.
- Slow: the GDD slow cue is local to the clock bezel; the full-frame overlay needs a placement check in engine (flagged by the prompt reviewer).
- Not done: in-engine import of the 9 sheets into the `_PH` slots (editor import waits for a free Unreal slot; first attempt used a relative script path, fixed), captures, panel rounds. Nothing shipped; every slot stays a tracked `_PH`.

## Slice 12 (Nov 13): video method, gold impact (one paid call)
- Merged origin/area/artvideo (tools/assetgen.py video, tools/build/video_to_strip.py) and main. The "Animated pieces from video" note is not on either branch yet; I used the area brief and the tool help.
- Still = frame 2 (full flare) of gold impact v3, cropped 640x360 and scaled to 1280x720, neighbour bursts painted green (`GoldImpact/Video/input.png`, provenance row added). One fal Veo 3.1 Fast call, 4 s, seed 7, $0.60 (`Video/gold-impact.request.json`); shared counter 19.27 of 33.82. Only one call fits what the shell cap allowed at the time; the other 9 pieces are not animated.
- Result: the motion is right (flare, blades fly out, sparks scatter and fade). `video_to_strip.py` fails ("no figure after keying") on effects: it anchors on a figure's feet and the clip ends on empty green. I cut the strip by hand from the keyed frames (frames 0,7,8,9,10,11?,12,14,17 of 8 fps; 8 cells of 128, camera is fixed so no registration): `Video/GoldImpact_video_strip.png`, palette-snapped `.snap.png`. `art_check --effect` on the snapped strip PASS (1.0 / 0 / 0).
- Defects, not fixed: the star in the video is larger than the frame, so the flying blades are clipped at the cell edge; the last 3 cells are near empty. No jitter check (no effect mode in frame_register), no blind panel, no art_pass_verify record. Nothing shipped; the slot stays `_PH`.
- Tool gap for the lead: video_to_strip needs an effect mode (centre anchor, no figure required, skip empty frames). Next: prompt for a smaller burst (about a quarter of the frame), regenerate (another $0.60), then panel.

## Slice 13 (Nov 13): merged main; gold impact round 7 not counted
- Merged main (resolved a `tools/assetgen.py` conflict: kept `video` and `batch`). Slot holds GoldImpact v3 snapped. In-engine capture taken (`-VfxDemo=SmallBlastImpact`, 1920x1080): `Saved/Logs/pipeline/vfx-gold-impact-shot.png`. `art_loop.py panel` prepared round 7 (`GoldImpact/round7`, 9 sessions).
- My critic fan-out script had a bug (stray `require`): the nine sessions ran but their answers were not written to the `.answer.md` files and could not be tied to folders. Several sessions also used Bash, so blindness is unproven. No `verdict` was run; round 7 does not count. Read by eye, the context pair (capture) still shows a tiny smear at game scale, the same "ours: capture timing/scale" defect as slice 10.
- Next: rerun round 7 with a clean fan-out that writes each answer to its own file and allows Read only, then `art_loop.py verdict`. No paint, spend unchanged. Nothing shipped; all slots stay `_PH`.

## Slice 13b (Nov 13): gold impact round 7 counted, no pass
- Reran the nine critics clean (Read and Write only, each answer in its own `.answer.md`), fixed `round7/panel.json` `ours` to the relative path the keys use, ran `art_loop.py verdict`.
- Result: `verdict=reference pairs=context:reference,quality_bar:reference,reference:ours`, calibration 8/9, checks pass (art_ref_check 0.552, screen_check, art_check --effect). Reference pair is ours; quality-bar and context pairs still go to the other image.
- Triage: context = "ours: capture" again (tiny burst at game scale in a paper-only shot; the critics' gap text describes a clock UI, so the pair is not judging the burst). Quality bar pair, the bar image is a sundial-casters picture, not a burst: possible check defect (bar not an effect image for vfx pieces); needs the lead to confirm which bar image applies. Not loosened by me.
- Next: fix the capture (crop to the burst, larger), and ask the lead about the quality bar for effect pieces. Nothing shipped; no paint, spend unchanged.
