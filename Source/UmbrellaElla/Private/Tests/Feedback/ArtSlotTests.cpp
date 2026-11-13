#include "Attack/StreamBeamActor.h"
#include "Components/StaticMeshComponent.h"
#include "Feedback/Art/ArtSlot.h"
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
#include "Feedback/Anim/WindPresenterSubsystem.h"
#include "Field/WindCurrent.h"
#include "Feedback/Vfx/UmbrellaVfxDirectorSubsystem.h"
#include "Feedback/Vfx/VfxCatalog.h"
#include "Feedback/Vfx/VfxSheetVisual.h"
#include "Tests/Shared/UmbrellaTestWorld.h"
#include "Feedback/Vfx/UmbrellaVfxSubsystem.h"
#include "Core/UmbrellaEvent.h"
#include "Core/UmbrellaEventBus.h"
#include "Projectile/UmbrellaProjectile.h"
#include "Feedback/Background/UmbrellaBackdropSubsystem.h"
#include "Feedback/Background/SceneArtSubsystem.h"
#include "Level/LevelCatalogue.h"
#include "GameFramework/Actor.h"
#include "Materials/MaterialInstanceDynamic.h"
#include "Misc/AutomationTest.h"
#include "Owl/KeeperOfTime.h"
#include "Feedback/Ui/UiArtSubsystem.h"

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
		// When the slot's own asset exists (T_Keeper_Owl_PH is on main), the stand-in already shows it at spawn, so a
		// second picture is refused; without the asset the first picture is drawn and the second refused.
		const UStaticMeshComponent* KeeperMesh = FindObjectFast<UStaticMeshComponent>(Keeper, FName(TEXT("KeeperStandIn")));
		if (KeeperMesh && ArtSlot::HasArt(KeeperMesh))
		{
			TestTrue(TEXT("keeper already shows its slot art"), ArtSlot::HasArt(KeeperMesh));
		}
		else
		{
			TestTrue(TEXT("keeper takes a picture"), KeeperPresenter->ShowArt(Keeper, Texture) == EArtSlotDraw::Drawn);
		}
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

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FArtSlotLoaderCache, "UmbrellaElla.Feedback.World.ArtSlotLoaderCache",
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::ClientContext | EAutomationTestFlags::EngineFilter)

bool FArtSlotLoaderCache::RunTest(const FString& Parameters)
{
	// Apply loads the material and plane once; later draws, and a row whose asset exists, load nothing again.
	UWorld* World = ArtSlotTestWorld();
	if (!TestNotNull(TEXT("world"), World))
	{
		return false;
	}
	const FArtSlotRow* Row = ArtSlot::Find(TEXT("ella-state:Down"));
	AActor* Owner = World->SpawnActor<AActor>();
	if (TestNotNull(TEXT("row"), Row) && TestNotNull(TEXT("owner"), Owner))
	{
		UTexture2D* Texture = ArtSlotTestTexture();
		auto MakeMesh = [Owner]()
		{
			UStaticMeshComponent* Mesh = NewObject<UStaticMeshComponent>(Owner);
			Mesh->RegisterComponent();
			return Mesh;
		};
		TestTrue(TEXT("first draw"), ArtSlot::Apply(MakeMesh(), Texture, *Row, FVector::OneVector) == EArtSlotDraw::Drawn);
		const int32 After = ArtSlot::LoadCallCount();
		for (int32 Index = 0; Index < 5; ++Index)
		{
			ArtSlot::Apply(MakeMesh(), Texture, *Row, FVector::OneVector);
		}
		TestEqual(TEXT("five more draws load nothing"), ArtSlot::LoadCallCount(), After);
		ArtSlot::LoadTexture(*Row);
		const int32 AfterTexture = ArtSlot::LoadCallCount();
		ArtSlot::LoadTexture(*Row);
		const bool bFound = ArtSlot::LoadTexture(*Row) != nullptr;
		TestTrue(TEXT("a texture that exists loads once"), !bFound || ArtSlot::LoadCallCount() == AfterTexture);
	}
	ArtSlotTestEnd(World);
	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FArtSlotUiScreens, "UmbrellaElla.Feedback.World.ArtSlotUiScreens",
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::ClientContext | EAutomationTestFlags::EngineFilter)

