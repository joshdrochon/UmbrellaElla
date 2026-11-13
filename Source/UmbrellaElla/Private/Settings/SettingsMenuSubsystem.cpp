#include "Settings/SettingsMenuSubsystem.h"
#include "EnhancedInputSubsystems.h"
#include "Core/UmbrellaTuning.h"
#include "Engine/GameInstance.h"
#include "Engine/GameViewportClient.h"
#include "Feedback/Ui/UiArtSubsystem.h"
#include "Engine/LocalPlayer.h"
#include "Engine/World.h"
#include "Feedback/Vfx/UmbrellaVfxSubsystem.h"
#include "Flow/UmbrellaPlayerController.h"
#include "GameFramework/Pawn.h"
#include "GameFramework/PlayerController.h"
#include "Harness/UmbrellaFeatureFlags.h"
#include "Input/EllaInputAdapterComponent.h"
#include "InputAction.h"
#include "InputMappingContext.h"
#include "InputModifiers.h"
#include "Settings/DeveloperOptions.h"
#include "Settings/SettingsStore.h"
#include "Settings/UmbrellaAccessibility.h"
#include "Sound/SoundClass.h"
#include "UI/Progression/XpRingWidget.h"
#include "UI/Settings/SettingsMenuWidget.h"
#include "UObject/UObjectIterator.h"

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
	if (IsFeatureEnabled(EFeatureId::FLOW_44))
	{
		// The pause and title menus belong to the player controller, which knows the mode; follow it every frame so
		// developer options never reach a Start Game run.
		PlayModeTicker = FTSTicker::GetCoreTicker().AddTicker(FTickerDelegate::CreateWeakLambda(this, [this](float)
		{
			SyncPlayModeFromPlayer();
			return true;
		}));
	}
	if (IsFeatureEnabled(EFeatureId::FLOW_43))
	{
		ReloadFromStore();
		ApplyVolumes(Session.GetSaved());
		// Reduced flash follows the saved value in every world that starts, and in the one already running.
		WorldInitHandle = FWorldDelegates::OnPostWorldInitialization.AddWeakLambda(this, [this](UWorld* World, const UWorld::InitializationValues)
		{
			HandleWorldInit(World);
		});
		ApplyReducedFlash();
	}
}

void USettingsMenuSubsystem::HandleWorldInit(UWorld* World)
{
	if (World && World->GetGameInstance() == GetGameInstance())
	{
		ApplyReducedFlashToWorld(World, Session.GetSaved());
	}
}

void USettingsMenuSubsystem::ApplyReducedFlash()
{
	const FUmbrellaSettingsData& SavedNow = Session.GetSaved();
	UmbrellaAccessibility::PublishSaved(SavedNow.TextScalePercent, SavedNow.bReducedMotion);
	const UGameInstance* GameInstance = GetGameInstance();
	ApplyReducedFlashToWorld(GameInstance ? GameInstance->GetWorld() : nullptr, Session.GetSaved());
}

void USettingsMenuSubsystem::ApplyReducedFlashToWorld(UWorld* World, const FUmbrellaSettingsData& Data)
{
	UUmbrellaVfxSubsystem* Vfx = World ? World->GetSubsystem<UUmbrellaVfxSubsystem>() : nullptr;
	if (Vfx && IsFeatureEnabled(EFeatureId::VFX_10))
	{
		Vfx->SetReducedFlash(Data.bReducedFlash);
	}
}

void USettingsMenuSubsystem::Deinitialize()
{
	FWorldDelegates::OnPostWorldInitialization.Remove(WorldInitHandle);
	FTSTicker::GetCoreTicker().RemoveTicker(PlayModeTicker);
#if UMBRELLAELLA_WORKBENCH
	RestoreBaselineTuning();
#endif
	CloseSettings();
	UmbrellaAccessibility::ResetPublished();
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
	if (PlayMode == Mode)
	{
		return;
	}
	PlayMode = Mode;
	RefreshLiveTuning();
}

void USettingsMenuSubsystem::SyncPlayModeFromPlayer()
{
	const UGameInstance* GameInstance = GetGameInstance();
	const AUmbrellaPlayerController* Controller = GameInstance ? Cast<AUmbrellaPlayerController>(GameInstance->GetFirstLocalPlayerController()) : nullptr;
	if (Controller)
	{
		SetPlayMode(Controller->GetPlayMode());
	}
}

bool USettingsMenuSubsystem::IsDeveloperTuningActive() const
{
	return DeveloperOptionRules::CanEdit(PlayMode, bWorkbenchBuild);
}

int32 USettingsMenuSubsystem::GetDeveloperOption(EDeveloperOption Option) const
{
	const int32 Default = DeveloperOptionRules::SpecFor(Option).Default;
	if (!IsDeveloperTuningActive())
	{
		return Default;
	}
	return DeveloperOptionRules::ValueOf(Session.GetSaved().DeveloperValues, Option);
}

void USettingsMenuSubsystem::GetBaselineLifeCounts(int32& OutRetryLives, int32& OutHitsPerLife) const
{
#if UMBRELLAELLA_WORKBENCH
	const FSettingsLiveTuning Baseline = bLiveTuningApplied ? BaselineTuning : FSettingsLiveTuning::ReadFrom(GetDefault<UUmbrellaTuning>());
	OutRetryLives = Baseline.Encounter.RetryLives;
	OutHitsPerLife = FMath::RoundToInt(Baseline.Health.HitsPerLife);
#else
	const UUmbrellaTuning* Tuning = GetDefault<UUmbrellaTuning>();
	OutRetryLives = Tuning->Encounter.RetryLives;
	OutHitsPerLife = FMath::RoundToInt(Tuning->Health.HitsPerLife);
#endif
}

