# Gameplay code and tests (on demand; core: `pipeline/unreal-rules.md`)

> GDD SH1.0 note (D-new-gdd-sh10): lines on this page that still describe the GDD 1.3 encounter (one owl bolt, the front shield, the 90 s survival timer, wear stages, the 1.3 QA-01..QA-28 tests) are history. The current design is `docs/gdd/GDD-SH1.0.md` and `docs/feature-manifest.json`, which win; the owning role re-files this page against the SH1.0 Rule IDs on its next card.


Load when you write or review gameplay code or tests. C++ rules: `pipeline/unreal/cpp-rules.md`.

## Code layout: lanes = GDD SH1.0 CORE-04 modules (so cards can run in parallel)
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

## Events and encounter states (GDD SH1.0 CORE-04, §7B, §8)
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

## Gameplay structure rules (the reviewer checks these too)
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

## Tests (pattern built by Day-0 card 0.5)
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
