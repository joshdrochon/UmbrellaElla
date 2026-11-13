#include "UI/Menus/FlowMenuWidgets.h"
#include "Flow/FlowMenuText.h"
#include "Flow/FlowRules.h"
#include "Brushes/SlateRoundedBoxBrush.h"
#include "Framework/Application/SlateApplication.h"
#include "Layout/WidgetPath.h"
#include "Rendering/DrawElements.h"
#include "Styling/CoreStyle.h"
#include "UI/Style/UmbrellaUIStyle.h"
#include "Widgets/Images/SImage.h"
#include "Widgets/Layout/SBox.h"
#include "Widgets/SBoxPanel.h"
#include "Widgets/SOverlay.h"
#include "Widgets/Text/STextBlock.h"

namespace
{
	/** Fraction part in [0, 1). */
	float FlowFrac(float Value)
	{
		return Value - FMath::FloorToFloat(Value);
	}

	/** The control hint: small, dim, set in from the bottom-right corner, Confirm then Back with a gap between. */
	constexpr int32 PromptTextSize = UmbrellaUI::MinTextSize + 2;
	constexpr float PromptInsetX = UmbrellaUI::PromptInsetX;
	constexpr float PromptInsetY = UmbrellaUI::PromptInsetY;
	constexpr float PromptGap = UmbrellaUI::PromptGap;

	TWeakPtr<SFlowMenu> LastOpenedMenu;
}

void SFlowBackground::Construct(const FArguments& InArgs)
{
	Backdrop = InArgs._Backdrop;
	Tuning = InArgs._Tuning;
}

FVector2D SFlowBackground::ComputeDesiredSize(float LayoutScaleMultiplier) const
{
	return FVector2D(1.0, 1.0);
}

