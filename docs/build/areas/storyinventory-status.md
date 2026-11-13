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
