> Generated from `pipeline/level/encounter.md`, `pipeline/level/encounter.json`, `pipeline/checklists/level-sections.md`, `pipeline/level/reference/owl-fight-ricky.md`, `pipeline/level/fixtures/card_ok.md`, `pipeline/level/fixtures/logger_output.csv`, `tools/encounter_check.py`, `tools/encounter_spec.py` at `a11903f` — edit the sources, not this file.
> Rebuild: `python3 tools/export_package.py`. Check: `python3 tools/export_package.py --check`.

# Level Pipeline

A readable copy for people. Agents load these rules from the repo paths listed below.

## About this pipeline

- **Purpose:** One arena and one owl encounter in three phases, described as data and checked before it is built.
- **Owner:** Level Designer (arena numbers, owl patterns, pacing), Encounter Designer (the boss fight as a whole: encounter presets, critic loop) and Integrator (map, placement, thin Blueprints).
- **Inputs:** The GDD encounter rules, `docs/balance.md`, playtest hit logs.
- **Outputs:** `pipeline/level/encounter.json` (top-level data and `encounter_presets`), the generated tables in `pipeline/level/encounter.md`, the arena map.
- **Gates:** `encounter_check.py` (data, presets, wiring, playtest, run log, critic lines) in CI and before `doing`; `check_pr.py` rule encounter; the arena acceptance checklist.

## Built from

- Encounter data: `pipeline/level/encounter.md`, `pipeline/level/encounter.json`
- Checklists: `pipeline/checklists/level-sections.md`
- Encounter references: `pipeline/level/reference/owl-fight-ricky.md`
- Check fixtures: `pipeline/level/fixtures/card_ok.md`, `pipeline/level/fixtures/logger_output.csv`
- Commands and checks: `tools/encounter_check.py`, `tools/encounter_spec.py`

## Encounter data

### `pipeline/level/encounter.md`

#### THE LAST HOUR: encounter tables

> GDD SH1.0 note (D-new-gdd-sh10): lines on this page that still describe the GDD 1.3 encounter (one owl bolt, the front shield, the 90 s survival timer, wear stages, the 1.3 QA-01..QA-28 tests) are history. The current design is `docs/gdd/GDD-SH1.0.md` and `docs/feature-manifest.json`, which win; the owning role re-files this page against the SH1.0 Rule IDs on its next card.


Source of the numbers: `pipeline/level/encounter.json`. The Level Designer edits that file only.
The block below is generated. Do not edit it by hand. After a data change run:

```
python3 tools/encounter_check.py --write-md
python3 tools/encounter_check.py
```

Paste the second command's output (tuning read, breathers, intensity, `0 problem(s)`) on the card.
Encounter Director states (GDD SH1.0 OWL-06, OWL-35): READY → ACTIVE → ENDING_SUCCESS or ENDING_FAILURE → RESTARTING → READY, plus PAUSED.
ENDING_SUCCESS stops and disables every threat before the owl departs; no lethal contact after `EncounterCompleted` (QA-09).
Baseline (GDD SH1.0 rule numbers (section 9 ranges blank, D-new-sh10-param-ranges), §7B, §8; manifest `approved_parameters`): 90 s of ACTIVE time, one phase `base`, one bolt `BOLT_Single`
(OWL-01): 2.0 s grace, then a 0.75 s warning every 3.0 s, a straight 350 cm/s bolt aimed at the player's position when the
windup starts, seed 20261112. E29 fails a warning, speed, interval or duration outside its GDD SH1.0 rule numbers (section 9 ranges blank, D-new-sh10-param-ranges) range, a different grace or seed, or any pattern whose `feature` is off.
Phases (intro, contest, desperation) are optional tuning presets, not required (GDD SH1.0 OWL-06, OWL-35). Extra patterns (`GUST_*` OWL-02,
`ARC_*` OWL-04, other bolts) need their feature on through a DECIDED decision row and a manifest PR first. The rules that
compare patterns (E4, E7, E8, E14 rows, E19, E21, E24, E26 breather) apply only once 2+ patterns are scheduled; E25 only with lift loss (SURV-04).
Build order: MVP 7 builds `BOLT_Single` only (OWL-01).
Rules and their ids (E1-E29, L1-L6, V1-V2, W1-W5, C1-C5) are in the checker's header and in `pipeline/checklists/level-sections.md`.

Numbers are Richard's approved provisional tuning (GDD SH1.0 rule numbers (section 9 ranges blank, D-new-sh10-param-ranges)), not balanced values. A change goes through the GDD and the manifest first.

##### How the data maps to Unreal [VERIFY: no engine here]
- One `UOwlPatternData` primary data asset per row of `patterns` (`DA_OwlPattern_<ID>`). Fields: Feature, Kind, TelegraphSec,
  ActiveSec, RecoverySec, TellPose, TellSound, TellVFX, Colour, AnglesDeg, Aimed, BaseAngleDeg, Speed,
  SpawnOffsetSec, Volleys, VolleyGapSec, SeedOffsetDeg, SeedAngleStepDeg, GustZone, InterruptibleSec and
  InterruptReplaysTelegraph (clock hit, E26), for the gust GustStrengthByWingTier and WingTearOverlays (wing hit, E27),
  and for the arc Reach, Side, FlightSec, CoreRadius (the out-and-back loop the checker simulates).
- Folder (a naming rule, not an engine fact): every pattern and phase asset lives in `Content/UmbrellaElla/Data/Owl/`.
- One `UOwlPhaseData` asset per phase (`DA_Phase_Base`; the optional presets `DA_Phase_Intro`, `DA_Phase_Contest`,
  `DA_Phase_Desperation`): StartPct, EndPct, SpaceRules, AltitudeCapY, Schedule (array of {AtSec, Pattern}).
- Adding or cutting a pattern = one row here plus one data asset. No Blueprint or C++ change.
- The engine assets and this JSON must match. The Integrator's dump card (`level-sections.md`, "Who builds the
  engine half") writes the assets as JSON; `encounter_check.py --data <dump>` must pass on it too.
- Hero speeds and hitbox ratios are not in this JSON. They come from `pipeline/feel/feel.json` (Game Designer, E22).

<!-- BEGIN GENERATED by encounter_check.py --write-md; do not edit by hand -->
Encounter length: 90 s (GDD 1.3 END-01, §8: unpaused ACTIVE time; approved provisional default). One phase, no phase-change cue. Seed: 20261112.
End clue: - (optional; narrative is DEFERRED).

###### Phases

| Phase | % of timer | Seconds | Patterns | Space rules | Longest breather |
|---|---|---|---|---|---|
| base | 0-100 | 0.0-90.0 | BOLT_Single | - | 2.0 s |

###### Patterns

| ID | Feature | Kind | Colour | Telegraph / active / recovery s | Count x volleys | Angles | Aimed | Speed | Stagger s | Seed step | Clock-hit pause s | Tell (pose / sound / VFX) |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| BOLT_Single | OWL-01 | bolt | amber | 0.75 / 0.1 / 1.0 | 1 x 1 | [0] | yes | 350 | 0 | 0 | 0 | Owl_Attack_Windup / SFX_OwlBoltWindup / VFX_ClockFlash_Amber |

###### Coverage (with 2+ patterns, rows must have an X in a pattern used by the end of contest)

| Row | BOLT_Single |
|---|---|
| pos_high | X |
| pos_low | X |
| pos_far |  |
| ctl_rise | X |
| ctl_fall | X |
| ctl_horizontal |  |
| ctl_gust |  |
<!-- END GENERATED -->

##### Encounter presets

The fight as a whole (phases, targets with HP, attacks with telegraph, effect and counterplay, transitions, pacing)
lives in `encounter_presets` in `pipeline/level/encounter.json`. Owner: the Encounter Designer
(`pipeline/roles/encounter-designer.md`). The Level Designer keeps the top-level arena, pattern and schedule data,
which the GDD 1.3 baseline preset reads. A proposed preset never ships until its decision row is DECIDED.
Rules S1-S13, P1-P8 and C6-C9 are in `tools/encounter_spec.py`. The block below is generated by `--write-md`.

<!-- BEGIN GENERATED PRESETS by encounter_check.py --write-md; do not edit by hand -->
Default preset: `GDD-SH1.0`. Select another in a workbench or practice build with `UmbrellaElla.Encounter.Preset`; list them with `python3 tools/encounter_check.py --presets --gdd 1.3`.

###### Preset GDD-SH1.0 (baseline)

GDD SH1.0 Keeper fight: wings, the three hanging mechanisms, then the clock (both modes)

Entry: full_run -> wings. Target length 60-240 s; estimated 103-142 s.

| Phase | Targets | Attacks | Ends when | Transition in | Next |
|---|---|---|---|---|---|
| wings | WINGS | RED_Fan, YELLOW_Packet, GUST_Band, TALON_Rake | broken: WINGS | 2.0 s, no new attacks, in flight: none | mechanisms |
| mechanisms | MECH_FRONT, MECH_MIDDLE, MECH_REAR, CLOCK | MECH_Front_Cast, MECH_Middle_Curve, MECH_Rear_TwoStage, RED_Fan, YELLOW_Packet, TALON_Rake | broken: MECH_FRONT, MECH_MIDDLE, MECH_REAR | 2.0 s, no new attacks, in flight: dangerous | clock |
| clock | CLOCK | CLOCK_DoubleBeat, YELLOW_Packet, TALON_Rake | CLOCK at 0 HP | 2.0 s, no new attacks, in flight: dangerous | end of fight |

| Target | HP | Hitbox | Vulnerable in | Hit share | On break |
|---|---|---|---|---|---|
| WINGS | 180 | keeper-wing | wings | 0.15 | cancels GUST_Band; in flight: cleared |
| MECH_FRONT | 100 | keeper-mech-front | mechanisms | 0.15 | cancels MECH_Front_Cast; stun 1.2 s; exposes CLOCK; in flight: dangerous |
| MECH_MIDDLE | 110 | keeper-mech-middle | mechanisms | 0.15 | cancels MECH_Middle_Curve; stun 1.2 s; exposes CLOCK; in flight: dangerous |
| MECH_REAR | 120 | keeper-mech-rear | mechanisms | 0.15 | cancels MECH_Rear_TwoStage; stun 1.2 s; exposes CLOCK; in flight: dangerous |
| CLOCK | 320 (keeps 40% until the final phase) | keeper-clock | mechanisms, clock | 0.1 | - |