int32 SFlowBackground::OnPaint(const FPaintArgs& Args, const FGeometry& AllottedGeometry, const FSlateRect& MyCullingRect,
	FSlateWindowElementList& OutDrawElements, int32 LayerId, const FWidgetStyle& InWidgetStyle, bool bParentEnabled) const
{
	const FVector2f Size = AllottedGeometry.GetLocalSize();
	const float Time = static_cast<float>(Args.GetCurrentTime());
	const FSlateBrush* White = FCoreStyle::Get().GetBrush(TEXT("WhiteBrush"));
	const FSlateRoundedBoxBrush Round(FLinearColor::White, Size.Y);
	const FLinearColor Gold = FUmbrellaUIStyle::Gold();

	// The painted ground of the shared style.
	int32 Layer = FUmbrellaUIStyle::PaintGround(AllottedGeometry, OutDrawElements, LayerId);

	++Layer;
	// Embers falling through the scene: index decides column, size and speed, so nothing needs a random stream.
	for (int32 Index = 0; Index < Tuning.FallingShapeCount; ++Index)
	{
		const float Spread = FlowFrac(static_cast<float>(Index + 1) * Tuning.BackgroundSpreadStep);
		const float ShapeSize = FMath::Lerp(Tuning.FallingShapeMinSize, Tuning.FallingShapeMaxSize, Spread) * UmbrellaUI::EmberSizeShare;
		const float Speed = FMath::Lerp(Tuning.FallingShapeMinSpeed, Tuning.FallingShapeMaxSpeed, FlowFrac(Spread * Tuning.FallingShapeCount));
		const float Travel = Size.Y + ShapeSize * 2.0f;
		const float Y = FlowFrac((Time * Speed + Spread * Travel) / Travel) * Travel - ShapeSize;
		const float X = Spread * Size.X + FMath::Sin(Time * Tuning.BackgroundSwaySpeed + Index) * Tuning.BackgroundSwayAmplitude;
		FSlateDrawElement::MakeBox(OutDrawElements, Layer,
			AllottedGeometry.ToPaintGeometry(FVector2f(ShapeSize, ShapeSize), FSlateLayoutTransform(FVector2f(X, Y))), &Round,
			ESlateDrawEffect::None, Gold.CopyWithNewOpacity(UmbrellaUI::EmberAlpha * (1.0f - Spread * UmbrellaUI::ClockLineShare)));
	}

	if (Backdrop == EFlowBackdrop::Clocks)
	{
		++Layer;
		const FLinearColor Line = Gold.CopyWithNewOpacity(UmbrellaUI::ClockLineAlpha);
		const float LineWidth = Tuning.ClockHandThickness * UmbrellaUI::ClockLineShare;
		for (int32 Index = 0; Index < Tuning.PauseClockCount; ++Index)
		{
			const float Spread = FlowFrac(static_cast<float>(Index + 1) * Tuning.BackgroundSpreadStep);
			const float Drift = FMath::Sin(Time * Tuning.BackgroundSwaySpeed + Index) * Tuning.BackgroundSwayAmplitude;
			const FVector2f Center(Spread * Size.X + Drift, FlowFrac(Spread * Tuning.PauseClockCount + Index * Tuning.BackgroundSpreadStep) * Size.Y);
			TArray<FVector2f> Ring;
			for (int32 Segment = 0; Segment <= UmbrellaUI::ClockRingSegments; ++Segment)
			{
				const float RingAngle = UE_TWO_PI * static_cast<float>(Segment) / static_cast<float>(UmbrellaUI::ClockRingSegments);
				Ring.Add(Center + FVector2f(FMath::Sin(RingAngle), -FMath::Cos(RingAngle)) * Tuning.PauseClockRadius);
			}
			FSlateDrawElement::MakeLines(OutDrawElements, Layer, AllottedGeometry.ToPaintGeometry(), MoveTemp(Ring), ESlateDrawEffect::None, Line, true, LineWidth);

			// Etched hour ticks.
			for (int32 Tick = 0; Tick < UmbrellaUI::ClockTickCount; ++Tick)
			{
				const float TickAngle = UE_TWO_PI * static_cast<float>(Tick) / static_cast<float>(UmbrellaUI::ClockTickCount);
				const FVector2f Dir(FMath::Sin(TickAngle), -FMath::Cos(TickAngle));
				TArray<FVector2f> Points;
				Points.Add(Center + Dir * Tuning.PauseClockRadius * UmbrellaUI::ClockTickInner);
				Points.Add(Center + Dir * Tuning.PauseClockRadius);
				FSlateDrawElement::MakeLines(OutDrawElements, Layer, AllottedGeometry.ToPaintGeometry(), MoveTemp(Points), ESlateDrawEffect::None, Line, true, LineWidth);
			}

			// A ticking minute hand: one step per second.
			const float Step = FMath::FloorToFloat(Time) / Tuning.ClockTurnSeconds;
			const float Angle = (Step + Spread) * UE_TWO_PI;
			const float Length = Tuning.PauseClockRadius * Tuning.ClockHandLengthShare;
			const FVector2f HandSize(Tuning.ClockHandThickness, Length);
			const FVector2f HandPos = Center - FVector2f(Tuning.ClockHandThickness * 0.5f, Length);
			FSlateDrawElement::MakeRotatedBox(OutDrawElements, Layer + 1,
				AllottedGeometry.ToPaintGeometry(HandSize, FSlateLayoutTransform(HandPos)), White, ESlateDrawEffect::None, Angle,
				FVector2D(HandSize.X * 0.5, HandSize.Y), FSlateDrawElement::RelativeToElement, Line);
		}
	}
	return Layer + 2;
}

