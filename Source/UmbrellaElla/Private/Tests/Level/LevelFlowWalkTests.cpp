#include "Misc/AutomationTest.h"

#if WITH_AUTOMATION_TESTS

#include "Core/EllaCharacter.h"
#include "Core/UmbrellaEventBus.h"
#include "Core/UmbrellaGameMode.h"
#include "Encounter/EncounterDirectorSubsystem.h"
#include "Enemy/UmbrellaEnemy.h"
#include "Engine/Engine.h"
#include "Engine/GameInstance.h"
#include "Engine/World.h"
#include "Flow/FlowRules.h"
#include "Flow/UmbrellaPlayerController.h"
#include "GameFramework/PlayerState.h"
#include "GameFramework/WorldSettings.h"
#include "Level/LevelPlan.h"
#include "Level/UmbrellaLevelDirector.h"
#include "Trap/UmbrellaTrap.h"

namespace
{
	/** A transient game world with the Umbrella game mode and one flow controller, as the menu starts it. */
	struct FLevelFlowWorld
	{
		UWorld* World = nullptr;
		UGameInstance* Instance = nullptr;
		AUmbrellaPlayerController* Controller = nullptr;

		FLevelFlowWorld()
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
			Controller->PlayerState = World->SpawnActor<APlayerState>();
			Controller->KeepTutorialInMemoryOnly();
			Controller->MarkTutorialSeen();
		}

		~FLevelFlowWorld()
		{
			GEngine->DestroyWorldContext(World);
			World->DestroyWorld(false);
			Instance->RemoveFromRoot();
		}
	};

	int32 LevelFlowCountRouteThreats(const AUmbrellaLevelDirector* Level)
	{
		int32 Count = 0;
		for (const TObjectPtr<AActor>& A : Level->GetSpawned())
		{
			if (IsValid(A) && (A->IsA<AUmbrellaEnemy>() || A->IsA<AUmbrellaTrap>()))
			{
				++Count;
			}
		}
		return Count;
	}
}

// FLOW-02 / FLOW-24 / FLOW-28: the Director's Cut menu choice walks the whole route in one run: Ella starts at CP0, each
// refuge raises CheckpointReached once in order, nothing hands off before the end, and crossing the handoff clears the
// route threats and starts the Keeper fight. Ella is moved and the director ticks as the game does each frame.
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FLevelFlowWalkRouteToKeeper, "UmbrellaElla.Level.World.DirectorsCutWalksRouteToKeeper",
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FLevelFlowWalkRouteToKeeper::RunTest(const FString& Parameters)
{
	FLevelFlowWorld Test;
	const TSharedRef<TArray<FName>> Reached = MakeShared<TArray<FName>>();
	const TSharedRef<FName> RouteSource = MakeShared<FName>();
	// The Keeper fight also raises CheckpointReached for its phases (source KeeperOfTime); count the route's own only.
	const FDelegateHandle Handle = UUmbrellaEventBus::Get(Test.World)->On(EUmbrellaEventType::CheckpointReached).AddLambda(
		[Reached, RouteSource](const FUmbrellaEvent& Event)
		{
			if (Event.SourceId == *RouteSource)
			{
				Reached->Add(Event.Detail);
			}
		});

	Test.Controller->StartDirectorsCut();
	TestEqual(TEXT("playing"), Test.Controller->GetScreen(), EFlowScreen::Playing);
	AUmbrellaGameMode* Mode = Test.World->GetAuthGameMode<AUmbrellaGameMode>();
	AUmbrellaLevelDirector* Level = Mode ? Mode->GetLevelDirector() : nullptr;
	APawn* Ella = Test.Controller->GetPawn();
	const UEncounterDirectorSubsystem* Encounter = Test.World->GetSubsystem<UEncounterDirectorSubsystem>();
	if (!TestNotNull(TEXT("route built"), Level) || !TestNotNull(TEXT("Ella"), Ella) || !TestNotNull(TEXT("encounter"), Encounter))
	{
		UUmbrellaEventBus::Get(Test.World)->On(EUmbrellaEventType::CheckpointReached).Remove(Handle);
		return false;
	}
	*RouteSource = Level->GetFName();
	TestEqual(TEXT("nine chunks"), Level->GetSlotsSpawned(), 9);
	TestTrue(TEXT("the route has threats"), LevelFlowCountRouteThreats(Level) > 0);
	TestTrue(TEXT("Keeper fight not active on the route"), Encounter->GetState() != EEncounterState::Active);

	// Walk: each refuge in order, then just short of the handoff, then over it.
	for (int32 Checkpoint = 1; Checkpoint <= LevelPlanConst::MaxCheckpoint; ++Checkpoint)
	{
		Ella->SetActorLocation(LevelPlan::CheckpointStandLocation(Checkpoint));
		Level->Tick(1.0f / 60.0f);
		TestEqual(*FString::Printf(TEXT("CP%d reached"), Checkpoint), Level->GetCheckpointReached(), Checkpoint);
		TestFalse(*FString::Printf(TEXT("no handoff at CP%d"), Checkpoint), Level->HasHandedOff());
	}
	FVector Short = Ella->GetActorLocation();
	Short.X = LevelPlan::KeeperHandoffX() - 1.0f;
	Ella->SetActorLocation(Short);
	Level->Tick(1.0f / 60.0f);
	TestFalse(TEXT("no handoff short of the line"), Level->HasHandedOff());
	TestTrue(TEXT("still no Keeper fight"), Encounter->GetState() != EEncounterState::Active);

	FVector Over = Short;
	Over.X = LevelPlan::KeeperHandoffX() + 1.0f;
	Ella->SetActorLocation(Over);
	Level->Tick(1.0f / 60.0f);
	UUmbrellaEventBus::Get(Test.World)->On(EUmbrellaEventType::CheckpointReached).Remove(Handle);

	TestTrue(TEXT("handed off"), Level->HasHandedOff());
	TestEqual(TEXT("Keeper fight active"), Encounter->GetState(), EEncounterState::Active);
	TestEqual(TEXT("route threats cleared (FLOW-28)"), LevelFlowCountRouteThreats(Level), 0);
	TestEqual(TEXT("checkpoint events, once each"), Reached->Num(), LevelPlanConst::MaxCheckpoint);
	for (int32 Index = 0; Index < Reached->Num(); ++Index)
	{
		TestEqual(TEXT("checkpoint order"), (*Reached)[Index], FName(*FString::Printf(TEXT("CP%d"), Index + 1)));
	}
	TestEqual(TEXT("still Director's Cut"), Test.Controller->GetPlayMode(), EUmbrellaPlayMode::DirectorsCut);
	TestEqual(TEXT("still playing"), Test.Controller->GetScreen(), EFlowScreen::Playing);
	return true;
}

#endif
