#include "UI/Menus/FlowMenuWidgets.h"
#include "Flow/FlowRules.h"
#include "Brushes/SlateRoundedBoxBrush.h"
#include "Framework/Application/SlateApplication.h"
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
		TSharedRef<SUmbrellaButton> Button = SNew(SUmbrellaButton)
			.Text(Item.Label)
			.FontSize(Tuning.MenuFontSize)
			.Ornament(true)
			.OnClicked_Lambda([Chosen = Item.OnChosen]()
			{
				Chosen.ExecuteIfBound();
				return FReply::Handled();
			});
		if (!FirstButton.IsValid())
		{
			FirstButton = Button;
		}
		Column->AddSlot().AutoHeight().HAlign(HAlign_Left).Padding(0.0f, UmbrellaUI::ItemGap)
		[
			Button
		];
	}

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
	];
}

bool SFlowMenu::SupportsKeyboardFocus() const
{
	return true;
}

FReply SFlowMenu::OnKeyDown(const FGeometry& MyGeometry, const FKeyEvent& InKeyEvent)
{
	const FKey Key = InKeyEvent.GetKey();
	const EFlowMenuIntent Intent = FFlowRules::MenuIntentForKey(Key);
	if (Intent == EFlowMenuIntent::Back)
	{
		return BackDelegate.ExecuteIfBound() ? FReply::Handled() : FReply::Unhandled();
	}
	// WASD walks the buttons like the arrow keys (arrows and the D-pad navigate through Slate already).
	const bool bWasdKey = Key == EKeys::W || Key == EKeys::A || Key == EKeys::S || Key == EKeys::D;
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
	// The menu itself is only a holder: focus given to it (the input mode does that) lands on the first button, so the
	// player always sees which item a key or pad press will choose.
	if (FirstButton.IsValid())
	{
		return FReply::Handled().SetUserFocus(FirstButton.ToSharedRef(), EFocusCause::SetDirectly);
	}
	return SCompoundWidget::OnFocusReceived(MyGeometry, InFocusEvent);
}

void SFlowMenu::FocusFirstItem()
{
	if (FirstButton.IsValid() && FSlateApplication::IsInitialized())
	{
		FSlateApplication::Get().SetAllUserFocus(FirstButton, EFocusCause::SetDirectly);
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
	];
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
