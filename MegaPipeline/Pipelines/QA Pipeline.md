> Generated from `pipeline/qa/test-map.md`, `pipeline/qa/playtests.md`, `pipeline/qa/presets.json`, `pipeline/qa/no-player-maps.txt`, `pipeline/templates/test-note.md`, `tools/ue/daily-checklist.md`, `tools/ue/smoke-allow.txt`, `tools/check_automation_report.py`, `tools/ue/test.ps1`, `tools/ue/test.sh`, `tools/ue/daily.ps1`, `tools/ue/daily.sh`, `tools/ue/package.ps1`, `tools/ue/package.sh`, `tools/ue/smoke.ps1`, `tools/ue/smoke.sh` at `a11903f` — edit the sources, not this file.
> Rebuild: `python3 tools/export_package.py`. Check: `python3 tools/export_package.py --check`.

# QA Pipeline

A readable copy for people. Agents load these rules from the repo paths listed below.

## About this pipeline

- **Purpose:** Daily packaged build, smoke run, automation tests, the GDD test catalog and cold playtests.
- **Owner:** QA and Build role; the playtest lead (human) runs cold playtests.
- **Inputs:** `main` at the day's cut, the GDD test catalog, playtest presets.
- **Outputs:** Daily build records, automation results, bug cards, playtest rows and test notes.
- **Gates:** A red build is reported within the hour; a QA test row has a passing automation test before its feature is done.

## Built from

- Test catalog and playtests: `pipeline/qa/test-map.md`, `pipeline/qa/playtests.md`, `pipeline/qa/presets.json`, `pipeline/qa/no-player-maps.txt`
- Templates: `pipeline/templates/test-note.md`
- Daily build: `tools/ue/daily-checklist.md`, `tools/ue/smoke-allow.txt`
- Commands and checks: `tools/check_automation_report.py`, `tools/ue/test.ps1`, `tools/ue/test.sh`, `tools/ue/daily.ps1`, `tools/ue/daily.sh`, `tools/ue/package.ps1`, `tools/ue/package.sh`, `tools/ue/smoke.ps1`, `tools/ue/smoke.sh`

## Test catalog and playtests

### `pipeline/qa/test-map.md`

#### GDD test catalog (QA-01..QA-28) → required automation tests

> GDD SH1.0 note (D-new-gdd-sh10): lines on this page that still describe the GDD 1.3 encounter (one owl bolt, the front shield, the 90 s survival timer, wear stages, the 1.3 QA-01..QA-28 tests) are history. The current design is `docs/gdd/GDD-SH1.0.md` and `docs/feature-manifest.json`, which win; the owning role re-files this page against the SH1.0 Rule IDs on its next card.


Rows are the GDD SH1.0 QA-29..QA-42 tests (`docs/gdd/GDD-1.3.md`), keyed by QA ID, plus supporting rows. Each test the GDD lets code prove has named tests. The card that builds the item creates them with these
names (or edits this table in the same PR). The daily build runs
`python3 tools/check_automation_report.py Saved/Automation/index.json --baseline <n> --test-map pipeline/qa/test-map.md`
(`tools/ue/test.sh --baseline <n> --test-map pipeline/qa/test-map.md`, `test.ps1 -Baseline <n> -TestMap pipeline\qa\test-map.md`).
Only rows with Status `merged` are required. A missing name from a merged row fails the build record, so a
test cannot quietly disappear; a `planned` row does not turn the build red before its card exists.

One card per row: a row lists only tests that one card builds, and names that card in
brackets. A card marks only its own rows merged, so a test another card has not built yet never turns the daily red,
and a card's own tests are required from its merge on. A card that builds part of a row splits the row in its PR.
A QA ID may span several rows.

Who fills what:
- **Card** and **Status**: `planned` until the card that builds the item merges. That card's own PR writes its issue number (`#<n>`)
  and `merged` in the same diff; its reviewer checks it. Edits are row-scoped, so `check_card.py --lanes` ignores this file.
  `merged` without a Card number fails the check. Any other Status word fails it too.

Each row has a normal test and a blocked or boundary test. A row whose features are gated (`docs/feature-manifest.json` flag not null)
also runs with the flag off and must show the baseline unchanged (GDD SH1.0 CORE-04: a disabled optional module leaves movement, health, defeat,
restart and progression working). `Features` lists the manifest IDs; `tools/gdd_impact.py` finds a row by them when the GDD changes.

Time limit: a rule test must finish in ≤ 1 s (`--max-rule-seconds 1.0`). A test that loads a map or plays a
flow is a world test: write `(world)` after its name in the table, or put `.World.` in its name. World tests
have no 1 s limit; the editor timeout still applies. Adding a `(world)` mark is reviewed like any test change.

