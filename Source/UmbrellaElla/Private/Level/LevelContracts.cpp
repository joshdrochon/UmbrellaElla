#include "Level/LevelContracts.h"
#include "Level/LevelCatalogue.h"
#include "Level/LevelRules.h"
#include "Harness/UmbrellaFeatureFlags.h"

namespace LevelContracts
{
	bool IsWindFieldDrawnTrue(float DrawnWidth, float UsableWidth, float Tolerance)
	{
		if (!IsFeatureEnabled(EFeatureId::FLOW_25))
		{
			return true;
		}
		return FMath::Abs(DrawnWidth - UsableWidth) <= Tolerance;
	}

	bool IsLeadSafeBothDirections(float PlayerX, float ViewWidth, float RouteMinX, float RouteMaxX)
	{
		if (!IsFeatureEnabled(EFeatureId::FLOW_25))
		{
			return true;
		}
		for (const int32 Direction : {-1, 1})
		{
			const float Centre = CameraRules::ScrollCentreX(PlayerX, Direction, ViewWidth, RouteMinX, RouteMaxX);
			if (FMath::Abs(PlayerX - Centre) > ViewWidth * 0.5f)
			{
				return false;
			}
		}
		return true;
	}

	bool IsRouteCoveredByBackground(const TArray<FVector2D>& Stages, const TArray<FVector2D>& Spans)
	{
		if (!IsFeatureEnabled(EFeatureId::FLOW_25))
		{
			return true;
		}
		for (const FVector2D& Stage : Stages)
		{
			float Reach = Stage.X;
			bool bGrew = true;
			while (bGrew && Reach < Stage.Y)
			{
				bGrew = false;
				for (const FVector2D& Span : Spans)
				{
					if (Span.X <= Reach && Span.Y > Reach)
					{
						Reach = Span.Y;
						bGrew = true;
					}
				}
			}
			if (Reach < Stage.Y)
			{
				return false;
			}
		}
		return true;
	}

	bool IsInsideQualifiedEnvelope(float Value, float QualifiedMin, float QualifiedMax)
	{
		if (!IsFeatureEnabled(EFeatureId::CAM_04))
		{
			return true;
		}
		return Value >= QualifiedMin && Value <= QualifiedMax;
	}

	bool IsReopenHeightEnough(float DecisionHeightAboveBottom, float ReopenHeight)
	{
		if (!IsFeatureEnabled(EFeatureId::CAM_07))
		{
			return true;
		}
		return DecisionHeightAboveBottom >= ReopenHeight;
	}

	bool IsRequiredCurrentValid(bool bChallengeClear, bool bCurrentActive)
	{
		if (!IsFeatureEnabled(EFeatureId::CAM_07))
		{
			return true;
		}
		return bChallengeClear || bCurrentActive;
	}

	int32 CarriedHealth(int32 Current, int32 Max)
	{
		return FMath::Clamp(Current, 0, FMath::Max(Max, 0));
	}

	bool IsBossArrivalReady(int32 ThreatsRemaining, bool bFramingSettled)
	{
		if (!IsFeatureEnabled(EFeatureId::FLOW_28))
		{
			return true;
		}
		return ThreatsRemaining <= 0 && bFramingSettled;
	}
}
