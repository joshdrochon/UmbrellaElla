#include "Arena/UmbrellaArena.h"
#include "Camera/CameraComponent.h"
#include "Core/UmbrellaDrawOrder.h"
#include "Core/UmbrellaTuning.h"
#include "Field/WindCurrent.h"
#include "Engine/Engine.h"
#include "Engine/World.h"
#include "Enemy/UmbrellaEnemy.h"
#include "Feedback/Build/BuildIdentity.h"
#include "Components/SceneComponent.h"
#include "GameFramework/Actor.h"
#include "Level/LevelPlan.h"
#include "Level/UmbrellaLevelDirector.h"
#include "Misc/AutomationTest.h"
#include "Trap/UmbrellaTrap.h"

#if WITH_AUTOMATION_TESTS

#define UMBRELLAELLA_LEVELDIR_FLAGS (EAutomationTestFlags::EditorContext | EAutomationTestFlags::ClientContext | EAutomationTestFlags::EngineFilter)

namespace
{
	UWorld* LevelDirTestMakeWorld()
	{
		UWorld* World = UWorld::CreateWorld(EWorldType::Game, false);
		FWorldContext& Context = GEngine->CreateNewWorldContext(EWorldType::Game);
		Context.SetCurrentWorld(World);
		return World;
	}

	void LevelDirTestDestroyWorld(UWorld* World)
	{
		GEngine->DestroyWorldContext(World);
		World->DestroyWorld(false);
	}
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FLevelPlanSeeded, "UmbrellaElla.Level.PlanIsSeededAndOrdered", UMBRELLAELLA_LEVELDIR_FLAGS)
bool FLevelPlanSeeded::RunTest(const FString& Parameters)
{
	const FRoute Route = LevelCatalogue::Generate(1001);
	const TArray<FLevelPlacement> A = LevelPlan::Build(Route);
	const TArray<FLevelPlacement> B = LevelPlan::Build(LevelCatalogue::Generate(1001));
	TestTrue(TEXT("plan not empty"), A.Num() > 0);
	TestEqual(TEXT("same seed same plan size"), A.Num(), B.Num());
	for (int32 I = 0; I < FMath::Min(A.Num(), B.Num()); ++I)
	{
		TestEqual(TEXT("same location"), A[I].Location, B[I].Location);
		TestEqual(TEXT("same colour"), A[I].bYellowShot, B[I].bYellowShot);
	}
	int32 Floors = 0;
	int32 Refuges = 0;
	int32 Checkpoints = 0;
	float LastFloorX = -1.0f;
	for (const FLevelPlacement& P : A)
	{
		if (P.Kind == ELevelPlacementKind::Floor)
		{
			++Floors;
			TestTrue(TEXT("floors in route order"), P.Location.X > LastFloorX);
			LastFloorX = P.Location.X;
		}
		Refuges += P.Kind == ELevelPlacementKind::Refuge;
		Checkpoints += P.Kind == ELevelPlacementKind::Checkpoint;
	}
	TestEqual(TEXT("nine chunk floors"), Floors, 9);
	TestEqual(TEXT("three refuges"), Refuges, 3);
	TestEqual(TEXT("three checkpoints"), Checkpoints, 3);
	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FLevelPlanCheckpoints, "UmbrellaElla.Level.CheckpointsAndHandoff", UMBRELLAELLA_LEVELDIR_FLAGS)
bool FLevelPlanCheckpoints::RunTest(const FString& Parameters)
{
	TestEqual(TEXT("before first refuge"), LevelPlan::CheckpointReachedAt(100.0f), 0);
	TestEqual(TEXT("at refuge 1"), LevelPlan::CheckpointReachedAt(LevelCatalogue::RefugeStartX(1)), 1);
	TestEqual(TEXT("at refuge 3"), LevelPlan::CheckpointReachedAt(LevelCatalogue::RefugeStartX(3) + 10.0f), 3);
	for (int32 Cp = 1; Cp <= 3; ++Cp)
	{
		TestEqual(TEXT("stand point maps back to its checkpoint"), LevelPlan::CheckpointReachedAt(LevelPlan::CheckpointStandLocation(Cp).X), Cp);
	}
	TestTrue(TEXT("handoff inside the route"), LevelPlan::KeeperHandoffX() < LevelCatalogue::RouteLength());
	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FLevelBuildInfoParse, "UmbrellaElla.Level.BuildIdentityRevisionAndManifest", UMBRELLAELLA_LEVELDIR_FLAGS)
bool FLevelBuildInfoParse::RunTest(const FString& Parameters)
{
	const FString Info = TEXT("commit=abc123\ndate=2026-11-12\nasset_manifest=m77\n");
	TestEqual(TEXT("reads asset manifest"), FBuildIdentity::ParseBuildInfoValue(Info, TEXT("asset_manifest")), FString(TEXT("m77")));
	TestEqual(TEXT("reads commit"), FBuildIdentity::ParseBuildInfoValue(Info, TEXT("commit")), FString(TEXT("abc123")));
	TestTrue(TEXT("missing key is empty"), FBuildIdentity::ParseBuildInfoValue(Info, TEXT("nope")).IsEmpty());
	const FBuildIdentity Id = FBuildIdentity::Capture();
	TestFalse(TEXT("revision filled"), Id.Revision.IsEmpty());
	TestFalse(TEXT("asset manifest filled"), Id.AssetManifest.IsEmpty());
	TestTrue(TEXT("record carries revision"), Id.ToText().Contains(TEXT("revision=")));
	TestTrue(TEXT("record carries asset manifest"), Id.ToText().Contains(TEXT("asset_manifest=")));
	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FLevelWorldRoute, "UmbrellaElla.Level.World.RouteSpawnsNineChunks", UMBRELLAELLA_LEVELDIR_FLAGS)
