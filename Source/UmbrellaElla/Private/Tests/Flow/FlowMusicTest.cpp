#include "Misc/AutomationTest.h"

#if WITH_AUTOMATION_TESTS

#include "Components/AudioComponent.h"
#include "Core/UmbrellaEventBus.h"
#include "Core/UmbrellaGameMode.h"
#include "Engine/Engine.h"
#include "Engine/GameInstance.h"
#include "Engine/World.h"
#include "Feedback/Audio/UmbrellaCueSubsystem.h"
#include "Flow/FlowRules.h"
#include "Flow/UmbrellaPlayerController.h"
#include "GameFramework/PlayerState.h"
#include "GameFramework/WorldSettings.h"
#include "Misc/Paths.h"
#include "Settings/SettingsMenuSubsystem.h"
#include "Settings/SettingsModel.h"
#include "Settings/SettingsStore.h"
#include "Sound/SoundBase.h"
#include "Sound/SoundClass.h"
#include "UObject/UObjectIterator.h"

namespace
{
	const EAutomationTestFlags FlowMusicFlags = EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter;
	const FName FlowMusicTitleId(TEXT("MusicTitle"));

	/**
	 * A transient game world whose game instance runs its subsystems (settings included, on a scratch file and a
	 * transient Music class), with the flow controller spawned on the Start screen as in the game.
	 */
	struct FFlowMusicWorld
	{
		UWorld* World = nullptr;
		UGameInstance* Instance = nullptr;
		USettingsMenuSubsystem* Settings = nullptr;
		USoundClass* MusicClass = nullptr;
		AUmbrellaPlayerController* Controller = nullptr;
		FString StorePath;

		explicit FFlowMusicWorld(bool bSpawnController = true)
		{
			StorePath = FPaths::Combine(FPaths::ProjectSavedDir(), TEXT("UmbrellaEllaTests"), TEXT("FlowMusic"), TEXT("settings.ini"));
			SettingsStore::Delete(StorePath);
			Instance = NewObject<UGameInstance>(GEngine);
			Instance->AddToRoot();
			Instance->InitializeStandalone();
			Settings = Instance->GetSubsystem<USettingsMenuSubsystem>();
			if (Settings)
			{
				// Transient classes, so the test never changes the engine's real Music volume.
				MusicClass = NewObject<USoundClass>(GetTransientPackage());
				Settings->SetSoundClasses(NewObject<USoundClass>(GetTransientPackage()), NewObject<USoundClass>(GetTransientPackage()), MusicClass);
				Settings->SetStorePath(StorePath);
				Settings->ReloadFromStore();
			}

			World = UWorld::CreateWorld(EWorldType::Game, false);
			FWorldContext& Context = GEngine->CreateNewWorldContext(EWorldType::Game);
			Context.SetCurrentWorld(World);
			Context.OwningGameInstance = Instance;
			World->SetGameInstance(Instance);
			World->GetWorldSettings()->DefaultGameMode = AUmbrellaGameMode::StaticClass();
			World->SetGameMode(FURL());
			World->InitializeActorsForPlay(FURL());
			World->BeginPlay();
			if (bSpawnController)
			{
				SpawnController();
			}
		}

		void SpawnController()
		{
			Controller = World->SpawnActor<AUmbrellaPlayerController>();
			Controller->PlayerState = World->SpawnActor<APlayerState>();
			Controller->KeepTutorialInMemoryOnly();
			Controller->MarkTutorialSeen();
		}

		~FFlowMusicWorld()
		{
			GEngine->DestroyWorldContext(World);
			World->DestroyWorld(false);
			Instance->Shutdown();
			Instance->RemoveFromRoot();
			SettingsStore::Delete(StorePath);
		}

		UUmbrellaCueSubsystem* Cues() const { return World->GetSubsystem<UUmbrellaCueSubsystem>(); }

		UAudioComponent* Music() const
		{
			const UUmbrellaCueSubsystem* Cue = Cues();
			return Cue ? Cue->GetMusicComponent() : nullptr;
		}
	};

