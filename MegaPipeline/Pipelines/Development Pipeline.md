> Generated from `pipeline/unreal-rules.md`, `pipeline/unreal/cpp-rules.md`, `pipeline/unreal/gameplay-code.md`, `docs/unreal-sources.md`, `pipeline/checklists/file-hygiene.md`, `.github/PULL_REQUEST_TEMPLATE.md`, `evals/reviewer/results.md`, `tools/run_reviewer_eval.py`, `tools/score_review.py`, `tools/check_pr.py` at `fbcd307` — edit the sources, not this file.
> Rebuild: `python3 tools/export_package.py`. Check: `python3 tools/export_package.py --check`.

# Development Pipeline

A readable copy for people. Agents load these rules from the repo paths listed below.

## About this pipeline

- **Purpose:** Write and review gameplay C++ on Unreal 5.8.4 to one standard, with tests and a review gate.
- **Owner:** Dev Lead (review) and Gameplay Dev (code).
- **Inputs:** A ready task card, the Unreal rules, the engine headers.
- **Outputs:** Code PRs with evidence, review verdicts, reviewer eval results.
- **Gates:** Dev Lead review on every code PR; `check_pr.py` on the PR body; the reviewer eval when the review prompt or model changes.

## Built from

- Unreal rules: `pipeline/unreal-rules.md`, `pipeline/unreal/cpp-rules.md`, `pipeline/unreal/gameplay-code.md`, `docs/unreal-sources.md`
- Checklists: `pipeline/checklists/file-hygiene.md`
- Pull request template: `.github/PULL_REQUEST_TEMPLATE.md`
- Reviewer eval: `evals/reviewer/results.md`, `tools/run_reviewer_eval.py`, `tools/score_review.py`
- Commands and checks: `tools/check_pr.py`

## Unreal rules

### `pipeline/unreal-rules.md`

#### Unreal rules (UE 5.8.4) — read by every role that touches the project

> GDD SH1.0 note (D-new-gdd-sh10): lines on this page that still describe the GDD 1.3 encounter (one owl bolt, the front shield, the 90 s survival timer, wear stages, the 1.3 QA-01..QA-28 tests) are history. The current design is `docs/gdd/GDD-SH1.0.md` and `docs/feature-manifest.json`, which win; the owning role re-files this page against the SH1.0 Rule IDs on its next card.


This file is always loaded. Load an on-demand file when your card needs it:
| File | Load it when |
|---|---|
| `pipeline/unreal/cpp-rules.md` | You write or review C++: modules, C++ vs Blueprint, correctness, the `module_check.py` standard. |
| `pipeline/unreal/gameplay-code.md` | You write or review gameplay code or tests: lanes per component, structure rules, test rules. |
| `pipeline/unreal/commands-and-packaging.md` | You build, test, package, smoke or capture eval shots. |

Items marked [VERIFY] could not be confirmed for 5.8.4 when this was written. The first person to
check one on a real 5.8.4 install edits the file that holds it and removes the tag. `[src: Uxx]` = row in `docs/unreal-sources.md`.

##### Project shape (decisions D3, D4, D9, D22, D23)
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

##### Feature flags (GDD SH1.0 CORE-04, §5; checked by `module_check.py` rule M)
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

##### Workbench: debug and dev builds only (D-new-workbench-debug)
The submission is a Development package (D25), so `!UE_BUILD_SHIPPING` does not keep the workbench out. One compile switch does.
- `UMBRELLAELLA_WORKBENCH` is set only in the Target.cs files, never in a Build.cs or a `#define`: `UmbrellaElla.Target.cs` (the submission) adds `ProjectDefinitions.Add("UMBRELLAELLA_WORKBENCH=0");`; `UmbrellaEllaEditor.Target.cs` and the tester target `UmbrellaEllaWorkbench.Target.cs` add `=1`. `ue_run.py workbench-check` fails anything else. [VERIFY on 5.8.4: `ProjectDefinitions` on a shared-build-environment game target, and the debug-mode switches below]
- Inside `#if UMBRELLAELLA_WORKBENCH`: the panel, sliders, toggles UI, preset load, scenarios, the overlay, note and config export, the `ue.Workbench` console variable and the `Harness` tests. It logs `WORKBENCH_ON debug=<0|1>` once at startup. Test the value, never whether it is defined: the submission target defines it as 0, so `#ifdef` or `#if defined(UMBRELLAELLA_WORKBENCH)` compiles the workbench in. `ue_run.py workbench-check` fails those lines.
- Debug mode: compiled in, the workbench still opens only in debug mode: on in PIE, off in a package until `-Workbench` or `ue.Workbench 1`.
- Testers' builds (the `package.ps1 -Workbench` tester package) can turn everything on: every manifest flag is a toggle and every tunable a slider, each at its default, all toggles off at launch. Debug toggles for testers (cards 0.25, 0.27), off by default, never manifest flags and never `// bake:` defaults, so the submission never has them: `dbg.no_ground_death` (ground impact and health zero do not end the run), `dbg.hover` (no-fall: the player holds her height), `dbg.health_bars` (a numbered `HP cur/max` bar over every damageable actor). Dev settings (card 0.27), each at its GDD 1.3 value by default: `dbg.move_model` (direct steering, the default, or wind-driven travel), 0-2 owl wing gusts with size, speed and height, rise and fall speed inside the §5A ranges. The dev tuning panel is never part of the player's settings menu.
- Outside the switch, in every build: `IsFeatureEnabled` and the tuning structs. With the switch off they return the baked defaults and nothing can change them. Sliders write a per-run copy at scenario reset, never a class default.
- Shipped values: each tunable default line ends `// bake: <feature ID>.<param>`, each flag default `// bake: <feature ID>.enabled`. `tools/bake_preset.py` writes the approved preset's export into them and into the manifest `default_enabled` (`pipeline/checklists/tuning.md`).
- Packaging: `package.ps1` builds the submission target and runs `workbench-check`; `-Workbench` builds the tester package (never submitted, not with `-Shipping`). BUILD_INFO gets `target=` and `workbench=`; the smoke checks `SMOKE_OK ... workbench=` against it.

##### Display: 16:9 lock and debug draws (GDD SH1.0 OWL-07, §9)
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

