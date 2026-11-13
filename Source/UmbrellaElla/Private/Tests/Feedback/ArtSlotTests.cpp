#include "Feedback/Art/ArtSlot.h"
#include "Components/StaticMeshComponent.h"
#include "Core/UmbrellaDrawOrder.h"
#include "Core/UmbrellaTuning.h"
#include "Engine/Engine.h"
#include "Engine/Texture2D.h"
#include "Engine/World.h"
#include "Enemy/UmbrellaEnemy.h"
#include "Feedback/Anim/EllaAnimPresenterComponent.h"
#include "Feedback/Anim/EnemyPresenterSubsystem.h"
#include "Feedback/Anim/KeeperPresenterSubsystem.h"
#include "Feedback/Anim/ShotPresenterSubsystem.h"
#include "Feedback/Vfx/UmbrellaVfxDirectorSubsystem.h"
#include "Feedback/Vfx/VfxCatalog.h"
#include "Feedback/Vfx/VfxSheetVisual.h"
#include "Tests/Shared/UmbrellaTestWorld.h"
#include "Feedback/Vfx/UmbrellaVfxSubsystem.h"
#include "Core/UmbrellaEvent.h"
#include "Projectile/UmbrellaProjectile.h"
#include "Feedback/Background/UmbrellaBackdropSubsystem.h"
#include "GameFramework/Actor.h"
#include "Materials/MaterialInstanceDynamic.h"
#include "Misc/AutomationTest.h"
#include "Owl/KeeperOfTime.h"

#if WITH_AUTOMATION_TESTS

namespace
{
	UTexture2D* ArtSlotTestTexture()
	{
		UTexture2D* Texture = UTexture2D::CreateTransient(4, 4);
		Texture->AddToRoot();
		return Texture;
	}

	UTexture2D* ArtSlotParamTexture(const UStaticMeshComponent* Mesh)
	{
		UTexture* Out = nullptr;
		if (const UMaterialInstanceDynamic* Dynamic = Cast<UMaterialInstanceDynamic>(Mesh->GetMaterial(0)))
		{
			Dynamic->GetTextureParameterValue(FName(TEXT("Art")), Out);
		}
		return Cast<UTexture2D>(Out);
	}

	UWorld* ArtSlotTestWorld()
	{
		UWorld* World = UWorld::CreateWorld(EWorldType::Game, false);
		if (World)
		{
			GEngine->CreateNewWorldContext(EWorldType::Game).SetCurrentWorld(World);
		}
		return World;
	}

	void ArtSlotTestEnd(UWorld* World)
	{
		GEngine->DestroyWorldContext(World);
		World->DestroyWorld(false);
	}
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FArtSlotCatalog, "UmbrellaElla.Feedback.ArtSlotCatalog",
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::ClientContext | EAutomationTestFlags::EngineFilter)

bool FArtSlotCatalog::RunTest(const FString& Parameters)
{
	TSet<FString> Seen;
	for (const FArtSlotRow& Row : ArtSlot::Rows())
	{
		TestTrue(TEXT("slot path is unique"), !Seen.Contains(ArtSlot::SlotPath(Row)));
		Seen.Add(ArtSlot::SlotPath(Row));
		TestTrue(TEXT("slot is under the Art root"), ArtSlot::SlotPath(Row).StartsWith(UmbrellaArtSlotConst::GameRoot));
	}
	TestTrue(TEXT("one slot per inventory visual"), ArtSlot::Rows().Num() >= 100);
	const FArtSlotRow* Paper = ArtSlot::Find(TEXT("bg-layer:Sky"));
	if (TestNotNull(TEXT("sky row"), Paper))
	{
		const TArray<FString> Paths = ArtSlot::TexturePaths(*Paper);
		TestEqual(TEXT("passed asset first"), Paths[0], FString(TEXT("/Game/UmbrellaElla/Art/Scene/T_Paper.T_Paper")));
		TestEqual(TEXT("placeholder second"), Paths[1], FString(TEXT("/Game/UmbrellaElla/Art/Scene/T_Paper_PH.T_Paper_PH")));
		TestTrue(TEXT("paper tiles"), Paper->bTile);
	}
	TestTrue(TEXT("every backdrop layer has a row"), ArtSlot::Find(*UUmbrellaBackdropSubsystem::LayerVisualId(TEXT("FarLand"))) != nullptr);
	TestTrue(TEXT("every Ella state has a row"), ArtSlot::Find(TEXT("ella-state:Down")) != nullptr);
	TestTrue(TEXT("every enemy type has a row"), ArtSlot::Find(*UEnemyPresenterSubsystem::VisualIdFor(EEnemyType::SkyCourier, EEnemyGender::Female)) != nullptr);
	TestTrue(TEXT("unknown visual has no row"), ArtSlot::Find(TEXT("nothing:here")) == nullptr);
	TestEqual(TEXT("plane keeps the box footprint"), ArtSlot::PlaneScaleFor(FVector(2.0, 0.1, 3.0)), FVector(2.0, 3.0, 1.0));
	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FArtSlotMaterialAsset, "UmbrellaElla.Feedback.ArtSlotMaterialExists",
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::ClientContext | EAutomationTestFlags::EngineFilter)

