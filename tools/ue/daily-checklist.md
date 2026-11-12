# Daily build: switches by gate and hand checks (QA and Build, on demand)

`pipeline/roles/qa-build.md` links here. Load it when you run or record the daily build.

## The smoke hook contract
The full contract is the docstring of `tools/ue_run.py` (switches, `SMOKE_OK` fields, `SMOKE_CYCLE` lines).
Card 0.6 builds it. Until a real Development package prints every field, each switch stays [VERIFY].
`daily` lists `real-engine pipeline (N VERIFY tag(s) left)` in `Not checked` while any tag is open.
`python3 tools/ue_run.py verify-tags` prints each one. Card 0.6d (due G3) closes them: each tag is
checked on 5.8.4 and removed, or turned into a decision row. Card 0.6 runs one smoke with
`SMOKE_FORCE_CRASH=1` (passes `-SmokeCrash`; the hook crashes on purpose). It must FAIL with
`new crash folder`. A PASS there means the crash paths are wrong.

Crash roots: `crash-check` exits 2 when none of the watched folders exists. Fix the path
(`SMOKE_CRASH_DIRS`); never treat that run as a pass.

## Steps of `daily` (in order; it stops at the first failure)
| Step | Passes when |
|---|---|
| clean-tree | `git status --porcelain` is empty (or `--allow-dirty`; the record then says `+dirty`) |
| build | the editor target compiles |
| test | the report meets `check_automation_report.py` with `--baseline`, `--test-map` and the 1 s rule-test limit |
| alone | each merged test-map test not yet in `Saved/Logs/pipeline/alone-passed.txt` passes run alone (`ALONE_NEW=0` turns it off) |
| shuffle | the merged test-map tests pass again as one `RunTests A+B+...` list in a random order. The seed is printed (`SHUFFLE_SEED=<n>` replays it). Not run with fewer than 2 merged tests; `SHUFFLE_TESTS=0` turns it off |
| validate | `tools/ue/validate.*` (`-run=DataValidation` [VERIFY]) exits 0 with zero `Error:` lines; warnings are recorded |
| package | cook log has no `Error:`, and `cook warnings: N` is not above the last DAILY line. A rise passes only with `COOK_WARN_DECISION=<id>` naming a row in `docs/decisions.md` |
| smoke | every cooked map meets the contract. GameDefaultMap runs `SMOKE_REPEAT` times (default 1); any crash in any run fails |
| display | each mode that fits the monitor meets the contract plus `res=`, `win=`, `textpx=` (1280x720, 1280x800, 2560x1080 windowed; 1920x1080, 3840x2160 fullscreen) |
| settings | GameDefaultMap smoke with a garbage `GameUserSettings.ini`, then with `SETTINGS_OLD_INI` (the ini from the last gate zip), each reaches `SMOKE_OK`. The real ini is put back. `SETTINGS_INI` overrides the path [VERIFY] |
| client-test | `UmbrellaElla.Flow.TitleToPlayToSurvived` passes in the package, exit code 0, `-abslog` file exists, zero `SMOKE_BAD`/`SMOKE_BAD_BROAD` lines, no new crash folder |
| shipping-alive | only with `SHIPPING_EXE`: first window within `SMOKE_MAX_BOOT_S` (20 s, Windows only), alive at 15 s, closes with exit code 0, no new crash folder. `SHIPPING_REQUIRED=1` fails the step when `SHIPPING_EXE` is unset |
| workbench | the tester package (`package.sh --workbench` / `package.ps1 -Workbench`, target `UmbrellaEllaWorkbench`) into `Packaged-Workbench/` exits 0. Runs only after every step above passed; a failure makes the DAILY line FAIL. Not run while `Source/UmbrellaEllaWorkbench.Target.cs` is missing |

Day-1 bootstrap. It is scoped and ends by itself, like `SMOKE_BOOTSTRAP` in `tools/check_pr.py`:
- Until card 0.5 adds `Source/UmbrellaElla/Private/Tests/Meta/`, the test step runs `--bootstrap` (`-Bootstrap`):
  card 0.3's placeholder is the only test. Listed as `gameplay tests (bootstrap: ...)` in `Not checked`.
- Until card 0.6's smoke hook exists, the smoke step is one alive run (`SMOKE_MODE=alive`: running at 15 s, exit 0,
  no new crash folder), and display and settings do not run. Listed as `smoke contract (bootstrap: ...)`.
