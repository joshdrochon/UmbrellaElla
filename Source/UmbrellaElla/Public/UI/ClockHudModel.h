#pragma once

#include "CoreMinimal.h"

struct FHudTuning;
struct FHealthState;

namespace ClockHudConstants
{
	/** Face geometry. Angles are degrees clockwise from XII. */
	static constexpr float FullTurnDegrees = 360.0f;
	static constexpr float QuarterTurnDegrees = 90.0f;
	static constexpr int32 NumeralCount = 4;
	static constexpr float NumeralRadiusFraction = 0.68f;
	static constexpr float TickStepDegrees = 30.0f;
	static constexpr float TickLengthFraction = 0.1f;
	static constexpr float TickThickness = 2.0f;
	static constexpr float LifeTipSize = 10.0f;
	static constexpr float ArcInsetFraction = 0.15f;
}

/** Where the clock sits on a canvas. */
struct FClockLayout
{
	/** The 16:9 play view inside the canvas (letterboxed). */
	FBox2D View = FBox2D(ForceInit);

	FVector2D Center = FVector2D::ZeroVector;
	float Radius = 0.0f;

	/** Bounding square of the clock including the rim. */
	FBox2D ClockBounds = FBox2D(ForceInit);
};

/** Plain rule functions of the clock HUD. Tests call them without a canvas. */
namespace ClockHudRules
{
	/** The largest 16:9 rectangle centered in the canvas, and the clock at its top-left. */
	UMBRELLAELLA_API FClockLayout ComputeLayout(const FVector2D& Canvas, const FHudTuning& Tuning);

	/** Text scale that keeps text at least MinTextPx tall: font height times scale >= MinTextPx x (view height / reference), floor MinTextPx. */
	UMBRELLAELLA_API float TextScale(float FontHeightPx, float ViewHeightPx, const FHudTuning& Tuning);

	/**
	 * Life hand angle, degrees clockwise from XII. Full lives: LifeHandFullDegrees. Each lost life moves it toward XII (360);
	 * restoring progress moves it back toward the next slot. No lives: 360 (XII).
	 */
	UMBRELLAELLA_API float LifeHandDegrees(const FHealthState& State, const FHudTuning& Tuning);

	/** Point on the face at an angle (degrees clockwise from XII, screen Y grows downward). */
	UMBRELLAELLA_API FVector2D PointOnFace(const FVector2D& Center, float Radius, float Degrees);

	/** Move a drawn angle toward its target at a capped speed. Presentation only. */
	UMBRELLAELLA_API float FollowAngle(float Drawn, float Target, float Dt, const FHudTuning& Tuning);
}
