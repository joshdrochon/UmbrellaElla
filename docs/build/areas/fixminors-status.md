# fixminors status

## Done (build exit 0, 207 tests PASS, module_check 0 problems, manifest_check run)
- Arena minor 4: `LevelContracts.cpp` now includes `Level/LevelRules.h`.
- Enemies minor: `UmbrellaTrap::ApplyContact` stops at the first `Consumed` receiver.
- Enemies minor: `BossTargetHit` with `Detail==Enemy` now maps to the `Hit` cue and `ShotImpact` effect, not the Keeper ones.

## Left, in lane (not done)
- `BrokenMillRoom::StepSeconds` never sets `bInNoWarningPhase`: the room has no source for reset/assist/underpass/exit phases. Needs a design input.
- `FTrapRules::BellowsPush` fixed vector; HAZ-21 lane-dependent direction is a design call.
- `FloodstriderStiltHeight` unused: no stilts/underbody passage (COM-15). Placeholder.
- `UmbrellaVfxSubsystem::PlayForEvent` uses a full `TActorIterator` per event; needs a source-id lookup cache.
- Level contracts (FLOW-25/28, CAM-04/07) are only called from tests.
- Visuals minors: backdrop ignores camera Z (fine while locked); ART-10/ANIM-08 status wording.

## Out of lane (owner)
- Arena status wording, `tools/build/assets/arena_audio_fix.py`, LevelUp .uasset: build lead / audio.
- enemies-status.md / requests/enemies.md stale numbers: docs, build lead.
- Flow, Health (GUST_Band in Core), Keeper (LivesLostThisPhase), Move, Progression, Settings, Story, Includes, Integration items: their lanes.
