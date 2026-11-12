# Requests from visuals

## 1. Wire reduced flash to the settings model (settings lane) — VFX-10
`UUmbrellaVfxSubsystem::SetReducedFlash(bool)` shrinks flashing effects to `ReducedFlashScale` (0.4), but nothing calls it:
`FSettingsData` has only `bReducedMotion`. Reduced flash is unreachable until settings does this.

1. `Settings/SettingsModel.h`: add `bool bReducedFlash = false;` next to `bReducedMotion`; include it in the equality
   operator, `Defaults` (false) and the Save copy (`SettingsModel.cpp` lines ~10, ~34, ~317); add `SetReducedFlash(bool)` on the draft (like line ~269).
2. `Settings/SettingsStore.cpp`: read/write `ReducedFlash` in the Access section (like `ReducedMotion`, lines ~69, ~92).
3. `UI/Settings/SettingsMenuSubsystem/Widget`: add an Accessibility checkbox bound to the draft (like line ~352).
4. On Save/apply, and when a world starts, call:

       if (UUmbrellaVfxSubsystem* Vfx = World->GetSubsystem<UUmbrellaVfxSubsystem>())
       {
           Vfx->SetReducedFlash(Saved.bReducedFlash);
       }

   (include `Feedback/Vfx/UmbrellaVfxSubsystem.h`). Visuals test `UmbrellaElla.Feedback.World.VfxLayersLightLimits` covers the shrink.
