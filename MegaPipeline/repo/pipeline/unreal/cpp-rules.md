# C++ rules (on demand; core: `pipeline/unreal-rules.md`)

Load when you write or review C++. The Dev Lead reviews every rule here.

## Modules are this project's "assembly definitions"
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

## C++ vs Blueprint (agents can diff text, not .uasset)
1. All gameplay rules in C++: umbrella state, vertical velocity, the firing lane, health, damage, owl patterns, survival end, win/lose. Put the rule core in plain functions so tests can call them without a world.
2. Blueprints are thin data subclasses (`BP_Ella : AEllaCharacter`) that only set asset references. No event-graph logic except cosmetic triggers.
3. Tuning lives in text: each component's `F<Comp>Tuning` struct defaults, gathered in the `UDeveloperSettings` class `UUmbrellaTuning` (`UCLASS(Config=Game, defaultconfig)`; no `defaultconfig` = saves to `Saved/`). Never edit tuning in Project Settings (that writes a `[/Script/UmbrellaElla.UmbrellaTuning]` section into `DefaultGame.ini`, which would override the baked defaults at runtime; `bake_preset.py defaults` and `check` fail any such section). Never hard-coded numbers in logic. [src: U22]
4. UI: C++ `UUserWidget` with `meta=(BindWidget)`; the UMG asset is layout only. Designer widget name = C++ property name, or the BP won't compile. [src: U23]
5. Asset references: `UPROPERTY(EditDefaultsOnly) TObjectPtr<...>` set in the BP. No `ConstructorHelpers` hard-coded paths.
6. Input: Enhanced Input (`IA_Move`, `IA_Attack`, `IA_Shield`, `IA_Pause`, `IA_Retry`, `IMC_Default`, `IMC_Menu`; GDD SH1.0 MOVE-04, DEC-01: hold `IA_Attack` = ATTACK_DESCENT with auto-fire (COM-01), hold `IA_Shield` = SHIELD_DESCENT (DEF-01), shield wins, release both = UP_OPEN; bindings in `docs/game-spec.md`). Menus (title, pause, win, lose) use `IMC_Menu` at priority 10: Flow adds it and removes `IMC_Default` when a menu opens, and reverses that when it closes, so gameplay actions never fire under a menu. [VERIFY priority and consume behavior on 5.8.4] Stick dead zones live in the `IA_Move` Dead Zone modifier, never in C++ (rule H). World test `UmbrellaElla.Flow.World.MenuBlocksGameplayInput` (card 0.21, checked by the TD): open a menu, inject `IA_Attack` and `IA_Shield`, assert the umbrella state did not change; done when it passes in `check_automation_report.py` output. [VERIFY input injection API on 5.8.4] No raw key polling (`IsInputKeyDown` and friends; module_check rule u). Hold vs toggle is D18. C++: `EnhancedInput` in Build.cs; `UEnhancedInputLocalPlayerSubsystem::AddMappingContext`; `BindAction` on `UEnhancedInputComponent` inside each component's own `BindInput`, which the character shell calls from `SetupPlayerInputComponent` (Movement binds `IA_Move`, Umbrella `IA_Attack` and `IA_Shield`, Flow `IA_Pause` and `IA_Retry`). [src: U30]
7. Collision channels defined in `DefaultEngine.ini` and mirrored in one C++ header. They must match.

## C++ correctness rules (the reviewer checks every one)
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

## C++ standard, checked by `tools/module_check.py` (rules h-P; full list: `python3 tools/module_check.py --help`)
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