| QA | Features | Required tests | Card | Status |
|---|---|---|---|---|
| QA-01 | UMB-01, CORE-02, SURV-02, MOVE-02 | `UmbrellaElla.Umbrella.OpenRises`, `UmbrellaElla.Umbrella.NoLiftFallsAtGravity`, `UmbrellaElla.Umbrella.World.NoLiftMatchesNoUmbrellaFall` | | planned |
| QA-02 | UMB-01, UMB-02, UMB-03, UMB-04, CORE-01, COM-01, DEF-01 | `UmbrellaElla.Umbrella.TransitionsNeverStick`, `UmbrellaElla.Umbrella.SideFacingGivesNoLift`, `UmbrellaElla.Move.World.HorizontalIndependentOfUmbrella` | | planned |
| QA-03 | OWL-01, OWL-04 | `UmbrellaElla.Owl.World.BoltVolleyMatchesData`, `UmbrellaElla.Owl.World.OriginLockedDuringTelegraph` (MVP 7 owl card) | | planned |
| QA-03 | OWL-01, OWL-04 | `UmbrellaElla.Collision.World.TestBoltOverlapsEllaOnce` (the card that adds the projectile channel) | | planned |
| QA-03 | OWL-01, CORE-03 | `UmbrellaElla.Health.World.ProjectileHitsOnce` (MVP 4 Health card) | | planned |
| QA-04 | UMB-03 | `UmbrellaElla.Defense.CatchOnlyFromFacedSide`, `UmbrellaElla.Defense.World.CatchFailedIsVisible` | | planned |
| QA-05 | SURV-03, DEF-01 | `UmbrellaElla.Health.RecoveryFiresOnceCapsAtMax`, `UmbrellaElla.Health.BlockDuringCooldownDoesNotHeal` | | planned |
| QA-06 | CORE-03 | `UmbrellaElla.Health.ZeroHealthBroadcastsFail` (MVP 4 Health card) | | planned |
| QA-06 | FLOW-01 | `UmbrellaElla.Arena.World.BottomExitBroadcastsOnce` (MVP 1 arena card) | | planned |
| QA-06 | CORE-03, FLOW-01 | `UmbrellaElla.Flow.World.BottomExitFailsRun` (MVP 4 Encounter Director defeat card) | | planned |
| QA-06 | FLOW-01 | `UmbrellaElla.Flow.World.RestartTwiceSameState` (MVP 5 card) | | planned |
| QA-07 | WIND-01, WIND-02, OWL-02 | `UmbrellaElla.Gust.World.ForceWithoutWearWhenWearOff`, `UmbrellaElla.Gust.World.WearOnlyWhenWearOn` | | planned |
| QA-08 | OWL-01, OWL-03, COM-04 | `UmbrellaElla.Owl.World.SameSeedSameEventOrder` | | planned |
| QA-09 | END-01, FLOW-01 | `UmbrellaElla.Flow.World.EndTriggerStopsThreats`, `UmbrellaElla.Owl.World.NoDamageAfterEndTrigger` (MVP 6 card) | | planned |
| QA-09 | FLOW-01 | `UmbrellaElla.Flow.World.SurvivedCardShows` (card 0.21, the Survived screen) | | planned |
| QA-10 | SURV-03, UMB-03, WIND-02, HAZ-01, COM-03, SURV-04 | `UmbrellaElla.Harness.DisabledDependencyRejectedWithLog`, `UmbrellaElla.Harness.World.FlagsOffBaselineUnchanged`, `UmbrellaElla.Harness.FlagsMatchManifest` | | planned |
| QA-11 | FLOW-01, VFX-01 | `UmbrellaElla.Content.AllMapsLoad` (world); the package and `SMOKE_OK` line are the rest (`tools/ue/smoke.sh`) | | planned |
| QA-12 | UMB-02, UMB-03, SURV-03, WIND-01, COM-02 | none: a human test. Each run is a test note (`pipeline/templates/test-note.md`) that passes `python3 tools/manifest_check.py --note` | | planned |
| QA-13 | DEF-01, COM-01, UMB-01, UMB-02 | `UmbrellaElla.Umbrella.ShieldOverridesAttack`, `UmbrellaElla.Attack.NoShotsInShield`, `UmbrellaElla.Umbrella.ReleaseBothRestoresLift` | | planned |
| QA-14 | OWL-05, COM-04 | `UmbrellaElla.Owl.HitRegionClockPriority`, `UmbrellaElla.Owl.World.OneTargetHitPerProjectile`, `UmbrellaElla.Owl.World.HitsNeverKillOwl` | | planned |
| QA-15 | ANIM-01 | `UmbrellaElla.Anim.World.CoreLoopsMatchStates`, `UmbrellaElla.Anim.World.SpriteNeverChangesCollisionOrSpeed` | | planned |
| QA-16 | BG-01 | `UmbrellaElla.Background.World.FarSlowerThanNearSeamless`, `UmbrellaElla.Background.World.StaticFallbackSafe` | | planned |
| QA-17 | END-01, OWL-01, QA-BASE | `UmbrellaElla.Flow.World.BasePresetCompletesAt90s`, `UmbrellaElla.Harness.RunLogsSeedAndGddRevision` | | planned |
| QA-18 | QA-BASE, FLOW-01 | none in-editor: the submission package (Development until Richard decides D-new-gdd13-shipping; GDD QA-18 says shipping) and `SMOKE_OK` line (`tools/ue/smoke.sh`); the shipped defaults equal the baked BASE (`python3 tools/bake_preset.py check`) | | planned |
| QA-19 | FLOW-01 | none: a human release check (`pipeline/checklists/submission.md`, `tools/submission_check.py`) | | planned |
| QA-20 | FLOW-01, OWL-01, DEF-01 | `UmbrellaElla.Flow.World.RestartDuringTelegraphClean`, `UmbrellaElla.Flow.World.PauseFreezesTimersAndProjectiles`, `UmbrellaElla.Flow.World.OneTerminalEvent` | | planned |
| QA-21 | ANIM-01, COM-01 | `UmbrellaElla.Anim.SpriteMetadataMatchesSheet`, `UmbrellaElla.Anim.World.MuzzleStableAcrossFrames` | | planned |
| QA-22 | QA-BASE | `UmbrellaElla.Harness.PresetRoundTrip`, `UmbrellaElla.Harness.RestoreBaseHasNoRehearsalDefaults` | | planned |
| QA-23 | WIND-01, OWL-02 | `UmbrellaElla.Gust.World.EnvironmentalCurrentNoDamage`, `UmbrellaElla.Gust.World.DisabledOwlGustEmitsNothing` | | planned |
| QA-24 | BG-01, CAM-02 | `UmbrellaElla.Background.World.RenderModesSameSimulation` | | planned |
| QA-25 | ANIM-01, OWL-05 | `UmbrellaElla.Art.World.MissingSpritesShowFallbackAndStayPlayable` | | planned |
| QA-26 | ANIM-01, ART-02 | `UmbrellaElla.Art.World.ArtSwapSameReplay` | | planned |
| QA-27 | ANIM-01, ART-02 | `UmbrellaElla.Art.MismatchedSetReportsNoCollisionEdit` | | planned |
| QA-28 | ART-02, QA-BASE | none in-editor: the shipping package has no ART-02 selector and no unused candidate assets (package file list; shipped defaults by `python3 tools/bake_preset.py check`) | | planned |
| QA-GP | QA-BASE | `UmbrellaElla.Smoke.GamepadReachesMoveAttackShield` (card 0.6e: raw gamepad keys through the IMC move Ella and hold attack and shield; the packaged smoke logs `gamepad=ok`) | | planned |
| Health | SURV-02 | `UmbrellaElla.Health.WearStageFollowsHealth` (SURV-02: intact 67-100, damaged 34-66, critical 1-33, defeated 0; MVP 4 builds it, apart from QA-01 so MVP 2 can mark QA-01 merged) | | planned |
| Owl | OWL-01 | `UmbrellaElla.Owl.EveryPatternHasTelegraph`, `UmbrellaElla.Owl.PhaseTableDistinct` (card 0.5b; each builds its own transient data) | | planned |
| Owl phases | OWL-01 | `UmbrellaElla.Owl.World.PhaseChangePlaysCue` (only with 2+ phase presets, GDD SH1.0 OWL-06, OWL-35; the GDD 1.3 base has one phase, so it stays planned) | | planned |
| Encounter presets | OWL-01 | `UmbrellaElla.Owl.PresetLoadsFromEncounterJson`, `UmbrellaElla.Owl.World.NoAttackDuringTransition` (card 0.32) | | planned |
| Encounter run log | OWL-01 | `UmbrellaElla.Owl.World.PlaythroughLogLines` (card 0.31) | | planned |
| Attack | COM-01, UMB-02 | `UmbrellaElla.Attack.FirstShotOnEntry`, `UmbrellaElla.Attack.CadenceMatchesApproved`, `UmbrellaElla.Attack.FiresPlusXOnly`, `UmbrellaElla.Attack.StopsOnExit` (MVP 9 card) | | planned |
| Shield | DEF-01, SURV-03 | `UmbrellaElla.Defense.FrontalArcCatches`, `UmbrellaElla.Defense.World.CatchConsumesBoltNoDamage` (MVP 10 card) | | planned |
| Flow | FLOW-01 | `UmbrellaElla.Flow.RetryReturnsToStart` (MVP 5 card) | | planned |
| Flow | FLOW-01 | `UmbrellaElla.Flow.TitleToPlayToSurvived` (world) (card 0.21, the title and Survived screen C++) | | planned |
| Flow | FLOW-01 | `UmbrellaElla.Flow.World.MenuBlocksGameplayInput` (card 0.21) | | planned |
| Flow | FLOW-01 | `UmbrellaElla.Flow.RunLogWritesRow` (card 0.23) | | planned |
| Gust | OWL-02, WIND-01 | `UmbrellaElla.Gust.World.ZoneLiftsOpenUmbrella` | | planned |
| Wear | SURV-04, WIND-02 | `UmbrellaElla.Umbrella.WearLowersLiftByTier`, `UmbrellaElla.Umbrella.CriticalLiftStaysAboveFloor` | | planned |
| Feel | – | `UmbrellaElla.Content.NiagaraSettings` (world) | | planned |
| Feel | – | `UmbrellaElla.Feel.HitStopFrames` (world) | | planned |
| Feel | – | `UmbrellaElla.Feel.HitStopStacksMax` (world) | | planned |
| Feel | – | `UmbrellaElla.Feel.Hitboxes` (world) (card 0.28, the hitbox alignment card) | | planned |
| Feel | – | `UmbrellaElla.Feel.InputSameTick` (world) | | planned |
| Feel | – | `UmbrellaElla.Feel.OwlConditionSteps` (world) | | planned |
| Feel | – | `UmbrellaElla.Feel.ShakeCurve` (world) | | planned |
| Feel | – | `UmbrellaElla.Feel.SquashCurve` (world) | | planned |
| Feel | – | `UmbrellaElla.Feel.SquashScalesWithFallSpeed` (world) | | planned |
| Feel | – | `UmbrellaElla.Feel.ToggleAtRuntime` (world) | | planned |
| Feel | – | `UmbrellaElla.Feel.ToggleBuffer` (world) | | planned |
| Feel | – | `UmbrellaElla.Move.World.FeelEnvelope` | | planned |
| Content | – | `UmbrellaElla.Content.AllMapsLoad` (world) | | planned |
| Settings | – | `UmbrellaElla.Settings.WindowModePersists`, `UmbrellaElla.Settings.BadIniFallsBackToDefaults` | | planned |
| Display | FLOW-01 | `UmbrellaElla.Display.World.ViewLocked16x9`, `UmbrellaElla.Display.World.DebugDrawOffByDefault` (card 0.6) | | planned |
| Story | NAR-01 | `UmbrellaElla.Story.World.NoStoryCardWhileFlagOff` (the NAR-01 `Hook only` card: with flag NAR_01 off, title → play → Survived shows no `Story.*` string and waits for no story card) | | planned |
| Story | FLOW-01 | `UmbrellaElla.UI.World.ScreenTextComesFromStringTable` (card 0.21: every visible text on title, pause, settings, Survived and fail is a `ST_UI` key, so `story_check.py --table` and `--scan` cover all of it) | | planned |

