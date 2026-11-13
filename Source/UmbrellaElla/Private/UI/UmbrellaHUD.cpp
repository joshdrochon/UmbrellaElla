#include "UI/UmbrellaHUD.h"
#include "Core/EllaCharacter.h"
#include "Attack/AttackEmitterComponent.h"
#include "Core/UmbrellaEvent.h"
#include "Core/UmbrellaEventBus.h"
#include "GameFramework/PlayerController.h"
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

	LastLayout = Layout;
	DrawDial(Layout, Tuning);

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

	StepEnergyFlow(Dt);
	DrawEnergy(Layout, Tuning);
	DrawSpellWheel(Layout, Tuning, Font);
}

void AUmbrellaHUD::BeginPlay()
{
	Super::BeginPlay();
	if (UUmbrellaEventBus* Bus = UUmbrellaEventBus::Get(this))
	{
		HealthHandle = Bus->On(EUmbrellaEventType::PlayerHealthChanged).AddUObject(this, &AUmbrellaHUD::OnHealthChanged);
	}
}

void AUmbrellaHUD::EndPlay(const EEndPlayReason::Type Reason)
{
	if (UUmbrellaEventBus* Bus = UUmbrellaEventBus::Get(this))
	{
		Bus->On(EUmbrellaEventType::PlayerHealthChanged).Remove(HealthHandle);
	}
	HealthHandle.Reset();
	Super::EndPlay(Reason);
}

void AUmbrellaHUD::OnHealthChanged(const FUmbrellaEvent& Event)
{
	// Only a real heal sends energy: damage drains, and a capture at full health/all lives is not shown as healing.
	if (!ClockHudRules::IsEnergyFlowEvent(Event.Detail))
	{
		return;
	}
	FClockEnergyMote& Mote = EnergyMotes.AddDefaulted_GetRef();
	Mote.From = EllaScreenPoint();
	Mote.To = LastLayout.Center;
}

FVector2D AUmbrellaHUD::EllaScreenPoint() const
{
	const APawn* Ella = GetOwningPawn();
	FVector2D Screen = LastLayout.View.bIsValid ? LastLayout.View.GetCenter() : FVector2D::ZeroVector;
	if (Ella && PlayerOwner)
	{
		FVector2D Projected;
		if (PlayerOwner->ProjectWorldLocationToScreen(Ella->GetActorLocation(), Projected))
		{
			Screen = Projected;
		}
	}
	return Screen;
}

void AUmbrellaHUD::StepEnergyFlow(float DeltaSeconds)
{
	EnergyArrived += ClockHudRules::StepEnergy(EnergyMotes, DeltaSeconds, GetDefault<UUmbrellaTuning>()->Hud);
}

void AUmbrellaHUD::DrawDial(const FClockLayout& Layout, const FHudTuning& Tuning)
{
	UTexture2D* Dial = FUmbrellaUIStyle::ClockFaceTexture();
	const FClockDialPlan Plan = ClockHudRules::BuildDialPlan(Layout, Tuning, Dial != nullptr);
	// The smoky face first, always: dark and part see-through, so the live scene shows faintly behind the hands.
	Canvas->K2_DrawPolygon(nullptr, Layout.Center, FVector2D(Layout.Radius, Layout.Radius), Tuning.RimSegments, Plan.FaceColor);
	if (Plan.bDrawArt && Dial)
	{
		const float Half = Layout.Radius / UmbrellaUIStyleConstants::ClockFaceRimShare;
		DrawTexture(Dial, Layout.Center.X - Half, Layout.Center.Y - Half, Half * 2.0f, Half * 2.0f, 0.0f, 0.0f, 1.0f, 1.0f, FLinearColor::White, BLEND_Translucent);
	}
	for (const FClockDialStroke& Stroke : Plan.Strokes)
	{
		if (Stroke.bRing)
		{
			DrawCircleOutline(Layout.Center, Stroke.Radius, Tuning.RimSegments, Stroke.Thickness, Stroke.Color);
			continue;
		}
		const FVector2D Outer = ClockHudRules::PointOnFace(Layout.Center, Stroke.Radius, Stroke.Degrees);
		const FVector2D Inner = ClockHudRules::PointOnFace(Layout.Center, Stroke.InnerRadius, Stroke.Degrees);
		DrawLine(Outer.X, Outer.Y, Inner.X, Inner.Y, Stroke.Color, Stroke.Thickness);
	}
}

void AUmbrellaHUD::DrawEnergy(const FClockLayout& Layout, const FHudTuning& Tuning)
{
	const float Size = Tuning.EnergyMoteSizePx;
	for (FClockEnergyMote& Mote : EnergyMotes)
	{
		Mote.To = Layout.Center;
		for (int32 Dot = Tuning.EnergyTrailDots; Dot >= 0; --Dot)
		{
			const float Age = Mote.Age - Tuning.EnergyTrailSpacingSeconds * static_cast<float>(Dot);
			if (Age < 0.0f)
			{
				continue;
			}
			// Trail dots shrink and fade behind the leading mote.
			const float Share = 1.0f - static_cast<float>(Dot) / static_cast<float>(Tuning.EnergyTrailDots + 1);
			const FVector2D At = ClockHudRules::EnergyPosition(Mote, Age, Tuning);
			FLinearColor Color = Tuning.EnergyColor;
			Color.A *= Share;
			Canvas->K2_DrawPolygon(nullptr, At, FVector2D(Size * Share, Size * Share) * 0.5f, ClockHudConstants::EnergyMoteSides, Color);
		}
	}
}

void AUmbrellaHUD::DrawSpellWheel(const FClockLayout& Layout, const FHudTuning& Tuning, UFont* Font)
{
	const AEllaCharacter* Ella = Cast<AEllaCharacter>(GetOwningPawn());
	const UAttackEmitterComponent* Attack = Ella ? Ella->GetAttack() : nullptr;
	if (!Attack || !Attack->IsWheelOpen() || !Font || !IsFeatureEnabled(EFeatureId::COM_11))
	{
		return;
	}
	const float ViewHeight = static_cast<float>(Layout.View.GetSize().Y);
	const float Scale = ClockHudRules::TextScale(Font->GetMaxCharHeight(), ViewHeight, Tuning);
	const FVector2D Center = Layout.View.GetCenter();
	const float Radius = ViewHeight * Tuning.WheelRadiusFraction;
	// Keys 1..4 sit at up, right, down, left (the right-stick directions).
	for (const FSpellWheelEntry& Entry : Attack->GetWheelEntries())
	{
		const float Degrees = ClockHudConstants::QuarterTurnDegrees * static_cast<float>(static_cast<int32>(Entry.Spell));
		const FVector2D At = ClockHudRules::PointOnFace(Center, Radius, Degrees);
		const FLinearColor Color = Entry.bLocked ? Tuning.WheelLockedColor : (Entry.Spell == Attack->GetWheelPreview() ? Tuning.WheelPreviewColor : Tuning.WheelTextColor);
		const FString Name = SpellPresentationRules::DisplayName(Entry.Spell);
		float Width = 0.0f;
		float Height = 0.0f;
		GetTextSize(Name, Width, Height, Font, Scale);
		DrawText(Name, Color, At.X - Width * 0.5f, At.Y - Height, Font, Scale);
		if (!Entry.LockLabel.IsEmpty())
		{
			float LockWidth = 0.0f;
			float LockHeight = 0.0f;
			GetTextSize(Entry.LockLabel, LockWidth, LockHeight, Font, Scale);
			DrawText(Entry.LockLabel, Color, At.X - LockWidth * 0.5f, At.Y, Font, Scale);
		}
	}
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
