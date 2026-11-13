#include "UI/Story/StoryWidgets.h"
#include "Story/StoryRules.h"
#include "Core/UmbrellaTuning.h"
#include "Harness/UmbrellaFeatureFlags.h"
#include "UI/Style/UmbrellaUIStyle.h"
#include "Framework/Application/SlateApplication.h"
#include "Widgets/Input/SButton.h"
#include "Widgets/Layout/SBox.h"
#include "Widgets/Layout/SBorder.h"
#include "Widgets/SBoxPanel.h"
#include "Widgets/SOverlay.h"
#include "Widgets/Text/STextBlock.h"

namespace
{
	FSlateFontInfo StoryFont(int32 Extra)
	{
		return FUmbrellaUIStyle::BodyFont(GetDefault<UUmbrellaTuning>()->Story.MinFontSize + Extra);
	}

	FSlateFontInfo StoryDisplayFont(int32 Extra)
	{
		return FUmbrellaUIStyle::DisplayFont(GetDefault<UUmbrellaTuning>()->Story.MinFontSize + Extra);
	}

	FVector2D StoryShadow()
	{
		return FVector2D(UmbrellaUI::ShadowOffset, UmbrellaUI::ShadowOffset);
	}

	FMargin SafeMargin()
	{
		const FVector2D& Margin = GetDefault<UUmbrellaTuning>()->Story.SafeMargin;
		return FMargin(static_cast<float>(Margin.X), static_cast<float>(Margin.Y));
	}
}

TSharedRef<SWidget> UStoryCaptionWidget::RebuildWidget()
{
	// Captions are read, never clicked: the full-screen overlay sits above the menus and would take every click.
	return SNew(SOverlay).Visibility(EVisibility::HitTestInvisible)
		+ SOverlay::Slot().HAlign(HAlign_Center).VAlign(VAlign_Bottom).Padding(SafeMargin())
		[
			SAssignNew(BottomText, STextBlock)
			.Font(StoryFont(GetDefault<UUmbrellaTuning>()->Story.CaptionFontExtra))
			.ColorAndOpacity(FUmbrellaUIStyle::Cream())
			.ShadowOffset(StoryShadow())
			.ShadowColorAndOpacity(FUmbrellaUIStyle::Shadow())
			.Justification(ETextJustify::Center)
			.AutoWrapText(true)
			.Text(FText::GetEmpty())
		]
		+ SOverlay::Slot().HAlign(HAlign_Center).VAlign(VAlign_Center).Padding(SafeMargin())
		[
			SAssignNew(CentreText, STextBlock)
			.Font(StoryFont(GetDefault<UUmbrellaTuning>()->Story.NarrationFontExtra))
			.ColorAndOpacity(FUmbrellaUIStyle::Cream())
			.ShadowOffset(StoryShadow())
			.ShadowColorAndOpacity(FUmbrellaUIStyle::Shadow())
			.Justification(ETextJustify::Center)
			.AutoWrapText(true)
			.Text(FText::GetEmpty())
		];
}

void UStoryCaptionWidget::ReleaseSlateResources(bool bReleaseChildren)
{
	Super::ReleaseSlateResources(bReleaseChildren);
	BottomText.Reset();
	CentreText.Reset();
}

void UStoryCaptionWidget::SetCaption(const FString& Text, EStoryCaptionPlace Place)
{
	Caption = Text;
	const bool bCentre = Place == EStoryCaptionPlace::Centre;
	if (BottomText.IsValid())
	{
		BottomText->SetText(bCentre ? FText::GetEmpty() : FText::FromString(Text));
	}
	if (CentreText.IsValid())
	{
		CentreText->SetText(bCentre ? FText::FromString(Text) : FText::GetEmpty());
	}
}

void UJourneyCompleteWidget::SetStats(const FStoryRunStats& InStats)
{
	Rows = StoryStatsRows(InStats);
	FillRows();
}

