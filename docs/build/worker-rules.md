# Area worker rules (every area reads this first)

Josh's call, Nov 12 13:40: no GitHub cards, PRs or reviewer ceremony during the build. Five area workers build the
game in parallel on `area/<name>` branches; the build lead runs the gates and merges to `main`. The pipeline rules are
engineering guidance, not ceremony: follow them where they make the code better, skip the card paperwork.

## How many workers (Josh, Nov 12)
Run as many workers as can usefully work in parallel: one per area that has ready work and a file lane that does not
overlap another active worker. Bound it by the machine (Unreal builds/tests go through `tools/build/ue_slot.sh`, 2 to 4 at once by free memory; workers spend most of their time writing code) and by Claude usage (workers run Sonnet).
Re-check whenever a worker finishes, an area merges, or new work unblocks: start workers for newly ready lanes, and
split a big area when its later list has independent parts (new area file + `docs/build/areas.py`, every Rule ID in
exactly one area, lanes disjoint).

## When a worker moves to Opus (Josh, Nov 12)
A worker runs Sonnet. When it fails the same gate check twice, or a builder/critic loop goes 2 rounds with the same gap
and no better score, the build lead restarts that one worker with `WORKER_MODEL=claude-opus-5-5 tools/build/start_area.sh
<area> "..."` and logs it in the build log (area, failing check, before/after). Others stay on Sonnet.

## Read first (in this order, only what you need)
1. Your area file `docs/build/areas/<name>.md` (Rule IDs, GDD sections, file lane, done).
2. `docs/jam-brief.md` (MVP and gates), the GDD sections your area file names (`docs/gdd/GDD-SH1.0.md`), and your
   Rule IDs' records in `docs/feature-manifest.json` (parameters, tests, approved_parameters).
3. `pipeline/unreal/cpp-rules.md` and `pipeline/unreal/gameplay-code.md` (component layout, C++ rules, tests).
   Lines there about GDD 1.3 (owl bolt, front shield, 90 s timer) are history; the GDD SH1.0 wins.
4. The Core contracts already on main (do not edit them; ask in your log if one is wrong, see "Contract changes"):
   - `Source/UmbrellaElla/Public/Core/EllaCharacter.h` shell: creates InputAdapter, Motor, UmbrellaState, Attack,
     Absorb, Health, AnimPresenter components and calls each `BindInput`. Nothing else goes in the shell (rule L).
   - `Core/UmbrellaTuning.h`: one member per module struct. Add your numbers to YOUR struct header
     (e.g. `Public/Motor/MotorTuning.h`), read them with `GetDefault<UUmbrellaTuning>()->Motor.X`.
   - `Core/UmbrellaEventBus.h` + `Core/UmbrellaEvent.h`: the manifest events. Modules talk through it; no hard
     references between Motor, Health and the Keeper.
   - `Core/UmbrellaCollision.h` (PlayerShot, EnemyShot, Hazard channels), `Core/UmbrellaDrawOrder.h` (all Y depths),
     `Core/UmbrellaPlayMode.h` (StartGame / DirectorsCut).
   - `Projectile/UmbrellaShotSpec.h`, `Projectile/UmbrellaShotReceiver.h` (interface every hittable thing implements),
     `Projectile/UmbrellaProjectile.h` (`AUmbrellaProjectile::Fire(World, Spec)`, the one way to fire a shot).
   - `Harness/UmbrellaFeatureFlags.h`: `IsFeatureEnabled(EFeatureId::OWL_06)`. Every file that names a Rule ID must
     check its flag (module_check rule M). All are on by default.
   - Seams owned by a lane, already stubbed: `Encounter/EncounterDirectorSubsystem` (keeper: `BeginKeeperFight`,
     `ResetForRestart`), `Owl/KeeperOfTime` (keeper), `Arena/UmbrellaArena` (arena), `Flow/UmbrellaPlayerController`
     (flow), `UI/UmbrellaHUD` (health). Fill in your own; call others only through their public functions and events.

## Hard rules
- Never write an absolute home path (`/Users/...`, `~/...` beyond `~/.umbrella-ella.env`) into a repo file; use paths
  relative to the repo or `../UmbrellaElla-areas/...`. `python3 tools/pipeline_check.py` (in every gate) rejects them.
- Unity builds merge many `.cpp` files into one: never put generic names (`Step`, `Count`, `Tolerance`) at file scope
  or in an anonymous namespace; prefix them with your area (`KeeperTestStep`), or `-Wshadow` breaks another area's build.
- Stay in your file lane (your area file lists it). Never edit another lane's files, `Core/`, `Harness/`, the
  `.uproject`, `Config/*.ini` or `Source/*.Target.cs`. If you truly need a change there, write it in
  `docs/build/requests/<area>.md` (create it) with the exact diff, and work around it with a stub in your lane.
- All gameplay rules in C++ with plain rule functions tests can call. Blueprints/UMG only as thin data/layout,
  ideally none: build UI in C++ (UUserWidget/Slate) and placeholders from engine primitives or Paper2D sprites made in code.
