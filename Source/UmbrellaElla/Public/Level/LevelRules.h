#pragma once

#include "CoreMinimal.h"

/** Plain rule functions for the Director's Cut traversal and camera contract. Tests call them. Lane e. */
namespace LevelRules
{
	/** initial margin m = max(0.03 H, a quarter of the hurtbox diameter). */
	UMBRELLAELLA_API float ClearanceMargin(float ArenaHeight, float HurtboxDiameter);

	/** the opening is at least 2 rx + 2 m wide and 2 rz + 2 m tall. */
	UMBRELLAELLA_API bool CanOpeningFit(float OpeningWidth, float OpeningHeight, float HalfExtentX, float HalfExtentZ, float Margin);

	/** entrance/exit centre height. */
	UMBRELLAELLA_API float InterfaceHeight(float ArenaHeight);

	/** safe vestibule length. */
	UMBRELLAELLA_API float VestibuleLength(float ArenaWidth);

	/** vertical clearance of an interface is at least max(0.3 H, the measured safe-cycle envelope). */
	UMBRELLAELLA_API float MinVerticalClearance(float ArenaHeight, float MeasuredSafeCycleEnvelope);

	/** the whole hazard box lies inside the view rectangle, with an edge margin. */
	UMBRELLAELLA_API bool IsFullyRevealed(const FBox2D& Hazard, const FBox2D& View, float EdgeMargin);

	/** the segment Start-End stays at least Radius + ShotRadius + Margin from Center along its whole length. */
	UMBRELLAELLA_API bool IsRayClearOfCircle(const FVector2D& Start, const FVector2D& End, const FVector2D& Center, float Radius, float ShotRadius, float Margin);

	/** point is inside the activation region [MinX,MaxX] x [MinZ,MaxZ]. */
	UMBRELLAELLA_API bool IsInActivationRegion(const FVector2D& Point, const FBox2D& Region);
}
