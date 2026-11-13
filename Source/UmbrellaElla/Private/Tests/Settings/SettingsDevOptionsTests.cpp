#include "Misc/AutomationTest.h"

#if WITH_AUTOMATION_TESTS

#include "Core/UmbrellaPlayMode.h"
#include "Core/UmbrellaTuning.h"
#include "Engine/Engine.h"
#include "Engine/GameInstance.h"
#include "Engine/World.h"
#include "Misc/Paths.h"
#include "Settings/DeveloperOptions.h"
#include "Settings/SettingsConstants.h"
#if UMBRELLAELLA_WORKBENCH
#include "Settings/SettingsLiveTuning.h"
#endif
#include "Settings/SettingsMenuSubsystem.h"
#include "Settings/SettingsModel.h"
#include "Settings/SettingsStore.h"
#include "Settings/UmbrellaAccessibility.h"
#include "Sound/SoundClass.h"
#include "Tests/Shared/UmbrellaTestWorld.h"
#include "UI/Settings/SettingsMenuWidget.h"
#include "UObject/Package.h"

namespace
{
	const EAutomationTestFlags SettingsDevFlags = EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter;

	FString SettingsDevScratchPath(const TCHAR* Name)
	{
		return FPaths::Combine(FPaths::ProjectSavedDir(), TEXT("UmbrellaEllaTests"), TEXT("Settings"), Name);
	}

	/** A subsystem made without a game instance (no Initialize), on a scratch file and transient sound classes. */
	USettingsMenuSubsystem* MakeSettingsDevSubsystem(const FString& Path)
	{
		USettingsMenuSubsystem* Subsystem = NewObject<USettingsMenuSubsystem>(NewObject<UGameInstance>(GEngine));
		Subsystem->SetSoundClasses(NewObject<USoundClass>(GetTransientPackage()), NewObject<USoundClass>(GetTransientPackage()),
			NewObject<USoundClass>(GetTransientPackage()));
		Subsystem->SetStorePath(Path);
		Subsystem->ReloadFromStore();
		return Subsystem;
	}

	/** Back to as-tuned: Start Game mode and a reload drop every developer value and restore the baseline. */
	void ResetSettingsDevSubsystem(USettingsMenuSubsystem* Subsystem, const FString& Path)
	{
		Subsystem->EditSession().ResetToDefaults();
		Subsystem->SaveSettings(ESettingsPage::Sound);
		Subsystem->SaveSettings(ESettingsPage::GameOptions);
		Subsystem->SetPlayMode(EUmbrellaPlayMode::StartGame);
		SettingsStore::Delete(Path);
		Subsystem->ReloadFromStore();
	}
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FSettingsDevSpecsTest, "UmbrellaElla.Settings.DeveloperOptionsList", SettingsDevFlags)
bool FSettingsDevSpecsTest::RunTest(const FString& Parameters)
{
	const TArray<FDeveloperOptionSpec> Specs = DeveloperOptionRules::AllSpecs();
	TestEqual(TEXT("one option per GDD candidate"), Specs.Num(), static_cast<int32>(EDeveloperOption::Count));
	const TCHAR* GddOrder[] = {TEXT("EntryRetries"), TEXT("Movement"), TEXT("Hop"), TEXT("Dash"), TEXT("VoluntaryCurrents"),
		TEXT("HostileGusts"), TEXT("Missiles"), TEXT("Absorption"), TEXT("HealthGround"), TEXT("FourWeapons"),
		TEXT("ProgressionScarf"), TEXT("OwlParts"), TEXT("Clock"), TEXT("Stun"), TEXT("Slow"), TEXT("EyesBlackout"),
		TEXT("Tutorial"), TEXT("Remapping"), TEXT("SizeHitbox"), TEXT("Background")};
	for (int32 Index = 0; Index < Specs.Num() && Index < UE_ARRAY_COUNT(GddOrder); ++Index)
	{
		TestEqual(FString::Printf(TEXT("option %d is in GDD order"), Index), Specs[Index].Name, FName(GddOrder[Index]));
		TestEqual(FString::Printf(TEXT("option %d id matches its slot"), Index), static_cast<int32>(Specs[Index].Id), Index);
		TestFalse(FString::Printf(TEXT("option %d has a label"), Index), Specs[Index].Label.IsEmpty());
		TestFalse(TEXT("no ammunition or energy control"), Specs[Index].Name.ToString().Contains(TEXT("Ammo")) || Specs[Index].Name.ToString().Contains(TEXT("Energy")));
	}
	TestTrue(TEXT("defaults are as tuned"), DeveloperOptionRules::IsAllDefault(DeveloperOptionRules::MakeDefaultValues()));
	TestTrue(TEXT("an empty list counts as defaults"), DeveloperOptionRules::IsAllDefault(TArray<int32>()));
	TestEqual(TEXT("percent clamps to the top"), DeveloperOptionRules::ClampValue(EDeveloperOption::Movement, 999), DeveloperOptionLimits::PercentHigh);
	TestEqual(TEXT("percent clamps to the floor"), DeveloperOptionRules::ClampValue(EDeveloperOption::Movement, -50), DeveloperOptionLimits::PercentLow);
	TestEqual(TEXT("off-able options reach 0"), DeveloperOptionRules::ClampValue(EDeveloperOption::HostileGusts, -50), 0);
	TestEqual(TEXT("percent snaps to its step"), DeveloperOptionRules::ClampValue(EDeveloperOption::Hop, 152), 150);
	TestEqual(TEXT("toggle stays 0 or 1"), DeveloperOptionRules::ClampValue(EDeveloperOption::FourWeapons, 7), DeveloperOptionLimits::ToggleOn);
	TestEqual(TEXT("a link has no value of its own"), DeveloperOptionRules::ClampValue(EDeveloperOption::Remapping, 5), 0);
	return true;
}

