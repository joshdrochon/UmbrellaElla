> Generated from `docs/gdd/README.md`, `docs/gdd/questions-1.3.md`, `docs/gdd/questions-B1.0.md`, `docs/game-spec.md`, `docs/balance.md`, `pipeline/checklists/design-review.md`, `pipeline/checklists/tuning.md`, `tools/manifest_check.py`, `tools/gdd_impact.py`, `tools/gdd_select.py`, `tools/bake_preset.py`, `tools/tuning.py`, `tools/progression_model.py` at `fbcd307` — edit the sources, not this file.
> Rebuild: `python3 tools/export_package.py`. Check: `python3 tools/export_package.py --check`.

# Design Pipeline

A readable copy for people. Agents load these rules from the repo paths listed below.

## About this pipeline

- **Purpose:** Keep the game spec, balance targets and tuning changes in line with the current GDD snapshot.
- **Owner:** Game Designer role; the game design owner (human) accepts numbers and design calls.
- **Inputs:** The GDD snapshot and feature manifest (see Reference/), playtest rows of class `design`.
- **Outputs:** `docs/game-spec.md` defaults, `docs/balance.md` targets, tuning cards, questions for the GDD authors.
- **Gates:** Design review before a rule card is ready; `manifest_check.py` in CI; `gdd_impact.py` on a GDD revision.

## Built from

- How a GDD revision lands: `docs/gdd/README.md`, `docs/gdd/questions-1.3.md`, `docs/gdd/questions-B1.0.md`
- Spec and balance: `docs/game-spec.md`, `docs/balance.md`
- Checklists: `pipeline/checklists/design-review.md`, `pipeline/checklists/tuning.md`
- Commands and checks: `tools/manifest_check.py`, `tools/gdd_impact.py`, `tools/gdd_select.py`, `tools/bake_preset.py`, `tools/tuning.py`, `tools/progression_model.py`

## How a GDD revision lands

### `docs/gdd/README.md`

#### GDD revisions: how a new one lands (on demand)

Load this when a GDD revision arrives or you change `docs/feature-manifest.json`. Expect 1-4 revisions a day.