UI tests are listed by `python3 tools/ui_check.py tests --tier all`; card 0.21 requires the P0 ones.
Notes on single tests:
- `NoLiftMatchesNoUmbrellaFall` (QA-01): from the same spawn, every NO_LIFT configuration falls exactly like plain gravity (same Z velocity each frame after the 0.2 s state blend, ±1%). No fast fall (GDD SH1.0 MOVE-19 critical invariant; MOVE-02 stays off).
- `SideFacingGivesNoLift` (QA-02): OPEN_LEFT and OPEN_RIGHT never apply lift (GDD SH1.0 MOVE-19 steps 7 and 9). `HorizontalIndependentOfUmbrella`: the same horizontal input gives the same horizontal velocity in every umbrella configuration (§3 step 5).
- `BottomExitBroadcastsOnce` (QA-06): leaving through the bottom edge broadcasts `PlayerDefeated` (reason bottom) once. `BottomExitFailsRun`: the Encounter Director goes to ENDING_FAILURE with that reason.
- `TestBoltOverlapsEllaOnce` (QA-03): a test-only projectile on the TD's projectile channel overlaps Ella once; the real owl bolt and Health reuse the channel. `ProjectileHitsOnce`: one bolt contact takes exactly one hit, even if several overlap events fire.
- Attack (COM-01, GDD SH1.0 OWL-08): `FirstShotOnEntry`: entering ATTACK_DESCENT fires one shot on that tick unless cooling down. `CadenceMatchesApproved`: held, the next shots come every `COM-01.cadence` active seconds (0.65, ±1 frame), read from the manifest value. `FiresPlusXOnly`: every shot moves along world +X whatever the sprite or facing. `StopsOnExit`: entering SHIELD_DESCENT or UP_OPEN fires no new shot from that tick.
- Shield (DEF-01, GDD SH1.0 SURV-05, FLOW-33, §7B): `FrontalArcCatches`: an owl bolt arriving inside the `DEF-01.shield_arc_deg` front arc (90°, so ±45° of +X facing) is caught, one just outside it hits. `CatchConsumesBoltNoDamage`: a caught bolt is consumed, sends one `CatchSucceeded`, and health does not drop.
- `SameSeedSameEventOrder` (QA-08): two runs with one preset and one seed log the same event names in the same order.
- `EndTriggerStopsThreats` (QA-09): after `EncounterCompleted` no projectile spawns and none deals damage, and the owl leaves the arena bounds before `end_event.quiet_sec` ends.
- `DisabledDependencyRejectedWithLog` (QA-10): enabling UMB-03 with DEF-01 off is refused with one `Warning` log line naming both IDs; nothing crashes (GDD 1.3 Appendix B: UMB-03 requires DEF-01). `FlagsOffBaselineUnchanged`: with every optional (non-APPROVED_P0) flag off, QA-01 and QA-06 still pass.
- Gust and Wear rows are gated features. `encounter_check.py` (gust coverage) and `submission_check.py footage --final` (gust and torn beats) require them only once their row is `merged`.
- `ZeroHealthBroadcastsFail`: Health only reports the defeat; the Encounter Director owns the retry (`pipeline/unreal/gameplay-code.md`).
- `RestartTwiceSameState`: fail → retry run twice leaves the same actor count and health (RESTARTING clears projectiles and timers).
- `TitleToPlayToSurvived`: from the title, a scripted run reaches `EncounterCompleted` and the Survived card with no debug skip.
- `MenuBlocksGameplayInput` (card 0.21 writes it, the TD checks it; it passes before the first menu card merges): open a menu, inject umbrella input, assert the umbrella state did not change. [VERIFY input injection API on 5.8.4]
- `Hitboxes` (card 0.28): every gameplay actor's collision shape equals its entry in `pipeline/feel/hitboxes.json` (type and size within 1 px, through the sprite's Pixels Per Unreal Unit), every entry has an actor, and each sprite component uses its visual-only scale and offset from `pipeline/art/visual-align.json`. Alignment of art to collider is `python3 tools/hitbox_check.py check`, required in CI; after any collider or art change it re-runs and the art swap waits for its PASS (`check_pr.py` rule hitbox). GDD 1.3 7C: colliders are gameplay data; only the art moves.
- `AllMapsLoad`: loads every map under `/Game/UmbrellaElla/Maps` in the editor with zero load errors. The daily smoke also loads each `+MapsToCook` map in the package.
- `ViewLocked16x9` (card 0.6; GDD SH1.0 OWL-07 fixed 16:9 gameplay camera, MVP 1): every cooked map's view target camera has Constrain Aspect Ratio on and Aspect Ratio within 0.001 of 16/9, and for a 2560x1080 and a 1280x800 viewport the constrained view rect is 1920x1080 and 1280x720 (centred, bars on the other axis). The packaged proof is the smoke's `view=`/`aspect=` and the display step at those sizes.
- `DebugDrawOffByDefault` (card 0.6): with no dev flag, `ue.Debug` reads 0, no collision or hitbox component is visible in game (bHiddenInGame), the Collision show flag is off and no on-screen debug message is queued, on every cooked map. The packaged proof is the smoke's `debugdraw=0` and its screenshot's `screen_check` PASS.
- `WindowModePersists` / `BadIniFallsBackToDefaults`: settings survive a reload; a garbage or missing ini loads defaults (resolution 1920x1080, team 11 Nov) without an error (`tools/ue/daily-checklist.md`).
- `ShieldOverridesAttack` (QA-13): ATTACK and SHIELD held together resolve to SHIELD_DESCENT; `NoShotsInShield`: no new shot while SHIELD is held; `ReleaseBothRestoresLift`: releasing both is UP_OPEN with lift on the same tick (GDD SH1.0 MOVE-19 step 6).
- `BlockDuringCooldownDoesNotHeal` (QA-05): a front catch inside the 2.0 s heal cooldown still blocks the bolt and heals 0 (GDD SH1.0 SURV-05, FLOW-33).
- `HitRegionClockPriority` (QA-14): a player bolt overlapping CLOCK and BODY emits one `BossTargetHit(region=CLOCK)`; the owl has no HP and never dies (GDD SH1.0 ANIM-02).
- QA-25..QA-28 (art swap): gameplay never reads sprite size, alpha, pose or background offset (GDD SH1.0 CORE-05). Same input replay and seed with another art set gives identical positions, shots, hits, HP and completion time.

### `pipeline/qa/playtests.md`

#### Playtests (cold players: never seen the game, no coaching)

> GDD SH1.0 note (D-new-gdd-sh10): lines on this page that still describe the GDD 1.3 encounter (one owl bolt, the front shield, the 90 s survival timer, wear stages, the 1.3 QA-01..QA-28 tests) are history. The current design is `docs/gdd/GDD-SH1.0.md` and `docs/feature-manifest.json`, which win; the owning role re-files this page against the SH1.0 Rule IDs on its next card.