| Attack | Phases | Telegraph s | Shows | Effect | Counterplay | Art | Sound |
|---|---|---|---|---|---|---|---|
| RED_Fan | wings, mechanisms | 0 | the launch / aim posture and the captured lane; no timed prefire delay (OWL-12) | damage 1, shots 4, spacing_sec 0.09, reduced one shot, every 2.16 s while a physical attack warns or strikes (OWL-11), absorbable False | move_off_line | keeper, red-shot, shot-impact | KeeperRedLaunch, RedShotTravel, PlayerHurt |
| CLOCK_DoubleBeat | clock | 0 | the clock hand beat XII to III and the first group's captured paths (OWL-28) | damage 1, shots 4, spacing_sec 0.09, speed 300, spread 48, repeat_wait_sec 0.6, recovery_sec 0.85, repeat the same captured paths once, never re-aimed, absorbable False | leave_first_pattern; dont_drift_back | keeper, red-shot, clock-beat | ClockBeat, ClockBeatRepeat, KeeperRedLaunch, PlayerHurt |
| YELLOW_Packet | wings, mechanisms, clock | 0 | two slower aimed packets with their own rhythm, trail and sound (OWL-14) | damage 1, shots 2, size 1.2, absorbable True, on_catch absorbing while dropping heals 0.5 + 0.3 per recovery rank, active life first; no XP, no ammunition, no stored energy (UMB-05) | absorb; dodge | yellow-shot, yellow-capture | KeeperYellowLaunch, YellowCatch, UmbrellaRepair |
| GUST_Band | wings | 1.1 | the wing gather / load and the locked altitude band (OWL-15) | damage 1, push 280, speed 350, band_width 120, lifetime_sec 3, bypasses ordinary post-hit and hop protection; dash protection stops the damage, never the push (OWL-16) | leave_band | keeper, hostile-gust | GustWarning, GustRelease, GustTravelLoop, PlayerHurt |
| TALON_Rake | wings, mechanisms, clock | 1.05 | the EMPTY claw drawn back and spread (OWL-18) | damage 1.5, tip_width 48, strike_sec 0.18, recovery_sec 1, cooldown_sec 3.5, strike one sweep toward the captured target, at most once per cast | bait_then_leave; change_altitude | keeper, talon | TalonWarning, TalonSlash, TalonRecovery, PlayerHurt |
| MECH_Front_Cast | mechanisms | 0.9 | the closed claw gripping the armillary ring and the locked destination (OWL-21) | damage 1.25, reach 800, speed 400, head_width 32, return_sec 1.2, path straight to the captured endpoint | move_off_line | mechanism-head, mechanism-chain, talon | CastWarning, FrontCastLaunch, ChainTravel, CastReturn, PlayerHurt |
| MECH_Middle_Curve | mechanisms | 0.9 | the curved stroke it will follow, sign by the global physical-attack serial (OWL-24) | damage 1.25, reach 800, speed 400, head_width 32, return_sec 1.2, path a +/-80 sine curve to the same endpoint, offset 80 | move_off_line; clear_curve | mechanism-head, mechanism-chain, talon | CastWarning, MiddleCastLaunch, ChainTravel, CastReturn, PlayerHurt |
| MECH_Rear_TwoStage | mechanisms | 0.9 | the line to the original endpoint; the second clack says it is not finished (OWL-27) | damage 1.25, reach 800, speed 400, head_width 32, return_sec 1.2, path half the stroke, a safe 0.65 s pause, then on to the original endpoint, pause_sec 0.65 | move_off_line; stay_clear_after_pause | mechanism-head, mechanism-chain, talon | CastWarning, RearCastLaunch, RearMidpointClack, ChainTravel, CastReturn, PlayerHurt |

End: final clock completion stops combat damage once; the Keeper withdraws alive in about 2.5 s (OWL-35, NAR-07).
<!-- END GENERATED PRESETS -->

### `pipeline/level/encounter.json`

