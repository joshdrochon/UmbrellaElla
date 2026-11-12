# Feel spec: THE LAST HOUR

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

## 1. Toggles and A/B: the core rule
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

## 2. Events and cues (ranked)
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

## 3. Hit-stop
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

## 4. Screen shake
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

## 5. Squash and stretch
- Peak change 10–40% on one axis. Recovery ≤ 0.25 s (Celeste jump stretch recovers in 0.23 s [sourced]).
- Render-only: a scale tween on the sprite component, driven by `DA_Feel`. Collision never changes size.
- Close squash scales with fall speed at the moment of closing (Celeste landing squash scales by fall speed / 240 [sourced]).
  `scale_by` is `none` (default) or `fall_speed`; the gate rejects anything else. With `fall_speed`, the deviation from 1 is
  multiplied by `min(v / max_fall, 1)`, where `max_fall` = the natural max fall (`max_fall_speed`). There is no fast fall (GDD SH1.0 rule numbers (section 9 ranges blank, D-new-sh10-param-ranges)).
- Test [VERIFY]: `UmbrellaElla.Feel.SquashCurve` logs sprite RelativeScale3D each tick. Pass: peak within ±0.03, back to 1 by spec time ±2 frames, capsule size unchanged.
- Boundary test [VERIFY]: `UmbrellaElla.Feel.SquashScalesWithFallSpeed` closes at 50% and 100% of max fall. Pass: the peak deviations are
  0.5× and 1× the `feel.json` deviation, each ±0.03.

## 6. Responsiveness and latency
| Rule | Target | Fail | How measured | Owner |
|---|---|---|---|---|
| Input → velocity change (game side) | same tick (0 f) | > 1 f | `UmbrellaElla.Feel.InputSameTick` [VERIFY]: inject the toggle through Enhanced Input at tick N, read velocity | Gameplay Dev |
| Input → first visible change | ≤ 1 f | > 1 f | same test, read sprite scale or flipbook | Gameplay Dev |
| Key press → photon | ≤ 67 ms | > 100 ms | 240 fps phone video of key and screen, ≥ 10 presses, median | QA and Build |

- Physics changes on frame 1 of the toggle. A pose may play over ≤ 3 frames; it never delays physics. No anticipation on player verbs.
- Bind the toggle on `Started`/`Pressed`, never `Hold` or `Released`.
- Done when, per gate build: `python3 tools/feel_check.py --gate G<n> --build <sha>` exits 0 (a `latency-log.csv` row with method "240 fps", ≥ 10 presses, median ≤ 100 ms, `measured_by` filled). Over 67 ms passes with a note and a TD card.
  `--build` must be a 7–40 character hex sha. It matches a row when one sha is a prefix of the other.

## 7. Movement (GDD SH1.0 rule numbers (section 9 ranges blank, D-new-sh10-param-ranges))
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

## 8. Forgiveness (defaults, written as rules)
These are sensible defaults, not open decisions. Change them only with a playtest row.
- Toggle buffer 0.1 s (range 0.07–0.13): a press during hit-stop, hit-stun or a tear animation applies on the first free frame. Test [VERIFY] `UmbrellaElla.Feel.ToggleBuffer`: press 6 f before the lock ends → applies; 8 f before → ignored.
- Gameplay collision is fixed data, never read from sprite size, alpha, atlas or pose (GDD SH1.0 ANIM-02, §7C). `feel.json` `forgiveness.player_hurtbox_cm` (52.8 × 79.9 cm) and `bolt_hitbox_radius_cm` (12 cm) are the `*Tuning.h` collider values. Swapping art never changes them.
- Alignment targets, art against collider: the player collider covers 60% of the body art box (50–65%; canopy, hair and wand stay outside it); the owl bolt collider is 80% of its bright core (70–85%; the glow never counts). When new art misses them, change the art's scale, pivot or offset. A collider change is a separate approved change with its own regressions (GDD SH1.0 CORE-05).
- Post-hit invulnerability 0.8 s (GDD SH1.0 SURV-05, FLOW-33; `feel_check.py` fails any other value), shown by an alpha pulse ≤ 3 per second.
- Arena-bound nudge: touching a top or side bound by ≤ 4 px slides the player along it instead of stopping.
- Test [VERIFY] `UmbrellaElla.Feel.Hitboxes`: the live collider sizes equal `player_hurtbox_cm` and `bolt_hitbox_radius_cm` with any art set loaded (swap the art, sizes unchanged); a separate alignment check reports the collider / art-box share against the targets above. It never resizes the collider.
  Nudge case: move the player up into the top bound, offset 3 px sideways from a corner; assert it slides along the bound, not stops.

## 8b. Threat spacing
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

## 9. Niagara rules
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

## 10. Easing and tweens
- Every tween uses a named curve from `CF_FeelEase` (`ease_out_quad`, `ease_out_back`, `ease_in_out_sine`, `spring`). Never linear.
- Checked only in `feel.json`. No engine test reads the curves on the real timelines; the Dev Lead review checks each new
  timeline or tween call names a `CF_FeelEase` curve.
- One exception: clock-hand rotation is linear.
- Tier change: one tear-pop burst, one sound and a short texture swap tween. Never a silent swap.

## 11. Who does what
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

## 12. When (feel from day one)
- **Day-0 card 0.13** (Gameplay Dev, test lane only): `FeelEnvelope` passes and `encounter_check.py --envelope` exits 0 on its line.
- **Feel card** (Gameplay Dev, filed by the Producer after G1): make `DA_Feel` from `feel_check.py --fields`, with the cvars (§1.5);
  wire the rank-1 cues of the 7 `mvp: true` events with placeholder sound and sprite. It owns the Feel rows of `pipeline/qa/test-map.md`.
  Done when `HitStopFrames` passes (output pasted), its test-map rows are `merged`, and `L_Graybox` is played with the cues on (`--arena` exits 0).
- **G1 → G2**: one A/B row per `mvp: true` event (§1.3). Other events get rows as their cards land.
- **Every gate**: QA and Build runs `--gate G<n> --build <sha>`.
