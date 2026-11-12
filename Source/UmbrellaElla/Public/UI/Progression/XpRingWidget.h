#pragma once

#include "CoreMinimal.h"
#include "Blueprint/UserWidget.h"
#include "XpRingWidget.generated.h"

class APlayerController;
class UProgressionSubsystem;

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
	/** Creates the ring and adds it to the player's viewport at the clock's corner; null in Start Game. */
	static UXpRingWidget* Show(APlayerController* Owner);

	void SetReducedMotion(bool bReduced);

	/** 0..1 fill toward the next level; 1 at the cap. */
	float GetDisplayedFill() const;
	bool IsMaxShown() const;
	bool IsRingVisible() const;
	/** 0..1, 1 at the instant of a level gain, falling to 0. */
	float GetPulse() const;

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
	void DrawArc(const FGeometry& Geometry, FSlateWindowElementList& Elements, int32 Layer, float Fraction, const FLinearColor& Color, float Thickness) const;

	TWeakObjectPtr<UProgressionSubsystem> Progression;
	FDelegateHandle ChangedHandle;
	FDelegateHandle LevelHandle;
	float Fill = 0.0f;
	float PulseRemaining = 0.0f;
	bool bMaxShown = false;
	bool bDirectorsCut = false;
	bool bReducedMotion = false;
};
