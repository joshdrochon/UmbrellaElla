#include "Misc/AutomationTest.h"

#if WITH_AUTOMATION_TESTS

#include "Core/UmbrellaPlayMode.h"
#include "Engine/Engine.h"
#include "Engine/GameInstance.h"
#include "InputAction.h"
#include "InputMappingContext.h"
#include "InputModifiers.h"
#include "Misc/Paths.h"
#include "HAL/FileManager.h"
#include "UObject/Package.h"
#include "HAL/FileManager.h"
#include "Settings/SettingsConstants.h"
#include "Settings/SettingsMenuSubsystem.h"
#include "Settings/SettingsModel.h"
#include "Settings/SettingsStore.h"
#include "Sound/SoundClass.h"
#include "UI/Settings/SettingsMenuWidget.h"
#include "Core/EllaCharacter.h"
#include "EnhancedInputComponent.h"
#include "Engine/World.h"
#include "Feedback/Vfx/UmbrellaVfxSubsystem.h"
#include "Input/EllaInputAdapterComponent.h"
#include "Tests/Shared/UmbrellaTestWorld.h"

namespace
{
	const EAutomationTestFlags SettingsFlags = EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter;

	/** A scratch file under Saved/UmbrellaEllaTests that the test deletes. */
	FString ScratchPath(const TCHAR* Name)
	{
		return FPaths::Combine(FPaths::ProjectSavedDir(), TEXT("UmbrellaEllaTests"), TEXT("Settings"), Name);
	}

	/** A subsystem made without a game instance, pointed at a scratch file and transient sound classes. */
	USettingsMenuSubsystem* MakeSubsystem(const FString& Path, USoundClass*& Master, USoundClass*& Sfx, USoundClass*& Music)
	{
		USettingsMenuSubsystem* Subsystem = NewObject<USettingsMenuSubsystem>(NewObject<UGameInstance>(GEngine));
		Master = NewObject<USoundClass>(GetTransientPackage());
		Sfx = NewObject<USoundClass>(GetTransientPackage());
		Music = NewObject<USoundClass>(GetTransientPackage());
		Subsystem->SetSoundClasses(Master, Sfx, Music);
		Subsystem->SetStorePath(Path);
		Subsystem->ReloadFromStore();
		return Subsystem;
	}
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FSettingsDefaultsTest, "UmbrellaElla.Settings.Defaults", SettingsFlags)
bool FSettingsDefaultsTest::RunTest(const FString& Parameters)
{
	const FUmbrellaSettingsData Defaults = SettingsRules::MakeDefaults();
	TestEqual(TEXT("master default"), Defaults.MasterVolume, SettingsConstants::DefaultVolume);
	TestEqual(TEXT("slider max is 100"), SettingsConstants::SliderMax, 100);
	TestTrue(TEXT("default bindings are the input defaults"), Defaults.Bindings.Num() == UmbrellaInputBindings::BuildDefaults().Num() && Defaults.Bindings.Num() > 0);
	TestFalse(TEXT("fresh session is clean"), FSettingsSession().IsDirty());
	TestFalse(TEXT("default Shoot and Absorb do not conflict"), SettingsRules::HasShootAbsorbConflict(Defaults.Bindings));
	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FSettingsPagesTest, "UmbrellaElla.Settings.PagesByMode", SettingsFlags)
bool FSettingsPagesTest::RunTest(const FString& Parameters)
{
	const TArray<ESettingsPage> Start = SettingsRules::GetPages(EUmbrellaPlayMode::StartGame);
	TestEqual(TEXT("Start Game page count"), Start.Num(), 3);
	TestFalse(TEXT("no Game Options in Start Game"), Start.Contains(ESettingsPage::GameOptions));
	TestFalse(TEXT("Game Options unavailable in Start Game"), SettingsRules::IsPageAvailable(ESettingsPage::GameOptions, EUmbrellaPlayMode::StartGame));
	TestEqual(TEXT("no developer options in Start Game"), SettingsRules::GetDeveloperOptionNames(EUmbrellaPlayMode::StartGame).Num(), 0);

	const TArray<ESettingsPage> Director = SettingsRules::GetPages(EUmbrellaPlayMode::DirectorsCut);
	TestEqual(TEXT("Director's Cut page count"), Director.Num(), 4);
	TestTrue(TEXT("Game Options in Director's Cut"), Director.Contains(ESettingsPage::GameOptions));
	TestEqual(TEXT("developer candidates in Director's Cut"), SettingsRules::GetDeveloperOptionNames(EUmbrellaPlayMode::DirectorsCut).Num(), 20);
	for (const ESettingsPage Page : {ESettingsPage::Sound, ESettingsPage::Controller, ESettingsPage::Credits})
	{
		TestTrue(TEXT("player page in Start Game"), SettingsRules::IsPageAvailable(Page, EUmbrellaPlayMode::StartGame));
		TestTrue(TEXT("player page in Director's Cut"), SettingsRules::IsPageAvailable(Page, EUmbrellaPlayMode::DirectorsCut));
	}
	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FSettingsSlidersTest, "UmbrellaElla.Settings.SliderRange", SettingsFlags)