bool FLevelWorldRoute::RunTest(const FString& Parameters)
{
	UWorld* World = LevelDirTestMakeWorld();
	AUmbrellaLevelDirector* Director = World->SpawnActor<AUmbrellaLevelDirector>();
	bool bOk = TestNotNull(TEXT("director"), Director);
	if (bOk)
	{
		TestEqual(TEXT("route built"), Director->BuildRoute(1001), 9);
		TestEqual(TEXT("nine chunks"), Director->GetSlotsSpawned(), 9);
		TestEqual(TEXT("order is the generated route"), Director->GetRoute().Signature(), LevelCatalogue::Generate(1001).Signature());
		TestTrue(TEXT("geometry spawned"), Director->GetSpawned().Num() >= 9 + 3);
		int32 Traps = 0;
		int32 Enemies = 0;
		int32 Winds = 0;
		for (const AActor* A : Director->GetSpawned())
		{
			Traps += Cast<AUmbrellaTrap>(A) != nullptr;
			Enemies += Cast<AUmbrellaEnemy>(A) != nullptr;
			if (const AWindCurrent* W = Cast<AWindCurrent>(A))
			{
				++Winds;
				TestEqual(TEXT("current in Ella's plane"), static_cast<float>(W->GetActorLocation().Y), UmbrellaDrawOrder::EllaY);
				TestTrue(TEXT("current has a direction"), !W->GetDirection().IsNearlyZero());
			}
		}
		int32 PlannedTraps = 0;
		int32 PlannedEnemies = 0;
		int32 PlannedWinds = 0;
		for (const FLevelPlacement& P : Director->GetPlan())
		{
			PlannedTraps += P.Kind == ELevelPlacementKind::Trap;
			PlannedEnemies += P.Kind == ELevelPlacementKind::Enemy;
			PlannedWinds += P.Kind == ELevelPlacementKind::Wind;
		}
		TestEqual(TEXT("traps spawned as planned"), Traps, PlannedTraps);
		TestEqual(TEXT("enemies spawned as planned"), Enemies, PlannedEnemies);
		TestTrue(TEXT("route has currents"), PlannedWinds >= 9 * 3);
		TestEqual(TEXT("currents spawned as planned"), Winds, PlannedWinds);
		AActor* Ella = World->SpawnActor<AActor>();
		USceneComponent* EllaRoot = NewObject<USceneComponent>(Ella, TEXT("Root"));
		Ella->SetRootComponent(EllaRoot);
		EllaRoot->RegisterComponent();
		for (int32 Cp = 1; Cp <= 3; ++Cp)
		{
			TestEqual(TEXT("placed at checkpoint"), Director->PlaceAtCheckpoint(Ella, Cp), Cp);
			TestEqual(TEXT("Ella at the stand point"), Ella->GetActorLocation(), LevelPlan::CheckpointStandLocation(Cp));
		}
		TestEqual(TEXT("checkpoint 4 does not exist"), Director->PlaceAtCheckpoint(Ella, 4), 0);
		Director->ClearRoute();
		TestEqual(TEXT("cleared"), Director->GetSlotsSpawned(), 0);
	}
	LevelDirTestDestroyWorld(World);
	return bOk;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FLevelWorldCamera, "UmbrellaElla.Level.World.CameraFollowsAndCheckpoints", UMBRELLAELLA_LEVELDIR_FLAGS)
bool FLevelWorldCamera::RunTest(const FString& Parameters)
{
	UWorld* World = LevelDirTestMakeWorld();
	AUmbrellaArena* Arena = World->SpawnActor<AUmbrellaArena>();
	AUmbrellaLevelDirector* Director = World->SpawnActor<AUmbrellaLevelDirector>();
	bool bOk = TestNotNull(TEXT("arena and director"), Arena && Director ? Arena : nullptr);
	if (bOk)
	{
		Director->SetArena(Arena);
		Director->BuildRoute(1001);
		const float Width = GetDefault<UUmbrellaTuning>()->ArenaCamera.ArenaWidth;
		Director->StepFollow(Width, 0);
		const float First = Director->GetLastCameraX();
		Director->StepFollow(LevelCatalogue::RefugeStartX(2), 1);
		const float Second = Director->GetLastCameraX();
		TestTrue(TEXT("camera moved forward with Ella"), Second > First);
		TestEqual(TEXT("camera matches the rule"), Second, CameraRules::ScrollCentreX(LevelCatalogue::RefugeStartX(2), 1, Width, 0.0f, LevelCatalogue::RouteLength()));
		TestEqual(TEXT("checkpoint 2 reached"), Director->GetCheckpointReached(), 2);
		TestFalse(TEXT("no handoff mid route"), Director->HasHandedOff());
		Director->StepFollow(LevelPlan::KeeperHandoffX() + 1.0f, 1);
		TestTrue(TEXT("handoff once at the end"), Director->HasHandedOff());
		TestEqual(TEXT("checkpoint 3 reached"), Director->GetCheckpointReached(), 3);
	}
	LevelDirTestDestroyWorld(World);
	return bOk;
}

#endif
