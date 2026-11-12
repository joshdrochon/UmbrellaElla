> Generated from `docs/audit.md` at `a11903f` — edit the sources, not this file.
> Rebuild: `python3 tools/export_package.py`. Check: `python3 tools/export_package.py --check`.

# Audit: AI agent pipeline for the Umbrella Ella jam (issue #11)

**Auditor role:** Staff AI-native software engineer. The job was to find every gap between the inherited
pipeline package, Rick's proposed jam pipeline, the GDD and the target key art. The bar: the pipeline,
prompts and guardrails are strong enough that agents can build the jam game in one pass. The fixes are
on the audit branch.
**Prepared by:** Josh (with Claude Code), 2026-11-06. **Status:** draft for team review. Nothing is pushed until the team confirms.
**Sources:** see `docs/references.md` (R1–R11). Every source was read only. Nothing shared was edited.
**Snapshot.** This is the 2026-11-06 audit (GDD Draft 1.0, 8 role cards). Counts and game facts in §2-§10 are as of
then. Current state: AGENTS.md (roles), `docs/gdd/CURRENT` (GDD 1.3), `docs/coverage-map.md`, `evals/reviewer/results.md`.

## 1. Method
- Read all 13 files in the inherited pipeline line by line: 77,707 words.
- The review was split across four reviewers: production/studio, technical/Unreal, art/design, and eval bars. Each finding cites `file:line`. The reviewers' notes are kept outside the repo.
- Rick's review summary and pipeline doc, the GDD (Umbrella Ella tab) and the key art were the baseline.
- Each of Rick's findings was confirmed with a citation before going further.
- Counts below are measured with grep across all 13 files using one term list. They are floors, not exact totals.

