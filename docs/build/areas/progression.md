# Area: progression (Director's Cut XP, levels, unlocks, upgrades, persistence, XP ring)

Branch `area/progression`. Read `docs/build/worker-rules.md` first. Added Nov 12 14:10 (Josh: 8 workers).

## Rule IDs (all Director's Cut, G3)
SURV-06, FLOW-05 .. FLOW-08, FLOW-10 .. FLOW-23 (run scaling, Final Hour, checkpoint retry XP, quit/reload, win carries
progression, reallocation, retry XP, boss part XP and rollback, baseline, levels/points/XP curve to level 62, spell unlock
schedule 1/10/20/30, upgrade safety, purchase vs reallocation, kill XP, reconciliation, runs contract, persistence,
developer level fixture), FLOW-29 (purchase context at refuges), FLOW-42 (Ella and spells purchase flow), FLOW-48 (XP ring
HUD).

## GDD sections
4 (Gameplay systems, Progression system card, Director's Cut progression baseline), 7 "Settings and earned-character
interactions", 9 (progression numbers). Oracle: `tools/progression_model.py` (read `--help`): your C++ rule functions
must give the same numbers; add a test that compares against values the oracle prints.

## File lane (only these)
- `Source/UmbrellaElla/{Public,Private}/Progression/**`, `Persistence/**`, `UI/Progression/**`
- `Source/UmbrellaElla/Private/Tests/Progression/**`, `Private/Tests/Persistence/**`
- `Content/UmbrellaElla/UI/Progression/**`, `docs/build/areas/progression-status.md`, `docs/build/requests/progression.md`

## What to build
- A progression subsystem (GameInstance subsystem, so it survives map changes) with the XP curve, levels, points, stat
  tracks, spell unlock schedule, checkpoint/retry XP rules and run scaling, all as plain rule functions plus tests.
- XP from kills only (listen on the event bus; the enemies and keeper areas broadcast hits/kills). Start Game gives no XP.
- Persistence: `USaveGame` slots. Tests write only under `Saved/UmbrellaElla Tests/`-style test slots and delete them
  (test.sh fails if Saved/SaveGames changes).
- XP ring HUD as a C++ widget in `UI/Progression/`; the purchase screen at refuges (FLOW-29/42) as a C++ widget.
- Expose getters other areas read: current level, unlocked spells, stat ranks (health reads health ranks via a getter).

## Done
Worker-rules DoD, plus rule tests that match `tools/progression_model.py` for the curve and unlocks, and tests for retry
XP rollback, persistence round-trip (test slot, deleted after), and no XP in Start Game.
