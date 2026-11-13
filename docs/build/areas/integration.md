# Area: integration (cross-lane tuning and bake fixes, assigned by the build lead)

Branch `area/integration`. Read `docs/build/worker-rules.md` first. Opened Nov 12 by the build lead (the integrator
owns cross-lane edits). Only the files named here; no other area is working in them right now.

## Goal
`python3 tools/bake_preset.py defaults` reports 0 problems on main (GitHub CI skips it because main fails it), and
every area's numbers live in the shared tuning settings (`GetDefault<UUmbrellaTuning>()`), so tuning presets bake.

## Tasks
1. `Source/UmbrellaElla/Public/Core/UmbrellaTuning.h`: add `UPROPERTY(Config, EditAnywhere)` members for the merged lane
   structs that are missing: `FEnemyTuning Enemy`, `FTrapTuning Trap`, `FBrokenMillTuning BrokenMill` (and
   `FProgressionTuning Progression`, `FStoryTuning Story` once `Merge area/progression` / `Merge area/story` are in
   `git log main`; merge main to get them).
2. Readers use `GetDefault<UUmbrellaTuning>()->X` at the point of use, or a `const` reference to it. Fix
   `Public/Enemy/UmbrellaEnemy.h:81` (non-const FEnemyTuning copy) and `Public/Encounter/KeeperFightModel.h:250`
   (non-const FKeeperTuning copy; keep the model testable: tests may pass their own tuning by const reference or
   pointer-to-const). Same for any Trap, BrokenMill, Progression, Story reader that keeps a private copy
   (`UProgressionSubsystem::GetTuning()` becomes `return GetDefault<UUmbrellaTuning>()->Progression;`).
3. One default per bake key (bake_preset "N markers; one default per key"). Owners (lead call):
   - `SURV-05.min_lift`, `UMB-05.heal_per_yellow`, `UMB-05.heal_per_recovery_rank`: `FHealthTuning` keeps them; remove
     the copies from `FUmbrellaFlightTuning` and make the motor read lift through health
     (`UUmbrellaHealthComponent::GetLiftMultiplier()` or `GetDefault<UUmbrellaTuning>()->Health`).
   - `FLOW-33.projectile_damage`, `chain_damage`, `talon_damage`: `FKeeperTuning` keeps them (the attack sets
     `Shot.Damage`); remove the marked copies from `FHealthTuning` (health uses `Shot.Damage`; its fallback for a shot
     with no damage reads `GetDefault<UUmbrellaTuning>()->Keeper.ProjectileDamage`). `FKeeperTuning::GustDamage` must not
     carry the projectile key: read `ProjectileDamage` instead, or drop the marker if the GDD gives the gust its own
     value.
4. Keep every existing test passing; update tests that read the moved fields.

## File lane
`Public/Core/UmbrellaTuning.h`, `Private/Core/UmbrellaTuning.cpp`, `Public|Private/Harness/**`,
`Public/Health/HealthTuning.h`, `Public/Umbrella/UmbrellaFlightTuning.h`, `Public/Owl/KeeperTuning.h`, and only the
reader lines in `Private/Health/**`, `Private/Motor/**`, `Private/Umbrella/**`, `Private/Encounter/**`, `Private/Owl/**`,
`Public|Private/Enemy/**`, `Trap/**`, `BrokenMill/**`, `Progression/**`, `Story/**`, plus their tests.

## Done
`python3 tools/bake_preset.py defaults` 0 problems; `tools/build/ue_slot.sh tools/ue/build.sh` exit 0; full
targeted tests PASS (`TEST_FILTER` from `tools/build/gate_plan.py`, plus `tools/affected_tests.py --run`) (Core changed); `module_check` 0. Commit after each task, then stop.
