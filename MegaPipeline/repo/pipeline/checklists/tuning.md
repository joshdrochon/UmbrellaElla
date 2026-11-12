# Tuning changes (the D20 values and anything else in `UUmbrellaTuning`, `feel.json` or `encounter.json`)

> GDD SH1.0 note (D-new-gdd-sh10): lines on this page that still describe the GDD 1.3 encounter (one owl bolt, the front shield, the 90 s survival timer, wear stages, the 1.3 QA-01..QA-28 tests) are history. The current design is `docs/gdd/GDD-SH1.0.md` and `docs/feature-manifest.json`, which win; the owning role re-files this page against the SH1.0 Rule IDs on its next card.


Each component's numbers live in its own `F<Comp>Tuning` struct, default values in the header, in that component's lane
(`pipeline/unreal/gameplay-code.md`, Code layout). `UUmbrellaTuning` holds one member per struct; `Config/DefaultGame.ini` holds no tuning lines.
This page is for PRs that change a value.

## Rules
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

## Baking the chosen preset (D-new-workbench-debug)
Testers tune with the workbench sliders in debug and dev builds only. The submitted package has no sliders, so the chosen values become plain defaults:
1. A tester exports the config from the workbench (`Saved/Workbench/config-T-nn.json`). The game design owner approves that preset ID on the tracker.
2. `python3 tools/bake_preset.py bake <export> --dry-run`, then without `--dry-run`. It writes every `// bake:` default, the manifest `default_enabled` of each flag, and `pipeline/qa/baked.json`. It refuses a flag changed from its manifest default on a feature that is not implementation_authorized, an exported value with no marker, a marked default the export leaves out, a flag marker on a number instead of `true`/`false`, and a marked literal inside an expression. The first bake (card 0.27, G2) runs before every P0 is coded: it lists each required key with no marker yet as `not marked yet` and still passes.
3. One rule for the bake and both sims (`tools/tuning.py`): a value with a GDD SH1.0 rule numbers (section 9 ranges blank, D-new-sh10-param-ranges) range may be baked inside it, on its step, and only at its GDD 1.3 start unless a counted DECIDED (Richard) row in `docs/decisions.md` names that key in `Overrides: <key>` (for example `Overrides: CORE-03.max_health`; GDD 1.3 line 226: no AI tunes a parameter). A `%` key is written in percent (`100.0f`), never as a ratio, and the code converts at the point of use; a value with no range (the seed, the 2.0 s grace, collider sizes and other values with no approved entry) is fixed and never changed by a bake. The bake refuses a value that differs from `feel.json` or `encounter.json` (and, once `pipeline/qa/baked.json` exists, `feel_check.py` and `encounter_check.py` E30 fail it too): change the data file in the same PR so the envelope and the fairness sim run on the shipped number. An unapproved feature's flag always bakes off. One PR with the printed diff, rules 2 and 9 above, and the `bake_preset.py check` PASS line (`check_pr.py` asks for it). Until the first bake, CI runs `bake_preset.py defaults` on the `// bake:` defaults in `Source/`: each flag at its manifest default, each value in range and on step, and each value the sims read equal to `feel.json` / `encounter.json`. After it, CI runs `bake_preset.py check`: a stamped default must equal the stamp, and a default coded after the bake (no gameplay card's lane holds `baked.json`) passes those same defaults rules and is listed `not baked yet`.
4. The runtime tie: the packaged game logs `SMOKE_EFFECTIVE` at start and at end of run with every reflected field of the `UUmbrellaTuning` structs (where gameplay reads them) and every flag, and `bake_preset.py effective` (run by `smoke.sh` / `smoke.ps1`, the daily, `check_pr.py` and the G4 gate record on the Windows LAUNCH line) fails any live value that differs from `baked.json`, else its marked default, else the GDD start.
5. The G4 bake: after G3 (feature freeze) the Producer files one bake card (lane: `pipeline/qa/baked.json`, `docs/feature-manifest.json` default_enabled, the `// bake:` lines) that bakes the approved preset again over every coded feature. `bake_preset.py check --complete` exits 0 on it: every marked key is in the stamp and every required key has a marker. The G4 gate record's `Baked preset:` line names the approved preset and pastes `bake_preset.py check --record <record>` (the same complete mode); it fails when the stamp is another preset, any default drifted from it, or any default is not baked. `--gate-record` runs the check itself on the Build commit. `bake_preset` also refuses a value outside its approved range, an APPROVED_P0 flag off, or a preset other than T-01, unless a counted DECIDED row says `Overrides: <ID>` for it (`docs/decisions.md` rules; a row that only names the ID lifts nothing; `manifest_check.py` p0-on reads the same clause).

## Log (one row per change)
| Date | PR | Parameter | Old → new | Motivating result | Expected | Observed | Kept / reverted |
|---|---|---|---|---|---|---|---|
