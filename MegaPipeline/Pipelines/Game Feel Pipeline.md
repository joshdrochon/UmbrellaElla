> Generated from `docs/feel-spec.md`, `pipeline/feel/feel.json`, `pipeline/feel/hitboxes.json`, `pipeline/feel/ab-log.csv`, `pipeline/feel/arena-log.csv`, `pipeline/feel/latency-log.csv`, `tools/feel_check.py`, `tools/hitbox_check.py` at `b201a66` — edit the sources, not this file.
> Rebuild: `python3 tools/export_package.py`. Check: `python3 tools/export_package.py --check`.

# Game Feel Pipeline

A readable copy for people. Agents load these rules from the repo paths listed below.

## About this pipeline

- **Purpose:** Hit-stop, shake, input latency and other feel numbers, kept in data and tested A/B.
- **Owner:** Game Designer (numbers) with the creative director (human) for feel calls.
- **Inputs:** The feel spec, playtest notes, latency measurements.
- **Outputs:** `pipeline/feel/feel.json`, A/B, arena and latency log rows.
- **Gates:** `feel_check.py` and `hitbox_check.py check` (art aligns to colliders) in CI; latency measured on the packaged build.

## Built from

- Feel spec and data: `docs/feel-spec.md`, `pipeline/feel/feel.json`, `pipeline/feel/hitboxes.json`
- Logs: `pipeline/feel/ab-log.csv`, `pipeline/feel/arena-log.csv`, `pipeline/feel/latency-log.csv`
- Commands and checks: `tools/feel_check.py`, `tools/hitbox_check.py`

## Feel spec and data

### `docs/feel-spec.md`

#### Feel spec: THE LAST HOUR

> GDD SH1.0 note (D-new-gdd-sh10): lines on this page that still describe the GDD 1.3 encounter (one owl bolt, the front shield, the 90 s survival timer, wear stages, the 1.3 QA-01..QA-28 tests) are history. The current design is `docs/gdd/GDD-SH1.0.md` and `docs/feature-manifest.json`, which win; the owning role re-files this page against the SH1.0 Rule IDs on its next card.


On-demand file. Load it when your card touches movement, umbrella state, firing, hits, owl tells,
the end event, VFX, shake, hit-stop or any tween. Game rules come from the GDD (§4–§8); this file only
says how those rules should *feel* and how we check it.

- Data: `pipeline/feel/feel.json` (owner: Game Designer proposes, game design owner accepts). One source per number:
  `movement` holds the design values (D20); the game reads them only from the header defaults of `FUmbrellaFlightTuning`
  and `FEllaMovementTuning` (D-new-tuning), and card 0.13's `FEEL_ENVELOPE` line proves the two match
  (`encounter_check.py --envelope`). The `DA_Feel` asset (juice only, no movement numbers) is made from the rest.
- Gate: `python3 tools/feel_check.py`. The limits live in the tool, not the data. Tuning the data can't loosen them.
- Logs: `pipeline/feel/ab-log.csv` (on/off checks), `pipeline/feel/latency-log.csv` (key-to-screen and peak frame time per gate build),
  `pipeline/feel/arena-log.csv` (tuning-arena runs, §8b).
- Numbers come from the team's feel research. **[sourced]** = read from a shipped game or paper. **[proposed]** = starting value; a playtest may move it inside the range.
- Frames are at 60 fps (16.7 ms).
- **Engine tests.** Every test tagged [VERIFY] below runs in Unreal, so CI can't run it. Each one has a row in
  `pipeline/qa/test-map.md` (owner Gameplay Dev). `python3 tools/feel_check.py --test-map` fails if any `UmbrellaElla.*` name in this file has no row,
  or a row without `(world)` (or `.World.` in the name), and `tests/test_feel_check.py` runs it in CI.
  `python3 tools/feel_check.py --test-map-rows` prints the `planned` rows to paste. The card that builds a test sets its row to `merged`;
  from then on the daily build requires it. Done when the test exits 0 in `tools/ue/test.sh` (or `test.ps1`) output pasted in the PR.
  All of them spawn actors, so each is a world test.
- **Tuning arena.** Tune feel in `L_Graybox` with one bolt pattern and one gust (`threat_spacing.arena_patterns`), never in an empty map.
  L_Graybox is the single-screen arena: fixed camera, owl spawn, one bolt volley, one gust zone (Day-0 card 0.8). Logged as in §8b.

##### 1. Toggles and A/B: the core rule
1. Every effect reads one bool and one strength (0–1) from `DA_Feel`. Example: `bPlayerHitShake`, `PlayerHitShakePower`. One global `ShakePower` scales all shake.
   `python3 tools/feel_check.py --fields` prints the full field list. The Gameplay Dev makes the asset from it.
