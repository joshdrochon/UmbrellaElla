#include "Feedback/Art/ArtSlot.h"
#include "Engine/Engine.h"
#include "Components/StaticMeshComponent.h"
#include "Engine/World.h"
#include "Feedback/Anim/EllaAnimPresenterComponent.h"
#include "Feedback/Anim/KeeperPresenterSubsystem.h"
#include "Owl/KeeperOfTime.h"
#include "Enemy/UmbrellaEnemy.h"
#include "Feedback/Anim/EnemyPresenterSubsystem.h"
#include "Components/BoxComponent.h"
#include "Feedback/Audio/UmbrellaCueSubsystem.h"
#include "Feedback/Build/BuildIdentity.h"
#include "Feedback/Vfx/UmbrellaVfxSubsystem.h"
#include "Feedback/Background/UmbrellaBackdropSubsystem.h"
#include "GameFramework/Actor.h"
#include "Core/UmbrellaEventBus.h"
#include "Core/UmbrellaDrawOrder.h"
#include "Components/PointLightComponent.h"
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
	Event.Type = EUmbrellaEventType::LevelGained;
	TestEqual(TEXT("level up cue"), UUmbrellaCueSubsystem::CueForEvent(Event), FName(TEXT("LevelUp")));
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
	// A shipped Ella asset (T_Ella_Idle_PH) is drawn instead of the stand-in; the stand-in checks run only when no state has art.
	const FArtSlotRow* IdleRow = ArtSlot::Find(TEXT("ella-state:Idle"));
	const bool bIdleArt = IdleRow && ArtSlot::LoadTexture(*IdleRow) != nullptr;
	TestNotNull(TEXT("stand-in component"), Presenter->GetStandIn());
	if (!bIdleArt)
	{
		TestTrue(TEXT("no art shows the stand-in"), Presenter->IsShowingStandIn());
	}
	Presenter->SetVisualState(EEllaVisualState::Absorb);
	TestEqual(TEXT("absorb state shown"), static_cast<int32>(Presenter->GetVisualState()), static_cast<int32>(EEllaVisualState::Absorb));
	if (!bIdleArt)
	{
		TestEqual(TEXT("absorb widens the stand-in"), Presenter->GetStandIn()->GetRelativeScale3D(), UEllaAnimPresenterComponent::StandInScaleFor(EEllaVisualState::Absorb));
	}
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
		// BG-02..04, BG-06: every layer has its own depth, scrolls with parallax and loops.
		TArray<float> Seen;
		for (const FBackdropLayerSpec& Spec : Backdrop->GetBuiltSpecs())
		{
			TestFalse(TEXT("layer depth is unique"), Seen.Contains(Spec.Depth));
			Seen.Add(Spec.Depth);
		}
		Backdrop->ScrollTo(3000.0f);
		for (int32 Index = 0; Index < Backdrop->GetLayers().Num(); ++Index)
		{
			const float ExpectedX = UUmbrellaBackdropSubsystem::LayerXForCamera(3000.0f, Backdrop->GetBuiltSpecs()[Index].Parallax);
			TestEqual(TEXT("layer follows camera"), static_cast<float>(Backdrop->GetLayers()[Index]->GetActorLocation().X), ExpectedX);
		}
	}
	GEngine->DestroyWorldContext(World);
	World->DestroyWorld(false);
	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FFeedbackVfxRules, "UmbrellaElla.Feedback.VfxRules",
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::ClientContext | EAutomationTestFlags::EngineFilter)