void SFlowMenu::Construct(const FArguments& InArgs)
{
	const FFlowTuning& Tuning = InArgs._Tuning;
	BackDelegate = InArgs._OnBack;
	bWasdNavigation = InArgs._WasdNavigation;

	// Labels, heading and body share one left edge; the focus ornament hangs to the left of it.
	const float TextInset = UmbrellaUI::ButtonPadX + UmbrellaUI::OrnamentWidth + UmbrellaUI::OrnamentGap;
	TSharedRef<SVerticalBox> Column = SNew(SVerticalBox);
	if (!InArgs._Heading.IsEmpty())
	{
		// A heading of two lines is the title lockup: the name lettered large, the subtitle small and widely spaced under it.
		FString Name;
		FString Subtitle;
		const FString Heading = InArgs._Heading.ToString();
		if (Heading.Split(TEXT("\n"), &Name, &Subtitle) && FUmbrellaUIStyle::TitleLockupBrush())
		{
			// The painted lockup (lettering, clock ring and hand in one image) replaces the typeset title.
			Column->AddSlot().AutoHeight().HAlign(HAlign_Left).Padding(TextInset - UmbrellaUI::OrnamentWidth, 0.0f, 0.0f, 0.0f)
			[
				SNew(SImage).Image(FUmbrellaUIStyle::TitleLockupBrush())
			];
		}
		else if (Heading.Split(TEXT("\n"), &Name, &Subtitle))
		{
			Column->AddSlot().AutoHeight().HAlign(HAlign_Left).Padding(TextInset, 0.0f, 0.0f, 0.0f)
			[
				SNew(STextBlock).Text(FText::FromString(Name)).Font(FUmbrellaUIStyle::DisplayFont(UmbrellaUI::LockupNameSize))
					.ColorAndOpacity(FUmbrellaUIStyle::Cream())
					.ShadowOffset(FVector2D(UmbrellaUI::ShadowOffset, UmbrellaUI::ShadowOffset)).ShadowColorAndOpacity(FUmbrellaUIStyle::Shadow())
			];
			Column->AddSlot().AutoHeight().HAlign(HAlign_Left).Padding(TextInset + UmbrellaUI::LockupSubtitleInset, 0.0f, 0.0f, 0.0f)
			[
				SNew(STextBlock).Text(FText::FromString(Subtitle.Replace(TEXT("\n"), TEXT(" "))))
					.Font(FUmbrellaUIStyle::DisplayFontSpaced(UmbrellaUI::LockupSubtitleSize, UmbrellaUI::LockupSubtitleSpacing))
					.ColorAndOpacity(FUmbrellaUIStyle::Gold())
					.ShadowOffset(FVector2D(UmbrellaUI::ShadowOffset, UmbrellaUI::ShadowOffset)).ShadowColorAndOpacity(FUmbrellaUIStyle::Shadow())
			];
		}
		else if (FUmbrellaUIStyle::HeadingBrush(Heading))
		{
			Column->AddSlot().AutoHeight().HAlign(HAlign_Left).Padding(TextInset - UmbrellaUI::OrnamentWidth, 0.0f, 0.0f, 0.0f)
			[
				SNew(SImage).Image(FUmbrellaUIStyle::HeadingBrush(Heading))
			];
		}
		else
		{
			const int32 HeadingSize = Heading.Len() > UmbrellaUI::LongHeadingLength ? FMath::Min(Tuning.TitleFontSize, UmbrellaUI::LongHeadingSize) : Tuning.TitleFontSize;
			Column->AddSlot().AutoHeight().HAlign(HAlign_Fill).Padding(TextInset, 0.0f, 0.0f, 0.0f)
			[
				SNew(STextBlock).Text(InArgs._Heading).Font(FUmbrellaUIStyle::DisplayFont(HeadingSize))
					.ColorAndOpacity(InArgs._HeadingColor.Get(FUmbrellaUIStyle::Cream())).AutoWrapText(true)
					.ShadowOffset(FVector2D(UmbrellaUI::ShadowOffset, UmbrellaUI::ShadowOffset)).ShadowColorAndOpacity(FUmbrellaUIStyle::Shadow())
			];
		}
		Column->AddSlot().AutoHeight().HAlign(HAlign_Fill).Padding(TextInset, UmbrellaUI::HeadingGap, UmbrellaUI::HeadingWidth - UmbrellaUI::ColumnWidth, UmbrellaUI::SectionGap)
		[
			SNew(SUmbrellaRule)
		];
	}
	if (!InArgs._Body.IsEmpty())
	{
		Column->AddSlot().AutoHeight().HAlign(HAlign_Fill).Padding(TextInset, 0.0f, UmbrellaUI::HeadingWidth - UmbrellaUI::ColumnWidth, UmbrellaUI::SectionGap)
		[
			SNew(STextBlock).Text(InArgs._Body).Font(FUmbrellaUIStyle::BodyFont(Tuning.BodyFontSize)).ColorAndOpacity(FUmbrellaUIStyle::Cream())
				.ShadowOffset(FVector2D(UmbrellaUI::ShadowOffset, UmbrellaUI::ShadowOffset)).ShadowColorAndOpacity(FUmbrellaUIStyle::Shadow())
				.AutoWrapText(true).Justification(ETextJustify::Left)
		];
	}
	for (const FFlowMenuItem& Item : InArgs._Items)
	{
		const int32 Index = Buttons.Num();
		TSharedRef<SUmbrellaButton> Button = SNew(SUmbrellaButton)
			.Text(Item.Label)
			.FontSize(Tuning.MenuFontSize)
			.Ornament(true)
			.LitOnlyWhenSelected(true)
			.Selected_Lambda([this, Index]() { return SelectedIndex == Index; })
			.OnClicked_Lambda([this, Index]()
			{
				SelectedIndex = Index;
				ConfirmSelection();
				return FReply::Handled();
			});
		Button->SetOnHovered(FSimpleDelegate::CreateSP(this, &SFlowMenu::HandleHovered, Index));
		Buttons.Add(Button);
		Choices.Add(Item.OnChosen);
		Labels.Add(Item.Label);
		Column->AddSlot().AutoHeight().HAlign(HAlign_Left).Padding(0.0f, UmbrellaUI::ItemGap)
		[
			Button
		];
	}
	// Start Game (or whatever comes first) is the choice the moment the screen opens, with or without focus.
	SelectedIndex = Buttons.Num() > 0 ? 0 : INDEX_NONE;
	LastOpenedMenu = SharedThis(this);
	// A click can hand focus to the game viewport; take it back so the keys and the pad keep working.
	RegisterActiveTimer(0.0f, FWidgetActiveTimerDelegate::CreateSP(this, &SFlowMenu::KeepFocus));

	ChildSlot
	[
		SNew(SOverlay)
		+ SOverlay::Slot()
		[
			SNew(SFlowBackground).Backdrop(InArgs._Backdrop).Tuning(Tuning)
		]
		+ SOverlay::Slot().HAlign(HAlign_Left).VAlign(VAlign_Center).Padding(UmbrellaUI::ColumnLeft - TextInset, 0.0f, 0.0f, UmbrellaUI::ColumnBottomLift)
		[
			SNew(SBox).WidthOverride(UmbrellaUI::HeadingWidth + TextInset)
			[
				Column
			]
		]
		+ SOverlay::Slot().HAlign(HAlign_Right).VAlign(VAlign_Bottom).Padding(0.0f, 0.0f, PromptInsetX, PromptInsetY)
		[
			SNew(SHorizontalBox).Visibility(EVisibility::HitTestInvisible)
			+ SHorizontalBox::Slot().AutoWidth()
			[
				SNew(STextBlock).Text(this, &SFlowMenu::GetConfirmPrompt).Font(FUmbrellaUIStyle::BodyFont(PromptTextSize))
					.ColorAndOpacity(FUmbrellaUIStyle::Dim())
					.ShadowOffset(FVector2D(UmbrellaUI::ShadowOffset, UmbrellaUI::ShadowOffset)).ShadowColorAndOpacity(FUmbrellaUIStyle::Shadow())
			]
			+ SHorizontalBox::Slot().AutoWidth().Padding(PromptGap, 0.0f, 0.0f, 0.0f)
			[
				SNew(STextBlock).Text(this, &SFlowMenu::GetBackPrompt).Font(FUmbrellaUIStyle::BodyFont(PromptTextSize))
					.ColorAndOpacity(FUmbrellaUIStyle::Dim())
					.ShadowOffset(FVector2D(UmbrellaUI::ShadowOffset, UmbrellaUI::ShadowOffset)).ShadowColorAndOpacity(FUmbrellaUIStyle::Shadow())
					.Visibility(BackDelegate.IsBound() ? EVisibility::HitTestInvisible : EVisibility::Collapsed)
			]
		]
	];
}

