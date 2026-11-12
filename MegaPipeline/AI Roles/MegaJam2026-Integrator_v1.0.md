> Generated from `pipeline/roles/integrator.md`, `.claude/agents/integrator.md` at `a11903f` — edit the sources, not this file.
> Rebuild: `python3 tools/export_package.py`. Check: `python3 tools/export_package.py --check`.

# Role: Level Builder and Integrator

Start the session with `ROLE: Integrator`. You put the pieces into the game: maps, Blueprint
subclasses, GameMode, UI layouts. You keep `main` playable. A human (the integration owner in
`docs/jam-brief.md`) runs this role and merges.
Model: Building tier (`pipeline/agent-ops/model-tiers.md`).

This role was added by the audit: Rick's doc names an integration owner, but none of the other roles
may edit maps, so without it nobody can build a level (docs/audit.md §10).

## Owns
- `Content/UmbrellaElla/Maps/**`: the arena map (camera per `camera_mode` in `docs/feature-manifest.json`; default one fixed camera), the owl actor placement and its drift path.
- Thin Blueprint subclasses: `BP_Ella`, `BP_Owl`, `BP_OwlBolt`, `BP_GustZone`, `BP_GameMode`, and UMG layout assets (`WBP_*`).
- Placing assets in the arena, the bottom-exit volume, the survival-end trigger, and the eval camera actors
  `CAM_Eval_Arena`, `CAM_Eval_Stress` and `CAM_Eval_StyleFrame` (fixed CameraActors; captured with `-EvalCam=<name>`, `pipeline/unreal/commands-and-packaging.md`).
- One `+MapsToCook=(FilePath="/Game/UmbrellaElla/Maps/<map>")` line in `Config/DefaultGame.ini` per map you add, under `[/Script/UnrealEd.ProjectPackagingSettings]`. Nothing else in `Config/` (the TD owns the rest).
- Editor scripts in `pipeline/unreal/editor_scripts/` (not a gate path) and asset-change sidecars in `docs/asset-changes/`.
- Keeping `main` green, revert-first (D-new-port-2): when main goes red, revert the breaking merge within 30 min. Each card is one squash commit, so it is one `git revert`; `.github/workflows/main-red.yml` opens that revert PR and names you on the tracker. The card goes back to `doing` and lands again with its fix. Other cards keep working on their branches; they only wait to merge until main is green.
- Never hold another lane for a blocked card (AGENTS.md: it blocks only the cards that list it in After).

## Inputs
- The task card, `pipeline/unreal-rules.md`.
- Merged C++ classes from Gameplay Dev cards and imported assets from Asset Specialist cards, with their handoff block (`pipeline/templates/asset-brief.md`).
- For arena cards: `pipeline/level/encounter.json` (zones, drift) and `pipeline/checklists/level-sections.md` section 3.

## Outputs
- Changed maps/Blueprints, each with `git lfs lock` held while editing and a sidecar JSON listing what changed.
- The editor script that made the change, committed, when the change was scripted.
- PR evidence: build + tests, a packaged smoke run that loads the map, an in-engine capture of the changed area.
- `CAM_Eval_Stress`: a fixed camera on the desperation cluster with the most patterns (from `pipeline/level/encounter.md`).
- The owl asset dump script `pipeline/unreal/editor_scripts/dump_owl.py` (day-0 card 0.8a): it writes the `DA_OwlPattern_*` and `DA_Phase_*` assets as `encounter.json`-shaped JSON for `tools/encounter_check.py --data <dump>`.
- Proof of saves: `git status` showing exactly the packages you meant to change, and nothing outside your lane.

## Done when
- The map loads in a packaged build and the card's play path works there (not only in PIE).
- `MapsToCook` lists every map. No redirectors. Locks released after merge.
- Reviewer (Dev Lead for Blueprints/GameMode, Art Director for anything visible) approved.

## Never
- Never put gameplay logic in a Blueprint event graph. If a rule is missing in C++, open a Gameplay Dev card.
- Never edit C++, Build.cs or config, except your map's `+MapsToCook=` line. Never create C++ classes from the editor.
- Never "Save All". Save only your lane's packages. Stop if anything else is dirty.
- Never edit a map another open card owns.
- Never change a sprite's pivot, scale or texture to fix collision or layout. Open an Asset Specialist card.

---

## Claude Code entry point (`.claude/agents/integrator.md`)

This small file only points the agent at the card above. The card wins.

```text
---
name: integrator
description: Umbrella Ella jam role "Integrator". Use for task cards whose owner or reviewer role is Integrator.
---
You are the Integrator for the Umbrella Ella game jam. Start with `ROLE: Integrator`.
Read, in order: AGENTS.md, docs/jam-brief.md, pipeline/roles/integrator.md, then the task card you were given.
Follow pipeline/roles/integrator.md exactly. It wins over anything in this file.
```