- `merge-check` counts these lines. A gate record never does: it needs `smoke=PASS(<n> map(s), repeat 5/5)`.
- `merge-check --require-client` asks for `client-test=PASS` only on commits whose own test map has the Flow row
  (`UmbrellaElla.Flow.TitleToPlayToSurvived`) merged.

Gate records read the DAILY line by step and by `Not checked` entry name (`NOT_CHECKED` in `tools/ue_run.py`):
every gate needs clean-tree, build, test, validate, package, smoke, display and settings = PASS. An entry for a
switch below that is past its gate is a P1 bug, so the record is `Pass with named exceptions` with it under Open
P0/P1. Entries for switches the docs leave off (Shipping smoke, `REF_HOST`, VERIFY tags, skipped display modes,
the old ini) never fail a gate.

Rule tests and world tests: a test marked `(world)` in `pipeline/qa/test-map.md`, or with `.World.` in its
name, has no 1 s limit. The packaged client-test step has no 1 s limit either.

Test files: a test that writes files writes them under `Saved/UmbrellaEllaTests/` and deletes them.
`test.*` removes leftovers from a crashed run before it starts, and fails if any file is left after it.
It also hashes `Saved/SaveGames/**` and `Saved/Config/*/GameUserSettings.ini` before the run and fails on any
change after it (`ue_run.py state-list` / `state-check`).

Reference host: the fps limits count only on the low-spec machine named in `REF_HOST` (open decision).
`daily` lists `reference host` in `Not checked` when `REF_HOST` is unset or differs from this machine.

Short form of one good line:
`SMOKE_OK map=L_Graybox fps=58 worst_ms=24 commit=abc1234 input=ok input_vz=-140 res=1920x1080 win=fullscreen textpx=20`
- `fps` is the 1% low over the 15 s window, not the mean. It must be ≥ 55.
- `worst_ms` is the slowest frame in the window. It must be ≤ 33.
- `input=ok input_vz=<cm/s>`: the hook held `IA_Attack` through Enhanced Input and, within 0.5 s, measured a Z
  velocity below 0 (`input_vz` < 0). GDD 1.3: with nothing held the umbrella is UP_OPEN and rises, so only descent
  proves input. `input=none` passes only on a map listed in `pipeline/qa/no-player-maps.txt`.
- `textpx` is the smallest visible UMG text height in px. It must be ≥ 18 on display runs.
- `load_ms` is the time from map load start to the first gameplay frame. It must be ≤ 10000
  (`SMOKE_MAX_LOAD_MS`). Each `SMOKE_CYCLE` line carries its restart `load_ms` too, held to the same limit.

## Log lines
`smoke-log` fails on any `Error:` line in any Log category and any `Failed to load` line, as well as the
crash patterns. A known harmless line goes in `tools/ue/smoke-allow.txt` as `<decision id> | <regex>`.
The id must be a row in `docs/decisions.md`, or `smoke-log` exits 2 (smoke.sh / smoke.ps1 then exit 1). Crash patterns can never be allowed.

## Switches by gate
Each switch that is off shows up in the DAILY line's `Not checked`. Past its gate, an input, gamepad, client-test or
restart-cycles entry is a P1 bug owned by QA and Build, filed the same day; `REF_HOST` and `SETTINGS_OLD_INI`
are recorded only and never fail a gate.

| Switch | Turn on by | What it adds |
|---|---|---|
| `SMOKE_REQUIRE_INPUT=1` (default) | Day 0 (`=0` only until MVP 2 merges) | `input=ok` on every gameplay map |
| `SMOKE_REQUIRE_GAMEPAD=1` (default) | G1 (`=0` only while the QA-GP row is planned; card 0.6e) | `gamepad=ok`: raw gamepad keys move Ella and hold attack and shield in the package |
| `CLIENT_TESTS=1` | G2 (the title screen is a GDD 1.3 §12A Nov 13 player screen) | `UmbrellaElla.Flow.TitleToPlayToSurvived` inside the package [VERIFY module] |
| `SMOKE_SECTIONS` and `SMOKE_SECTION_MAP` | removed | daily ignores them; the single arena needs no section smoke (D-new-cut5) |
| `SMOKE_RESTART_CYCLES=5` | G3 | 5 die → restart cycles; actor count and health must not drift |
| `SMOKE_REPEAT=5` | before each gate | GameDefaultMap smoked 5 times; any crash fails |
| art checks on the smoke screenshot (always on) | G2: the art bootstrap ends by itself when card 0.10b adds `Content/UmbrellaElla/Art/Anchors/`; until then `Not checked: art checks (no anchor art ...)` and the results print without failing | `art_check.py`, `screen_check.py`, `art_judge.py scene` on each smoke's `-SmokeShot=` screenshot |
| `REF_HOST=<machine name>` | Day 1: the weakest team laptop (D-new-ref-host) | the fps limits are checked on that host |
| `SETTINGS_OLD_INI=<ini from last gate zip>` | G1 | boot with the old settings file |

