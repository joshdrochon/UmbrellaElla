#include "Misc/AutomationTest.h"

#if WITH_AUTOMATION_TESTS

#include "Core/UmbrellaEventBus.h"
#include "Core/UmbrellaGameMode.h"
#include "Core/UmbrellaTuning.h"
#include "Engine/Engine.h"
#include "Engine/GameInstance.h"
#include "Engine/World.h"
#include "Flow/FlowRules.h"
#include "Flow/FlowStoryText.h"
#include "Flow/UmbrellaPlayerController.h"
#include "GameFramework/PlayerState.h"
#include "GameFramework/WorldSettings.h"
#include "Input/UmbrellaInputBindings.h"
#include "Progression/ProgressionSubsystem.h"
#include "Story/StorySubsystem.h"

// Story wiring in flow (area storyflow): NAR-04 skip routing, NAR-07 / FLOW-49 one ending timeline.

namespace
{
	/** A transient game world with the Umbrella game mode, one flow controller and story progress kept in memory. */
	struct FStoryFlowTestWorld
	{
		UWorld* World = nullptr;
		UGameInstance* Instance = nullptr;
		AUmbrellaPlayerController* Controller = nullptr;
		UStorySubsystem* Story = nullptr;

		explicit FStoryFlowTestWorld(const FStoryProgress& Progress)
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
			Story = World->GetSubsystem<UStorySubsystem>();
			if (Story)
			{
				// Never touch the player's saved story flags from a test.
				Story->KeepProgressInMemoryOnly();
				Story->SetProgress(Progress);
			}
			Controller = World->SpawnActor<AUmbrellaPlayerController>();
			Controller->PlayerState = World->SpawnActor<APlayerState>();
			Controller->KeepTutorialInMemoryOnly();
			Controller->MarkTutorialSeen();
		}

		~FStoryFlowTestWorld()
		{
			GEngine->DestroyWorldContext(World);
			World->DestroyWorld(false);
			Instance->RemoveFromRoot();
		}

		void Broadcast(EUmbrellaEventType Type, int32 Amount = 0) const
		{
			FUmbrellaEvent Event;
			Event.Type = Type;
			Event.Amount = Amount;
			UUmbrellaEventBus::Get(World)->Broadcast(Event);
		}

		/** Tick flow (and story, which runs on the world tick) until the screen changes or the step budget runs out. */
		void TickWhile(EFlowScreen Screen, float Step, int32 MaxSteps) const
		{
			for (int32 Index = 0; Index < MaxSteps && Controller->GetScreen() == Screen; ++Index)
			{
				Controller->TickFlow(Step);
				if (Story)
				{
					Story->Tick(Step);
				}
			}
		}

