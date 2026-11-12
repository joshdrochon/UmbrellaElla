# fixsettings status
Done: (1) reduced flash: `FSettingsData.bReducedFlash`, store key, Sound-page checkbox, applied to the Vfx subsystem on Save and at startup/world init (`USettingsMenuSubsystem::ApplyReducedFlash*`). Test `UmbrellaElla.Settings.World.ReducedFlashReachesVfx`.
(2) Saved key reaches live IMC_Default after respawn: `UmbrellaElla.Settings.World.SavedBindingReachesLiveContext` (real game instance).
(3) `logs/review-settings.txt` does not exist on this machine, so no minor items were fixed. Left: those items, if the file is supplied.
Evidence: build exit 0, `UmbrellaElla.Settings` PASS tests=14 failed=0.

## Review round 1 (FLOW-43, FLOW-45)
Done: `PressSave` and `ChooseBack(Save)` check `ESettingsResult`; on `Failed` the menu stays open and shows "Could not save your settings." Test `UmbrellaElla.Settings.SaveFailureKeepsMenuOpen`.
`ReducedFlashReachesVfx` now uses a game-instance-owned subsystem, goes through `SaveSettings`, and runs the world-init hook (`HandleWorldInit`), including the other-game-instance case. The test world has no game instance of its own, so `SaveSettings`' push to the GI world is not asserted separately.
Minor items fixed (stray space, duplicate include, member order). The earlier review's item 3 (FLOW-43) is this fix.
FLOW-45: `GetSavedTextScalePercent()` / `IsReducedMotionSaved()` added; the HUD, XP ring and flow screens are outside the lane, so the reads are requested in `requests/settings.md` item 6.
Evidence: build exit 0, `UmbrellaElla.Settings` PASS tests=15 failed=0, module_check 0, manifest_check 0.
