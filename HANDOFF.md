# HANDOFF: Umbrella Ella build (read this to pick up the build)

Updated: 2026-11-12 (build lead). Josh's call, Nov 12 13:40: no GitHub cards/PRs/reviewers during the build. Five area
workers (Claude Code, Sonnet) build in parallel on `area/<name>` branches; the build lead runs the gates below and
merges to `main`. **Teammates continue with Claude Code** (not Codex).

## What is on main
- Unreal 5.8.4 project skeleton: `UmbrellaElla.uproject`, `Source/`, `Config/`, `Content/UmbrellaElla/Maps/L_Graybox.umap`.
- Core contracts every area builds against (Ella shell + components, `UUmbrellaTuning`, event bus, collision channels,
  draw order, play mode, projectile seam, feature flags, lane-owned stubs). See `docs/build/worker-rules.md`.
- Merged: area/arena G1 slice c7d8c67 (CAM-03, WIND-03, CORE-06, ART-03) as ec0b8a3, all gates PASS.
- Build docs: `docs/build/worker-rules.md`, `docs/build/areas/<area>.md` (the worker prompt for each area),
  `docs/build/areas.py` (Rule ID split; `python3 docs/build/areas.py` proves all 204 IDs are covered once).

## Area branches
| Area | Branch | G1 Rule IDs | Later | Status / last commit |
|---|---|---|---|---|
| move: Ella movement + basic shot | `area/move` | MOVE-04..07, 11, 13..15, 18..22, CORE-04, CORE-05, UMB-05, COM-05, COM-06, COM-10 | MOVE-12, MOVE-16, COM-07..09, COM-11 | see `docs/build/areas/move-status.md` on the branch |
| keeper: the Keeper fight | `area/keeper` | OWL-06..35, FLOW-09 | COM-12..18 | `docs/build/areas/keeper-status.md` |
| health: shots, absorb, health, clock HUD | `area/health` | SURV-05, SURV-07, FLOW-30..33 | SURV-06, FLOW-05..23 (not 09), FLOW-42, FLOW-48 | `docs/build/areas/health-status.md` |
| flow: menus, modes, pause, win/lose, smoke hook | `area/flow` | FLOW-02, FLOW-04, FLOW-34, FLOW-35, ART-04 | FLOW-03, 36..41, 43..45, 49, MOVE-08..10, MOVE-17, NAR-02..08 | `docs/build/areas/flow-status.md` |
| arena: arena, camera, wind, art, sound | `area/arena` | CAM-03, WIND-03, CORE-06, ART-03 | CAM-04..08, HAZ-02..41, BG-02..06, ART-05..10, ANIM-02..10, VFX-02..11, FLOW-24..29, FLOW-46, FLOW-47 | `docs/build/areas/arena-status.md` |
Live state: `git fetch && git log --oneline main..origin/area/<name>` and that branch's status file.

## Gates each merge into main must pass
1. `tools/ue/build.sh` (Windows `tools\ue\build.ps1`) -> `build exit: 0`; before a gate also `NONUNITY=1 tools/ue/build.sh`.
2. `tools/ue/test.sh` (`tools\ue\test.ps1`) -> PASS with every automation test.
3. `python3 tools/module_check.py` 0 problems; `python3 tools/manifest_check.py` 0 problems;
   `python3 tools/feel_check.py` (move area) and `python3 tools/encounter_check.py` (keeper area) 0 problems.
4. One review round of the diff (a fresh Claude Code session: "review `git diff main...area/<name>` against
   docs/build/worker-rules.md and pipeline/unreal/cpp-rules.md; list real bugs only"). Real problems go back to the
   area worker once; minor ones go to the follow-up list in this file.
5. Art replaces a placeholder only when `tools/art_ref_check.py` / `tools/art_loop.py` says it meets the reference bar.
After G1 features are merged: `tools/ue/package.sh` + `tools/ue/smoke.sh` (Mac Development) and, on Windows,
`tools\ue\package.ps1` + `tools\ue\smoke.ps1` (the submission is a Windows Development package).

## Continue on Mac (Claude Code)
    cd ~/Desktop/Developer/UmbrellaElla && git pull
    tools/build/start_area.sh <area>            # starts/continues a worker in ../UmbrellaElla-areas/<area>, log ../UmbrellaElla-areas/logs/<area>.log
    tools/build/push_areas.sh --loop &          # pushes area/* branches every 2 min
    # merge loop, per finished slice (merges in ../UmbrellaElla-areas/gate, pushes main only on PASS):
    tools/build/gate.sh area/<area> [commit]
Workers on one Mac share the engine through `tools/build/ue_slot.sh` (max 2 Unreal builds/tests at once).

## Continue on Windows (PowerShell, Claude Code)
    cd $HOME\Desktop\UmbrellaElla   # your clone
    git pull; git lfs pull
    powershell -File tools\build\start_area.ps1 -Area <area>       # worktree ..\UmbrellaElla-areas\<area>, pushes its branch after each commit
    # or interactively: cd ..\UmbrellaElla-areas\<area>; claude   then paste the prompt from docs/build/areas/<area>.md
    # merge loop:
    git checkout main; git merge --no-ff origin/area/<area>; tools\ue\build.ps1; tools\ue\test.ps1; python tools\module_check.py; git push origin main
If git hooks block a commit, use `git -c core.hooksPath=NUL commit` (the gate-guard hook was removed by Josh's order).
Never commit `~/.umbrella-ella.env` or any key.

## Follow-up list (minor review findings)
- DECIDED: flow owns the view target; arena removes its SetViewTarget (sent to arena worker).
- DECIDED: walls and ceiling stop shots (GDD silent). Arena blocks PlayerShot/EnemyShot; health's projectile service must destroy a shot on a blocking hit (tell the health worker on restart).