bool FFeedbackVfxRules::RunTest(const FString& Parameters)
{
	// Acceptance: every effect has a spec on a layer that is in front of the arena and behind the foreground.
	for (const FName Effect : UUmbrellaVfxSubsystem::AllEffects())
	{
		const FVfxEffectSpec Spec = UUmbrellaVfxSubsystem::SpecForEffect(Effect);
		TestEqual(TEXT("spec is named"), Spec.Name, Effect);
		TestTrue(TEXT("effect layer is in front of the arena"), Spec.LayerY > UmbrellaDrawOrder::ArenaY);
		TestTrue(TEXT("effect layer is behind the foreground"), Spec.LayerY < UmbrellaDrawOrder::ForegroundY);
		TestTrue(TEXT("effect life is readable"), Spec.LifeSeconds >= UmbrellaVfxConst::MinReadableSeconds);
	}
	TestEqual(TEXT("telegraph is on the hazard layer"), UUmbrellaVfxSubsystem::SpecForEffect(TEXT("KeeperTelegraph")).LayerY, UmbrellaDrawOrder::HazardY);
	TestEqual(TEXT("impact is on the vfx layer"), UUmbrellaVfxSubsystem::SpecForEffect(TEXT("ShotImpact")).LayerY, UmbrellaDrawOrder::VfxY);
	// Readability sync: a telegraph lasts as long as its warning, clamped.
	FUmbrellaEvent Telegraph;
	Telegraph.Type = EUmbrellaEventType::BossAttackTelegraphed;
	const FVfxEffectSpec TelegraphSpec = UUmbrellaVfxSubsystem::SpecForEffect(TEXT("KeeperTelegraph"));
	Telegraph.Value = 1.2f;
	TestEqual(TEXT("telegraph life follows the warning"), UUmbrellaVfxSubsystem::LifeFor(TelegraphSpec, Telegraph), 1.2f);
	Telegraph.Value = 99.0f;
	TestEqual(TEXT("long warning is capped"), UUmbrellaVfxSubsystem::LifeFor(TelegraphSpec, Telegraph), UmbrellaVfxConst::MaxLifeSeconds);
	Telegraph.Value = 0.01f;
	TestEqual(TEXT("short warning stays readable"), UUmbrellaVfxSubsystem::LifeFor(TelegraphSpec, Telegraph), UmbrellaVfxConst::MinReadableSeconds);
	// Performance and flash limits.
	TestFalse(TEXT("under the cap is shown"), UUmbrellaVfxSubsystem::ShouldSuppress(0, false, 0.0f));
	TestTrue(TEXT("over the cap is dropped"), UUmbrellaVfxSubsystem::ShouldSuppress(UmbrellaVfxConst::MaxActiveEffects, false, 99.0f));
	TestTrue(TEXT("a flash too soon is dropped"), UUmbrellaVfxSubsystem::ShouldSuppress(0, true, 0.05f));
	TestFalse(TEXT("a non-flashing effect ignores the flash gap"), UUmbrellaVfxSubsystem::ShouldSuppress(0, false, 0.05f));
	TestFalse(TEXT("a flash after the gap is shown"), UUmbrellaVfxSubsystem::ShouldSuppress(0, true, UmbrellaVfxConst::MinFlashGapSeconds + 0.01f));
	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FFeedbackVfxLayersWorld, "UmbrellaElla.Feedback.World.VfxLayersLightLimits",
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::ClientContext | EAutomationTestFlags::EngineFilter)

bool FFeedbackVfxLayersWorld::RunTest(const FString& Parameters)
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
		Event.Type = EUmbrellaEventType::BossAttackTelegraphed;
		Event.Frame = 42;
		Vfx->PlayForEvent(Event);
		AActor* Telegraph = Vfx->GetLastActor();
		if (TestNotNull(TEXT("telegraph actor"), Telegraph))
		{
			TestEqual(TEXT("telegraph on its own layer"), static_cast<float>(Telegraph->GetActorLocation().Y), UmbrellaDrawOrder::HazardY);
			TestNotNull(TEXT("lit effect lights nearby surfaces"), Telegraph->FindComponentByClass<UPointLightComponent>());
			const UPrimitiveComponent* Mesh = Cast<UPrimitiveComponent>(Telegraph->GetRootComponent());
			TestTrue(TEXT("effect has no collision"), Mesh && Mesh->GetCollisionEnabled() == ECollisionEnabled::NoCollision);
		}
		TestEqual(TEXT("effect is synced to the event frame"), Vfx->GetLastEventFrame(), static_cast<int64>(42));
		// A fizzle is unlit: no light.
		Event.Type = EUmbrellaEventType::CatchFailed;
		Vfx->PlayForEvent(Event);
		if (AActor* Fizzle = Vfx->GetLastActor())
		{
			TestNull(TEXT("unlit effect has no light"), Fizzle->FindComponentByClass<UPointLightComponent>());
		}
		// Two flashing effects in the same instant: the second is dropped.
		Event.Type = EUmbrellaEventType::CatchSucceeded;
		Vfx->PlayForEvent(Event);
		const int32 Shown = Vfx->GetEffectCount();
		Vfx->PlayForEvent(Event);
		TestEqual(TEXT("second flash inside the gap is dropped"), Vfx->GetEffectCount(), Shown);
		TestEqual(TEXT("and counted as suppressed"), Vfx->GetSuppressedCount(), 1);
		// Reduced flash shrinks a flashing effect.
		UUmbrellaVfxSubsystem* Other = NewObject<UUmbrellaVfxSubsystem>(World);
		TestFalse(TEXT("reduced flash defaults off"), Other->IsReducedFlash());
		Other->SetReducedFlash(true);
		TestTrue(TEXT("reduced flash can be set"), Other->IsReducedFlash());
		const AActor* Full = Vfx->GetLastActor();
		const float FullScale = Full && Full->GetRootComponent() ? Full->GetRootComponent()->GetRelativeScale3D().X : 0.0f;
		Other->PlayForEvent(Event);
		const AActor* Small = Other->GetLastActor();
		if (TestNotNull(TEXT("reduced flash still shows an effect"), Small) && FullScale > 0.0f)
		{
			TestEqual(TEXT("reduced flash shrinks a flashing effect"), static_cast<float>(Small->GetRootComponent()->GetRelativeScale3D().X),
				FullScale * UmbrellaVfxConst::ReducedFlashScale);
		}
	}
	GEngine->DestroyWorldContext(World);
	World->DestroyWorld(false);
	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FFeedbackStateCoverage, "UmbrellaElla.Feedback.PresenterStateCoverage",
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::ClientContext | EAutomationTestFlags::EngineFilter)

