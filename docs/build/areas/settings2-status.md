# settings2 status

## FLOW-44 developer Game Options (done, agent default D-new-flow44-dev-options)
- `Settings/DeveloperOptions.h/.cpp`: all 20 GDD candidates in GDD order, each with a control (percent of tuned value,
  whole-number change, toggle, or link to the Controller page). No ammunition or energy controls.
- Director's Cut only; session only (never written to the settings file). Save on Game Options writes the composed
  values into the live `UUmbrellaTuning` defaults (`USettingsMenuSubsystem::RefreshLiveTuning`); Start Game, a reload or
  all-defaults restores the captured baseline. Settings follows the player controller's play mode every frame.
- Release exposure (D-new-flow44-release): read-only in the submission build, editable in editor/tester builds;
  one constant flips it (`DeveloperOptionRelease::bEditableInSubmissionBuild`).
- Game Options page: slider/checkbox/button per option, value text, Reset to as tuned; dirty Back prompt as other pages.
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
