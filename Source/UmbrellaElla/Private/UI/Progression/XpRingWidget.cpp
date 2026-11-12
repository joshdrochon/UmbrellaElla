#include "UI/Progression/XpRingWidget.h"
#include "Core/UmbrellaPlayMode.h"
#include "GameFramework/PlayerController.h"
#include "Harness/UmbrellaFeatureFlags.h"
#include "Progression/ProgressionTuning.h"
#include "Progression/ProgressionSubsystem.h"
#include "Rendering/DrawElements.h"
#include "Widgets/SBoxPanel.h"
#include "Widgets/Layout/SBox.h"

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
		const FProgressionTuning& Tuning = Subsystem->GetTuning();
		Ring->SetDesiredSizeInViewport(FVector2D(Tuning.RingSizePixels, Tuning.RingSizePixels));
		Ring->SetPositionInViewport(Tuning.RingViewportPosition, false);
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

void UXpRingWidget::DrawArc(const FGeometry& Geometry, FSlateWindowElementList& Elements, int32 Layer, float Fraction,
	const FLinearColor& Color, float Thickness) const
{
	const UProgressionSubsystem* Subsystem = Progression.Get();
	if (Subsystem == nullptr || Fraction <= 0.0f)
	{
		return;
	}
	const FProgressionTuning& Tuning = Subsystem->GetTuning();
	const FVector2D Size = Geometry.GetLocalSize();
	const FVector2D Center = Size * 0.5;
	const double Radius = FMath::Max(1.0, FMath::Min(Size.X, Size.Y) * 0.5 - static_cast<double>(Tuning.RingThickness + Tuning.RingPulseExtraThickness));
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
	if (Subsystem == nullptr || !bDirectorsCut)
	{
		return Painted;
	}
	const FProgressionTuning& Tuning = Subsystem->GetTuning();
	const float Pulse = GetPulse();
	const float Extra = bReducedMotion ? 0.0f : Tuning.RingPulseExtraThickness * Pulse;
	const FLinearColor Base = bMaxShown ? Tuning.RingMaxColor : Tuning.RingFillColor;
	const FLinearColor Fillcolor = FMath::Lerp(Base, Tuning.RingLevelUpColor, Pulse);
	DrawArc(AllottedGeometry, OutDrawElements, Painted, 1.0f, Tuning.RingTrackColor, Tuning.RingThickness);
	DrawArc(AllottedGeometry, OutDrawElements, Painted + 1, Fill, Fillcolor, Tuning.RingThickness + Extra);
	return Painted + 2;
}
