# Unreal rules (UE 5.8.4) — read by every role that touches the project

> GDD SH1.0 note (D-new-gdd-sh10): lines on this page that still describe the GDD 1.3 encounter (one owl bolt, the front shield, the 90 s survival timer, wear stages, the 1.3 QA-01..QA-28 tests) are history. The current design is `docs/gdd/GDD-SH1.0.md` and `docs/feature-manifest.json`, which win; the owning role re-files this page against the SH1.0 Rule IDs on its next card.


This file is always loaded. Load an on-demand file when your card needs it:
| File | Load it when |
|---|---|
| `pipeline/unreal/cpp-rules.md` | You write or review C++: modules, C++ vs Blueprint, correctness, the `module_check.py` standard. |
| `pipeline/unreal/gameplay-code.md` | You write or review gameplay code or tests: lanes per component, structure rules, test rules. |
| `pipeline/unreal/commands-and-packaging.md` | You build, test, package, smoke or capture eval shots. |

Items marked [VERIFY] could not be confirmed for 5.8.4 when this was written. The first person to
check one on a real 5.8.4 install edits the file that holds it and removes the tag. `[src: Uxx]` = row in `docs/unreal-sources.md`.

## Project shape (decisions D3, D4, D9, D22, D23)
- 2D with **Paper2D flipbooks**, no PaperZD (a missing plugin build stops the project opening). Enable it explicitly in the `.uproject` Plugins (default: see Editor checks).
- Pawn: `APaperCharacter` + `UCharacterMovementComponent`, plane-constrained: `SetPlaneConstraintEnabled(true)` (or `bConstrainToPlane = true`) and `SetPlaneConstraintNormal(FVector(0,1,0))`. The normal alone does nothing. Play in X/Z. [src: U2, U3]
- Camera: orthographic. Mode from `camera_mode` (`docs/feature-manifest.json` `build_parameters`; default fixed single screen, D9), read at scenario reset; no code assumes one screen. The GameMode sets the arena's placed camera as the view target; the shell's spring-arm camera (collision test off) is not the play view.
- Set Paper2D "Default Pixels Per Unreal Unit" before the first import; it only affects new sprites. Card 0.3 sets a provisional value; card 0.10 confirms it (D-new-port-10). A change after 0.10 re-imports only the 5 anchors. [src: U28]
- Modules: one runtime module `UmbrellaElla`, one editor module `UmbrellaEllaEditor` (data validators).
- Level: one arena map, one owner at a time under an LFS lock; art layers in sublevels (D23). Create maps as non–World Partition levels (Basic/Empty Level, not Open World), or sublevels won't work the classic way. Template maps use World Partition; don't reuse them. [src: U4-U6]

```
UmbrellaElla.uproject                       TD-owned
Config/DefaultEngine.ini                    TD-owned (collision channels, GameDefaultMap, CoreRedirects)
Config/DefaultGame.ini                      TD-owned, except the +MapsToCook= lines: the Integrator adds one per map card.
                                            No tuning lines (tuning defaults live in each F<Comp>Tuning header)
Source/UmbrellaElla.Target.cs, UmbrellaEllaEditor.Target.cs   TD-owned
Source/UmbrellaElla/{UmbrellaElla.Build.cs, Public/, Private/, Private/Tests/}
                                            Every lane includes its tests: Private/Tests/<Area>/**
Source/UmbrellaEllaEditor/
Content/UmbrellaElla/...                    assets, Git LFS (path table below)
tools/ue/                                   build, test, package scripts
```

Content paths (the only ones; every role card, brief and lane uses these):
| What | Path | Owner |
|---|---|---|
| Maps and sublevels | `Content/UmbrellaElla/Maps/` | Integrator |
| Thin Blueprints (`BP_*`), GameMode | `Content/UmbrellaElla/Blueprints/` | Integrator |
| UMG layouts (`WBP_*`) | `Content/UmbrellaElla/UI/` | Integrator |
| Textures, sprites, flipbooks of one asset | `Content/UmbrellaElla/Art/<Asset>/` | Asset Specialist |
| Sounds and sound cues | `Content/UmbrellaElla/Audio/<Sound>/` | Audio |
| Sound classes, submix, concurrency | `Content/UmbrellaElla/Audio/Core/` | Audio (built by TD card 0.4c) |
| Source WAVs (outside Content, never cooked) | `Audio/Source/<Id>/` | Audio |
| Input actions and mapping context | `Content/UmbrellaElla/Input/` | Technical Director |
| Layered source art (outside Content, never cooked) | `Art/Source/<Asset>/` | Asset Specialist |