At least 2 cold players per gate playtest; G3 has 4 (D-new-pool). The playtest lead lists 10 cold players on the Jam
tracker before G1 (G1 2, G2 2, G3 4, G4 2, none reused). Fewer than 2 left for a gate is a blocker the Producer reports a day ahead.
At least 1 of each gate's players does not play action games often. By G2 the list has 1 player with a visual or motor
impairment, or a line `none available` signed by the game design owner.
The game design owner watches every gate playtest, in the room or on a live screen share (D-new-owner-present). An agent cannot watch a player; it reads the log.
Any failure of P1, P2 or P4 blocks that day's gate. The GDD §11 gates map to these tests: movement prototype = P1, P2;
wind integration = P3; combat integration = P5; shield = P12; full encounter = P6, P7, P11; readability = P8.

##### Play data: the game counts, the observer explains
The Development package writes one CSV per session to `Saved/Playtest/<yyyymmdd-hhmmss>.csv` (card 0.23) [VERIFY: where a packaged Win64 build puts `Saved/`].
Columns: `session,event,phase,pattern_id,explained,t_run_s,build`.
- `event` is `hit`, `death` or `survive`. `phase` is `intro`, `contest` or `desperation`, or `base` when the encounter has no phase presets (GDD SH1.0 OWL-06, OWL-35: phases are optional). `pattern_id` is the hitting pattern's ID from `pipeline/level/encounter.json` (`BOTTOM_EXIT` for leaving through the bottom edge). `explained` is `y` or `n`, from the observer's "What hit you, and what warned you?" (P4). `t_run_s` is the time on the run timer.
- `python3 tools/encounter_check.py --playtest Saved/Playtest/*.csv` checks the rows (L1-L6; a log with no rows fails) and prints hits, deaths and `explained=n` per pattern. Paste it into the Measured column of P6 and P7. An `explained=n` hit is a bug against its `pattern_id`.
- If the CSV and the observer's tally differ by more than 1 for one player, the row is `invalid test` until someone finds why.
- Until card 0.23 merges, hits are counted by hand and the Measured cell says `hand count`.

