#pragma once

#include "CoreMinimal.h"

/** Plain rule functions for the Director's Cut traversal and camera contract (CAM-05, CAM-06, CAM-08, HAZ-04). Tests call them. Lane e. */
namespace LevelRules
{
	/** CAM-06: initial margin m = max(0.03 H, a quarter of the hurtbox diameter). */
	UMBRELLAELLA_API float ClearanceMargin(float ArenaHeight, float HurtboxDiameter);

	/** CAM-06: the opening is at least 2 rx + 2 m wide and 2 rz + 2 m tall. */
	UMBRELLAELLA_API bool OpeningFits(float OpeningWidth, float OpeningHeight, float HalfExtentX, float HalfExtentZ, float Margin);

	/** CAM-05: entrance/exit centre height. */
	UMBRELLAELLA_API float InterfaceHeight(float ArenaHeight);

	/** CAM-05: safe vestibule length. */
	UMBRELLAELLA_API float VestibuleLength(float ArenaWidth);

	/** CAM-05: vertical clearance of an interface is at least max(0.3 H, the measured safe-cycle envelope). */
	UMBRELLAELLA_API float MinVerticalClearance(float ArenaHeight, float MeasuredSafeCycleEnvelope);

	/** CAM-08: the whole hazard box lies inside the view rectangle, with an edge margin. */
	UMBRELLAELLA_API bool IsFullyRevealed(const FBox2D& Hazard, const FBox2D& View, float EdgeMargin);

	/** HAZ-09: the segment Start-End stays at least Radius + ShotRadius + Margin from Center along its whole length. */
	UMBRELLAELLA_API bool RayClearsCircle(const FVector2D& Start, const FVector2D& End, const FVector2D& Center, float Radius, float ShotRadius, float Margin);

	/** HAZ-04: point is inside the activation region [MinX,MaxX] x [MinZ,MaxZ]. */
	UMBRELLAELLA_API bool InActivationRegion(const FVector2D& Point, const FBox2D& Region);
}
