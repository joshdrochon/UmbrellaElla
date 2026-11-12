#include "Arena/UmbrellaArena.h"
#include "Camera/CameraComponent.h"
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
		Arena->BuildPlaceholders();
		TestNotNull(TEXT("keeper stand-in"), Arena->GetKeeperStandIn());
		TestNotNull(TEXT("far background"), Arena->GetBackgroundFar());
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
