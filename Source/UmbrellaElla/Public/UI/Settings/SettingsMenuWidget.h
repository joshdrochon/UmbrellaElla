#pragma once

#include "CoreMinimal.h"
#include "Blueprint/UserWidget.h"
#include "Core/UmbrellaPlayMode.h"
#include "Settings/SettingsModel.h"
#include "SettingsMenuWidget.generated.h"

class SVerticalBox;
class USettingsMenuSubsystem;

/**
 * The settings screen, built in C++ with Slate: page tabs (Sound, Controller, Credits, and Game Options in Director's
 * Cut only), the page body, and Back and Save. Dirty Back asks Save / Discard / Keep Editing. All rules live in
 * FSettingsSession; this widget only shows them and forwards clicks.
 */
UCLASS()
class UMBRELLAELLA_API USettingsMenuWidget final : public UUserWidget
{
	GENERATED_BODY()

public:
	/** Call before the widget is added to the screen. */
	void Setup(USettingsMenuSubsystem* InOwner, EUmbrellaPlayMode InMode);

	ESettingsPage GetPage() const { return Page; }
	void ShowPage(ESettingsPage NewPage);

	/** Back: closes when clean; when dirty shows the Save / Discard / Keep Editing prompt. */
	void PressBack();
	void PressSave();
	void ChooseBack(ESettingsBackChoice Choice);
	bool IsBackPromptShown() const { return bBackPrompt; }

	/** Start waiting for the next key for Action's Slot-th binding. */
	void BeginRemap(EUmbrellaInputAction Action, int32 Slot);
	bool IsCapturingKey() const { return bCapturing; }

	/** Give the pending remap its key (Escape cancels). Does nothing when no remap is pending. */
	void CaptureKey(const FKey& Key);

	/** Controller page Reset button: shipped default bindings in the draft. */
	void PressResetBindings();

protected:
	virtual TSharedRef<SWidget> RebuildWidget() override;
	virtual void ReleaseSlateResources(bool bReleaseChildren) override;
	virtual FReply NativeOnKeyDown(const FGeometry& InGeometry, const FKeyEvent& InKeyEvent) override;
	virtual FReply NativeOnMouseButtonDown(const FGeometry& InGeometry, const FPointerEvent& InMouseEvent) override;

private:
	void RebuildBody();
	void AddSoundBody();
	void AddControllerBody();
	void AddCreditsBody();
	void AddGameOptionsBody();
	void CloseMenu();
	int32 ScaledFont(int32 Size) const;

	TWeakObjectPtr<USettingsMenuSubsystem> Owner;
	EUmbrellaPlayMode Mode = EUmbrellaPlayMode::StartGame;
	ESettingsPage Page = ESettingsPage::Sound;
	bool bBackPrompt = false;
	bool bCapturing = false;
	EUmbrellaInputAction CaptureAction = EUmbrellaInputAction::Shoot;
	int32 CaptureSlot = 0;

	TSharedPtr<SVerticalBox> BodyBox;
	TSharedPtr<SVerticalBox> FooterBox;
};
