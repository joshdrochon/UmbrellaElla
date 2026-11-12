# integration status

Done (merged main for Progression; Story has no tuning struct on main yet, so no `Story` member):
- `UUmbrellaTuning` now has `Enemy`, `Trap`, `BrokenMill`, `Progression` members.
- Enemy, Trap, BrokenMill, Progression and the Keeper model read tuning through `GetDefault<UUmbrellaTuning>()` (or a const pointer for the model); no private copies.
- One default per bake key: Health keeps SURV-05.min_lift and the UMB-05 heal keys; Keeper keeps FLOW-33 damage keys (gust has its own unmarked value); Flight keeps absorb keys; Progression copies are unmarked base values; `FProgressionTuning::MaxLives` renamed `MaxLivesCap`.

Proof: `bake_preset defaults` 0 problems; build exit 0; test.sh PASS tests=190 failed=0; manifest_check 0; module_check has only [I] include hints.

Left: `FStoryTuning` member once a Story tuning struct exists on main.