bool FSettingsSlidersTest::RunTest(const FString& Parameters)
{
	FSettingsSession Session;
	Session.SetMasterVolume(250);
	Session.SetSfxVolume(-10);
	Session.SetMusicVolume(40);
	TestEqual(TEXT("master clamps to 100"), Session.GetDraft().MasterVolume, 100);
	TestEqual(TEXT("sfx clamps to 0"), Session.GetDraft().SfxVolume, 0);
	TestEqual(TEXT("music keeps 40"), Session.GetDraft().MusicVolume, 40);
	TestEqual(TEXT("40 is 0.4 of the class"), SettingsRules::VolumeToClassScale(40), 0.4f);
	Session.SetTextScalePercent(50);
	TestEqual(TEXT("text scale floor"), Session.GetDraft().TextScalePercent, 100);
	Session.SetTextScalePercent(900);
	TestEqual(TEXT("text scale ceiling"), Session.GetDraft().TextScalePercent, 200);
	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FSettingsRemapTest, "UmbrellaElla.Settings.RemapChangesDraftKey", SettingsFlags)
bool FSettingsRemapTest::RunTest(const FString& Parameters)
{
	FSettingsSession Session;
	const int32 Index = SettingsRules::FindBindingIndex(Session.GetDraft().Bindings, EUmbrellaInputAction::Shoot, 0);
	TestTrue(TEXT("Shoot has a first binding"), Index != INDEX_NONE);
	TestTrue(TEXT("can remap"), Session.CanRemap(EUmbrellaInputAction::Shoot, 0, EKeys::F));
	TestFalse(TEXT("cannot remap a missing slot"), Session.CanRemap(EUmbrellaInputAction::Shoot, 99, EKeys::F));
	TestFalse(TEXT("cannot remap to an invalid key"), Session.CanRemap(EUmbrellaInputAction::Shoot, 0, FKey()));
	Session.Remap(EUmbrellaInputAction::Shoot, 0, EKeys::F);
	TestEqual(TEXT("draft key changed"), Session.GetDraft().Bindings[Index].Key, EKeys::F);
	TestNotEqual(TEXT("saved key unchanged"), Session.GetSaved().Bindings[Index].Key, EKeys::F);
	TestTrue(TEXT("remap makes the Controller page dirty"), Session.IsPageDirty(ESettingsPage::Controller));
	TestFalse(TEXT("Sound page stays clean"), Session.IsPageDirty(ESettingsPage::Sound));
	TestEqual(TEXT("instructions follow the remap"), SettingsRules::FirstKeyLabel(Session.GetDraft().Bindings, EUmbrellaInputAction::Shoot), SettingsRules::KeyLabel(EKeys::F));
	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FSettingsBackTest, "UmbrellaElla.Settings.BackDiscardsUnsaved", SettingsFlags)
bool FSettingsBackTest::RunTest(const FString& Parameters)
{
	FSettingsSession Session;
	TestEqual(TEXT("clean Back closes"), Session.RequestBack(ESettingsPage::Sound), ESettingsBackResult::Close);
	Session.SetMasterVolume(10);
	Session.Remap(EUmbrellaInputAction::Absorb, 0, EKeys::L);
	TestEqual(TEXT("dirty Back asks"), Session.RequestBack(ESettingsPage::Sound), ESettingsBackResult::AskSaveDiscardKeep);

	TestEqual(TEXT("Keep Editing stays"), Session.ResolveBack(ESettingsPage::Sound, ESettingsBackChoice::KeepEditing), ESettingsBackOutcome::StayOpen);
	TestEqual(TEXT("draft survives Keep Editing"), Session.GetDraft().MasterVolume, 10);

	TestEqual(TEXT("Discard closes"), Session.ResolveBack(ESettingsPage::Sound, ESettingsBackChoice::Discard), ESettingsBackOutcome::CloseMenu);
	TestEqual(TEXT("Discard restores the sound page"), Session.GetDraft().MasterVolume, SettingsConstants::DefaultVolume);
	TestTrue(TEXT("Discard on the Sound page leaves the Controller draft"), Session.IsPageDirty(ESettingsPage::Controller));
	Session.Discard();
	TestFalse(TEXT("full discard is clean"), Session.IsDirty());
	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FSettingsSaveScopeTest, "UmbrellaElla.Settings.SaveAppliesCurrentPage", SettingsFlags)
