# HANDOFF: Umbrella Ella build (read this to pick up the build)

Updated: 2026-11-12 (build lead). Josh's call, Nov 12 13:40: no GitHub cards/PRs/reviewers during the build. Area
workers (Claude Code, Sonnet) build in parallel on `area/<name>` branches; the build lead runs the gates below and
merges to `main`. **Teammates continue with Claude Code** (not Codex).

Lessons learned (pipeline failures and what changed): `MegaPipeline/Reference/Lessons Learned.md`. Add a row whenever a gate, critic, worker or package step fails for a pipeline reason.

## What is on main
- Unreal 5.8.4 project skeleton: `UmbrellaElla.uproject`, `Source/`, `Config/`, `Content/UmbrellaElla/Maps/L_Graybox.umap`.
- Core contracts every area builds against (Ella shell + components, `UUmbrellaTuning`, event bus, collision channels,
  draw order, play mode, projectile seam, feature flags, lane-owned stubs). See `docs/build/worker-rules.md`.
- Merged: area/arena G1 slice c7d8c67 (CAM-03, WIND-03, CORE-06, ART-03) as ec0b8a3, all gates PASS.
- Merged with the full gate: arena, move (all), health (G1 + review fixes), flow G1 + FLOW-03 tutorials, enemies.
- Build docs: `docs/build/worker-rules.md`, `docs/build/areas/<area>.md` (the worker prompt for each area),
  `docs/build/areas.py` (Rule ID split; `python3 docs/build/areas.py` proves all 204 IDs are covered once).

## How many workers
Run as many workers as can usefully work in parallel: one per area with ready work and a file lane that does not overlap
another active worker, bounded by the machine (memory-adaptive Unreal slots, `tools/build/ue_slot.sh`) and Claude
usage (Sonnet workers). Re-check whenever a worker finishes, an area merges or new work unblocks; split a big area when
its later list has independent parts (`docs/build/areas.py` must still show every Rule ID in exactly one area).

Escalation: a worker that fails the same gate check twice, or loops 2 rounds on the same gap with no better score,
restarts on Fable (`WORKER_MODEL=claude-fable-5-2 tools/build/start_area.sh <area>`). Default models: Fable for art and audio, Opus for the rest.

## Area branches
| Area | Branch | G1 Rule IDs | Later | Status / last commit |
|---|---|---|---|---|
| move: Ella movement + basic shot | `area/move` | MOVE-04..07, 11, 13..15, 18..22, CORE-04, CORE-05, UMB-05, COM-05, COM-06, COM-10 | MOVE-12, MOVE-16, COM-07..09, COM-11 | see `docs/build/areas/move-status.md` on the branch |
| keeper: the Keeper fight | `area/keeper` | OWL-06..35, FLOW-09 | - | `docs/build/areas/keeper-status.md` |
| health: shots, absorb, health, clock HUD | `area/health` | SURV-05, SURV-07, FLOW-30..33 | - | `docs/build/areas/health-status.md` |
| flow: menus, modes, pause, win/lose, smoke hook | `area/flow` | FLOW-02, FLOW-04, FLOW-34, FLOW-35, ART-04 | FLOW-03, FLOW-41, MOVE-08, MOVE-09 | `docs/build/areas/flow-status.md` |
| arena: arena, camera, wind, level route, art, sound | `area/arena` | CAM-03, WIND-03, CORE-06, ART-03 | CAM-04..08, HAZ-24..41, FLOW-24..28, FLOW-47 (and sound) | `docs/build/areas/arena-status.md` |
| enemies: Director's Cut enemies, Broken Mill, traps | `area/enemies` | - | COM-12..18, HAZ-02..23, FLOW-46 | `docs/build/areas/enemies-status.md` |
| progression: XP, levels, unlocks, upgrades, persistence, XP ring | `area/progression` | - | SURV-06, FLOW-05..08, FLOW-10..23, FLOW-29, FLOW-42, FLOW-48 | `docs/build/areas/progression-status.md` |
| visuals: final art, animation, VFX, backgrounds | `area/visuals` | - | BG-02..06, ART-05..10, ANIM-02..10, VFX-02..11 | `docs/build/areas/visuals-status.md` |
| settings: settings, remap, credits, dev options | `area/settings` | - | FLOW-36..40, FLOW-43..45, MOVE-10, MOVE-17 | `docs/build/areas/settings-status.md` |
| story: Director's Cut story, Journey Complete | `area/story` | - | NAR-02..08, FLOW-49 | `docs/build/areas/story-status.md` |
Live state: `git fetch && git log --oneline main..origin/area/<name>` and that branch's status file.