void USettingsMenuSubsystem::RefreshLiveTuning()
{
#if UMBRELLAELLA_WORKBENCH
	// Developer options only, workbench builds only (reduced motion is read through UmbrellaAccessibility, not written here): a composed copy goes into the live tuning object. The submission never writes the
	// tuning class default (the // bake: defaults are the shipped values), so there the options stay read-only.
	const FUmbrellaSettingsData& Saved = Session.GetSaved();
	const bool bDeveloper = IsDeveloperTuningActive() && !DeveloperOptionRules::IsAllDefault(Saved.DeveloperValues);
	if (!bDeveloper)
	{
		RestoreBaselineTuning();
		ApplyReducedMotionToRings();
		return;
	}
	UUmbrellaTuning* Live = GetMutableDefault<UUmbrellaTuning>();
	if (!bLiveTuningApplied)
	{
		// Capture "as tuned" once, before the first write; every later write composes from it.
		BaselineTuning = FSettingsLiveTuning::ReadFrom(Live);
	}
	FSettingsLiveTuning Composed = BaselineTuning;
	if (bDeveloper)
	{
		DeveloperOptionRules::Apply(Saved.DeveloperValues, Composed);
	}
	Composed.WriteTo(Live);
	bLiveTuningApplied = true;
#endif
	ApplyReducedMotionToRings();
}

#if UMBRELLAELLA_WORKBENCH
void USettingsMenuSubsystem::RestoreBaselineTuning()
{
	if (bLiveTuningApplied)
	{
		BaselineTuning.WriteTo(GetMutableDefault<UUmbrellaTuning>());
		bLiveTuningApplied = false;
	}
}
#endif

void USettingsMenuSubsystem::ApplyReducedMotionToRings()
{
	if (!IsFeatureEnabled(EFeatureId::FLOW_45))
	{
		return;
	}
	const bool bReduced = Session.GetSaved().bReducedMotion;
	const UGameInstance* GameInstance = GetGameInstance();
	for (TObjectIterator<UXpRingWidget> It; It; ++It)
	{
		const UWorld* RingWorld = It->GetWorld();
		if (GameInstance && RingWorld && RingWorld->GetGameInstance() == GameInstance)
		{
			It->SetReducedMotion(bReduced);
		}
	}
}

void USettingsMenuSubsystem::ReloadFromStore()
{
	FUmbrellaSettingsData Loaded;
	SettingsStore::Read(StorePath, Loaded);
	Session = FSettingsSession(Loaded);
	UmbrellaAccessibility::PublishSaved(Loaded.TextScalePercent, Loaded.bReducedMotion);
	// Developer options are never in the file, so a reload also returns the live tuning to "as tuned".
	RefreshLiveTuning();
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
	ApplyReducedFlash();
	RefreshLiveTuning();
	const ESettingsResult Result = SettingsStore::Write(StorePath, Session.GetSaved());
	SettingsSavedEvent.Broadcast();
	return Result;
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
	// The controller knows the mode (Game Options exists only in Director's Cut).
	if (const AUmbrellaPlayerController* UmbrellaController = Cast<AUmbrellaPlayerController>(Controller))
	{
		SetPlayMode(UmbrellaController->GetPlayMode());
	}
	OpenWidget = CreateWidget<USettingsMenuWidget>(Controller, USettingsMenuWidget::StaticClass());
	if (OpenWidget)
	{
		OpenWidget->Setup(this, PlayMode);
		// Same layer as the flow menus (viewport overlay), above them and their art, so Settings is what the player sees.
		OpenSlate = OpenWidget->TakeWidget();
		if (UGameViewportClient* Viewport = FindViewport(Controller))
		{
			Viewport->AddViewportWidgetContent(OpenSlate.ToSharedRef(), SettingsLayer::ZOrder());
			OpenViewport = Viewport;
		}
		Controller->SetShowMouseCursor(true);
		FInputModeUIOnly InputMode;
		InputMode.SetWidgetToFocus(OpenSlate);
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
		if (UGameViewportClient* Viewport = OpenViewport.Get(); Viewport && OpenSlate.IsValid())
		{
			Viewport->RemoveViewportWidgetContent(OpenSlate.ToSharedRef());
		}
		OpenViewport.Reset();
		OpenSlate.Reset();
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

int32 SettingsLayer::ZOrder()
{
	return GetDefault<UUmbrellaTuning>()->Flow.MenuContextPriority + UmbrellaUiArtConst::ZOrderAboveMenu + AboveMenuArt;
}

void USettingsMenuSubsystem::SetViewportForTests(UGameViewportClient* Viewport)
{
	TestViewport = Viewport;
}

UGameViewportClient* USettingsMenuSubsystem::FindViewport(const APlayerController* Controller) const
{
	if (UGameViewportClient* Viewport = TestViewport.Get())
	{
		return Viewport;
	}
	const UWorld* World = Controller ? Controller->GetWorld() : nullptr;
	return World ? World->GetGameViewport() : nullptr;
}

bool USettingsMenuSubsystem::IsSettingsOpen() const
{
	return OpenWidget != nullptr;
}