```json
{
  "version": 3,
  "gdd_revision": "SH1.0",
  "model": "state",
  "model_note": "GDD SH1.0: the Keeper fight is state-driven (HP-gated phases, an interval scheduler, phase-start checkpoints), so the fight is the baseline preset below. The GDD 1.3 timer timeline (top-level patterns, phases, duration_sec) is history: tests/fixtures/gdd13/encounter.json.",
  "arena": {
    "units": "GDD world units = Unreal cm (D-new-sh10-units); x right, y up from the bottom edge of the fixed camera view",
    "width": 1920,
    "height": 1080,
    "tuning_source": "pipeline/feel/feel.json",
    "tuning_note": "Ella's speeds and the fixed collider sizes come from the tuning file (Game Designer), which mirrors the manifest approved_parameters. Never copy them here."
  },
  "encounter_presets": {
    "_about": "Encounter presets (owner: Encounter Designer, pipeline/roles/encounter-designer.md). The fight as a whole: phases, targets with HP, attacks with their telegraph, effect and counterplay, phase transitions, pacing and story beats. Gameplay code reads the selected preset from this file (never hardcoded). The default preset is the GDD SH1.0 baseline Keeper fight: every GDD number it uses is listed in numbers_from_gdd and equals the manifest start (E29). Any other preset is PROPOSED: selectable only in workbench and practice builds and through the GDD picker, never shipped, until its decision row is DECIDED by its owner. Checked by tools/encounter_check.py (S rules; --ready for the hitbox, art and sound rows; --playthrough for the automated run log; --critic-packet and the card rules C6-C8 for the critic loop).",
    "default": "GDD-SH1.0",
    "presets": {
      "GDD-SH1.0": {
        "status": "baseline",
        "title": "GDD SH1.0 Keeper fight: wings, the three hanging mechanisms, then the clock (both modes)",
        "gdd_revision": "SH1.0",
        "source": "GDD SH1.0 section 5 (OWL-06..OWL-35) and the incoming damage of FLOW-33. Every number in numbers_from_gdd is the manifest start (E29); first_at, transition seconds, hit_share and fight_length_sec are pipeline prototype defaults (D-new-sh10-open-details)",
        "selectable_in": [
          "ship",
          "workbench",
          "practice",
          "gdd_picker"
        ],
        "modes": [
          "Start Game",
          "Director's Cut"
        ],
        "numbers_from_gdd": {
          "targets.WINGS.hp": "OWL-08.wings_hp",
          "targets.MECH_FRONT.hp": "OWL-08.front_hp",
          "targets.MECH_MIDDLE.hp": "OWL-08.middle_hp",
          "targets.MECH_REAR.hp": "OWL-08.rear_hp",
          "targets.CLOCK.hp": "OWL-08.clock_hp",
          "targets.MECH_FRONT.on_break.stun_sec": "OWL-30.break_stun_s",
          "targets.MECH_MIDDLE.on_break.stun_sec": "OWL-30.break_stun_s",
          "targets.MECH_REAR.on_break.stun_sec": "OWL-30.break_stun_s",
          "attacks.RED_Fan.cadence_by_phase.wings": "OWL-11.red_interval_s",
          "attacks.RED_Fan.cadence_by_phase.mechanisms": "OWL-11.red_interval_s",
          "attacks.RED_Fan.effect.damage": "FLOW-33.projectile_damage",
          "attacks.RED_Fan.effect.spacing_sec": "OWL-11.red_spacing_s",
          "attacks.RED_Fan.effect.speed_by_phase.wings": "OWL-11.red_speed_wings",
          "attacks.RED_Fan.effect.speed_by_phase.mechanisms": "OWL-11.red_speed_mechanisms",
          "attacks.RED_Fan.effect.spread_by_phase.wings": "OWL-11.red_spread_wings_deg",
          "attacks.RED_Fan.effect.spread_by_phase.mechanisms": "OWL-11.red_spread_mechanisms_deg",
          "attacks.CLOCK_DoubleBeat.effect.damage": "FLOW-33.projectile_damage",
          "attacks.CLOCK_DoubleBeat.effect.speed": "OWL-11.red_speed_clock",
          "attacks.CLOCK_DoubleBeat.effect.spread": "OWL-11.red_spread_clock_deg",
          "attacks.CLOCK_DoubleBeat.effect.repeat_wait_sec": "OWL-28.repeat_wait_s",
          "attacks.CLOCK_DoubleBeat.effect.recovery_sec": "OWL-28.repeat_recovery_s",
          "attacks.CLOCK_DoubleBeat.effect.spacing_sec": "OWL-11.red_spacing_s",
          "attacks.YELLOW_Packet.cadence_sec": "OWL-13.yellow_interval_s",
          "attacks.YELLOW_Packet.effect.damage": "FLOW-33.projectile_damage",
          "attacks.YELLOW_Packet.effect.size": "OWL-13.yellow_size",
          "attacks.YELLOW_Packet.effect.speed_by_phase.wings": "OWL-13.yellow_speed_wings",
          "attacks.YELLOW_Packet.effect.speed_by_phase.mechanisms": "OWL-13.yellow_speed_mechanisms",
          "attacks.YELLOW_Packet.effect.speed_by_phase.clock": "OWL-13.yellow_speed_clock",
          "attacks.GUST_Band.telegraph.sec": "OWL-15.gust_warning_s",
          "attacks.GUST_Band.cadence_sec": "OWL-15.physical_interval_s",
          "attacks.GUST_Band.effect.damage": "FLOW-33.projectile_damage",
          "attacks.GUST_Band.effect.push": "OWL-16.gust_push",
          "attacks.GUST_Band.effect.speed": "OWL-16.gust_speed",
          "attacks.GUST_Band.effect.band_width": "OWL-16.gust_band_width",
          "attacks.GUST_Band.effect.lifetime_sec": "OWL-16.gust_lifetime_s",
          "attacks.TALON_Rake.telegraph.sec": "OWL-18.talon_warning_s",
          "attacks.TALON_Rake.trigger.radius": "OWL-18.talon_reach",
          "attacks.TALON_Rake.trigger.rearm_exit": "OWL-20.talon_rearm_exit",
          "attacks.TALON_Rake.effect.damage": "FLOW-33.talon_damage",
          "attacks.TALON_Rake.effect.tip_width": "OWL-19.talon_tip_width",
          "attacks.TALON_Rake.effect.strike_sec": "OWL-19.talon_strike_s",
          "attacks.TALON_Rake.effect.recovery_sec": "OWL-20.talon_recovery_s",
          "attacks.TALON_Rake.effect.cooldown_sec": "OWL-20.talon_cooldown_s",
          "attacks.MECH_Front_Cast.telegraph.sec": "OWL-21.cast_warning_s",
          "attacks.MECH_Front_Cast.cadence_sec": "OWL-15.physical_interval_s",
          "attacks.MECH_Front_Cast.effect.damage": "FLOW-33.chain_damage",
          "attacks.MECH_Front_Cast.effect.reach": "OWL-22.chain_reach",
          "attacks.MECH_Front_Cast.effect.speed": "OWL-22.chain_speed",
          "attacks.MECH_Front_Cast.effect.head_width": "OWL-22.chain_head_width",
          "attacks.MECH_Front_Cast.effect.return_sec": "OWL-23.chain_return_s",
          "attacks.MECH_Middle_Curve.telegraph.sec": "OWL-21.cast_warning_s",
          "attacks.MECH_Middle_Curve.cadence_sec": "OWL-15.physical_interval_s",
          "attacks.MECH_Middle_Curve.effect.damage": "FLOW-33.chain_damage",
          "attacks.MECH_Middle_Curve.effect.reach": "OWL-22.chain_reach",
          "attacks.MECH_Middle_Curve.effect.speed": "OWL-22.chain_speed",
          "attacks.MECH_Middle_Curve.effect.head_width": "OWL-22.chain_head_width",
          "attacks.MECH_Middle_Curve.effect.return_sec": "OWL-23.chain_return_s",
          "attacks.MECH_Rear_TwoStage.telegraph.sec": "OWL-21.cast_warning_s",
          "attacks.MECH_Rear_TwoStage.cadence_sec": "OWL-15.physical_interval_s",
          "attacks.MECH_Rear_TwoStage.effect.damage": "FLOW-33.chain_damage",
          "attacks.MECH_Rear_TwoStage.effect.reach": "OWL-22.chain_reach",
          "attacks.MECH_Rear_TwoStage.effect.speed": "OWL-22.chain_speed",
          "attacks.MECH_Rear_TwoStage.effect.head_width": "OWL-22.chain_head_width",
          "attacks.MECH_Rear_TwoStage.effect.return_sec": "OWL-23.chain_return_s",
          "attacks.MECH_Middle_Curve.effect.offset": "OWL-24.middle_offset",
          "attacks.MECH_Rear_TwoStage.effect.pause_sec": "OWL-26.rear_pause_s"
        },
        "fight_length_sec": {
          "min": 60,
          "max": 240
        },
        "player": {
          "verbs": [
            "move",
            "rise",
            "fall",
            "shoot",
            "absorb",
            "dash"
          ],
          "shot_damage": 10,
          "shot_cadence": 0.2,
          "shot_note": "Small Blasts, 5 shots/s (COM-06), the Start Game basic shot; Director's Cut spells change the DPS",
          "shooting_falls": true,
          "absorbing_falls": true,
          "damage_reduces": [
            "active_health",
            "lift"
          ]
        },
        "entry": {
          "full_run": "wings"
        },
        "targets": [
          {
            "id": "WINGS",
            "hp": 180,
            "regions": [
              "WING_NEAR",
              "WING_FAR"
            ],
            "shared_hp": true,
            "hitbox": "keeper-wing",
            "vulnerable_in": [
              "wings"
            ],
            "hit_share": 0.15,
            "on_break": {
              "cancels": [
                "GUST_Band"
              ],
              "visual": "depleted wings stay visible as cover, smoke stays, no wing damage region returns (OWL-09, OWL-17)",
              "stun_sec": 0,
              "new_attacks": false,
              "in_flight": "cleared"
            }
          },
          {
            "id": "MECH_FRONT",
            "hp": 100,
            "order": 1,
            "hitbox": "keeper-mech-front",
            "vulnerable_in": [
              "mechanisms"
            ],
            "vulnerable_when": "after the wings; front first (OWL-09)",
            "hit_share": 0.15,
            "on_break": {
              "cancels": [
                "MECH_Front_Cast"
              ],
              "stun_sec": 1.2,
              "exposes": "CLOCK",
              "new_attacks": false,
              "in_flight": "dangerous"
            }
          },
          {
            "id": "MECH_MIDDLE",
            "hp": 110,
            "order": 2,
            "hitbox": "keeper-mech-middle",
            "vulnerable_in": [
              "mechanisms"
            ],
            "vulnerable_when": "after the front",
            "hit_share": 0.15,
            "on_break": {
              "cancels": [
                "MECH_Middle_Curve"
              ],
              "stun_sec": 1.2,
              "exposes": "CLOCK",
              "new_attacks": false,
              "in_flight": "dangerous"
            }
          },
          {
            "id": "MECH_REAR",
            "hp": 120,
            "order": 3,
            "hitbox": "keeper-mech-rear",
            "vulnerable_in": [
              "mechanisms"
            ],
            "vulnerable_when": "after the middle",
            "hit_share": 0.15,
            "on_break": {
              "cancels": [
                "MECH_Rear_TwoStage"
              ],
              "stun_sec": 1.2,
              "exposes": "CLOCK",
              "new_attacks": false,
              "in_flight": "dangerous"
            }
          },
          {
            "id": "CLOCK",
            "hp": 320,
            "floor_pct_before_final": 40,
            "carry_damage": true,
            "hitbox": "keeper-clock",
            "vulnerable_in": [
              "mechanisms",
              "clock"
            ],
            "vulnerable_when": "open: 1.8 s after an outer hit or a mechanism break, 1.9 s every 4.8 s in the finale (OWL-29)",
            "hit_share": 0.1,
            "on_hit": {
              "slow": "3 s at x0.35 world speed, 3 s cooldown, on a hit that lowers HP (OWL-31)",
              "eye": "2 s eye window; an eye hit starts the 3 s blackout and the 5 s eye cooldown; the eye has no HP (OWL-32)"
            }
          }
        ],
        "attacks": [
          {
            "id": "RED_Fan",
            "feature": "OWL-11",
            "phases": [
              "wings",
              "mechanisms"
            ],
            "first_at": 2.0,
            "cadence_by_phase": {
              "wings": 1.35,
              "mechanisms": 1.35
            },
            "telegraph": {
              "sec": 0,
              "shows": "the launch / aim posture and the captured lane; no timed prefire delay (OWL-12)",
              "pose": "Keeper_Red_Launch",
              "vfx": "VFX_RedLaunch",
              "sound": "KeeperRedLaunch",
              "no_prefire": "OWL-12"
            },
            "effect": {
              "damage": 1,
              "shots": 4,
              "spacing_sec": 0.09,
              "speed_by_phase": {
                "wings": 240,
                "mechanisms": 270
              },
              "spread_by_phase": {
                "wings": 36,
                "mechanisms": 70
              },
              "aim": {
                "wings": "captured position",
                "mechanisms": "fixed-left wide fan"
              },
              "reduced": "one shot, every 2.16 s while a physical attack warns or strikes (OWL-11)",
              "absorbable": false
            },
            "counterplay": [
              {
                "verb": "move_off_line",
                "how": "leave the captured lane by rising, falling, riding a current or a falling dash"
              }
            ],
            "not_counterplay": [
              {
                "verb": "absorb",
                "why": "red is never absorbable"
              }
            ],
            "art": [
              "keeper",
              "red-shot",
              "shot-impact"
            ],
            "sound": [
              "KeeperRedLaunch",
              "RedShotTravel",
              "PlayerHurt"
            ]
          },
          {
            "id": "CLOCK_DoubleBeat",
            "feature": "OWL-28",
            "phases": [
              "clock"
            ],
            "first_at": 2.0,
            "cadence_sec": 1.99,
            "telegraph": {
              "sec": 0,
              "shows": "the clock hand beat XII to III and the first group's captured paths (OWL-28)",
              "pose": "Keeper_Clock_Beat",
              "vfx": "VFX_ClockBeat_Red",
              "sound": "ClockBeat",
              "no_prefire": "OWL-12"
            },
            "effect": {
              "damage": 1,
              "shots": 4,
              "spacing_sec": 0.09,
              "speed": 300,
              "spread": 48,
              "repeat_wait_sec": 0.6,
              "recovery_sec": 0.85,
              "repeat": "the same captured paths once, never re-aimed",
              "absorbable": false
            },
            "counterplay": [
              {
                "verb": "leave_first_pattern",
                "how": "leave the first group's paths"
              },
              {
                "verb": "dont_drift_back",
                "how": "the repeat flies the same paths"
              }
            ],
            "art": [
              "keeper",
              "red-shot",
              "clock-beat"
            ],
            "sound": [
              "ClockBeat",
              "ClockBeatRepeat",
              "KeeperRedLaunch",
              "PlayerHurt"
            ]
          },
          {
            "id": "YELLOW_Packet",
            "feature": "OWL-13",
            "phases": [
              "wings",
              "mechanisms",
              "clock"
            ],
            "first_at": 3.0,
            "cadence_sec": 2.3,
            "telegraph": {
              "sec": 0,
              "shows": "two slower aimed packets with their own rhythm, trail and sound (OWL-14)",
              "pose": "Keeper_Yellow_Launch",
              "vfx": "VFX_YellowLaunch",
              "sound": "KeeperYellowLaunch",
              "no_prefire": "OWL-12"
            },
            "effect": {
              "damage": 1,
              "shots": 2,
              "size": 1.2,
              "speed_by_phase": {
                "wings": 180,
                "mechanisms": 195,
                "clock": 210
              },
              "absorbable": true,
              "on_catch": "absorbing while dropping heals 0.5 + 0.3 per recovery rank, active life first; no XP, no ammunition, no stored energy (UMB-05)"
            },
            "counterplay": [
              {
                "verb": "absorb",
                "how": "hold Absorb while dropping and face it to heal"
              },
              {
                "verb": "dodge",
                "how": "or leave its path"
              }
            ],
            "art": [
              "yellow-shot",
              "yellow-capture"
            ],
            "sound": [
              "KeeperYellowLaunch",
              "YellowCatch",
              "UmbrellaRepair"
            ]
          },
          {
            "id": "GUST_Band",
            "feature": "OWL-16",
            "phases": [
              "wings"
            ],
            "cancelled_by": "WINGS",
            "first_at": 3.0,
            "cadence_sec": 6.5,
            "telegraph": {
              "sec": 1.1,
              "shows": "the wing gather / load and the locked altitude band (OWL-15)",
              "pose": "Keeper_Gust_Gather",
              "vfx": "VFX_GustBand_Warn",
              "sound": "GustWarning"
            },
            "effect": {
              "damage": 1,
              "push": 280,
              "speed": 350,
              "band_width": 120,
              "lifetime_sec": 3,
              "bypasses": "ordinary post-hit and hop protection; dash protection stops the damage, never the push (OWL-16)"
            },
            "counterplay": [
              {
                "verb": "leave_band",
                "how": "leave the warned band; account for the push near the ceiling and the bottom"
              }
            ],
            "not_counterplay": [
              {
                "verb": "absorb",
                "why": "a hostile gust is never absorbed or ridden"
              }
            ],
            "art": [
              "keeper",
              "hostile-gust"
            ],
            "sound": [
              "GustWarning",
              "GustRelease",
              "GustTravelLoop",
              "PlayerHurt"
            ]
          },
          {
            "id": "TALON_Rake",
            "feature": "OWL-19",
            "phases": [
              "wings",
              "mechanisms",
              "clock"
            ],
            "first_at": 2.0,
            "trigger": {
              "kind": "proximity",
              "radius": 270,
              "rearm_exit": 370,
              "rearm": "leave beyond 370, then come back within 270 (OWL-20)"
            },
            "telegraph": {
              "sec": 1.05,
              "shows": "the EMPTY claw drawn back and spread (OWL-18)",
              "pose": "Keeper_Talon_Warn",
              "vfx": "VFX_Talon_Warn",
              "sound": "TalonWarning"
            },
            "effect": {
              "damage": 1.5,
              "tip_width": 48,
              "strike_sec": 0.18,
              "recovery_sec": 1,
              "cooldown_sec": 3.5,
              "strike": "one sweep toward the captured target, at most once per cast"
            },
            "counterplay": [
              {
                "verb": "bait_then_leave",
                "how": "bait the warning, then leave"
              },
              {
                "verb": "change_altitude",
                "how": "or change altitude"
              }
            ],
            "art": [
              "keeper",
              "talon"
            ],
            "sound": [
              "TalonWarning",
              "TalonSlash",
              "TalonRecovery",
              "PlayerHurt"
            ]
          },
          {
            "id": "MECH_Front_Cast",
            "feature": "OWL-22",
            "phases": [
              "mechanisms"
            ],
            "active_while": "MECH_FRONT",
            "cancelled_by": "MECH_FRONT",
            "first_at": 2.5,
            "cadence_sec": 6.5,
            "telegraph": {
              "sec": 0.9,
              "shows": "the closed claw gripping the armillary ring and the locked destination (OWL-21)",
              "pose": "Keeper_Front_Grasp",
              "vfx": "VFX_Cast_Warn",
              "sound": "CastWarning"
            },
            "effect": {
              "damage": 1.25,
              "reach": 800,
              "speed": 400,
              "head_width": 32,
              "return_sec": 1.2,
              "path": "straight to the captured endpoint",
              "hurts": [
                "head_outward"
              ],
              "harmless": [
                "links",
                "return"
              ]
            },
            "counterplay": [
              {
                "verb": "move_off_line",
                "how": "leave the captured lane by rising, falling, riding a current or a falling dash"
              }
            ],
            "art": [
              "mechanism-head",
              "mechanism-chain",
              "talon"
            ],
            "sound": [
              "CastWarning",
              "FrontCastLaunch",
              "ChainTravel",
              "CastReturn",
              "PlayerHurt"
            ]
          },
          {
            "id": "MECH_Middle_Curve",
            "feature": "OWL-25",
            "phases": [
              "mechanisms"
            ],
            "active_while": "MECH_MIDDLE",
            "cancelled_by": "MECH_MIDDLE",
            "first_at": 2.5,
            "cadence_sec": 6.5,
            "telegraph": {
              "sec": 0.9,
              "shows": "the curved stroke it will follow, sign by the global physical-attack serial (OWL-24)",
              "pose": "Keeper_Middle_Cradle",
              "vfx": "VFX_Cast_Warn",
              "sound": "CastWarning"
            },
            "effect": {
              "damage": 1.25,
              "reach": 800,
              "speed": 400,
              "head_width": 32,
              "return_sec": 1.2,
              "path": "a +/-80 sine curve to the same endpoint",
              "hurts": [
                "head_outward"
              ],
              "harmless": [
                "links",
                "return"
              ],
              "offset": 80
            },
            "counterplay": [
              {
                "verb": "move_off_line",
                "how": "leave the captured lane by rising, falling, riding a current or a falling dash"
              },
              {
                "verb": "clear_curve",
                "how": "clear the whole curve, not the straight line"
              }
            ],
            "art": [
              "mechanism-head",
              "mechanism-chain",
              "talon"
            ],
            "sound": [
              "CastWarning",
              "MiddleCastLaunch",
              "ChainTravel",
              "CastReturn",
              "PlayerHurt"
            ]
          },
          {
            "id": "MECH_Rear_TwoStage",
            "feature": "OWL-26",
            "phases": [
              "mechanisms"
            ],
            "active_while": "MECH_REAR",
            "cancelled_by": "MECH_REAR",
            "first_at": 2.5,
            "cadence_sec": 6.5,
            "telegraph": {
              "sec": 0.9,
              "shows": "the line to the original endpoint; the second clack says it is not finished (OWL-27)",
              "pose": "Keeper_Rear_Prepare",
              "vfx": "VFX_Cast_Warn",
              "sound": "CastWarning"
            },
            "effect": {
              "damage": 1.25,
              "reach": 800,
              "speed": 400,
              "head_width": 32,
              "return_sec": 1.2,
              "path": "half the stroke, a safe 0.65 s pause, then on to the original endpoint",
              "hurts": [
                "head_outward"
              ],
              "harmless": [
                "links",
                "return"
              ],
              "pause_sec": 0.65
            },
            "counterplay": [
              {
                "verb": "move_off_line",
                "how": "leave the captured lane by rising, falling, riding a current or a falling dash"
              },
              {
                "verb": "stay_clear_after_pause",
                "how": "it is not finished at the pause"
              }
            ],
            "art": [
              "mechanism-head",
              "mechanism-chain",
              "talon"
            ],
            "sound": [
              "CastWarning",
              "RearCastLaunch",
              "RearMidpointClack",
              "ChainTravel",
              "CastReturn",
              "PlayerHurt"
            ]
          }
        ],
        "phases": [
          {
            "id": "wings",
            "targets": [
              "WINGS"
            ],
            "attacks": [
              "RED_Fan",
              "YELLOW_Packet",
              "GUST_Band",
              "TALON_Rake"
            ],
            "ends_when": {
              "broken": [
                "WINGS"
              ]
            },
            "next": "mechanisms",
            "checkpoint": true,
            "transition_in": {
              "sec": 2.0,
              "new_attacks": false,
              "in_flight": "none"
            },
            "story_beat": "arrival: the single remaining clock hand and the empty mounting are visible (NAR-06)"
          },
          {
            "id": "mechanisms",
            "targets": [
              "MECH_FRONT",
              "MECH_MIDDLE",
              "MECH_REAR",
              "CLOCK"
            ],
            "attacks": [
              "MECH_Front_Cast",
              "MECH_Middle_Curve",
              "MECH_Rear_TwoStage",
              "RED_Fan",
              "YELLOW_Packet",
              "TALON_Rake"
            ],
            "ends_when": {
              "broken": [
                "MECH_FRONT",
                "MECH_MIDDLE",
                "MECH_REAR"
              ]
            },
            "next": "clock",
            "checkpoint": true,
            "sequence": [
              "MECH_FRONT",
              "MECH_MIDDLE",
              "MECH_REAR"
            ],
            "transition_in": {
              "sec": 2.0,
              "new_attacks": false,
              "in_flight": "dangerous"
            }
          },
          {
            "id": "clock",
            "targets": [
              "CLOCK"
            ],
            "attacks": [
              "CLOCK_DoubleBeat",
              "YELLOW_Packet",
              "TALON_Rake"
            ],
            "ends_when": {
              "hp_zero": "CLOCK"
            },
            "next": null,
            "ends_fight": true,
            "checkpoint": true,
            "transition_in": {
              "sec": 2.0,
              "new_attacks": false,
              "in_flight": "dangerous"
            }
          }
        ],
        "end": {
          "stop_threats": true,
          "story_beat": "final clock completion stops combat damage once; the Keeper withdraws alive in about 2.5 s (OWL-35, NAR-07)"
        },
        "open_items": [
          "same-frame fatal hit vs final clock hit precedence (OWL-35, OPEN)",
          "exact spawn, camera and collision proportions (section 5, OPEN; D-new-sh10-units default)",
          "the state-driven fairness sim of overlapping red fans, casts and the talon is not built (encounter_check E1-E27 model the GDD 1.3 timer arena)"
        ]
      }
    },
    "select": {
      "workbench_cvar": "UmbrellaElla.Encounter.Preset",
      "env": "JAM_ENCOUNTER_PRESET",
      "list": "python3 tools/encounter_check.py --presets --gdd 1.3"
    }
  }
}
```

