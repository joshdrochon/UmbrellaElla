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
- Main's wording kept where storyinventory fixed a line. (Wrong, corrected below: this merge cut story-ending-page-2 and the Director's Cut spell line; main had the full text.)
- lane_precheck: FAIL on two tests that also fail on a clean origin/main (checked in a detached worktree): `test_story_check.RepoStoryFilesPass.test_strixon_is_denied_and_nar_is_authorized` (P-facts status GDD in the bible) and `test_assetgen_image_method.StripFrames.test_three_figures_cut_to_equal_frames_on_one_baseline`. Neither touches the settings2 lane. Needs the story lane / build lead.

## Handoff blocker B3 + Pause step 5 (Nov 13)
- B3: Settings drew under the Paused menu. It was added with `AddToPlayerScreen` (player layer, which UE draws under
  every viewport overlay); the flow menus use `AddViewportWidgetContent` at `Flow.MenuContextPriority` and their art at +1.
  Settings now goes into the same viewport overlay at `SettingsLayer::ZOrder()` (menus + art + 1) and is removed on close.
- Pause step 5: Escape (and the flow menus' other Back keys: F1, gamepad B, Start) inside Settings backs out like Back;
  with the Save / Discard / Keep Editing prompt up it keeps editing; during a remap it still cancels the remap.
- Tests: `UmbrellaElla.Settings.World.DrawsAboveFlowMenus` (top overlay widget is Settings, stays on top when a flow
  menu is re-added, gone on close), `UmbrellaElla.Settings.World.EscapeBacksOut`. Break-proven: with the old code
  (AddToPlayerScreen, no Back key) both fail on 7 asserts. Settings + Flow: 66 of 66 pass, build 0 warnings.
- The reader WIP that was uncommitted in this worktree (HUD AccessibleTextScale, XP ring paint plan, flow backdrop
  PaintTime, SettingsReaderTests.cpp) is set aside on local branch `settings2-wip-readers`, not merged here.
- Real game (pause_settings.txt, on a local branch with origin/area/agentplay's journey hook merged; main lacks it):
  21 pass, 4 fail. Step 24 "Escape inside Settings -> Paused" now PASSES (was the step-5 FAIL). Step 25 "click Back"
  fails only because Escape already closed Settings (the script's fallback for the old bug). The 3 `shot` steps FAIL
  in this run: no PNG is written, the hook logs `out=/joanmiguel/Desktop/...` (the `/Users` prefix is lost), an
  agentplay-lane path bug. So B3 has test proof (top overlay widget is Settings) but no picture yet: agentplay to re-shoot p02.

## Review fixes for B3 (Nov 13, review-settings2.txt)
- Restored from main: `story-ending-page-2` full text ("...or perhaps something about Ella has challenged even his
  understanding of time.", GDD line 564, bible F15) in `FlowStoryText.cpp` and `lines.csv`; Director's Cut tutorial
  page "Shoot with J or the left mouse button. Cycle spells with [ and ] or press 1 to 4." and its `lines.csv` row with
  the "Director's Cut only" note. The earlier status claim that the source "already matches" was wrong.
- Lane: every edit outside `Settings/**`, `UI/Settings/**`, `Tests/Settings/**` reverted to main (Feedback/Background,
  Feedback/Vfx, VfxCatalog, UI/Menus, UI/Story, UmbrellaHUD, UmbrellaPlayerController, rule-status VFX-10 note). The
  reader lines, with the include-order and single-VFX_10 fixes, are request 7 in `docs/build/requests/settings2.md`.
  So the "FLOW-45 / VFX-10 readers wired" section above no longer holds on this branch: the published API and its test
  stay; the readers wait on their lanes.
- `PublishSaved` lost its unused `bReducedFlash` param.
- The earlier note that two Python tests also fail on clean main is withdrawn; the gate evidence does not show them.
- Evidence at cb529b44 (origin/main 6a4b2bc5 merged): build exit 0, 0 warnings; gate_plan tests
  (Feedback.World, Field.World, Flow.World, Settings) 78 of 78 pass; Flow+Move+Settings+UI+Feedback.World+Field.World
  171 of 171 pass; module_check 0, manifest_check 0, affected_tests OK. Diff vs main is Settings/**, UI/Settings/**,
  Tests/Settings/** and docs only.