	/** The title track is the music, playing, looping, through the Music slider's class. Earlier tests passed on a null component. */
	bool FlowMusicExpectTitle(FAutomationTestBase& Test, const FFlowMusicWorld& Fixture, const TCHAR* When)
	{
		const UUmbrellaCueSubsystem* Cue = Fixture.Cues();
		UAudioComponent* Music = Fixture.Music();
		if (!Test.TestNotNull(*FString::Printf(TEXT("%s: a music component exists (an audio device is required)"), When), Music))
		{
			return false;
		}
		Test.TestEqual(*FString::Printf(TEXT("%s: the music is the title track"), When), Cue->GetMusicId(), FlowMusicTitleId);
		Test.TestTrue(*FString::Printf(TEXT("%s: the music is playing"), When), Music->IsPlaying());
		Test.TestTrue(*FString::Printf(TEXT("%s: the take is SW_MusicTitle_*"), When),
			Music->Sound && Music->Sound->GetName().StartsWith(TEXT("SW_MusicTitle_")));
		Test.TestTrue(*FString::Printf(TEXT("%s: the track loops"), When), Music->Sound && Music->Sound->IsLooping());
		return true;
	}
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FFlowMusicTitleTest, "UmbrellaElla.Flow.World.StartScreenPlaysLoopingTitleMusic", FlowMusicFlags)
bool FFlowMusicTitleTest::RunTest(const FString& Parameters)
{
	TestEqual(TEXT("rule: Start and credits play the title track"), FFlowRules::MusicFor(EFlowScreen::Title), FlowMusicTitleId);
	TestEqual(TEXT("rule: credits share it"), FFlowRules::MusicFor(EFlowScreen::Credits), FlowMusicTitleId);
	TestTrue(TEXT("rule: gameplay leaves music as it is"), FFlowRules::MusicFor(EFlowScreen::Playing).IsNone());

	FFlowMusicWorld Test;
	TestEqual(TEXT("the Start screen is up"), Test.Controller->GetScreen(), EFlowScreen::Title);
	FlowMusicExpectTitle(*this, Test, TEXT("Start screen, before any input"));
	TestEqual(TEXT("started once"), Test.Cues()->GetMusicStartCount(), 1);
	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FFlowMusicModePickTest, "UmbrellaElla.Flow.World.ModePickKeepsTitleMusicWithoutRestart", FlowMusicFlags)
bool FFlowMusicModePickTest::RunTest(const FString& Parameters)
{
	FFlowMusicWorld Test;
	if (!FlowMusicExpectTitle(*this, Test, TEXT("Start screen")))
	{
		return false;
	}
	UAudioComponent* Before = Test.Music();
	const int32 StartsBefore = Test.Cues()->GetMusicStartCount();
	Test.Controller->StartGame();
	TestEqual(TEXT("the run is up"), Test.Controller->GetScreen(), EFlowScreen::Playing);
	// Lead order (Josh, Nov 13 22:20): Start Game begins the Keeper fight, so the title cross-fades into MusicContest
	// (UmbrellaElla.Audio.World.FightStartCrossFadesTitleToContest). The title is never restarted or doubled.
	TestEqual(TEXT("the fight music follows Start Game"), Test.Cues()->GetMusicId(), FName(TEXT("MusicContest")));
	TestTrue(TEXT("the title fades out on its own component, not restarted"),
		Test.Cues()->GetOutgoingMusicComponent() == Before && Before->GetPlayState() == EAudioComponentPlayState::FadingOut);
	TestEqual(TEXT("ModeSelected added no start; the fight track added one"), Test.Cues()->GetMusicStartCount(), StartsBefore + 1);

	int32 TitleMusicComponents = 0;
	for (TObjectIterator<UAudioComponent> It; It; ++It)
	{
		// The music component persists across level loads, so it has no world; every other test world stopped its own.
		if (It->IsPlaying() && It->Sound && It->Sound->GetName().StartsWith(TEXT("SW_MusicTitle_")))
		{
			++TitleMusicComponents;
		}
	}
	TestEqual(TEXT("one title-music instance playing, not two"), TitleMusicComponents, 1);
	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FFlowMusicCreditsTest, "UmbrellaElla.Flow.World.CreditsPlayTitleMusicAfterStory", FlowMusicFlags)