Display modes bigger than the monitor are skipped and listed as `display WxH <mode> (monitor WxH)`.
`SMOKE_DESKTOP_RES=WxH` overrides the size the OS reports.

## Package at every merge
Before each gate, run `python3 tools/ue_run.py merge-check --since <last gate tag>`. Each first-parent
commit on `main` needs a DAILY line with `package=PASS`, `smoke=PASS` and no step `=FAIL`. From G2 add
`--require-client`, so `client-test=PASS` is needed too. A dirty run (`+dirty`) never counts.
Paste the summary line in the gate record. Who runs `daily` after each merge is an open decision
(proposed default: QA and Build, within 1 h of each merge to `main`; done when `merge-check` exits 0 at each gate).

## Before each gate (commands)
- Fresh clone: empty folder, `git clone`, `git lfs pull`, build and package from it.
- Each test alone: `for t in $(python3 tools/check_automation_report.py --list-test-map pipeline/qa/test-map.md); do TEST_FILTER=$t tools/ue/test.sh --require $t || echo "ALONE FAIL $t"; done` (`test.ps1 -Filter <name>` on Windows).
- Repeat boots: `SMOKE_REPEAT=5` in the daily run; the gate record pastes that whole `DAILY <sha> | ...` line (the Build commit).
- `python3 tools/ue_run.py playthrough-check --commit <sha> --gate G<n>` (line below; `--gate-record` needs the `G<n>:` output). `shipping-check` is optional: no Shipping run is required (D-new-ship-required).

## Hand-check record lines
Append to `Saved/Logs/pipeline/daily-records.txt` and post with the record. A blank field is not a pass.
`PLAYTHROUGH <sha> | <one field per phase preset in encounter.json, none for the GDD 1.3 base phase> | survived pass|fail | fail-retry pass|fail | fail-bottom pass|fail | quit-play pass|fail | quit-title pass|fail | quit-pause pass|fail`
Each phase is played through in order, never skipped with a debug jump. Quit means exit code 0, no new crash folder. `quit-play` (due from G1): from play, an in-game quit (key or button) closes the game; Alt+F4 or Task Manager is a fail.
`SHIPPING <sha> | boot_s=<seconds from launch to the title screen> | quit rc=<exit code>`
Shipping zip on a machine or user profile that never had the editor. `shipping-check` passes at `boot_s` ≤ 20 and `rc=0`.

## Hand checks from G3 (one record line each)
Append the line to `Saved/Logs/pipeline/daily-records.txt` and post it with the record:
`STRESS <sha> | pause-restart pass|fail | pause-quit pass|fail | hold-alt-tab pass|fail | two-runs pass|fail |
audio-switch pass|fail (<n> s) | gamepad pass|fail|not merged`
`python3 tools/ue_run.py stress-check --commit <sha>` passes only when the line exists, every field is pass
(gamepad may be `not merged`), and audio resumed in ≤ 2 s.
- pause → restart and pause → quit mid-level.
- Hold the umbrella, pause or alt-tab, release, resume. The umbrella must be closed.
- Two full runs without relaunching.
- Switch the Windows default audio device mid-level. Audio continues within 2 s.
- If the gamepad stretch merged: unplug mid-level, the game pauses; replug, resume with no stuck input.
- Audio voices, on the packaged run: at the 90% timer mark, run the voice-count command in `pipeline/audio/audio-rules.md` section 4 and note active voices twice, 10 s apart. Then `python3 tools/audio_check.py --log <log>`. Fail if over 24 or rising.
A blank field is not a pass. Any stuck state is P1.

## Display before each gate
`HighResShot` of title, HUD, pause and lose at 720p and 4K, attached to the record. Alt+Enter to fullscreen and
back mid-level with no cut-off or stretched UI.
