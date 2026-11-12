#pragma once

#include "CoreMinimal.h"
#include "Core/UmbrellaPlayMode.h"
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

	/** The draft the widgets edit. */
	FSettingsSession& EditSession() { return Session; }
	const FSettingsSession& GetSession() const { return Session; }

	/** Save applies the current page: commit its draft, write the file, apply volumes. Failed when the file could not be written. */
	ESettingsResult SaveSettings(ESettingsPage Page);

	/** Drop unsaved changes on one page. */
	void DiscardChanges(ESettingsPage Page);

	/** Push reduced flash to the Vfx subsystem of this game instance's world (and any world that starts later). */
	void ApplyReducedFlash();

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
	FDelegateHandle WorldInitHandle;

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
