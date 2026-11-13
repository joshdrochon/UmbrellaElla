> Generated from `docs/jam-brief.md`, `docs/jam-rules.md`, `pipeline/day0-cards.md`, `pipeline/human-checkpoints.md`, `pipeline/how-to-run-the-jam.md`, `pipeline/what-the-pipeline-controls.md`, `pipeline/checklists/card-ready.md`, `pipeline/templates/task-card.md`, `pipeline/templates/spike-card.md`, `pipeline/templates/gate-record.md`, `pipeline/templates/tracker-table.md`, `pipeline/templates/clock-workflow.yml`, `.github/ISSUE_TEMPLATE/task.yml`, `.github/workflows/blocked-report.yml`, `.github/workflows/main-red.yml`, `tools/check_card.py`, `tools/lane_guard.py`, `tools/status_board.py` at `b201a66` — edit the sources, not this file.
> Rebuild: `python3 tools/export_package.py`. Check: `python3 tools/export_package.py --check`.

# Production Pipeline

A readable copy for people. Agents load these rules from the repo paths listed below.

## About this pipeline

- **Purpose:** Turn the brief into ready task cards, keep lanes parallel, run the daily cadence, call cuts and record gates.
- **Owner:** Producer role; the scope decision-maker and integration owner in `docs/jam-brief.md` are the humans.
- **Inputs:** The jam brief and rules, the Day-0 card list, open rows in `docs/decisions.md`.
- **Outputs:** Task cards (GitHub issues), lane plan, status line, gate records, cut calls, new decision rows.
- **Gates:** A card is not `todo` until `check_card.py` passes. G1-G4 are closed with a gate record. Main red: revert first.

## Built from

- Brief, rules and the Day-0 plan: `docs/jam-brief.md`, `docs/jam-rules.md`, `pipeline/day0-cards.md`
- Humans in the loop: `pipeline/human-checkpoints.md`, `pipeline/how-to-run-the-jam.md`, `pipeline/what-the-pipeline-controls.md`
- Checklists: `pipeline/checklists/card-ready.md`
- Templates: `pipeline/templates/task-card.md`, `pipeline/templates/spike-card.md`, `pipeline/templates/gate-record.md`, `pipeline/templates/tracker-table.md`, `pipeline/templates/clock-workflow.yml`, `.github/ISSUE_TEMPLATE/task.yml`
- Automation: `.github/workflows/blocked-report.yml`, `.github/workflows/main-red.yml`
- Commands and checks: `tools/check_card.py`, `tools/lane_guard.py`, `tools/status_board.py`

## Brief, rules and the Day-0 plan

### `docs/jam-brief.md`

#### Jam Brief: Umbrella Ella: The Stolen Hour

Every agent reads this first. If it disagrees with another document, add a decision row, build its default, say so in the PR.

##### The game
- **What:** Umbrella Ella: The Stolen Hour (GDD SH1.0). A 2D side-view game for 13+: Ella rises under her umbrella, drops to shoot or absorb, rides harmless currents, and takes apart the Keeper of Time's wings, three hanging mechanisms and clock. Two modes share the complete Keeper fight: **Start Game** (one basic shot, straight to the Keeper) and **Director's Cut** (story, progression, four spells, a nine-chunk level with enemies, then the same Keeper). The Keeper leaves alive; no survival timer.
- **Engine:** Unreal Engine **5.8.4**. **Platform:** Windows. Submission: a Windows **Development** package (no Shipping).
- **Win:** the final clock hit (OWL-35); the Keeper withdraws alive, then story and credits (FLOW-04). **Lose:** the last life empties (FLOW-31). Retry: the current phase or checkpoint, 3 lives, full health (FLOW-09).
- **Design source:** the snapshot `docs/gdd/CURRENT` names (now `docs/gdd/GDD-SH1.0.md`); feature statuses in `docs/feature-manifest.json`. GDD 1.3 and B1.0 are history (D-new-gdd-sh10).

Content caps: none set by GDD SH1.0. Frame counts and sizes follow each receiving contract (ANIM-02); the Art Director sets the art budget.

##### Jam facts (`docs/jam-rules.md` quotes them)
- Theme revealed Nov 11 (kickoff). Card 0.19 runs that day: 3 pitches in 1 hour, the game design owner picks one, a new GDD revision follows.
- No game building before the start, Nov 11 21:00 PST (D39). Tools, agents, MCP and the generic workbench (cards 0.25, 0.26) are allowed.
- From Nov 12, every agent prompt is logged (`tools/prompt_log.py`).
- Pre-jam work is declared in `docs/pre-jam-declaration.md`.
- We write the devlog (`pipeline/submission/devlog.md`, Glass Box).
- Submit a Windows Development build and a 30-60 s video by Nov 15, 5:59 PM PST. 7 equal criteria.

Theme: TBD
Theme in game: TBD

##### Clock (card 0.0 sets it; times ISO 8601 with UTC offset, Hard stop a daily `HH:MM-HH:MM` window; time zone D-new-clock)
Submission deadline: 2026-11-15T17:59-08:00
Hard stop: TBD
Card 0.9 cutoff: TBD

| Gate | Due |
|---|---|
| G1 | TBD |
| G2 | TBD |
| G3 | TBD |
| G4 | TBD |

Checked by `python3 tools/check_card.py --clock` (D-new-tune-day: G3 at least 20 h before the deadline).

##### Sources of truth
Play: the GDD snapshot, its mirror `docs/feature-manifest.json`, then `docs/game-spec.md`. Look: the key art + `pipeline/art/art-bible.md` (D0).
Feel: `docs/feel-spec.md`. Keeper fight: `pipeline/level/encounter.md`. Progression oracle: `tools/progression_model.py`. Undecided: `docs/decisions.md`. Process: `AGENTS.md`.

##### MVP — the game is "done" when all of these are true in a packaged build
**GDD SH1.0 approves every filled requirement as APPROVED_P0** (Rick, 2026-11-12): every line is P0, never cut. Build only after the start (D39). Numbers: manifest `approved_parameters`. The tag ends each line with its gate; `tools/check_card.py` reads it (D-new-sh10-g1).
1. Start screen with Start Game and Start Director's Cut; Start Game goes straight to the Keeper with one basic shot (FLOW-02, FLOW-34, ART-04). [G1]
2. Ella's four-state movement and inputs: rise, shoot-fall, absorb-fall, free fall, hop, dash, ride, trim, fixed-right fire (MOVE-04..MOVE-07, MOVE-11, MOVE-13..MOVE-15, MOVE-18..MOVE-22, WIND-03, CORE-04, CORE-05). [G1]
3. Small Blasts, the one unlimited basic shot, fired only while dropping (COM-05, COM-06, COM-10). [G1]
4. Health: one clock HUD with health and life hands, 3 hits x 3 lives, damage 1 / 1.25 / 1.5, lift by health, yellow heals (SURV-05, SURV-07, UMB-05, FLOW-30..FLOW-33). [G1]
5. The complete Keeper fight: wings, three mechanisms, clock, every attack and effect, phase checkpoints, the living departure (OWL-06..OWL-35, FLOW-09). [G1]
6. Pause (Continue, Settings, Quit), defeat retry and the win ending: story text over the background, then credits (FLOW-04, FLOW-35, NAR-07). [G1]
7. First-start tutorials in both modes, Pause then Skip at every step (FLOW-03, MOVE-16). [G2]
8. Player settings in both modes: Sound, Controller remap, Credits, Back and Save (MOVE-08..MOVE-10, MOVE-17, FLOW-36, FLOW-37, FLOW-39..FLOW-41, FLOW-43, FLOW-45). [G2]
9. Director's Cut level: the nine-chunk route, refuges, traps, camera, the Broken Mill room, procedural placement (FLOW-24..FLOW-29, FLOW-46, FLOW-47, HAZ-02..HAZ-41, CAM-03..CAM-08). [G2]
10. Regular enemies: Roadwarden (three types), Floodstrider, Sky Courier, male and female, red and yellow shots (COM-12..COM-18, ART-10, ANIM-08). [G2]
11. Director's Cut story: caption, text narration, light and umbra, the clock-hand clue, ending, Final Hour line (NAR-02..NAR-08). [G2]
12. Director's Cut progression: kills-only XP, the level-62 curve, stat tracks, checkpoint rules, persistence, run scaling, Final Hour, the XP ring (FLOW-05..FLOW-23, FLOW-42, FLOW-48, SURV-06). [G3]
13. The four Director's Cut spells with unlocks at levels 1 / 10 / 20 / 30 and the spell wheel (COM-07..COM-09, COM-11, MOVE-12). [G3]
14. Director's Cut win statistics (Journey Complete) and the Director-only developer Game Options (FLOW-38, FLOW-44, FLOW-49). [G3]
15. Final art, animation, VFX and audio at the key-art bar; no `_PH` left (ANIM-02..ANIM-07, ANIM-09, ANIM-10, ART-03, ART-05..ART-09, BG-02..BG-06, VFX-02..VFX-11, CORE-06). [G3]

Acceptance (GDD SH1.0 section 10): QA-29..QA-42 with recorded build, profile and seed.
Gate checks, not MVP items (D7): the title, pause, win and fail screens (defeat retry), `pipeline/qa/playtests.md`.

Stretch (never P0): stretch cards start automatically once every MVP item passes; GDD SH1.0 approves every filled requirement as APPROVED_P0, so the stretch list is:
none
Not authorized (GDD SH1.0): a fifth weapon, ammunition or stored energy, steering or mouse aiming in the normal modes, a boss tutorial on arrival, XP in Start Game, killing the Keeper.

