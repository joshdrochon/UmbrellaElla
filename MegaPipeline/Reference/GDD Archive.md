> Generated from `docs/gdd/GDD-1.3.md`, `docs/gdd/GDD-B1.0.md`, `docs/gdd/archive/gdd-umbrella-ella-draft1.0.md` at `fbcd307` — edit the sources, not this file.
> Rebuild: `python3 tools/export_package.py`. Check: `python3 tools/export_package.py --check`.

---

<!-- source: docs/gdd/GDD-1.3.md -->

# GDD snapshot 1.3 (read-only)

| Field | Value |
|---|---|
| Revision | 1.3 |
| Title | UMBRELLA / OWL, GameDesignDocument.pdf (gameplay and pipeline specification) |
| Date | 8 November 2026 (Review Candidate 1.3, Richard-approved baseline) |
| Authors | Richard (design owner and document approver, section 14); Josh (pipeline / AI lead) |
| Source | `GameDesignDocument.pdf` on `origin/main`, commit `73b6a93` ("publish GameDesignDocument v1.3 with replaceable art contracts"). Same PDF bytes as `03ee884` on `origin/docs/gdd-1.3-replaceable-art`. |
| Previous snapshot | `docs/gdd/GDD-B1.0.md` (commit `d716fae`). Revisions 1.1 and 1.2 never reached this repo; 1.2 is summarized in Appendix D. |
| Converted | 2026-11-09, `pdftotext -layout` of the PDF. Tables became Markdown tables; bullets became `-`; page headers and footers ("TEAM REVIEW • 08 NOV 2026 \| PAGE n") were dropped. List numbers are kept as printed (the PDF numbers its lists 5-10, 11-15, 16-22). Two edits to the printed words, for repo checks only: one teammate's first name is written as "the design reviewer" (private-name check), and two slash phrases are spaced ("pipeline / AI lead", "pipeline / tooling tests") so the path check does not read them as paths. |
| Printed status line | The cover says "REVIEW CANDIDATE 1.3 \| Richard-approved baseline \| 8 November 2026 \| Not yet merged to GitHub". The design owner merged it to `origin/main` in `73b6a93`; section 14 makes the PDF in GitHub authoritative after upload. See `docs/gdd/questions-1.3.md` Q1. |
| Change rule (commit message) | "Future changes must increment the document version and add dated revision notes." |

Never edit this file. A new revision is a new file `docs/gdd/GDD-<rev>.md` plus a one-line change to `docs/gdd/CURRENT`
(`docs/gdd/README.md`). Where this text and `docs/feature-manifest.json` disagree on status, this text wins until the manifest is corrected (source-of-truth priority 1 is the approved GitHub PDF, including its feature manifest).

---

UMBRELLA / OWL
GameDesignDocument.pdf | Gameplay and pipeline specification
REVIEW CANDIDATE 1.3 | Richard-approved baseline | 8 November 2026 | Not yet merged to GitHub

Working source of truth for the four-day 2026 Epic AI MegaJam. Revision 1.3 updates the approved gameplay
baseline with explicit placeholder-art and asset-swap boundaries, while preserving modular mechanics, tuning
controls, test requirements and the release-first schedule. All initial art, animation sheets, UI ornament and
background illustrations are replaceable presentation assets, not locked design choices. Narrative remains deferred.

PRIMARY OBJECTIVE Ship a complete, clear, polished and submitted 90-second aerial survival encounter in the
four-day window. Permit controlled experiments in development builds, but do not allow optional mechanics to
endanger shipping the baseline.

## A. Interpretation contract (read before generating any files)

| Term | Agent interpretation |
|---|---|
| CONFIRMED | Gameplay intent chosen by the team or the user; still require scope assignment before implementation. |
| APPROVED_P0 | Required for the current approved playable baseline. Build only after the official jam start. |
| APPROVED_P1 | Approved next candidate, only after P0 works and the owner releases it. |
| PROPOSED | Documented possibility with no implementation authority. |
| EXPERIMENT | Requires a contained implementation ticket, test scenario, and acceptance measure. |
| DEFERRED | Do not implement. Keep as idea/reference. |
| OPEN | No decision. Preserve the interface, log the question; no irreversible assumption. |
| REJECTED | Known excluded behavior; do not revive without explicit decision. |

Priority and approval are separate axes. Richard (document/design owner) approved the P0 behavior and
provisional numerical defaults on 8 November 2026. This file is a review candidate; only a subsequently approved
replacement of the GitHub file is authoritative. Josh must consume a named GDD revision and frozen feature
manifest, not infer requirements from Discord history.

Source-of-truth priority
1. Current approved GitHub GameDesignDocument.pdf revision, including its feature manifest and revision log.
2. Explicit APPROVED_P0 gameplay rules and numerical baseline in the same revision.
3. PROPOSED, EXPERIMENTAL and DEFERRED inventory: preserved, not implementation authority.
4. Meeting notes, historical comments and external AI summaries: supporting evidence only; cannot override
   approved rules.

## 1. One-page game definition

| Attribute | Definition |
|---|---|
| Fantasy | A small airborne character manipulates an umbrella to survive a powerful clockwork owl. Player skill centers on movement, timing and positioning. |
| Player goal | Remain alive until the owl departs. Do not require a boss kill. |
| Failure | Player health depleted OR player crosses bottom defeat boundary. |
| World | Single 2D collision plane, landscape fixed-camera single-screen arena. Two repeatable background art layers may slide independently to imply travel; this never moves the gameplay camera or player hitboxes. |
| Inputs | Horizontal steering always available. Default open/upright; hold ATTACK to descend and auto-fire; hold SHIELD to descend and absorb. Shield wins simultaneous input. Keyboard + controller, PC only. |
| Core input rule | Only open-and-upright umbrella generates active ascent. Otherwise player falls naturally, modified only by physics/environmental forces. No "fast-fall" state. |
| Attacks | Automatic straight-forward shots while ATTACK_DESCENT is held. The owl is on the right in baseline, so default firing is world +X; no independent aiming or firing-angle input. Opening/shielding stops new shots. |
| Opponent | One owl with one readable telegraphed bolt attack. Owl BODY and CLOCK are distinct target hitboxes, with clock special effects OFF in baseline. |
| Tone | Gothic storybook / clockwork; no narrative prerequisite. |
| Platform | Windows first, keyboard and controller targeted; mobile/touch not first-build scope. |
| Engine | Team target UE 5.8.4, technical compatibility to be verified. |
| Outcome | Survive 90 seconds (provisional tunable) then see owl depart, with a distinct survived screen. Health zero or bottom boundary produces defeat; retry works. |

Design constraints
- The interesting action is navigating danger through umbrella orientation and altitude, not memorizing a long attack combo.
- No mechanic may make defeat unavoidable without a visible warning or reasonable response window.
- Experimental systems should be isolated by component and configuration boundary wherever practical.
- A config toggle is not the same as hot-swappable physics. Mechanics with incompatible state may require a scene reset.
- Do not include story-specific assumptions in win logic, clock logic, boss AI, asset naming or state ownership.

## 2. Approved intent versus candidate mechanics

| Rule ID | Behavior | Decision |
|---|---|---|
| CORE-01 | Regular horizontal steering is always enabled in the initial build; wind/dash-only variants are optional. | APPROVED_P0 |
| CORE-02 | Unassisted natural falling uses one gravity rule whenever upright-open lift is unavailable; fast-fall extra acceleration OFF. | APPROVED_P0 |
| UMB-01 | Open and upright umbrella provides upward ascent even without wind; default configuration on release of attack/shield. | APPROVED_P0 |
| CORE-03 | Single health resource, visible umbrella wear; health 0 or bottom crossing causes defeat. | APPROVED_P0 |
| END-01 | Survive 90 seconds (tunable prototype default); owl departs; owl cannot be killed in baseline. | APPROVED_P0 |
| COM-01 | Hold ATTACK -> ATTACK_DESCENT -> automatic forward (+X) shots every 0.65s; stops new shots on exit. | APPROVED_P0 |
| UMB-02 | Closed/lowered umbrella is part of required ATTACK_DESCENT; variable aim angles and charged aim remain optional. | APPROVED_P0 for fixed-forward configuration |
| UMB-03 | Independent open-left/open-right catching remains optional; front-facing shield descent is a distinct P0 action. | PROPOSED / OFF |
| UMB-04 | Inversion and forced recovery stay available as a named experiment; not active in baseline. | EXPERIMENT / OFF |
| SURV-02 | Visible damage to umbrella communicates the single health resource; damage does not reduce lift by default. | APPROVED_P0 |
| SURV-03 | Successful front shield absorption blocks the projectile and restores 20 health, cooldown 2s, cap at maximum. | APPROVED_P0 |
| WIND-01 | One readable environmental upward wind zone, on in full baseline; wear disabled. | APPROVED_P0 |
| WIND-02 | Some wind variants may damage umbrella health; requires a visible danger cue and approval. | EXPERIMENT / OFF |
| OWL-01 | One telegraphed, dodgeable bolt pattern with independently configurable warning, interval and travel speed. | APPROVED_P0 |
| OWL-02 | Owl-generated wind attack is separate from environmental wind field. | PROPOSED / OFF |
| OWL-03 | Clock damage disrupting owl attacks and wing damage altering wind are OPTIONAL effects; independent clock/body hitboxes required. | EXPERIMENT / OFF for special effects |
| OWL-04 | Curving or returning owl bolts, clearly telegraphed before arrival. | EXPERIMENT / OFF |
| HAZ-01 | Pipes, steam vents and separate environmental hazard cycles. | EXPERIMENT / OFF |
| FLOW-01 | Title, pause, defeat, survived, restart and deterministic encounter lifecycle. | APPROVED_P0 |
| NAR-01 | Story premise, character history, clockkeeper lore, missing time, stolen clock hand. | DEFERRED / no implementation authority |
| DEF-01 | Hold SHIELD -> SHIELD_DESCENT: natural fall; catches frontal owl bolts, heals one health resource; shield priority. | APPROVED_P0 |
| OWL-05 | Clock has a separate collider from body; target IDs differ; each projectile registers at most one hit. | APPROVED_P0 |
| ANIM-01 | Character core movement uses sprite sheets and event-driven Paper 2D flipbooks; no physics in animation system. | APPROVED_P0 |
| BG-01 | Two seamless, horizontally sliding parallax visual layers under the fixed camera; no world translation. | APPROVED_P0 (visual, safe static fallback) |
| QA-BASE | Development-only toggles, parameters, presets, reset, export and validation; no workbench in shipping build. | APPROVED_P0 pipeline contract |

## 3. Core interaction model

### A. Umbrella configuration and physical effect

| State ID | Definition | Motion / action | Status |
|---|---|---|---|
| UP_OPEN | Default when ATTACK and SHIELD are released. Umbrella open/upright. | Active lift toward ascent speed; regular horizontal steering. No automatic firing. | APPROVED_P0 |
| NO_LIFT | Derived physics condition, not a separate player input or special descent mode. | Gravity-driven fall with ordinary terminal speed; optional external wind influences travel. | APPROVED_P0 |
| ATTACK_DESCENT | ATTACK held and SHIELD not held. Umbrella lowered/closed. | Natural fall; emit automatic shots horizontally to world +X every configured interval. | APPROVED_P0 |
| OPEN_LEFT | Optional manually oriented umbrella catch from left. | Falls normally; direction-filtered catch if UMB-03 becomes approved. | PROPOSED / OFF |
| OPEN_RIGHT | Optional manually oriented umbrella catch from right. | Falls normally; direction-filtered catch if UMB-03 becomes approved. | PROPOSED / OFF |
| INVERTED | Umbrella inverted/disrupted. | Falls until orientation/recovery rule resolves. | EXPERIMENT |
| DEFEATED | Health <= 0 OR player bottom boundary crossed. | Stop motion and combat, clear active interactions, show defeat. | APPROVED_P0 |
| SHIELD_DESCENT | SHIELD held, whether or not ATTACK held. Umbrella defensively oriented toward owl (+X). | Natural fall; no new attack shots; catches frontal projectiles, heals on successful absorption subject to cooldown. | APPROVED_P0 |

State resolution and input precedence
5. While ACTIVE and alive, read regular left/right steering independently of umbrella configuration; horizontal
   acceleration and max speed are tunable.
6. Resolve umbrella state in priority order: failure/success/pause lockout; then SHIELD_DESCENT (if SHIELD held);
   else ATTACK_DESCENT (if ATTACK held); otherwise UP_OPEN. No input-order ambiguity.
7. Apply upward lift only when state is UP_OPEN and umbrella is functional; input release defaults to UP_OPEN
   and active lift.
