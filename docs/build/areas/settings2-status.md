# settings2 status

## FLOW-44 developer Game Options (done, agent default D-new-flow44-dev-options)
- `Settings/DeveloperOptions.h/.cpp`: all 20 GDD candidates in GDD order, each with a control (percent of tuned value,
  whole-number change, toggle, or link to the Controller page). No ammunition or energy controls.
- Director's Cut only; session only (never written to the settings file). Save on Game Options writes the composed
  values into the live `UUmbrellaTuning` defaults (`USettingsMenuSubsystem::RefreshLiveTuning`); Start Game, a reload or
  all-defaults restores the captured baseline. Settings follows the player controller's play mode every frame.
- Release exposure (D-new-flow44-release): read-only in the submission build, editable in editor/tester builds;
  one constant flips it (`DeveloperOptionRelease::bEditableInSubmissionBuild`).
- Game Options page: slider/checkbox/button per option, value text, Reset to default; dirty Back prompt as other pages.
- Tests: `UmbrellaElla.Settings.DeveloperOptionsList`, `.DeveloperOptionsApply`, `.DeveloperOptionsDirectorOnly`,
  `.World.DeveloperOptionsReachLiveTuning`; `.PagesByMode` still passes.

## FLOW-45 accessibility readers (done in lane; reads outside the lane requested)
- `Settings/UmbrellaAccessibility.h/.cpp`: settings API for readers (text scale, reduced motion, reduced flash, shake
  scale); `OnSettingsSaved()` delegate.
- Reduced motion reaches the XP ring (`UXpRingWidget::SetReducedMotion`, also in the submission build) and is readable by
  everything via `IsReducedMotion`. Menu backgrounds and the Keeper hover do NOT react yet: no reader exists in Flow or Keeper
  (requests 5 and 6). Settings no longer writes reduced motion into the tuning. Reduced flash already reached Vfx.
- Tests: `UmbrellaElla.Settings.AccessibilityDefaults`, `UmbrellaElla.Settings.World.AccessibilityReachesReaders`.
- Left (requests in `docs/build/requests/settings2.md`): text scale read by the artui shared UI style; screen shake
  does not exist yet (whoever adds it multiplies by `GetShakeScale`); gameplay backdrop parallax under reduced motion
  (visuals lane); flow reads the Tutorial developer toggle; flow and keeper read reduced motion (requests 5, 6).

Evidence: not re-run after this fix; the build lead's gate runs build and tests (gate evidence at a6fef4d showed 39 tests).

## FLOW-45 / VFX-10 readers wired (this slice)
- `UmbrellaAccessibility::Published*` snapshot (no world context), published by the settings subsystem on load and Save.
- Readers: flow menu fonts and backdrop (still under reduced motion), story text, HUD clock numerals, Director's Cut label,
  gameplay backdrop parallax 0, looping VFX frame 0 (`VfxCatalog::FrameAt(..., bReducedMotion)`).
- Test: `UmbrellaElla.Settings.World.AccessibilityReachesReaders` extended. Targeted run (Flow, Settings, Story, Feedback): 92 pass.
- Left: Keeper hover has no reader; screen shake does not exist.

## Merge of main into settings2 (Nov 13)
- Resolved conflicts in FlowMenuWidgets, StoryWidgets, UmbrellaPlayerController: main's shared UI style kept, text scale
  (`PublishedFontSize`) and reduced motion re-applied on its fonts and backdrop.
- Evidence at 207400a3: build exit 0, 0 warnings; module_check 0 problems; targeted run (Settings, Flow, Story, Feedback): 97 of 98 pass.
- Failing: `UmbrellaElla.Feedback.World.ArtSlotKeeperEnemy` ("keeper takes a picture": Keeper ShowArt not Drawn). Keeper
  presenter is not in this lane and no settings2 change touches it; not triaged against main. Keeper lane / build lead to check.
- Left: Keeper hover has no reader; screen shake does not exist.

## Merge of origin/main 7aabf929 (Nov 13, 53a93252)
- Main's wording kept where storyinventory fixed a line; lines.csv matches source (only story-ending-page-2 differs from main: the shorter ending line, source already matches).
- lane_precheck: FAIL on two tests that also fail on a clean origin/main (checked in a detached worktree): `test_story_check.RepoStoryFilesPass.test_strixon_is_denied_and_nar_is_authorized` (P-facts status GDD in the bible) and `test_assetgen_image_method.StripFrames.test_three_figures_cut_to_equal_frames_on_one_baseline`. Neither touches the settings2 lane. Needs the story lane / build lead.
