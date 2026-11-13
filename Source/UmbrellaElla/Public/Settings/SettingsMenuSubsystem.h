#pragma once

#include "CoreMinimal.h"
#include "Core/UmbrellaPlayMode.h"
#include "Containers/Ticker.h"
#if UMBRELLAELLA_WORKBENCH
#include "Settings/SettingsLiveTuning.h"
#endif
#include "Settings/SettingsModel.h"
#include "Subsystems/GameInstanceSubsystem.h"
#include "SettingsMenuSubsystem.generated.h"

class APlayerController;
class UWorld;
class USettingsMenuWidget;
class UInputMappingContext;
class USoundClass;

/**
 * Player settings: Sound, Controller, Credits and (Director's Cut only) Game Options. Owns the draft and the saved
 * copy, applies volumes to sound classes and remaps to the live input mapping context, and persists on Save.
 * Pause and title menus call OpenSettings. Earned progression is never touched here.
 */
UCLASS()
class UMBRELLAELLA_API USettingsMenuSubsystem final : public UGameInstanceSubsystem
{
	GENERATED_BODY()

public:
	virtual void Initialize(FSubsystemCollectionBase& Collection) override;
	virtual void Deinitialize() override;

	/** Open the settings menu for this player (adds the widget, shows the cursor). */
	void OpenSettings(APlayerController* Controller);

	/** Close the menu if open. */
	void CloseSettings();

	bool IsSettingsOpen() const;

	/** The mode the menus run in. Flow sets it when a run starts; it decides if Game Options exists. */
	void SetPlayMode(EUmbrellaPlayMode Mode);
	EUmbrellaPlayMode GetPlayMode() const { return PlayMode; }

	/** The class the Music slider scales; the music component plays through it. */
	USoundClass* GetMusicClass() const { return MusicClass; }

	/** The draft the widgets edit. */
	FSettingsSession& EditSession() { return Session; }
	const FSettingsSession& GetSession() const { return Session; }

	/** Save applies the current page: commit its draft, write the file, apply volumes. Failed when the file could not be written. */
	ESettingsResult SaveSettings(ESettingsPage Page);

	/** Drop unsaved changes on one page. */
	void DiscardChanges(ESettingsPage Page);

	/** Push reduced flash to the Vfx subsystem of this game instance's world (and any world that starts later). */
	void ApplyReducedFlash();

	/** What the world-init hook runs: apply the saved reduced flash to a world owned by this game instance. */
	void HandleWorldInit(UWorld* World);

	/** Saved accessibility reads for screens outside Settings (HUD, XP ring). Text size is a percent; motion is off when true.
	 *  Readers outside Settings use UmbrellaAccessibility (Settings/UmbrellaAccessibility.h), which finds this subsystem. */
	int32 GetSavedTextScalePercent() const { return Session.GetSaved().TextScalePercent; }
	bool IsReducedMotionSaved() const { return Session.GetSaved().bReducedMotion; }
	bool IsReducedFlashSaved() const { return Session.GetSaved().bReducedFlash; }

	/** Fires after every Save, so screens that cache text size or motion can re-read them. */
	FSimpleMulticastDelegate& OnSettingsSaved() { return SettingsSavedEvent; }

	/** Saved value of a developer option (its default outside Director's Cut or when the options cannot be edited). */
	int32 GetDeveloperOption(EDeveloperOption Option) const;

	/** True when the developer options take effect: Director's Cut, and a build that allows them. */
	bool IsDeveloperTuningActive() const;

	/** Write the live tuning: the baseline plus the saved developer options (when active) and reduced motion. Runs on
	 *  Save, on a play-mode change and at startup; restores the baseline when nothing is active. */
	void RefreshLiveTuning();

	/** True while the settings hold a composed copy in the live tuning (the baseline is restored when it ends). */
	bool IsLiveTuningApplied() const { return bLiveTuningApplied; }

	/** The tuning captured before the settings first changed it (what "as tuned" means on the Game Options page). */
	void GetBaselineLifeCounts(int32& OutRetryLives, int32& OutHitsPerLife) const;

	/** Follow the play mode of the first local player's controller (flow does not call SetPlayMode). */
	void SyncPlayModeFromPlayer();

	/** Tests: pretend the build is (or is not) a workbench build. */
	void SetWorkbenchBuildForTest(bool bWorkbench) { bWorkbenchBuild = bWorkbench; }

	/** Set reduced flash on one world's Vfx subsystem. Does nothing when the world has none. */
	static void ApplyReducedFlashToWorld(UWorld* World, const FUmbrellaSettingsData& Data);

	/** Set the volumes of the three sound classes from data. */
	void ApplyVolumes(const FUmbrellaSettingsData& Data);

	/** Rebuild a mapping context's keys from data's bindings. Returns how many mappings it made. */
	static int32 ApplyBindingsToContext(UInputMappingContext* Context, const FUmbrellaSettingsData& Data);

	/** Apply the saved bindings to this player's live IMC_Default (via Ella's input adapter). Returns mappings made; 0 when no pawn or context. */
	int32 ApplySavedBindings(APlayerController* Controller);

	/** Use these sound classes (tests inject transient ones). Defaults to the engine's Master, SFX and Music classes. */
	void SetSoundClasses(USoundClass* Master, USoundClass* Sfx, USoundClass* Music);

	/** Where Save writes. Tests point this at a scratch file. */
	void SetStorePath(const FString& Path);
	const FString& GetStorePath() const { return StorePath; }

	/** Reload the saved copy from the store (the draft restarts from it). */
	void ReloadFromStore();

private:
	void LoadDefaultSoundClasses();
#if UMBRELLAELLA_WORKBENCH
	void RestoreBaselineTuning();
#endif
	void ApplyReducedMotionToRings();

	FDelegateHandle WorldInitHandle;
	FTSTicker::FDelegateHandle PlayModeTicker;
	FSimpleMulticastDelegate SettingsSavedEvent;
#if UMBRELLAELLA_WORKBENCH
	FSettingsLiveTuning BaselineTuning;
#endif
	bool bLiveTuningApplied = false;
	bool bWorkbenchBuild = DeveloperOptionRules::IsWorkbenchBuild();
	FSettingsSession Session;
	FString StorePath;
	EUmbrellaPlayMode PlayMode = EUmbrellaPlayMode::StartGame;

	UPROPERTY(Transient)
	TObjectPtr<USoundClass> MasterClass;

	UPROPERTY(Transient)
	TObjectPtr<USoundClass> SfxClass;

	UPROPERTY(Transient)
	TObjectPtr<USoundClass> MusicClass;

	UPROPERTY(Transient)
	TObjectPtr<USettingsMenuWidget> OpenWidget;
	TWeakObjectPtr<APlayerController> OpenController;
};
