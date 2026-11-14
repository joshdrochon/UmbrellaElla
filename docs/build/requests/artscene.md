# Requests from artscene

## 1. Critic packet ground for transparent layers (tools/art_loop.py, not my lane)
Now: `flatten_on_ground` puts a transparent piece on a flat fill, `PACKET_GROUND = (238, 229, 210)`.
Problem: against the key art the critics keep naming the ground, not the piece: "sits on a flat cream fill with no aged-paper grain"
(skyline r12 c1, r13 c3, r14 01-c3, r15 01-c1 and 01-c3). The paper is its own piece; the skyline ships transparent.
Change: composite transparent images (ours and any reference with alpha) over one shared paper-textured ground instead of a flat colour, for
example a tile cut from the paper area of `pipeline/art/reference/target-keyart.png` (x 300-900, y 60-300, mirrored to fill), or flat
`PACKET_GROUND` plus the grain `art_check` measures as paper_texture >= 0.38. Same ground for both sides, so the bar does not move.
Workaround in my lane: none; I keep judging on the flat ground.

## 2. Context pair for scene pieces (arena / flow lanes)
`art_loop verdict` cannot pass skyline, paper or menu-screen without an in-engine capture newer than the piece
(`Saved/Logs/pipeline/*-shot.png` or `Saved/Screenshots/**`). That needs the piece imported as a `_PH`-free texture and drawn by the arena, then a smoke
run. Ask: after a piece wins its reference and quality-bar pairs, the build lead imports it on a scratch branch, runs the smoke, and drops the shot
in my worktree's `Saved/Logs/pipeline/`; I run the context panel on it.

## 3. Context capture is impossible from my lane: the backdrop has no texture slot (visuals lane, Source/UmbrellaElla/Private/Feedback/Background)
The lead's recipe says import the candidate into the piece's `_PH` slot and run `run_game.sh -SmokeShot=...`. There is no slot:
`UUmbrellaBackdropSubsystem::BuildLayers` draws every layer (Sky, FarLand, ...) as an untextured `/Engine/BasicShapes/Cube`, and no `T_*Skyline_PH`
or `T_*Paper_PH` asset exists under Content/ or Art/. A smoke shot today shows grey cubes, not the skyline, so it would not be a context capture.
Ask (visuals lane, or the build lead on main): per layer, load `/Game/UmbrellaElla/Art/Scene/T_<Piece>_PH` (skyline, paper) if present, and put it on a
masked/translucent unlit material on the panel (UV tile for paper). Then I import `pipeline/art/proof/scene/skyline/skyline_r2_keyed.png` under that name with an
editor script in `tools/build/assets/art_scene_*.py` and make the shot myself.

## 3 update (Nov 12 evening): slot now exists, capture still blocked by the smoke shot timing
Merged main + artslots. `bg-layer:FarLand` / `bg-layer:Sky` now map to T_Skyline / T_Paper; I imported skyline_r2_keyed.png and paper_r3.png as `_PH`
with import_art_candidate.py (works; Content/UmbrellaElla/Art/Scene/*_PH.uasset left untracked, not committed).
`run_game.sh -SmokeShot=...` x3 (640x360 and default): shot is taken at 5 s wall clock, written (7431 bytes), but the frame is black except the HUD clock.
The game ran at fps 0.1-3.2 (worst frame 34 s) while the gate and other workers use the machine, so no backdrop frame is drawn by 5 s.
Ask (lead): make the shot wait for the first N rendered frames (or `-SmokeShotDelay=<s>` / tuning `Flow.SmokeShotDelaySeconds` readable from the command line), or
run my capture when the machine is idle. Not faking a capture. Until then no piece in my lane can pass the context pair; every `_PH` stays.

## 3 update (Nov 13 02:50): command-line ini override tried, no shot
Merged main (4c3dea15). Tried `run_game.sh "-ini:Game:[/Script/UmbrellaElla.UmbrellaTuning]:Flow=(SmokeShotDelaySeconds=150.0)" -SmokeShot=...`:
the run waited 10 min on ue_slot.sh (slots held by other lanes' imports and the gate test run) and was killed; no shot written. Whether the override
works is untested. Ask stands: run the capture when slots are free, or add a `-SmokeShotDelay=` flag. Every `_PH` stays; zero spend.

## 3 closed (Nov 13): frame-based smoke shots and journeys on main give the context captures; nothing more needed.

## 4 (Nov 13, Opus lead order: the study's world): draw the route floor as island, not a cream bar
File: `Source/UmbrellaElla/Private/Feedback/Background/WorldArtSubsystem.cpp`, `UWorldArtSubsystem::VisualFor`.
Change: `case ELevelPlacementKind::Floor:` returns `TEXT("world:solids")` (add it above `case ELevelPlacementKind::Solid:`).
Why: the floor is the one flat cream stand-in left across the bottom of every route frame (pipeline/art/proof/artscene/world-r1-route-*.png);
the study has no ground, only floating eroded land. The slot art (T_WorldSolids_PH: a crust-topped slab with a drippy underside) already
draws on every ledge. Visual only, collision untouched (ArtSlot::Apply never touches collision). Test: ArtSlotFamilyTests' VisualFor case
gains Floor -> world:solids.
