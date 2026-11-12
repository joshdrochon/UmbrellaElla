# Arena and owl encounter acceptance (THE LAST HOUR)

> GDD SH1.0 note (D-new-gdd-sh10): lines on this page that still describe the GDD 1.3 encounter (one owl bolt, the front shield, the 90 s survival timer, wear stages, the 1.3 QA-01..QA-28 tests) are history. The current design is `docs/gdd/GDD-SH1.0.md` and `docs/feature-manifest.json`, which win; the owning role re-files this page against the SH1.0 Rule IDs on its next card.


One fixed-camera arena, one owl, one bolt over 90 s (optional phase presets), then the end event.
This list makes every arena, pattern and phase card's Done-when checkable.
Design source: GDD 1.3 (§7 owl and wind, §7B first encounter, §8 phases as optional presets, §6 health); numbers from the
manifest `approved_parameters` (E29). Lines marked [2+ patterns] or [SURV-04] apply only once those are on. The old five-section
platformer docs do not apply here. Numbers live in `pipeline/level/encounter.json`; tables in `pipeline/level/encounter.md`.

Owner of every line below is the Level Designer, unless the line names another role.
`[VERIFY]` = needs Unreal; there is no engine here, so the test name and rule are fixed but the code is not written.

## Who builds the engine half
The data gate (section 0) runs on a JSON mirror. These two cards prove the shipped owl matches it.
Rule: no encounter card moves to `doing` until `python3 tools/encounter_check.py --wiring` prints
`wiring_check: 0 problem(s)`. Owner: Producer. It fails (W1-W5) while any of these is missing: both card rows below
in `pipeline/day0-cards.md`, the 5 test names in `pipeline/qa/test-map.md`, the section 6 log columns in
`pipeline/qa/playtests.md`, the Level Designer row in the AGENTS.md roles table, and `encounter_check.py` as the
Game Designer's review criteria. It fails until those files' owners add the rows.

| Card | Owner | Reviewer | Done when |
|---|---|---|---|
| Owl data types + 5 Owl tests | Gameplay Dev | Dev Lead | `UOwlPatternData` and `UOwlPhaseData` exist with the fields in `encounter.md`. `tools/ue/test.sh --require` with the 5 `UmbrellaElla.Owl.*` names below prints PASS (pasted). Each test's row is in `pipeline/qa/test-map.md`. |
| Owl dump + eval cameras (after the card above) | Integrator | Dev Lead | An editor script writes every `DA_OwlPattern_*` and `DA_Phase_*` as JSON in the `encounter.json` shape. `python3 tools/encounter_check.py --data <dump>` prints `0 problem(s)` (pasted). `CAM_Eval_Arena` and `CAM_Eval_Stress` are in the arena map and `-EvalCam=<name>` captures each. |

The 5 tests: `UmbrellaElla.Owl.EveryPatternHasTelegraph`, `UmbrellaElla.Owl.PhaseTableDistinct`,
`UmbrellaElla.Owl.World.OriginLockedDuringTelegraph`, `UmbrellaElla.Owl.World.PhaseChangePlaysCue`,
`UmbrellaElla.Owl.World.NoDamageAfterEndTrigger` (sections 1, 2, 4 say what each asserts).
`UmbrellaElla.Owl.World.SafePathAtDriftExtremes` (section 3) is a sixth, built by the same card if time allows; it is
listed `planned` until then. Until both cards merge, an encounter card lists the tests and the dump under
"Not run" with the card number. G4 does not pass while a test-map Owl row is `planned` (QA and Build).

## 0. The data gate (every card that touches the encounter)
- [ ] `python3 tools/encounter_check.py` prints `encounter_check: 0 problem(s)`. Paste its full output on the card
      (it prints the tuning it read, breathers and intensity; with presets, the midpoint and the desperation share).
- [ ] `pipeline/level/encounter.md` was regenerated with `--write-md` in the same PR (E18 fails a stale block).
- [ ] The engine assets match the JSON: the editor dump passes `encounter_check.py --data <dump>` [VERIFY].
- [ ] Hero speeds, hurtbox and bolt hitbox ratio come from the Game Designer's `pipeline/feel/feel.json`
      (`arena.tuning_source`). A copy of them in `encounter.json` fails (E22). The sim uses the worst case:
      sideways speed, UP_OPEN rise at the lowest lift tier (1.0 unless SURV-04), max fall.
- [ ] GDD 1.3 numbers (E29): every pattern names an enabled manifest `feature`; the OWL-01 bolt's warning, speed and
      cadence and `duration_sec` sit inside their GDD SH1.0 rule numbers (section 9 ranges blank, D-new-sh10-param-ranges) ranges (the starts are provisional tuning); grace and
      `seed` have no range and equal the approved values.

