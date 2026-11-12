#include "Misc/AutomationTest.h"

#if WITH_AUTOMATION_TESTS

#include "Arena/UmbrellaArena.h"
#include "Core/EllaCharacter.h"
#include "Core/UmbrellaEventBus.h"
#include "Core/UmbrellaGameMode.h"
#include "Engine/Engine.h"
#include "Engine/LocalPlayer.h"
#include "Engine/GameInstance.h"
#include "Engine/World.h"
#include "Encounter/EncounterDirectorSubsystem.h"
#include "Flow/UmbrellaPlayerController.h"
#include "Level/UmbrellaLevelDirector.h"
#include "GameFramework/PlayerState.h"
#include "GameFramework/WorldSettings.h"
#include "Kismet/GameplayStatics.h"
#include "Progression/ProgressionSubsystem.h"
#include "UI/Progression/ProgressionPurchaseWidget.h"

namespace
{
	/** A transient game world with the Umbrella game mode and one flow controller. */
	struct FFlowTestWorld
	{
		UWorld* World = nullptr;
		UGameInstance* Instance = nullptr;
		AUmbrellaPlayerController* Controller = nullptr;

		FFlowTestWorld()
		{
			World = UWorld::CreateWorld(EWorldType::Game, false);
			FWorldContext& Context = GEngine->CreateNewWorldContext(EWorldType::Game);
			Context.SetCurrentWorld(World);
			Instance = NewObject<UGameInstance>(GEngine);
			Instance->AddToRoot();
			Context.OwningGameInstance = Instance;
			World->SetGameInstance(Instance);
			World->GetWorldSettings()->DefaultGameMode = AUmbrellaGameMode::StaticClass();
			World->SetGameMode(FURL());
			World->InitializeActorsForPlay(FURL());
			World->BeginPlay();
			Controller = World->SpawnActor<AUmbrellaPlayerController>();
			// Pausing is owned by a player state, as for a real player.
			Controller->PlayerState = World->SpawnActor<APlayerState>();
			// Most tests start a run directly; the tutorial tests clear this.
			Controller->KeepTutorialInMemoryOnly();
			Controller->MarkTutorialSeen();
		}

		~FFlowTestWorld()
		{
			GEngine->DestroyWorldContext(World);
			World->DestroyWorld(false);
			Instance->RemoveFromRoot();
		}