Files:
- `docs/gdd/GDD-<rev>.md`: one read-only snapshot per revision. Never edited after it merges.
- `docs/gdd/CURRENT`: one line, the snapshot agents read (now `GDD-1.3.md`).
- `docs/feature-manifest.json`: one record per feature ID, statuses copied from the GDD (source of truth #1).
- `docs/gdd/questions-<rev>.md`: open questions for the GDD authors.
- `docs/gdd/archive/`: superseded drafts. Never in any read order.

##### A new revision (about 30 min, one PR, the integration owner)
1. Convert the PDF to `docs/gdd/GDD-<rev>.md`: same header table as `GDD-1.3.md` (revision, date, source commit), text below `---`.
2. Point `docs/gdd/CURRENT` at it. Pin it: add the line `python3 tools/manifest_check.py --pin docs/gdd/GDD-<rev>.md` prints to
   `gdd_snapshots` in `docs/feature-manifest.json`, and set `gdd_snapshot`. Old pins never change (CI compares them with the base branch).
3. Update `docs/feature-manifest.json`: new or removed IDs, status words exactly as the GDD prints them, `gdd_revision`.
   Never promote: only the design owner and the technical owner change a status or `implementation_authorized`.
4. Run, and paste both under `## GDD impact` in the PR (`check_pr.py` fails without it):
   `python3 tools/gdd_impact.py docs/gdd/GDD-<old>.md docs/gdd/GDD-<rev>.md`
   `git show origin/main:docs/feature-manifest.json > /tmp/old.json && python3 tools/gdd_impact.py /tmp/old.json docs/feature-manifest.json`
5. `python3 tools/gdd_select.py docs/gdd/GDD-<rev>.md --set-current --check`, `python3 tools/manifest_check.py` and
   `python3 tools/pipeline_check.py` print no problems. `gdd_select.py <rev> --check` lists what a revision still needs,
   one line each; `tools/kickoff.sh --gdd <rev>` tests a revision for one run without changing `CURRENT`.
6. Each "cited by" line is a card, test-map row, preset or doc line to re-check. Fix it in this PR or file a card for it.
   Open cards on the old revision stay valid unless one of their Features changed; `check_card.py` fails exactly those.
7. Move answered questions out of `questions-<old>.md` into a new `questions-<rev>.md`.

A status change (a sign-off) is a new revision too: the GDD's own change rule says "Future changes must increment the
document version and add dated revision notes", and `manifest_check.py` holds every status to the current snapshot.
Richard signs off by publishing the new PDF revision; then steps 1-7 run as above.

### `docs/gdd/questions-1.3.md`

#### Open questions for the GDD authors (GDD 1.3)

Master list for `docs/gdd/GDD-1.3.md` (commit `73b6a93`). Each has the pipeline's interim behavior, so work goes on.
Answer in the next GDD revision (the commit note says: increment the version and add dated revision notes) or on the
decision row named. Owner: Richard (design owner and document approver, GDD 1.3 §14) unless the row says otherwise.
The B1.0 round and what 1.3 answered: `docs/gdd/questions-B1.0.md`.

| # | Question | Interim behavior in the pipeline | Where it lands | Status (source) |
|---|---|---|---|---|
| Q1 | The cover says "REVIEW CANDIDATE 1.3 ... Not yet merged to GitHub" and §A says only a later approved replacement of the GitHub file is authoritative. The design owner merged it to `origin/main` (`73b6a93`). Is 1.3 the approved revision? | Treated as the approved revision: it is the PDF in GitHub (§14: "Only the approved PDF in the GitHub repository is the authoritative source after upload") and it calls itself "Richard-approved baseline". The manifest marks its APPROVED_P0 items implementation_authorized | next GDD revision's cover line | open (GDD v1.3 cover vs §14) |
| Q2 | ART-02 (developer art-set selector) has no status word, only "Optional debug capability / OFF" (§5). Which status? | PROPOSED, off, no implementation authority, like VFX-01 | `docs/feature-manifest.json` ART-02 | open (GDD v1.3 §5) |
| Q3 | VFX-01 still has no status word ("Optional; reset", §5). Which status? | PROPOSED, off (D-new-unstated-status) | `docs/feature-manifest.json` VFX-01 | open (GDD v1.3 §5; carried from B1.0 Q9) |
| Q4 | QA-18 and §12A ask for a clean Windows **shipping** build. D6, D25 and D-new-ship-required say the jam takes a **Development** package and no Shipping run is needed. Which build does QA-18 mean? | The submission stays the Development package (jam rule). QA-18 runs on it: no workbench (D-new-workbench-debug), no missing assets, keyboard and controller play | D-new-gdd13-shipping (`docs/decisions.md`) | open (GDD v1.3 QA-18, §12A vs D6/D25) |
| Q5 | Encounter numbers: `pipeline/level/encounter.json` still has a 150 s encounter with several patterns (D-new-level-rules); GDD 1.3 approves 90 s and one bolt pattern (3.0 s cadence, 0.75 s warning, 350 cm/s, 2.0 s grace, seed 20261112) | GDD 1.3 wins. The manifest `approved_parameters` holds the 1.3 numbers; a Level Designer card re-files `encounter.json` and `pipeline/feel/feel.json` to them (D20: numbers change only through tuning cards) | D-new-gdd13-numbers (`docs/decisions.md`) | open (GDD v1.3 §5A, §7B) |
| Q6 | Is the manifest's feature-to-QA mapping right? GDD 1.3 gives it only for UMB-03 (Appendix B: QA-04, QA-10) | The `tests` mapping in the manifest, kept equal to `pipeline/qa/test-map.md` Features columns; QA-13..QA-28 mapped by the pipeline | D-new-qa-mapping | open (carried from B1.0 Q12) |
| Q7 | Exact art style reference file (Appendix D: open for Josh) | `pipeline/art/art-bible.md` and the key art, both provisional placeholders (GDD 1.3 §7C, §9) | D-new-art-direction-doc | open (GDD v1.3 Appendix D; carried from B1.0 Q13) |
| Q8 | Hold/Toggle setting (D18) was for "hold Space to open". In 1.3 the umbrella is open by default and ATTACK/SHIELD are holds. Does a Toggle setting apply to ATTACK and SHIELD? | Hold is the default for ATTACK and SHIELD (GDD 1.3 §9). A Toggle option is P1 and applies to each separately; shield still wins | D18, `pipeline/ui/accessibility.md` | open (GDD v1.3 §9 vs D18) |

### `docs/gdd/questions-B1.0.md`

#### Open questions for the GDD authors (GDD B1.0)

Superseded by GDD 1.3 (`docs/gdd/GDD-1.3.md`, commit `73b6a93`). Kept as the record of the B1.0 round; the
"GDD 1.3" note at the end of each Status cell says what the new revision decided. Still-open items moved to
`docs/gdd/questions-1.3.md`. Where GDD 1.3 decides, it wins over the 11/8 baseline and the midnight defaults.

Master list (B1.0). Each has the pipeline's interim behavior, so work goes on. Answer in the next GDD revision or on the
decision row named. Owner: the design owner (Rick) unless the row says otherwise.

Status as of 2026-11-09. No new GDD revision came and nobody answered on Discord. Sources: the 11/8 meeting
baseline (Drive Meeting Notes, 11/8; D-new-team-baseline), team chat 8 Nov 9:13 PM, and Josh's default to the team
at 9:08 PM 8 Nov ("if no answer by midnight PST, the default is written in"). DEFAULTED rows are
"DEFAULTED 2026-11-09 00:00 PST, changeable; design items need Richard (GDD approver) to confirm".

| # | Question | Interim behavior in the pipeline | Where it lands | Status (source) |
|---|---|---|---|---|
| Q1 | Gravity / fall-speed slider: now, or in a later revision? | Answered for scope by D-new-workbench-debug: sliders (gravity included, GDD B §10) exist only in the workbench in debug and dev builds. The submitted game has no slider; the approved preset's values ship as plain defaults (`tools/bake_preset.py`). Still no fast fall; a player-facing fall-speed setting would be a new feature ID | D-new-workbench-debug; next GDD revision for a player-facing slider | ANSWERED 2026-11-08 (team chat 9:13 PM, D-new-workbench-debug): sliders exist in debug builds only; fall speed is fixed in the shipped build. GDD 1.3: ANSWERED by GDD v1.3 (§5A, §9): gravity 980 cm/s^2 is an approved tuning value with a dev-only slider; the submitted build has no workbench |
| Q2 | Which features are APPROVED_P0? B1.0 approves none | Recommended baseline (`docs/jam-brief.md` MVP) approved for Nov 12 builds, pending Richard. The manifest stays unsigned until he signs | D-new-p0-signoff (Day-1 blocker) | DEFAULTED 2026-11-09 (Josh's 9:08 PM default): recommended baseline approved for Nov 12 builds, pending Richard. GDD 1.3: ANSWERED by GDD v1.3 (§2): Richard approved the P0 list; the manifest marks it APPROVED_P0 |
| Q3 | Default attack trigger: what makes COM-01 fire (always, closed only, in a lane)? | COM-01 stays OPEN, flag off. Attack-descent auto shots and the shield-descent mode are built behind the COM_01 flag | DEC-02 | ANSWERED 2026-11-08 (11/8 meeting baseline): attack-descent auto shots, separate shield-descent mode. Replaces the 9:08 PM "hook only" default. GDD 1.3: ANSWERED by GDD v1.3 (DEC-02, §7B): hold ATTACK for ATTACK_DESCENT, fixed +X shots every 0.65 s; no shots in UP_OPEN or SHIELD |
| Q4 | Default key and controller bindings? | Data-driven bindings. Controller in, mobile out. A/D move, Space hold umbrella, Esc pause, remappable; attack-descent and shield-descent bindings (all PROPOSED) | DEC-01 | PARTLY ANSWERED (11/8 meeting baseline): controller in, mobile out. Rest DEFAULTED 2026-11-09 (Josh's 9:08 PM default): A/D, Space hold, Esc, remappable, mode bindings, all PROPOSED. GDD 1.3: ANSWERED by GDD v1.3 (§9): A/D or arrows steer, hold left mouse attack, hold right mouse shield, release both = UP_OPEN, Esc pause, R retry; controller left stick, R2, L2, Options/Menu, confirm. Replaces the Space-hold default |
| Q5 | Who are "R" (implementation support) and "organizer" (tester with C)? | Richard approves design, a design reviewer (named in the 11/8 notes) reviews, Rick runs most builds. "R" and "organizer" kept as written; no seat assigned | D-new-gddb-people | PARTLY ANSWERED (11/8 meeting baseline): Richard approves design, a design reviewer (named in the 11/8 notes) reviews, Rick runs most builds. "R" and "organizer" DEFAULTED 2026-11-09 (Josh's 9:08 PM default): left as written. GDD 1.3: ANSWERED by GDD v1.3 (§14): Richard is design owner and approver; Josh is pipeline and AI lead with the design reviewer assisting; Rick is GDD contributor and runs rehearsal builds. "R" and "organizer" are gone |
| Q6 | How much of the tester workbench should exist before the jam? | Toggles, presets, seeds and reset on stand-in objects only, no umbrella or owl content (cards 0.25, 0.26). Debug-only in every build (D-new-workbench-debug) | D-new-workbench-prejam; `pipeline/day0-cards.md` | DEFAULTED 2026-11-09 (Josh's 9:08 PM default): toggles, presets, seeds and reset on stand-in objects only. GDD 1.3: ANSWERED by GDD v1.3 (§12, §14): only a generic harness on unrelated stand-in objects before the start |
| Q7 | Completion rule: what makes the owl depart? | Configurable completion rule; a timer is only a test fixture | DEC-06 | DEFAULTED 2026-11-09 (Josh's 9:08 PM default): timer as a test-only placeholder; DEC-06 stays open. GDD 1.3: ANSWERED by GDD v1.3 (§8, DEC-06): 90 s of unpaused ACTIVE time; the rule stays replaceable |
| Q8 | Two-part statuses (COM-01, SURV-02, FLOW-01 say "CONFIRMED intent / OPEN implementation"): which half governs building? | Treated as OPEN, behind a switch: the manifest records the implementation half, so nothing is promoted; FLOW-01 stays default on | D-new-two-part-status; `docs/feature-manifest.json` | PARTLY ANSWERED (11/8 meeting baseline): wear from certain wind currents, healing via shield mode. Rest DEFAULTED 2026-11-09 (Josh's 9:08 PM default): OPEN, behind a switch. GDD 1.3: ANSWERED by GDD v1.3 (§2): no two-part statuses left; COM-01, SURV-02 and FLOW-01 are APPROVED_P0 |
| Q9 | COM-02, COM-03, COM-04 and VFX-01 have no status in §2. Confirm them | COM-02, COM-03: EXPERIMENT (§7 "Experiment"); COM-04, VFX-01: PROPOSED | D-new-unstated-status; `docs/feature-manifest.json` | DEFAULTED 2026-11-09 (Josh's 9:08 PM default): EXPERIMENT / PROPOSED as listed, all off. GDD 1.3: PARTLY ANSWERED by GDD v1.3 (§5): COM-02, COM-03, COM-04 are Experiment. VFX-01 still has no status word (questions-1.3 Q3) |
| Q10 | Does horizontal speed depend on the umbrella state? §3 step 5 says input is independent of orientation | `feel.json` keeps separate open and closed sideways numbers as tuning values only; the "open must be slower" rule is gone | `docs/feel-spec.md` section 7 | open (not in the 11/9 defaults). GDD 1.3: ANSWERED by GDD v1.3 (§3 step 5, §5A): steering is independent of the umbrella; one open-horizontal multiplier, default 100% |
| Q11 | Camera and arena: fixed single screen (B1.0 §1, §7) or scrolling? Raised in team chat 8 Nov, not decided | `camera_mode` in `docs/feature-manifest.json` `build_parameters`, default `fixed_single_screen`; lanes and checks read it, none assume one screen | next GDD revision; scrolling changes §1, §7 and the arena cards | open (not in the 11/9 defaults). GDD 1.3: ANSWERED by GDD v1.3 (§1, §7, Appendix A): fixed 16:9 single screen; scrolling is CAM-02, EXPERIMENT, off |
| Q12 | Is the manifest's feature-to-QA mapping right? GDD B gives it only for UMB-03 | The current `tests` mapping; Rick and Richard check it at sign-off | D-new-qa-mapping | DEFAULTED 2026-11-09 (Josh's 9:08 PM default): current mapping, checked at sign-off. GDD 1.3: OPEN: GDD v1.3 still gives the mapping only for UMB-03 (questions-1.3 Q6) |
| Q13 | Is there a separate art direction doc? | None found. Art rules come from `pipeline/art/art-bible.md` and the key art; `Test_Assets/Asset Notes.md` on origin/main is the asset spec reference | D-new-art-direction-doc | DEFAULTED 2026-11-09 (Josh's 9:08 PM default): no separate file; art bible + key art. GDD 1.3: OPEN: GDD v1.3 Appendix D lists the art style reference file as open for Josh (questions-1.3 Q7) |

## Spec and balance

### `docs/game-spec.md`

#### Game spec defaults (owner: game design owner)

The current GDD snapshot (`docs/gdd/CURRENT`, now `docs/gdd/GDD-SH1.0.md`) and `docs/feature-manifest.json` win on mechanics.
This file holds the defaults agents need that the GDD leaves to the team. Every line is a default, not a decision. Change it
in a PR the game design owner approves. Where a row in `docs/decisions.md` covers the same thing, that row wins. Numbers live
in `pipeline/feel/feel.json` (movement and feel) and `pipeline/level/encounter.json` (the Keeper fight); this file does not copy them.
GDD SH1.0 prints the starting numbers in its rule text (`docs/feature-manifest.json` `approved_parameters`, traced by
`tools/manifest_check.py`); its section 9 ranges are blank (D-new-sh10-param-ranges). The prototype defaults for details the
GDD leaves OPEN are listed in the ledger's import report and follow D-new-sh10-open-details.

##### Controls (GDD SH1.0 MOVE-04..MOVE-10, MOVE-17)
Bindings are data (Input Adapter, `Content/UmbrellaElla/Input/`). Keyboard / mouse and controller are both required, all remappable (MOVE-10).
| Action | Keyboard / mouse | Gamepad |
|---|---|---|
| Rise: release Shoot and Absorb (overhead) | – | – |
| Shoot + drop (unlimited, fires right) | Left mouse / J | R2 / RT |
| Absorb + drop (catch yellow, heal) | Right mouse / K | L2 / LT |
| Fast free fall (no fire, no suction) | both | both |
| Hop (overhead) / context dash (falling) | Space | Cross / A |
| Falling dash back / forward | Q / E | L1 / LB, R1 / RB |
| Ride a harmless current (overhead, inside it) | Left Shift | Triangle / Y |
| Trim up / down | W / S, arrows | Left stick |
| Spells (Director's Cut) | 1-4, [ / ] | Right stick, D-pad |
| Pause | Esc, F1 | Options / Menu |
| Retry after defeat | Enter | Cross / A |
Direct horizontal steering is OFF and there is no mouse aiming (MOVE-07). Fire always goes right. Controls show in the
tutorial and the pause menu, read from the current bindings. Every menu works with keyboard only (`pipeline/ui/menus.md`).

##### Movement modes (GDD SH1.0 MOVE-19, MOVE-21)
Neither held = overhead rise; Shoot only = shooting fall; Absorb only = absorbing fall; both = fast free fall. Each mode is a
speed, not gravity (`feel.json` rise_speed / fall_speed / free_fall_speed). Wind, gust push, damage and the ceiling modify motion
separately. Lift falls with active health to `lift_min` (SURV-05). Dash invulnerability is OFF; hop protection and post-hit
protection are separate (MOVE-15).

##### The Keeper arena and the level (GDD SH1.0 section 5; D-new-sh10-units, D-new-sh10-camera)
- Keeper fight (both modes): fixed 16:9 single screen, 1920 x 1080 units (1 unit = 1 cm). Map `L_Graybox` first, then the arena map the Integrator builds from it (D23).
- Director's Cut level: nine chunks from the 12-chunk / 24-variant catalogue, 1920 units each, three refuges with checkpoints, a side-scrolling camera that reveals the next current, hazard and exit (FLOW-24, HAZ-37, CAM-08).
- The bottom is lethal; supports and solid land are harmless (WIND-03).

##### Keeper phases (GDD SH1.0 OWL-06..OWL-35; owner: Encounter Director)
Wings, then the three hanging mechanisms front → middle → rear, then the clock; a checkpoint at each phase start. Death retries
the current phase with full active health and exactly 3 current lives. Success happens once at the final clock hit; the Keeper
withdraws alive in about 2.5 s. Same-frame defeat versus final clock hit is OPEN: default, defeat wins (one terminal event).
Attacks, numbers and breaks: the `GDD-SH1.0` preset in `pipeline/level/encounter.json` (`pipeline/level/encounter.md`).

##### Screens and flow (FLOW-02..FLOW-04, FLOW-34..FLOW-41, FLOW-49; D-new-lose)
Start (Start Game, Start Director's Cut) → first-start tutorial (Pause → Skip) → play. Start Game goes straight to the Keeper;
Director's Cut plays the level first. Win: ending story text over the background, then credits with music; Director's Cut then
shows Journey Complete statistics (Try Again, Main Menu). Fail screen when the last life empties: says what ended the run,
then Retry (the checkpoint, not a mid-run restart) or Quit. Pause: Continue, Settings, Quit.
Settings and accessibility: `pipeline/ui/accessibility.md`, `pipeline/ui/menus.md`.

##### Health (GDD SH1.0 SURV-05, FLOW-30..FLOW-33)
One top-left antique clock: the health hand (III full, back toward XII on hits) and the life hand. 3 hits per life, 3 lives;
incoming damage 1 (red, yellow, gust, traps), 1.25 (chain head), 1.5 (talon). Yellow absorbed while dropping heals 0.5 (+0.3 per
recovery rank), active life first, then a spent reserve. No revival after final defeat. Reference model: `tools/progression_model.py`.

##### Feedback the player reads
| Signal | Means | Owner |
|---|---|---|
| Clock HUD hands and arc | Active health and lives (FLOW-30) | Art Director |
| Keeper wings, mechanisms and clock | Phase, eligible target, warning / strike / recovery (ANIM-06) | Art Director |
| Broad ash-blue current vs jagged front | Safe current vs hostile gust (OWL-17, BG-05) | Art Director |
| XP ring (Director's Cut) | XP toward the next level, pulse and clock sound on level-up (FLOW-48) | UI and UX |
| Sound | Warnings, launches, hits, catches, state changes (`pipeline/audio/sound-list.csv`) | Audio |
Every critical event has one sound and one visual: `pipeline/ui/signals.json`, checked by `python3 tools/ui_check.py signals`.

##### Engine tests
GDD SH1.0 acceptance scenarios QA-29..QA-42 (the manifest `tests` of each feature) and the engine tests in
`pipeline/qa/test-map.md`. A card for a feature is not ready without its test in Done-when (`pipeline/checklists/design-review.md`).

##### Audio
The sound list is `pipeline/audio/sound-list.csv` (Audio role); tier P0 = due at G1. Music and sound effects are separate
deliverables (`pipeline/roles/audio.md`). Every sound has a provenance row (`pipeline/art/provenance.csv`).

### `docs/balance.md`

#### Balance (owned by the Game Designer role; values decided by the human game design owner)

Combat balancing is the Game Designer's job, with the Level Designer's encounter data (`pipeline/level/encounter.json`).
All targets are proposed until the game design owner accepts them. Measured numbers are pasted from command output
with the commit they came from. GDD SH1.0 rule numbers (section 9 ranges blank, D-new-sh10-param-ranges) gives Richard's approved provisional numbers (90 s, one bolt, 100 HP,
34 damage, heal 20 with a 2 s cooldown, 0.8 s invulnerability). They are not balanced values; a change goes through the GDD and the manifest.

##### Targets per phase
The baseline is one `base` phase with one bolt (GDD SH1.0 OWL-06, OWL-35: phases are optional presets). The preset rows apply only if a
DECIDED row turns the presets on. The gust row needs OWL-02 on; the weaker climb needs SURV-04 on (DEC-05: off).
| Phase | New element | Target hits taken (median, cold players) | Max share of the phase's hits from one pattern | Target rating (1–7, survey) | Status |
|---|---|---|---|---|---|
| Base (0-100%, baseline) | rise vs fall, the one bolt, shield catch and heal, safe wind | 1–3 | n/a (one pattern) | 3–5 | proposed |
| Intro preset (0-25%) | rise vs fall, the bolt; one gust only with OWL-02 on | 0–1 | n/a | 2–3 | proposed |
| Contest preset (25-70%) | bolts; telegraphed owl winds only with OWL-02 on | 1–2 | 50% (only with 2+ patterns) | 3–5 | proposed |
| Desperation preset (70-100%) | faster cadence; weaker climb only with SURV-04 on | 1–2, and a recovery route used | 50% (only with 2+ patterns) | 4–5 | proposed |
| Whole run | | survive rate of cold players on a first run 30–60%; a fail names its cause (P4) | no pattern over 50% of all hits, only with 2+ patterns (P7) | fun ≥ 5 (P11) | proposed |

How each column is measured:
- Hits and fails: the run log (`pipeline/qa/playtests.md`, card 0.23) and `python3 tools/encounter_check.py --playtest Saved/Playtest/*.csv`, which prints hits, deaths and `explained=n` per pattern.
- Rating: the median of the survey's per-phase score (`pipeline/qa/playtests.md`, Survey).
- Status is `proposed`, `accepted` (owner agreed; not yet met), `missed`, or `met n=<players> tuning=<sha>`. `met` needs 4 or more valid players at one tuning commit (D-new-pool). G3 runs 4 cold players for that.

##### Movement envelope (measured by `UmbrellaElla.Move.World.FeelEnvelope`, card 0.13; paste output + commit)
| Measure | Value | Commit |
|---|---|---|
| Sideways accel frames, 0 to 350 cm/s (`accel_f`) | not measured | |
| Max fall cm/s (one gravity rule; no multiplier, no fast fall, GDD SH1.0 rule numbers (section 9 ranges blank, D-new-sh10-param-ranges)) | not measured | |
| UP_OPEN rise cm/s, full / lowest health (equal: no lift loss, DEC-05) | not measured | |
| State blend frames | not measured | |
Targets: GDD SH1.0 rule numbers (section 9 ranges blank, D-new-sh10-param-ranges) (manifest `approved_parameters`), copied in `docs/feel-spec.md` section 7. `encounter_check.py` reads hero
speeds from the tuning file, so the safe-path check (E13), and the recovery check (E25, only with SURV-04 on), use them.
Every Commit cell must be the last `*Tuning.h` commit or newer.

##### Change history
See the log in `pipeline/checklists/tuning.md`.

## Checklists

### `pipeline/checklists/design-review.md`

#### Design review checklist (run by the Producer before a rule card is ready)

Use it for cards that add or change a game rule or the arena: umbrella, wand, damage, health, wear,
gusts, owl patterns or phases, the end event. Art, import, tooling and pipeline cards skip it.
A card that fails any line is not ready. Fix the card or open a decision row.

##### 1. Where each line comes from
Tag every design line the card quotes:
- `GDD RULE`: in the GDD snapshot `docs/gdd/CURRENT` names, with its feature ID authorized in `docs/feature-manifest.json`. Build it exactly.
- `DEFAULT (Dn)`: a default from `docs/decisions.md` or `docs/game-spec.md`. Build it, and name the row in the PR.
- `HYPOTHESIS (Pn)`: something a playtest is meant to check. Build it so it is easy to change (a tuning value, not code).
- `ILLUSTRATIVE`: comes only from the key art or an example. It adds no rule. A card may not build it as a rule.

##### 2. The card says
- [ ] **Player outcome:** "The player sees X, does Y, and can tell why." If the card adds nothing the player sees, does or learns, flag it to the scope decision-maker.
- [ ] **Inputs:** which Enhanced Input actions it reads.
- [ ] **States and changes:** every state it adds or changes, and what moves between them.
- [ ] **Blocked path:** what happens when the player does it at the wrong time (opening while DEFEATED, a catch from the wrong side). The blocked path has its own cue and its own test.
- [ ] **Input conflicts:** the outcome for each one that applies. Open on the same frame as a hit. Close while still rising. Open during hit-stop. Pause during the end event. Anything not stated becomes a decision row first.
- [ ] **Pause, respawn, restart:** in Hold mode the umbrella state matches the held button after each one; in Toggle mode it keeps the last toggled state (D18).
- [ ] **Cues:** a visual and a sound for each state change, with the art-bible row and the `pipeline/audio/sound-list.csv` row that supply it. No state change without a cue. Each key state also reads with no sound.
- [ ] **Not colour alone:** each state cue differs by shape or motion, not colour alone.
- [ ] **No fast flashing:** no cue flashes more than 3 times per second. The card states each flash's duration and rate. Checked by `python3 tools/ui_check.py flashes` on a capture clip.
- [ ] **No feel words without a check.** "Responsive", "floaty", "fair", "readable", "satisfying" must name the number or the P-test that checks it.
- [ ] **Prompts wait for the player:** a text prompt stays until the action is done or the player dismisses it. No timed-out teaching text.
- [ ] **Settings persist:** a card that adds a setting (volume, window mode, umbrella mode, remap, assist) has a Done-when that changes it, restarts the packaged build, and reads the kept value from the log.
- [ ] **Owl windups:** each owl attack has its own windup sound, which starts at or before the visual tell and >= 0.2 s before danger (`audio_check.py --log`).
- [ ] **Owl pattern or phase card:** Done-when has `encounter_check.py` 0 problems and names the `UmbrellaElla.Owl.*` tests from `pipeline/checklists/level-sections.md`.
- [ ] **Named test copied:** a card that builds a feature has the tests of every `pipeline/qa/test-map.md` row that lists its feature ID in its Done-when.
- [ ] **Behind its flag:** a card for a non-CONFIRMED feature builds it behind its flag at the manifest default, with a flag-off test (`pipeline/unreal-rules.md`, Feature flags).
- [ ] **Menus by keyboard:** a card that adds or changes a menu has the Done-when "works with arrows, Enter and Esc only", proven by a packaged-build smoke step that goes title → play → pause → quit by keys.
- [ ] **No hidden help:** owl timing, damage and lift never change with how the player is doing. Any assist is a visible setting with a decision row, and the run log records it.
- [ ] **Gamepad too:** GDD SH1.0 MOVE-04 targets keyboard and controller. A card that adds an input action binds a gamepad key next to the keyboard key in `IMC_Default`/`IMC_Menu` (bindings stay the GDD's open default-bindings question until decided). From G2, at least one valid gate playtest run is on a gamepad (the observer notes the device).
- [ ] **Done-when** has the normal path plus at least one blocked or interrupted path.
- [ ] **New numbers or behavior** not in the GDD, game-spec or D20 (coyote time, knockback, buffers) have a decision row.

##### 3. What else it can break (re-run before merge)
- [ ] A card that changes the camera, sprite scale, palette, background motion or owl telegraph art re-runs the P8 captures (`CAM_Eval_Arena`, `CAM_Eval_Stress` once it exists) with `art_check.py` and `ui_check.py contrast`, output pasted in the PR.
- [ ] A rule or tuning card lists under `Used by` the P-tests and `encounter_check.py` codes its change can move; those re-run before merge (encounter_check) or at the next gate (P-tests), and the gate record links them.

##### 4. Same behavior, new look
A projectile or pattern that looks different but behaves the same is a new sprite or data asset on the existing class.
It is never a new C++ class.

### `pipeline/checklists/tuning.md`

#### Tuning changes (the D20 values and anything else in `UUmbrellaTuning`, `feel.json` or `encounter.json`)

> GDD SH1.0 note (D-new-gdd-sh10): lines on this page that still describe the GDD 1.3 encounter (one owl bolt, the front shield, the 90 s survival timer, wear stages, the 1.3 QA-01..QA-28 tests) are history. The current design is `docs/gdd/GDD-SH1.0.md` and `docs/feature-manifest.json`, which win; the owning role re-files this page against the SH1.0 Rule IDs on its next card.


Each component's numbers live in its own `F<Comp>Tuning` struct, default values in the header, in that component's lane
(`pipeline/unreal/gameplay-code.md`, Code layout). `UUmbrellaTuning` holds one member per struct; `Config/DefaultGame.ini` holds no tuning lines.
This page is for PRs that change a value.

##### Rules
1. One value per PR, or one named linked set (for example rise speed + blend time). Never "retuned the feel".
2. The PR states: parameter, old → new, why (the playtest row or measurement), expected effect, and how it will be checked.
3. The old value is in the commit message, so a revert is one line.
4. The Game Designer role writes the tuning card (`pipeline/roles/game-designer.md`, targets in `docs/balance.md`); the owning lane applies it. The game design owner reviews it (`docs/jam-brief.md` People). Until that person is named, the scope decision-maker does.
5. "Kept" only when the targeted P-test improves with cold players. A designer run or an agent's opinion does not count.
   A number moving the expected way is not an improvement on its own.
6. If a P-test fails because a rule is wrong in the build (for example, a closed umbrella that climbs), file a bug.
   Never retune numbers to hide a broken rule.
7. Rise speed, fall speed, sideways speed and the state blend shape every safe path. A change to any of them
   re-runs `python3 tools/encounter_check.py` (E13, E25) and P1 and P7 before it is kept.
8. Every log row has Expected filled when it is added. Observed and Kept / reverted may say `pending` until the next
   gate. The gate record fails a row still `pending`.
9. A movement value lives twice: `feel.json` `movement` (design, what the encounter sim reads) and the `*Tuning.h` default (what the game reads).
   One PR changes both. After it, the envelope table in `docs/balance.md` is re-pasted with a commit at or after it, and
   `python3 tools/encounter_check.py --envelope` on that line exits 0.
10. Percentages carry raw counts ("2 of 5 hits"), here and in the playtest log.
11. A tuning merge between two gates resets the player count for `docs/balance.md` `met` (D-new-pool).

##### Baking the chosen preset (D-new-workbench-debug)
Testers tune with the workbench sliders in debug and dev builds only. The submitted package has no sliders, so the chosen values become plain defaults:
1. A tester exports the config from the workbench (`Saved/Workbench/config-T-nn.json`). The game design owner approves that preset ID on the tracker.
2. `python3 tools/bake_preset.py bake <export> --dry-run`, then without `--dry-run`. It writes every `// bake:` default, the manifest `default_enabled` of each flag, and `pipeline/qa/baked.json`. It refuses a flag changed from its manifest default on a feature that is not implementation_authorized, an exported value with no marker, a marked default the export leaves out, a flag marker on a number instead of `true`/`false`, and a marked literal inside an expression. The first bake (card 0.27, G2) runs before every P0 is coded: it lists each required key with no marker yet as `not marked yet` and still passes.
3. One rule for the bake and both sims (`tools/tuning.py`): a value with a GDD SH1.0 rule numbers (section 9 ranges blank, D-new-sh10-param-ranges) range may be baked inside it, on its step, and only at its GDD 1.3 start unless a counted DECIDED (Richard) row in `docs/decisions.md` names that key in `Overrides: <key>` (for example `Overrides: CORE-03.max_health`; GDD 1.3 line 226: no AI tunes a parameter). A `%` key is written in percent (`100.0f`), never as a ratio, and the code converts at the point of use; a value with no range (the seed, the 2.0 s grace, collider sizes and other values with no approved entry) is fixed and never changed by a bake. The bake refuses a value that differs from `feel.json` or `encounter.json` (and, once `pipeline/qa/baked.json` exists, `feel_check.py` and `encounter_check.py` E30 fail it too): change the data file in the same PR so the envelope and the fairness sim run on the shipped number. An unapproved feature's flag always bakes off. One PR with the printed diff, rules 2 and 9 above, and the `bake_preset.py check` PASS line (`check_pr.py` asks for it). Until the first bake, CI runs `bake_preset.py defaults` on the `// bake:` defaults in `Source/`: each flag at its manifest default, each value in range and on step, and each value the sims read equal to `feel.json` / `encounter.json`. After it, CI runs `bake_preset.py check`: a stamped default must equal the stamp, and a default coded after the bake (no gameplay card's lane holds `baked.json`) passes those same defaults rules and is listed `not baked yet`.
4. The runtime tie: the packaged game logs `SMOKE_EFFECTIVE` at start and at end of run with every reflected field of the `UUmbrellaTuning` structs (where gameplay reads them) and every flag, and `bake_preset.py effective` (run by `smoke.sh` / `smoke.ps1`, the daily, `check_pr.py` and the G4 gate record on the Windows LAUNCH line) fails any live value that differs from `baked.json`, else its marked default, else the GDD start.
5. The G4 bake: after G3 (feature freeze) the Producer files one bake card (lane: `pipeline/qa/baked.json`, `docs/feature-manifest.json` default_enabled, the `// bake:` lines) that bakes the approved preset again over every coded feature. `bake_preset.py check --complete` exits 0 on it: every marked key is in the stamp and every required key has a marker. The G4 gate record's `Baked preset:` line names the approved preset and pastes `bake_preset.py check --record <record>` (the same complete mode); it fails when the stamp is another preset, any default drifted from it, or any default is not baked. `--gate-record` runs the check itself on the Build commit. `bake_preset` also refuses a value outside its approved range, an APPROVED_P0 flag off, or a preset other than T-01, unless a counted DECIDED row says `Overrides: <ID>` for it (`docs/decisions.md` rules; a row that only names the ID lifts nothing; `manifest_check.py` p0-on reads the same clause).

##### Log (one row per change)
| Date | PR | Parameter | Old → new | Motivating result | Expected | Observed | Kept / reverted |
|---|---|---|---|---|---|---|---|

## Commands and checks

### `tools/manifest_check.py`

Usage text from the file:

```text
Feature manifest gate (docs/feature-manifest.json). GDD B section 5 and Appendix B are the spec. Stdlib only.

Checks:
  schema      every record has the fields below with the right types; status and priority from the manifest's
              own vocabulary lists, which must be exactly the GDD B status words
  unique      feature IDs are unique and look like CORE-01 / UMB-02 / ...
  resolve     every requires / conflicts entry is a feature ID or a module key (GDD B section 4); never itself
  events      every emits entry is in the event vocabulary
  gdd         every feature ID and QA ID cited in the current snapshot (docs/gdd/CURRENT) is in the manifest,
              and every manifest feature ID and test ID is cited in the snapshot; gdd_revision matches it
  authorized  implementation_authorized is true only for APPROVED_P0 / APPROVED_P1, or EXPERIMENT with a named
              ticket (#<n> or UE-<n>)
  flag        a CONFIRMED record has flag null; every other record has flag = its ID with '_' (UMB-02 -> UMB_02)
  params      build_parameters (e.g. camera_mode): a default that is one of its allowed values, and a status word
  presets     pipeline/qa/presets.json: preset IDs equal the T- IDs in the snapshot; enabled features exist and are
              implementation_authorized; BASE (T-01) has empty enable and disable lists (dry run B H6)
  gdd-status  each record's status equals the status word the snapshot states for it (the first status word in
              the last cell of the table row that starts with the ID; dry run B C1: a demoted or promoted
              record fails). A row that says OFF needs default_enabled false; "no implementation authority"
              needs implementation_authorized false. An ID with no stated status may not be authorized, on, or
              APPROVED_*/CONFIRMED. priority P0 goes with APPROVED_P0 and only with it
  p0-on       every APPROVED_P0 record has default_enabled true (GDD 1.3 section 5: the BASE preset loads all P0),
              unless a DECIDED row in docs/decisions.md says `Overrides: <ID>` (decided_overrides; bake_preset agrees)
  approved    approved_parameters equals the snapshot's section 5A tables: every 5A row maps to one key (PARAM_ROWS),
              and start, step, min and max match the printed row. A new 5A row with no mapping fails too. Every entry
              traces to a 5A row or one quoted GDD sentence (PROSE_ROWS), and holds no number the GDD does not print;
              any other key or field fails (final-8 B C2)

  pin         gdd_snapshots pins every docs/gdd/GDD-*.md by sha256 (line endings normalized); CURRENT names
              gdd_snapshot; --pins-from BASE.json (CI: the base branch's manifest) fails a changed or dropped pin
  rules-pin   rules_pdf pins docs/rules/*.pdf (the Official Rules, the top source for jam rules) by sha256: the file,
              or its Git LFS pointer's oid in a checkout without LFS, matches the pin, and the sha256 line in
              docs/rules/official-rules.md's header equals it. A changed PDF with no pin update fails
  off         default_enabled true needs implementation_authorized true and an APPROVED status (dry run B C1)
  overrides   a row with an `Overrides:` clause that is DECIDED but does not count (decided_overrides) fails
  grace       a 2 h grace default row (pipeline/human-checkpoints.md): Status exactly `DECIDED <date> (agent default
              after 2h grace; <role>; human may overturn)` with a GRACE_ROLES role, in the Open decisions table, linking
              the needs-human issue; never on a human-only kind (grace_kind) and never an Overrides row (P0 is the design owner's)

  --note FILE  checks one tester note (JSON, GDD B Appendix C; pipeline/templates/test-note.md) instead

Usage: python3 tools/manifest_check.py [--root PATH] [--manifest FILE] [--note FILE]
Exit 0 = clean, 1 = problems, 2 = unreadable input.
```

Run in CI by:

- `.github/workflows/pipeline-checks.yml`: Feature manifest matches the current GDD snapshot (statuses, IDs, QA tests, presets, snapshot pins)

Tests: `tests/test_audio_check.py`, `tests/test_final8_fixes.py`, `tests/test_final9_fixes.py`, `tests/test_gdd_select.py`, `tests/test_hitbox_check.py`, `tests/test_honest_jam.py`, `tests/test_manifest_check.py`, `tests/test_pipeline_check.py`, `tests/test_story_check.py`

### `tools/gdd_impact.py`

Usage text from the file:

```text
What a GDD revision (or a feature-manifest change) touches. Stdlib only.

Compares two GDD snapshots (docs/gdd/GDD-<rev>.md) or two feature manifests (docs/feature-manifest.json shape):
  added / removed      IDs in one and not the other (feature IDs, QA-, T- and DEC- IDs)
  changed              IDs whose GDD lines (or manifest record) differ
  status               feature IDs whose status changed (old -> new)
Then lists every line in the repo that cites one of those IDs: Day-0 cards, test-map rows, presets, manifest
records and doc lines (docs/gdd/ itself is skipped: snapshots are never edited).

The first output line is the one check_pr.py looks for in a PR's "## GDD impact" section:
  gdd_impact old=<rev> new=<rev> added=N removed=N changed=N status=N cited=N

Usage:
  python3 tools/gdd_impact.py docs/gdd/GDD-B1.0.md docs/gdd/GDD-1.3.md
  git show origin/main:docs/feature-manifest.json > /tmp/old.json && python3 tools/gdd_impact.py /tmp/old.json docs/feature-manifest.json
Exit 0 always on readable input (the list is information); 2 = unreadable input.
```

Tests: `tests/test_check_pr.py`, `tests/test_final8_fixes.py`, `tests/test_gdd_impact.py`, `tests/test_manifest_check.py`

### `tools/gdd_select.py`

Usage text from the file:

```text
Pick the GDD revision a run tests, check the pipeline can import it, and say what to fix when it cannot. Stdlib only.

  python3 tools/gdd_select.py 1.4                     a revision: docs/gdd/GDD-1.4.md, else the one .md file under
                                                      scratch/gdd/ whose `| Revision | 1.4 |` row says 1.4
  python3 tools/gdd_select.py scratch/gdd/v1.4/GameDesignDocument-v1.4.md     or any .md path inside the repo
  python3 tools/gdd_select.py 1.4 --check             validate only (the same as no option: nothing is written)
  python3 tools/gdd_select.py 1.4 --set-current       validate as the official snapshot, then write docs/gdd/CURRENT
  tools/kickoff.sh --gdd 1.4 [--set-current]          (Windows: tools\kickoff.ps1 --gdd 1.4) the same check, then the
                                                      run uses that GDD and its run record stores it

What "importable" means: what the pipeline's own readers need (tools/gdd_impact.py, tools/manifest_check.py).
  GDD file   a `| Revision | <rev> |` row (gdd_impact.REVISION) and a `---` line under the header table
             (gdd_impact.body; docs/gdd/README.md step 1); feature status rows (a table row that starts with a feature
             ID like CORE-01 and ends with a status word); at least one APPROVED_P0 (the P0 list the BASE preset
             loads); section 5A parameter tables (manifest_check.PARAM_TABLE_HEADS; printed blank, as in GDD SH1.0
             section 9, they import and every approved start traces to a GDD sentence instead,
             manifest_check.PROSE_ROWS); test preset IDs with T-01 BASE;
             QA test IDs; a revision you asked for matches its Revision row; a copy that reuses a pinned snapshot's
             revision is byte-identical to it
  repo       everything tools/manifest_check.py holds the manifest to, against this GDD instead of docs/gdd/CURRENT:
             gdd_revision, a record for every cited feature and QA ID, statuses as the GDD states them, P0 on,
             approved_parameters equal to the 5A numbers, presets equal to the T- IDs, decisions.md rows
  snapshot   a docs/gdd/GDD-*.md file has a sha256 pin in gdd_snapshots that matches (manifest_check pins every one);
             with --set-current also: the file is docs/gdd/GDD-<rev>.md, the manifest's gdd_snapshot names it, and
             no other pinned snapshot has the same Revision
Each problem is one line: the file to change and what to add or fix there.

This tool never edits a GDD file, a status or approved_parameters (the GDD and its design owner own those). It writes one file,
docs/gdd/CURRENT, and only with --set-current. Without it the choice is run-scoped: kickoff sets JAM_GDD for its own
process and its agent sessions, so the run record (tools/journal.py runs) stores that GDD revision while the team
repo's official CURRENT stays as it is. The repo checks (manifest_check, pipeline_check) keep reading CURRENT.

Exit 0 = importable, 1 = problems (listed), 2 = no such file or revision.
```

Tests: `tests/test_gdd_select.py`

### `tools/bake_preset.py`

Usage text from the file:

```text
Bake the approved workbench preset into the shipped defaults (decision D-new-workbench-debug). Stdlib only.

The workbench (GDD B section 10: toggles, sliders, presets, scenarios, overlay) is compiled only into
editor and dev builds. The submitted Development package has no workbench, so the values the team picked in
it must become plain defaults. This tool writes them, so the change goes through a normal PR with the diff.

Where values go:
  params  each `F<Comp>Tuning` header default that carries a marker comment, e.g.
              float MoveSpeed = 600.f;   // bake: CORE-01.move_speed
          (pipeline/unreal/gameplay-code.md; key = manifest feature ID + one of its `parameters`)
  flags   `default_enabled` in docs/feature-manifest.json, and the C++ flag default marked
              { EFeatureId::UMB_02, false },   // bake: UMB-02.enabled
          A flag may differ from its manifest default only when the record is implementation_authorized.
  stamp   pipeline/qa/baked.json: preset ID, export hash, every baked value. The check reads it.

Workbench config export (card 0.26 writes it; Saved/Workbench/config-<preset>.json):
  {"kind": "workbench_config", "preset": "T-03", "commit": "<sha>", "manifest_version": "B1.0-m1",
   "flags": {"UMB-03": true}, "params": {"CORE-01.move_speed": 640.0, "UMB-03.catch_window": 0.25}}
  The export lists every marked key in Source/ (a value left out would ship unreviewed).

Commands:
  bake EXPORT [--dry-run]       validate, write the values and the stamp, print the diff (--dry-run: diff only)
  check [--record FILE | --preset T-nn] [--complete]
                                every stamped value equals its marked default in Source/ and its flag default,
                                the manifest version is the stamped one, and (with --record) the gate record's
                                `Baked preset: T-nn` line names the stamped preset. A marked key not in the stamp
                                yet (a feature coded after the bake) passes the `defaults` rules instead; it is
                                listed, not failed (final-7 dry run A H4). --record and --complete are the G4 mode:
                                every marked key is in the stamp and every required key has a marker
  marker   every flagged record's `<ID>.enabled` and every approved_parameters key of a built feature has a
           `// bake:` marker (dry run B H4). Required at G4 (check --record / --complete); before that the bake
           and CI list the missing ones, since the first bake (card 0.27, G2) runs before every P0 is coded
  shape    a `.enabled` marker sits on `true` or `false`, never a number; a parameter marker on a number; and the
           literal is the whole initializer (`= 350.f;`, `{ ID, false }`), never part of an expression such as
           `2 * 350.f` (final-7 dry run B H3, M2)
  ini      no `Config/**/*.ini` section names a config class that holds `// bake:` defaults (`UmbrellaTuning`, or any
           `UCLASS(Config...)` in a header with a marker): an ini line would override the shipped default at runtime,
           so the C++ default stays the one source of shipped values (defaults and check; final-7 dry run B H5)
  branch   a `// bake:` marker never sits inside a preprocessor conditional (`#if`, `#ifdef`, `#ifndef`, `#elif`,
           `#else`): the build that ships compiles one branch, and the checks read every line, so a marked
           value under `#if UMBRELLAELLA_WORKBENCH` with another value under `#else` shipped unchecked (final-8 B C1)
  one-src  the marked line is the only write of a baked member: no `.cpp`, `.h` or `.inl` under Source/ or Plugins/
           assigns it (`=`, `+=`, `*=`, ...) or sets it in a constructor initializer list (only the true branch of
           exactly `#if UMBRELLAELLA_WORKBENCH`, compiled out of the submission, may write a per-run copy), no
           other line sets a marked flag token to a literal, and no ini line names it
           or a Config UPROPERTY whose type is a struct holding a marker (final-8 B H2, H3). Final-10 B H3: no
           GetMutableDefault or const_cast of the tuning class, and no non-const copy of a marked struct (member,
           local, pointer) outside the UUmbrellaTuning class and Private/Tests/: gameplay reads the class default
           at the point of use, the object the hook reads at start and end of run
  defaults                      before the first bake: every `// bake:` default in Source/ passes the safety
                                rules below, each flag equals its manifest default_enabled, and each value the
                                sims read equals feel.json / encounter.json (CI runs it until baked.json exists;
                                dry run B M4, final-7 dry run B H3, H4)
  validate EXPORT [--shape-only]  the export's shape (and, without --shape-only, its IDs against the manifest)
  effective LOG... [--complete]   the packaged game's SMOKE_EFFECTIVE lines (tools/ue_run.py contract: one at=start,
                                at least one at=end, reflected `<Struct>.<Field>` mapped to keys by the marked line;
                                at the tree of the commit the game was built from, final-10): every live
                                value equals baked.json, else its `// bake:` default, else the manifest / GDD start;
                                every marked key is reported; --complete (G4) every required key. The runtime check
                                behind smoke.sh / smoke.ps1, check_pr and the G4 tie (final-9 B C1, H2, H3). The
                                static rules below stay: they fail before a package exists, and the startup read does
                                not see a write that happens after startup

Safety rules (validate, bake and check; GDD 1.3 sections 5, 5A, 12A):
  tuning  tools/tuning.py: a tunable param (approved min, max, step) sits in range and on the step; a fixed one
          equals its approved start, or (no approved entry, e.g. collider data) the value already in Source/
  off     an unapproved feature's flag is false, whatever the manifest default says (dry run B C1)
  start   a parameter other than its GDD start needs a counted DECIDED (<design owner>) row with `Overrides: <key>`:
          range and step are not an approval (GDD 1.3 line 226: no AI tunes a parameter; final-9 B H1)
  sim     each value the sims read (tuning.SIM_KEYS) equals feel.json / encounter.json: the export at bake time,
          the stamp after it, and the `// bake:` defaults before it (dry run B H4, final-7 dry run B H4)
  p0      an APPROVED_P0 flag may not be off: the shipped game is the full BASE baseline
  preset  the shipped preset is T-01 (BASE)
  A DECIDED row in docs/decisions.md whose text says `Overrides: <IDs>` lifts that rule for those IDs only. A
  DECIDED row that merely names an ID (D-new-p0-signoff, DEC-03) lifts nothing; manifest_check p0-on agrees.

Usage: python3 tools/bake_preset.py bake Saved/Workbench/config-T-01.json
       python3 tools/bake_preset.py check --record g4-record.md
Exit 0 = ok, 1 = problems, 2 = unreadable input.
```

Run in CI by:

- `.github/workflows/pipeline-checks.yml`: Shipped defaults equal the baked preset; before the G4 bake, every C++ default follows the tuning rules

Tests: `tests/test_bake_preset.py`, `tests/test_final10_fixes.py`, `tests/test_final8_fixes.py`, `tests/test_final9_fixes.py`, `tests/test_honest_jam.py`, `tests/test_pipeline_check.py`, `tests/test_plan_checks.py`, `tests/test_ue_scripts.py`

### `tools/tuning.py`

Usage text from the file:

```text
One definition of which tuning values are tunable and which are fixed (dry run B H3, H4). Stdlib only.

tools/bake_preset.py, tools/feel_check.py and tools/encounter_check.py all read this module, so the value the game
ships, the value the feel envelope checks and the value the encounter fairness sim checks follow the same rule.

  tunable  an approved_parameters key (docs/feature-manifest.json; GDD 1.3 printed section 5A ranges) with min, max
           and step: the value sits in min-max and on the step from the start ("use stated step")
  fixed    every other key. An approved_parameters key without a range (every GDD SH1.0 start: its section 9
           tables are blank, D-new-sh10-param-ranges; GDD 1.3 OWL-01.seed, OWL-01.initial_grace_s) must
           equal its start. A key with no approved entry (collider data such as OWL-01.collision_radius, the
           ENGINEERING_PROVISIONAL values) must equal the value already in the source (the bake never changes it;
           a change is a separate approved change, GDD 1.3 sections 7A, 7C)
  flags    an `<ID>.enabled` value is true only for an implementation_authorized APPROVED_P0/P1 (or CONFIRMED)
           record (dry run B C1)

SIM_KEYS maps each bake key to where the sims read it. Once pipeline/qa/baked.json exists, every SIM_KEYS value
in it must equal the sim's value (baked_vs_sim_problems): to ship a new number, change feel.json or encounter.json
in the same PR so the envelope and the fairness sim run on it.

Usage: python3 tools/tuning.py [--root PATH]   prints the baked-vs-sim result (exit 0 = equal or nothing baked)
```

Tests: `tests/test_bake_preset.py`, `tests/test_tuning.py`

### `tools/progression_model.py`

Usage text from the file:

```text
Reference model of the GDD SH1.0 health, progression and retry rules. Stdlib only.

The engine code (Gameplay Dev cards) must agree with this model; tests/test_progression_model.py checks the model
against the numbers docs/feature-manifest.json approved_parameters copies from the GDD. Every number here is read from
the manifest, so a new GDD revision changes the model without editing this file. All of it is adjustable prototype
tuning (GDD SH1.0: "approved starting values for playtesting, not proof of final balance").

  health   FLOW-33 / SURV-05 / SURV-07: 3 ordinary hits per life, 3 lives; incoming damage 1 / 1.25 / 1.5 health
           (former 8 / 10 / 12 divided by 8); defense ranks 0 / 10 / 20 / 30 %; damage overflows into the next life;
           lift = min_lift + (1 - min_lift) x clamp(active / capacity); yellow heals 0.5 + 0.3 x recovery rank,
           active life first, then a spent reserve (one active-life capacity per reserve, a derived default)
  xp       FLOW-15: next level from L costs xp_curve_base + floor((L - 1) / 2); one stat point per level; cap 62
  scaling  FLOW-05 / FLOW-06: completed runs C scale enemy HP, ordinary cadence and count; Final Hour replaces them
  retry    FLOW-07 / FLOW-09 / FLOW-13 / FLOW-20: a level-checkpoint death retry keeps XP and levels; a boss-checkpoint
           retry restores the checkpoint's XP, points and unlocks; every death retry gives exactly 3 current lives and
           a full active life; normal checkpoint passage never heals

Usage: python3 tools/progression_model.py   prints the XP milestones and the run-scaling table
```

Tests: `tests/test_progression_model.py`
