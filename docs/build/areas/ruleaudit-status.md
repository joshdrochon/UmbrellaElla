# ruleaudit status

Re-checked at b119b0f8 (main merged): `build exit: 0 mode=unity warnings: 0`; `TEST_FILTER=UmbrellaElla.Flow` `PASS tests=30 failed=0`.

## Set to built (evidence in the csv)
NAR-04, NAR-07, FLOW-49 (storyflow, dcb08d4). FLOW-49 caveat: keyboard focus on the Journey Complete widget is an artui follow-up.

## Notes rewritten, still partial
- WIND-03: built. Motor `IsEventForElla` accepts TargetId == owner actor name (EllaMotorComponent.cpp:167-172); `Move.World.RideCurrentFromVolume` covers it.
- HAZ-14 / HAZ-15: the only gap is that BrokenMill tests still name the pawn "Ella" instead of using the real-name path.
- FLOW-45: no HUD, XP ring or Flow screen reads text scale or reduced motion (requests/settings.md 6 not applied).
- FLOW-28: health carry across route checkpoints not shown; QA-36 not run.
- HAZ-08..13: measured by enemies2; remaining GAPs named per row. Owner was ORPHAN, now enemies2 (restoring field) or lead (Attack fixture).

## Not audited
The other partial rows (art, VFX, audio, level chunks, playtest) have no code gap that a test run can close; notes left as written.

## Rule audit (Nov 13, Opus): built rows vs GDD SH1.0 clauses vs evidence test bodies
Method: each built row's GDD text split into clauses; evidence test bodies read (plus any other test that asserts the clause).
A clause counts only when a test body asserts it. Unproven clause -> row `partial`, note `unproven: ...`, owner = area that closes it.