bool FSettingsSaveScopeTest::RunTest(const FString& Parameters)
{
	FSettingsSession Session;
	Session.SetMusicVolume(30);
	Session.Remap(EUmbrellaInputAction::Hop, 0, EKeys::H);
	Session.SavePage(ESettingsPage::Sound);
	TestEqual(TEXT("Sound page saved"), Session.GetSaved().MusicVolume, 30);
	TestFalse(TEXT("Sound page clean after save"), Session.IsPageDirty(ESettingsPage::Sound));
	TestTrue(TEXT("Controller page still unsaved"), Session.IsPageDirty(ESettingsPage::Controller));
	// Reset is a settings reset only: it never reaches the saved copy until Save.
	Session.ResetToDefaults();
	TestEqual(TEXT("reset changes the draft"), Session.GetDraft().MusicVolume, SettingsConstants::DefaultVolume);
	TestEqual(TEXT("reset leaves the saved copy"), Session.GetSaved().MusicVolume, 30);
	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FSettingsConflictTest, "UmbrellaElla.Settings.ShootAbsorbConflictRecovery", SettingsFlags)
bool FSettingsConflictTest::RunTest(const FString& Parameters)
{
	FSettingsSession Session;
	Session.Remap(EUmbrellaInputAction::Absorb, 0, EKeys::J);
	TestTrue(TEXT("shared key is flagged"), SettingsRules::HasShootAbsorbConflict(Session.GetDraft().Bindings));
	Session.ResetBindings();
	TestFalse(TEXT("reset bindings recovers"), SettingsRules::HasShootAbsorbConflict(Session.GetDraft().Bindings));
	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FSettingsCreditsTest, "UmbrellaElla.Settings.Credits", SettingsFlags)
bool FSettingsCreditsTest::RunTest(const FString& Parameters)
{
	const TArray<FSettingsCreditLine> Credits = SettingsRules::GetCredits();
	TestEqual(TEXT("four credit lines"), Credits.Num(), 4);
	bool bFoundJosh = false;
	for (const FSettingsCreditLine& Line : Credits)
	{
		bFoundJosh = bFoundJosh || (Line.Name == TEXT("Josh Rochon") && Line.Role == TEXT("Technical Lead"));
	}
	TestTrue(TEXT("Josh Rochon, Technical Lead"), bFoundJosh);
	TestTrue(TEXT("Rick's role is still open"), Credits[0].Name == TEXT("Rick Rispoli") && Credits[0].Role.IsEmpty());
	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FSettingsPersistTest, "UmbrellaElla.Settings.SavePersistsRemap", SettingsFlags)
bool FSettingsPersistTest::RunTest(const FString& Parameters)
{
	const FString Path = ScratchPath(TEXT("persist.ini"));
	SettingsStore::Delete(Path);
	USoundClass* Master = nullptr;
	USoundClass* Sfx = nullptr;
	USoundClass* Music = nullptr;
	USettingsMenuSubsystem* First = MakeSubsystem(Path, Master, Sfx, Music);
	First->EditSession().Remap(EUmbrellaInputAction::Shoot, 0, EKeys::F);
	First->EditSession().SetMusicVolume(35);
	TestEqual(TEXT("controller save ok"), First->SaveSettings(ESettingsPage::Controller), ESettingsResult::Ok);
	TestEqual(TEXT("sound save ok"), First->SaveSettings(ESettingsPage::Sound), ESettingsResult::Ok);

	USettingsMenuSubsystem* Second = MakeSubsystem(Path, Master, Sfx, Music);
	const FUmbrellaSettingsData& Loaded = Second->GetSession().GetSaved();
	const int32 Index = SettingsRules::FindBindingIndex(Loaded.Bindings, EUmbrellaInputAction::Shoot, 0);
	TestTrue(TEXT("binding slot exists"), Index != INDEX_NONE);
	if (Index != INDEX_NONE)
	{
		TestEqual(TEXT("remapped key survives a reload"), Loaded.Bindings[Index].Key, EKeys::F);
	}
	TestEqual(TEXT("music volume survives a reload"), Loaded.MusicVolume, 35);
	TestEqual(TEXT("binding count unchanged"), Loaded.Bindings.Num(), UmbrellaInputBindings::BuildDefaults().Num());
	TestTrue(TEXT("negative-scale binding keeps its sign"), FSettingsSession(Loaded).GetSaved() == Loaded);
	SettingsStore::Delete(Path);
	TestFalse(TEXT("scratch file deleted"), IFileManager::Get().FileExists(*Path));
	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FSettingsVolumeTest, "UmbrellaElla.Settings.SlidersSetClassVolume", SettingsFlags)
