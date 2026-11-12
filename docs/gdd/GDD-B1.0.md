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