##### Cut list (first to go at the top)
1. Recorded or generated narration voice (optional in GDD SH1.0, NAR-02; text narration stays)
2. Extra ambience and music beyond the required Start / End music (ANIM-09; Ricky's sound list "to discuss")
3. Animation polish beyond each family's required actions (ANIM-02..ANIM-08 list the required ones)

Never cut: any MVP item (all are APPROVED_P0) and a packaged build.
Trigger: a gate over 2 hours late cuts the next item, without debate. GDD SH1.0 leaves its own scope-cut triggers OPEN (section 11).

##### Top risks (the Producer reviews them at each gate)
| Risk | Trigger | Fallback | Owner |
|---|---|---|---|
| The package fails or differs from the editor | Package or smoke fails | Submit the last good gate zip | Packaging and submission owner |
| Paper2D or a setting misbehaves on 5.8.4 | A [VERIFY] item fails | Decision row; TD workaround same day | Technical Director, human |
| A teammate can't compile C++ | Card 0.9 fails | Non-C++ cards only (D24) | Scope decision-maker |
| A new GDD revision changes P0 | The design owner publishes a revision | Import it the same day (`docs/gdd/README.md`); `gdd_impact.py` lists the cards to re-file (D-new-gdd-sh10) | Game design owner |
| Art or audio late | MVP art or sounds missing at G2 | Tracked `_PH` placeholders (`pipeline/art/blender/characters.json` coverage), never shipped; CC0 set, card 0.15 (D-new-fallback) | Art Director |
| Human review is the bottleneck | `--queue` fails twice (D-new-port-3) | Pause new agent cards | Producer / time keeper, human |

##### People (fill in; card 0.0)
Rows marked **BLOCKER** stop Day 1.
| Role | Person | Confirmed? | Day-1 blocker |
|---|---|---|---|
| Scope decision-maker (final call on cuts) | Rick (proposed) | no | BLOCKER |
| Creative director (tie-breaker on look, feel and theme; D34) | Rick (proposed; GDD SH1.0: "Rick's creative approval") | no | before Nov 11 |
| Producer / time keeper, human (D-new-producer) | Richard (proposed; GDD SH1.0 credits: Producer) | no | BLOCKER |
| Integration owner (merges to main, keeps it building; one integrator owns cross-lane edits) | TBD | no | BLOCKER |
| Packaging and submission owner | TBD | no | BLOCKER |
| Windows packaging machine (owner, machine name, OS) | TBD | no | BLOCKER |
| Game design owner (GDD revisions, feature statuses, P0; D-new-sh10-design-owner) | Rick (GDD SH1.0 revision note: "Rick approves all filled requirements") | no | BLOCKER |
| Technical Director, human (code-owner seat, D26) | Josh (GDD SH1.0 credits: Technical Lead) | no | BLOCKER |
| GDD author (GDD SH1.0 document owner: Team Glass Umbrella) | Rick | no | |
| Human testers (GDD SH1.0 HAZ-16, QA-29..QA-42 human checks) | TBD | no | before G2 |
| Audio owner (approves the mix by ear) | TBD | no | before card 0.4c |
| Playtest lead | TBD | no | before G1 |

##### Team hours (card 0.0: one row per teammate)
| Person | Hours D1/D2/D3/D4 | Away windows | Built UE C++ before (y/n) | Confirmed? |
|---|---|---|---|---|
| TBD | TBD | TBD | TBD | no |

##### Hard limits
- Main opens in the editor and packages at every merge. A broken main stops feature work until fixed.
- No agent merges or accepts its own work.
- Every "works" claim carries evidence: command output, a test result, or a capture.

### `docs/jam-rules.md`

#### Jam rules (quoted) and the team rules that follow from them

> GDD SH1.0 note (D-new-gdd-sh10): lines on this page that still describe the GDD 1.3 encounter (one owl bolt, the front shield, the 90 s survival timer, wear stages, the 1.3 QA-01..QA-28 tests) are history. The current design is `docs/gdd/GDD-SH1.0.md` and `docs/feature-manifest.json`, which win; the owning role re-files this page against the SH1.0 Rule IDs on its next card.


Source of truth: the **Official Rules**, `docs/rules/2026_Epic_AI_MegaJam_Official_Rules_EN.pdf` (last updated
November 5, 2026; sha256 pinned in `docs/feature-manifest.json` `rules_pdf`), text in `docs/rules/official-rules.md`.
They prevail over everything else in this repo (`docs/references.md` R0). `§n` below is a section of that PDF.
Secondary: the jam's itch page, https://itch.io/jam/2026-epic-ai-megajam (read 2026-11-07; it calls itself "a summary"),
and itch's jam docs, https://itch.io/docs/creators/game-jams (read 2026-11-07), for how uploads behave.
Where the itch page asks for more than the PDF (a Development build, the zip name), the team follows both.
Checks: `tools/submission_check.py` (`rules` ties this file and the constants to the PDF text). Checklist: `pipeline/checklists/submission.md`.

##### Quoted rules
| Rule | Official Rules | itch page or team note | Our check |
|---|---|---|---|
| Deadline | §4: "The Contest begins at 12:00 AM Eastern Time ("ET") on November 12, 2026, and ends at 8:59 PM ET on November 15, 2026." §3: late entries are not Sponsor's responsibility | "before November 15, 5:59 PM PST / 8:59 PM EST" | `JAM_START`, `JAM_END` in `submission_check.py`; `submission_check.py rules` fails unless the Clock `Submission deadline` equals §4's end; `check_card.py --clock --uploaded` |
| Build | §1(b): "must be packaged for Windows and playable on Windows 10 or 11" (or macOS, Android, iOS). §7(f): "should not require any additional software to run". No build configuration is named | "Package your game for Windows (development build)." | `submission_check.py zip`: BUILD_INFO `config=Development`, `Binaries/Win64`, exactly one game exe; the zip is downloaded again and launched on another machine from G1 (`pipeline/templates/gate-record.md`); the G4 checklist asks for a machine with no extra software (§7(f)) |
| Zip | Official Rules: silent | Name the .zip "TeamName_GameName" and "keep it under 1 GB." | `submission_check.py zip`: name and 1,000,000,000 bytes |
| Upload | §1: "Online submissions only" via https://itch.io/jam/2026-epic-ai-megajam. §2: "Limit one (1) Submission per team. Entrants are not permitted to submit a Submission more than once during the Contest Period." | "Upload it to your own itch.io account, then submit to this jam." | Upload section of the checklist; team rule 5 |
| Human submits | §17: "each Submission must be submitted by an Entrant (on behalf of the team) and not by an AI agent or other automated means." §15(a): "The Team Owner submits on behalf of, and with authority from, all Entrants" | – | Needs-human checkpoint (`pipeline/human-checkpoints.md`); `hook.py` blocks `butler push` and `butler login` for every agent (`gates.json` `human_only_commands`) |
| Video | §1(e): "a video short (between 30-60 seconds) demonstrating recorded gameplay". §7(c): "Resolution of the Video must match 1920x1080 or higher" | "Show gameplay in the first five seconds." | `submission_check.py video` (30-60 s, at least 1920x1080, audio); human `VIDEO` sign-off for the first 5 s |
| Team | §1(a): "a team of one (1) to five (5) Entrants". §5: each Entrant is at least 18 and has "an active, valid Epic Account"; Cabined Accounts are ineligible | "There's no limit on agents." | `submission_check.py page`: 1 to 5 Team rows; card 0.0 asks each member to confirm §5 |
| Team details | §1(c): "the full name and email address of all Entrants on a submitting team, identifying one of them as the team owner" | "each member's name and the email address linked to their Epic Games account" | `submission_check.py page`: full name, email collected = y, exactly one Team Owner (`pipeline/submission/itch-page.md` Team table) |
| Start | §7(h): "Entrants may prepare AI tools, agent configurations, Model Context Protocol ("MCP") settings, prompt libraries, and scripts before the Contest Period. Sponsor may ask Entrants to provide these materials, or their version control history ... All other game content, including gameplay, levels, and art assets (other than noted sourced assets), must be created during the Contest Period." | "Declare anything you made earlier." | `submission_check.py prejam`, `declaration` and `assets` (team rules 7, 12) |
| Assets | §1(d): "the sourced assets must be noted upon submission". §15(c): sourced assets "will not be reviewed or scored"; "Content the Entrants generate with AI tools is not considered a sourced asset." | "List them in your submission." | `submission_check.py credits` and `assets`: every sourced asset is in `pipeline/submission/credits.md` "Sourced assets" |
| AI | §7(a): "Submissions may, but are not required to, use artificial intelligence ("AI") tools in their creation or gameplay". §9: "The extent of AI use disclosed in a Submission will be considered for context only" | "Use any AI tools you like" | Default disclosure line in `pipeline/submission/itch-page.md`; D14 cites this row |
| English | §7(i): "All Submission content (including in-game text, audio and the Video) and all entry information must be in English" | – | `submission_check.py english` (submission text and string tables); the human `VIDEO` sign-off covers audio and video |
| Original game | §7(d): not "an obvious extension of one of Sponsor's official Unreal Engine tutorials". §7(e): "custom gameplay that exceeds that found in Sponsor's starter templates" | – | Template maps are not reused (`pipeline/unreal-rules.md`); G4 human sign-off (checklist, Content) |
| Theme | §7(g): "Submissions must demonstrate use of the Contest Theme." §1: the theme is given "at the start of the Contest Period" | Kickoff livestream, November 11, 11 AM PST | `submission_check.py theme`: `Theme:` and `Theme in game:` in `docs/jam-brief.md` by 2026-11-11T13:00-08:00 (card 0.19) |
| Content | §8: "appropriate for a teen audience, meaning content suitable for players aged 13 and over (consistent with a "Teen" rating under the ESRB system". No disparagement, no infringing material | – | G4 human sign-off (checklist, Content) |
| Trademarks | §15(d): "Submissions may not feature any trademarks (including logos), except ... the Unreal Engine logo ... as described in Sponsor's Branding Guidelines" (https://www.unrealengine.com/branding) | – | G4 human sign-off (checklist, Content); the video end card uses only the Unreal Engine logo per those guidelines |
| Devlog | §10 Glass Box: "the dev log must be submitted together with the Submission during the Contest Period" | "Dev log link (optional, but required for the Glass Box modifier)." | `submission_check.py devlog --published` before the deadline; prompts logged daily from Nov 12 (`prompt_log.py export --check`) |
| Late changes | Official Rules: silent on updating a submission; §2 forbids submitting more than once | itch docs: "Submitting early will still let you publish updates right up until the deadline." | Team rules 5 and 10; D-new-upload |
| Judging | §9: Ambition and Innovation, Use of Contest Theme, Fun Factor, Gameplay, Visuals, Level Design, Audio, each "Up to 5 points" (35 total). "In the event of a tie, the tying Submissions will be re-scored with double weight given to Fun Factor." | – | Judges score. Our nearest gate is P11 Fun (`pipeline/qa/playtests.md`), and Fun Factor breaks ties |

##### Team rules that follow
1. **Build.** The submitted zip is a Windows Development package (Win64): the itch page asks for it, and §1(b) names no configuration. A Shipping package is optional, never submitted. GDD 1.3 QA-18 says "shipping": open for Richard in D-new-gdd13-shipping.
2. **Zip name.** `<TeamName>_<GameName>.zip`, letters and digits only. The commit SHA lives in `BUILD_INFO.txt` and the record, not the name.
   Gate zips keep the same file name inside a folder `G<n>-<sha>/`, so the fallback needs no rename. `submission_check.py zip <path> --gate G<n>` checks the folder and file name at every gate.
3. **Size.** Over 1,000,000,000 bytes fails the check. A 2D single-screen game is far under it. If it ever fails, cut content first; butler is the upload tool either way.
4. **Upload tool.** butler (`butler push <zip> <itch-user>/<game>:windows-dev`), run by a human only (§17; the hook blocks agents). By G1 the packaging owner runs `butler -V` and `butler login` on the packaging machine and puts `BUTLER version=<v> login=ok user=<itch-user> by=<name>` in the G1 gate record (`submission_check.py butler`).
5. **Early uploads.** From G1 the zip goes to the team's own itch project while the project is Draft (the jam page's own words: "Upload it to your own itch.io account, then submit to this jam"). Never "to the jam page".
   §2 allows one Submission per team and forbids submitting "more than once"; the PDF does not say whether files on a submitted entry may be replaced. So the team submits exactly once and never makes a second entry. Whether that one submission happens at G2 and is updated, or only at G4, is D-new-upload (open; ask the organisers on the itch community page if it matters).
6. **Internal cutoff.** Final upload at least 3 h before the deadline (`check_card.py --clock --uploaded`). G4 is the internal deadline.
7. **Jam start.** No commit touching `Source/`, `Content/`, `Config/` or a `.uproject` before the jam start, 2026-11-11T21:00-08:00 (Nov 11 21:00 PST = Nov 12 00:00 ET, §4; GDD SH1.0 section 11), unless it is listed in `docs/pre-jam-declaration.md` (`submission_check.py prejam`). Pre-jam work is only what §7(h) names: AI tools, agent configs, MCP settings, prompt libraries and scripts. Keep their history: the Sponsor may ask for it.
8. **Theme.** By 2026-11-11T13:00-08:00 the game design owner (card 0.19) writes `Theme: "<kickoff quote>"` and `Theme in game: <one line>` in `docs/jam-brief.md` (`submission_check.py theme` fails after that time while either is empty). The theme is visible in the game (title or end card) and named on the itch page (§7(g)).
9. **Packaging owner.** Named in the People table of `docs/jam-brief.md` by card 0.0. Until then, nobody packages a submission.
10. **Files lock at the deadline; page text may change.** The zip on the page at the deadline is the entry. The G4 zip is final: after G4 no new zip goes up unless a P0 forces it, and never after the deadline, even if itch would allow it. After the deadline only the page text and images may change; the devlog is submitted with the entry before the deadline (§10). A new zip before the deadline needs a new submission record first (checklist, Upload).
11. **README.txt and LICENSE.txt.** Both sit next to the game exe in every zip. Their text lives in `pipeline/submission/README.txt` and `LICENSE.txt` (owner: packaging owner; `itch-page.md`). `tools/ue/package.ps1` copies them in (requested from the build lane). `submission_check.py files` checks the text; `--final` at G4 also fails on TBD.
12. **Pre-jam art is reference only.** Key art, style frames and rehearsal builds made before the start stay under `pipeline/art/reference/` or `scratch/` and are never shipped. `submission_check.py assets` fails when a provenance row under `Content/`, `Art/` or `Audio/` is dated before the start and is not listed as sourced, or when a shipped file is a byte copy of a reference file. Prompt libraries are kept (§7(h) allows them).
13. **English.** Every in-game string, voice line, the video and every entry field is English (§7(i); `submission_check.py english`).
14. **Submission is human.** The final upload and the jam form are a needs-human checkpoint for the Team Owner (§15(a), §17). An agent prepares the record and stops.

### `pipeline/day0-cards.md`

#### Day-0 cards: the first work, in order

"No card, no work" needs a first card. These are it (MVP item field: `Day 0`, GDD ref and Player outcome: `none`).
Their lanes are listed here because the paths don't exist until card 0.3 is merged.
Each line in "Done when" (split at `<br>`) becomes one checkbox. `tests/test_day0_cards.py` files every row through
`tools/check_card.py`, so a row the checker rejects fails CI. `tools/pipeline_check.py` fails on an "After" cycle or an unknown card.

**When.** Pre-jam (before the start, Nov 11 21:00 PST = Nov 12 00:00 EST): 0.0, 0.1, 0.2, 0.7, 0.11, 0.15, 0.16, 0.17, and the generic workbench 0.25, 0.26 (0.11, 0.15, 0.16 and 0.17 still wait for card 0.0, per the Day-1 blockers rule below) (GDD SH1.0 ART-03: no pre-jam art; synthetic objects only, no umbrella or owl content). Nov 11, after the theme reveal: 0.19, then the story bible 0.34 (Story role).
Every other card makes or needs game files, so it starts at the jam start (D39). "Day 0" below means "before the first MVP card", not a date.
Before the start, `tools/kickoff.sh` on the team repo files and runs only the pre-jam cards in the line below (tools, agent setup, rules and the
synthetic workbench sample: Official Rules §7(h), `docs/pre-jam-declaration.md`); in a practice repo it runs every card. `tools/check_card.py` reads this line:
**Pre-jam cards:** 0.0, 0.1, 0.2, 0.7, 0.11, 0.15, 0.16, 0.17, 0.19, 0.25, 0.26
**G1 cards:** 0.0, 0.3, 0.4a, 0.4c, 0.4e, 0.5, 0.5b, 0.6, 0.6c, 0.6e, 0.8, 0.8a, 0.8b, 0.12, 0.14b
`tools/kickoff.sh --until G1` (`tools/kickoff.py` gate_targets) builds only these, the MVP cards whose MVP item the brief tags `[G1]` (MVP 1-6), and every card they list in After; it ends with the G1 Mac package: `tools/ue/daily.sh` on `main` (build, tests, package, smoke) must print a DAILY line with package and smoke PASS. Every G1 card runs on the Mac; the Windows cards (0.3w, 0.6w, 0.4b, 0.6d) wait for the Windows packaging machine and never hold up G1.

**Filing.** "After" = cards that must be merged first. The Producer files a card only when all its After cards have merged,
so `check_card.py --lanes` never sees two open cards with overlapping lanes.

**Owners and sign-offs.** Agents own all the work. Column 3 is `<agent role> / <human seat> (sign-off: <kinds>)`: the agent
role builds the whole card and kickoff merges it; the seat after `/` is the card's Human, who is asked only when the pipeline
is stuck, and does only the Done-when lines that start `HUMAN <kind>:`. Two kinds remain (`pipeline/human-checkpoints.md`
"Checkpoint kinds"): `submission` (the itch upload) and `secrets` (setting API keys). Every reviewer is an agent role (a
fresh session; kickoff merges on its approve). A card that must run on the Windows packaging machine says
`Runs on: the Windows packaging machine` in its Done-when: only a kickoff there builds it. When filing, the Producer writes
that seat's person from the `docs/jam-brief.md` People table as the card's Human (the name only). `tools/pipeline_check.py`
and `tests/test_day0_cards.py` fail a row whose owner or reviewer is a person, and a Done-when line that names a person
without its `HUMAN <kind>:` tag (`check_card.day0_owner_problems`).

**Gate paths.** `tools/**`, `tests/**`, `.github/**`, `pipeline/art/style.json`, `pipeline/agent-ops/**` and the rest of
`pipeline/agent-ops/gates.json` are gate files. No agent session commits them, during the jam too: no local git hook stops it, so `check_pr.py` rule gate on the PR and kickoff's merge gate catch it.
Where a lane below holds one, the owner agent still does the work: it writes the change as a git patch to `$JAM_OUTBOX/gate.patch`
(and tests it from that copy); kickoff keeps it as `.pipeline/gate-patches/UE-<id>/` and applies it itself with
`python3 tools/git_gate.py apply UE-<id> --auto`. The tools decide, not a person: every patched path is in the card's lane, no
guardrail enforcer (`git_gate.py` GUARD_CORE) changes, and no guardrail file loosens (gates.json and `.claude/settings*.json`).
It commits with the trailer `GATE EDIT: by=kickoff`; CI's `check_pr.py` rule gate finds that commit in the PR's git history
(never the PR body) and re-runs the same checks, and kickoff's merge gate runs this checkout's rule gate too. A refused patch goes back to the builder with the reasons.
Editor scripts that are not gates live in `pipeline/unreal/editor_scripts/`.

**Other card fields.** The table has no Budget, Inputs, Out of scope, Used by or Needs column. When filing, the Producer writes
Budget `60 min agent + 15 min human` (more means split the card; cards 0.3, 0.4d, 0.25 and 0.26 get `120 min agent + 60 min human`, the `check_card.py` caps, as builds on two OSes and gate scripts take longer), Inputs = the files its Done-when names,
Out of scope = anything outside the lane, Used by = the cards that list it in After (or none), Needs = what its Done-when runs.

**Day-1 blockers.** Card 0.0 must be done before any other card moves to `doing`, except 0.1, 0.2, 0.7, 0.19, 0.25 and 0.26 (the theme is due Nov 11 even if 0.0 slips). GDD SH1.0 already authorizes every Rule ID as APPROVED_P0 (D-new-gdd-sh10), so MVP cards pass `check_card.py` now; the Producer files them only after the jam start (D39).

| # | Card | Owner role / human sign-off | Reviewer | Lane | After | Done when |
|---|---|---|---|---|---|---|
| 0.0 | People, Clock, packaging machine, Day-1 decisions (BLOCKER) | Producer / Rick | Technical Director | `docs/decisions.md` rows D34, D39, D-new-clock, D-new-gdd-sh10, D-new-sh10-design-owner, D-new-sh10-g1, `docs/jam-brief.md` Clock, People and Team hours tables, `.github/CODEOWNERS` | – | The Producer agent fills every People row from the repo's GitHub collaborators (`gh api repos/{owner}/{repo}/collaborators`: the login is the name until that person edits the row) and the GDD SH1.0 credits (FLOW-39), and every Team hours row with the jam window (`docs/jam-rules.md`, the Clock) as the default hours, each row's Confirmed cell `default (agent)`; the Clock from Official Rules §4 and D-new-clock; `.github/CODEOWNERS` from `CODEOWNERS.example` (D26) as the card's gate patch<br>`python3 tools/check_card.py --clock` exits 0: deadline, G1-G4 times, hard stop and card 0.9 cutoff are set, and G4 is at least 3 h before the deadline<br>`python3 tools/check_card.py --people` exits 0 on the agent-default rows (pasted)<br>`grep -n TBD docs/jam-brief.md` prints only the `Theme:` and `Theme in game:` lines, or nothing if card 0.19 already filled them (pasted)<br>The Producer agent marks D34, D39, D-new-clock, D-new-gdd-sh10, D-new-sh10-design-owner and D-new-sh10-g1 (G1 = the Start Game mode) DECIDED (dated, `agent default; Producer; the team may override`) with each row's own default<br>`python3 tools/manifest_check.py` prints 0 problems and the PR pastes the `tools/gdd_impact.py` list the agent ran (pasted)<br>The CODEOWNERS handles are the People rows' GitHub logins; kickoff applies it itself through the tool checks (`python3 tools/git_gate.py apply UE-0.0 --auto`: every path in the card's lane, no guardrail enforcer changed, no guardrail file loosened; the PR has a `GATE EDIT: by=kickoff` line naming the patched paths) |
| 0.1 | Jam tracker issue | Producer | QA and Build | GitHub only | – | `gh issue list --label tracker` lists 1 pinned issue "Jam tracker"<br>Its first comment holds the daily status line and build record formats from `producer.md` and `qa-build.md` |
| 0.2 | Read the official rules PDF | Producer | QA and Build | `docs/jam-rules.md` | – | The PDF in `docs/rules/` matches the sha256 in `docs/rules/official-rules.md` (pasted), and the Producer agent confirms every quote in `docs/jam-rules.md` against its text: `python3 tools/submission_check.py rules` exits 0 (pasted)<br>The quote in docs/jam-rules.md row AI is the one D14 cites<br>3 quotes are pasted on the card: making files before Nov 12 (D39), declaring a skeleton (D39), and updating an early submission (D-new-upload) |
| 0.3 | Project skeleton (Nov 12) | Technical Director / TD human | Dev Lead | `UmbrellaElla.uproject`, `Source/**` (new), `Config/**`, `Content/UmbrellaElla/Input/**`, `Content/UmbrellaElla/Maps/L_Graybox.umap` | 0.0 | Contents as in `technical-director.md` Outputs, including GameDefaultMap `/Game/UmbrellaElla/Maps/L_Graybox` (an empty level made here; card 0.8 builds it out), a C++ GameMode whose DefaultPawnClass is the Ella shell set as GlobalDefaultGameMode, and a provisional Default Pixels Per Unreal Unit set before any import. `Config/DefaultEngine.ini` also sets `UIScaleRule=ShortestSide` so `python3 tools/ui_check.py ci` passes on this PR (card 0.20 adds the DPI curve)<br>Three targets set the workbench switch (D-new-workbench-debug, `pipeline/unreal-rules.md` Workbench): `UmbrellaElla.Target.cs` `UMBRELLAELLA_WORKBENCH=0`, `UmbrellaEllaEditor.Target.cs` and `UmbrellaEllaWorkbench.Target.cs` `=1`; `python3 tools/ue_run.py workbench-check` prints PASS, and FAILS once with the submission target flipped to 1 on purpose (both pasted)<br>Runs on: the Mac build machine: a kickoff there (`tools/kickoff.sh`) builds and fixes this card, a kickoff on Windows leaves it waiting (`tools/kickoff.py` RUNS_ON_MAC); that session runs every line below on the Mac (UE 5.8.4, Xcode)<br>`tools/ue/build.sh` exits 0 on the Mac (log tail pasted); the Windows build is card 0.3w<br>`tools/ue/test.sh --bootstrap` runs the placeholder test `UmbrellaElla.Bootstrap.Placeholder`; `check_automation_report.py` prints PASS tests=1 (summary line pasted)<br>`tools/ue/package.sh` exits 0 on the Mac: its `package exit: 0  commit=SHA  dirty=no ... platform=Mac` line is pasted, and the packaged app launches: `tools/ue/smoke.sh` with `SMOKE_MODE=alive` on its executable prints exit 0 (pasted)<br>The PR pastes `package exit: 0` and `SMOKE_BOOTSTRAP: no smoke hook before card 0.6` in place of SMOKE_OK; `check_pr.py` accepts that line only while `Source/UmbrellaElla/Private/Smoke/` does not exist (Day-1 bootstrap, `tools/check_pr.py`)<br>Paste whether `Automation RunTests` (what `tools/ue/test.sh` runs) found the tests; if only `Automation RunTest` does, file a bug card for the scripts (this card has no gate patch)<br>The PR also pastes (`technical-director.md` Done when): the `NONUNITY=1 tools/ue/build.sh` line, a 5.8.4 `index.json` excerpt showing each test's `duration` field, the compile log of one `final` UCLASS, and `python3 tools/module_check.py --rules K` exit 0 on the real `Source/`. Card 0.4a copies the `final` log into `pipeline/unreal/cpp-rules.md` (its lane) and removes its [VERIFY]; rule K then runs by default (`module_check.py` k_proven)<br>kickoff tags `jam-start` on `main` itself when this card starts (only on or after the start, never in a practice repo), the pre-jam record the Sponsor may ask for (Official Rules §7(h), `docs/pre-jam-declaration.md`); `git tag -l jam-start` prints it (pasted) |
| 0.3w | Windows skeleton build, tests and package (the Windows packaging machine) | Technical Director / packaging machine owner | Dev Lead | `Config/Windows/**`, `Source/UmbrellaElla/Private/Platform/Windows/**` | 0.3 | Runs on: the Windows packaging machine: a kickoff there (`tools\kickoff.ps1`) builds and fixes this card, a kickoff elsewhere leaves it waiting (`tools/kickoff.py` RUNS_ON_WINDOWS); nothing on the Mac G1 path lists this card in After, so it never holds up G1<br>`tools\ue\build.ps1` exits 0 on the packaging machine on `main` (log tail pasted)<br>`tools\ue\test.ps1` prints the same `PASS tests=N` summary as the latest Mac run of `tools/ue/test.sh` on `main` (both lines pasted)<br>`tools\ue\package.ps1` exits 0: its `package exit: 0  commit=SHA  dirty=no ... platform=Win64` line is pasted<br>A Windows-only fix lives in this card's lane (`Config/Windows/`, `Platform/Windows/`); a fix that needs a shared file is a bug card for the Producer, never an edit outside the lane |
| 0.4a | Editor MCP inventory and editor [VERIFY] items | Technical Director / TD human | Dev Lead | `pipeline/unreal-rules.md`, `pipeline/unreal/`, `pipeline/agent-ops/components.csv`, `pipeline/agent-ops/gates.json`, `pipeline/agent-ops/mcp.template.json` | 0.3 | The MCP's real tool list is pasted into the unreal-rules MCP section<br>The generated `.mcp.json` is compared with `pipeline/agent-ops/mcp.template.json`, each [VERIFY on 5.8.4] there is removed with the editor output pasted, and `python3 tools/editor_mcp.py check` exits 0 (pasted); the MCP stays off until kickoff (`pipeline/agent-ops/editor-mcp.md`)<br>The agent drafts `components.csv` vetted_by and the `mcp_allow` list from the real tool list, with this card's other `pipeline/agent-ops/` edits, as the card's gate patch<br>kickoff applies it itself through the tool checks (`python3 tools/git_gate.py apply UE-0.4a --auto`: every path in the card's lane, no guardrail enforcer changed, no guardrail file loosened; the PR has a `GATE EDIT: by=kickoff` line naming the patched paths); `mcp_allow` may only add tools whose names match no `mcp_ask_words` entry, and `mcp_enabled` stays false; `python3 tools/secrets_check.py --rules mcp,components` exits 0 (pasted)<br>Each editor-side [VERIFY] item (Paper2D default, World Partition off on a Basic level, IWYU flag, exceptions and RTTI off, `ue.Debug` macro, validator commandlet name, transient test world API, Enhanced Input user settings, the feature-flag data asset and subsystem, the tick prerequisite in `pipeline/unreal/gameplay-code.md`) has its tag removed or its rule rewritten, with the output pasted<br>The `final` UCLASS compile log from the card 0.3 PR is pasted into `pipeline/unreal/cpp-rules.md` and that [VERIFY] removed<br>`grep -c VERIFY pipeline/unreal-rules.md` prints 1 (only the intro line that explains the tag), and the editor's texture group list is pasted for D-new-art-texgroup |
| 0.4b | Packaging-machine [VERIFY] items, first test upload | Technical Director / packaging and submission owner (sign-off: submission) | QA and Build | `pipeline/unreal-rules.md`, `pipeline/unreal/` | 0.2, 0.4a, 0.8, 0.3w, 0.6w | `tools\ue\build.ps1` with `-DisableUnity -NoPCH -NoSharedPCH` exits 0 on the packaging machine (Runs on: the Windows packaging machine: a kickoff there (`tools\kickoff.ps1`) builds and fixes this card, a kickoff elsewhere leaves it waiting (`tools/kickoff.py` RUNS_ON_WINDOWS))<br>Each packaging [VERIFY] item (non-unity flags, `-abslog`, BUILD_INFO platform folder, Maps cooked from `MapsToCook`) has its tag removed or its rule rewritten, with the log line pasted<br>The agent builds the Development zip of `main` and writes the exact `butler push` line and its sha256 on the card<br>HUMAN submission: by the Clock G1 time, the packaging and submission owner uploads that zip to the team's Draft itch project (Official Rules §17: never an agent)<br>The card's session unzips that zip into a new folder outside the build tree and launches it with `$env:SMOKE_ZIP="ZIP"; tools\ue\smoke.ps1 -Exe EXE` on the unzipped copy (it writes the `LAUNCH` record line the gate record needs)<br>The agent posts `Itch test upload: LINK sha256=HASH` on the tracker, and `check_card.py --status` exits 0 after G1 (D-new-upload-g1) |
| 0.4c | Audio core assets + audio_dump.py | Technical Director / TD human | Audio | `Content/UmbrellaElla/Audio/Core/**`, `pipeline/audio/audio-rules.md` ([VERIFY] tags only), `tools/ue/audio_dump.py` (gate patch only) | 0.4a | `Content/UmbrellaElla/Audio/Core/` holds `SCL_SFX`, `SCL_Telegraph`, `SCL_UI`, `SCL_Music`, `SM_Master` with one limiter, and the 7 `SCON_*` groups in `pipeline/audio/audio-rules.md` section 2<br>The editor run of `tools/ue/audio_dump.py` writes `Saved/AudioDump.json`; its `engine` field reads 5.8.x (log line pasted)<br>`python3 tools/audio_check.py --ue-dump Saved/AudioDump.json` prints PASS with an empty `unread` list (pasted)<br>`grep -c VERIFY pipeline/audio/audio-rules.md` prints 0<br>Only if the agent changed `pipeline/audio/ue/audio_dump.py`: the matching `tools/ue/audio_dump.py` is the card's gate patch and kickoff applies it itself through the tool checks (`python3 tools/git_gate.py apply UE-0.4c --auto`: every path in the card's lane, no guardrail enforcer changed, no guardrail file loosened; the PR has a `GATE EDIT: by=kickoff` line naming the patched paths); `cmp pipeline/audio/ue/audio_dump.py tools/ue/audio_dump.py` exits 0 |
| 0.4e | G1 sounds: every P0 row of the sound list (ElevenLabs, tracked placeholders on failure) | Audio / audio owner | QA and Build | `Audio/Source/**`, `Content/UmbrellaElla/Audio/**` (not `Core/`), `pipeline/art/provenance.csv` | 0.4c, 0.14b | For every row of `pipeline/audio/sound-list.csv` with tier P0 that has no take yet, the agent runs `python3 tools/assetgen.py sfx` (`music` for a music row) with `--sound` set to the row's id and `--out` set to each take file under `Audio/Source/` (the names `pipeline/roles/audio.md` gives); the step queues and kickoff runs it with ELEVENLABS_API_KEY after the session (`tools/assetgen.py fulfil`); then `python3 tools/audio_loop.py start --card UE-0.4e` names every generated id<br>A take ElevenLabs could not make (no key, an HTTP error, no credits left) is a tracked placeholder: a procedural take whose provenance origin says `placeholder: REASON`; `python3 tools/audio_check.py --placeholders` lists each one (pasted), the MVP 15 audio card regenerates it, and `audio_check.py --scan Audio/Source --release` fails while one is left<br>kickoff runs the blind critic for each generated piece (`tools/kickoff.py` audio_loop_card) and the PR pastes the `python3 tools/audio_loop.py close --card UE-0.4e` output: `audio_loop close: PASS` with one `AUDIO LOOP: PASS` or `AUDIO PLACEHOLDER:` line per sound<br>`python3 tools/audio_check.py --scan Audio/Source --require-dir` prints PASS: every P0 row has all its takes (pasted)<br>Each take is imported into its folder under `Content/UmbrellaElla/Audio/` (wave assets and a cue, `pipeline/roles/audio.md` Owns) with its class and concurrency, and `python3 tools/audio_check.py --ue-dump Saved/AudioDump.json` prints PASS (pasted)<br>Each new file has a provenance row (`python3 tools/audio_check.py --scan Audio/Source` reads them) |
| 0.4d | Art dump script | Technical Director / TD human | Art Director | `tools/ue/art_dump.py`, `pipeline/art/style.json`, `pipeline/art/import-rules.md` | 0.4a, 0.10b | The agent writes `tools/ue/art_dump.py` and the `style.json` lines, runs them from its outbox copy, and sends them as the card's gate patch<br>Kickoff applies it itself through the tool checks (`python3 tools/git_gate.py apply UE-0.4d --auto`: every path in the card's lane, no guardrail enforcer changed, no guardrail file loosened; the PR has a `GATE EDIT: by=kickoff` line naming the patched paths)<br>Every line of the "Card 0.4d done-when" block in `pipeline/art/import-rules.md` is met, with outputs pasted<br>`python3 tools/sprite_check.py --import-report Saved/ArtDump.json` on the 5 anchors prints errors=0 (pasted)<br>`grep -c VERIFY pipeline/art/import-rules.md` prints 0 |
| 0.5 | Test harness pattern | Gameplay Dev | Dev Lead | `Source/UmbrellaElla/Private/Tests/Meta/**`, `Source/UmbrellaElla/Private/Tests/Shared/**`, `Source/UmbrellaElla/Private/Tests/Bootstrap/**` | 0.3 | `UmbrellaElla.Meta.SampleRule` (pure function, no world) passes headless through `tools/ue/test.sh`<br>`UmbrellaElla.Meta.World.SampleWorld` passes: it creates a transient world in code (no .umap), spawns a plain stand-in actor (not Ella, so no later gameplay card changes its result), ticks 60 frames at 1/60 s and reads the world time 1.0 s and the actor's tick count 60 from the running world<br>A temporary `UmbrellaElla.Meta.MustFail` is run once and `check_automation_report.py` prints FAIL (pasted); then it is removed<br>`UmbrellaElla.Bootstrap.Placeholder` is removed; `tools/ue/test.sh` without `--bootstrap` prints PASS tests=2. Later cards copy this pattern |
| 0.5a | Audio telemetry | Gameplay Dev | QA and Build | `Source/UmbrellaElla/Private/Audio/**` | 0.5 | One C++ file pair under `Source/UmbrellaElla/Private/Audio/` prints every `AUDIO:` line in `pipeline/audio/audio-rules.md` section 3 (category `LogUmbrellaElla`); feature cards call it and never format lines<br>An automation test calls it once per event and `python3 tools/audio_check.py --log` on that test's log prints PASS (pasted)<br>On a packaged Development run, the `master_peak`, `voices` and `voice` values come from the master submix and the audio device, not constants (log lines pasted) |
| 0.5b | Owl data types and Owl tests | Gameplay Dev | Dev Lead | `Source/UmbrellaElla/Public/Owl/**`, `Source/UmbrellaElla/Private/Owl/**`, `Source/UmbrellaElla/Private/Tests/Owl/**`, `pipeline/qa/test-map.md` | 0.5 | `UOwlPatternData` and `UOwlPhaseData` primary data assets exist with the fields listed in `pipeline/level/encounter.md`<br>`tools/ue/test.sh --require UmbrellaElla.Owl.EveryPatternHasTelegraph --require UmbrellaElla.Owl.PhaseTableDistinct` prints PASS (pasted). Each test builds its own transient pattern and phase data, so it never passes on zero assets<br>With a planted pattern whose telegraph is 0, `EveryPatternHasTelegraph` FAILS once (pasted), then the plant is removed<br>The three owl world tests belong to the MVP 5 Keeper cards (`pipeline/qa/test-map.md`)<br>The Owl row in `pipeline/qa/test-map.md` (not the Owl phases row) is set to merged with this card's number |
| 0.6 | Smoke hook | Gameplay Dev | Dev Lead | `Source/UmbrellaElla/Private/Smoke/**`, `Source/UmbrellaElla/Private/Tests/Display/**`, `pipeline/qa/test-map.md` | 0.3, 0.8 | `-SmokeQuitAfter=15` on a Development package logs one `SMOKE_OK map=L_Graybox fps=N worst_ms=N commit=SHA input=ok input_vz=N res=WxH win=W view=WxH aspect=N debugdraw=0 textpx=N load_ms=N workbench=0` line per the contract in `tools/ue_run.py` and quits with exit code 0. view= is the measured gameplay view inside the letterbox or pillarbox bars (never computed from the camera's AspectRatio) and debugdraw= is 1 when any debug draw is on (`pipeline/unreal-rules.md` Display). W is windowed or fullscreen. input=ok means it held `IA_Attack` through Enhanced Input and measured Z velocity < 0 within 0.5 s, logged as `input_vz=N` (cm/s) (GDD SH1.0 MOVE-05: with nothing held the umbrella rises, so only descent proves input; the hook reads no state name, so MVP 2 never edits it); until MVP 2 merges (its QA-01 test-map row reads merged), run with SMOKE_REQUIRE_INPUT=0 and paste that setting: `check_pr.py` then accepts input=none<br>At the first gameplay frame it logs one `SMOKE_EFFECTIVE at=start commit=SHA workbench=0 platform=Mac manifest=V FIELD=VALUE ...` line, and the same read as `at=end outcome=...` when the run ends, per the contract in `tools/ue_run.py`: every field of the `UUmbrellaTuning` structs by reflection over the settings object gameplay reads (`UUmbrellaTuning` class default, `pipeline/unreal-rules.md`) and every flag with `manifest=` through the harness seam card 0.3 made (`UHarnessSubsystem::ForEachFlag` and `ManifestVersion()`), never from a header or BUILD_INFO; a card that marks a key or adds a flag never edits the hook. commit= and workbench= are compiled in (`UMBRELLAELLA_BUILD_COMMIT`, stamped by the package script at build start; `pipeline/unreal-rules.md` Smoke hook); `bake_preset.py effective` in the smoke output prints PASS (pasted)<br>It supports `-SmokeMap=/Game/UmbrellaElla/Maps/L_Graybox` (that map loads instead of GameDefaultMap), pasted<br>`-SmokeShot=PNG` writes one whole-window screenshot (bars and UI included) 5 s after the first gameplay frame and logs `SMOKE_SHOT at_s=5 w=W h=H`; `tools/ue/smoke.sh` output shows the `smoke-art: art_check:`, `smoke-art: screen_check:` and `smoke-art: art_judge:` lines for it (pasted)<br>Proof runs FAIL on purpose (pasted): `SMOKE_FORCE_NO_ASPECT=1 SMOKE_RES=2560x1080 tools/ue/smoke.sh EXE` (`-SmokeNoAspectLock` turns the view target camera's aspect constraint off) FAILS on aspect; `SMOKE_FORCE_DEBUGDRAW=1 tools/ue/smoke.sh EXE` (`-SmokeDebugDraw` sets `ue.Debug 1`) FAILS on `debugdraw=1`<br>`UmbrellaElla.Display.World.ViewLocked16x9` and `UmbrellaElla.Display.World.DebugDrawOffByDefault` pass (pasted `PASS  tests=` line) and this PR marks their `pipeline/qa/test-map.md` rows merged<br>`tools/ue/smoke.sh` prints PASS on a real Development package (pasted); it found `BUILD_INFO.txt`, and the `-abslog` game log file exists (paste `ls`); the Win64 smoke is card 0.6w<br>A `-SmokeCrash` switch (non-Shipping only) crashes on purpose: `SMOKE_FORCE_CRASH=1 tools/ue/smoke.sh EXE` FAILS with a new crash folder (pasted)<br>`tools/ue/daily.sh` prints a DAILY line with build, test, package and smoke PASS on a real Development package, run with SMOKE_MIN_TEXT_PX=0 until the first UI card merges (pasted). The Windows daily is card 0.6w; display and verify-tags are card 0.6d. No Shipping smoke (D-new-smoke). Whether 0.6 blocks other gameplay cards is D-new-06-block<br>Runs on: the Mac build machine: a kickoff there (`tools/kickoff.sh`) builds and fixes this card, a kickoff on Windows leaves it waiting (`tools/kickoff.py` RUNS_ON_MAC) |
| 0.6b | Restart-cycle smoke (after the MVP 6 retry card merges) | Gameplay Dev | Dev Lead | `Source/UmbrellaElla/Private/Smoke/Restart/**` | 0.6 | `-SmokeRestartCycles=5` on a Development package logs `SMOKE_CYCLE n=I actors=N health=H load_ms=N` after each fail and restart, 5 lines in total (pasted)<br>`tools\ue\smoke.ps1` with SMOKE_RESTART_CYCLES=5 prints PASS (pasted) |
| 0.6c | Capture switch for the video | Gameplay Dev | Dev Lead | `Source/UmbrellaElla/Private/Smoke/Capture/**` | 0.6 | By G1: `-CaptureMode` on a Development package logs `CAPTURE_MODE hud=off debug=off cursor=off` (pasted)<br>`python3 tools/submission_check.py capture Saved/Logs/capture.log` exits 0 (pasted)<br>A pasted 1920x1080 capture shows no debug text and no cursor |
| 0.6d | Display smoke and open tags (due G3) | QA and Build / TD human | Dev Lead | `tools/**` | 0.6, 0.20, 0.4d, 0.6w | Every `tools/` edit is the agent's gate patch<br>Kickoff applies it itself through the tool checks (`python3 tools/git_gate.py apply UE-0.6d --auto`: every path in the card's lane, no guardrail enforcer changed, no guardrail file loosened; the PR has a `GATE EDIT: by=kickoff` line naming the patched paths)<br>Runs on: the Windows packaging machine: a kickoff there (`tools\kickoff.ps1`) builds and fixes this card, a kickoff elsewhere leaves it waiting (`tools/kickoff.py` RUNS_ON_WINDOWS) (a real display); there `tools\ue\daily.ps1` prints a DAILY line with display PASS on a real Development package at the default SMOKE_MIN_TEXT_PX (pasted); its 1280x800 and 2560x1080 runs log `aspect=1.778` with letterbox and pillarbox bars, and screen_check prints PASS on their screenshots (pasted)<br>`python3 tools/ue_run.py verify-tags` exits 0: each VERIFY tag is removed with its output pasted, or turned into a decision row<br>`-SmokeRestartCycles` is checked on a package once card 0.6b has merged (pasted) |
| 0.6e | Gamepad smoke: a controller shoots, absorbs and pauses in the package (due G1) | Gameplay Dev / playtest lead | QA and Build | `Source/UmbrellaElla/Private/Smoke/**`, `Source/UmbrellaElla/Private/Tests/Smoke/**`, `Content/UmbrellaElla/Input/**`, `pipeline/qa/test-map.md` | 0.6 | The smoke hook feeds raw gamepad keys (Gamepad_LeftX=+1, Gamepad_RightTriggerAxis, Gamepad_LeftTriggerAxis) into the local player's input as a gamepad device, never the actions, and adds `gamepad=ok gp_vx=N gp_attack_vz=N gp_shield_vz=N` to the SMOKE_OK line (`tools/ue_run.py` contract; gp_shield_vz is the Absorb descent (L2 / LT, MOVE-05); it reads none until the MVP 2 card merges)<br>The `IMC_*` assets map every gamepad input GDD SH1.0 MOVE-04..MOVE-09 names (left stick trim, R2 shoot, L2 absorb, Cross / A hop, L1 / R1 dash, Triangle / Y ride, right stick spells, Options / Menu pause, confirm retry) beside keyboard and mouse (mapping list pasted)<br>`UmbrellaElla.Smoke.GamepadReachesMoveAttackShield` passes (pasted `PASS  tests=` line), and this PR marks the QA-GP row in `pipeline/qa/test-map.md` merged, which ends the `SMOKE_REQUIRE_GAMEPAD=0` waiver<br>`tools/ue/smoke.sh` on a Mac Development package prints `smoke: exit=0 SMOKE_OK=yes` with gamepad=ok, gp_vx above 0 and gp_attack_vz below 0 (pasted), and FAILS once with the gamepad mappings removed from the IMC on purpose (pasted)<br>Runs on: the Mac build machine: a kickoff there (`tools/kickoff.sh`) builds and fixes this card, a kickoff on Windows leaves it waiting (`tools/kickoff.py` RUNS_ON_MAC); the smoke feeds the raw gamepad keys as a gamepad device, so no person plays this card. The Win64 gamepad smoke is card 0.6w |
| 0.6w | Windows smoke, gamepad smoke and daily (the Windows packaging machine) | QA and Build / packaging machine owner | Dev Lead | `Config/Windows/**`, `Source/UmbrellaElla/Private/Platform/Windows/**` | 0.3w, 0.6, 0.6e | Runs on: the Windows packaging machine: a kickoff there (`tools\kickoff.ps1`) builds and fixes this card, a kickoff elsewhere leaves it waiting (`tools/kickoff.py` RUNS_ON_WINDOWS); nothing on the Mac G1 path lists this card in After, so it never holds up G1<br>`tools\ue\package.ps1` exits 0 (its `package exit: 0 ... platform=Win64` line pasted) and `tools\ue\smoke.ps1 -Exe EXE` on that package prints `smoke: exit=0 SMOKE_OK=yes` with a `SMOKE_EFFECTIVE ... platform=Windows` line (pasted)<br>The same smoke shows gamepad=ok with gp_vx above 0 and gp_attack_vz below 0 on the Win64 package (pasted)<br>`$env:SMOKE_FORCE_CRASH=1; tools\ue\smoke.ps1 -Exe EXE` FAILS with a new crash folder (pasted)<br>`tools\ue\daily.ps1` prints a DAILY line with build, test, package and smoke PASS on a real Development package (pasted); from then on kickoff's QA and Build session runs it on each merge while `native_windows_shell` is allow (`tools/kickoff.py` windows_daily) |
| 0.7 | Measure the palette | Art Director / TD human | Technical Director | `pipeline/art/style.json`, `pipeline/art/reference/**` | – | The Art Director agent measures the key art (`art_check.py --measure-palette`) and writes the `style.json` values as the card's gate patch, measurements pasted (no art sign-off: the art gate is automated; `style.json` stays a guardrail file)<br>Kickoff applies it itself through the tool checks (`python3 tools/git_gate.py apply UE-0.7 --auto`: every path in the card's lane, no guardrail enforcer changed, no guardrail file loosened; the PR has a `GATE EDIT: by=kickoff` line naming the patched paths)<br>`python3 tools/art_check.py --references` exits 0: every required picture in `pipeline/art/references.json` is present (pasted)<br>`git lfs ls-files` lists `pipeline/art/reference/target-keyart.png`<br>`art_check.py --extract` output pasted; palette replaced with measured values and `palette_status: measured`<br>`paper_texture_min` set to half the reference's measured `paper_texture` (about 0.38), so a near-flat frame fails<br>`python3 -m unittest tests.test_art_check` prints OK with 0 skipped (ReferenceCalibrationTests ran)<br>The key art still passes with the measured palette: `python3 tools/art_ref_check.py --card 0.10 --scene pipeline/art/reference/target-keyart.png` prints PASS (pasted) |
| 0.8 | Graybox arena | Integrator / integration owner | Dev Lead | `Content/UmbrellaElla/Maps/L_Graybox.umap`, its `+MapsToCook` line in `Config/DefaultGame.ini`, `Content/UmbrellaElla/Blueprints/BP_Ella.uasset`, `Content/UmbrellaElla/Blueprints/BP_GameMode.uasset` | 0.3 | L_Graybox is one screen with a fixed camera: top and side bounds, a bottom exit volume, a hero start and a Keeper placeholder in the 1920 x 1080 cm Keeper arena (`docs/feature-manifest.json` approved_parameters.fixtures, D-new-sh10-units; `pipeline/level/encounter.json` arena)<br>The placed arena camera (the GameMode's view target) has Constrain Aspect Ratio on and Aspect Ratio 1.777778, so any other window ratio shows black letterbox or pillarbox bars (GDD SH1.0 Keeper fight: fixed 16:9, D-new-sh10-camera; `pipeline/unreal-rules.md` Display), and no collision or hitbox component is visible in game (property values pasted)<br>`+MapsToCook=(FilePath="/Game/UmbrellaElla/Maps/L_Graybox")` is in `Config/DefaultGame.ini`<br>`BP_Ella` (parent `AEllaCharacter`) sets the `IA_*` and `IMC_*` references, and `BP_GameMode` sets DefaultPawnClass to `BP_Ella`. L_Graybox's World Settings GameMode Override is `BP_GameMode` (property values pasted)<br>A Development package opens it: `grep -c L_Graybox` on the packaged run's log prints 1 or more (pasted). If card 0.6 has not merged yet, the PR uses the same `SMOKE_BOOTSTRAP` line as card 0.3; once it has, it pastes SMOKE_OK (input=none with `SMOKE_REQUIRE_INPUT=0` only until MVP 2's QA-01 row is merged) |
| 0.8a | Owl dump and arena eval cameras | Integrator / integration owner | Dev Lead | `pipeline/unreal/editor_scripts/dump_owl.py`, `Content/UmbrellaElla/Maps/L_Graybox.umap` | 0.5b, 0.8, 0.12 | The editor script writes every `DA_OwlPattern_*` and `DA_Phase_*` as JSON in the `encounter.json` shape. No owl assets exist yet (card 0.8b makes them)<br>On the empty dump, `python3 tools/encounter_check.py --data` FAILS with E28 (pasted): the dump path works end to end. The 0 problems line is card 0.8b's<br>`-EvalCam=CAM_Eval_Arena` and `-EvalCam=CAM_Eval_Stress` each log `EVALCAM_OK` (pasted) |
| 0.8b | Encounter data v1 matches assets | Level Designer | Game Designer | `pipeline/level/encounter.json`, `pipeline/level/encounter.md`, `Content/UmbrellaElla/Data/Owl/**` | 0.8a | The assets equal the GDD SH1.0 Keeper fight in the `GDD-SH1.0` baseline preset (`pipeline/level/encounter.json`): wings 180, mechanisms 100 / 110 / 120, clock 320 HP; red fans, yellow packets, gust, talon, three casts, double beat; every number in its numbers_from_gdd<br>`python3 tools/encounter_check.py` prints `encounter_check: 0 problem(s)` (pasted)<br>`python3 tools/encounter_check.py --data` on the card 0.8a dump prints `encounter_check: 0 problem(s)` (pasted)<br>The card has a `Coverage signed:` line with a name and date<br>The tells are data on this card, checked by the two runs above (S6 telegraph, S11 art and sound ids, and the same rules on the asset dump); the card puts nothing on screen, so it has no capture for an art review and its one reviewer is the Game Designer |
| 0.9 | Pipeline smoke on every machine | QA and Build / human Producer | Dev Lead | `scratch/**` on a branch `ue-0.9-NAME` that is never merged | 0.3, 0.17 | kickoff runs this card's session on the machine it runs on (`tools/kickoff.sh`, Windows `tools\kickoff.ps1`); the session does every line below<br>`python3 tools/pipeline_check.py` and `python3 tools/affected_tests.py --run tools/kickoff.py tools/check_card.py` exit 0 on each machine (the kickoff and card tests, a 5-minute target; the full suite is CI's), or the error is posted<br>`gh issue view --comments` on the card 0.9 issue shows 1 comment per machine, written by that machine's session: machine, OS, `Engine/Build/Build.version`, results, blockers<br>Each machine's session opens 1 PR from a trivial card and `check_pr.py` exits 0 on it in CI<br>Done by the Clock's card 0.9 cutoff. A teammate whose build is not green by then takes only non-C++ cards (D24); the Producer agent posts it on the tracker |
| 0.10a | Swatch and locked post-process | Integrator / TD human | Art Director | `Content/UmbrellaElla/Maps/L_StyleFrame.umap`, its `+MapsToCook` line in `Config/DefaultGame.ini`, its row in `pipeline/qa/no-player-maps.txt`, `pipeline/art/style.json` `unreal_import.texture.mips` (a gate file: the card's gate patch), `Content/UmbrellaElla/Art/Swatch/**`, `Art/Source/Swatch/**` | 0.8, 0.12 | Before the swatch import (the first art import), the agent sets `pipeline/art/style.json` `unreal_import.texture.mips` from D13, or D13's default (`mips`, 2x with mipmaps) while it is open, in the card's gate patch: `tests/test_sprite_check.py` fails once L_StyleFrame exists with it still null<br>Kickoff applies it itself through the tool checks (`python3 tools/git_gate.py apply UE-0.10a --auto`: every path in the card's lane, no guardrail enforcer changed, no guardrail file loosened; the PR has a `GATE EDIT: by=kickoff` line naming the patched paths)<br>The swatch sprite made by `python3 tools/make_art_calibration.py --swatch` is imported and placed in front of `CAM_Eval_Swatch` in L_StyleFrame, with its `+MapsToCook` line and an `L_StyleFrame` row (card 0.10a, style frame, no player) in `pipeline/qa/no-player-maps.txt` (the daily smokes every cooked map; a map with no player logs input=none)<br>The post-process volume is set as `pipeline/art/art-bible.md` locks it (values pasted)<br>`python3 tools/art_check.py --swatch` on the `-EvalCam=CAM_Eval_Swatch` capture prints PASS (pasted) |
| 0.10b | Anchor sprites | Asset Specialist / TD human | Art Director | `Art/Source/Anchors/**`, `Content/UmbrellaElla/Art/Anchors/**`, `pipeline/art/provenance.csv`, `.github/workflows/pipeline-checks.yml` (sprite step) | 0.7, 0.10a | Five anchors are imported at the card 0.3 Pixels Per Unreal Unit: Ella open, Ella closed, the owl, one clockwork bolt, the paper layer<br>Each source PNG under `Art/Source/Anchors/` has a `.sprite.json` sidecar (frame grid and pivot from the `layout` entries of `pipeline/art/references.json`, SpriteLayout.json and Asset Notes.md; drawn new, never copied from a reference) and `python3 tools/sprite_check.py --scan Art --require-dir` prints 0 problems (pasted)<br>`--require-dir` on the CI sprite step is the card's gate patch<br>Kickoff applies it itself through the tool checks (`python3 tools/git_gate.py apply UE-0.10b --auto`: every path in the card's lane, no guardrail enforcer changed, no guardrail file loosened; the PR has a `GATE EDIT: by=kickoff` line naming the patched paths)<br>Each has a provenance row<br>Round trip on one anchor: edit its layered source (one visible change), re-export, Reimport over the same `T_`/`SPR_` asset; `--import-report` errors=0 and `--sources Content/UmbrellaElla/Art Art/Source` PASS pasted, the map still loads, and the minutes it took are pasted. Over 10 min: the TD files a card for a one-command reimport + check + capture loop<br>Each anchor is generated with `python3 tools/assetgen.py image` and is an art-loop piece (`python3 tools/art_loop.py pieces --card 0.10b`): kickoff runs builder and blind-critic rounds until it reaches the bar, and this PR pastes, for this commit, `python3 tools/art_ref_check.py --card 0.10b --element ID FILES` PASS and the `art_loop: PASS card=0.10b piece=...` line of each piece (`python3 tools/art_loop.py evidence --card 0.10b`). No human approves the look; the stuck rule (3 rounds with no improvement) raises NEEDS HUMAN |
| 0.10 | Style frame: the key-art scene, the first visual milestone (D-new-port-9) | Integrator / integration owner | Art Director | `Content/UmbrellaElla/Maps/L_StyleFrame.umap`, `pipeline/art/references.json` (scene thresholds only) | 0.10a, 0.10b, 0.10c, 0.4d, 0.12 | L_StyleFrame rebuilds `pipeline/art/reference/target-keyart.png` at the gameplay camera (art-bible Target frame) from the anchors and the card 0.10c art: owl large on the right with the chest clock gold, Ella small on the left, the skyline, wind lines, a harmless wind current (WIND-03), red and yellow shots and Small Blasts pulses, with a `CAM_Eval_StyleFrame` camera<br>Captured with `-EvalCam=CAM_Eval_StyleFrame` from a Development package at 1920x1080: `art_check.py` and `screen_check.py` print PASS on it, and the full frame is an art-loop piece (`python3 tools/art_loop.py pieces --card 0.10`): kickoff runs builder and blind-critic rounds until it reaches the bar, and this PR pastes, for this commit, `python3 tools/art_ref_check.py --card 0.10 --scene CAPTURE` PASS and the `art_loop: PASS card=0.10 piece=...` line of each piece (`python3 tools/art_loop.py evidence --card 0.10`). No human approves the look; the stuck rule (3 rounds with no improvement) raises NEEDS HUMAN<br>`python3 tools/art_check.py --gate` on that `CAM_Eval_StyleFrame` capture prints `ART_GATE: PASS` (numeric check, every `pipeline/art/references.json` picture present, the calibrated judge, and the blind X/Y row against the key art; pasted).<br>Pixels Per Unreal Unit confirmed: Ella is 80–100 px tall in the 1080p capture (D-new-port-10). A different value goes to a TD card, and the anchors are re-imported before any other asset card<br>If the key art itself fails a `scene` threshold in `pipeline/art/references.json`, or the capture passes by a wide margin, the thresholds are recalibrated on it in this PR and `python3 -m unittest tests.test_art_judge` prints OK (pasted). The Art Director's follow-up card adds the capture to `evals/art-judge/anchors/` (the G2 anchor) in a gate patch. No other asset cards before this |
| 0.10c | Scene and gameplay-zone art | Asset Specialist / integration owner | Art Director | `Art/Source/Scene/**`, `Content/UmbrellaElla/Art/Scene/**`, `pipeline/art/provenance.csv` | 0.10b, 0.4d | `python3 tools/assetgen.py image` makes 3 or more candidates each for the skyline layer, the decorative wind lines, the WIND-03 current and the Small Blasts pulse into `Art/Source/Scene/Raw/`, each with its provenance row<br>Each of skyline, wind-lines, wind-zone and wand-shot (the Small Blasts pulse) is an art-loop piece (`python3 tools/art_loop.py pieces --card 0.10c`): kickoff runs builder and blind-critic rounds until it reaches the bar, and this PR pastes, for this commit, `python3 tools/art_ref_check.py --card 0.10c --element ID FILES` PASS and the `art_loop: PASS card=0.10c piece=...` line of each piece (`python3 tools/art_loop.py evidence --card 0.10c`). No human approves the look; the stuck rule (3 rounds with no improvement) raises NEEDS HUMAN<br>The wind zone follows the art-bible Gameplay zones rule: `python3 tools/screen_check.py` on a 1920x1080 preview of the picked zone over the paper anchor prints PASS with flat=0 grey=0 (pasted), and the wind-zone pick is a different file from the wind-lines pick<br>Each picked sheet has a `.sprite.json` sidecar and `python3 tools/sprite_check.py --scan Art/Source/Scene` prints PASS (pasted)<br>Imported into `Content/UmbrellaElla/Art/Scene/`: `python3 tools/sprite_check.py --import-report Saved/ArtDump.json` prints errors=0 (pasted) |
| 0.11 | Spike cards for open decisions | Producer | Technical Director | GitHub only | – | `gh issue list --label spike` lists 3 issues, one per open row whose test is due by G2: D3, D4, D13<br>`python3 tools/check_card.py` exits 0 on each before it starts. The spike check needs a `Decision row:` line, `Decides it:` as "if X, pick A", and `Time box:` of at most 60 min (`pipeline/templates/spike-card.md`) |
| 0.12 | Eval camera switch | Gameplay Dev | Dev Lead | `Source/UmbrellaElla/Private/Smoke/EvalCam/**` | 0.6 | `-EvalCam=CAM_Eval_Arena` (any CameraActor name) on a Development package views from that camera, runs `HighResShot 1920x1080`, logs `EVALCAM_OK cam=CAM_Eval_Arena file=PATH` and exits 0<br>A camera name that is not in the map logs an Error naming it and the run exits 1 (pasted)<br>The switch is compiled only when `!UE_BUILD_SHIPPING` (`pipeline/unreal-rules.md`, eval cameras) |
| 0.13 | Movement envelope test (after the MVP 2 movement cards merge) | Gameplay Dev | Dev Lead | `Source/UmbrellaElla/Private/Tests/Move/**` | 0.5 | `UmbrellaElla.Move.World.FeelEnvelope` passes headless and logs the `FEEL_ENVELOPE` line in `docs/feel-spec.md` section 7 (pasted)<br>`python3 tools/encounter_check.py --envelope` on that line prints `envelope_check: 0 problem(s)`: the game matches `feel.json`, so the encounter sim uses the game's numbers (pasted)<br>Each value is read from the running world, not computed from the tuning structs<br>The test-map row for `UmbrellaElla.Move.World.FeelEnvelope` is set to merged with this card's number |
| 0.14 | Balance targets | Game Designer | Producer | `docs/balance.md` | 0.13 | The Game Designer agent proposes every target in `docs/balance.md` from the 0.13 envelope<br>The Game Designer agent marks each Status cell in the targets table `accepted (agent default)` and adds one DECIDED row for them (dated, `agent default; Game Designer; the team may override`) (`grep -cE 'proposed [[:punct:]]$' docs/balance.md` prints 0)<br>The envelope table holds the 0.13 output line and its commit |
| 0.14b | Yellow catch, heal and wind feedback (before the MVP 4 absorption card) | Audio | UI and UX | `pipeline/audio/sound-list.csv` (rows below), `pipeline/ui/signals.json` (rows below), `Audio/Source/ShieldCatch/**`, `Audio/Source/ShieldHeal/**`, `Audio/Source/GustCatch/**` | 0.4c | Sound-list rows ShieldCatch and ShieldHeal (the yellow catch and heal, P0, GDD SH1.0 UMB-05, FLOW-32) and GustCatch (the safe current, P0, WIND-03) keep their fallback paths; `python3 tools/audio_check.py --list` prints PASS (pasted)<br>`pipeline/ui/signals.json` rows shield-catch, shield-heal and wind-enter name those sounds and a visual (catch flash, wear steps back, wind boundary lines); `python3 tools/ui_check.py signals` prints PASS (pasted)<br>`SW_ShieldCatch_00.wav`, `SW_ShieldHeal_00.wav` and `SW_GustCatch_00.wav` pass `python3 tools/audio_check.py --scan Audio/Source` (pasted)<br>The MVP 4 absorption card (UMB-05, SURV-05) lists this card in After; a full-health catch plays ShieldCatch only (FLOW-32) |
| 0.15 | Fallback CC0 art and audio set (D-new-fallback) | Asset Specialist | Art Director | `pipeline/art/fallback-cc0.csv`, `pipeline/art/fallback/**`, `pipeline/art/provenance.csv` | 0.2 | `pipeline/art/fallback-cc0.csv` has 21 rows: 14 sounds, one at each `fallback` path in `pipeline/audio/sound-list.csv` (under `pipeline/art/fallback/audio/`: WandBolt, OwlBoltWindup, OwlBoltLaunch, GustWindup, ArcWindup, HitOwl, PlayerHurt, ShieldCatch, ShieldHeal, UmbrellaOpen, UmbrellaClose, EndEvent, PhaseChime, GustCatch), and 7 placeholder sprites (the art lane sets which)<br>`python3 tools/audio_check.py --list --release` prints PASS (pasted)<br>`python3 tools/audio_style_check.py check pipeline/art/fallback/ --ids WandBolt,OwlBoltLaunch,GustWindup,HitOwl,PlayerHurt,ShieldCatch,ShieldHeal,UmbrellaOpen,UmbrellaClose,EndEvent,PhaseChime,GustCatch` prints `audio_style check: PASS files=12` or more (pasted): the measured bar stands in for a listen (OwlBoltWindup and ArcWindup are cut rows with no style family)<br>`grep -c CC0 pipeline/art/provenance.csv` prints 21 or more: each fallback file has a provenance row with its licence URL<br>Each file is listed in `docs/pre-jam-declaration.md` if picked before Nov 12. The files stay out of `Content/` until the art-or-audio risk in `docs/jam-brief.md` fires |
| 0.16 | Install the scheduled clock run (D-new-schedule, D-new-clock-install) | Agent Ops / TD human | Producer | `.github/workflows/clock.yml` | 0.0, 0.1 | The agent writes `.github/workflows/clock.yml` as the card's gate patch; `cmp pipeline/templates/clock-workflow.yml .github/workflows/clock.yml` exits 0 (an exact copy)<br>Kickoff applies it itself through the tool checks (`python3 tools/git_gate.py apply UE-0.16 --auto`: every path in the card's lane, no guardrail enforcer changed, no guardrail file loosened; the PR has a `GATE EDIT: by=kickoff` line naming the patched paths)<br>After the merge kickoff sets the repo variables itself (`gh variable set`, `tools/kickoff.py` repo_settings; an agent session never does) and posts the read-back on the card: `gh variable list` shows PIPELINE_CLOCK=on and TRACKER_ISSUE set to the card 0.1 tracker number<br>After kickoff's `gh workflow run clock`, `gh run list -w clock` lists 1 run or more that is not `skipped`; its link is posted on the tracker<br>Done by the Clock's card 0.9 cutoff |
| 0.17 | Install agent settings | Agent Ops / TD human | Technical Director | `.claude/**`, `.gitignore` | 0.0 | The agent makes the `.gitignore` lines and the `.claude/` files `python3 tools/secrets_check.py --install` writes, as the card's gate patch<br>Kickoff applies it itself through the tool checks (`python3 tools/git_gate.py apply UE-0.17 --auto`: every path in the card's lane, no guardrail enforcer changed, no guardrail file loosened; the PR has a `GATE EDIT: by=kickoff` line naming the patched paths); `python3 tools/secrets_check.py --rules secret,secretfile,gitignore,settings,agents` exits 0 on the branch (pasted). Rules `mcp` and `components` are card 0.4a's<br>After the merge kickoff sets branch protection on `main` itself (required status check `checks`, the job name in `pipeline-checks.yml`, the `card` job runs on issues only; no force push, no delete; no required review: the card's reviewer agent approves and kickoff merges) and lets GitHub Actions create pull requests (`main-red.yml` opens revert PRs), and posts the `gh api` read-back on the card (`tools/kickoff.py` repo_settings)<br>`python3 tools/install_git_hooks.py --check` exits 0 on every clone: kickoff installs the hooks on each machine it runs on, and each card 0.9 session pastes the check on the card 0.9 smoke issue<br>Each card 0.9 session pastes `python3 tools/secrets_check.py --rules settings,agents` from its machine on the card 0.9 smoke issue (`pipeline/agent-ops/README.md`)<br>Done by the Clock's card 0.9 cutoff |
| 0.18 | Guardrail rehearsal | Agent Ops / TD human | QA and Build | `scratch/**` on a branch `ue-0.18-rehearsal` that is never merged, `pipeline/agent-ops/` ([VERIFY] tags only) | 0.17, 0.3 | One fake card, run by the Agent Ops agent in a sandboxed session, hits every block and ask in `pipeline/agent-ops/README.md` (pastes on the card; an ask nobody answers counts as refused)<br>`prompt_log.py attempts --card 0.18` exits 1 after two planted build failures (pasted)<br>A sandboxed role session posts one `gh issue comment` on this card, so the `~/.config/gh` read deny does not block `gh` (pasted)<br>Each `VERIFY on 0.18` tag is removed in the card's gate patch with its paste<br>Kickoff applies it itself through the tool checks (`python3 tools/git_gate.py apply UE-0.18 --auto`: every path in the card's lane, no guardrail enforcer changed, no guardrail file loosened; the PR has a `GATE EDIT: by=kickoff` line naming the patched paths); `grep -rI "VERIFY on 0.18" pipeline/agent-ops` prints 0 lines (exit 1)<br>Done by the Clock's card 0.9 cutoff |
| 0.19 | Theme fit (Nov 11, 1 hour) | Game Designer | Producer | `docs/jam-brief.md` Theme lines | – | Within 1 hour of the kickoff, 3 one-paragraph pitches that tie the umbrella-and-owl encounter to the theme (DEC-10) are on the tracker<br>The Game Designer agent picks one by the pitches' fit to DEC-10 and records it as a DECIDED row (theme pick; dated, `agent default; Game Designer; the team may override`) linked on the tracker<br>`Theme:` and `Theme in game:` lines are filled in `docs/jam-brief.md`, and `python3 tools/submission_check.py theme` exits 0 (pasted)<br>The theme reaches the GDD with its next published revision (`docs/gdd/README.md`); this card does not wait for it<br>`python3 tools/check_pr.py` exits 0 on the PR |
| 0.20 | UI string table, text styles and DPI rule | Technical Director | UI and UX | `Content/UmbrellaElla/UI/ST_UI.csv`, `Content/UmbrellaElla/UI/text-styles.csv`, `Config/DefaultEngine.ini` | 0.3 | `python3 tools/ui_check.py strings`, `fonts` and `config` exit 0 (pasted)<br>The table imports in 5.8.4 (editor log line pasted)<br>`python3 tools/story_check.py --scan Content/UmbrellaElla/UI/ST_UI.csv` prints PASS (pasted; the placeholder text has no deny-list name or off-tone word, and card 0.30 writes the final words) |
| 0.21 | Menu and settings C++ | Gameplay Dev | Dev Lead | `Source/UmbrellaElla/Public/UI/**`, `Source/UmbrellaElla/Private/UI/**`, `Source/UmbrellaElla/Private/Tests/UI/**`, `Source/UmbrellaElla/Private/Smoke/**` | 0.20, 0.6 | The C++ behind the Start (Start Game, Start Director's Cut), pause (Continue, Settings, Quit), settings, win ending and fail screens in `pipeline/ui/menus.md` (no `WBP_*` assets)<br>Master volume: `FUITuning::MasterVolume` in `Public/UI/UITuning.h` defaults to 80 (pipeline default; GDD SH1.0 FLOW-37 prints only the 0-100 range) on a line ending `// bake: FLOW-37.master_volume`, the game applies it to `SM_Master` at startup, and `python3 tools/bake_preset.py defaults` prints PASS (pasted)<br>With `-SmokeQuitAfter`, the smoke hook passes the title through the title's own Play path (the function the Play button calls) before its input check and logs `SMOKE_TITLE skipped=FUNCTION`; `tools/ue/smoke.sh` on GameDefaultMap still prints input=ok (pasted)<br>`UmbrellaElla.Flow.TitleToPlayToWinEnding` (in `Tests/UI/`) passes, and its test-map row is set to merged with this card's number (the card whose lane holds the test owns it)<br>`check_automation_report.py --require $(python3 tools/ui_check.py tests)` prints PASS for the P0 UI tests (pasted)<br>`check_automation_report.py --require UmbrellaElla.Flow.World.MenuBlocksGameplayInput` prints PASS (pasted)<br>Settings remaps keyboard and mouse and the controller, and the tutorial can be skipped (`pipeline/ui/menus.md` Required screens): `check_automation_report.py --require UmbrellaElla.UI.World.RemapUpdatesPrompt --require UmbrellaElla.UI.World.RemapGamepadUpdatesPrompt --require UmbrellaElla.UI.World.TutorialSkipReachesPlay --require UmbrellaElla.UI.World.TutorialShowsControlGlyphs` prints PASS (pasted); a garbage `GameUserSettings.ini` falls back to 1920x1080 (`UmbrellaElla.Settings.BadIniFallsBackToDefaults` asserts it) |
| 0.21b | Menu layouts | Integrator / integration owner | UI and UX | `Content/UmbrellaElla/UI/**` | 0.21 | Start, pause, settings, win ending and fail `WBP_*` screens as in `pipeline/ui/menus.md`, bound to the card 0.21 C++<br>A UIFLOW line passes `python3 tools/ui_check.py flow-check` (pasted)<br>The `Theme in game:` line in `docs/jam-brief.md` shows on the Start or win ending screen (1080p capture pasted)<br>HUD and pause stay inside the 16:9 view: `python3 tools/screen_check.py` prints PASS with `bars=pillarbox` on a 2560x1080 windowed screenshot of each (a widget in the bars breaks the bars and FAILS), pasted<br>A 1920x1080 capture of the HUD over play passes `python3 tools/art_ref_check.py --card 0.21b --scene CAPTURE` (the HUD keeps the key-art look; PASS line for this commit pasted)<br>Each tutorial screen shows keyboard and gamepad glyphs in our style, no placeholder dots or boxes: `python3 tools/screen_check.py --strict` prints PASS on a 1080p capture of each (pasted), and a UIFLOW line with `tutorial-skip pass` and `remap-gamepad pass` passes `python3 tools/ui_check.py flow-check` (pasted)<br>Each menu screen and transition meets the menu style bar (`pipeline/ui/menus.md` Menu look): it is an art-loop piece `menu-screen`, judged blind against the brand references and the written menu target until the critic cannot pick them over ours; the `art_loop: PASS card=0.21b piece=...` lines for this commit are pasted (`python3 tools/art_loop.py evidence --card 0.21b`) |
| 0.22 | Capture boxes, G2 set | UI and UX | Art Director | `pipeline/ui/captures/**` | 0.21b, 0.12 | `boxes.json` for HUD and pause at 1.0 and at 2.0, and `swatches.json` for `CAM_Eval_Stress`<br>`python3 tools/ui_check.py contrast`, `layout --scale 2` and `grayscale` exit 0 on them (pasted) |
| 0.23 | Run logger | Gameplay Dev | Dev Lead | `Source/UmbrellaElla/Private/RunLog/**` | 0.5 | `UmbrellaElla.Flow.RunLogWritesRow` passes headless: one hit, one fail and one survive each write one row with the columns in `pipeline/qa/playtests.md`<br>A packaged Development run writes the CSV; `python3 tools/encounter_check.py --playtest Saved/Playtest/run.csv` exits 0 on it (pasted), and its real path replaces the [VERIFY] in `pipeline/qa/playtests.md` |
| 0.24 | Video cut (G3-G4) | Asset Specialist | Producer | `pipeline/submission/video-plan.md`, `pipeline/submission/footage.md` | 0.6c | The 30-60 s cut follows `pipeline/submission/video-plan.md`; gameplay shows in the first 5 s<br>`python3 tools/submission_check.py video Saved/Video/cut.mp4` and `loudness Saved/Video/cut.mp4` exit 0 (pasted)<br>A human watches the cut and writes the VIDEO line; `python3 tools/submission_check.py signoff` on it exits 0 (pasted)<br>`python3 tools/submission_check.py footage --final` exits 0 (pasted) |
| 0.25 | Workbench sample: flags, reset, logging on synthetic objects (pre-jam) | Technical Director | Dev Lead | `Samples/Workbench/**`, `docs/pre-jam-declaration.md` | – | `Samples/Workbench/README.md` holds the repeatable commands that made the sample project; `PROJECT=Samples/Workbench/Workbench.uproject tools/ue/build.sh` exits 0 on 5.8.4 (log tail pasted)<br>`grep -rli -e umbrella -e owl Samples/Workbench` prints nothing (exit 1): synthetic objects only (moving boxes, a spawner, a damage volume), no game content before the start (GDD SH1.0 ART-03)<br>Feature flags come from one data asset in the `docs/feature-manifest.json` shape and load at scenario reset: three synthetic flags, B requires A, C conflicts with A [VERIFY data asset load on 5.8.4]<br>`PROJECT=Samples/Workbench/Workbench.uproject TEST_FILTER=Workbench tools/ue/test.sh` prints PASS with `Workbench.Flags.RequiresBlockedWithReason`, `Workbench.Flags.ConflictNeedsReset`, `Workbench.Flags.ChangeAppliesAtReset` and `Workbench.Reset.ClearsSpawnedAndTimers` (0 spawned objects and 0 active timers after one reset), pasted<br>A planted flag that requires an unknown ID makes `Workbench.Flags.ManifestResolves` FAIL once (pasted), then the plant is removed<br>Every synthetic feature (moving boxes, spawner, damage volume, gravity) has a workbench toggle, and every one is off by default: `Workbench.Flags.AllOffByDefault` passes, and FAILS once with one default flipped on purpose (both pasted)<br>Debug toggles for testers, each off by default and only inside `#if UMBRELLAELLA_WORKBENCH`: `dbg.no_ground_death` (off = a body that hits the damage floor dies; on = it lands and lives), `dbg.hover` (no-fall: a falling body holds its height and still steers sideways), `dbg.health_bars` (a numbered `HP cur/max` bar over every damageable object). `Workbench.Debug.GroundDeathToggle`, `Workbench.Debug.HoverHoldsHeight` and `Workbench.Debug.HealthBarsShowNumbers` pass (pasted)<br>Every event logs one line with frame, source ID, target ID and run ID (GDD SH1.0 CORE-05), 3 lines pasted<br>All workbench code sits inside `#if UMBRELLAELLA_WORKBENCH` (D-new-workbench-debug) so card 0.27 ports it as is: a sample build with the switch at 0 compiles and its log has no `WORKBENCH_ON` line; at 1 it logs `WORKBENCH_ON debug=1` (both pasted)<br>The sample is listed in `docs/pre-jam-declaration.md` |
| 0.26 | Workbench presets, seed, scenarios and note export (pre-jam) | Technical Director | Dev Lead | `Samples/Workbench/**` | 0.25 | `Workbench.Presets.LoadSetsFlagsAndParams` passes: a synthetic preset in the `pipeline/qa/presets.json` shape sets its flags and parameters and logs 1 `TestPresetLoaded` event<br>Each run logs one `RUN build=SHA manifest=VER preset=ID seed=N` line; `Workbench.Seed.SameSeedSameOrder` passes: two runs with seed 7 log the same event order<br>`Workbench.Params.ClampToRange` passes: a parameter set outside its safe range is clamped and logged<br>Every synthetic tunable (speeds, gravity, spawn rate, damage, health) has a slider with its min, max and step and starts at its default: `Workbench.Params.EveryTunableHasRange` passes (pasted)<br>`Workbench.Scenario.StartsAtTemplatePoint` passes: one scenario template sets start position, spawn pattern and seed<br>The note export writes JSON in the `pipeline/templates/test-note.md` shape: `python3 tools/manifest_check.py --note Saved/Workbench/note.json` exits 0 on it, and exits 1 on a copy with a rating of 6 (both pasted)<br>The config export writes `Saved/Workbench/config-T-01.json` (one file per preset ID) in the bake shape (`tools/bake_preset.py`): `python3 tools/bake_preset.py validate --shape-only` exits 0 on it, and 1 on a copy with a text param value (both pasted)<br>`grep -rli -e umbrella -e owl Samples/Workbench` prints nothing (exit 1) |
| 0.27 | Workbench in the game build (Director's Cut Game Options, FLOW-38, FLOW-44) | Gameplay Dev | Dev Lead | `Source/UmbrellaElla/Public/Harness/**`, `Source/UmbrellaElla/Private/Harness/**`, `Source/UmbrellaElla/Private/Tests/Harness/**`, `pipeline/qa/test-map.md`, `pipeline/qa/baked.json` | 0.3, 0.5, 0.26 | The 0.25-0.26 harness code is ported into `Harness/`, filling the seam card 0.3 made (flag table, `GManifestVersion` = the manifest's `manifest_version`; the smoke hook enumerates both, so this card never edits `Smoke/`), with one flag per manifest record that has a flag, each at its manifest default: `UmbrellaElla.Harness.FlagsMatchManifest` passes, and FAILS once with one default flipped on purpose (pasted)<br>`UmbrellaElla.Harness.DisabledDependencyRejectedWithLog` and `UmbrellaElla.Harness.World.FlagsOffBaselineUnchanged` pass (QA-10); the QA-10 row in `pipeline/qa/test-map.md` is set to merged with this card's number<br>Preset T-01 from `pipeline/qa/presets.json` loads and logs 1 `TestPresetLoaded` line with build, manifest version and seed (pasted)<br>Debug-only (D-new-workbench-debug): panel, sliders, presets, scenarios, overlay and export sit inside `#if UMBRELLAELLA_WORKBENCH`; `IsFeatureEnabled` stays in every build. Each flag default and each tunable default carries its `// bake:` marker. On the submission package `tools\ue\smoke.ps1` passes with `workbench=0` and no `WORKBENCH_ON` line; on a `package.ps1 -Workbench` package `-Workbench` shows the panel and logs `WORKBENCH_ON debug=1` (pasted)<br>Testers can turn it all on: the tester package (`package.ps1 -Workbench`) opens the workbench with `-Workbench` or `ue.Workbench 1`, and every feature flag is a toggle and every tunable in the manifest and `pipeline/feel/feel.json` a slider, each at its manifest default. The card 0.25 debug toggles are ported for the game, all off at launch: `dbg.no_ground_death` (the bottom exit and health zero do not end the run), `dbg.hover` (Ella holds her height), `dbg.health_bars` (numbered bars over Ella and the owl). `UmbrellaElla.Harness.DebugTogglesOffByDefault` passes; none of them is a manifest flag or a `// bake:` default, so the submission package never has them (pasted)<br>Team-meeting dev settings, debug-only and each at its GDD SH1.0 value by default: a movement-model A/B toggle (`dbg.move_model`: direct left/right steering, the GDD default, or wind-driven travel with no left/right steering); owl wing gusts, 1 or 2 at different heights, each with size, speed and height sliders (OWL-02 is PROPOSED/OFF, so 0 gusts by default); rise and fall speed sliders at their GDD SH1.0 starts until section 9 prints ranges (D-new-sh10-param-ranges) (a value outside needs a DECIDED row, `pipeline/checklists/tuning.md`). `UmbrellaElla.Harness.DevSettingsDefaultToGdd` passes, and `python3 tools/bake_preset.py effective` on the submission smoke shows the shipped rise and fall speeds equal the GDD starts (both pasted)<br>The dev tuning panel is its own debug-only widget, separate from the player's settings menu (card 0.21): `grep -rl Harness Source/UmbrellaElla/Private/UI` prints nothing (exit 1) and the settings menu shows no workbench control (1080p capture pasted)<br>First bake: T-01 exported from the workbench, `python3 tools/bake_preset.py bake Saved/Workbench/config-T-01.json` (diff pasted, values unchanged) writes `pipeline/qa/baked.json` for the features coded so far (it lists the rest as `not marked yet`; the G4 bake card covers them, `pipeline/checklists/tuning.md`), and `bake_preset.py check --preset T-01` prints PASS; it FAILS once with one marked default edited by hand (both pasted)<br>`python3 tools/module_check.py` prints `module_check: 0 problem(s)` (rule M included), pasted |
| 0.28 | Hitbox alignment | Gameplay Dev | Art Director | `pipeline/feel/hitboxes.json`, `pipeline/art/visual-align.json`, `Source/UmbrellaElla/Private/Tests/Feel/**` | 0.5, 0.10b | Every gameplay sprite (Ella, owl body, owl clock, bolts) has its collider in `pipeline/feel/hitboxes.json` as gameplay data: Ella's hurtbox and the bolt name their `feel.json` forgiveness value (GDD SH1.0 CORE-05: cosmetic swaps never alter hitboxes)<br>`python3 tools/hitbox_check.py fit` aligns each sprite's visual-only scale and offset; `python3 tools/hitbox_check.py check --fail-lfs-pointer --require` prints `hitbox_check: PASS` (pasted)<br>`UmbrellaElla.Feel.Hitboxes` passes: each actor's collision equals its entry and the sprite uses its `visual-align.json` scale and offset (pasted `PASS  tests=` line), and this PR marks its `pipeline/qa/test-map.md` row merged |
| 0.29 | Encounter presets in data (the GDD SH1.0 baseline) | Encounter Designer | Game Designer | `pipeline/level/encounter.json` (`encounter_presets` only), `pipeline/level/encounter.md`, `pipeline/level/reference/**`, `docs/decisions.md` (each proposed preset's own row) | 0.8b | `python3 tools/encounter_check.py` prints `encounter_check: 0 problem(s)` (pasted)<br>`python3 tools/encounter_check.py --presets --context ship` lists 1 preset, `GDD-SH1.0` (pasted)<br>`python3 tools/encounter_check.py --presets --context gdd_picker` lists each proposed preset with its decision row and that row's owner (pasted) |
| 0.30 | Encounter rows ready: hitbox, art and sound per preset | Encounter Designer | Art Director | GitHub only (one request issue per missing row, filed to that row's owner) | 0.29, 0.28, 0.14b | `python3 tools/encounter_check.py --ready --preset GDD-SH1.0` prints `encounter_ready: 0 problem(s) preset=GDD-SH1.0` (pasted)<br>each FAIL line of that run names a request issue (#n): hitbox to Gameplay Dev, art element to the Art Director, sound row to Audio |
| 0.31 | Encounter run log (`ENCOUNTER_EVT` lines) | Gameplay Dev | Dev Lead | `Source/UmbrellaElla/Private/Owl/RunLog/**`, `Source/UmbrellaElla/Private/Tests/Owl/RunLog/**`, `pipeline/qa/test-map.md` | 0.5b, 0.23 | `UmbrellaElla.Owl.World.PlaythroughLogLines` passes headless: a scripted run writes one `ENCOUNTER_EVT` line per phase start and end, transition start and end, telegraph, fire, hit, break and end, in the format `tools/encounter_spec.py` lists<br>`python3 tools/encounter_check.py --playthrough Saved/Logs/encounter.log --preset GDD-SH1.0` on that run's log prints `playthrough_check: 0 problem(s)` (pasted) |
| 0.32 | Encounter preset loader and selector (workbench, practice) | Gameplay Dev | Encounter Designer | `Source/UmbrellaElla/Public/Owl/Preset/**`, `Source/UmbrellaElla/Private/Owl/Preset/**`, `Source/UmbrellaElla/Private/Tests/Owl/Preset/**`, `pipeline/qa/test-map.md` | 0.5b, 0.27, 0.31 | `UmbrellaElla.Owl.PresetLoadsFromEncounterJson` passes: it loads every preset in `encounter_presets` of `pipeline/level/encounter.json`, with no fight number in C++<br>`UmbrellaElla.Owl.World.NoAttackDuringTransition` passes: no attack starts inside a transition_in or a break stun<br>A Development package logs `SMOKE_OK ... workbench=0` on the default preset, and `UmbrellaElla.Encounter.Preset=` naming a proposed preset is refused unless the workbench or practice mode is on (both log lines pasted) |
| 0.33 | Encounter loop per phase of the Keeper fight (one card each: GDD-SH1.0 wings, mechanisms, clock) | Encounter Designer | Game Designer | `pipeline/level/encounter.json` (`encounter_presets` only), `pipeline/level/encounter.md` | 0.30, 0.32 | The card has an `Encounter phases: GDD-SH1.0/wings` line (mechanisms and clock on their own cards)<br>`playthrough_check: 0 problem(s) preset=GDD-SH1.0 phases=...` from a full run in a practice build (pasted)<br>The newest `ENCOUNTER CRITIC:` line for the phase is PASS on its current spec hash, each round with its playthrough= and check= scores (no round cap; a needs-human ask to the game design checkpoint only after 3 FAIL rounds in a row with the same gap and no better score)<br>`python3 tools/encounter_check.py --card card.md` prints `card_check: 0 problem(s)` (pasted) |
| 0.34 | Story bible v1 (after the theme) | Story / game design owner | Game Designer | `pipeline/story/story-bible.md`, `docs/decisions.md` rows D-new-story-canon, D-new-owl-name | 0.19 | Every #story post pasted on the card and every GDD SH1.0 narrative item (section 6: the team story, NAR-02..NAR-08) is a Names or Facts row with a status and a source; no #story row is marked GDD<br>`python3 tools/story_check.py` prints `story_check: PASS bible=... sheet=...` (pasted)<br>`python3 tools/story_check.py --calibrate` prints PASS, and the critic session's `STORY_CALIBRATION: PASS rows=22` line is pasted (`evals/story-critic/README.md`)<br>The final `STORY_CRITIC: PASS ... cycle=<n>` line (no cycle cap), from a session other than the builder, names the same bible and sheet hashes, and `python3 tools/story_check.py --critic` on that line prints `story_check: critic line ok` (pasted)<br>1 `NEEDS HUMAN: Richard (game design owner) confirm story canon ...` comment (rows, link, UTC time) lists every PROPOSED and OPEN row; `check_card.py --needs-human` prints it with HUMAN ONLY |
| 0.35 | Screen copy and tooltips (FLOW-34..FLOW-41) | Story | UI and UX | `pipeline/story/lines.csv`, `Content/UmbrellaElla/UI/ST_UI.csv` (SourceString cells only) | 0.34, 0.20 | `pipeline/story/lines.csv` has a row for every key of `Content/UmbrellaElla/UI/ST_UI.csv` (Start, pause, settings, win ending, credits, fail, prompts; `pipeline/ui/menus.md`): `python3 tools/story_check.py --table Content/UmbrellaElla/UI/ST_UI.csv` prints PASS (pasted)<br>`python3 tools/story_check.py` and `python3 tools/story_check.py --scan Content/UmbrellaElla/UI/ST_UI.csv` print PASS (pasted); no narrative-surface row ships text the story bible has not confirmed (the check fails it)<br>The final `STORY_CRITIC: PASS ... cycle=<n>` line (no cycle cap) from a separate critic session names the same hashes, and `story_check.py --critic` prints `story_check: critic line ok` (pasted) |
| 0.36 | Store page and video narration drafts (G3) | Story | Producer | `pipeline/story/lines.csv` (store_short, store_long and narration rows) | 0.35 | `pipeline/story/lines.csv` has 1 store_short row (20 words or fewer), 1 store_long row (150 or fewer) and 1 narration row per beat in `pipeline/submission/video-plan.md`; `python3 tools/story_check.py` prints PASS (pasted)<br>`python3 tools/story_check.py --scan pipeline/submission/itch-page.md` prints PASS (pasted)<br>The final `STORY_CRITIC: PASS ... cycle=<n>` line (no cycle cap) from a separate critic session names the same hashes, and `story_check.py --critic` prints `story_check: critic line ok` (pasted)<br>Each row resting on a PROPOSED fact stays ship=no and is listed in 1 `NEEDS HUMAN: Richard (game design owner) confirm story canon ...` comment |
| 0.37 | Keeper rig and animations (replaces the `FB_Keeper_*_PH` placeholders) | Asset Specialist | Art Director | `pipeline/art/blender/characters.json` (keeper rows), `pipeline/art/blender/stand_ins.py` (keeper builder), `Art/Source/Keeper/**`, `Content/UmbrellaElla/Art/Keeper/**`, `pipeline/art/provenance.csv` | 0.10b, 0.4d | For every `coverage` row of `pipeline/art/blender/characters.json` whose `replaced_by` is 0.37, the agent adds the rig parts and recipe rows (`stand_ins.py` builder, `characters.json` anims) and `python3 tools/assetgen.py blender --character keeper --anim ANIM` renders it; the render output line of each anim is pasted<br>`python3 tools/sprite_check.py --scan Art/Source` prints PASS (pasted)<br>Each family is an art-loop piece judged against the key art and the GDD SH1.0 text (references are judging targets, never generation inputs): `python3 tools/art_ref_check.py --card 0.37 --element owl FILES` PASS and the `art_loop: PASS card=0.37 piece=...` lines for this commit are pasted (`python3 tools/art_loop.py evidence --card 0.37`)<br>Each replaced row's status reads `recipe` and its `_PH` flipbook is deleted from `Content/UmbrellaElla/Art/`; `python3 -m unittest tests.test_art_coverage` prints OK (pasted)<br>The capture shows a crownless fabricated metal owl in side profile with exactly two feet, two vane wings, the chest clock and three distinct hanging mechanisms (OWL-08, ART-06)<br>Each new file has a provenance row (`python3 tools/art_check.py --references` exits 0, pasted) |
| 0.38 | Ella rig and animations (replaces the `FB_Ella_*_PH` placeholders) | Asset Specialist | Art Director | `pipeline/art/blender/characters.json` (ella rows), `pipeline/art/blender/stand_ins.py` (ella builder), `Art/Source/Ella/**`, `Content/UmbrellaElla/Art/Ella/**`, `pipeline/art/provenance.csv` | 0.10b, 0.4d | For every `coverage` row of `pipeline/art/blender/characters.json` whose `replaced_by` is 0.38, the agent adds the rig parts and recipe rows (`stand_ins.py` builder, `characters.json` anims) and `python3 tools/assetgen.py blender --character ella --anim ANIM` renders it; the render output line of each anim is pasted<br>`python3 tools/sprite_check.py --scan Art/Source` prints PASS (pasted)<br>Each family is an art-loop piece judged against the key art and the GDD SH1.0 text (references are judging targets, never generation inputs): `python3 tools/art_ref_check.py --card 0.38 --element character FILES` PASS and the `art_loop: PASS card=0.38 piece=...` lines for this commit are pasted (`python3 tools/art_loop.py evidence --card 0.38`)<br>Each replaced row's status reads `recipe` and its `_PH` flipbook is deleted from `Content/UmbrellaElla/Art/`; `python3 -m unittest tests.test_art_coverage` prints OK (pasted)<br>The capture shows an adult Ella with her face hidden by the mask, two hands on one striped umbrella and no wand (ART-06)<br>Each new file has a provenance row (`python3 tools/art_check.py --references` exits 0, pasted) |
| 0.39 | Regular enemy rigs and animations, male and female (replaces the `FB_Warden*_PH`, `FB_Floodstrider_*_PH`, `FB_Courier*_PH` placeholders) | Asset Specialist | Art Director | `pipeline/art/blender/characters.json` (enemy rows), `pipeline/art/blender/stand_ins.py` (enemy builders), `Art/Source/Enemies/**`, `Content/UmbrellaElla/Art/Enemies/**`, `pipeline/art/provenance.csv` | 0.38 | For every `coverage` row of `pipeline/art/blender/characters.json` whose `replaced_by` is 0.39, the agent adds the rig parts and recipe rows (`stand_ins.py` builder, `characters.json` anims) and `python3 tools/assetgen.py blender --character warden_sundial_f --anim ANIM` renders it; the render output line of each anim is pasted<br>`python3 tools/sprite_check.py --scan Art/Source` prints PASS (pasted)<br>Each family is an art-loop piece judged against the key art and the GDD SH1.0 text (references are judging targets, never generation inputs): `python3 tools/art_ref_check.py --card 0.39 --element character FILES` PASS and the `art_loop: PASS card=0.39 piece=...` lines for this commit are pasted (`python3 tools/art_loop.py evidence --card 0.39`)<br>Each replaced row's status reads `recipe` and its `_PH` flipbook is deleted from `Content/UmbrellaElla/Art/`; `python3 -m unittest tests.test_art_coverage` prints OK (pasted)<br>Each of the five enemy types has a male and a female version with separate red and yellow release frames (COM-12, ART-10)<br>Each new file has a provenance row (`python3 tools/art_check.py --references` exits 0, pasted) |
| 0.40 | Clock HUD, XP ring and menu art (replaces the `T_HUD_*_PH` and `T_Menu_*_PH` placeholders) | Asset Specialist | Art Director | `pipeline/art/blender/characters.json` (hud rows), `Art/Source/UI/**`, `Content/UmbrellaElla/Art/UI/**`, `pipeline/art/provenance.csv` | 0.10b, 0.4d | For every `coverage` row of `pipeline/art/blender/characters.json` whose `replaced_by` is 0.40, the agent adds the rig parts and recipe rows (`stand_ins.py` builder, `characters.json` anims) and `python3 tools/assetgen.py blender --character hud_clock --anim ANIM` renders it; the render output line of each anim is pasted<br>`python3 tools/sprite_check.py --scan Art/Source` prints PASS (pasted)<br>Each family is an art-loop piece judged against the key art and the GDD SH1.0 text (references are judging targets, never generation inputs): `python3 tools/art_ref_check.py --card 0.40 --element character FILES` PASS and the `art_loop: PASS card=0.40 piece=...` lines for this commit are pasted (`python3 tools/art_loop.py evidence --card 0.40`)<br>Each replaced row's status reads `recipe` and its `_PH` flipbook is deleted from `Content/UmbrellaElla/Art/`; `python3 -m unittest tests.test_art_coverage` prints OK (pasted)<br>The HUD capture shows one top-left clock with a separate health hand and life hand over a translucent face (FLOW-30, ART-08)<br>Each new file has a provenance row (`python3 tools/art_check.py --references` exits 0, pasted) |
| 0.41 | Environment components and Unreal VFX (replaces the `T_Env_*_PH` and `NS_*_PH` placeholders) | Asset Specialist | Art Director | `pipeline/art/blender/characters.json` (environment and vfx rows), `Art/Source/Scene/**`, `Content/UmbrellaElla/Art/Scene/**`, `Content/UmbrellaElla/VFX/**`, `pipeline/art/provenance.csv` | 0.10c, 0.4d | For every `coverage` row of `pipeline/art/blender/characters.json` whose `replaced_by` is 0.41, the agent adds the rig parts and recipe rows (`stand_ins.py` builder, `characters.json` anims) and `python3 tools/assetgen.py blender --character skyline --anim ANIM` renders it; the render output line of each anim is pasted<br>`python3 tools/sprite_check.py --scan Art/Source` prints PASS (pasted)<br>Each family is an art-loop piece judged against the key art and the GDD SH1.0 text (references are judging targets, never generation inputs): `python3 tools/art_ref_check.py --card 0.41 --element background FILES` PASS and the `art_loop: PASS card=0.41 piece=...` lines for this commit are pasted (`python3 tools/art_loop.py evidence --card 0.41`)<br>Each replaced row's status reads `recipe` and its `_PH` flipbook is deleted from `Content/UmbrellaElla/Art/`; `python3 -m unittest tests.test_art_coverage` prints OK (pasted)<br>An effect on / off capture pair shows nearby-surface light from the lit-overlay layer (VFX-07, D-new-sh10-vfx-lighting)<br>Each new file has a provenance row (`python3 tools/art_check.py --references` exits 0, pasted) |

After 0.3 is merged, the Producer files the MVP cards for G1 (MVP 1-6, the Start Game mode; D-new-sh10-g1), then G2 (MVP 7-11), then G3 (MVP 12-15), each passing `pipeline/checklists/card-ready.md`,
with lanes split per component (`pipeline/unreal/gameplay-code.md`, code layout), so cards can run in parallel.
A card that creates tests writes its own issue number and `merged` in its `pipeline/qa/test-map.md` row, in its own PR.
That file, `docs/decisions.md` (a card adds or edits only its own rows) and `docs/jam-brief.md` (only the lines its lane names) are row-scoped: `check_card.py --lanes` does not count them as shared lanes.

##### Post-start build order (GDD SH1.0 sections 2, 5, 11) mapped onto cards
Every MVP card names its feature IDs (every GDD SH1.0 Rule ID is APPROVED_P0, so every feature card is an MVP card) and `GDD revision:`; `check_card.py` fails it until those IDs are authorized.
| Step | GDD SH1.0 | Cards |
|---|---|---|
| 1 | Empty game project from frozen tooling; build | 0.3, then 0.5, 0.6 |
| 2 | Start Game mode: Start screen, Ella's four-state movement, Small Blasts, the clock HUD, the complete Keeper fight, pause, retry, win ending (G1) | 0.8, 0.5b, 0.8a, 0.8b, 0.14b, MVP 1-6, then 0.29-0.33 per Keeper phase |
| 3 | Director's Cut route: tutorials, settings, the nine-chunk level, regular enemies, story (G2) | MVP 7-11, 0.21, 0.21b, 0.34, 0.35 |
| 4 | Director's Cut growth: progression, the four spells, win statistics, Game Options (G3) | 0.27, 0.23, MVP 12-14 |
| 5 | Final art, animation, VFX and audio; every `_PH` replaced (G3) | 0.10, 0.10b, 0.10c, 0.37-0.41, MVP 15 |
| 6 | Regression, human playtests, polish, package early (G3, G4) | 0.6b, 0.6d, 0.24, gates G3 and G4 |
| Windows | The Win64 build, smoke, daily and zip on the Windows packaging machine (never on the Mac G1 path) | 0.3w, 0.6w, 0.4b, 0.6d |
A placeholder asset ends in `_PH` and names the card that replaces it (`pipeline/art/blender/characters.json` coverage); `tools/pipeline_check.py --release` fails any left at G4.

## Humans in the loop

### `pipeline/human-checkpoints.md`

#### Human checkpoints

> GDD SH1.0 note (D-new-gdd-sh10): lines on this page that still describe the GDD 1.3 encounter (one owl bolt, the front shield, the 90 s survival timer, wear stages, the 1.3 QA-01..QA-28 tests) are history. The current design is `docs/gdd/GDD-SH1.0.md` and `docs/feature-manifest.json`, which win; the owning role re-files this page against the SH1.0 Rule IDs on its next card.


Agents own all build and setup work (Josh: "take the onus off the user, this stuff needs to be built out"). A person
acts only at the checkpoints below, and only to sign off: the agent prepares everything, and the person's step is
one command, one click, one answer or a physical act. Every point where a human must act, and who acts. "Who" is a seat in the People table of `docs/jam-brief.md`;
card 0.0 fills in the names. An agent that reaches one labels the issue `needs-human`, comments
`NEEDS HUMAN: <who/role> <what> <link> <YYYY-MM-DDTHH:MMZ>` (AGENTS.md section 4; the UTC time the label went on)
and stops that step. The Producer sweeps the queue every jam hour (`check_card.py --needs-human`;
`pipeline/how-to-run-the-jam.md`).

##### Checkpoint kinds
A Day-0 card's person part is a Done-when line that starts `HUMAN <kind>:`, and column 3 of `pipeline/day0-cards.md`
names the kinds the card signs off (`<agent role> / <seat> (sign-off: <kinds>)`). `tools/check_card.py`
(`CHECKPOINT_KINDS`, `day0_owner_problems`) and `tools/pipeline_check.py` fail a person as Owner or reviewer, an
untagged person step, and any other kind. Everything else on a card is the owner agent's or kickoff's.
| Kind | The person's step | Why a person |
|---|---|---|
| `submission` | every upload (`butler push`), the jam form, closing G4 | Official Rules §17: a human entrant submits, never an AI agent |
| `secrets` | set an API key or token once per machine (environment or keychain, never a file) | a secret only a person holds |

No person on a Day-0 card does these any more; the tools do them, and the guardrails stay enforced by tools and CI:
- Gate patches: kickoff applies a session's `$JAM_OUTBOX/gate.patch` itself (`python3 tools/git_gate.py apply UE-<id> --auto`,
  commit trailer `GATE EDIT: by=kickoff`). It refuses a patch with a path outside the card's lane, a change to a guardrail enforcer
  (`git_gate.py` GUARD_CORE: the hooks, `check_pr.py`, `kickoff.py`, `secrets_check.py`), or a loosened guardrail file
  (gates.json or `.claude/settings*.json`: a deny entry dropped, an allow entry added, `mcp_enabled` or
  `native_windows_shell` opened). CI's `check_pr.py` rule gate finds that commit in the PR's git history and re-runs those
  checks, and kickoff's merge gate runs this checkout's rule gate too. A refused patch goes back to the builder; a loosening never goes through the pipeline.
- Repo settings: after cards 0.16 and 0.17 merge, kickoff sets the variables, branch protection and the Actions setting
  itself with fixed commands (`tools/kickoff.py` repo_settings) and posts the read-back.
- Machine work: a card that says `Runs on: the Windows packaging machine` is built by the kickoff running there, and
  one that says `Runs on: the Mac build machine` by a kickoff on the Mac. Every G1 card runs on the Mac; the Windows
  cards (0.3w, 0.6w, 0.4b, 0.6d) wait for that machine and never hold up G1 (`tools/kickoff.sh --until G1`).
- Audio: kickoff runs the audio critic sessions itself, and a sound the ElevenLabs API could not make (no key, an HTTP
  error, no credits left) becomes a tracked placeholder take; the run goes on (`tools/audio_check.py --placeholders`).
- `jam-start`: kickoff tags it when card 0.3 starts. People and Team hours: card 0.0 fills them from the repo's GitHub
  collaborators (`default (agent)`). Day-1 design rows: their owner agent decides them as `agent default` rows.

Art direction is not a sign-off checkpoint (Josh, 2026-11-10). The automated art gate decides: `python3 tools/art_check.py --gate`
on an in-engine capture (the numeric check against `pipeline/art/style.json`, every picture in
`pipeline/art/references.json` present, a calibrated judge, and the blind X/Y row against the key art). The Art
Director agent and the art loop (`tools/art_loop.py`) re-place or regenerate until it passes (no round cap, D-new-no-round-cap); a person
sees a piece only when it is stuck: 3 rounds in a row with the same gap and no better score (the art direction row below).
Changing `style.json` thresholds stays a guardrail.

##### 2-hour grace default (approved by Josh)
If no human answers within 2 hours, `check_card.py --needs-human` prints `GRACE EXPIRED -> <role>` and the item goes
to a director session at the Hard calls tier (Fable 5.1, high effort; `pipeline/agent-ops/model-tiers.md`):
- Producer: scope, schedule, cut-list and approval calls.
- Technical Director: technical calls (asks to the TD seat).
- Producer for Richard: design calls in Richard's area.

The director adds a row to the Open decisions table of `docs/decisions.md` with Status
`DECIDED <date> (agent default after 2h grace; <role>; human may overturn)` and a link to the needs-human issue,
comments on the issue, removes the label, and work continues. If a human replies later, the human's answer wins and
the change gets its own decisions row (the grace row is marked `SUPERSEDED by D<n>`).

**Never a grace default.** These stay human-only however long they wait (`check_card.py` prints `HUMAN ONLY`;
`manifest_check.py` fails a grace row on them):
1. The final submission or any upload (Official Rules §17), and closing G4.
2. Physical work: Windows packaging and launch, playtests, the editor check of `.uasset`/`.umap` changes.
3. Changing guardrails: `gate_paths` in `pipeline/agent-ops/gates.json`, tools, tests, CI, hooks, role cards, model tiers.
4. Deleting someone else's work.
5. A P0 override or lifting a P0 rule: an `Overrides:` row needs `DECIDED <date> (Richard)`.
6. `approved_parameters` ranges: a grace default never changes them.
7. A hitbox or collider change (`hitbox_check.py fit` says `NEEDS HUMAN: Richard hitbox change request`): only Richard
   approves it (GDD 1.3 7C: "Never silently resize collisions to an atlas or damage mask").
8. Story canon: a PROPOSED or OPEN story bible row, the game title, the owl's name. Only Richard confirms it; the story
   agent writes proposals and waits (`pipeline/roles/story.md`). Until then the text stays `ship=no` (`tools/story_check.py`).

##### What needs a human
| Kind | Examples |
|---|---|
| (a) Irreversible or external | an upload or submission, closing a gate |
| (b) Design or scope | GDD status, the P0 and cut lists, tuning outside the approved ranges (art is the automated art gate) |
| (c) Changing the guardrails | `tools/`, `tests/`, CI, role cards, agent settings (the gate paths below) |
| (d) Physical work | Windows packaging and launch, playtests |
| (e) Deleting someone else's work | any delete under `Content/` or `Source/`, a branch or file another card owns |

Everything else is reversible in-lane work with machine-checkable evidence. It needs no approval.

`tools/kickoff.sh` raises these items itself (label, `NEEDS HUMAN:` comment, one printed line) and keeps running the
other cards. It merges a card's PR itself (`gh pr merge --squash --match-head-commit`, one commit per card) once
every required CI check on the head is green, the reviewer agent's last verdict after the last push is approve, and
`tools/check_pr.py` passes on the head (its artship rule is the art ship gate); agent sessions still never push or
merge. A merge that fails is tried again, then asked (row below). It never closes a gate or uploads, even where a row
below allows a grace default: those wait for a human (or a director session a human starts). It closes a card whose
PR merged and a GitHub-only card its reviewer role approved itself (no ask), and before the jam start it runs the
pre-jam cards on the team repo (PRE-JAM mode).

##### Where they happen
| Checkpoint | Who acts | Source | Grace default |
|---|---|---|---|
| A card PR kickoff could not merge after its retry (`merge PR #N: ...` with the reason: a red or missing CI check, a `check_pr.py` problem, a conflict, branch protection): fix the cause, then run kickoff again | the card's `Human:` (the integration owner for cross-lane cards) | AGENTS.md §4; `tools/kickoff.py` merger | yes: Producer (not a gate-path PR, row below) |
| Merge a lane_guard revert PR within 30 min | integration owner | AGENTS.md §6; `tools/lane_guard.py` | yes: Technical Director |
| Add the `REVERT_TOKEN` secret so revert PRs run CI | TD human (repo admin) | `.github/workflows/main-red.yml` | no (3): CI |
| A gate patch the tool route refused MAX_FAILS times in a row (the card is labelled blocked). Gate paths: `tools/**`, `tests/**`, `.github/**`, `evals/` cases and results, `pipeline/roles/**`, `pipeline/agent-ops/**`, `pipeline/art/style.json`, `pipeline/audio/style.json`, `pipeline/audio/sound-events.json`, `pipeline/story/story.json`, `.claude/**`, `AGENTS.md`, `CLAUDE.md`, `.mcp.json`, `.gitattributes`, `.gitignore`. Normally nobody acts: kickoff applies the session's `$JAM_OUTBOX/gate.patch` with `python3 tools/git_gate.py apply UE-<id> --auto` (lane, guardrail enforcers, no loosening; `GATE EDIT: by=kickoff`) | the card's `Human:` (fix the card or the patch, remove `blocked`) | `pipeline/agent-ops/gates.json` `gate_paths`; `tools/git_gate.py` auto_problems | no (3) |
| `gh pr merge`, `gh release`, `gh api`, `gh secret`, `gh variable`, `gh ruleset`, `gh repo` edits; a push to `main`; a bulk delete under `Content/` or `Source/`, in an agent session (kickoff's own merge and its fixed repo-settings steps are not a session and do not ask) | whoever runs the session (the hook asks) | `gates.json` `ask_commands`, `protected_branches`, `delete_ask_paths` | no (3, 4): the hook asks whoever runs the session |
| Close G1-G4 (Pass, Pass with named exceptions, Fail) | scope decision-maker | `pipeline/roles/producer.md` Gates; `pipeline/templates/gate-record.md` | yes for G1-G3: Producer. no for G4 (1) |
| Decide an open row; a `DECIDED (Richard)` row with `Overrides:` | the row's Owner; Richard for P0, presets and GDD status | `docs/decisions.md` | yes for an open row: by its Owner (TD rows to Technical Director, Richard's to Producer for Richard, else Producer). no for `Overrides:` (5). Day-0 cards 0.0, 0.14 and 0.19 decide their rows themselves as `agent default` rows the team may override (no ask) |
| A new GDD revision, a P0 or cut-list change | Richard (game design owner); cuts: scope decision-maker | `docs/gdd/README.md`; `docs/jam-brief.md` | yes for a cut list with no P0: Producer. no for a GDD revision or a P0 (5), except card 0.0 recording the GDD SH1.0 import as printed (D-new-gdd-sh10: every Rule ID APPROVED_P0; an agent default the team may override) |
| Tuning outside a GDD SH1.0 start (section 9 ranges are blank, D-new-sh10-param-ranges) | Richard, by a DECIDED row | `pipeline/checklists/tuning.md` | no (6) |
| Art direction: no human approves a look (Josh, 10 Nov). The references in `pipeline/art/references.json` are the bar; the art loop's blind critic and the deterministic checks decide (`pipeline/art/art-bible.md`). A human acts only when a piece is stuck (3 rounds with no improvement) | Art Director human, with the first and latest image and the critic's gaps | `tools/art_loop.py`; `pipeline/roles/art-director.md` | yes: Producer |
| The audio mix by ear: the final listen after every piece closed its loop (`pipeline/audio/style-target.md` section 5); it is not the bar | audio owner | `pipeline/roles/audio.md` | no (2): needs ears |
| A stuck audio piece (`audio_loop.py verdict` prints `NEEDS HUMAN: Audio-owner ...` after 3 rounds with no improvement): listen to the files and answer with `audio_loop.py resume` | audio owner | `pipeline/audio/style-target.md` section 5 | no (2): needs ears |
| `daily.ps1` on the Windows packaging machine, each merge and each gate, while `gates.json` `native_windows_shell` is `block` (with `allow`, kickoff's QA and Build session runs it) | packaging machine owner | `pipeline/roles/qa-build.md` step 1 | no (2) |
| Start the gate zip on a second Windows machine (LAUNCH line) | launch machine owner | `pipeline/templates/gate-record.md` | no (2) |
| Playtests P1-P11 and the end-of-day 15-min play (one per gate on a real controller: the `GAMEPAD:` line; the automated `gamepad=ok` smoke, card 0.6e, does not replace it) | playtest lead and the human testers | `pipeline/qa/playtests.md` | no (2) |
| Every upload (`butler push`) and the jam form, final submission included, before the deadline | the Team Owner or the packaging and submission owner, a human entrant. Official Rules §17: never an AI agent; `hook.py` blocks `butler push` and `butler login` (`gates.json` `human_only_commands`) | `pipeline/checklists/submission.md` Upload; `docs/jam-rules.md` team rule 14 | no (1) |
| Set the audio API keys once per machine that runs kickoff (`ELEVENLABS_API_KEY`, `STABILITY_API_KEY`; art needs none: Blender), in the environment or the OS keychain, never a file | whoever runs `tools/kickoff.sh` on that machine | `tools/keys.py`; `tools/connections.py` names a missing key | no (3): a secret only a person holds; until then sounds fall back to placeholders |
| Turn on the MCP servers at kickoff: Unreal editor, GIMP, Aseprite, Blender (`mcp_enabled`, the kickoff record; both agents get them through `tools/kickoff.py`) | TD human, with the team's OK | `pipeline/agent-ops/editor-mcp.md`; `tools/mcp_config.py` | no (3) |
| Open and check each `.uasset`/`.umap` a PR changes (`EDITOR CHECK:` line) | the card's `Human:` | `tools/check_pr.py` rule editor | no (2) |
| Confirm story canon: a PROPOSED or OPEN row of `pipeline/story/story-bible.md`, the title, the owl's name (`STORY CONFIRM: by=Richard <row ids>` on the PR) | Richard (game design owner) | `pipeline/roles/story.md`; `docs/decisions.md` D-new-story-canon, D-new-owl-name; `tools/check_pr.py` rule story | no (8): a design call stays human |
| G4 content sign-off (`CONTENT ...` line: teen, trademarks, original, no extra software, English) | the Team Owner or the packaging and submission owner | `pipeline/checklists/submission.md` Content and rules | no (1) |
| Start an agent session (`tools/start_session.sh <role> <card>`) | whoever runs that machine | `pipeline/agent-ops/model-tiers.md` | no (2): a person at the machine |
| Answer an `--overrun` ask, a token-cap OK, a hard-stop exception | Producer human | `pipeline/roles/producer.md`; `pipeline/roles/agent-ops.md` | yes: Producer |
| The `HUMAN <kind>:` lines on Day-0 cards (column 3 `sign-off:` kinds; every card is agent-owned) | the card's `Human:` | `pipeline/day0-cards.md` | no for submission and secrets |

### `pipeline/how-to-run-the-jam.md`

#### How to run the jam (for humans)



Agents follow `AGENTS.md` and own every card; you only sign off where
`pipeline/human-checkpoints.md` says.

##### Start: one command, Claude Code or Codex
1. Type `tools/kickoff.sh` (Windows: `tools\kickoff.ps1`). It prints the version, checks every connection
   and starts your agent (asking if you have both); a problem prints what to type.
   API keys: once per machine (`python3 tools/keys.py status`). MCP servers stay off until the kickoff record.
2. Then it files the cards, runs each ready card in a fresh session, opens PRs, runs the reviewer and merges;
   it stops only for a human. `--agent codex` or `claude` picks the agent. First night: `--max-cards 5` stops after
   5 cards merge or block; rerun. `--until G1`: G1 cards only, then the Mac package.
3. Before Nov 12 the team repo runs only the pre-jam cards; a test repo with `--practice` runs all. `--dry-run`
   shows the plan.
4. Answer the needs-human queue (below), then run it again: it resumes. One card:
   `tools/start_session.sh <role> <card>`.

##### Build modes
`docs/build/MODE`: `direct` (no cards or PRs) or `cards` (below). README explains.

##### A/B test a build
`tools/kickoff.sh --prompt-file my-prompt.txt` records your prompt and adds it to every session; each run prints a
`RUN #<n>: ...` line. Record it: `python3 tools/journal.py run-outcome
--run <n> --outcome pass|fail`; `python3 tools/journal.py compare <a> <b>` diffs two runs.

##### Another boss fight (encounter presets)
Fights are data in `pipeline/level/encounter.json` (Encounter Designer role); GDD 1.3 ships. A proposal such as
`OWL-FIGHT-RICKY` (`D-new-encounter-ricky`) loads only in workbench and practice builds; `python3
tools/encounter_check.py --presets --gdd 1.3` lists them.

##### How a PR merges
kickoff squash-merges it (nobody clicks merge) once:
1. CI (`pipeline-checks`) is green and the card's reviewer role posted `approve` from a different session.
2. Evidence pastes real output per Done-when line; "Not run" lines name who runs them.
   Unit tests: `tools/affected_tests.py`; the full suite is CI's.
3. `tools/check_pr.py` passes on the head. A gate-path change is the agent's gate patch; kickoff applies it
   (`git_gate.py apply --auto`).
A `merge PR #N: ...` ask names the blocker: fix it and rerun kickoff, or label the card `cut` / `superseded`.
`tools\ue\daily.ps1` within 1 h: kickoff runs it (Windows, `native_windows_shell: allow`) or its owner posts `DAILY`.
`main` red: a revert PR opens itself; the integration owner merges it within 30 min.

##### Clear the needs-human queue
Each jam hour the Producer runs:

    gh issue list --label needs-human --state open --json number,title,labels,comments \
      | python3 tools/check_card.py --needs-human

Each line reads `#<issue> <who>: <what> <link>`. If you are the named person or seat:
1. Do it (fix a blocked merge, decide the row, play the build, run the Windows step).
2. Reply on the issue: what you did, linked.
3. Remove the `needs-human` label; the next session picks it up.
An ask naming no one, or off the list, goes back to the agent.
`GRACE EXPIRED -> <role>` (2 h, no human answer): that director session decides it; a later human answer wins (`pipeline/human-checkpoints.md`).
Then `python3 tools/status_board.py --source gh` rewrites `Saved/status-board.md`; link it on the tracker.

##### Close a gate (G1-G4)
1. The Producer posts the gate record on the tracker (its lines: `pipeline/templates/gate-record.md`).
2. On the packaging machine: `gh issue view <tracker #> --json comments | python3 tools/check_card.py --gate-record`
   exits 0.
3. The scope decision-maker posts the outcome (Pass, Pass with named exceptions with owner and hour, or Fail) and
   alone closes the gate.
4. Fail or 2 h late (`check_card.py --clock` prints `CUT FIRES`): cut the next cut-list item in `docs/jam-brief.md`.
5. G4 ends with the upload: `pipeline/checklists/submission.md`, run by the packaging and submission owner.

### `pipeline/what-the-pipeline-controls.md`

#### What the pipeline controls

The pipeline checks some things with a tool, the same way every time. Other things are taste and feel: a person decides.
If it is not on the first list, no tool will catch it. Say so on the card.

##### Checked by a tool (pass or fail)

| What | Tool |
|---|---|
| Art lines up with its collider (coverage, spill, fairness margin per role); colliders are data and never move; an art swap waits for a PASS | `tools/hitbox_check.py check` (`fit` moves only the art) |
| Sprite sheets: size, clean background, soft edges, halo, pivot drift, tile seams | `tools/sprite_check.py --scan Art` |
| Art numbers on a capture: on-palette share, accent area, dark share, hue bands, paper texture | `tools/art_check.py` |
| Text size, contrast, outlines, colour-blind states, flashes, shake size | `tools/ui_check.py` (`contrast`, `grayscale`, `flashes`, `shake`) |
| Every sound has a visual, every colour has a second signal | `tools/ui_check.py signals` |
| Strings: sentence case, no baked key names, plain words | `tools/ui_check.py strings` |
| A Quit exists (title Quit, pause Quit to title, quit code in the game) | `tools/ui_check.py quit` |
| The packaged flow: play, pause, cards, restart, quits, keyboard, mouse in menus | `tools/ui_check.py flow-check` on QA's UIFLOW line |
| Hand-check lines for each gate: survive, fail, retry, quit from play, both menu quits | `tools/ue_run.py playthrough-check` |
| Build, package, smoke: it builds, boots, holds frame rate, takes input, quits with exit 0 | `tools/ue/daily.sh` / `daily.ps1`, `tools/ue_run.py` |
| Automation tests ran and none went missing | `tools/check_automation_report.py --test-map pipeline/qa/test-map.md` |
| Owl encounter data: telegraphs, spacing, gust coverage | `tools/encounter_check.py` |
| Feel numbers stay in their limits | `tools/feel_check.py` |
| Shipped defaults equal the approved preset | `tools/bake_preset.py check` |
| Feature list matches the GDD | `tools/manifest_check.py` |
| Code stays in its modules; C++ rules | `tools/module_check.py` |
| Audio list and source files | `tools/audio_check.py` |
| A card is complete before work starts; gate records are filled and true | `tools/check_card.py` |
| A PR has its evidence, and the evidence is for this commit | `tools/check_pr.py` |
| Agents stay in their lane and off gate files | `pipeline/agent-ops/hook.py`, `tools/check_pr.py` rule gate and kickoff's merge gate (no local git hook), `tools/check_card.py --lanes` |
| No secrets in the repo | `tools/secrets_check.py` |
| Docs agree with each other; no dead links | `tools/pipeline_check.py` |
| Submission zip, page, credits, rules | `tools/submission_check.py` |
| Which prompt, pipeline version, agent, model and GDD made a run | `tools/journal.py runs`, `compare` |

##### Human taste and feel (a person decides)

- Is it fun? Does the umbrella feel good to float with?
- Does the art look good and read as one style? (The Art Director signs; tools only give numbers.)
- Is the owl fair? Are the telegraphs readable in the moment? (Playtests, `pipeline/qa/playtests.md`.)
- Do the sounds and music fit? Is the mix pleasant?
- Is the difficulty right? Is 90 seconds the right length?
- Does the theme come through?
- Is a hitbox fair in play? The tool checks the numbers; playtests set them. A collider change is Richard's call.
- Do the menus feel clear? The tools check that they work, not that they are nice.
- Should a feature be cut? (Scope decision-maker.)

Checks prove a build works. They never prove it is good.

## Checklists

### `pipeline/checklists/card-ready.md`

#### Card readiness (Producer, before a card is labelled todo)

A card that fails a line is not ready. `pipeline/templates/task-card.md` lists the fields. Run `python3 tools/check_card.py` on the card first (empty fields, roles, lane, measurable Done-when); this list covers what the script can't.

- Full cards only for the next gate's MVP items. Later items stay one-line placeholders until the gate before them passes (D-new-port-11).
- Every Input path exists on `main` or is another open card's Output. No "as discussed" references.
- Rule cards pass `pipeline/checklists/design-review.md`. Asset cards have the brief from `pipeline/templates/asset-brief.md`.
- Every open decision whose test is due Day 0 or Day 1 has a spike card (`pipeline/templates/spike-card.md`). A card that depends on it waits for the result.
- Budget reads `<n> min agent + <n> min human`; agent over 120 min or human over 60 min means split (check_card enforces all three; D-new-human-cap). A Stretch card while an MVP card is open fails (`--lanes`; no override). Before labelling todo, `gh issue list --label task --state open --json number,title,body --limit 200 | python3 tools/check_card.py --hours --day N` exits 0 with this card included. It fails when a person's human budget is over 70% of their Team hours that day (D-new-reserve). That person gets no new card.
- Not too small: a card under 20 min agent + 10 min human in the same lane as another `todo` card for the same human is merged into that card. Each card costs one review session, and the review queue is capped at 3.
- Done-when and Out of scope say what must be true, not how to code it: no new class, function or member names unless `pipeline/unreal/gameplay-code.md` names them or they are test names.
- Before a card moves to `doing`: `gh issue list --label review --state open --json number,title,body | python3 tools/check_card.py --queue` exits 0 (at most 3 in review per human, D-new-port-3).
- `... | python3 tools/check_card.py --lanes` exits 0 with this card included: no shared lane glob, `.umap` or lock.
- Flipbook frame counts stay within the content caps in `docs/jam-brief.md`, or the card cites the decision row (check_card enforces).
- A stretch card names which open-vs-close decision it changes. One that changes none goes to the end of the stretch order.
- When a new GDD revision lands, run `tools/gdd_impact.py` (`docs/gdd/README.md`); every open card it lists is re-checked, and `check_card.py` fails a card whose Features changed since its `GDD revision`.
- Features are authorized in `docs/feature-manifest.json`, or the card is `Hook only` for an OPEN or PROPOSED ID (check_card enforces).
- A Python test line names its modules (`python3 -m unittest tests.test_x`) or `tools/affected_tests.py --run`; the full suite is CI's, never a card's.
- Done-when has at least one blocked, negative or interrupted check besides the normal path (owl outside the firing lane: no shot; a hit during invulnerability does no damage).
- `Out of scope`, `Used by` and `Needs` are filled. If `Used by` names something in another lane, the follow-up card (usually Integrator) is filed now and its number is in `Used by` (check_card enforces). For an Asset Specialist card, that Integrator card is open with a Budget, so `--hours` counts its human time on the same day (`--hours` fails the asset card otherwise).
- A card that creates tests named in `pipeline/qa/test-map.md` has a Done-when line that writes its issue number and `merged` in that row (the file is row-scoped; `--lanes` ignores it).
- Any card that changes maps, `Config/**`, `*.Build.cs`, `*.Target.cs`, `.uproject` or assets loaded by path has a package + `SMOKE_OK` line in Done-when.

## Templates

### `pipeline/templates/task-card.md`

#### Task card template

One card = one GitHub issue = one branch = one PR. File it with the "Task card" issue form; this template
is the reference for what each field means. A card with an empty field is not ready.

```
ID:            UE-000
Title:         <verb + thing, e.g. "Umbrella open/close changes vertical velocity">
MVP item:      <number from docs/jam-brief.md, or "Stretch: <name>">
GDD ref:       <section + quote, ≤20 words, from the current GDD snapshot (docs/gdd/CURRENT names it); "none" for tooling cards>
               <tag: GDD RULE | DEFAULT (Dn) | HYPOTHESIS (Pn) | ILLUSTRATIVE; see pipeline/checklists/design-review.md>
GDD revision:  <the revision the card was written against, e.g. 1.3 (docs/gdd/CURRENT)>
Features:      <feature IDs from docs/feature-manifest.json, e.g. UMB-03; each must be implementation_authorized.
               "UMB-03 Hook only" = interface + flag at its manifest default, no behavior (OPEN or PROPOSED IDs only).
               "none" for tooling cards>
Player outcome: <"the player sees X, does Y, can tell why"; "none" for tooling cards>
Owner role:    <Gameplay Dev | Asset Specialist | Art Director | ...>
Reviewer role: <must differ from owner>
Human:         <teammate kickoff asks when the card is stuck>

Inputs:        <files/assets/specs that must already exist, with paths>
Context:       <what the code or asset next to Outputs does today, 1-2 lines with file:line; "new files only" if nothing exists yet>
Outputs:       <exact paths this card creates or changes>
File lane:     <glob this card may write, e.g. Source/UmbrellaElla/{Public,Private}/Movement/**, Content/UmbrellaElla/Art/Ella/**;
               "GitHub only" if it writes no files. Never "none" or "everything">
Do not touch:  <paths owned by other lanes; always includes Content/UmbrellaElla/Maps/** unless this is an integration card>
Out of scope:  <behaviors not to build, e.g. "no new animation states, no stretch mechanics"; the reviewer rejects them>
Used by:       <BPs, maps, widgets or components that read what this card changes, with the follow-up card (#<n> or UE-<n>);
               "none" if nothing outside this lane reads it>
Needs:         <build | tests | editor MCP | Windows packaging machine>; the agent states what it can run (AGENTS.md §1).
               tests = Unreal automation tests. Python unit tests: `tools/affected_tests.py --run` (5 min target)
Binary locks:  <.uasset/.umap files to `git lfs lock` before editing; "none" if none>

Done when:     <each line checkable: a number with a unit, a test name, or a command with its result on the same line
               ("`tools/ue/smoke.sh` prints PASS"). "exits 0" without the command, or "eventually", fails check_card.
               A Python test line names its modules (`python3 -m unittest tests.test_x`); the full suite is CI's and
               a line asking for it fails check_card. Builder runs these lines, the reviewer re-runs only what it doubts>
  - [ ] tools/ue/build.sh (or tools\ue\build.ps1) exits 0 and the log is attached
  - [ ] <automation test name> passes
  - [ ] <negative or blocked case test, e.g. owl outside the firing lane → no shot>
  - [ ] <PIE or packaged-build observation with screenshot/clip path>
  - [ ] package + SMOKE_OK (required if the card touches maps, Config/**, Build.cs, Target.cs, .uproject or path-loaded assets)
Evidence:      <where the logs/screenshots go: the PR body>

Budget:        <n> min agent + <n> min human, e.g. "90 min agent + 20 min human". Agent over 120 min or human over 60 min: split the card.
               The clock starts at the `doing` label. 60 min over: see AGENTS.md §6 (D-new-overrun)
Stop if:       2 failed attempts with the same error → set blocked, write the diagnosis, stop
Cut tier:      MVP | Stretch-1 | Stretch-2 | ...
Unknowns:      <Decision needed / Why it matters / Proposed test / Choice: test now, accept risk, or postpone>
```

Feature IDs and statuses: `docs/feature-manifest.json` (checked by `tools/manifest_check.py`). `check_card.py` fails a card
whose features are not authorized, and a card on an older GDD revision whose features changed since (`tools/gdd_impact.py`).

After (optional, below Used by; the form's After field): the cards that must merge first, `#<n>` or `UE-<n>`. `check_card.py --blocked-by` reads it.

Asset cards add the brief in `pipeline/templates/asset-brief.md`. Spikes use `pipeline/templates/spike-card.md`.
Readiness is checked with `pipeline/checklists/card-ready.md`.

States: `todo → doing → review → done`, plus `blocked`. Only the human named on the card
moves a card to `done`, and only after the reviewer role approved and the evidence is in the PR.

Session end without a PR: post the handoff comment from AGENTS.md §6 on this card.
A card closed without being done carries the label `cut` or `superseded` and a one-line reason.

### `pipeline/templates/spike-card.md`

#### Spike card (answers one open row in `docs/decisions.md`)

Several open rows ask for a quick test before the team decides (D3, D4, D13).
A spike is a task card with these extra fields. It answers a question. It does not ship.
Title it `[UE-<n>] Spike D<n>: <question>` and paste the block under Unknowns. `check_card.py` fails a card titled
`Spike: ...` or `Spike D<n>: ...`, or any card with a `Decision row:` line, unless `Decision row` names a row,
`Decides it` reads "if ..., pick ..." and `Time box` is at most 60 min.

```
Decision row:  D<n>
Question:      <one sentence>
Variants:      <the 2-3 options being compared>
Setup:         <map/section, input device, build config, commit>
Measure:       <the number or observation that will be read>
Decides it:    <written BEFORE running: "if X, pick A; if Y, pick B">
Time box:      <at most 60 min>
Branch:        spike-D<n>-<short-name>
```

##### Rules
- The branch `spike-*` is never merged. If the team keeps the idea, a normal card rebuilds it with tests and Done-when.
- Stop at the time box or at the first result that decides it.
- Compare like with like: same section, same device, same build. In a playtest A/B, alternate which version each player sees first.
- Post the result on the decision row's issue, even if it is inconclusive:
  `Question | Commit | Setup | Observed (numbers) | Not run | Recommendation: Keep / Revise / Cut / Retest`
- The human owner of the row decides from it. A spike never marks a row DECIDED.

### `pipeline/templates/gate-record.md`

#### Gate record template (Producer)

Post on the Jam tracker at each gate. The scope decision-maker's reply closes it.
Gate times come from the Clock in `docs/jam-brief.md`. Run `python3 tools/check_card.py --clock` first and paste its line for this gate.
After posting, `gh issue view <tracker #> --json comments | python3 tools/check_card.py --gate-record` exits 0, run on the packaging machine: it always reads that machine's `Saved/Logs/pipeline/daily-records.txt`, and `--records <file>` adds one other machine's record (repeat it per machine, e.g. the launch machine's). It fails on a missing or unfilled line, and on a Top risks row with no `<n> fired yes/no` (a yes names its owner).

```
Gate: G<n> | due <Clock time> | closed <time> | late by <h> h (over 2 h fires the next cut)
Build: commit | packaged zip name | config
MVP items for this gate: MVP <n> pass|fail for every item due (G1: 1-6, 9, 11; G2 on: 1-12), with the build record or test link
Playtests for this gate: P<n> pass | fail | insufficient for each test run, with results-log rows
Jam-page test upload (G1 on): <link> | sha256=<hash> | re-downloaded and launched: yes/no
Open P0/P1: <list or none>
PLAYTHROUGH: <ue_run.py playthrough-check --gate G<n> output>
Repeat boots: <the Build commit's DAILY line from `$env:SMOKE_REPEAT=5; tools\ue\daily.ps1` on the Win64 packaging machine, with smoke=PASS(... repeat 5/5)>
Gate checks: <ui_check.py ci --release last line (G1: plain ui_check.py ci)> | <submission_check.py zip ... --gate G<n> PASS line, with its commit= and sha256=>
Cut fired: no | yes, <item>
What slowed us / change for next gate: <one line each>
Process change: <card #n, owner <role> | none>
Incidents since last gate: <none | #n cause=<AGENTS §6 class> missed-by=<check that should have caught it, or none> follow-up=<#n or none>, one per P0 or main-red revert>
Verdicts: design <name> pass|fail <link> | art <name> pass|fail <link> | UI <ui_check ci line> | tech <name> pass|fail <link>
Risks: <row n> fired yes/no for each Top risks row in docs/jam-brief.md, e.g. 1 fired no | 2 fired yes, owner Rick, fallback started
Proposed outcome: Pass | Pass with named exceptions | Miss → cut
```

- G1 only: add the line `BUTLER version=<v> login=ok user=<itch-user> by=<name>` from the packaging machine. `--gate-record` fails a G1 record without it (`submission_check.py butler`).
- G4 only: add the line `Final upload: <jam submission time, ISO with offset>`. `--gate-record` fails a G4 record without it, or with a time less than 3 h before the deadline (D-new-clock). It runs the same test as `check_card.py --clock --uploaded`.
- G4 only: add the line `Baked preset: <T-nn> | approved by <name> <link> | <bake_preset.py check --record output>` (D-new-workbench-debug). `--gate-record` fails a G4 record without it, or whose pasted check is not `PASS` for that preset. The preset is T-01 (BASE) unless a DECIDED row in `docs/decisions.md` says `Overrides: <T-nn>`; a row that only names the preset lifts nothing.
- A gate with an open P0 or P1 bug passes only as "Pass with named exceptions". A failing MVP item or a FAIL in PLAYTHROUGH, Repeat boots or Gate checks is never an exception: fix it or write Miss. Each exception has an owner and the hour it is fixed or cut. The status line repeats it until it closes.
- When a human passes a gate, tag `main` with an annotated tag: `git tag -a gate-G<n> -m "G<n>"`. The tag time is the gate's closed time for `--clock`.
- One hour before each gate, the Producer posts two questions on the tracker: "What slowed us since the last gate?" and "What do we change for the next one?". The answers fill the "What slowed us" line.
- UIFLOW (from G2, when the player screens exist): QA appends the UIFLOW line (`pipeline/ui/accessibility.md` section 4) for the Build commit to the record file. `--gate-record` re-checks it with `ui_check.py flow-check`: a build with no working Quit, or a mouse that does not work in menus, does not pass. From G1 the PLAYTHROUGH line needs `quit-play pass` (no Alt+F4) and `ui_check ci` needs a Quit in game code (U15).
- Machine records: the Repeat boots line must be a line of the record file as daily printed it, from the Win64 packaging machine named in the People table (a Mac DAILY line fails until a Mac fallback rule is DECIDED: Josh, pending); every first-parent commit since the last `gate-G<n>` tag (G1: `jam-start`) up to the Build commit has a passing DAILY line, re-run as `merge-check` (from G2 with client tests); the Gate checks UI line is re-run as `ui_check ci` (`--release` from G2) on the Build commit; the PLAYTHROUGH line is re-checked from the record, the zip named in the zip check must be on disk with that sha256 and pass `submission_check.py zip --gate` again, and `re-downloaded and launched: yes` needs the record's `LAUNCH <sha256>` line: unzip the re-downloaded zip on Windows and run `$env:SMOKE_ZIP="<zip>"; tools\ue\smoke.ps1 -Exe <unzipped exe>` on a machine other than the packaging one. launch-record writes the line only when the smoked exe is a file of that zip (same name and sha256), and `--gate-record` re-hashes that zip member. Fetch main before the launch smoke: values are checked at the commit the game was built from. The LAUNCH line's `SMOKE_EFFECTIVE` must be `platform=Windows`, `workbench=0`, compiled from the Build commit, from another host than the DAILY line, and pass `bake_preset.py effective` on that commit (G4: `--complete`, the bake tie).
- From G1 on (D-new-upload-g1; card 0.4b makes the first one): the Development zip goes to the team's Draft itch project, is downloaded again on another machine and launched. The link and the zip's SHA256 go in the record. A gate from G1 on without a link is not passed. After G1, `check_card.py --status` fails until a tracker comment has the link and `sha256=`.
- Verdicts: each discipline signs its own part (design: Game Designer human, art: the Art Director agent's `ART_GATE: PASS|FAIL` line from `art_check.py --gate` on the gate's `CAM_Eval_Arena` capture (no human art sign-off), UI: the `ui_check.py ci --release` line (G1: plain `ci`), tech: TD human). The Producer never fills another discipline's verdict. `--gate-record` fails a missing slot.
- Process change: a "What slowed us" answer seen at two gates in a row needs a card (with an owner), not "none". The Producer files it before the next gate.
- Incidents: every P0 closed and every main-red revert since the last `gate-G<n>` tag gets one entry: its cause class (AGENTS.md §6), the check that should have caught it, and a follow-up card (a new check or test) or "none" with a reason.
- Proposed outcome is exactly `Pass`, `Pass with named exceptions` (then `: <exceptions>` may follow) or `Miss` (then ` → cut <item>` may follow). Any other spelling or case fails. One line per key: a second `PLAYTHROUGH:` line fails. Late by over 2 h with `Cut fired: no` fails. The lateness is computed from the Gate line's `due` and `closed` times (ISO with offset); `due` is the Clock's time for that gate, and a typed `late by` that disagrees fails. `re-downloaded and launched:` passes only as exactly `yes`. Pass with named exceptions names at least one, and each playtest fail or verdict fail in it has `owner <name> by HH:MM`. Each `P<n>` reads exactly pass, fail or insufficient (`not run` or `crashed` fails). The Repeat boots DAILY line needs `clean-tree`, `build`, `test`, `validate`, `package`, `smoke`, `display` and `settings` = PASS, and every `Not checked` entry must be one `ue_run.py daily` writes (`NOT_CHECKED` there). An entry for a switch the docs leave off (Shipping smoke, `REF_HOST`, VERIFY tags, skipped display modes) never fails a gate. An entry for a switch past its gate in `tools/ue/daily-checklist.md` (input from Day 0, client tests from G2, restart cycles from G3) is a P1 bug: the record proposes `Pass with named exceptions` and lists it under Open P0/P1.
- `--gate-record` fails a record that proposes Pass while an MVP item fails, a verdict reads fail, Open P0/P1 is not none, PLAYTHROUGH, Repeat boots or Gate checks shows FAIL, or the upload was not re-downloaded and launched.
- For Pass and for Pass with named exceptions, `--gate-record` also fails (never an exception): an MVP item due at the gate that is missing or not `pass`; Build config other than Development; a playtest that is `insufficient`, or a P1, P2 or P4 `fail` (any other playtest fail needs named exceptions); a failure word in any case or a failing summary (`2 problem(s)`, `errors=3`, `exit 1`) in PLAYTHROUGH, Repeat boots or Gate checks; PLAYTHROUGH that is not the tool's `PASS: PLAYTHROUGH <sha>: G<n>: ... passed` line for the Build commit; Repeat boots that is not the Build commit's `DAILY <sha> | ... smoke=PASS(<n> map(s), repeat N/N)` line with N >= 5; Gate checks without `ui_check ci --release: PASS (0 problem(s))` (G1, before the player screens: `ui_check ci: PASS (0 problem(s))`) and the zip check's `PASS: <zip> config=Development platform=Win64 commit=<sha> sha256=<hash>` line for the Build commit and zip; an upload `sha256=` that is not that zip's sha256; a failure word on the MVP line; an open P0/P1 `#n` with no `owner <name> by HH:MM`.

### `pipeline/templates/tracker-table.md`

#### Tracker table template (Producer)

Keep this table in the body of the pinned "Jam tracker" issue. One row per MVP item in `docs/jam-brief.md` (12 rows).
`gh issue view <tracker #> --json body,comments | python3 tools/check_card.py --tracker` exits 0. `--status` runs the same check.

```
| MVP | Card | Status | Build sha | Playtest |
|---|---|---|---|---|
| 1 | #12 | todo | - | - |
| 2 | #13 | passed | 1a2b3c4 | P1 pass 2026-11-13 |
```

- Answer a question about one card in one line (answer, reason, next step). A gate gets the gate record, a cut gets its decision row. No multi-section report for a scheduling question.
- Status is one of: `todo`, `doing`, `review`, `closed`, `in build`, `passed`, `cut`.
- `in build` and `passed` need the commit sha of the packaged build where the item was seen.
- `passed` also needs `P<n> pass <YYYY-MM-DD>` from `pipeline/qa/playtests.md`, or `no P-test` when the item has none.
- Card names the issue (`#<n>`), except for a `cut` row.
- Every MVP item is APPROVED_P0 and never cut (`docs/jam-brief.md`). `--tracker` fails a `cut` row unless a DECIDED row in `docs/decisions.md` says `Overrides:` with every feature ID on that MVP line.
- A gate counts an item only when it is `passed`.

### `pipeline/templates/clock-workflow.yml`

```yaml
# Copy to .github/workflows/clock.yml (D-new-schedule). It does nothing until the human Producer sets the
# repo variable PIPELINE_CLOCK=on and TRACKER_ISSUE=<tracker issue number> (Settings > Variables).
# Each run fails red when a time check fails. tests/test_plan_checks.py keeps this file and clock.yml in step.
name: clock
on:
  schedule:
    - cron: "0 */3 * * *"
  workflow_dispatch:
permissions:
  contents: read
  issues: read
jobs:
  clock:
    if: vars.PIPELINE_CLOCK == 'on'
    runs-on: ubuntu-latest
    env:
      GH_TOKEN: ${{ github.token }}
      GH_REPO: ${{ github.repository }}
      TRACKER: ${{ vars.TRACKER_ISSUE }}
    steps:
      - uses: actions/checkout@v4
        with:
          lfs: false
          fetch-depth: 0   # gate-G<n> tags for --clock
      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"
      - name: Clock, gate lateness and cuts
        run: python3 tools/check_card.py --clock
      - name: Status line, tracker table and retro questions
        if: always()
        run: gh issue view "$TRACKER" --json body,comments | python3 tools/check_card.py --status
      - name: Cards over budget
        if: always()
        run: gh issue list --label doing --state open --json number,title,body | python3 tools/check_card.py --overrun
```

### `.github/ISSUE_TEMPLATE/task.yml`

```yaml
name: Task card
description: One agent-sized piece of work (see pipeline/templates/task-card.md)
title: "[UE-___] "
labels: ["task"]
body:
  - type: input
    id: mvp
    attributes: {label: "MVP item (number from docs/jam-brief.md), Day 0, or Stretch: <name>"}
    validations: {required: true}
  - type: input
    id: gdd
    attributes: {label: "GDD ref (section + short quote; \"none\" for tooling cards)"}
    validations: {required: true}
  - type: input
    id: gddrev
    attributes: {label: "GDD revision (the one in docs/gdd/CURRENT, e.g. 1.3)"}
    validations: {required: true}
  - type: input
    id: features
    attributes: {label: "Features (IDs from docs/feature-manifest.json; add \"Hook only\" for an interface + default flag with no behavior, OPEN/PROPOSED only; \"none\" for tooling cards)"}
    validations: {required: true}
  - type: textarea
    id: outcome
    attributes: {label: "Player outcome (the player sees X, does Y, can tell why; \"none\" for tooling cards)"}
    validations: {required: true}
  - type: dropdown
    id: owner
    attributes:
      label: Owner role
      options: [Producer, Dev Lead, Technical Director, Gameplay Dev, Integrator, Art Director, Asset Specialist, Audio, QA and Build, Game Designer, Encounter Designer, Story, Level Designer, UI and UX, Agent Ops]
    validations: {required: true}
  - type: dropdown
    id: reviewer
    attributes:
      label: Reviewer role (must differ from owner)
      options: [Producer, Dev Lead, Technical Director, Integrator, Art Director, Audio, QA and Build, Game Designer, Encounter Designer, Level Designer, UI and UX, Story, Agent Ops, Gameplay Dev, Asset Specialist]
    validations: {required: true}
  - type: input
    id: human
    attributes: {label: "Human (asked only when the card is stuck; kickoff merges)"}
    validations: {required: true}
  - type: textarea
    id: io
    attributes: {label: "Inputs and outputs (exact paths)"}
    validations: {required: true}
  - type: textarea
    id: context
    attributes: {label: "Context (what the code or asset next to Outputs does today, with file:line)", description: "Read it before you design the change. Write \"new files only\" if nothing exists yet."}
    validations: {required: true}
  - type: textarea
    id: lane
    attributes:
      label: "File lane, do-not-touch paths, binary files to lock"
      description: "Three lines, each read on its own by tools/check_card.py. Lane is paths or globs, or \"GitHub only\" for a card that writes no files; never none/everything."
      value: |
        Lane: 
        Do not touch: Content/UmbrellaElla/Maps/**
        Locks: none
    validations: {required: true}
  - type: textarea
    id: scope
    attributes: {label: "Out of scope (behaviors not to build; the reviewer rejects them)"}
    validations: {required: true}
  - type: input
    id: after
    attributes: {label: "After (cards that must merge first: #<n> or UE-<n>, comma separated; \"none\")", description: "check_card.py --blocked-by reads it, so a blocked card holds only the cards that wait on it (AGENTS.md section 6)."}
    validations: {required: false}
  - type: textarea
    id: usedby
    attributes: {label: "Used by (BPs, maps, widgets or components that read what this card changes; follow-up card IDs)", description: "Name the follow-up card (#<n> or UE-<n>), or write none if nothing outside this lane reads it."}
    validations: {required: true}
  - type: input
    id: needs
    attributes: {label: "Needs (build | tests | editor MCP | Windows packaging machine)"}
    validations: {required: true}
  - type: textarea
    id: done
    attributes: {label: "Done when (each line checkable)", description: "The builder runs these lines; the reviewer re-runs only what it doubts. A Python test line names its modules (python3 -m unittest tests.test_x); the full suite is CI's."}
    validations: {required: true}
  - type: input
    id: budget
    attributes: {label: "Budget and cut tier", description: "<n> min agent + <n> min human, then the cut tier. Agent over 120 min or human over 60 min: split the card.", placeholder: "90 min agent + 20 min human, MVP"}
    validations: {required: true}
  - type: textarea
    id: unknowns
    attributes: {label: "Unknowns (Decision needed / Why it matters / Proposed test / Choice; \"none\" if none)"}
    validations: {required: true}
```

## Automation

### `.github/workflows/blocked-report.yml`

```yaml
# Daily: for every open card with the `blocked` label, post on the tracker the cards that wait on it
# (tools/check_card.py --blocked-by). Every other card keeps working. Does nothing until the repo variable
# TRACKER_ISSUE is set. The logic lives in tools/lane_guard.py (tests/test_lane_guard.py).
# Direct local build (docs/build/MODE says `direct`, or no MODE file and HANDOFF.md exists): skipped, there are no cards.
name: blocked-report
on:
  schedule:
    - cron: "0 12 * * *"
  workflow_dispatch:
permissions:
  contents: read
  issues: write
jobs:
  mode:
    if: vars.TRACKER_ISSUE != ''
    runs-on: ubuntu-latest
    timeout-minutes: 5
    outputs:
      direct: ${{ steps.mode.outputs.direct }}
    steps:
      - uses: actions/checkout@v4
        with:
          lfs: false
      - name: Build mode from docs/build/MODE (direct = local build lead merges, no cards or PRs)
        id: mode
        run: |
          if [ -f docs/build/MODE ]; then mode=$(tr -d '[:space:]' < docs/build/MODE); elif [ -f HANDOFF.md ]; then mode=direct; else mode=cards; fi
          if [ "$mode" = direct ]; then direct=true; else direct=false; fi
          echo "build mode: $mode (direct=$direct)"
          echo "direct=$direct" >> "${GITHUB_OUTPUT:-/dev/null}"
  blocked:
    needs: mode
    if: vars.TRACKER_ISSUE != '' && needs.mode.outputs.direct != 'true'
    runs-on: ubuntu-latest
    timeout-minutes: 10
    env:
      GH_TOKEN: ${{ github.token }}
      GH_REPO: ${{ github.repository }}
      TRACKER: ${{ vars.TRACKER_ISSUE }}
    steps:
      - uses: actions/checkout@v4
        with:
          lfs: false
      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"
      - name: Post each blocked card and the cards that wait on it
        run: python3 tools/lane_guard.py blocked --tracker "$TRACKER"
```

### `.github/workflows/main-red.yml`

```yaml
# Revert-first (AGENTS.md section 6, D-new-port-2). On each push to main, run the pipeline checks; if they fail,
# tools/lane_guard.py opens a revert PR of the breaking squash commit and comments on the tracker issue naming the
# integration owner. Repo admin: allow "GitHub Actions to create and approve pull requests" (Settings > Actions),
# and set the repo variable TRACKER_ISSUE. The logic lives in tools/lane_guard.py (tests/test_lane_guard.py).
# GITHUB_TOKEN caveat (final-10 A H3): GitHub starts no workflow run for a PR opened with GITHUB_TOKEN, so the
# required `checks` job would never report on the revert PR. Workaround: add a REVERT_TOKEN secret (a fine-grained
# PAT or GitHub App token: contents and pull-requests write); the step below uses it. Without it, the integration
# owner closes and reopens the revert PR (a human event starts pipeline-checks).
# Direct local build (docs/build/MODE says `direct`, or no MODE file and HANDOFF.md exists): skipped. The build lead
# pushes main only after the local gate passes, and pipeline-checks still reports a red main.
name: main-red
on:
  push:
    branches: [main]
permissions:
  contents: write
  pull-requests: write
  issues: write
concurrency:
  group: main-red
  cancel-in-progress: false
jobs:
  mode:
    runs-on: ubuntu-latest
    timeout-minutes: 5
    outputs:
      direct: ${{ steps.mode.outputs.direct }}
    steps:
      - uses: actions/checkout@v4
        with:
          lfs: false
      - name: Build mode from docs/build/MODE (direct = local build lead merges, no cards or PRs)
        id: mode
        run: |
          if [ -f docs/build/MODE ]; then mode=$(tr -d '[:space:]' < docs/build/MODE); elif [ -f HANDOFF.md ]; then mode=direct; else mode=cards; fi
          if [ "$mode" = direct ]; then direct=true; else direct=false; fi
          echo "build mode: $mode (direct=$direct)"
          echo "direct=$direct" >> "${GITHUB_OUTPUT:-/dev/null}"
  revert-first:
    needs: mode
    if: needs.mode.outputs.direct != 'true'
    runs-on: ubuntu-latest
    timeout-minutes: 30
    env:
      GH_TOKEN: ${{ secrets.REVERT_TOKEN || github.token }}
      GH_REPO: ${{ github.repository }}
      TRACKER: ${{ vars.TRACKER_ISSUE }}
    steps:
      - uses: actions/checkout@v4
        with:
          lfs: false
          fetch-depth: 0
      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"
      - name: Pipeline checks
        id: checks
        run: |
          python3 tools/pipeline_check.py
          python3 -m unittest discover -s tests
      - name: Main is red, open the revert PR and tell the integration owner
        if: failure() && steps.checks.outcome == 'failure'
        run: python3 tools/lane_guard.py revert --sha "$GITHUB_SHA" --tracker "$TRACKER"
```

## Commands and checks

### `tools/check_card.py`

Usage text from the file:

```text
Producer's task-card linter. A card with an empty or vague field is not ready (AGENTS.md section 4).

Accepts both shapes a card comes in:
  template   "Field: value" lines as in pipeline/templates/task-card.md (fields are read from it)
  issue form "### <label>" sections as GitHub renders .github/ISSUE_TEMPLATE/task.yml
             (the card ID then comes from the issue title, "[UE-012] ...", passed with --title)

Checks:
  field     every field present, not empty, not a template placeholder (<...>, UE-000, TBD, _No response_)
  id        ID looks like UE-<number> (UE-000 is the template; Day-0 cards are UE-0.<n>, e.g. UE-0.4a)
  mvp       MVP item is a number in the docs/jam-brief.md MVP list, "Day 0", or "Stretch: <item from the brief>";
            a numbered item whose brief line names feature IDs needs one of them in Features
  owner     Owner role is in the AGENTS.md roles table: an agent role, never a person (agents own all the work; a
            person's part is a `HUMAN <kind>:` Done-when line, pipeline/human-checkpoints.md "Checkpoint kinds").
            Reviewer role is an agent role too (a fresh session reviews; no "Human only" reviewer); owner and
            reviewer differ
  lane      File lane names at least one path or glob; "none", "everything", "all" and the whole repo
            are rejected. "GitHub only" is allowed for cards that write no files (Day-0 0.1, 0.11).
            On issue-form cards the lane field holds three lines, each read on its own:
            `Lane: ...`, `Do not touch: ...`, `Locks: ...`
  done      Done when has at least one line with a measurable value: a number with a unit or comparison,
            an automation test name UmbrellaElla.<Area>.<Behavior>, SMOKE_OK, "marked DECIDED", or a
            command result ("exits 0", "prints PASS", "lists 8") on a line that names the command
            (`backticks`, tools/..., *.py/*.sh/*.ps1, gh/git/grep). A line that says "works" /
            "looks good" / "feels right" needs one of these; a hedge ("eventually", "should") always fails, and so
            does a line that asks for the full unit suite (`unittest discover`: CI's job, never a card session's)
  GDD ref   tooling cards write "none" ("n/a" is read as an unfilled placeholder)
  gdd       GDD revision names a snapshot in docs/gdd/ (GDD-<rev>.md). A card on an older revision than docs/gdd/CURRENT
            fails only if one of its Features changed between the two (tools/gdd_impact.py); other cards stay valid
  features  Features lists IDs from docs/feature-manifest.json, or "none" (tooling cards; a numeric MVP card needs IDs).
            Every ID must be implementation_authorized, unless the card says "Hook only" (interface + flag at its
            manifest default, no behavior) and the ID is OPEN or PROPOSED
  budget    Budget reads "<n> min agent + <n> min human"; agent time over 120 min or human time over
            60 min means split the card
  usedby    Used by is "none ..." or names the follow-up card (#<n> or UE-<n>)
  cap       a count of flipbook frames above the total cap in docs/jam-brief.md needs a decision row
            (D<n> / D-new-...) on the card
  story     a card whose Owner role is Story names, in Done when, `tools/story_check.py` with its PASS and the final
            `STORY_CRITIC: PASS` line of a separate critic session (pipeline/roles/story.md): no story card closes
            on the builder's word alone; tools/check_pr.py rule story asks for the same lines on its PR
  spike     a card titled 'Spike: ...' / 'Spike D<n>: ...', or with a 'Decision row:' line, needs
            'Decision row: D<n>', 'Decides it:' with an if/then, and 'Time box:' of at most SPIKE_MAX_MIN
            (pipeline/templates/spike-card.md)

Blocked card:
  --blocked-by C  prints only the cards that wait on card C, directly or transitively, one per line, and nothing
                  else: Day-0 rows whose After lists it, plus (with --issues FILE, gh issue list --json
                  number,title,body) filed cards with an 'After: <ids>' line naming it or named in its Used by.
                  Every other card keeps working. Exit 0; 2 = unknown card

Board and plan checks (each prints problems and exits 1 on any):
  --clock         docs/jam-brief.md Clock: deadline, gate times G1-G4, hard stop and card 0.9 cutoff are set;
                  gates in order; G4 at least MARGIN_H hours and G3 at least TUNE_DAY_H hours before the
                  deadline. With gate tags (gate-G<n>), a gate closed or still open more than CUT_AFTER_H
                  hours past its time prints CUT FIRES. --uploaded <ISO>: the jam-page time of the final
                  upload is at least MARGIN_H hours before the deadline. From the Card 0.9 cutoff on,
                  .github/workflows/clock.yml must exist and match pipeline/templates/clock-workflow.yml
                  (Day-0 card 0.16, D-new-clock-install)
  --people        People and Team hours tables: no TBD, no "(proposed)", Confirmed = yes or default (agent), hours as 8/8/8/6;
                  every teammate holds a People seat, nobody holds more than BLOCKER_SEATS_MAX BLOCKER seats;
                  away windows are 'none' or 'D<n> HH:MM-HH:MM', comma-separated; more than TEAM_MAX
                  Team hours rows, or fewer than CPP_MIN rows with UE C++ = y, prints a WARN line (exit code
                  unchanged; D-new-team-size, D-new-cpp-team)
  --hours --day N open cards (gh issue list JSON on stdin): human budget minutes per person vs RESERVE of
                  that person's Team hours for day N, minus their away windows on day N; an Asset
                  Specialist card's Used by card must be open
                  with a Budget, so the integration time is counted too
  --lanes         open cards (gh issue list JSON on stdin): no two share a lane glob, a .umap or a lock
                  (test-map.md, decisions.md and jam-brief.md are row-scoped and not counted);
                  no Stretch card while a numeric MVP card is open (no override; stretch waits for every MVP card)
  --status        Jam tracker (gh issue view --json body,comments on stdin): a status line with every
                  field of the producer.md format was posted in the last STATUS_MAX_H hours; 'Next gate' is
                  on track / at risk / will miss plus a reason; 'will miss' needs a 'Cut proposed: <item>'
                  comment since the last gate time; 'Absences next 12h' is 'none' or a name; once
                  the Clock G1 time has passed, a comment holds the itch test upload (link + sha256=<64 hex>);
                  within RETRO_LEAD_H of a gate, both retro questions are on the tracker; --tracker runs too;
                  and submission_check.status_hook (devlog, footage and theme for the day just ended)
  --tracker       tracker issue body: the MVP table (pipeline/templates/tracker-table.md) has one row per MVP
                  item, a status from TRACKER_STATUS, a sha for 'in build'/'passed', a playtest for 'passed'
  --gate-record   tracker comments: the newest 'Gate: G<n>' comment has every pipeline/templates/gate-record.md
                  line filled, and Risks has '<n> fired yes/no' per Top risks row (a yes names an owner);
                  a G1 record also needs a BUTLER line that passes submission_check.butler_problems;
                  a G4 record also needs 'Final upload: <ISO>' at least MARGIN_H hours before the deadline
                  and 'Baked preset: T-nn | bake_preset check: PASS preset=T-nn ...' (D-new-workbench-debug).
                  In a practice repo (tools/practice.py) a G4 record always fails.
                  Machine records (final-9 B H4, H5): the Repeat boots line is a line of the record file, the
                  PLAYTHROUGH line is re-checked from it (from G2 the UIFLOW line for the Build commit too: quits,
                  mouse in menus), the zip is on disk with that sha256, and 'launched: yes'
                  needs the record's LAUNCH line (Win64 smoke of that zip) whose SMOKE_EFFECTIVE passes on the
                  Build commit (complete at G4). Run it on the packaging machine, or pass --records FILE (repeat)
  --queue         cards in review (gh issue list --label review JSON on stdin): no Human has more than
                  QUEUE_MAX. Prints the count per human for the status line
  --overrun       cards in doing (gh issue list --label doing JSON on stdin): time with the doing label
                  (from each issue's timeline, fetched with gh api) vs agent + human Budget. Prints
                  OVER BUDGET past the budget and fails with OVERRUN #n +NN min past OVERRUN_MIN over it.
                  An issue with no Budget (a bug) is timed against 0 min
  --hardstop      commits on main (origin/main if present) in the last 24 h (or --since) whose time, in the
                  Clock's time zone (the deadline's UTC offset), falls inside the Hard stop window

Usage:
  python3 tools/check_card.py card.md [--title "[UE-012] ..."]
  python3 tools/check_card.py --event          # GitHub Actions issue event ($GITHUB_EVENT_PATH)
  gh issue view 12 --json title,body | python3 tools/check_card.py --json-stdin
  python3 tools/check_card.py --clock | --people
  gh issue list --label task --state open --json number,title,body --limit 200 | python3 tools/check_card.py --lanes
  gh issue list --label task --state open --json number,title,body --limit 200 | python3 tools/check_card.py --hours --day 2
  gh issue view <tracker #> --json body,comments | python3 tools/check_card.py --status | --tracker | --gate-record
  gh issue list --label review --state open --json number,title,body | python3 tools/check_card.py --queue
  gh issue list --label doing --state open --json number,title,body | python3 tools/check_card.py --overrun
  python3 tools/check_card.py --hardstop [--since 2026-11-14T08:00-05:00]
  python3 tools/check_card.py --clock --uploaded 2026-11-16T13:05-05:00
  python3 tools/check_card.py --blocked-by 0.3 [--issues open.json]   # one line per card that waits on 0.3
  gh issue list --label needs-human --state open --json number,title,labels,comments | python3 tools/check_card.py --needs-human
                  the human queue (pipeline/human-checkpoints.md): one line per labelled issue; exit 1 if one has no
                  `NEEDS HUMAN: <who/role> <what> <link> <YYYY-MM-DDTHH:MMZ>` comment. An ask no human answered in 2 h
                  ends `GRACE EXPIRED -> <role>` (the Producer's hourly sweep); a human-only kind ends `HUMAN ONLY`
Exit 0 = ready, 1 = problems, 2 = usage/input error.
```

Run in CI by:

- `.github/workflows/pipeline-checks.yml`: Task card is ready (Producer)
- `.github/workflows/pipeline-checks.yml`: Linked task card is ready (Producer)

Tests: `tests/test_affected_tests.py`, `tests/test_audio_loop.py`, `tests/test_check_card.py`, `tests/test_day0_cards.py`, `tests/test_doc_consistency.py`, `tests/test_final10_fixes.py`, `tests/test_final8_fixes.py`, `tests/test_final9_fixes.py`, `tests/test_honest_jam.py`, `tests/test_lane_guard.py`, `tests/test_pipeline_check.py`, `tests/test_plan_checks.py`, `tests/test_practice.py`, `tests/test_smoke_visual.py`, `tests/test_story_check.py`, `tests/test_ui_check.py`

### `tools/lane_guard.py`

Usage text from the file:

```text
Keep lanes running in parallel (AGENTS.md section 6). Stdlib only; the logic for two workflows.

  revert   .github/workflows/main-red.yml, when the pipeline checks fail on a push to main.
           Opens a revert PR of the breaking commit (each card is one squash commit, so one `git revert`)
           on branch revert-<sha7>, and comments on the tracker issue naming the integration owner from the
           docs/jam-brief.md People table, who merges it within REVERT_MIN minutes. The card goes back to doing.
           Skips when a revert PR for that commit is open. A red revert commit gets a comment, never a revert.
  blocked  .github/workflows/blocked-report.yml, daily. Posts one tracker comment: for every open card with
           the `blocked` label, the cards that wait on it (tools/check_card.py --blocked-by). Nothing else waits.

           The PR body has every check_pr.py section and `Revert of: <sha>`; check_pr passes it when the diff is exactly
           the inverse of that commit (final-10 A H3).
           GITHUB_TOKEN caveat: GitHub starts no workflow for a PR that GITHUB_TOKEN opened, so the required `checks`
           job never reports on it. main-red.yml passes the REVERT_TOKEN secret (a fine-grained PAT or GitHub App
           token with contents and pull-requests write) when it is set; without it, the integration owner closes and
           reopens the PR (a human event starts the checks).
Usage: python3 tools/lane_guard.py revert --sha SHA [--tracker N] [--dry-run]
       python3 tools/lane_guard.py blocked --tracker N [--dry-run]
--dry-run prints the git and gh commands instead of running them. Needs gh with GH_TOKEN in Actions.
Exit 0 = done (or nothing to do), 1 = a command failed, 2 = usage error.
```

Run in CI by:

- `.github/workflows/blocked-report.yml`: Post each blocked card and the cards that wait on it
- `.github/workflows/main-red.yml`: Main is red, open the revert PR and tell the integration owner

Tests: `tests/test_final10_fixes.py`, `tests/test_honest_jam.py`, `tests/test_lane_guard.py`

### `tools/status_board.py`

Usage text from the file:

```text
Status board: one static page that shows where the jam stands. Stdlib only.

The Producer regenerates it every jam hour (pipeline/how-to-run-the-jam.md) and pastes or links it on the tracker.
It never writes to GitHub. It shows:
  Cards        every task card (issue labelled `task`): state from its labels (todo | doing | review | blocked | cut |
               superseded; closed = done), owner role, the card's Human, and a needs-human mark
  Needs human  each open needs-human card: who and what, from its newest `NEEDS HUMAN: <who/role> <what> <link>`
               comment (check_card.py --needs-human reads the same line)
  Sessions     which role and machine is on which card: the newest journal `start` per card (tools/journal.py),
               open until an `end`; with --source gh also the newest `ROLE: <role> | session ...` comment
  Open PRs     each open PR, its card (branch ue-<id>-... or `Closes #n`) and its checks: pass | fail | pending | none
  Gates        G1-G4 from the Clock in docs/jam-brief.md: due time, and closed (annotated tag gate-G<n>), record
               posted (a tracker comment `Gate: G<n> ...` with its Proposed outcome), OVERDUE, due or TBD

Sources:
  --source gh        gh issue list / gh pr list (needs a logged-in gh; the network)
  --source local     local git (ue-* branches, gate-G* tags) and the journal; no network, no GitHub
  --from-json DIR    saved gh output instead of calling gh: DIR/issues.json and DIR/prs.json (tests, offline)
The journal (JOURNAL_DB, else .pipeline/journal.db; --journal FILE) is read in every mode when it exists.

Problems (exit 1, the page is still written): a needs-human card with no NEEDS HUMAN comment, a card with two
state labels, a doing card with no session in the journal or comments.

Usage: python3 tools/status_board.py [--source gh|local] [--from-json DIR] [--repo OWNER/NAME] [--out FILE]
       [--html] [--now ISO] [--journal FILE] [--root PATH]
Default out: Saved/status-board.md (Saved/ is git-ignored); --html writes HTML instead (default .html name).
Exit 0 = written, no problems; 1 = written, with problems; 2 = unreadable input (bad JSON, gh failed, no source).
```

Tests: `tests/test_honest_jam.py`, `tests/test_practice.py`, `tests/test_status_board.py`
