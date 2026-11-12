> Generated from `pipeline/checklists/submission.md`, `docs/pre-jam-declaration.md`, `pipeline/submission/LICENSE.txt`, `pipeline/submission/README.txt`, `pipeline/submission/credits.md`, `pipeline/submission/devlog.md`, `pipeline/submission/footage.md`, `pipeline/submission/itch-page.md`, `pipeline/submission/video-plan.md`, `tools/submission_check.py` at `a11903f` — edit the sources, not this file.
> Rebuild: `python3 tools/export_package.py`. Check: `python3 tools/export_package.py --check`.

# Submission Pipeline

A readable copy for people. Agents load these rules from the repo paths listed below.

## About this pipeline

- **Purpose:** Ship a clean build, page, video, credits and declaration on time.
- **Owner:** Packaging and submission owner (human) with QA and Build.
- **Inputs:** The packaged build, footage log, provenance rows, jam rules.
- **Outputs:** The submission zip, itch page, video, devlog, credits, README and licence files.
- **Gates:** G4 submission checklist; `submission_check.py` for zip, credits, footage and gate records.

## Built from

- Checklist and declaration: `pipeline/checklists/submission.md`, `docs/pre-jam-declaration.md`
- Submission files: `pipeline/submission/LICENSE.txt`, `pipeline/submission/README.txt`, `pipeline/submission/credits.md`, `pipeline/submission/devlog.md`, `pipeline/submission/footage.md`, `pipeline/submission/itch-page.md`, `pipeline/submission/video-plan.md`
- Commands and checks: `tools/submission_check.py`

## Checklist and declaration

### `pipeline/checklists/submission.md`

#### Submission checklist (G4, owner: packaging and submission owner in `docs/jam-brief.md`)

> GDD SH1.0 note (D-new-gdd-sh10): lines on this page that still describe the GDD 1.3 encounter (one owl bolt, the front shield, the 90 s survival timer, wear stages, the 1.3 QA-01..QA-28 tests) are history. The current design is `docs/gdd/GDD-SH1.0.md` and `docs/feature-manifest.json`, which win; the owning role re-files this page against the SH1.0 Rule IDs on its next card.


Jam rules and their quotes: `docs/jam-rules.md`. QA and Build runs it. The packaging owner ticks it.
Tests for the checks: `python3 -m unittest tests.test_submission_check` (pytest is not installed; `python3 -m unittest discover tests` runs every suite).
Each line needs pasted output or a link. A line that was not run says "not run" and why. Not run is never a pass.
The submitted build is a **Windows Development package** (jam rule). A Shipping package is optional and never submitted.

##### Before G4: the in-jam inputs (each fails G4 if skipped; none can be made up on Nov 15)
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

##### The build
- [ ] `main` is tagged `submit-<sha>`. The working tree was clean (`git status --short` empty) when it was packaged.
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

##### The record (post on the Jam tracker)
```
Submission: tag | commit | zip name | zip SHA256 | config Development | platform Win64
MVP: pass/fail each, with the build record or test that shows it
Playtests P1-P12: pass | fail | insufficient | untested, each with its results-log row
Known limitations: <one line each, with issue link>
Not checked: <list, or "none">
```

##### Content and rules
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

##### Video, devlog and page
- [ ] Video (`pipeline/submission/video-plan.md`): `submission_check.py video <file>` and `submission_check.py loudness <file>` exit 0,
      `submission_check.py signoff "<VIDEO line>"` exits 0 on the pasted human line (music and SFX beats heard),
      and `submission_check.py footage --day 4 --final` exits 0. Link on the submission.
- [ ] Game audio: `submission_check.py loudness <capture>` on a 30 s capture from the zip exits 0, or the gap is in Known limitations.
- [ ] Devlog (Glass Box, owner Producer): `submission_check.py devlog --day 4 --published` exits 0. The link is on the submission, before the deadline (Official Rules §10: submitted together with the Submission during the Contest Period), and opens logged out. `prompt_log.py export --check --day D` passed for every jam day from Nov 12.
- [ ] Page (`pipeline/submission/itch-page.md`): `submission_check.py page` exits 0. Controls follow rows DEC-02 (firing) and DEC-01 (keys) in `docs/decisions.md` once both are DECIDED; `page` fails while either is open.
      `page` also fails on a TBD or `n` in the Team table, and on a missing role or member in Credits by role.
      The human previews the Draft page, then makes it public.
