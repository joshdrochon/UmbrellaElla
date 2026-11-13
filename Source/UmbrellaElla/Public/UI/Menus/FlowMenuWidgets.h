#pragma once

#include "CoreMinimal.h"
#include "Widgets/SCompoundWidget.h"
#include "Widgets/SLeafWidget.h"
#include "Flow/FlowTuning.h"

/** Which shapes the moving background draws. */
enum class EFlowBackdrop : uint8
{
	/** Start screen, ending and credits: slow drifting shapes, nobody on screen. */
	Drift,
	/** Pause: the same plus ticking clocks. Presentation only, it never reads or advances the simulation. */
	Clocks
};

/** The slowly moving character-free background (Start screen, pause, ending, credits). Time comes from Slate, not the game. */
class UMBRELLAELLA_API SFlowBackground : public SLeafWidget
{
public:
	SLATE_BEGIN_ARGS(SFlowBackground)
	{
	}
	SLATE_ARGUMENT_DEFAULT(EFlowBackdrop, Backdrop) = EFlowBackdrop::Drift;
	SLATE_ARGUMENT(FFlowTuning, Tuning)
	SLATE_END_ARGS()

	void Construct(const FArguments& InArgs);

	virtual int32 OnPaint(const FPaintArgs& Args, const FGeometry& AllottedGeometry, const FSlateRect& MyCullingRect,
		FSlateWindowElementList& OutDrawElements, int32 LayerId, const FWidgetStyle& InWidgetStyle, bool bParentEnabled) const override;
	virtual FVector2D ComputeDesiredSize(float LayoutScaleMultiplier) const override;

private:
	EFlowBackdrop Backdrop = EFlowBackdrop::Drift;
	FFlowTuning Tuning;
};

/** One menu button: label and what it does. */
struct UMBRELLAELLA_API FFlowMenuItem
{
	FText Label;
	FSimpleDelegate OnChosen;
};

/**
 * A full-screen menu in the shared UI style (UI/Style): the painted ground, a lettered heading with its rule, optional
 * body text and a column of lettered buttons, set in the dark left third as on the title-screen reference.
 * Gamepad and keyboard navigation use Slate focus; Escape, F1, B or Menu call OnBack.
 */
class UMBRELLAELLA_API SFlowMenu : public SCompoundWidget
{
public:
	SLATE_BEGIN_ARGS(SFlowMenu)
	{
	}
	SLATE_ARGUMENT_DEFAULT(EFlowBackdrop, Backdrop) = EFlowBackdrop::Drift;
	SLATE_ARGUMENT(FFlowTuning, Tuning)
	SLATE_ARGUMENT(FText, Heading)
	/** Heading colour; unset = the style's cream. The Defeated screen uses the rust accent. */
	SLATE_ARGUMENT(TOptional<FLinearColor>, HeadingColor)
	SLATE_ARGUMENT(FText, Body)
	SLATE_ARGUMENT(TArray<FFlowMenuItem>, Items)
	SLATE_EVENT(FSimpleDelegate, OnBack)
	SLATE_ARGUMENT_DEFAULT(bool, WasdNavigation) = true;
	SLATE_END_ARGS()

	void Construct(const FArguments& InArgs);

	virtual bool SupportsKeyboardFocus() const override;
	virtual FReply OnKeyDown(const FGeometry& MyGeometry, const FKeyEvent& InKeyEvent) override;
	virtual FReply OnFocusReceived(const FGeometry& MyGeometry, const FFocusEvent& InFocusEvent) override;

	/** Put keyboard and gamepad focus on the first button. */
	void FocusFirstItem();

private:
	FSimpleDelegate BackDelegate;
	bool bWasdNavigation = true;
	TSharedPtr<SWidget> FirstButton;
};

/** Moving text over the ground, set in the same left column as the menus: ending story pages and the credits. */
class UMBRELLAELLA_API SFlowTextScreen : public SCompoundWidget
{
public:
	SLATE_BEGIN_ARGS(SFlowTextScreen)
	{
	}
	SLATE_ARGUMENT(FFlowTuning, Tuning)
	SLATE_END_ARGS()

	void Construct(const FArguments& InArgs);

	/** Replace the text; ScrollOffset slides it up from below (0 = centered). */
	void SetText(const FText& NewText, float ScrollOffset);

private:
	TOptional<FSlateRenderTransform> GetScrollTransform() const;

	TSharedPtr<class STextBlock> TextBlock;
	float Scroll = 0.0f;
};