#if UMBRELLAELLA_WORKBENCH
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FSettingsDevApplyTest, "UmbrellaElla.Settings.DeveloperOptionsApply", SettingsDevFlags)
bool FSettingsDevApplyTest::RunTest(const FString& Parameters)
{
	const FSettingsLiveTuning Base = FSettingsLiveTuning::ReadFrom(GetDefault<UUmbrellaTuning>());
	FSettingsLiveTuning Same = Base;
	DeveloperOptionRules::Apply(DeveloperOptionRules::MakeDefaultValues(), Same);
	TestEqual(TEXT("defaults leave movement as tuned"), Same.Motor.RiseSpeed, Base.Motor.RiseSpeed);
	TestEqual(TEXT("defaults leave the slow attack as tuned"), Same.Keeper.bSlowEnabled, Base.Keeper.bSlowEnabled);
	TestEqual(TEXT("defaults leave retries as tuned"), Same.Encounter.RetryLives, Base.Encounter.RetryLives);

	TArray<int32> Values = DeveloperOptionRules::MakeDefaultValues();
	auto Set = [&Values](EDeveloperOption Option, int32 Value) { Values[static_cast<int32>(Option)] = DeveloperOptionRules::ClampValue(Option, Value); };
	Set(EDeveloperOption::Movement, 150);
	Set(EDeveloperOption::Dash, 50);
	Set(EDeveloperOption::HostileGusts, 0);
	Set(EDeveloperOption::EntryRetries, 2);
	Set(EDeveloperOption::HealthGround, -2);
	Set(EDeveloperOption::FourWeapons, 1);
	Set(EDeveloperOption::Slow, 0);
	Set(EDeveloperOption::OwlParts, 200);
	Set(EDeveloperOption::SizeHitbox, 50);
	Set(EDeveloperOption::ProgressionScarf, 200);
	FSettingsLiveTuning Changed = Base;
	DeveloperOptionRules::Apply(Values, Changed);
	TestEqual(TEXT("movement 150% scales rise speed"), Changed.Motor.RiseSpeed, Base.Motor.RiseSpeed * 1.5f);
	TestEqual(TEXT("movement 150% scales horizontal speed"), Changed.Motor.HorizontalMaxSpeed, Base.Motor.HorizontalMaxSpeed * 1.5f);
	TestEqual(TEXT("dash 50% halves the distance"), Changed.Motor.DashDistance, Base.Motor.DashDistance * 0.5f);
	TestEqual(TEXT("hop untouched"), Changed.Motor.HopDistance, Base.Motor.HopDistance);
	TestEqual(TEXT("gusts 0% push nothing"), Changed.Keeper.GustPush, 0.0f);
	TestEqual(TEXT("gusts 0% deal no damage"), Changed.Keeper.GustDamage, 0.0f);
	TestEqual(TEXT("two more retries"), Changed.Encounter.RetryLives, Base.Encounter.RetryLives + 2);
	TestEqual(TEXT("hits per life never below one"), Changed.Health.HitsPerLife,
		static_cast<float>(FMath::Max(DeveloperOptionLimits::CountFloor, FMath::RoundToInt(Base.Health.HitsPerLife) - 2)));
	TestEqual(TEXT("four weapons: twin unlocked at level 1"), Changed.Progression.UnlockLevelTwin, DeveloperOptionLimits::AllWeaponsUnlockLevel);
	TestEqual(TEXT("four weapons: needle unlocked at level 1"), Changed.Attack.NeedleUnlockLevel, DeveloperOptionLimits::AllWeaponsUnlockLevel);
	TestFalse(TEXT("slow attack off"), Changed.Keeper.bSlowEnabled);
	TestEqual(TEXT("owl parts 200%"), Changed.Keeper.WingsHp, Base.Keeper.WingsHp * 2.0f);
	TestEqual(TEXT("clock untouched by owl parts"), Changed.Keeper.ClockHp, Base.Keeper.ClockHp);
	TestEqual(TEXT("hitbox 50%"), Changed.Encounter.PlayerRadius, Base.Encounter.PlayerRadius * 0.5f);
	TestEqual(TEXT("experience 200%"), Changed.Progression.XpClock, Base.Progression.XpClock * 2);
	TestEqual(TEXT("value text shows the resulting lives"), DeveloperOptionRules::ValueText(EDeveloperOption::EntryRetries, 2, Base.Encounter.RetryLives, FMath::RoundToInt(Base.Health.HitsPerLife)).ToString(),
		FString::FromInt(Base.Encounter.RetryLives + 2));
	return true;
}
#endif // UMBRELLAELLA_WORKBENCH

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FSettingsDevDirectorOnlyTest, "UmbrellaElla.Settings.DeveloperOptionsDirectorOnly", SettingsDevFlags)
bool FSettingsDevDirectorOnlyTest::RunTest(const FString& Parameters)
{
	TestFalse(TEXT("never in Start Game"), DeveloperOptionRules::CanEdit(EUmbrellaPlayMode::StartGame, true));
	TestTrue(TEXT("Director's Cut in a workbench build"), DeveloperOptionRules::CanEdit(EUmbrellaPlayMode::DirectorsCut, true));
	TestEqual(TEXT("submission build follows the release rule"), DeveloperOptionRules::CanEdit(EUmbrellaPlayMode::DirectorsCut, false),
		DeveloperOptionRelease::bEditableInSubmissionBuild);

	const FString Path = SettingsDevScratchPath(TEXT("devmode.ini"));
	SettingsStore::Delete(Path);
	USettingsMenuSubsystem* Subsystem = MakeSettingsDevSubsystem(Path);
	Subsystem->SetWorkbenchBuildForTest(true);
	USettingsMenuWidget* Widget = NewObject<USettingsMenuWidget>(GetTransientPackage());
	Widget->Setup(Subsystem, EUmbrellaPlayMode::StartGame);
	Widget->SetDeveloperOption(EDeveloperOption::Movement, 200);
	TestEqual(TEXT("Start Game widget cannot set a developer option"),
		DeveloperOptionRules::ValueOf(Subsystem->GetSession().GetDraft().DeveloperValues, EDeveloperOption::Movement), DeveloperOptionLimits::PercentUnit);
	Widget->ShowPage(ESettingsPage::GameOptions);
	TestTrue(TEXT("Start Game has no Game Options page"), Widget->GetPage() != ESettingsPage::GameOptions);

	USettingsMenuWidget* Director = NewObject<USettingsMenuWidget>(GetTransientPackage());
	Director->Setup(Subsystem, EUmbrellaPlayMode::DirectorsCut);
	Director->ShowPage(ESettingsPage::GameOptions);
	TestEqual(TEXT("Director's Cut opens Game Options"), Director->GetPage(), ESettingsPage::GameOptions);
	Director->SetDeveloperOption(EDeveloperOption::Movement, 200);
	TestEqual(TEXT("Director's Cut widget sets the draft"),
		DeveloperOptionRules::ValueOf(Subsystem->GetSession().GetDraft().DeveloperValues, EDeveloperOption::Movement), 200);
	TestTrue(TEXT("Game Options page is dirty"), Subsystem->GetSession().IsPageDirty(ESettingsPage::GameOptions));
	TestFalse(TEXT("Sound page is not"), Subsystem->GetSession().IsPageDirty(ESettingsPage::Sound));
	Director->PressBack();
	TestTrue(TEXT("dirty Back asks Save / Discard / Keep Editing"), Director->IsBackPromptShown());
	Director->ChooseBack(ESettingsBackChoice::Discard);
	TestFalse(TEXT("Discard drops the developer change"), Subsystem->GetSession().IsDirty());
	Director->PressResetDeveloperOptions();
	TestTrue(TEXT("Reset leaves everything as tuned"), DeveloperOptionRules::IsAllDefault(Subsystem->GetSession().GetDraft().DeveloperValues));

	Subsystem->SetPlayMode(EUmbrellaPlayMode::DirectorsCut);
	TestEqual(TEXT("an unsaved option reads as its default"), Subsystem->GetDeveloperOption(EDeveloperOption::Tutorial), DeveloperOptionLimits::ToggleOn);
	ResetSettingsDevSubsystem(Subsystem, Path);
	return true;
}