## Checklists

### `pipeline/checklists/level-sections.md`

#### Arena and owl encounter acceptance (THE LAST HOUR)

> GDD SH1.0 note (D-new-gdd-sh10): lines on this page that still describe the GDD 1.3 encounter (one owl bolt, the front shield, the 90 s survival timer, wear stages, the 1.3 QA-01..QA-28 tests) are history. The current design is `docs/gdd/GDD-SH1.0.md` and `docs/feature-manifest.json`, which win; the owning role re-files this page against the SH1.0 Rule IDs on its next card.


One fixed-camera arena, one owl, one bolt over 90 s (optional phase presets), then the end event.
This list makes every arena, pattern and phase card's Done-when checkable.
Design source: GDD 1.3 (§7 owl and wind, §7B first encounter, §8 phases as optional presets, §6 health); numbers from the
manifest `approved_parameters` (E29). Lines marked [2+ patterns] or [SURV-04] apply only once those are on. The old five-section
platformer docs do not apply here. Numbers live in `pipeline/level/encounter.json`; tables in `pipeline/level/encounter.md`.

Owner of every line below is the Level Designer, unless the line names another role.
`[VERIFY]` = needs Unreal; there is no engine here, so the test name and rule are fixed but the code is not written.

##### Who builds the engine half
The data gate (section 0) runs on a JSON mirror. These two cards prove the shipped owl matches it.
Rule: no encounter card moves to `doing` until `python3 tools/encounter_check.py --wiring` prints
`wiring_check: 0 problem(s)`. Owner: Producer. It fails (W1-W5) while any of these is missing: both card rows below
in `pipeline/day0-cards.md`, the 5 test names in `pipeline/qa/test-map.md`, the section 6 log columns in
`pipeline/qa/playtests.md`, the Level Designer row in the AGENTS.md roles table, and `encounter_check.py` as the
Game Designer's review criteria. It fails until those files' owners add the rows.