bool FFeedbackStateCoverage::RunTest(const FString& Parameters)
{
	// Every Ella visual state has a distinct, non-empty stand-in shape and is reachable from a bus event.
	const FName Ella(TEXT("Ella"));
	TSet<FString> Shapes;
	for (const EEllaVisualState State : { EEllaVisualState::Idle, EEllaVisualState::Shoot, EEllaVisualState::Absorb, EEllaVisualState::Hurt, EEllaVisualState::Down })
	{
		const FVector Scale = UEllaAnimPresenterComponent::StandInScaleFor(State);
		TestTrue(TEXT("state has a visible shape"), Scale.X > 0.0 && Scale.Z > 0.0);
		TestTrue(TEXT("state shape is distinct"), !Shapes.Contains(Scale.ToString()));
		Shapes.Add(Scale.ToString());
	}
	TSet<int32> Reached;
	for (int32 Index = 0; Index < static_cast<int32>(EUmbrellaEventType::Count); ++Index)
	{
		FUmbrellaEvent Event;
		Event.Type = static_cast<EUmbrellaEventType>(Index);
		Event.SourceId = Ella;
		Reached.Add(static_cast<int32>(UEllaAnimPresenterComponent::StateForEvent(Event, Ella)));
	}
	for (const EEllaVisualState State : { EEllaVisualState::Shoot, EEllaVisualState::Absorb, EEllaVisualState::Hurt, EEllaVisualState::Down })
	{
		TestTrue(TEXT("state is reachable from an event"), Reached.Contains(static_cast<int32>(State)));
	}
	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FFeedbackArtSwapCollision, "UmbrellaElla.Feedback.World.ArtSwapKeepsCollision",
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::ClientContext | EAutomationTestFlags::EngineFilter)

bool FFeedbackArtSwapCollision::RunTest(const FString& Parameters)
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
	const FVector RootScale = Root->GetComponentScale();
	const FVector RootLocation = Root->GetComponentLocation();
	for (const EEllaVisualState State : { EEllaVisualState::Shoot, EEllaVisualState::Absorb, EEllaVisualState::Hurt, EEllaVisualState::Down, EEllaVisualState::Idle })
	{
		Presenter->SetVisualState(State);
		TestTrue(TEXT("stand-in never collides"), Presenter->GetStandIn() && Presenter->GetStandIn()->GetCollisionEnabled() == ECollisionEnabled::NoCollision);
		TestEqual(TEXT("owner scale (collision size) is unchanged by art state"), Root->GetComponentScale(), RootScale);
		TestEqual(TEXT("owner location is unchanged by art state"), Root->GetComponentLocation(), RootLocation);
	}
	GEngine->DestroyWorldContext(World);
	World->DestroyWorld(false);
	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FFeedbackEnemyArtKeys, "UmbrellaElla.Feedback.EnemyPresenterCoverage",
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::ClientContext | EAutomationTestFlags::EngineFilter)