#if UMBRELLAELLA_WORKBENCH
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FSettingsDevLiveTest, "UmbrellaElla.Settings.World.DeveloperOptionsReachLiveTuning", SettingsDevFlags)
bool FSettingsDevLiveTest::RunTest(const FString& Parameters)
{
	const FString Path = SettingsDevScratchPath(TEXT("devlive.ini"));
	SettingsStore::Delete(Path);
	USettingsMenuSubsystem* Subsystem = MakeSettingsDevSubsystem(Path);
	Subsystem->SetWorkbenchBuildForTest(true);
	const float BaseRise = GetDefault<UUmbrellaTuning>()->Motor.RiseSpeed;
	const int32 BaseRetries = GetDefault<UUmbrellaTuning>()->Encounter.RetryLives;

	Subsystem->SetPlayMode(EUmbrellaPlayMode::DirectorsCut);
	Subsystem->EditSession().SetDeveloperOption(EDeveloperOption::Movement, 200);
	Subsystem->EditSession().SetDeveloperOption(EDeveloperOption::EntryRetries, 3);
	TestEqual(TEXT("draft does not reach the live tuning before Save"), GetDefault<UUmbrellaTuning>()->Motor.RiseSpeed, BaseRise);
	Subsystem->SaveSettings(ESettingsPage::GameOptions);
	TestTrue(TEXT("Save applies"), Subsystem->IsLiveTuningApplied());
	TestEqual(TEXT("live rise speed doubled"), GetDefault<UUmbrellaTuning>()->Motor.RiseSpeed, BaseRise * 2.0f);
	TestEqual(TEXT("live retries +3"), GetDefault<UUmbrellaTuning>()->Encounter.RetryLives, BaseRetries + 3);
	int32 BaselineRetries = 0;
	int32 BaselineHits = 0;
	Subsystem->GetBaselineLifeCounts(BaselineRetries, BaselineHits);
	TestEqual(TEXT("the page's baseline is still as tuned"), BaselineRetries, BaseRetries);
	TestEqual(TEXT("readers get the saved value"), Subsystem->GetDeveloperOption(EDeveloperOption::Movement), 200);

	Subsystem->SetPlayMode(EUmbrellaPlayMode::StartGame);
	TestFalse(TEXT("Start Game drops the developer tuning"), Subsystem->IsLiveTuningApplied());
	TestEqual(TEXT("Start Game rise speed is as tuned"), GetDefault<UUmbrellaTuning>()->Motor.RiseSpeed, BaseRise);
	TestEqual(TEXT("Start Game readers get defaults"), Subsystem->GetDeveloperOption(EDeveloperOption::Movement), DeveloperOptionLimits::PercentUnit);

	Subsystem->SetPlayMode(EUmbrellaPlayMode::DirectorsCut);
	TestEqual(TEXT("back in Director's Cut the saved options return"), GetDefault<UUmbrellaTuning>()->Motor.RiseSpeed, BaseRise * 2.0f);

	Subsystem->SetWorkbenchBuildForTest(false);
	Subsystem->RefreshLiveTuning();
	TestEqual(TEXT("a submission build follows the release rule"), Subsystem->IsLiveTuningApplied(), DeveloperOptionRelease::bEditableInSubmissionBuild);
	Subsystem->SetWorkbenchBuildForTest(true);
	Subsystem->RefreshLiveTuning();

	// Session only: a reload from the file is as tuned again.
	Subsystem->ReloadFromStore();
	TestFalse(TEXT("developer values are not in the file"), Subsystem->IsLiveTuningApplied());
	TestEqual(TEXT("reload restores the rise speed"), GetDefault<UUmbrellaTuning>()->Motor.RiseSpeed, BaseRise);
	ResetSettingsDevSubsystem(Subsystem, Path);
	return true;
}
#endif // UMBRELLAELLA_WORKBENCH

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FSettingsAccessDefaultsTest, "UmbrellaElla.Settings.AccessibilityDefaults", SettingsDevFlags)
bool FSettingsAccessDefaultsTest::RunTest(const FString& Parameters)
{
	TestEqual(TEXT("no context: 100% text"), UmbrellaAccessibility::GetTextScalePercent(nullptr), SettingsConstants::TextScaleMin);
	TestEqual(TEXT("no context: scale 1"), UmbrellaAccessibility::GetTextScale(nullptr), 1.0f);
	TestFalse(TEXT("no context: full motion"), UmbrellaAccessibility::IsReducedMotion(nullptr));
	TestFalse(TEXT("no context: full flash"), UmbrellaAccessibility::IsReducedFlash(nullptr));
	TestEqual(TEXT("no context: full shake"), UmbrellaAccessibility::GetShakeScale(nullptr), 1.0f);
	TestEqual(TEXT("150% of an 18 pt font"), UmbrellaAccessibility::ScaledFontSize(18, 150), 27);
	TestEqual(TEXT("text scale clamps at 200%"), UmbrellaAccessibility::TextScaleFromPercent(300), 2.0f);
	TestEqual(TEXT("reduced motion zeroes shake"), UmbrellaAccessibility::ShakeScaleFor(true), 0.0f);

	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FSettingsAccessLiveTest, "UmbrellaElla.Settings.World.AccessibilityReachesReaders", SettingsDevFlags)
