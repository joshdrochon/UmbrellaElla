#pragma once

#include "CoreMinimal.h"

/** Plain cadence rule for the Attack Emitter. */
namespace AttackCadence
{
	/**
	 * Advance the countdown by DeltaSeconds. While bWantsFire is true each time it reaches zero a shot is due and the
	 * countdown grows by one interval (leftover time is kept, so the rate is exact at any delta). Returns shots due.
	 * Not firing: the countdown stops at zero, so the first shot after a pause is immediate.
	 */
	UMBRELLAELLA_API int32 Step(float& Countdown, float DeltaSeconds, float ShotsPerSecond, bool bWantsFire);
}