## Gates each merge into main must pass (`tools/build/gate.sh <area> [commit]`)
Josh: no PR/CI ceremony, every quality check kept, per-merge checks only for what the change touches.
| Check | When | Blocks? |
|---|---|---|
| merge onto main in `../UmbrellaElla-areas/gate` | always | conflicts outside docs/build |
| `tools/ue/build.sh` | Source changed | yes |
| automation tests for the touched prefixes (`tools/build/gate_plan.py`) | Source changed | yes |
| `module_check`, `manifest_check`, `feel_check`, `encounter_check` | when their files changed | yes |
| `tools/build/quality_gate.py`: art (art loop pass record), audio (audio_check + audio_style_check) | art/audio changed | ship only on pass: below-bar pieces stay tracked placeholders |
| `quality_gate.py`: `ui_check ci`, `story_check`, `bake_preset defaults`, `pipeline_check` | always | no new FAIL vs main |
| `submission_check prejam` / `assets` | always / content changed | yes |
| audio critic (`tools/build/critic.sh audio`, blind session per sound id, `tools/audio_loop.py` packet) | sounds changed | no: a failed piece becomes a tracked placeholder (gate commit sets provenance origin `placeholder: audio critic fail`) |
| story critic (`tools/build/critic.sh story`) | story changed | yes |
| encounter critic (`critic.sh encounter`) | keeper/enemy changed | yes once the game writes a run log (DEFERRED before) |
| independent review (`tools/build/review.sh`, area role card, fresh session, not the build lead) | always | one round: changes go back once (exit 3), then follow-ups |
Before each packaged build: `tools/build/prepackage.sh` (full Unreal + Python suites, non-unity build, package, smoke
with input/gamepad/16:9, `ui_check flow-check`, encounter playthrough + critic). Windows: `docs/build/windows-check.md`.

## Continue on Mac (Claude Code)
    cd <your UmbrellaElla clone> && git pull     # area worktrees live in the sibling folder ../UmbrellaElla-areas/
    tools/build/start_area.sh <area>            # starts/continues a worker in ../UmbrellaElla-areas/<area>, log ../UmbrellaElla-areas/logs/<area>.log
    tools/build/push_areas.sh --loop &          # pushes area/* branches every 2 min
    # merge loop, per finished slice (merges in ../UmbrellaElla-areas/gate, pushes main only on PASS):
    tools/build/gate_runner.sh add <area>...; tools/build/gate_runner.sh run   # one gate at a time; logs ../UmbrellaElla-areas/logs/gate-<area>.log
    # gate.sh exit: 0 merged, 1 failed, 3 held for review changes (send review-<area>.txt to the worker once, then re-add)
Workers on one Mac share the engine through `tools/build/ue_slot.sh` (memory-adaptive: 4 at once under 36 GB used, 3 under 44 GB, else 2, none started at 56 GB+).

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
- Flow: queue a level-up that arrives while another screen is open and show it when that screen closes (D-new-levelup-queue); today it is dropped. Next flow pass after flowroute.
- Keeper (review): with OWL-35 off a final hit leaves the fight Active with the model halted; LivesLostThisPhase written, never read; StartTransition zeroes stun without StunEnded; stun does not freeze queued shots; gust push uses unscaled delta.
- Progression: the run-start checkpoint is written before the run-2 reallocation, so a boss retry reverts it.
- Settings must call visuals' SetReducedFlash.
- Core: add a shared source-id header (e.g. `Core/UmbrellaSourceIds.h`, `GUST_Band`, `TALON_Rake`, `MECH_Front_Cast`) and switch health and keeper to it (health request, review of health).
- Keeper: the gust push moves Ella with `AddActorWorldOffset` from the Encounter Director; the motor should own it (one writer of position/velocity).
- DECIDED: flow owns the view target; arena removes its SetViewTarget (sent to arena worker).
- DECIDED: walls and ceiling stop shots (GDD silent). Arena blocks PlayerShot/EnemyShot; health's projectile service must destroy a shot on a blocking hit (tell the health worker on restart).