##### Smoke hook contract (card 0.6)
The packaged game itself is the evidence of what ships; the regex checks in `bake_preset.py` stay as early warnings.
- Commit compiled in: the package scripts stamp `git rev-parse HEAD` at build start and export it as `UMBRELLAELLA_BUILD_COMMIT`. `UmbrellaElla.Target.cs` passes it on: `ProjectDefinitions.Add("UMBRELLAELLA_BUILD_COMMIT=\"" + (System.Environment.GetEnvironmentVariable("UMBRELLAELLA_BUILD_COMMIT") ?? "unknown") + "\"");`. BUILD_INFO gets the same stamped value; the package script fails if HEAD moved during the build. The hook never reads BUILD_INFO. Card 0.6 confirms on 5.8.4 that a new commit value rebuilds the module (a stale value fails the smoke's commit check).
- The hook logs `SMOKE_EFFECTIVE at=start commit=<compiled commit> workbench=<UMBRELLAELLA_WORKBENCH> platform=<UGameplayStatics::GetPlatformName()> manifest=<the manifest_version the flag table was made from> <field>=<value> ...` once at the first gameplay frame, and the same read as `SMOKE_EFFECTIVE at=end outcome=<survived|fail|quit> ...` when the run ends: at the Survived or fail screen (each restart cycle's fail screen too), else at the `-SmokeQuitAfter` quit. A value written after startup shows at the end. Category `LogUmbrellaElla`, at the start of its log line.
- Where it reads: where gameplay reads, `GetDefault<UUmbrellaTuning>()` (`pipeline/unreal/gameplay-code.md`) and the live harness subsystem (`UHarnessSubsystem`). Both exist on every map, with or without a player, so a no-player map (`pipeline/qa/no-player-maps.txt`) reports the same line.
- How it enumerates: by reflection, never a key list. `TFieldIterator<FStructProperty>` over `UUmbrellaTuning::StaticClass()`, then `TFieldIterator<FProperty>` over each struct, logs each field as `<Struct>.<Field>=<value>` (struct name as reflection gives it, no F prefix, e.g. `UmbrellaFlightTuning.AscentSpeed=300`, manifest units: a `%` key in percent); each flag-table entry as `<ID>.enabled=1|0` by `UHarnessSubsystem::ForEachFlag`, and `manifest=` from its `ManifestVersion()`. Card 0.3 makes that seam (an empty flag table, `GManifestVersion = TEXT("none")`); card 0.27 fills it in `Harness/`. The hook reads no gameplay state name: input=ok is the measured descent, so MVP 2 never edits it. `bake_preset.py` maps a field to its key from the `// bake:` line. A card that marks a key in its own struct, or adds a flag, never edits the hook; the field must be a `UPROPERTY` and its struct a `UPROPERTY` of `UUmbrellaTuning` (card 0.3 adds one per component). UPROPERTY meta tags are editor-only data, so a packaged hook cannot read a `BakeKey` meta. Never from the header text or BUILD_INFO.
- Every Target.cs (game, editor, workbench) passes `UMBRELLAELLA_BUILD_COMMIT` with the line above, since each compiles the hook; `workbench-check` fails a Target.cs without it once one has it.
- Title: with `-SmokeQuitAfter`, the hook passes the title through the title's own Play path (card 0.21), then runs the input check.
- `bake_preset.py effective` fails any live value, on any of the lines, that is not the baked one (else the marked default, else the GDD start) at the commit the game was built from, a marked key the line leaves out, a key given twice, a missing `at=start` or `at=end` line, and at G4 a required key it leaves out.

##### Editor checks (card 0.4a clears these on a 5.8.4 install)
Each line is a rule from this file set whose engine fact is not yet confirmed. Clear the tag or rewrite the rule.
- Paper2D is not enabled by default, so the `.uproject` lists it. [VERIFY default in 5.8.4; src: U1]
- A new Basic level has World Partition off. [VERIFY WP is off on a new Basic level]
- Build.cs sets `IWYUSupport = IWYUSupport.Full` (`pipeline/unreal/cpp-rules.md`, Modules). [VERIFY; src: U8]
- Exceptions and RTTI are off by default in UE module builds, which backs the no `try`/`throw`/`dynamic_cast` rule. [VERIFY on 5.8.4]
- `ue.Debug` is a `TAutoConsoleVariable<int32>` and Shipping has no console (`pipeline/unreal/gameplay-code.md`, Debug). [VERIFY macro name, and that Shipping has no console, on 5.8.4]
- Feature flags: a `UPrimaryDataAsset` loaded at scenario reset and a harness subsystem (`UGameInstanceSubsystem`) answering `IsFeatureEnabled` (Feature flags). [VERIFY asset loading and subsystem lifetime on 5.8.4; card 0.4a]
- The world-test helper creates a transient world in code (`pipeline/unreal/gameplay-code.md`, Tests). [VERIFY the world-creation API on 5.8.4; card 0.4a]

##### Binary assets (.uasset, .umap)
- Never edit, move, rename or delete them with file tools or git. Only inside the editor.
- `git lfs lock <file>` before you change one; `git lfs locks` must show you. Unlock after merge. `lockable` files stay read-only until locked. [src: U24]
- Never "Save All". Save named packages in your lane. If anything outside your lane is dirty, stop.
- After moves: Fix Up Redirectors on the folder. Main has zero redirectors.
- Close the editor before `git pull`, rebase or branch switch.
- Header or reflection change: close the editor, build with UBT, reopen. Live Coding only for `.cpp` body edits (stricter than Epic). Never save a Blueprint while the log shows `REINST_`. [src: U19, U20]
- Sprite textures: `pipeline/art/art-bible.md`. Never "Apply Paper2D Texture Settings" (Nearest, no mips: wrong for painted art). [src: U27]
- Asset names: Epic prefixes (`T_`, `BP_`, `WBP_`, `M_`, `MI_`, `DT_`). None exist for sprites, flipbooks, input, maps; TD sets them Day 0. [src: U32]

##### Agents driving the editor through MCP
Epic's **Unreal MCP** (Experimental in 5.8): TD enables plugins Unreal MCP + All Toolsets. `http://127.0.0.1:8000/mcp`, local, no auth;
`ModelContextProtocol.GenerateClientConfig ClaudeCode` writes `.mcp.json`. Calls run serially on the game thread. [src: U25] [VERIFY tool list; Day-0 card lists it here]
Setup, roles and the kickoff switch: `pipeline/agent-ops/editor-mcp.md` (off by default; Level Designer, Integrator, Art Director, Asset Specialist, UI and UX only; card branch and PR; the card's human opens each changed asset).
1. Script first: write an editor Python script in `pipeline/unreal/editor_scripts/<card>.py` (not a gate path, so the agent can write it), commit it, then run it. One-off MCP edits only for level layout.
2. Lock before touch. Lane folders only. Named saves only. One agent per editor instance.
3. After each binary change, write a text summary `docs/asset-changes/<card>-<asset>.json`: class, parent, changed properties old → new, components, references; for maps, actor list with transforms. Reviewers diff this.
4. MCP agents never create C++ classes or trigger compiles.
5. Stop when a save prompt names a file outside your lane, a file is read-only, the log shows reinstancing, or validation fails twice.

### `pipeline/unreal/cpp-rules.md`

#### C++ rules (on demand; core: `pipeline/unreal-rules.md`)

Load when you write or review C++. The Dev Lead reviews every rule here.

##### Modules are this project's "assembly definitions"
A module = `Source/<Name>/<Name>.Build.cs` + `Public/` + `Private/`. Dependencies go in Build.cs:
Private by default; Public only when that module's types appear in your Public headers. Cross-module
symbols need the `UMBRELLAELLA_API` macro. Turn on `IWYUSupport = IWYUSupport.Full` (unconfirmed: core, Editor checks).
Where the comparison to Unity breaks:
1. Blueprints and assets ignore module boundaries. Any asset can reference anything. Asset rules need editor data validators.
2. Public/Private is a convention. A relative include into another module's `Private/` compiles. `tools/module_check.py` catches it (and missing Build.cs deps, missing `_API`, generated.h order, and the C++ standard rules h-P below).
3. Editor builds are per-module DLLs; packaged games are one executable. Only a package proves it links.
4. UBT's merged "unity" builds hide missing includes. Run a non-unity build (`NONUNITY=1 tools/ue/build.sh`: `-DisableUnity -NoPCH -NoSharedPCH`) before each gate, and paste its last line (`build exit: 0  mode=nonunity ...`) on every PR that touches anything under `Source/` (a `.cpp` that leans on another file's include merges green in a unity build). D-new-nonunity-pr. [VERIFY flags; src: U7]
   Headers forward-declare (`class UFoo;`) a project type they use only by pointer, reference or `TObjectPtr`, and include it in the `.cpp` (rule I).
5. Adding a module means regenerating project files and restarting the editor.

##### C++ vs Blueprint (agents can diff text, not .uasset)
1. All gameplay rules in C++: umbrella state, vertical velocity, the firing lane, health, damage, owl patterns, survival end, win/lose. Put the rule core in plain functions so tests can call them without a world.
2. Blueprints are thin data subclasses (`BP_Ella : AEllaCharacter`) that only set asset references. No event-graph logic except cosmetic triggers.
3. Tuning lives in text: each component's `F<Comp>Tuning` struct defaults, gathered in the `UDeveloperSettings` class `UUmbrellaTuning` (`UCLASS(Config=Game, defaultconfig)`; no `defaultconfig` = saves to `Saved/`). Never edit tuning in Project Settings (that writes a `[/Script/UmbrellaElla.UmbrellaTuning]` section into `DefaultGame.ini`, which would override the baked defaults at runtime; `bake_preset.py defaults` and `check` fail any such section). Never hard-coded numbers in logic. [src: U22]
4. UI: C++ `UUserWidget` with `meta=(BindWidget)`; the UMG asset is layout only. Designer widget name = C++ property name, or the BP won't compile. [src: U23]
5. Asset references: `UPROPERTY(EditDefaultsOnly) TObjectPtr<...>` set in the BP. No `ConstructorHelpers` hard-coded paths.
6. Input: Enhanced Input (`IA_Move`, `IA_Attack`, `IA_Shield`, `IA_Pause`, `IA_Retry`, `IMC_Default`, `IMC_Menu`; GDD SH1.0 MOVE-04, DEC-01: hold `IA_Attack` = ATTACK_DESCENT with auto-fire (COM-01), hold `IA_Shield` = SHIELD_DESCENT (DEF-01), shield wins, release both = UP_OPEN; bindings in `docs/game-spec.md`). Menus (title, pause, win, lose) use `IMC_Menu` at priority 10: Flow adds it and removes `IMC_Default` when a menu opens, and reverses that when it closes, so gameplay actions never fire under a menu. [VERIFY priority and consume behavior on 5.8.4] Stick dead zones live in the `IA_Move` Dead Zone modifier, never in C++ (rule H). World test `UmbrellaElla.Flow.World.MenuBlocksGameplayInput` (card 0.21, checked by the TD): open a menu, inject `IA_Attack` and `IA_Shield`, assert the umbrella state did not change; done when it passes in `check_automation_report.py` output. [VERIFY input injection API on 5.8.4] No raw key polling (`IsInputKeyDown` and friends; module_check rule u). Hold vs toggle is D18. C++: `EnhancedInput` in Build.cs; `UEnhancedInputLocalPlayerSubsystem::AddMappingContext`; `BindAction` on `UEnhancedInputComponent` inside each component's own `BindInput`, which the character shell calls from `SetupPlayerInputComponent` (Movement binds `IA_Move`, Umbrella `IA_Attack` and `IA_Shield`, Flow `IA_Pause` and `IA_Retry`). [src: U30]
7. Collision channels defined in `DefaultEngine.ini` and mirrored in one C++ header. They must match.

##### C++ correctness rules (the reviewer checks every one)
- Every UObject member: `UPROPERTY()` + `TObjectPtr<>`. Non-owning: `TWeakObjectPtr`. Check with `IsValid()`.
- Functions bound with `AddDynamic` are `UFUNCTION()`.
- Overrides call `Super::`. `CreateDefaultSubobject` only in constructors.
- `#include "X.generated.h"` is the last include in its header.
- Movement and timers scale by `DeltaTime`.
- No gameplay logic inside `check()` (its expression is not evaluated in Shipping). `ensure()` always evaluates and reports once per session. `if (!ensure(Ptr)) return;` as a guard is fine; never make gameplay depend on it firing. Must-run expressions: `verify()`. [src: U9]
- Timers and lambdas never capture raw `this` on destroyable actors, and a deferred lambda never captures by reference (`[&]`, `&Local`) or with `[=]` (it captures `this` implicitly); use `CreateUObject`, `CreateWeakLambda(this, ...)` or capture by value (rule x, also for a lambda stored in a variable first).
- Every engine API you introduce that is not already used elsewhere in `Source/`: cite its engine header in the PR (`Engine/Source/.../X.h`). Reviewers block an API they don't recognize when it has no citation.
- `override` on every override (module_check rule m checks the common engine ones, including `NotifyHit`, `NotifyActorBeginOverlap`/`EndOverlap`, `Falling`, `OnMovementModeChanged` [VERIFY names on 5.8.4]). A member function that writes no member is `const`, whatever its name (`ComputeLift`); rule A checks only `Get`/`Is`/`Has`/`Can`/`Should`, the reviewer checks the rest. Getters are `const` (rule A); no `const` on a by-value return type (rule B). Gameplay state members are `private` (expose with `meta=(AllowPrivateAccess)` or a getter); tuning and asset references may be `protected` (rule C: a protected data member must be a `UPROPERTY` with `EditDefaultsOnly`, `EditAnywhere` or `EditInstanceOnly`, or an `F*Tuning` struct); any public data member of a `UCLASS`, `UPROPERTY` or not, is rule C (only the `UDeveloperSettings` class `UUmbrellaTuning` is exempt). `final` on a C++ class nothing derives from, including Blueprints [VERIFY UHT accepts it on a UCLASS; owner TD, done when a compile log of a `final` UCLASS is pasted here; rule K is written and runs only with `module_check.py --rules K` until this tag is removed, then by default; see `pipeline/roles/technical-director.md`]. A by-value `bool` parameter on a `UCLASS` member function (`Move(true)`) is rule J; use an enum or two functions. `Set<X>(bool)`, `On<X>` delegate handlers and static rule functions are exempt (D-new-bool-param).
- One reflected type (`UCLASS`/`USTRUCT`) per header, named after the file without its prefix (`UUmbrellaComponent` in `UmbrellaComponent.h`); a small enum or struct used only by that type may stay. Rule e checks the generated header name; the reviewer checks the rest.
- One state change per statement: no assignment inside an `if`/`while` condition, no chained `A = B = C`, no `++` or assignment inside a call argument or a ternary.
- Never order gameplay by `TMap`/`TSet` iteration (not repeatable across runs); sort the keys or keep a `TArray`.
- Renamed or removed reflected names (`UCLASS`, `UPROPERTY`, ...) need a `[CoreRedirects]` entry, e.g. `+ClassRedirects=(OldName="/Script/UmbrellaElla.Old",NewName="/Script/UmbrellaElla.New")`, or asset data is lost silently. [src: U21]

##### C++ standard, checked by `tools/module_check.py` (rules h-P; full list: `python3 tools/module_check.py --help`)
Epic's coding standard, mechanical part. CI fails on any finding, so reviewers don't spend review cycles on these.
`#pragma once` in every header · `nullptr`, never `NULL` · no `std::`, STL headers, exceptions or `dynamic_cast` · no `LogTemp` · no `using namespace` ·
`override` on engine virtuals · bools named `bX`, bitfields too (`uint8 bX : 1`); bool functions start `Is`/`Has`/`Can`/`Should` · braces on every `if`/`else`/`for`/`while` body ·
every `switch` has `default:` · `TEXT()` on every string literal in code (level names, asset paths, logs; not `#` lines, `UPROPERTY` specifiers or `LOCTEXT`) · console variables and cheats inside `#if !UE_BUILD_SHIPPING`, no `UFUNCTION(Exec)` ·
indent with tabs (tab size 4) · no raw key polling · a looping `SetTimer` (loop argument not `false`) is cleared in `EndPlay` in the same `.cpp` ·
type prefixes `U`/`A`/`F`/`E`/`T`/`I`, PascalCase members, locals and parameters (w) · no by-reference, `[=]` or raw-`this` capture in deferred lambdas, inline or stored (x) ·
no `auto` except lambda variables and range-for (y) · every enum is `enum class`, and a `UENUM` is `enum class E... : uint8` (z) · const getters (A), no const by-value return (B) ·
no public data member in a `UCLASS`, and protected only for tuning and asset refs (C) · UObjects passed by pointer, never `UObject&` (D) · `#define` names start `UMBRELLAELLA_` (E) ·
a delegate bound on another object is removed in `EndPlay` (F) · no number in `.cpp` logic except 0, 0.5, 1, 2, and a `const` in the `.cpp` does not make one OK; tuning goes in `F<Comp>Tuning`, a true constant in a header as `static constexpr` (G; D-new-magic-numbers) ·
no dead zone in C++ (H) · forward-declare what a header uses only by pointer (I) · no file-scope `using X::Y;` (l) · no behavior-picking `bool` parameter (J) · the `AEllaCharacter` shell defines only its constructor and `SetupPlayerInputComponent`, which calls only `AddMappingContext` and each component's `BindInput` (L) ·
no wall-clock read or unseeded random outside `Harness/` and tests: world time and the preset-seeded `FRandomStream` (N; GDD QA-08) · no mutable `static` data or static delegates, since PIE keeps the module loaded (O) · a getter never returns a non-const `TArray`/`TMap`/`TSet` reference or pointer (P).
Run it before every PR that touches `Source/` and paste the output.

### `pipeline/unreal/gameplay-code.md`

#### Gameplay code and tests (on demand; core: `pipeline/unreal-rules.md`)

> GDD SH1.0 note (D-new-gdd-sh10): lines on this page that still describe the GDD 1.3 encounter (one owl bolt, the front shield, the 90 s survival timer, wear stages, the 1.3 QA-01..QA-28 tests) are history. The current design is `docs/gdd/GDD-SH1.0.md` and `docs/feature-manifest.json`, which win; the owning role re-files this page against the SH1.0 Rule IDs on its next card.


Load when you write or review gameplay code or tests. C++ rules: `pipeline/unreal/cpp-rules.md`.

##### Code layout: lanes = GDD SH1.0 CORE-04 modules (so cards can run in parallel)
Each module is its own component with its own folder under `Source/UmbrellaElla/{Public,Private}/` and its tests under
`Private/Tests/<Folder>/`. A module never does what GDD SH1.0 CORE-04 says it "must not own".
| Module | Owns | Folder | MVP / features |
|---|---|---|---|
| Input Adapter | Keyboard/controller holds → requested actions (steer, ATTACK, SHIELD, pause, retry); bindings as data; no physics or attack timing | `Input/` | 2, 3, 9, 10 |
| Player Motor | Horizontal motion, gravity, lift force, collisions, bounds and the bottom boundary. The only writer of velocity | `Motor/`, `Arena/` | 1, 2, 3 (CORE-01, CORE-02) |
| Umbrella State | The state enum (UP_OPEN, ATTACK_DESCENT, SHIELD_DESCENT, OPEN_LEFT, OPEN_RIGHT, INVERTED, DEFEATED; NO_LIFT is derived, not a state) and its transitions; priority lockout > SHIELD > ATTACK > UP_OPEN | `Umbrella/` | 2, 9, 10 (UMB-01..04, DEF-01) |
| Attack Emitter | Fixed +X player bolts during ATTACK_DESCENT: first on entry, then every cadence; start/stop and cooldown; muzzle is a named socket | `Attack/` | 9 (COM-01, UMB-02) |
| Defense Receiver | Front shield catches during SHIELD_DESCENT; consumes the shot, emits CatchSucceeded; never changes health. Side catch filters (UMB-03, off) | `Defense/` | 10 (DEF-01; UMB-03) |
| Health/Condition | The one HP value, damage, invulnerability, shield heal and its cooldown, HP → wear stage; requests defeat. No lift change unless SURV-04 | `Health/` | 4, 10 (CORE-03, SURV-02, SURV-03; SURV-04) |
| Projectile Service | Spawn, motion, telegraph, collision reports, lifetime | `Projectile/` | 7 |
| Boss Director | Owl attack schedule and telegraphs, hit-region reactions, departure pose. No collision routing, player HP, camera or timer (data types: card 0.5b) | `Owl/` | 7 (OWL-01..04; COM-02..04 reactions) |
| Hit Region Router | CLOCK and BODY colliders with stable IDs, CLOCK priority, one BossTargetHit per projectile; sizes from gameplay collision config, never from art | `Owl/HitRegion/` | 7 (OWL-05) |
| Wind/Hazard Field | Force and hazard zones, warnings, optional wear events; the environmental current and owl gusts are separate owners | `Field/` | 11 (WIND-01); WIND-02, OWL-02 zone, HAZ-01 |
| Encounter Director | READY, ACTIVE, ENDING_SUCCESS, ENDING_FAILURE, RESTARTING, PAUSED; the completion rule; title, fail and Survived flow | `Encounter/` | 4, 5, 6 (END-01, FLOW-01) |
| Feedback Adapter | State/event → sound, FX, damage flashes, clock-hit cue; diegetic indicators. Never gameplay authority | `Feedback/` | VFX-01; every cue |
| Animation Presenter | Resolved state → Paper 2D flipbook from the visual asset map; stable pivot; neutral fallback when art is missing. Never collision, velocity or cadence | `Feedback/Anim/` | 12 (ANIM-01; ART-02) |
| Background Presenter | Two looping layers behind the fixed camera, far slower than near; static fallback. Never camera, hitboxes or wind | `Feedback/Background/` | 12 (BG-01) |
| Test Harness | Feature flags, presets, scenarios, seed, run log, note export; dev builds only (cards 0.25-0.27, 0.23) | `Harness/`, `RunLog/` | 8 (QA-BASE) |
| Core (TD) | `UUmbrellaTuning` (settings), collision header, `AEllaCharacter` shell, `UmbrellaDrawOrder.h`, log category, event types | `Core/` | TD-owned |
MVP 4 is two cards: Health, then the Encounter Director defeat card (`BottomExitFailsRun`). The Encounter cards for MVP 4, 5
and 6 run one after another. Each module's rule core is a plain function or struct (e.g. `FMotorRules::NextVerticalVelocity`)
that tests call without a world.

##### Events and encounter states (GDD SH1.0 CORE-04, §7B, §8)
- Modules talk through the GDD 1.3 event vocabulary, one native multicast delegate each, declared in `Core/`:
  UmbrellaConfigChanged, LiftAvailabilityChanged, PlayerHealthChanged, ProjectileSpawned, ProjectileContact, CatchAttempt,
  CatchSucceeded, CatchFailed, BossTargetHit, BossAttackTelegraphed, WindEntered, WindExited, PlayerDefeated,
  EncounterCompleted, AnimationCue, BackgroundLooped, TestPresetLoaded (the list in `docs/feature-manifest.json` `events`). Each payload carries frame,
  source ID, target ID, run/config ID and the relevant feature IDs. No circular hard reference between Player Motor, Health/Condition and Boss Director.
- An unknown event or a missing asset logs a `Warning` and falls back to a visible neutral stand-in at the gameplay anchor; it never crashes.
- Art is a replaceable placeholder (GDD SH1.0 CORE-05). Movement, fall speed, hitboxes, projectile radius, spawn direction, health and
  outcome never read sprite size, scale, pose, alpha or background offset. Art swaps never change velocity, HP or the seeded schedule (QA-25, QA-26).
- The Encounter Director owns the encounter state as one `UENUM` with exactly the six GDD SH1.0 OWL-06, OWL-35 states. RESTARTING clears every
  projectile, timer and module state, reloads the preset and returns to READY. PAUSED has one owner and freezes timer, projectiles, animation, background and attack scheduling. Defeat and completion in one update: defeat wins, one terminal event.

- `AEllaCharacter` is a shell. Constructor: create the components, spring arm and orthographic camera, set the plane constraint.
  `SetupPlayerInputComponent`: add `IMC_Default` at priority 0, then call `BindInput(UEnhancedInputComponent*)` on each component. Nothing else; no rule and no `BindAction` in the character.
- Tuning: each component owns a `USTRUCT() F<Comp>Tuning` in its own Public folder (e.g. `Public/Attack/AttackTuning.h`). Exception: the umbrella's is `FUmbrellaFlightTuning` in `Public/Umbrella/UmbrellaFlightTuning.h`, because `FUmbrellaTuning` would clash with the settings class `UUmbrellaTuning` (same reflected name and same `.generated.h`). Each struct holds every number,
  its default, units and clamps. `UUmbrellaTuning` (Core) has one `UPROPERTY(Config)` member per struct, added by the TD in card 0.3.
  A new number = edit your own struct; read it with `GetDefault<UUmbrellaTuning>()->Attack.CooldownSeconds`. A number the workbench can change ends its default line with `// bake: <feature ID>.<param>` (`pipeline/unreal-rules.md`, Workbench).
- The Feedback Adapter only reads other modules' state (getters, events) and drives flipbooks, audio, FX and camera. It never writes gameplay state.
  Each sound event prints its `AUDIO:` line through the card 0.5a logger (`pipeline/audio/audio-rules.md` section 3).

##### Gameplay structure rules (the reviewer checks these too)
- One writer per fact. Each fact has one owning module, and only it writes the fact. Only the Player Motor writes velocity and gravity scale; it reads the resolved configuration from Umbrella State and applies lift only for UP_OPEN. NO_LIFT is plain gravity: no multiplier, no fast fall (GDD SH1.0 MOVE-19). No second copy of a state elsewhere.
  Others ask through named calls only, e.g. `ResetForRestart()` (Encounter Director).
- A component that writes `CharacterMovement->Velocity` ticks before movement: in `BeginPlay`, `Move->AddTickPrerequisiteComponent(this)`. Otherwise the write lands before or after gravity depending on order. A rule step that crosses a threshold inside one frame (e.g. braking past zero into rising) splits the step at the threshold, so the result does not depend on frame rate. [VERIFY on 5.8.4]
- "Falling" means one thing everywhere: `CharacterMovement->IsFalling()` (airborne, MovementMode Falling) and `Velocity.Z < 0`. `Velocity.Z < 0` alone is not falling (walking downhill). "Rising" = airborne and `Velocity.Z > 0`. The umbrella state is separate from both.
- Defeat and restart: Health/Condition owns health and broadcasts `PlayerDefeated` at zero; the Encounter Director owns ENDING_FAILURE, the fail screen and RESTARTING (D5). Health never moves the player or reloads anything.
- Game invariants are numbered (`INV-1`, `INV-2`, ...) in the comment block at the top of the owning component's header, e.g. `INV-1: no damage after the survival-end trigger`. Each has a test whose name or comment cites the number.
- State: each component and gameplay actor keeps its state as one `UENUM` (`enum class E<Name> : uint8`, rule z) changed by one function (a single two-state flag may stay one bool), with a test that the forbidden combination can't be reached. No parallel bools (`bOpen` + `bFalling`). No shared Ella-wide enum unless the TD adds one in Core (D-new-port-4). No GameplayTags or GAS for the jam: state labels are these per-component enums (D-new-gameplay-tags). Done when: rule z passes and each state enum has its forbidden-combination test.
- `EndPlay` removes every delegate you bound onto another object (rule F), and clears every looping timer by its saved `FTimerHandle` (rule v). Call `Super::EndPlay`.
- No `GetAllActorsOfClass`, `GetActorOfClass` or `FindComponentByClass` in `Tick` or anything called every frame. Find it once in `BeginPlay` and keep a `TWeakObjectPtr`.
- Gameplay code reads the settings object with `GetDefault<UUmbrellaTuning>()` at the point of use; the smoke hook reads the same object at start and end of run. Never `GetMutableDefault` or `const_cast`, never a non-const copy of a marked tuning struct (a component member, a local, a pointer; a `const` reference is fine), and never write a DataAsset or class default at runtime. `bake_preset.py` fails each outside `#if UMBRELLAELLA_WORKBENCH` and `Private/Tests/`.
- Constructor: `CreateDefaultSubobject`, attachment, default values of members that are not tuning. A `// bake:` tuning member or flag is never assigned in code: its header default is the one source of the shipped value (`bake_preset.py` fails any other write outside `#if UMBRELLAELLA_WORKBENCH`). Nothing that needs a world. `BeginPlay`: find and cache references; a required reference that is missing logs an `Error` naming it and returns. `EndPlay`: unbind and clear (above).
- One log category for the game module: `DECLARE_LOG_CATEGORY_EXTERN(LogUmbrellaElla, Log, All)` in a Core header, `DEFINE_LOG_CATEGORY` in one `.cpp`. No `LogTemp` in merged code. A fault that can repeat every frame logs once per run (a member `bLogged<X>`), then stays silent. Log lines never carry user names, machine names or absolute paths.
- No `std::` containers or algorithms, no `try`/`throw`, no `dynamic_cast`. Use `TArray`/`TMap`, return codes, and `Cast<>`/`CastChecked<>`. (Exceptions and RTTI are off by default in UE module builds; unconfirmed: core, Editor checks.)
- No gameplay driven by flipbook events (`OnFinishedPlaying`, frame callbacks), notifies or sound events. Timing comes from C++ timers or tuning values; animation and sound only show it.
- Draw order: every depth offset (Y, since play is in X/Z) and sort priority lives in one header, `Core/UmbrellaDrawOrder.h`, in the art-bible draw order. No depth literal anywhere else.
- Debug: one dev-only console variable `ue.Debug` (`TAutoConsoleVariable<int32>`), defined and read only inside `#if !UE_BUILD_SHIPPING` (module_check rule s). Shipping behavior never depends on it. (Macro name and no Shipping console: unconfirmed, core, Editor checks.)
- Each `BP_*` subclass has a test (or validator rule) that its required asset references are set.

##### Tests (pattern built by Day-0 card 0.5)
- Rule tests: simple automation tests named `UmbrellaElla.<Area>.<Behavior>`, calling the plain rule functions. Headless, and each one finishes in under 1 s in the automation report (`check_automation_report.py --max-rule-seconds`, default 1).
- World tests are named `UmbrellaElla.<Area>.World.<Behavior>` (e.g. `UmbrellaElla.Umbrella.World.OpenRises`), or carry a `(world)` mark on their `pipeline/qa/test-map.md` row. Either one exempts them from the 1 s limit; `test.sh` / `test.ps1` read the marks by default (`--world-map`), so plain `test.sh`, the daily and the test map agree. A world test with neither fails the gate. Never pass `--max-rule-seconds 0` to get past a slow world test: rename it.
- World tests: one shared helper (card 0.5, `Private/Tests/Shared/`) creates a transient world in code (no `.umap`, so Source-lane cards can write them), spawns Ella,
  ticks N frames at a fixed delta, and reads a value (e.g. Z velocity). Sweep the delta at 1/30, 1/60, 1/120. (World-creation API: unconfirmed, core, Editor checks.)
- Placeholder: card 0.3 adds `UmbrellaElla.Bootstrap.Placeholder` in `Private/Tests/Bootstrap/` and passes with `check_automation_report.py --bootstrap`; card 0.5 removes it. `--bootstrap` fails once a real test exists.
- Every MVP item has at least one test that reads a value; screenshots don't count.
- A rule test is enough when the behavior is the rule function alone. Behavior that depends on the world (collision, overlap, movement, timers, spawning, input) also needs a world test.
- Each test builds its own transient world or tuning, reads only objects it created, and does not depend on another test's state. It must pass when run alone (`RunTests <full name>`).
- A test that writes files writes them under `Saved/UmbrellaEllaTests/` and deletes them; `tools/ue/test.*` fails if any file is left.
- UI: set the DPI curve (Project Settings > User Interface, shortest side) so the smallest UI text is at least 18 px from 720p to 2160p (`UIScalesWithResolution`, smoke `textpx=`). [VERIFY on 5.8.4]

### `docs/unreal-sources.md`

#### Unreal sources for `pipeline/unreal-rules.md`

Checked 2026-11-06 by web research only. No Unreal install was used, so nothing here was run on 5.8.4.
Verdicts: **confirmed** (primary source says it), **partly** (part right, or only a secondary source),
**wrong**, **unverifiable** (no source found either way). `[src: Uxx]` in the rules points here.
Epic doc pages below were titled "Unreal Engine 5.8 Documentation" when fetched, unless noted.

| # | Claim | Verdict | What the source says | Source |
|---|---|---|---|---|
| U1 | Paper2D ships enabled in 5.8.4 | unverifiable | 5.8 Paper 2D overview says "Enable the plugin and restart the editor." A third-party blog says it is on by default (5.6). No primary statement either way. | https://dev.epicgames.com/documentation/en-us/unreal-engine/paper-2d-overview-in-unreal-engine |
| U2 | `SetPlaneConstraintEnabled`, `SetPlaneConstraintNormal`, `bConstrainToPlane` exist on `UMovementComponent` | confirmed | All three listed. `bConstrainToPlane` is public; `PlaneConstraintNormal` is protected (use the setter). Normal applies only "if bConstrainToPlane is enabled". | https://dev.epicgames.com/documentation/unreal-engine/API/Runtime/Engine/GameFramework/UMovementComponent?application_version=5.1 ; https://dev.epicgames.com/documentation/unreal-engine/API/Runtime/Engine/GameFramework/UMovementComponent/SetPlaneConstraintEnabled?application_version=5.5 |
| U3 | `SetPlaneConstraintAxisSetting` is an alternative to a custom normal | confirmed | Public virtual setter on the same class. Known bug UE-25987: editing a custom normal back to default may not stick. | same as U2 ; https://issues.unrealengine.com/issue/UE-25987 |
| U4 | Basic / Empty Level are non–World Partition; Open World uses WP | partly | Docs say Open World and Empty Open World "use World Partition". Basic and Empty Level descriptions do not mention WP either way. | https://dev.epicgames.com/documentation/en-us/unreal-engine/working-with-levels-in-unreal-engine |
| U5 | Project templates' maps use WP | confirmed | "World Partition is enabled by default in many of the project templates found in the Games category" (Blank, First/Third Person, Top Down, Vehicle Advanced). | https://dev.epicgames.com/documentation/en-us/unreal-engine/world-partition-in-unreal-engine |
| U6 | Classic sublevels don't work in WP maps | partly | Epic: WP "removes the previous need to divide large levels into sublevels"; old levels become Level Instances. Forum: streaming nodes ignore sublevels in WP maps. | same as U5 ; https://forums.unrealengine.com/t/ue5-map/626666 |
| U7 | UBT flags `-DisableUnity -NoPCH -NoSharedPCH` | partly | Epic's Build Configuration page lists `bUseUnityBuild`, `bUsePCHFiles`, `bUseSharedPCHs` but no switches. Community: UAT `-StrictIncludes` "adds -DisableUnity -NoPCH -NoSharedPCH to UBT". No primary source for the switch names. | https://dev.epicgames.com/documentation/en-us/unreal-engine/build-configuration-for-unreal-engine?application_version=5.6 ; https://github.com/getnamo/SocketIOClient-Unreal/issues/419 |
| U8 | `IWYUSupport = IWYUSupport.Full` | partly | 5.8 module properties list `IWYUSupport` but not its values. Forum: `Full` is the current default. Epic's IWYU page still describes `bEnforceIWYU` and says IWYU is off for games (outdated). | https://dev.epicgames.com/documentation/en-us/unreal-engine/module-properties-in-unreal-engine ; https://forums.unrealengine.com/t/iwyu-documentation-is-outdated-incomplete-and-lacks-guidance/2729518 |
| U9 | `check()` not evaluated in Shipping; `ensure()` still evaluates | confirmed | "check macros only operate in Debug and Development builds"; "Ensure macros evaluate their expressions in all builds"; ensure reports once per session; `verify` always evaluates. | https://dev.epicgames.com/documentation/en-us/unreal-engine/asserts-in-unreal-engine |
| U10 | Shipping has no log; `bUseLoggingInShipping` turns it on | confirmed / partly | Target property "Whether to turn on logging for test/shipping builds." Forum: with an installed (launcher) engine, `BuildEnvironment = Unique` is refused; whether the flag alone works is unclear; shipping logs land in `%LOCALAPPDATA%\<Project>`. | https://dev.epicgames.com/documentation/en-us/unreal-engine/unreal-engine-build-tool-target-reference ; https://forums.unrealengine.com/t/enable-logging-in-shipping-build-using-installed-builds/1805603 |
| U11 | Shipping strips the console | confirmed | Shipping "Disables console commands, stats, and profiling tools". | https://dev.epicgames.com/documentation/en-us/unreal-engine/packaging-your-project |
| U12 | `-ReportExportPath=<dir>` writes `<dir>/index.json` | confirmed | "-ReportExportPath ... stores the report in a .json file"; "Index.html and index.json (normally found in the target directory)". No default path when the flag is absent. | https://dev.epicgames.com/documentation/en-us/unreal-engine/review-test-results-in-unreal-engine ; https://dev.epicgames.com/documentation/en-us/unreal-engine/setting-up-an-automation-test-report-server |
| U13 | index.json format | confirmed | Top level: `succeeded`, `succeededWithWarnings`, `failed`, `notRun`, `inProcess`, `tests`. Each test: `fullTestPath`, `testDisplayName`, `state` (example values `Success`, `Skipped`), `entries`, `errors`. | same as U12 |
| U14 | Command `Automation RunTests <prefix>` | partly | 5.8 docs spell it `Automation RunTest A+B;Quit` and `Automation RunTest Group:X`. `RunTests` is widely used in UE5 forum posts. No primary source that both work. | https://dev.epicgames.com/documentation/en-us/unreal-engine/run-automation-tests-in-unreal-engine ; https://forums.unrealengine.com/t/ue5-3-does-not-find-automation-tests-through-command-line/1747873 |
| U15 | `-TestExit="Automation Test Queue Empty"` | unverifiable | Forum only; one post calls it legacy. | https://forums.unrealengine.com/t/run-automated-testing-from-command-line/294995 |
| U16 | `-prereqs` ships the VC++ runtime | partly | Packaging settings: `IncludePrerequisites` ("an installer for prerequisites") and `IncludeAppLocalPrerequisites` ("alongside the game executable"). Forum: since 5.1 some clean PCs still miss the VC++ runtime; app-local was the fix. | https://dev.epicgames.com/documentation/en-us/unreal-engine/API/Developer/DeveloperToolSettings/UProjectPackagingSettings ; https://forums.unrealengine.com/t/microsoft-visual-c-runtime-no-longer-automatically-included-in-v5-1-builds/758116 |
| U17 | `MapsToCook` in DefaultGame.ini | confirmed | "List of maps to include when no other map list is specified on commandline." Class is `Config=Game, defaultconfig`. `DirectoriesToAlwaysCook` cooks unreferenced assets. Empty list = cook all maps (forum). | same API as U16 ; https://forums.unrealengine.com/t/list-of-maps-to-cook/55462 |
| U18 | `GameDefaultMap` must be set | confirmed | "The Game Default Map is the map that loads when your packaged project launches." | same as U11 |
| U19 | Live Coding only for `.cpp` bodies | partly | Epic: Object Reinstancing is on by default and covers UCLASS/UFUNCTION/USTRUCT changes, but "large-scale changes ... will behave unpredictably". The rule is stricter than Epic, which is safe. | https://dev.epicgames.com/documentation/en-us/unreal-engine/using-live-coding-to-recompile-unreal-engine-applications-at-runtime |
| U20 | `REINST_` log prefix | confirmed | `FBlueprintCompileReinstancer::IsReinstClass`: "starts with the 'REINST_' prefix". | https://dev.epicgames.com/documentation/en-us/unreal-engine/API/Editor/UnrealEd/FBlueprintCompileReinstancer |
| U21 | CoreRedirects syntax and location | confirmed | `[CoreRedirects]` in DefaultEngine.ini; `+ClassRedirects=(OldName="/Script/MyModule.MyOldClass",NewName="/Script/MyModule.MyNewClass")`; `+PropertyRedirects=(OldName="MyActor.OldProp",NewName="NewProp")`. Renames without a redirect lose asset data. | https://dev.epicgames.com/documentation/en-us/unreal-engine/core-redirects-in-unreal-engine |
| U22 | `UDeveloperSettings` with `Config=Game` → DefaultGame.ini | partly | Needs `defaultconfig` too, or editor saves go to the local `Saved/Config` ini. Epic's own packaging settings class uses `Config=Game, defaultconfig`. | https://tomlooman.com/unreal-engine-developer-settings/ ; same API as U16 |
| U23 | `meta=(BindWidget)` | confirmed | UMG metadata: `BindWidget` "requires a widget be bound to it in the designer". Epic staff forum answer: missing or wrong-class widget is a compile error. | https://dev.epicgames.com/documentation/en-us/unreal-engine/API/Runtime/UMG/UMWidget_1 ; https://forums.unrealengine.com/t/setting-up-widget-elements-in-constructor-of-uuserwidget/386638 |
| U24 | Git LFS `lockable` | confirmed | "Once file patterns in .gitattributes are lockable, Git LFS will make them readonly"; push verifies locks. `.gitattributes` here already marks .uasset/.umap lockable. | https://github.com/git-lfs/git-lfs/wiki/File-Locking ; https://github.com/git-lfs/git-lfs/blob/main/docs/man/git-lfs-lock.adoc |
| U25 | "Unreal editor MCP" in 5.8 | confirmed | Epic ships **Unreal MCP** (experimental). Enable plugins Unreal MCP + All Toolsets. Start: Editor Preferences > Model Context Protocol > Auto Start Server, or `ModelContextProtocol.StartServer`. `http://127.0.0.1:8000/mcp`, HTTP only, no auth, loopback only. Tool calls run one at a time on the game thread. `ModelContextProtocol.GenerateClientConfig ClaudeCode` writes `.mcp.json`. Named toolsets: SceneTools, ActorTools, MaterialInstanceTools, ObjectTools. Docs do not say it can create C++ classes, compile or save. | https://dev.epicgames.com/documentation/unreal-engine/unreal-mcp-in-unreal-editor?lang=en-US |
| U26 | Win64 packages only on Windows | partly | Epic's Wine container doc: it "cannot be used to package Unreal Engine projects that include C++ code". Forums: Windows builds need a Windows host. No direct primary statement. | https://dev.epicgames.com/documentation/unreal-engine/wine-enabled-containers-quick-start-for-unreal-engine ; https://forums.unrealengine.com/t/how-do-i-package-my-ue5-game-from-mac-to-windows-for-development/736505 |
| U27 | "Apply Paper2D Texture Settings" | confirmed | It "removes Mipmaps, sets the Filter to Nearest, and uses the Editor Icon as the Compression Setting." Wrong for this game's painted art (art bible). | https://dev.epicgames.com/documentation/en-us/unreal-engine/how-to-import-and-use-paper-2d-sprites-in-unreal-engine |
| U28 | Pixels Per Unreal Unit applies only to new sprites | confirmed | Default Pixels Per Unreal Unit is "to use for newly created sprite Assets" (0.64 → 64 px = 100 cm). | https://dev.epicgames.com/documentation/en-us/unreal-engine/paper2d-import-settings-in-the-unreal-engine-project-settings |
| U29 | UserInterface2D compression renamed in 5.7 | unverifiable | Forum user (no staff badge): "as of UE 5.7 the User Interface (RGBA8) compression setting has been renamed to Uncompressed (RGBA8)". The 5.8 Paper2D import page still lists "UserInterface2D (RGBA)". | https://forums.unrealengine.com/t/missing-compression-setting-userinterface2d/2692223 |
| U30 | Enhanced Input in C++ | confirmed | Enabled by default. Add context with `LocalPlayer->GetSubsystem<UEnhancedInputLocalPlayerSubsystem>()->AddMappingContext(ctx, priority)`; cast to `UEnhancedInputComponent` in `SetupPlayerInputComponent` and `BindAction(IA, ETriggerEvent::Triggered, this, &F)`. `EnhancedInput` Build.cs dependency: community wiki only. | https://dev.epicgames.com/documentation/en-us/unreal-engine/enhanced-input-in-unreal-engine ; https://unrealcommunity.wiki/using-the-enhancedinput-system-in-c++-74b72b |
| U31 | OrthoWidth = visible width in world units | partly | Forum only; matches the property name. Not used in the rules for lack of a primary source. | https://forums.unrealengine.com/t/paper2d-and-orthographic-width/10721 |
| U32 | Asset name prefixes | confirmed | T_, BP_, WBP_, M_, MI_, DT_ ... Paper2D, input and map types are not listed; "use the existing list as a guideline". | https://dev.epicgames.com/documentation/unreal-engine/recommended-asset-naming-conventions-in-unreal-engine-projects?lang=en-US |

Not checked against a source (project policy, not engine facts): one sublevel per owner, lane rules,
"Never Save All", `-SmokeQuitAfter`, `tools/ue/*` behaviour.

## Checklists

### `pipeline/checklists/file-hygiene.md`

#### File hygiene checklist (Project Librarian, run by any human or agent before a gate)

Rick's pipeline doc: this role proposes cleanup with reasons and never deletes or moves files
automatically, because Unreal references need care.

- [ ] `python3 tools/pipeline_check.py` reports 0 problems.
- [ ] No new top-level folders outside the layout in `pipeline/unreal-rules.md`.
- [ ] Asset names follow `T_`, `SPR_`, `FB_`, `BP_`, `IA_`, `IMC_`, `L_` prefixes.
- [ ] Zero redirectors on main (Fix Up Redirectors run in the editor after any move).
- [ ] The last `DAILY` line has `validate=PASS(err 0, ...)` (DataValidation, `tools/ue/validate.*`). Paste it.
- [ ] No stray Markdown: agent notes, plans and logs live in the PR or issue, not new files.
- [ ] Every committed capture or log is referenced by a PR, issue or doc; otherwise propose deleting it.
- [ ] `git lfs locks` shows no lock older than a day without an open PR.
- [ ] Every asset has a row in `pipeline/art/provenance.csv`.
- [ ] No `_v2`, `_final`, `_new` or `_old` in any file or asset name. Versions live in git.
- [ ] Every `_PH` placeholder is listed with the card that replaces it (D-new-port-8).
- [ ] No new file or class named `*Helpers*`, `*Utils*`, `*Types*` or `*Manager*` unless a card named it.
- [ ] Every `TODO` reads `TODO(UE-<id>)` or `TODO(D<n>)`. Every stub reads `// STUB(UE-<id>)` and is listed in its PR's "Not done".
- [ ] No pipeline text in shipped content: no `ROLE:`, role names or agent notes in UI strings, credits or level text.
- [ ] Rejected AI generations are outside `Content/`, so they are never cooked.

Output: a comment listing proposed moves/deletions, each with a reason. A human does them in the editor.

## Pull request template

### `.github/PULL_REQUEST_TEMPLATE.md`

<!-- tools/check_pr.py fails this PR if a required section is empty. -->
##### Task
Part of #<issue>. Card ID: UE-___  Owner role: ___  Reviewer role: ___
<!-- Link form is open decision D-new-port-1. Default: "Part of #<issue>" (the human on the card closes it after the
     packaged-build check). Alternative: "Closes #<issue>" (merge closes the card). tools/check_pr.py accepts both. -->

##### What changed
<files and assets, one line each>

##### Done-when checks
<copy the card's Done-when list; tick only what you ran and observed>
- [ ]

##### Evidence
commit=<sha> engine=5.8.4 config=<Development|Shipping|none> host=<win|mac> run=<PIE|Standalone|packaged|none>
<build log tail, test output, screenshot or clip paths. "Not run" is allowed if you say why.
Changes maps, Config/**, *.Build.cs, *.Target.cs or .uproject: the package script's `package exit: 0  commit=<sha>  dirty=no ...`
line and the smoke output (tools/ue/smoke.sh / smoke.ps1 print the game's SMOKE_OK log line as is; paste the whole output).
Touches Source/: the `build exit: 0  mode=nonunity  commit=<sha> ...` line as printed (NONUNITY=1 tools/ue/build.sh, build.ps1 -NonUnity)
and the check_automation_report.py result line (PASS  tests=N failed=0  commit=<sha>). Every commit= is the header commit:
after a new push, run them again. A claim like "all good" fails check_pr.
A failure the card's Done-when asks for on purpose (MustFail, a planted plant, SMOKE_FORCE_CRASH) goes under a line
`PLANTED FAIL: <what>`, up to the next blank line; any other FAIL line fails check_pr.
A changed .uasset/.umap needs the card's human to open it: `EDITOR CHECK: by=<name> opened=<path>[,<path>] ok`.
Last line: developer-tested (PIE), developer-tested (packaged) or QA-verified in build <sha> (qa-build.md).>

##### Not done / risks
<one line each, each with a link (issue #N, decision row, or URL). Write "none" only if true.>
Could not read: <card Inputs or cited docs you could not open (missing, LFS pointer, no access), or "none". Build nothing that rests only on one>
Next: <next role and exact step after this PR, or "none">

##### Binary assets touched
<.uasset/.umap paths and whether you held the LFS lock. "none" if none.>

##### GDD impact
<only if this PR changes docs/gdd/ or docs/feature-manifest.json: paste `python3 tools/gdd_impact.py <old> <new>`
(docs/gdd/README.md). Otherwise delete this section.>

##### Journal
<paste the output of `python3 tools/journal.py export --card UE-___` (AGENTS.md section 6)>

## Reviewer eval

### `evals/reviewer/results.md`

#### Reviewer eval results

Runner: `python3 tools/run_reviewer_eval.py` · reviewer CLI `claude -p` (Claude Code, default model) · Josh's Mac · 2026-11-06.
Raw outputs are in `evals/reviewer/runs/` locally (gitignored); summaries are copied here. Every run is listed, including failures.

| Run | Setup | Defects found | Blockers | Defective blocked | Clean approved | Bar |
|---|---|---|---|---|---|---|
| 191617 | v1 cases, reviewer could read the repo | 13/13 | 8/8 | 12/12 | 2/3 | FAIL |
| 191951 | clean cases only | – | – | – | 2/3 | FAIL |
| 192045, 192345, 192631 | clean cases given test evidence | 13/13 | 8/8 | 12/12 | 3/3 | PASS ×3 |
| 193201, 193534, 193851 | uniform wording, reviewer isolated (no file/shell tools, empty folder) | 13/13 | 8/8 | 12/12 | 2/3, 3/3, 3/3 | 1 FAIL, 2 PASS |
| 194251, 194647, 195030 | case 15 fixed, Unreal rules updated | 13/13 | 8/8 | 12/12 | 2/3, 3/3, 3/3 | 1 FAIL, 2 PASS |
| **195457, 195848, 200244** | **case 13 fixed, evidence line aligned with the rules** | **13/13** | **8/8** | **12/12** | **3/3** | **PASS ×3** |

Across all 14 full runs: every planted defect was found and every defective change was blocked, every time.
The failures were all clean code wrongly rejected. Each time, the reviewer's reason was valid:
- Case 14 (run 191617): `Velocity.Z < 0` is also true walking downhill, so the "clean" code broke the falling rule. No test evidence either.
- Case 15 (run 193201): a non-owning pointer held strongly, against our own `TWeakObjectPtr` rule.
- Case 13 (run 194251): logic in the character instead of the umbrella component, which the new code-layout rule requires; test name not `<Area>.<Behavior>`.
Fixes went into the clean cases and into the shared evidence line, never into the defective cases or the reviewer prompt
(other than the verdict rule "any medium finding blocks", made to match the scorer).

How to read it: the Dev Lead prompt reliably catches these planted bugs. It is strict, and it will reject code that breaks
any rule in `pipeline/unreal-rules.md`, so clean code must actually follow the rules. 15 cases is small; add a case for every real miss during the jam.
Not covered yet: missing-evidence cases (every case claims build and tests passed), Codex as the reviewer, other models.

##### Round 2 (35 cases: 20 new ones written by a separate agent, incl. 4 evidence cases)
| Run | Change | Defects found | Blockers | Defective blocked | Clean approved | Bar |
|---|---|---|---|---|---|---|
| 232645 | 35 cases; rules + reviewer card grew in round 2 (lanes, structure rules, world-test rule) | 22/22 | 18/18 | 28/28 | 3/7 | FAIL |

Why the 4 clean cases were rejected (read from the run JSON):
- 13: TickComponent writes `Velocity.Z` with no tick order set against the movement component, and has no world test. Valid under the new checklist item 6.
- 14: written before the lane rules; attack logic sits in the character, not `UEllaAttackComponent`. Valid; the case is stale.
- 33: same tick-order gap as 13, and the braking step that crosses zero uses the brake acceleration for the whole frame (frame-rate dependent). Valid.
- 35: one medium finding was speculative ("if CanAttack applies a threshold...") about code not in the diff. Reviewer fault.

##### Round 3 case refresh (no run yet)
All 35 cases were moved onto the current rules (per-component lanes, `AEllaCharacter` shell, `GetDefault<UUmbrellaTuning>()-><Comp>.<Field>`,
one UENUM state per component, tick prerequisite stated in Context, rule + world tests, split-at-threshold braking), so each defective case
breaks only its planted rule. Clean cases 13, 14, 33 and 35 were stale under the round-2 rules (reasons above); 14 now lives in
`UEllaAttackComponent`. Case 09's second planted API changed from `SetGravity` to `PlayOneShot2D`, because presentation code may not
write gravity. Expected lines were recomputed by script from the new diffs.
| 001843, 003151, 004431 | all 35 cases refreshed to the round-2 rules | 28/29 ×3 | 17/18 ×3 | 30/30 ×3 | 5/7, 6/7, 6/7 | FAIL ×3 |

- Case 13 rejected 3/3, validly: its own Done-when says speed "levels off at RiseSpeed", but `Max(CurrentZ, ...)` never brings a faster upward speed down (e.g. after a kill bounce). Case fixed (`FInterpConstantTo`, plus a level-off rule test; braking stated out of scope).
- Case 15 rejected 1/3 (wanted an invariant block and more negative tests). Left as is: 2/3 approve, and the findings are rule-backed but borderline.
- Case 31 missed 3/3 by the scorer, though blocked every time: the reviewer named the test-count drop as a finding but still wrote `checks_seen.tests: pass` (echoing the tool's PASS). Fix went into the reviewer card: `checks_seen` is the reviewer's judgement, with the cases that make `tests` = fail listed.
| 005802, 011227, 012751 | case 13 fixed; `checks_seen` defined in the reviewer card | 29/29 ×3 | 18/18 ×3 | 30/30 ×3 | 6/7, 4/7, 4/7 | PASS, FAIL, FAIL |

- Detection is now perfect in all 3 runs, including case 31.
- The new failures were caused by my `checks_seen` wording: it says tests fail when the run skipped `--baseline`/`--require`, and the shared evidence line didn't show those flags. So the reviewer blocked clean cases 13, 15, 32, 35 for evidence, correctly by its card. Fix went into the evidence line (it now shows the real command per AGENTS.md), not the card. Case 15's world test now lists its negative overlaps, which its "defeats it once" Done-when needs.
| **014310, 015628, 020800** | **evidence line shows the real test command; case 15 test lists negatives** | **29/29 ×3** | **18/18 ×3** | **30/30 ×3** | **7/7 ×3** | **PASS ×3** |

Round 2 total: 10 full runs of 35 cases. Every run blocked every defective change. Planted defects were missed only in 3 runs, all case 31 (scored miss: blocked, but checks_seen said pass) before the card defined checks_seen. Clean-case failures were each traced to a case or evidence line that broke our own rules, except one speculative reviewer finding (case 35, run 232645), fixed in the card ("a finding about code you cannot see is low at most").

##### Round 4 (55 cases: 20 new, 36-55)
New cases: 36 character shell with logic, 37 non-const query, 38 comment contradicts code, 39/40 delegate on another actor (defect/clean),
41/42 actor lookup every tick, 43/44 settings written at runtime, 45/46 looping timer, 47/48 parallel bools vs one UENUM,
49/50 INV-n with no test, 51/52 behavior-picking bool, 53 no module_check output (evidence), 54 inline lambda by-ref capture,
55 stored lambda by-ref capture. 33 older task.md files now name world tests `UmbrellaElla.<Area>.World.<Name>`.
The shared evidence line now shows a NONUNITY=1 build and module_check exit 0, which the reviewer card requires.
Pass bar adds MUST_CATCH in `tools/run_reviewer_eval.py`: cases 37 and 38 must be fully caught in each run.
| Run | Change | Defects found | Blockers | Defective blocked | Clean approved | Bar |
|---|---|---|---|---|---|---|
| 180818, 180821, 180824 | 55 cases, first run | 40/41, 41/41, 40/41 | 20/20 ×3 | 41/41 ×3 | 10/14, 11/14, 11/14 | FAIL ×3 |

- Case 39 scored as missed 2/3, though caught: the reviewer pointed at the EndPlay line, outside the planted range. Fix: EndPlay added as an `also` place.
- Clean cases 46 and 52 rejected 3/3, validly: `UpdateWind` and `ApplyWalk` write no member, so card item 4 wants them `const`. Cases fixed.
- Clean case 44 rejected 2/3, validly: a second state bool next to `EAttackState`, and its world test ended PIE (item 17). Case changed.
- Clean case 13 rejected 1/3: its comment did not match the code (item 16, new). Comment fixed.
- Clean case 15 rejected 1/3: public `UPROPERTY` delegate `OnDefeated` breaks rule C as built. Left as is; it depends on D-new-public-state.
| **183121, 183124, 183127** | **cases 13, 39, 44, 46, 52 fixed** | **41/41 ×3** | **20/20 ×3** | **41/41 ×3** | **13/14, 12/14, 13/14** | **PASS ×3** |

- Cases 37 and 38 (MUST_CATCH) were caught in all 6 runs.
- Case 44 was still rejected 3/3: the reviewer calls `NextCooldownSeconds` a hidden "combo pending" state outside `EAttackState`. That is a fair reading of the one-enum rule; the case should move the combo into the enum before the next round.
- Case 32 rejected 1/3 (overlap does not refire for an actor already inside the box). Left as is.

##### Round 5 (consolidation pass, 55 cases)
Changed: `pipeline/unreal-rules.md` split into a core plus `pipeline/unreal/*.md` (the runner loads all of them, so the
reviewer sees the same rules); a link fix in `pipeline/roles/dev-lead.md`; every case's task line "GDD rule: attack only
while the umbrella is closed and Ella is falling" became "GDD rule: open umbrella = rise, closed umbrella = fall (GDD §4)",
because the GDD is now THE LAST HOUR; case 30's build-log path no longer names a personal home folder. No planted defect changed.
Correction (round 6): only the task line changed then. The code and Done-when of the attack cases still used the old rule
(TryAttack on IA_Attack, attack only while closed and falling), and about 20 more cases still described the platformer.
| Run | Change | Recall | Blockers | Defective blocked | Clean approved | Bar |
|---|---|---|---|---|---|---|
| 215814, 222138, 222142 | consolidation pass | 1.0, 0.976, 1.0 | 20/20 ×3 | 41/41 ×3 | 13/14, 12/14, 12/14 | PASS ×3 |

- MUST_CATCH cases 37 and 38 were caught in all 3 runs.
- Clean case 44 (combo cooldown) was rejected 2/3, the same "second state outside the enum" reading as round 4. Its task is a retired stretch item (D19). It should be rewritten for the owl game.
- Clean case 15 (enemy header) was rejected 2/3. It is also an old-game case (enemies are gone).

- Run 222138 scored one planted defect as missed (case 45, loop-timer), but still blocked that change.

##### Round 6 (case refresh for the new game, 55 cases)
Written by a separate agent session; `pipeline/roles/dev-lead.md` and the `pipeline/` rules were not touched.
- Shared task line is now "GDD rules: open umbrella = rise, closed umbrella = fall (GDD §4); the wand fires on its own at the
  tuned cadence, only while the owl is in the firing lane with line of sight, and there is no attack input (GDD §5, D1 default)."
- Old attack-gate cases now plant a broken auto-fire rule in `UEllaAttackComponent`: 04 fires outside the lane (blocker),
  25 inverts the line-of-sight check (blocker), 27 calls a made-up `AActor::HasLineOfSightTo` (blocker); 14 (clean) and 35
  (clean rule test `UmbrellaElla.Wand.FiresOnlyInLane`) follow the D1 default; 21 and 36 and 07 dropped `IA_Attack`.
- Platformer cases moved to current lanes: enemy → `AClockworkOwl` (01, 02, 06, 15, 28, 39, 40, 43, 44), spikes → owl
  telegraph timer (19, 32, 55), enemy defeat → `AOwlBolt` (11, 30), level end → `ASurvivalClock` (31), per-tick enemy facing →
  `AArenaBottomExit` / `BOTTOM_EXIT` (41, 42, 53), ground/air walk → open/closed steering (51, 52), attack flipbook/flash →
  hurt reaction (09, 54), title/results maps → title/arena maps with `ShowRunEnd(ERunResult)` (23), channels → OwlBolt/WandShot (24).
- Other cases: MVP numbers remapped to the new list, "lift-off from the ground", "kill bounce", "hazards and enemies" removed.
- Each planted defect keeps its id, kind and severity. Expected lines were recomputed by script from the new diffs.
| Run | Change | Recall | Blockers | Defective blocked | Clean approved | Bar |
|---|---|---|---|---|---|---|
| 20261107-234655 | first run after the refresh | 0.976 | 20/20 | 40/41 | 11/14 | FAIL |
| 20261108-001002, 003154, 003159 | cases 01/02/15, 14 (and its siblings), 41/42/53 fixed | 1.0 ×3 | 20/20 ×3 | 41/41 ×3 | 13/14, 14/14, 12/14 | PASS ×3 |

- Run 234655, case 51: the reviewer found the planted bool parameter, but wrote prose after the JSON whose `{ return; }`
  broke the runner's JSON extraction, so the verdict scored "invalid". Runner limit, not a case fault; not changed here.
- Clean rejections in run 234655, each valid, each fixed in the case: 14 used `IsValid` and `TWeakObjectPtr::Get` without
  listing them as already used (item 5), and its comment overstated "fires at once"; 15 had a "stops for good" rule with no
  numbered INV (now INV-1 in the header, cited by the test); 42 read Ella's position with no tick order (Context now states
  TG_PostPhysics).
- Clean case 34 rejected in runs 001002 and 003159, validly: its Done-when says BP_Ella keeps its flipbooks, but no test loaded
  BP_Ella. Clean case 15 rejected in run 003159, validly: Context said BP_ClockworkOwl sets a sprite the header does not have.
  Both fixed after the three runs (34 and 18 now list a BP_Ella asset test; 15/01/02 Context corrected). Not re-run yet.
- MUST_CATCH cases 37 and 38 were caught in all 4 runs.

##### Round 7 (case refresh for GDD B1.0, 55 cases)
Written by a separate agent session; `pipeline/roles/dev-lead.md`, `pipeline/` rules and `tools/` were not touched.
- Shared task line is now "GDD rules (GDD B1.0 ...): only UP_OPEN lifts and every other umbrella configuration falls at normal
  gravity, with no fast fall (§3); only the Player Motor writes velocity and gravity (§4); a non-CONFIRMED feature runs only behind
  IsFeatureEnabled(EFeatureId::<ID>) at its manifest default (§5); COM-01 is automatic in intent, its trigger OPEN (DEC-02);
  the card's features are implementation_authorized."
- Lanes moved to the 12 GDD B modules: velocity/lift → `UPlayerMotorComponent` reading `EUmbrellaConfig` from
  `UUmbrellaStateComponent` (05, 12, 13, 20, 22, 26, 27, 33, 37); umbrella state (17, 47, 48); presentation → `UFeedbackAdapterComponent`
  (03, 09, 10, 18, 21, 34, 38, 45, 46, 54); Flow/OnSurvivalEnd/ASurvivalClock → `UEncounterDirectorSubsystem` with the six §8 states and
  EncounterCompleted/PlayerDefeated on `UGameEventsSubsystem` (01, 02, 15, 23, 31, 39-43, 51-53); `AOwlBolt` → Projectile/ (11, 30);
  owl timers cleared in `ResetForRestart()` (19, 32, 44, 55); channels → Projectile/ArenaBounds (24); shell has no attack input (07, 36).
- Old auto-fire cases: 04 (blocker) emits without checking the COM_01 flag; 25 (blocker) inverts the flag check; 27 (blocker) calls a
  made-up `UCharacterMovementComponent::IsAirborne()` in the Motor; 14 and 35 stay clean (flag + cooldown on the DEC-02 `RequestEmit` seam).
  44 (retired combo cooldown) is now a clean owl `ResetForRestart`; 51/52 are now an `EndEncounter(bool bSurvived)` bool parameter.
- Each planted defect keeps its id, kind and severity. Expected lines recomputed by script from the new diffs; 45 gains its EndPlay as an
  `also` place (reviewer pointed there, as in case 39 in round 4).
| Run | Change | Recall | Blockers | Defective blocked | Clean approved | Bar |
|---|---|---|---|---|---|---|
| 20261108-202146 | first run after the refresh | 0.976 | 20/20 | 41/41 | 9/14 | FAIL |
| 20261108-204754 | 14, 15, 34, 45/46, 52 fixed | 1.0 | 20/20 | 41/41 | 13/14 | PASS |
| 20261108-211213, 213731, 220146 | 45/46 test fixed | 1.0 ×3 | 20/20 ×3 | 41/41 ×3 | 13/14, 12/14, 12/14 | PASS ×3 |
| 20261108-222544 (--only 8 cases) | 14, 15, 34 fixed | 1.0 | 4/4 | 5/5 | 1/3 | (partial) |
| 20261108-223108 (--only 6 cases) | 14 cooldown, 15 first-run reset fixed | 1.0 | 4/4 | 4/4 | 1/2 | (partial) |
| 20261108-223524 (--only 01, 02, 15) | 15 header comment fixed | 1.0 | 1/1 | 2/2 | 1/1 | (partial) |

Every clean rejection was valid and fixed in the case (never the prompt or a defective case):
- 202146: 14 Done-when "reset makes the next request ready" untested; 15 two writers of `EOwlState` (now one `SetState(State, Why)`);
  34 test covered only UP_OPEN/NO_LIFT; 46 my restart edit stopped the wind loop for good; 52 Done-when blocked cases untested.
  45 scored missed: the reviewer cited the EndPlay line, outside the planted range.
- 204754: 46 Done-when "no wind field → silent" untested.
- 211213-220146: 14 cooldown clamp is frame-quantized (2/3), 15 drift speed untested and a stale member comment (2/3), 34 test never
  returned to UP_OPEN (1/3). Fixed after the three runs.
- 222544: my carry-over fix let a shot come up to one frame early against Done-when; reverted to whole frames, now stated in Done-when
  with a gap test. 15: `CurrentDriftPoint` unset on the first run, `DriftPoints[1]` unguarded (now BeginPlay calls `ResetForRestart`, which
  warns under 2 points). 223108: 15 header comment did not match that. 223524: 15 approved.
- The cases as committed passed only the partial re-runs after 220146, not a fresh full run of 55.
- MUST_CATCH cases 37 and 38 were caught in every run.

##### Round 8 (clean cases 14, 40, 52 after run 20261108-230255)
Written by a separate agent session; only cases 14, 40, 52 and this file were touched. In 230255 all three rejections were valid:
14 float cooldown countdown depended on tick order vs RequestEmit (could fire a frame early); 40 the test never read the owl's
position for "stops drifting"; 52 DefeatEndsRunOnce did not sweep DeltaSeconds.
- Fix A: 14 now stores `NextEmitTime` (world time) and compares in RequestEmit, no tick, Done-when says world time within
  UE_KINDA_SMALL_NUMBER; 40 test records and re-reads GetActorLocation(); 52 DefeatEndsRunOnce sweeps 1/30, 1/60, 1/120.
- Fix B (after 235325): 40 Context lists INV-1 in the header block and the test cites it (reviewer raised the missing INV as med).
- Fix C (after full run 002114): 14 test reads each spawn's kind, origin and velocity (Done-when spawn request was untested);
  52 lacked GDD B §8 "defeat wins in one update": Context now says CompleteEncounter() runs only from the Director's Tick, which ticks
  after every tick group, Done-when states defeat wins, CompletionEndsRunOnce adds a same-update defeat check.
  Full run 004657 started 38 s before Fix C landed; its 14 and 52 ran after it, so it used the fixed cases.

| Run | Change | Recall | Blockers | Defective blocked | Clean approved | Bar |
|---|---|---|---|---|---|---|
| 20261108-235325 (--only 14, 40, 52) | Fix A | n/a | 0/0 | n/a | 2/3 (40: INV) | (partial) |
| 20261108-235457, 235605 (--only 14, 40, 52) | Fix B | n/a | 0/0 | n/a | 3/3, 3/3 | (partial) |
| 20261108-235732 | full, Fix B | 1.0 | 20/20 | 41/41 | 13/14 (34) | PASS |
| 20261109-002114 | full, Fix B | 1.0 | 20/20 | 41/41 | 10/14 (14, 35, 48, 52) | FAIL |
| 20261109-004657 | full, Fix C | 1.0 | 20/20 | 41/41 | 12/14 (34, 48) | PASS |
| 20261109-011347, 011459 (--only 14, 40, 52) | Fix C | n/a | 0/0 | n/a | 3/3, 3/3 | (partial) |

Clean rejections outside this round's scope, not fixed: 34 (SMOKE_OK line has no workbench= field, blocker, 2/3 full runs, same reason
both times; looks valid against the SMOKE_OK contract), 48 (NoLift stored as a state and the default; gameplay-code.md says NO_LIFT is derived and DEC-01 says no input
is UP_OPEN, 2/3, looks stale against the 11/8 attack baseline), 35 (rule test cites INV-1 but never calls RequestEmit, 1/3).
- MUST_CATCH cases 37 and 38 were caught in every run.

##### Round 9 (clean cases re-filed to GDD 1.3 and 6130c77)
Only clean cases and this file were touched; no defective case or expected.json changed.
- All 14 clean cases: the GDD rules line now cites GDD 1.3 (NO_LIFT derived, no per-state gravity multiplier, DEC-01 holds, DEC-02
  fires +X only in ATTACK_DESCENT, APPROVED_P0 flags default on) instead of GDD B1.0 and "COM-01 trigger is OPEN".
- 34: SMOKE_OK line has workbench=0, with workbench-check PASS and BUILD_INFO workbench=0.
- 35: the rule test no longer claims INV-1; it covers CanEmit, and the merged world test that calls RequestEmit cites INV-1.
- 48: rewritten to DEC-01: starts UpOpen, ApplyInput(FUmbrellaInput) resolves shield > attack > UpOpen, no NoLift state.
- 13, 33: EUmbrellaConfig list is the GDD 1.3 states; GravityScale is one value for every falling state.
- 14, 35: COM-01 is MVP 9 (APPROVED_P0), not Stretch; 14 names the ATTACK_DESCENT trigger and +X aim. 46: WIND-01 is MVP 11.
- 32: one bolt per volley (BOLT_Single). 40, 52: GDD 1.3 §8.

| Run | Recall | Blockers | Defective blocked | Clean approved | Bar |
|---|---|---|---|---|---|
| 20261109-015026 | 0.976 | 20/20 | 41/41 | 14/14 | pass true, recall below 1.0 |
| 20261109-021615 | 1.0 | 20/20 | 41/41 | 14/14 | PASS |
| 20261109-024124 | 1.0 | 20/20 | 41/41 | 14/14 | PASS |

Reviewer mistake, not fixed: 015026 missed 49 inv-untested on location. It named INV-2 at HealthComponent.h:3 in the summary but
filed the finding at HealthComponent.cpp:42, outside the planted range.
- Defective cases still cite GDD B1.0 in their GDD rules line.
- MUST_CATCH cases 37 and 38 were caught in every run.

##### Round 10 (defective cases re-filed to GDD 1.3)
The 41 defective cases still cited GDD B1.0, so a reviewer could tell clean from defective by the citation. Only
defective cases and this file were touched. No planted defect, expected verdict or line range changed, and no diff line
count changed, so expected.json is untouched.
- All 41 defective cases: the GDD rules line is now the clean cases' GDD 1.3 line.
- GDD B §3/§4/§8/§9 references now cite GDD 1.3 (02, 03, 10, 17, 29, 30, 31, 38, 39, 43, 45, 47, 51).
- 04, 25: COM-01 is MVP 9 (APPROVED_P0), not Stretch. RequestEmit's trigger is ATTACK_DESCENT with +X aim, matching 14.
- 45: WIND-01 is MVP 11, matching 46. 19, 55: one bolt per volley (BOLT_Single), matching 32.
- 05, 20, 26: EUmbrellaConfig list and the GravityScale wording match 13/33.
- 03, 10, 12, 27, 37: tests set ATTACK_DESCENT/SHIELD_DESCENT (ApplyInput), not NoLift or RequestOpen/RequestClose.
- 07, 36: Input Adapter binds IA_Attack and IA_Shield (DEC-01), not IA_Umbrella; dropped "no attack input until DEC-01/02".
- 17: Config starts UpOpen (diff context line), and the test sets AttackDescent twice and then UpOpen once.
- 47: starts UpOpen (bUpOpen = true); RequestClose gives AttackDescent and is called on IA_Attack. The planted bFalling
  bool at line 49 is unchanged.
- 31: DEC-06 is the provisional 90 s survival default (END-01.survival_s), not a 150 s fixture.
- 02: BossTargetHit(region=BODY); the CLOCK collider is a later card (DEC-08, OWL-05).
- 7c94d50 changed one reviewer-visible rule (workbench #ifdef). No case uses it, so no clean case went stale.

| Run | Recall | Blockers | Defective blocked | Clean approved | Bar |
|---|---|---|---|---|---|
| 20261109-031511 | 1.0 | 20/20 | 41/41 | 14/14 | PASS |
| 20261109-034016 | 1.0 | 20/20 | 41/41 | 14/14 | PASS |
| 20261109-040547 | 1.0 | 20/20 | 41/41 | 14/14 | PASS |

- No reviewer misses. MUST_CATCH cases 37 and 38 were caught in every run.

##### Round 11 (re-run against the rules at 50927e5)
The rules changed between 19251b5 and 50927e5 (smoke hook contract, GetMutableDefault/const_cast ban, tuning via GetDefault,
build commit stamp, build log last line, input_vz on SMOKE_OK). Only case 34 went stale; no defective case or expected.json changed.
- 34: evidence.txt now pastes the build script's last line (`build exit: 0  mode=nonunity  commit=3e7a91c ...`), adds
  input_vz=-412 to SMOKE_OK, says the package stamped UMBRELLAELLA_BUILD_COMMIT=3e7a91c (BUILD_INFO commit=3e7a91c), and adds the
  SMOKE_EFFECTIVE at=start and at=end lines (commit=3e7a91c workbench=0 platform=Windows manifest=1.3-m1) with bake_preset.py
  effective PASS.

| Run | Change | Recall | Blockers | Defective blocked | Clean approved | Bar |
|---|---|---|---|---|---|---|
| 20261109-103039 | full, 34 not yet fixed (stopped earlier attempt) | 1.0 | 20/20 | 41/41 | 13/14 (34: SMOKE_OK has no input_vz) | pass true |
| 20261109-105727 | full, 34 not yet fixed (stopped partway, 40/55 cases, not scored) | n/a | n/a | n/a | n/a | (partial) |
| 20261109-112117 (--only 34) | 34 fixed | n/a | 0/0 | n/a | 1/1 | (partial) |
| 20261109-112144 | full, 34 fixed | 1.0 | 20/20 | 41/41 | 14/14 | PASS |
| 20261109-114643 | full, 34 fixed | 1.0 | 20/20 | 41/41 | 14/14 | PASS |
| 20261109-121135 | full, 34 fixed | 1.0 | 20/20 | 41/41 | 14/14 | PASS |

- No reviewer misses. MUST_CATCH cases 37 and 38 were caught in every run.
- Unit tests: `python3 -m unittest discover -s tests` -> Ran 1458 tests, OK (skipped=2).

##### Round 13 (Official Rules round, on top of 2236f37)
Rules the reviewer loads changed only in the editor MCP pointer in `pipeline/unreal-rules.md`; no case or expected.json changed.

| Run | Change | Recall | Blockers | Defective blocked | Clean approved | Bar |
|---|---|---|---|---|---|---|
| 20261109-175718 | full, 55 cases | 1.0 | 20/20 | 41/41 | 14/14 | PASS |

- No reviewer misses. MUST_CATCH cases 37 and 38 were caught.

### `tools/run_reviewer_eval.py`

Usage text from the file:

```text
Run the Dev Lead reviewer prompt on every seeded-defect case, then score it.

The reviewer CLI is whatever the teammate uses. It gets the prompt on stdin and must print
the review JSON. Defaults to Claude Code; for Codex pass --cmd "codex exec -".

Usage:
  python3 tools/run_reviewer_eval.py                       # claude -p
  python3 tools/run_reviewer_eval.py --cmd "codex exec -"
  python3 tools/run_reviewer_eval.py --only 04-attack-while-open
Writes evals/reviewer/runs/<timestamp>/<case>.json and prints the score from tools/score_review.py.
A pass also needs every defect in the MUST_CATCH cases caught.
```

Tests: `tests/test_run_reviewer_eval.py`, `tests/test_score_review.py`

### `tools/score_review.py`

Usage text from the file:

```text
Score a reviewer agent against seeded-defect cases (evals/reviewer/cases/*).

Rick's pipeline doc: "We should test the reviewer with known problems: an agent saying
'approved' is not proof that the code is good." This is that test.

Each case folder holds:
  change.diff     the change under review (we planted the defects)
  task.md         the task card the change claims to satisfy
  expected.json   {"clean": bool, "defects": [{"id", "severity", "file", "lines": [a, b], "keywords": [...],
                                             "also": [{"file", "lines": [a, b]}]  (optional)}],
                   "checks": {"tests": "missing" | "fail", "build": ...}  (optional)}
  evidence.txt    optional; replaces the default author evidence (see tools/run_reviewer_eval.py)

The reviewer writes one JSON file per case into a run folder:
  {"verdict": "approve" | "request_changes", "findings": [{"file", "line", "severity", "summary"}],
   "checks_seen": {"build": ..., "tests": ..., "package": ...}}

A planted defect counts as caught when a finding names the same file (or an "also" file), points
within LINE_SLACK lines of that file's planted range, and mentions at least one keyword.
"also" lists other places the same defect shows (e.g. the ini side of an ini/header mismatch).

An evidence defect ("checks") has no code line. Each key counts as one blocker, caught when the
reviewer's checks_seen has that key with a value other than "pass" AND the verdict is request_changes.

Bar (see evals/README.md):
  every blocker caught, overall recall >= 0.80, clean cases approved >= 0.80.

Usage: python3 tools/score_review.py evals/reviewer/cases evals/reviewer/runs/<run-id>
Exit 0 = bar met, 1 = bar missed, 2 = bad input.
```

Tests: `tests/test_score_review.py`

## Commands and checks

### `tools/check_pr.py`

Usage text from the file:

```text
Fail a PR whose body leaves a required template section empty.

Reads the PR body from $GITHUB_EVENT_PATH (GitHub Actions) or from a file argument.
Required sections come from .github/PULL_REQUEST_TEMPLATE.md.

Also checks:
  header    Evidence starts with the AGENTS.md section 5 line
            `commit=<sha> engine=5.8.4 config=<..> host=<win|mac> run=<..>`; with a known PR head
            (event or --head), the commit must match it, or the evidence is stale
  package   if the PR changes maps (*.umap), Config/**, *.Build.cs, *.Target.cs or *.uproject, or its
            Done-when (copied from the card) asks for package + SMOKE_OK, Evidence has the package
            script's `package exit: 0` line and the game's `SMOKE_OK map=<map> ...` line. "not run" for
            package or smoke fails (a human on the packaging machine adds the evidence before merge).
            Every SMOKE_OK line needs commit= (matching the header commit) and workbench=0. Changed paths come from
            --changed FILE (one per line, CI passes `git diff --name-only`) plus any such path named
            under "What changed"
  nonunity  if a changed path (--changed or "What changed") is under Source/, the header says engine=5.8.4 and a
            run other than none, and Evidence has the line `build exit: 0  mode=nonunity` that NONUNITY=1
            tools/ue/build.sh / build.ps1 -NonUnity prints, at the start of a line (D-new-nonunity-pr)
  exact     success lines are the tools' own lines at the start of a line (`package exit: 0`, `build exit: 0`,
            `PASS  tests=<n> failed=0`, the game's `[..]LogX: SMOKE_OK map=...` log line); a look-alike after
            other text ("expected:", "Not run:") fails. Any failing line of those kinds fails the PR, whatever
            else is pasted: `package exit: <n>0`, `build exit: <n>0`, `FAIL  tests=`, `SMOKE_FAIL` (final-6 B H6)
  commit    the build, test and package lines name the commit they ran on, and it is the header commit; the
            package line says dirty=no (final-7 B H7, M8): `build exit: 0  mode=nonunity  commit=<sha>`,
            `PASS  tests=<n> failed=0  commit=<sha>`, `package exit: 0  commit=<sha>  dirty=no`. The SMOKE_OK line
            may keep the `<file>.log:<n>:` prefix of a grep -n / Select-String hit; smoke.sh / smoke.ps1 print the
            game's line as is (final-7 A H2)
  run       the smoke script's own verdict, not only the game's SMOKE_OK line (final-8 A H1): with a SMOKE_OK line,
            Evidence also has smoke-log's `smoke: exit=0 SMOKE_OK=yes ...` summary with every count 0 and
            crash-check's `crash folders: 0 new`. Any tool failure line at the start of a line (`FAIL: ...`,
            `FAIL  tests=`, `crash folders: <n> new` with n > 0, a summary with exit or a count above 0) fails
  planted   a card whose Done-when asks for a failure on purpose (MustFail, a planted telegraph, a flipped flag,
            SMOKE_FORCE_CRASH) pastes it under a line `PLANTED FAIL: <what>`; that block runs to the next blank
            line. Its lines are neither failures nor passes. The block is allowed only when the linked card's
            Done-when (or, without --card, the PR's copy) has FAIL in capitals (final-8 A H3)
  card      with --card (CI passes the linked issue), the card's own Done-when also decides package evidence; a
            PR that needs package evidence has run=packaged in its header (final-6 A H4)
  proof     Evidence (below the header) has at least one re-runnable line: a command (`backticks`, tools/...,
            *.py/*.sh/*.ps1), tool output (PASS, FAIL, OK, exit N, key=value, "problem(s)", SMOKE_OK), a capture
            path (.png/.mp4/.log), or a "Not run: <what>, <why>" line. "all good, trust me" fails
  tests     if a changed path is under Source/, Evidence has the `tools/check_automation_report.py` result line
            (`PASS  tests=<n> failed=0`); a human on a CAN RUN build=n card pastes it before merge. The bootstrap
            line `... (bootstrap: placeholder tests only, card 0.3)` counts only when the Card ID is UE-0.3
  smoke     the SMOKE_OK line meets the smoke contract in tools/ue_run.py (fps, worst_ms, input=ok with a negative
            input_vz on a gameplay map, load_ms, a 16:9 gameplay view: view=WxH aspect=N within 0.01 of 1.778 and
            filling the window on one axis, and debugdraw=0: no debug draw in a default launch),
            when a .umap changed, map= names one of the changed maps, and a workbench= field reads 0: PR
            evidence comes from the submission package, never the -Workbench tester package (D-new-workbench-debug)
  bootstrap two scoped Day-1 exceptions to the package rule, each tied to repo state at the PR head so it ends
            by itself (dry run A C1: card 0.3 must merge before the smoke hook or MVP 2 exist):
              smoke  while Source/UmbrellaElla/Private/Smoke/ does not exist (card 0.6 not merged, and this PR does
                     not add it), `package exit: 0` plus a `SMOKE_BOOTSTRAP: no smoke hook before card 0.6` line
                     stands in for SMOKE_OK. Once the hook exists the line fails
              input  while the pipeline/qa/test-map.md QA-01 row (MVP 2 lift, UMB-01) is not `merged`, SMOKE_OK may
                     read input=none if Evidence shows the run used SMOKE_REQUIRE_INPUT=0 (card 0.6). After MVP 2
                     merges, input=ok is required again
            Nothing else is waived: "not run" still fails, and fps, worst_ms, load_ms and workbench still apply.
            Both waivers fail closed: a QA-01 Status other than exactly `planned` ends the input waiver, and any
            Source/ file that writes SMOKE_OK ends the smoke waiver (final-6 B M7, M8)
  art       every smoke ran art_check.py and screen_check.py on its own default-build screenshot (tools/ue_run.py
            smoke-log --shot): once the smoke hook exists, Evidence with a SMOKE_OK line also has the smoke's
            `smoke-art: art_check: PASS` and `smoke-art: screen_check: PASS ...` lines (and, on a map with a player,
            `smoke-art: art_judge: PASS scene ...`: the key-art composition judge), and any `smoke-art: <tool>: FAIL`
            fails. GitHub CI cannot run Unreal: the checks run in the smoke on the build machine (smoke.sh / smoke.ps1,
            the daily, kickoff's art gate) and this rule rejects a PR whose pasted smoke lacks them. Art bootstrap
            (repo state, ends by itself): until Content/UmbrellaElla/Art/Anchors/ exists (card 0.10b) a FAIL is
            accepted next to the smoke's `smoke-art: bootstrap: not blocking ...` line; after that the line fails.
            A PR that changes Content/**, pipeline/art/visual-align.json or UI or presenter code
            (Source/UmbrellaElla/*/UI/**, */Feedback/**) needs package + smoke evidence, so the art lines too
  artref    a PR that changes an art path (Content/*/Art/**, Content/*/UI/**, Content/*/VFX/**, Art/**,
            pipeline/art/**, *.sprite.json) or whose linked card is an art
            card (a card that pipeline/art/references.json assigns references to) has the line tools/art_ref_check.py
            prints: `art_ref_check: PASS card=<id> target=... refs=<hash12> commit=<sha> ...`, on the header commit and
            the current references.json hash (a PASS made against an older or smaller reference set fails); an art
            card's line names that card. Any `art_ref_check: FAIL` fails. The smoke's art_judge line carries refs= too
  artloop   a linked art card also has the `art_loop: PASS card=<id> piece=<p> verdict=<ours|same> ... refs=<hash12>
            commit=<sha>` line of each of its pieces (tools/art_loop.py: builder and blind critic until the critic
            cannot pick the reference over ours and every deterministic check passes; no round cap)
  artship   a PR that adds or changes shipped art (an image under Art/ outside Art/Source/) has, per file, the
            `art_loop: PASS ... commit=<header> file=<path> sha=<sha12>` line and the committed <stem>.artloop.json
            record for those exact bytes: a panel of 3 calibrated blind critics, unanimous ours or SAME against every
            reference of its element, the quality bar, the motion pair (a sheet) and the in-engine context; art_check,
            screen_check and art_ref_check PASS; current references.json. The gate re-runs those checks on the file
            itself (the record's word is not taken) and the record must name the piece its provenance names; only
            kickoff's art loop writes records (gates.json kickoff_only_paths). A Content/*/Art, VFX or UI .uasset
            change (visible UI too: menu screens, HUD art; not string tables, data tables or fonts) needs that line
            for the image it came from. A labelled placeholder or stand-in never passes; no label, sign-off or human
            approval waives it (tools/art_loop.py record_problems)
  hitbox    if the PR changes pipeline/feel/hitboxes.json, pipeline/art/visual-align.json or a sprite PNG hitboxes.json
            names (an art swap), Evidence has the `hitbox_check: PASS entities=<n> ...` line of
            `python3 tools/hitbox_check.py check`: the art was aligned to its collider and the check re-ran. A FAIL
            line from it fails the PR
  audio     if the PR changes a sound (a path under Audio/Source/<Id>/ or Content/UmbrellaElla/Audio/<Id>/, Core
            excluded), Evidence has the lines `python3 tools/audio_loop.py close --card <id>` prints, for the evidence
            header commit: `audio_loop close: PASS card=<the Task's Card ID> ...`, `audio_style check: PASS files=<n>
            commit=<sha> dirty=no`, and one `AUDIO LOOP: PASS piece=<Id> ... critic=<s> builder=<s> ...` line per
            changed sound id, with a critic session that is not the builder's. Any `audio_loop close: FAIL`,
            `audio_style check: FAIL` or `AUDIO LOOP: FAIL` line fails (pipeline/audio/style-target.md section 5).
            A sound whose every take is a tracked placeholder in this tree's provenance (the audio API could not
            make it) has the `AUDIO PLACEHOLDER: piece=<Id> ... commit=<sha>` line in place of its AUDIO LOOP line
  encounter if the PR changes pipeline/level/encounter.json, Evidence has `encounter_check: 0 problem(s)` and the PR
            carries `Encounter phases: <preset>/<phase>, ...` (or `Encounter phases: none (<why>)`). For each listed
            phase (in the PR or the linked card) the encounter critic loop must have passed: the newest
            `ENCOUNTER CRITIC:` line is PASS on the phase's current spec hash, by a critic session that is not the
            builder, each round with its playthrough= and check= scores (no round cap; stuck = 3 FAIL rounds with
            the same gap and no better score, then needs-human); plus the `playthrough_check: 0 problem(s)` and `encounter_ready: 0 problem(s)`
            lines (tools/encounter_spec.py C6-C9). A card or PR that lists phases needs them even without a data change
  bake      if the PR changes pipeline/qa/baked.json (tools/bake_preset.py), Evidence has its
            `bake_preset check: PASS preset=T-nn` line (D-new-workbench-debug)
  story     if the PR changes pipeline/story/** (the story bible, the text lines), Evidence has the
            `story_check: PASS bible=<h> sheet=<h> lines=<n> ...` line of `python3 tools/story_check.py` and the final
            `STORY_CRITIC: PASS ...` line of a separate critic session (tools/story_critic_prompt.md): same bible and
            sheet hashes as that PASS line and as the PR's files (any cycle: no cap), critic session other than
            the builder's. If it changes Content/UmbrellaElla/UI/ST_UI.csv or pipeline/submission/itch-page.md, Evidence
            has a `story_check: PASS` line (`--scan <file>`). Any `story_check: FAIL` line fails the PR. With --base, a
            bible row newly set to CONFIRMED needs `STORY CONFIRM: by=<game design owner> <row ids>` under Evidence: only
            Richard confirms canon (pipeline/roles/story.md)
  editor    if a changed path (--changed or "What changed") is a .uasset or .umap (editor MCP work included), Evidence
            has an `EDITOR CHECK: by=<the card's human> opened=<path>[,<path>...] ok` line naming every changed asset:
            the card's human opened each one in the editor and checked it (pipeline/agent-ops/editor-mcp.md)
  gate      a changed path that is a gate path (pipeline/agent-ops/gates.json gate_paths) is named in a
            `GATE EDIT: by=<name> <path>[,<path>]` line under Evidence. by=kickoff: kickoff applied the session's
            gate.patch through the tool checks (tools/git_gate.py apply --auto), and this rule re-runs them with --card
            and --base (lane, guardrail enforcers, no loosening). Any other by= is the card's Human or the TD human
            (JAM_HUMAN route). The git hooks stop agent commits for every agent; this is the CI backstop
  task      the Task section links the card: `Part of #<n>` (D-new-port-1 default) or
            `Closes|Fixes|Resolves #<n>`. Both pass until D-new-port-1 is decided
  links     every line under "Not done / risks" (except "none" and the Next: line) has a link:
            #<n>, a D-row id, or a URL
  next      a `Next:` line with a value under "Not done / risks"
  unread    a `Could not read:` line with a value under "Not done / risks": the card Inputs and cited docs the agent
            could not open (missing on main, an LFS pointer, no access), or "none". Nothing may rest on an unread
            source (docs/coverage-map.md, ported rule)
  journal   (not for a linked card whose Owner role is Human: its Journal says `Human card, no agent session`)
            "## Journal" holds the block `python3 tools/journal.py export --card <id>` prints: its
            `journal.py export card=<id>` line names the Task's Card ID, and it has a `Next step:` line
  gdd       if a changed path (--changed or "What changed") is under docs/gdd/ or is docs/feature-manifest.json, a
            "## GDD impact" section holds the pasted `tools/gdd_impact.py <old> <new>` output: its
            `gdd_impact old=<rev> new=<rev> ...` line and its `cited by:` list (docs/gdd/README.md)
  revert    a PR whose Evidence has `Revert of: <sha>` (tools/lane_guard.py writes it) is the revert-first PR of
            AGENTS.md section 6: it passes when its diff against the base (--base) is exactly the inverse of that
            commit (the same removed and added lines per file; context may differ, so a non-tip revert passes),
            every section is filled, Not done lines link, and the Journal says `Revert bot, no agent session`.
            Build, test, package and smoke evidence are not asked; the next daily builds and smokes main
            (final-10 A H3, final-11 A H2)
Usage: python3 tools/check_pr.py [body.md] [--changed files.txt] [--head SHA] [--base SHA]
```

Run in CI by:

- `.github/workflows/pipeline-checks.yml`: PR body has task, evidence header, package evidence where paths or the linked card need it, linked risks

Tests: `tests/test_agent_ops_hook.py`, `tests/test_art_ship.py`, `tests/test_audio_loop.py`, `tests/test_check_card.py`, `tests/test_check_pr.py`, `tests/test_encounter_presets.py`, `tests/test_final10_fixes.py`, `tests/test_final8_fixes.py`, `tests/test_git_gate.py`, `tests/test_hitbox_check.py`, `tests/test_honest_jam.py`, `tests/test_pipeline_check.py`, `tests/test_prompt_log.py`, `tests/test_story_check.py`, `tests/test_ue_scripts.py`