		/** Start a Director's Cut run past a run-start purchase screen if progression offers one. */
		void StartDirectorsCut() const
		{
			Controller->StartDirectorsCut();
			if (Controller->GetScreen() == EFlowScreen::Purchase)
			{
				Controller->ApplyCommand(EFlowCommand::Continue);
				Controller->StartDirectorsCut();
			}
		}
	};

	FStoryProgress StoryFlowProgress(bool bOpeningSeen, bool bFirstWinSeen)
	{
		FStoryProgress Progress;
		Progress.bOpeningSeen = bOpeningSeen;
		Progress.bFirstWinSeen = bFirstWinSeen;
		return Progress;
	}
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FFlowEndingRulesTest, "UmbrellaElla.Flow.EndingTimelineRules",
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FFlowEndingRulesTest::RunTest(const FString& Parameters)
{
	TestTrue(TEXT("hold at the start of the story screen"), FFlowRules::IsEndingHoldAt(0.0f, 2.5f));
	TestTrue(TEXT("still holding at 2.4 s"), FFlowRules::IsEndingHoldAt(2.4f, 2.5f));
	TestFalse(TEXT("hold over at 2.5 s"), FFlowRules::IsEndingHoldAt(2.5f, 2.5f));
	TestEqual(TEXT("no page during the hold"), FFlowRules::EndingPageAt(1.0f, 2.5f, 5.0f, 3), static_cast<int32>(INDEX_NONE));
	TestEqual(TEXT("first page after the hold"), FFlowRules::EndingPageAt(2.5f, 2.5f, 5.0f, 3), 0);
	TestEqual(TEXT("third page"), FFlowRules::EndingPageAt(12.6f, 2.5f, 5.0f, 3), 2);
	TestEqual(TEXT("story over after the last page"), FFlowRules::EndingPageAt(17.5f, 2.5f, 5.0f, 3), static_cast<int32>(INDEX_NONE));
	TestEqual(TEXT("no hold: pages start at once"), FFlowRules::EndingPageAt(0.0f, 0.0f, 8.0f, 2), 0);

	TestEqual(TEXT("Director's Cut credits lead to Journey Complete"),
		FFlowRules::AfterCredits(EUmbrellaPlayMode::DirectorsCut, true), EFlowCommand::ShowStatistics);
	TestEqual(TEXT("Start Game credits lead to the title"),
		FFlowRules::AfterCredits(EUmbrellaPlayMode::StartGame, true), EFlowCommand::TimelineDone);
	TestEqual(TEXT("statistics off: title"), FFlowRules::AfterCredits(EUmbrellaPlayMode::DirectorsCut, false), EFlowCommand::TimelineDone);
	TestEqual(TEXT("credits then statistics"), FFlowRules::Next(EFlowScreen::Credits, EFlowCommand::ShowStatistics), EFlowScreen::Statistics);
	TestEqual(TEXT("skip from story to statistics"), FFlowRules::Next(EFlowScreen::Story, EFlowCommand::ShowStatistics), EFlowScreen::Statistics);
	TestEqual(TEXT("statistics are not reachable from play"), FFlowRules::Next(EFlowScreen::Playing, EFlowCommand::ShowStatistics), EFlowScreen::Playing);
	TestEqual(TEXT("death never leads to statistics"), FFlowRules::Next(EFlowScreen::Defeat, EFlowCommand::ShowStatistics), EFlowScreen::Defeat);
	TestEqual(TEXT("statistics ignore pause"), FFlowRules::Next(EFlowScreen::Statistics, EFlowCommand::Pause), EFlowScreen::Statistics);
	TestEqual(TEXT("statistics ignore timeline ends"), FFlowRules::Next(EFlowScreen::Statistics, EFlowCommand::TimelineDone), EFlowScreen::Statistics);
	TestTrue(TEXT("statistics block gameplay input"), FFlowRules::IsInputBlockedOn(EFlowScreen::Statistics));

	TestTrue(TEXT("Try Again option found"), FFlowRules::IsTryAgainStart(FString::Printf(TEXT("?Game=X?%s"), FFlowRules::TryAgainOption())));
	TestTrue(TEXT("Try Again option with a value"), FFlowRules::IsTryAgainStart(FString::Printf(TEXT("?%s=1"), FFlowRules::TryAgainOption())));
	TestFalse(TEXT("plain load is not Try Again"), FFlowRules::IsTryAgainStart(TEXT("?Game=X?listen")));
	TestFalse(TEXT("whole keys only"), FFlowRules::IsTryAgainStart(FString::Printf(TEXT("?%sLater"), FFlowRules::TryAgainOption())));

	// NAR-04: a skip key bound to a gameplay action would leak the press into play.
	const TArray<FUmbrellaDefaultBinding> Gameplay = UmbrellaInputBindings::BuildDefaults();
	TestTrue(TEXT("skip keys exist"), FFlowRules::StorySkipKeys().Num() > 0);
	for (const FKey& Key : FFlowRules::StorySkipKeys())
	{
		bool bUsed = false;
		for (const FUmbrellaDefaultBinding& Binding : Gameplay)
		{
			bUsed |= Binding.Key == Key;
		}
		TestFalse(FString::Printf(TEXT("skip key %s is no gameplay key"), *Key.ToString()), bUsed);
	}
	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FFlowWorldDirectorsCutEndingTest, "UmbrellaElla.Flow.World.DirectorsCutEndingOneTimeline",
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FFlowWorldDirectorsCutEndingTest::RunTest(const FString& Parameters)
{
	FStoryFlowTestWorld Test(StoryFlowProgress(true, false));
	if (!TestNotNull(TEXT("story subsystem"), Test.Story))
	{
		return false;
	}
	Test.StartDirectorsCut();
	TestEqual(TEXT("playing"), Test.Controller->GetScreen(), EFlowScreen::Playing);
	TestTrue(TEXT("story runs Director's Cut"), Test.Story->GetModel().IsDirectorsCut());
	Test.Broadcast(EUmbrellaEventType::XPAwarded, 12);

	Test.Broadcast(EUmbrellaEventType::EncounterCompleted);
	TestEqual(TEXT("win: story screen"), Test.Controller->GetScreen(), EFlowScreen::Story);
	TestTrue(TEXT("holding on Ella"), Test.Controller->IsInEndingHold());
	TestTrue(TEXT("story follows: hold"), Test.Story->GetModel().GetEndingStage() == EStoryEndingStage::Hold);
	TestTrue(TEXT("light still falls in the hold"), Test.Story->IsLightShaftOn());

	const float Hold = GetDefault<UUmbrellaTuning>()->Story.EndingHoldSeconds;
	Test.Controller->TickFlow(Hold * 0.5f);
	TestTrue(TEXT("still holding halfway"), Test.Controller->IsInEndingHold());
	Test.Controller->TickFlow(Hold * 0.5f + 0.01f);
	TestFalse(TEXT("hold over"), Test.Controller->IsInEndingHold());
	TestTrue(TEXT("story follows: story text"), Test.Story->GetModel().GetEndingStage() == EStoryEndingStage::StoryText);
	TestFalse(TEXT("light shaft off on the ending background"), Test.Story->IsLightShaftOn());

	const TArray<FText> Pages = Test.Controller->GetEndingPages();
	const TArray<FString> Lines = Test.Story->GetEndingLines();
	TestTrue(TEXT("story lines exist"), Lines.Num() > 0);
	TestEqual(TEXT("one text source: flow pages are the story's ending lines"), Pages.Num(), Lines.Num());
	TestTrue(TEXT("first page is the first ending line"), Pages.Num() > 0 && Lines.Num() > 0 && Pages[0].ToString() == Lines[0]);

	Test.Broadcast(EUmbrellaEventType::XPAwarded, 40);
	Test.Controller->PressSkip();
	TestEqual(TEXT("first win: skip does nothing"), Test.Controller->GetScreen(), EFlowScreen::Story);

	Test.TickWhile(EFlowScreen::Story, 0.25f, 400);
	TestEqual(TEXT("credits follow the story"), Test.Controller->GetScreen(), EFlowScreen::Credits);
	TestTrue(TEXT("story follows: credits"), Test.Story->GetModel().GetEndingStage() == EStoryEndingStage::Credits);
	TestFalse(TEXT("no statistics during the credits"), Test.Story->GetModel().ShouldShowStatistics());

	Test.TickWhile(EFlowScreen::Credits, 0.25f, 400);
	TestEqual(TEXT("Journey Complete after the credits"), Test.Controller->GetScreen(), EFlowScreen::Statistics);
	TestTrue(TEXT("story shows statistics"), Test.Story->GetModel().ShouldShowStatistics());
	TestTrue(TEXT("first win saved"), Test.Story->GetModel().GetProgress().bFirstWinSeen);
	TestEqual(TEXT("current-run XP, frozen at the win"), Test.Story->GetModel().GetStats().XpEarned, 12);
	TestFalse(TEXT("not sent to the title"), Test.Controller->HasRequestedTitleReturn());

	Test.Controller->TickFlow(60.0f);
	TestEqual(TEXT("Journey Complete waits for a choice"), Test.Controller->GetScreen(), EFlowScreen::Statistics);
	Test.Story->GetTryAgainDelegate().Broadcast();
	TestTrue(TEXT("Try Again reaches flow"), Test.Controller->HasRequestedTryAgain());
	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FFlowWorldLaterWinSkipTest, "UmbrellaElla.Flow.World.LaterWinSkipsToStatistics",
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FFlowWorldLaterWinSkipTest::RunTest(const FString& Parameters)
{
	FStoryFlowTestWorld Test(StoryFlowProgress(true, true));
	if (!TestNotNull(TEXT("story subsystem"), Test.Story))
	{
		return false;
	}
	Test.StartDirectorsCut();
	Test.Broadcast(EUmbrellaEventType::EncounterCompleted);
	Test.Controller->PressSkip();
	TestEqual(TEXT("no skip during the hold"), Test.Controller->GetScreen(), EFlowScreen::Story);
	Test.Controller->TickFlow(GetDefault<UUmbrellaTuning>()->Story.EndingHoldSeconds + 0.1f);
	Test.Controller->PressSkip();
	TestEqual(TEXT("later win: skip from the story goes to Journey Complete"), Test.Controller->GetScreen(), EFlowScreen::Statistics);
	TestTrue(TEXT("story shows statistics"), Test.Story->GetModel().ShouldShowStatistics());

	FStoryFlowTestWorld Credits(StoryFlowProgress(true, true));
	Credits.StartDirectorsCut();
	Credits.Broadcast(EUmbrellaEventType::EncounterCompleted);
	Credits.TickWhile(EFlowScreen::Story, 0.25f, 400);
	TestEqual(TEXT("credits reached"), Credits.Controller->GetScreen(), EFlowScreen::Credits);
	Credits.Controller->PressSkip();
	TestEqual(TEXT("later win: skip from the credits goes to Journey Complete"), Credits.Controller->GetScreen(), EFlowScreen::Statistics);
	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FFlowWorldStartGameEndingTest, "UmbrellaElla.Flow.World.StartGameEndingHasNoStatistics",
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FFlowWorldStartGameEndingTest::RunTest(const FString& Parameters)
{
	FStoryFlowTestWorld Test(StoryFlowProgress(true, true));
	Test.Controller->StartGame();
	Test.Broadcast(EUmbrellaEventType::EncounterCompleted);
	TestTrue(TEXT("Start Game holds too"), Test.Controller->IsInEndingHold());
	TestEqual(TEXT("Start Game keeps flow's ending pages"), Test.Controller->GetEndingPages().Num(), FFlowStoryText::GetEndingPages().Num());
	Test.Controller->TickFlow(GetDefault<UUmbrellaTuning>()->Story.EndingHoldSeconds + 0.1f);
	Test.Controller->PressSkip();
	TestEqual(TEXT("no skip in Start Game"), Test.Controller->GetScreen(), EFlowScreen::Story);
	Test.TickWhile(EFlowScreen::Story, 0.5f, 600);
	TestEqual(TEXT("credits"), Test.Controller->GetScreen(), EFlowScreen::Credits);
	Test.TickWhile(EFlowScreen::Credits, 0.5f, 600);
	TestEqual(TEXT("title after the credits, no statistics"), Test.Controller->GetScreen(), EFlowScreen::Title);
	TestTrue(TEXT("title requested"), Test.Controller->HasRequestedTitleReturn());
	if (Test.Story)
	{
		TestFalse(TEXT("story stays out of Start Game"), Test.Story->GetModel().ShouldShowStatistics());
	}
	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FFlowWorldOpeningSkipTest, "UmbrellaElla.Flow.World.OpeningSkipGoesToStory",
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FFlowWorldOpeningSkipTest::RunTest(const FString& Parameters)
{
	FStoryFlowTestWorld First(StoryFlowProgress(false, false));
	if (!TestNotNull(TEXT("story subsystem"), First.Story))
	{
		return false;
	}
	First.StartDirectorsCut();
	First.Story->Tick(0.1f);
	TestTrue(TEXT("opening caption up"), First.Story->GetModel().IsOpeningShowing());
	TestTrue(TEXT("the press belongs to the story"), First.Story->IsSkipPressForStory());
	First.Controller->PressSkip();
	TestTrue(TEXT("first viewing is not skippable"), First.Story->GetModel().IsOpeningShowing());
	TestEqual(TEXT("still playing: the press only reached the story"), First.Controller->GetScreen(), EFlowScreen::Playing);

	FStoryFlowTestWorld Later(StoryFlowProgress(true, false));
	Later.StartDirectorsCut();
	Later.Story->Tick(0.1f);
	TestTrue(TEXT("opening caption up on a later start"), Later.Story->GetModel().IsOpeningShowing());
	Later.Controller->PressSkip();
	TestFalse(TEXT("later start: skip clears it"), Later.Story->GetModel().IsOpeningShowing());
	TestFalse(TEXT("ending flag untouched by the opening"), Later.Story->GetModel().GetProgress().bFirstWinSeen);
	TestEqual(TEXT("still playing"), Later.Controller->GetScreen(), EFlowScreen::Playing);
	return true;
}

#endif
