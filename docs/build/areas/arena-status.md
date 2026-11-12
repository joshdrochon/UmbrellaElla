# arena status

## Done (G1 slice 1): CAM-03, WIND-03, CORE-06, ART-03
- CAM-03: `AUmbrellaArena` (Arena/): orthographic fixed 16:9 camera (constrained aspect 1.777778), walls/ceiling, lethal-bottom overlap box, player start and Keeper anchor, two looping background offsets (BackgroundLooped event), takes the view target. Works spawned from code. Test: `UmbrellaElla.Arena.World.CameraAndAnchors`, `UmbrellaElla.Arena.BackgroundLoopWraps`.
- WIND-03: `AWindCurrent` (Field/): harmless volume, WindEntered/WindExited on the bus (Value=force, Detail=Left/Right/Up/Down). Never writes velocity. Tests: `UmbrellaElla.Field.World.BroadcastsEnterExit`, `UmbrellaElla.Field.DirectionLabel`.
- CORE-06: `FBuildIdentity::Capture()` (Feedback/Build): engine, config, platform, units/pixel, camera aspect, packaging, manifest. Test: `UmbrellaElla.Feedback.BuildIdentityRecord`. Revision/asset-manifest fields come from the build lead's BUILD_INFO, not yet wired.
- ART-03: `UEllaAnimPresenterComponent` builds a stand-in box (no art, no image input) when no flipbook is set. Test: `UmbrellaElla.Feedback.World.PresenterStandIn`.
- Sound cues: `UUmbrellaCueSubsystem` maps bus events to cue names and plays `/Game/UmbrellaElla/Audio/<Cue>` if it exists. Test: `UmbrellaElla.Feedback.CueMapping`.

Checks: build exit 0, 8 tests PASS, module_check 0, manifest_check 0.

## Left
- Sound assets (Shot, Hit, Absorb, AbsorbFail, KeeperHit, KeeperAttack, StartMusic, EndMusic) not generated; cues are silent until they exist. Not attempted: needs the ElevenLabs shell.
- Arena now builds placeholder box planes (two backgrounds) and a Keeper stand-in box at the anchor (tested via BuildPlaceholders). Plane scrolling is not applied to the meshes yet.
- Later list (CAM-04..08, HAZ-*, BG-*, ART-05+, ANIM-*, VFX-*, FLOW-24..29/46/47) not started.
- Ella flipbook states beyond Idle.