bool FArtSlotMaterialAsset::RunTest(const FString& Parameters)
{
	TestNotNull(TEXT("M_ArtSlot_Unlit (tools/build/assets/art_slot_material.py)"),
		LoadObject<UMaterialInterface>(nullptr, UmbrellaArtSlotConst::MaterialPath, nullptr, LOAD_NoWarn | LOAD_Quiet));
	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FArtSlotBackdrop, "UmbrellaElla.Feedback.World.ArtSlotBackdrop",
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::ClientContext | EAutomationTestFlags::EngineFilter)

bool FArtSlotBackdrop::RunTest(const FString& Parameters)
{
	UWorld* World = ArtSlotTestWorld();
	if (!TestNotNull(TEXT("world"), World))
	{
		return false;
	}
	UUmbrellaBackdropSubsystem* Backdrop = World->GetSubsystem<UUmbrellaBackdropSubsystem>();
	if (TestNotNull(TEXT("backdrop"), Backdrop) && TestTrue(TEXT("layers built"), Backdrop->BuildLayers() > 0))
	{
		// No asset in the slot: the stand-in panel stays.
		const int32 Layer = 0;
		if (!Backdrop->IsLayerDrawnWithArt(Layer))
		{
			UStaticMeshComponent* Panel = Cast<UStaticMeshComponent>(Backdrop->GetLayers()[Layer]->GetRootComponent());
			TestEqual(TEXT("stand-in is the cube"), Panel->GetStaticMesh()->GetFName(), FName(TEXT("Cube")));
			TestTrue(TEXT("a missing texture keeps the cube"), Backdrop->ApplyLayerArt(Layer, nullptr) == EArtSlotDraw::NoTexture && Panel->GetStaticMesh()->GetFName() == FName(TEXT("Cube")));
			UTexture2D* Texture = ArtSlotTestTexture();
			TestTrue(TEXT("texture draws the layer"), Backdrop->ApplyLayerArt(Layer, Texture) == EArtSlotDraw::Drawn);
			TestTrue(TEXT("layer shows art"), Backdrop->IsLayerDrawnWithArt(Layer));
			TestTrue(TEXT("the layer's texture is the one given"), ArtSlotParamTexture(Panel) == Texture);
			TestEqual(TEXT("art has no collision"), static_cast<int32>(Panel->GetCollisionEnabled()), static_cast<int32>(ECollisionEnabled::NoCollision));
			TestEqual(TEXT("art keeps the panel width"), static_cast<float>(Panel->GetRelativeScale3D().X * UmbrellaArtSlotConst::PlaneEdge), UmbrellaBackdropConst::PanelWidth);
			TestEqual(TEXT("art keeps the panel height"), static_cast<float>(Panel->GetRelativeScale3D().Y * UmbrellaArtSlotConst::PlaneEdge), UmbrellaBackdropConst::PanelHeight);
			TestTrue(TEXT("art stays behind Ella"), Backdrop->GetLayers()[Layer]->GetActorLocation().Y < UmbrellaDrawOrder::EllaY);
		}
		// Paper (Sky) tiles; the other layers do not.
		int32 SkyIndex = INDEX_NONE;
		for (int32 Index = 0; Index < Backdrop->GetBuiltSpecs().Num(); ++Index)
		{
			if (Backdrop->GetBuiltSpecs()[Index].Name == TEXT("Sky"))
			{
				SkyIndex = Index;
			}
		}
		if (SkyIndex != INDEX_NONE && !Backdrop->IsLayerDrawnWithArt(SkyIndex))
		{
			Backdrop->ApplyLayerArt(SkyIndex, ArtSlotTestTexture());
			const UMaterialInstanceDynamic* Dynamic = Cast<UMaterialInstanceDynamic>(Cast<UStaticMeshComponent>(Backdrop->GetLayers()[SkyIndex]->GetRootComponent())->GetMaterial(0));
			float TileU = 0.0f;
			if (TestNotNull(TEXT("dynamic material"), Dynamic) && Dynamic->GetScalarParameterValue(FName(TEXT("TileU")), TileU))
			{
				TestTrue(TEXT("paper repeats across the panel"), TileU > 1.0f);
			}
		}
	}
	ArtSlotTestEnd(World);
	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FArtSlotElla, "UmbrellaElla.Feedback.World.ArtSlotElla",
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::ClientContext | EAutomationTestFlags::EngineFilter)