		void Broadcast(EUmbrellaEventType Type) const
		{
			FUmbrellaEvent Event;
			Event.Type = Type;
			UUmbrellaEventBus::Get(World)->Broadcast(Event);
		}
	};
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FFlowWorldStartTest, "UmbrellaElla.Flow.World.StartGameReachesFight",
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FFlowWorldStartTest::RunTest(const FString& Parameters)
{
	FFlowTestWorld Test;
	TestEqual(TEXT("the title comes first"), Test.Controller->GetScreen(), EFlowScreen::Title);
	TestNull(TEXT("no Ella on the title"), Test.Controller->GetPawn());

	const TSharedRef<int32> ModeEvents = MakeShared<int32>(0);
	const TSharedRef<FName> ModeDetail = MakeShared<FName>();
	const TSharedRef<bool> ModeWorldUp = MakeShared<bool>(false);
	const FDelegateHandle Handle = UUmbrellaEventBus::Get(Test.World)->On(EUmbrellaEventType::ModeSelected).AddLambda(
		[ModeEvents, ModeDetail, ModeWorldUp, World = Test.World, Controller = Test.Controller](const FUmbrellaEvent& Event)
		{
			++(*ModeEvents);
			*ModeDetail = Event.Detail;
			AUmbrellaGameMode* Up = World->GetAuthGameMode<AUmbrellaGameMode>();
			*ModeWorldUp = Up && Up->IsFightStarted() && Controller->GetPawn() != nullptr;
		});
	Test.Controller->StartGame();
	UUmbrellaEventBus::Get(Test.World)->On(EUmbrellaEventType::ModeSelected).Remove(Handle);

	TestEqual(TEXT("playing"), Test.Controller->GetScreen(), EFlowScreen::Playing);
	TestEqual(TEXT("mode selected once"), *ModeEvents, 1);
	TestEqual(TEXT("mode event names the mode"), ModeDetail->ToString(), FString(TEXT("StartGame")));
	TestTrue(TEXT("the world was up when the mode event fired"), *ModeWorldUp);
	TestTrue(TEXT("Ella is possessed"), Cast<AEllaCharacter>(Test.Controller->GetPawn()) != nullptr);
	AUmbrellaGameMode* Mode = Test.World->GetAuthGameMode<AUmbrellaGameMode>();
	TestTrue(TEXT("fight started"), Mode && Mode->IsFightStarted());
	TestTrue(TEXT("the arena exists"), Mode && Mode->GetArena() != nullptr);
	TestTrue(TEXT("camera is the arena"), Test.Controller->GetViewTarget() == Mode->GetArena());
	TestEqual(TEXT("start game mode"), Test.Controller->GetPlayMode(), EUmbrellaPlayMode::StartGame);
	const UEncounterDirectorSubsystem* Director = Test.World->GetSubsystem<UEncounterDirectorSubsystem>();
	TestTrue(TEXT("the director is Active"), Director && Director->GetState() == EEncounterState::Active);
	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FFlowWorldTutorialTest, "UmbrellaElla.Flow.World.TutorialFirstStartSkippable",
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FFlowWorldTutorialTest::RunTest(const FString& Parameters)
{
	{
		FFlowTestWorld Test;
		Test.Controller->ClearTutorialSeen();
		Test.Controller->StartGame();
		TestEqual(TEXT("first start shows the tutorial"), Test.Controller->GetScreen(), EFlowScreen::Tutorial);
		TestNull(TEXT("the fight waits for the tutorial"), Test.Controller->GetPawn());
		Test.Controller->ApplyCommand(EFlowCommand::Pause);
		TestEqual(TEXT("pause works inside the tutorial"), Test.Controller->GetScreen(), EFlowScreen::TutorialPaused);
		Test.Controller->ApplyCommand(EFlowCommand::SkipTutorial);
		TestEqual(TEXT("skip waits for neutral input"), Test.Controller->GetScreen(), EFlowScreen::Resuming);
		TestTrue(TEXT("skip starts the fight"), Cast<AEllaCharacter>(Test.Controller->GetPawn()) != nullptr);
		TestTrue(TEXT("skip marks the tutorial seen"), Test.Controller->IsTutorialSeen());
	}
	{
		FFlowTestWorld Test;
		Test.Controller->ClearTutorialSeen();
		Test.Controller->StartDirectorsCut();
		TestEqual(TEXT("Director's Cut also shows it"), Test.Controller->GetScreen(), EFlowScreen::Tutorial);
		Test.Controller->ApplyCommand(EFlowCommand::NextPage);
		Test.Controller->ApplyCommand(EFlowCommand::SkipTutorial);
		TestEqual(TEXT("skip from a page"), Test.Controller->GetScreen(), EFlowScreen::Resuming);
	}
	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FFlowWorldDirectorsCutTest, "UmbrellaElla.Flow.World.DirectorsCutReachesSameFight",
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FFlowWorldDirectorsCutTest::RunTest(const FString& Parameters)
{
	FFlowTestWorld Test;
	Test.Controller->StartDirectorsCut();
	TestEqual(TEXT("playing"), Test.Controller->GetScreen(), EFlowScreen::Playing);
	TestEqual(TEXT("director's cut mode"), Test.Controller->GetPlayMode(), EUmbrellaPlayMode::DirectorsCut);
	TestTrue(TEXT("Ella is possessed"), Cast<AEllaCharacter>(Test.Controller->GetPawn()) != nullptr);
	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FFlowWorldRouteTest, "UmbrellaElla.Flow.World.DirectorsCutReachesFirstCheckpointWithRoute",
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FFlowWorldRouteTest::RunTest(const FString& Parameters)
{
	FFlowTestWorld Test;
	Test.Controller->StartDirectorsCut();
	AUmbrellaGameMode* Mode = Test.World->GetAuthGameMode<AUmbrellaGameMode>();
	AUmbrellaLevelDirector* Level = Mode ? Mode->GetLevelDirector() : nullptr;
	if (!TestNotNull(TEXT("level director spawned"), Level))
	{
		return false;
	}
	TestEqual(TEXT("nine chunks"), Level->GetSlotsSpawned(), 9);
	TestFalse(TEXT("Keeper not started yet"), Level->HasHandedOff());
	const APawn* Pawn = Test.Controller->GetPawn();
	if (!TestNotNull(TEXT("Ella"), Pawn))
	{
		return false;
	}
	TestEqual(TEXT("Ella stands at checkpoint 1"), Pawn->GetActorLocation().X, LevelPlan::CheckpointStandLocation(1).X);
	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FFlowWorldStartGameNoRouteTest, "UmbrellaElla.Flow.World.StartGameSkipsRouteAndStartsKeeper",
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FFlowWorldStartGameNoRouteTest::RunTest(const FString& Parameters)
{
	FFlowTestWorld Test;
	Test.Controller->StartGame();
	AUmbrellaGameMode* Mode = Test.World->GetAuthGameMode<AUmbrellaGameMode>();
	TestTrue(TEXT("fight started"), Mode && Mode->IsFightStarted());
	TestTrue(TEXT("no level director"), Mode && Mode->GetLevelDirector() == nullptr);
	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FFlowWorldMenuTest, "UmbrellaElla.Flow.World.MenuBlocksGameplayInput",
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FFlowWorldMenuTest::RunTest(const FString& Parameters)
{
	FFlowTestWorld Test;
	TestTrue(TEXT("the title blocks gameplay input"), Test.Controller->IsGameplayInputBlocked());
	Test.Controller->StartGame();
	TestFalse(TEXT("playing takes gameplay input"), Test.Controller->IsGameplayInputBlocked());

	Test.Controller->ApplyCommand(EFlowCommand::Pause);
	TestEqual(TEXT("paused"), Test.Controller->GetScreen(), EFlowScreen::Paused);
	TestTrue(TEXT("pause blocks gameplay input"), Test.Controller->IsGameplayInputBlocked());
	// World::IsPaused also waits PauseDelay of game time; the pauser is the immediate request.
	TestTrue(TEXT("pause freezes the world"), Test.World->GetWorldSettings()->GetPauserPlayerState() != nullptr);

	Test.Controller->ApplyCommand(EFlowCommand::Continue);
	TestEqual(TEXT("resume waits"), Test.Controller->GetScreen(), EFlowScreen::Resuming);
	TestTrue(TEXT("still blocked while waiting for neutral"), Test.Controller->IsGameplayInputBlocked());
	Test.Controller->TickFlow(1.0f);
	TestEqual(TEXT("playing again"), Test.Controller->GetScreen(), EFlowScreen::Playing);
	TestFalse(TEXT("gameplay input is back"), Test.Controller->IsGameplayInputBlocked());
	TestFalse(TEXT("world runs again"), Test.World->GetWorldSettings()->GetPauserPlayerState() != nullptr);
	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FFlowWorldDefeatTest, "UmbrellaElla.Flow.World.DefeatShowsRetryAndRetryResets",
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FFlowWorldDefeatTest::RunTest(const FString& Parameters)
{
	FFlowTestWorld Test;
	Test.Controller->StartGame();
	Test.Broadcast(EUmbrellaEventType::PlayerDefeated);
	TestEqual(TEXT("retry screen"), Test.Controller->GetScreen(), EFlowScreen::Defeat);
	TestEqual(TEXT("nothing reset yet"), Test.Controller->GetRetryCount(), 0);

	Test.Controller->ApplyCommand(EFlowCommand::Retry);
	TestEqual(TEXT("retry reset the encounter once"), Test.Controller->GetRetryCount(), 1);
	TestEqual(TEXT("resume waits for neutral"), Test.Controller->GetScreen(), EFlowScreen::Resuming);
	Test.Controller->TickFlow(1.0f);
	TestEqual(TEXT("fight again"), Test.Controller->GetScreen(), EFlowScreen::Playing);
	TestTrue(TEXT("Ella is back"), Test.Controller->GetPawn() != nullptr);
	const UEncounterDirectorSubsystem* Director = Test.World->GetSubsystem<UEncounterDirectorSubsystem>();
	TestTrue(TEXT("the director is Ready or Active again after the reset"),
		Director && (Director->GetState() == EEncounterState::Ready || Director->GetState() == EEncounterState::Active));
	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FFlowWorldWinTest, "UmbrellaElla.Flow.World.EncounterCompletedReachesCredits",
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FFlowWorldWinTest::RunTest(const FString& Parameters)
{
	FFlowTestWorld Test;
	Test.Controller->StartGame();
	Test.Broadcast(EUmbrellaEventType::EncounterCompleted);
	TestEqual(TEXT("story over the background"), Test.Controller->GetScreen(), EFlowScreen::Story);

	// Tick in small steps through every story page, then the credits.
	for (int32 Step = 0; Step < 600 && Test.Controller->GetScreen() == EFlowScreen::Story; ++Step)
	{
		Test.Controller->TickFlow(0.5f);
	}
	TestEqual(TEXT("credits follow the story"), Test.Controller->GetScreen(), EFlowScreen::Credits);
	for (int32 Step = 0; Step < 600 && Test.Controller->GetScreen() == EFlowScreen::Credits; ++Step)
	{
		Test.Controller->TickFlow(0.5f);
	}
	TestEqual(TEXT("title after the credits"), Test.Controller->GetScreen(), EFlowScreen::Title);
	TestTrue(TEXT("the title was requested"), Test.Controller->HasRequestedTitleReturn());
	return true;
}

#endif

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FFlowWorldPurchaseDraftTest, "UmbrellaElla.Flow.World.LeavingPurchaseDiscardsDraft",
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FFlowWorldPurchaseDraftTest::RunTest(const FString& Parameters)
{
	FFlowTestWorld Test;
	// The test game instance has no subsystems until it is initialised.
	Test.Instance->Init();
	UProgressionSubsystem* Progression = UProgressionSubsystem::Get(Test.World);
	if (!TestNotNull(TEXT("progression subsystem"), Progression))
	{
		return false;
	}
	Progression->UseSaveSlot(FString());
	Progression->SetPlayMode(EUmbrellaPlayMode::DirectorsCut);
	Progression->BeginShadowProgress(10);
	// Widgets need a local player; the test world has none, so give the controller one.
	Test.Controller->SetPlayer(NewObject<ULocalPlayer>(GEngine, GEngine->LocalPlayerClass));
	Test.Controller->ApplyCommand(EFlowCommand::OpenPurchase);
	TestEqual(TEXT("purchase screen"), Test.Controller->GetScreen(), EFlowScreen::Purchase);
	UProgressionPurchaseWidget* Widget = Test.Controller->GetPurchaseWidget();
	if (!TestNotNull(TEXT("purchase widget"), Widget))
	{
		return false;
	}
	// No viewport here, so build the Slate tree by hand; that runs NativeConstruct and starts the draft.
	Widget->TakeWidget();
	Widget->StageBuy(EProgressionTrack::HitCapacity);
	TestTrue(TEXT("a staged purchase is a dirty draft"), Widget->IsDraftDirty());
	Test.Controller->ApplyCommand(EFlowCommand::Pause);
	TestEqual(TEXT("pause leaves the purchase screen"), Test.Controller->GetScreen(), EFlowScreen::Title);
	TestNull(TEXT("widget released"), Test.Controller->GetPurchaseWidget());
	TestFalse(TEXT("the unconfirmed draft was discarded"), Widget->IsDraftDirty());
	Progression->EndShadowProgress();
	return true;
}
