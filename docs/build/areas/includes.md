# Area: includes (make the non-unity build pass)

Branch `area/includes`. Read `docs/build/worker-rules.md` first. Opened Nov 12 by the build lead; no other worker is in
these files now.

## Goal
`NONUNITY=1 tools/build/ue_slot.sh tools/ue/build.sh` ends `build exit: 0  mode=nonunity`. Today it fails in about 20
files (each .cpp relies on includes another file pulled in under unity): GEngine / FWorldContext (Engine/Engine.h),
APawn to AActor conversions (GameFramework/Pawn.h), and others in Flow/UmbrellaPlayerController.cpp,
Tests/Health/*, Tests/Projectile/ProjectileWorldTests.cpp, Tests/Settings/*, Public/Level/LevelCatalogue.h,
Public/Progression/ProgressionSubsystem.h, Tests/Shared/UmbrellaTestWorld.*, Smoke, Settings, Feedback/Audio,
BrokenMill, Arena/Enemy/Trap/Field/Feedback/Move tests.

## Rules
Only `#include` lines and forward declarations (IWYU: include what you use, in the file that uses it; headers forward
declare what they use only by pointer). No logic, no renames. Any file under `Source/UmbrellaElla/` is in your lane for
include lines only.

## Done
Non-unity build exit 0, unity build exit 0, targeted tests PASS (`TEST_FILTER` from `tools/build/gate_plan.py`, plus `tools/affected_tests.py --run`), `module_check` 0. Commit, stop.
