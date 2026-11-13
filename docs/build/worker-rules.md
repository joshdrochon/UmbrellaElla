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
Default model (Josh, Nov 12, latest): Sonnet (`claude-sonnet-5-5`) for every worker, reviewer and critic. A job moves
to a stronger model only with evidence Sonnet was not effective, through the repeat-failure rule below (triage first).
A worker runs Sonnet. When it fails the same gate check twice, or a builder/critic loop goes 2 rounds with the same gap
and no better score, the build lead restarts that one worker with `WORKER_MODEL=claude-opus-5-5 tools/build/start_area.sh
<area> "..."` and logs it in the build log (area, failing check, before/after). Others stay on Sonnet.
Fable (`claude-fable-5-2`) only by an explicit emergency call from the build lead for a very challenging task, told to
Josh when made (Josh, Nov 12 late); never as the routine escalation.

## Repeat failures: triage before any retry or escalation (Josh, Nov 12)
When the same check fails twice, or a loop goes flat (2 rounds, same gap, no better score):
1. Triage first. Is the failure in the work, or in the rule, check or source? Test the check on a known-good input
   (a reference image, an approved track, the GDD text) and a known-bad one, and check the rule against the GDD and the
   decisions (source order: GDD, decisions, then the pipeline docs). Write the verdict in the build log: "work" or
   "check defect: <what>".
2. Check defect: fix the check with a test (never a loosening of the bar), add a row to the lessons inbox, then rerun.
   Work: escalate that worker to Opus (rule above).
3. Every 30 minutes the build lead scans the logs for any area or check with 3 or more attempts and triages it the same way.

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
- Every automated game launch (editor -game or packaged) goes through `tools/build/run_game.sh` or `tools/ue/smoke.sh`:
  no sound, a 640x360 window, no crash reporter. Never start `UnrealEditor -game` or the packaged app by hand.
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
- Never print, log or commit `~/.umbrella-ella.env` or any key value. Any area that generates assets through an API (audio,
  image: the snd* lanes, audio, imagegen, the art loops once the lead says Spend OK) may source it in the one shell that
  runs generation, and nowhere else.
  Spend OK is given for all seven art loops (Nov 12, cap in IMAGE_SPEND_CAP_USD). Load the key in the same command as the
  call, never on its own: `set -a; . ~/.umbrella-ella.env; set +a; python3 tools/assetgen.py image ...` (the file's lines
  have no `export`, so a plain `source` doesn't reach python). Never echo, cat or grep the file.

## Unreal commands (Mac; many workers share this machine, so always through the slot lock)
    tools/build/ue_slot.sh tools/ue/build.sh                 # compile (editor target); must end "build exit: 0"
    eval "$(python3 tools/build/gate_plan.py origin/main HEAD | grep '^TESTS=')"   # the prefixes your change touches
    TEST_FILTER="${TESTS:-UmbrellaElla.<Area>}" tools/build/ue_slot.sh tools/ue/test.sh   # targeted only; must PASS
    python3 tools/affected_tests.py --base origin/main --run          # only the Python tests your change affects
    python3 tools/module_check.py                            # must be 0 problems
Windows (PowerShell, no lock needed): `tools\ue\build.ps1`, `tools\ue\test.ps1`.
Do not run package.sh; the build lead packages after merges.

## Definition of done (per slice and for the area)
1. `tools/build/ue_slot.sh tools/ue/build.sh` -> `build exit: 0`.
2. Targeted tests only (Josh, Nov 12): `TEST_FILTER=<prefixes from gate_plan.py>` with `tools/build/ue_slot.sh tools/ue/test.sh`
   -> PASS, your new tests included, plus `python3 tools/affected_tests.py --base origin/main --run`. Never run the full
   Unreal or Python suite in a worker or the gate; the full suites run only in `tools/build/prepackage.sh`.
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