- Assets (`.uasset`/`.umap`) only if you must; make them with a committed editor Python script
  (`UnrealEditor-Cmd <uproject> -run=pythonscript -script=<file> -unattended -nullrhi -nosplash -nocrashreports`), so they
  can be rebuilt. Every headless editor launch passes those four flags (no crash-reporter dialogs on the shared Mac). They go through Git LFS.
- Every number in your tuning struct, with the GDD/manifest value and `// bake: <ID>.<param>` where the manifest has
  a parameter. No magic numbers in `.cpp` (rule G).
- Tests: `Private/Tests/<YourArea>/`, names `UmbrellaElla.<Area>.<Behavior>` (rule tests, under 1 s) and
  `UmbrellaElla.<Area>.World.<Behavior>` (transient world tests). Every behavior you claim has a test that reads a value.
  Leave `Private/Tests/Bootstrap/PlaceholderTest.cpp` alone (plain `test.sh` passes once your real tests exist).
- Never push, never merge, never touch `main` or another worktree. Never `git commit --amend` or rebase after a commit.
  Commit on your branch with `git -c core.hooksPath=/dev/null commit` after each working slice (the build lead pushes
  your branch to origin every 2 minutes, so a teammate can take over from any commit).
- Never read or print `~/.umbrella-ella.env` or any key. Only the arena area may source it, in the one shell that
  runs audio generation.

## Unreal commands (Mac; many workers share this machine, so always through the slot lock)
    tools/build/ue_slot.sh tools/ue/build.sh                 # compile (editor target); must end "build exit: 0"
    tools/build/ue_slot.sh tools/ue/test.sh                  # all automation tests; must PASS
    TEST_FILTER=UmbrellaElla.<Area> tools/build/ue_slot.sh tools/ue/test.sh   # just yours while iterating
    python3 tools/module_check.py                            # must be 0 problems
Windows (PowerShell, no lock needed): `tools\ue\build.ps1`, `tools\ue\test.ps1`.
Do not run package.sh; the build lead packages after merges.

## Definition of done (per slice and for the area)
1. `tools/build/ue_slot.sh tools/ue/build.sh` -> `build exit: 0`.
2. `tools/build/ue_slot.sh tools/ue/test.sh` -> PASS, your new tests included.
3. `python3 tools/module_check.py` -> 0 problems; `python3 tools/manifest_check.py` clean; feel/encounter checks
   if your area file names them.
4. Committed on your branch with a message naming the Rule IDs done.
5. Append to `docs/build/areas/<area>-status.md` (your lane): Rule IDs done, tests that prove them, what is left.
Work G1 Rule IDs first, then the "later" list. Keep going until both are done or you are blocked; when blocked,
write why in the status file, commit, and stop.

## Quality bars (Josh, Nov 12; enforced by tools/build/gate.sh on every merge)
- Art ships only on a pass: every image under `Art/` (outside `Art/Source/`) or art asset under `Content/*/Art` that is
  not a tracked `_PH` placeholder needs its art loop pass record (`tools/art_loop.py`: calibrated blind critic panel
  against the references and the quality bar, plus art_check, screen_check and art_ref_check on those bytes). Art below
  the bar stays a tracked `_PH` placeholder (put `_PH` in the file name); the merge goes ahead without it.
- Audio ships only on a pass: every WAV under `Audio/Source/` passes `tools/audio_check.py --scan Audio/Source` and
  `tools/audio_style_check.py check Audio/Source`, or is a tracked placeholder take (provenance origin
  `placeholder: <reason>`), and the blind audio critic (`tools/audio_loop.py` packet, one fresh session per sound id)
  must pass it; a piece the critic fails is marked a tracked placeholder by the gate and regenerated later.
- UI (`tools/ui_check.py ci`) and story (`tools/story_check.py`) may not get worse than main. Story merges also need the
  blind story critic (`tools/build/critic.sh story`); Keeper and enemy merges need the encounter critic once the game
  writes a run log.
- Jam rules: `tools/submission_check.py prejam`, and `assets` when content changes (provenance, no pre-jam content).
- Every merge gets an independent review session (`tools/build/review.sh`, the role card for your domain). One round:
  "changes" comes back to you once; after that the items become follow-ups.

## Tests per merge vs before a package
Per merge the gate runs only what relates to the change (`tools/build/gate_plan.py`): your area's automation test
prefix (`UmbrellaElla.<Area>.*`) plus the prefixes of any other folder the merge touched (all tests if Core/Harness or
a Build.cs changed), and only the Python checks that apply to the changed files. The full Unreal and Python suites run
once before each packaged build (`tools/build/prepackage.sh`). So: name your tests `UmbrellaElla.<YourArea>...` and
run `TEST_FILTER=UmbrellaElla.<YourArea> tools/build/ue_slot.sh tools/ue/test.sh` while you work.

## Contract changes
If a Core contract blocks you, do not edit it. Write the request (file, exact change, why) in
`docs/build/requests/<area>.md`, commit, and continue with a local workaround. The build lead applies it on main.