## 2. Verdict
The inherited pipeline is careful, honest governance writing. It is not a jam pipeline. It describes a different game
in a different engine, it puts a human approval in front of almost every step, and nothing in it runs.
Round 1 kept about 30 of its rules and Rick's 7 roles. Round 2 went back through all 13 files and ported about 60 more, in Unreal terms and checkable form (`docs/port-log.md`). The result is a short, checked pipeline:
- About 2,000–3,500 words of context per task (AGENTS.md + brief + one role card, plus the Unreal rules for engine work), down from about 78,000.
- 8 role cards (Rick's 7 plus an Integrator) with fixed inputs, outputs and stop rules.
- Scripts that fail when the rules are broken, and tests proving those scripts fail.

## 3. Measured facts about the package
| Measure | Result |
|---|---|
| Size | 77,707 words (≈100k tokens). An agent told to "read the charter and consult applicable pipelines" spends most of its context on governance |
| Unity-specific terms (Unity, MonoBehaviour, ScriptableObject, asmdef, PlayMode, EditMode) | 219 hits. Development Pipeline 82, Technical Development Pipeline 81, Art Pipeline 25 |
| Other-game terms (Liquid Neon, Puro Búho, bartender, restaurant, hospitality, Martini, venue, guests, ...) | 172+ hits. Design Pipeline 47, Production Pipeline 42, Technical Development Pipeline 34, README 23 |
| Mentions of Unreal / UE5 / Blueprint / uasset | 1 (a documentation link in the Art Director charter, line 1336) |
| Mentions of Umbrella, Ella, the owl or a boss | 0 |

## 4. Findings
Severity: **blocker** = agents build the wrong game or stall. **high** = large time or quality loss.

### 4.1 Rick's findings, confirmed
| Finding | Evidence |
|---|---|
| The other game leaks in | README:22–37 sets the project identity to "Bartender Game / Liquid Neon". Production Pipeline:30–44 calls the bar-sim requirements "inherited product requirements", i.e. binding |
| Unity-specific | 219 hits (section 3). Production Pipeline:256 "Use Unity for host and presentation" |
| Too large | 77,707 words |
| Describes a workflow but enforces nothing | README:158 "Publication does not establish … CI or other enforcement". Also Technical Development Pipeline:13 and Development Pipeline:22 |
| README approval status conflicts | README:5 "APPROVED — Active" vs README:365 "Review Candidate; final EP approval … pending" |
| Lead Developer adoption clause names the Art Director | LeadDeveloper:1083 "This charter governs the Art Director role" |
| "UEProject" folder describes Unity files | Technical Development Pipeline:168–172: `UEProject/Assets/…`, "Unity composition adapters" |

### 4.2 New blockers
| # | Finding | Evidence | Fixed by |
|---|---|---|---|
| B1 | **The package blocks its own use.** Design docs "do not authorize implementation", every Push needs two Executive Producer gates, and only the next Push may be planned. An obedient agent cannot start | README:199; Project Instructions:19,22; Technical Development Pipeline:8,128; LeadDeveloper:223 | AGENTS.md §4: routine work inside a card needs no further approval. Humans approve only scope, decisions, deletions, art direction and submission |
| B2 | **Anti-deadline philosophy** | Production Pipeline:28, 376 "Fixed time is not an intrinsic quality standard"; README:331 | jam-brief "Hard limits"; producer.md cut rule: "The deadline is fixed; scope moves" |
| B3 | **Wrong art north star, presented as binding.** "handcrafted, contemporary pixel art … restrained neon" | Production Pipeline:42; Art Pipeline:56 | `pipeline/art/art-bible.md` from the key art. `tools/art_check.py` fails off-style captures |
| B4 | **Conflicts have no tiebreaker.** Every conflict escalates, so the GDD vs key-art conflict alone stalls Day 1 | README:53; Studio Pipeline:45 | AGENTS.md §2 precedence list. D0 decided: key art = look, GDD = mechanics |
| B5 | **Integration has three owners, so no one owns it.** No one owns QA, audio or the level layout either | README:144,147; Project Instructions:13; Production Pipeline:83–84 | jam-brief People table (integration owner, packaging owner, playtest lead). qa-build.md |
| B6 | **No handling of Unreal binary assets.** No LFS, locks or file ownership. `.uasset`/`.umap` cannot merge, so two agents on one map lose work | 0 hits for uasset/LFS/lock in production docs | `.gitattributes` (LFS + lockable), lanes on every card, unreal-rules.md "Binary assets" and "MCP" sections, pipeline_check `lfs` check |
| B7 | **Bar-sim acceptance gates.** M2 is "the Martini reference scenario". "Mandatory design checks for MegaJam2026" are restaurant checks | Production Pipeline:151–166, 250 | Four day-gates tied to the GDD MVP (producer.md), playtests P1–P9 |
| B8 | **No numbers anywhere.** Six rules forbid agents from inventing thresholds, frame rates or pixels-per-unit, so "done" has no definition | Art Pipeline:26,305,452; GameDesigner:1430,1673,1810 | Prototype numbers in art-bible.md, style.json, D20 tuning defaults, the 16.7 ms frame budget. Every number is marked as changeable only on measured evidence |
| B9 | **The docs discourage building enforcement.** "do not make custom automation a prerequisite" | Studio Pipeline:172,224; Project Instructions:25 | tools/ and CI. AGENTS.md §8 lists every check |
| B10 | **Referenced files don't exist or point at another project.** The "binding" TDD is not in the package, the GDD sections cited (§§3–116) belong to the bar-sim GDD, `Studio Pipeline.md` is really `Studio Pipleine.md`, and there are personal home-folder paths | Development Pipeline:59,279,813; README:234 | Not carried over. AGENTS.md read order names only files that exist |

### 4.3 High
- Seven different state vocabularies across files (Project Instructions:22, Studio Pipeline:93, Production Pipeline:90,214, Producer:167,199). Replaced by one: `todo → doing → review → done (+blocked)`.
- Jargon an agent will misread. `!Producer` reads as "not Producer". "Push" collides with `git push` (31 hits). "EP" appears 88 times and is expanded once. "RC" is never defined. Replaced with `ROLE: <name>` and plain words.
- Milestone closure contradicts itself. Producer:86 grants it; Studio Pipeline:149 and Project Instructions:22 deny it. Now one human (the scope decision-maker) closes each gate.
- The Art Director charter claims "APPROVED by Sutdio Heads", an approval our team never gave (the typo appears 4 times).
- Development Pipeline naming rules (`_camelCase`, 4 spaces) conflict with Epic's C++ coding standard. Not carried over.
- No licensing or provenance rules for AI or third-party art. The only mention is a folder comment (Art Pipeline:226). Added a provenance ledger as a hard gate, plus D14 (jam AI-art rules).
- Usage meters tied to one product ("At START and END of substantial Codex work retrieve live five-hour/weekly allowances", Project Instructions:29). Replaced by per-card time budgets and stop rules.

### 4.4 Gaps in Rick's pipeline doc and the GDD (not the inherited pipeline)
| Gap | Fixed by / owner |
|---|---|
| Rick's doc says "test the reviewer with known problems" but defines no test | `evals/reviewer/`: 12 planted-defect cases, 3 clean cases, a scorer and a runner. Results in §6 |
| Rick's doc notes GitHub instructions don't enforce themselves, but no enforcement is designed | CI workflow, pipeline_check, check_pr, issue form, PR template, CODEOWNERS example |
| No task card format, cadence, cut list, submission checklist | task-card.md, producer.md, jam-brief.md, qa-build.md |
| GDD "colorful, storybook" vs key art | D0 decided. D16 asks the GDD owner to edit the line (agents never edit shared docs) |
| GDD falling attack vs key-art shooting; boss stretch vs centerpiece; vertical vs side-on | D1, D2, D9, D15, with defaults so work is not blocked |
| GDD's 5 open design questions | D5, D9, D10, D17–D20 with defaults |
| Who decides scope, integrates and packages (issue #4 requires it) | D12, jam-brief People table |

## 5. Eval bars → this pipeline
Each bar is a practice that makes a check trustworthy, stated on its own merits.

| Bar | Adapted for the jam | Status |
|---|---|---|
| "A gate is only real once you have watched it fail" | Every check has tests that plant a defect. We also broke the checks on purpose (loosened art thresholds, emptied the leak list, disabled the hue gate) and confirmed the tests failed | Built and run |
| Golden set + boolean rubric + regression gate (fail on a drop) | Reviewer eval: 35 cases (28 defective incl. 5 evidence-only, 7 clean); 20 written by a separate agent. Art gates are pass/fail per gate, no 1–10 scores | Built. 35 cases, not 50 |
| Judge must catch 100% of a seeded set; any defect graded safe is a build failure | Reviewer bar: every blocker caught, recall ≥ 0.80, every defective change blocked, clean approve ≥ 0.80 | Built and run (§6) |
| Judge calibration pinned to (model, rubric version); stability re-runs | Art judge calibration set (known-good + 4 known-bad generated from the key art); re-run on any model/prompt change; 3-run stability check | Built; needs the key-art file to generate the set |
| Blind X/Y critic, pick + biggest gap, no numeric scores | Art Director revision review, Dev Lead "biggest_gap" field | Written into role cards |
| Sweep ≥ 3 values, never one operating point | Gameplay Dev tests sweep tuning values at ≥ 3 settings | Written; enforced by review |
| DONE = pasted output from a runnable command | AGENTS.md §5, check_pr.py, check_automation_report.py (exit code alone proves nothing) | Built |
| Measured pixel gates for visuals | art_check.py: palette ΔE, gold/rust hue bands, accent area, silhouette share | Built; palette provisional until measured |
| Cap on builder/critic cycles | No round cap; needs-human after 3 rounds in a row with no improvement (D-new-no-round-cap, supersedes D21) | Decided 2026-11-10 |
| 60 fps HARD gate | ≤ 16.7 ms in a Development package on the packaging machine (qa-build.md) | Written; runs once a project exists |
| Human gates on irreversibility, not severity | Humans approve scope, decisions, deletions, art direction, submission. Everything reversible is autonomous | Written |
| Decision register with defaults | `docs/decisions.md`: 23 open rows with a default, an owner and a Blocks date; 111 settled rules | Built (consolidated, §9c) |
| Gates for every role, each watched failing | TD: `module_check.py` (module boundaries, the assembly-definition equivalent). Producer: `check_card.py`. Art: `art_check.py` thresholds + flat-frame gate, `sprite_check.py`, blind pairwise judge protocol. QA: test-map with merged-only `--require`, smoke log checks. PR: evidence header, stale commit, package required by path | Built; 202 tests |

## 6. Reviewer eval result (measured)
Full history: `evals/reviewer/results.md`. Reviewer = `pipeline/roles/dev-lead.md` through `claude -p`, isolated from the repo.
- **Round 2, final three runs: PASS, all three.** 35 cases: 29/29 planted defects found, 18/18 blockers, 30/30 defective changes blocked, 7/7 clean changes approved.
- Across 10 round-2 runs, no defective change was ever approved. Failing runs came from clean cases or evidence lines that broke our own rules (fixed in the cases), one speculative finding and one `checks_seen` ambiguity (both fixed in the card). Every fix is logged with its run id.
- Round 1 (15 cases, 14 runs) also never missed a planted defect.
- **Round 5 (consolidation pass), 55 cases: PASS ×3** (runs 215814, 222138, 222142). Recall 1.0 / 0.976 / 1.0, 20/20 blockers, 41/41 defective changes blocked, clean approved 13/14, 12/14, 12/14. Clean cases 15 and 44 still describe the old game and were rejected 2/3 each.
- Not yet measured: Codex as the reviewer (`--cmd "codex exec -"`; not installed here), other models, real jam PRs.

## 7. What this pipeline does not do yet (plainly)
- **No Unreal project exists yet, and none may before Nov 12** (jam rule, D39). The build, test and package wrappers are checked only against a fake engine. None has run against UE 5.8.4.
- **Unreal facts were checked against Epic's docs, not a 5.8.4 install.** 16 [VERIFY] tags remain across `pipeline/unreal-rules.md` and `pipeline/unreal/`; cards 0.4a, 0.4b and 0.6d close them.
- **The Windows scripts (`tools/ue/*.ps1`) have never run.** PowerShell isn't on this Mac. The .sh versions and the shared `tools/ue_run.py` are tested with a fake engine.
- **The CI sprite check pulls only the PNGs a PR changes** (D-new-ci-lfs). It has not run on GitHub yet.
- **The palette is not measured yet.** The key art is now in the repo through LFS; card 0.7 measures it and raises `paper_texture_min`.
- **CI cannot run Unreal.** Engine checks are local and rely on logs pasted into PRs.
- **Blueprint logic and binary asset changes can't be diffed.** The mitigations are thin Blueprints, text sidecars and locks.
- **Playtests need humans.** Agents can't judge fun; the pipeline only records it.
- **No CODEOWNERS and no branch protection yet.** Both need a human with admin rights (cards 0.0 and 0.17).
- **The design has open items.** GDD 1.3 is approved (Richard, 8 Nov); its open items are rows in `docs/decisions.md`. Card 0.19 checks the theme fit.
- **`check_card.py` does not yet check that a card's Human is a named person** from the People table; the Producer swaps seat names for names when filing (`pipeline/day0-cards.md`).

## 8. Keep / don't keep, file by file
The inherited pipeline stays linked (R3) as reference for humans. Agents load none of it. The rules marked "keep"
were rewritten into our files (right-hand column), and the Unity and bar-sim specifics were removed.

| Inherited file (words) | Keep (now lives in) | Don't keep (why) |
|---|---|---|
| Project Instructions (907) | One role per conversation is not an independent review (PI:2) → AGENTS.md §3. Diagnose once, no repeated failed attempts (PI:30) → AGENTS.md §6. Evidence/handoff fields (PI:33) → PR template | `!Role` activation (reads as "not"), "Push" and two Executive Producer gates per batch (PI:19), product-specific usage meters (PI:29), "Liquid Neon" source list (PI:12) |
| README v1.5 (2,338) | Never claim to have read files you couldn't access (:111). Authority by subject: gameplay → GDD, look → art (:162) → AGENTS.md §2 | Bar-game identity (:22–37), "rather than optimize against an arbitrary launch deadline" (:331), conflicting status (:5 vs :365), PuroBuho naming/root (:215, :294) |
| Studio Pipeline (4,848) | "A command must not be reported as executed unless its execution was observed" (:490), "do not represent an attempted change as completed" (:320) → AGENTS.md §5. Don't impersonate another discipline's approval (:69) | 110 lines of change-record rules with no check (:226–336), anti-automation rules (:172, :224), compaction thresholds the agent can't see (:534) |
| Production Pipeline (7,782) | "The integration build is the measure of game progress" (:321), "a local screenshot or generated patch alone is not done" (:224), Definition of Ready (:222), P0–P3 defect ladder (:308), status line (:382), evidence card (:510) → producer.md, qa-build.md, AGENTS.md §5 | Bar-sim north star and "inherited requirements" (:20, :30–44), pixel-art/neon (:42), Martini gate (:151–166), save/crash harness (:141, :295), Unity build gates (:110, :256, :327), M0–M7 launch milestones (:107) |
| Producer charter (3,674) | Revision request format (:185), "review actual outputs, not only success messages", "prepared, not sent" honesty (:179) → producer.md, dev-lead.md | Project-agnostic design with no jam facts (:9, :44), milestone-closure authority that contradicts the Studio Pipeline (:86), expertise and reference register (:36, :213) |
| Technical Development Pipeline (7,538) | Parse result files, not exit codes; prove the runner with a failing test (:121, :317) → check_automation_report.py + tests. Not Run is never Pass (:284). Editor FPS is not release proof (:437). Pin versions (:330). No secrets (:190) | Unity layout incl. "UEProject/Assets" (:168), PlayMode/EditMode tests (:296–314), restaurant systems (:336–366), "not implementation authorization" (:8, :128) |
| Development Pipeline (9,032) | Simplest correct code (SIMPLE-01..04, :144). AI-01..04: inspect first, smallest change, mark assumptions (:193). Reject list (:240). Never edit generated files (:83) → gameplay-dev.md, dev-lead.md, unreal-rules.md | C#/Unity rules (82 Unity hits), `_camelCase` naming against Epic's standard, personal home-folder paths (:59, :279, :813), other-project hashes appendix |
| Technical Director charter (4,674) | Recommendation or passing test is not authorization to merge (:189). Never present untested as validated (:155). Brief template (:618) → task-card.md | Engine-agnostic text with no Unreal knowledge; no file ownership (abstract "system boundaries") |
| Lead Developer charter (4,540) | Inspect diffs, not summaries (:729). Reproduce → isolate → fix → regress (:578). Reconcile handoff claims with real repo state (:899) → dev-lead.md | Adoption clause naming the Art Director (:1083), Puro Búho studio name (:1, :20) |
| Art Director charter (6,748) | Readability before ornament (:202). Fact / interpretation / preference labels (:226). "A generated image … is not automatically an accepted production asset" (:965). Revision loop (:926) → art-director.md | Configured for the author's studio's games (its author's own note). "APPROVED by Sutdio Heads", which our team never gave |
| Art Pipeline (7,220) | Every asset must work in the game (:14). Judge at gameplay scale (:57, :273). Collision never from sprite pixels (:289). Label references by accepted traits (:321). Decode files to validate (:348) → art-bible.md, art_check.py | Pixel-art/neon north star (:56), Unity runtime (:49), bar-game GDD as binding (:35), 14-state approval flow, ban on numbers (:26, :305, :452) |
| Design Pipeline (7,828) | Authority labels GDD RULE / PROTOTYPE HYPOTHESIS / ILLUSTRATIVE (:95). Observed / measured / reported / inferred (:194). Observe before asking (:366). Lightweight path as default (:562) → playtests.md, decisions.md | Restaurant core loop "Plan → Commit → Operate" (:30), bar-game GDD as binding (:66), day gates for another game (:112) |
| Game Designer charter (10,578) | Vague goals must become observable behavior (:1417). "Do not allow an attractive image to silently establish gameplay rules" (:1463), which is our D0. One severe usability failure is a real defect (:1651). Smaller coherent game wins (:1889) | Bans on stating numbers (:1430, :1673, :1810), length (10,578 words for one role) |

**Correction (round 2).** The first version of this table listed items as kept that were in none of our
files: the P0–P3 ladder, SIMPLE rules, revision-request format, Design Pipeline :95/:194/:366/:562, Game
Designer :1417/:1651, Lead Dev :578/:899, Producer :179/:185. Round 2 went through all 13 files line by line
and ported those plus about 60 more items (Unreal terms, checkable form). Every move is listed with its
source line in `docs/port-log.md`. The "Don't keep" column stands.

**Coverage map (round 3).** Every rule of all 13 inherited files (1,661 items) is mapped with its status, our location
and how it is enforced in `docs/coverage-map.md`; the 38 items that were still missing are ported there, and 0 remain.

## 9. Self-review: a fresh reviewer audited this pipeline
After building the pipeline, a separate reviewer with no context from the build read every file and tried to break it.
It found 28 problems: 3 critical, 10 high, 10 medium, 5 low. The critical and high ones, and what changed:

| Problem found | Fix |
|---|---|
| No role was allowed to edit maps, so nobody could build a level, BP_Ella, the GameMode or the UI | New Integrator role (`pipeline/roles/integrator.md`) |
| No first card: "no card, no work" with no Day-0 cards | `pipeline/day0-cards.md` (9 cards in order) |
| Agents couldn't read the GDD (Google Doc link only) | Read-only snapshot `docs/gdd/archive/gdd-umbrella-ella-draft1.0.md`; owner refreshes it from the shared doc |
| Clean eval cases had extra "tests pass" wording, which revealed which ones were clean | Every case now has the same evidence and context lines; a test enforces it; eval re-run (§6) |
| The reviewer CLI ran inside the repo and could have opened the answer key | Runner now runs it from an empty temp folder with file and shell tools disabled |
| LFS check only matched file names, so a raw binary committed without LFS passed | Checks the stored blob is an LFS pointer; new test commits a raw `.umap` and expects failure |
| Automation report passed tests that never ran, and `--require OpenRises` matched `NotOpenRises` | NotRun counts as failure; names must match a whole dotted segment; tests added |
| Art and playtest rules assumed shots and projectiles the MVP doesn't have | Rules made conditional on D1/D2 |
| Playtests P2–P3 were due before the attack existed | Rescheduled (P1 at G1, P2–P3 at G2) |
| Art judge calibration was circular (the only known-good was a source image the judge must reject) | Known-good is the first human-approved in-engine frame; until then approvals need Rick |
| Smoke line could never appear in a Shipping build | TD skeleton sets `bUseLoggingInShipping`; the smoke hook has one owner (Day-0 card 0.6) |
| All MVP code was in one file, so cards could only run one at a time | Component-per-lane code layout in `pipeline/unreal-rules.md` |
| No pattern for headless tests that read values from the running game | Day-0 card 0.5 builds one, others copy it |
| Dev Lead could approve with medium findings; the scorer expected a block | Any blocker, high or medium finding = request_changes |
| `check_pr` accepted "n/a" as evidence; CI didn't re-run on PR edits | Fixed, with tests |
| Smaller items: conflicting conflict-rules, decision-ID collisions across branches, a wrong script path, PowerShell 5.1 stopping on stderr, missing owners in the People table | Fixed |

Still open from that review: Unreal facts it flagged as uncertain (plane constraint flag, World Partition vs sublevels,
manual exposure value) are tagged [VERIFY] for Day-0 card 0.4a. Every eval case still claims "build: pass", so the eval
doesn't yet test whether the reviewer catches missing evidence.

## 9b. Round 2: built on the inherited pipeline, then a fresh dry run
- Ported ~60 more items from the inherited files (`docs/port-log.md`), each traced to `file:line`.
- An independent agent wrote 20 harder reviewer cases, including fake and missing evidence.
- A fresh agent simulated the jam from card 0.0 to submission and found 36 problems. 5 were critical: Day-0 test deadlock, daily-build deadlock, no owner for movement and input, no owner for `DefaultGame.ini`, merge closing cards. All critical and high are fixed, and most mediums; the rest are decision rows.
- Round-2 decision rows got defaults (D-new-port-1..13, D-new-smoke, D-new-ci-lfs, D-new-tuning, D-new-lose, D-new-cut5). Since §9c they are settled rules.
- Round 3 added the Game Designer role, balance targets and the movement envelope card.

## 9c. Studio-bar review (two batches) and the GDD switch
**What ran.** Two review batches, 11 lanes in all (batch 1: 5 lanes, batch 2: 6 lanes: submission, UI and UX, audio,
game feel, agent ops, level). Each lane ran up to 4 builder and critic rounds against a written studio bar, judged blind.
**Result: no lane beat its bar in the blind comparison.** Each lane still left real work: new gate tools
(`audio_check.py`, `feel_check.py`, `encounter_check.py`, `ui_check.py`, `submission_check.py`, `secrets_check.py`,
`prompt_log.py`), each with tests, and new role cards for Audio, UI and UX, Level Designer and Agent Ops.

**Dry runs.** Two fresh agents ran the jam from card 0.0 on paper. They found 3 critical and 27 high problems.
The worst: card 0.6 could not finish on Day 0 (it needed UI text that comes at G4), the TD's Day-0 PR needed a menu
test that gameplay cards build, the Art Director could never give a verdict (no card placed the swatch camera),
22 cited decision IDs had no row, card IDs 0.16-0.19 collided between lanes, and `check_pr.py` and `check_card.py`
passed PRs and gate records that ran nothing. Many parallel lanes edited the same docs, so they drifted apart.

**What changed in the consolidation pass (one integrator).**
- GDD switch: `docs/gdd/archive/gdd-umbrella-ella-draft1.0.md` is now THE LAST HOUR (Draft 1.0, a single-arena owl encounter). The old
  five-section platformer is gone from the brief, spec, balance, test map, playtests, Day-0 cards and checklists.
  MVP = GDD P0 (9 items); stretch = P1 then P2. Rick's review comments are open rows D1 and D27-D33.
- Decisions: 99 rows became 23 open tradeoffs (each with an owner from the People table and a Blocks date) and
  111 settled rules. A Creative director row (D34, default Rich) breaks ties.
- A consistency gate in `tools/pipeline_check.py`, run in CI: it fails on a decision ID with no row, a card ID not
  in the Day-0 table, a path that does not exist, an owner who is not a People seat or role, and an "After" cycle.
  It also fails on private references. Both have tests that break each case on purpose.
- Day-0 deadlocks removed: 0.6 no longer needs display or verify-tags (new card 0.6d, due G3); the TD PR no longer
  needs the menu test; swatch (0.10a), anchors (0.10b) and the art dump (0.4d) have cards; the skeleton sets a
  GameMode; cards are filed only when their After cards merge, so lanes never overlap.
- Jam facts everywhere: the Development build is the submission (the SHIPPING gate line is gone); no game files
  before Nov 12; a Nov 11 theme-fit card (0.19); prompt logging from Nov 12; the pre-jam declaration; the devlog.
- `check_pr.py` now fails a `Source/` PR with `engine=none` or a "not run" non-unity line, and a smoke line that breaks
  the contract or names an unchanged map. `--gate-record` fails a Pass with failing lines. CI pulls changed PNGs from LFS.
- `pipeline/unreal-rules.md` is a 952-word core plus three on-demand files in `pipeline/unreal/`.
- One integrator owns cross-lane edits (AGENTS.md, producer.md). Eval cases are written by a different agent than
  the one that edits the reviewer prompt (evals/README.md).

## 10. Summary for the team (in the style of Rick's review)
Rick, and the inherited pipeline's author: I finished the audit of the inherited pipeline against Rick's pipeline, the GDD and the key art,
and built the result on a branch for review.

**What I'd keep.** The inherited pipeline's honesty rules are the best part. Don't claim what you didn't run. Don't
treat your own second opinion as review. The packaged build is the measure of progress. Art isn't accepted
until it works in engine. Those are now the core of our agent rules. Rick's seven roles and his unknowns
format are the structure.

**What blocked us.** Beyond Rick's findings, the package stops an obedient agent from starting: design
docs "don't authorize implementation", and every batch of work needs two executive approvals. It rejects
fixed deadlines. Its art north star is pixel art and neon, which is the opposite of our key art. It never
mentions Unreal binary files, so two agents on one level would lose work. It also tells agents not to build
enforcement. Measured across all 13 files: 219 Unity-specific terms, at least 172 references to the other
game, one Unreal mention and zero mentions of our game.

**What I built (branch, not merged).** A one-page AGENTS.md and jam brief, about 2,000–3,500 words per task
instead of 78,000. Eight short role cards (Rick's seven plus an Integrator, because no role was allowed to build the level) with inputs, outputs, done-when and never-do lists, and the first nine Day-0 cards. Unreal 5.8.4
rules: modules as our code boundaries, C++ for rules with thin Blueprints, LFS locking, and rules for agents
using the editor MCP. An art bible from the key art, plus a script that fails off-style screenshots. A
reviewer test with 35 planted-bug, fake-evidence and clean cases, 20 of them written by a separate agent. The final 3 runs passed the full bar: every bug caught, every clean change approved. Gates for the TD (module boundaries), Producer (task cards), Art (palette, flat frames, sprites) and QA (tests, smoke). CI that blocks leaks, build junk, missing LFS and empty
PR evidence. Every check has tests, and we broke each one on purpose to make sure the tests notice. Then a fresh reviewer audited the pipeline (28 problems), and a second one simulated the whole jam (36 problems). The critical and high ones are fixed (§9, §9b).

**What's still open.** 45 decisions with defaults in `docs/decisions.md`. The ones that block Day 1: jam
rules on AI art (D14), attack rule (D1), who integrates and packages (D12), Mac and C++ (D24). The
Unreal commands haven't run against 5.8.4 yet, the palette needs measuring from the real key-art file,
and the editor MCP's tools need listing on Day 0.

**Recommendation:** review and merge the branch, settle D1, D12, D14 and D24, then run issue #4 (pipeline
on every machine) with the Day-0 Technical Director skeleton card as the test task.