### Downgraded (row | owner | unproven clauses)
- FLOW-02 | titlemusic | Director's Cut arrives at the Keeper with wings still to destroy; no boss-specific tutorial on Director's Cut arrival
- FLOW-03 | titlemusic | Director's Cut tutorial Skip begins the first level (only Resuming asserted); both tutorials teach the same controls (only page counts compared)
- FLOW-04 | titlemusic | credits roll with music; credits use the Start screen background
- NAR-04 | settings2 | start confirmation consumed so it cannot also fire/hop
- NAR-07 | agentplay | Keeper withdraws alive into darkness
- FLOW-34 | titlemusic | title music plays; background moves slowly; background art contains no characters; second button label is 'Director's Cut', GDD says 'Start Director's Cut'
- FLOW-35 | titlemusic | Quit exits the game; pause background animates ticking clocks and falling objects; pause background motion never advances gameplay
- FLOW-39 | settings2 | Richard - Producer credit line; end credits roll (FlowStoryText) lists the full team, only one role checked
- FLOW-40 | settings2 | each page (Sound, Controller, Credits, Game Options) shows Back and Save buttons
- FLOW-49 | settings2 | title text 'Journey Complete'; Main Menu button; approved Gothic storybook look; readable controller/keyboard focus
- FLOW-43 | settings2 | dirty Back 'Save' choice saves; named setups independent of earned character state; HP-max tuning requires explicit encounter restart; reset never erases the earned profile
- ART-04 | titlemusic | credits/End screen uses the Start background (only Story+Title flag tested); background moves slowly; background art contains no characters
- MOVE-07 | move | arrow-key trim aliases; fire goes right while traveling left; right stick selects spells
- MOVE-08 | titlemusic | D-pad left/right and [ cycle spells; keys 2/3 bound to Stream/Twin; right-stick directions select spells; Escape/Menu opens pause during play; Cross/A/Enter triggers retry on defeat screen
- MOVE-09 | titlemusic | mouse click selects in menus; controller (gamepad) button remap
- MOVE-10 | settings2 | controller (gamepad) button remap in Controller menu
- MOVE-17 | settings2 | controller (gamepad) button remap in Controller menu
- SURV-05 | settings2 | clock HUD actually drawn in game; no extra clocks, umbrella icons or numeric count; Shoot-only fall does not auto-catch; no absorption cooldown (repeated world catches)
- SURV-06 | settings2 | +1 life per point (lives value after purchase); previous-rank dependency for three-rank tracks
- FLOW-30 | settings2 | clock HUD actually drawn in game (only layout math tested); antique bronze/gold look, smoky translucent face, etched rim; warm gold upper-right arc; no extra clocks, umbrella HUD units or numeric count; hands high-contrast/readable over face across scenes
- FLOW-31 | health | life-loss transition adds no protection window
- FLOW-32 | settings2 | absorbed energy visibly flows into the clock; gold arc restores on heal / drains on hit; life hand unchanged on partial damage/heal; reserve handover shown without invulnerability/reset pause
- FLOW-33 | health | ordinary red/yellow projectile damage is 1 (no bound key; tests inject 1); same-shot heal overflow into spent reserve; handover grants no new protection; retry restores exactly 3 lives (test asserts max=4 instead); progression rollback applied before health restore; normal checkpoint passage does not heal; +1 life per point in Director's Cut
- MOVE-11 | move | same movement/controls asserted inside a boss encounter; same rules asserted inside a level route
- MOVE-12 | move | no ammo/energy for Stream, Twin, Needle (only Small tested)
- MOVE-13 | move | same profile asserted in every level/boss encounter
- MOVE-15 | move | hop protection actually blocks damage in Health; hop vs post-hit protection asserted distinct; qualifying route rejects developer protection setting
- MOVE-19 | move | right stick selects a spell
- MOVE-20 | move | Absorb/Free fall disengage Ride (only Shoot tested); remapped controls keep the four combinations
- UMB-05 | move | catch gives no ammo/stored-energy reward; repair not disabled by reward eligibility
- WIND-03 | levelchunks | riding a current deals zero damage; safe supports/solids/lethal bottoms explicitly tagged
- MOVE-22 | move | effective profile recorded before qualifying play; encounter display vs collision scale tested independently
- COM-05 | move | Stream/Twin/Needle never run out (only Small tested); catch gives no weapon charge
- COM-06 | move | fold-ready, snap open, pulse, cock, reset cycle tied to emission
- COM-07 | move | canopy strands converge around dark body (art); shoulder-braced body family used for Stream; posture/art adds no damage or aim (beam)
- COM-09 | move | Needle penetrates wings during clock opening; Needle never bypasses clock protection/order
- COM-11 | move | locked-weapon UI shows levels 1/10/20/30; XP display derived from tuned curve; damage ranks applied once to baseline; RegularFall vs ShoulderFall poses per spell; only Small uses fold/open/cock; required routes clearable with basic fire
- FLOW-05 | settings2 | Enemy HP/cadence/count multipliers applied to real enemies (GetRunScaling has no consumer); Ordinary firing cooldowns divided by cadence multiplier; Projectiles/telegraphs/recoveries/pauses/protection not accelerated; Physical boss scheduling intact under scaling; Extra enemies only in authored slots under local threat caps; Warnings, escapes, early yellow healing, generator limits preserved; No unsafe mandatory encounter from more enemies
- FLOW-06 | settings2 | Final Hour intro screen shown before the Extreme run; Exact text 'Your borrowed time has run its course...' shown; Final Hour multipliers applied to real enemies; Telegraphs/recovery/scheduling/projectile speed/safe placement preserved; No automatic increase in incoming damage
- FLOW-08 | settings2 | Quit reload restores checkpoint upgrades (ranks); only XP asserted
- FLOW-09 | agentplay | Exactly 3 lives on retry in both modes (Start Game not tested); 3-life reset keeps purchased max lives (Health.World.RetryRestoresFullLivesAndHealth asserts 4 lives, not 3); Rollback applied before full heal (ordering); Level-checkpoint retry fully heals (only event-driven retry tested)
- FLOW-10 | settings2 | Upgrades (ranks) retained into next run after win; Unlocks/weapons retained into next run after win
- FLOW-13 | settings2 | Level checkpoint after boss checkpoint does not exempt gains from rollback; Living Keeper departure grants no reward
- FLOW-15 | settings2 | MAX displayed in UI at cap; Spell access survives refunds; No traversal XP; Start Game has no stat upgrades (purchase not tested)
- FLOW-17 | settings2 | Health purchase/refund preserves current health fraction; Fractional health retained without per-hit rounding (C++); Defense does not cancel gust displacement; Defense does not make lethal boundaries safe; Damage ranks don't change rate/geometry/protection/penetration/aim; Effects derived from baseline once
- FLOW-19 | settings2 | Living Keeper departure gives no kill reward; CP2/CP3 passage and reload give no XP (only CP1 tested)
- FLOW-20 | settings2 | Quit/reload restores checkpoint upgrades (only XP asserted); No catch XP in world (only rule-table 'Absorb' label)
- FLOW-21 | settings2 | Enemy count advanced in-world after win (only HP/cadence asserted); Levers applied to real enemies within generator/fairness limits; Weapons/unlocks and upgrades retained into next run
- FLOW-22 | settings2 | Earned data separate from tuning/bindings; Two corrupt copies error is recoverable; Shadow progress restored on relaunch; Tutorial replay uses shadow progress
- FLOW-29 | settings2 | Defeat/retry context alone is inspection-only; 'Active' eligibility condition; CP0 alone is not a purchase zone
- FLOW-42 | settings2 | Review screen shows complete costs and effects; Confirm saves the staged draft atomically (draft commit untested); Context change discards unconfirmed draft; Start Game has no upgrades (purchase path)
- OWL-06 | agentplay | Rules apply in BOTH modes (no Director's Cut keeper test); Retained/restored capacity, max lives, upgrades on retry; Normal phase advancement carries Ella's health
- OWL-07 | agentplay | Complete fight contract (OWL-06..35 rows themselves partial); No player resource system (no test); Gameplay state, not animation length, owns damage/transitions
- OWL-08 | agentplay | Crownless metallic owl in side profile (visual); Exactly two feet, two wings, central clock (visual); Three visually distinct hanging mechanisms; Front/middle/rear identity, attachment, reachability through movement; Front is armillary/ring, not duplicated
- OWL-09 | agentplay | Wings reachable at supported owl sizes; Wings damaged from lift; No new gusts after wing depletion; Depleted wings remain visible as cover; Middle/rear break cancels cast and removes attack
- OWL-10 | agentplay | Both modes checkpoint at each phase start; No mid-mechanism checkpoint after a mechanism breaks; Retained/restored capacity, max lives, upgrades on retry; Initial phase advancement carries Ella's health
- OWL-11 | agentplay | Wings/clock aim at captured positions; Mechanisms use fixed-left fan; No homing; Spacing 0.09s; Normal interval 1.35s; One-shot reduced volley (assertion has vacuous OR); Queued/traveling shots keep counts/paths; Recovery: yellow <=0.15s, red >=0.6s, longer red kept; Four shots (no spec key bound for 4); Spreads 36/70/48 deg (no test uses spread fields); Speeds 270/300 (no mechanism/clock speed test)
- OWL-12 | agentplay | No separate timed prefire delay; Captured lane shown, no hidden tracking; Player can leave via rise/fall/current/evade; Traveling missiles continue during electrical stun
- OWL-13 | agentplay | Yellow shots are aimed; Independent 2.3s cadence; Keeper yellow ordinary contact deals 1 health; Shoot alone never auto-catches; No absorption cooldown or energy reward; Speeds 195/210 (no mechanism/clock yellow test)
- OWL-15 | agentplay | Gust in wing act only; Shared physical scheduler 6.5s from attack start; Talon priority over gust; Wing gather/load then flap cue, readable direction; Complete owl warning/strike/recovery animation verified
- OWL-16 | agentplay | Gust damage 1 health (only hit count checked); Bypasses hop protection; Dash protection blocks damage not push; Speed 350 (bound, but no test exercises speed); Band width 120 (bound, no test exercises it); Lifetime 3s (bound, no test exercises it)
- OWL-17 | agentplay | Wing recovery follows the flap; Stun clears active gusts; No new gusts after depletion/stun; Depleted wing smoke remains (visual); Hostile fronts distinct from voluntary wind (geometry/motion)
- OWL-18 | agentplay | Empty claw draws back, distinct from carrying claw (visual); Strike direction captured at commitment, no tracking; Cooldown must be clear to trigger; No test that talon stays idle outside 270
- OWL-19 | agentplay | Empty space and recovery do no damage; Vertical-exit check suppresses impossible launches; Tip width 48 (bound, no test exercises width); Sweep aims at captured target
- OWL-20 | agentplay | Quiet recovery 1s; Shared scheduling with talon; Must re-enter <=270 after leaving to rearm; No rearm on simple exit at attack radius; Cooldown 3.5s from commitment (bound, behavior not asserted)
- OWL-21 | agentplay | front head locks Ella's destination (move after lock not tested); 0.9s warning duration; closed claw grips armillary outer ring, load/release/follow-through; original attachments pay out; no duplicate ring or floating grasp; choreography does not change lock window or collision
- OWL-22 | agentplay | committed straight outward head path; reach 800; speed basis 400 units/s; head width 32; only the outward moving head damages; links harmless; visible position = shootable target = damaging sweep
- OWL-23 | agentplay | return home is harmless; return takes 1.2s then settles; broken part's attack stays removed until explicit reset; explicit reset restores the attack
- OWL-24 | agentplay | middle cast keeps same endpoint/warning/head/link/return contract; ±80-unit sine offset; sign uses GLOBAL physical serial (talon counts) in real casts; no every-cast alternation (talon-intervening case untested)
- OWL-25 | agentplay | shown and collides on the actual curved path; moving middle head shootable on the curve; timing uses straight-distance basis (not constant 400/s); telegraph shows enough curve for a viable exit; destroying the middle cancels its cast (only front tested); dedicated art follows curved geometry
- OWL-26 | agentplay | 0.9s warning before rear stroke; first stroke stops at half of outward stroke; continues to ORIGINAL captured endpoint, no re-aim; both strokes share one serial, damage at most once; chain links harmless; 1.2s return harmless
- OWL-27 | agentplay | second clack / stopped head signals unfinished movement; destruction cancels either rear stroke or pause immediately; held-in-claw artwork reconciled to mid-flight pause
- OWL-28 | agentplay | repeat without re-aim (player never moved in test); 0.6s wait after last shot; at least 0.85s recovery after repeat; yellow keeps its own timer; clock-hand move, tick and path cue mark the reprise; destroyed hazards not resurrected / world not rewound
- OWL-29 | agentplay | exposure cycle uses unscaled active-gameplay time; needle never bypasses magic or target order; clock exposure independent of volley cadence
- OWL-30 | agentplay | mechanism break opens the clock; break clears gusts; new fire stops during stun, traveling missiles continue; fire pause freezes physical timers and pending emissions; fire pause is not stun; blackout cancels the physical move
- OWL-31 | agentplay | hit at 128-HP floor does not start slow; slow cooldown must be ready; slow lasts 3s; 3s slow cooldown; new clock opening resets slow/eye flags and clears eye; extending an opening does not reset flags; lethal final-clock hit clears all effects
- OWL-32 | agentplay | eye-when-slow-off enabled by default and works with slow off; eye window lasts 2s; eye needs cooldown ready and unused per-opening chance; eye outlasts clock closing until its timer ends; new clock opening clears the eye; 5s eye cooldown starts on eye hit; blackout clears physical moves and gusts; shaft/clock/fresh-shot cues and ground danger kept; prior damaged body restored at blackout expiry; blackout does not extend clock exposure
- OWL-33 | agentplay | slow/eye/cooldowns/stun/blackout/clock timers run unscaled; physical attack timing scaled at x0.35; player projectiles stay unscaled; fire pause suspends physical timers; traveling missiles continue during fire pause; decorative menu clocks may run while paused, no gameplay/VFX advance
- OWL-34 | agentplay | full warning→stroke→recovery→idle sequence asserted; blackout and presentation locks respected by scheduler; fire pause freezes pending emissions; reduced projectile pressure during physical activity (assertion has vacuous OR); overlapping escape routes tested
- OWL-35 | agentplay | living departure lasts ~2.5s as presentation only; retry clears casts, gusts, queued repeats, locks; new-run reset clears state; phase reset clears state; XP policy applied
- HAZ-02 | enemies2 | land is solid and harmless for Ella on contact
- HAZ-03 | enemies2 | fixed camera at (960,540) (binding is RoomSize/2, no camera checked); guard is stationary (never moves); guard contact damage 0 (bound, but no test exercises contact)
- HAZ-04 | enemies2 | entry must be from the left; source and muzzle fully visible check; engagement validity required at warning start (only release tested)
- HAZ-05 | enemies2 | recovery must complete before rearm; no warning in reset/underpass (room only flags assist and exit); launched projectile actor persists after guard disabled; pause freezes all gameplay clocks (only guard clock tested); no arbitrary seam culling of danger
- HAZ-17 | enemies2 | gate checks incoming velocity/mode; gate checks low health; gate checks dash state; gate checks pending warnings; gate checks delayed impacts; one active owner; no new simultaneous timing demand without proof; exact fallback specified; integrate with progression, preserve earned state; catalogue not silently replaced
- CAM-03 | levelchunks | required paths work with direct steering OFF; no mandatory dash/spell/invulnerability on required paths
- CAM-05 | levelchunks | support incoming speed and settle excess momentum at interface
- CAM-06 | levelchunks | opening height >= 2rz+2m (no failing-height case); openings checked against full trap sweeps; unassisted recovery climb limited to ~0.15H or lift route (not in game); enlarged unqualified profiles get wider variants or labels
- CAM-08 | levelchunks | next current, hazard and safe exit revealed before commitment; reveal holds when backtracking left (real chunks); clearance includes reaction, braking, height-change time; upper limits and bottom danger readable
- HAZ-19 | levelchunks | lethal world boundaries separately marked; collision follows visible moving parts; air mill visible hub and four blades; never require tip-threading, destroying or invulnerability; foreground mill distinct from decorative distant windmill
- HAZ-20 | levelchunks | visible crank/tension warning; clearly open look in recovery; hazard-free waiting pocket; always-open low bypass in every variant (07B has upper detour); damage only on visible panels, never the gap; committed travel never trapped without exit
- HAZ-21 | levelchunks | visible nozzle warning; warning locks one lane; push actually applied toward safe catch space (Motor ignores it); cannot Ride or absorb the gust; required wind never silently redirected; distinct cues: transport curls vs jagged hostile front
- HAZ-22 | levelchunks | high-contrast projection visible on approach; no surprise activation; no confusing decorative tiles
- HAZ-23 | levelchunks | retime/reject encounter instead of freezing geometry; no attacks from UNcleared neighbours (test checks cleared); no pursuers past cleared exits; no shots through refuges; clear at observed safe boundary
- FLOW-27 | levelchunks | refuge core permanent harmless lift/reacquisition; clear cycling space; no incoming threat lane into core; no forced damage or timer in refuge; optional yellow bay ahead/right expires shots before core; ordinary yellow contact still hurts
- FLOW-24 | levelchunks | story events deterministic on retry
- COM-12 | enemies2 | Floodstrider/Courier male+female art assets present; identity consistent across actions, colours, damage states; gender parity tested only for Roadwarden; Floodstrider two-person four-stilt rig; woman-carrier/man-operator version and per-role alternatives; carrier/operator roles stay distinct; enemy contact damage OFF; zero HP stops new/delayed fire; non-graphic defeat/disable/withdrawal visual; launched projectiles obey ownership/exit after defeat; equipment art adds no extra shots
- COM-13 | enemies2 | Roadwarden equipment variants fire red and yellow; Floodstrider crew versions fire red and yellow; Courier gender variants fire red and yellow (colour asserted)
- FLOW-46 | levelchunks | Floodstriders placed high without platform; shot colour chosen independently of gender; MIX02 authored yellow reserved first; collision clearance of placed enemies; simultaneous-threat limits preserved; unsafe/unreachable encounters rejected, ratio not forced
- HAZ-41 | levelchunks | spawned enemy stays on its floating area in world; holes and gaps in support accounted for; patrol span shrinks to available surface; turn/attack motion kept within support
- FLOW-47 | levelchunks | QA-40/41/42 automated tests as defined; short/long stilt configs validated; actual body/weapon extents validated, not spawn points; safe firing/catch-lane test; seeded record: seed, revision, enemy type/colour/transform, results
- COM-14 | enemies2 | female Roadwarden red/yellow firing; patrol cannot move target behind fixed-right fire; equipment variants keep same burst/cadence
- COM-15 | enemies2 | two-person rig on four stilts; adjustable short/long stilt heights; placed high without floating platform; male/female crew fire red and yellow; harmless legs leave real underbody passage; gender keeps crew count/HP/scale/targeting/stilts
- COM-16 | enemies2 | male/female propeller art; body about 48x88; Courier fires red and yellow (colour asserted); four mounts never give simultaneous shots
- COM-17 | enemies2 | launched shots resolve normally after withdrawal; duplicate callback actually rejected in world
- COM-18 | enemies2 | all required traversal works with basic fire; Courier need not die to supply healing; descent window and left reset before every enemy
- HAZ-24 | levelchunks | no horizontal whole-chunk mirror
- VFX-06 | visuals | no dynamic VFX/illumination baked into base sprites; effects off: character stays dark, posed, damaged; audio cleared on retry/phase reset/defeat; effects cleared on defeat; destroyed parts not restored incorrectly
- VFX-09 | visuals | effects inspected at camera scale on every background/state; visual threat extent matches hitboxes; glow never implies range or hides safe gap; red/yellow distinguishable without colour; warning/active/recovery distinguishable without colour; VFX/animation obey pause/slow/cancel timing; no added delays, re-aims or beats
- CORE-04 | move | movement owns input mode, position/velocity, locks; weapons own emission/trajectory/hit identity, not ammo; encounter owns targets, scheduling, cancellation; attack model owns target/path/warning/stroke/recovery; presentation never infers damage from animation completion; story owns facts/cues, not combat success; level owns route/checkpoints/spawns; tuning owns validated persistence
- CORE-05 | move | stable anchors and event identities; cosmetic swaps keep target order and attack timing; settings and earned growth independent
- HAZ-31 | levelchunks | neither variant requires a timed dash
- HAZ-32 | levelchunks | bellows source and whole path visible
- HAZ-33 | levelchunks | no hidden roof-face collision
- HAZ-34 | levelchunks | net progress right (no test asserts it); sequence order low->reset->upper not asserted
- HAZ-35 | levelchunks | A Warden fire starts only after crossing clears
- HAZ-36 | levelchunks | A alternate attack windows; B stilt and Courier on the right (X not checked); no unavoidable simultaneous lanes; B bypass specifically avoids the stilt
- HAZ-37 | levelchunks | refuge CP2 placed after group B; once-only journey clue at CP2; refuge CP3 after group C; quiet arrival before Keeper; recovery/story ordering stays fixed
- HAZ-40 | levelchunks | separate layout, cosmetic and story random streams; new run saves seed and generator/catalog/profile versions; saved variants immutable and ordered; retry preserves resolved layout; route check: minimum lift, gun windows, pressure; route check: story/recovery order; at most 32 attempts then named verified fallback; fallback failure branch force-tested

### Audited so far: 150 rows
FLOW-34 ART-04 FLOW-02 FLOW-03 FLOW-04 FLOW-35 FLOW-36 FLOW-37 FLOW-38 FLOW-39 FLOW-40 FLOW-41 FLOW-43 FLOW-49 NAR-04 NAR-07 NAR-08 NAR-02 NAR-03 HAZ-25 HAZ-26 HAZ-27 HAZ-28 HAZ-29 HAZ-30 HAZ-31 HAZ-32 HAZ-33 HAZ-34 HAZ-35 HAZ-36 HAZ-37 HAZ-40 MOVE-11 MOVE-12 MOVE-13 MOVE-14 MOVE-15 MOVE-18 MOVE-19 MOVE-20 MOVE-21 MOVE-22 UMB-05 WIND-03 COM-05 COM-06 COM-07 COM-08 COM-09 COM-10 COM-11 FLOW-05 FLOW-06 FLOW-07 FLOW-08 FLOW-09 FLOW-10 FLOW-11 FLOW-12 FLOW-13 FLOW-14 FLOW-15 FLOW-16 FLOW-17 FLOW-18 FLOW-19 FLOW-20 FLOW-21 FLOW-22 FLOW-23 FLOW-29 FLOW-42 OWL-06 OWL-07 OWL-08 OWL-09 OWL-10 OWL-11 OWL-12 OWL-13 OWL-15 OWL-16 OWL-17 OWL-18 OWL-19 OWL-20 OWL-21 OWL-22 OWL-23 OWL-24 OWL-25 OWL-26 OWL-27 OWL-28 OWL-29 OWL-30 OWL-31 OWL-32 OWL-33 OWL-34 OWL-35 HAZ-02 HAZ-03 HAZ-04 HAZ-05 HAZ-17 CAM-03 CAM-05 CAM-06 CAM-08 HAZ-19 HAZ-20 HAZ-21 HAZ-22 HAZ-23 FLOW-27 COM-12 COM-13 COM-14 COM-15 COM-16 COM-17 COM-18 FLOW-46 HAZ-41 FLOW-47 FLOW-24 HAZ-24 ART-03 VFX-06 VFX-09 CORE-04 CORE-05 FLOW-30 FLOW-31 FLOW-32 FLOW-33 SURV-05 SURV-06 SURV-07 MOVE-04 MOVE-05 MOVE-06 MOVE-07 MOVE-08 MOVE-09 MOVE-10 MOVE-16 MOVE-17

### Done
All 150 rows that were `built` on main at 56a187ec are audited; 119 moved to partial, 31 stay built.
Number clauses count as proven when gdd_check binds the GDD value (MISMATCH=0) and a test exercises that tuning field.
Code gap beyond tests: FLOW-05 run scaling (`UProgressionSubsystem::GetRunScaling`) has no consumer outside Progression.
Label: title button reads "Director's Cut"; GDD section 7 says "Start Director's Cut" (FLOW-34 note).
