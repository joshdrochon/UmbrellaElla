#include "UI/ClockHudModel.h"
#include "Health/HealthModel.h"
#include "UI/HudTuning.h"
#include "Harness/UmbrellaFeatureFlags.h"

FClockLayout ClockHudRules::ComputeLayout(const FVector2D& Canvas, const FHudTuning& Tuning)
{
	FClockLayout Layout;
	const float Aspect = Tuning.ViewAspectWidth / Tuning.ViewAspectHeight;
	const float ViewW = FMath::Min(static_cast<float>(Canvas.X), static_cast<float>(Canvas.Y) * Aspect);
	const float ViewH = ViewW / Aspect;
	const FVector2D Min((Canvas.X - ViewW) * 0.5, (Canvas.Y - ViewH) * 0.5);
	Layout.View = FBox2D(Min, Min + FVector2D(ViewW, ViewH));

	Layout.Radius = ViewH * Tuning.ClockRadiusFraction;
	const float Margin = ViewH * Tuning.MarginFraction;
	const float Edge = Layout.Radius + Tuning.RimThickness;
	Layout.Center = Min + FVector2D(Margin + Edge, Margin + Edge);
	Layout.ClockBounds = FBox2D(Layout.Center - FVector2D(Edge, Edge), Layout.Center + FVector2D(Edge, Edge));
	return Layout;
}

float ClockHudRules::TextScale(float FontHeightPx, float ViewHeightPx, const FHudTuning& Tuning)
{
	const float Wanted = Tuning.MinTextPx * FMath::Max(ViewHeightPx / Tuning.TextReferenceHeightPx, 1.0f);
	return FontHeightPx > 0.0f ? Wanted / FontHeightPx : 1.0f;
}

float ClockHudRules::LifeHandDegrees(const FHealthState& State, const FHudTuning& Tuning)
{
	const float Full = Tuning.LifeHandFullDegrees;
	if (State.IsDefeated() || State.MaxLives <= 0)
	{
		return ClockHudConstants::FullTurnDegrees;
	}
	const float Progress = State.Capacity > 0.0f ? State.ReserveProgress / State.Capacity : 0.0f;
	const float LivesFraction = FMath::Clamp((static_cast<float>(State.Lives) + Progress) / static_cast<float>(State.MaxLives), 0.0f, 1.0f);
	return Full + (ClockHudConstants::FullTurnDegrees - Full) * (1.0f - LivesFraction);
}

FVector2D ClockHudRules::PointOnFace(const FVector2D& Center, float Radius, float Degrees)
{
	const float Radians = FMath::DegreesToRadians(Degrees);
	return Center + FVector2D(FMath::Sin(Radians), -FMath::Cos(Radians)) * Radius;
}

float ClockHudRules::FollowAngle(float Drawn, float Target, float Dt, const FHudTuning& Tuning)
{
	const float MaxStep = Tuning.HandSpeedDegreesPerSecond * FMath::Max(Dt, 0.0f);
	return Drawn + FMath::Clamp(Target - Drawn, -MaxStep, MaxStep);
}

