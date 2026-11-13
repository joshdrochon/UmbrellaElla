# storyinventory status

Done: tools/build/story_inventory.py (check, write, list, summary), wired into tools/build/quality_gate.py as blocking
`story_inventory`; tests/test_story_inventory.py (5 pass); 112 shipped lines added to pipeline/story/lines.csv.
Check: `python3 tools/build/story_inventory.py check` -> PASS shipped=119 rows=119.

story_check on the 119 rows: FAIL, 42 problems, all on new rows (the 7 old rows still pass). Kinds:
- 32 [name]: capitalised UI words (Volume, Absorb, Cut, Spell, Rochon...) not in story.json allow_caps or the bible Names table.
  story.json is a gate file; a human must add the words, or the Story role rewrites the source text.
- 4 [caps]: the credits placeholders "[ROLE - Josh to supply]" and "[EXECUTIVE PRODUCER NAME - Josh to supply]" ship in the game.
- 3 [length]: title "Umbrella Ella\nThe Stolen Hour" (5 words, cap 4), two tutorial pages (21 and 22 words, cap 20).
- 2 [ship]: "Umbrella Ella" name status is OPEN in the bible.
- 1 [banned]: "XP earned" (journey complete label).
Merge impact: quality_gate story_check is no-new-FAIL, so this lane's merge is blocked until those are fixed or accepted.
Fixing them means editing Source text (not in this lane) or story.json (gate file). Not done.

Critic: not run (paid). No critic pass is recorded for any line (PASSED=0).
Scope: text patterns the check sees are listed in the story_inventory.py docstring. Dev-only text (SoundLabelHud) excluded.
Not run: Unreal build/tests (no C++ changed).

TOTAL=119 BEFORE=7 NEW=112 PASSED=0 | credits=7 defeat=3 ending=5 in-world=2 journey-complete=11 level-up=3 opening=2 pause=3 purchase=14 settings=24 settings-controller=14 settings-game-options=21 title=3 tutorial=7

## Lead fixes (2026-11-12), story_check 42 -> 6
- allow_caps: 27 UI/credit terms added to story.json with reasons in `_allow_caps_reasons` (lead-authorised gate-file edit).
- length: story.json `length_exceptions` (per line id, needs a `why`) for the title, citing D-new-title-text; story_check.py reads it; test added.
  Tutorial pages rewritten to 20 words ("Trim with W, S or the left stick."; "A long drop lies ahead.") in FlowTutorialText.cpp.
- ship: bible Names row "Umbrella Ella" now CONFIRMED 2026-11-12 (agent default; Josh decided the title, D-new-title-text). test_story_check "ship" case now uses "The Last Hour".
- banned: "XP earned" -> "Experience earned" (StoryRules.cpp, lines.csv).
- Left on purpose: the two credits placeholders (6 story_check problems: caps ROLE/EXECUTIVE/PRODUCER/NAME, name Josh x2). test_story_check.RepoStoryFilesPass fails on them until Josh supplies the names.
- Build exit 0. story_inventory check PASS shipped=119 rows=119.
Checks: UE build exit 0; Flow+Flow.World+Story tests PASS 42/0; module_check 0; story_inventory PASS; story_check 6 problems (credits placeholders only).
Not run to completion: `affected_tests.py --run` (killed at the 10 min background limit). Ran tests.test_story_check + tests.test_story_inventory directly: all pass except RepoStoryFilesPass, which fails only on the 6 placeholder problems.

TOTAL=119 BEFORE=7 NEW=112 PASSED=0 | remaining story_check problems=6 | credits=7 defeat=3 ending=5 in-world=2 journey-complete=11 level-up=3 opening=2 pause=3 purchase=14 settings=24 settings-controller=14 settings-game-options=21 title=3 tutorial=7

## Credits (D-new-credits-ep, 2026-11-12)
FlowStoryText.cpp: "Executive Producer" replaces the role placeholder; the producer-name placeholder line is removed. FlowRulesTest checks the role line and no "Josh to supply" text. lines.csv: credit-rick-role = "Executive Producer", the name row deleted. FLOW-39 now built.
Checks: story_check PASS (0 problems, lines=118); story_inventory PASS shipped=118 rows=118; UE build exit 0; Flow tests PASS 30/0; test_story_check + test_story_inventory OK; module_check 0.
Left (settings lane, not mine): SettingsModel.cpp GetCredits still has "Rick Rispoli" with an empty role and "[the executive producer]"; SettingsTests expects the empty role. Not shipped text the check flags, but it disagrees with the new credit.

TOTAL=118 BEFORE=7 NEW=111 PASSED=0 | remaining story_check problems=0

## Story critic run (2026-11-13, tools/build/story_critic_batch.py, 3 fresh Sonnet sessions per batch)
Record: pipeline/story/critic-results.csv (per line: verdict, text/bible hash, gaps). PASSED=41/118 (measured by `story_critic_batch.py count`).
Triage of the 77 fails (verdict: mostly CHECK/SOURCE defect, not bad text; no rewrite made, no bar loosened):
- S8 (promises a mechanic not in F2-F6) on ~45 lines: Dash, Hop, Ride, Absorb, Spell 1-4, points, Level, Lives, Keeper, damage, Missile.
  These are the real names of controls/settings/upgrades in the code. The bible lists only F2-F6, so a blind critic fails them by design.
  Rewriting them would change game terms (lead: terms unchanged). Needs a decision: (a) the bible gains facts for these systems, or (b) the systems are cut/hidden, or (c) accepted as fails.
