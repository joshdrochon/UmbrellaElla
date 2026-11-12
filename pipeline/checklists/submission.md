# Submission checklist (G4, owner: packaging and submission owner in `docs/jam-brief.md`)

> GDD SH1.0 note (D-new-gdd-sh10): lines on this page that still describe the GDD 1.3 encounter (one owl bolt, the front shield, the 90 s survival timer, wear stages, the 1.3 QA-01..QA-28 tests) are history. The current design is `docs/gdd/GDD-SH1.0.md` and `docs/feature-manifest.json`, which win; the owning role re-files this page against the SH1.0 Rule IDs on its next card.


Jam rules and their quotes: `docs/jam-rules.md`. QA and Build runs it. The packaging owner ticks it.
Tests for the checks: `python3 -m unittest tests.test_submission_check` (pytest is not installed; every suite runs in the pipeline repos' CI).
Each line needs pasted output or a link. A line that was not run says "not run" and why. Not run is never a pass.
The submitted build is a **Windows Development package** (jam rule). A Shipping package is optional and never submitted.

## Before G4: the in-jam inputs (each fails G4 if skipped; none can be made up on Nov 15)
| Input | Owner | Done when | Check |
|---|---|---|---|
| Theme | Game design owner (card 0.19) | By 2026-11-11T13:00-08:00, `Theme: "<kickoff quote>"` and `Theme in game: <one line>` in `docs/jam-brief.md` | `submission_check.py theme` |
| Capture switch | Gameplay Dev (card 0.6c, requested) | By G1: `-CaptureMode` on a Development package logs `CAPTURE_MODE hud=off debug=off cursor=off`, `submission_check.py capture <log>` exits 0 (pasted), and a pasted 1920x1080 capture shows no debug text and no cursor (the diegetic health indicator stays, D37) [VERIFY: needs Unreal] | `submission_check.py capture` |
| Devlog | Producer (human) | Each day's end: 3 linked obstacle lines in `pipeline/submission/devlog.md` | `submission_check.py devlog --day N` |
| Footage | Asset Specialist | From Day 2: 2 or more `-CaptureMode` clips a day logged in `pipeline/submission/footage.md` | `submission_check.py footage --day N` |
| Rules PDF | Human (card 0.2) | The Official Rules PDF is in `docs/rules/` and pinned; `docs/jam-rules.md` cites its sections with no [VERIFY] left; Rick confirms the quotes against the PDF and D14 cites the AI row, before Day 1 | `submission_check.py rules`, `manifest_check.py` (rules-pin) |
| Wiring | Producer | Before Day 1: each duty above has a card or role-card line, `check_card.py` runs the daily and butler checks, and `package.ps1` copies README.txt and LICENSE.txt | `submission_check.py wiring` |
| README and LICENSE text | Packaging owner | From Day 0 `files` exits 0; at G4 `files --final` exits 0 (no TBD) | `submission_check.py files` |
| butler | Packaging owner | By G1: the G1 gate record has `BUTLER version=<v> login=ok user=<itch-user> by=<name>` from the packaging machine | `submission_check.py butler "<line>"` |
| Video cut | Asset Specialist (card 0.24, G3 to G4) | Video checks below exit 0, pasted in the G4 gate record | `submission_check.py video`, `loudness`, `signoff` |
| Early jam submission | Packaging owner (Team Owner, human) | By G2, only if D-new-upload is DECIDED for it: the Draft project is submitted once, the team form is filled, and the submission URL is in the G2 gate record. Official Rules §2: one Submission per team, never a second entry | Gate record |
`submission_check.py daily --day N` runs the devlog, footage and theme checks together. The Producer runs it at each day start for the day just ended (N-1) and pastes it on the status line.
Once `check_card.py --status` calls `submission_check.status_hook()` (requested; `wiring` shows it), the hand run is no longer needed.

## The build
- [ ] `main` is tagged `submit-<sha>`. The working tree was clean (`git status --short` empty) when it was packaged.
- [ ] The packaging owner (a person, not a card session) runs the full unit suite on that tag:
      `python3 -m unittest discover -s tests` exits 0 before packaging (the `Ran N tests` line pasted). Card sessions and game-repo CI never run it.
- [ ] Development package from a fresh clone of that tag: empty folder, `git clone`, `git lfs pull`, then `tools\ue\package.ps1`.
      Cook log has no `Error:`. `cook warnings: N` pasted; not above the last `DAILY` line unless a decision row accepts it. A missing file is P0.
- [ ] Workbench compiled out (D-new-workbench-debug): `package.ps1` ran without `-Workbench` and printed `workbench-check: PASS`; BUILD_INFO.txt says `workbench=0` (the `zip` check fails otherwise); the smoke's `SMOKE_OK` line says `workbench=0` and the log has no `WORKBENCH_ON`, `LogWorkbench` or `TestPresetLoaded` line (`smoke.ps1` checks both from BUILD_INFO).
- [ ] Shipped defaults are the approved preset: `python3 tools/bake_preset.py check --record <G4 record>` exits 0, pasted on the G4 `Baked preset:` line.
- [ ] README.txt (title, controls, team, credits from `pipeline/submission/credits.md`) and LICENSE.txt sit next to the game exe. `package.ps1` copies them from `pipeline/submission/`; `python3 tools/submission_check.py files --final` exits 0, output pasted.
- [ ] Zip named `<TeamName>_<GameName>.zip`. `python3 tools/submission_check.py zip <zip> --team <TeamName> --game <GameName> --commit <sha>` exits 0, output pasted
      (Development, Win64, cooked only, no Saved/, under 1,000,000,000 bytes, README/LICENSE/BUILD_INFO next to the exe; it prints the SHA256).
- [ ] Smoke: `$env:SMOKE_REPEAT=5; tools\ue\daily.ps1` on the same tag on the packaging machine at 1920x1080, `DAILY` line pasted with clean-tree, build, test, validate, package, smoke, display, settings and client-test PASS (Shipping, alone and shuffle may be NOT RUN)
      (a `SMOKE_OK` line that meets the contract in `tools/ue_run.py`, exit code 0, zero `SMOKE_BAD` and `SMOKE_BAD_BROAD` lines, no new `Saved/Crashes` folder).
- [ ] Clean-profile launch: the zip, unpacked on a machine or Windows user that never had the editor, starts, plays and quits with exit code 0. No new crash folder.
- [ ] Playthrough on the zip by a human, pasted as the `PLAYTHROUGH` line in `tools/ue/daily-checklist.md`
      (Survived, a health fail and retry, a bottom-exit fail, both quits; GDD 1.3 has one base phase, so no phase presets);
      `python3 tools/ue_run.py playthrough-check --commit <sha> --gate G4` passes.
- [ ] Zero open P0 or P1 bugs (`qa-build.md`). Every open P2/P3 is in the known-limitations list below.

## The record (post on the Jam tracker)
```
Submission: tag | commit | zip name | zip SHA256 | config Development | platform Win64
MVP: pass/fail each, with the build record or test that shows it
Playtests P1-P12: pass | fail | insufficient | untested, each with its results-log row
Known limitations: <one line each, with issue link>
Not checked: <list, or "none">
```

## Content and rules
- [ ] `python3 tools/submission_check.py credits` exits 0 (every CC-BY, OFL, Fab and third-party row and every font is credited).
- [ ] `python3 tools/pipeline_check.py --release` exits 0 (no `_PH` asset left), unless the scope decision-maker accepted one in writing (a scope call).
- [ ] Pre-jam declaration: `python3 tools/submission_check.py declaration --ref jam-start` and `python3 tools/submission_check.py prejam` exit 0.
      The paste text from `docs/pre-jam-declaration.md` is on the submission.
- [ ] AI disclosure on the page: the default line in `pipeline/submission/itch-page.md` (Official Rules §7(a), §9; `docs/jam-rules.md` row AI).
- [ ] Pre-jam assets (§7(h)): `python3 tools/submission_check.py assets` exits 0. Every sourced asset is in `credits.md` "Sourced assets" and noted on the submission (§1(d)).
- [ ] English (§7(i)): `python3 tools/submission_check.py english` exits 0, and the human who signs the video confirms every voice line, sound with words, and in-game text is English.
- [ ] Content sign-off by a human, pasted as `CONTENT teen=yes trademarks=ue-logo-only original=yes extra-software=none english=yes by=<name>` (`submission_check.py signoff "<line>"` exits 0): teen-appropriate (§8), no trademarks or logos except the Unreal Engine logo per https://www.unrealengine.com/branding (§15(d)), not a tutorial or starter-template extension (§7(d), §7(e)), and the zip runs on a clean Windows 10 or 11 machine with no extra software (§1(b), §7(f)).
- [ ] Theme: `submission_check.py theme` exits 0, and the theme is visible on the title or end card. Screenshot of it attached, from the zip.
- [ ] No pipeline text in shipped content: no `ROLE:`, role names, or agent notes in UI strings, credits or README.

## Video, devlog and page
- [ ] Video (`pipeline/submission/video-plan.md`): `submission_check.py video <file>` and `submission_check.py loudness <file>` exit 0,
      `submission_check.py signoff "<VIDEO line>"` exits 0 on the pasted human line (music and SFX beats heard),
      and `submission_check.py footage --day 4 --final` exits 0. Link on the submission.
- [ ] Game audio: `submission_check.py loudness <capture>` on a 30 s capture from the zip exits 0, or the gap is in Known limitations.
- [ ] Devlog (Glass Box, owner Producer): `submission_check.py devlog --day 4 --published` exits 0. The link is on the submission, before the deadline (Official Rules §10: submitted together with the Submission during the Contest Period), and opens logged out. `prompt_log.py export --check --day D` passed for every jam day from Nov 12.
- [ ] Page (`pipeline/submission/itch-page.md`): `submission_check.py page` exits 0. Controls follow rows DEC-02 (firing) and DEC-01 (keys) in `docs/decisions.md` once both are DECIDED; `page` fails while either is open.
      `page` also fails on a TBD or `n` in the Team table, and on a missing role or member in Credits by role.
      The human previews the Draft page, then makes it public.
- [ ] Team name, every member's full name and Epic account email, and the Team Owner entered on the jam form (Official Rules §1(a), §1(c)). Team of 1 to 5.

## Upload
Needs-human checkpoint: the Team Owner (or the packaging and submission owner, a human entrant) runs every upload and the jam form. Official Rules §17: never an AI agent; `hook.py` blocks `butler push` and `butler login` for agents.
- [ ] The G1 gate record has the BUTLER line, and `submission_check.py butler "<line>"` exits 0. Upload with `butler push <zip> <itch-user>/<game>:windows-dev`, never from a practice repo (`.pipeline-practice`: `tools/practice.py` blocks the submission checks and G4 there).
- [ ] The uploaded zip's SHA256 equals the one in the record above. Any later commit needs a new record first.
- [ ] Files lock at the deadline (`docs/jam-rules.md` rule 10). The G4 zip is final; after the deadline only page text and images change; the devlog was submitted with the entry (§10). No zip goes up after the deadline.
- [ ] Upload verified by downloading it again from the team's itch page and playing it once to the "Survived" card or a death, by a human.
- [ ] Final upload at least 3 h before the deadline: `python3 tools/check_card.py --clock --uploaded <jam-page time>` exits 0.
- [ ] Fallback ready: every gate zip is kept as `G<n>-<sha>/<TeamName>_<GameName>.zip` (no rename needed), and `submission_check.py zip <that path> --team <T> --game <G> --gate G<n>` exited 0 at that gate (its `Gate checks` line). The newest one's SHA256 is in the record.

## Optional (only if time is left after every line above)
- Shipping package, launched once by hand on a clean machine. Never submitted.
- Display check at 1280x720 windowed and 3840x2160 fullscreen; `HighResShot` of title, HUD, pause and end card.
- `python3 tools/ue_run.py stress-check --commit submit-<sha>`. (Repeat boots, `SMOKE_REPEAT=5`, are required at every gate: the record pastes that DAILY line.)
