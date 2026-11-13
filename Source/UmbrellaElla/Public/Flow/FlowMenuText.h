#pragma once

#include "CoreMinimal.h"

/** The fixed wording of the Start, Pause and retry menus (the retained design). Placeholder: Story owns final text. */
struct UMBRELLAELLA_API FFlowMenuText
{
	static FText TitleHeading();
	static FText StartGameLabel();
	static FText DirectorsCutLabel();
	static FText PausedHeading();
	static FText ContinueLabel();
	static FText SettingsLabel();
	static FText QuitLabel();
	static FText SkipLabel();
	static FText DoneLabel();
	static FText BackLabel();
	static FText SettingsHeading();
	static FText SettingsStubBody();
	static FText LevelUpHeading(int32 Level);
	static FText LevelUpBody();
	static FText DefeatHeading();
	static FText RetryLabel();
	static FText QuitToTitleLabel();

	/** The control hint at the bottom right of every menu (pipeline/ui/menus.md rule 4): Confirm, then Back. */
	static FText ConfirmPrompt(bool bGamepad);
	static FText BackPrompt(bool bGamepad);

	/** Button order on the Start screen, the pause menu and the retry screen. */
	static TArray<FText> TitleLabels();
	static TArray<FText> PauseLabels();
	static TArray<FText> DefeatLabels();
};