void UJourneyCompleteWidget::FillRows()
{
	if (!RowBox.IsValid())
	{
		return;
	}
	RowBox->ClearChildren();
	for (const TPair<FString, FString>& Row : Rows)
	{
		RowBox->AddSlot().AutoHeight().Padding(0.0f, GetDefault<UUmbrellaTuning>()->Story.RowGap)
		[
			SNew(SHorizontalBox)
			+ SHorizontalBox::Slot().AutoWidth()
			[
				SNew(SBox).WidthOverride(GetDefault<UUmbrellaTuning>()->Story.RowLabelWidth)
				[
					SNew(STextBlock).Font(StoryFont(GetDefault<UUmbrellaTuning>()->Story.RowFontExtra)).ColorAndOpacity(FUmbrellaUIStyle::Dim()).Text(FText::FromString(Row.Key))
				]
			]
			+ SHorizontalBox::Slot().AutoWidth()
			[
				SNew(STextBlock).Font(StoryDisplayFont(GetDefault<UUmbrellaTuning>()->Story.RowFontExtra)).ColorAndOpacity(FUmbrellaUIStyle::GoldBright()).Text(FText::FromString(Row.Value))
			]
		];
	}
}

TSharedRef<SWidget> UJourneyCompleteWidget::RebuildWidget()
{
	const FStoryTuning& Story = GetDefault<UUmbrellaTuning>()->Story;
	TSharedRef<SWidget> Root = SNew(SOverlay)
		+ SOverlay::Slot()
		[
			SNew(SUmbrellaGround)
		]
		+ SOverlay::Slot().HAlign(HAlign_Left).VAlign(VAlign_Center).Padding(UmbrellaUI::ColumnLeft - UmbrellaUI::PanelPadding, 0.0f, 0.0f, 0.0f)
		[
			SNew(SBorder)
			.BorderImage(FUmbrellaUIStyle::PanelBrush())
			.Padding(UmbrellaUI::PanelPadding)
			[
				SNew(SVerticalBox)
				+ SVerticalBox::Slot().AutoHeight()
				[
					SNew(STextBlock).Font(StoryDisplayFont(Story.TitleFontExtra)).ColorAndOpacity(FUmbrellaUIStyle::Cream()).Text(FText::FromString(TEXT("Journey Complete")))
				]
				+ SVerticalBox::Slot().AutoHeight().Padding(0.0f, UmbrellaUI::HeadingGap, 0.0f, Story.BlockGap)
				[
					SNew(SUmbrellaRule)
				]
				+ SVerticalBox::Slot().AutoHeight()
				[
					SAssignNew(RowBox, SVerticalBox)
				]
				+ SVerticalBox::Slot().AutoHeight().Padding(0.0f, Story.BlockGap, 0.0f, 0.0f)
				[
					SNew(SHorizontalBox)
					+ SHorizontalBox::Slot().AutoWidth().Padding(0.0f, 0.0f, Story.BlockGap, 0.0f)
					[
						SAssignNew(TryAgainButton, SUmbrellaButton).Text(FText::FromString(TEXT("Try Again"))).FontSize(Story.MinFontSize + Story.ButtonFontExtra)
							.OnClicked(FOnClicked::CreateUObject(this, &UJourneyCompleteWidget::HandleTryAgain))
					]
					+ SHorizontalBox::Slot().AutoWidth()
					[
						SAssignNew(MainMenuButton, SUmbrellaButton).Text(FText::FromString(TEXT("Main Menu"))).FontSize(Story.MinFontSize + Story.ButtonFontExtra)
							.OnClicked(FOnClicked::CreateUObject(this, &UJourneyCompleteWidget::HandleMainMenu))
					]
				]
			]
		];
	// Hover selects: the hovered button also takes keyboard and pad focus, so one button is lit and Enter chooses it.
	for (const TSharedPtr<SUmbrellaButton>& Button : { TryAgainButton, MainMenuButton })
	{
		Button->SetOnHovered(FSimpleDelegate::CreateLambda([Weak = TWeakPtr<SUmbrellaButton>(Button)]()
		{
			const TSharedPtr<SUmbrellaButton> Hovered = Weak.Pin();
			if (Hovered.IsValid() && FSlateApplication::IsInitialized())
			{
				FSlateApplication::Get().SetAllUserFocus(Hovered, EFocusCause::Mouse);
			}
		}));
	}
	FillRows();
	return Root;
}

void UJourneyCompleteWidget::ReleaseSlateResources(bool bReleaseChildren)
{
	Super::ReleaseSlateResources(bReleaseChildren);
	RowBox.Reset();
	TryAgainButton.Reset();
	MainMenuButton.Reset();
}

FReply UJourneyCompleteWidget::HandleTryAgain()
{
	TryAgainDelegate.Broadcast();
	return FReply::Handled();
}

FReply UJourneyCompleteWidget::HandleMainMenu()
{
	MainMenuDelegate.Broadcast();
	return FReply::Handled();
}