bool FArtSlotElla::RunTest(const FString& Parameters)
{
	UWorld* World = ArtSlotTestWorld();
	if (!TestNotNull(TEXT("world"), World))
	{
		return false;
	}
	AActor* Owner = World->SpawnActor<AActor>();
	USceneComponent* Root = NewObject<USceneComponent>(Owner, TEXT("Root"));
	Owner->SetRootComponent(Root);
	Root->RegisterComponent();
	UEllaAnimPresenterComponent* Presenter = NewObject<UEllaAnimPresenterComponent>(Owner);
	Presenter->RegisterComponent();
	Presenter->BuildVisual();
	if (TestNotNull(TEXT("stand-in"), Presenter->GetStandIn()) && !Presenter->IsShowingArt())
	{
		TestTrue(TEXT("no asset keeps the stand-in"), Presenter->IsShowingStandIn());
		UTexture2D* Idle = ArtSlotTestTexture();
		UTexture2D* Hurt = ArtSlotTestTexture();
		Presenter->SetStateTexture(EEllaVisualState::Idle, Idle);
		TestTrue(TEXT("idle picture draws art"), Presenter->IsShowingArt());
		TestFalse(TEXT("art is not the stand-in"), Presenter->IsShowingStandIn());
		TestTrue(TEXT("idle picture shown"), ArtSlotParamTexture(Presenter->GetStandIn()) == Idle);
		Presenter->SetStateTexture(EEllaVisualState::Hurt, Hurt);
		Presenter->SetVisualState(EEllaVisualState::Hurt);
		TestTrue(TEXT("hurt picture shown"), ArtSlotParamTexture(Presenter->GetStandIn()) == Hurt);
		Presenter->SetVisualState(EEllaVisualState::Shoot);
		TestTrue(TEXT("a state without a picture shows idle"), ArtSlotParamTexture(Presenter->GetStandIn()) == Idle);
		const FVector Down = ArtSlot::PlaneScaleFor(UEllaAnimPresenterComponent::StandInScaleFor(EEllaVisualState::Down));
		Presenter->SetVisualState(EEllaVisualState::Down);
		TestEqual(TEXT("art keeps the state footprint"), Presenter->GetStandIn()->GetRelativeScale3D(), Down);
		TestEqual(TEXT("art has no collision"), static_cast<int32>(Presenter->GetStandIn()->GetCollisionEnabled()), static_cast<int32>(ECollisionEnabled::NoCollision));
	}
	// A state with its own art and no Idle art still draws (review item 2).
	AActor* Owner2 = World->SpawnActor<AActor>();
	USceneComponent* Root2 = NewObject<USceneComponent>(Owner2, TEXT("Root"));
	Owner2->SetRootComponent(Root2);
	Root2->RegisterComponent();
	UEllaAnimPresenterComponent* NoIdle = NewObject<UEllaAnimPresenterComponent>(Owner2);
	NoIdle->RegisterComponent();
	NoIdle->BuildVisual();
	if (TestNotNull(TEXT("no-idle stand-in"), NoIdle->GetStandIn()) && !NoIdle->IsShowingArt())
	{
		UTexture2D* ShootOnly = ArtSlotTestTexture();
		NoIdle->SetStateTexture(EEllaVisualState::Shoot, ShootOnly);
		TestTrue(TEXT("shoot-only art draws"), NoIdle->IsShowingArt());
		TestTrue(TEXT("shoot-only picture shown"), ArtSlotParamTexture(NoIdle->GetStandIn()) == ShootOnly);
	}
	ArtSlotTestEnd(World);
	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FArtSlotEllaFlipbookPaths, "UmbrellaElla.Feedback.ArtSlotEllaFlipbookPaths",
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::ClientContext | EAutomationTestFlags::EngineFilter)

