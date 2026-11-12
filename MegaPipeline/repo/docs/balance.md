# Balance (owned by the Game Designer role; values decided by the human game design owner)

Combat balancing is the Game Designer's job, with the Level Designer's encounter data (`pipeline/level/encounter.json`).
All targets are proposed until the game design owner accepts them. Measured numbers are pasted from command output
with the commit they came from. GDD SH1.0 rule numbers (section 9 ranges blank, D-new-sh10-param-ranges) gives Richard's approved provisional numbers (90 s, one bolt, 100 HP,
34 damage, heal 20 with a 2 s cooldown, 0.8 s invulnerability). They are not balanced values; a change goes through the GDD and the manifest.

## Targets per phase
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

## Movement envelope (measured by `UmbrellaElla.Move.World.FeelEnvelope`, card 0.13; paste output + commit)
| Measure | Value | Commit |
|---|---|---|
| Sideways accel frames, 0 to 350 cm/s (`accel_f`) | not measured | |
| Max fall cm/s (one gravity rule; no multiplier, no fast fall, GDD SH1.0 rule numbers (section 9 ranges blank, D-new-sh10-param-ranges)) | not measured | |
| UP_OPEN rise cm/s, full / lowest health (equal: no lift loss, DEC-05) | not measured | |
| State blend frames | not measured | |
Targets: GDD SH1.0 rule numbers (section 9 ranges blank, D-new-sh10-param-ranges) (manifest `approved_parameters`), copied in `docs/feel-spec.md` section 7. `encounter_check.py` reads hero
speeds from the tuning file, so the safe-path check (E13), and the recovery check (E25, only with SURV-04 on), use them.
Every Commit cell must be the last `*Tuning.h` commit or newer.

## Change history
See the log in `pipeline/checklists/tuning.md`.