| Card | Owner | Reviewer | Done when |
|---|---|---|---|
| Owl data types + 5 Owl tests | Gameplay Dev | Dev Lead | `UOwlPatternData` and `UOwlPhaseData` exist with the fields in `encounter.md`. `tools/ue/test.sh --require` with the 5 `UmbrellaElla.Owl.*` names below prints PASS (pasted). Each test's row is in `pipeline/qa/test-map.md`. |
| Owl dump + eval cameras (after the card above) | Integrator | Dev Lead | An editor script writes every `DA_OwlPattern_*` and `DA_Phase_*` as JSON in the `encounter.json` shape. `python3 tools/encounter_check.py --data <dump>` prints `0 problem(s)` (pasted). `CAM_Eval_Arena` and `CAM_Eval_Stress` are in the arena map and `-EvalCam=<name>` captures each. |

The 5 tests: `UmbrellaElla.Owl.EveryPatternHasTelegraph`, `UmbrellaElla.Owl.PhaseTableDistinct`,
`UmbrellaElla.Owl.World.OriginLockedDuringTelegraph`, `UmbrellaElla.Owl.World.PhaseChangePlaysCue`,
`UmbrellaElla.Owl.World.NoDamageAfterEndTrigger` (sections 1, 2, 4 say what each asserts).
`UmbrellaElla.Owl.World.SafePathAtDriftExtremes` (section 3) is a sixth, built by the same card if time allows; it is
listed `planned` until then. Until both cards merge, an encounter card lists the tests and the dump under
"Not run" with the card number. G4 does not pass while a test-map Owl row is `planned` (QA and Build).

##### 0. The data gate (every card that touches the encounter)
- [ ] `python3 tools/encounter_check.py` prints `encounter_check: 0 problem(s)`. Paste its full output on the card
      (it prints the tuning it read, breathers and intensity; with presets, the midpoint and the desperation share).
- [ ] `pipeline/level/encounter.md` was regenerated with `--write-md` in the same PR (E18 fails a stale block).
- [ ] The engine assets match the JSON: the editor dump passes `encounter_check.py --data <dump>` [VERIFY].
- [ ] Hero speeds, hurtbox and bolt hitbox ratio come from the Game Designer's `pipeline/feel/feel.json`
      (`arena.tuning_source`). A copy of them in `encounter.json` fails (E22). The sim uses the worst case:
      sideways speed, UP_OPEN rise at the lowest lift tier (1.0 unless SURV-04), max fall.
- [ ] GDD 1.3 numbers (E29): every pattern names an enabled manifest `feature`; the OWL-01 bolt's warning, speed and
      cadence and `duration_sec` sit inside their GDD SH1.0 rule numbers (section 9 ranges blank, D-new-sh10-param-ranges) ranges (the starts are provisional tuning); grace and
      `seed` have no range and equal the approved values.

##### 1. Every pattern (one `DA_OwlPattern_<ID>` row each)
- [ ] Three stages: TelegraphSec ≥ 0.4 s (proposed), ActiveSec > 0, RecoverySec ≥ 0 (E1, E2).
      Nothing can deal damage before TelegraphSec ends.
- [ ] A visual tell on every pattern: pose or VFX. Sound is never the only cue (GDD SH1.0 MOVE-04) (E1).
- [ ] Bolts and the arc have a layered tell: pose and sound and VFX, all three set (E1).
      Bolts: amber clock flash plus wind-up pose. Arc: red trail. Gust: wing pose plus flow lines.
- [ ] Colour code: amber only on bolt tells, red only on the arc (E9).
- [ ] Art Director verdict on a `CAM_Eval_Arena` capture with no attack running, written on the card as:
      `Accent check: no amber or red outside bolts, tells and the arc. <name> <YYYY-MM-DD>`. Judged against
      `pipeline/art/reference/target-keyart.png`. The signed verdict is the rule; `--card` fails without it (C3).
- [ ] The fire origin is fixed from the start of the telegraph to the last bolt. Owl drift pauses for it (E12).
- [ ] Spreads: no lone bolt outside the group, staggered spawns, seed angle changes each volley,
      aimed spreads have an even count or a written `odd_count_reason` (E11).
- [ ] Projectiles draw on top and use a directional sprite with a bright core (E10).
- [ ] Engine test `UmbrellaElla.Owl.EveryPatternHasTelegraph`: loads every pattern asset; fails if
      TelegraphSec < 0.4, a bolt or arc has an empty TellPose, TellSound or TellVFX, or a pattern with
      InterruptibleSec > 0 has InterruptReplaysTelegraph false [VERIFY].
- [ ] Engine test `UmbrellaElla.Owl.World.OriginLockedDuringTelegraph`: start a pattern, move the drift
      target, assert the fire origin did not move until RecoverySec starts [VERIFY].

##### 2. Every phase (`DA_Phase_Base`, or the presets `DA_Phase_Intro`, `DA_Phase_Contest`, `DA_Phase_Desperation`)
- [ ] One `base` phase 0-100%, or intro, contest, desperation back to back. Desperation ≤ 30% of the timer (E3).
- [ ] [2+ patterns] Each phase adds or swaps a pattern or space rule. Speed alone does not count (E4).
      Desperation's space rule is the torn umbrella altitude cap (`altitude_cap_y`).
- [ ] With 2+ phases, every phase change plays the one `phase_change_cue` (the clock chime). No per-phase cue (E5).
- [ ] Intro teaches before it tests: single bolts only, one gust at most, [2+ patterns] one attack at a time (E6).
- [ ] [2+ patterns] A pattern's first use never overlaps another attack (E7).
- [ ] [2+ patterns] Each phase has a breather ≥ 3.0 s (proposed) with no attack in telegraph, active or flight (E8).
- [ ] [2+ patterns] Intensity (E19, proposed numbers): no phase has an attack running more than 60% of its time.
      Density (attack-seconds per second) rises from intro to contest, and desperation is at most 1.3x contest.
      Two peaks (clusters of 2+ attacks) always have a 3.0 s breather between them.
- [ ] No camping (E20): after intro (in the one base phase), a still hero on every point of a 5x5 grid over the hero zone (corners,
      mid-edges, centre; under the altitude cap) is hit by a bolt or the arc in that phase, at both ends of the owl's drift.
- [ ] [2+ patterns] Layering (E21): contest has at least one cluster with an aimed bolt pattern (forces a move) and a
      non-aimed one (blocks a route) together.
- [ ] [2+ patterns] Midpoint turn (E24): a pattern makes its first appearance in the second half of contest
      (from about 47% of the timer). It gives the long middle phase a second beat.
- [ ] [2+ phases] Engine test `UmbrellaElla.Owl.PhaseTableDistinct`: loads the three phase assets; fails if a phase
      has the same pattern set and space rules as the one before [VERIFY].
- [ ] [2+ phases] Engine test `UmbrellaElla.Owl.World.PhaseChangePlaysCue`: run the timer through both changes,
      assert the chime fired exactly twice with the same sound asset [VERIFY].

##### 3. The arena
- [ ] The owl stays in the right half. Hero zone and owl zone do not overlap (E17).
- [ ] Safe path (E13): the hero starts at each aim point (high, middle, low) with the owl at both drift ends,
      moves at the tuning speeds, and has a hero-sized safe path through every cluster. 2D, on the data.
      The arc is simulated as an out-and-back loop from its row: `reach`, `side`, `flight_sec`, `core_radius`
      (E2 fails a missing field). The engine test below checks the real curve.
- [ ] [SURV-04] Recovery with the torn umbrella (E25): at the lowest lift tier, the climb from the lowest hero spot to the
      highest one under desperation's cap (plus half the open rise ramp) fits in desperation's longest breather.
      The checker prints both numbers. Fix by lowering the cap or widening a breather, never by a speed copy.
- [ ] Engine test `UmbrellaElla.Owl.World.SafePathAtDriftExtremes`: same rule on the real projectiles,
      the real hero collision and the arc [VERIFY].
