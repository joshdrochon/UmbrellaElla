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
	/** Look checks of the dial colours: smoky face and antique bronze/gold rim. */
	static constexpr float SmokyMaxLuminance = 0.15f;
	static constexpr float SmokyMinAlpha = 0.25f;
	static constexpr float SmokyMaxAlpha = 0.8f;
	static constexpr float BronzeMinRed = 0.5f;
	static constexpr float BronzeMaxBlueShare = 0.5f;
	/** t(1-t) peaks at 1/4: this scale makes the energy bow peak at EnergyArcBow of the distance. */
	static constexpr float EnergyBowPeakScale = 4.0f;
	static constexpr int32 EnergyMoteSides = 8;
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

/** One ring or mark of the drawn dial: a circle (ring) or a radial line (mark). */
struct FClockDialStroke
{
	bool bRing = true;
	float Radius = 0.0f;
	float InnerRadius = 0.0f;
	float Degrees = 0.0f;
	float Thickness = 1.0f;
	FLinearColor Color = FLinearColor::White;
};

/** What the HUD draws for the dial: the smoky face (always, so the live scene shows faintly through), then either the
 *  dial art or the drawn bronze rim with its etched ring and marks. */
struct FClockDialPlan
{
	FLinearColor FaceColor = FLinearColor::Black;
	bool bDrawArt = false;
	TArray<FClockDialStroke> Strokes;
};

/** One mote of absorbed energy on its way into the clock. Screen space. */
struct FClockEnergyMote
{
	FVector2D From = FVector2D::ZeroVector;
	FVector2D To = FVector2D::ZeroVector;
	float Age = 0.0f;
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

	/** The dial to draw (bHasArt: the face art is imported). */
	UMBRELLAELLA_API FClockDialPlan BuildDialPlan(const FClockLayout& Layout, const FHudTuning& Tuning, bool bHasArt);

	/** A smoky translucent face: dark (luminance under 0.15) and part see-through (alpha 0.25..0.8). */
	UMBRELLAELLA_API bool IsSmokyTranslucent(const FLinearColor& Color);

	/** Antique bronze/gold: warm (red over green over blue), bright enough to read, blue well under red. */
	UMBRELLAELLA_API bool IsAntiqueBronzeGold(const FLinearColor& Color);

	/** A health event that sends energy into the clock: only a real heal (not a full-health capture, not damage). */
	UMBRELLAELLA_API bool IsEnergyFlowEvent(FName HealthDetail);

	/** Advance motes by Dt; a mote that has arrived is removed. Returns how many arrived this step. */
	UMBRELLAELLA_API int32 StepEnergy(TArray<FClockEnergyMote>& Motes, float Dt, const FHudTuning& Tuning);

	/** Where a mote is at its age: leaves From, bows upward, lands exactly on To when the flow time is over. */
	UMBRELLAELLA_API FVector2D EnergyPosition(const FClockEnergyMote& Mote, float AgeSeconds, const FHudTuning& Tuning);

	/** Move a drawn angle toward its target at a capped speed. Presentation only. */
	UMBRELLAELLA_API float FollowAngle(float Drawn, float Target, float Dt, const FHudTuning& Tuning);
}
