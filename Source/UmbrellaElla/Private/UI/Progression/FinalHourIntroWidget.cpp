#include "UI/Progression/FinalHourIntroWidget.h"
#include "GameFramework/PlayerController.h"
#include "Harness/UmbrellaFeatureFlags.h"
#include "Progression/ProgressionSubsystem.h"
#include "Progression/ProgressionTuning.h"
#include "Styling/CoreStyle.h"
#include "UI/Style/UmbrellaUIStyle.h"
#include "Widgets/Layout/SBorder.h"
#include "Widgets/Text/STextBlock.h"

#define LOCTEXT_NAMESPACE "FinalHourIntro"

UFinalHourIntroWidget* UFinalHourIntroWidget::Show(APlayerController* Owner, float Seconds)
{
	if (Owner == nullptr || !IsFeatureEnabled(EFeatureId::FLOW_06))
	{
		return nullptr;
	}
	UFinalHourIntroWidget* Intro = CreateWidget<UFinalHourIntroWidget>(Owner);
	if (Intro != nullptr)
	{
		Intro->SecondsLeft = Seconds;
		Intro->AddToViewport();
	}
	return Intro;
}

FText UFinalHourIntroWidget::IntroText()
{
	return LOCTEXT("Text", "Your borrowed time has run its course. Now, face the Final Hour.");
}

TSharedRef<SWidget> UFinalHourIntroWidget::RebuildWidget()
{
	const UProgressionSubsystem* Subsystem = UProgressionSubsystem::Get(GetOwningPlayer());
	const int32 Size = Subsystem != nullptr ? Subsystem->GetTuning().FinalHourIntroTextSize : FProgressionTuning().FinalHourIntroTextSize;
	return SNew(SBorder)
		.BorderImage(FCoreStyle::Get().GetBrush(TEXT("WhiteBrush")))
		.BorderBackgroundColor(FUmbrellaUIStyle::Ink())
		.HAlign(HAlign_Center)
		.VAlign(VAlign_Center)
		[
			SNew(STextBlock)
				.Font(FUmbrellaUIStyle::DisplayFont(Size))
				.ColorAndOpacity(FUmbrellaUIStyle::GoldBright())
				.Justification(ETextJustify::Center)
				.AutoWrapText(true)
				.Text(IntroText())
		];
}

void UFinalHourIntroWidget::NativeTick(const FGeometry& MyGeometry, float InDeltaTime)
{
	Super::NativeTick(MyGeometry, InDeltaTime);
	SecondsLeft -= InDeltaTime;
	if (SecondsLeft <= 0.0f)
	{
		RemoveFromParent();
	}
}

#undef LOCTEXT_NAMESPACE