bool FFeedbackEnemyArtKeys::RunTest(const FString& Parameters)
{
	// Production state coverage: every (type, gender, state) has its own art key, and gender never changes height.
	TSet<FName> Keys;
	for (const EEnemyType Type : { EEnemyType::Roadwarden, EEnemyType::Floodstrider, EEnemyType::SkyCourier })
	{
		for (const EEnemyGender Gender : { EEnemyGender::Male, EEnemyGender::Female })
		{
			for (const EEnemyState State : { EEnemyState::Patrol, EEnemyState::Aim, EEnemyState::Recovery, EEnemyState::Defeated, EEnemyState::Withdrawn })
			{
				Keys.Add(UEnemyPresenterSubsystem::ArtKeyFor(Type, Gender, State));
			}
		}
	}
	TestEqual(TEXT("30 distinct art keys"), Keys.Num(), 30);
	TestEqual(TEXT("key format"), UEnemyPresenterSubsystem::ArtKeyFor(EEnemyType::Roadwarden, EEnemyGender::Female, EEnemyState::Aim), FName(TEXT("Roadwarden_Female_Aim")));
	TestEqual(TEXT("gender keeps height"), UEnemyPresenterSubsystem::StandInScaleFor(EEnemyState::Patrol, EEnemyGender::Male).Z, UEnemyPresenterSubsystem::StandInScaleFor(EEnemyState::Patrol, EEnemyGender::Female).Z);
	TestTrue(TEXT("patrol visible"), UEnemyPresenterSubsystem::IsVisibleIn(EEnemyState::Patrol));
	TestFalse(TEXT("defeated hidden"), UEnemyPresenterSubsystem::IsVisibleIn(EEnemyState::Defeated));
	TestFalse(TEXT("withdrawn hidden"), UEnemyPresenterSubsystem::IsVisibleIn(EEnemyState::Withdrawn));
	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FFeedbackEnemyStandIn, "UmbrellaElla.Feedback.World.EnemyStandIn",
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::ClientContext | EAutomationTestFlags::EngineFilter)

bool FFeedbackEnemyStandIn::RunTest(const FString& Parameters)
{
	UWorld* World = UWorld::CreateWorld(EWorldType::Game, false);
	if (!TestNotNull(TEXT("world"), World))
	{
		return false;
	}
	FWorldContext& Context = GEngine->CreateNewWorldContext(EWorldType::Game);
	Context.SetCurrentWorld(World);
	UEnemyPresenterSubsystem* Presenter = World->GetSubsystem<UEnemyPresenterSubsystem>();
	if (TestNotNull(TEXT("enemy presenter"), Presenter))
	{
		AUmbrellaEnemy* Enemy = World->SpawnActor<AUmbrellaEnemy>();
		if (TestNotNull(TEXT("enemy"), Enemy))
		{
			TestEqual(TEXT("one stand-in on spawn"), Presenter->GetPresentedCount(), 1);
			Presenter->ShowStandIn(Enemy);
			TestEqual(TEXT("second show adds none"), Presenter->GetPresentedCount(), 1);
			const UBoxComponent* Hitbox = Enemy->FindComponentByClass<UBoxComponent>();
			const FVector HitboxExtent = Hitbox ? Hitbox->GetScaledBoxExtent() : FVector::ZeroVector;
			const ECollisionEnabled::Type HitboxCollision = Hitbox ? Hitbox->GetCollisionEnabled() : ECollisionEnabled::NoCollision;
			bool bFound = false;
			TInlineComponentArray<UStaticMeshComponent*> Meshes(Enemy);
			for (UStaticMeshComponent* Mesh : Meshes)
			{
				if (Mesh->GetFName() == FName(TEXT("EnemyStandIn")))
				{
					bFound = true;
					TestEqual(TEXT("stand-in never collides"), static_cast<int32>(Mesh->GetCollisionEnabled()), static_cast<int32>(ECollisionEnabled::NoCollision));
					TestEqual(TEXT("stand-in is on the character layer"), static_cast<float>(Mesh->GetComponentLocation().Y), UmbrellaDrawOrder::KeeperY);
					const FVector PatrolBox = UEnemyPresenterSubsystem::StandInScaleFor(EEnemyState::Patrol, Enemy->GetGender());
					// Filled: the slot's stand-in texture is drawn on a plane that keeps the patrol footprint.
					const FArtSlotRow* Row = ArtSlot::Find(*Presenter->VisualIdOf(Enemy));
					TestTrue(TEXT("stand-in shows its slot texture"), Row && ArtSlot::LoadTexture(*Row) && ArtSlot::HasArt(Mesh));
					TestEqual(TEXT("patrol shape with art"), Mesh->GetComponentScale(), ArtSlot::PlaneScaleFor(PatrolBox));
					// Empty: with the slot's art cleared, the stand-in keeps the patrol box shape.
					ArtSlot::SetFlatUnlit(Mesh, Enemy, UmbrellaArtSlotConst::StandInEnemyColor);
					Presenter->Refresh(Enemy);
					TestFalse(TEXT("cleared stand-in has no art"), ArtSlot::HasArt(Mesh));
					TestEqual(TEXT("patrol shape"), Mesh->GetComponentScale(), PatrolBox);
				}
			}
			TestTrue(TEXT("stand-in exists"), bFound);
			TestEqual(TEXT("hitbox size untouched"), Hitbox ? Hitbox->GetScaledBoxExtent() : FVector::ZeroVector, HitboxExtent);
			TestEqual(TEXT("hitbox collision untouched"), static_cast<int32>(Hitbox ? Hitbox->GetCollisionEnabled() : ECollisionEnabled::NoCollision), static_cast<int32>(HitboxCollision));
		}
	}
	GEngine->DestroyWorldContext(World);
	World->DestroyWorld(false);
	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FFeedbackBackdropLoop, "UmbrellaElla.Feedback.BackdropLoop",
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::ClientContext | EAutomationTestFlags::EngineFilter)