FClockDialPlan ClockHudRules::BuildDialPlan(const FClockLayout& Layout, const FHudTuning& Tuning, bool bHasArt)
{
	FClockDialPlan Plan;
	Plan.FaceColor = Tuning.FaceColor;
	Plan.bDrawArt = bHasArt;
	if (bHasArt)
	{
		return Plan;
	}
	FClockDialStroke& Rim = Plan.Strokes.AddDefaulted_GetRef();
	Rim.Radius = Layout.Radius;
	Rim.Thickness = Tuning.RimThickness;
	Rim.Color = Tuning.RimColor;
	for (float Degrees = 0.0f; Degrees < ClockHudConstants::FullTurnDegrees; Degrees += ClockHudConstants::TickStepDegrees)
	{
		FClockDialStroke& Tick = Plan.Strokes.AddDefaulted_GetRef();
		Tick.bRing = false;
		Tick.Degrees = Degrees;
		Tick.Radius = Layout.Radius;
		Tick.InnerRadius = Layout.Radius * (1.0f - ClockHudConstants::TickLengthFraction);
		Tick.Thickness = ClockHudConstants::TickThickness;
		Tick.Color = Tuning.RimColor;
	}
	if (!IsFeatureEnabled(EFeatureId::FLOW_30))
	{
		return Plan;
	}
	// The etching: a fine ring just inside the rim and fine marks between the hour ticks.
	const float EtchRadius = Layout.Radius * (1.0f - Tuning.EtchRingInsetFraction);
	FClockDialStroke& Ring = Plan.Strokes.AddDefaulted_GetRef();
	Ring.Radius = EtchRadius;
	Ring.Thickness = Tuning.EtchThickness;
	Ring.Color = Tuning.EtchColor;
	const int32 Marks = FMath::Max(Tuning.EtchMarkCount, 1);
	const float Step = ClockHudConstants::FullTurnDegrees / static_cast<float>(Marks);
	for (int32 Index = 0; Index < Marks; ++Index)
	{
		const float Degrees = Step * static_cast<float>(Index);
		if (FMath::IsNearlyZero(FMath::Fmod(Degrees, ClockHudConstants::TickStepDegrees), KINDA_SMALL_NUMBER))
		{
			continue;
		}
		FClockDialStroke& Mark = Plan.Strokes.AddDefaulted_GetRef();
		Mark.bRing = false;
		Mark.Degrees = Degrees;
		Mark.Radius = EtchRadius;
		Mark.InnerRadius = EtchRadius - Layout.Radius * Tuning.EtchMarkLengthFraction;
		Mark.Thickness = Tuning.EtchThickness;
		Mark.Color = Tuning.EtchColor;
	}
	return Plan;
}

bool ClockHudRules::IsSmokyTranslucent(const FLinearColor& Color)
{
	return Color.GetLuminance() < ClockHudConstants::SmokyMaxLuminance && Color.A >= ClockHudConstants::SmokyMinAlpha && Color.A <= ClockHudConstants::SmokyMaxAlpha;
}

bool ClockHudRules::IsAntiqueBronzeGold(const FLinearColor& Color)
{
	return Color.R >= ClockHudConstants::BronzeMinRed && Color.R > Color.G && Color.G > Color.B && Color.B <= Color.R * ClockHudConstants::BronzeMaxBlueShare;
}

bool ClockHudRules::IsEnergyFlowEvent(FName HealthDetail)
{
	static const FName HealName(TEXT("Heal"));
	return IsFeatureEnabled(EFeatureId::FLOW_32) && HealthDetail == HealName;
}

int32 ClockHudRules::StepEnergy(TArray<FClockEnergyMote>& Motes, float Dt, const FHudTuning& Tuning)
{
	int32 Arrived = 0;
	for (int32 Index = Motes.Num() - 1; Index >= 0; --Index)
	{
		Motes[Index].Age += FMath::Max(Dt, 0.0f);
		if (Motes[Index].Age >= Tuning.EnergyFlowSeconds)
		{
			Motes.RemoveAt(Index);
			++Arrived;
		}
	}
	return Arrived;
}

FVector2D ClockHudRules::EnergyPosition(const FClockEnergyMote& Mote, float AgeSeconds, const FHudTuning& Tuning)
{
	const float T = FMath::Clamp(AgeSeconds / FMath::Max(Tuning.EnergyFlowSeconds, KINDA_SMALL_NUMBER), 0.0f, 1.0f);
	// Ease in, so the energy gathers and then rushes into the clock; a quadratic bow lifts it on the way.
	const float Eased = T * T;
	const FVector2D Straight = FMath::Lerp(Mote.From, Mote.To, Eased);
	const float Bow = static_cast<float>((Mote.To - Mote.From).Size()) * Tuning.EnergyArcBow * ClockHudConstants::EnergyBowPeakScale * Eased * (1.0f - Eased);
	return Straight - FVector2D(0.0f, Bow);
}
