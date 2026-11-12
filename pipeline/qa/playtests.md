# Playtests (cold players: never seen the game, no coaching)

> GDD SH1.0 note (D-new-gdd-sh10): lines on this page that still describe the GDD 1.3 encounter (one owl bolt, the front shield, the 90 s survival timer, wear stages, the 1.3 QA-01..QA-28 tests) are history. The current design is `docs/gdd/GDD-SH1.0.md` and `docs/feature-manifest.json`, which win; the owning role re-files this page against the SH1.0 Rule IDs on its next card.


At least 2 cold players per gate playtest; G3 has 4 (D-new-pool). The playtest lead lists 10 cold players on the Jam
tracker before G1 (G1 2, G2 2, G3 4, G4 2, none reused). Fewer than 2 left for a gate is a blocker the Producer reports a day ahead.
At least 1 of each gate's players does not play action games often. By G2 the list has 1 player with a visual or motor
impairment, or a line `none available` signed by the game design owner.
The game design owner watches every gate playtest, in the room or on a live screen share (D-new-owner-present). An agent cannot watch a player; it reads the log.
Any failure of P1, P2 or P4 blocks that day's gate. The GDD §11 gates map to these tests: movement prototype = P1, P2;
wind integration = P3; combat integration = P5; shield = P12; full encounter = P6, P7, P11; readability = P8.

## Play data: the game counts, the observer explains
The Development package writes one CSV per session to `Saved/Playtest/<yyyymmdd-hhmmss>.csv` (card 0.23) [VERIFY: where a packaged Win64 build puts `Saved/`].
Columns: `session,event,phase,pattern_id,explained,t_run_s,build`.
- `event` is `hit`, `death` or `survive`. `phase` is `intro`, `contest` or `desperation`, or `base` when the encounter has no phase presets (GDD SH1.0 OWL-06, OWL-35: phases are optional). `pattern_id` is the hitting pattern's ID from `pipeline/level/encounter.json` (`BOTTOM_EXIT` for leaving through the bottom edge). `explained` is `y` or `n`, from the observer's "What hit you, and what warned you?" (P4). `t_run_s` is the time on the run timer.
- `python3 tools/encounter_check.py --playtest Saved/Playtest/*.csv` checks the rows (L1-L6; a log with no rows fails) and prints hits, deaths and `explained=n` per pattern. Paste it into the Measured column of P6 and P7. An `explained=n` hit is a bug against its `pattern_id`.
- If the CSV and the observer's tally differ by more than 1 for one player, the row is `invalid test` until someone finds why.
- Until card 0.23 merges, hits are counted by hand and the Measured cell says `hand count`.