## Feature flags (GDD SH1.0 CORE-04, §5; checked by `module_check.py` rule M)
- Every non-CONFIRMED feature in `docs/feature-manifest.json` (a record with a `flag`) is built behind that flag, named after its
  ID (`UMB-02` → `UMB_02`), at its manifest default. CONFIRMED features have no flag.
- One source of shipped values: the `// bake:` C++ defaults (flag defaults in `Harness/`, numbers in the
  `F<Comp>Tuning` structs). Nothing else may set them in the submission build: no `UmbrellaTuning` section in any `Config/*.ini`
  (`bake_preset.py defaults` and `check` fail one, and any ini line or Config UPROPERTY that reaches a marked member through another class), no DataAsset, no C++ assignment of a marked member outside the true branch of `#if UMBRELLAELLA_WORKBENCH`, and no marker inside any `#if`/`#else` block (one branch ships).
- Workbench presets: one `UPrimaryDataAsset` of flags and parameters per preset (`DA_Preset_T01` ...), made from the manifest and
  `pipeline/qa/presets.json`, owned by the Test Harness (`Harness/`), loaded only inside `#if UMBRELLAELLA_WORKBENCH` (Workbench
  below). In a workbench build the Encounter Director applies the chosen preset in READY, at scenario reset, as a per-run copy;
  it never writes a class default. A module reads `IsFeatureEnabled(EFeatureId::UMB_02)` from the harness subsystem, never a raw
  bool or a cvar (Editor checks).
- A flag change takes effect only at the next reset unless the module documents a safe runtime change (GDD SH1.0 CORE-04).
- APPROVED_P0 features have flags too (GDD 1.3; T-02 turns some off), default on. With every optional (non-P0) flag off, movement, health, defeat, restart and progression still work (QA-10, `FlagsOffBaselineUnchanged`).
- A feature needing an off feature is refused at reset with one `Warning` naming both IDs (QA-10). Never a crash.

## Workbench: debug and dev builds only (D-new-workbench-debug)
The submission is a Development package (D25), so `!UE_BUILD_SHIPPING` does not keep the workbench out. One compile switch does.
- `UMBRELLAELLA_WORKBENCH` is set only in the Target.cs files, never in a Build.cs or a `#define`: `UmbrellaElla.Target.cs` (the submission) adds `ProjectDefinitions.Add("UMBRELLAELLA_WORKBENCH=0");`; `UmbrellaEllaEditor.Target.cs` and the tester target `UmbrellaEllaWorkbench.Target.cs` add `=1`. `ue_run.py workbench-check` fails anything else. [VERIFY on 5.8.4: `ProjectDefinitions` on a shared-build-environment game target, and the debug-mode switches below]
- Inside `#if UMBRELLAELLA_WORKBENCH`: the panel, sliders, toggles UI, preset load, scenarios, the overlay, note and config export, the `ue.Workbench` console variable and the `Harness` tests. It logs `WORKBENCH_ON debug=<0|1>` once at startup. Test the value, never whether it is defined: the submission target defines it as 0, so `#ifdef` or `#if defined(UMBRELLAELLA_WORKBENCH)` compiles the workbench in. `ue_run.py workbench-check` fails those lines.
- Debug mode: compiled in, the workbench still opens only in debug mode: on in PIE, off in a package until `-Workbench` or `ue.Workbench 1`.
- Testers' builds (the `package.ps1 -Workbench` tester package) can turn everything on: every manifest flag is a toggle and every tunable a slider, each at its default, all toggles off at launch. Debug toggles for testers (cards 0.25, 0.27), off by default, never manifest flags and never `// bake:` defaults, so the submission never has them: `dbg.no_ground_death` (ground impact and health zero do not end the run), `dbg.hover` (no-fall: the player holds her height), `dbg.health_bars` (a numbered `HP cur/max` bar over every damageable actor). Dev settings (card 0.27), each at its GDD 1.3 value by default: `dbg.move_model` (direct steering, the default, or wind-driven travel), 0-2 owl wing gusts with size, speed and height, rise and fall speed inside the §5A ranges. The dev tuning panel is never part of the player's settings menu.
- Outside the switch, in every build: `IsFeatureEnabled` and the tuning structs. With the switch off they return the baked defaults and nothing can change them. Sliders write a per-run copy at scenario reset, never a class default.
- Shipped values: each tunable default line ends `// bake: <feature ID>.<param>`, each flag default `// bake: <feature ID>.enabled`. `tools/bake_preset.py` writes the approved preset's export into them and into the manifest `default_enabled` (`pipeline/checklists/tuning.md`).
- Packaging: `package.ps1` builds the submission target and runs `workbench-check`; `-Workbench` builds the tester package (never submitted, not with `-Shipping`). BUILD_INFO gets `target=` and `workbench=`; the smoke checks `SMOKE_OK ... workbench=` against it.

