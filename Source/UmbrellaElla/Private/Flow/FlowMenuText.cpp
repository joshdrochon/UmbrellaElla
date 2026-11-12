#include "Flow/FlowMenuText.h"

FText FFlowMenuText::TitleHeading() { return FText::FromString(TEXT("Umbrella Ella")); }
FText FFlowMenuText::StartGameLabel() { return FText::FromString(TEXT("Start Game")); }
FText FFlowMenuText::DirectorsCutLabel() { return FText::FromString(TEXT("Start Director's Cut")); }
FText FFlowMenuText::PausedHeading() { return FText::FromString(TEXT("Paused")); }
FText FFlowMenuText::ContinueLabel() { return FText::FromString(TEXT("Continue")); }
FText FFlowMenuText::SettingsLabel() { return FText::FromString(TEXT("Settings")); }
FText FFlowMenuText::QuitLabel() { return FText::FromString(TEXT("Quit")); }
FText FFlowMenuText::SkipLabel() { return FText::FromString(TEXT("Skip")); }
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
