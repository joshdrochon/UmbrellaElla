#include "Engine/World.h"
#include "Feedback/Anim/EllaAnimPresenterComponent.h"
#include "Feedback/Audio/UmbrellaCueSubsystem.h"
#include "Feedback/Build/BuildIdentity.h"
#include "GameFramework/Actor.h"
#include "Core/UmbrellaEventBus.h"
#include "Misc/AutomationTest.h"

#if WITH_AUTOMATION_TESTS

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FFeedbackCueMap, "UmbrellaElla.Feedback.CueMapping",
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::ClientContext | EAutomationTestFlags::EngineFilter)

bool FFeedbackCueMap::RunTest(const FString& Parameters)
{
	FUmbrellaEvent Event;
	Event.Type = EUmbrellaEventType::CatchSucceeded;
	TestEqual(TEXT("absorb cue"), UUmbrellaCueSubsystem::CueForEvent(Event), FName(TEXT("Absorb")));
	Event.Type = EUmbrellaEventType::ProjectileSpawned;
	TestEqual(TEXT("shot cue"), UUmbrellaCueSubsystem::CueForEvent(Event), FName(TEXT("Shot")));
	Event.Type = EUmbrellaEventType::WindEntered;
	TestTrue(TEXT("wind has no cue"), UUmbrellaCueSubsystem::CueForEvent(Event).IsNone());
	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FFeedbackBuildIdentity, "UmbrellaElla.Feedback.BuildIdentityRecord",
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::ClientContext | EAutomationTestFlags::EngineFilter)

bool FFeedbackBuildIdentity::RunTest(const FString& Parameters)
{
	const FBuildIdentity Id = FBuildIdentity::Capture();
	TestEqual(TEXT("camera aspect"), Id.CameraAspectRatio, 1.777778f);
	TestEqual(TEXT("units per pixel"), Id.UnitsPerPixel, 1.0f);
	TestTrue(TEXT("engine version recorded"), !Id.EngineVersion.IsEmpty());
	TestTrue(TEXT("record has platform"), Id.ToText().Contains(TEXT("platform=")));
	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FFeedbackStandIn, "UmbrellaElla.Feedback.World.PresenterStandIn",
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::ClientContext | EAutomationTestFlags::EngineFilter)

bool FFeedbackStandIn::RunTest(const FString& Parameters)
{
	UWorld* World = UWorld::CreateWorld(EWorldType::Game, false);
	if (!TestNotNull(TEXT("world"), World))
	{
		return false;
	}
	FWorldContext& Context = GEngine->CreateNewWorldContext(EWorldType::Game);
	Context.SetCurrentWorld(World);
	AActor* Owner = World->SpawnActor<AActor>();
	USceneComponent* Root = NewObject<USceneComponent>(Owner, TEXT("Root"));
	Owner->SetRootComponent(Root);
	Root->RegisterComponent();
	UEllaAnimPresenterComponent* Presenter = NewObject<UEllaAnimPresenterComponent>(Owner);
	Presenter->RegisterComponent();
	Presenter->BuildVisual();
	TestTrue(TEXT("no art shows the stand-in"), Presenter->IsShowingStandIn());
	TestNotNull(TEXT("stand-in component"), Presenter->GetStandIn());
	GEngine->DestroyWorldContext(World);
	World->DestroyWorld(false);
	return true;
}

#endif