- [ ] Team name, every member's full name and Epic account email, and the Team Owner entered on the jam form (Official Rules §1(a), §1(c)). Team of 1 to 5.

##### Upload
Needs-human checkpoint: the Team Owner (or the packaging and submission owner, a human entrant) runs every upload and the jam form. Official Rules §17: never an AI agent; `hook.py` blocks `butler push` and `butler login` for agents.
- [ ] The G1 gate record has the BUTLER line, and `submission_check.py butler "<line>"` exits 0. Upload with `butler push <zip> <itch-user>/<game>:windows-dev`, never from a practice repo (`.pipeline-practice`: `tools/practice.py` blocks the submission checks and G4 there).
- [ ] The uploaded zip's SHA256 equals the one in the record above. Any later commit needs a new record first.
- [ ] Files lock at the deadline (`docs/jam-rules.md` rule 10). The G4 zip is final; after the deadline only page text and images change; the devlog was submitted with the entry (§10). No zip goes up after the deadline.
- [ ] Upload verified by downloading it again from the team's itch page and playing it once to the "Survived" card or a death, by a human.
- [ ] Final upload at least 3 h before the deadline: `python3 tools/check_card.py --clock --uploaded <jam-page time>` exits 0.
- [ ] Fallback ready: every gate zip is kept as `G<n>-<sha>/<TeamName>_<GameName>.zip` (no rename needed), and `submission_check.py zip <that path> --team <T> --game <G> --gate G<n>` exited 0 at that gate (its `Gate checks` line). The newest one's SHA256 is in the record.

##### Optional (only if time is left after every line above)
- Shipping package, launched once by hand on a clean machine. Never submitted.
- Display check at 1280x720 windowed and 3840x2160 fullscreen; `HighResShot` of title, HUD, pause and end card.
- `python3 tools/ue_run.py stress-check --commit submit-<sha>`. (Repeat boots, `SMOKE_REPEAT=5`, are required at every gate: the record pastes that DAILY line.)

### `docs/pre-jam-declaration.md`

#### Pre-jam declaration

The jam says: "Declare any prompts, scripts, or assets you made before the jam."
Official Rules §7(h) (`docs/jam-rules.md`): only "AI tools, agent configurations, Model Context Protocol ("MCP") settings, prompt libraries, and scripts" may be prepared before the Contest Period; the Sponsor may ask for them or for version-control history, so this repo's history is kept. Pre-jam art (key art, style frames) is reference only and never shipped (`submission_check.py assets`).
Everything below existed before the build window opened (2026-11-11T21:00-08:00: Nov 11 21:00 PST = Nov 12 00:00 EST).
The text under "Paste into the submission" goes on the jam submission as is. The tables are the full list.

Checks:
- `python3 tools/submission_check.py declaration --ref jam-start` exits 0: every file in the repo at the `jam-start` tag matches a row below.
- `python3 tools/submission_check.py prejam` exits 0: every commit that touched `Source/`, `Content/`, `Config/` or a `.uproject` before the start is listed by short SHA under "Game files made before the jam".

Owner: Producer (human). Done when both checks exit 0 on the `jam-start` tag and the paste text is on the submission.
kickoff tags `jam-start` on `main` when card 0.3 starts, on or after the jam start (`tools/kickoff.py` ensure_jam_start).

##### Paste into the submission
> Before the jam we built an agent pipeline and no game content. It is: process rules and role prompts for AI agents
> (AGENTS.md, pipeline/roles), checklists and templates, Python and PowerShell check scripts (tools/), a reviewer
> evaluation set of small C++ snippets (evals/), unit tests for those scripts (tests/), and a planning design document.
> Pre-existing tools we drive from that pipeline: a teammate's GimpCLI (GIMP automation) and Rick's Aseprite MCP server,
> plus the asset scripts that call Blender, ElevenLabs, Stable Audio, GIMP, Aseprite, ffmpeg, SoX, OBS
> and 7-Zip (tools/assetgen.py; MCP settings in pipeline/agent-ops/).
> One reference image was made before the jam and is used only as a style target, never shipped.
> [If filled: list each row of "Game files made before the jam" and "Assets made or picked before the jam".]
> All game code, maps, art and audio in the build were made from the jam start (Nov 11 21:00 PST, Nov 12 00:00 EST) on, except the items listed above.