8. In every other configuration, normal gravity continues. Wind/external impulses may still change actual velocity;
   they do not create a faster-falling mode.
9. Only ATTACK_DESCENT emits new player shots; only SHIELD_DESCENT can catch frontal projectiles in baseline.
   Side catch OPEN_LEFT/OPEN_RIGHT is separately disabled. Every projectile may generate at most one contact
   outcome.
10. If the player is defeated or encounter is ended, apply the configured stop/control transitions; do not leave stale
    attack or collision events active.

Critical invariant: the lowered/closed umbrella never applies an automatic fast-fall multiplier. Fast-fall is an isolated
optional acceleration modifier, OFF in approved baseline. State transitions do not modify gravity.

## 4. System boundaries and contracts

| Module | Owns | Must not own |
|---|---|---|
| Input Adapter | Read keyboard/controller states, hold behavior and configurable mappings; produce requested actions. | No physics or attack timings. |
| Player Motor | Horizontal motion, gravity, lift forces, collisions, bounds. | Healing, owl phase selection, narrative. |
| Umbrella State | Open/closed/orientation/disrupted state and state transitions. | Movement physics details or projectile spawn rules. |
| Attack Emitter | Fire fixed-forward (+X) player bolts on attack-descent intervals; start/stop emitter and own cooldown. | No owl condition changes or outcome authority. |
| Defense Receiver | Detect frontal owl projectile catches while shield descent active; consume one shot and emit CatchSucceeded. | No health mutations; Health/Condition owns the heal and cooldown. |
| Health/Condition | Own exactly one player HP value, damage, invulnerability, absorption healing/cooldown and health->visual stages. | No lift changes unless optional SURV-04 enabled; no boss phase logic. |
| Projectile Service | Projectile spawn, motion, telegraph, collision reporting, lifetime. | Pacing logic or individual actor storyline. |
| Boss Director | Owl attack schedule and telegraphs, return hit-region messages and departure pose. | No collision routing, player HP, camera, or encounter timer. |
| Wind/Hazard Field | Forces and hazard zones, warning indicators, optional wear events. | Player state authority. |
| Encounter Director | Start/pause/restart, single 90-second elapsed-active timer, survival/defeat results and clean cleanup. | No owl animation details or player projectile damage. |
| Feedback Adapter | Map states/events to sprite flipbook, audio, damage flashes, clock-hit and background visual cues. | No gameplay state authority or collision resolutions. |
| Test Harness | Own dev-only preset loading, switch statuses, slider edits, scenario reset, logs and export. | No runtime shipping menu, no direct undocumented mutations of combat actors. |
| Hit Region Router | Own two distinct owl target regions: CLOCK and BODY; resolve overlap by clock priority; issue BossTargetHit once. | No clock interrupt behavior, boss damage outcome, or player health. |
| Animation Presenter | Read resolved actor/action states and select Paper 2D Flipbook with stable sprite pivot and layers. | No collision boxes, player velocity, attack cadence, or authority over state transitions. |
| Background Presenter | Scroll/wrap far and near visual layers independently behind fixed camera; expose motion rates and enable flag. | No gameplay camera motion, level translation, hitboxes, wind, or hazards. |

Required event vocabulary
Required semantic events (concrete Blueprint names may vary only if mapped in the manifest):
UmbrellaConfigChanged, PlayerHealthChanged, ProjectileSpawned, ProjectileContact, CatchSucceeded, CatchFailed,
BossTargetHit(region=CLOCK|BODY), BossAttackTelegraphed, WindEntered, WindExited, PlayerDefeated,
EncounterCompleted, AnimationCue, BackgroundLooped, TestPresetLoaded. For each: timestamp/frame, source,
target, run ID, and relevant feature IDs. TargetHit must fire once per projectile even if target colliders overlap.

Event contracts and failure modes
- Every module documents required inputs, emitted events, editable parameters, side effects, dependencies and
  safe disable behavior. Rehearsal-informed interface check: specify units/coordinate space, state ownership,
  whether changes are immediate or require reset, and exactly one owner for saving each configuration key.
- No circular hard dependency between player motor, health system and boss director. Communication may use
  shared events/interfaces. A useful reference split in the rehearsal is visual-only boss presentation versus
  encounter-rule ownership, and environmental currents versus forced owl gusts; preserve that separation, not
  the rehearsal class layout.
- A disabled optional module must leave basic movement, health, defeat, restart and encounter progression
  functional.
- Parameter changes should load at scenario restart by default unless the module explicitly supports safe runtime
  changes. Rehearsal evidence suggests that category-owned Save/Discard and named presets reduce tester
  confusion; P0 may use a simpler UI with equivalent persistence and explicit applied/unsaved status.
- Unknown events and missing assets should produce a logged fallback, not an invisible hard crash. Record any
  sprite-grid or attachment-metadata mismatch as an asset-validation error with a visible placeholder rather than
  silently offsetting collision or muzzle coordinates.

## 5. Feature manifest and option ownership

Recommended canonical feature record fields: feature_id, name, status, owner, priority, default_enabled,
dependencies, conflicts, parameters, required_events, tests, implementation_commit, known_limitations. Track
changes to statuses rather than changing prose silently. Parameter fields must also carry units, numeric type, initial
value, min/max, step, live-safe/reset-required flag and who owns persistence. This resembles the rehearsal
GameplayTuning catalog; do not copy its different numeric defaults.

| ID | Feature / default for proposed test build | Dependencies | Isolation |
|---|---|---|---|
| UMB-02 | Fixed-forward attack descent / ON | Umbrella state, COM-01 | P0; hold attack |
| UMB-03 | Independent left/right catch / OFF | DEF-01, directional state and projectile contact | Optional; reset to activate |
| UMB-04 | Wind inversion / OFF | Wind field, umbrella config | Experiment; reset |
| COM-01 | Automatic forward shots / ON (0.65 sec interval) | ATTACK_DESCENT, player attack emitter | P0; dev scenario may override |
| COM-02 | Clock interrupts active owl attack / OFF | OWL-05 clock hit router + boss director | Experiment; reset |
| COM-03 | Wing target changes future wind / OFF | Optional wing hitbox + wind director | Experiment; reset |
| COM-04 | Special body-hit consequences / OFF; normal hit feedback ON | OWL-05 router + feedback adapter | Experiment; reset |
| SURV-04 | Umbrella damage reduces lift / OFF | Health/Condition + Player Motor | Experiment; reset |
| SURV-03 | Absorption healing / ON (20 HP, 2-sec cooldown) | DEF-01, health resource | P0; dev scenario may override |
| WIND-01 | One safe upward environmental wind current / ON in full baseline | Wind field + Player Motor | P0; OFF in movement-only test |
| WIND-02 | Wind wear / OFF | WIND-01 + health resource | Experiment; reset |
| OWL-02 | Owl wing gust / OFF | Wind field + Boss Director | Experiment; reset |
| OWL-04 | Returning bolt / OFF | Projectile service + path config | Experiment; reset |
| HAZ-01 | Steam vent / OFF | Hazard field + warning cue | Experiment; reset |
| VFX-01 | Dynamic background pressure motif / OFF | Background presenter + Encounter Director | Optional; reset |
| DEF-01 | Front shield descent and catch / ON | Umbrella state, Projectile Service, Health | P0; dev override |
| OWL-05 | CLOCK vs BODY separate gameplay hit regions / ON; independent of art masks, layer order and damage sprites. Special clock effects remain OFF. | Owl actor, Hit Region Router | P0; no clock special effect |
| ANIM-01 | State-driven character animation / ON. Accept provisional sheets or minimal visible placeholders until approved art is supplied; asset swap must not change physics or collision. | Animation Presenter, action states | P0; static fallback only during integration |
| BG-01 | Fixed-camera background layer movement / ON. Source textures are provisional and replaceable; neutral-color tiling fallback if artwork is missing. | Background Presenter, 2 tiling layers | P0 visual; fallback to static if asset fails |
| CAM-02 | Actual camera/world scrolling / OFF | Camera module, arena boundary logic | Experiment; reset |
| MOVE-02 | Additional fast-fall acceleration / OFF | Player Motor | Experiment; reset |
| MOVE-03 | Wind-only steering and falling dash / OFF | Input adapter, Player Motor | Experiment; reset |
| ART-02 | Developer art-set selection / OFF. Art mappings remain replaceable even when the menu is absent. This compares candidate sprite families or background looks without gameplay changes. | Feedback Adapter, Animation Presenter, visual asset map; validated candidate asset sets | Optional debug capability; never changes hitboxes, physics, projectile spawn or game rules |

Manifest invariants: APPROVED_P0 features are ON in the full gameplay preset and implemented after jam start.
Experiments are OFF until approved. A listed toggle with implementation_state=NOT_BUILT must be visibly
unavailable, not a false promise that the mechanic exists. Input actions and selected preset have explicit owners. No
AI may invent a default, tune a parameter or silently enable an experiment.

Feature lifecycle
11. Propose with rationale and expected player decision.
12. Approve a bounded experiment plus test owner and pass/fail criterion.
13. Generate feature implementation in an isolated branch or component.
14. Run automated checks and an independent human A/B test.
15. Promote to APPROVED_P1/P0, revise, disable or defer; log what changed and why.

## 5A. Approved starting parameters and test presets

All defaults below were approved by Richard as provisional tuning, not as balanced values. The slider must show
unit and actual value, stay within range, use stated step, and apply on scenario reset unless marked live-safe. Values
are in Unreal centimeters and seconds; gravity is a magnitude acting downward. Lower/upper bounds and initial
placements are synthetic test fixtures, not permanent level geometry.

| Player movement parameter | Start / step | Dev range |
|---|---|---|
| Horizontal maximum speed | 350 cm/s; step 25 | 150-650 cm/s |
| Horizontal acceleration | 1800 cm/s^2; step 100 | 400-3500 cm/s^2 |
| Gravity magnitude | 980 cm/s^2; step 20 | 400-1600 cm/s^2 |
| Maximum natural fall speed | 650 cm/s; step 25 | 250-1000 cm/s |
| UP_OPEN ascent target speed | 300 cm/s; step 25 | 120-550 cm/s |
| Acceleration toward ascent speed | 1200 cm/s^2; step 100 | 400-2600 cm/s^2 |
| Open-horizontal steering multiplier | 100%; step 5% | 50-125% |
| Optional dash speed (OFF) | 750 cm/s; step 25 | 350-1200 cm/s |
| Optional dash duration (OFF) | 0.15 s; step 0.01 | 0.08-0.35 s |

The baseline character falls naturally in attack and shield descent. No per-state gravity multiplier exists. Separate
fast-fall option MOVE-02 remains OFF. For initial test geometry use a 1600 x 900 cm fixed arena, left/right/top
clamped, bottom lethal, and a centered player spawn that cannot overlap the owl or active gust. These are fixture
values and may be adjusted by a named preset.

| Combat / health parameter | Start / step | Dev range |
|---|---|---|
| Player attack interval | 0.65 s; step 0.05 | 0.20-1.50 s |
| Player bolt travel speed | 700 cm/s; step 50 | 300-1400 cm/s |
| Owl bolt travel speed | 350 cm/s; step 25 | 150-900 cm/s |
| Owl warning duration | 0.75 s; step 0.05 | 0.30-1.50 s |
| Owl attack interval | 3.0 s; step 0.25 | 1.2-6.0 s |
| Player maximum health | 100 HP; step 5 | 50-200 HP |
| Owl bolt damage | 34 HP; step 1 | 5-60 HP |
| Successful front absorption healing | 20 HP; step 5 | 0-50 HP |
| Healing cooldown after success | 2.0 s; step 0.25 | 0-8 s |
| Post-hit invulnerability | 0.8 s; step 0.05 | 0-2 s |
| Shield frontal interception arc | 90 degrees; step 5 | 45-180 degrees |

| Encounter / art parameter | Start / step | Dev range |
|---|---|---|
| Wind upward velocity contribution | +180 cm/s; step 20 | 0-500 cm/s |
| Wind active interval | 2.0 s; step 0.25 | 0.5-6.0 s |
| Wind wear when option enabled | 10 HP/s; step 1 | 0-30 HP/s |
| Survival/departure timer | 90 s; step 5 | 30-240 s |
| Master audio volume | 80%; step 5% | 0-100% |
| Animation playback (core loops) | 8 frames/s; step 1 | 4-16 frames/s |
| Far background slide speed | 0.25% viewport width/s; step 0.05% | 0-2.0% viewport width/s |
| Near background slide speed | 1.0% viewport width/s; step 0.1% | 0-4.0% viewport width/s |
| Random seed: owl test fixture | 20261112 fixed (no slider) | Integer field; logged/exported |

