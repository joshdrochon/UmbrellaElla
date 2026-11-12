#pragma once

#include "CoreMinimal.h"
#include "Core/UmbrellaEvent.h"
#include "Story/StoryRules.h"
#include "Subsystems/WorldSubsystem.h"
#include "StorySubsystem.generated.h"

class UJourneyCompleteWidget;
class UStoryCaptionWidget;

DECLARE_MULTICAST_DELEGATE(FOnStorySimple);

/**
 * Director's Cut story and Journey Complete. Reacts to bus events through FStoryModel and shows captions, ending
 * text and the Journey Complete screen. Story never decides combat success. Lane story.
 */
UCLASS()
class UMBRELLAELLA_API UStorySubsystem : public UTickableWorldSubsystem
{
	GENERATED_BODY()

public:
	virtual bool ShouldCreateSubsystem(UObject* Outer) const override;
	virtual void Initialize(FSubsystemCollectionBase& Collection) override;
	virtual void Deinitialize() override;
	virtual void PostInitialize() override;
	virtual void Tick(float DeltaTime) override;
	virtual TStatId GetStatId() const override;

	/**
	 * Flow calls this when a Director's Cut win must show its ending. Idempotent: the ending also starts by itself on
	 * EncounterCompleted. Does nothing outside Director's Cut.
	 */
	void ShowDirectorsCutEnding();

	/**
	 * Flow calls this once the play world for the chosen mode is up (the mode may have been chosen before this world
	 * existed, so the ModeSelected event can be missed). A later ModeSelected for the same untouched run is ignored.
	 */
	void BeginNewRun(EUmbrellaPlayMode Mode);

	/** Flow asks before routing a skip press to play: true while the opening or a skippable ending is on screen. */
	bool IsSkipPressForStory() const;

	/** Skip press from flow (after IsSkipPressForStory()). */
	void HandleSkipPressed();

	const FStoryModel& GetModel() const { return Model; }

	/** Bound by flow: Try Again / Main Menu from the statistics screen. */
	FOnStorySimple& GetTryAgainDelegate() const { return TryAgainDelegate; }
	FOnStorySimple& GetMainMenuDelegate() const { return MainMenuDelegate; }

	static FString ProgressPath();
	static FStoryProgress LoadProgress(const FString& Path);
	static void SaveProgress(const FString& Path, const FStoryProgress& Progress);

private:
	void HandleEvent(const FUmbrellaEvent& Event);
	void HandleTryAgain();
	void HandleMainMenu();
	void Refresh();
	void EnsureWidgets();

	mutable FOnStorySimple TryAgainDelegate;
	mutable FOnStorySimple MainMenuDelegate;
	FStoryModel Model;
	TArray<TPair<EUmbrellaEventType, FDelegateHandle>> Handles;

	UPROPERTY(Transient)
	TObjectPtr<UStoryCaptionWidget> Caption;

	UPROPERTY(Transient)
	TObjectPtr<UJourneyCompleteWidget> Statistics;

	bool bStatisticsShown = false;
};
