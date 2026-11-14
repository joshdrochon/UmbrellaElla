# artkeeper requests
## Owl sprite slot and loader (blocks the in-engine context capture)
Content/UmbrellaElla/Art has only VFX; no owl `_PH` asset exists, and `Private/Owl/KeeperOfTime.cpp` builds the Keeper from engine cube meshes (LoadObject StaticMesh/BasicMaterial), `KeeperPresenterSubsystem.cpp` loads no owl texture or flipbook. So importing a candidate into a `_PH` slot (docs/build/art-image-model.md "Context capture" step 1) changes nothing on screen.
Needed from the gameplay/keeper lane (outside artkeeper): a named slot, e.g. `/Game/UmbrellaElla/Art/Keeper/T_Keeper_Owl_PH` (or a 4-frame flipbook `FB_Keeper_Owl_PH`), that KeeperOfTime/KeeperPresenter displays as a Paper2D sprite. artkeeper will then import the candidate into that name with a committed editor script and take the -SmokeShot capture.

## Update Nov 13: slot exists, context capture still impossible (2 items)
1. The slot now exists (artslots: keeper:body-hover-flap -> T_Keeper_Owl, UKeeperPresenterSubsystem). I imported R10 keyed_3 as T_Keeper_Owl_PH (import_art_candidate.py) and ran `run_game.sh -SmokeShot=... -SmokeQuitAfter=15`. The capture is a black L_Graybox frame with only the HUD clock: no Keeper, because the smoke run never starts the Keeper fight (SmokeHookSubsystem has no -SmokeSection/-SmokeMap handling; docs mention it, Source does not).
   Needed (Smoke/Flow lane): a smoke switch that calls AUmbrellaGameMode::BeginFight (e.g. -SmokeKeeper) so the Keeper is on screen at the shot time.
2. A relative -SmokeShot path is resolved against the engine's Binaries/Mac folder, not the repo: the file lands in /Users/Shared/Epic Games/UE_5.8/Engine/Binaries/Mac/Saved/Logs/pipeline/. art_loop find_capture will not see it. Fix: resolve ShotPath against FPaths::ProjectDir() (or have run_game.sh cd to the repo).

## Update Nov 13 (3): capture now starts the fight, but the old cube covers the owl
Items 1-2 are fixed on main. The -SmokeKeeper capture now shows the Keeper sprite with a flat lilac cube (KeeperOfTime's engine-cube body) drawn over it, plus a grey gradient bar. Needed (keeper lane, Private/Owl/KeeperOfTime.cpp / KeeperPresenterSubsystem.cpp): hide the cube meshes whenever the T_Keeper_Owl or T_Keeper_Owl_PH sprite is loaded, so the in-engine context pair shows the owl alone.

## Update Nov 13 (4): request 3 still open on main (checked after merging origin/main 523292da); exact diff
Source unchanged since: KeeperOfTime::PlaceVisual (Private/Owl/KeeperOfTime.cpp:101) always SetVisibility(true) on the engine-cube parts, drawn over the sprite.
Diff (keeper lane; presenter owns the decision, the actor obeys it):
1. Public/Owl/KeeperOfTime.h: `bool bArtReplacesStandIn = false;` (UPROPERTY not needed).
2. KeeperOfTime.cpp PlaceVisual: `Visual->SetVisibility(!bArtReplacesStandIn);` (replaces the unconditional `true`; cubes stay for gameplay when no art asset exists).
3. KeeperPresenterSubsystem.cpp ShowStandIn, after `ArtSlot::ApplyRow(Mesh, *Row, ...)`: if it reports the sprite drew (EArtSlotDraw other than the cube fallback), `Cast<AKeeperOfTime>(Keeper)->bArtReplacesStandIn = true;`.
Capture and context pair for owl and every keeper-* piece wait on this; no paint round can pass the context pair before it (paint is not the gap).

## Update Nov 13 (5): art-slot material draws only the top row of a grid sheet (blocks any grid flipbook, Ella's idle too)
`tools/build/assets/art_slot_material.py` builds UV = ((U*TileU + Frame)/Cols, V*TileV). With a 6x4 grid (TileV = 1/4) every Frame >= 6 samples past U = 1 (clamped): only frames 0-5 of a 24-frame sheet can show, and nothing calls `ArtSlot::SetFrame` for Ella or the Keeper, so both grids draw frame 0 only.
Needed (TD / art-slot owner; regenerates M_ArtSlot.uasset): U = (U*TileU + fmod(Frame, Cols)) / Cols, V = (V + floor(Frame / Cols)) * TileV. Tiled slots (Frame 0) unchanged.
Until then artkeeper's KeeperPresenterSubsystem plays the Keeper idle grid on row 0 only (frames 0-5 of 24, see artkeeper-status.md); one constant switches it to all 24 once this lands.

## Update Nov 13 (6): owl softness in game is the TSR anti-aliasing and the owl's screen size, not the art (TD / lead)
Measured with tools/build/assets/art_keeper_sharpness.py (numbers in pipeline/qa/visual/owl-sharpness/owl-sharpness.json and artkeeper-status.md session 21).
The key, grade and grid cut lose nothing (ratios 1.00). In game the owl is drawn 378-384 px wide at 1280x720 (2.48 texels per screen px), and TSR leaves 0.75 of the sharpness a clean downscale to that size has.
Options (engine settings or post-process volume, not this lane):
1. `r.Tonemapper.Sharpen=1` in Config/DefaultEngine.ini [SystemSettings] (or the arena post-process): 0.75 -> 0.97 at 720p, 0.66 -> 0.79 at 1080p with 100 %. Engine-wide: sharpens everything, not just the owl. 2 overshoots (1.11).
2. `r.ScreenPercentage=100` (today: auto, renders under 100 % at 1080p): 0.57 -> 0.66 at 1920x1080.
3. Bigger owl on screen (KeeperPresenter StandInScale.X 6 = 600 of the 1920-unit arena): gameplay size, design call.
Tested and rejected in this lane: texture mipmaps (simple average 0.68, sharpen5 0.74, sharpen10 0.77-0.83 vs base 0.73-0.76, inside run-to-run noise, +33 % memory); FXAA 0.84 but jagged; TAA 0.65.