##### Tools, prompts and scripts
| Pattern | What it is | Made by |
|---|---|---|
| `AGENTS.md`, `CLAUDE.md`, `README.md`, `START_HERE.md` | Agent process rules, repo readme and the first-run guide (prompts) | Team + AI agents |
| `.claude/agents/*` | Agent entry prompts that point at the role cards | Team + AI agents |
| `pipeline/roles/*` | Role cards: the role prompts for each agent | Team + AI agents |
| `pipeline/*.md`, `pipeline/VERSION`, `pipeline/checklists/*`, `pipeline/templates/*`, `pipeline/qa/*` | Rules, checklists, card and record templates, the pipeline version string | Team + AI agents |
| `pipeline/submission/*` | Submission plans: devlog skeleton, video plan, itch page plan, credits; README.txt and LICENSE.txt templates shipped next to the exe (filled in during the jam) | Team + AI agents |
| `pipeline/story/*` | Story bible (design notes from the team's #story channel and the GDD, all PROPOSED until the game design owner confirms), the text rules, and the empty text-line sheet (lines are written from the jam start) | Team + AI agents |
| `pipeline/art/*.md`, `pipeline/art/*.json`, `pipeline/art/*.csv` | Art bible, import rules, palette numbers, provenance log | Team + AI agents |
| `pipeline/art/blender/*` | Blender scripts and stand-in recipes the agents render the game's art with during the jam (no art in them) | Team + AI agents |
| `tools/*`, `tools/ue/*` | Check and build scripts (Python, PowerShell, shell); the art judge prompt | Team + AI agents |
| `tests/*`, `tests/fixtures/*` | Unit tests and test inputs for the scripts | Team + AI agents |
| `evals/*` | Reviewer evaluation cases (small planted-bug C++ snippets) and the art judge set | Team + AI agents |
| `.github/*` | Issue forms, PR template, CI workflow | Team + AI agents |
| `docs/*` | Planning docs: jam brief, decisions, design drafts, references, rules | Team + AI agents |
| `.editorconfig`, `.gitattributes`, `.gitignore`, `.pipeline-installed.json` | Repo settings; the pipeline install record (`MegaPipeline/install.py`) | Team |
| `.pipeline-ci-full` | CI profile marker: the long pipeline suites run (pipeline repos only, never shipped) | Team |
| `MegaPipeline/*` | Readable copy of the pipeline docs for people, generated by `tools/export_package.py` | Team + AI agents |
| `pipeline/agent-ops/*`, `prompts/*` | Agent settings template, hooks, gate data, MCP component list, prompt-log readme | Team + AI agents |
| `Samples/Workbench/*` | The generic tester workbench sample (cards 0.25, 0.26): a separate test project on synthetic objects (moving boxes, a spawner, a damage volume), with flags, reset, logging, presets, seeds, scenarios and debug toggles; no umbrella, owl or other game content (GDD SH1.0 ART-03 and section 11; Official Rules §7(h) tools and scripts). Its code is ported into the game from the jam start (card 0.27) | Team + AI agents |
| `pipeline/audio/*`, `pipeline/feel/*`, `pipeline/level/*`, `pipeline/ui/*` | Design data drafts from the GDD: sound list, feel numbers, owl encounter tables, UI signals, empty logs. The game's data assets are made from them on Nov 12 or later | Team + AI agents |

##### Pre-built tools (Official Rules §7(h): AI tools, agent configurations, MCP settings, prompts, scripts)
Every tool from issue #13 that the pipeline drives; licences in `pipeline/agent-ops/asset-tools.json`. The ones we made
or that a teammate made before the jam are declared here; vendor tools are listed so the Sponsor sees the whole chain.
| Tool | What it is | Made by |
|---|---|---|
| GimpCLI | GIMP automation CLI used by `tools/assetgen.py clean` (pre-existing, made before the jam) | A teammate |
| Aseprite MCP | MCP server for Aseprite (pre-existing, made before the jam) | Rick |
| `tools/assetgen.py`, `tools/kickoff.py`, `tools/connections.py`, `tools/mcp_config.py`, `tools/keys.py`, `tools/git_gate.py`, `tools/practice.py` | Pipeline scripts: asset steps, the one-command loop, connection check, MCP config, keys, git gate | Team + AI agents |
| `pipeline/agent-ops/asset-tools.json`, `pipeline/agent-ops/mcp.tools.template.json`, `pipeline/agent-ops/codex-mcp.template.toml` | Tool inventory and MCP settings for Claude Code and Codex | Team + AI agents |
| Blender (all game art is rendered in it), ElevenLabs, Stable Audio 3, GIMP 3, Aseprite, Paper2D, PaperZD (conditional), ffmpeg, SoX, OBS + obs-websocket, 7-Zip, butler, Fab, Audacity and Clipchamp (human fallbacks) | Vendor tools and services, unchanged; every asset they make gets a provenance row in `pipeline/art/provenance.csv` during the jam | Vendors |

##### Assets made or picked before the jam
| Pattern | What it is | Shipped? |
|---|---|---|
| `pipeline/art/reference/*` | Target key art: a style reference for judging captures | No, reference only |
| `pipeline/art/fallback/*`, `pipeline/art/fallback-cc0.csv` | Fallback CC0 art and audio set, if card 0.15 runs before Nov 12: owl, bolt, gust telegraph and 3 umbrella-tier sprites; projectile launch, hit, gust windup, umbrella state change and owl-departure sounds (GDD §8) (each file credited in `pipeline/submission/credits.md`) | Only if used |

Supplied sound effects a teammate made before the jam (`tools/audio_import.py`, `pipeline/audio/style-target.md` section 7) are declared, not blocked: `apply` with a `--made` date before the start adds one row per take to the table above and to `pipeline/submission/credits.md` Sourced assets (Official Rules 7(h); sourced assets are noted on the submission and not scored).

##### Game files made before the jam
Every commit before the start that touched `Source/`, `Content/`, `Config/` or a `.uproject`, one row per commit.
Empty: no game files before the jam start (D39). If D39 is decided the other way, each such commit goes here.
| Commit | Card | What it holds |
|---|---|---|

## Submission files

### `pipeline/submission/LICENSE.txt`

```text
Copyright 2026 TBD (team name). All rights reserved.

You may download and play this game for free. You may not sell it or redistribute changed copies.

Third-party assets in this game keep their own licences. Each one is listed under Credits in README.txt.
```

### `pipeline/submission/README.txt`

```text
Title: TBD (same as the Title field in itch-page.md)
TBD (one line: survive the clockwork owl's last hour with a fragile umbrella)

How to run
Unzip the folder and run the game exe next to this file. Windows 64-bit.

Controls
TBD (copied from docs/jam-brief.md once the controls row in docs/decisions.md is DECIDED)
Esc or P: pause

Team
TBD (team name, then one line per member: name and role, from the Team table in itch-page.md)

Credits
TBD (third-party assets from credits.md, each with its licence)
Made with Unreal Engine. Code, art and audio made with AI tools; see the devlog.

Theme
TBD (the Theme line in docs/jam-brief.md)
```

### `pipeline/submission/credits.md`

#### Credits: third-party assets, fonts and licences

Every row in `pipeline/art/provenance.csv` whose licence or origin is CC-BY, OFL, Fab or third-party has a row here with its exact path.
Fonts count: a font file, or a font asset under a `Content/**/Fonts/` folder, needs a provenance row.
Check: `python3 tools/submission_check.py credits` exits 0. Owner: Asset Specialist adds the row in the same PR as the asset.
This file is pasted into the itch page credits and copied into the zip's README.txt at G4.

| Asset path | Author | Licence | Source link | Credit text |
|---|---|---|---|---|

##### Sourced assets
Official Rules §1(d) and §15(c): every sourced (non-original) asset is noted upon submission; sourced assets are not
scored, and AI-generated content is not a sourced asset. One row per path under `Content/`, `Art/` or `Audio/` that the
team did not make during the jam. `submission_check.py assets` fails on a pre-jam provenance date not listed here.
| Asset path | Made by | Licence | Why sourced |
|---|---|---|---|

### `pipeline/submission/devlog.md`

#### Devlog: how we built it (Glass Box)

The jam: "Dev log link (optional, but required for the Glass Box modifier)." Glass Box = "Best dev log showing how you built your game."
Judges want to see the agent pipeline at work: real obstacles, with the record that shows them.

Owner: Producer (human). Published as an itch devlog post on the game's page; its link goes on the jam submission.
Check: `python3 tools/submission_check.py devlog --day N` exits 0 at each day's end (N = the day just ended).
Trigger: at each day start the Producer runs `python3 tools/submission_check.py daily --day N-1` and pastes it on the status line.
Wiring `check_card.py --status` to call `submission_check.status_hook()` is requested (Producer's tools lane). Until `submission_check.py wiring` shows it, the hand run is the only trigger.
Done when: `python3 tools/submission_check.py devlog --day 4 --published` exits 0 and the `Published:` link opens logged out.

Rules for the Producer:
- Each day, 3 or more real obstacles under that day. Each line names what broke, what the pipeline did, and links the proof:
  a PR, an issue (`#12`), a gate record (`gate-G1`), or an https link. A line without a link does not count.
- Plain words. No secrets, no personal emails, no local paths, no other projects.
- Show at least one agent mistake a gate caught, and one a gate missed.
- At G4, write the three sections below from the daily lines (3-6 bullets each), add 2 images (a gate record and a game capture), and publish.

Published: TBD

##### Went right

##### Went wrong

##### Change next time

##### Daily obstacles
###### Day 1
###### Day 2
###### Day 3
###### Day 4

### `pipeline/submission/footage.md`

#### Footage log (clips for the video, cover and screenshots)

Owner: Asset Specialist. Rules: `pipeline/submission/video-plan.md`, "Footage capture".
Check: `python3 tools/submission_check.py footage --day N` exits 0 at each day's end. The day-start `submission_check.py daily --day N-1` run covers it (`devlog.md`, Trigger).
Done when: `python3 tools/submission_check.py footage --day 4 --final` exits 0 (2 or more clips a day from Day 2, every beat at least once).

One line per clip, under its day: `- <day>-<beat>-<sha>.mp4`, beat from volley, rise, fall, gust, torn, end.
Only clips from a `-CaptureMode` run count (the run's `CAPTURE_MODE` line passed `submission_check.py capture`).
The clips themselves live in the team's shared footage folder, never in git.

##### Clips
###### Day 1
###### Day 2
###### Day 3
###### Day 4

### `pipeline/submission/itch-page.md`

#### itch page spec

Owner: packaging and submission owner (human). Due: G4. The page stays Draft until that human previews it, then sets it public and submits to the jam.
Done when: `python3 tools/submission_check.py page` exits 0, the preview is done, and the jam submission shows the page.

##### Images (in `pipeline/submission/page/`, Git LFS)
- `cover.png`: at least 630x500, ratio 315:250. Taken from a packaged `-CaptureMode` run (no HUD; `video-plan.md`), cropped to the owl and Ella.
  It must read like the key art (`pipeline/art/reference/target-keyart.png`): sepia parchment, ink silhouettes, the amber chest clock, red bolts.
  The Art Director (human) approves it against the key art.
- `shot-<beat>.png`: 3 to 5 screenshots at 1920x1080 or more from the packaged build, each a different beat from:
  volley, rise, fall, gust, torn, end. No two the same file. All from `-CaptureMode` runs: no HUD, no debug text.
- Gameplay only: no title, menu, pause or end-card screens. `shot-end.png` shows the owl leaving with Ella in flight, no card text.
  The packaging owner checks this by eye; the tool checks only names, sizes and duplicates.

##### Page fields
| Field | Value |
|---|---|
| Title | TBD (the game design owner decides; the GDD's working title is "The Last Hour") |
| Short description | TBD (one line: survive the clockwork owl's last hour with a fragile umbrella) |
| Genre | Action |
| Tags | TBD (up to 10, e.g. boss-fight, umbrella, survival, 2D, unreal-engine) |
| Controls | TBD (the controls in `docs/jam-brief.md` once row DEC-02 in `docs/decisions.md` (attack trigger, GDD SH1.0 section 11 open decisions) is DECIDED; never from a GDD file directly. `submission_check.py page` fails while D1 is open, and while D1 still asks the old falling-attack question instead of automatic fire vs player-fired shot) |
| Theme | TBD (copy the `Theme:` and `Theme in game:` lines of `docs/jam-brief.md`; `submission_check.py theme`) |
| Team name | TBD |
| Video link | TBD (`video-plan.md`) |
| Devlog link | TBD (`devlog.md`) |
| AI disclosure | Code, art and audio made with AI agents and tools; see the devlog. (Default. Official Rules §7(a) allow AI tools and §9 uses the disclosure "for context only", `docs/jam-rules.md` row AI.) |
| Pre-jam declaration | TBD (paste from `docs/pre-jam-declaration.md`) |
| Credits | TBD (paste from `credits.md`) |

##### Files next to the exe
Owner: packaging and submission owner (human). Text: `README.txt` and `LICENSE.txt` in this folder. `tools/ue/package.ps1` copies both next to the game exe in every package.
README.txt copies Title, Controls, Team, Credits and Theme from this page; no pipeline text. LICENSE.txt default: all rights reserved, free to play, third-party assets under their own licences.
`python3 tools/submission_check.py files` exits 0 from Day 0; `files --final` exits 0 at G4 (no TBD).

##### Team (Official Rules §1(a), §1(c): 1 to 5 Entrants, full name and email of each, one Team Owner)
Card 0.0 collects these. Emails are entered on the jam form only, never committed. Each member confirms §5 (18 or over, an active Epic Account that is not a Cabined Account).
The Team Owner submits for the team (§15(a)) and receives any prize (§13).
`submission_check.py page` fails on any TBD or `n` in Email, a one-word name, fewer than 1 or more than 5 rows, or not exactly one Team Owner `y`.
| Full name | Role | Team Owner (y/n) | Epic email collected (y/n) |
|---|---|---|---|
| TBD | TBD | n | n |

##### Credits by role
One line per role, with names. Every member in the Team table is named at least once. `submission_check.py page` fails on a missing role, a TBD, or a member left out.
Third-party assets come from `credits.md`.
- Game design: TBD
- Programming: TBD
- Art: TBD
- Audio: TBD
- Production: TBD
- QA: TBD

### `pipeline/submission/video-plan.md`

#### Gameplay video plan (30-60 s)

The jam: "a 30–60 second gameplay video" and "Show gameplay in the first five seconds." Size: Official Rules §7(c), "Resolution of the Video must match 1920x1080 or higher"; §1(e), "between 30-60 seconds"; §7(i), English audio and text (`docs/jam-rules.md`).
Owner: Asset Specialist cuts it; the packaging and submission owner (human) signs it off.
Schedule: the cut is its own card, "Video cut" (Asset Specialist, 2 h, starts at G3, due G4; requested in `pipeline/day0-cards.md`). Footage is captured daily before that (below).
Done at G4 means checks 1-4 exit 0 and are pasted in the G4 gate record.
Done when: all four checks below pass, and the link is on the jam submission.

##### Checks
1. `python3 tools/submission_check.py video <file>` exits 0: 30-60 s, video at least 1920x1080, an audio stream.
2. `python3 tools/submission_check.py loudness <file>` exits 0: integrated loudness -14 LUFS +- 2.
3. Human sign-off, pasted on the tracker:
   `VIDEO first-frame=gameplay logo-first=no gameplay-by=<s> end=logo+CTA music=yes sfx-beats=yes by=<name>`.
   `python3 tools/submission_check.py signoff "<that line>"` exits 0 (gameplay-by is 5 s or less).
   The first frame is the owl attacking, not a logo, title card or black.
4. `python3 tools/submission_check.py footage --day 4 --final` exits 0 (every beat below was captured).

##### Shot list (in order)
| # | Time | Shot | Audio | Source clip |
|---|---|---|---|---|
| 1 | 0-5 s | Owl bolt volley: amber clock flash, red bolts cross the screen, Ella closes and drops under them | Music; bolt-hit SFX audible | `volley` |
| 2 | 5-15 s | Rise and fall: open to climb, close to dive, wand shots hitting the clock | Music | `rise`, `fall` |
| 3 | 15-25 s | Gust ride: wing gust telegraph, Ella catches the lift | Music; gust SFX | `gust` |
| 4 | 25-35 s | Torn umbrella: critical tier, weak lift, a narrow escape | Music | `torn` |
| 5 | 35-45 s | Desperation phase, then the owl pauses and leaves; "Survived" card | Music; owl-departure and "Survived" SFX audible | `end` |
| 6 | last 3-5 s | Game logo, then the call to action: "Play it on itch.io" with the page link | Music out | Title capture |

Audio rule: one game music track runs under the whole cut. Game SFX stay in the mix; music never covers the SFX on shots 1 and 5.
`music=yes` and `sfx-beats=yes` in the sign-off mean the human heard both. If the game has no music by G4, the video uses the game SFX only and says so in Known limitations.
Cut at most 60 s. Cut shots 2 and 4 shorter first; never cut shot 1 or 5.
Theme: one shot or the end card shows the theme, as written on the `Theme in game:` line of `docs/jam-brief.md`.
No HUD, no debug overlay, no smoke or eval text, no mouse cursor: every clip comes from a `-CaptureMode` run.

##### Capture switch (`-CaptureMode`)
- Non-Shipping only. On a packaged Development build it hides the HUD (health pips included), debug text, pipeline indicators and the cursor.
- It logs one line: `CAPTURE_MODE hud=off debug=off cursor=off`. `python3 tools/submission_check.py capture <game log>` exits 0 on that log.
- Who builds it: Gameplay Dev, Day-0 card 0.6c in the `Smoke/**` lane, due G1 (requested; not on the board yet). [VERIFY: needs Unreal; not built yet]
- `python3 tools/submission_check.py wiring` fails until that card is in `pipeline/day0-cards.md`. Until then the switch has no owner, and the Producer raises it at each day start.
- Done when: the check above passes on a real package log, and a pasted 1920x1080 capture shows no HUD health pips.
- Until it exists, no clip counts toward the footage log.

##### Footage capture (during the jam)
- Clips come from a packaged Development build run with `-CaptureMode`, at 1920x1080 or more, with game audio.
- From Day 2 (after G1), the Asset Specialist saves 2 or more clean clips a day to the team's shared footage folder, named `<day>-<beat>-<sha>.mp4`
  with a beat from: volley, rise, fall, gust, torn, end. Capture far more than the cut uses.
- Each clip gets one line in `pipeline/submission/footage.md` the same day. The day-start `submission_check.py daily --day N-1` run fails without them.
- Clips are not committed to git (they are large); only the final video link goes on the submission.

## Commands and checks

### `tools/submission_check.py`

Usage text from the file:

```text
Submission gate (G4). Stdlib only, plus ffprobe/ffmpeg for the video and loudness checks.
Rules and their sources: docs/jam-rules.md. Checklist: pipeline/checklists/submission.md.

  zip PATH [--team T --game G] [--commit SHA] [--gate G<n>]
        The jam zip, and every gate zip (the fallback). Fails when: the name is not TeamName_GameName.zip (letters and digits only);
        it is over 1,000,000,000 bytes; it holds a .uproject, C++ source, a Saved/ folder, or a
        .uasset/.umap outside a Paks folder (not a cooked package); there is not exactly one game exe
        outside Engine/ and Binaries/; README.txt, LICENSE.txt or BUILD_INFO.txt is missing next to
        that exe; BUILD_INFO.txt says config is not Development, workbench is not 0 (D-new-workbench-debug)
        or dirty=yes, or its platform (if
        written) is not Win64; no <Project>/Binaries/Win64/*.exe; the commit differs from --commit.
        --gate G<n>: the zip sits in a folder named G<n>-<sha>, and BUILD_INFO commit starts with that sha.
        Prints the zip's SHA256 for the submission record.
  video PATH        30-60 s, a video stream at least 1920x1080, an audio stream (ffprobe).
  loudness PATH     integrated loudness within LUFS_TARGET +- LUFS_TOL (ffmpeg ebur128).
  page [DIR]        pipeline/submission/page/: cover.png at least 630x500 and 315:250; 3-5
                    shot-<beat>.png, each a known beat, at least 1920x1080, no two the same file;
                    no TBD left in the Page fields table of pipeline/submission/itch-page.md;
                    the Team table has a row per member, no TBD, Epic email collected = y;
                    Credits by role has a `- <role>: <names>` line for each CREDIT_ROLES role and
                    names every Team member; the controls rows (CONTROLS_ROW DEC-02 firing, KEYS_ROW DEC-01
                    keys) in docs/decisions.md are DECIDED or say "default accepted" with a link.
  credits           every provenance row that needs credit (CC-BY, OFL, Fab, third-party) is named
                    in pipeline/submission/credits.md; every font file in the repo, and every
                    .uasset under a Content/**/Fonts/ folder, has a provenance row.
  devlog --day N [--published]
                    pipeline/submission/devlog.md has the three Glass Box headings and, for days
                    1..N, at least 3 obstacle lines each with a link; --published also needs the
                    `Published:` line to hold an https link.
  prejam [--log-file F]
                    every commit that touched Source/, Content/, Config/ or a .uproject before the
                    jam start (JAM_START) is listed by short SHA in docs/pre-jam-declaration.md.
  declaration [--ref REF]
                    every file tracked at REF (default HEAD) matches a pattern in the declaration's
                    tables. Run it with --ref jam-start at G4.

In-jam inputs (G4 depends on them; run during the jam, not at G4):
  theme [--now ISO] [--brief F]
                    from THEME_DUE on, docs/jam-brief.md has `Theme: "<kickoff quote>"` and
                    `Theme in game: <one line>`, neither empty nor TBD. Before THEME_DUE: pass.
  capture LOG       a game log from a -CaptureMode run holds `CAPTURE_MODE hud=off debug=off cursor=off`.
  footage --day N [--final]   (--final alone: --day 4)
                    pipeline/submission/footage.md: from FOOTAGE_FROM_DAY to N, at least
                    FOOTAGE_MIN_PER_DAY clips per day named <day>-<beat>-<sha>.mp4 under that day;
                    --final also needs every beat in BEATS at least once; the P1 beats (gust, torn)
                    only once their Gust / Wear row in pipeline/qa/test-map.md is merged.
  daily --day N [--now ISO]
                    devlog --day N + footage --day N + theme. check_card.py --status runs it for
                    day just ended. The import for check_card.py is status_hook(brief_text, now):
                    it reads the gate times in the jam-brief Clock (Day N ends at G<N>).
  wiring            the submission duties are wired into the files that agents load: the cards,
                    role cards and check_card.py lines in WIRING are there. Fails until they are.
  (practice repo, tools/practice.py: zip without --gate G1-G3, page, signoff, files --final, devlog --published,
   footage --final, prejam and declaration exit 1; assets skips the date rule. video and loudness still measure)
  assets            Official Rules 7(h): a provenance row under Content/, Art/ or Audio/ dated before JAM_START
                    fails unless its path is in credits.md '## Sourced assets'; a file there that is a byte copy of
                    a pipeline/art/reference/ file (pre-jam key art) fails. LFS pointers compare by oid.
                    It also runs `art`.
  art               every shipped image (under Art/ outside Art/Source/) has its passing art-loop record for its exact
                    bytes (<stem>.artloop.json, tools/art_loop.py): a panel of 3 calibrated blind critics, unanimous
                    ours or SAME against every reference, the quality bar, the motion pair (a sheet) and the in-engine
                    context; art_check/screen_check/art_ref_check PASS; current references.json. A labelled
                    placeholder or stand-in fails; nothing waives it.
  english          Official Rules 7(i): README.txt, LICENSE.txt, itch-page.md, credits.md, devlog.md and string
                    tables (*.csv, *.json under Content/ and pipeline/ui/) hold no letters from a non-Latin script.
  butler LINE       the G1 gate-record line: BUTLER version=<v> login=ok user=<itch-user> by=<name>.
  rules             docs/jam-rules.md has no [VERIFY] left and each quoted row cites an Official Rules section;
                    docs/rules/official-rules.md still holds every RULES_FACTS phrase; the Clock deadline is §4's end.
  files [--final]   pipeline/submission/README.txt and LICENSE.txt (package.ps1 copies them next to the
                    exe): neither empty; README has a 'Title:' line and 'Controls', 'Team' and 'Credits'
                    sections, and no pipeline text (ROLE:, 'card <n>'); LICENSE names a copyright
                    holder line. --final (G4): no TBD left in either file.
  signoff LINE      the human CONTENT line (G4, Official Rules 8, 15(d), 7(d)(e), 7(f), 7(i)):
                    CONTENT teen=yes trademarks=ue-logo-only original=yes extra-software=none english=yes by=<name>; or
                    the human VIDEO line: first-frame=gameplay logo-first=no gameplay-by=<s, at most 5>
                    end=logo+CTA music=yes sfx-beats=yes by=<name>.

Exit 0 = pass, 1 = problems, 2 = not run (a tool is missing, or git failed).
Tests: python3 -m unittest tests.test_submission_check (all suites: python3 -m unittest discover tests).
```

Run in CI by:

- `.github/workflows/pipeline-checks.yml`: Submission duties and the deadline guard stay wired (Producer; dry run B M2)
- `.github/workflows/pipeline-checks.yml`: Official Rules (docs/rules) - jam rules cite them, deadline = section 4, pre-jam assets (7(h)), English (7(i))

Tests: `tests/fixtures/kickoff/stub_agent.py`, `tests/test_art_ship.py`, `tests/test_assetgen.py`, `tests/test_audio_import.py`, `tests/test_final9_fixes.py`, `tests/test_honest_jam.py`, `tests/test_pipeline_check.py`, `tests/test_plan_checks.py`, `tests/test_practice.py`, `tests/test_submission_check.py`
