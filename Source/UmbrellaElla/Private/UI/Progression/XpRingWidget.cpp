#include "UI/Progression/XpRingWidget.h"
#include "Core/UmbrellaPlayMode.h"
#include "Core/UmbrellaTuning.h"
#include "GameFramework/PlayerController.h"
#include "Harness/UmbrellaFeatureFlags.h"
#include "Progression/ProgressionTuning.h"
#include "Progression/ProgressionSubsystem.h"
#include "Rendering/DrawElements.h"
#include "UI/ClockHudModel.h"
#include "UI/Style/UmbrellaUIStyle.h"
#include "Widgets/SBoxPanel.h"
#include "Widgets/Layout/SBox.h"

FXpRingCircle UXpRingWidget::ComputeCircle(const FVector2D& CanvasPixels, const FHudTuning& Hud, const FProgressionTuning& Tuning)
{
	const FClockLayout Layout = ClockHudRules::ComputeLayout(CanvasPixels, Hud);
	FXpRingCircle Circle;
	Circle.Center = Layout.Center;
	// The clock's outer edge: the dial art's edge (its gold rim sits at ClockFaceRimShare of the art's half size), or the
	// drawn bronze rim's outer edge when the art is missing; whichever is further out.
	Circle.ClockEdge = FMath::Max(Layout.Radius / UmbrellaUIStyleConstants::ClockFaceRimShare, Layout.Radius + Hud.RimThickness * 0.5f);
	Circle.Radius = Circle.ClockEdge + Tuning.RingGapPixels + Tuning.RingThickness * 0.5f;
	return Circle;
}

FXpRingColors UXpRingWidget::ComputeColors(bool bMax, float Pulse, const FProgressionTuning& Tuning)
{
	const FLinearColor Gold = FUmbrellaUIStyle::Gold();
	const FLinearColor Bright = FUmbrellaUIStyle::GoldBright();
	FXpRingColors Colors;
	Colors.Track = FLinearColor(Gold.R * Tuning.RingTrackShade, Gold.G * Tuning.RingTrackShade, Gold.B * Tuning.RingTrackShade, Tuning.RingTrackAlpha);
	const FLinearColor Base = bMax ? Bright : FMath::Lerp(Gold, Bright, Tuning.RingFillAlpha);
	const FLinearColor Lit = FMath::Lerp(Base, FUmbrellaUIStyle::Cream(), FMath::Clamp(Pulse, 0.0f, 1.0f));
	Colors.Fill = Lit.CopyWithNewOpacity(bMax ? 1.0f : Tuning.RingFillAlpha);
	Colors.Halo = Lit.CopyWithNewOpacity(Tuning.RingHaloAlpha);
	return Colors;
}

UXpRingWidget* UXpRingWidget::Show(APlayerController* Owner)
{
	if (Owner == nullptr || !IsFeatureEnabled(EFeatureId::FLOW_48))
	{
		return nullptr;
	}
	const UProgressionSubsystem* Subsystem = UProgressionSubsystem::Get(Owner);
	if (Subsystem == nullptr || Subsystem->GetPlayMode() != EUmbrellaPlayMode::DirectorsCut)
	{
		return nullptr;
	}
	UXpRingWidget* Ring = CreateWidget<UXpRingWidget>(Owner);
	if (Ring != nullptr)
	{
		// Stretched over the whole viewport with no offset: the ring paints itself on the clock's centre, from the same
		// layout rule the HUD canvas uses, so it cannot drift from the clock at any window size or DPI scale.
		// (No position or desired size: either one turns the stretch offsets into a small box at the corner.)
		Ring->SetAnchorsInViewport(FAnchors(0.0f, 0.0f, 1.0f, 1.0f));
		Ring->SetVisibility(ESlateVisibility::HitTestInvisible);
		Ring->AddToViewport();
	}
	return Ring;
}

void UXpRingWidget::NativeConstruct()
{
	Super::NativeConstruct();
	Progression = UProgressionSubsystem::Get(GetOwningPlayer());
	if (UProgressionSubsystem* Subsystem = Progression.Get())
	{
		ChangedHandle = Subsystem->OnChanged().AddUObject(this, &UXpRingWidget::Refresh);
		LevelHandle = Subsystem->OnLevelGained().AddUObject(this, &UXpRingWidget::NotifyLevelGained);
	}
	Refresh();
}

void UXpRingWidget::NativeDestruct()
{
	if (UProgressionSubsystem* Subsystem = Progression.Get())
	{
		Subsystem->OnChanged().Remove(ChangedHandle);
		Subsystem->OnLevelGained().Remove(LevelHandle);
	}
	Super::NativeDestruct();
}

void UXpRingWidget::SetReducedMotion(bool bReduced)
{
	bReducedMotion = bReduced;
}

void UXpRingWidget::Refresh()
{
	const UProgressionSubsystem* Subsystem = Progression.Get();
	bDirectorsCut = Subsystem != nullptr && Subsystem->GetPlayMode() == EUmbrellaPlayMode::DirectorsCut;
	if (!bDirectorsCut)
	{
		Fill = 0.0f;
		bMaxShown = false;
		return;
	}
	const FLevelProgress Level = Subsystem->GetLevelProgress();
	Fill = FProgressionRules::RingFill(Level);
	bMaxShown = Level.bMax;
}