bool FSettingsAccessLiveTest::RunTest(const FString& Parameters)
{
	const FString Path = SettingsDevScratchPath(TEXT("access.ini"));
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

	FUmbrellaTestWorld TestWorld;
	UWorld* World = TestWorld.GetWorld();
	if (!TestNotNull(TEXT("test world"), World))
	{
		SettingsStore::Delete(Path);
		return false;
	}
	World->SetGameInstance(GameInstance);
	TestFalse(TEXT("before Save: full motion"), UmbrellaAccessibility::IsReducedMotion(World));

	const TSharedRef<int32> SavedEvents = MakeShared<int32>(0);
	const FDelegateHandle Handle = Subsystem->OnSettingsSaved().AddLambda([SavedEvents]() { ++(*SavedEvents); });
	Subsystem->EditSession().SetReducedMotion(true);
	Subsystem->EditSession().SetTextScalePercent(150);
	Subsystem->EditSession().SetReducedFlash(true);
	TestFalse(TEXT("draft is not read"), UmbrellaAccessibility::IsReducedMotion(World));
	Subsystem->SaveSettings(ESettingsPage::Sound);
	TestEqual(TEXT("Save fires the saved event"), *SavedEvents, 1);
	TestTrue(TEXT("readers see reduced motion"), UmbrellaAccessibility::IsReducedMotion(World));
	TestEqual(TEXT("camera shake readers get 0"), UmbrellaAccessibility::GetShakeScale(World), 0.0f);
	TestTrue(TEXT("readers see reduced flash"), UmbrellaAccessibility::IsReducedFlash(World));
	TestEqual(TEXT("readers see 150% text"), UmbrellaAccessibility::GetTextScale(World), 1.5f);
	// World-free readers (Slate, subsystems with no world context) see the same saved values.
	TestEqual(TEXT("published text 150%"), UmbrellaAccessibility::PublishedTextScalePercent(), 150);
	TestEqual(TEXT("flow menu font 28 -> 42"), UmbrellaAccessibility::PublishedFontSize(28), 42);
	TestTrue(TEXT("published reduced motion"), UmbrellaAccessibility::IsPublishedReducedMotion());

	Subsystem->EditSession().SetReducedMotion(false);
	Subsystem->SaveSettings(ESettingsPage::Sound);
	TestFalse(TEXT("motion back on"), UmbrellaAccessibility::IsReducedMotion(World));
	TestFalse(TEXT("published motion back on"), UmbrellaAccessibility::IsPublishedReducedMotion());
	TestFalse(TEXT("nothing left in the live tuning"), Subsystem->IsLiveTuningApplied());

	Subsystem->OnSettingsSaved().Remove(Handle);
	World->SetGameInstance(nullptr);
	ResetSettingsDevSubsystem(Subsystem, Path);
	return true;
}

#endif
