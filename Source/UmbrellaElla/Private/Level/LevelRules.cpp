#include "Level/LevelRules.h"
#include "Core/UmbrellaTuning.h"
#include "Harness/UmbrellaFeatureFlags.h"

namespace LevelRules
{
	float ClearanceMargin(float ArenaHeight, float HurtboxDiameter)
	{
		const FFieldTuning& T = GetDefault<UUmbrellaTuning>()->Field;
		return FMath::Max(T.ClearanceMarginHeightFraction * ArenaHeight, T.ClearanceMarginDiameterFraction * HurtboxDiameter);
	}

	bool OpeningFits(float OpeningWidth, float OpeningHeight, float HalfExtentX, float HalfExtentZ, float Margin)
	{
		return OpeningWidth >= 2.0f * HalfExtentX + 2.0f * Margin && OpeningHeight >= 2.0f * HalfExtentZ + 2.0f * Margin;
	}

	float InterfaceHeight(float ArenaHeight)
	{
		return GetDefault<UUmbrellaTuning>()->Field.InterfaceHeightFraction * ArenaHeight;
	}

	float VestibuleLength(float ArenaWidth)
	{
		return GetDefault<UUmbrellaTuning>()->Field.VestibuleFraction * ArenaWidth;
	}

	float MinVerticalClearance(float ArenaHeight, float MeasuredSafeCycleEnvelope)
	{
		return FMath::Max(GetDefault<UUmbrellaTuning>()->Field.MinClearanceHeightFraction * ArenaHeight, MeasuredSafeCycleEnvelope);
	}

	bool IsFullyRevealed(const FBox2D& Hazard, const FBox2D& View, float EdgeMargin)
	{
		const FBox2D Inner(View.Min + FVector2D(EdgeMargin, EdgeMargin), View.Max - FVector2D(EdgeMargin, EdgeMargin));
		return Inner.bIsValid && Hazard.bIsValid && Inner.IsInside(Hazard.Min) && Inner.IsInside(Hazard.Max);
	}

	bool RayClearsCircle(const FVector2D& Start, const FVector2D& End, const FVector2D& Center, float Radius, float ShotRadius, float Margin)
	{
		const FVector Closest = FMath::ClosestPointOnSegment(FVector(Center, 0.0), FVector(Start, 0.0), FVector(End, 0.0));
		return FVector2D::Distance(FVector2D(Closest.X, Closest.Y), Center) >= Radius + ShotRadius + Margin;
	}

	bool InActivationRegion(const FVector2D& Point, const FBox2D& Region)
	{
		return Region.IsInside(Point);
	}
}
