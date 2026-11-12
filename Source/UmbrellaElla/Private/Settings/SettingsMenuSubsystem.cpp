#include "Settings/SettingsMenuSubsystem.h"
#include "EnhancedInputSubsystems.h"
#include "Engine/LocalPlayer.h"
#include "GameFramework/PlayerController.h"
#include "Harness/UmbrellaFeatureFlags.h"
#include "Input/EllaInputAdapterComponent.h"
#include "InputAction.h"
#include "InputMappingContext.h"
#include "InputModifiers.h"
#include "Settings/SettingsStore.h"
#include "Sound/SoundClass.h"
#include "UI/Settings/SettingsMenuWidget.h"

namespace
{
	const TCHAR* const MasterClassPath = TEXT("/Engine/EngineSounds/Master.Master");
	const TCHAR* const SfxClassPath = TEXT("/Engine/EngineSounds/SFX.SFX");
	const TCHAR* const MusicClassPath = TEXT("/Engine/EngineSounds/Music.Music");
}

void USettingsMenuSubsystem::Initialize(FSubsystemCollectionBase& Collection)
{
	Super::Initialize(Collection);
	StorePath = SettingsStore::GetDefaultPath();
	LoadDefaultSoundClasses();
	if (IsFeatureEnabled(EFeatureId::FLOW_43))
	{
		ReloadFromStore();
		ApplyVolumes(Session.GetSaved());
	}
}

void USettingsMenuSubsystem::Deinitialize()
{
	CloseSettings();
	Super::Deinitialize();
}

void USettingsMenuSubsystem::LoadDefaultSoundClasses()
{
	MasterClass = LoadObject<USoundClass>(nullptr, MasterClassPath);
	SfxClass = LoadObject<USoundClass>(nullptr, SfxClassPath);
	MusicClass = LoadObject<USoundClass>(nullptr, MusicClassPath);
}

void USettingsMenuSubsystem::SetSoundClasses(USoundClass* Master, USoundClass* Sfx, USoundClass* Music)
{
	MasterClass = Master;
	SfxClass = Sfx;
	MusicClass = Music;
}

void USettingsMenuSubsystem::SetStorePath(const FString& Path)
{
	StorePath = Path;
}

void USettingsMenuSubsystem::SetPlayMode(EUmbrellaPlayMode Mode)
{
	PlayMode = Mode;
}

void USettingsMenuSubsystem::ReloadFromStore()
{
	FUmbrellaSettingsData Loaded;
	SettingsStore::Read(StorePath, Loaded);
	Session = FSettingsSession(Loaded);
}

void USettingsMenuSubsystem::ApplyVolumes(const FUmbrellaSettingsData& Data)
{
	// Master is the parent of SFX and Music in the engine's class tree, so it scales both on top of their own value.
	if (MasterClass)
	{
		MasterClass->Properties.Volume = SettingsRules::VolumeToClassScale(Data.MasterVolume);
	}
	if (SfxClass)
	{
		SfxClass->Properties.Volume = SettingsRules::VolumeToClassScale(Data.SfxVolume);
	}
	if (MusicClass)
	{
		MusicClass->Properties.Volume = SettingsRules::VolumeToClassScale(Data.MusicVolume);
	}
}

int32 USettingsMenuSubsystem::ApplyBindingsToContext(UInputMappingContext* Context, const FUmbrellaSettingsData& Data)
{
	if (!Context || !IsFeatureEnabled(EFeatureId::MOVE_17))
	{
		return 0;
	}
	// Keep one UInputAction per name from the current mappings, then rebuild the keys from the saved list.
	TMap<FName, TObjectPtr<const UInputAction>> ActionsByName;
	for (const FEnhancedActionKeyMapping& Mapping : Context->GetMappings())
	{
		if (Mapping.Action)
		{
			ActionsByName.Add(Mapping.Action->GetFName(), Mapping.Action);
		}
	}
	Context->UnmapAll();
	int32 Made = 0;
	for (const FUmbrellaDefaultBinding& Binding : Data.Bindings)
	{
		const TObjectPtr<const UInputAction>* Found = ActionsByName.Find(UmbrellaInputBindings::ActionName(Binding.Action));
		if (!Found)
		{
			continue;
		}
		FEnhancedActionKeyMapping& Mapping = Context->MapKey(*Found, Binding.Key);
		if (Binding.Scale < 0.0f)
		{
			Mapping.Modifiers.Add(NewObject<UInputModifierNegate>(Context));
		}
		++Made;
	}
	return Made;
}

int32 USettingsMenuSubsystem::ApplySavedBindings(APlayerController* Controller)
{
	APawn* Pawn = Controller ? Controller->GetPawn() : nullptr;
	UEllaInputAdapterComponent* Adapter = Pawn ? Pawn->FindComponentByClass<UEllaInputAdapterComponent>() : nullptr;
	UInputMappingContext* Context = Adapter ? Adapter->GetMappingContext() : nullptr;
	if (!Context)
	{
		return 0;
	}
	const int32 Made = ApplyBindingsToContext(Context, Session.GetSaved());
	const ULocalPlayer* LocalPlayer = Controller->GetLocalPlayer();
	if (UEnhancedInputLocalPlayerSubsystem* Input = LocalPlayer ? LocalPlayer->GetSubsystem<UEnhancedInputLocalPlayerSubsystem>() : nullptr)
	{
		Input->RequestRebuildControlMappings();
	}
	return Made;
}

ESettingsResult USettingsMenuSubsystem::SaveSettings(ESettingsPage Page)
{
	if (!IsFeatureEnabled(EFeatureId::FLOW_43))
	{
		return ESettingsResult::Failed;
	}
	Session.SavePage(Page);
	ApplyVolumes(Session.GetSaved());
	return SettingsStore::Write(StorePath, Session.GetSaved());
}

void USettingsMenuSubsystem::DiscardChanges(ESettingsPage Page)
{
	Session.DiscardPage(Page);
}

void USettingsMenuSubsystem::OpenSettings(APlayerController* Controller)
{
	if (!Controller || !IsFeatureEnabled(EFeatureId::FLOW_36) || IsSettingsOpen())
	{
		return;
	}
	OpenWidget = CreateWidget<USettingsMenuWidget>(Controller, USettingsMenuWidget::StaticClass());
	if (OpenWidget)
	{
		OpenWidget->Setup(this, PlayMode);
		OpenWidget->AddToPlayerScreen();
		Controller->SetShowMouseCursor(true);
		FInputModeUIOnly InputMode;
		InputMode.SetWidgetToFocus(OpenWidget->TakeWidget());
		InputMode.SetLockMouseToViewportBehavior(EMouseLockMode::DoNotLock);
		Controller->SetInputMode(InputMode);
		OpenWidget->SetUserFocus(Controller);
		OpenController = Controller;
	}
}

void USettingsMenuSubsystem::CloseSettings()
{
	if (OpenWidget)
	{
		OpenWidget->RemoveFromParent();
		OpenWidget = nullptr;
		if (APlayerController* Controller = OpenController.Get())
		{
			Controller->SetInputMode(FInputModeGameOnly());
			Controller->SetShowMouseCursor(false);
		}
		OpenController = nullptr;
		// A draft left on another page must not reappear on the next open.
		Session.Discard();
	}
}

bool USettingsMenuSubsystem::IsSettingsOpen() const
{
	return OpenWidget != nullptr;
}
