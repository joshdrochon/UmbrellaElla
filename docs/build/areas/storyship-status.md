# storyship status (area/storyship)

Done: story canon adopted (D-new-story-canon agent default): bible Names Ella, Mother and facts P1-P8 now read
"CONFIRMED 2026-11-12 (agent default; team may override)". P9 and P10 stay PROPOSED (P10 waits for the Art Director).
Q1 and Q5 answered. All 7 Director's Cut lines in `pipeline/story/lines.csv` are ship=yes.
Blind story critic: `STORY_CRITIC: PASS lines=7` (4 rounds; fixes only what it named: no "Mother:" label, no "bronze",
no falling light, clear clock-hand lines). Not run: the consistency repeat of the critic.

Blocked on the build lead (outside my lane, `docs/build/requests/storyship.md` item 10 has the exact diff):
`tools/story_check.py` only accepts `CONFIRMED <date> (Richard)` and looks for a NAR-01 record the SH1.0 manifest lacks;
the calibration row `bad-ship-proposed` uses P1 (now CONFIRMED) and must use P9.
With the diff applied here: `story_check` PASS, `--calibrate` PASS rows=22. On this branch as committed (diff not
applied) `story_check` FAILS 26 problems, and the gate's critic step will see them.

No Unreal code or tests changed in this slice (text data only).
