# Requests from settings2 (FLOW-44, FLOW-45)

The settings API for readers outside Settings is `Settings/UmbrellaAccessibility.h` (namespace `UmbrellaAccessibility`).
Every function takes a world context and returns the shipped default when no settings subsystem exists:
`GetTextScalePercent` (100 to 200), `GetTextScale` (1.0 to 2.0), `IsReducedMotion`, `IsReducedFlash`, `GetShakeScale`
(0 under reduced motion, else 1), plus the pure `ScaledFontSize(Base, Percent)`. Values change only on Save;
`USettingsMenuSubsystem::OnSettingsSaved()` fires after every Save so a screen that caches them can re-read.
Callers guard their read with their own FLOW_45 check (module_check rule M).

## 1. Text scale in the shared UI style (artui lane)
The artui area's shared UI style multiplies every font size by `UmbrellaAccessibility::GetTextScale(WorldContext)`
(or `ScaledFontSize(Base, GetTextScalePercent(WorldContext))`) and rebuilds on `OnSettingsSaved()`. That covers the HUD
clock text, the flow menus and the story/tutorial text, which replaces item 6 (text-size half) of
`docs/build/requests/settings.md`. The settings menu itself already scales (`USettingsMenuWidget::ScaledFont`).

## 2. Screen shake (feel / Feedback lane, when a shake exists)
No camera or screen shake exists in `Source/` today (`grep -ri shake Source` finds only this API). Whoever adds the
`pipeline/feel/feel.json` shakes multiplies each amplitude by `UmbrellaAccessibility::GetShakeScale(WorldContext)`, so
reduced motion zeroes them (`pipeline/ui/accessibility.md` E8).

## 3. Gameplay backdrop motion (visuals lane, `Feedback/Background`)
Reduced motion already stills the menu backgrounds, the XP ring pulse and the Keeper hover through the live tuning.
The gameplay backdrop's parallax constants are not tuning, so Settings cannot reach them. Request: in
`UUmbrellaBackdropSubsystem::ScrollTo`, when `UmbrellaAccessibility::IsReducedMotion(this)` use parallax 0 for every
layer (fixed to the camera, no relative slide), and tag each layer actor `BackgroundMotion` (accessibility E8).

## 4. Tutorial developer toggle (flow lane)
Game Options "First-play tutorials" (Director's Cut, developer option `EDeveloperOption::Tutorial`) has no tuning
number. Where flow decides to show a first-play tutorial, skip it when
`Settings->GetDeveloperOption(EDeveloperOption::Tutorial) == DeveloperOptionLimits::ToggleOff`. The read returns the
default (on) outside Director's Cut, so Start Game is unchanged.

## 5. Play mode (flow lane, optional)
Settings now follows `AUmbrellaPlayerController::GetPlayMode()` itself (every frame, and on `OpenSettings`), so
developer options never reach a Start Game run. Calling `USettingsMenuSubsystem::SetPlayMode` from `StartMode` would
apply them one frame earlier; not required.
