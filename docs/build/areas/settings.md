# Area: settings (player settings, remapping, credits, developer options)

Branch `area/settings`. Read `docs/build/worker-rules.md` first. Split from `flow` Nov 12 14:08.

## Rule IDs (G2/G3)
FLOW-36 .. FLOW-40 (player settings in both modes, sound sliders, Director-only developer Game Options, credits,
submenu Back and Save), FLOW-43 .. FLOW-45 (settings save/reset scope, developer menu candidates, accessibility help
candidates), MOVE-10, MOVE-17 (the Controller menu remaps keyboard, mouse and controller buttons).

## GDD sections
7 (Menus, settings and accessibility; Settings and earned-character interactions), 3 "Menus and remapping" and
"Default controls and input behavior".

## File lane (only these)
- `Source/UmbrellaElla/{Public,Private}/Settings/**`, `UI/Settings/**`
- `Source/UmbrellaElla/Private/Tests/Settings/**`
- `Content/UmbrellaElla/UI/Settings/**`, `docs/build/areas/settings-status.md`, `docs/build/requests/settings.md`

## What to build
- `USettingsMenuSubsystem` (GameInstance subsystem) with `OpenSettings(APlayerController*)`; the flow area's pause and
  title menus call it. C++ widgets: Sound (sliders by sound class), Controller (remap), Credits, Back, Save.
- Remapping through Enhanced Input user settings (`UEnhancedInputUserSettings`, player-mappable keys) for the
  gameplay actions the move area defined in `Content/UmbrellaElla/Input/` (read their names; do not edit their assets).
  If those actions are not player-mappable, write the exact change in `docs/build/requests/settings.md`.
- Save applies and persists (`UGameUserSettings` or a settings `USaveGame`); persistent settings stay independent of
  earned progression (CORE-05). Tests must not leave changes in Saved/ (test.sh hashes GameUserSettings.ini and
  SaveGames): use a test-only slot and delete it.
- Developer Game Options (FLOW-38) only in Director's Cut, behind its flag.

## Done
Worker-rules DoD, plus tests: a remap changes the key for an action and Save persists it (test slot), Back discards
unsaved changes, sound sliders set the class volume, developer options hidden in Start Game.
