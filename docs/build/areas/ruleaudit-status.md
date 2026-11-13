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

### Audited so far: 19 rows
FLOW-34 ART-04 FLOW-02 FLOW-03 FLOW-04 FLOW-35 FLOW-36 FLOW-37 FLOW-38 FLOW-39 FLOW-40 FLOW-41 FLOW-43 FLOW-49 NAR-04 NAR-07 NAR-08 NAR-02 NAR-03

