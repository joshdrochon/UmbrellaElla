#pragma once

#include "CoreMinimal.h"

/**
 * Figure draw scale (D-new-character-scale, Josh, 13 Nov): Ella's and the Keeper's pictures draw this many times their
 * old size. Visual only: hitboxes, collision, speeds, GDD numbers and the camera framing are unchanged (the camera margin
 * still frames the old sprite height, so the background stays exactly as before).
 */
namespace UmbrellaFigureScale
{
	/** Ella about 1.5x, toward ~15% of the screen height. */
	static constexpr double Ella = 1.5;
	/** The Keeper about 1.5x, toward 45-50% of the screen height. */
	static constexpr double Keeper = 1.5;
}
