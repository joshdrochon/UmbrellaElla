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