##### How to run one
1. Use today's packaged Development integration build. Note its commit and the tuning commit: `git log -1 --format=%h -- 'Source/UmbrellaElla/Public/*/*Tuning.h'`.
2. Watch first, ask after. No question and no hint while the player is playing. At G3 and G4 the full run is never interrupted; questions come after the survey (D-new-session-order).
   Think aloud: before play, ask the player to say what they are doing and why. Never reply. After 30 s of silence, say only "keep talking".
3. The observer writes down: pauses over 3 s, each hit and fail with its pattern, where they got stuck, anything said aloud, any move a player repeats that skips a pattern or phase rule (corner hugging, staying low, never opening), and the device (keyboard or gamepad). At least one session per gate uses a real controller on the Windows package and posts `GAMEPAD: device=NAME move=ok attack=ok shield=ok pause=ok by=NAME` (card 0.6e; the automated `gamepad=ok` smoke does not replace it).
4. Order of one session: the full cold run; the survey, filled alone; one-on-one questions (P4, P9); freeze-frame tasks (P8) and the P10 sound tasks; a group talk last. Group comments never count toward a result.
5. A/B tests (feel toggles, presets T-02..T-07) alternate which version each player gets first (`docs/feel-spec.md` section 1).

##### When a result counts
- A row counts toward a gate only if Cold = y, Coached = n, and Build commit = the gate's build.
- Fewer than 2 valid cold players: the result is **insufficient**. Insufficient never passes a gate. P10 needs 3 (`audio_check.py --blind-id`).
- Report raw counts next to every percentage ("3 of 4 hits explained").
- One player stuck over 60 s, or quitting, opens a bug even if the other passed (D-new-port-5).
- A surprising single result first gets a bug check (does the build match the GDD?) and a retest, before any rule changes.

##### Every failing row gets
- A **class**: `bug` (build differs from GDD or spec → Gameplay Dev), `cue` (rule works, the player can't read it → Art Director, Integrator or Audio), `design` (rule works, play is bad → Game Designer or Level Designer: a tuning card or a decision row), or `invalid test`.
- A **severity**: `blocks gate`, `fix before submit`, `known limitation`, or `after jam`. At G3 and G4 nothing that blocks a gate stays open.
- Exactly one linked issue or decision row with one owner.

| ID | What | Method | Pass |
|---|---|---|---|
| P0 | Paper walk of the phase table (D-new-p0) | Before the first encounter card: 1 person outside the team reads `pipeline/level/encounter.md` and says, per phase, what the owl will do and where they would stand | Every misread opens a row on the encounter card. Never counts toward a gate; that person is not cold afterwards |
| P1 | Rise and fall understood | Time from first input to a deliberate rise → hold ATTACK or SHIELD to descend → release to rise (GDD SH1.0 section 1 Inputs) | Both players ≤ 30 s |
| P2 | Players predict and recover | Ask after the run: "What happens when you let go? When you hold attack or shield?" and "Why did you fail?" | Both answer rise/descend in their own words and name a real cause. "Yes, it's clear" is a fail |
| P3 | Wind is a choice | Count entries into the safe wind zone (WIND-01) on purpose vs avoided (observer tally) | Each player enters the wind zone on purpose at least once and avoids it at least once |
| P4 | Hit attribution | After the run, for each hit on the tally: "What hit you, and what warned you?" Log `explained` y/n with its `pattern_id` | ≥ 80% `explained=y`; each `n` opens a bug against its `pattern_id` |
| P5 | Shots land on purpose | Ask "When do your shots hit the owl?" | Both describe lining up with the owl |
| P6 | Survive or fail a full loop | Full cold run | Both reach the end or a fail and can retry without help; a designer run survives |
| P7 | No pattern spike | Hits per pattern, or per phase preset (`encounter_check.py --playtest`) | With 2+ owl patterns: no `pattern_id` has > 50% of all hits. With one pattern (the GDD 1.3 base bolt) and phase presets on: no phase has > 50%. One pattern, no presets: `n/a (one pattern)`, not a fail. Only with 3+ hits; else `too few hits` |
| P8 | Readability without a HUD | 4 in-engine captures (`CAM_Eval_Arena`, `CAM_Eval_Stress`); the player points at: me, umbrella state and wear, health, the next threat (no timer is shown, GDD 1.3 DEC-09) | ≥ 90% correct; 100% on "me" |
| P9 | Core decision felt | Ask "What were you deciding most of the time?" | Mentions rising vs falling, or catching vs avoiding wind |
| P12 | Shield blocks and heals | Count bolts the player blocks on purpose with the front shield (observer tally; `CatchSucceeded` lines in the run log), then ask "What did holding shield do?" | Each player blocks at least 1 bolt on purpose and says it stopped the hit and mended the umbrella (DEF-01, SURV-03) |
| P10 | Playable muted, sounds distinct | During the G3 playtest: one muted run (`audio_check.py --muted`), then the blind sound ID in `pipeline/audio/audio-rules.md` section 6 (`audio_check.py --blind-id`) | `--muted` PASS and `--blind-id` PASS, both outputs pasted |

Schedule: before the first encounter card: P0. G1: P1, P2, P3 (once the wind card, MVP 11, has merged). G2: P4, P5, P12 (once the MVP 10 shield card has merged), survey. G3 (4 players): P6, P7, P8, P10, survey, P11. G4: P9, survey, P11.

##### Survey (filled alone, before any talk)
Ratings are 1 (very low) to 7 (very high). One log row per player: Test = `SURVEY`, scores in Measured as `key=value`:
`fun=` · `again=y|n` ("Would you play it again?") · `intro=` `contest=` `desperation=` (difficulty; `-` if not reached).
"Was anything hard to see, hear or press?" goes word for word in Player said.
**P11 Fun (G3 and G4, D-new-fun):** median `fun` ≥ 5, written with "N of M"; `again=y` from at least half the valid players; no phase rated 7 by every player. A P11 fail needs a named exception with an owner and an hour in the gate record (only P1, P2 and P4 fails block it).

##### Results log
| Date | Gate | Build commit | Tuning commit | Test | Player | Cold (y/n) | Coached (y/n) | Design owner present (y/n) | Observed | Measured | Player said | Inferred | Result | Class, severity, link |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|

Player = a short id (`G3-a`), never a name. Observed = what the player did. Measured = counts and times. Player said = their words. Inferred = a guess, labelled as one.
Result is `pass`, `fail` or `insufficient`. The playtest lead signs each gate's rows on the gate record.

### `pipeline/qa/presets.json`

```json
{
 "gdd_revision": "SH1.0",
 "note": "GDD SH1.0 section 10 QA presets: only T-01 BASE is assigned; the other preset rows are blank templates ('T-<two digits>'), so no other preset exists yet (D-new-sh10-presets). The GDD 1.3 presets T-02..T-07 are history (docs/gdd/GDD-1.3.md section 10). The workbench that loads presets exists only in debug and dev builds (D-new-workbench-debug).",
 "presets": [
  {
   "id": "T-01",
   "name": "BASE",
   "enable": [],
   "disable": [],
   "learning_goal": "Does the complete game work with every APPROVED_P0 rule on: Start Game (Keeper fight, one basic shot) and Director's Cut (story, progression, full level, same Keeper fight)?",
   "note": "GDD SH1.0 section 10: 'The reviewed export requires T-01 BASE with empty enable / disable arrays.' Every APPROVED_P0 rule on; nothing else exists to enable."
  }
 ]
}
```

### `pipeline/qa/no-player-maps.txt`

```text
# Maps with no player pawn: the smoke accepts input=none on them (tools/ue_run.py no_player_maps, tools/check_pr.py).
# One row per map: <map short name> | <card that adds it> | <why there is no player>. The card that adds a cooked map
# with no player adds its row in the same PR (card 0.10a: L_StyleFrame). GameDefaultMap is never exempt.
L_Title | default | a separate title map, if a card adds one (the title screen normally runs on L_Graybox)
```

## Templates

### `pipeline/templates/test-note.md`

#### Test note (GDD 1.3 Appendix C)

> GDD SH1.0 note (D-new-gdd-sh10): lines on this page that still describe the GDD 1.3 encounter (one owl bolt, the front shield, the 90 s survival timer, wear stages, the 1.3 QA-01..QA-28 tests) are history. The current design is `docs/gdd/GDD-SH1.0.md` and `docs/feature-manifest.json`, which win; the owning role re-files this page against the SH1.0 Rule IDs on its next card.


One note per run. A tester (the GDD SH1.0 credits (FLOW-39), QA-12) writes it; the workbench exports it as JSON. Check it with
`python3 tools/manifest_check.py --note <note>.json` (exit 0). No personal data beyond the tester's team name.

| Field | What to record | JSON key |
|---|---|---|
| Build / run | Commit SHA, GDD revision, test ID, feature preset, random seed, date | `commit`, `gdd_revision`, `test_id` (QA-nn or T-nn), `preset` (T-nn), `seed`, `date` (YYYY-MM-DD) |
| What changed | The ONE important variable changed versus the comparison run | `what_changed` (one string) |
| Observed | Controls, visual clarity, failure reason, surprising interactions and reproducible steps. Failure reason is one of: player confusion, unfair pressure, unresponsive controls, bug (GDD B §11) | `observed` |
| Ratings | Fun, fairness, readability and responsiveness, each 1–5 (team scale) | `ratings.fun`, `ratings.fairness`, `ratings.readability`, `ratings.responsiveness` |
| Decision | Keep, revise, remove, retest. Include owner and a short rationale | `decision`, `owner`, `rationale` |

```json
{"commit": "abc1234", "gdd_revision": "1.3", "test_id": "QA-04", "preset": "T-03", "seed": 7, "date": "2026-11-13",
 "what_changed": "catch_window 0.2 s -> 0.3 s", "observed": "caught 4 of 6; failure reason: unresponsive controls",
 "ratings": {"fun": 4, "fairness": 3, "readability": 4, "responsiveness": 2},
 "decision": "retest", "owner": "Rick", "rationale": "window felt late"}
```
A note never promotes a feature (GDD SH1.0 section 12: notes are supporting evidence only). It is evidence for the design owner and the technical owner.

## Daily build

### `tools/ue/daily-checklist.md`

#### Daily build: switches by gate and hand checks (QA and Build, on demand)

`pipeline/roles/qa-build.md` links here. Load it when you run or record the daily build.

##### The smoke hook contract
The full contract is the docstring of `tools/ue_run.py` (switches, `SMOKE_OK` fields, `SMOKE_CYCLE` lines).
Card 0.6 builds it. Until a real Development package prints every field, each switch stays [VERIFY].
`daily` lists `real-engine pipeline (N VERIFY tag(s) left)` in `Not checked` while any tag is open.
`python3 tools/ue_run.py verify-tags` prints each one. Card 0.6d (due G3) closes them: each tag is
checked on 5.8.4 and removed, or turned into a decision row. Card 0.6 runs one smoke with
`SMOKE_FORCE_CRASH=1` (passes `-SmokeCrash`; the hook crashes on purpose). It must FAIL with
`new crash folder`. A PASS there means the crash paths are wrong.

Crash roots: `crash-check` exits 2 when none of the watched folders exists. Fix the path
(`SMOKE_CRASH_DIRS`); never treat that run as a pass.

##### Steps of `daily` (in order; it stops at the first failure)
| Step | Passes when |
|---|---|
| clean-tree | `git status --porcelain` is empty (or `--allow-dirty`; the record then says `+dirty`) |
| build | the editor target compiles |
| test | the report meets `check_automation_report.py` with `--baseline`, `--test-map` and the 1 s rule-test limit |
| alone | each merged test-map test not yet in `Saved/Logs/pipeline/alone-passed.txt` passes run alone (`ALONE_NEW=0` turns it off) |
| shuffle | the merged test-map tests pass again as one `RunTests A+B+...` list in a random order. The seed is printed (`SHUFFLE_SEED=<n>` replays it). Not run with fewer than 2 merged tests; `SHUFFLE_TESTS=0` turns it off |
| validate | `tools/ue/validate.*` (`-run=DataValidation` [VERIFY]) exits 0 with zero `Error:` lines; warnings are recorded |
| package | cook log has no `Error:`, and `cook warnings: N` is not above the last DAILY line. A rise passes only with `COOK_WARN_DECISION=<id>` naming a row in `docs/decisions.md` |
| smoke | every cooked map meets the contract. GameDefaultMap runs `SMOKE_REPEAT` times (default 1); any crash in any run fails |
| display | each mode that fits the monitor meets the contract plus `res=`, `win=`, `textpx=` (1280x720, 1280x800, 2560x1080 windowed; 1920x1080, 3840x2160 fullscreen) |
| settings | GameDefaultMap smoke with a garbage `GameUserSettings.ini`, then with `SETTINGS_OLD_INI` (the ini from the last gate zip), each reaches `SMOKE_OK`. The real ini is put back. `SETTINGS_INI` overrides the path [VERIFY] |
| client-test | `UmbrellaElla.Flow.TitleToPlayToSurvived` passes in the package, exit code 0, `-abslog` file exists, zero `SMOKE_BAD`/`SMOKE_BAD_BROAD` lines, no new crash folder |
| shipping-alive | only with `SHIPPING_EXE`: first window within `SMOKE_MAX_BOOT_S` (20 s, Windows only), alive at 15 s, closes with exit code 0, no new crash folder. `SHIPPING_REQUIRED=1` fails the step when `SHIPPING_EXE` is unset |
| workbench | the tester package (`package.sh --workbench` / `package.ps1 -Workbench`, target `UmbrellaEllaWorkbench`) into `Packaged-Workbench/` exits 0. Runs only after every step above passed; a failure makes the DAILY line FAIL. Not run while `Source/UmbrellaEllaWorkbench.Target.cs` is missing |

Day-1 bootstrap. It is scoped and ends by itself, like `SMOKE_BOOTSTRAP` in `tools/check_pr.py`:
- Until card 0.5 adds `Source/UmbrellaElla/Private/Tests/Meta/`, the test step runs `--bootstrap` (`-Bootstrap`):
  card 0.3's placeholder is the only test. Listed as `gameplay tests (bootstrap: ...)` in `Not checked`.
- Until card 0.6's smoke hook exists, the smoke step is one alive run (`SMOKE_MODE=alive`: running at 15 s, exit 0,
  no new crash folder), and display and settings do not run. Listed as `smoke contract (bootstrap: ...)`.
- `merge-check` counts these lines. A gate record never does: it needs `smoke=PASS(<n> map(s), repeat 5/5)`.
- `merge-check --require-client` asks for `client-test=PASS` only on commits whose own test map has the Flow row
  (`UmbrellaElla.Flow.TitleToPlayToSurvived`) merged.

Gate records read the DAILY line by step and by `Not checked` entry name (`NOT_CHECKED` in `tools/ue_run.py`):
every gate needs clean-tree, build, test, validate, package, smoke, display and settings = PASS. An entry for a
switch below that is past its gate is a P1 bug, so the record is `Pass with named exceptions` with it under Open
P0/P1. Entries for switches the docs leave off (Shipping smoke, `REF_HOST`, VERIFY tags, skipped display modes,
the old ini) never fail a gate.

Rule tests and world tests: a test marked `(world)` in `pipeline/qa/test-map.md`, or with `.World.` in its
name, has no 1 s limit. The packaged client-test step has no 1 s limit either.

Test files: a test that writes files writes them under `Saved/UmbrellaEllaTests/` and deletes them.
`test.*` removes leftovers from a crashed run before it starts, and fails if any file is left after it.
It also hashes `Saved/SaveGames/**` and `Saved/Config/*/GameUserSettings.ini` before the run and fails on any
change after it (`ue_run.py state-list` / `state-check`).

Reference host: the fps limits count only on the low-spec machine named in `REF_HOST` (open decision).
`daily` lists `reference host` in `Not checked` when `REF_HOST` is unset or differs from this machine.

Short form of one good line:
`SMOKE_OK map=L_Graybox fps=58 worst_ms=24 commit=abc1234 input=ok input_vz=-140 res=1920x1080 win=fullscreen textpx=20`
- `fps` is the 1% low over the 15 s window, not the mean. It must be ≥ 55.
- `worst_ms` is the slowest frame in the window. It must be ≤ 33.
- `input=ok input_vz=<cm/s>`: the hook held `IA_Attack` through Enhanced Input and, within 0.5 s, measured a Z
  velocity below 0 (`input_vz` < 0). GDD 1.3: with nothing held the umbrella is UP_OPEN and rises, so only descent
  proves input. `input=none` passes only on a map listed in `pipeline/qa/no-player-maps.txt`.
- `textpx` is the smallest visible UMG text height in px. It must be ≥ 18 on display runs.
- `load_ms` is the time from map load start to the first gameplay frame. It must be ≤ 10000
  (`SMOKE_MAX_LOAD_MS`). Each `SMOKE_CYCLE` line carries its restart `load_ms` too, held to the same limit.

##### Log lines
`smoke-log` fails on any `Error:` line in any Log category and any `Failed to load` line, as well as the
crash patterns. A known harmless line goes in `tools/ue/smoke-allow.txt` as `<decision id> | <regex>`.
The id must be a row in `docs/decisions.md`, or `smoke-log` exits 2 (smoke.sh / smoke.ps1 then exit 1). Crash patterns can never be allowed.

##### Switches by gate
Each switch that is off shows up in the DAILY line's `Not checked`. Past its gate, an input, gamepad, client-test or
restart-cycles entry is a P1 bug owned by QA and Build, filed the same day; `REF_HOST` and `SETTINGS_OLD_INI`
are recorded only and never fail a gate.

| Switch | Turn on by | What it adds |
|---|---|---|
| `SMOKE_REQUIRE_INPUT=1` (default) | Day 0 (`=0` only until MVP 2 merges) | `input=ok` on every gameplay map |
| `SMOKE_REQUIRE_GAMEPAD=1` (default) | G1 (`=0` only while the QA-GP row is planned; card 0.6e) | `gamepad=ok`: raw gamepad keys move Ella and hold attack and shield in the package |
| `CLIENT_TESTS=1` | G2 (the title screen is a GDD 1.3 §12A Nov 13 player screen) | `UmbrellaElla.Flow.TitleToPlayToSurvived` inside the package [VERIFY module] |
| `SMOKE_SECTIONS` and `SMOKE_SECTION_MAP` | removed | daily ignores them; the single arena needs no section smoke (D-new-cut5) |
| `SMOKE_RESTART_CYCLES=5` | G3 | 5 die → restart cycles; actor count and health must not drift |
| `SMOKE_REPEAT=5` | before each gate | GameDefaultMap smoked 5 times; any crash fails |
| art checks on the smoke screenshot (always on) | G2: the art bootstrap ends by itself when card 0.10b adds `Content/UmbrellaElla/Art/Anchors/`; until then `Not checked: art checks (no anchor art ...)` and the results print without failing | `art_check.py`, `screen_check.py`, `art_judge.py scene` on each smoke's `-SmokeShot=` screenshot |
| `REF_HOST=<machine name>` | Day 1: the weakest team laptop (D-new-ref-host) | the fps limits are checked on that host |
| `SETTINGS_OLD_INI=<ini from last gate zip>` | G1 | boot with the old settings file |

Display modes bigger than the monitor are skipped and listed as `display WxH <mode> (monitor WxH)`.
`SMOKE_DESKTOP_RES=WxH` overrides the size the OS reports.

##### Package at every merge
Before each gate, run `python3 tools/ue_run.py merge-check --since <last gate tag>`. Each first-parent
commit on `main` needs a DAILY line with `package=PASS`, `smoke=PASS` and no step `=FAIL`. From G2 add
`--require-client`, so `client-test=PASS` is needed too. A dirty run (`+dirty`) never counts.
Paste the summary line in the gate record. Who runs `daily` after each merge is an open decision
(proposed default: QA and Build, within 1 h of each merge to `main`; done when `merge-check` exits 0 at each gate).

##### Before each gate (commands)
- Fresh clone: empty folder, `git clone`, `git lfs pull`, build and package from it.
- Each test alone: `for t in $(python3 tools/check_automation_report.py --list-test-map pipeline/qa/test-map.md); do TEST_FILTER=$t tools/ue/test.sh --require $t || echo "ALONE FAIL $t"; done` (`test.ps1 -Filter <name>` on Windows).
- Repeat boots: `SMOKE_REPEAT=5` in the daily run; the gate record pastes that whole `DAILY <sha> | ...` line (the Build commit).
- `python3 tools/ue_run.py playthrough-check --commit <sha> --gate G<n>` (line below; `--gate-record` needs the `G<n>:` output). `shipping-check` is optional: no Shipping run is required (D-new-ship-required).

##### Hand-check record lines
Append to `Saved/Logs/pipeline/daily-records.txt` and post with the record. A blank field is not a pass.
`PLAYTHROUGH <sha> | <one field per phase preset in encounter.json, none for the GDD 1.3 base phase> | survived pass|fail | fail-retry pass|fail | fail-bottom pass|fail | quit-play pass|fail | quit-title pass|fail | quit-pause pass|fail`
Each phase is played through in order, never skipped with a debug jump. Quit means exit code 0, no new crash folder. `quit-play` (due from G1): from play, an in-game quit (key or button) closes the game; Alt+F4 or Task Manager is a fail.
`SHIPPING <sha> | boot_s=<seconds from launch to the title screen> | quit rc=<exit code>`
Shipping zip on a machine or user profile that never had the editor. `shipping-check` passes at `boot_s` ≤ 20 and `rc=0`.

##### Hand checks from G3 (one record line each)
Append the line to `Saved/Logs/pipeline/daily-records.txt` and post it with the record:
`STRESS <sha> | pause-restart pass|fail | pause-quit pass|fail | hold-alt-tab pass|fail | two-runs pass|fail |
audio-switch pass|fail (<n> s) | gamepad pass|fail|not merged`
`python3 tools/ue_run.py stress-check --commit <sha>` passes only when the line exists, every field is pass
(gamepad may be `not merged`), and audio resumed in ≤ 2 s.
- pause → restart and pause → quit mid-level.
- Hold the umbrella, pause or alt-tab, release, resume. The umbrella must be closed.
- Two full runs without relaunching.
- Switch the Windows default audio device mid-level. Audio continues within 2 s.
- If the gamepad stretch merged: unplug mid-level, the game pauses; replug, resume with no stuck input.
- Audio voices, on the packaged run: at the 90% timer mark, run the voice-count command in `pipeline/audio/audio-rules.md` section 4 and note active voices twice, 10 s apart. Then `python3 tools/audio_check.py --log <log>`. Fail if over 24 or rising.
A blank field is not a pass. Any stuck state is P1.

##### Display before each gate
`HighResShot` of title, HUD, pause and lose at 720p and 4K, attached to the record. Alt+Enter to fullscreen and
back mid-level with no cut-off or stretched UI.

### `tools/ue/smoke-allow.txt`

```text
# Log lines the smoke may contain although they match `Error:` or `Failed to load` (SMOKE_BAD_BROAD in
# tools/ue_run.py). One line each: <decision id> | <regex>. The id must be a row in docs/decisions.md, so
# this list only grows through a decision. Crash patterns (SMOKE_BAD) can never be allowed.
# Example: D<n> | LogAudio: Error: No default audio device
```

## Commands and checks

### `tools/check_automation_report.py`

Usage text from the file:

```text
Read Unreal's automation report (Saved/Automation/index.json) and decide pass/fail.