bool FSettingsVolumeTest::RunTest(const FString& Parameters)
{
	const FString Path = ScratchPath(TEXT("volume.ini"));
	SettingsStore::Delete(Path);
	USoundClass* Master = nullptr;
	USoundClass* Sfx = nullptr;
	USoundClass* Music = nullptr;
	USettingsMenuSubsystem* Subsystem = MakeSubsystem(Path, Master, Sfx, Music);
	Subsystem->EditSession().SetMasterVolume(40);
	Subsystem->EditSession().SetSfxVolume(25);
	Subsystem->EditSession().SetMusicVolume(70);
	Subsystem->SaveSettings(ESettingsPage::Sound);
	TestEqual(TEXT("master class volume"), Master->Properties.Volume, 0.4f);
	TestEqual(TEXT("sfx class volume"), Sfx->Properties.Volume, 0.25f);
	TestEqual(TEXT("music class volume"), Music->Properties.Volume, 0.7f);

	// An unsaved slider move and a Discard leave the class volume at the saved value.
	Subsystem->EditSession().SetMasterVolume(90);
	Subsystem->DiscardChanges(ESettingsPage::Sound);
	TestEqual(TEXT("discard keeps the saved master volume"), Master->Properties.Volume, 0.4f);
	TestEqual(TEXT("discard resets the draft"), Subsystem->GetSession().GetDraft().MasterVolume, 40);
	SettingsStore::Delete(Path);
	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FSettingsApplyContextTest, "UmbrellaElla.Settings.RemapRebuildsMappingContext", SettingsFlags)
bool FSettingsApplyContextTest::RunTest(const FString& Parameters)
{
	UInputMappingContext* Context = NewObject<UInputMappingContext>(GetTransientPackage());
	for (int32 Index = 0; Index < static_cast<int32>(EUmbrellaInputAction::Count); ++Index)
	{
		const EUmbrellaInputAction Id = static_cast<EUmbrellaInputAction>(Index);
		UInputAction* Action = NewObject<UInputAction>(Context, UmbrellaInputBindings::ActionName(Id));
		Action->ValueType = UmbrellaInputBindings::IsAxisAction(Id) ? EInputActionValueType::Axis1D : EInputActionValueType::Boolean;
		for (const FUmbrellaDefaultBinding& Binding : UmbrellaInputBindings::BuildDefaults())
		{
			if (Binding.Action == Id)
			{
				Context->MapKey(Action, Binding.Key);
			}
		}
	}
	FUmbrellaSettingsData Data = SettingsRules::MakeDefaults();
	const int32 Index = SettingsRules::FindBindingIndex(Data.Bindings, EUmbrellaInputAction::Shoot, 0);
	const FKey Old = Data.Bindings[Index].Key;
	Data.Bindings[Index].Key = EKeys::F;
	const int32 Made = USettingsMenuSubsystem::ApplyBindingsToContext(Context, Data);
	TestEqual(TEXT("every binding mapped"), Made, Data.Bindings.Num());

	bool bHasNew = false;
	bool bHasOld = false;
	int32 Negated = 0;
	for (const FEnhancedActionKeyMapping& Mapping : Context->GetMappings())
	{
		if (Mapping.Action && Mapping.Action->GetFName() == UmbrellaInputBindings::ActionName(EUmbrellaInputAction::Shoot))
		{
			bHasNew = bHasNew || Mapping.Key == EKeys::F;
			bHasOld = bHasOld || Mapping.Key == Old;
		}
		for (const UInputModifier* Modifier : Mapping.Modifiers)
		{
			Negated += Modifier && Modifier->IsA<UInputModifierNegate>() ? 1 : 0;
		}
	}
	TestTrue(TEXT("Shoot now has the new key"), bHasNew);
	TestFalse(TEXT("Shoot lost the old key"), bHasOld);
	int32 ExpectedNegated = 0;
	for (const FUmbrellaDefaultBinding& Binding : Data.Bindings)
	{
		ExpectedNegated += Binding.Scale < 0.0f ? 1 : 0;
	}
	TestEqual(TEXT("negative-scale keys keep their Negate modifier"), Negated, ExpectedNegated);
	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FSettingsWidgetBackTest, "UmbrellaElla.Settings.WidgetBackAndPages", SettingsFlags)
