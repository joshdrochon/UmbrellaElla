# standins status (2026-11-13)

Stand-ins, not passes. Record: `pipeline/art/standins.json` (59 slots; per slot piece, source lane/path, round, panel result, score, sha256).
Selection: panel result first, else art_ref_check, else the latest round (clean/keyed variant where it exists).

| Family | Slots with a stand-in | Basis |
|---|---|---|
| Ella | Idle, Hurt, Down | panel / videoframes grid |
| Keeper | body-hover-flap, clock, mech front/middle/rear, talon, wing | owl: panel; rest: latest first draft (no panel) |
| Scene backgrounds | Sky, FarLand, NearArchitecture, ClockWaterWind, Base, clocks, land, atmosphere, start-end, water | panel where recorded, else latest round |
| Shots and effects | gold, red, red-impact, yellow, stream-beam, wind zone, wind lines; VFX ClockBeat, GoldRelease, GoldTravel, TwinStarHead, GoldImpact, ClockOpen, Departure, EyeExposed, KeeperRecovery, KeeperStrike, Restoration | panel for wand-shot/owl-bolt/bolt-hit; videoframes grid for GoldImpact; rest latest first draft |
| Enemies | Armillary, Sundial, SkyCourier, EscapementRepeater (videoframes attack grid), Floodstrider (latest draft), both genders | panel for the first three |
| UI | Credits, Defeat, Paused, Playing, Resuming, Settings, Story, Title, LevelUp, Purchase, Statistics | panel / latest draft |

Videoframes strips: imported only where no better-scored candidate existed (GoldImpact, EscapementRepeater). Ella idle/down/hurt grids already in. The other videoframes clips (wand-shot, owl-bolt, bolt-hit, clock-beat, armillary, sundial) have a panel-scored candidate in the slot, so they stay in `pipeline/art/proof/videoframes/` unimported; ella-transition has no drawing slot.

## Drawn slots with no candidate at all (still gray _PH)
ella-state:Absorb, ella-state:Shoot, scene:gameplay-frame (only paper/skyline exist), VFX Blackout, Blocked, GoldFade, Gust, GustPuff, KeeperWarning, LightShaft, NeedleChannel, NeedlePierce, NeedleSliver, PartBreak, PartHit, Slow, StreamStart, StreamSustain, Stun, Umbra.
Passed already, skipped: screen:Tutorial, screen:TutorialPaused.

## Not run
Build, tests, in-engine capture, art_ref_check on the unscored drafts (near-copy-of-reference check not run for them). Sprite-sheet layout of the first drafts is not verified against each presenter; some drafts may not be grids.

Location note: copies live in pipeline/art/proof/standins/<piece>/, not pipeline/art/proof/standins/ (art_inventory.py counts every file under Art/ as an unmapped visual and sprite_check --scan Art wants a sidecar for each, so precheck failed on them).

## OWL-32 / OWL-33 visual and projectile-scale clauses (Nov 13): not built, blocked on lane
No clause-proof rows added. Findings (read-only):
- The brief says "stand-in art at the GDD scale", but the 16 open OWL-32/33 clause-audit rows are rule behaviour (eye window, blackout clears, time domains), not art. No stand-in slot is involved; the art slots for Slow, Blackout, LightShaft stay in the no-candidate list above.
- `OWL-33 player projectiles stay unscaled`: true today only because nothing scales time. `AUmbrellaProjectile::Tick` advances by raw DeltaSeconds and the world has no time dilation. A test would pass without any code, so it cannot be break-proven.
- `OWL-33 physical attack timing scaled at x0.35` for missiles already in flight: not implemented. The model scales only queued emissions (`KeeperFightModel.cpp:399`); `EncounterDirectorSubsystem::ProcessCommands` fires `Spec.Velocity = Command.B` unscaled, and shots in flight keep full speed during slow. Fix needs Projectile (a per-shot time scale for enemy kinds, player kinds fixed at 1) plus a director call each Step: both outside the standins lane.
- Blackout cue-kept and menu-clock clauses sit in VFX/UI lanes.
Request for the build lead: assign the in-flight enemy-shot scale to the projectile lane (enemy kinds x `GetWorldScale()`, player kinds x 1, test with a slowed model and one shot of each kind).
Not run: build, tests (no code changed).
