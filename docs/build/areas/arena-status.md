# arena status

## Done (G1 slice 1): CAM-03, WIND-03, CORE-06, ART-03
- CAM-03: `AUmbrellaArena` (Arena/): orthographic fixed 16:9 camera (constrained aspect 1.777778), walls/ceiling, lethal-bottom overlap box, player start and Keeper anchor, two looping background offsets (BackgroundLooped event), takes the view target. Works spawned from code. Test: `UmbrellaElla.Arena.World.CameraAndAnchors`, `UmbrellaElla.Arena.BackgroundLoopWraps`.
- WIND-03: `AWindCurrent` (Field/): harmless volume, WindEntered/WindExited on the bus (Value=force, Detail=Left/Right/Up/Down). Never writes velocity. Tests: `UmbrellaElla.Field.World.BroadcastsEnterExit`, `UmbrellaElla.Field.DirectionLabel`.
- CORE-06: `FBuildIdentity::Capture()` (Feedback/Build): engine, config, platform, units/pixel, camera aspect, packaging, manifest. Test: `UmbrellaElla.Feedback.BuildIdentityRecord`. Revision/asset-manifest fields come from the build lead's BUILD_INFO, not yet wired.
- ART-03: `UEllaAnimPresenterComponent` builds a stand-in box (no art, no image input) when no flipbook is set. Test: `UmbrellaElla.Feedback.World.PresenterStandIn`.
- Sound cues: `UUmbrellaCueSubsystem` maps bus events to cue names and plays `/Game/UmbrellaElla/Audio/<Cue>` if it exists. Test: `UmbrellaElla.Feedback.CueMapping`.

Checks: build exit 0, 8 tests PASS, module_check 0, manifest_check 0.

## Done (slice 2, Nov 12 14:15): level API
- `Level/LevelCatalogue` (FLOW-24, FLOW-27, FLOW-47, HAZ-24..41): 12 chunks x A/B, nine-slot grammar (`LevelGrammar.h`), seeded layout stream, 32-attempt budget, verified named fallback, avoid-previous, `ValidateRoute` gate, refuge positions, patrol footprint clamp. The enemies area places traps through `FChunkVariant`.
- `Level/LevelRules` (CAM-05, CAM-06, CAM-08, HAZ-04, HAZ-09 rule functions): margins, openings, vestibule, reveal, ray clearance, activation region.
- `AUmbrellaArena::FollowEllaX` (CAM-08 scroll with lead, clamped to route), behind the CAM_08 flag.
- Tests: `UmbrellaElla.Level.*` (catalogue, same seed same route, nine-slot grammar, rules), `UmbrellaElla.Arena.World.CameraAndAnchors` (scroll lead and clamp).
Checks: build exit 0, 37 tests PASS, module_check 0, manifest_check 0.

## Left
- Sounds: all 8 cue assets and the source clips exist (WandBolt, HitOwl, ShieldCatch, PlayerHurt, OwlBoltLaunch, KeeperHoot, EndEvent, MusicTitle, stings). No new generation done this slice.
- Nothing calls `FollowEllaX` yet; Flow/player controller must feed it Ella's X (not my lane). Chunk geometry is data only; no per-chunk level actors.
- CAM-04, CAM-07, FLOW-25, FLOW-26, FLOW-28: QA-36 measurement items with no parameters. Not built; need playtest.
- Presentation (BG, ART-05+, ANIM, VFX) moved to the visuals area.

## Slice 3 (Nov 12 14:50): audio bar, level-up cue, contract rules
- Audio: every take in `Audio/Source` now passes `audio_check --scan` and `audio_style_check check` (the only remaining `--scan` errors are P0 sounds nobody has made yet, outside this lane's cues). Takes regenerated with ElevenLabs where the spectrum or onset was off (WandBolt, HitOwl, OwlBoltLaunch, PlayerHurt, ShieldCatch, KeeperHoot 3 s, EndEvent 4 s, stings), then processed by `tools/build/assets/arena_audio_fix.py` (trim lead silence, EQ chosen by search against the family ranges, loudness to the family, -1.5 dBFS limiter, 50-80 ms end fade, stereo where listed, common RMS per group). No tracked placeholders left. The recorded prompt in provenance is the generation prompt; the post-processing is this script.
- Stings: both pass the numbers; the audio_loop critic round was not run (no separate critic session available to this worker). The lead's gate may want one.
- LevelUp: `LevelGained` -> cue `LevelUp` (`UUmbrellaCueSubsystem`), source `LevelUpClock` take passes. The `.uasset` is not made yet: run `tools/build/assets/arena_audio_import.py` in the editor (LevelUp added).
- CAM-04, CAM-07, FLOW-25, FLOW-28 rule functions in `Level/LevelContracts` (no GDD numbers, QA-36 measures): wind drawn width, lead both ways, background coverage, qualified envelope, reopen height, required current persists, carried health (no free heal), boss arrival ready. Test: `UmbrellaElla.Level.ContractsReadabilityCatchCheckpoint`. FLOW-26 is authored design only (GDD says do not claim it implemented); nothing built.
Checks: build exit 0, 72 tests PASS, module_check 0, manifest_check 0.
