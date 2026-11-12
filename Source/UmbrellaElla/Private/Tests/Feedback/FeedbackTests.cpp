#include "Components/StaticMeshComponent.h"
#include "Engine/World.h"
#include "Feedback/Anim/EllaAnimPresenterComponent.h"
#include "Feedback/Audio/UmbrellaCueSubsystem.h"
#include "Feedback/Build/BuildIdentity.h"
#include "Feedback/Vfx/UmbrellaVfxSubsystem.h"
#include "Feedback/Background/UmbrellaBackdropSubsystem.h"
#include "GameFramework/Actor.h"
#include "Core/UmbrellaEventBus.h"
#include "Core/UmbrellaDrawOrder.h"
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
	Presenter->SetVisualState(EEllaVisualState::Absorb);
	TestEqual(TEXT("absorb state shown"), static_cast<int32>(Presenter->GetVisualState()), static_cast<int32>(EEllaVisualState::Absorb));
	TestEqual(TEXT("absorb widens the stand-in"), Presenter->GetStandIn()->GetRelativeScale3D(), UEllaAnimPresenterComponent::StandInScaleFor(EEllaVisualState::Absorb));
	Presenter->TickComponent(10.0f, LEVELTICK_All, nullptr);
	TestEqual(TEXT("transient state returns to idle"), static_cast<int32>(Presenter->GetVisualState()), static_cast<int32>(EEllaVisualState::Idle));
	FUmbrellaEvent Down;
	Down.Type = EUmbrellaEventType::PlayerDefeated;
	if (UUmbrellaEventBus* Bus = UUmbrellaEventBus::Get(World))
	{
		Bus->Broadcast(Down);
	}
	GEngine->DestroyWorldContext(World);
	World->DestroyWorld(false);
	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FFeedbackStateMap, "UmbrellaElla.Feedback.PresenterStateMapping",
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::ClientContext | EAutomationTestFlags::EngineFilter)

bool FFeedbackStateMap::RunTest(const FString& Parameters)
{
	const FName Ella(TEXT("Ella"));
	FUmbrellaEvent Event;
	Event.Type = EUmbrellaEventType::ProjectileSpawned;
	Event.SourceId = Ella;
	TestEqual(TEXT("own shot shows shoot"), static_cast<int32>(UEllaAnimPresenterComponent::StateForEvent(Event, Ella)), static_cast<int32>(EEllaVisualState::Shoot));
	Event.SourceId = TEXT("Keeper");
	TestEqual(TEXT("keeper shot is not Ella shooting"), static_cast<int32>(UEllaAnimPresenterComponent::StateForEvent(Event, Ella)), static_cast<int32>(EEllaVisualState::Idle));
	Event.Type = EUmbrellaEventType::CatchSucceeded;
	TestEqual(TEXT("catch shows absorb"), static_cast<int32>(UEllaAnimPresenterComponent::StateForEvent(Event, Ella)), static_cast<int32>(EEllaVisualState::Absorb));
	Event.Type = EUmbrellaEventType::LifeLost;
	TestEqual(TEXT("life lost shows hurt"), static_cast<int32>(UEllaAnimPresenterComponent::StateForEvent(Event, Ella)), static_cast<int32>(EEllaVisualState::Hurt));
	Event.Type = EUmbrellaEventType::PlayerDefeated;
	TestEqual(TEXT("defeat shows down"), static_cast<int32>(UEllaAnimPresenterComponent::StateForEvent(Event, Ella)), static_cast<int32>(EEllaVisualState::Down));
	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FFeedbackVfxMap, "UmbrellaElla.Feedback.VfxMapping",
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::ClientContext | EAutomationTestFlags::EngineFilter)

