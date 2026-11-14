// Keeper fight music (lead order, Josh Nov 13 22:20): the fight cross-fades MusicTitle -> MusicContest, the clock phase
// switches to MusicDesperation (sound-list.csv MusicDesperation row "Keeper fight music, clock"; GDD SH1.0 OWL-06 Phase 3
// clock), and the Title and Credits screens bring MusicTitle back.
#include "Misc/AutomationTest.h"

#if WITH_AUTOMATION_TESTS

#include "Components/AudioComponent.h"
#include "Core/UmbrellaEventBus.h"
#include "Core/UmbrellaGameMode.h"
#include "Encounter/EncounterDirectorSubsystem.h"
#include "Encounter/KeeperFightModel.h"
#include "Engine/Engine.h"
#include "Engine/GameInstance.h"
#include "Engine/World.h"
#include "Feedback/Audio/UmbrellaCueSubsystem.h"
#include "Feedback/Audio/UmbrellaCueTable.h"
#include "Flow/FlowRules.h"
#include "Flow/UmbrellaPlayerController.h"
#include "GameFramework/PlayerState.h"
#include "GameFramework/WorldSettings.h"
#include "Misc/Paths.h"
#include "Settings/SettingsMenuSubsystem.h"
#include "Settings/SettingsStore.h"
#include "Sound/SoundBase.h"
#include "Sound/SoundClass.h"

namespace
{
	const EAutomationTestFlags FightMusicFlags = EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter;
	const FName FightMusicTitleId(TEXT("MusicTitle"));
	const FName FightMusicContestId(TEXT("MusicContest"));
	const FName FightMusicDesperationId(TEXT("MusicDesperation"));
	/** Flow ticks of half a second until the story hands over to the credits, and the credits to the Start screen. */
	const int32 FightMusicMaxFlowTicks = 2000;
	const float FightMusicFlowTick = 0.5f;

	/** A game world as in the game: a game instance with settings, the flow controller on the Start screen. */
	struct FFightMusicWorld
	{
		UWorld* World = nullptr;
		UGameInstance* Instance = nullptr;
		AUmbrellaPlayerController* Controller = nullptr;
		FString StorePath;

		FFightMusicWorld()
		{
			StorePath = FPaths::Combine(FPaths::ProjectSavedDir(), TEXT("UmbrellaEllaTests"), TEXT("FightMusic"), TEXT("settings.ini"));
			SettingsStore::Delete(StorePath);
			Instance = NewObject<UGameInstance>(GEngine);
			Instance->AddToRoot();
			Instance->InitializeStandalone();
			if (USettingsMenuSubsystem* Settings = Instance->GetSubsystem<USettingsMenuSubsystem>())
			{
				// Transient classes, so the test never changes the engine's real Music volume.
				Settings->SetSoundClasses(NewObject<USoundClass>(GetTransientPackage()), NewObject<USoundClass>(GetTransientPackage()),
					NewObject<USoundClass>(GetTransientPackage()));
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
			Controller = World->SpawnActor<AUmbrellaPlayerController>();
			Controller->PlayerState = World->SpawnActor<APlayerState>();
			Controller->KeepTutorialInMemoryOnly();
			Controller->MarkTutorialSeen();
		}

		~FFightMusicWorld()
		{
			if (UUmbrellaCueSubsystem* Cue = Cues())
			{
				Cue->StopMusic();
			}
			GEngine->DestroyWorldContext(World);
			World->DestroyWorld(false);
			Instance->Shutdown();
			Instance->RemoveFromRoot();
			SettingsStore::Delete(StorePath);
		}

		UUmbrellaCueSubsystem* Cues() const { return World->GetSubsystem<UUmbrellaCueSubsystem>(); }
		UEncounterDirectorSubsystem* Encounter() const { return World->GetSubsystem<UEncounterDirectorSubsystem>(); }

		/** Start Game: BeginRun begins the Keeper fight at the wings phase (AUmbrellaGameMode::BeginFight), as in the game. */
		bool BeginFight()
		{
			Controller->StartGame();
			return Encounter() != nullptr && Controller->GetScreen() == EFlowScreen::Playing;
		}

		/** The fight's phase-start event, as UEncounterDirectorSubsystem broadcasts it. */
		void SendPhase(EKeeperPhase Phase) const
		{
			FUmbrellaEvent Event;
			Event.Type = EUmbrellaEventType::PhaseStarted;
			Event.Detail = UEncounterDirectorSubsystem::PhaseName(Phase);
			UUmbrellaEventBus::Get(World)->Broadcast(Event);
		}
	};