2. Every event and every cue in `feel.json` has its own flag. `feel_check.py` fails a row without one.
3. A feel card is done when `python3 tools/feel_check.py --ab <flag>` exits 0. That means a row in `ab-log.csv`:
   the same build played with the effect on and off, what the player did or said each way, a verdict (`keep` / `cut` / `tune`),
   and `signed_by` = the game design owner. Agents never sign. The row's `event` must be the event that owns the flag.
   The gate holds this: `signed_by` must be a name in the confirmed "Game design owner" row of `docs/jam-brief.md` People
   (read with `check_card.py`'s People parsing), and `build_sha` must be a commit in this repo. Any other name fails.
   **How many rows.** One row per event, on the event flag (16 at most). That row covers the event's rank 1–2 cues:
   `--ab bOpenSquash` passes on a signed `bOpenFeel` row. A rank 3+ cue needs its own row. So does any cue being cut.
4. Players get a shake off option (`shake_off_option: true`). `ShakePower = 0` must remove all shake. It also turns rumble off (`rumble_off_with_shake`).
5. **Flip it live.** Every `DA_Feel` field is also a console variable `feel.<Field>` in Development builds (`feel.bPlayerHitShake 0`).
   `--fields` prints the cvar name on each line. The A/B check flips the cvar in one running build; it never re-cooks.
   Shipping builds read only the asset. Test [VERIFY] `UmbrellaElla.Feel.ToggleAtRuntime`: for each event, set its cvar to 0,
   trigger the event, assert no cue fired; set it to 1, assert the rank-1 cues fired. Owner: Gameplay Dev.

##### 2. Events and cues (ranked)
`feel.json` has one row per event. Each cue has a rank. **Ranks 1–2 are MVP**: build them first. Rank 3+ is optional polish.
Every event needs a rank 1–2 sound **and** a rank 1–2 visual (particles, squash, flash, pose, nudge or tween).

| Event | GDD | MVP cues (rank 1–2) | Hit-stop | Shake |
|---|---|---|---|---|
| `umbrella_open` | §4 | sound, squash (1.2, 0.85) 0.2 s, pose | 0 | none |
| `umbrella_close` | §4 | sound, stretch (0.8, 1.2) 0.15 s scaled by fall speed, pose | 0 | none |
| `gust_catch` | 1.3 §7 WIND-01 (WindEntered, P0) | sound, wind lines, stretch (0.85, 1.15) 0.2 s | 0 | none |
| `bolt_fire` | §5 | soft tick sound, 3-particle muzzle | never | never (rank-3 kick ≤ 2 px) |
| `bolt_fire_manual` | §5 + review comment | blast sound, muzzle, 2 px kick | never | never |
| `bolt_hit_clock` | §5, §8 | sound, clock spark, clock flash, reaction pose | 3 f (rank 3), cooldown 0.5 s | never |
| `bolt_hit_wing` | §5, §8 | sound, wing spark, flash | 0 | never |
| `bolt_hit_body` | §5 | sound, body spark, flash | 0 | never |
| `player_hit` | §7 | hurt sound, 1-frame white flash, squash (1.3, 0.7) 0.25 s, rumble 0.2 s (gamepad) | 5 f | 0.2 s, 2.5% screen height |
| `tier_damaged` | §4, §8 | tear sound, tear-pop burst, texture swap tween | 0 | none |
| `tier_critical` | §4, §8 | big tear sound, burst, rumble 0.15 s (gamepad) | 6 f | 0.15 s, 1.5% |
| `owl_tell_bolts` | 1.3 §7B | clock wind-up sound, amber clock flash, pose held 0.75 s; 0.75 s tell (= OWL-01 warning) | 0 | none |
| `owl_tell_gust` | §6 | gust wind-up sound, wing pose, flow lines; 1.0 s tell | 0 | none |
| `owl_tell_arc` | §6 (P2) | wind-up sound, red arc path preview; 0.8 s tell | 0 | none |
| `end_trigger` | §2 | departure sound, owl pose | 6 f | 0.2 s, 1% |
| `owl_condition_step` | §5, §8 | gear-slip sound, clock crack overlay step, wing-hole overlay step, clock-hand stutter | 0 | none |
| `shield_catch` | 1.3 §6, §7A DEF-01 (CatchSucceeded) | `SFX_ShieldCatch`, 2-frame catch flash; plays during the heal cooldown too | 0 | none |
| `shield_heal` | 1.3 §6 SURV-03 (20 HP applied) | `SFX_ShieldHeal`, umbrella wear step-up tween; never during the 2 s cooldown | 0 | none |

**Firing mode.** GDD 1.3 decides it (DEC-02): auto-fire on ATTACK_DESCENT, no manual fire. `bolt_fire` is the cue. `bolt_fire_manual` stays as an optional row and is not required (`feel_check.py`). `bolt_hit_wing` and `owl_condition_step` are optional too (OWL-03 / COM-03 effects off; the owl has no HP). `bolt_hit_clock` is P0 (clock-hit visual cue on).

**Colours (key art).** Player bolt, muzzle and clock sparks are gold/amber. Owl projectiles and danger cues are rust red. Nothing else saturated (`art-bible.md` rule 3).
**Owl reactions.** Clock, wing and body hits each get a flash or pose. No flash faster than 3 per second (WCAG 2.3.1).
**Owl condition (the enemy's face).** Per-hit flashes are not enough: the owl shows what the player has done so far (GDD §8,
"owl chest clock = mechanism condition", "wing holes"). `owl_condition_step` fires each time a part reaches `hits_per_step` more hits.
That part's `overlay` cue steps up one tier (`steps` 2–5) and stays until restart (`persist: true`). The gate needs one rank 1–2
overlay for the clock and one for the wing. It shows condition, never a countdown and never an owl health bar (GDD §5, §8).
`hits_per_step` (4 / 4) is [proposed]. Test [VERIFY] `UmbrellaElla.Feel.OwlConditionSteps`: in a transient world, hit the clock
`hits_per_step` × 2 times; assert the clock overlay index is 2 and the wing index is 0; hit past the last step; assert it stays at `steps`. Owner: Gameplay Dev.
**Owl tells hold.** Each tell has a pose or flash with `hold_s` ≥ `telegraph_s`, or a tween with `duration_s` ≥ `telegraph_s`. The gate checks it.
The Asset Specialist sets the wind-up key frame of the owl flipbook (Paper2D per-key-frame duration) to at least that `hold_s` [VERIFY: read in the editor, pasted in the asset PR].

##### 3. Hit-stop
| Rule | Value | Basis |
|---|---|---|
| Range | 0–6 frames | Celeste 3 f (dash), 6 f (launch) [sourced]; Melee ≥ 3 f [sourced] |
| Player hit | 5 f | research [proposed] |
| Critical tear, end event | 6 f | top of range |
| Bolt hits | 0–3 f; > 0 needs a cooldown ≥ 0.3 s | constant stops on auto-fire stutter [proposed] |
| Bolt fire | never | — |
| Two at once | take the longer one, never the sum (`hitstop_stacking: max`) | — |
| Time already slowed | skip hit-stop | — |
| Input during hit-stop | buffered 0.1 s, applied on the first free frame | research §2 [proposed] |
| Curve | hard cut only for the jam; no fade in or out. The gate rejects `fade*` keys on hit-stop cues | keeps one number per cue |

Test [VERIFY]: `UmbrellaElla.Feel.HitStopFrames` triggers each event in a transient world at a fixed 1/60 s step
and counts ticks with global time dilation ≈ 0. Pass: equals the `feel.json` frames. Owner: Gameplay Dev.
It has a slowed case: set global time dilation to 0.5, fire `player_hit`, assert 0 hit-stop ticks (`hitstop_skip_if_slowed`).
Boundary test [VERIFY]: `UmbrellaElla.Feel.HitStopStacksMax` fires `player_hit` (5 f) and `tier_critical` (6 f) on one frame. Pass: 6 ticks, not 11.

##### 4. Screen shake
- Only on `player_hit`, `tier_critical` and `end_trigger`. Never on bolt fire or bolt hits (the gate fails it).
- Directional: `direction` is `away_from_source` (player hit, critical tear) or `toward_owl` (end). The gate rejects anything else. Lasts ≤ 0.2 s. Amplitude ≤ 2.5% of screen height
  (the same cap as `tools/ui_check.py` `MAX_SHAKE_AMP_PCT_H`; a test fails if the two differ).
- Decays as a damped spring. Sized by event: player hit 2.5%, critical tear 1.5%, end 1%.
- **Spring.** Per frame at 60 fps, from offset `x = 1` along `direction` and `v = 0`: `v += -spring_elasticity * x; v *= 1 - spring_drag; x += v`.
  The offset is forced to 0 at `duration_s`. Limits: `spring_drag` 0.1–0.5, `spring_elasticity` 0.05–0.6 (`feel.json` `global`).
  The gate runs the spring for each shake cue and fails it if |x| over the last 3 frames is above 0.25: the cut to 0 would show as a pop.
  Start values 0.3 / 0.2 [proposed]. Drag 0.1 / elasticity 0.1 is still at 0.47 after 12 frames, so it fails.
- Test [VERIFY] `UmbrellaElla.Feel.ShakeCurve` logs the camera offset each tick for each shake event. Pass: peak within ±10% of `amp_pct_h`,
  0 by `duration_s` + 2 f, the first offset's sign matches `direction`, and with `ShakePower = 0` every offset is 0. Owner: Gameplay Dev.
  The settings toggle is the UI lane's own test (`UI.World.ShakeOffZeroesShake`, its row is theirs); this test proves the shake side.
- **Rumble** (gamepad only, `applies_if: gamepad`). Only on `player_hit` and `tier_critical`, ≤ 0.2 s, its own flag and power.
  The gate fails rumble on any other event. If the GDD owner decides keyboard only, the rumble cues stay in data and never fire.
- Bolt fire may nudge the sprite ≤ 2 px opposite the shot (render only), or nothing.
- `bBoltKick` (rank 3) can only leave `feel.json` after a signed `ab-log.csv` row for it with verdict `cut`. The gate fails otherwise.
- Basis: Celeste DirectionalShake 0.1–0.2 s [sourced]; Eiserloh trauma model (shake ∝ trauma², decays) [sourced].

##### 5. Squash and stretch
- Peak change 10–40% on one axis. Recovery ≤ 0.25 s (Celeste jump stretch recovers in 0.23 s [sourced]).
- Render-only: a scale tween on the sprite component, driven by `DA_Feel`. Collision never changes size.
- Close squash scales with fall speed at the moment of closing (Celeste landing squash scales by fall speed / 240 [sourced]).
  `scale_by` is `none` (default) or `fall_speed`; the gate rejects anything else. With `fall_speed`, the deviation from 1 is
  multiplied by `min(v / max_fall, 1)`, where `max_fall` = the natural max fall (`max_fall_speed`). There is no fast fall (GDD SH1.0 rule numbers (section 9 ranges blank, D-new-sh10-param-ranges)).
- Test [VERIFY]: `UmbrellaElla.Feel.SquashCurve` logs sprite RelativeScale3D each tick. Pass: peak within ±0.03, back to 1 by spec time ±2 frames, capsule size unchanged.
- Boundary test [VERIFY]: `UmbrellaElla.Feel.SquashScalesWithFallSpeed` closes at 50% and 100% of max fall. Pass: the peak deviations are
  0.5× and 1× the `feel.json` deviation, each ±0.03.

##### 6. Responsiveness and latency
| Rule | Target | Fail | How measured | Owner |
|---|---|---|---|---|
| Input → velocity change (game side) | same tick (0 f) | > 1 f | `UmbrellaElla.Feel.InputSameTick` [VERIFY]: inject the toggle through Enhanced Input at tick N, read velocity | Gameplay Dev |
| Input → first visible change | ≤ 1 f | > 1 f | same test, read sprite scale or flipbook | Gameplay Dev |
| Key press → photon | ≤ 67 ms | > 100 ms | 240 fps phone video of key and screen, ≥ 10 presses, median | QA and Build |

- Physics changes on frame 1 of the toggle. A pose may play over ≤ 3 frames; it never delays physics. No anticipation on player verbs.
- Bind the toggle on `Started`/`Pressed`, never `Hold` or `Released`.
- Done when, per gate build: `python3 tools/feel_check.py --gate G<n> --build <sha>` exits 0 (a `latency-log.csv` row with method "240 fps", ≥ 10 presses, median ≤ 100 ms, `measured_by` filled). Over 67 ms passes with a note and a TD card.
  `--build` must be a 7–40 character hex sha. It matches a row when one sha is a prefix of the other.

##### 7. Movement (GDD SH1.0 rule numbers (section 9 ranges blank, D-new-sh10-param-ranges))
GDD SH1.0 rule numbers (section 9 ranges blank, D-new-sh10-param-ranges) sets the movement numbers (Richard-approved provisional tuning, cm and s). `feel.json` `movement` mirrors the
manifest `approved_parameters` start values; `feel_check.py` fails any difference or a value outside the dev range.
A change goes through the GDD and the manifest first. Only UP_OPEN lifts. Attack and shield descent fall naturally under one
gravity rule: no per-state gravity multiplier, no fast fall (MOVE-02 off). Damage does not reduce lift (SURV-02, DEC-05).
The game reads the values from the `F<Comp>Tuning` header defaults.

| Parameter | Value | Dev range | Source |
|---|---|---|---|
| Horizontal max speed (`move_speed`) | 350 cm/s | 150–650 | GDD SH1.0 rule numbers (section 9 ranges blank, D-new-sh10-param-ranges) |
| Horizontal acceleration (`move_accel`) | 1800 cm/s² (0 → max in 0.19 s) | 400–3500 | GDD SH1.0 rule numbers (section 9 ranges blank, D-new-sh10-param-ranges) |
| Open-horizontal steering multiplier | 100% | 50–125% | GDD SH1.0 rule numbers (section 9 ranges blank, D-new-sh10-param-ranges) |
| Gravity (`gravity`) | 980 cm/s² | 400–1600 | GDD SH1.0 rule numbers (section 9 ranges blank, D-new-sh10-param-ranges) |
| Max natural fall (`max_fall_speed`) | 650 cm/s | 250–1000 | GDD SH1.0 rule numbers (section 9 ranges blank, D-new-sh10-param-ranges) |
| UP_OPEN ascent target (`ascent_speed`) | 300 cm/s | 120–550 | GDD SH1.0 rule numbers (section 9 ranges blank, D-new-sh10-param-ranges) |
| Acceleration toward ascent (`ascent_accel`) | 1200 cm/s² | 400–2600 | GDD SH1.0 rule numbers (section 9 ranges blank, D-new-sh10-param-ranges) |
| Lift by health stage (intact / damaged / critical) | 1.0 / 1.0 / 1.0 | other values only with SURV-04 on (then critical ≥ 0.5) | GDD SH1.0 SURV-05, FLOW-33, DEC-05 |
| Stop time (`stop_s`) | 0.2 s | 0.08–0.80 | ENGINEERING_PROVISIONAL |
| State blend | 0.20 s, sign change within 2 f | 0.15–0.25 | ENGINEERING_PROVISIONAL |

Test [VERIFY]: `UmbrellaElla.Move.World.FeelEnvelope` spawns the player in a transient world, holds each input and prints
`FEEL_ENVELOPE accel_f=N fall=N rise_intact=N rise_critical=N blend_f=N commit=SHA`, read from the live actor.
Units: `*_f` in frames at 60 fps; fall and rise in cm/s. A correct GDD 1.3 game prints about
`accel_f=12 fall=650 rise_intact=300 rise_critical=300 blend_f=12`.
Pass: `python3 tools/encounter_check.py --envelope "<line>"` exits 0 (each value within ±5%, or ±2 f, of `feel.json`). Owner: Gameplay Dev.

##### 8. Forgiveness (defaults, written as rules)
These are sensible defaults, not open decisions. Change them only with a playtest row.
- Toggle buffer 0.1 s (range 0.07–0.13): a press during hit-stop, hit-stun or a tear animation applies on the first free frame. Test [VERIFY] `UmbrellaElla.Feel.ToggleBuffer`: press 6 f before the lock ends → applies; 8 f before → ignored.
- Gameplay collision is fixed data, never read from sprite size, alpha, atlas or pose (GDD SH1.0 ANIM-02, §7C). `feel.json` `forgiveness.player_hurtbox_cm` (52.8 × 79.9 cm) and `bolt_hitbox_radius_cm` (12 cm) are the `*Tuning.h` collider values. Swapping art never changes them.
- Alignment targets, art against collider: the player collider covers 60% of the body art box (50–65%; canopy, hair and wand stay outside it); the owl bolt collider is 80% of its bright core (70–85%; the glow never counts). When new art misses them, change the art's scale, pivot or offset. A collider change is a separate approved change with its own regressions (GDD SH1.0 CORE-05).
- Post-hit invulnerability 0.8 s (GDD SH1.0 SURV-05, FLOW-33; `feel_check.py` fails any other value), shown by an alpha pulse ≤ 3 per second.
- Arena-bound nudge: touching a top or side bound by ≤ 4 px slides the player along it instead of stopping.
- Test [VERIFY] `UmbrellaElla.Feel.Hitboxes`: the live collider sizes equal `player_hurtbox_cm` and `bolt_hitbox_radius_cm` with any art set loaded (swap the art, sizes unchanged); a separate alignment check reports the collider / art-box share against the targets above. It never resizes the collider.
  Nudge case: move the player up into the top bound, offset 3 px sideways from a corner; assert it slides along the bound, not stops.

##### 8b. Threat spacing
Data: `feel.json` `threat_spacing` (% of the GDD 1.3 fixture arena, 1600 × 900 cm, manifest `fixtures.arena_cm`). Bolts fly sideways, so the gap between two bolts is vertical. Hurtbox = `forgiveness.player_hurtbox_cm` (fixed collider data, as % of the arena); the body box is art, only compared with it.
| Rule | Limit | Checked by |
|---|---|---|
| Gap between two bolts in one volley | ≥ 2.5 × hurtbox height | `feel_check.py` |
| Farthest move to reach a safe gap | the natural fall reaches it inside the bolt tell: (max fall / gravity)/2 + distance / max fall ≤ `owl_tell_bolts.telegraph_s` (now 0.33 + 25 / 72.2 = 0.68 s ≤ 0.75 s) | `feel_check.py` |
| Gust width (only with OWL-02 on) | from the gust centre, a sideways move clears it inside the gust tell: accel time/2 + (width/2 + hurtbox/2) / max sideways ≤ `owl_tell_gust.telegraph_s` | `feel_check.py` |
| Real patterns stay inside these numbers | encounter patterns use these as limits | encounter lane [cross-lane] |
Owner: Game Designer proposes, game design owner accepts. Done when `feel_check.py` exits 0 and `python3 tools/feel_check.py --arena` exits 0.
**Arena log** (`pipeline/feel/arena-log.csv`): `date,gate,build_sha,map,patterns,cues_on,note,played_by`. A row passes when `map` is `L_Graybox`,
`patterns` lists every `threat_spacing.arena_patterns` name (`;` between), `cues_on` is `yes`, `note` says what the player did,
`build_sha` is a commit in this repo, and `played_by` is a confirmed person in `docs/jam-brief.md` People (an agent cannot play).
`--gate G2` (and G3, G4) also runs `--arena`, so G2 cannot pass without a logged arena run.

##### 9. Niagara rules
1. `NS_HitSpark` is the one parent hit spark. Clock, wing and body sparks are child systems that override only colour, count and size.
2. Sprite renderer only. No ribbons, meshes or lights.
2b. Use built-in Niagara modules and dynamic inputs. A new module or scratch-pad script needs its own TD card.
3. Fixed bounds on every system.
4. Pooling on for anything used by bolt fire or bolt hits. Bursts on those events stay ≤ 8 particles; others ≤ 32.
5. Two Effect Types: `EFT_Gameplay` (hit sparks, wind lines: never culled) and `EFT_Cosmetic` (puffs, muzzle, tear pop: may be culled).
   The gate fails any `NS_HitSpark*` or `NS_WindLines` row that is not `gameplay`.
6. Budget: peak frame ≤ 33 ms (the smoke contract, `SMOKE_MAX_FRAME_MS`) at peak bullet count in a packaged Development build. Target 16.7 ms (60 fps); over it passes with a note.
   Done when, once per gate: `stat unit` and `stat Niagara` are read at peak bullet count [VERIFY: needs the engine], `peak_bolts` and `peak_frame_ms` are in that gate's `latency-log.csv` row,
   `feel_check.py --gate G<n> --build <sha>` exits 0, and the `stat Niagara` capture is pasted in the gate record. Owner: QA and Build.
7. Renderer, parent, pooling, fixed bounds and effect type in `feel.json` are self-declared. Two checks hold them to the real assets:
   - Every PR that adds or changes an `NS_` asset pastes, per system: renderer class(es), parent system, Fixed Bounds, Effect Type, and the pooling
     method on the spawning call. The Art Director's review is done when each pasted value matches that system's `feel.json` row. A missing paste is `request_changes`.
   - Test [VERIFY] `UmbrellaElla.Content.NiagaraSettings` loads every system in `vfx.systems` and asserts: `bFixedBounds`; the Effect Type is
     `EFT_Gameplay` or `EFT_Cosmetic` as the row says; every renderer is a sprite renderer; and a row with `parent` has that system as its parent
     [VERIFY: the 5.8.4 API that reads a system's parent and renderer list]. Pooling lives on the spawn call, so only the review checks it.

##### 10. Easing and tweens
- Every tween uses a named curve from `CF_FeelEase` (`ease_out_quad`, `ease_out_back`, `ease_in_out_sine`, `spring`). Never linear.
- Checked only in `feel.json`. No engine test reads the curves on the real timelines; the Dev Lead review checks each new
  timeline or tween call names a `CF_FeelEase` curve.
- One exception: clock-hand rotation is linear.
- Tier change: one tear-pop burst, one sound and a short texture swap tween. Never a silent swap.

##### 11. Who does what
| Step | Owner | Done when |
|---|---|---|
| Keep `feel.json` in range | Game Designer proposes, game design owner accepts | `feel_check.py` exits 0 on the PR |
| Make `DA_Feel` and wire cues | Gameplay Dev | `--fields` list matches the asset; the engine tests above pass |
| On/off check per effect | game design owner | `feel_check.py --ab <flag>` exits 0 |
| Latency per gate build | QA and Build | `feel_check.py --gate G<n> --build <sha>` exits 0 |
| Niagara budget per gate | QA and Build | `--gate` exits 0 with `peak_frame_ms`; `stat Niagara` capture pasted |
| Engine feel tests | Gameplay Dev | each [VERIFY] test exits 0 in pasted `tools/ue/test.sh` output |
| Owl wind-up flipbook hold | Asset Specialist | wind-up key frame ≥ the tell's `hold_s` |
| Threat spacing and tuning arena | Game Designer | `feel_check.py` exits 0; `L_Graybox` run logged |
| Niagara asset settings | Art Director | pasted Properties match `feel.json` (§9.7); `NiagaraSettings` passes |
| Engine test rows | Gameplay Dev | `feel_check.py --test-map` exits 0; each row set `merged` by the card that builds it |
| Tuning-arena run | Game Designer runs it, a teammate plays | `feel_check.py --arena` exits 0 before G2 |
| Owl condition overlays | Gameplay Dev (code), Asset Specialist (3 clock and 3 wing overlay frames) | `OwlConditionSteps` passes |

##### 12. When (feel from day one)
- **Day-0 card 0.13** (Gameplay Dev, test lane only): `FeelEnvelope` passes and `encounter_check.py --envelope` exits 0 on its line.
- **Feel card** (Gameplay Dev, filed by the Producer after G1): make `DA_Feel` from `feel_check.py --fields`, with the cvars (§1.5);
  wire the rank-1 cues of the 7 `mvp: true` events with placeholder sound and sprite. It owns the Feel rows of `pipeline/qa/test-map.md`.
  Done when `HitStopFrames` passes (output pasted), its test-map rows are `merged`, and `L_Graybox` is played with the cues on (`--arena` exits 0).
- **G1 → G2**: one A/B row per `mvp: true` event (§1.3). Other events get rows as their cards land.
- **Every gate**: QA and Build runs `--gate G<n> --build <sha>`.

### `pipeline/feel/feel.json`

```json
{
  "version": 1,
  "game": "Umbrella Ella: The Stolen Hour",
  "spec": "docs/feel-spec.md",
  "fps": 60,
  "data_asset": "DA_Feel",
  "source": "game_feel_research (team research notes, 2026-11-07). [sourced] = read from a shipped game or paper; [proposed] = starting value, change by playtest.",
  "global": {
    "ShakePower": 1.0,
    "shake_off_option": true,
    "hitstop_stacking": "max",
    "hitstop_skip_if_slowed": true,
    "hitstop_input_buffer_s": 0.1,
    "spring_drag": 0.3,
    "spring_elasticity": 0.2,
    "rumble_off_with_shake": true,
    "runtime_toggle": "cvar feel.<Field> in Development builds"
  },
  "latency": {
    "game_side_input_frames": 0,
    "first_visible_change_frames": 1,
    "input_to_photon_target_ms": 67,
    "input_to_photon_fail_ms": 100,
    "owner": "QA and Build",
    "note": "[sourced] Swink ~100 ms lag threshold; NES SMB ~2 frames. Measured with a 240 fps phone capture per gate build."
  },
  "movement": {
    "owner": "Game Designer proposes, game design owner accepts",
    "asset": "FEllaMovementTuning header defaults (copied from docs/feature-manifest.json approved_parameters; card 0.13 envelope proves the match)",
    "units": "GDD world units per second = Unreal cm/s (D-new-sh10-units)",
    "gdd_note": "GDD SH1.0 MOVE-13 / MOVE-21: four states, each a speed, no gravity: rise 120 (overhead, neither trigger), fall 330 (Shoot or Absorb), free fall 610 (both). Direct horizontal steering is OFF in both modes (MOVE-07); horizontal_max_speed 290 caps current-driven travel. Lift falls with active health to lift_min (SURV-05). feel_check holds these to the manifest starts; GDD SH1.0 prints no dev ranges yet (D-new-sh10-param-ranges).",
    "rise_speed": 120,
    "fall_speed": 330,
    "free_fall_speed": 610,
    "horizontal_max_speed": 290,
    "steering": "off",
    "lift_min": 0.3,
    "engineering_provisional": [
      "stop_s",
      "state_blend_s",
      "sign_change_max_frames",
      "pose_max_frames"
    ],
    "stop_s": 0.2,
    "state_blend_s": 0.2,
    "sign_change_max_frames": 2,
    "pose_max_frames": 3
  },
  "forgiveness": {
    "toggle_buffer_s": 0.1,
    "collision_note": "Gameplay collision is fixed data (the *Tuning.h collider values), never read from sprite size, alpha or atlas (GDD SH1.0 CORE-05, MOVE-22: display and collision scale are separate). The two ratios are alignment targets: collider / visible art box. When art changes and misses them, fix the art's scale, pivot or offset; a collider change is a separate approved change.",
    "player_hurtbox_cm": {
      "w": 52.8,
      "h": 79.9
    },
    "bolt_hitbox_radius_cm": 12,
    "player_hurtbox_ratio": 0.6,
    "projectile_hitbox_ratio": 0.8,
    "iframes_s": 0.65,
    "bound_nudge_px": 4,
    "hop_protection_s": 0.2
  },
  "threat_spacing": {
    "owner": "Game Designer proposes, game design owner accepts",
    "arena_map": "L_Graybox",
    "arena_patterns": [
      "RED_Fan",
      "GUST_Band"
    ],
    "note": "Percent of the Keeper arena (manifest approved_parameters.fixtures.arena_cm, 1920 x 1080; D-new-sh10-units). Red fans fly sideways, so the gap between two shots is vertical. Hurtbox = forgiveness.player_hurtbox_cm (fixed collider data); the player_body box is art and is only compared with it. The wing gust (OWL-16, P0) is a 120-unit horizontal band left by changing altitude.",
    "player_body_w_pct_w": 4.58,
    "player_body_h_pct_h": 12.33,
    "bolt_gap_min_pct_h": 25,
    "bolt_dodge_max_pct_h": 25,
    "gust_band_pct_h": 11.1
  },
  "easing": {
    "curve_asset": "CF_FeelEase",
    "curves": [
      "ease_out_quad",
      "ease_out_back",
      "ease_in_out_sine",
      "spring"
    ],
    "linear_allowed_for": [
      "clock_hand_rotation"
    ]
  },
  "vfx": {
    "parent": "NS_HitSpark",
    "systems": {
      "NS_HitSpark": {
        "renderer": "sprite",
        "fixed_bounds": true,
        "pooled": true,
        "effect_type": "gameplay"
      },
      "NS_HitSpark_Clock": {
        "parent": "NS_HitSpark",
        "renderer": "sprite",
        "fixed_bounds": true,
        "pooled": true,
        "effect_type": "gameplay"
      },
      "NS_HitSpark_Wing": {
        "parent": "NS_HitSpark",
        "renderer": "sprite",
        "fixed_bounds": true,
        "pooled": true,
        "effect_type": "gameplay"
      },
      "NS_HitSpark_Body": {
        "parent": "NS_HitSpark",
        "renderer": "sprite",
        "fixed_bounds": true,
        "pooled": true,
        "effect_type": "gameplay"
      },
      "NS_Muzzle": {
        "renderer": "sprite",
        "fixed_bounds": true,
        "pooled": true,
        "effect_type": "cosmetic"
      },
      "NS_Puff": {
        "renderer": "sprite",
        "fixed_bounds": true,
        "pooled": true,
        "effect_type": "cosmetic"
      },
      "NS_WindLines": {
        "renderer": "sprite",
        "fixed_bounds": true,
        "pooled": true,
        "effect_type": "gameplay"
      },
      "NS_TearPop": {
        "renderer": "sprite",
        "fixed_bounds": true,
        "pooled": true,
        "effect_type": "cosmetic"
      },
      "NS_HurtBurst": {
        "renderer": "sprite",
        "fixed_bounds": true,
        "pooled": true,
        "effect_type": "cosmetic"
      },
      "NS_Departure": {
        "renderer": "sprite",
        "fixed_bounds": true,
        "pooled": false,
        "effect_type": "cosmetic"
      },
      "NS_OwlCrack": {
        "renderer": "sprite",
        "fixed_bounds": true,
        "pooled": false,
        "effect_type": "cosmetic"
      }
    }
  },
  "events": [
    {
      "id": "umbrella_open",
      "kind": "state",
      "gdd": "§4",
      "mvp": true,
      "flag": "bOpenFeel",
      "cues": [
        {
          "rank": 1,
          "kind": "sound",
          "flag": "bOpenSound",
          "power": 1.0,
          "asset": "SFX_UmbrellaOpen",
          "pitch_jitter_pct": 5
        },
        {
          "rank": 1,
          "kind": "squash",
          "flag": "bOpenSquash",
          "power": 1.0,
          "scale": [
            1.2,
            0.85
          ],
          "recover_s": 0.2,
          "ease": "ease_out_back",
          "target": "render_only"
        },
        {
          "rank": 2,
          "kind": "pose",
          "flag": "bOpenPose",
          "power": 1.0,
          "frames": 2
        },
        {
          "rank": 3,
          "kind": "particles",
          "flag": "bOpenPuff",
          "power": 1.0,
          "system": "NS_Puff",
          "count": 4
        }
      ]
    },
    {
      "id": "umbrella_close",
      "kind": "state",
      "gdd": "§4",
      "mvp": true,
      "flag": "bCloseFeel",
      "cues": [
        {
          "rank": 1,
          "kind": "sound",
          "flag": "bCloseSound",
          "power": 1.0,
          "asset": "SFX_UmbrellaClose",
          "pitch_jitter_pct": 5
        },
        {
          "rank": 1,
          "kind": "squash",
          "flag": "bCloseSquash",
          "power": 1.0,
          "scale": [
            0.8,
            1.2
          ],
          "recover_s": 0.15,
          "ease": "ease_out_quad",
          "target": "render_only",
          "scale_by": "fall_speed"
        },
        {
          "rank": 2,
          "kind": "pose",
          "flag": "bClosePose",
          "power": 1.0,
          "frames": 2
        }
      ]
    },
    {
      "id": "gust_catch",
      "kind": "state",
      "gdd": "GDD SH1.0 OWL-07 WIND-01 (WindEntered)",
      "mvp": true,
      "flag": "bGustFeel",
      "cues": [
        {
          "rank": 1,
          "kind": "sound",
          "flag": "bGustSound",
          "power": 1.0,
          "asset": "SFX_GustCatch",
          "pitch_jitter_pct": 5
        },
        {
          "rank": 1,
          "kind": "particles",
          "flag": "bGustLines",
          "power": 1.0,
          "system": "NS_WindLines",
          "count": 8
        },
        {
          "rank": 2,
          "kind": "squash",
          "flag": "bGustSquash",
          "power": 1.0,
          "scale": [
            0.85,
            1.15
          ],
          "recover_s": 0.2,
          "ease": "ease_out_quad",
          "target": "render_only"
        }
      ]
    },
    {
      "id": "bolt_fire",
      "kind": "fire",
      "gdd": "§5",
      "mvp": true,
      "flag": "bBoltFireFeel",
      "applies_if": "any_fire_mode",
      "cues": [
        {
          "rank": 1,
          "kind": "sound",
          "flag": "bBoltFireSound",
          "power": 1.0,
          "asset": "SFX_WandBolt",
          "pitch_jitter_pct": 5
        },
        {
          "rank": 1,
          "kind": "particles",
          "flag": "bBoltMuzzle",
          "power": 1.0,
          "system": "NS_Muzzle",
          "count": 3
        },
        {
          "rank": 3,
          "kind": "nudge",
          "flag": "bBoltKick",
          "power": 1.0,
          "px": 1,
          "direction": "opposite_fire",
          "target": "render_only"
        }
      ]
    },
    {
      "id": "bolt_fire_manual",
      "kind": "fire",
      "gdd": "§5 + open review comment",
      "mvp": false,
      "flag": "bManualFireFeel",
      "applies_if": "manual_fire",
      "cues": [
        {
          "rank": 1,
          "kind": "sound",
          "flag": "bManualFireSound",
          "power": 1.0,
          "asset": "SFX_ChargeRelease",
          "pitch_jitter_pct": 5
        },
        {
          "rank": 1,
          "kind": "particles",
          "flag": "bManualMuzzle",
          "power": 1.0,
          "system": "NS_Muzzle",
          "count": 6
        },
        {
          "rank": 2,
          "kind": "nudge",
          "flag": "bManualKick",
          "power": 1.0,
          "px": 2,
          "direction": "opposite_fire",
          "target": "render_only"
        }
      ]
    },
    {
      "id": "bolt_hit_clock",
      "kind": "owl_hit",
      "gdd": "1.3 §7 (clock-hit visual cue ON, P0)",
      "mvp": true,
      "flag": "bHitClockFeel",
      "cues": [
        {
          "rank": 1,
          "kind": "sound",
          "flag": "bHitClockSound",
          "power": 1.0,
          "asset": "SFX_HitClock",
          "pitch_jitter_pct": 5
        },
        {
          "rank": 1,
          "kind": "particles",
          "flag": "bHitClockSpark",
          "power": 1.0,
          "system": "NS_HitSpark_Clock",
          "count": 8
        },
        {
          "rank": 2,
          "kind": "flash",
          "flag": "bHitClockFlash",
          "power": 1.0,
          "frames": 2,
          "max_rate_hz": 3,
          "target": "owl_clock"
        },
        {
          "rank": 2,
          "kind": "pose",
          "flag": "bHitClockPose",
          "power": 1.0,
          "frames": 3
        },
        {
          "rank": 3,
          "kind": "hitstop",
          "flag": "bHitClockStop",
          "power": 1.0,
          "frames": 3,
          "cooldown_s": 0.5
        }
      ]
    },
    {
      "id": "bolt_hit_wing",
      "kind": "owl_hit",
      "gdd": "SH1.0 OWL-09 (the wings are the phase-1 target)",
      "mvp": true,
      "flag": "bHitWingFeel",
      "cues": [
        {
          "rank": 1,
          "kind": "sound",
          "flag": "bHitWingSound",
          "power": 1.0,
          "asset": "SFX_HitWing",
          "pitch_jitter_pct": 5
        },
        {
          "rank": 1,
          "kind": "particles",
          "flag": "bHitWingSpark",
          "power": 1.0,
          "system": "NS_HitSpark_Wing",
          "count": 6
        },
        {
          "rank": 2,
          "kind": "flash",
          "flag": "bHitWingFlash",
          "power": 1.0,
          "frames": 1,
          "max_rate_hz": 3,
          "target": "owl_wing"
        }
      ]
    },
    {
      "id": "bolt_hit_body",
      "kind": "owl_hit",
      "gdd": "§5",
      "mvp": true,
      "flag": "bHitBodyFeel",
      "cues": [
        {
          "rank": 1,
          "kind": "sound",
          "flag": "bHitBodySound",
          "power": 1.0,
          "asset": "SFX_HitOwl",
          "pitch_jitter_pct": 5
        },
        {
          "rank": 1,
          "kind": "particles",
          "flag": "bHitBodySpark",
          "power": 1.0,
          "system": "NS_HitSpark_Body",
          "count": 4
        },
        {
          "rank": 2,
          "kind": "flash",
          "flag": "bHitBodyFlash",
          "power": 1.0,
          "frames": 1,
          "max_rate_hz": 3,
          "target": "owl_body"
        }
      ]
    },
    {
      "id": "player_hit",
      "kind": "player_hit",
      "gdd": "§7",
      "mvp": true,
      "flag": "bPlayerHitFeel",
      "cues": [
        {
          "rank": 1,
          "kind": "sound",
          "flag": "bPlayerHitSound",
          "power": 1.0,
          "asset": "SFX_PlayerHurt",
          "pitch_jitter_pct": 0
        },
        {
          "rank": 1,
          "kind": "flash",
          "flag": "bPlayerHitFlash",
          "power": 1.0,
          "frames": 1,
          "max_rate_hz": 3,
          "target": "player"
        },
        {
          "rank": 1,
          "kind": "hitstop",
          "flag": "bPlayerHitStop",
          "power": 1.0,
          "frames": 5
        },
        {
          "rank": 2,
          "kind": "shake",
          "flag": "bPlayerHitShake",
          "power": 1.0,
          "duration_s": 0.2,
          "amp_pct_h": 2.5,
          "direction": "away_from_source",
          "decay": "spring"
        },
        {
          "rank": 2,
          "kind": "rumble",
          "flag": "bPlayerHitRumble",
          "power": 0.8,
          "duration_s": 0.2,
          "applies_if": "gamepad"
        },
        {
          "rank": 2,
          "kind": "squash",
          "flag": "bPlayerHitSquash",
          "power": 1.0,
          "scale": [
            1.3,
            0.7
          ],
          "recover_s": 0.25,
          "ease": "ease_out_quad",
          "target": "render_only"
        },
        {
          "rank": 3,
          "kind": "particles",
          "flag": "bPlayerHitBurst",
          "power": 1.0,
          "system": "NS_HurtBurst",
          "count": 6
        }
      ]
    },
    {
      "id": "tier_damaged",
      "kind": "state",
      "gdd": "§4, §8",
      "mvp": false,
      "flag": "bTierDamagedFeel",
      "cues": [
        {
          "rank": 1,
          "kind": "sound",
          "flag": "bTierDamagedSound",
          "power": 1.0,
          "asset": "SFX_UmbrellaTear",
          "pitch_jitter_pct": 0
        },
        {
          "rank": 1,
          "kind": "particles",
          "flag": "bTierDamagedPop",
          "power": 1.0,
          "system": "NS_TearPop",
          "count": 6
        },
        {
          "rank": 2,
          "kind": "tween",
          "flag": "bTierDamagedSwap",
          "power": 1.0,
          "duration_s": 0.15,
          "ease": "ease_out_back"
        }
      ]
    },
    {
      "id": "tier_critical",
      "kind": "state",
      "gdd": "§4, §8",
      "mvp": false,
      "flag": "bTierCriticalFeel",
      "cues": [
        {
          "rank": 1,
          "kind": "sound",
          "flag": "bTierCriticalSound",
          "power": 1.0,
          "asset": "SFX_UmbrellaTear",
          "pitch_jitter_pct": 0
        },
        {
          "rank": 1,
          "kind": "particles",
          "flag": "bTierCriticalPop",
          "power": 1.0,
          "system": "NS_TearPop",
          "count": 10
        },
        {
          "rank": 2,
          "kind": "hitstop",
          "flag": "bTierCriticalStop",
          "power": 1.0,
          "frames": 6
        },
        {
          "rank": 2,
          "kind": "shake",
          "flag": "bTierCriticalShake",
          "power": 1.0,
          "duration_s": 0.15,
          "amp_pct_h": 1.5,
          "direction": "away_from_source",
          "decay": "spring"
        },
        {
          "rank": 2,
          "kind": "rumble",
          "flag": "bTierCriticalRumble",
          "power": 1.0,
          "duration_s": 0.15,
          "applies_if": "gamepad"
        },
        {
          "rank": 3,
          "kind": "tween",
          "flag": "bTierCriticalSwap",
          "power": 1.0,
          "duration_s": 0.15,
          "ease": "ease_out_back"
        }
      ]
    },
    {
      "id": "owl_tell_gust",
      "kind": "tell",
      "gdd": "SH1.0 OWL-15",
      "mvp": true,
      "flag": "bTellGustFeel",
      "telegraph_s": 1.1,
      "cues": [
        {
          "rank": 1,
          "kind": "sound",
          "flag": "bTellGustSound",
          "power": 1.0,
          "asset": "SFX_GustWindup",
          "pitch_jitter_pct": 0
        },
        {
          "rank": 1,
          "kind": "pose",
          "flag": "bTellGustPose",
          "power": 1.0,
          "frames": 3,
          "hold_s": 1.1
        },
        {
          "rank": 2,
          "kind": "particles",
          "flag": "bTellGustLines",
          "power": 1.0,
          "system": "NS_WindLines",
          "count": 12
        }
      ]
    },
    {
      "id": "owl_tell_cast",
      "kind": "tell",
      "gdd": "SH1.0 OWL-21, OWL-24, OWL-26 (mechanism casts, P0)",
      "mvp": true,
      "flag": "bTellCastFeel",
      "telegraph_s": 0.9,
      "cues": [
        {
          "rank": 1,
          "kind": "sound",
          "flag": "bTellCastSound",
          "power": 1.0,
          "asset": "SFX_CastWarning",
          "pitch_jitter_pct": 0
        },
        {
          "rank": 1,
          "kind": "tween",
          "flag": "bTellCastPreview",
          "power": 1.0,
          "duration_s": 0.9,
          "ease": "ease_in_out_sine"
        }
      ]
    },
    {
      "id": "end_trigger",
      "kind": "end",
      "gdd": "§2",
      "mvp": true,
      "flag": "bEndFeel",
      "cues": [
        {
          "rank": 1,
          "kind": "sound",
          "flag": "bEndSound",
          "power": 1.0,
          "asset": "SFX_EndEvent",
          "pitch_jitter_pct": 0
        },
        {
          "rank": 1,
          "kind": "pose",
          "flag": "bEndPose",
          "power": 1.0,
          "frames": 3
        },
        {
          "rank": 2,
          "kind": "hitstop",
          "flag": "bEndStop",
          "power": 1.0,
          "frames": 6
        },
        {
          "rank": 2,
          "kind": "shake",
          "flag": "bEndShake",
          "power": 1.0,
          "duration_s": 0.2,
          "amp_pct_h": 1.0,
          "direction": "toward_owl",
          "decay": "spring"
        },
        {
          "rank": 3,
          "kind": "particles",
          "flag": "bEndDeparture",
          "power": 1.0,
          "system": "NS_Departure",
          "count": 24
        }
      ]
    },
    {
      "id": "owl_condition_step",
      "kind": "owl_state",
      "gdd": "§5, §8",
      "mvp": false,
      "flag": "bOwlConditionFeel",
      "note": "Clock and wing hits add up. Every hits_per_step hits on a part, that part's overlay steps up once and stays. Shows condition, not a countdown and not owl health. [proposed]",
      "hits_per_step": {
        "clock": 4,
        "wing": 4
      },
      "cues": [
        {
          "rank": 1,
          "kind": "sound",
          "flag": "bOwlConditionSound",
          "power": 1.0,
          "asset": "SFX_OwlGearSlip",
          "pitch_jitter_pct": 0
        },
        {
          "rank": 1,
          "kind": "overlay",
          "flag": "bOwlClockCrack",
          "power": 1.0,
          "part": "clock",
          "steps": 3,
          "persist": true,
          "ease": "ease_out_back"
        },
        {
          "rank": 1,
          "kind": "overlay",
          "flag": "bOwlWingHoles",
          "power": 1.0,
          "part": "wing",
          "steps": 3,
          "persist": true,
          "ease": "ease_out_back"
        },
        {
          "rank": 2,
          "kind": "tween",
          "flag": "bOwlClockStutter",
          "power": 1.0,
          "duration_s": 0.2,
          "ease": "ease_out_back"
        },
        {
          "rank": 3,
          "kind": "particles",
          "flag": "bOwlCrackDust",
          "power": 1.0,
          "system": "NS_OwlCrack",
          "count": 6
        }
      ]
    },
    {
      "id": "shield_catch",
      "kind": "state",
      "gdd": "GDD SH1.0 SURV-05, FLOW-33, §7A DEF-01 (CatchSucceeded; plays during the heal cooldown too)",
      "mvp": true,
      "flag": "bShieldCatchFeel",
      "cues": [
        {
          "rank": 1,
          "kind": "sound",
          "flag": "bShieldCatchSound",
          "power": 1.0,
          "asset": "SFX_ShieldCatch",
          "pitch_jitter_pct": 5
        },
        {
          "rank": 1,
          "kind": "flash",
          "flag": "bShieldCatchFlash",
          "power": 1.0,
          "frames": 2,
          "max_rate_hz": 3,
          "target": "player"
        },
        {
          "rank": 3,
          "kind": "particles",
          "flag": "bShieldCatchSpark",
          "power": 1.0,
          "system": "NS_Puff",
          "count": 4
        }
      ]
    },
    {
      "id": "shield_heal",
      "kind": "state",
      "gdd": "GDD SH1.0 SURV-05, FLOW-33 SURV-03 (heal 20 HP applied; not during the 2 s cooldown)",
      "mvp": true,
      "flag": "bShieldHealFeel",
      "cues": [
        {
          "rank": 1,
          "kind": "sound",
          "flag": "bShieldHealSound",
          "power": 1.0,
          "asset": "SFX_ShieldHeal",
          "pitch_jitter_pct": 0
        },
        {
          "rank": 1,
          "kind": "tween",
          "flag": "bShieldHealSwap",
          "power": 1.0,
          "duration_s": 0.15,
          "ease": "ease_out_back"
        }
      ]
    }
  ]
}
```

### `pipeline/feel/hitboxes.json`

```json
{
  "_about": "Collider data, one shape per gameplay sprite, in sprite pixels (origin top-left of the frame, y down). Owner: Gameplay Dev. GDD 1.3 7C: colliders are independently defined gameplay data and the art aligns to them; no tool writes this file. A change here is a separate feature/config change with adjacent regressions and Richard's approval (a human-only needs-human). The player hurtbox and the bolt collider name their tuning value (\"fixed\": pipeline/feel/feel.json forgiveness) and must equal it. tools/hitbox_check.py check fails when the art (after its visual-only scale and offset in pipeline/art/visual-align.json) misses a collider, or the art changed since it was aligned; `hitbox_check.py fit <id>` moves only the art. UmbrellaElla.Feel.Hitboxes (pipeline/qa/test-map.md) checks the engine's collision equals this file. Limits are [proposed] starting values, set from the feel.json forgiveness ratios (collider / visible art box: player 0.6, projectile 0.8); change one only with a playtest note or a measurement, written in the commit message.",
  "alpha_solid": 128,
  "roles": {
    "player": {
      "coverage_min": 0.3,
      "coverage_max": 0.8,
      "spill_max": 0.1,
      "inset_px": 3,
      "_why": "Fairness: Ella's hurtbox (player_hurtbox_ratio 0.6 of her art box) sits inside her art, so a graze on the edge never hurts. Never bigger than the art."
    },
    "hazard": {
      "coverage_min": 0.45,
      "coverage_max": 0.95,
      "spill_max": 0.1,
      "inset_px": 1,
      "_why": "A bolt (projectile_hitbox_ratio 0.8) hurts only where you can see it. A little smaller than the art is fair."
    },
    "target": {
      "coverage_min": 0.7,
      "coverage_max": 1.0,
      "spill_max": 0.2,
      "inset_px": 0,
      "_why": "The owl BODY and CLOCK targets (OWL-05): the art sits on its collider, so a shot that looks like a hit is one."
    }
  },
  "entities": []
}
```

## Logs

### `pipeline/feel/ab-log.csv`

```csv
date,build_sha,event,flag,on_note,off_note,verdict,signed_by
```

### `pipeline/feel/arena-log.csv`

```csv
date,gate,build_sha,map,patterns,cues_on,note,played_by
```

### `pipeline/feel/latency-log.csv`

```csv
date,gate,build_sha,host,method,presses,median_ms,worst_ms,measured_by,peak_bolts,peak_frame_ms
```

## Commands and checks

### `tools/feel_check.py`

Usage text from the file:

```text
Feel gate for THE LAST HOUR. Stdlib only; runs locally and in CI.

Checks pipeline/feel/feel.json (the data the DA_Feel asset is made from) against the
limits in docs/feel-spec.md, and its GDD 1.3 section 5A numbers against the approved start values in
docs/feature-manifest.json approved_parameters (manifest_check.py holds the manifest to the GDD tables).
The limits live in this file and the manifest, not in feel.json, so tuning the data cannot loosen the gate.

Usage:
  python3 tools/feel_check.py                      check feel.json
  python3 tools/feel_check.py --fields             print the DA_Feel fields (one bool + one power per cue)
  python3 tools/feel_check.py --ab FLAG            the A/B log has a signed on/off row for FLAG
  python3 tools/feel_check.py --gate G2 --build SHA  the latency log has a 240 fps row and a peak frame time for this gate and build
  python3 tools/feel_check.py --test-map           every engine test named in docs/feel-spec.md has a (world) row in pipeline/qa/test-map.md
  python3 tools/feel_check.py --test-map-rows      print the planned test-map rows to paste
  python3 tools/feel_check.py --arena              the arena log has a signed L_Graybox run (also run by --gate G2..G4)
Exit 0 = clean, 1 = problems found.
```

Run in CI by:

- `.github/workflows/pipeline-checks.yml`: Feel data limits (Game Designer)

Tests: `tests/test_feel_check.py`, `tests/test_pipeline_check.py`, `tests/test_tuning.py`

### `tools/hitbox_check.py`

Usage text from the file:

```text
Hitbox-vs-art alignment check. Stdlib only. Colliders are gameplay data; the art aligns to them.

GDD 1.3 section 7C, Fairness and calibration: "Replaced graphics must remain visually aligned with the independently
defined gameplay collider and muzzle/catch anchors. When art and gameplay geometry visibly disagree, first adjust
visual-only scale, pivot or offset. If actual hitbox or physics changes are needed for fairness, log a separate
feature/configuration change, run adjacent gameplay regressions, and obtain Richard approval. Never silently resize
collisions to an atlas or damage mask."

Two files:
  pipeline/feel/hitboxes.json     collider data (Gameplay Dev). One shape per gameplay sprite: Ella's hurtbox, bolts,
                                  the owl BODY and CLOCK targets. The player hurtbox and the bolt collider also name
                                  their tuning value ("fixed": pipeline/feel/feel.json forgiveness, the mirror of the
                                  *Tuning.h values) and must equal it. No tool writes this file; a change is a separate
                                  approved change (Richard).
  pipeline/art/visual-align.json  the art's visual-only scale and offset per entity, and the SHA-256 of the art it was
                                  aligned on. `fit` writes it. The game applies it to the sprite component only.

The check measures each sprite's alpha mask (PNG, after its visual scale and offset) against the collider:
  coverage  opaque art pixels inside the collider / all opaque art pixels
  spill     collider pixels with no opaque art under them / all collider pixels
Opaque = alpha >= "alpha_solid". Limits per role ("roles" in hitboxes.json; per entity with an override_reason):
  player  the hurtbox sits inside the art (a graze never hurts), never bigger: coverage_max < 1
  hazard  bolts: a little smaller than the art is fair
  target  owl body and clock: close to the art
With several frames, the worst frame decides. New art (a hash that differs from visual-align.json) fails until `fit`
re-aligns it, so an art swap waits for a PASS.

Commands:
  check [--root R] [--fail-lfs-pointer] [--require] [--json]   exit 1 on any misalignment, a stale or missing
        alignment, a collider that is not its tuning value, a missing sprite or a silhouette sidecar without a hitbox
  fit ID [--root R]   the lane agent's own fix when check fails (no human): searches a visual-only scale (0.5x-2x)
        and the offset that centres the art on the collider, keeps the one whose worst frame lands nearest the middle
        of the role limits, writes it to visual-align.json, and re-runs check. It never writes collider data. When no
        visual-only change reaches the limits it prints `NEEDS HUMAN: Richard hitbox change request ...` with a traced
        shape as a suggestion for Richard, and exits 3. That call is human-only: no grace default
  suggest SPRITE --role R [--frame x,y,w,h] [--inset PX] [--max-points N]   prints a polygon traced from the alpha mask,
        for a hitbox change request. Suggestion only: nothing is written
  lfs-include   comma list of the sprite paths, for `git lfs pull --include` in CI
A .sprite.json sidecar of kind "silhouette" under Art/ names its entity ("hitbox": "<id>") or says
"hitbox": "none" with a "hitbox_reason".

Exit 0 = pass (or nothing to check), 1 = fail, 2 = usage or input error, 3 = needs Richard (hitbox change request).
Last line: `hitbox_check: PASS entities=<n> ...` or `hitbox_check: FAIL <n> problem(s)`.
```

Run in CI by:

- `.github/workflows/pipeline-checks.yml`: Hitboxes fit the art (Gameplay Dev; required). Pulls every sprite named in pipeline/feel/hitboxes.json, so a stale shape or an art swap without a re-fit fails

Tests: `tests/test_hitbox_check.py`, `tests/test_pipeline_check.py`