bool FArtSlotEllaFlipbookPaths::RunTest(const FString& Parameters)
{
	const TArray<FString> Open = UEllaAnimPresenterComponent::FlipbookSlotPaths(EEllaVisualState::Idle);
	if (TestEqual(TEXT("two paths per state"), Open.Num(), 2))
	{
		TestEqual(TEXT("passed asset first"), Open[0], FString(TEXT("/Game/UmbrellaElla/Art/Ella/FB_Ella_Open.FB_Ella_Open")));
		TestEqual(TEXT("placeholder second"), Open[1], FString(TEXT("/Game/UmbrellaElla/Art/Ella/FB_Ella_Open_PH.FB_Ella_Open_PH")));
	}
	TestEqual(TEXT("shoot is Attack"), UEllaAnimPresenterComponent::FlipbookSlotName(EEllaVisualState::Shoot), FString(TEXT("Attack")));
	TestEqual(TEXT("absorb is Shield"), UEllaAnimPresenterComponent::FlipbookSlotName(EEllaVisualState::Absorb), FString(TEXT("Shield")));
	TestEqual(TEXT("down is Closed"), UEllaAnimPresenterComponent::FlipbookSlotName(EEllaVisualState::Down), FString(TEXT("Closed")));
	TestEqual(TEXT("hurt has no flipbook slot"), UEllaAnimPresenterComponent::FlipbookSlotPaths(EEllaVisualState::Hurt).Num(), 0);
	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FArtSlotKeeperEnemy, "UmbrellaElla.Feedback.World.ArtSlotKeeperEnemy",
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::ClientContext | EAutomationTestFlags::EngineFilter)

bool FArtSlotKeeperEnemy::RunTest(const FString& Parameters)
{
	UWorld* World = ArtSlotTestWorld();
	if (!TestNotNull(TEXT("world"), World))
	{
		return false;
	}
	UKeeperPresenterSubsystem* KeeperPresenter = World->GetSubsystem<UKeeperPresenterSubsystem>();
	AKeeperOfTime* Keeper = World->SpawnActor<AKeeperOfTime>();
	if (TestNotNull(TEXT("keeper presenter"), KeeperPresenter) && TestNotNull(TEXT("keeper"), Keeper))
	{
		UTexture2D* Texture = ArtSlotTestTexture();
		TestTrue(TEXT("keeper takes a picture"), KeeperPresenter->ShowArt(Keeper, Texture) == EArtSlotDraw::Drawn);
		TestTrue(TEXT("a second picture is refused"), KeeperPresenter->ShowArt(Keeper, Texture) != EArtSlotDraw::Drawn);
	}
	UEnemyPresenterSubsystem* EnemyPresenter = World->GetSubsystem<UEnemyPresenterSubsystem>();
	AUmbrellaEnemy* Enemy = World->SpawnActor<AUmbrellaEnemy>();
	if (TestNotNull(TEXT("enemy presenter"), EnemyPresenter) && TestNotNull(TEXT("enemy"), Enemy))
	{
		UTexture2D* Texture = ArtSlotTestTexture();
		TestTrue(TEXT("enemy takes a picture"), EnemyPresenter->ShowArt(Enemy, Texture) == EArtSlotDraw::Drawn);
		const UStaticMeshComponent* Mesh = nullptr;
		TInlineComponentArray<UStaticMeshComponent*> Meshes(Enemy);
		for (UStaticMeshComponent* Candidate : Meshes)
		{
			if (Candidate->GetFName() == FName(TEXT("EnemyStandIn")))
			{
				Mesh = Candidate;
			}
		}
		if (TestNotNull(TEXT("enemy stand-in"), Mesh))
		{
			TestTrue(TEXT("enemy shows the picture"), ArtSlot::HasArt(Mesh) && ArtSlotParamTexture(Mesh) == Texture);
			TestEqual(TEXT("enemy art has no collision"), static_cast<int32>(Mesh->GetCollisionEnabled()), static_cast<int32>(ECollisionEnabled::NoCollision));
		}
	}
	ArtSlotTestEnd(World);
	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FBackdropCoversRoute, "UmbrellaElla.Feedback.World.BackdropCoversRoute",
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::ClientContext | EAutomationTestFlags::EngineFilter)

