#include "UI/Menus/FlowMenuWidgets.h"
#include "Flow/FlowRules.h"
#include "Brushes/SlateColorBrush.h"
#include "Brushes/SlateRoundedBoxBrush.h"
#include "Fonts/SlateFontInfo.h"
#include "Framework/Application/SlateApplication.h"
#include "Rendering/DrawElements.h"
#include "Styling/CoreStyle.h"
#include "Widgets/Input/SButton.h"
#include "Widgets/Layout/SBox.h"
#include "Widgets/SBoxPanel.h"
#include "Widgets/SOverlay.h"
#include "Widgets/Text/STextBlock.h"

namespace
{
	/** Fraction part in [0, 1). */
	float Frac(float Value)
	{
		return Value - FMath::FloorToFloat(Value);
	}

	FSlateFontInfo MakeFont(int32 Size)
	{
		return FCoreStyle::GetDefaultFontStyle(TEXT("Bold"), Size);
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
	int32 Layer = LayerId;

	FSlateDrawElement::MakeBox(OutDrawElements, Layer, AllottedGeometry.ToPaintGeometry(Size, FSlateLayoutTransform()), White,
		ESlateDrawEffect::None, Tuning.BackgroundColor);

	++Layer;
	// Falling shapes: index decides column, size and speed, so nothing needs a random stream.
	for (int32 Index = 0; Index < Tuning.FallingShapeCount; ++Index)
	{
		const float Spread = Frac(static_cast<float>(Index + 1) * Tuning.BackgroundSpreadStep);
		const float ShapeSize = FMath::Lerp(Tuning.FallingShapeMinSize, Tuning.FallingShapeMaxSize, Spread);
		const float Speed = FMath::Lerp(Tuning.FallingShapeMinSpeed, Tuning.FallingShapeMaxSpeed, Frac(Spread * Tuning.FallingShapeCount));
		const float Travel = Size.Y + ShapeSize * 2.0f;
		const float Y = Frac((Time * Speed + Spread * Travel) / Travel) * Travel - ShapeSize;
		const float X = Spread * Size.X + FMath::Sin(Time * Tuning.BackgroundSwaySpeed + Index) * Tuning.BackgroundSwayAmplitude;
		FSlateDrawElement::MakeBox(OutDrawElements, Layer,
			AllottedGeometry.ToPaintGeometry(FVector2f(ShapeSize, ShapeSize), FSlateLayoutTransform(FVector2f(X, Y))), &Round,
			ESlateDrawEffect::None, Tuning.ShapeColor);
	}

	if (Backdrop == EFlowBackdrop::Clocks)
	{
		++Layer;
		const FSlateRoundedBoxBrush Face(FLinearColor::Transparent, Tuning.PauseClockRadius, Tuning.ClockColor, Tuning.ClockHandThickness);
		for (int32 Index = 0; Index < Tuning.PauseClockCount; ++Index)
		{
			const float Spread = Frac(static_cast<float>(Index + 1) * Tuning.BackgroundSpreadStep);
			const float Diameter = Tuning.PauseClockRadius * 2.0f;
			const float Drift = FMath::Sin(Time * Tuning.BackgroundSwaySpeed + Index) * Tuning.BackgroundSwayAmplitude;
			const FVector2f Center(Spread * Size.X + Drift, Frac(Spread * Tuning.PauseClockCount + Index * Tuning.BackgroundSpreadStep) * Size.Y);
			FSlateDrawElement::MakeBox(OutDrawElements, Layer,
				AllottedGeometry.ToPaintGeometry(FVector2f(Diameter, Diameter), FSlateLayoutTransform(Center - FVector2f(Tuning.PauseClockRadius, Tuning.PauseClockRadius))),
				&Face, ESlateDrawEffect::None, Tuning.ClockColor);

			// A ticking minute hand: one step per second.
			const float Step = FMath::FloorToFloat(Time) / Tuning.ClockTurnSeconds;
			const float Angle = (Step + Spread) * UE_TWO_PI;
			const float Length = Tuning.PauseClockRadius * Tuning.ClockHandLengthShare;
			const FVector2f HandSize(Tuning.ClockHandThickness, Length);
			const FVector2f HandPos = Center - FVector2f(Tuning.ClockHandThickness * 0.5f, Length);
			FSlateDrawElement::MakeRotatedBox(OutDrawElements, Layer + 1,
				AllottedGeometry.ToPaintGeometry(HandSize, FSlateLayoutTransform(HandPos)), White, ESlateDrawEffect::None, Angle,
				FVector2D(HandSize.X * 0.5, HandSize.Y), FSlateDrawElement::RelativeToElement, Tuning.ClockColor);
		}
	}
	return Layer + 2;
}

void SFlowMenu::Construct(const FArguments& InArgs)
{
	const FFlowTuning& Tuning = InArgs._Tuning;
	BackDelegate = InArgs._OnBack;
	bWasdNavigation = InArgs._WasdNavigation;

	NormalBrush = MakeShared<FSlateRoundedBoxBrush>(Tuning.ButtonColor, Tuning.ButtonCornerRadius);
	HoverBrush = MakeShared<FSlateRoundedBoxBrush>(Tuning.ButtonHoverColor, Tuning.ButtonCornerRadius);
	PressedBrush = MakeShared<FSlateRoundedBoxBrush>(Tuning.ButtonPressedColor, Tuning.ButtonCornerRadius);
	ButtonStyle = FButtonStyle().SetNormal(*NormalBrush).SetHovered(*HoverBrush).SetPressed(*PressedBrush);

	TSharedRef<SVerticalBox> Column = SNew(SVerticalBox);
	if (!InArgs._Heading.IsEmpty())
	{
		Column->AddSlot().AutoHeight().HAlign(HAlign_Center).Padding(0.0f, 0.0f, 0.0f, Tuning.MenuSpacing)
		[
			SNew(STextBlock).Text(InArgs._Heading).Font(MakeFont(Tuning.TitleFontSize)).ColorAndOpacity(Tuning.TextColor)
		];
	}
	if (!InArgs._Body.IsEmpty())
	{
		Column->AddSlot().AutoHeight().HAlign(HAlign_Center).Padding(0.0f, 0.0f, 0.0f, Tuning.MenuSpacing)
		[
			SNew(SBox).WidthOverride(Tuning.TextBlockWidth)
			[
				SNew(STextBlock).Text(InArgs._Body).Font(MakeFont(Tuning.BodyFontSize)).ColorAndOpacity(Tuning.TextColor)
					.AutoWrapText(true).Justification(ETextJustify::Center)
			]
		];
	}
	for (const FFlowMenuItem& Item : InArgs._Items)
	{
		TSharedRef<SButton> Button = SNew(SButton)
			.ButtonStyle(&ButtonStyle)
			.ContentPadding(FMargin(Tuning.ButtonPaddingX, Tuning.ButtonPaddingY))
			.HAlign(HAlign_Center)
			.OnClicked_Lambda([Chosen = Item.OnChosen]()
			{
				Chosen.ExecuteIfBound();
				return FReply::Handled();
			})
			[
				SNew(STextBlock).Text(Item.Label).Font(MakeFont(Tuning.MenuFontSize)).ColorAndOpacity(Tuning.TextColor)
			];
		if (!FirstButton.IsValid())
		{
			FirstButton = Button;
		}
		Column->AddSlot().AutoHeight().HAlign(HAlign_Center).Padding(0.0f, Tuning.MenuSpacing * 0.5f)
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
		+ SOverlay::Slot().HAlign(HAlign_Center).VAlign(VAlign_Center)
		[
			Column
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
		+ SOverlay::Slot().HAlign(HAlign_Center).VAlign(VAlign_Center)
		[
			SNew(SBox).WidthOverride(Tuning.TextBlockWidth)
			[
				SAssignNew(TextBlock, STextBlock).Font(MakeFont(Tuning.BodyFontSize)).ColorAndOpacity(Tuning.TextColor)
					.AutoWrapText(true).Justification(ETextJustify::Center)
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