void UXpRingWidget::NotifyLevelGained(int32 NewLevel)
{
	const UProgressionSubsystem* Subsystem = Progression.Get();
	PulseRemaining = Subsystem != nullptr ? Subsystem->GetTuning().LevelUpPulseSeconds : 0.0f;
	Refresh();
}

void UXpRingWidget::NativeTick(const FGeometry& MyGeometry, float InDeltaTime)
{
	Super::NativeTick(MyGeometry, InDeltaTime);
	PulseRemaining = FMath::Max(0.0f, PulseRemaining - InDeltaTime);
}

float UXpRingWidget::GetDisplayedFill() const
{
	return Fill;
}

bool UXpRingWidget::IsMaxShown() const
{
	return bMaxShown;
}

bool UXpRingWidget::IsRingVisible() const
{
	return bDirectorsCut;
}

float UXpRingWidget::GetPulse() const
{
	const UProgressionSubsystem* Subsystem = Progression.Get();
	const float Length = Subsystem != nullptr ? Subsystem->GetTuning().LevelUpPulseSeconds : 0.0f;
	return Length > 0.0f ? FMath::Clamp(PulseRemaining / Length, 0.0f, 1.0f) : 0.0f;
}

void UXpRingWidget::DrawArc(const FGeometry& Geometry, FSlateWindowElementList& Elements, int32 Layer, const FVector2D& Center,
	double Radius, float Fraction, const FLinearColor& Color, float Thickness) const
{
	const UProgressionSubsystem* Subsystem = Progression.Get();
	if (Subsystem == nullptr || Fraction <= 0.0f || Radius <= 0.0)
	{
		return;
	}
	const FProgressionTuning& Tuning = Subsystem->GetTuning();
	const int32 Steps = FMath::Max(2, FMath::CeilToInt(static_cast<float>(Tuning.RingSegments) * Fraction));
	TArray<FVector2D> Points;
	Points.Reserve(Steps + 1);
	for (int32 Step = 0; Step <= Steps; ++Step)
	{
		// Start at twelve o'clock and run clockwise.
		const double Angle = -UE_DOUBLE_HALF_PI + UE_DOUBLE_TWO_PI * static_cast<double>(Fraction) * static_cast<double>(Step) / static_cast<double>(Steps);
		Points.Add(Center + FVector2D(FMath::Cos(Angle), FMath::Sin(Angle)) * Radius);
	}
	FSlateDrawElement::MakeLines(Elements, Layer, Geometry.ToPaintGeometry(), Points, ESlateDrawEffect::None, Color, true, Thickness);
}

int32 UXpRingWidget::NativePaint(const FPaintArgs& Args, const FGeometry& AllottedGeometry, const FSlateRect& MyCullingRect,
	FSlateWindowElementList& OutDrawElements, int32 LayerId, const FWidgetStyle& InWidgetStyle, bool bParentEnabled) const
{
	const int32 Painted = Super::NativePaint(Args, AllottedGeometry, MyCullingRect, OutDrawElements, LayerId, InWidgetStyle, bParentEnabled);
	const UProgressionSubsystem* Subsystem = Progression.Get();
	LastDrawn = FXpRingCircle();
	if (Subsystem == nullptr || !bDirectorsCut)
	{
		return Painted;
	}
	const FProgressionTuning& Tuning = Subsystem->GetTuning();
	// The widget spans the viewport; the HUD clock is laid out in canvas pixels, so convert pixels to local units.
	const float PixelScale = AllottedGeometry.Scale > 0.0f ? AllottedGeometry.Scale : 1.0f;
	const FXpRingCircle Circle = ComputeCircle(AllottedGeometry.GetLocalSize() * PixelScale, GetDefault<UUmbrellaTuning>()->Hud, Tuning);
	const FVector2D Center = Circle.Center / PixelScale;
	const double Radius = Circle.Radius / PixelScale;
	LastDrawn.Center = AllottedGeometry.LocalToAbsolute(Center);
	LastDrawn.Radius = Circle.Radius;
	LastDrawn.ClockEdge = Circle.ClockEdge;
	const float Pulse = GetPulse();
	const float Extra = bReducedMotion ? 0.0f : Tuning.RingPulseExtraThickness * Pulse;
	const FXpRingColors Colors = ComputeColors(bMaxShown, Pulse, Tuning);
	const float Thickness = (Tuning.RingThickness + Extra) / PixelScale;
	DrawArc(AllottedGeometry, OutDrawElements, Painted, Center, Radius, 1.0f, Colors.Track, Tuning.RingThickness / PixelScale);
	// Soft edge: a wide faint halo under the thin bright line.
	DrawArc(AllottedGeometry, OutDrawElements, Painted + 1, Center, Radius, Fill, Colors.Halo, Thickness * Tuning.RingHaloWidthScale);
	DrawArc(AllottedGeometry, OutDrawElements, Painted + 2, Center, Radius, Fill, Colors.Fill, Thickness);
	return Painted + PaintLayerCount;
}
