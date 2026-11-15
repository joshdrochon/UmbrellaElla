#pragma once

#include "CoreMinimal.h"
#include "Blueprint/UserWidget.h"
#include "XpRingWidget.generated.h"

class APlayerController;
class UProgressionSubsystem;
struct FHudTuning;
struct FProgressionTuning;

/** Where the ring is drawn, in canvas pixels: the HUD clock's centre and a radius just outside its gold rim. */
struct FXpRingCircle
{
	FVector2D Center = FVector2D::ZeroVector;
	/** Radius of the ring's centre line. */
	float Radius = 0.0f;
	/** The clock's outer rim edge the ring wraps. */
	float ClockEdge = 0.0f;
};

/** The ring's colours, all from the shared UI gold tokens. */
struct FXpRingColors
{
	FLinearColor Track = FLinearColor::Transparent;
	FLinearColor Fill = FLinearColor::Transparent;
	FLinearColor Halo = FLinearColor::Transparent;
};

/**
 * Director's Cut XP ring: a thin glowing ring drawn around the existing clock, never a third hand. Fills with earned XP
 * toward the next level, pulses on a level gain (no motion in reduced-motion mode, a colour change instead) and shows a
 * full gold ring at the cap. Hidden in Start Game. The audible level-up cue rides the LevelGained bus event the
 * subsystem broadcasts, so the sound and the pulse come from the same moment.
 */
UCLASS()
class UMBRELLAELLA_API UXpRingWidget final : public UUserWidget
{
	GENERATED_BODY()

public:
	/** Ring placement on a canvas of this pixel size: the same layout rule the HUD clock is drawn with. */
	static FXpRingCircle ComputeCircle(const FVector2D& CanvasPixels, const FHudTuning& Hud, const FProgressionTuning& Tuning);

	/** Ring colours: brass track, bright gold fill (full gold at the cap), cream at the level-up flash (Pulse 0..1). */
	static FXpRingColors ComputeColors(bool bMax, float Pulse, const FProgressionTuning& Tuning);

	/** Creates the ring over the whole viewport (it finds the clock itself); null in Start Game. */
	static UXpRingWidget* Show(APlayerController* Owner);

	void SetReducedMotion(bool bReduced);

	/** 0..1 fill toward the next level; 1 at the cap. */
	float GetDisplayedFill() const;
	bool IsMaxShown() const;
	bool IsRingVisible() const;
	/** 0..1, 1 at the instant of a level gain, falling to 0. */
	float GetPulse() const;

	/** The circle the last paint drew, in window pixels (zero radius before the first paint or when hidden). */
	FXpRingCircle GetLastDrawnCircle() const { return LastDrawn; }

	/** Test seam: the same call the subsystem's level-gained delegate makes. */
	void NotifyLevelGained(int32 NewLevel);

protected:
	virtual void NativeConstruct() override;
	virtual void NativeDestruct() override;
	virtual void NativeTick(const FGeometry& MyGeometry, float InDeltaTime) override;
	virtual int32 NativePaint(const FPaintArgs& Args, const FGeometry& AllottedGeometry, const FSlateRect& MyCullingRect,
		FSlateWindowElementList& OutDrawElements, int32 LayerId, const FWidgetStyle& InWidgetStyle, bool bParentEnabled) const override;

private:
	void Refresh();
	void DrawArc(const FGeometry& Geometry, FSlateWindowElementList& Elements, int32 Layer, const FVector2D& Center, double Radius, float Fraction, const FLinearColor& Color, float Thickness) const;

	TWeakObjectPtr<UProgressionSubsystem> Progression;
	FDelegateHandle ChangedHandle;
	FDelegateHandle LevelHandle;
	float Fill = 0.0f;
	float PulseRemaining = 0.0f;
	bool bMaxShown = false;
	bool bDirectorsCut = false;
	bool bReducedMotion = false;
	mutable FXpRingCircle LastDrawn;
	/** Paint layers used: track, fill halo, fill. */
	static constexpr int32 PaintLayerCount = 3;
};