## 1. Every pattern (one `DA_OwlPattern_<ID>` row each)
- [ ] Three stages: TelegraphSec ≥ 0.4 s (proposed), ActiveSec > 0, RecoverySec ≥ 0 (E1, E2).
      Nothing can deal damage before TelegraphSec ends.
- [ ] A visual tell on every pattern: pose or VFX. Sound is never the only cue (GDD SH1.0 MOVE-04) (E1).
- [ ] Bolts and the arc have a layered tell: pose and sound and VFX, all three set (E1).
      Bolts: amber clock flash plus wind-up pose. Arc: red trail. Gust: wing pose plus flow lines.
- [ ] Colour code: amber only on bolt tells, red only on the arc (E9).
- [ ] Art Director verdict on a `CAM_Eval_Arena` capture with no attack running, written on the card as:
      `Accent check: no amber or red outside bolts, tells and the arc. <name> <YYYY-MM-DD>`. Judged against
      `pipeline/art/reference/target-keyart.png`. The signed verdict is the rule; `--card` fails without it (C3).
- [ ] The fire origin is fixed from the start of the telegraph to the last bolt. Owl drift pauses for it (E12).
- [ ] Spreads: no lone bolt outside the group, staggered spawns, seed angle changes each volley,
      aimed spreads have an even count or a written `odd_count_reason` (E11).
- [ ] Projectiles draw on top and use a directional sprite with a bright core (E10).
- [ ] Engine test `UmbrellaElla.Owl.EveryPatternHasTelegraph`: loads every pattern asset; fails if
      TelegraphSec < 0.4, a bolt or arc has an empty TellPose, TellSound or TellVFX, or a pattern with
      InterruptibleSec > 0 has InterruptReplaysTelegraph false [VERIFY].
- [ ] Engine test `UmbrellaElla.Owl.World.OriginLockedDuringTelegraph`: start a pattern, move the drift
      target, assert the fire origin did not move until RecoverySec starts [VERIFY].

## 2. Every phase (`DA_Phase_Base`, or the presets `DA_Phase_Intro`, `DA_Phase_Contest`, `DA_Phase_Desperation`)
- [ ] One `base` phase 0-100%, or intro, contest, desperation back to back. Desperation ≤ 30% of the timer (E3).
- [ ] [2+ patterns] Each phase adds or swaps a pattern or space rule. Speed alone does not count (E4).
      Desperation's space rule is the torn umbrella altitude cap (`altitude_cap_y`).
- [ ] With 2+ phases, every phase change plays the one `phase_change_cue` (the clock chime). No per-phase cue (E5).
- [ ] Intro teaches before it tests: single bolts only, one gust at most, [2+ patterns] one attack at a time (E6).
- [ ] [2+ patterns] A pattern's first use never overlaps another attack (E7).
- [ ] [2+ patterns] Each phase has a breather ≥ 3.0 s (proposed) with no attack in telegraph, active or flight (E8).
- [ ] [2+ patterns] Intensity (E19, proposed numbers): no phase has an attack running more than 60% of its time.
      Density (attack-seconds per second) rises from intro to contest, and desperation is at most 1.3x contest.
      Two peaks (clusters of 2+ attacks) always have a 3.0 s breather between them.
- [ ] No camping (E20): after intro (in the one base phase), a still hero on every point of a 5x5 grid over the hero zone (corners,
      mid-edges, centre; under the altitude cap) is hit by a bolt or the arc in that phase, at both ends of the owl's drift.
- [ ] [2+ patterns] Layering (E21): contest has at least one cluster with an aimed bolt pattern (forces a move) and a
      non-aimed one (blocks a route) together.
- [ ] [2+ patterns] Midpoint turn (E24): a pattern makes its first appearance in the second half of contest
      (from about 47% of the timer). It gives the long middle phase a second beat.
- [ ] [2+ phases] Engine test `UmbrellaElla.Owl.PhaseTableDistinct`: loads the three phase assets; fails if a phase
      has the same pattern set and space rules as the one before [VERIFY].
- [ ] [2+ phases] Engine test `UmbrellaElla.Owl.World.PhaseChangePlaysCue`: run the timer through both changes,
      assert the chime fired exactly twice with the same sound asset [VERIFY].

## 3. The arena
- [ ] The owl stays in the right half. Hero zone and owl zone do not overlap (E17).
- [ ] Safe path (E13): the hero starts at each aim point (high, middle, low) with the owl at both drift ends,
      moves at the tuning speeds, and has a hero-sized safe path through every cluster. 2D, on the data.
      The arc is simulated as an out-and-back loop from its row: `reach`, `side`, `flight_sec`, `core_radius`
      (E2 fails a missing field). The engine test below checks the real curve.
- [ ] [SURV-04] Recovery with the torn umbrella (E25): at the lowest lift tier, the climb from the lowest hero spot to the
      highest one under desperation's cap (plus half the open rise ramp) fits in desperation's longest breather.
      The checker prints both numbers. Fix by lowering the cap or widening a breather, never by a speed copy.
