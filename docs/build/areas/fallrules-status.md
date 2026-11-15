# fallrules status

## Built
- Bottom and ceiling lethal: `UEllaMotorComponent` calls `UUmbrellaHealthComponent::DefeatAtBoundary` (one PlayerDefeated); tests
  `UmbrellaElla.Move.World.RisingPastCeilingTopDefeats`, `UnderCeilingLineLives`, `ShootHeldFallsAtFallSpeedToLethalBottom`.
  Director's Cut retry restores health after a route death. Merged in main 1d95f1fd.
- Single movement path: the character movement's tick is off; the motor sweeps X then Z (route solids still block; walker tests pass).
- Felt speeds through D-new-move-speeds (Values + Overrides, D-new-creative-director-feel); `tools/tuning.py` decided_values,
  `tools/manifest_check.py` FEEL_DIRECTOR / FEEL_KEYS. gdd_check bound values that follow the speeds are cited in the row.
- Broken Mill world tests skip while `FBrokenMillRules::IsInRun()` is false (D-new-mill-in-route), thresholds unchanged.

## Measured
- Real game, offscreen, Start Game: rise 240 / 240 per s and Shoot fall 659 / 661 per s, before / after the fix. Full suite 471/471.