	/** Track Id is the music: its id, playing, looping, the take named after it. */
	bool FightMusicExpect(FAutomationTestBase& Test, const FFightMusicWorld& Fixture, FName Id, const TCHAR* When)
	{
		const UUmbrellaCueSubsystem* Cue = Fixture.Cues();
		UAudioComponent* Music = Cue ? Cue->GetMusicComponent() : nullptr;
		if (!Test.TestNotNull(*FString::Printf(TEXT("%s: a music component exists (an audio device is required)"), When), Music))
		{
			return false;
		}
		Test.TestEqual(*FString::Printf(TEXT("%s: the music is %s"), When, *Id.ToString()), Cue->GetMusicId(), Id);
		Test.TestTrue(*FString::Printf(TEXT("%s: the music is playing"), When), Music->IsPlaying());
		const FString Take = Music->Sound ? Music->Sound->GetName() : FString();
		Test.TestTrue(*FString::Printf(TEXT("%s: the take %s is a %s take"), When, *Take, *Id.ToString()), Take.Contains(Id.ToString()));
		Test.TestTrue(*FString::Printf(TEXT("%s: the track loops"), When), Music->Sound && Music->Sound->IsLooping());
		return true;
	}

	bool FightMusicRouted(EUmbrellaEventType Type, const TCHAR* Detail, FName Id)
	{
		FUmbrellaEvent Event;
		Event.Type = Type;
		Event.Detail = FName(Detail);
		for (const FUmbrellaSoundCue* Row : UmbrellaCueTable::ForEvent(Event))
		{
			if (FName(Row->Id) == Id)
			{
				return true;
			}
		}
		return false;
	}
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FFightMusicRoutesTest, "UmbrellaElla.Audio.FightMusicRoutes",
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::ClientContext | EAutomationTestFlags::EngineFilter)
bool FFightMusicRoutesTest::RunTest(const FString& Parameters)
{
	const FName Wings = UEncounterDirectorSubsystem::PhaseName(EKeeperPhase::Wings);
	const FName Mechanisms = UEncounterDirectorSubsystem::PhaseName(EKeeperPhase::Mechanisms);
	const FName Clock = UEncounterDirectorSubsystem::PhaseName(EKeeperPhase::Clock);
	TestTrue(TEXT("wings phase start plays MusicContest"), FightMusicRouted(EUmbrellaEventType::PhaseStarted, *Wings.ToString(), FightMusicContestId));
	TestTrue(TEXT("mechanisms phase start keeps MusicContest"), FightMusicRouted(EUmbrellaEventType::PhaseStarted, *Mechanisms.ToString(), FightMusicContestId));
	TestTrue(TEXT("clock phase start plays MusicDesperation"), FightMusicRouted(EUmbrellaEventType::PhaseStarted, *Clock.ToString(), FightMusicDesperationId));
	TestFalse(TEXT("clock phase does not also play MusicContest"), FightMusicRouted(EUmbrellaEventType::PhaseStarted, *Clock.ToString(), FightMusicContestId));
	TestFalse(TEXT("wings phase does not play MusicDesperation"), FightMusicRouted(EUmbrellaEventType::PhaseStarted, *Wings.ToString(), FightMusicDesperationId));
	TestEqual(TEXT("Start screen music"), FFlowRules::MusicFor(EFlowScreen::Title), FightMusicTitleId);
	TestEqual(TEXT("credits music"), FFlowRules::MusicFor(EFlowScreen::Credits), FightMusicTitleId);
	TestTrue(TEXT("cross-fade within the music fade cap (audio-rules.json fade_s_max 0.5)"),
		UmbrellaCueConst::MusicCrossFadeSeconds > 0.0f && UmbrellaCueConst::MusicCrossFadeSeconds <= 0.5f);
	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FFightMusicStartTest, "UmbrellaElla.Audio.World.FightStartCrossFadesTitleToContest", FightMusicFlags)
bool FFightMusicStartTest::RunTest(const FString& Parameters)
{
	FFightMusicWorld Test;
	if (!FightMusicExpect(*this, Test, FightMusicTitleId, TEXT("Start screen")))
	{
		return false;
	}
	UAudioComponent* Title = Test.Cues()->GetMusicComponent();
	if (!TestTrue(TEXT("the Keeper fight begins"), Test.BeginFight()))
	{
		return false;
	}
	FightMusicExpect(*this, Test, FightMusicContestId, TEXT("fight start (wings)"));
	UAudioComponent* Fight = Test.Cues()->GetMusicComponent();
	TestTrue(TEXT("the fight track plays on the other component"), Fight != Title);
	TestTrue(TEXT("the title track is the outgoing one"), Test.Cues()->GetOutgoingMusicComponent() == Title);
	TestTrue(TEXT("the title track fades out (not a hard cut)"), Title->GetPlayState() == EAudioComponentPlayState::FadingOut);
	TestTrue(TEXT("the fight track fades in"), Fight->GetPlayState() == EAudioComponentPlayState::FadingIn);

	const int32 Starts = Test.Cues()->GetMusicStartCount();
	Test.SendPhase(EKeeperPhase::Mechanisms);
	FightMusicExpect(*this, Test, FightMusicContestId, TEXT("mechanisms phase"));
	TestEqual(TEXT("phase 2 carries the fight track on, no restart"), Test.Cues()->GetMusicStartCount(), Starts);
	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FFightMusicDesperationTest, "UmbrellaElla.Audio.World.ClockPhaseSwitchesToDesperation", FightMusicFlags)
bool FFightMusicDesperationTest::RunTest(const FString& Parameters)
{
	FFightMusicWorld Test;
	if (!TestTrue(TEXT("the Keeper fight begins"), Test.BeginFight()))
	{
		return false;
	}
	Test.SendPhase(EKeeperPhase::Mechanisms);
	if (!FightMusicExpect(*this, Test, FightMusicContestId, TEXT("mechanisms phase")))
	{
		return false;
	}
	UAudioComponent* Contest = Test.Cues()->GetMusicComponent();
	Test.SendPhase(EKeeperPhase::Clock);
	FightMusicExpect(*this, Test, FightMusicDesperationId, TEXT("clock phase"));
	TestTrue(TEXT("MusicContest fades out"), Contest->GetPlayState() == EAudioComponentPlayState::FadingOut);

	// A fight begun at the clock checkpoint (the director's real PhaseStarted) goes straight to MusicDesperation.
	FFightMusicWorld Checkpoint;
	UEncounterDirectorSubsystem* Director = Checkpoint.Encounter();
	if (TestNotNull(TEXT("encounter director"), Director))
	{
		Director->SetManualStepping(true);
		Director->BeginKeeperFightAtPhase(EKeeperPhase::Clock);
		FightMusicExpect(*this, Checkpoint, FightMusicDesperationId, TEXT("fight begun at the clock checkpoint"));
	}
	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FFightMusicCreditsTitleTest, "UmbrellaElla.Audio.World.CreditsAndTitleReturnToTitleMusic", FightMusicFlags)
bool FFightMusicCreditsTitleTest::RunTest(const FString& Parameters)
{
	FFightMusicWorld Test;
	if (!TestTrue(TEXT("the Keeper fight begins"), Test.BeginFight()))
	{
		return false;
	}
	Test.SendPhase(EKeeperPhase::Clock);
	if (!FightMusicExpect(*this, Test, FightMusicDesperationId, TEXT("clock phase")))
	{
		return false;
	}
	FUmbrellaEvent Won;
	Won.Type = EUmbrellaEventType::EncounterCompleted;
	UUmbrellaEventBus::Get(Test.World)->Broadcast(Won);
	TestEqual(TEXT("story text first"), Test.Controller->GetScreen(), EFlowScreen::Story);
	TestTrue(TEXT("the fight music stops for the story"), Test.Cues()->GetMusicId().IsNone());

	for (int32 FightMusicStep = 0; FightMusicStep < FightMusicMaxFlowTicks && Test.Controller->GetScreen() == EFlowScreen::Story; ++FightMusicStep)
	{
		Test.Controller->TickFlow(FightMusicFlowTick);
	}
	TestEqual(TEXT("credits follow the story"), Test.Controller->GetScreen(), EFlowScreen::Credits);
	FightMusicExpect(*this, Test, FightMusicTitleId, TEXT("credits"));

	for (int32 FightMusicStep = 0; FightMusicStep < FightMusicMaxFlowTicks && Test.Controller->GetScreen() == EFlowScreen::Credits; ++FightMusicStep)
	{
		Test.Controller->TickFlow(FightMusicFlowTick);
	}
	TestEqual(TEXT("the Start screen follows the credits"), Test.Controller->GetScreen(), EFlowScreen::Title);
	FightMusicExpect(*this, Test, FightMusicTitleId, TEXT("back on the Start screen"));
	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FFightMusicBackToTitleTest, "UmbrellaElla.Audio.World.TitleCrossFadesBackFromFightMusic", FightMusicFlags)
bool FFightMusicBackToTitleTest::RunTest(const FString& Parameters)
{
	FFightMusicWorld Test;
	if (!TestTrue(TEXT("the Keeper fight begins"), Test.BeginFight())
		|| !FightMusicExpect(*this, Test, FightMusicContestId, TEXT("fight")))
	{
		return false;
	}
	UAudioComponent* Fight = Test.Cues()->GetMusicComponent();
	// What the flow controller does on entering the Start screen (PlayFlowMusic -> FFlowRules::MusicFor(Title)).
	Test.Cues()->EnsureMusic(FFlowRules::MusicFor(EFlowScreen::Title));
	FightMusicExpect(*this, Test, FightMusicTitleId, TEXT("Start screen after the fight"));
	TestTrue(TEXT("the fight track fades out"), Fight->GetPlayState() == EAudioComponentPlayState::FadingOut);
	TestTrue(TEXT("two music components at most: the second is reused"), Test.Cues()->GetOutgoingMusicComponent() == Fight);
	return true;
}

#endif