- [ ] Engine test `UmbrellaElla.Owl.World.SafePathAtDriftExtremes`: same rule on the real projectiles,
      the real hero collision and the arc [VERIFY].
- [ ] Owl hit reactions (COM-02, COM-03: off in GDD 1.3, so 0 and `[1.0]`; E29). Clock hit (E26): every pattern has `interruptible_sec` (0 = not
      disrupted, at most 1.0 s, proposed). If it is above 0, `interrupt_replays_telegraph` is true: the attack pauses
      and, if its telegraph was showing, the full telegraph plays again. An interrupt never shortens a telegraph.
      [2+ patterns] Every phase still has a 3.0 s breather with every interruptible attack late by its pause plus a telegraph.
      Wing hit (E27): the gust has `gust_strength_by_wing_tier` (1.0 first, never rising, in (0, 1]) and one
      `wing_tear_overlays` texture per damaged tier, so the weaker gust is visible. Cut = `[1.0]` and 0 everywhere.
- [ ] Hitboxes: hero hurtbox ≤ 50% of the body sprite area (E22, from `feel.json`). Owl hitbox ≥ 80% of
      the owl sprite area, so auto-fire lands on what the player sees (E23). Live sizes:
      `UmbrellaElla.Feel.Hitboxes` (Feel lane) [VERIFY].
- [ ] Every gust zone sits inside the hero zone and leaves a hero-sized lane above or below (E15).
- [ ] Coverage (E14): by the end of contest every row has a pattern: high, low, far, rise, fall, horizontal,
      gust. A bolt or arc that claims a position must reach that third. Card line:
      `Coverage signed: <name> <YYYY-MM-DD>`, by the Game Designer reviewer. `--card` fails without it (C2).
- [ ] Two fixed eval cameras, placed by the Integrator: `CAM_Eval_Arena` (full arena, no attack) and
      `CAM_Eval_Stress` (the desperation cluster with the most patterns at once).
- [ ] Nothing moves against the bolts. Art Director verdict on two `CAM_Eval_Stress` frames 0.1 s apart, written as:
      `Motion check: nothing but projectiles moves within 64 px of a projectile. <name> <YYYY-MM-DD>`.
      The signed verdict is the rule; `--card` fails without it (C3).
- [ ] The card lists any decor in `CAM_Eval_Stress` that looks like a hazard or a ledge but is not.

## 4. The end event
- [ ] `end_event` stops threats, the owl departs, the Survived card shows, quiet ≥ 5 s (E16, GDD SH1.0 OWL-06, OWL-35).
      A story clue is optional: narrative is DEFERRED (NAR-01).
- [ ] Engine test `UmbrellaElla.Owl.World.NoDamageAfterEndTrigger`: fire the end trigger with bolts in
      flight, tick 5 s, assert 0 damage events and the Survived card is shown [VERIFY].

## 5. Before the first encounter card
- [ ] P0: one person from outside the team walks the phase table from `encounter.md` on paper: for each
      phase, what they think the owl will do and where they would stand. The card has a line
      `Paper walk: <link or #n to the tracker comment with their answers>` and lists what changed, or `no change`.
      Later encounter cards repeat the same line. `--card` fails without it (C4).

## 5b. The card itself
- [ ] `python3 tools/encounter_check.py --card <card.md>` prints `card_check: 0 problem(s)`, pasted by the
      reviewer. It checks the pasted data gate (C1), the coverage, art and paper-walk lines (C2-C4), and that each
      of the 5 Owl tests is on a `PASS` line or a `Not run` line with the building card's number (C5).
      `pipeline/level/fixtures/card_ok.md` is a passing example.

## 6. Reading the playtest
- [ ] After every hit, the observer asks "What hit you, and what warned you?"
- [ ] Log columns: `session,event,phase,pattern_id,explained,t_run_s,build`. `event` is `hit`, `death` or `survive`.
      Every hit and death row has a `pattern_id` from `encounter.json` (or `BOTTOM_EXIT`) and `explained` = y/n.
- [ ] `python3 tools/encounter_check.py --playtest <log.csv ...>` prints `playtest_check: 0 problem(s)`
      (rules L1-L6; a header-only log fails) and a per-pattern table of hits, deaths and `explained=n`. Paste it on the playtest record.
      Owner: QA and Build. The `Columns:` line in `pipeline/qa/playtests.md` and the logger card must match these
      columns (`--wiring`, W3). `pipeline/level/fixtures/logger_output.csv` is the logger's expected output;
      a unit test runs `--playtest` on it.
- [ ] A hit the player cannot explain (`explained=n`) is a bug against that pattern ID (tell too weak, too short,
      or hidden). Fix the tell, not the numbers. Only explained hits count toward difficulty tuning.