- [ ] Owl hit reactions (COM-02, COM-03: off in GDD 1.3, so 0 and `[1.0]`; E29). Clock hit (E26): every pattern has `interruptible_sec` (0 = not
      disrupted, at most 1.0 s, proposed). If it is above 0, `interrupt_replays_telegraph` is true: the attack pauses
      and, if its telegraph was showing, the full telegraph plays again. An interrupt never shortens a telegraph.
      [2+ patterns] Every phase still has a 3.0 s breather with every interruptible attack late by its pause plus a telegraph.
      Wing hit (E27): the gust has `gust_strength_by_wing_tier` (1.0 first, never rising, in (0, 1]) and one
      `wing_tear_overlays` texture per damaged tier, so the weaker gust is visible. Cut = `[1.0]` and 0 everywhere.
- [ ] Hitboxes: hero hurtbox ≤ 50% of the body sprite area (E22, from `feel.json`). Owl hitbox ≥ 80% of
      the owl sprite area, so auto-fire lands on what the player sees (E23). Live sizes:
      `UmbrellaElla.Feel.Hitboxes` (Feel lane) [VERIFY].
- [ ] Every gust zone sits inside the hero zone and leaves a hero-sized lane above or below (E15).
- [ ] Coverage (E14): by the end of contest every row has a pattern: high, low, far, rise, fall, horizontal,
      gust. A bolt or arc that claims a position must reach that third. Card line:
      `Coverage signed: <name> <YYYY-MM-DD>`, by the Game Designer reviewer. `--card` fails without it (C2).
- [ ] Two fixed eval cameras, placed by the Integrator: `CAM_Eval_Arena` (full arena, no attack) and
      `CAM_Eval_Stress` (the desperation cluster with the most patterns at once).
- [ ] Nothing moves against the bolts. Art Director verdict on two `CAM_Eval_Stress` frames 0.1 s apart, written as:
      `Motion check: nothing but projectiles moves within 64 px of a projectile. <name> <YYYY-MM-DD>`.
      The signed verdict is the rule; `--card` fails without it (C3).
- [ ] The card lists any decor in `CAM_Eval_Stress` that looks like a hazard or a ledge but is not.

##### 4. The end event
- [ ] `end_event` stops threats, the owl departs, the Survived card shows, quiet ≥ 5 s (E16, GDD SH1.0 OWL-06, OWL-35).
      A story clue is optional: narrative is DEFERRED (NAR-01).
- [ ] Engine test `UmbrellaElla.Owl.World.NoDamageAfterEndTrigger`: fire the end trigger with bolts in
      flight, tick 5 s, assert 0 damage events and the Survived card is shown [VERIFY].

##### 5. Before the first encounter card
- [ ] P0: one person from outside the team walks the phase table from `encounter.md` on paper: for each
      phase, what they think the owl will do and where they would stand. The card has a line
      `Paper walk: <link or #n to the tracker comment with their answers>` and lists what changed, or `no change`.
      Later encounter cards repeat the same line. `--card` fails without it (C4).

##### 5b. The card itself
- [ ] `python3 tools/encounter_check.py --card <card.md>` prints `card_check: 0 problem(s)`, pasted by the
      reviewer. It checks the pasted data gate (C1), the coverage, art and paper-walk lines (C2-C4), and that each
      of the 5 Owl tests is on a `PASS` line or a `Not run` line with the building card's number (C5).
      `pipeline/level/fixtures/card_ok.md` is a passing example.

##### 6. Reading the playtest
- [ ] After every hit, the observer asks "What hit you, and what warned you?"
- [ ] Log columns: `session,event,phase,pattern_id,explained,t_run_s,build`. `event` is `hit`, `death` or `survive`.
      Every hit and death row has a `pattern_id` from `encounter.json` (or `BOTTOM_EXIT`) and `explained` = y/n.
- [ ] `python3 tools/encounter_check.py --playtest <log.csv ...>` prints `playtest_check: 0 problem(s)`
      (rules L1-L6; a header-only log fails) and a per-pattern table of hits, deaths and `explained=n`. Paste it on the playtest record.
      Owner: QA and Build. The `Columns:` line in `pipeline/qa/playtests.md` and the logger card must match these
      columns (`--wiring`, W3). `pipeline/level/fixtures/logger_output.csv` is the logger's expected output;
      a unit test runs `--playtest` on it.
- [ ] A hit the player cannot explain (`explained=n`) is a bug against that pattern ID (tell too weak, too short,
      or hidden). Fix the tell, not the numbers. Only explained hits count toward difficulty tuning.

## Encounter references

### `pipeline/level/reference/owl-fight-ricky.md`

#### Reference: Ricky's owl fight (proposed encounter preset OWL-FIGHT-RICKY)

> GDD SH1.0 note (D-new-gdd-sh10): lines on this page that still describe the GDD 1.3 encounter (one owl bolt, the front shield, the 90 s survival timer, wear stages, the 1.3 QA-01..QA-28 tests) are history. The current design is `docs/gdd/GDD-SH1.0.md` and `docs/feature-manifest.json`, which win; the owning role re-files this page against the SH1.0 Rule IDs on its next card.


Source: Ricky in the team Discord, #owl-fight-mechanics, 10 Nov 2026 19:28 PST. He describes the rebuilt fight as it
plays now (build WIN015), reviewed by an encounter specialist without starting the game. The team's goal from the
meeting notes: bring the pipeline build closer to the demonstrated fight.

This file is the reference the encounter critic judges against (`python3 tools/encounter_check.py --critic-packet
OWL-FIGHT-RICKY/<phase>`). It is not the GDD. GDD 1.3 stays the baseline and the default preset. Whether this fight
replaces it is decision row `D-new-encounter-ricky` (owner Richard). The data is preset `OWL-FIGHT-RICKY` in
`pipeline/level/encounter.json`; numbers it lists under `numbers_from_reference` come from this description, every
other number there is a pipeline proposal.

##### The goal
- Ella fights through the Keeper's wings, three hanging mechanisms, then the clock.
- Shooting, absorbing and regaining altitude compete: shooting and absorbing make Ella fall.
- Damage reduces both umbrella health and upward lift.

##### Phase 1: wings
- Two reachable wing regions share 180 HP. Breaking them stops the damaging wind gusts. The damaged wings stay attached.
- Gust: warns an altitude band, then pushes left and deals damage. Counter: move out of the warned band.
- Absorbing does not cancel the gust. A protected dash avoids the damage but not the push.

##### Phase 2: hanging mechanisms
- After the wings, the mechanisms become targets in order: front 100 HP, middle 110 HP, rear 120 HP.
- Each can be shot while its head moves. Breaking one cancels its attack and makes the next one available.
- Front: warns, then throws straight at where Ella was targeted. Counter: move off the line.
- Middle: follows a high or a low curve. Counter: clear the whole curve, not only the straight path.
- Rear: moves halfway, pauses (safe), then continues to its original target. Counter: it is not done when it pauses.
- Only the outward-moving head hurts. The chain and the return are harmless.

##### Phase 3: the clock
- After wings and mechanisms, shoot the clock during its openings. 320 max HP.
- Outer-part hits can expose it earlier, so it can be chipped, but it keeps at least 40% for the final phase.
  Earlier damage carries forward.
- The final clock opens on its own cycle. Its double beat fires a red group, then repeats the same paths without
  re-aiming. Counter: move away from the first pattern and do not drift back into it.
- The clock at zero completes the fight. Story: the Keeper leaves alive.

##### Throughout the fight
- Red shots: four-shot volleys, faster as the fight goes on. They hurt and cannot normally be absorbed.
- Yellow shots: two-shot packets. Contact hurts, but catching them on purpose repairs the umbrella and charges Stored
  Thunder, also after the catch-XP limit.
- Talon rake: when Ella gets close the claw warns and commits to a quick strike. Counter: bait it, then move away or
  change altitude. It re-arms only after Ella leaves the area and comes back.
- Breaking a mechanism briefly stuns the Keeper and exposes the clock. New attacks stop; shots already flying still hurt.
- A clock hit can briefly slow the world. An optional eye can appear: hitting it blacks out and clears old threats,
  but does not extend the clock's vulnerability.

##### Testing notes from the same post
- A normal full run starts with the wings. The saved Boss Practice setup starts at phase 3 and skips wings and
  mechanisms, and practice uses different movement and protection settings, so it can feel different.
- Several attack visuals (the finished talon and grasp/throw animations) are still placeholders.
- Automated behaviour does not show that the fight is fair or fun: a human playtest decides that.

## Check fixtures

### `pipeline/level/fixtures/card_ok.md`

Fixture: an encounter card that passes `encounter_check.py --card`. Names and dates are made up for the test.

##### Evidence
```
breather contest: 6.5 s
encounter_check: 0 problem(s)
```
Coverage signed: Sam Lee 2026-11-20
Accent check: no amber or red outside bolts, tells and the arc. Ana Ruiz 2026-11-20
Motion check: nothing but projectiles moves within 64 px of a projectile. Ana Ruiz 2026-11-20
Paper walk: #41 (no change)