The editor's exit code alone does not prove tests ran. This fails when:
  - the report is missing or unreadable
  - zero tests ran
  - only placeholder tests ran (`UmbrellaElla.Bootstrap.*`) or no `UmbrellaElla.` test ran at all
  - any test failed, or any test did not run (state other than Success)
  - fewer tests ran than the baseline (tests were deleted or not discovered)
  - a test name required by the task card is absent (--require UmbrellaElla.Umbrella.OpenRises)
  - a test name from a `merged` row of pipeline/qa/test-map.md is absent (--test-map FILE). Rows still
    `planned` are not required, so the daily build does not go red for tests no merged card has made yet.
    A test-map row with an unknown Status, or `merged` without a `#<n>` Card, fails too.
  - a rule test took longer than --max-rule-seconds (default 1.0; 0 = off). A rule test is any `UmbrellaElla.`
    test without a `.World.` name segment and not marked `(world)` in the test map (--test-map FILE, or
    --world-map FILE for the marks alone, which test.sh / test.ps1 pass by default: final-10 A H4; the
    marker counts on every row, planned or merged, because a planned test that exists is still timed). It reads each test's `duration` (seconds) [VERIFY field on 5.8.4]
    and always prints the total suite time and the slowest test. While the limit is on, a rule test with no
    `duration` fails too: a missing measurement never counts as a pass.