Engineering defaults for omitted parameters: use an explicit per-module safe value recorded in the feature manifest
and mark it ENGINEERING_PROVISIONAL. Do not ask AI to optimize a value by genre intuition at generation time.
No new mechanics may be auto-approved because a slider exists. The full BASE preset loads all P0 values above. A
movement-only preset intentionally disables bolts, shield healing and wind for isolated tests; it does not change the
BASE defaults.

## 6. Player survival, health and recovery

- CORE-03: Damage is limited and visible; health depletion or bottom-boundary crossing ends an attempt.
- Exactly one player health resource (100 HP baseline) drives game-over and visible umbrella condition. No
  separate umbrella integrity resource. Normal open ascent causes zero wear; special hazardous wind can
  damage health only if WIND-02 is explicitly enabled. Umbrella condition does not alter lift in baseline.
- APPROVED_P0: 100 maximum HP, 34 damage per ordinary owl bolt, 0.8-second post-hit invulnerability; exposed
  as parameters. Visual stages: intact 67-100, damaged 34-66, critical 1-33, defeated 0. Three-hit behavior is a
  baseline consequence, not a hardcoded hit counter.
- APPROVED_P0: Front-facing SHIELD_DESCENT absorbs one eligible owl shot, prevents that shot from applying
  damage, emits CatchSucceeded and heals 20 HP once if the 2-second healing cooldown is ready. During
  cooldown the projectile still blocks but does not heal. Never exceed max HP. Optional OPEN_LEFT/OPEN_RIGHT
  catching remains OFF.
- If worn umbrella reduces lift, require a test that verifies recovery remains possible and that the player is not
  forced into an unwinnable fall spiral.
- Upper and side arena bounds should be safe or contained unless another explicit hazard is approved. Bottom is
  the required defeat boundary.

## 7. Boss, projectiles, wind and arena

Boss patterns and target zones

| Item | Description | Priority |
|---|---|---|
| Base bolt | One telegraphed owl projectile, default warning 0.75s, speed 350 cm/s, attack interval 3.0s. Collision resolved once. | APPROVED_P0 |
| Wing gust | Telegraphed force zone, wind enters/exits, optional umbrella wear. Separate forced owl attack from environmental movement current, including spawn ownership, warnings, damage and lifetime. | P1 candidate |
| Returning arc | Curving/boomerang projectile; requires a reviewed diagram and trajectory specification before building. | Experiment |
| Clock target collider (separate clock geometry and hit response from any independent clock health, timing disruption or destruction) | Separate child collider on owl chest with ID CLOCK; overrides BODY on overlap. Clock-hit visual cue ON; attack interruption OFF. | APPROVED_P0 geometry; effect experiment |
| Wing target | Optional additional collider; future gust consequences OFF in baseline. | Experiment / OFF |
| Body target collider | Baseline BODY collider and hit response; owl does not require HP and cannot die. Each shot hits at most one region. | APPROVED_P0 geometry and feedback |
| Steam vent | Environmental timed obstacle independent of owl AI. | Experiment |
| Complex pattern | Combine only attacks that have passed individual readability and recovery testing. | P1/P2 |

Encounter space
- Gameplay uses a single constrained 2D movement plane even if art is layered in depth. Rehearsal modes such as
  movement-responsive scrolling, fixed-angle scrolling and vertical scenery shift are useful VISUAL experiments,
  but only background offsets may change in P0; they must not move the gameplay camera, arena boundaries,
  projectile targeting or hitboxes.
- Use a fixed 16:9 gameplay camera and visibly contained 2D arena. Background layer offset never translates
  gameplay actors. Left, right and upper boundaries safely clamp the player; only crossing the bottom causes
  instant defeat. An independent CAM-02 experiment may later move the camera, OFF in baseline.
- Define projectile spawn area, collision shape, lifetime, and telegraph separately from attack pacing.
- Every hazard has a warning, active interval, recovery interval and reset behavior; expose them as parameters.
- WIND-01: one safe environmental upward-flow field is ON in the baseline, distinct from the owl. It contributes
  +180 cm/s to vertical movement while inside; implement as a bounded continuous contribution, not a value
  added cumulatively each frame. Visual cue/field boundary must be readable. For first deterministic test, use an
  always-present zone; activation duration 2.0s can control an optional pulsed test preset. WIND-02 wear and
  OWL-02 owl-generated gust remain OFF. Hazardous wind must display a distinct danger cue when enabled.

## 7A. Animation, backgrounds, collision and asset contracts

Animation, art selection and collision independence are P0 architecture requirements. PlayerMotor, UmbrellaState,
Health/Condition and Hit Region Router remain authoritative for gameplay. Animation Presenter and visual
adapters observe semantic states/events and render replaceable sprites or Paper 2D Flipbooks. If artwork is missing,
invalid or replaced, render a neutral fallback and report the issue; the game must not silently change collisions,
attack direction, velocity, health or win conditions.

| Asset / state | P0 content and rendering rule | Fallback / optional |
|---|---|---|
| Player: UP_OPEN | Animated open-upright flying loop; independent horizontal sway/flip is visual only. Default 8 FPS. Rehearsal source `Test_Assets/SpriteLayout.json` illustrates explicit grid, pivot and FPS metadata; use the final selected asset manifest as authority, not rehearsal timing. | Use 2+ consistent frames minimum, aim for 4-6; optional turn/bank OFF. |
| Player: ATTACK_DESCENT | Animated lowered umbrella / falling shooting loop. Shots spawn from stable named muzzle socket, not a frame-dependent pixel. If the sprite uses per-frame attachment data, transform the author-provided wand-tip coordinates into one consistent world-space muzzle. Do not allow the rendering frame to change attack cadence or projectile direction. | 2+ frames minimum; static muzzle fallback if socket art absent. |
| Player: SHIELD_DESCENT | Animated forward-facing shield descent / catch reaction. Catch flash indicates accepted projectile. Rehearsal test art includes a guard-fall row and transition frames, but it does not by itself prove a distinct attack-descent loop is delivered; missing pose uses an explicitly logged fallback until its own art is approved. | 2+ frames minimum; no mandatory side-facing variants. |
| Player: transitions | Hit, defeat and survived visual states must be distinguishable. | One-frame pose + overlay accepted at content lock. |
| Owl | Idle, one bolt telegraph, bolt release, depart; chest clock visually identifiable. | Minimal 2-3 poses acceptable. No complex wing rig. |
| Background | Fixed camera with two separately looping horizontal visual layers behind game plane. Far slower than near. Rehearsal sky/skyline art demonstrates independent seamless wrap. Keep layer offsets presentation-only; alternative follow-travel/fixed-diagonal styles remain dev-only, OFF in BASE. | If a seamless tile unavailable, use a static layer and log art issue. |
| Clock hit region | CLOCK collider distinct from BODY; visually align to chest clock. One hit event with region and shot ID. The rehearsal adds other clock/wing/eye regions and HP; those are not imported. Only CLOCK and BODY routing is P0. | No damage mechanic for clock unless COM-02 approved. |

Sprite import contract: preserve asset ID and provenance, frame size/order, optional frame pivots and visual
attachment offsets, intended frame rate, transparent alpha and animation-to-state mapping. These describe the
chosen artwork only and may be replaced with the asset set. Do not treat sprite dimensions, alpha silhouettes, atlas
origin, source FPS or frame animation as authoritative hitbox/physics/muzzle data. The renderer can use per-
artwork offsets to align appearance to stable gameplay anchors. Replacements must pass import/preview validation
before selection.

Visual parallax contract: BG-01 loops layers leftward at independently configurable rates while the camera remains
fixed; use tiled/repeated art with seamless wrap and no camera tracking. Offscreen movement is never inferred
from the background. Visual layers do not spawn colliders or affect wind. Optional CAM-02 changes actual world-
camera relation and is OFF. If the frame rate drops or motion is distracting, turn off the layer without affecting
gameplay.

Owl collision router contract: CLOCK and BODY are independent gameplay collision regions, not derived from the
current artwork or visible masking. They carry stable region IDs on one owl actor. CLOCK has priority when they
overlap; each player projectile resolves at most one BossTargetHit. Collision dimensions and anchor positions are
stored in a separate gameplay collision configuration; only an explicitly approved collision-tuning change can alter
them. Art-layer order, clock illustration changes, sprite scale and visual damage effects do not alter targeting or
physics.

## 7B. Deterministic first-encounter behavior

P0 world coordinates and starting fixtures: use horizontal world +X and vertical +Z, with locked gameplay depth
Y=0; right-facing means +X. For the first 1600 x 900 cm fixture, place the owl at x=+560 and the player at x=-350, z=0.
Clamp player sides and top before touching the owl; crossing the bottom boundary defeats. The geometry is a test
preset and remains tunable, not a story or level-scrolling rule.

Player attacks: on entry to ATTACK_DESCENT, emit the first fixed-forward +X shot immediately if not cooling down,
then every 0.65 active seconds; fired projectiles continue until a hit, expiry or leaving the arena. Entering
SHIELD_DESCENT or UP_OPEN prevents new shots immediately. A projectile cannot hit its owner. Baseline player
shot speed is 700 cm/s; damage does not deplete owl HP or end the encounter. Actor visuals and body orientation
never change the fixed +X aim direction.

Owl attacks: allow a 2.0-second configurable initial grace interval after ACTIVE starts. Telegraph a single straight-
line bolt every 3.0 active seconds measured from telegraph start. On windup start, snapshot the player position and
lock the projectile direction toward that point; do not home or track the player afterward. Show a 0.75-second
visual/audio warning, then launch a 350 cm/s bolt. Pattern sequence and initial delay use fixed preset values and
logged random seed; only approved alternate patterns may use randomness.

Projectile collision order: a live owl bolt first checks enabled shield interception, then player HP collision; successful
interception consumes it and sends one catch event, otherwise a body hit applies one damage event (subject to
invulnerability). Player bolts resolve CLOCK before BODY and emit one region event. Consume projectile after one
resolved target contact. Despawn all projectiles on hit, leaving bounds, reaching a provisional 5-second lifetime,
reset, defeat or success. Collision sizes and spawn offsets are data values aligned to artwork; their default fixture is
documented per asset, not inferred from sprite alpha edges.

Encounter reset: a restart restores 100 HP, state UP_OPEN, spawn, zero transient velocity, full 90-second timer, one
active wind zone, owl attack initial delay, catches/heal cooldown, consumed shot IDs, slide offsets, and test seed;
destroys residual projectiles. Pause freezes encounter timer, projectile movement, actor animation and background
scroll, and attack scheduling. If health depletion/bottom crossing and duration completion occur in the same update,
resolve defeat first; emit exactly one terminal event and show exactly one result screen.

## 7C. Replaceable visual assets and non-authoritative artwork

Status: APPROVED_P0 architecture contract. The current screenshots, Rick/design-reviewer rehearsal art, generated sprite
sheets, visual effects, interface ornaments and scenery are temporary presentation candidates. None is mandatory
for the shipping game. Swapping/removing them must not require rebuilding movement, collision, health, attack
logic, owl targeting, encounter flow or camera rules. The player-facing result still needs legible states and warning
cues.

Asset ownership: Gameplay components expose stable semantic state IDs (UP_OPEN, ATTACK_DESCENT,
SHIELD_DESCENT, DEFEATED), damage-stage IDs, projectile/hit events, CLOCK/BODY region IDs and gameplay-space
anchors. A separate visual asset map selects the images, flipbooks, material, animation rates, layer offsets and
effects for each state. The map may be changed in developer builds by applying another validated asset set; shipping
builds include only selected licensed/approved assets and required fallbacks.

No cross-coupling: Movement, fall speed, hitbox extent, knockback, projectile collision radius, spawn direction,
health and boss outcome never read sprite dimensions, visual scales, animation poses, texture transparency or
background offsets. Firing/catches are governed by gameplay timers/collision and may trigger matching animations;
animation frame timing must not independently create extra shots or healing. Cosmetic asset changes do not reset
player progress, cause velocity changes or modify the seeded attack schedule.

Fairness and calibration: Replaced graphics must remain visually aligned with the independently defined gameplay
collider and muzzle/catch anchors. When art and gameplay geometry visibly disagree, first adjust visual-only scale,
pivot or offset. If actual hitbox or physics changes are needed for fairness, log a separate feature/configuration
change, run adjacent gameplay regressions, and obtain Richard approval. Never silently resize collisions to an atlas
or damage mask.