## Display: 16:9 lock and debug draws (GDD SH1.0 OWL-07, §9)
- The gameplay view is always exactly 16:9. Every map's view target camera (the arena camera the GameMode sets, the
  title and eval cameras too) has Constrain Aspect Ratio on and Aspect Ratio 1.777778 (card 0.8). Any other window or
  screen ratio shows black letterbox (16:10) or pillarbox (21:9) bars; the arena is never stretched or cropped
 . Card 0.4a confirms `bConstrainAspectRatio` letterboxing in a 5.8.4 package (Editor checks).
- UI stays inside the 16:9 view: GDD 1.3 and `pipeline/ui/` give it no room in the bars. Widgets are added to the
  player's screen or under a 16:9 root, never anchored to the window edge. Card 0.21b's 2560x1080 screen_check proves it on 5.8.4. A widget in the bars breaks them, and `screen_check.py` FAILS the screenshot.
- Debug and placeholder visuals never show in a default launch: hitbox and collision draws (`DrawDebug*`, the
  Collision show flag, a visible collision component), on-screen debug text and flat primitive stand-ins appear only
  while the dev flag `ue.Debug` is on, and it is off by default. Collision and hitbox components are hidden in game.
  `-CaptureMode` (card 0.6c) hides them too. The GDD fallback for missing art is still a neutral visible stand-in
  (QA-25), but no default build ships one once the anchors exist.
- Proof, automatic on every smoke (`tools/ue_run.py` smoke contract): `SMOKE_OK ... view=<WxH> aspect=<a>
  debugdraw=0` (the view inside the bars, 16:9 within 0.01, filling the window on one axis), and `-SmokeShot=` takes
  a whole-window screenshot that `art_check.py`, `screen_check.py` and `art_judge.py scene` check. The daily display
  step runs 1280x800 (letterbox) and 2560x1080 (pillarbox). Tests: `UmbrellaElla.Display.World.ViewLocked16x9`,
  `UmbrellaElla.Display.World.DebugDrawOffByDefault` (`pipeline/qa/test-map.md`).

