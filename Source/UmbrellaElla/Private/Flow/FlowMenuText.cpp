#include "Flow/FlowMenuText.h"

FText FFlowMenuText::TitleHeading() { return FText::FromString(TEXT("Umbrella Ella\nThe Stolen Hour")); }
FText FFlowMenuText::StartGameLabel() { return FText::FromString(TEXT("Start Game")); }
FText FFlowMenuText::DirectorsCutLabel() { return FText::FromString(TEXT("Director's Cut")); }
FText FFlowMenuText::PausedHeading() { return FText::FromString(TEXT("Paused")); }
FText FFlowMenuText::ContinueLabel() { return FText::FromString(TEXT("Continue")); }
FText FFlowMenuText::SettingsLabel() { return FText::FromString(TEXT("Settings")); }
FText FFlowMenuText::QuitLabel() { return FText::FromString(TEXT("Quit")); }
FText FFlowMenuText::SkipLabel() { return FText::FromString(TEXT("Skip")); }
FText FFlowMenuText::DoneLabel() { return FText::FromString(TEXT("Done")); }
FText FFlowMenuText::BackLabel() { return FText::FromString(TEXT("Back")); }
FText FFlowMenuText::SettingsHeading() { return FText::FromString(TEXT("Settings")); }
FText FFlowMenuText::SettingsStubBody() { return FText::FromString(TEXT("Sound, Controller and Credits have their own pages.")); }
FText FFlowMenuText::LevelUpHeading(int32 Level) { return FText::FromString(FString::Printf(TEXT("Level %d"), Level)); }
FText FFlowMenuText::LevelUpBody() { return FText::FromString(TEXT("A new point to spend at the next refuge.")); }
FText FFlowMenuText::DefeatHeading() { return FText::FromString(TEXT("Defeated")); }
FText FFlowMenuText::RetryLabel() { return FText::FromString(TEXT("Retry")); }
FText FFlowMenuText::QuitToTitleLabel() { return FText::FromString(TEXT("Quit to Title")); }

TArray<FText> FFlowMenuText::TitleLabels()
{
	return { StartGameLabel(), DirectorsCutLabel() };
}

TArray<FText> FFlowMenuText::PauseLabels()
{
	return { ContinueLabel(), SettingsLabel(), QuitLabel() };
}

TArray<FText> FFlowMenuText::DefeatLabels()
{
	return { RetryLabel(), QuitToTitleLabel() };
}