bool FFeedbackVfxMap::RunTest(const FString& Parameters)
{
	FUmbrellaEvent Event;
	Event.Type = EUmbrellaEventType::ProjectileSpawned;
	TestEqual(TEXT("shot muzzle"), UUmbrellaVfxSubsystem::EffectForEvent(Event), FName(TEXT("ShotMuzzle")));
	Event.Type = EUmbrellaEventType::CatchSucceeded;
	TestEqual(TEXT("absorb burst"), UUmbrellaVfxSubsystem::EffectForEvent(Event), FName(TEXT("AbsorbBurst")));
	Event.Type = EUmbrellaEventType::BossAttackTelegraphed;
	TestEqual(TEXT("keeper telegraph"), UUmbrellaVfxSubsystem::EffectForEvent(Event), FName(TEXT("KeeperTelegraph")));
	Event.Type = EUmbrellaEventType::WindEntered;
	TestTrue(TEXT("wind has no effect"), UUmbrellaVfxSubsystem::EffectForEvent(Event).IsNone());
	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FFeedbackVfxWorld, "UmbrellaElla.Feedback.World.VfxStandIn",
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::ClientContext | EAutomationTestFlags::EngineFilter)

bool FFeedbackVfxWorld::RunTest(const FString& Parameters)
{
	UWorld* World = UWorld::CreateWorld(EWorldType::Game, false);
	if (!TestNotNull(TEXT("world"), World))
	{
		return false;
	}
	FWorldContext& Context = GEngine->CreateNewWorldContext(EWorldType::Game);
	Context.SetCurrentWorld(World);
	UUmbrellaVfxSubsystem* Vfx = World->GetSubsystem<UUmbrellaVfxSubsystem>();
	if (TestNotNull(TEXT("vfx subsystem"), Vfx))
	{
		FUmbrellaEvent Event;
		Event.Type = EUmbrellaEventType::CatchSucceeded;
		Vfx->PlayForEvent(Event);
		TestEqual(TEXT("last effect"), Vfx->GetLastEffect(), FName(TEXT("AbsorbBurst")));
		TestEqual(TEXT("one effect"), Vfx->GetEffectCount(), 1);
		Event.Type = EUmbrellaEventType::WindEntered;
		Vfx->PlayForEvent(Event);
		TestEqual(TEXT("still one effect"), Vfx->GetEffectCount(), 1);
	}
	GEngine->DestroyWorldContext(World);
	World->DestroyWorld(false);
	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FFeedbackBackdrop, "UmbrellaElla.Feedback.World.BackdropLayers",
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::ClientContext | EAutomationTestFlags::EngineFilter)

bool FFeedbackBackdrop::RunTest(const FString& Parameters)
{
	UWorld* World = UWorld::CreateWorld(EWorldType::Game, false);
	if (!TestNotNull(TEXT("world"), World))
	{
		return false;
	}
	FWorldContext& Context = GEngine->CreateNewWorldContext(EWorldType::Game);
	Context.SetCurrentWorld(World);
	UUmbrellaBackdropSubsystem* Backdrop = World->GetSubsystem<UUmbrellaBackdropSubsystem>();
	if (TestNotNull(TEXT("backdrop subsystem"), Backdrop))
	{
		const int32 Expected = UUmbrellaBackdropSubsystem::LayerDepths().Num();
		TestEqual(TEXT("layers built"), Backdrop->BuildLayers(), Expected);
		TestEqual(TEXT("second build adds none"), Backdrop->BuildLayers(), Expected);
		for (const AActor* Layer : Backdrop->GetLayers())
		{
			const UPrimitiveComponent* Panel = Cast<UPrimitiveComponent>(Layer->GetRootComponent());
			TestTrue(TEXT("panel has no collision"), Panel && Panel->GetCollisionEnabled() == ECollisionEnabled::NoCollision);
			TestTrue(TEXT("panel is behind Ella"), Layer->GetActorLocation().Y < UmbrellaDrawOrder::EllaY);
		}
	}
	GEngine->DestroyWorldContext(World);
	World->DestroyWorld(false);
	return true;
}

#endif