Fallback/acceptance: When a sprite sheet or material cannot load, show a neutral visible stand-in at the gameplay
anchor, maintain readable warning shapes, and log the missing asset ID. A replacement set must pass
dimensions/alpha/frame checks, 16:9 gameplay readability, collision-alignment preview, and same-seed
comparisons of position, collision hits, projectiles, HP and completion timing. Default game presentation uses the
first approved or temporary art set. Optional developer art-set comparison (ART-02) starts OFF; it is not required in
the shipping UI.

## 8. Encounter control and progression

The approved initial success condition is 90 seconds of accumulated ACTIVE (unpaused) encounter time. Encounter
Director owns the timer and emits EncounterCompleted once; owl departs, projectiles and damaging collisions stop,
and the SURVIVED screen appears. No kill or damage threshold is required. The completion-rule interface remains
replaceable for later review; 90 seconds is the explicit provisional default, not an undecided placeholder.

| State | Entry / exit rule |
|---|---|
| READY | Load approved preset, reset all modules and place actors; await start. |
| ACTIVE | Accept player input, owl attack scheduling, hazards and damage. |
| ENDING_SUCCESS | Completion rule triggers; stop/disable threats, owl departs, show unmistakable outcome. |
| ENDING_FAILURE | Health zero or bottom boundary; stop interactions and display clear defeat. |
| RESTARTING | Clear active projectiles, timers and state, restore configuration and return to READY. |
| PAUSED | Suspend simulation according to a single owner to prevent stale timers or inputs. |

Suggested progress phases (introduction, contest, desperation) are tuning presets, not required numbered phases or
a hardcoded percentage of the total timer. Do not equate the owl chest clock with a visible completion timer without
explicit approval.

## 9. Feedback, readability and accessibility

- Main presentation should favor diegetic status indicators: the umbrella for condition, the owl/clock for enemy
  state, wing pose/flow for gusts, distinct projectile silhouette for threats.
- Development builds include visible developer-only overlay and workbench; the submitted build omits
  slider/toggle interface, saves the approved tuned preset as constants/assets and retains only player-facing
  controls/screens. Optional one-key debug overlay does not ship.
- Audio signals can reinforce telegraphs, hits, catches, and pacing; required hazards also need visual cues.
- Display explicit start, defeat and success feedback. Clear retry should be possible without an editor restart.
- PC keyboard/mouse + controller are required. Baseline keyboard: A/D or arrows steer, hold left mouse
  ATTACK_DESCENT, hold right mouse SHIELD_DESCENT, release both UP_OPEN, Esc pause, R retry after defeat.
  Controller: left stick steer, R2 attack, L2 shield, release both rise, Options/Menu pause, confirm retry. Inputs may
  be remapped in dev tools. Shield wins held simultaneously.
- Visual direction is a provisional reference, not a locked asset selection: favor readable silhouettes, clear
  clock/umbrella cues and strong threat contrast. Current gothic/clockwork mockups and rehearsal sprite sheets
  may serve as placeholders or inspiration only, subject to asset rights and future visual approval. The player uses
  state-driven sprite-sheet animation and background art layers, but any qualifying replacement art must be
  swappable without changing gameplay. No narrative-specific animation, dialogue or cutscene is required.

## 10. Human tester workbench (required pipeline capability)

The team will use a separate game-specific rehearsal/mockup for immediate feel testing and validate the pipeline
independently with unrelated generic content before the jam. After the start, the game generated by the pipeline
includes a development-only test workbench with visible statuses for every toggle, numeric sliders, presets, scenario
reset, logs and export. No implementation_state=NOT_BUILT switch can claim to be interactive. Gameplay feedback
does not automatically update feature authority.

| Tester capability | Acceptance behavior |
|---|---|
| Feature toggles | A tester sees which options are enabled. Incompatible options are blocked with a plain-language explanation or require reset. |
| Parameter tuning | Move speed, lift, gravity, projectile speed, cadence, damage, gust force, and wind wear can be adjusted within safe ranges where implemented. |
| Named presets | Save/load baseline, wind, combat, catch, condition and combined configurations with persistent IDs. |
| Scenarios | Start at specific test points with controlled enemy patterns, hazard spawns and player position. |
| Reproducibility | Record build ID, feature manifest version, preset, random seed and start conditions. |
| Feedback | Tester records a short note: fun, clarity, difficulty, suspected bug, preferred variant. |
| Restart/reset | One action restores state and clears lingering effects. |
| Log/export | Export/share config and feedback as text or JSON without requiring nonproject personal data. |

Suggested test presets (not actual gameplay modes)

| Preset ID | Enabled candidate features | Learning goal |
|---|---|---|
| T-01 BASE | All APPROVED_P0 features ON: movement, auto attack, front shield/heal, one owl bolt, safe wind, sprite animations, parallax, clock/body hitboxes, screens. Experimental modules OFF. | Does the complete 90-second encounter work and remain readable? |
| T-02 MOTOR | Base movement only: turn off owl attacks, shield healing and wind for this TEST ONLY. | Do gravity, ascent, steering and state priority work? |
| T-03 SHIELD | Use frontal shield + one bolt; separately log catches during healing cooldown. Side-catching still OFF. | Do blocks register once, avoid damage, and only heal when allowed? |
| T-04 RECOVER | Baseline plus low-health starting scenario and shield cooldown values. | Can a damaged player recover without creating an infinite-health loop? |
| T-05 WIND | Safe environmental wind ON, then optionally wind wear as isolated EXPERIMENT. | Is wind readable; are danger and advantage distinguishable? |
| T-06 CLOCK | Required clock/body hit routing ON; optional clock interrupt OFF until approved. | Does CLOCK precedence work, and can effects be attached later? |
| T-07 VISUAL | P0 animated sprite loops and sliding background ON; compare static background and minimal frames. | Are frames anchored and threats legible at gameplay size? |

## 11. Test catalog and acceptance criteria

| Test ID | Setup | Pass / failure evidence |
|---|---|---|
| QA-01 | UP_OPEN versus NO_LIFT at same spawn. | Upright-open rises; non-lift falls naturally; no state-specific fast fall. |
| QA-02 | Transition repeatedly across umbrella states. | No stuck input, unintended lift, excessive velocity or stale attack state. |
| QA-03 | Turn on a single telegraphed owl bolt. | Players can react; collisions register once; warning precedes danger. |
| QA-04 | Activate side catch only, if implemented. | Left and right directional catches behave as documented; failure is visible. |
| QA-05 | Enable recovery only with catch prerequisite. | Recovery fires once, modifies intended resource and cannot exceed max. |
| QA-06 | Apply damage then bottom-out. | Correct loss reason, proper feedback, clean restart. |
| QA-07 | Switch wind force and wear independently. | Forces work with no wear when wear is disabled; UI reflects actual state. |
| QA-08 | Set a deterministic owl pattern and random seed. | A repeated test gives same event ordering within reasonable engine variability. |
| QA-09 | Trigger departure during active attacks. | No post-victory lethal collision; success clearly visible; retry works. |
| QA-10 | Disable optional feature with active dependencies. | Safe rejection, reset or fallback with explicit log. |
| QA-11 | Package and launch a development Windows build. | Correct game mode, input, logs, success/failure UI; no missing assets. |
| QA-12 | Have Richard and the design reviewer compare one tuning value at a time. | Each run logs preset ID, GDD revision, selected change, preference and failure reason. |
| QA-13 | Hold ATTACK, hold SHIELD together, release both. | Shield overrides attack; no new firing in shield; releasing both immediately restores upright ascent. |
| QA-14 | Fire player projectiles at BODY, CLOCK and an overlap. | Distinct region event, clock priority, one BossTargetHit per projectile, no unexpected owl death. |
| QA-15 | Cycle UP_OPEN, ATTACK_DESCENT, SHIELD_DESCENT sprites. | Three animated core loops match states; pivots stable; no sprite changes to collision or speed. |
| QA-16 | Scroll far and near background for 90 seconds at 16:9. | Seamless loops, far layer slower, fixed camera and static gameplay hitboxes; static fallback safe. |
| QA-17 | Re-run same baseline preset and scripted owl attack schedule. | Same P0 settings, 90-sec completion, no random agent changes; seed and GDD revision logged. |
| QA-18 | Package clean Windows shipping build and run without editor. | No dev slider/toggle menu, no missing plugins/assets, keyboard/controller play, pause/retry, success/fail. |
| QA-19 | Review source declarations, gameplay video, upload requirements. | 30-60 s gameplay video and packaged build uploaded before deadline; credits/provenance included. |
| QA-20 | Restart or pause during telegraph, projectile flight and catch. | No stale actors or timers; fixed target snapshot and deterministic reset; exactly one terminal event. |
| QA-21 | Verify any supplied sprite-sheet frame grid and per-pose anchor metadata; switch rise/attack/shield rapidly. | Sheet dimensions and frame counts match source metadata; umbrella grip stays attached; shot muzzle remains aligned; collision/physics do not change with animation frame. |
| QA-22 | Save a non-default development preset, relaunch, restore the named preset, then restore the Richard-approved BASE. | All enabled states, parameter values, units and input mappings round-trip; unsaved edits are identified and no rehearsal defaults leak into BASE. |
| QA-23 | Test environmental wind and optional owl gust independently in separate fixtures. | Environmental current can change movement without damage; disabled owl gust emits no attacks; the two sources own separate warnings, controls and logs. |
| QA-24 | Compare fixed P0 background offsets with optional travel-follow and fixed-angle rendering fixtures, with identical game simulation. | Player/world coordinates, hitboxes, bounds and attack targeting are identical across rendering modes; only art-layer motion changes. |
| QA-25 | Replace or delete all default character/umbrella/clock sprite references in a dev fixture. | Visible fallback and warnings appear. Movement, health, state transitions, collision and fixed clock/body hit routing remain playable and unchanged. |
| QA-26 | Swap between original, rehearsal-preview and neutral stand-in art under the same fixed input replay/seed. | Actor trajectory, physics values, shot counts, collision outcomes, HP and elapsed-success time remain identical; only visual data changes. |
| QA-27 | Choose an asset set with different frame dimensions, fps, pivot and graphic silhouette. | Visual-only mapping compensates or reports failed alignment; no automatic collision/attack edits. Source metadata and validation result recorded. |
| QA-28 | Package with approved final visuals and turn off ART-02 developer selector. | No dev selector or unused candidate assets shipped unless explicitly approved; readable fallback is available for recoverable missing-art cases. |

Automated tests verify technical contracts; humans judge feel and fun. Successful automation does not mean a
feature is enjoyable. Tests should include a "why did this run fail?" category for player confusion, unfair pressure,
unresponsive controls and bugs.

## 12. Pipeline specification and safe handoff

Required pre-jam pipeline properties
- Create a clean Unreal project or generic sample using repeatable commands; verify UE 5.8.4
  installation/compatibility.
- Agents have bounded repository/folder permissions and explicit approval before writes outside the project
  scope; no blanket local-machine access.
- Generate versioned modules and tests from an approved specification; report which feature IDs and decisions
  were used.
- Support create, edit, compile/validate, run tests, record errors, revert failed steps and resume from a known
  checkpoint.
- Create a generic test harness with feature toggles, parameter presets, reset, logging and scenario templates on
  unrelated synthetic objects before the jam.
- Capture agent identity, prompt/tool inputs, changed files, license/provenance of sourced assets, commit hash and
  test result for every change.
- Support one clean packaged development build, or a documented packaging error if target environment is not
  ready.
- Validate architecture with unrelated sample content. Do not instantiate game-specific umbrella/owl actors,
  attack patterns or art before the permitted jam start.

Recommended post-start generation order
16. Generate empty game project from frozen tooling and confirm build.
17. Create core 2D arena, player motor, normal falling and open-upright lift.
18. Add bottom defeat, minimal health state, clear restart and simple outcome trigger.
19. Add one owl with one telegraphed projectile; playtest P0 movement and threat readability.
20. Enable test harness and telemetry in an actual game-specific build.
21. Implement approved options in isolated modules, first alone, then in deliberate combinations.
22. Run automated regression tests, human playtests, adjust scope, polish and package early.

AI agent task format
Each generation ticket should include: task ID, approved GDD revision, required feature IDs, permitted files/folders,
interface contract, dependencies, test cases, status/priority, allowed assets, rollback point, owner and acceptance
gate. Agents return: changed files, assumptions made, screenshots/logs if applicable, test output, blockers, new
decision requests and commit hash.

## 12A. Four-day release plan and change-control gates

Time box is the primary production constraint. Do not optimize for the largest feature count; optimize for a
complete and reliably submitted experience. Jam begins November 12 at 12:00 AM EST (November 11 at 9:00 PM
PST). Official submission deadline is November 15 at 5:59 PM PST; treat an earlier internal cutoff as mandatory
buffer. All periods are America/Los_Angeles unless otherwise stated.

