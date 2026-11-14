#include "Misc/AutomationTest.h"

#if WITH_AUTOMATION_TESTS

#include "Arena/UmbrellaArena.h"
#include "Camera/CameraComponent.h"
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
#include "Owl/KeeperOfTime.h"
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

	/** True when World lies inside the orthographic play camera's frame (X across, Z up), i.e. it projects into the viewport. */
	bool LevelFlowInCameraFrame(const UCameraComponent* Camera, const FVector& World)
	{
		const FVector Centre = Camera->GetComponentLocation();
		const double HalfW = 0.5 * Camera->OrthoWidth;
		const double HalfH = HalfW / Camera->AspectRatio;
		return FMath::Abs(World.X - Centre.X) <= HalfW && FMath::Abs(World.Z - Centre.Z) <= HalfH;
	}

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

// B6 / B5: Director's Cut keeps the action in the camera frame. At the route start Ella stands inside the first view
// (CP0 used to be x -720, left of the camera clamp). At the Keeper handoff the arena moves to the route end, so the
// fixed arena camera frames both Ella and the freshly spawned Keeper; the scroll stops. Start Game keeps its arena put.
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FLevelFlowDirectorsCutFramesFight, "UmbrellaElla.Level.World.DirectorsCutFramesEllaAndKeeper",
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FLevelFlowDirectorsCutFramesFight::RunTest(const FString& Parameters)
{
	FLevelFlowWorld Test;
	Test.Controller->StartDirectorsCut();
	AUmbrellaGameMode* Mode = Test.World->GetAuthGameMode<AUmbrellaGameMode>();
	AUmbrellaLevelDirector* Level = Mode ? Mode->GetLevelDirector() : nullptr;
	AUmbrellaArena* Arena = Mode ? Mode->GetArena() : nullptr;
	APawn* Ella = Test.Controller->GetPawn();
	const UEncounterDirectorSubsystem* Encounter = Test.World->GetSubsystem<UEncounterDirectorSubsystem>();
	if (!TestNotNull(TEXT("route built"), Level) || !TestNotNull(TEXT("arena"), Arena) || !TestNotNull(TEXT("Ella"), Ella)
		|| !TestNotNull(TEXT("encounter"), Encounter) || !TestNotNull(TEXT("play camera"), Arena->GetPlayCamera()))
	{
		return false;
	}
	const UCameraComponent* Camera = Arena->GetPlayCamera();
	const FVector Home = Arena->GetActorLocation();

	// B6: route start, after the first follow step.
	Level->Tick(1.0f / 60.0f);
	TestTrue(TEXT("route start: Ella in the camera frame"), LevelFlowInCameraFrame(Camera, Ella->GetActorLocation()));
	TestTrue(TEXT("route start: Ella on the route (x >= 0)"), Ella->GetActorLocation().X >= LevelCatalogue::SlotStartX(0));

	// Mid route the camera scrolls with her.
	FVector At = LevelPlan::CheckpointStandLocation(2);
	Ella->SetActorLocation(At);
	Level->Tick(1.0f / 60.0f);
	TestTrue(TEXT("mid route: Ella in the camera frame"), LevelFlowInCameraFrame(Camera, Ella->GetActorLocation()));

	// B5: over the handoff line.
	At.X = LevelPlan::KeeperHandoffX() + 1.0f;
	Ella->SetActorLocation(At);
	Level->Tick(1.0f / 60.0f);
	TestTrue(TEXT("handed off"), Level->HasHandedOff());
	TestEqual(TEXT("Keeper fight active"), Encounter->GetState(), EEncounterState::Active);
	const AKeeperOfTime* Keeper = Encounter->GetKeeper();
	if (!TestNotNull(TEXT("Keeper spawned"), Keeper))
	{
		return false;
	}
	TestTrue(TEXT("arena at the route end"), Arena->GetActorLocation().Equals(LevelPlan::KeeperArenaOrigin()));
	TestTrue(TEXT("camera on the fixed arena frame"), Arena->IsCameraOnArenaFrame());
	TestTrue(TEXT("fight: Ella in the camera frame"), LevelFlowInCameraFrame(Camera, Ella->GetActorLocation()));
	TestTrue(TEXT("fight: Keeper in the camera frame"), LevelFlowInCameraFrame(Camera, Keeper->GetActorLocation()));
	TestTrue(TEXT("fight: Keeper at the moved anchor"), FMath::IsNearlyEqual(Keeper->GetActorLocation().X, Arena->GetKeeperAnchorLocation().X, 1.0));

	// Ella moving on does not scroll the fight away.
	const FVector FightCamera = Camera->GetComponentLocation();
	At.X += 0.25 * Camera->OrthoWidth;
	Ella->SetActorLocation(At);
	Level->Tick(1.0f / 60.0f);
	TestTrue(TEXT("fight camera holds"), Camera->GetComponentLocation().Equals(FightCamera));

	// A rebuilt route puts the arena home.
	Level->ClearRoute();
	TestTrue(TEXT("cleared route: arena home"), Arena->GetActorLocation().Equals(Home));
	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FLevelFlowStartGameArenaStays, "UmbrellaElla.Level.World.StartGameKeepsArenaAndKeeperFrame",
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FLevelFlowStartGameArenaStays::RunTest(const FString& Parameters)
{
	FLevelFlowWorld Test;
	Test.Controller->StartGame();
	AUmbrellaGameMode* Mode = Test.World->GetAuthGameMode<AUmbrellaGameMode>();
	AUmbrellaArena* Arena = Mode ? Mode->GetArena() : nullptr;
	const UEncounterDirectorSubsystem* Encounter = Test.World->GetSubsystem<UEncounterDirectorSubsystem>();
	if (!TestNotNull(TEXT("arena"), Arena) || !TestNotNull(TEXT("encounter"), Encounter))
	{
		return false;
	}
	TestTrue(TEXT("Start Game: arena at the origin"), Arena->GetActorLocation().Equals(FVector::ZeroVector));
	TestTrue(TEXT("Start Game: camera on the fixed arena frame"), Arena->IsCameraOnArenaFrame());
	if (const AKeeperOfTime* Keeper = Encounter->GetKeeper())
	{
		TestTrue(TEXT("Start Game: Keeper in the camera frame"), LevelFlowInCameraFrame(Arena->GetPlayCamera(), Keeper->GetActorLocation()));
	}
	if (const APawn* Ella = Test.Controller->GetPawn())
	{
		TestTrue(TEXT("Start Game: Ella in the camera frame"), LevelFlowInCameraFrame(Arena->GetPlayCamera(), Ella->GetActorLocation()));
	}
	return true;
}

#endif
