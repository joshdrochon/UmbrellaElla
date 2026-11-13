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
 * The menu owns one selection (the first item when it opens) and only that row shows the focus mark. Keys and the pad
 * move it through Slate focus, hovering a row selects it, a click chooses it; Escape, F1, B or Menu call OnBack.
 * A control hint (Confirm, then Back when there is one) sits at the bottom right in the wording of the last device used.
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
	virtual FReply OnPreviewKeyDown(const FGeometry& MyGeometry, const FKeyEvent& InKeyEvent) override;
	virtual FReply OnFocusReceived(const FGeometry& MyGeometry, const FFocusEvent& InFocusEvent) override;
	virtual void OnFocusChanging(const FWeakWidgetPath& PreviousFocusPath, const FWidgetPath& NewWidgetPath, const FFocusEvent& InFocusEvent) override;
	virtual FReply OnMouseButtonDown(const FGeometry& MyGeometry, const FPointerEvent& MouseEvent) override;
	virtual FReply OnMouseMove(const FGeometry& MyGeometry, const FPointerEvent& MouseEvent) override;

	/** Put keyboard and gamepad focus on the selected button (the first one when the menu opens). */
	void FocusFirstItem();

	/** The row that shows the focus mark and that Confirm chooses; INDEX_NONE only for a menu without items. */
	int32 GetSelectedIndex() const { return SelectedIndex; }
	int32 GetItemCount() const { return Buttons.Num(); }
	TSharedPtr<class SUmbrellaButton> GetItemButton(int32 Index) const;
	/** The row lettered Label, or INDEX_NONE. */
	int32 FindItem(const FText& Label) const;

	/** Select a row and give it keyboard and pad focus (a hover does this). */
	void SelectItem(int32 Index);

	/** Run the selected row's action, as Confirm or a click does. False when there is nothing to choose. */
	bool ChooseSelected();

	/** True while the hint shows the pad wording (the last key came from a pad). */
	bool IsShowingGamepadPrompts() const { return bGamepadPrompts; }

	/** The menu most recently built that is still on screen (the dev capture driver clicks through it). */
	static TSharedPtr<SFlowMenu> GetLastOpened();

private:
	void HandleHovered(int32 Index);
	void MoveSelection(int32 Step);
	EActiveTimerReturnType KeepFocus(double InCurrentTime, float InDeltaTime);
	FText GetConfirmPrompt() const;
	FText GetBackPrompt() const;

	FSimpleDelegate BackDelegate;
	TArray<FSimpleDelegate> Choices;
	TArray<FText> Labels;
	bool bWasdNavigation = true;
	bool bGamepadPrompts = false;
	int32 SelectedIndex = INDEX_NONE;
	TArray<TSharedPtr<class SUmbrellaButton>> Buttons;
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