bool FFlowMusicCreditsTest::RunTest(const FString& Parameters)
{
	FFlowMusicWorld Test;
	Test.Controller->StartGame();
	FUmbrellaEvent Won;
	Won.Type = EUmbrellaEventType::EncounterCompleted;
	UUmbrellaEventBus::Get(Test.World)->Broadcast(Won);
	TestEqual(TEXT("story text first"), Test.Controller->GetScreen(), EFlowScreen::Story);
	TestTrue(TEXT("the story plays without the run's music"), Test.Cues()->GetMusicId().IsNone());

	for (int32 FlowMusicStep = 0; FlowMusicStep < 600 && Test.Controller->GetScreen() == EFlowScreen::Story; ++FlowMusicStep)
	{
		Test.Controller->TickFlow(0.5f);
	}
	TestEqual(TEXT("credits follow the story"), Test.Controller->GetScreen(), EFlowScreen::Credits);
	const int32 StartsAtCredits = Test.Cues()->GetMusicStartCount();
	FlowMusicExpectTitle(*this, Test, TEXT("credits"));
	Test.Controller->TickFlow(0.5f);
	TestEqual(TEXT("ticking the credits does not restart it"), Test.Cues()->GetMusicStartCount(), StartsAtCredits);
	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FFlowMusicVolumeTest, "UmbrellaElla.Flow.World.MusicVolumeReachesPlayingMusic", FlowMusicFlags)
bool FFlowMusicVolumeTest::RunTest(const FString& Parameters)
{
	FFlowMusicWorld Test;
	if (!TestNotNull(TEXT("the game instance runs settings"), Test.Settings) || !FlowMusicExpectTitle(*this, Test, TEXT("Start screen")))
	{
		return false;
	}
	UAudioComponent* Music = Test.Music();
	TestTrue(TEXT("the music plays through the Music slider's class"), Music->SoundClassOverride == Test.Settings->GetMusicClass());

	const int32 Lowered = 25;
	Test.Settings->EditSession().SetMusicVolume(Lowered);
	Test.Settings->SaveSettings(ESettingsPage::Sound);
	TestEqual(TEXT("the playing music's class volume follows the slider"),
		Music->SoundClassOverride ? Music->SoundClassOverride->Properties.Volume : -1.0f, SettingsRules::VolumeToClassScale(Lowered));

	const int32 Muted = 0;
	Test.Settings->EditSession().SetMusicVolume(Muted);
	Test.Settings->SaveSettings(ESettingsPage::Sound);
	TestEqual(TEXT("0 mutes it"), Music->SoundClassOverride ? Music->SoundClassOverride->Properties.Volume : -1.0f,
		SettingsRules::VolumeToClassScale(Muted));
	TestTrue(TEXT("still the same playing component"), Test.Music() == Music && Music->IsPlaying());
	return true;
}



// D-new-music-at-launch (Josh, 13 Nov): MusicTitle is playing on the first frame after launch, before any Start screen
// widget or flow controller exists, and the controller then adds no second start.
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FFlowMusicFirstFrameTest, "UmbrellaElla.Flow.World.MusicPlayingOnFirstFrameAfterLaunch", FlowMusicFlags)
bool FFlowMusicFirstFrameTest::RunTest(const FString& Parameters)
{
	FFlowMusicWorld Test(false);
	TestTrue(TEXT("no flow controller yet: nothing but the world has begun"), Test.Controller == nullptr);
	FlowMusicExpectTitle(*this, Test, TEXT("first frame, world begun, no controller"));
	TestEqual(TEXT("started once"), Test.Cues()->GetMusicStartCount(), 1);

	Test.SpawnController();
	FlowMusicExpectTitle(*this, Test, TEXT("after the Start screen opens"));
	TestEqual(TEXT("the Start screen did not restart or double it"), Test.Cues()->GetMusicStartCount(), 1);
	return true;
}

#endif