##### Engine tests
- `UmbrellaElla.Owl.EveryPatternHasTelegraph` PASS
- `UmbrellaElla.Owl.PhaseTableDistinct` PASS
- Not run: `UmbrellaElla.Owl.World.OriginLockedDuringTelegraph` (#20)
- Not run: `UmbrellaElla.Owl.World.PhaseChangePlaysCue` (#20)
- Not run: `UmbrellaElla.Owl.World.NoDamageAfterEndTrigger` (#20)

### `pipeline/level/fixtures/logger_output.csv`

```csv
session,event,phase,pattern_id,explained,t_run_s,build
s01,hit,intro,BOLT_Single,y,9.8,abc1234
s01,hit,contest,BOLT_Fan3,n,40.2,abc1234
s01,hit,contest,GUST_Wing,y,55.0,abc1234
s01,death,desperation,BOLT_Aimed2,y,118.6,abc1234
s02,hit,contest,BOLT_Aimed2,y,77.1,abc1234
s02,death,desperation,BOTTOM_EXIT,n,131.0,abc1234
s03,hit,desperation,ARC_Return,y,107.4,abc1234
s03,survive,desperation,,,150.0,abc1234
```

## Commands and checks

### `tools/encounter_check.py`

Usage text from the file:

```text
Encounter gate. GDD SH1.0 (the current GDD): the state-driven Keeper fight is the encounter.json baseline preset;
E29 holds every GDD number it copies (numbers_from_gdd) to the manifest, and S1-S13 (tools/encounter_spec.py) check its
phases, targets, attacks, breaks and transitions. GDD 1.3 (history, and the frozen 1.3 data in tests/fixtures/gdd13):
one arena, one clockwork owl, one approved bolt on a timer (GDD 1.3 §7, §7B, §8), checked by the timeline rules E1-E29
below. Which applies is the manifest's GDD model (tools/tuning.py MODELS: `timeline`).

GDD SH1.0 state mode (data `"model": "state"`):
  E29 gdd        every attack names a manifest `feature` that is on; every numbers_from_gdd path resolves to a number
                 equal to its manifest key's approved value (tools/tuning.py rule: the start, while GDD SH1.0 prints no
                 range); a top-level timeline (patterns, phases, duration_sec) is GDD 1.3 history and fails
  E28 empty      no baseline preset, or one with no attacks or no numbers_from_gdd

Reads pipeline/level/encounter.json (the mirror of the DA_OwlPattern and DA_Phase assets) and
checks it against the rules in pipeline/checklists/level-sections.md. Stdlib only.
Thresholds live in this file (a gate file), not in the data the Level Designer edits.

Rules (id: what fails):
  E1 telegraph   TelegraphSec < 0.4 s, or no visual tell (pose or VFX). Sound alone fails (GDD §7).
                 Bolts and arcs need all three layers: pose, sound and VFX (a player watching the hero still gets it).
  E2 stages      ActiveSec <= 0, RecoverySec < 0, or ActiveSec shorter than the volleys and stagger need.
  E3 phases      not one `base` phase 0-100% and not intro/contest/desperation in order (GDD 1.3 §8: phases are
                 optional tuning presets), gaps or overlaps in 0-100%, desperation > 30% (pipeline default).
  E4 distinct    [2+ patterns] a phase that does not add or swap a pattern or space rule vs the phase before.
  E5 cue         [2+ phases] no single phase_change_cue, or a phase that sets its own cue.
  E6 intro       intro uses a bolt with count > 1, an arc, more than 1 gust, or [2+ patterns] overlapping attacks.
  E7 first-use   [2+ patterns] a pattern's first use overlaps another attack (teach before testing).
  E8 breather    [2+ patterns] a phase has no window >= 3.0 s with no attack in telegraph, active or flight.
                 With the one approved bolt the GDD sets the rhythm (E29), so E8, E19 and E26's breather part are off.
  E9 colour      amber on anything but a bolt tell, red on anything but the arc, or a bolt/arc without it.
  E10 readable   a projectile pattern without draw_on_top and directional_sprite.
  E11 spread     a lone angle (nearest-neighbour gap > 2x the median gap), a spread with spawn_offset_sec 0,
                 an aimed spread with an odd count and no odd_count_reason, volleys > 1 with seed step 0.
  E12 origin     origin_locked_during_telegraph is not true (owl drift must not move the fire point).
  E2 also       an arc without reach > 0, flight_sec > 0, flight_sec <= active_sec, or core_radius > 0.
  E13 safe-path  with the owl at the min and the max of its drift Y, and aimed bolts and arcs aimed at the
                 hero's high, middle and low spots, a hero-sized box can move (at hero speed) through every
                 simulated step of every attack cluster without touching a bolt or the arc.
                 The arc is an out-and-back loop: along the aim line reach x 4s(1-s), sideways
                 side x sin(2 pi s), s = time since launch / flight_sec. It is gone when it gets back.
  E14 coverage   [2+ patterns] a row (pos_high, pos_low, pos_far, ctl_rise, ctl_fall, ctl_horizontal; ctl_gust only once the
                 Gust row of pipeline/qa/test-map.md is merged, because the gust is P1) has no pattern used by
                 the end of phase 2. Always: a bolt claims a position its bolts never reach.
  E15 gust       a gust zone outside the hero zone, or one with no hero-sized lane above or below it.
  E16 end        end_event does not stop threats, the owl does not depart, no Survived card, quiet < 5 s.
                 (A story clue is optional: narrative is DEFERRED, NAR-01, GDD 1.3 §1.)
  E17 arena      owl zone not in the right half, hero and owl zones overlap, drift outside the arena.
  E18 doc        the generated block in pipeline/level/encounter.md differs from this data.
  E19 intensity  [2+ patterns] a phase's threat share (seconds with any attack in telegraph, active or flight / phase
                 length) is over 60%; density (attack-seconds per second, overlaps add up) of intro is over
                 contest's, or desperation's is over 1.3x contest's; or two peaks (clusters of 2+ attacks)
                 have no 3.0 s breather between them.
  E20 camping    after intro (in every phase of a one-phase encounter), a hero standing still on any point of a 5x5 grid over the hero zone (under the
                 altitude cap) is never hit by a bolt or arc in that phase, at either end of the owl's drift.
  E21 layering   [2+ patterns] contest has no cluster with an aimed bolt pattern and a non-aimed bolt pattern together
                 (aimed shots force a move, static shapes block a route).
  E22 tuning     hero speeds, hurtbox and bolt hitbox are not read from the Game Designer's tuning file
                 (arena.tuning_source), a copy of them sits in encounter.json, or the hurtbox is > 50% of
                 the body sprite area.
  E23 owl box    the owl hitbox is < 80% of the owl sprite area (auto-fire must land on what the player sees).
  E24 midpoint   [2+ patterns] no pattern makes its first appearance in the second half of contest (the midpoint turn).
  E25 recovery   [lift loss on: lowest lift tier < 1.0, SURV-04] at the lowest lift tier (the torn umbrella), climbing from the lowest hero spot to the highest
                 one under desperation's (or base's) cap (plus half the open rise ramp) takes longer than desperation's
                 longest breather. A hero knocked to the bottom must be able to climb back in one breather.
  E26 clock hit  a pattern without interruptible_sec (0 = a clock hit does not disrupt it), one over 1.0 s
                 ("briefly", GDD §5), or one > 0 without interrupt_replays_telegraph true (a clock hit pauses
                 the attack; if its telegraph was showing, the full telegraph plays again, so an interrupt never
                 shortens a telegraph already on screen). [2+ patterns] Also fails a phase whose breather drops
                 under 3.0 s when every interruptible attack runs late by interruptible_sec + telegraph_sec.
  E28 empty      the data has no patterns or no phases (an empty editor dump proves nothing).
  E27 wing hit   a gust without gust_strength_by_wing_tier (a list: 1.0 first, never rising, every value in
                 (0, 1]; [1.0] = wing hits cut), or a list longer than 1 without wing_tear_overlays (one
                 texture per damaged tier, so a weaker gust is visible).
  E30 baked      once pipeline/qa/baked.json exists, each value the game ships that this sim or feel_check reads
                 (tools/tuning.py SIM_KEYS) equals the data file value (dry run B H4)
  E29 gdd        GDD 1.3 approved numbers (docs/feature-manifest.json approved_parameters, held to the GDD by
                 manifest_check.py): every pattern names a manifest `feature` that is on (default_enabled); exactly
                 one OWL-01 base bolt, single and aimed, with telegraph_sec in the OWL-01.telegraph_delay range and
                 speed in the OWL-01.projectile_speed range; duration_sec in the END-01.survival_s range; seed =
                 OWL-01.seed (no range). The section 5A starts are provisional tuning, so any in-range value passes
                 (dry run A H4; bake_preset uses the same range). With only the base bolt: first telegraph at
                 OWL-01.initial_grace_s (no range), then one interval inside the OWL-01.cadence range to the end.
                 interruptible_sec > 0 needs COM-02 on; a wing-tier gust list longer than [1.0] needs COM-03 on.

Playtest log mode (--playtest CSV...; the log's owner is QA and Build):
  L1 header      columns are not exactly session,event,phase,pattern_id,explained,t_run_s,build.
  L2 event       event is not hit, death or survive.
  L3 pattern     a hit or death row has an empty pattern_id, or one that is not in encounter.json
                 (BOTTOM_EXIT is the one extra id: leaving through the bottom edge, GDD §2).
  L4 explained   a hit or death row has explained other than y or n.
  L5 row         phase not base/intro/contest/desperation, t_run_s not a number >= 0, empty session or build.
  L6 empty       a log has no hit, death or survive row (a header alone is not a playtest).
  The report prints hits, deaths and explained=n per pattern. explained=n is a bug against that pattern
  (fix the tell), not a log error, so it does not fail the check.

Envelope mode (--envelope "FEEL_ENVELOPE ..."; the line card 0.13's UmbrellaElla.Move.World.FeelEnvelope logs):
  V1 field       a field of the line is missing or not a number.
  V2 differs     a measured value is off the tuning file (feel.json `movement`, the numbers this sim uses) by
                 more than 5% (or 2 frames for the *_f fields). Fields: accel_f = frames from 0 to move_speed
                 (move_speed / move_accel x 60), fall = max fall cm/s, rise_intact and rise_critical = UP_OPEN rise
                 cm/s at full and lowest health (equal unless SURV-04 is on), blend_f = state blend frames. Then the game and the sim disagree: fix the
                 header default or feel.json in one tuning PR.

Wiring mode (--wiring [ROOT]; owner: Producer). No encounter card moves to doing until it prints 0 problem(s):
  W1 day0       pipeline/day0-cards.md has no `Owl data types` row naming UmbrellaElla.Owl, or no `Owl dump`
                row naming `encounter_check.py --data`.
  W2 test-map   pipeline/qa/test-map.md is missing an UmbrellaElla.Owl test name (the 2 phase tests only when
                 encounter.json has more than one phase).
  W3 log spec   pipeline/qa/playtests.md has no `Columns:` line equal to the L1 columns.
  W4 role row   AGENTS.md has no roles-table row for pipeline/roles/level-designer.md.
  W5 reviewer   pipeline/roles/game-designer.md does not name encounter_check.py (its review criteria).
  W6 presets    (with encounter_presets) AGENTS.md has no roles-table row for pipeline/roles/encounter-designer.md,
                 pipeline/day0-cards.md has no row naming `--ready` or `--playthrough`, or pipeline/qa/test-map.md
                 misses an encounter preset test (ENCOUNTER_TESTS).

Card mode (--card FILE...; an encounter card's text, owner: the card's reviewer; C6-C9 in tools/encounter_spec.py
apply when the card has an `Encounter phases:` line):
  C1 data gate  no pasted `encounter_check: 0 problem(s)` line.
  C2 coverage   no `Coverage signed: <name> <YYYY-MM-DD>` line.
  C3 art        no `Accent check: ... <name> <YYYY-MM-DD>` or `Motion check: ... <name> <YYYY-MM-DD>` line.
  C4 paper walk no `Paper walk: <link or #n>` line.
  C5 engine     an Owl test name (phase tests only with 2+ phases) is on no line with PASS, and on no `Not run` line with a card number (#n).

Tuning read from the tuning file (cm/s, GDD 1.3 §5A; worst case, so the sim never passes on a speed the hero lacks):
  sideways = move_speed x open_steer_multiplier; up = ascent_speed x the lowest lift tier (1.0 unless SURV-04);
  down = max_fall_speed; hurtbox = forgiveness.player_hurtbox_cm and bolt hitbox radius =
  forgiveness.bolt_hitbox_radius_cm, both fixed collider data, never derived from sprite size (GDD 1.3 7A, 7C).
  The body art box is only compared with the collider (E22 area share). Experiment arcs (off) scale their
  core_radius by bolt_hitbox_radius_cm / bolt_core_radius in the sim only.

Encounter presets (S1-S13, P1-P8, C6-C9): the whole fight as data in encounter.json `encounter_presets` (owner:
Encounter Designer). The rules are listed in tools/encounter_spec.py. Every check runs S1-S11 and S13 on every preset;
the GDD 1.3 baseline preset takes its numbers from the top level, so E29 still holds them to the manifest.
  --presets [--gdd REV] [--context C]   list the presets a context may load (C: ship, workbench, practice, gdd_picker;
                                        the GDD picker asks with the revision it picked and gdd_picker)
  --ready --preset ID                   S12: every hitbox, art and sound row the preset names exists; prints
                                        `encounter_ready: 0 problem(s) preset=ID` (the line an encounter card carries)
  --spec-hash ID/PHASE                  the phase's spec hash (critic verdicts carry it)
  --critic-packet ID/PHASE [--log L] [--video V]   the blind critic's whole input for one phase
  --playthrough LOG --preset ID         P1-P8 on the game's ENCOUNTER_EVT run log; prints
                                        `playthrough_check: <n> problem(s) preset=ID phases=...`

Usage:
  python3 tools/encounter_check.py                 # check; prints measured numbers
  python3 tools/encounter_check.py --write-md      # rewrite the generated block in encounter.md
  python3 tools/encounter_check.py --data F --md M # other files (tests, the editor dump)
  python3 tools/encounter_check.py --tuning F      # another tuning file (default: arena.tuning_source)
  python3 tools/encounter_check.py --playtest a.csv b.csv   # check playtest logs, per-pattern report
  python3 tools/encounter_check.py --envelope "FEEL_ENVELOPE accel_f=12 ..."   # game vs tuning file
  python3 tools/encounter_check.py --manifest F    # another feature manifest (default: docs/feature-manifest.json)
  python3 tools/encounter_check.py --wiring                 # are the engine cards, tests and docs filed?
  python3 tools/encounter_check.py --card card.md           # does an encounter card carry its lines?
Exit 0 = clean, 1 = problems.
```

Run in CI by:

- `.github/workflows/pipeline-checks.yml`: Owl encounter data (Level Designer)

Tests: `tests/test_encounter_arena.py`, `tests/test_encounter_check.py`, `tests/test_encounter_presets.py`, `tests/test_encounter_wiring.py`, `tests/test_pipeline_check.py`, `tests/test_playtest_log.py`, `tests/test_tuning.py`

### `tools/encounter_spec.py`

Usage text from the file:

```text
Encounter presets: the boss fight as a whole, as data (owner: Encounter Designer). Stdlib only.

pipeline/level/encounter.json `encounter_presets` holds one or more presets. Each one is the full fight: phases,
targets with HP, attacks (telegraph, effect, counterplay), phase transitions, pacing over the run and story beats.
Gameplay code reads the selected preset; nothing about the fight is hardcoded. The default preset is the GDD 1.3
baseline. GDD 1.3: it takes its numbers from the top-level patterns, phases and duration_sec (uses_top_level; E29
holds those to the manifest approved_parameters) and copies none. GDD SH1.0: the baseline holds its own numbers and
lists each GDD one in numbers_from_gdd (E29 holds those to the manifest). Every other preset is `proposed`: workbench, practice and the GDD picker
only, never shipped, until its decision row is DECIDED by its owner.
tools/encounter_check.py runs these rules on every check; this module has no command line of its own.

Rules (id: what fails; each FAIL line says what to change):
  S1 presets     no presets block, no default, a default that is not the one `baseline` preset, a status other than
                 baseline/proposed, a proposed preset with `ship` in selectable_in, an unknown selectable_in value,
                 no gdd_revision, or a proposed preset without a decision row in docs/decisions.md or an owner.
  S2 baseline    the baseline copies a number the top level owns (telegraph, first_at, cadence, timer seconds),
                 names a pattern the top level does not have, leaves a scheduled pattern out, or has other phase ids.
  S3 refs        a phase names an unknown target or attack; an attack's phases and the phase lists disagree;
                 cancelled_by, active_while or a sequence names an unknown target; a numbers_from_reference path
                 does not resolve; the reference file is missing.
  S4 reachable   no entry.full_run, a phase not reachable from it, an unknown next, a cycle, not exactly one
                 ends_fight phase, an ends_fight phase with a next, or another entry naming an unknown phase.
  S5 finishable  a phase without ends_when; a target it needs is not in the phase, has no HP, is optional, is not
                 vulnerable in that phase or has hit_share <= 0; HP targets with player shot_damage <= 0; a target
                 with a floor before the final phase that is not ended in the final phase.
  S6 telegraph   an attack telegraph shorter than the floor (the larger of encounter_check MIN_TELEGRAPH_SEC and the
                 manifest OWL-01.telegraph_delay min, the GDD minimum reaction time), with no visual (pose or VFX:
                 sound alone fails, GDD section 7) or with no `shows` text. A shot the GDD gives no timed prefire
                 (GDD SH1.0 OWL-12: red and yellow volleys) sets `no_prefire: <Rule ID>` and sec 0; it still needs
                 its visual and `shows`.
  S7 counterplay an attack with no counterplay, an unknown verb, a verb the preset's player cannot do
                 (player.verbs), or a verb listed both as counterplay and as not_counterplay.
  S8 pacing      fight_length_sec outside the manifest END-01.survival_s range; the estimated fight length
                 (HP / (shot damage / shot cadence x hit_share) per target, plus stuns and transitions; clock floor
                 gives the short and the long case) outside fight_length_sec.
  S9 cancel      an attack scheduled in a phase after its cancelled_by target broke; a break that cancels an attack
                 that does not name it; a break without new_attacks false or without in_flight.
  S10 transition a phase without transition_in, with new_attacks not false or a negative length; an attack whose
                 first_at falls inside the transition (it would fire while the phase changes); a cadence not longer
                 than the telegraph.
  S11 names      a target without a hitbox id; an attack without art or sound ids.
  S12 ready      (--ready only, and on every encounter card) a hitbox id not in pipeline/feel/hitboxes.json
                 entities, an art id not in pipeline/art/references.json elements, a sound id not in
                 pipeline/audio/sound-list.csv.
  S13 doc        the generated presets block in pipeline/level/encounter.md differs from this data.

Playthrough log (--playthrough LOG; the game's ENCOUNTER_EVT lines, card 0.31):
  ENCOUNTER_EVT t=<s> preset=<id> kind=<kind> phase=<id> [attack=<id>] [target=<id>]
  kinds: phase_start phase_end transition_start transition_end telegraph fire hit break end
  P1 line       a field is missing, t is not a number, an unknown kind, another preset.
  P2 order      phases do not start in the preset's order from the entry (entry=<id> on the first phase_start).
  P3 telegraph  a fire with no telegraph of that attack before it, or a lead shorter than the spec telegraph.
  P4 transition a telegraph or fire inside a transition or inside a break's stun.
  P5 schedule   an attack in a phase that does not list it, or after its cancelled_by target broke.
  P6 targets    breaks out of the phase's sequence; a phase that ends with a required target unbroken.
  P7 end        no end event (the run did not finish), or a full run's length outside fight_length_sec.
  P8 empty      no ENCOUNTER_EVT line.

Critic loop (card rules, encounter_check.py --card and tools/check_pr.py rule encounter):
  A card or PR that builds or tunes part of a fight carries `Encounter phases: <preset>/<phase>, ...`
  (or `Encounter phases: none (<why>)` when it changes encounter.json without changing a fight).
  C6 critic      for each listed phase the newest `ENCOUNTER CRITIC:` line is PASS, its spec= is the phase's current
                 spec hash (--spec-hash), and builder= and critic= are different sessions. Every verdict line records
                 its round's scores: playthrough=<problems> check=<problems> (the playthrough_check and
                 encounter_check counts of that round), and rounds go up line by line. There is no round cap: the
                 loop runs until the critic passes.
  C7 stuck       the newest STUCK_ROUNDS verdicts are FAIL rounds in a row with no improvement: the same biggest gap
                 and no better playthrough or check score than the round before. Only then the card waits for a
                 human (needs-human, `NEEDS HUMAN: <owner>`). A new gap or a better score keeps the loop going.
  C8 run log     no `playthrough_check: 0 problem(s) preset=<preset> phases=...` line covering each listed phase.
  C9 ready       no `encounter_ready: 0 problem(s) preset=<preset>` line (the S12 rows exist).
```

Tests: `tests/test_encounter_presets.py`, `tests/test_gdd_select.py`