bool FArtSlotUiScreens::RunTest(const FString& Parameters)
{
	// Every flow screen has its own slot row; a picture shows click-through, swaps with the screen, and clears.
	TSet<FString> Assets;
	for (int32 Value = 0; Value <= static_cast<int32>(EFlowScreen::Statistics); ++Value)
	{
		const FString Id = UUiArtSubsystem::VisualIdFor(static_cast<EFlowScreen>(Value));
		const FArtSlotRow* Row = ArtSlot::Find(*Id);
		if (TestNotNull(*Id, Row))
		{
			Assets.Add(ArtSlot::SlotPath(*Row));
		}
	}
	TestEqual(TEXT("one asset per screen"), Assets.Num(), static_cast<int32>(EFlowScreen::Statistics) + 1);
	UWorld* World = ArtSlotTestWorld();
	if (!TestNotNull(TEXT("world"), World))
	{
		return false;
	}
	UUiArtSubsystem* Ui = World->GetSubsystem<UUiArtSubsystem>();
	if (TestNotNull(TEXT("ui art subsystem"), Ui))
	{
		UTexture2D* Texture = ArtSlotTestTexture();
		Ui->ShowScreenArt(EFlowScreen::Title, nullptr);
		TestFalse(TEXT("nothing shown without a picture"), Ui->IsShowingArt());
		Ui->ShowScreenArt(EFlowScreen::Title, Texture);
		TestTrue(TEXT("shown for Title"), Ui->IsShowingArt() && Ui->GetShownScreen() == EFlowScreen::Title && Ui->GetShownTexture() == Texture);
		TestTrue(TEXT("clicks go through to the menu"), Ui->IsClickThrough());
		Ui->ShowScreenArt(EFlowScreen::Paused, Texture);
		TestTrue(TEXT("paused picture replaces it"), Ui->IsShowingArt() && Ui->GetShownScreen() == EFlowScreen::Paused);
		Ui->ClearScreenArt();
		TestFalse(TEXT("cleared"), Ui->IsShowingArt());
	}
	ArtSlotTestEnd(World);
	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FArtSlotRoadwardenVariants, "UmbrellaElla.Feedback.World.ArtSlotRoadwardenVariants",
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::ClientContext | EAutomationTestFlags::EngineFilter)

