# Commands, smoke, eval cameras, packaging (on demand; core: `pipeline/unreal-rules.md`)

Load when you build, test, package, smoke or capture eval shots.

## Commands (wrapped by tools/ue/*; set UE_ROOT once per machine)
- Compile: `tools/ue/build.sh` (Mac) / `tools\ue\build.ps1` (Windows). Non-unity build: `pipeline/unreal/cpp-rules.md`, Modules item 4.
- Tests: `tools/ue/test.sh` / `test.ps1`, then `python3 tools/check_automation_report.py Saved/Automation/index.json`. The exit code of the editor alone proves nothing. [src: U12, U13]
  Epic's 5.8 docs spell it `Automation RunTest`; scripts use `RunTests`. Zero tests? Try the docs spelling. [src: U14]
- Package (Win64 only on Windows): `tools\ue\package.ps1 [-Shipping] [-Workbench]`. Fails on any `Error:` in the cook log.
  Default is the submission target, workbench compiled out (`workbench-check` must pass); `-Workbench` makes the tester package, never submitted (D-new-workbench-debug).
  Package scripts refuse a dirty git tree (`--allow-dirty` / `-AllowDirty` overrides), write `BUILD_INFO.txt` (commit, date, config) (plus `target=` and `workbench=`) into the package, and time out (`UE_TIMEOUT` seconds, default 7200).
- Smoke: run the packaged game with `-SmokeQuitAfter=15`; the log must contain one line per the contract in `tools/ue_run.py`: `SMOKE_OK map=<map> fps=<n> worst_ms=<n> commit=<sha> input=ok|none input_vz=<Z cm/s while IA_Attack is held, below 0> res=<W>x<H> win=windowed|fullscreen view=<W>x<H> aspect=<a> debugdraw=0|1 textpx=<n> load_ms=<n> workbench=0|1`. view= is the gameplay view inside the bars (16:9 within 0.01), debugdraw=1 means a debug draw is on (a default launch logs 0). `-SmokeShot=<png>` writes the whole-window screenshot the smoke checks with `art_check.py`, `screen_check.py` and `art_judge.py scene` (`pipeline/unreal-rules.md` Display). textpx = smallest UI text height in px on title, HUD, pause and lose at the current resolution. `-SmokeMap=<path>` loads that map instead of GameDefaultMap. (The switches are Day-0 card 0.6.) [VERIFY]
- `tools/ue/smoke.sh <exe>` / `smoke.ps1 -Exe <exe>` fails on a non-zero exit, a `SMOKE_OK` line that misses the contract in `tools/ue_run.py` (fps < 55 is one miss), any `SMOKE_BAD` pattern, any `Error:` line or `Failed to load` line (allowlist `tools/ue/smoke-allow.txt`, one decision row per line), or a new `Saved/Crashes` folder.
- A PR that changes a map smokes that map: `SMOKE_GAME_MAP=/Game/UmbrellaElla/Maps/<Map> SMOKE_MAP=<Map> tools/ue/smoke.sh <exe>` (`$env:` for `smoke.ps1`). `SMOKE_GAME_MAP` is the full path the game loads (`-SmokeMap=`); `SMOKE_MAP` is the short name the `SMOKE_OK map=` field must show. `check_pr.py` fails a pasted `SMOKE_OK` line whose map is not one the PR changes, so paste only changed-map smokes.
- The smoke runs on the Development package (D-new-smoke). Shipping writes no log. [src: U10]

## Eval cameras (art captures from a packaged build)
- `-EvalCam=<CameraActor name>` (e.g. `-EvalCam=CAM_Eval_Arena`), Day-0 card 0.12, lane `Source/UmbrellaElla/Private/Smoke/**`.
  After the map and its sublevels load (wait up to 10 s), it sets the player's view target to that camera with no blend, waits 2 s,
  runs `HighResShot 1920x1080`, logs `EVALCAM_OK cam=<name> file=<path>` and quits with exit code 0. A name not in the map logs an `Error` naming it and exits 1.
- Dev-only: compiled inside `#if !UE_BUILD_SHIPPING`, so captures come from a Development package. Shipping ignores the switch.
- The Integrator places the `CAM_Eval_*` actors. The Art Director judges only captures made this way (`pipeline/roles/art-director.md`).

## Packaging gotchas
- Every map is listed in `MapsToCook` (the Integrator's map card adds its line); `GameDefaultMap` is set (TD, card 0.3). Assets loaded only by string path are not cooked; use `DirectoriesToAlwaysCook`. [src: U17, U18]
- Shipping strips `check`, logging and the console. The submission is the Windows Development package; Shipping is not required (D25). [src: U9, U10, U11]
- Win64 packages build only on Windows; Mac packages only on a Mac. The Windows packaging machine is named in the `docs/jam-brief.md` People table by Day-0 card 0.0 (a Day-1 blocker). [src: U26]
- `-prereqs` adds Epic's prerequisites installer (VC++ runtime); since 5.1 some clean PCs still miss it (fallback: app-local prerequisites). Test the zip on a machine or user profile that never had the editor. [src: U16]