| Gate | Must be true | If behind schedule |
|---|---|---|
| Before start: tool freeze | Generic pipeline rehearsal generates, builds, runs tests, rolls back, logs and packages; no pre-start game-specific implementation. Pin GDD revision and tool versions. | Freeze pipeline changes; write known issue and manual fallback procedure. |
| Nov 12: first playable | P0 motion states, owl bolt, health/death, basic wind, timer and restart functioning in editor. | No new experiments. Generic temporary sprites permitted. |
| Nov 13: feature complete target | Clock/body hit separation, core sprite loops, simple background layers, player screens and developer baseline preset functioning; first clean packaged build. | Simplify art frames and parallax, not gameplay authority or packaging. |
| Nov 14: test/polish lock | Human playtests, regression tests, controller pass, one planned tuning configuration; capture provisional video. Freeze optional features by midday. | Disable all nonessential features; focus on blockers and readability. |
| Nov 15: release day | Clean shipping build, sanity run, 30-60s gameplay video, credits/declared assets, upload and submission verification. Internal target: 3:59 PM PST, 2h ahead of 5:59 PM deadline. | No new game features; use last known good build, only blocker fixes. |

Go/no-go rule: gameplay feature changes end before final QA and packaging. Each new feature needs explicit
Richard approval and a named ticket. If a P0 art enhancement blocks packaging, substitute a smaller compliant
implementation; if a P0 control/survival rule fails, repair it ahead of art expansion. Maintain a known-good
packaged build and recorded rollback point every day. The last day is for build, video, submission, and final
technical verification, not concept exploration.

Before jam starts, build only generic reusable pipeline / tooling tests; do not transplant pre-jam rehearsal game code
as newly created game content without checking official rules. Declare any premade prompts, scripts, artwork, or
assets used. Test plan must not assume the existing UmbrellaGirl rehearsal is automatically eligible jam content.

Determinism and modularity gate: after the initial approved post-start generation, test new options in the SAME
version-controlled game by switching presets or adding isolated modules; do not independently regenerate the
entire game for every A/B run. Each agent ticket pins the GDD revision, feature IDs, tool versions, interfaces, target
files and test suite. AI generated code need not be byte-identical across independent runs, but baseline behavior,
runtime data, seed and test results must be reproducible from the same commit. If a mechanic is not built, expose it
as NOT_BUILT, not as an enabled slider or silently synthesized implementation.

## 13. Resolved decisions and nonblocking open items

| Decision ID | Question | Safe interim behavior |
|---|---|---|
| DEC-01 | Umbrella inputs? | RESOLVED: default UP_OPEN, hold ATTACK or SHIELD to descend; shield priority; bindings in section 9. |
| DEC-02 | Does closed/lowered attack automatically fire? | RESOLVED: YES; fixed-forward +X 0.65s per shot while ATTACK_DESCENT; no firing in UP_OPEN/SHIELD. |
| DEC-03 | Does shielding repair health? | RESOLVED: Front SHIELD_DESCENT blocks projectile and heals 20 HP on successful catch after 2-second cooldown; side catching OFF. |
| DEC-04 | Health vs umbrella condition? | RESOLVED: One HP resource; umbrella wear visualizes remaining HP. |
| DEC-05 | Does wear reduce lift? | RESOLVED for baseline: NO; optional SURV-04 OFF. |
| DEC-06 | What triggers owl departure? | RESOLVED provisional default: 90 seconds of unpaused ACTIVE time; completion rule is configurable. |
| DEC-07 | Which wind danger is required? | RESOLVED baseline: one safe environmental upward current ON; wear and owl gust attack OFF. |
| DEC-08 | How do owl target regions work? | RESOLVED geometry: separate CLOCK and BODY hitboxes, priority CLOCK. Special effects OFF. |
| DEC-09 | How is progress communicated? | RESOLVED P0: readable telegraphs, umbrella wear and distinct start/defeat/survived; optional dynamic background intensity OFF. |
| DEC-10 | How does theme change gameplay? | PENDING until Nov 11 theme reveal; Richard approves any scope change. |

## 14. Production and governance

| Role | Responsibilities |
|---|---|
| Richard: design owner and document approver | Final approval for GameDesignDocument.pdf, feature status/priority, player experience and gameplay presets; collaborates in testing. |
| Josh: pipeline / AI lead | Agent orchestration, safe permissions, versioned contracts, automation and technical pipeline acceptance, with the design reviewer assisting. |
| Rick: GDD contributor / rehearsal and build execution | Proposes edits/art, executes/reviews builds and integrates work as agreed. Can review candidate with another AI; not an additional formal design approval gate. |
| Design reviewer: technical review / human playtester | Review design alignment and pipeline integration with Josh; test gameplay with Richard and report results. |
| Entire team | Review theme fit, source/license declarations, player-facing QA, build packaging, video, and submission verification. |

Authority: Richard owns design sign-off and the review candidate. Josh owns pipeline feasibility and technical gates.
Rick and the design reviewer offer independent feedback. A second AI review is optional quality assurance, not a veto. A proposed
option never becomes APPROVED_P0 without a named approval and new GDD revision. Only the approved PDF in
the GitHub repository is the authoritative source after upload.

Schedule and compliance
- November 8-10: finalize this GDD, freeze agent feature manifest, test tools using non-game stand-in content, and
  rehearse compilation/packaging. Do not start actual jam game implementation before official start.
- November 11: theme reveal is 11:00 AM PST. Review theme mapping and make bounded approved changes.
  Game production starts November 11 at 9:00 PM PST (November 12 at 12:00 AM EST).
- November 12-14: core implementation, first playable, automated/human testing, performance and packaging
  rehearsal. No design scope expansion without approval; see section 12A.
- November 15: official deadline 5:59 PM PST. Internal upload target 3:59 PM PST to leave two hours for final
  submission verification. Last day prioritizes packaging, video, upload, source declarations and technical fixes.
- Maintain provenance declarations for scripts/assets made before the jam, per organizer instructions.

## Appendix A. Preserved option backlog

None of these are assumed implemented. They can be evaluated with an explicit experiment ticket once the baseline
proves enjoyable.

| Theme | Candidates |
|---|---|
| Movement | Optional umbrella inversion, emergency recovery, side catch orientation, momentum variants, reduced-lift wear, faster-fall force, no-direct-steering wind/dash variant. All OFF in baseline. |
| Attack | Optional angled/charged shot, precise timing, dive bonus, vulnerability, clock interrupt; fixed-forward auto-fire is REQUIRED baseline. |
| Defense | Front shield/descent, successful absorption and HP healing are REQUIRED baseline; optional left/right catch, perfect-catch reward, emergency block remain OFF. |
| Owl | Clock/body distinct target colliders are REQUIRED. Returning bolt, wing special response, gust attack, gear hazards, adaptive pressure and complex patterns are OPTIONAL. |
| Arena | Fixed camera, safe environmental upward current and sliding background art are REQUIRED. Steam vents, scroll camera, diagonal or hazardous currents and separate obstacles are OPTIONAL. |
| Progression | Introduction/contest/desperation pacing, optional player-responsive pressure, clear owl departure, nonlethal boss resolution. |
| Art/audio | Three core sprite-sheet character animation loops and layered horizontal background movement are REQUIRED. Complex owl rigging, time distortion, progression motifs and extensive effects are optional. |
| Narrative | Ella, the clockkeeper, night/dawn transition, stolen clock hand in umbrella, mysterious departure, chapter framing. Entire category DEFERRED. |

## Appendix B. Example agent-readable feature record

Illustrative record below. IDs and values are proposed conventions, not Unreal configuration syntax. A technical
lead can implement it as DataAssets, JSON, tables or other versioned configuration.

```
feature_id: UMB-03
name: optional_sideways_catch
status: PROPOSED
priority: P1_candidate
default_enabled: false
implementation_state: NOT_BUILT until separately approved
requires: [UMB-01, DEF-01, projectile_contact]
conflicts: []
configurations: [OPEN_LEFT, OPEN_RIGHT]
emits: [CatchAttempt, CatchSucceeded, CatchFailed]
parameters: [catch_arc, catch_window, catch_cooldown]
reset_required_for_toggle: true
acceptance_tests: [QA-04, QA-10]
implementation_authorized: false
owner: Richard (decision); Josh (pipeline implementation after approval)
```

## Appendix C. Test note template

| Field | What to record |
|---|---|
| Build / run | Commit SHA, GDD revision, test ID, feature preset, random seed, date. |
| What changed | The ONE important variable changed versus the comparison run. |
| Observed | Controls, visual clarity, failure reason, surprising interactions and reproducible steps. |
| Ratings | Fun, fairness, readability and responsiveness, each 1-5 (team scale). |
| Decision | Keep, revise, remove, retest. Include owner and a short rationale. |

## Appendix D. Baseline configuration and change register

REVIEW CANDIDATE 1.3 (November 8, 2026): All starting visuals remain replaceable placeholders. Added art-to-
gameplay separation (7C), explicit asset mapping/fallback, developer-only optional art comparison ART-02 OFF, and
QA-25 through QA-28. Confirmed latest Rick rehearsal source commit d69f0b1 and documented packaged WIN008;
rehearsal code/test claims are reference evidence, not acceptance of our game. P0 controls, horizontal steering, fixed
camera, one HP resource, 90-second victory timer and numerical defaults are unchanged.

PRIOR REVIEW CANDIDATE 1.2 changes from GitHub PDF blob dd20aa7f987032143fb81f39c15d65dbc77a752b: (1)
Richard approved P0 scope, controls, camera, single health, 90-second provisional completion and numerical
defaults; (2) split P0 frontal shield from experimental left/right catch; (3) add Paper 2D character sprite animation
and visual-only background slide; (4) add owl CLOCK vs BODY distinct hitboxes; (5) name authority roles and
replace obsolete open decisions; (6) set package-first four-day schedule with an early internal upload target. GitHub
is unchanged until Richard explicitly chooses the reviewed PDF for replacement. (5) 8 November rehearsal sweep:
clarified animation anchors, preserved environmental wind versus forced gust separation, refined tester-config
persistence and visual-only scrolling modes, added QA-21-QA-24 and non-normative Appendix F with source-
specific adoption limits. These additions do NOT change approved gameplay or numerical defaults.

Deliberately NOT authorized by this revision: story/lore implementation, complex boss phases, owl kill/health bar,
player aim angle, damage-dependent lift, damaging gust, extra fast fall, mobile build, actual scrolling camera, new
content after final feature lock, or game-specific development before the official start. Preserve these ideas in the
appendix, OFF until deliberately approved.

Open nonblocking technical items for Josh to confirm: exact art style reference file and sourced-asset provenance;
final UE 5.8.x project/plugin compatibility; reproducible packaged build and first launch on a clean PC; whether
optional features have implemented modules or only dormant hooks; exact internal freeze time and exception
owner; theme requirements revealed November 11. None permits agents to choose alternative default game
mechanics.

## Appendix E. References and rule verification

- 2026 Epic AI MegaJam official jam page: https://itch.io/jam/2026-epic-ai-megajam
- Epic organizer preparation FAQ: https://forums.unrealengine.com/t/vibe-your-way-to-50k-the-2026-epic-ai-megajam-is-coming/2843973
- Unreal Engine 5.8 Automation Test Framework: https://dev.epicgames.com/documentation/unreal-engine/automation-test-framework-in-unreal-engine
- Unreal Engine 5.8 Gameplay Systems: https://dev.epicgames.com/documentation/unreal-engine/gameplay-systems-in-unreal-engine
- User-provided screenshots of Rick's draft and team's subsequent umbrella decisions, November 8, 2026.

## Appendix F. Rehearsal evidence and transfer boundaries

Source reviewed: RickTheBuilder/GameJam2026 on 8 November 2026. This is a SEPARATE pre-jam experiment, not
the approved jam implementation. Findings below are source-derived evidence or suggested engineering practices
only. They do not override Richard's approved P0 values, camera, input precedence, encounter objective or four-day
scope.

