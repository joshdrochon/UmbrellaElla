#pragma once

#include "CoreMinimal.h"
#include "Core/UmbrellaPlayMode.h"
#include "Flow/FlowRules.h"
#include "GameFramework/PlayerController.h"
#include "UmbrellaPlayerController.generated.h"

struct FUmbrellaEvent;
class SWidget;
class SFlowTextScreen;
class UInputAction;
class UInputMappingContext;
class UProgressionPurchaseWidget;
class UXpRingWidget;

/**
 * Menus, pause, mode select and IMC_Menu switching (Flow, lane d). Owns the screen state (FFlowRules), the widgets for
 * each screen and the swap between gameplay and menu input contexts.
 */
UCLASS()
class UMBRELLAELLA_API AUmbrellaPlayerController : public APlayerController
{
	GENERATED_BODY()

public:
	AUmbrellaPlayerController();

	EFlowScreen GetScreen() const { return Screen; }

	/** The level the level-up screen shows (0 before the first). */
	int32 GetLevelUpShown() const { return LevelUpShown; }

	EUmbrellaPlayMode GetPlayMode() const { return PlayMode; }

	/** True while a menu or end screen holds the input (gameplay contexts are off). */
	bool IsGameplayInputBlocked() const;

	/** How many times Retry has reset the encounter. */
	int32 GetRetryCount() const { return RetryCount; }

	/** True once the credits asked to return to the title. */
	bool HasRequestedTitleReturn() const { return bTitleReturnRequested; }

	/** The Start screen buttons call this. Start Game: one basic shot, straight to the Keeper. */
	void StartGame();

	/** Director's Cut: until its level exists, the same Keeper fight with a banner. */
	void StartDirectorsCut();

	/** The smoke hook starts a run through the Start Game path, not around it. */
	void RequestSmokeStart();

	/** Apply a flow command (Escape, buttons, events, timers all end here). */
	void ApplyCommand(EFlowCommand Command);

	/** True once the first-start tutorial was finished or skipped. */
	bool IsTutorialSeen() const { return bTutorialSeen; }

	/** The tutorial page showing now (zero based). */
	int32 GetTutorialPage() const { return TutorialPage; }

	/** Mark the tutorial seen (kept in the player's settings file unless KeepTutorialInMemoryOnly was called). */
	void MarkTutorialSeen();

	/** Forget that the tutorial was seen, in memory only (the next Start shows it again). */
	void ClearTutorialSeen();

	/** Never read or write the settings file for the tutorial flag (tests and the smoke hook use this). */
	void KeepTutorialInMemoryOnly();

	/** True when a Director's Cut start should first offer the purchase screen (unspent points to spend). */
	bool ShouldOfferPurchase() const;

	/** The purchase screen while it is open (null otherwise); tests read its draft. */
	UProgressionPurchaseWidget* GetPurchaseWidget() const { return PurchaseWidget; }

	/** Advance the screen timers by real seconds; runs while the world is paused. */
	void TickFlow(float DeltaSeconds);

protected:
	virtual void BeginPlay() override;
	virtual void EndPlay(const EEndPlayReason::Type EndPlayReason) override;
	virtual void SetupInputComponent() override;
	virtual void PlayerTick(float DeltaTime) override;
	virtual void OnPossess(APawn* InPawn) override;

private:
	void StartMode(EUmbrellaPlayMode Mode);
	void BeginRun();
	void AdvanceTutorial();
	void OpenSettingsMenu();
	void CloseSettingsMenu();
	bool IsSettingsMenuOpen() const;
	void ShowPurchaseScreen();
	void ClearPurchaseScreen();
	void SyncProgressionMode(EUmbrellaPlayMode Mode);
	void EnterScreen(EFlowScreen To, EFlowCommand Cause);
	void ShowScreenWidget();
	void ClearScreenWidget();
	void SetInputBlocked(bool bBlocked);
	void ApplyPawnInputBlock();
	void SetInputModeFor(EFlowScreen To);
	void AddViewportWidget(const TSharedRef<SWidget>& Widget);
	void ReturnToTitle();
	void QuitGame();
	bool IsAnyNeutralKeyHeld() const;
	void OnPausePressed();
	void HandlePlayerDefeated(const FUmbrellaEvent& Event);
	void HandleEncounterCompleted(const FUmbrellaEvent& Event);
	void HandleLevelGained(const FUmbrellaEvent& Event);
	void RefreshTimedText();

	UPROPERTY()
	TObjectPtr<UInputMappingContext> MenuContext;

	UPROPERTY()
	TObjectPtr<UInputAction> PauseAction;

	UPROPERTY()
	TObjectPtr<UProgressionPurchaseWidget> PurchaseWidget;

	UPROPERTY()
	TObjectPtr<UXpRingWidget> XpRing;

	TSharedPtr<SWidget> PurchaseDoneButton;
	bool bPurchaseDone = false;
	bool bSettingsOpened = false;

	EFlowScreen Screen = EFlowScreen::Title;
	EUmbrellaPlayMode PlayMode = EUmbrellaPlayMode::StartGame;
	TSharedPtr<SWidget> ScreenWidget;
	TSharedPtr<SFlowTextScreen> TextScreen;
	FDelegateHandle DefeatHandle;
	FDelegateHandle CompletedHandle;
	FDelegateHandle LevelHandle;
	int32 LevelUpShown = 0;
	float StoryElapsed = 0.0f;
	float CreditsElapsed = 0.0f;
	float NeutralSeconds = 0.0f;
	int32 RetryCount = 0;
	int32 TutorialPage = 0;
	bool bTutorialSeen = false;
	bool bTutorialInMemoryOnly = false;
	bool bRunBegun = false;
	bool bInputBlocked = false;
	bool bTitleReturnRequested = false;
};