bool FArtSlotRoadwardenVariants::RunTest(const FString& Parameters)
{
	// Each Roadwarden equipment variant has its own slot row and path.
	TSet<FString> Slots;
	for (const ERoadwardenEquipment Equipment : { ERoadwardenEquipment::SundialCaster, ERoadwardenEquipment::ArmillaryLauncher, ERoadwardenEquipment::EscapementRepeater })
	{
		for (const EEnemyGender Gender : { EEnemyGender::Male, EEnemyGender::Female })
		{
			const FString Id = UEnemyPresenterSubsystem::VisualIdFor(EEnemyType::Roadwarden, Gender, Equipment);
			const FArtSlotRow* Row = ArtSlot::Find(*Id);
			if (TestNotNull(*Id, Row))
			{
				Slots.Add(ArtSlot::TexturePaths(*Row)[0]);
			}
		}
	}
	TestEqual(TEXT("six variants, six distinct assets"), Slots.Num(), 6);
	TestEqual(TEXT("equipment is ignored off Roadwarden"), UEnemyPresenterSubsystem::VisualIdFor(EEnemyType::Floodstrider, EEnemyGender::Male, ERoadwardenEquipment::ArmillaryLauncher), FString(TEXT("enemy:Floodstrider:Male")));
	UWorld* World = ArtSlotTestWorld();
	if (!TestNotNull(TEXT("world"), World))
	{
		return false;
	}
	UEnemyPresenterSubsystem* Presenter = World->GetSubsystem<UEnemyPresenterSubsystem>();
	AUmbrellaEnemy* Enemy = World->SpawnActor<AUmbrellaEnemy>();
	if (TestNotNull(TEXT("presenter"), Presenter) && TestNotNull(TEXT("enemy"), Enemy))
	{
		TestEqual(TEXT("default variant"), Presenter->VisualIdOf(Enemy), UEnemyPresenterSubsystem::VisualIdFor(EEnemyType::Roadwarden, Enemy->GetGender(), ERoadwardenEquipment::SundialCaster));
		Presenter->SetEquipment(Enemy, ERoadwardenEquipment::EscapementRepeater);
		TestEqual(TEXT("stored variant"), Presenter->VisualIdOf(Enemy), UEnemyPresenterSubsystem::VisualIdFor(EEnemyType::Roadwarden, Enemy->GetGender(), ERoadwardenEquipment::EscapementRepeater));
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


IMPLEMENT_SIMPLE_AUTOMATION_TEST(FArtSlotWind, "UmbrellaElla.Feedback.World.ArtSlotWind",
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::ClientContext | EAutomationTestFlags::EngineFilter)

bool FArtSlotWind::RunTest(const FString& Parameters)
{
	UWorld* World = ArtSlotTestWorld();
	if (!TestNotNull(TEXT("world"), World))
	{
		return false;
	}
	TestEqual(TEXT("gust starts on frame 0"), UWindPresenterSubsystem::GustFrameAt(0.0f, 8), 0);
	TestTrue(TEXT("gust advances"), UWindPresenterSubsystem::GustFrameAt(0.5f, 8) > 0);
	TestTrue(TEXT("gust wraps inside the sheet"), UWindPresenterSubsystem::GustFrameAt(99.0f, 8) < 8);
	UWindPresenterSubsystem* Presenter = World->GetSubsystem<UWindPresenterSubsystem>();
	AWindCurrent* Wind = World->SpawnActor<AWindCurrent>();
	if (TestNotNull(TEXT("wind presenter"), Presenter) && TestNotNull(TEXT("wind"), Wind))
	{
		Wind->SetHalfExtent(300.0f, 200.0f);
		UStaticMeshComponent* Field = Wind->GetField();
		UTexture2D* Texture = ArtSlotTestTexture();
		const FString FieldId = UmbrellaWindPresenterConst::FieldVisual;
		TestTrue(TEXT("field takes the picture"), Presenter->ShowArt(Wind, FieldId, Texture) == EArtSlotDraw::Drawn);
		TestTrue(TEXT("second field picture refused"), Presenter->ShowArt(Wind, FieldId, Texture) != EArtSlotDraw::Drawn);
		TestTrue(TEXT("field shows the picture"), ArtSlot::IsDrawingArt(Field) && ArtSlotParamTexture(Field) == Texture);
		TestEqual(TEXT("picture is the field width"), Field->GetRelativeScale3D().X, 6.0);
		TestEqual(TEXT("picture is the field height"), Field->GetRelativeScale3D().Y, 4.0);
		TestEqual(TEXT("picture has no collision"), static_cast<int32>(Field->GetCollisionEnabled()), static_cast<int32>(ECollisionEnabled::NoCollision));

		// The current refreshes its colour card when resized; the presenter puts the picture back at the new size.
		Wind->SetHalfExtent(400.0f, 200.0f);
		TestFalse(TEXT("refresh put the card back"), ArtSlot::IsDrawingArt(Field));
		Presenter->Tick(0.0f);
		TestTrue(TEXT("picture is back after refresh"), ArtSlot::IsDrawingArt(Field) && ArtSlotParamTexture(Field) == Texture);
		TestEqual(TEXT("picture follows the new width"), Field->GetRelativeScale3D().X, 8.0);

		for (const FString& Overlay : { FString(UmbrellaWindPresenterConst::LinesVisual), FString(UmbrellaWindPresenterConst::GustVisual) })
		{
			// The shipped _PH gust sheet may already be drawn by the tick above; then the transient picture is refused.
			const bool bAlready = UWindPresenterSubsystem::FindOverlay(Wind, Overlay) != nullptr;
			const EArtSlotDraw OverlayResult = bAlready ? EArtSlotDraw::Drawn : Presenter->ShowArt(Wind, Overlay, Texture);
			TestTrue(*FString::Printf(TEXT("overlay %s is drawn (result %d)"), *Overlay, static_cast<int32>(OverlayResult)), OverlayResult == EArtSlotDraw::Drawn);
			const UStaticMeshComponent* Mesh = UWindPresenterSubsystem::FindOverlay(Wind, Overlay);
			if (TestNotNull(TEXT("overlay component"), Mesh))
			{
				TestTrue(TEXT("overlay shows a picture"), ArtSlot::IsDrawingArt(Mesh) && (bAlready || ArtSlotParamTexture(Mesh) == Texture));
				TestEqual(TEXT("overlay matches the field width"), Mesh->GetRelativeScale3D().X, 8.0);
				TestEqual(TEXT("overlay has no collision"), static_cast<int32>(Mesh->GetCollisionEnabled()), static_cast<int32>(ECollisionEnabled::NoCollision));
			}
		}

		// A wind slot asset that exists must be drawn by a fresh current.
		AWindCurrent* Fresh = World->SpawnActor<AWindCurrent>();
		if (TestNotNull(TEXT("fresh wind"), Fresh))
		{
			Fresh->SetHalfExtent(300.0f, 200.0f);
			Presenter->Tick(0.0f);
			for (const TCHAR* Visual : { UmbrellaWindPresenterConst::FieldVisual, UmbrellaWindPresenterConst::LinesVisual, UmbrellaWindPresenterConst::GustVisual })
			{
				const FArtSlotRow* Row = ArtSlot::Find(Visual);
				if (TestNotNull(TEXT("wind slot row"), Row) && ArtSlot::LoadTexture(*Row))
				{
					const bool bDrawn = FString(Visual) == UmbrellaWindPresenterConst::FieldVisual ? ArtSlot::IsDrawingArt(Fresh->GetField()) : UWindPresenterSubsystem::FindOverlay(Fresh, Visual) != nullptr;
					TestTrue(*FString::Printf(TEXT("%s asset exists, so the wind draws it"), Visual), bDrawn);
				}
			}
		}
	}
	ArtSlotTestEnd(World);
	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FArtSlotScene, "UmbrellaElla.Feedback.World.ArtSlotScene",
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::ClientContext | EAutomationTestFlags::EngineFilter)

bool FArtSlotScene::RunTest(const FString& Parameters)
{
	UWorld* World = ArtSlotTestWorld();
	if (!TestNotNull(TEXT("world"), World))
	{
		return false;
	}
	USceneArtSubsystem* Scene = World->GetSubsystem<USceneArtSubsystem>();
	if (TestNotNull(TEXT("scene art subsystem"), Scene))
	{
		UTexture2D* Texture = ArtSlotTestTexture();
		TSet<FName> Visuals;
		for (const FSceneArtSpec& Spec : USceneArtSubsystem::Specs())
		{
			Visuals.Add(Spec.Visual);
		}
		TestEqual(TEXT("six scene slots have a consumer"), Visuals.Num(), 6);
		for (const FName Visual : Visuals)
		{
			const FString Id = Visual.ToString();
			const FArtSlotRow* Row = ArtSlot::Find(*Id);
			if (!TestNotNull(*FString::Printf(TEXT("%s has a slot row"), *Id), Row))
			{
				continue;
			}
			TestFalse(*FString::Printf(TEXT("%s names a consumer"), *Id), FString(Row->DrawnBy) == TEXT("-"));
			// A slot asset that exists is drawn at start; otherwise the transient picture is.
			const bool bAssetExists = ArtSlot::LoadTexture(*Row) != nullptr;
			TestEqual(*FString::Printf(TEXT("%s is drawn at start iff its asset exists"), *Id), Scene->PanelCount(Id) > 0, bAssetExists);
			if (!bAssetExists)
			{
				TestTrue(*FString::Printf(TEXT("%s takes a picture"), *Id), Scene->ShowArt(Id, Texture) == EArtSlotDraw::Drawn);
			}
			TestTrue(*FString::Printf(TEXT("second picture for %s refused"), *Id), Scene->ShowArt(Id, Texture) != EArtSlotDraw::Drawn);
			const int32 Expected = Id == TEXT("bg:start-end") ? 2 : 1;
			TestEqual(*FString::Printf(TEXT("%s panel count"), *Id), Scene->PanelCount(Id), Expected);
			const UStaticMeshComponent* Panel = Scene->FindPanel(Id);
			if (TestNotNull(*FString::Printf(TEXT("%s panel"), *Id), Panel))
			{
				TestTrue(*FString::Printf(TEXT("%s shows art"), *Id), ArtSlot::IsDrawingArt(Panel));
				TestEqual(*FString::Printf(TEXT("%s has no collision"), *Id), static_cast<int32>(Panel->GetCollisionEnabled()), static_cast<int32>(ECollisionEnabled::NoCollision));
			}
		}

		for (const FName Visual : Visuals)
		{
			TestEqual(*FString::Printf(TEXT("%s follows its own flag (all on by default)"), *Visual.ToString()), USceneArtSubsystem::IsVisualEnabled(Visual.ToString()), true);
		}

		// Depth: backdrop pictures sit between the sky and the play layer; the frame is in front of play.
		for (const FSceneArtSpec& Spec : USceneArtSubsystem::Specs())
		{
			const bool bFrame = Spec.Visual == FName(TEXT("scene:gameplay-frame"));
			TestTrue(*FString::Printf(TEXT("%s depth"), *Spec.Visual.ToString()), bFrame ? Spec.Depth >= UmbrellaDrawOrder::ForegroundY : (Spec.Depth >= UmbrellaDrawOrder::BackgroundFarY && Spec.Depth < UmbrellaDrawOrder::ArenaY));
		}

		// Placement: the frame follows the camera, route ends stay at the ends, layers scroll with parallax.
		const float CameraX = 5000.0f;
		Scene->ScrollTo(CameraX);
		const AActor* Frame = Scene->FindPanel(TEXT("scene:gameplay-frame")) ? Scene->FindPanel(TEXT("scene:gameplay-frame"))->GetOwner() : nullptr;
		if (TestNotNull(TEXT("frame actor"), Frame))
		{
			TestEqual(TEXT("frame follows the camera"), static_cast<float>(Frame->GetActorLocation().X), CameraX);
		}
		const AActor* End = Scene->FindPanel(TEXT("bg:start-end"), 1) ? Scene->FindPanel(TEXT("bg:start-end"), 1)->GetOwner() : nullptr;
		if (TestNotNull(TEXT("route end actor"), End))
		{
			TestTrue(TEXT("route end picture sits at the route end"), End->GetActorLocation().X > LevelCatalogue::RouteLength() - GetDefault<UUmbrellaTuning>()->ArenaCamera.ArenaWidth);
		}
		const AActor* Land = Scene->FindPanel(TEXT("bg:land")) ? Scene->FindPanel(TEXT("bg:land"))->GetOwner() : nullptr;
		if (TestNotNull(TEXT("land actor"), Land))
		{
			TestEqual(TEXT("land scrolls like a backdrop layer"), static_cast<float>(Land->GetActorLocation().X), UUmbrellaBackdropSubsystem::LayerXForCamera(CameraX, UmbrellaBackdropConst::FarParallax));
		}
	}
	ArtSlotTestEnd(World);
	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FArtSlotBeam, "UmbrellaElla.Feedback.World.ArtSlotBeam",
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::ClientContext | EAutomationTestFlags::EngineFilter)

bool FArtSlotBeam::RunTest(const FString& Parameters)
{
	UWorld* World = ArtSlotTestWorld();
	if (!TestNotNull(TEXT("world"), World))
	{
		return false;
	}
	UShotPresenterSubsystem* Presenter = World->GetSubsystem<UShotPresenterSubsystem>();
	AStreamBeamActor* Beam = World->SpawnActor<AStreamBeamActor>();
	if (TestNotNull(TEXT("shot presenter"), Presenter) && TestNotNull(TEXT("beam"), Beam))
	{
		TestNotNull(TEXT("beam slot row"), ArtSlot::Find(UShotPresenterSubsystem::BeamVisualId()));
		Beam->SetBeam(FVector(0.0, 0.0, 300.0), 800.0f, 14.0f);
		UStaticMeshComponent* Mesh = Cast<UStaticMeshComponent>(Beam->GetRootComponent());
		UTexture2D* Texture = ArtSlotTestTexture();
		// A shipped beam asset is drawn on the first tick; otherwise the transient picture is.
		Presenter->Tick(0.0f);
		const bool bAlready = ArtSlot::HasArt(Mesh);
		if (!bAlready)
		{
			TestTrue(TEXT("beam takes the picture"), Presenter->ShowBeamArt(Beam, Texture) == EArtSlotDraw::Drawn);
		}
		TestTrue(TEXT("second beam picture refused"), Presenter->ShowBeamArt(Beam, Texture) != EArtSlotDraw::Drawn);
		TestTrue(TEXT("beam shows a picture"), ArtSlot::IsDrawingArt(Mesh) && (bAlready || ArtSlotParamTexture(Mesh) == Texture));
		TestEqual(TEXT("beam has no collision"), static_cast<int32>(Mesh->GetCollisionEnabled()), static_cast<int32>(ECollisionEnabled::NoCollision));
		const float Length = Beam->GetEffectiveLength();
		TestEqual(TEXT("picture is the beam length"), static_cast<float>(Mesh->GetComponentScale().X), Length / AStreamBeamActor::CubeSize);
		// The beam grows and resets its cube scale; the next presenter tick puts the picture back at the beam's size.
		Beam->SetBeam(FVector(0.0, 0.0, 300.0), 1200.0f, 14.0f);
		Presenter->Tick(0.0f);
		TestTrue(TEXT("still a picture after growth"), ArtSlot::IsDrawingArt(Mesh));
		TestEqual(TEXT("picture follows the grown length"), static_cast<float>(Mesh->GetComponentScale().X), Beam->GetEffectiveLength() / AStreamBeamActor::CubeSize);
		TestTrue(TEXT("beam grew"), Beam->GetEffectiveLength() > Length);
	}
	ArtSlotTestEnd(World);
	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FArtSlotKeeperParts, "UmbrellaElla.Feedback.World.ArtSlotKeeperParts",
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::ClientContext | EAutomationTestFlags::EngineFilter)

bool FArtSlotKeeperParts::RunTest(const FString& Parameters)
{
	UWorld* World = ArtSlotTestWorld();
	if (!TestNotNull(TEXT("world"), World))
	{
		return false;
	}
	UKeeperPresenterSubsystem* Presenter = World->GetSubsystem<UKeeperPresenterSubsystem>();
	AKeeperOfTime* Keeper = World->SpawnActor<AKeeperOfTime>();
	if (TestNotNull(TEXT("keeper presenter"), Presenter) && TestNotNull(TEXT("keeper"), Keeper))
	{
		Presenter->ShowStandIn(Keeper);
		UTexture2D* Texture = ArtSlotTestTexture();
		float LastDepth = -1.0e9f;
		for (const UmbrellaKeeperPresenterConst::FKeeperPartLayer& Layer : UmbrellaKeeperPresenterConst::PartLayers)
		{
			const FString Id = Layer.Visual;
			const FArtSlotRow* Row = ArtSlot::Find(*Id);
			if (!TestNotNull(*FString::Printf(TEXT("%s has a slot row"), *Id), Row))
			{
				continue;
			}
			TestFalse(*FString::Printf(TEXT("%s names a consumer"), *Id), FString(Row->DrawnBy) == TEXT("-"));
			TestTrue(*FString::Printf(TEXT("%s layers are ordered back to front"), *Id), Layer.DepthOffset > LastDepth);
			LastDepth = Layer.DepthOffset;
			// A part asset that exists is drawn when the Keeper appears; otherwise the transient picture is.
			const bool bAssetExists = ArtSlot::LoadTexture(*Row) != nullptr;
			TestEqual(*FString::Printf(TEXT("%s drawn at spawn iff its asset exists"), *Id), UKeeperPresenterSubsystem::FindPart(Keeper, Id) != nullptr, bAssetExists);
			if (!bAssetExists)
			{
				TestTrue(*FString::Printf(TEXT("%s takes a picture"), *Id), Presenter->ShowPartArt(Keeper, Id, Texture) == EArtSlotDraw::Drawn);
			}
			TestTrue(*FString::Printf(TEXT("second picture for %s refused"), *Id), Presenter->ShowPartArt(Keeper, Id, Texture) != EArtSlotDraw::Drawn);
			const UStaticMeshComponent* Part = UKeeperPresenterSubsystem::FindPart(Keeper, Id);
			if (TestNotNull(*FString::Printf(TEXT("%s part"), *Id), Part))
			{
				TestTrue(*FString::Printf(TEXT("%s shows art"), *Id), ArtSlot::IsDrawingArt(Part));
				TestEqual(*FString::Printf(TEXT("%s has no collision"), *Id), static_cast<int32>(Part->GetCollisionEnabled()), static_cast<int32>(ECollisionEnabled::NoCollision));
				TestEqual(*FString::Printf(TEXT("%s depth offset"), *Id), static_cast<float>(Part->GetComponentLocation().Y - Keeper->GetActorLocation().Y), Layer.DepthOffset);
				TestEqual(*FString::Printf(TEXT("%s is the body width"), *Id), static_cast<float>(Part->GetComponentScale().X), static_cast<float>(UmbrellaKeeperPresenterConst::StandInScale.X));
			}
		}
		// State layers: hidden until a part is destroyed (masks) or the Keeper departs (departure).
		const UStaticMeshComponent* Masks = UKeeperPresenterSubsystem::FindPart(Keeper, UmbrellaKeeperPresenterConst::MaskVisual);
		const UStaticMeshComponent* Departure = UKeeperPresenterSubsystem::FindPart(Keeper, UmbrellaKeeperPresenterConst::DepartureVisual);
		if (TestNotNull(TEXT("mask layer"), Masks) && TestNotNull(TEXT("departure layer"), Departure))
		{
			Presenter->Tick(0.0f);
			TestFalse(TEXT("masks hidden at full health"), Masks->IsVisible());
			TestFalse(TEXT("departure hidden while the Keeper stays"), Departure->IsVisible());
			FUmbrellaEvent Event;
			Event.Type = EUmbrellaEventType::BossPartDestroyed;
			UUmbrellaEventBus::Get(World)->Broadcast(Event);
			Keeper->BeginDeparture(1.0f);
			Presenter->Tick(0.0f);
			TestTrue(TEXT("masks shown after a part is destroyed"), Masks->IsVisible());
			TestTrue(TEXT("departure shown while the Keeper leaves"), Departure->IsVisible());
		}
	}
	ArtSlotTestEnd(World);
	return true;
}

#endif