## Smoke hook contract (card 0.6)
The packaged game itself is the evidence of what ships; the regex checks in `bake_preset.py` stay as early warnings.
- Commit compiled in: the package scripts stamp `git rev-parse HEAD` at build start and export it as `UMBRELLAELLA_BUILD_COMMIT`. `UmbrellaElla.Target.cs` passes it on: `ProjectDefinitions.Add("UMBRELLAELLA_BUILD_COMMIT=\"" + (System.Environment.GetEnvironmentVariable("UMBRELLAELLA_BUILD_COMMIT") ?? "unknown") + "\"");`. BUILD_INFO gets the same stamped value; the package script fails if HEAD moved during the build. The hook never reads BUILD_INFO. Card 0.6 confirms on 5.8.4 that a new commit value rebuilds the module (a stale value fails the smoke's commit check).
- The hook logs `SMOKE_EFFECTIVE at=start commit=<compiled commit> workbench=<UMBRELLAELLA_WORKBENCH> platform=<UGameplayStatics::GetPlatformName()> manifest=<the manifest_version the flag table was made from> <field>=<value> ...` once at the first gameplay frame, and the same read as `SMOKE_EFFECTIVE at=end outcome=<survived|fail|quit> ...` when the run ends: at the Survived or fail screen (each restart cycle's fail screen too), else at the `-SmokeQuitAfter` quit. A value written after startup shows at the end. Category `LogUmbrellaElla`, at the start of its log line.
- Where it reads: where gameplay reads, `GetDefault<UUmbrellaTuning>()` (`pipeline/unreal/gameplay-code.md`) and the live harness subsystem (`UHarnessSubsystem`). Both exist on every map, with or without a player, so a no-player map (`pipeline/qa/no-player-maps.txt`) reports the same line.
- How it enumerates: by reflection, never a key list. `TFieldIterator<FStructProperty>` over `UUmbrellaTuning::StaticClass()`, then `TFieldIterator<FProperty>` over each struct, logs each field as `<Struct>.<Field>=<value>` (struct name as reflection gives it, no F prefix, e.g. `UmbrellaFlightTuning.AscentSpeed=300`, manifest units: a `%` key in percent); each flag-table entry as `<ID>.enabled=1|0` by `UHarnessSubsystem::ForEachFlag`, and `manifest=` from its `ManifestVersion()`. Card 0.3 makes that seam (an empty flag table, `GManifestVersion = TEXT("none")`); card 0.27 fills it in `Harness/`. The hook reads no gameplay state name: input=ok is the measured descent, so MVP 2 never edits it. `bake_preset.py` maps a field to its key from the `// bake:` line. A card that marks a key in its own struct, or adds a flag, never edits the hook; the field must be a `UPROPERTY` and its struct a `UPROPERTY` of `UUmbrellaTuning` (card 0.3 adds one per component). UPROPERTY meta tags are editor-only data, so a packaged hook cannot read a `BakeKey` meta. Never from the header text or BUILD_INFO.
- Every Target.cs (game, editor, workbench) passes `UMBRELLAELLA_BUILD_COMMIT` with the line above, since each compiles the hook; `workbench-check` fails a Target.cs without it once one has it.
- Title: with `-SmokeQuitAfter`, the hook passes the title through the title's own Play path (card 0.21), then runs the input check.
- `bake_preset.py effective` fails any live value, on any of the lines, that is not the baked one (else the marked default, else the GDD start) at the commit the game was built from, a marked key the line leaves out, a key given twice, a missing `at=start` or `at=end` line, and at G4 a required key it leaves out.

## Editor checks (card 0.4a clears these on a 5.8.4 install)
Each line is a rule from this file set whose engine fact is not yet confirmed. Clear the tag or rewrite the rule.
- Paper2D is not enabled by default, so the `.uproject` lists it. [VERIFY default in 5.8.4; src: U1]
- A new Basic level has World Partition off. [VERIFY WP is off on a new Basic level]
- Build.cs sets `IWYUSupport = IWYUSupport.Full` (`pipeline/unreal/cpp-rules.md`, Modules). [VERIFY; src: U8]
- Exceptions and RTTI are off by default in UE module builds, which backs the no `try`/`throw`/`dynamic_cast` rule. [VERIFY on 5.8.4]
- `ue.Debug` is a `TAutoConsoleVariable<int32>` and Shipping has no console (`pipeline/unreal/gameplay-code.md`, Debug). [VERIFY macro name, and that Shipping has no console, on 5.8.4]
- Feature flags: a `UPrimaryDataAsset` loaded at scenario reset and a harness subsystem (`UGameInstanceSubsystem`) answering `IsFeatureEnabled` (Feature flags). [VERIFY asset loading and subsystem lifetime on 5.8.4; card 0.4a]
- The world-test helper creates a transient world in code (`pipeline/unreal/gameplay-code.md`, Tests). [VERIFY the world-creation API on 5.8.4; card 0.4a]

## Binary assets (.uasset, .umap)
- Never edit, move, rename or delete them with file tools or git. Only inside the editor.
- `git lfs lock <file>` before you change one; `git lfs locks` must show you. Unlock after merge. `lockable` files stay read-only until locked. [src: U24]
- Never "Save All". Save named packages in your lane. If anything outside your lane is dirty, stop.
- After moves: Fix Up Redirectors on the folder. Main has zero redirectors.
- Close the editor before `git pull`, rebase or branch switch.
- Header or reflection change: close the editor, build with UBT, reopen. Live Coding only for `.cpp` body edits (stricter than Epic). Never save a Blueprint while the log shows `REINST_`. [src: U19, U20]
- Sprite textures: `pipeline/art/art-bible.md`. Never "Apply Paper2D Texture Settings" (Nearest, no mips: wrong for painted art). [src: U27]
- Asset names: Epic prefixes (`T_`, `BP_`, `WBP_`, `M_`, `MI_`, `DT_`). None exist for sprites, flipbooks, input, maps; TD sets them Day 0. [src: U32]

## Agents driving the editor through MCP
Epic's **Unreal MCP** (Experimental in 5.8): TD enables plugins Unreal MCP + All Toolsets. `http://127.0.0.1:8000/mcp`, local, no auth;
`ModelContextProtocol.GenerateClientConfig ClaudeCode` writes `.mcp.json`. Calls run serially on the game thread. [src: U25] [VERIFY tool list; Day-0 card lists it here]
Setup, roles and the kickoff switch: `pipeline/agent-ops/editor-mcp.md` (off by default; Level Designer, Integrator, Art Director, Asset Specialist, UI and UX only; card branch and PR; the card's human opens each changed asset).
1. Script first: write an editor Python script in `pipeline/unreal/editor_scripts/<card>.py` (not a gate path, so the agent can write it), commit it, then run it. One-off MCP edits only for level layout.
2. Lock before touch. Lane folders only. Named saves only. One agent per editor instance.
3. After each binary change, write a text summary `docs/asset-changes/<card>-<asset>.json`: class, parent, changed properties old → new, components, references; for maps, actor list with transforms. Reviewers diff this.
4. MCP agents never create C++ classes or trigger compiles.
5. Stop when a save prompt names a file outside your lane, a file is read-only, the log shows reinstancing, or validation fails twice.
