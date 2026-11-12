#include "UI/ClockHudModel.h"
#include "Health/HealthModel.h"
#include "UI/HudTuning.h"

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