bool FBackdropCoversRoute::RunTest(const FString& Parameters)
{
	// Route-stage coverage: the backdrop covers every route stage, at the stage's middle and at both ends.
	const int32 StageCount = GetDefault<UUmbrellaTuning>()->Field.RouteSlotCount;
	TestEqual(TEXT("route has nine stages"), StageCount, 9);
	UWorld* World = ArtSlotTestWorld();
	if (!TestNotNull(TEXT("world"), World))
	{
		return false;
	}
	UUmbrellaBackdropSubsystem* Backdrop = World->GetSubsystem<UUmbrellaBackdropSubsystem>();
	if (TestNotNull(TEXT("backdrop"), Backdrop) && TestTrue(TEXT("layers built"), Backdrop->BuildLayers() > 0))
	{
		for (int32 Slot = 0; Slot < StageCount; ++Slot)
		{
			TestTrue(*FString::Printf(TEXT("stage %d is covered"), Slot), Backdrop->IsRouteStageCovered(Slot));
		}
		TestEqual(TEXT("all stages covered"), Backdrop->CountCoveredStages(), StageCount);
		// The covering holds after the layers follow a camera to the far end of the route, and with art on a layer.
		Backdrop->ScrollTo(UUmbrellaBackdropSubsystem::StageCameraX(StageCount - 1));
		Backdrop->ApplyLayerArt(0, ArtSlotTestTexture());
		TestEqual(TEXT("still covered after scroll and art"), Backdrop->CountCoveredStages(), StageCount);
		// Each built panel is really there: its actor sits within the footprint the cover check uses.
		const float EndCamera = UUmbrellaBackdropSubsystem::StageCameraX(StageCount - 1);
		for (int32 Index = 0; Index < Backdrop->GetLayers().Num(); ++Index)
		{
			const FBox2D Box = UUmbrellaBackdropSubsystem::LayerFootprint(EndCamera, Backdrop->GetBuiltSpecs()[Index].Parallax);
			TestTrue(TEXT("panel actor is at its footprint centre"), FMath::IsNearlyEqual(static_cast<float>(Backdrop->GetLayers()[Index]->GetActorLocation().X), static_cast<float>(Box.GetCenter().X), 1.0f));
		}
	}
	ArtSlotTestEnd(World);
	return true;
}


IMPLEMENT_SIMPLE_AUTOMATION_TEST(FArtSlotShots, "UmbrellaElla.Feedback.World.ArtSlotShots",
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::ClientContext | EAutomationTestFlags::EngineFilter)

bool FArtSlotShots::RunTest(const FString& Parameters)
{
	UWorld* World = ArtSlotTestWorld();
	if (!TestNotNull(TEXT("world"), World))
	{
		return false;
	}
	TestEqual(TEXT("player shot slot"), UShotPresenterSubsystem::VisualIdFor(EUmbrellaShotKind::PlayerBlast), FString(TEXT("shot:gold")));
	TestEqual(TEXT("owl bolt slot"), UShotPresenterSubsystem::VisualIdFor(EUmbrellaShotKind::EnemyRed), FString(TEXT("shot:red")));
	TestEqual(TEXT("yellow shot slot"), UShotPresenterSubsystem::VisualIdFor(EUmbrellaShotKind::EnemyYellow), FString(TEXT("shot:yellow")));
	UShotPresenterSubsystem* Presenter = World->GetSubsystem<UShotPresenterSubsystem>();
	FUmbrellaShotSpec Spec;
	Spec.Kind = EUmbrellaShotKind::EnemyRed;
	Spec.Velocity = FVector(100.0, 0.0, 0.0);
	AUmbrellaProjectile* Shot = AUmbrellaProjectile::Fire(World, Spec);
	if (TestNotNull(TEXT("shot presenter"), Presenter) && TestNotNull(TEXT("shot"), Shot))
	{
		UStaticMeshComponent* Mesh = Cast<UStaticMeshComponent>(Shot->GetRootComponent());
		const FVector SphereScale = Mesh ? Mesh->GetRelativeScale3D() : FVector::ZeroVector;
		UTexture2D* Texture = ArtSlotTestTexture();
		TestTrue(TEXT("shot takes a picture"), Presenter->ShowArt(Shot, Texture) == EArtSlotDraw::Drawn);
		TestTrue(TEXT("second picture refused"), Presenter->ShowArt(Shot, Texture) != EArtSlotDraw::Drawn);
		if (TestNotNull(TEXT("shot visual"), Mesh))
		{
			TestTrue(TEXT("shot shows the picture"), ArtSlot::HasArt(Mesh) && ArtSlotParamTexture(Mesh) == Texture);
			TestEqual(TEXT("shot art keeps the sphere width"), Mesh->GetRelativeScale3D().X, SphereScale.X);
			TestEqual(TEXT("shot art keeps the sphere height"), Mesh->GetRelativeScale3D().Y, SphereScale.Z);
			TestEqual(TEXT("shot art has no collision"), static_cast<int32>(Mesh->GetCollisionEnabled()), static_cast<int32>(ECollisionEnabled::NoCollision));
		}
	}
	UUmbrellaVfxSubsystem* Vfx = World->GetSubsystem<UUmbrellaVfxSubsystem>();
	if (TestNotNull(TEXT("vfx"), Vfx))
	{
		FUmbrellaEvent Event;
		Event.Type = EUmbrellaEventType::ProjectileContact;
		Vfx->PlayForEvent(Event);
		AActor* Hit = Vfx->GetLastActor();
		if (TestNotNull(TEXT("impact effect"), Hit))
		{
			UTexture2D* Texture = ArtSlotTestTexture();
			TestTrue(TEXT("bolt hit takes a picture"), Vfx->ShowImpactArt(Hit, Texture) == EArtSlotDraw::Drawn);
			const UStaticMeshComponent* HitMesh = Cast<UStaticMeshComponent>(Hit->GetRootComponent());
			TestTrue(TEXT("bolt hit shows the picture"), HitMesh && ArtSlot::HasArt(HitMesh) && ArtSlotParamTexture(HitMesh) == Texture);
		}
	}
	ArtSlotTestEnd(World);
	return true;
}