| Relevant repository source | Useful evidence or pattern | Transfer decision for the jam |
|---|---|---|
| Rehearsal/UmbrellaGirl/PLAYTEST.md; README.md | Documents a playable Windows rehearsal, optional diagnostic HP bars, 20 settings categories, two scrolling visual styles, saved setups and feedback export. | ADAPT workbench structure and reproducibility, not its full feature count. Verify actual behavior in the new game. |
| Source/UmbrellaGirl/GameplayTuning.h/.cpp; MovementSettings.h | Central catalog of stable setting keys, kind, initial value, range, step and units; sparse overrides, named setups and category-specific save. | ADAPT the schema and clear Save/Discard/Restore behavior. Preserve our 1.2 approved numbers, switches and no-AI-guessing rule. |
| Source/UmbrellaGirl/WindField.h; EncounterDirector.h; BossPresentation.h | Voluntary environmental currents, forced boss attacks and visual-only boss presentation have distinct owners. | ADAPT ownership boundaries. P0 has one safe upward current; rehearsal's four alternating rideable lanes and forced damaging gusts are NOT defaults. |
| Test_Assets/SpriteLayout.json; Asset Notes.md | Exact frame grids, pivot/umbrella grip, per-frame wand tips, damage rows, frames/sec and animation provenance are available. | ADAPT metadata/validation process; approved gameplay animation states still control presentation. Actual source assets must be approved and declared separately. |
| Rehearsal/UmbrellaGirl/Source/.../GameContracts.h; EncounterDirector.h | Shows separately named owl parts including clock, wings and eye, plus region-specific hit results. | ADAPT the clock/body region-tagged hit contract only. Extra HP, coverings, eye blackout, attack interruptions and kill conditions stay optional/OFF. |
| Rehearsal/UmbrellaGirl/Source/.../*Tests.cpp; README.md | Source describes Unreal tests and reports 66 passing automation tests in the latest PLAYTEST document (earlier README describes 46), plus Windows rehearsal packaging checks. Physical controller feel remains human work. | ADAPT test categories and evidence standards; do not label the new pipeline or final game verified because the rehearsal tests passed. |
| (design reviewer's pipeline repo)/V101/AGENTS.md; Pipelines/Design Pipeline.md | Review-candidate workflow separates authorized requirements, exploratory assumptions, checks, human approval and integration ownership. | ADAPT disciplined change control and truthful pass/fail evidence. V101 is not automatically an adopted or operational production pipeline. |

Latest rehearsal source: RickTheBuilder/GameJam2026 commit d69f0b1 (November 8, 2026, 11:31 PM PST).
`PLAYTEST.md` identifies WIN008 and a selectable candidate sprite family, useful only as a separate visual
experiment. Reuse requires rights and rule checks.

Non-transfer / explicit conflict list. The rehearsal allows SHOOT+ABSORB to mean accelerated free fall and starts
direct steering OFF; our approved BASE instead gives SHIELD priority and direct steering ON. Its multi-stage
tutorial, outer-part/clock defeat chain, five spells, XP/collectibles, rideable-lane controls, Android build, and lift
degradation are excluded from P0. No rehearsal parameter or asset becomes a requirement merely because it exists
in source.

Provenance: Rehearsal art uses generated and reference-derived imagery (`Test_Assets/Asset Notes.md`). Do not
copy into the jam entry without checking source rights, permissions and pre-jam disclosures. Preview art is not final
art approval.

---

<!-- source: docs/gdd/GDD-B1.0.md -->

# GDD snapshot B1.0 (read-only)

| Field | Value |
|---|---|
| Revision | B1.0 |
| Title | UMBRELLA / OWL, GDD B (pipeline-first, testable game specification) |
| Date | 8 November 2026 (Draft B1.0, team decision proposal) |
| Authors | the team (design owner: Rick, GDD B §14) |
| Source | `GameDesignDocument.pdf` on `origin/main`, commit `d716fae` |
| Converted | 2026-11-08, text conversion of the PDF. Tables became Markdown tables; bullets became `-`; page headers and footers were dropped. List numbers are kept as printed (the PDF numbers its lists 1-4, 5-10, 11-15, 16-22). |
| Author clarification | Fall speed is fixed in this revision: no fast-fall, and "closed" never means faster fall. A fall/gravity slider may come in a later revision (`docs/gdd/questions-B1.0.md` Q1). |

Never edit this file. A new revision is a new file `docs/gdd/GDD-<rev>.md` plus a one-line change to `docs/gdd/CURRENT`
(`docs/gdd/README.md`). Where this text and `docs/feature-manifest.json` disagree on status, the manifest wins (GDD B "Source-of-truth priority" 1).

---

UMBRELLA / OWL
GDD B | Pipeline-first, testable game specification
Draft B1.0 | Team decision proposal | 8 November 2026

A new GDD organized for team review, AI-assisted generation, independent feature experiments and reproducible
human playtesting. "The Last Hour" remains a provisional encounter or chapter title; no narrative is required.

PRIMARY OBJECTIVE Design one fun, readable aerial survival encounter; make its systems independently
configurable so testers can compare mechanic choices without repeatedly rewriting the whole game. Modularity is a
design constraint, not permission to build all features.

## A. Interpretation contract (read before generating any files)

| Term | Agent interpretation |
|---|---|
| CONFIRMED | Gameplay intent chosen by the team or the user; still require scope assignment before implementation. |
| APPROVED_P0 | Required for the current approved playable baseline. Build only after the official jam start. |
| APPROVED_P1 | Approved next candidate, only after P0 works and the owner releases it. |
| PROPOSED | Documented possibility with no implementation authority. |
| EXPERIMENT | Requires a contained implementation ticket, test scenario, and acceptance measure. |
| DEFERRED | Do not implement. Keep as idea/reference. |
| OPEN | No decision. Preserve the interface, log the question; no irreversible assumption. |
| REJECTED | Known excluded behavior; do not revive without explicit decision. |

Priority and approval are separate axes. A feature can be high value but still PROPOSED. For this document, P0 is a
recommended baseline for team approval, not a claim that R, C or Josh have signed it off.

Source-of-truth priority
1. Signed-off feature manifest plus approved change log for the current build.
2. Explicit CONFIRMED gameplay statements in this GDD.
3. PROPOSED or EXPERIMENTAL ideas, which are reference only until promoted.
4. Historical comments or narrative descriptions, which never silently override the approved mechanics.

## 1. One-page game definition

| Attribute | Definition |
|---|---|
| Fantasy | A small airborne character manipulates an umbrella to survive a powerful clockwork owl. Player skill centers on movement, timing and positioning. |
| Player goal | Remain alive until the owl departs. Do not require a boss kill. |
| Failure | Player health depleted OR player crosses bottom defeat boundary. |
| World | One 2D gameplay plane, fixed single-screen landscape view, multiple visual background layers. |
| Inputs | Horizontal movement and umbrella operation. Optional aiming/catching interactions must be separately mapped and tested. |
| Core input rule | Only open-and-upright umbrella generates active ascent. Otherwise player falls naturally, modified only by physics/environmental forces. No "fast-fall" state. |
| Attacks | Automatic attack concept preferred so movement remains primary; triggering and aim configuration must be resolved. |
| Opponent | One owl providing clear telegraphed projectile and wind threats. |
| Tone | Gothic storybook / clockwork; no narrative prerequisite. |
| Platform | Windows first, keyboard and controller targeted; mobile/touch not first-build scope. |
| Engine | Team target UE 5.8.4, technical compatibility to be verified. |
| Outcome | A replayable, readable challenge that testers can vary with feature flags and tuning presets. |

Design constraints
- The interesting action is navigating danger through umbrella orientation and altitude, not memorizing a long attack combo.
- No mechanic may make defeat unavoidable without a visible warning or reasonable response window.
- Experimental systems should be isolated by component and configuration boundary wherever practical.
- A config toggle is not the same as hot-swappable physics. Mechanics with incompatible state may require a scene reset.
- Do not include story-specific assumptions in win logic, clock logic, boss AI, asset naming or state ownership.

## 2. Approved intent versus candidate mechanics

| Rule ID | Behavior | Decision |
|---|---|---|
| CORE-01 | Player can move horizontally. | CONFIRMED |
| CORE-02 | Player falls under gravity when no upright-open lift is applied. | CONFIRMED |
| UMB-01 | Open and upright umbrella provides ascent without a gust. | CONFIRMED |
| CORE-03 | Limited health and bottom-out defeat. | CONFIRMED |
| END-01 | Success is surviving until owl departure; owl kill not required. | CONFIRMED |
| COM-01 | Attack execution is automatic; precise trigger/orientation undecided. | CONFIRMED intent / OPEN implementation |
| UMB-02 | Closed umbrella can be aimed to shoot while falling. | PROPOSED |
| UMB-03 | Open umbrella can face left/right to catch or block owl shots. | PROPOSED |
| UMB-04 | Umbrella inversion and forced recovery. | EXPERIMENT |
| SURV-02 | Umbrella wear is visible as health or condition feedback. | CONFIRMED visual intent / OPEN resource model |
| SURV-03 | Catching projectiles repairs or heals. | PROPOSED |
| WIND-01 | Readable wind affects velocity / upward travel. | PROPOSED, strongly desired |
| WIND-02 | Some wind damages umbrella integrity. | PROPOSED |
| OWL-01 | Owl launches visible, dodgeable projectile threats. | CONFIRMED |
| OWL-02 | Owl produces gust attacks. | PROPOSED |
| OWL-03 | Clock, wing and body create different consequences on hit. | PROPOSED |
| OWL-04 | Returning/curving projectile attack. | EXPERIMENT |
| HAZ-01 | Steam pipes or independent environmental obstacles. | EXPERIMENT |
| FLOW-01 | Arena has pacing, restart and survival-end feedback. | CONFIRMED experience / implementation open |
| NAR-01 | Story, witch identities, time magic and stolen clock hand. | DEFERRED |

## 3. Core interaction model

### A. Umbrella configuration and physical effect

| State ID | Definition | Motion / action | Status |
|---|---|---|---|
| UP_OPEN | Umbrella open and pointing upright, functional. | Apply configurable upward lift; horizontal movement remains available. | CONFIRMED |
| NO_LIFT | Any configuration not explicitly producing upright-open lift. | Gravity-driven falling. No special descent-speed multiplier. | CONFIRMED |
| CLOSED_AIM | Umbrella closed and oriented to fire. | Falls under gravity; MAY allow automatic attack emit. | PROPOSED |
| OPEN_LEFT | Umbrella open and facing left. | Falls under gravity; MAY catch shots arriving from left. | PROPOSED |
| OPEN_RIGHT | Umbrella open and facing right. | Falls under gravity; MAY catch shots arriving from right. | PROPOSED |
| INVERTED | Umbrella inverted/disrupted. | Falls until orientation/recovery rule resolves. | EXPERIMENT |
| DEFEATED | Health zero or bottom defeat boundary crossed. | Stop player control and enter defeat result. | CONFIRMED |

State resolution and input precedence
5. Update horizontal input if the player is alive, independent of active umbrella orientation.
6. Resolve the requested umbrella configuration from available inputs. In ambiguous input combinations, select a
   single explicit priority order through a named configuration, never by accidental key order.
7. Apply upward lift if and only if the resolved configuration is UP_OPEN and the umbrella is allowed to function.
8. In every other configuration, normal gravity continues. Wind/external impulses may still change actual velocity;
   they do not create a faster-falling mode.
9. If an attack or catch module is enabled, evaluate only its own eligibility rule and collision/event result. Do not
   give a side-facing catch state automatic lift.
10. If the player is defeated or encounter is ended, apply the configured stop/control transitions; do not leave stale
    attack or collision events active.

Critical invariant: "closed" does not mean "faster fall." Any additional downward acceleration is a separate
experimental mechanic and is currently REJECTED for the baseline.

## 4. System boundaries and contracts

| Module | Owns | Must not own |
|---|---|---|
| Input Adapter | Keyboard/controller events and requested action/orientation; remapping. | Umbrella physics constants or boss attacks. |
| Player Motor | Horizontal motion, gravity, lift forces, collisions, bounds. | Healing, owl phase selection, narrative. |
| Umbrella State | Open/closed/orientation/disrupted state and state transitions. | Movement physics details or projectile spawn rules. |
| Attack Emitter | Whether/when a projectile fires, trajectory and cooldown. | Owl win condition or health source of truth. |
| Defense Receiver | Blocking/catching eligibility, success events and direction filters. | Permanent healing balance; emits event to recovery. |
| Health/Condition | Damage, immunity, optional condition and recovery; defeat request. | Owl AI or input mapping. |
| Projectile Service | Projectile spawn, motion, telegraph, collision reporting, lifetime. | Pacing logic or individual actor storyline. |
| Boss Director | Owl threat pattern selection, attack cue timing and target reaction events. | Player motor, win screen UI. |
| Wind/Hazard Field | Forces and hazard zones, warning indicators, optional wear events. | Player state authority. |
| Encounter Director | Start/pause/restart, phase configuration, survival trigger, result. | Individual firing, damage formulas or story. |
| Feedback Adapter | State-to-animation/audio/FX/camera signals, optional diegetic indicators. | Gameplay authority or damage calculation. |
| Test Harness | Feature flags, presets, scenarios, telemetry and test logs. | Gameplay data except through approved APIs. |

Required event vocabulary
Suggested stable events (names are illustrative, not mandated Blueprint identifiers): UmbrellaConfigChanged;
LiftAvailabilityChanged; PlayerHealthChanged; ProjectileSpawned; ProjectileContact; CatchAttempt;
CatchSucceeded; CatchFailed; BossTargetHit; BossAttackTelegraphed; WindEntered; WindExited; PlayerDefeated;
EncounterCompleted; TestPresetLoaded. Each event carries timestamp/frame, source ID, target ID and
run/configuration ID if applicable.

Event contracts and failure modes
- Every module documents required inputs, emitted events, editable parameters, side effects, dependencies and safe disable behavior.
- No circular hard dependency between player motor, health system and boss director. Communication may use shared events/interfaces.
- A disabled optional module must leave basic movement, health, defeat, restart and encounter progression functional.
- Parameter changes should load at scenario restart by default unless the module explicitly supports safe runtime changes.
- Unknown events and missing assets should produce a logged fallback, not an invisible hard crash.

## 5. Feature manifest and option ownership

Recommended canonical feature record fields: feature_id, name, status, owner, priority, default_enabled,
dependencies, conflicts, parameters, required_events, tests, implementation_commit, known_limitations. Track
changes to statuses rather than changing prose silently.

| ID | Feature / default for proposed test build | Dependencies | Isolation |
|---|---|---|---|
| UMB-02 | Closed aiming / OFF | Umbrella state, attack module | Toggle at reset |
| UMB-03 | Sideways catching / OFF | Umbrella state, defense receiver | Toggle at reset |
| UMB-04 | Inversion / OFF | Wind, umbrella state | Toggle at reset |
| COM-01 | Automatic attacks / ON for full baseline once trigger approved; OFF for isolated motion | Attack module, optional UMB-02 | Scenario switch |
| COM-02 | Clock interrupt / OFF | Attack contact, boss target map | Toggle + scenario |
| COM-03 | Wing changes wind / OFF | Attack contact, wind director | Toggle + scenario |
| COM-04 | Body hit response / OFF | Attack contact, feedback | Toggle |
| SURV-02 | Condition affects lift / OFF | Health/condition, motor | Toggle at reset |
| SURV-03 | Successful catch restores condition / OFF | UMB-03, condition resource | Toggle at reset |
| WIND-01 | Wind force / OFF in base movement test | Wind/hazard field | Toggle + scenario |
| WIND-02 | Wind wear / OFF | WIND-01, condition resource | Toggle |
| OWL-02 | Wing gust attack / OFF | Wind/hazard field, boss director | Toggle + scenario |
| OWL-04 | Returning projectile / OFF | Projectile service, path spec | Dedicated scenario |
| HAZ-01 | Steam vent / OFF | Hazard field | Dedicated scenario |
| VFX-01 | Background pressure motif / OFF | Feedback adapter, progress | Toggle |

These OFF defaults are proposed test-harness defaults, not decisions to exclude the ideas. All approved P0 systems
are ON in the first intended baseline once production begins.

Feature lifecycle
11. Propose with rationale and expected player decision.
12. Approve a bounded experiment plus test owner and pass/fail criterion.
13. Generate feature implementation in an isolated branch or component.
14. Run automated checks and an independent human A/B test.
15. Promote to APPROVED_P1/P0, revise, disable or defer; log what changed and why.

## 6. Player survival, health and recovery
- CORE-03: Damage is limited and visible; health depletion or bottom-boundary crossing ends an attempt.
- Do not assume health and umbrella integrity are two separate resources. The initial implementation may use one health value with umbrella visuals until the team explicitly approves dual resources.
- EXPERIMENT: three hit points, invulnerability window and stagger/hit reaction. Values are tuning variables.
- EXPERIMENT: one successful side catch sends CatchSucceeded, enabling a distinct recovery module that can restore health, lift condition or neither.
- If worn umbrella reduces lift, require a test that verifies recovery remains possible and that the player is not forced into an unwinnable fall spiral.
- Upper and side arena bounds should be safe or contained unless another explicit hazard is approved. Bottom is the required defeat boundary.

## 7. Boss, projectiles, wind and arena

Boss patterns and target zones

| Item | Description | Priority |
|---|---|---|
| Base bolt | One clearly telegraphed slow enough projectile type. Configurable delay, direction, speed and collision. | Recommended P0 |
| Wing gust | Telegraphed force zone, wind enters/exits, optional umbrella wear. | P1 candidate |
| Returning arc | Curving/boomerang projectile; requires a reviewed diagram and trajectory specification before building. | Experiment |
| Clock target | Successful hit may interrupt currently prepared attack. | Experiment |
| Wing target | Hits may alter future wind attacks with a tradeoff. | Experiment |
| Body target | Nonlethal confirmation and contact response. | P1 candidate |
| Steam vent | Environmental timed obstacle independent of owl AI. | Experiment |
| Complex pattern | Combine only attacks that have passed individual readability and recovery testing. | P1/P2 |

Encounter space
- Gameplay uses a single constrained 2D movement plane even if art is layered in depth.
- Use fixed camera and visible safe play area. Enemy location should preserve time to react and opportunities to reposition.
- Define projectile spawn area, collision shape, lifetime, and telegraph separately from attack pacing.
- Every hazard has a warning, active interval, recovery interval and reset behavior; expose them as parameters.
- If wind hurts the umbrella, mark hazardous winds distinctly from beneficial currents and allow intentional acceptance of risk.

## 8. Encounter control and progression
The goal is survival until a clear departure event. Encounter Director accepts a configurable completion rule and
emits EncounterCompleted. A simple duration-based rule is acceptable only as a prototype placeholder, not as an
approved story/gameplay decision. The system should also support a future alternate trigger without rewriting owl
attacks.

| State | Entry / exit rule |
|---|---|
| READY | Load approved preset, reset all modules and place actors; await start. |
| ACTIVE | Accept player input, owl attack scheduling, hazards and damage. |
| ENDING_SUCCESS | Completion rule triggers; stop/disable threats, owl departs, show unmistakable outcome. |
| ENDING_FAILURE | Health zero or bottom boundary; stop interactions and display clear defeat. |
| RESTARTING | Clear active projectiles, timers and state, restore configuration and return to READY. |
| PAUSED | Suspend simulation according to a single owner to prevent stale timers or inputs. |

Suggested progress phases (introduction, contest, desperation) are tuning presets, not required numbered phases or
a hardcoded percentage of the total timer. Do not equate the owl chest clock with a visible completion timer without
explicit approval.

## 9. Feedback, readability and accessibility
- Main presentation should favor diegetic status indicators: the umbrella for condition, the owl/clock for enemy state, wing pose/flow for gusts, distinct projectile silhouette for threats.
- A tiny developer-only overlay is permitted in test builds: it is not part of the intended player HUD.
- Audio signals can reinforce telegraphs, hits, catches, and pacing; required hazards also need visual cues.
- Display explicit start, defeat and success feedback. Clear retry should be possible without an editor restart.
- Support keyboard and controller input, default comfortable bindings and keyboard-only testing. Final mapping remains OPEN.
- For art implementation, retain layered 2D presentation, clockwork/owl motif and illustrated gothic contrast, but do not require narrative-specific animations.

## 10. Human tester workbench (required pipeline capability)
The team wants to compare candidate mechanics one by one and in combinations. Provide a test-accessible
configuration panel or equivalent data-driven workflow in development builds. Feature modules may need
generation after the jam starts; the pre-jam pipeline itself should be able to generate such a harness.

| Tester capability | Acceptance behavior |
|---|---|
| Feature toggles | A tester sees which options are enabled. Incompatible options are blocked with a plain-language explanation or require reset. |
| Parameter tuning | Move speed, lift, gravity, projectile speed, cadence, damage, gust force, and wind wear can be adjusted within safe ranges where implemented. |
| Named presets | Save/load baseline, wind, combat, catch, condition and combined configurations with persistent IDs. |
| Scenarios | Start at specific test points with controlled enemy patterns, hazard spawns and player position. |
| Reproducibility | Record build ID, feature manifest version, preset, random seed and start conditions. |
| Feedback | Tester records a short note: fun, clarity, difficulty, suspected bug, preferred variant. |
| Restart/reset | One action restores state and clears lingering effects. |
| Log/export | Export/share config and feedback as text or JSON without requiring nonproject personal data. |

Suggested test presets (not actual gameplay modes)

| Preset ID | Enabled candidate features | Learning goal |
|---|---|---|
| T-01 BASE | Approved P0, including auto attack once trigger defined; separate movement-only smoke tests may disable it. | Is movement and survival fun in the simplest complete encounter? |
| T-02 AIM | UMB-02 + COM-01 if approved for test. | Is falling while aiming engaging and readable? |
| T-03 CATCH | UMB-03 + basic defense receiver. | Can players understand orientation and contact? |
| T-04 RECOVER | T-03 + SURV-03. | Does reward for catching create meaningful risk? |
| T-05 WIND | WIND-01; later WIND-02. | Are currents worth seeking and avoiding? |
| T-06 CLOCK | COM-02 + target hit event. | Does attack disruption matter strategically? |
| T-07 COMBO | Approved mechanics that passed individual tests. | Does the full encounter remain readable? |

## 11. Test catalog and acceptance criteria

| Test ID | Setup | Pass / failure evidence |
|---|---|---|
| QA-01 | UP_OPEN versus NO_LIFT at same spawn. | Upright-open rises; non-lift falls naturally; no state-specific fast fall. |
| QA-02 | Transition repeatedly across umbrella states. | No stuck input, unintended lift, excessive velocity or stale attack state. |
| QA-03 | Turn on a single telegraphed owl bolt. | Players can react; collisions register once; warning precedes danger. |
| QA-04 | Activate side catch only, if implemented. | Left and right directional catches behave as documented; failure is visible. |
| QA-05 | Enable recovery only with catch prerequisite. | Recovery fires once, modifies intended resource and cannot exceed max. |
| QA-06 | Apply damage then bottom-out. | Correct loss reason, proper feedback, clean restart. |
| QA-07 | Switch wind force and wear independently. | Forces work with no wear when wear is disabled; UI reflects actual state. |
| QA-08 | Set a deterministic owl pattern and random seed. | A repeated test gives same event ordering within reasonable engine variability. |
| QA-09 | Trigger departure during active attacks. | No post-victory lethal collision; success clearly visible; retry works. |
| QA-10 | Disable optional feature with active dependencies. | Safe rejection, reset or fallback with explicit log. |
| QA-11 | Package and launch a development Windows build. | Correct game mode, input, logs, success/failure UI; no missing assets. |
| QA-12 | Have testers (C and organizer) compare one setting at a time. | Each run has config ID and recorded preference/failure reason. |

Automated tests verify technical contracts; humans judge feel and fun. Successful automation does not mean a
feature is enjoyable. Tests should include a "why did this run fail?" category for player confusion, unfair pressure,
unresponsive controls and bugs.

## 12. Pipeline specification and safe handoff

Required pre-jam pipeline properties
- Create a clean Unreal project or generic sample using repeatable commands; verify UE 5.8.4 installation/compatibility.
- Agents have bounded repository/folder permissions and explicit approval before writes outside the project scope; no blanket local-machine access.
- Generate versioned modules and tests from an approved specification; report which feature IDs and decisions were used.
- Support create, edit, compile/validate, run tests, record errors, revert failed steps and resume from a known checkpoint.
- Create a generic test harness with feature toggles, parameter presets, reset, logging and scenario templates on unrelated synthetic objects before the jam.
- Capture agent identity, prompt/tool inputs, changed files, license/provenance of sourced assets, commit hash and test result for every change.
- Support one clean packaged development build, or a documented packaging error if target environment is not ready.
- Validate architecture with unrelated sample content. Do not instantiate game-specific umbrella/owl actors, attack patterns or art before the permitted jam start.

Recommended post-start generation order
16. Generate empty game project from frozen tooling and confirm build.
17. Create core 2D arena, player motor, normal falling and open-upright lift.
18. Add bottom defeat, minimal health state, clear restart and simple outcome trigger.
19. Add one owl with one telegraphed projectile; playtest P0 movement and threat readability.
20. Enable test harness and telemetry in an actual game-specific build.
21. Implement approved options in isolated modules, first alone, then in deliberate combinations.
22. Run automated regression tests, human playtests, adjust scope, polish and package early.

AI agent task format
Each generation ticket should include: task ID, approved GDD revision, required feature IDs, permitted files/folders,
interface contract, dependencies, test cases, status/priority, allowed assets, rollback point, owner and acceptance
gate. Agents return: changed files, assumptions made, screenshots/logs if applicable, test output, blockers, new
decision requests and commit hash.

## 13. Decisions that genuinely block a final game build

| Decision ID | Question | Safe interim behavior |
|---|---|---|
| DEC-01 | How do players request closed aiming or sideways catching? | Keep action bindings data-driven; only core open/close required. |
| DEC-02 | Does closed aiming cause automatic fire? | Build event seam; do not require COM-01 to operate. |
| DEC-03 | Is sideways catch block-only, repair-only or both? | Use CatchSucceeded event; effects are optional subscribers. |
| DEC-04 | Are umbrella condition and health the same? | Treat health as one resource pending approval. |
| DEC-05 | Does wear reduce upright lift? | No reduction unless experiment is approved. |
| DEC-06 | What causes the owl to depart? | Use configurable completion rule; prototype timer is only a test fixture. |
| DEC-07 | Which gust risks are desirable? | Start with visible force only; add wear after isolated review. |
| DEC-08 | Which owl target effects matter? | Keep target mapping optional; body hits may be feedback-only. |
| DEC-09 | How should progression be communicated without a HUD? | Clear telegraphs and end screens first; motif later. |
| DEC-10 | How does theme affect core mechanics after reveal? | Add bounded theme mapping and explicitly approve its effects. |

## 14. Production and governance

| Role | Responsibilities |
|---|---|
| Design owner (Rick, per working notes) | Approve mechanics, priority changes, GDD revisions and the core gameplay experience. |
| Technical/pipeline owner (Josh) | Agent orchestration, project/UE setup, architecture, coding/test workflow and logs. |
| Implementation support (R, per team arrangement) | Review integration problems, make bounded adjustments and help resolve engineering issues. |
| Human testers (C and organizer) | Run standardized presets, compare fun and fairness, record issues and recommend mechanic promotion/removal. |
| All team members | Review theme fit, submission readiness, sourced-asset declarations and final build. |

Role assignments are based on the working team description and may change with group agreement. A test result
never auto-promotes a feature; the design owner and technical lead jointly authorize a changed build scope.

Schedule and compliance
- November 8–10: finalize GDD direction, agent interfaces and generic tooling tests. Keep all game-specific implementation out of pre-start builds.
- November 11: read official theme announcement, map new requirements, validate readiness. The official start is November 12 at 00:00 EST, equal to November 11 at 21:00 PST.
- After allowed start: game generation, build/test cycles and scoped feature decisions.
- November 15 at 17:59 PST: currently posted submission deadline; reserve earlier packaging and video time.
- Maintain provenance declarations for scripts/assets made before the jam, per organizer instructions.

## Appendix A. Preserved option backlog
None of these are assumed implemented. They can be evaluated with an explicit experiment ticket once the baseline
proves enjoyable.

| Theme | Candidates |
|---|---|
| Movement | Umbrella inversion, emergency recovery, side orientation control, momentum tuning, different wind directions, condition-dependent lift, altitudinal positioning. |
| Attack | Closed aim, automatic shots, range/alignment bonus, charged wand shot, dive-to-charge, timed vulnerability, clock disruption, body confirmation. |
| Defense | Sideways shield catch, perfect catch bonus, absorption restores condition, one-time emergency shield, visual catch feedback. |
| Owl | Returning arc, clockwork bolts, gusts, gear hazards, wing weakening changes wind, behavior adaptation, layerable attack patterns. |
| Arena | Steam vents, pipes, timed obstacles, horizontal/diagonal air currents, safe upper/side boundaries, wind-wear tradeoffs. |
| Progression | Introduction/contest/desperation pacing, optional player-responsive pressure, clear owl departure, nonlethal boss resolution. |
| Art/audio | Background wilting/eclipsing/lighting changes, music intensification, clock animations, umbrella tears, strong silhouettes. |
| Narrative | Ella, the clockkeeper, night/dawn transition, stolen clock hand in umbrella, mysterious departure, chapter framing. Entire category DEFERRED. |

## Appendix B. Example agent-readable feature record
Illustrative record below. IDs and values are proposed conventions, not Unreal configuration syntax. A technical
lead can implement it as DataAssets, JSON, tables or other versioned configuration.

```text
feature_id: UMB-03
name: sideways_projectile_catch
status: PROPOSED
priority: P1_candidate
default_enabled: false
requires: [umbrella_state, defense_receiver, projectile_contact]
conflicts: []
configurations: [OPEN_LEFT, OPEN_RIGHT]
emits: [CatchAttempt, CatchSucceeded, CatchFailed]
parameters: [catch_arc, catch_window, catch_cooldown]
reset_required_for_toggle: true
acceptance_tests: [QA-02, QA-04]
implementation_authorized: false
owner: unassigned
```

## Appendix C. Test note template

| Field | What to record |
|---|---|
| Build / run | Commit SHA, GDD revision, test ID, feature preset, random seed, date. |
| What changed | The ONE important variable changed versus the comparison run. |
| Observed | Controls, visual clarity, failure reason, surprising interactions and reproducible steps. |
| Ratings | Fun, fairness, readability and responsiveness, each 1–5 (team scale). |
| Decision | Keep, revise, remove, retest. Include owner and a short rationale. |

## Appendix D. References and rule verification
- 2026 Epic AI MegaJam official jam page: https://itch.io/jam/2026-epic-ai-megajam
- Epic organizer preparation FAQ: https://forums.unrealengine.com/t/vibe-your-way-to-50k-the-2026-epic-ai-megajam-is-coming/2843973
- Unreal Engine 5.8 Automation Test Framework: https://dev.epicgames.com/documentation/unreal-engine/automation-test-framework-in-unreal-engine
- Unreal Engine 5.8 Gameplay Systems: https://dev.epicgames.com/documentation/unreal-engine/gameplay-systems-in-unreal-engine
- User-provided screenshots of Rick's draft and team's subsequent umbrella decisions, November 8, 2026.

---

<!-- source: docs/gdd/archive/gdd-umbrella-ella-draft1.0.md -->

> **SUPERSEDED.** This is the old Draft 1.0 (6 Nov 2026). It was replaced by GDD B1.0 (`docs/gdd/GDD-B1.0.md`, 8 Nov 2026).
> Kept for history only. It is not in any agent read order. Never build from it.

# GDD snapshot: THE LAST HOUR (working title), Draft 1.0

Read-only snapshot for agents. Do not edit it to change the design.
Source: Google Doc "Umbrella Ella GDD Draft v1", id `1m3seh8jm58AnBLvH0Mx1G-wuyZ3Yuh7wh3V1REt-ONY` (docs/references.md R6).
Copied 2026-11-07. Doc date: 6 Nov 2026. Status in the doc: design draft for team review.
The game design owner edits the Google Doc, then refreshes this copy in a PR.
Where this snapshot and a DECIDED row in `docs/decisions.md` disagree, the DECIDED row wins.
Open review comments on the doc are open rows D1 and D27-D33 in `docs/decisions.md` (owner: game design owner). Until they are decided, build the text below.
This replaces the earlier Draft 1 (a five-section platformer). That design is no longer used.

```text
THE LAST HOUR — working title | Draft 1.0 | 6 Nov 2026 | STATUS: design draft for team review. CONFIRMED vs PROPOSED vs OPTIONAL labels are binding.

Pitch: Survive a desperate aerial encounter against a giant clockwork owl by opening a fragile magic umbrella to rise, closing it to fall and dodge, and using dangerous winds to reposition before the last hour ends.
Constraints: UE 5.8.4; 2D-styled single-screen landscape encounter, fixed camera; art: gothic illustrated storybook, parchment, sepia, ink silhouettes, restrained amber and red accents (key art: pipeline/art/reference/target-keyart.png); one boss; minimal animation states; single player; PC keyboard proposed baseline; minimal narrative — the owl survives and leaves if the player endures.
Pillars: ascend vs fall (umbrella states trade-off); risk/reward in the wind (strong lift can damage the umbrella); a world that communicates (umbrella tears show lift loss, clockwork shows boss condition, background motif + sound show approaching end); small scope, large character.
§2 CONFIRMED: survive until the owl departs; the hero does not kill it; losing all health or exiting through the bottom = failure; duration set by playtests. PROPOSED phases by normalized timer: 0-25% intro (simple spaced projectiles, one gust); 25-70% contest (projectiles + telegraphed winds); 70-100% desperation (torn umbrella weakens ascent; harder but fair; recovery routes); end event (owl pauses, departs, clue remains; no lethal attacks after trigger). PROPOSED: at end trigger stop threats, short exit, explicit "Survived" end card. Must be winnable without targeting any owl component.
§3 Loop: observe tells → choose altitude + umbrella state → ascend or fall/reposition → optionally catch a gust (lift at durability risk) → keep an automatic firing line to the owl → survive next attack → repeat until countdown completes.
Controls (PROPOSED keyboard): A/D or Left/Right move horizontally; W/S steer vertically within rise/fall constraints (cannot turn closed-state fall into sustained ascent); Space hold = umbrella open, release closes (subject to UX test); Attack automatic in valid firing geometry, no attack button; Esc/P pause.
§4 Open: CONFIRMED gains altitude, slower/less agile horizontally. PROPOSED fixed upward accel, terminal rise speed scaled by umbrella condition. Gusts amplify rise; strong gusts wear umbrella. Closed: CONFIRMED falls, faster and more precise. PROPOSED gravity to capped fall speed; higher horizontal accel. Closing prevents gust wear. Deterioration: CONFIRMED INTENT visibly tears and loses lift; PROPOSED normalized integrity reduced by strong gusts and direct hits, lift falls with integrity, 3 visual tiers (intact/damaged/critical), never unwinnable without warning and recovery. Wind: PROPOSED one telegraphed gust zone, one direction/type for v1.
§5 CONFIRMED (disputed in comments): attacks automatic. PROPOSED wand bolt at fixed cadence when owl in broad firing lane with line of sight; no separate aim; can hit clock (briefly disrupts an attack), wings (weakens future gusts, visible tears), body (feedback only, no boss health bar). Owl not killable. OPTIONAL clock-fracture slow motion (not MVP).
§6 PROPOSED owl stays on right half, modest vertical drift; hero left/center. Patterns: clockwork bolts (amber clock flash + wind-up; simple spread; one reusable projectile, configurable angles), returning arc (red arc trail; curved/returning; P2), wing gust (wing pose + flow lines; timed rectangular gust zone; P1). One main pattern at a time initially.
§7 CONFIRMED limited health; health depletion and bottom boundary = defeat. PROPOSED 3 HP, brief invulnerability after damage, clear hit reaction; top/side boundaries contain or bounce; retry returns to start with minimal delay; no-HUD preference but a small diegetic indicator beats ambiguity; never convey timing by music alone; remapping if practical.
§8 Feedback: umbrella fabric = lift/risk; owl chest clock = mechanism condition (NOT the encounter timer by default); wing holes = wind change; background motif = encounter progress (one concept: eclipse / receding light / wilting emblem); music and audio = escalating urgency, distinct sounds for gust windup, projectile launch, hits, state change; projectiles high contrast vs sepia. Key art is aesthetic inspiration, not an asset list. Animation budget: hero open/closed, owl resting/attacking/reacting, umbrella 3 texture states, clock hands rotation, wing damage overlay; reuse transforms, particles, layer motion.
§9 Narrative EXPLORATORY: owl = ancient clockkeeper bound to an unnatural hour; young witch with failing umbrella of unfamiliar time magic; survive, owl leaves; opening card, visual clue, ending card if needed.
§10 P0/Must: single arena, 2 umbrella states, horizontal/vertical steering, collision, one projectile pattern, automatic firing, health/failure, fixed survival-end trigger, restart. Acceptance: a new player can survive or fail a full loop; state changes visible and responsive. P1: gust zone, umbrella wear + visual tiers, environmental countdown, clock/wing hit feedback, second owl pattern, simple ending. P2: clock-fracture slow-mo, target-specific balance changes, returning projectile, time distortion, branching lore.
§11 Gates: movement prototype (players predict rise/fall, recover altitude, know why they failed); wind integration (players choose to catch or avoid gusts); combat integration (shots land when players deliberately align); full encounter (fair, replayable, paced; record time, failure cause, damage, umbrella use); readability (players read wear, health, remaining time without HUD). No encounter length or balance values approved yet.
§12 Open team decisions: progress motif; keyboard input approach and firing lane vs mild aim assist; clock/wing hit effects; health signaling without HUD; end trigger, final owl behavior, clue; art capacity and animation states; platform target; time-slow only after movement prototype.
```