bool FSettingsWidgetBackTest::RunTest(const FString& Parameters)
{
	const FString Path = ScratchPath(TEXT("widget.ini"));
	SettingsStore::Delete(Path);
	USoundClass* Master = nullptr;
	USoundClass* Sfx = nullptr;
	USoundClass* Music = nullptr;
	USettingsMenuSubsystem* Subsystem = MakeSubsystem(Path, Master, Sfx, Music);

	USettingsMenuWidget* Widget = NewObject<USettingsMenuWidget>(GetTransientPackage());
	Widget->Setup(Subsystem, EUmbrellaPlayMode::StartGame);
	Widget->ShowPage(ESettingsPage::GameOptions);
	TestNotEqual(TEXT("Game Options refused in Start Game"), Widget->GetPage(), ESettingsPage::GameOptions);
	Widget->ShowPage(ESettingsPage::Controller);
	TestEqual(TEXT("Controller page opens"), Widget->GetPage(), ESettingsPage::Controller);

	Widget->BeginRemap(EUmbrellaInputAction::Shoot, 0);
	TestTrue(TEXT("waiting for a key"), Widget->IsCapturingKey());
	Widget->CaptureKey(EKeys::G);
	TestFalse(TEXT("capture done"), Widget->IsCapturingKey());
	const int32 Index = SettingsRules::FindBindingIndex(Subsystem->GetSession().GetDraft().Bindings, EUmbrellaInputAction::Shoot, 0);
	TestEqual(TEXT("captured key lands in the draft"), Subsystem->GetSession().GetDraft().Bindings[Index].Key, EKeys::G);

	Widget->BeginRemap(EUmbrellaInputAction::Shoot, 0);
	const FPointerEvent LeftClick(0, 0, FVector2D::ZeroVector, FVector2D::ZeroVector, TSet<FKey>(), EKeys::LeftMouseButton, 0, FModifierKeysState());
	const FReply Preview = Widget->NativeOnPreviewMouseButtonDown(FGeometry(), LeftClick);
	TestTrue(TEXT("preview click is handled while capturing"), Preview.IsEventHandled());
	TestFalse(TEXT("left mouse ends the capture"), Widget->IsCapturingKey());
	TestEqual(TEXT("left mouse lands in the draft"), Subsystem->GetSession().GetDraft().Bindings[Index].Key, EKeys::LeftMouseButton);

	Widget->PressBack();
	TestTrue(TEXT("dirty Back shows the prompt"), Widget->IsBackPromptShown());
	Widget->ChooseBack(ESettingsBackChoice::KeepEditing);
	TestFalse(TEXT("Keep Editing hides the prompt"), Widget->IsBackPromptShown());
	TestTrue(TEXT("Keep Editing keeps the draft"), Subsystem->GetSession().IsPageDirty(ESettingsPage::Controller));
	Widget->PressBack();
	Widget->ChooseBack(ESettingsBackChoice::Discard);
	TestFalse(TEXT("Back then Discard drops the change"), Subsystem->GetSession().IsDirty());

	Widget->BeginRemap(EUmbrellaInputAction::Shoot, 0);
	Widget->CaptureKey(EKeys::Escape);
	TestFalse(TEXT("Escape cancels a remap"), Subsystem->GetSession().IsDirty());
	SettingsStore::Delete(Path);
	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FSettingsReducedFlashTest, "UmbrellaElla.Settings.World.ReducedFlashReachesVfx", SettingsFlags)
