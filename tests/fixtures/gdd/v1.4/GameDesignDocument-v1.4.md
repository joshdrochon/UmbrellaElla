# Umbrella and Owl Game Design Document

**Version 1.4 · First-trial baseline · 10 November 2026 · Design owner Richard**

This document defines the first v1.4 playable trial. Richard’s decisions govern the game. The values below are the concrete starting settings for the trial and can be revised after playtesting. The [v1.3 master PDF](https://github.com/RickTheBuilder/GameJam2026/blob/3af5731a48b4014ccff76a5050625e0cd25a90e0/GameDesignDocument.pdf) is the prior master baseline. Rick’s rehearsal supplies reference mechanics and trial art. Pipeline adoption and release are separate approval steps.

[Game flow](#game-flow) · [Controls and physics](#controls-and-physics) · [Arena fixture](#arena-fixture) · [Owl attacks](#owl-attacks) · [Combat and recovery](#combat-and-recovery) · [Art and assets](#art-and-assets) · [Trial build contract](#trial-build-contract) · [Acceptance](#acceptance) · [Revision and migration](#revision-and-migration) · [Asset source pins](#appendix-a-asset-source-pins)

| Publication | Value |
| --- | --- |
| Revision | 1.4 |
| Build target | First-trial design for the next v1.4 implementation |
| Pipeline import | Use this package with each downloaded pipeline copy. The repository's pinned scaffold snapshot has its own migration gate. |

## Game definition

Ella drops into a fixed-screen arena from the top left. The clockwork owl waits on the right. Ella spends altitude to fall and fire, holds Rise to gain it back, and uses Absorb to catch a recovery shot while descending. Two leftward paths from the owl ask her to choose when to climb and when to fall. The chest clock briefly slows red projectiles. The body is the damage objective.

The initial target is Windows, keyboard and mouse, and controller. Use a fixed 16:9 camera, one gameplay plane, a safe top and sides, and a lethal bottom during combat. Background layers move independently of the camera and collision. Health, attack warnings, recovery, and phase changes read through poses, wear, effects, and sound. Brief tutorial prompts and start, pause, and result choices are the player-facing text.

| At a glance | Player experience |
| --- | --- |
| Move | Hold Rise to gain altitude. Release both actions to fall and fire. Hold Absorb to catch eligible shots while falling. |
| Fight | Read two leftward paths, find a vertical escape, and line up body damage. Hit the chest clock to briefly slow red shots. |
| Progress | Play or skip the controls tutorial. Damage advances the fight into Phase 3 and wins it. Retry starts a fresh boss attempt. |

## Game flow

| ID | State | Entry and exit |
| --- | --- | --- |
| FLOW-START | Start | Focus **Play Tutorial** by default. **Skip Tutorial** starts Phase 2. Confirm with Enter or controller South. |
| FLOW-P1 | Phase 1 · Controls | Start with the [entrance](#arena-fixture). Advance through the tutorial table on successful actions. **Skip Tutorial** is also available while paused here. Completion and Skip use the same fresh Phase 2 initialization. |
| FLOW-P2 | Phase 2 · Opening fight | Reset Ella and the owl to full HP, reset attacks and effects, and play the same entrance. Release control into normal combat at the end of the entrance. Owl HP reaching the Phase 3 gate starts the phase change. |
| FLOW-P3 | Phase 3 · Finish the fight | Enter at the body HP gate. Resume after the phase cue. Reach zero owl HP to win. |
| FLOW-RESULT | Victory or defeat | Stop new actions and clear active threats immediately. On victory, hold the owl still for the result delay, then have it retreat right as the result appears. Defeat holds Ella’s last pose with a clear loss cue. Both results offer **Retry** and **Return to Start**. Retry starts a fresh Phase 2. |

| Setting | Value | Apply |
| --- | --- | --- |
| P3_GATE | 50% of max owl HP, rounded up | Require at least 2 max owl HP and clamp the gate between 1 and max HP minus 1. When a Phase 2 hit reaches or crosses the gate, set owl HP to the gate and discard excess damage. Even an extreme damage preset must enter Phase 3. |
| P3_TRANSITION | 0.60 s | Combat, input, and countdowns freeze while the cue plays. |
| RESULT_DELAY | 0.75 s | Delay before result choices become available. Victory retreat then moves the owl right at 260 cm/s until offscreen. |
| PAUSE | Escape / controller Menu | Freeze gameplay, lesson clocks, transitions, and all projectiles. **Resume** and **Return to Start** are available, plus **Skip Tutorial** in Phase 1. |

### Phase 3 handoff

1. At the gate, clear all active projectiles, warnings, pending launches, and clock slowdown.
2. Hold Ella’s position and velocity during the cue. Carry her HP and remaining post-hit protection forward. Pause the protection timer and fire cooldown.
3. At the end of the cue, restore velocity, resolve fresh input, and reset the attack beat index. Default fire can resume when the existing cooldown is ready.

Menu Up and Down or controller D-pad Up and Down change focus. Pause opens focused on Resume. Results open focused on Retry. Start, pause, skip, and retry commands consume the confirming press. At the start of active play after a menu, entry, or phase change, sample steering normally and require any held Rise or Absorb button to be released before it can act again. Default falling fire resumes from the normal state rules. A simultaneous player defeat and boss result resolves to player defeat. Resolve either outcome once.

### Tutorial prompts

Show one short line with glyphs from the active bindings. Default fade-in is 0.15 s. On success, hold the prompt and cue for 0.45 s before the next lesson. Show a fresh prompt when the state changes. There is no countdown, health bar, or phase meter.

| ID | Prompt | Completion and setup |
| --- | --- | --- |
| TUT-FALL | “Let yourself fall. Your umbrella will answer.” | After the entrance, fire one shot while descending. A practice hit gives feedback and changes no owl HP. |
| TUT-RISE | “Catch the air above you. Hold [Rise].” | Show as soon as the previous lesson clears. Gain 30 cm from the lowest point recorded while holding Rise in this lesson, or hold Rise against the ceiling for 0.25 continuous seconds. |
| TUT-STEER | “Find a clear lane. Move with [Left] and [Right].” | Move 70 cm horizontally from the position where the prompt appeared. Either direction qualifies. |
| TUT-WIND | “Feel the pull of the wind. Hold [Rise] in the current.” | Hold Rise inside the visible current for 0.25 continuous seconds. The current itself works whenever Ella is inside it. |
| TUT-ABSORB | “Open your umbrella to the golden spark. Hold [Absorb].” | On entry to this lesson, place Ella at (−550, 200) with zero velocity, and set HP to 85 to show repair. After a 0.35 s warning, launch one yellow shot at X + 110 cm, Z equal to Ella’s canopy at launch, moving horizontally left. Use normal capture rules. If uncaught after 2.0 s from launch, clear it and reinitialize this lesson. Capture completes the tutorial. |

Phase 1 is protected and red attacks are disabled. Uncaught yellow shots disappear on contact without damage in practice. If Ella reaches the bottom before the last lesson, clear practice shots, respawn at (−600, 300) with zero velocity, and restart the current lesson with fresh completion progress and position references. In the last lesson, use its own reset point. Tutorial HP, shots, and hits stay in Phase 1.

## Controls and physics

| ID | Action | Keyboard and mouse | Controller |
| --- | --- | --- | --- |
| INPUT-STEER | Left and right | A / D | Left stick X |
| INPUT-RISE | Hold Rise | Space | Right trigger |
| INPUT-ABSORB | Hold Absorb | Right mouse | Left trigger |
| INPUT-CONFIRM | Confirm menu choice | Enter | South face button |
| INPUT-PAUSE | Pause / resume | Escape | Menu |

Default fire is automatic. Remap gameplay bindings in the development settings and substitute the active binding into prompts. Digital left plus right resolves to neutral. The active device is the last device used for a button press or deliberate steering. Gamepad steering deadzone is 0.20, with the remaining magnitude rescaled linearly to 1. Triggers are held at or above 0.50. If both devices send steering on the same step, use the active device.

| Priority | State ID | Condition | Motion and action |
| --- | --- | --- | --- |
| 1 | ELLA-LOCKED | Entrance, pause, phase-change cue, or result | Scripted entrance, held pose, or result presentation. Gameplay actions are suspended. |
| 2 | ELLA-RISE | Rise held, including when Absorb is held | Open umbrella overhead, move toward rise speed, and suspend shooting and suction. |
| 3 | ELLA-ABSORB | Absorb held with Rise released | Open canopy forward, fall under ordinary gravity, and pull eligible shots. |
| 4 | ELLA-FIRE | Neither action held | Closed umbrella aimed right, fall under ordinary gravity, and fire toward +X from its tip. |

| Setting ID | Default |
| --- | --- |
| MOTION-STEP | 120 simulation steps per active second, with swept projectile contacts. Use the same step rate for entrance, phase-transition, and result presentation clocks while the combat clock is stopped. Pause stops both clocks. |
| MOTION-HORIZONTAL | Steering on. Target velocity is input × 350 cm/s. Approach it at 1,800 cm/s², including braking toward zero on release. Apply in all three active states. |
| MOTION-RISE | Approach +300 cm/s intrinsic vertical speed at 1,200 cm/s² while Rise is held. Damage leaves lift consistent. |
| MOTION-FALL | Gravity is 980 cm/s² downward in either falling state. Cap intrinsic fall speed at 650 cm/s. |
| MOTION-CARRY | On leaving Rise, retain 50% of signed intrinsic vertical velocity once. Swapping between falling states preserves velocity. |
| MOTION-WIND | One safe updraft contributes +180 cm/s to vertical displacement while Ella’s root is inside the wind volume. It does not accumulate in intrinsic velocity. Entry, pause and phase transition use their own locked motion rules. |

Apply the resolved action and movement for each step, then swept collision and result resolution. Steering never rotates shots. At the top or side clamp, zero any intrinsic velocity component pushing outward. Integrate the wind contribution before clamping. Keep gameplay anchors fixed relative to Ella’s root as poses change. The visible umbrella tip and canopy align to their active anchors.

## Arena fixture

Coordinates are centimeters in the X/Z gameplay plane at Y = 0. X increases right and Z increases up. Bounds below use the gameplay root or center, as labeled. Boxes are axis-aligned and dimensions are full width × height.

| ID | Geometry and setup |
| --- | --- |
| FIX-CAMERA | Center (0, 0), view 1,600 × 900. View bounds X −800 to 800 and Z −450 to 450. No camera tracking or shake in the default trial. |
| FIX-ELLA | Ella’s center clamps to X −740 through +320 and a ceiling of Z 405. Her hurtbox is 44 × 72. Its lower edge touching Z −450 triggers the bottom rule. |
| FIX-ENTRY | Start Ella at (−600, 495), slightly above the top left. Drift straight down at 150 cm/s for 0.60 s, ending at (−600, 405). Use the closed falling pose. Suppress fire, collision, and owl scheduling during entry. Enable control at the endpoint with vertical velocity −150 cm/s. The phase clock starts when controls unlock. |
| FIX-WIND | Updraft rectangle X −320 to −140, Z −240 to +260. The volume is active throughout playable phases. No wear or forced gust in the default trial. |
| FIX-ELLA-ANCHORS | Relative to Ella’s root. Closed umbrella muzzle (+47, +4). Forward-open canopy and capture center (+39, +3). |
| FIX-OWL | Static owl root at (560, 0), facing left. Coordinates in the owl region table are world positions. Visual animation can flap around the fixed anchor. |
| FIX-FIRING | Upper red origin (480, +104). Lower red origin (506, −62). Yellow origin (496, 0). |
| FIX-PARALLAX | Far layer scrolls left at 0.25% viewport width per second. Near layer scrolls left at 1% per second. Repeat horizontally during entry and active play. Reset offsets for a fresh Phase 1 or Phase 2 entry. Preserve offsets through Phase 3 and freeze them during pause, phase transition, and results. |

| Region ID | Group | Collider at world position | Ella projectile response |
| --- | --- | --- | --- |
| OWL-BODY-UPPER | BODY | Box 190 × 128 at (580, +95) | Body HP damage |
| OWL-BODY-LOWER | BODY | Box 170 × 54 at (600, −56) | Body HP damage |
| OWL-CLOCK | CLOCK | Circle radius 40 at (560, 0) | Red projectile slowdown progress and zero body damage |
| OWL-FEET-FRONT | FEET | Box 52 × 36 at (525, −94) | Block and zero damage |
| OWL-FEET-REAR | FEET | Box 50 × 36 at (620, −105) | Block and zero damage |
| OWL-TAIL | BODY | Box 106 × 124 at (685, −163) | Body HP damage |
| OWL-BALL-FRONT | BODY | Circle radius 15 at (535, −162) | Body HP damage |
| OWL-BALL-MIDDLE | BODY | Circle radius 15 at (575, −190) | Body HP damage |
| OWL-BALL-REAR | BODY | Circle radius 15 at (617, −141) | Body HP damage |

Each Ella shot resolves the earliest swept region contact. If regions tie, resolve **FEET → CLOCK → BODY**, then row order within the group. Consume the shot once. The clock balls and tail are reachable below the feet and use the same HP pool as upper and lower BODY. Ella cannot physically reach the owl’s contact geometry within her movement bounds.

## Owl attacks

The default creates overlapping threats from two heights and leaves a reachable vertical escape route. Use both visual warnings before either red shot launches. Commit both red directions at the start of the warning. Measure angle from directly left, with positive angles rising. Clamp the upper aim at Ella’s sampled center to [−30°, +30°]. Lower aim is upper aim +12°. If this would exceed +30°, use upper aim −12°. Angles remain fixed for that beat.

| ID | Pattern | Launch schedule |
| --- | --- | --- |
| RED-UPPER | Aimed upper red shot from FIX-FIRING | Launch at the end of the warning. |
| RED-LOWER | Offset lower red shot from FIX-FIRING | Launch 0.15 s after RED-UPPER. |
| RED-ECHO | Phase 3 echo from the original upper origin on its committed path | On even-numbered Phase 3 beats, show the repeat cue at the original upper launch, then launch the echo 0.45 s after the original. |
| YELLOW-RECOVERY | One gold/yellow recovery shot from FIX-FIRING, aimed at Ella’s center when its warning begins and clamped to the same leftward sector | On red beats 2, 5, 8, and every third beat thereafter, start the yellow tell 0.55 s after RED-UPPER launches. Launch 0.45 s after that tell. The resulting shot launches 1.00 s after RED-UPPER. |

| Setting ID | Phase 2 | Phase 3 |
| --- | --- | --- |
| OWL-FIRST-WARNING | 0.60 s after entry hands over control | 0.60 s after the phase transition hands back control |
| OWL-RED-WARNING | 0.75 s | 0.70 s |
| OWL-RED-BEAT | 2.40 s warning-to-warning | 2.00 s warning-to-warning |
| OWL-RED-COUNT | Two per beat | Two per beat, plus RED-ECHO on even beats |

Beat 1 starts with the first warning. For beat n, warning start = first warning + (n − 1) × beat interval. Recovery uses the authored beat slot. The runtime keeps those commitments. If playtesting finds a gap unreachable, change the geometry or schedule in a named trial and rerun the overlap check. Cancel outstanding warnings and launches on phase change or a terminal result.

The first successful combat clear should feel like roughly 60–90 seconds of active decisions. This is an observation target. Phase and victory gates use damage only.

## Combat and recovery

| Setting ID | Default | Behavior |
| --- | --- | --- |
| HP-ELLA | 100 HP | Defeat at zero HP or the combat bottom. |
| HP-OWL | 500 HP | Shared body pool across both boss phases. |
| HIT-PROTECTION | 0.80 s | Successful damage grants protection against projectile damage. The bottom remains lethal. |
| SHOT-ELLA | 10 body damage, 0.65 s interval, 700 cm/s, radius 6 cm, 3.00 s lifetime | Start ready on fresh entry. Fire whenever the cooldown is ready in default fall and repeat on the interval. Keep one cooldown across stance changes. A phase transition freezes the cooldown. |
| SHOT-RED | 25 damage, 350 cm/s, radius 10 cm, 5.00 s lifetime | Dodge threat. |
| SHOT-YELLOW | 15 damage when uncaught, 220 cm/s, radius 9 cm, 7.00 s lifetime | Recovery opportunity with harmful ordinary contact in combat. |
| CLOCK-EFFECT | 1 hit, 20% red speed reduction, 1.00 s | Count chest clock hits in the current phase. At threshold, reset count and apply the multiplier to existing and new red shots. Refresh duration on another qualifying hit and keep one multiplier. Restore each shot’s base speed on expiry. Clear on phase change or retry. |
| ABSORB-GEOMETRY | 240 cm range, 60° full cone, 700 cm/s pull, 24 cm capture radius | Cone starts at the forward-open canopy center and points +X. A yellow shot within the cone is pulled toward the canopy while eligible. |
| ABSORB-HEAL | 12 HP per committed capture | Cap at the player’s configured maximum HP. At full HP still consume and show a successful capture. |
| ABSORB-FINISH | 0.125 s visual finish | Once contact with the active canopy capture volume occurs, commit the catch immediately. Consume the shot and credit the heal once on that step. The visual finish continues across stance changes. |

**Before canopy contact.** Releasing Absorb or pressing Rise ends suction on any uncommitted yellow shot. Restore its original heading and configured base speed from its current position. Lifetime continues to run while pulled. Process a simultaneous eligible canopy and body contact as a capture. A shot touching Ella’s body earlier counts as an ordinary hit.

**After canopy contact.** A committed shot cannot hit Ella, resume flight, or be captured twice. Changing stance cannot cancel the credited heal. Use the contact event to play the pull-in finish and repair cue. Visual completion carries no damage or healing authority.

Shots pass through one another. Ella’s shots only hit owl regions. Hostile shots only contact Ella’s hurtbox or active canopy as applicable. On player contact, consume hostile shots even during hit protection. In a simulation step, process swept contacts by path time, using capture before body at a tied yellow contact and earlier projectile spawn order for ties between different shots. At a tied combat outcome, player defeat wins. A projectile expires at its lifetime or after its center leaves the camera bounds by more than 64 cm on any side. Clock slowdown changes red speed only. Keep trajectories, warning times, launch times, lifetimes, and yellow and player speeds on their own rules.

## Art and assets

The illustrations below are embedded concept references. They show scale, palette, silhouette, the clock and feet, and direction of fire. A chain reaching across the arena in a concept does not add a chain attack to this baseline. Keep this folder and its `art-references` subfolder together when moving the GDD.

![Reference 1. Ella rises on the left while a bronze clockwork owl extends a hanging mechanism above a lakeside town.](art-references/gameplay-01.png)

*Reference 1 · Scale contrast, overhead umbrella pose, silhouette and layered scenery.*

![Reference 2. An owl with a prominent chest clock and hanging mechanisms fires a red volley toward Ella.](art-references/gameplay-02.png)

*Reference 2 · Chest clock, feet and hanging components, and readable leftward fire.*

The asset slot ID stays stable across replacements. `ART-*` names a required slot. `PH-*` names the baseline graybox implementation for a slot without matching art. **Rick trial source** identifies an actual source assignment for this local trial. Use the named fallback if the team explicitly selects the graybox art profile. Log the chosen mapping and file hash for each run. If a selected source fails import, report the slot and run a new pinned profile with its fallback. Any shipping reuse needs separate provenance, eligibility, and approval review.

### Arena art

| Asset slot ID | Need | First-trial assignment and fallback |
| --- | --- | --- |
| ART-ARENA-FAR | Far scenery | Rick [star-paper sky](https://github.com/RickTheBuilder/GameJam2026/blob/3af5731a48b4014ccff76a5050625e0cd25a90e0/Test_Assets/SKY_StarPaper_Tile.png). PH-ARENA-FAR is a flat warm-gray repeat tile. |
| ART-ARENA-FLOOR | Lethal bottom cue | PH-ARENA-FLOOR is a dark bottom band 18 cm high with a light top edge. No collider comes from art. |
| ART-ARENA-NEAR | Near scenery | Rick [gothic skyline](https://github.com/RickTheBuilder/GameJam2026/blob/3af5731a48b4014ccff76a5050625e0cd25a90e0/Test_Assets/ENV_GothicSkyline_Tile.png). PH-ARENA-NEAR is a flat charcoal silhouette occupying the bottom 12% of view. |
| ART-ARENA-WIND | Safe upward current | Rick [wind curl](https://github.com/RickTheBuilder/GameJam2026/blob/3af5731a48b4014ccff76a5050625e0cd25a90e0/Test_Assets/FX_Wind_Curl.png) within FIX-WIND, with a soft visible edge. PH-ARENA-WIND is a vertical line of upward-moving pale chevrons inside the same volume. |

### Ella art

| Asset slot ID | Need | First-trial assignment and fallback |
| --- | --- | --- |
| ART-ELLA-REPAIR | Capture finish and repair | Rick [umbrella repair effect](https://github.com/RickTheBuilder/GameJam2026/blob/3af5731a48b4014ccff76a5050625e0cd25a90e0/Test_Assets/FX_Umbrella_Repair.png) aligned to the canopy. PH-ELLA-REPAIR is a shrinking gold ring at contact. The capture finish duration is owned by ABSORB-FINISH. A trailing effect is cosmetic. |
| ART-ELLA-SFX-CATCH | Capture sound | PH-ELLA-SFX-CATCH is a soft two-tone rise, 440 to 660 Hz over 0.16 s. |
| ART-ELLA-FIRE | Closed forward wand pose | Hold zero-based frame 0 of Rick [Ella Shooting 03](https://github.com/RickTheBuilder/GameJam2026/blob/3af5731a48b4014ccff76a5050625e0cd25a90e0/Rehearsal/Art/Sprites/Ella/Shooting/Ella-Shooting-03.png). The shaft tip points right. The other frames open the canopy and are excluded from this slot. PH-ELLA-FIRE is a dark figure and a closed umbrella silhouette aimed through the muzzle. |
| ART-ELLA-DEFEAT | Ella defeat pose | PH-ELLA-DEFEAT holds the last visible pose and desaturates it. |
| ART-ELLA-ABSORB | Open forward fall | Rick [Ella Absorbing 04](https://github.com/RickTheBuilder/GameJam2026/blob/3af5731a48b4014ccff76a5050625e0cd25a90e0/Rehearsal/Art/Sprites/Ella/Absorbing/Ella-Absorbing-04.png), six frames. PH-ELLA-ABSORB is a dark figure with a visible semicircle at FIX-ELLA-ANCHORS. |
| ART-ELLA-RISE | Open overhead rise | Rick [Ella Rising 02](https://github.com/RickTheBuilder/GameJam2026/blob/3af5731a48b4014ccff76a5050625e0cd25a90e0/Rehearsal/Art/Sprites/Ella/Rising/Ella-Rising-02.png), six frames. PH-ELLA-RISE is a dark figure with a visible overhead canopy. |
| ART-ELLA-HIT | Player damage cue | PH-ELLA-HIT is a single 0.10 s light outline pulse on damage. |
| ART-ELLA-TRANSITION | Pose changes | PH-ELLA-TRANSITION switches pose on the resolved state step with a common body root. |
| ART-ELLA-SFX-FIRE | Shot sound | PH-ELLA-SFX-FIRE is a short 520 Hz pulse, 0.06 s. |
| ART-ELLA-WEAR | Wear across all poses | PH-ELLA-WEAR is an overlay on the canopy or closed ribs. Intact above 66% HP. One visible notch above 33% through 66%. Two notches at 33% or below while alive. Broken at zero. Rick’s [stance damage sheet](https://github.com/RickTheBuilder/GameJam2026/blob/3af5731a48b4014ccff76a5050625e0cd25a90e0/Test_Assets/PROP_Umbrella_Stance_Damage.png) is a wear reference for future compatible poses. |

### Owl art

| Asset slot ID | Need | First-trial assignment and fallback |
| --- | --- | --- |
| ART-OWL-CLOCK | Chest clock and slowdown reaction | PH-OWL-CLOCK is a brass disc matching OWL-CLOCK. Pulse once on contact and show a cool outer ring for the active slowdown. |
| ART-OWL-SFX-CLOCK | Clock slowdown cue | PH-OWL-SFX-CLOCK is a 0.15 s descending tick, 600 to 400 Hz. |
| ART-OWL-DEFEAT | Halt and retreat cue | PH-OWL-DEFEAT holds the owl with extinguished attack cues and then uses the FLOW-RESULT retreat. |
| ART-OWL-LOWER-TELL | Lower origin and aim | PH-OWL-LOWER-TELL marks the lower anchor with a short angled line along its committed path during the warning. |
| ART-OWL-FEET | Non-damaging shot blockers | PH-OWL-FEET draws two distinct dark-bronze talons over the FEET boxes. A brief pale spark marks a block. |
| ART-OWL-SFX-WARNING | Offensive warning | PH-OWL-SFX-WARNING is a 280 Hz pulse, 0.12 s. Both origin cues have distinct positions on screen. |
| ART-OWL-PHASE | Phase 3 transition | PH-OWL-PHASE gives the body a single expanding outline over P3_TRANSITION. |
| ART-OWL-TAIL | Reachable lower BODY surface | PH-OWL-TAIL uses a tapered bronze silhouette covering the tail collider. |
| ART-OWL-SFX-ECHO | Repeat tell sound | PH-OWL-SFX-ECHO is a short 360 Hz tick, 0.08 s. |
| ART-OWL-BALLS | Three visible BODY targets | PH-OWL-BALLS draws a chain and one brass ring or ball on each ball collider. The chain itself is decorative. |
| ART-OWL-BODY | Upper and lower damageable body | PH-OWL-BODY uses bronze shapes aligned to both body boxes. Rick’s [owl flap and damage atlas](https://github.com/RickTheBuilder/GameJam2026/blob/3af5731a48b4014ccff76a5050625e0cd25a90e0/Test_Assets/CHR_Owl_Flap_Damage.png) is the mapped candidate for an art-swap trial after silhouette alignment. |
| ART-OWL-UPPER-TELL | Upper origin and aim | PH-OWL-UPPER-TELL marks the upper anchor with a short angled line along its committed path during the warning. |
| ART-OWL-ECHO | Upper-path repeat | PH-OWL-ECHO pulses the upper origin and briefly redraws the committed upper direction until echo launch. |

### Projectile art

| Asset slot ID | Need | First-trial assignment and fallback |
| --- | --- | --- |
| ART-PROJ-YELLOW | Distinct recovery shot and capture | PH-PROJ-YELLOW is a gold circle with a double ring and dotted trail. It remains distinguishable by shape if color is hard to see. |
| ART-PROJ-ELLA | Fixed-right shot | Rick [wand star travel](https://github.com/RickTheBuilder/GameJam2026/blob/3af5731a48b4014ccff76a5050625e0cd25a90e0/Test_Assets/FX_Wand_Star_Travel.png) emitted from the umbrella tip. PH-PROJ-ELLA is a pale four-point star. |
| ART-PROJ-IMPACT | Hit or block flash | Rick [missile impact](https://github.com/RickTheBuilder/GameJam2026/blob/3af5731a48b4014ccff76a5050625e0cd25a90e0/Test_Assets/FX_Owl_Missile_Hit.png) for projectile impacts. PH-PROJ-IMPACT is a short fading ring. The contact cue for a foot block must look different from body damage. |
| ART-PROJ-RED | Leftward red shot and speed cue | Rick [owl missile travel](https://github.com/RickTheBuilder/GameJam2026/blob/3af5731a48b4014ccff76a5050625e0cd25a90e0/Test_Assets/FX_Owl_Missile_Travel.png), tinted red with a sharp trail. PH-PROJ-RED is a red pointed bolt with the same trail. A cool rim marks the clock effect. |

### Result art

| Asset slot ID | Need | First-trial assignment and fallback |
| --- | --- | --- |
| ART-RESULT-DEFEAT | Defeat, Retry, Return to Start | PH-RESULT-DEFEAT uses warm-gray lettering on a darkened arena. |
| ART-RESULT-VICTORY | Victory, Retry, Return to Start | PH-RESULT-VICTORY uses pale-gold lettering on a darkened arena. |

### Tutorial art

| Asset slot ID | Need | First-trial assignment and fallback |
| --- | --- | --- |
| ART-TUT-GLYPHS | Current keyboard/controller bindings | PH-TUT-GLYPHS prints the actual bound key or button name. |
| ART-TUT-SKIP | Explicit tutorial skip | PH-TUT-SKIP is a plain selectable Skip Tutorial line with the active confirm binding. |
| ART-TUT-PROMPT | Motif-matched in-world prompt | PH-TUT-PROMPT is light storybook text with a dark backing, placed in the safe left portion of the view. |

Use [Rick’s sprite layout](https://github.com/RickTheBuilder/GameJam2026/blob/3af5731a48b4014ccff76a5050625e0cd25a90e0/Test_Assets/SpriteLayout.json) and [Ella candidate layout](https://github.com/RickTheBuilder/GameJam2026/blob/3af5731a48b4014ccff76a5050625e0cd25a90e0/Rehearsal/Art/Sprites/Ella/CandidateLayout.json) for frame dimensions, pivots, and frame rates. Use the game anchors above for all mechanics, including the umbrella muzzle. The shooting placeholder uses a held frame. In other assigned Ella poses, use the candidate’s loop and common body anchor. Keep the art scale and offsets adjustable for alignment. [Rick’s asset notes](https://github.com/RickTheBuilder/GameJam2026/blob/3af5731a48b4014ccff76a5050625e0cd25a90e0/Test_Assets/Asset%20Notes.md) record the test-art provenance and import notes.

## Trial build contract

| Trial ID | Uses | Overrides |
| --- | --- | --- |
| TRIAL-DEFAULT | All gameplay tables and first-trial art assignments above. Normal damage, no debug aids. | None. Seed 20261112. Start from FLOW-START unless the trial record explicitly chooses FLOW-P2. |
| TRIAL-GRAYBOX | Same gameplay and seed | Use every named PH assignment. Record asset profile separately from gameplay. |
| TRIAL-STRESS | Development only. Same arena, phase gates, player movement, and damage. | Both boss phases use a 1.65 s red interval and 0.55 s warning. Keep RED-UPPER and RED-LOWER, then repeat those directions from their original origins at +0.30 and +0.45 s after RED-UPPER, with both extra launches included in the warning. Disable the separate Phase 3 echo in this profile. Yellow keeps its authored beat slot and timing. |

### First slider envelope

Use typed settings and reset between trials. The linked setting owns the default. Use explicit trial overrides for other changes. Reject any combination that schedules a committed red or yellow launch at or after the next red warning. The stress profile’s extra shots follow the same constraint.

| Slider | Default setting | Unit | Min | Max | Step |
| --- | --- | --- | --- | --- | --- |
| Horizontal max speed | [MOTION-HORIZONTAL](#controls-and-physics) | cm/s | 150 | 650 | 25 |
| Rise speed | [MOTION-RISE](#controls-and-physics) | cm/s | 100 | 550 | 25 |
| Gravity | [MOTION-FALL](#controls-and-physics) | cm/s² | 400 | 1,600 | 20 |
| Fall cap | [MOTION-FALL](#controls-and-physics) | cm/s | 250 | 1,000 | 25 |
| Rise-to-fall carryover | [MOTION-CARRY](#controls-and-physics) | % | 0 | 100 | 5 |
| Wind strength | [MOTION-WIND](#controls-and-physics) | cm/s | 0 | 500 | 20 |
| Red speed | [SHOT-RED](#combat-and-recovery) | cm/s | 150 | 900 | 25 |
| Phase red interval | [OWL-RED-BEAT](#owl-attacks) | s | 1.35 | 8.00 | 0.05 |
| Red warning | [OWL-RED-WARNING](#owl-attacks) | s | 0.30 | 1.50 | 0.05 |
| Lower angle offset | [RED-LOWER](#owl-attacks) | degrees | 4 | 24 | 1 |
| Lower launch stagger | [RED-LOWER](#owl-attacks) | s | 0.05 | 0.35 | 0.05 |
| Heal amount | [ABSORB-HEAL](#combat-and-recovery) | HP | 0 | 50 | 1 |
| Clock hits | [CLOCK-EFFECT](#combat-and-recovery) | hits | 1 | 10 | 1 |
| Red speed reduction | [CLOCK-EFFECT](#combat-and-recovery) | % | 0 | 60 | 5 |
| Clock effect duration | [CLOCK-EFFECT](#combat-and-recovery) | s | 0.25 | 3.00 | 0.25 |

### Trial evidence and promotion

Each build records the exact GDD content hash, build commit, trial ID, resolved settings and asset hashes or placeholder names, seed, and starting scenario. Reload the baseline on every new run and apply only that trial’s declared overrides. Fail preparation on conflicting values, missing required assets, or missing assignments. Report the specific ID. A new value becomes effective through an explicit override or approved revision. Art metadata cannot silently change collision, motion, or shot timing. Compare the settings loaded by the build with the pinned trial before reporting results.

Keep the approved feature manifest and acceptance mapping in sync when this GDD is promoted. That migration must replace v1.3’s survival timer and single-bolt assumptions in the affected checks. Keep input, player motion, shot collision, health, encounter flow, and presentation independently testable. Windows packaging and human approval are separate gates.

## Acceptance

| Check ID | Setup | Pass evidence |
| --- | --- | --- |
| QA14-ENTRY | Start, finish or skip the tutorial, and retry. | Ella eases into the frame high on the left. Both tutorial exits reach the same combat position, HP, controls and beat schedule. |
| QA14-INPUT | Hold both actions, release them in both orders, steer in every state, and rebind a control. | Rise wins. Releasing Rise selects Absorb if held. Releasing both selects fire. Steering remains independent. Signed carryover applies once and prompts show the active binding. |
| QA14-REGIONS | Shoot upper body, clock, each foot, and all lower targets. | One result per shot. Feet block. Balls and tail deal body damage. |
| QA14-RECOVERY | Release Absorb or press Rise before and after contact. Catch at full HP and take an uncaught yellow hit. | Only committed captures heal, once each. Full-HP catches consume and show the cue. An uncaught shot deals normal damage. |
| QA14-CLOCK | Compare the same schedule with and without clock hits. | Red speed changes while warning times, launch times, trajectories and yellow speed agree. A second qualifying hit refreshes one effect. |
| QA14-PHASE | Hit exactly on and past the gate, including with a high-damage override. Test simultaneous lethal outcomes. | A real Phase 3 starts with HP carried, position and velocity frozen through the cue, old shots cleared and fresh attacks. A lethal tie produces one defeat result. |
| QA14-PACING | Play a full default fight from Skip with debug aids off. Check the ceiling and floor with overlapping red, echo, yellow and slowed shots. Test stress separately. | Both origins read. Rise and fall routes and recovery opportunities remain viable. Record where escapes or recovery fail. |
| QA14-ASSET | Swap the art profile with identical gameplay settings and seed. Check both reference links. | Appearance changes and hit routes and outcomes agree. Import anchors, poses, clock, feet and balls remain readable. |
| QA14-PACKAGE | Launch the Windows package, test physical keyboard/mouse and controller, finish the fight, and retry. | Both input routes work through the encounter and retry. Record the build and resolved trial snapshot. |

The first playtest should judge the opening descent, availability of low and high routes, yellow catch reliability, and whether Phase 3 increases pressure without hiding the escape route. The spec and asset checks establish a repeatable starting point. First-clear timing, human feel, final art and release acceptance are playtest and review results.

## Revision and migration

| Revision | Record |
| --- | --- |
| v1.3 | Prior master baseline. Defined survival completion, an aimed single bolt, replaceable visuals, and the pipeline approval contract. |
| v1.4 | First-trial baseline. Adds a skippable controls tutorial, damage-driven boss phases, default falling fire, two-origin volleys, clock slowdown, committed recovery, and a pinned arena and asset grid. |
| v1.4 presentation pass | Condenses the overview and phase handoff, tabulates slider ranges and QA evidence, adds the crosswalk below, and separates human-readable fingerprints from full verification digests. |

The crosswalk identifies migration work. It does not create feature IDs or change an old ID’s meaning. The integration owner reconciles the manifest, presets, and acceptance map in the same revision change. Use the [GitHub changelog and handoff](CHANGELOG-v1.4.md) for publication notes.

Richard approves design changes and trial baselines. Josh owns the technical integration checks. A trial override is evidence for a decision and stays scoped to that trial until Richard adopts it in a pinned revision.

| v1.3 feature references | v1.4 treatment | Trial checks |
| --- | --- | --- |
| END-01, FLOW-01 | Replace the survival timer with Phase 2 and Phase 3 body damage gates. Keep a clear result and retry. | QA14-ENTRY, QA14-PHASE, QA14-PACKAGE |
| CORE-01, CORE-02, UMB-01, UMB-02, COM-01 | Retain steering, natural fall and fixed-right auto-fire. Replace the old input and pose precedence with held Rise and default falling fire. | QA14-INPUT, QA14-ENTRY |
| CORE-03, SURV-02, DEF-01, SURV-03 | Retain one HP pool, readable wear and bottom defeat. Replace frontal shield healing with yellow suction and committed canopy contact. | QA14-RECOVERY, QA14-PHASE |
| WIND-01, WIND-02 | Retain one safe upward current. Wear stays outside the default trial. | QA14-INPUT, QA14-PACING |
| OWL-01, OWL-05, COM-02 | Replace the single-bolt pattern. Keep one outcome per shot and separate regions. Add blocking feet and red speed slowdown. Attack timing remains independent of clock hits. | QA14-REGIONS, QA14-CLOCK, QA14-PACING |
| ANIM-01, BG-01, QA-BASE | Retain event-driven presentation, fixed-camera parallax, repeatable dev profiles and validation. Add stable slots and pinned source assignments. | QA14-ASSET, QA14-PACKAGE |

## Appendix A Asset source pins

Use the short fingerprint to identify a source during review. Before import, verify the full SHA-256 digest in [asset-source-pins.json](asset-source-pins.json). Full digests detect changes to the selected bytes and pin the exact inputs to a repeatable trial.

| Slot or import ID | Use | Short fingerprint |
| --- | --- | --- |
| ART-ARENA-FAR | Default trial | `1f7411017383` |
| ART-ARENA-NEAR | Default trial | `e3a976692a37` |
| ART-ARENA-WIND | Default trial | `aa69da4ab016` |
| ART-ELLA-ABSORB | Default trial | `6f15cf25ffd3` |
| ART-ELLA-FIRE | Default trial | `fa5093018ca4` |
| ART-ELLA-REPAIR | Default trial | `7e8dec8db123` |
| ART-ELLA-RISE | Default trial | `fefe774b93f4` |
| ART-ELLA-WEAR | Art-swap reference | `93ad465e71a1` |
| ART-OWL-BODY | Art-swap reference | `0461359166fc` |
| ART-PROJ-ELLA | Default trial | `d038c49a2151` |
| ART-PROJ-IMPACT | Default trial | `424b772b8859` |
| ART-PROJ-RED | Default trial | `a30b041be0f0` |
| IMPORT-ELLA-LAYOUT | Import metadata | `4e833e066cfb` |
| IMPORT-TEST-LAYOUT | Import metadata | `6a0a54ac16e3` |

## References

- [Prior master GDD v1.3](https://github.com/RickTheBuilder/GameJam2026/blob/3af5731a48b4014ccff76a5050625e0cd25a90e0/GameDesignDocument.pdf) for the carried-forward fixed arena, Windows scope, independent gameplay and art, and release process.
- Rick’s `UmbrellaGirl-GDD.md` Draft 2.1, §§5C and 6A, for reference recovery values and capture behavior. Its attack schedule, control rules, and phase design belong to Rick’s rehearsal.
- [Itay Keren’s Boss Up GDC slides](https://media.gdcvault.com/gdc2018/presentations/Keren_Itay_BossUp.pdf) and [Studio MDHR’s Cuphead design interview](https://www.gamedeveloper.com/business/road-to-the-igf-studio-mdhr-s-i-cuphead-i-) for readable paths and phase escalation. The timing values in this GDD are local trial settings.
