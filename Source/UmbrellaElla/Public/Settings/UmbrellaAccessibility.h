#pragma once

#include "CoreMinimal.h"

class UObject;
struct FSettingsLiveTuning;

/**
 * The saved accessibility settings for readers outside the settings menu (HUD, menus, effects, camera).
 * Values change only when the player presses Save. With no settings subsystem (a bare test world) every reader gets the
 * shipped default: 100% text, full motion, full flash.
 */
namespace UmbrellaAccessibility
{
	/** Saved text size in percent (100 to 200). */
	UMBRELLAELLA_API int32 GetTextScalePercent(const UObject* WorldContext);

	/** Saved text size as a multiplier (1.0 to 2.0). */
	UMBRELLAELLA_API float GetTextScale(const UObject* WorldContext);

	/** True when the player asked for reduced motion (no screen shake, still backgrounds). */
	UMBRELLAELLA_API bool IsReducedMotion(const UObject* WorldContext);

	/** True when the player asked for reduced flash. */
	UMBRELLAELLA_API bool IsReducedFlash(const UObject* WorldContext);

	/** Multiply every screen-shake amplitude by this: 0 under reduced motion, 1 otherwise. */
	UMBRELLAELLA_API float GetShakeScale(const UObject* WorldContext);

	/** Text percent to a multiplier. Pure. */
	UMBRELLAELLA_API float TextScaleFromPercent(int32 Percent);

	/** A font size scaled by a text percent. Pure. */
	UMBRELLAELLA_API int32 ScaledFontSize(int32 BaseSize, int32 Percent);

	/** Shake multiplier for a reduced-motion state. Pure. */
	UMBRELLAELLA_API float ShakeScaleFor(bool bReducedMotion);

#if UMBRELLAELLA_WORKBENCH
	/** Reduced-motion presentation on a tuning copy: still menu backgrounds, no ring pulse, no Keeper hover. Pure. */
	UMBRELLAELLA_API void ApplyReducedMotion(FSettingsLiveTuning& Tuning);
#endif
}
