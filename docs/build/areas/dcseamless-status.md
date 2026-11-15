# dcseamless status

## Nov 14 00:10 (Opus): DC route seams, round 1
Capture: 45-shot sweep of the DC route, start to Keeper (journey in the lane scratch, `route 9 1.2` steps + `routeassist 1..4`,
1280x720 offscreen). Measured with tools/build/assets/art_scene_frameseam.py (median col-to-col / row-to-row luma jump
along a whole line; a straight edge >= 3.0, painted content <= 2.9).

Seams found on main dab58cfa:
1. Route start picture's right edge (hard vertical cut, slides across the screen for the first ~3000 units):
   x 1189 -> 991 -> 793 -> 93 in shots 004-010, jump 4.9-7.1. Source: SceneArtSubsystem.cpp PanelX RouteStart + masked
   M_ArtSlot_Unlit (opacity mask, no soft edge).
2. Route end picture's left edge (hard cut before the Keeper fight): x 601, jump 3.8-4.8 (shots 033-034). Same code, RouteEnd.
3. Arena stand-in planes BackgroundFar (3840 x 1080, Z 0..1080) and BackgroundNear (Z 0..540), darkened by frame
   composition, drawn at the backdrop's own depths: horizontal edges y 53 and y 359/457 (jump 3.0-4.1) and vertical
   edges x 500 / 304 (3.6-4.9) in shots 001-010. Source: UmbrellaArena.cpp:163-164 (BuildPlaceholders).
4. Every backdrop layer wrapped every 1200 units (UmbrellaBackdropSubsystem.cpp LoopOffset): over the 22000-unit route
   the near layers jumped a quarter picture 8-10 times, so the same island and arch kept coming back. Not visible in one
   still; caught by the new continuity test (old code: 1200-unit jump per camera step).

Fix (composition only; no approved image changed):
- New M_ArtSlot_EdgeFade (tools/build/assets/art_slot_fade_material.py): translucent slot material with FadeLeft/FadeRight.
  The start picture fades its right 35%, the end picture its left 35% (SceneArtSubsystem::EdgeFades/ApplyEdgeFade).
- UUmbrellaBackdropSubsystem::HideArenaStandIns: the arena's flat planes hide once a backdrop layer draws art.
- Layers no longer wrap: one continuous slide across the route (LayerOffset), every parallax scaled by the same factor so
  the fastest layer crosses its 4800-unit picture once without its edge showing (depth order kept).
Measured (route shots 001-034): before 14 of 34 fail, worst 7.1; after 0 of 34 fail, worst 2.4.
Keeper-fight shots score 3.0-3.3 at x 888 both before and after: the Keeper's straight hanging chains, not the backdrop.
Tests: UmbrellaElla.Feedback.BackdropSeamless, UmbrellaElla.Feedback.World.BackdropSeamless (Feedback 65/65 PASS),
tests/test_art_scene_frameseam.py (6 OK). Proof: pipeline/art/proof/dcseamless/composite-{005,010,033}.png.

## Nov 14 00:25: round 2
- Precheck: `ApplyEdgeFade` returned bool (naming rule) -> void.
- visual_qa run on a93d46c3 (no baseline compare): `play=41 dc_route=44 keeper=32` (main dab58cfa baseline 43/45/42).
  dc_route: no backdrop item (floor bar, thin platform, rope: level/Ella, not mine). keeper: "dark rectangular panel
  top-left with hard straight edges": the arena stand-in planes showed again by the Keeper fight (hidden once, at the
  first tick with art). Fix: HideArenaStandIns every tick. Recapture (Saved/VisualQA/dcs-r2): rectangle gone; frameseam
  keeper 3.1 at x888 = the Keeper's hanging chains (main's frame scores the same), dc_route 1.5, play 3.1 at the owl's chains.

## Nov 14 01:10: the DC route jolt (Josh played main b79af92a: "pressing Space to move forward jolts the view")
Real input, offscreen 1280x720 at 30 fps: journey DC -> `route 9 10` (D held, Space/E tapped) -> `hold SpaceBar 2` -> `route 9 6`,
per-frame trace with `-BackdropTrace` (BDTRACE: rendered camera X, the X the backdrop scrolled to, Ella X/vx, each layer's
on-screen offset). (Traces kept out of the repo; numbers below. Re-run: the journey above with -BackdropTrace, grep BDTRACE.)
Causes:
1. Camera lead snap (UmbrellaLevelDirector.cpp Tick -> StepFollow(X, Sign(vx)) -> LevelCatalogue ScrollCentreX): the lead
   (+-0.25 x 1920 = 480) followed the SIGN of Ella's X velocity instantly. Every stop (flap, key release; vx 0) moved the view
   480 back in one frame, every restart 480 forward. Before: per-frame camera step -480..+960, 139 frames with a step change
   > 15 units, camera speed change p99 23516 u/s.
2. Backdrop one frame late: UWorld::Tick runs tickable objects (both backdrop subsystems) before
   PlayerController::UpdateCameraManager (LevelTick.cpp 1821 vs 1847), so layers scrolled with last frame's camera: gap
   mean 104, max 521 units; each layer's on-screen step jumped by the whole camera move (up to 1015 units).