TSharedPtr<SFlowMenu> SFlowMenu::GetLastOpened()
{
	return LastOpenedMenu.Pin();
}

TSharedPtr<SUmbrellaButton> SFlowMenu::GetItemButton(int32 Index) const
{
	return Buttons.IsValidIndex(Index) ? Buttons[Index] : nullptr;
}

int32 SFlowMenu::FindItem(const FText& Label) const
{
	return Labels.IndexOfByPredicate([&Label](const FText& Each) { return Each.EqualTo(Label); });
}

void SFlowMenu::SelectItem(int32 Index)
{
	if (!Buttons.IsValidIndex(Index))
	{
		return;
	}
	SelectedIndex = Index;
	if (FSlateApplication::IsInitialized() && !Buttons[Index]->HasAnyUserFocus().IsSet())
	{
		FSlateApplication::Get().SetAllUserFocus(Buttons[Index], EFocusCause::Mouse);
	}
}

bool SFlowMenu::CanConfirmSelection() const
{
	return Choices.IsValidIndex(SelectedIndex) && Choices[SelectedIndex].IsBound();
}

void SFlowMenu::ConfirmSelection()
{
	if (!CanConfirmSelection())
	{
		return;
	}
	// Copy first: the action usually closes this menu, which destroys the array.
	const FSimpleDelegate Chosen = Choices[SelectedIndex];
	Chosen.ExecuteIfBound();
}

