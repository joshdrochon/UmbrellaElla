# hotfixfb (lead hotfix lane)

Lead-run lane for fixes that keep main buildable and its checks green; no feature work.

Rule IDs: none of its own; it restores existing checks.
- Nov 13 (Feedback): ArtSlotKeeperEnemy accepts the Keeper stand-in already showing its slot art.
- Nov 13 (build): SettingsMenuWidget.cpp includes its own header first (non-unity builds failed).
- Nov 13 (tests): gdd_check bindings for CAM-05 bands removed in 3935a344 move to not_in_game (owner level); gdd_check
  test fixture moves off HAZ-10.actor_scale (built in 3481eb4d); test_area sandbox drops HANDOFF.md (6a205554);
  story bible GDD fact P11 renamed F15 (35ac89a0).

Definition of done: `python3 -m unittest tests.test_gdd_check tests.test_area tests.test_story_check` OK,
`python3 tools/build/gdd_check.py` shows no `FAIL broken` line, the build passes.