## How to run one
1. Use today's packaged Development integration build. Note its commit and the tuning commit: `git log -1 --format=%h -- 'Source/UmbrellaElla/Public/*/*Tuning.h'`.
2. Watch first, ask after. No question and no hint while the player is playing. At G3 and G4 the full run is never interrupted; questions come after the survey (D-new-session-order).
   Think aloud: before play, ask the player to say what they are doing and why. Never reply. After 30 s of silence, say only "keep talking".
3. The observer writes down: pauses over 3 s, each hit and fail with its pattern, where they got stuck, anything said aloud, any move a player repeats that skips a pattern or phase rule (corner hugging, staying low, never opening), and the device (keyboard or gamepad). At least one session per gate uses a real controller on the Windows package and posts `GAMEPAD: device=NAME move=ok attack=ok shield=ok pause=ok by=NAME` (card 0.6e; the automated `gamepad=ok` smoke does not replace it).
4. Order of one session: the full cold run; the survey, filled alone; one-on-one questions (P4, P9); freeze-frame tasks (P8) and the P10 sound tasks; a group talk last. Group comments never count toward a result.
5. A/B tests (feel toggles, presets T-02..T-07) alternate which version each player gets first (`docs/feel-spec.md` section 1).

## When a result counts
- A row counts toward a gate only if Cold = y, Coached = n, and Build commit = the gate's build.
- Fewer than 2 valid cold players: the result is **insufficient**. Insufficient never passes a gate. P10 needs 3 (`audio_check.py --blind-id`).
- Report raw counts next to every percentage ("3 of 4 hits explained").
- One player stuck over 60 s, or quitting, opens a bug even if the other passed (D-new-port-5).
- A surprising single result first gets a bug check (does the build match the GDD?) and a retest, before any rule changes.

## Every failing row gets
- A **class**: `bug` (build differs from GDD or spec → Gameplay Dev), `cue` (rule works, the player can't read it → Art Director, Integrator or Audio), `design` (rule works, play is bad → Game Designer or Level Designer: a tuning card or a decision row), or `invalid test`.
- A **severity**: `blocks gate`, `fix before submit`, `known limitation`, or `after jam`. At G3 and G4 nothing that blocks a gate stays open.
- Exactly one linked issue or decision row with one owner.

| ID | What | Method | Pass |
|---|---|---|---|
| P0 | Paper walk of the phase table (D-new-p0) | Before the first encounter card: 1 person outside the team reads `pipeline/level/encounter.md` and says, per phase, what the owl will do and where they would stand | Every misread opens a row on the encounter card. Never counts toward a gate; that person is not cold afterwards |
| P1 | Rise and fall understood | Time from first input to a deliberate rise → hold ATTACK or SHIELD to descend → release to rise (GDD SH1.0 section 1 Inputs) | Both players ≤ 30 s |
| P2 | Players predict and recover | Ask after the run: "What happens when you let go? When you hold attack or shield?" and "Why did you fail?" | Both answer rise/descend in their own words and name a real cause. "Yes, it's clear" is a fail |
| P3 | Wind is a choice | Count entries into the safe wind zone (WIND-01) on purpose vs avoided (observer tally) | Each player enters the wind zone on purpose at least once and avoids it at least once |
| P4 | Hit attribution | After the run, for each hit on the tally: "What hit you, and what warned you?" Log `explained` y/n with its `pattern_id` | ≥ 80% `explained=y`; each `n` opens a bug against its `pattern_id` |
| P5 | Shots land on purpose | Ask "When do your shots hit the owl?" | Both describe lining up with the owl |
| P6 | Survive or fail a full loop | Full cold run | Both reach the end or a fail and can retry without help; a designer run survives |
| P7 | No pattern spike | Hits per pattern, or per phase preset (`encounter_check.py --playtest`) | With 2+ owl patterns: no `pattern_id` has > 50% of all hits. With one pattern (the GDD 1.3 base bolt) and phase presets on: no phase has > 50%. One pattern, no presets: `n/a (one pattern)`, not a fail. Only with 3+ hits; else `too few hits` |
| P8 | Readability without a HUD | 4 in-engine captures (`CAM_Eval_Arena`, `CAM_Eval_Stress`); the player points at: me, umbrella state and wear, health, the next threat (no timer is shown, GDD 1.3 DEC-09) | ≥ 90% correct; 100% on "me" |
| P9 | Core decision felt | Ask "What were you deciding most of the time?" | Mentions rising vs falling, or catching vs avoiding wind |
| P12 | Shield blocks and heals | Count bolts the player blocks on purpose with the front shield (observer tally; `CatchSucceeded` lines in the run log), then ask "What did holding shield do?" | Each player blocks at least 1 bolt on purpose and says it stopped the hit and mended the umbrella (DEF-01, SURV-03) |
| P10 | Playable muted, sounds distinct | During the G3 playtest: one muted run (`audio_check.py --muted`), then the blind sound ID in `pipeline/audio/audio-rules.md` section 6 (`audio_check.py --blind-id`) | `--muted` PASS and `--blind-id` PASS, both outputs pasted |

Schedule: before the first encounter card: P0. G1: P1, P2, P3 (once the wind card, MVP 11, has merged). G2: P4, P5, P12 (once the MVP 10 shield card has merged), survey. G3 (4 players): P6, P7, P8, P10, survey, P11. G4: P9, survey, P11.

## Survey (filled alone, before any talk)
Ratings are 1 (very low) to 7 (very high). One log row per player: Test = `SURVEY`, scores in Measured as `key=value`:
`fun=` · `again=y|n` ("Would you play it again?") · `intro=` `contest=` `desperation=` (difficulty; `-` if not reached).
"Was anything hard to see, hear or press?" goes word for word in Player said.
**P11 Fun (G3 and G4, D-new-fun):** median `fun` ≥ 5, written with "N of M"; `again=y` from at least half the valid players; no phase rated 7 by every player. A P11 fail needs a named exception with an owner and an hour in the gate record (only P1, P2 and P4 fails block it).

## Results log
| Date | Gate | Build commit | Tuning commit | Test | Player | Cold (y/n) | Coached (y/n) | Design owner present (y/n) | Observed | Measured | Player said | Inferred | Result | Class, severity, link |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|

Player = a short id (`G3-a`), never a name. Observed = what the player did. Measured = counts and times. Player said = their words. Inferred = a guess, labelled as one.
Result is `pass`, `fail` or `insufficient`. The playtest lead signs each gate's rows on the gate record.
