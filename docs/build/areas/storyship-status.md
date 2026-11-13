# storyship status (area/storyship)

Done: story canon adopted (D-new-story-canon agent default): bible Names Ella, Mother and facts P1-P8 now read
"CONFIRMED 2026-11-12 (agent default; team may override)". P9 and P10 stay PROPOSED (P10 waits for the Art Director).
Q1 and Q5 answered. All 7 Director's Cut lines in `pipeline/story/lines.csv` are ship=yes.
Cue table synced: StoryCues.tsv, StoryRules.cpp DefaultText and StoryTests.cpp carry the seven lines.csv texts
(`story_check --scan` on the cue file PASS; `--table` only reads Key/SourceString CSVs, so it does not apply).
Opening caption now matches GDD NAR-04: "Mother: Keep it open, Ella. It'll protect you from the owl."
Blind story critic (1 round after the change): FAIL on that one line, S2 ("Mother:" label). Six lines pass every row.
Kept as the GDD words it; recorded as a critic defect in `docs/build/requests/storyship.md`. Consistency repeat: not run.

Request #10 diff applied (story_check, calibration); tests/test_story_check.py updated to D-new-story-canon (P9 now the
PROPOSED negative; NAR-* records authorize). `unittest tests.test_story_check` 27 OK, `story_check` PASS, `--calibrate` PASS rows=22,
`nar_authorized` now needs NAR-04..07 all authorized.

No Unreal code or tests changed in this slice (text data only).

Panel round (Nov 12, after lead's 3-critic panel): Status words now define "CONFIRMED (agent default; team may override)"
per D-new-story-canon. F8 (stolen hand) is DEFERRED, so story-keeper-arrival and story-shaft-clue no longer state it:
"The clock keeps one hand. Beside it is an empty place." and "The umbrella's shaft matches the bronze of the clock."
(cue table, StoryRules.cpp, StoryTests.cpp synced). New GDD fact F9 (NAR-06 clue) backs both. Critic reasons fixed:
"mounting" was jargon (S5), bronze had no bible source (S1). Results: story_check PASS, --calibrate PASS rows=22,
test_story_check OK, `critic.sh story` panel 3/3 PASS (bible=4789a3d2). Unreal tests not rerun (text-only strings; one test string changed).