bool FFeedbackBackdropLoop::RunTest(const FString& Parameters)
{
	// dcseamless: layers no longer wrap; they slide at most SlideHeadroom from the camera, for any camera X (never run out).
	const float Headroom = UmbrellaBackdropConst::SlideHeadroom;
	for (const FBackdropLayerSpec& Spec : UUmbrellaBackdropSubsystem::LayerSpecs())
	{
		for (const float Camera : { -5000.0f, -1.0f, 0.0f, 777.0f, 1.0e6f })
		{
			const float Offset = UUmbrellaBackdropSubsystem::LayerOffset(Camera, Spec.Parallax);
			TestTrue(TEXT("offset stays inside the headroom (never runs out)"), FMath::Abs(Offset) <= Headroom);
			TestEqual(TEXT("layer X is camera plus offset"), UUmbrellaBackdropSubsystem::LayerXForCamera(Camera, Spec.Parallax), Camera + Offset);
		}
	}
	TestTrue(TEXT("all layers sit behind the arena"), [] {
		for (const FBackdropLayerSpec& Spec : UUmbrellaBackdropSubsystem::LayerSpecs())
		{
			if (Spec.Depth >= UmbrellaDrawOrder::ArenaY) { return false; }
		}
		return true; }());
	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FFeedbackKeeperStandIn, "UmbrellaElla.Feedback.World.KeeperStandIn",
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::ClientContext | EAutomationTestFlags::EngineFilter)

bool FFeedbackKeeperStandIn::RunTest(const FString& Parameters)
{
	UWorld* World = UWorld::CreateWorld(EWorldType::Game, false);
	if (!TestNotNull(TEXT("world"), World))
	{
		return false;
	}
	FWorldContext& Context = GEngine->CreateNewWorldContext(EWorldType::Game);
	Context.SetCurrentWorld(World);
	UKeeperPresenterSubsystem* Presenter = World->GetSubsystem<UKeeperPresenterSubsystem>();
	if (TestNotNull(TEXT("keeper presenter"), Presenter))
	{
		AKeeperOfTime* Keeper = World->SpawnActor<AKeeperOfTime>();
		if (TestNotNull(TEXT("keeper"), Keeper))
		{
			TestEqual(TEXT("one stand-in on spawn"), Presenter->GetPresentedCount(), 1);
			Presenter->ShowStandIn(Keeper);
			TestEqual(TEXT("second show adds none"), Presenter->GetPresentedCount(), 1);
			const UPrimitiveComponent* Mesh = Keeper->FindComponentByClass<UPrimitiveComponent>();
			TestTrue(TEXT("stand-in has no collision"), Mesh && Mesh->GetCollisionEnabled() == ECollisionEnabled::NoCollision);
		}
	}
	GEngine->DestroyWorldContext(World);
	World->DestroyWorld(false);
	return true;
}

#endif