--list-test-map FILE prints the required names of merged rows, one per line (for the gate isolation loop).

--bootstrap is for Day-0 card 0.3 only (pipeline/day0-cards.md): the skeleton has no gameplay tests yet,
so its run passes when at least one test ran, every test passed, and none is a real `UmbrellaElla.` test
(only the placeholder `UmbrellaElla.Bootstrap.*` or engine smoke tests). It refuses --baseline/--require/--test-map, and it fails as soon as a real
`UmbrellaElla.` test exists, so it cannot be used to skip checks later. "Zero tests" fails in both modes.

The result line names the commit it ran on (`PASS  tests=<n> failed=0  commit=<sha>`; --commit, default the repo's
HEAD), so tools/check_pr.py can tell a line from an earlier push (final-7 dry run B H7).

Usage: python3 tools/check_automation_report.py Saved/Automation/index.json [--baseline N] [--require NAME ...]
                                                [--test-map pipeline/qa/test-map.md] [--bootstrap] [--max-rule-seconds S]
       python3 tools/check_automation_report.py --list-test-map pipeline/qa/test-map.md
Exit 0 = pass, 1 = fail, 2 = report missing/unreadable or bad arguments.
```

Tests: `tests/test_check_automation_report.py`, `tests/test_check_pr.py`, `tests/test_final10_fixes.py`

### `tools/ue/test.ps1`

Usage text from the file:

```text
Run UmbrellaElla automation tests headless on Windows, then check the report (not the exit code).
-Filter <full test name> runs one test alone (gate isolation check in qa-build.md).
Tests that write files write under Saved\UmbrellaEllaTests and delete them. Leftovers from a crashed run are
removed before the run; any file left there after the run fails it. Save slots and GameUserSettings.ini
are hashed before the run; any change after it fails (state-check).
```

Tests: `tests/test_day0_cards.py`, `tests/test_final10_fixes.py`, `tests/test_practice.py`, `tests/test_ue_scripts.py`

### `tools/ue/test.sh`

Usage text from the file:

```text
Run UmbrellaElla automation tests headless on Mac, then check the report (not the exit code).
Extra arguments go to check_automation_report.py: --bootstrap (card 0.3 only), --require NAME...,
--test-map pipeline/qa/test-map.md (daily build), --max-rule-seconds S. BASELINE=<n> sets --baseline.
TEST_FILTER=<full test name> runs one test alone (gate isolation check in qa-build.md).
Tests that write files write under Saved/UmbrellaEllaTests and delete them. Leftovers from a crashed run are
removed before the run; any file left there after the run fails it. Save slots (Saved/SaveGames) and
Saved/Config/*/GameUserSettings.ini are hashed before the run; any change after it fails (state-check).
```

Tests: `tests/test_day0_cards.py`, `tests/test_final10_fixes.py`, `tests/test_git_gate.py`, `tests/test_honest_jam.py`, `tests/test_journal.py`, `tests/test_practice.py`, `tests/test_ue_scripts.py`

### `tools/ue/daily.ps1`

Usage text from the file:

```text
The daily integration build as one graph (Windows): clean-tree, build (non-unity: -DisableUnity -NoPCH -NoSharedPCH,
same as build.ps1 -NonUnity), test, alone, validate, package,
smoke every map, display runs, client-test, shipping-alive, then the tester package (workbench) (steps: tools\ue\daily-checklist.md). Stops at the first failing step, so a commit whose tests failed is never
packaged or smoked. Prints one record line and appends it to Saved\Logs\pipeline\daily-records.txt.
Usage: tools\ue\daily.ps1 [-AllowDirty]. Env as daily.sh. Steps and record format: tools\ue_run.py `daily`.
```

Tests: `tests/test_check_card.py`, `tests/test_day0_cards.py`, `tests/test_honest_jam.py`, `tests/test_kickoff_windows_daily.py`, `tests/test_ue_scripts.py`

### `tools/ue/daily.sh`

Usage text from the file:

```text
The daily integration build as one graph (Mac): clean-tree, build (non-unity: -DisableUnity -NoPCH -NoSharedPCH,
same as NONUNITY=1 tools/ue/build.sh), test, alone, validate, package,
smoke every map, display runs, client-test, shipping-alive, then the tester package (workbench) (steps: tools/ue/daily-checklist.md). Stops at the first failing step, so a commit whose tests failed is never
packaged or smoked. Prints one record line and appends it to Saved/Logs/pipeline/daily-records.txt.
Usage: tools/ue/daily.sh [--allow-dirty]. Env: SMOKE_EXE, SMOKE_DISPLAY_MODES, RULE_MAX_SECONDS (1.0),
CLIENT_TESTS=1 (packaged-client automation run), SMOKE_RESTART_CYCLES=5,
SMOKE_REQUIRE_INPUT (1), SMOKE_DESKTOP_RES (WxH; else read from the OS), SHIPPING_EXE (step shipping-alive, on a Shipping
package, only if D-new-smoke picks it), ALONE_NEW (1), COOK_WARN_DECISION=<decision id> (accepts a cook
warning rise), SMOKE_MAX_LOAD_MS (10000). Each check left off is listed in "Not checked".
Steps and record format: tools/ue_run.py `daily`. Merge coverage: tools/ue_run.py merge-check --since <ref>.
```

Tests: `tests/fixtures/kickoff/stub_daily.py`, `tests/test_day0_cards.py`, `tests/test_honest_jam.py`, `tests/test_kickoff_unattended.py`, `tests/test_kickoff_windows_daily.py`, `tests/test_ue_scripts.py`

### `tools/ue/package.ps1`

Usage text from the file:

```text
Package Win64 (only possible on Windows). The submission is this Development package (D25); -Shipping is optional.
Refuses a dirty git tree unless -AllowDirty (or ALLOW_DIRTY=1). build-info writes BUILD_INFO.txt into the package
and copies pipeline/submission/README.txt and LICENSE.txt next to the exe.
Default: the submission target UmbrellaElla, workbench compiled out (D-new-workbench-debug); workbench-check must pass.
-Workbench (or WORKBENCH=1): the tester target UmbrellaEllaWorkbench, never submitted (BuildCookRun -target= [VERIFY on 5.8.4]). Not with -Shipping.
```

Tests: `tests/fixtures/kickoff/stub_agent.py`, `tests/test_check_pr.py`, `tests/test_day0_cards.py`, `tests/test_final9_fixes.py`, `tests/test_honest_jam.py`, `tests/test_score_review.py`, `tests/test_submission_check.py`, `tests/test_ue_scripts.py`

### `tools/ue/package.sh`

Usage text from the file:

```text
Package a Mac build (Win64 must be packaged on Windows with package.ps1). SHIPPING=1 for Shipping.
Default: the submission target UmbrellaElla, workbench compiled out (D-new-workbench-debug); workbench-check must pass.
--workbench (or WORKBENCH=1): the tester target UmbrellaEllaWorkbench, never submitted (BuildCookRun -target= [VERIFY on 5.8.4]). Not with SHIPPING=1.
Refuses a dirty git tree unless --allow-dirty (or ALLOW_DIRTY=1). build-info writes BUILD_INFO.txt into the package
and copies pipeline/submission/README.txt and LICENSE.txt next to it.
```

Tests: `tests/test_day0_cards.py`, `tests/test_final9_fixes.py`, `tests/test_honest_jam.py`, `tests/test_score_review.py`, `tests/test_ue_scripts.py`

### `tools/ue/smoke.ps1`

Usage text from the file:

```text
Smoke a packaged build: run it with -SmokeQuitAfter=15, then check exit code, SMOKE_OK, fps and the
SMOKE_BAD log patterns in tools\ue_run.py (any > 0 fails), and fail on any new Saved\Crashes folder.
Usage: tools\ue\smoke.ps1 -Exe <packaged game .exe> [-Res 1280x720 -Window windowed|fullscreen] [-Alive]
Env as smoke.sh: SMOKE_TIMEOUT, SMOKE_MAP, SMOKE_GAME_MAP, SMOKE_MIN_FPS (55), SMOKE_RES, SMOKE_WINDOW,
SMOKE_MIN_TEXT_PX (18), SMOKE_MAX_FRAME_MS (33), SMOKE_MAX_LOAD_MS (10000), SMOKE_REQUIRE_INPUT (1), SMOKE_REQUIRE_GAMEPAD (1), SMOKE_SECTION, SMOKE_RESTART_CYCLES,
SMOKE_NO_PLAYER_MAPS (default: pipeline\qa\no-player-maps.txt), SMOKE_ALIVE_SECONDS (15), SMOKE_CRASH_DIRS (;-separated), SMOKE_MODE=alive. -Alive = no-log run (alive at 15 s,
closed by WM_CLOSE, exit 0); use it on Shipping only if D-new-smoke picks a Shipping smoke.
SMOKE_MAX_BOOT_S (alive: first window within N s, 0 = off), SMOKE_FORCE_CRASH=1 (passes -SmokeCrash; card 0.6).
Every run passes -SmokeShot=<png>: smoke-log runs art_check.py and screen_check.py on that default-build screenshot
(either FAIL fails the smoke) and checks view=/aspect= (16:9) and debugdraw=0. SMOKE_FORCE_NO_ASPECT=1 passes
-SmokeNoAspectLock, SMOKE_FORCE_DEBUGDRAW=1 passes -SmokeDebugDraw: proof runs that must FAIL (card 0.6).
SMOKE_ZIP=<gate zip> (the exe is from that zip, unzipped: a passing run appends its LAUNCH record line). The game's
SMOKE_EFFECTIVE line is checked by tools\bake_preset.py effective against baked.json and the manifest (final-9 B C1).
```

Tests: `tests/test_check_pr.py`, `tests/test_feel_check.py`, `tests/test_honest_jam.py`, `tests/test_ue_scripts.py`

### `tools/ue/smoke.sh`

Usage text from the file:

```text
Smoke a packaged build: run it with -SmokeQuitAfter=15, then check exit code, SMOKE_OK, fps and the
SMOKE_BAD log patterns in tools/ue_run.py (any > 0 fails), and fail on any new Saved/Crashes folder.
Usage: tools/ue/smoke.sh <path to packaged game executable>. Env (all optional):
  SMOKE_TIMEOUT=120  SMOKE_MAP=L_Graybox (short name the SMOKE_OK map= field must show)  SMOKE_GAME_MAP=/Game/UmbrellaElla/Maps/L_Graybox (full path, passes -SmokeMap=, card 0.6)
  SMOKE_MIN_FPS=55 (0 = off)  SMOKE_RES=1280x720 SMOKE_WINDOW=windowed|fullscreen (display run; also checks
  res=, win= and textpx >= SMOKE_MIN_TEXT_PX, default 18)  SMOKE_CRASH_DIRS=dir:dir (extra crash roots)
  SMOKE_MAX_FRAME_MS=33 (worst_ms limit, 0 = off)  SMOKE_MAX_LOAD_MS=10000 (load_ms limit, 0 = off)  SMOKE_REQUIRE_INPUT=1 (0 = skip input=ok)  SMOKE_REQUIRE_GAMEPAD=1 (0 = skip gamepad=ok)
  SMOKE_SECTION=S5 (passes -SmokeSection=)  SMOKE_RESTART_CYCLES=5 (passes -SmokeRestartCycles=, checks SMOKE_CYCLE)
  SMOKE_NO_PLAYER_MAPS (default: pipeline/qa/no-player-maps.txt)  SMOKE_ALIVE_SECONDS=15  SMOKE_MODE=alive: no-log run (alive at 15 s, closed, exit 0); Shipping only if D-new-smoke picks it.
  SMOKE_MAX_BOOT_S=20 (alive mode: first window within N s, 0 = off)  SMOKE_FORCE_CRASH=1 (passes -SmokeCrash; card 0.6
  proves crash-check catches it: the run must FAIL with a new crash folder)
  Every run passes -SmokeShot=<png>: smoke-log runs art_check.py and screen_check.py on that default-build screenshot
  (either FAIL fails the smoke) and checks view=/aspect= (16:9) and debugdraw=0. SMOKE_FORCE_NO_ASPECT=1 passes
  -SmokeNoAspectLock, SMOKE_FORCE_DEBUGDRAW=1 passes -SmokeDebugDraw: proof runs that must FAIL (card 0.6)
SMOKE_OK fields and switches: the smoke hook contract in tools/ue_run.py.
  SMOKE_ZIP=<gate zip> (the exe is from that zip, unzipped: a passing run appends its LAUNCH record line; launch-record
  fails when the exe is not a file of that zip, final-10 B H2)
The commit is checked against the package's BUILD_INFO.txt. The game's SMOKE_EFFECTIVE line (live tuning values and
flags, compiled-in commit and workbench) is checked by tools/bake_preset.py effective against baked.json and the
manifest (final-9 B C1).
```

Tests: `tests/test_check_pr.py`, `tests/test_day0_cards.py`, `tests/test_honest_jam.py`, `tests/test_ue_scripts.py`
