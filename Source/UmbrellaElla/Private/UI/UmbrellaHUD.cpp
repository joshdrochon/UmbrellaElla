#include "UI/UmbrellaHUD.h"
#include "Core/EllaCharacter.h"
#include "Core/UmbrellaTuning.h"
#include "Engine/Canvas.h"
#include "Engine/Engine.h"
#include "Engine/Font.h"
#include "Engine/World.h"
#include "Harness/UmbrellaFeatureFlags.h"
#include "Health/UmbrellaHealthComponent.h"
#include "UI/ClockHudModel.h"
#include "UI/Style/UmbrellaUIStyle.h"

namespace
{
	/** Numerals on the quarter marks, clockwise from XII. */
	const TCHAR* NumeralText[ClockHudConstants::NumeralCount] = { TEXT("XII"), TEXT("III"), TEXT("VI"), TEXT("IX") };
}

void AUmbrellaHUD::DrawHUD()
{
	Super::DrawHUD();
	if (!IsFeatureEnabled(EFeatureId::FLOW_30) || !Canvas)
	{
		return;
	}
	const AEllaCharacter* Ella = Cast<AEllaCharacter>(GetOwningPawn());
	const UUmbrellaHealthComponent* Health = Ella ? Ella->GetHealth() : nullptr;
	if (!Health)
	{
		return;
	}
	const FHudTuning& Tuning = GetDefault<UUmbrellaTuning>()->Hud;
	const FHealthState& State = Health->GetState();
	const FClockLayout Layout = ClockHudRules::ComputeLayout(FVector2D(Canvas->ClipX, Canvas->ClipY), Tuning);

	const float Dt = GetWorld() ? GetWorld()->GetDeltaSeconds() : 0.0f;
	const float HealthTarget = HealthRules::HealthHandDegrees(State);
	const float LifeTarget = ClockHudRules::LifeHandDegrees(State, Tuning);
	DrawnHealthDegrees = DrawnHealthDegrees < 0.0f ? HealthTarget : ClockHudRules::FollowAngle(DrawnHealthDegrees, HealthTarget, Dt, Tuning);
	DrawnLifeDegrees = DrawnLifeDegrees < 0.0f ? LifeTarget : ClockHudRules::FollowAngle(DrawnLifeDegrees, LifeTarget, Dt, Tuning);

	// Face and rim: the etched dial of the shared UI style; the plain drawn dial only while that art is not imported.
	if (UTexture2D* Dial = FUmbrellaUIStyle::ClockFaceTexture())
	{
		const float Half = Layout.Radius / UmbrellaUIStyleConstants::ClockFaceRimShare;
		DrawTexture(Dial, Layout.Center.X - Half, Layout.Center.Y - Half, Half * 2.0f, Half * 2.0f, 0.0f, 0.0f, 1.0f, 1.0f, FLinearColor::White, BLEND_Translucent);
	}
	else
	{
		Canvas->K2_DrawPolygon(nullptr, Layout.Center, FVector2D(Layout.Radius, Layout.Radius), Tuning.RimSegments, Tuning.FaceColor);
		DrawCircleOutline(Layout.Center, Layout.Radius, Tuning.RimSegments, Tuning.RimThickness, Tuning.RimColor);

		// Hour ticks.
		for (float Degrees = 0.0f; Degrees < ClockHudConstants::FullTurnDegrees; Degrees += ClockHudConstants::TickStepDegrees)
		{
			const FVector2D Outer = ClockHudRules::PointOnFace(Layout.Center, Layout.Radius, Degrees);
			const FVector2D Inner = ClockHudRules::PointOnFace(Layout.Center, Layout.Radius * (1.0f - ClockHudConstants::TickLengthFraction), Degrees);
			DrawLine(Outer.X, Outer.Y, Inner.X, Inner.Y, Tuning.RimColor, ClockHudConstants::TickThickness);
		}
	}

	// Numerals, at least the minimum text size.
	// Lettered in the game's display face; the engine font only if that face is missing.
	UFont* Font = FUmbrellaUIStyle::DisplayCanvasFont();
	if (!Font)
	{
		Font = GEngine ? GEngine->GetMediumFont() : nullptr;
	}
	if (Font)
	{
		const float ViewHeight = static_cast<float>(Layout.View.GetSize().Y);
		const float Scale = ClockHudRules::TextScale(Font->GetMaxCharHeight(), ViewHeight, Tuning);
		for (int32 Quarter = 0; Quarter < ClockHudConstants::NumeralCount; ++Quarter)
		{
			const TCHAR* Text = NumeralText[Quarter];
			const float Degrees = ClockHudConstants::QuarterTurnDegrees * static_cast<float>(Quarter);
			float Width = 0.0f;
			float Height = 0.0f;
			GetTextSize(Text, Width, Height, Font, Scale);
			const FVector2D At = ClockHudRules::PointOnFace(Layout.Center, Layout.Radius * ClockHudConstants::NumeralRadiusFraction, Degrees);
			DrawText(Text, Tuning.NumeralColor, At.X - Width * 0.5f, At.Y - Height * 0.5f, Font, Scale);
		}
	}

	// Warm gold arc: drains with damage, refills with healing.
	if (IsFeatureEnabled(EFeatureId::FLOW_32))
	{
		const float Fraction = State.Capacity > 0.0f ? FMath::Clamp(State.Active / State.Capacity, 0.0f, 1.0f) : 0.0f;
		DrawArc(Layout.Center, Layout.Radius * (1.0f - ClockHudConstants::ArcInsetFraction), 0.0f, ClockHudConstants::QuarterTurnDegrees * Fraction,
			Tuning.RimSegments, Tuning.ArcThickness, Tuning.ArcColor);
	}

	// Life hand: shorter, thicker, with a block at the tip.
	if (IsFeatureEnabled(EFeatureId::FLOW_31))
	{
		const FVector2D Tip = ClockHudRules::PointOnFace(Layout.Center, Layout.Radius * Tuning.LifeHandLength, DrawnLifeDegrees);
		DrawHandBlade(Layout.Center, Tip, Tuning.LifeHandThickness * UmbrellaUI::HandBladeWidthShare, Tuning.LifeHandColor);
		DrawRect(Tuning.LifeHandColor, Tip.X - ClockHudConstants::LifeTipSize * 0.5f, Tip.Y - ClockHudConstants::LifeTipSize * 0.5f, ClockHudConstants::LifeTipSize, ClockHudConstants::LifeTipSize);
	}

	// Health hand: long and thin.
	const FVector2D HealthTip = ClockHudRules::PointOnFace(Layout.Center, Layout.Radius * Tuning.HealthHandLength, DrawnHealthDegrees);
	DrawHandBlade(Layout.Center, HealthTip, Tuning.HealthHandThickness * UmbrellaUI::HandBladeWidthShare, Tuning.HealthHandColor);
}

