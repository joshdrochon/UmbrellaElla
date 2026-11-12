# settings status

## Done (commit "settings: ...")
Rule IDs: FLOW-36, FLOW-37, FLOW-38, FLOW-39, FLOW-40, FLOW-43, FLOW-44, FLOW-45 (candidates), MOVE-10, MOVE-17.
- `Settings/SettingsModel` (draft over saved, page-scoped Save/Discard, Back prompt, pages by mode, credits, developer
  option names, Shoot/Absorb conflict, remap-aware key labels), `SettingsStore` (plain-text file), 
  `SettingsMenuSubsystem` (OpenSettings, SaveSettings, volumes to sound classes, remap into the live mapping context).
- `UI/Settings/SettingsMenuWidget`: Slate widget, tabs Sound / Controller / Credits / Game Options (Director's Cut
  only), Back + Save, Save / Discard / Keep Editing prompt, click-to-remap capture (key, mouse, gamepad; Esc cancels),
  text size and reduced motion on the Sound page, Reset bindings.

## Tests (`UmbrellaElla.Settings.*`, 12, all PASS)
Defaults, PagesByMode (developer options hidden in Start Game), SliderRange, RemapChangesDraftKey,
BackDiscardsUnsaved, SaveAppliesCurrentPage, ShootAbsorbConflictRecovery, Credits, SavePersistsRemap (scratch file,
deleted), SlidersSetClassVolume, RemapRebuildsMappingContext, WidgetBackAndPages.

## Left / not verified
- No window test: the Slate layout has not been seen on screen (headless only).
- Saved bindings are not applied at spawn until request 1 in `requests/settings.md` lands.
- Flow must call `SetPlayMode` and `OpenSettings` (requests 2).
- A left-click while waiting for a key lands on a Slate button first, so the mouse can only be captured on a non-button area; keyboard and gamepad capture normally.
- Game Options page lists the FLOW-44 candidate names only (contents are OPEN in the GDD).
- Text size and reduced motion are stored and shown here; other screens do not read them yet.
