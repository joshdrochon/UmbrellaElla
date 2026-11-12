#pragma once

#include "CoreMinimal.h"

/** Plain contract rules for readability, calibration, descent catch flow and checkpoint /
 *  boss arrival. No tuning numbers: the GDD gives none (QA-36 measures them). Each returns true (not
 *  enforced) when its feature flag is off. Lane e. */
namespace LevelContracts
{
	/** the drawn wind field width equals the usable width within Tolerance (not just its centreline). */
	UMBRELLAELLA_API bool IsWindFieldDrawnTrue(float DrawnWidth, float UsableWidth, float Tolerance);

	/** the player stays inside the view after the scroll lead in both directions. */
	UMBRELLAELLA_API bool IsLeadSafeBothDirections(float PlayerX, float ViewWidth, float RouteMinX, float RouteMaxX);

	/** every route stage [Start,End] is covered by a background span; Spans may overlap. */
	UMBRELLAELLA_API bool IsRouteCoveredByBackground(const TArray<FVector2D>& Stages, const TArray<FVector2D>& Spans);

	/** Value lies inside the measured, qualified envelope [Min,Max]; outside is unqualified. */
	UMBRELLAELLA_API bool IsInsideQualifiedEnvelope(float Value, float QualifiedMin, float QualifiedMax);

	/** a descent decision at DecisionHeight above the bottom leaves at least ReopenHeight to reopen. */
	UMBRELLAELLA_API bool IsReopenHeightEnough(float DecisionHeightAboveBottom, float ReopenHeight);

	/** a required current may only be gone once its challenge is clear. */
	UMBRELLAELLA_API bool IsRequiredCurrentValid(bool bChallengeClear, bool bCurrentActive);

	/** health carried through a checkpoint or boss arrival; never healed, never above Max. */
	UMBRELLAELLA_API int32 CarriedHealth(int32 Current, int32 Max);

	/** boss arrival begins when no threats remain and the framing has settled. */
	UMBRELLAELLA_API bool IsBossArrivalReady(int32 ThreatsRemaining, bool bFramingSettled);
}