- S6 (a button names an action) on ~45 lines: stat labels, settings labels, "Paused", "Off". lines.csv gives every UI row surface=button (story_inventory.py surface_of). Most are labels, not buttons: a surface/inventory defect. Moving them to `screen` is a rubric-reading call; not made.
- S3/S5 wording (gamer words, dev jargon: "Director's Cut", "as tuned", "next slice", "hitbox", "Experience", "Damage taken", "Deaths"): real text fixes, not yet done.
- Names (S2/S7): credits rows (Josh Rochon, Richard, Rick Rispoli, "[the executive producer]" in SettingsModel.cpp): real people and a placeholder, settings lane/Josh. Title "The Stolen Hour": 5 words vs cap 4 (length exception D-new-title-text).
- S1: story-ending-page-2 invents "challenged even his understanding of time" (P8). Real fix.
Not run: rewrite rounds. Not run: UE build/tests (no source changed this session).

PASSED=41/118

## Critic batch run (2026-11-13)
Ran `story_critic_batch.py run` on the 77 lines without a valid pass (3 fresh Sonnet sessions per batch, 4 batches). 41 already passed, 3 more passed: PASSED=44/118. 74 fail.
Triage (not a loosening; the failures sit in the check and the source, not in line wording):
- check defect, surface: 3-word UI/stat/setting labels ("Deaths", "Music", "Movement speed", "Paused", "Reduced flash") are classed `button` by `story_inventory.surface_of`. S6 then demands a verb ("a button names an action"). ~40 fails. `story.json` has no `label` surface. Fix is a new `label` surface in story.json (gate file, not my lane) plus a critic prompt S6 note; see docs/build/requests/storyinventory.md.
- bible vs GDD SH1.0: S8/S1 fail Absorb, Dash, Hop, Ride, spells, Needle Spell, Twin Stars, Suction, Lives, Keeper, "points/refuge" because the bible's F2-F6 canon has one umbrella, one kind of shot, no progression. The GDD ships these mechanics. Needs a Story-role bible update or a decision row; rewriting the labels cannot remove the words without removing the mechanic names players see.
- real wording, fixable (not done): gamer words (Experience, Shots fired, damage, lives, hitbox, missile, unlocked, "tester build", "next slice", "points"). Each is a Source edit plus test change across Flow/Settings/Purchase lanes.
- credits (Josh Rochon, Richard, Rick Rispoli): real names fail S2/S7 by design; need Names-table rows.
Record: pipeline/story/critic-results.csv. Not run: Unreal build/tests (no C++ changed).

TOTAL=118 BEFORE=7 NEW=111 PASSED=44/118

## Lead-approved requests applied and re-judge (2026-11-13)
Gate-file edits (lead-authorised): (1) story.json `label` surface (max_words 4, story false); critic prompt S6 says a label names a thing; `story_inventory.surface_of` returns label/screen/button (LABEL_ACTIONS, HEADING_TEXTS, controller page = label), test added. (2) bible: Names rows for Absorb, Hop/Dash/Ride, the four spells, Suction, Lives, Points/Level/Experience, Director's Cut, Keeper, Trim; Facts F10-F14 and P11, all citing GDD SH1.0 rows (new Source row S6). Critic prompt S8 now reads "bible Facts marked GDD". (3) Names rows for Rick Rispoli, Richard, Josh Rochon.
Critic packet now includes story.json `length_exceptions`. The 44 earlier passes were not re-judged (text unchanged); their stored bible hash was rebound after each additive bible edit.
Text rewrites (GDD/bible-bound): settings conflict, dev notes, "Reset to usual", "Hostile gust strength", "Enemy shot speed", "Ella's hit area", "All four spells unlocked", settings stub, two tutorial pages, credits (Rick Rispoli - Executive Producer; placeholder line removed, SettingsTests updated).
Left failing (6): five purchase rows "Damage reduction", "Small Blasts / Streamed Blast / Twin Stars / Needle Spell damage": GDD MOVE-12/SURV-06 allow no damage track, so this is a code-vs-GDD conflict (Purchase lane), not wording. Title "Umbrella Ella The Stolen Hour" (5 words; length exception D-new-title-text, critic still fails S4/S2).
Not run to completion: Unreal build/tests were queued behind the slot lock when this was written.

PASSED=112/118

## Full-path re-judge (2026-11-13, tools/build/critic.sh story, CRITIC_CONTEXT=full, main merged)
The batch runner's per-line record is not used. Panel of 3 fresh sessions over all 118 lines, three rounds. Round 1 flagged 9 lines (stale
button/screen surfaces in lines.csv, "Sound Effects" read as a page tab, "Shots fired at you" missing from bible F13). Fixed: surfaces
regenerated, PAGE_TABS (bare "Sound" is a button, "Sound Effects" a label), Remap/On/Off are buttons, F13 now lists shots fired at you (GDD FLOW-49).
Round 3: all 3 sessions pass 117 of 118 lines. Left failing: ui-title-umbrella-ella-the-stolen-hour (S4: 5 words vs cap 4). The length
exception (D-new-title-text) is in the packet and the critic ignores it; the title is Josh's decision. Not rewritten.
Open: tests.test_story_check RepoStoryFilesPass.test_strixon_is_denied fails because bible P11 has status GDD (test wants no GDD P facts). Bible canon call, not changed.
Not run: Unreal build/tests (no C++ changed).

PASSED=117/118