IMPLEMENT_SIMPLE_AUTOMATION_TEST(FArtSlotSheetFrames, "UmbrellaElla.Feedback.World.ArtSlotSheetFrames",
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::ClientContext | EAutomationTestFlags::EngineFilter)

bool FArtSlotSheetFrames::RunTest(const FString& Parameters)
{
	FUmbrellaTestWorld Harness;
	UWorld* World = Harness.GetWorld();
	UUmbrellaVfxDirectorSubsystem* Director = World ? World->GetSubsystem<UUmbrellaVfxDirectorSubsystem>() : nullptr;
	const FVfxArtRow* Row = VfxCatalog::Find(TEXT("SmallBlastTravel"));
	if (!TestNotNull(TEXT("effect director"), Director) || !TestNotNull(TEXT("sheet row"), Row))
	{
		return false;
	}
	TestTrue(TEXT("effect plays"), Director->Play(TEXT("SmallBlastTravel"), FVector(0.0, 0.0, 300.0), nullptr) > 0);
	UStaticMeshComponent* Visual = Cast<UStaticMeshComponent>(IsValid(Director->GetLiveActor(TEXT("SmallBlastTravel"))) ? Director->GetLiveActor(TEXT("SmallBlastTravel"))->GetRootComponent() : nullptr);
	if (!TestNotNull(TEXT("effect visual"), Visual) || !TestTrue(TEXT("the sheet is drawn, not the stand-in"), VfxSheetVisual::HasArt(Visual)))
	{
		return false;
	}
	const UMaterialInstanceDynamic* Dynamic = Cast<UMaterialInstanceDynamic>(Visual->GetMaterial(0));
	if (!TestNotNull(TEXT("sheet material"), Dynamic))
	{
		return false;
	}
	float Frame = -1.0f;
	Dynamic->GetScalarParameterValue(FName(TEXT("Frame")), Frame);
	TestEqual(TEXT("starts on the first frame"), Frame, 0.0f);
	const float Elapsed = 3.5f / Row->Fps;
	Director->StepEffects(Elapsed);
	Dynamic->GetScalarParameterValue(FName(TEXT("Frame")), Frame);
	TestTrue(TEXT("frame advanced with game time"), Frame > 0.0f);
	TestEqual(TEXT("frame is the catalogue frame at that time"), static_cast<int32>(Frame), VfxCatalog::FrameAt(*Row, Elapsed));
	Director->StepEffects(Elapsed);
	float Later = -1.0f;
	Dynamic->GetScalarParameterValue(FName(TEXT("Frame")), Later);
	TestTrue(TEXT("frame keeps advancing"), Later > Frame);
	return true;
}

#endif
