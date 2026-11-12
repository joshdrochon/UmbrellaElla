#include "UI/Story/StoryWidgets.h"
#include "Story/StoryRules.h"
#include "Harness/UmbrellaFeatureFlags.h"
#include "Styling/CoreStyle.h"
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
		return FCoreStyle::GetDefaultFontStyle(TEXT("Regular"), FStoryTuning::Get().MinFontSize + Extra);
	}

	FMargin SafeMargin()
	{
		const FVector2D& Margin = FStoryTuning::Get().SafeMargin;
		return FMargin(static_cast<float>(Margin.X), static_cast<float>(Margin.Y));
	}
}

TSharedRef<SWidget> UStoryCaptionWidget::RebuildWidget()
{
	return SNew(SOverlay)
		+ SOverlay::Slot().HAlign(HAlign_Center).VAlign(VAlign_Bottom).Padding(SafeMargin())
		[
			SAssignNew(BottomText, STextBlock)
			.Font(StoryFont(FStoryTuning::Get().CaptionFontExtra))
			.ColorAndOpacity(FStoryTuning::Get().TextColor)
			.Justification(ETextJustify::Center)
			.AutoWrapText(true)
			.Text(FText::GetEmpty())
		]
		+ SOverlay::Slot().HAlign(HAlign_Center).VAlign(VAlign_Center).Padding(SafeMargin())
		[
			SAssignNew(CentreText, STextBlock)
			.Font(StoryFont(FStoryTuning::Get().NarrationFontExtra))
			.ColorAndOpacity(FStoryTuning::Get().TextColor)
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
		RowBox->AddSlot().AutoHeight().Padding(0.0f, FStoryTuning::Get().RowGap)
		[
			SNew(SHorizontalBox)
			+ SHorizontalBox::Slot().AutoWidth()
			[
				SNew(SBox).WidthOverride(FStoryTuning::Get().RowLabelWidth)
				[
					SNew(STextBlock).Font(StoryFont(FStoryTuning::Get().RowFontExtra)).ColorAndOpacity(FStoryTuning::Get().TextColor).Text(FText::FromString(Row.Key))
				]
			]
			+ SHorizontalBox::Slot().AutoWidth()
			[
				SNew(STextBlock).Font(StoryFont(FStoryTuning::Get().RowFontExtra)).ColorAndOpacity(FStoryTuning::Get().TextColor).Text(FText::FromString(Row.Value))
			]
		];
	}
}

TSharedRef<SWidget> UJourneyCompleteWidget::RebuildWidget()
{
	TSharedRef<SWidget> Root = SNew(SBorder)
		.BorderBackgroundColor(FStoryTuning::Get().PanelColor)
		.Padding(SafeMargin())
		[
			SNew(SVerticalBox)
			+ SVerticalBox::Slot().AutoHeight().Padding(0.0f, 0.0f, 0.0f, FStoryTuning::Get().BlockGap)
			[
				SNew(STextBlock).Font(StoryFont(FStoryTuning::Get().TitleFontExtra)).ColorAndOpacity(FStoryTuning::Get().TextColor).Text(FText::FromString(TEXT("Journey Complete")))
			]
			+ SVerticalBox::Slot().AutoHeight()
			[
				SAssignNew(RowBox, SVerticalBox)
			]
			+ SVerticalBox::Slot().AutoHeight().Padding(0.0f, FStoryTuning::Get().BlockGap, 0.0f, 0.0f)
			[
				SNew(SHorizontalBox)
				+ SHorizontalBox::Slot().AutoWidth().Padding(0.0f, 0.0f, FStoryTuning::Get().BlockGap, 0.0f)
				[
					SNew(SButton).OnClicked(FOnClicked::CreateUObject(this, &UJourneyCompleteWidget::HandleTryAgain))
					[
						SNew(STextBlock).Font(StoryFont(FStoryTuning::Get().ButtonFontExtra)).Text(FText::FromString(TEXT("Try Again")))
					]
				]
				+ SHorizontalBox::Slot().AutoWidth()
				[
					SNew(SButton).OnClicked(FOnClicked::CreateUObject(this, &UJourneyCompleteWidget::HandleMainMenu))
					[
						SNew(STextBlock).Font(StoryFont(FStoryTuning::Get().ButtonFontExtra)).Text(FText::FromString(TEXT("Main Menu")))
					]
				]
			]
		];
	FillRows();
	return Root;
}

void UJourneyCompleteWidget::ReleaseSlateResources(bool bReleaseChildren)
{
	Super::ReleaseSlateResources(bReleaseChildren);
	RowBox.Reset();
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