void SFlowMenu::MoveSelection(int32 Step)
{
	if (Buttons.Num() > 0)
	{
		SelectItem(FMath::Clamp(SelectedIndex + Step, 0, Buttons.Num() - 1));
	}
}

EActiveTimerReturnType SFlowMenu::KeepFocus(double InCurrentTime, float InDeltaTime)
{
	if (FSlateApplication::IsInitialized() && Buttons.IsValidIndex(SelectedIndex) && GetVisibility().IsVisible())
	{
		const TSharedPtr<SWidget> Focused = FSlateApplication::Get().GetUserFocusedWidget(0);
		// Only from nothing or the game viewport: another widget (the settings page) may own focus on purpose.
		if (!Focused.IsValid() || Focused->GetType() == FName(TEXT("SViewport")))
		{
			FSlateApplication::Get().SetAllUserFocus(Buttons[SelectedIndex], EFocusCause::SetDirectly);
		}
	}
	return EActiveTimerReturnType::Continue;
}

void SFlowMenu::HandleHovered(int32 Index)
{
	bGamepadPrompts = false;
	SelectItem(Index);
}

FText SFlowMenu::GetConfirmPrompt() const
{
	return FFlowMenuText::ConfirmPrompt(bGamepadPrompts);
}

FText SFlowMenu::GetBackPrompt() const
{
	return FFlowMenuText::BackPrompt(bGamepadPrompts);
}

bool SFlowMenu::SupportsKeyboardFocus() const
{
	return true;
}

FReply SFlowMenu::OnPreviewKeyDown(const FGeometry& MyGeometry, const FKeyEvent& InKeyEvent)
{
	// Only watches which device spoke last, for the hint's wording; the key goes on to the focused button.
	bGamepadPrompts = InKeyEvent.GetKey().IsGamepadKey();
	return FReply::Unhandled();
}

FReply SFlowMenu::OnMouseMove(const FGeometry& MyGeometry, const FPointerEvent& MouseEvent)
{
	bGamepadPrompts = false;
	return FReply::Unhandled();
}

FReply SFlowMenu::OnMouseButtonDown(const FGeometry& MyGeometry, const FPointerEvent& MouseEvent)
{
	// A click on the empty ground keeps keys and the pad on the menu (the game viewport would otherwise take focus).
	if (Buttons.IsValidIndex(SelectedIndex))
	{
		return FReply::Handled().SetUserFocus(Buttons[SelectedIndex].ToSharedRef(), EFocusCause::SetDirectly);
	}
	return FReply::Handled();
}

void SFlowMenu::OnFocusChanging(const FWeakWidgetPath& PreviousFocusPath, const FWidgetPath& NewWidgetPath, const FFocusEvent& InFocusEvent)
{
	SCompoundWidget::OnFocusChanging(PreviousFocusPath, NewWidgetPath, InFocusEvent);
	// Keys and the pad move Slate focus between the rows; the selection follows it.
	for (int32 Index = 0; Index < Buttons.Num(); ++Index)
	{
		if (NewWidgetPath.ContainsWidget(Buttons[Index].Get()))
		{
			SelectedIndex = Index;
			return;
		}
	}
}