void AUmbrellaHUD::DrawHandBlade(const FVector2D& Center, const FVector2D& Tip, float Width, const FLinearColor& Color)
{
	// A tapered blade, as the hands on the painted clocks of the menus: two triangles.
	const FUmbrellaHandBlade Blade = FUmbrellaUIStyle::HandBlade(Center, Tip, Width);
	TArray<FCanvasUVTri> Triangles;
	for (const FVector2D& Outer : { Blade.Tail, Blade.Tip })
	{
		FCanvasUVTri& Triangle = Triangles.AddDefaulted_GetRef();
		Triangle.V0_Pos = Blade.Left;
		Triangle.V1_Pos = Outer;
		Triangle.V2_Pos = Blade.Right;
		Triangle.V0_Color = Color;
		Triangle.V1_Color = Color;
		Triangle.V2_Color = Color;
	}
	Canvas->K2_DrawTriangle(nullptr, Triangles);
}

void AUmbrellaHUD::DrawCircleOutline(const FVector2D& Center, float Radius, int32 Segments, float Thickness, const FLinearColor& Color)
{
	DrawArc(Center, Radius, 0.0f, ClockHudConstants::FullTurnDegrees, Segments, Thickness, Color);
}

void AUmbrellaHUD::DrawArc(const FVector2D& Center, float Radius, float FromDegrees, float ToDegrees, int32 Segments, float Thickness, const FLinearColor& Color)
{
	if (ToDegrees <= FromDegrees || Segments < 1)
	{
		return;
	}
	const float Step = (ToDegrees - FromDegrees) / static_cast<float>(Segments);
	FVector2D Previous = ClockHudRules::PointOnFace(Center, Radius, FromDegrees);
	for (int32 Index = 1; Index <= Segments; ++Index)
	{
		const FVector2D Next = ClockHudRules::PointOnFace(Center, Radius, FromDegrees + Step * static_cast<float>(Index));
		DrawLine(Previous.X, Previous.Y, Next.X, Next.Y, Color, Thickness);
		Previous = Next;
	}
}
