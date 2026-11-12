#include "Arena/UmbrellaArena.h"
#include "Camera/CameraComponent.h"
#include "Components/BoxComponent.h"
#include "Components/StaticMeshComponent.h"
#include "Core/UmbrellaCollision.h"
#include "Core/UmbrellaEventBus.h"
#include "Core/UmbrellaTuning.h"
#include "Engine/World.h"
#include "Misc/AutomationTest.h"
#include "Tests/AutomationCommon.h"

#if WITH_AUTOMATION_TESTS

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FArenaLoopWraps, "UmbrellaElla.Arena.BackgroundLoopWraps",
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::ClientContext | EAutomationTestFlags::EngineFilter)

bool FArenaLoopWraps::RunTest(const FString& Parameters)
{
	float Offset = 0.0f;
	TestFalse(TEXT("no wrap below period"), AUmbrellaArena::HasWrappedAfterAdvance(Offset, 100.0f, 1.0f, 1920.0f));
	TestEqual(TEXT("offset advanced"), Offset, 100.0f);
	Offset = 1900.0f;
	TestTrue(TEXT("wraps at period"), AUmbrellaArena::HasWrappedAfterAdvance(Offset, 100.0f, 1.0f, 1920.0f));
	TestEqual(TEXT("offset wrapped"), Offset, 80.0f);
	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FArenaPlaneCover, "UmbrellaElla.Arena.ScrollPlaneCoversView",
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::ClientContext | EAutomationTestFlags::EngineFilter)

bool FArenaPlaneCover::RunTest(const FString& Parameters)
{
	const float Width = 1920.0f;
	const float Scale = 2.0f;
	for (const float Offset : { 0.0f, 960.0f, 1919.0f })
	{
		const float Center = AUmbrellaArena::PlaneCenterX(Offset, Width, Scale);
		TestTrue(TEXT("plane covers left edge"), Center - Width * Scale * 0.5f <= 0.0f);
		TestTrue(TEXT("plane covers right edge"), Center + Width * Scale * 0.5f >= Width);
	}
	TestNotEqual(TEXT("offset moves the plane"), AUmbrellaArena::PlaneCenterX(100.0f, Width, Scale), AUmbrellaArena::PlaneCenterX(0.0f, Width, Scale));
	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FArenaWorldCamera, "UmbrellaElla.Arena.World.CameraAndAnchors",
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::ClientContext | EAutomationTestFlags::EngineFilter)

bool FArenaWorldCamera::RunTest(const FString& Parameters)
{
	UWorld* World = UWorld::CreateWorld(EWorldType::Game, false);
	if (!TestNotNull(TEXT("world"), World))
	{
		return false;
	}
	FWorldContext& Context = GEngine->CreateNewWorldContext(EWorldType::Game);
	Context.SetCurrentWorld(World);
	AUmbrellaArena* Arena = World->SpawnActor<AUmbrellaArena>();
	bool bOk = TestNotNull(TEXT("arena spawned from code"), Arena);
	if (bOk)
	{
		const UCameraComponent* Camera = Arena->GetPlayCamera();
		bOk = TestNotNull(TEXT("camera"), Camera);
		if (bOk)
		{
			TestEqual(TEXT("aspect 16:9"), Camera->AspectRatio, 1.777778f);
			TestTrue(TEXT("aspect constrained"), Camera->bConstrainAspectRatio);
			TestEqual(TEXT("orthographic"), static_cast<int32>(Camera->ProjectionMode), static_cast<int32>(ECameraProjectionMode::Orthographic));
		}
		TArray<UBoxComponent*> Boxes;
		Arena->GetComponents<UBoxComponent>(Boxes);
		int32 Blocking = 0;
		for (const UBoxComponent* Box : Boxes)
		{
			if (!Box->ComponentHasTag(TEXT("LethalBottom")))
			{
				++Blocking;
				TestEqual(TEXT("wall blocks player shot"), static_cast<int32>(Box->GetCollisionResponseToChannel(UmbrellaCollision::PlayerShot)), static_cast<int32>(ECR_Block));
				TestEqual(TEXT("wall blocks enemy shot"), static_cast<int32>(Box->GetCollisionResponseToChannel(UmbrellaCollision::EnemyShot)), static_cast<int32>(ECR_Block));
			}
		}
		TestEqual(TEXT("two walls and a ceiling"), Blocking, 3);
		Arena->BuildPlaceholders();
		TestNotNull(TEXT("keeper stand-in"), Arena->GetKeeperStandIn());
		TestNotNull(TEXT("far background"), Arena->GetBackgroundFar());
		const double FarBefore = Arena->GetBackgroundFar()->GetRelativeLocation().X;
		Arena->Tick(1.0f);
		TestTrue(TEXT("far background scrolled left"), Arena->GetBackgroundFar()->GetRelativeLocation().X < FarBefore);
		const FArenaCameraTuning& T = GetDefault<UUmbrellaTuning>()->ArenaCamera;
		TestNearlyEqual(TEXT("keeper anchor X"), Arena->GetKeeperAnchorLocation().X, static_cast<double>(T.ArenaWidth * T.KeeperAnchorXFraction));
		TestNearlyEqual(TEXT("keeper anchor Z"), Arena->GetKeeperAnchorLocation().Z, static_cast<double>(T.ArenaHeight * T.KeeperAnchorZFraction));
		TestNearlyEqual(TEXT("player start Z"), Arena->GetPlayerStartLocation().Z, static_cast<double>(T.ArenaHeight * T.PlayerStartZFraction));
	}
	GEngine->DestroyWorldContext(World);
	World->DestroyWorld(false);
	return bOk;
}

#endif