Fix: StepCameraFollow (critically damped spring 0.25 s on Ella + lead; the lead turns at <= 300 u/s and is kept when she
stops; cuts > 3840 snap); both backdrop subsystems scroll in OnWorldPostActorTick (after the camera update).
After: camera speed change p99 63 u/s (max 751 on a 92 ms frame hitch, machine load avg 14), step changes > 15: only
the level-load placement; backdrop gap 0.00; layer on-screen step 0..-8 (sky) to 0..-99 (nearest, at the load placement).
Hide-per-tick: no measurable cost (hitches 3 vs 7 > 50 ms on a loaded Mac, at chunk spawns, none at a fixed period).
Test: UmbrellaElla.Level.CameraFollowSmooth (old follow: change 480/frame; new <= 10). 142/142 Level+Feedback+Flow+Arena PASS.
Review (gate batch 01:32, changes): lane extension recorded in docs/build/areas/dcseamless.md; cuts snap (Ella jump > 400
units per step resets the follow; test "a near respawn snaps"); trace behind !UE_BUILD_SHIPPING; TickCameraX -> RenderCameraX;
empty SceneArt Tick commented; trace files dropped.

## Nov 14 16:10: start picture edge, the floor bar, vertical wind (Josh played ffba0e20)
1. Start picture "fades into transparency": the 0.35 alpha ramp dissolved the barn island over the void. Now
   M_ArtSlot_EdgeFade eases the colour into the picture's own haze tone (sRGB 34,28,23, mean of its outer 8% columns) over
   0.2 of its width and fades opacity only over the outer 0.3 of that band (the haze). Same for the end picture's left edge.
   Seam check, real-input sweep start..CP3 (14 route shots): worst 2.2 (Keeper-fight shots 3.0-3.1 at x888 = chains, as before).
   Proof: pipeline/art/proof/dcseamless/haze-{start-001,edge-005,end-014}.png. Approved texture bytes unchanged.
2. "Trapped on the bottom track": the bar is LevelPlan's per-slot placeholder floor (not chunk-catalogue land; the GDD has
   none: WIND-03 "the bottom is lethal", no ground-running). Removed (LevelPlan.cpp). Ella is held at the bottom by the
   motor's arena-floor clamp (EllaMotorComponent.cpp:145), and nothing applies the lethal rule (IsAtPlayFloor is unread).
   Trap not reproduced with real input: from the bottom she rose 180-290 units in 1 s at 7 route positions (release, Space).
   Guard test UmbrellaElla.Move.World.BottomRisesWithinOneSecond. Proof: floorbar-before.png / floorbar-after.png.
3. Vertical wind (Josh 16:02): D-new-no-vertical-wind; LevelPlan::Build skips winds with |Z| > |X| (catalogue rows kept).
   Real input start -> Keeper, no assists: reaches the Keeper (CP1 18 s, CP3 26 s). The walker stalls at x 11464, z 450 (the
   known 07A low solid, test RealInputWalkerAtZ450StopsAt07ALowSolid) with and without vertical wind (40 s / 100+ s).
Review round (16:29): lane extension written into dcseamless.md; HAZ-25/27/34/36 set to partial in rule-status.csv
(columns authored, not placed); fade test added to BackdropSeamTests (alpha ramp <= 0.1 of the width and a haze colour: the
old 0.35 ramp fails it); the bottom-rise test is a guard (the trap did not reproduce; it passes on the old code too).
Lethal bottom not applied anywhere: handed to the owner (see dcseamless.md).
Main 1d95f1fd (fallrules) made the bottom lethal (EllaMotorComponent DefeatAtBoundary): the bottom-rise guard test
(BottomRisesWithinOneSecond) contradicted it and is dropped; with the bar gone and the bottom lethal there is no ground to be
trapped on.

## Nov 14 19:00: barn picture off the route; arch stop and arena-entry haze
Josh (6:22 PM): remove the barn picture; the clock-arch layer stops abruptly; the arena entry reads as a haze. Both were the
route-end barn picture: its left edge (haze fade) cut the layered backdrop (atmosphere arches, islands) off before the Keeper
fight (arenaentry-before.png). bg:start-end is no longer in SceneArtSubsystem::Specs; the layers already span the Keeper
fight frame (test FrameComposition.KeeperBackdropContinuous rewritten to check the layer footprints). Art bytes unchanged.
Real-input sweep start..CP3 (45 shots): every route shot < 3.0 (w02 = tutorial card). Keeper fight shots 2.9-3.2 rows at
y 204/343 (island tops), was 3.0-3.3 (chains) with the barn picture. Proof: arenaentry-after.png, route-after-w30.png.
Gate 4d0c3f99 FAIL (visual_qa play): scores rose (46/43 vs 40) but a new detector hit, "flat box" at (927,115): with the
barn picture gone, Start Game showed the atmosphere layer where the barn picture had been. The barn picture is Start Game's
backdrop (its arena sits at the route start), so its start copy is back and hides in Director's Cut
(SceneArtSubsystem::IsShownInDirectorsCut, applied each post-actor tick); no route-end copy. Start Game play backdrop pixels
match main 63266143 again; the DC Keeper capture differs from main by design (no barn picture).