FReply SFlowMenu::OnKeyDown(const FGeometry& MyGeometry, const FKeyEvent& InKeyEvent)
{
	const FKey Key = InKeyEvent.GetKey();
	const EFlowMenuIntent Intent = FFlowRules::MenuIntentForKey(Key);
	if (Intent == EFlowMenuIntent::Back)
	{
		return BackDelegate.ExecuteIfBound() ? FReply::Handled() : FReply::Unhandled();
	}
	// Confirm reaching the menu itself (no row held focus): choose the selected row, as the mark shows.
	if (Intent == EFlowMenuIntent::Confirm && !InKeyEvent.IsRepeat())
	{
		if (!CanConfirmSelection())
		{
			return FReply::Unhandled();
		}
		ConfirmSelection();
		return FReply::Handled();
	}
	const bool bWasdKey = Key == EKeys::W || Key == EKeys::A || Key == EKeys::S || Key == EKeys::D;
	// Up and Down move the selection here, not through Slate's focus walk, so they work whatever holds focus.
	if ((Intent == EFlowMenuIntent::Up || Intent == EFlowMenuIntent::Down) && (bWasdNavigation || !bWasdKey))
	{
		MoveSelection(Intent == EFlowMenuIntent::Down ? 1 : -1);
		return FReply::Handled();
	}
	// WASD walks the buttons like the arrow keys (left and right still go through Slate).
	if (bWasdNavigation && bWasdKey && FSlateApplication::IsInitialized())
	{
		const FKey Arrow = Intent == EFlowMenuIntent::Up ? EKeys::Up : Intent == EFlowMenuIntent::Down ? EKeys::Down
			: Intent == EFlowMenuIntent::Left ? EKeys::Left : EKeys::Right;
		FSlateApplication::Get().ProcessKeyDownEvent(FKeyEvent(Arrow, InKeyEvent.GetModifierKeys(), InKeyEvent.GetUserIndex(), InKeyEvent.IsRepeat(), 0, 0));
		return FReply::Handled();
	}
	return SCompoundWidget::OnKeyDown(MyGeometry, InKeyEvent);
}

FReply SFlowMenu::OnFocusReceived(const FGeometry& MyGeometry, const FFocusEvent& InFocusEvent)
{
	// The menu itself is only a holder: focus given to it (the input mode does that) lands on the selected button, so
	// a key or pad press chooses the row the mark is on.
	if (Buttons.IsValidIndex(SelectedIndex))
	{
		return FReply::Handled().SetUserFocus(Buttons[SelectedIndex].ToSharedRef(), EFocusCause::SetDirectly);
	}
	return SCompoundWidget::OnFocusReceived(MyGeometry, InFocusEvent);
}

void SFlowMenu::FocusFirstItem()
{
	if (Buttons.IsValidIndex(SelectedIndex) && FSlateApplication::IsInitialized())
	{
		FSlateApplication::Get().SetAllUserFocus(Buttons[SelectedIndex], EFocusCause::SetDirectly);
	}
	else if (FSlateApplication::IsInitialized())
	{
		FSlateApplication::Get().SetAllUserFocus(AsShared(), EFocusCause::SetDirectly);
	}
}

void SFlowTextScreen::Construct(const FArguments& InArgs)
{
	const FFlowTuning& Tuning = InArgs._Tuning;
	ChildSlot
	[
		SNew(SOverlay)
		+ SOverlay::Slot()
		[
			SNew(SFlowBackground).Backdrop(EFlowBackdrop::Drift).Tuning(Tuning)
		]
		+ SOverlay::Slot().HAlign(HAlign_Left).VAlign(VAlign_Center).Padding(UmbrellaUI::ColumnLeft, 0.0f, 0.0f, 0.0f)
		[
			SNew(SBox).WidthOverride(FMath::Min(Tuning.TextBlockWidth, UmbrellaUI::ColumnWidth))
			[
				SAssignNew(TextBlock, STextBlock).Font(FUmbrellaUIStyle::BodyFont(Tuning.BodyFontSize)).ColorAndOpacity(FUmbrellaUIStyle::Cream())
					.ShadowOffset(FVector2D(UmbrellaUI::ShadowOffset, UmbrellaUI::ShadowOffset)).ShadowColorAndOpacity(FUmbrellaUIStyle::Shadow())
					.AutoWrapText(true).Justification(ETextJustify::Left)
					.RenderTransform(this, &SFlowTextScreen::GetScrollTransform)
			]
		]
		+ SOverlay::Slot().HAlign(HAlign_Left).VAlign(VAlign_Center).Padding(UmbrellaUI::ColumnLeft, 0.0f, 0.0f, 0.0f)
		[
			SNew(SBox).WidthOverride(FMath::Min(Tuning.TextBlockWidth, UmbrellaUI::ColumnWidth))
			[
				SAssignNew(CreditsBox, SVerticalBox)
				.Visibility(EVisibility::Collapsed)
				.RenderTransform(this, &SFlowTextScreen::GetScrollTransform)
			]
		]
	];
}

