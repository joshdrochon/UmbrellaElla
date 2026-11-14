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
