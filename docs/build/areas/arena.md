# Area: arena (arena, camera, wind, hazards, placeholder art, sounds, presentation)

Branch `area/arena`. Read `docs/build/worker-rules.md` first.

## Rule IDs
G1 first: CAM-03, WIND-03, CORE-06, ART-03, plus the Keeper arena itself, Ella's and the Keeper's placeholder visuals,
and placeholder sounds for shots, hits, absorb, Keeper attacks, menu and Start/End music.
Later (G2/G3): CAM-04 .. CAM-08, HAZ-02 .. HAZ-41, BG-02 .. BG-06, ART-05 .. ART-10, ANIM-02 .. ANIM-10, VFX-02 ..
VFX-11, FLOW-24 .. FLOW-29, FLOW-46, FLOW-47 (the Director's Cut nine-chunk level, refuges, traps, camera, Broken Mill
room, procedural placement, final art/anim/VFX/audio). This list is large; the build lead may split it later.

## GDD sections
5 "Director's Cut full level" and its subsections (traversal/camera contract, traps, chunks, refuges), 8 (Art,
animation, VFX and audio: every subsection), 9. Art bar: `pipeline/art/art-bible.md` and the key art; checks
`python3 tools/art_ref_check.py --help`, `tools/art_loop.py`, `tools/audio_check.py`, `tools/audio_loop.py`.

## File lane (only these)
- `Source/UmbrellaElla/{Public,Private}/Arena/**`, `Field/**`, `Hazard/**`, `Level/**`, `Feedback/**`
- `Source/UmbrellaElla/Private/Tests/Arena/**`, `Private/Tests/Field/**`, `Private/Tests/Level/**`,
  `Private/Tests/Feedback/**`
- `Content/UmbrellaElla/Maps/**`, `Content/UmbrellaElla/Art/**`, `Content/UmbrellaElla/Audio/**`, `Audio/Source/**`,
  `Art/Source/**`, `pipeline/art/**`, `pipeline/audio/**`, `tools/build/assets/arena_*.py`,
  `docs/build/areas/arena-status.md`, `docs/build/requests/arena.md`

## What to build
- `AUmbrellaArena`: bounds (walls/ceiling/bottom from tuning), the fixed orthographic play camera with Constrain
  Aspect Ratio 1.777778 (CAM-03), Ella start, Keeper anchor, two looping background layers (placeholder). Flow spawns it
  if the map has none, so it must work spawned from code with no placed actors.
- Wind currents (WIND-03, Field/): harmless current volumes Ella can ride; on overlap broadcast WindEntered/WindExited
  on the event bus (source/target IDs, force in Value, direction in Detail). The Motor (move area) applies motion;
  you never write velocity.
- Feedback: `UEllaAnimPresenterComponent` shows Ella (Paper2D sprite/flipbook placeholders built from
  `pipeline/art/reference` or simple shapes; neutral stand-in on missing art, never gameplay authority). Sounds:
  generate with the pipeline ElevenLabs tooling (`tools/audio_loop.py`, `pipeline/audio/`; key in
  `~/.umbrella-ella.env`, source it only in that shell, never print it); if it fails, use tracked `_PH` placeholders.
  Play cues from event-bus events (ProjectileSpawned, ProjectileContact, CatchSucceeded, BossTargetHit, ...).
- Art replaces a placeholder only when `tools/art_ref_check.py` / art_loop says it meets the reference bar. Gameplay
  never waits on art.

## Done
Worker-rules DoD, plus world tests: the arena spawned from code has a camera with aspect 1.777778 and a Keeper anchor,
a wind current broadcasts WindEntered/WindExited for Ella, the anim presenter falls back to a stand-in with no art.