void SFlowTextScreen::SetCredits(const TArray<FString>& Lines, float ScrollOffset)
{
	Scroll = ScrollOffset;
	if (!CreditsBox.IsValid())
	{
		return;
	}
	if (TextBlock.IsValid())
	{
		TextBlock->SetVisibility(EVisibility::Collapsed);
	}
	CreditsBox->SetVisibility(EVisibility::HitTestInvisible);
	if (Lines == CreditsShown)
	{
		return;
	}
	CreditsShown = Lines;
	CreditsBox->ClearChildren();
	const auto AddRow = [this](const FString& Text, const FSlateFontInfo& Font, const FLinearColor& Color, float Above)
	{
		CreditsBox->AddSlot().AutoHeight().Padding(0.0f, Above, 0.0f, 0.0f)
		[
			SNew(STextBlock).Text(FText::FromString(Text)).Font(Font).ColorAndOpacity(Color)
				.ShadowOffset(FVector2D(UmbrellaUI::ShadowOffset, UmbrellaUI::ShadowOffset)).ShadowColorAndOpacity(FUmbrellaUIStyle::Shadow())
		];
	};
	const auto IsRole = [](const FString& Line)
	{
		return Line.Contains(TEXT("Producer")) || Line.Contains(TEXT("Lead")) || Line.Contains(TEXT("Director"))
			|| Line.Contains(TEXT("Designer")) || Line.Contains(TEXT("Artist")) || Line.Contains(TEXT("Composer"));
	};
	for (int32 Index = 0; Index < Lines.Num(); ++Index)
	{
		FString Name, Role;
		if (Index == 0)
		{
			// "Umbrella Ella The Stolen Hour": the name on one row, the subtitle under it, as on the title screen.
			FString TitleName, TitleSubtitle;
			if (!Lines[0].Split(TEXT(" The "), &TitleName, &TitleSubtitle))
			{
				TitleName = Lines[0];
			}
			AddRow(TitleName, FUmbrellaUIStyle::DisplayFont(UmbrellaUI::CreditsTitleSize), FUmbrellaUIStyle::Cream(), 0.0f);
			if (!TitleSubtitle.IsEmpty())
			{
				AddRow(TEXT("The ") + TitleSubtitle, FUmbrellaUIStyle::DisplayFontSpaced(UmbrellaUI::CreditsSubtitleSize, UmbrellaUI::LockupSubtitleSpacing), FUmbrellaUIStyle::Gold(), 0.0f);
			}
			CreditsBox->AddSlot().AutoHeight().Padding(0.0f, UmbrellaUI::HeadingGap, UmbrellaUI::HeadingWidth - UmbrellaUI::ColumnWidth, UmbrellaUI::SectionGap)
			[
				SNew(SUmbrellaRule)
			];
		}
		else if (Lines[Index].Split(TEXT(" - "), &Name, &Role))
		{
			AddRow(Name, FUmbrellaUIStyle::DisplayFont(UmbrellaUI::CreditsNameSize), FUmbrellaUIStyle::Cream(), UmbrellaUI::CreditsGap);
			AddRow(Role, FUmbrellaUIStyle::DisplayFontSpaced(UmbrellaUI::CreditsRoleSize, UmbrellaUI::LockupSubtitleSpacing), FUmbrellaUIStyle::Gold(), 0.0f);
		}
		else if (IsRole(Lines[Index]))
		{
			AddRow(Lines[Index], FUmbrellaUIStyle::DisplayFontSpaced(UmbrellaUI::CreditsRoleSize, UmbrellaUI::LockupSubtitleSpacing), FUmbrellaUIStyle::Gold(), 0.0f);
		}
		else
		{
			AddRow(Lines[Index], FUmbrellaUIStyle::DisplayFont(UmbrellaUI::CreditsNameSize), FUmbrellaUIStyle::Cream(), UmbrellaUI::CreditsGap);
		}
	}
}

void SFlowTextScreen::SetText(const FText& NewText, float ScrollOffset)
{
	Scroll = ScrollOffset;
	if (TextBlock.IsValid())
	{
		TextBlock->SetText(NewText);
	}
}

TOptional<FSlateRenderTransform> SFlowTextScreen::GetScrollTransform() const
{
	return FSlateRenderTransform(FVector2D(0.0, -Scroll));
}
