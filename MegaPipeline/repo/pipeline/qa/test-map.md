# GDD test catalog (QA-01..QA-28) → required automation tests

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
