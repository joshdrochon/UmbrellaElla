# fixsettings status
Done: (1) reduced flash: `FSettingsData.bReducedFlash`, store key, Sound-page checkbox, applied to the Vfx subsystem on Save and at startup/world init (`USettingsMenuSubsystem::ApplyReducedFlash*`). Test `UmbrellaElla.Settings.World.ReducedFlashReachesVfx`.
(2) Saved key reaches live IMC_Default after respawn: `UmbrellaElla.Settings.World.SavedBindingReachesLiveContext` (real game instance).
(3) `logs/review-settings.txt` does not exist on this machine, so no minor items were fixed. Left: those items, if the file is supplied.
Evidence: build exit 0, `UmbrellaElla.Settings` PASS tests=14 failed=0.