bool FSettingsReducedFlashTest::RunTest(const FString& Parameters)
{
	const FString Path = ScratchPath(TEXT("flash.ini"));
	SettingsStore::Delete(Path);
	USoundClass* Master = nullptr;
	USoundClass* Sfx = nullptr;
	USoundClass* Music = nullptr;
	USettingsMenuSubsystem* Subsystem = MakeSubsystem(Path, Master, Sfx, Music);
	FUmbrellaTestWorld TestWorld;
	UWorld* World = TestWorld.GetWorld();
	UUmbrellaVfxSubsystem* Vfx = World ? World->GetSubsystem<UUmbrellaVfxSubsystem>() : nullptr;
	if (!TestNotNull(TEXT("world has the Vfx subsystem"), Vfx))
	{
		return false;
	}
	TestFalse(TEXT("reduced flash defaults off"), Subsystem->GetSession().GetSaved().bReducedFlash);
	Subsystem->EditSession().SetReducedFlash(true);
	TestFalse(TEXT("draft change does not reach Vfx before Save"), Vfx->IsReducedFlash());
	Subsystem->SaveSettings(ESettingsPage::Sound);
	TestTrue(TEXT("saved copy has reduced flash"), Subsystem->GetSession().GetSaved().bReducedFlash);
	TestTrue(TEXT("the saved value applies to a world"), USettingsMenuSubsystem::ApplyReducedFlashToWorld(World, Subsystem->GetSession().GetSaved().bReducedFlash));
	TestTrue(TEXT("Vfx is reduced after apply"), Vfx->IsReducedFlash());

	// Startup: a fresh subsystem reading the file gets the saved value.
	USettingsMenuSubsystem* Fresh = MakeSubsystem(Path, Master, Sfx, Music);
	TestTrue(TEXT("saved value survives a reload"), Fresh->GetSession().GetSaved().bReducedFlash);
	Vfx->SetReducedFlash(false);
	USettingsMenuSubsystem::ApplyReducedFlashToWorld(World, Fresh->GetSession().GetSaved().bReducedFlash);
	TestTrue(TEXT("startup applies the saved value"), Vfx->IsReducedFlash());
	SettingsStore::Delete(Path);
	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FSettingsSavedKeyLiveTest, "UmbrellaElla.Settings.World.SavedBindingReachesLiveContext", SettingsFlags)
bool FSettingsSavedKeyLiveTest::RunTest(const FString& Parameters)
{
	const FString Path = ScratchPath(TEXT("live.ini"));
	SettingsStore::Delete(Path);
	UGameInstance* GameInstance = NewObject<UGameInstance>(GEngine);
	GameInstance->InitializeStandalone();
	USettingsMenuSubsystem* Subsystem = GameInstance->GetSubsystem<USettingsMenuSubsystem>();
	if (!TestNotNull(TEXT("game instance owns the settings subsystem"), Subsystem))
	{
		return false;
	}
	Subsystem->SetStorePath(Path);
	Subsystem->ReloadFromStore();
	Subsystem->EditSession().Remap(EUmbrellaInputAction::Shoot, 0, EKeys::F);
	Subsystem->SaveSettings(ESettingsPage::Controller);

	FUmbrellaTestWorld TestWorld;
	UWorld* World = TestWorld.GetWorld();
	AEllaCharacter* Ella = World ? TestWorld.SpawnElla() : nullptr;
	if (!TestNotNull(TEXT("Ella spawned"), Ella))
	{
		SettingsStore::Delete(Path);
		return false;
	}
	World->SetGameInstance(GameInstance);
	// Respawn path: BindInput builds a fresh IMC_Default and applies the saved keys.
	Ella->GetInputAdapter()->BindInput(NewObject<UEnhancedInputComponent>(Ella));
	const UInputMappingContext* Context = Ella->GetInputAdapter()->GetMappingContext();
	bool bShootOnF = false;
	bool bShootOnOld = false;
	const FKey OldKey = SettingsRules::MakeDefaults().Bindings[SettingsRules::FindBindingIndex(SettingsRules::MakeDefaults().Bindings, EUmbrellaInputAction::Shoot, 0)].Key;
	if (TestNotNull(TEXT("Ella has a mapping context"), Context))
	{
		for (const FEnhancedActionKeyMapping& Mapping : Context->GetMappings())
		{
			if (Mapping.Action && Mapping.Action->GetFName() == UmbrellaInputBindings::ActionName(EUmbrellaInputAction::Shoot))
			{
				bShootOnF |= Mapping.Key == EKeys::F;
				bShootOnOld |= Mapping.Key == OldKey;
			}
		}
	}
	TestTrue(TEXT("saved Shoot key is live after respawn"), bShootOnF);
	TestFalse(TEXT("the old Shoot key is gone"), bShootOnOld);
	SettingsStore::Delete(Path);
	return true;
}

#endif
