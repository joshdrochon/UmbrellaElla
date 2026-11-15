#include "Arena/UmbrellaArena.h"
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
#include "Owl/KeeperLook.h"
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

	UTexture2D* ArtSlotSizedTestTexture(int32 Width, int32 Height)
	{
		UTexture2D* Texture = UTexture2D::CreateTransient(Width, Height);
		Texture->AddToRoot();
		return Texture;
	}

	float ArtSlotParamScalar(const UStaticMeshComponent* Mesh, const TCHAR* Name)
	{
		float Out = -1.0f;
		if (const UMaterialInstanceDynamic* Dynamic = Cast<UMaterialInstanceDynamic>(Mesh->GetMaterial(0)))
		{
			Dynamic->GetScalarParameterValue(FName(Name), Out);
		}
		return Out;
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

	/** Test-only empty state: put the flat stand-in material back, so the slot holds no art (HasArt false). */
	void ArtSlotTestClearArt(UStaticMeshComponent* Mesh, UObject* Outer)
	{
		ArtSlot::SetFlatUnlit(Mesh, Outer, UmbrellaArtSlotConst::StandInDefaultColor);
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
		// Hurt is a 24x1 strip (2x2 cells), Idle a 6x4 grid: different cell shapes, so per-state sizing shows.
		UTexture2D* Hurt = ArtSlotSizedTestTexture(48, 2);
		Presenter->SetStateTexture(EEllaVisualState::Idle, Idle);
		TestTrue(TEXT("idle picture draws art"), Presenter->IsShowingArt());
		TestFalse(TEXT("art is not the stand-in"), Presenter->IsShowingStandIn());
		TestTrue(TEXT("idle picture shown"), ArtSlotParamTexture(Presenter->GetStandIn()) == Idle);
		Presenter->SetStateTexture(EEllaVisualState::Hurt, Hurt);
		Presenter->SetVisualState(EEllaVisualState::Hurt);
		TestTrue(TEXT("hurt picture shown"), ArtSlotParamTexture(Presenter->GetStandIn()) == Hurt);
		Presenter->SetVisualState(EEllaVisualState::Shoot);
		TestTrue(TEXT("a state without a picture shows idle"), ArtSlotParamTexture(Presenter->GetStandIn()) == Idle);
		// screenfix B2: a picture is drawn at its own cell size (art bible height, cell aspect), not the stand-in box.
		// Each state uses its own sheet layout: Hurt (24x1 strip) and Idle (6x4 grid) differ.
		const FArtSlotRow* IdleRow = ArtSlot::Find(TEXT("ella-state:Idle"));
		const FArtSlotRow* HurtRow = ArtSlot::Find(TEXT("ella-state:Hurt"));
		if (TestNotNull(TEXT("idle row"), IdleRow) && TestNotNull(TEXT("hurt row"), HurtRow))
		{
			TestEqual(TEXT("hurt row is a 24x1 strip"), FIntPoint(HurtRow->Cols, HurtRow->Rows), FIntPoint(24, 1));
			TestEqual(TEXT("idle row is a 6x4 grid"), FIntPoint(IdleRow->Cols, IdleRow->Rows), FIntPoint(6, 4));
			const FVector IdleScale = ArtSlot::PlaneScaleFor(UEllaAnimPresenterComponent::ArtBoxScaleFor(Idle, *IdleRow));
			const FVector HurtScale = ArtSlot::PlaneScaleFor(UEllaAnimPresenterComponent::ArtBoxScaleFor(Hurt, *HurtRow));
			TestFalse(TEXT("hurt and idle cells have different shapes"), HurtScale.Equals(IdleScale));
			Presenter->SetVisualState(EEllaVisualState::Hurt);
			TestEqual(TEXT("hurt art is drawn at the hurt cell size"), Presenter->GetStandIn()->GetRelativeScale3D(), HurtScale);
			TestEqual(TEXT("hurt strip draws its one row"), ArtSlotParamScalar(Presenter->GetStandIn(), TEXT("TileV")), 1.0f);
			TestEqual(TEXT("hurt strip is cut in 24 columns"), ArtSlotParamScalar(Presenter->GetStandIn(), TEXT("Cols")), 24.0f);
			Presenter->SetVisualState(EEllaVisualState::Down);
			TestTrue(TEXT("down without its own picture shows idle"), ArtSlotParamTexture(Presenter->GetStandIn()) == Idle);
			TestEqual(TEXT("down falls back to the idle cell size"), Presenter->GetStandIn()->GetRelativeScale3D(), IdleScale);
			TestEqual(TEXT("idle grid draws one of its 4 rows"), ArtSlotParamScalar(Presenter->GetStandIn(), TEXT("TileV")), 0.25f);
			TestEqual(TEXT("idle grid is cut in 6 columns"), ArtSlotParamScalar(Presenter->GetStandIn(), TEXT("Cols")), 6.0f);
		}
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
		UStaticMeshComponent* KeeperMesh = FindObjectFast<UStaticMeshComponent>(Keeper, FName(TEXT("KeeperStandIn")));
		const FArtSlotRow* KeeperRow = ArtSlot::Find(TEXT("keeper:body-hover-flap"));
		if (TestNotNull(TEXT("keeper stand-in"), KeeperMesh) && TestNotNull(TEXT("keeper row"), KeeperRow))
		{
			// Filled: the slot's stand-in texture is drawn at spawn, and a second picture is refused.
			UTexture2D* SlotArt = ArtSlot::LoadTexture(*KeeperRow);
			TestTrue(TEXT("keeper shows its slot stand-in texture"), SlotArt && ArtSlot::HasArt(KeeperMesh) && ArtSlotParamTexture(KeeperMesh) == SlotArt);
			TestTrue(TEXT("a filled keeper refuses a picture"), KeeperPresenter->ShowArt(Keeper, Texture) != EArtSlotDraw::Drawn);
			// Empty: with the slot's art cleared, the first picture is drawn and the second refused.
			ArtSlotTestClearArt(KeeperMesh, Keeper);
			TestFalse(TEXT("cleared keeper has no art"), ArtSlot::HasArt(KeeperMesh));
			TestTrue(TEXT("keeper takes a picture"), KeeperPresenter->ShowArt(Keeper, Texture) == EArtSlotDraw::Drawn);
			TestTrue(TEXT("keeper shows the picture"), ArtSlot::HasArt(KeeperMesh) && ArtSlotParamTexture(KeeperMesh) == Texture);
			TestTrue(TEXT("a second picture is refused"), KeeperPresenter->ShowArt(Keeper, Texture) != EArtSlotDraw::Drawn);
		}
	}
	UEnemyPresenterSubsystem* EnemyPresenter = World->GetSubsystem<UEnemyPresenterSubsystem>();
	AUmbrellaEnemy* Enemy = World->SpawnActor<AUmbrellaEnemy>();
	if (TestNotNull(TEXT("enemy presenter"), EnemyPresenter) && TestNotNull(TEXT("enemy"), Enemy))
	{
		UTexture2D* Texture = ArtSlotTestTexture();
		UStaticMeshComponent* Mesh = nullptr;
		TInlineComponentArray<UStaticMeshComponent*> Meshes(Enemy);
		for (UStaticMeshComponent* Candidate : Meshes)
		{
			if (Candidate->GetFName() == FName(TEXT("EnemyStandIn")))
			{
				Mesh = Candidate;
			}
		}
		const FArtSlotRow* EnemyRow = ArtSlot::Find(*EnemyPresenter->VisualIdOf(Enemy));
		if (TestNotNull(TEXT("enemy stand-in"), Mesh) && TestNotNull(TEXT("enemy row"), EnemyRow))
		{
			// Filled: the slot's stand-in texture is drawn at spawn, and a picture is refused.
			UTexture2D* SlotArt = ArtSlot::LoadTexture(*EnemyRow);
			TestTrue(TEXT("enemy shows its slot stand-in texture"), SlotArt && ArtSlot::HasArt(Mesh) && ArtSlotParamTexture(Mesh) == SlotArt);
			TestTrue(TEXT("a filled enemy refuses a picture"), EnemyPresenter->ShowArt(Enemy, Texture) != EArtSlotDraw::Drawn);
			// Empty: with the slot's art cleared, the picture is drawn.
			ArtSlotTestClearArt(Mesh, Enemy);
			TestFalse(TEXT("cleared enemy has no art"), ArtSlot::HasArt(Mesh));
			TestTrue(TEXT("enemy takes a picture"), EnemyPresenter->ShowArt(Enemy, Texture) == EArtSlotDraw::Drawn);
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
		// Hits are cached, misses are retried (an asset imported later is still found): a repeat load costs exactly
		// one try per path before the first that resolves.
		const TArray<FString> Paths = ArtSlot::TexturePaths(*Row);
		int32 HitIndex = INDEX_NONE;
		for (int32 Index = 0; Index < Paths.Num() && HitIndex == INDEX_NONE; ++Index)
		{
			HitIndex = LoadObject<UTexture2D>(nullptr, *Paths[Index], nullptr, LOAD_NoWarn | LOAD_Quiet) ? Index : INDEX_NONE;
		}
		// Filled: the slot's stand-in texture exists, loads once, and later loads return it without reloading it.
		UTexture2D* SlotArt = ArtSlot::LoadTexture(*Row);
		const int32 AfterTexture = ArtSlot::LoadCallCount();
		TestTrue(TEXT("the filled slot has its stand-in texture"), SlotArt != nullptr && HitIndex != INDEX_NONE);
		TestTrue(TEXT("a repeat load returns the same texture"), ArtSlot::LoadTexture(*Row) == SlotArt);
		TestEqual(TEXT("a texture that exists loads once"), ArtSlot::LoadCallCount() - AfterTexture, HitIndex);
		// Empty: a test-only row with no asset finds nothing and retries every path.
		const FArtSlotRow EmptyRow = { TEXT("test:empty"), TEXT("Test"), TEXT("T_ArtSlotTestNoSuchArt"), 1, false, TEXT("-") };
		const int32 BeforeEmpty = ArtSlot::LoadCallCount();
		TestNull(TEXT("an empty slot loads no texture"), ArtSlot::LoadTexture(EmptyRow));
		TestEqual(TEXT("an empty slot tries every path"), ArtSlot::LoadCallCount() - BeforeEmpty, ArtSlot::TexturePaths(EmptyRow).Num());
		TestEqual(TEXT("an empty slot draws nothing"), static_cast<int32>(ArtSlot::ApplyRow(MakeMesh(), EmptyRow, FVector::OneVector)), static_cast<int32>(EArtSlotDraw::NoTexture));
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
			UStaticMeshComponent* HitMesh = Cast<UStaticMeshComponent>(Hit->GetRootComponent());
			const FArtSlotRow* ImpactRow = ArtSlot::Find(TEXT("shot:red-impact"));
			// Filled: the impact slot's stand-in texture is drawn when the effect plays, and a picture is refused.
			UTexture2D* SlotArt = ImpactRow ? ArtSlot::LoadTexture(*ImpactRow) : nullptr;
			TestTrue(TEXT("bolt hit shows its slot stand-in texture"), SlotArt && HitMesh && ArtSlot::HasArt(HitMesh) && ArtSlotParamTexture(HitMesh) == SlotArt);
			TestTrue(TEXT("a filled bolt hit refuses a picture"), Vfx->ShowImpactArt(Hit, Texture) != EArtSlotDraw::Drawn);
			// Empty: with the slot's art cleared, the picture is drawn.
			ArtSlotTestClearArt(HitMesh, Hit);
			TestFalse(TEXT("cleared bolt hit has no art"), HitMesh && ArtSlot::HasArt(HitMesh));
			TestTrue(TEXT("bolt hit takes a picture"), Vfx->ShowImpactArt(Hit, Texture) == EArtSlotDraw::Drawn);
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
	// visualqa (Josh's 15:50 frame): wind drew as framed, stretched picture cards. Wind is thin ash-blue ribbons in code.
	UWorld* World = ArtSlotTestWorld();
	if (!TestNotNull(TEXT("world"), World))
	{
		return false;
	}
	TestEqual(TEXT("narrow current still has strands"), UWindPresenterSubsystem::StrandCount(10.0f), UmbrellaWindPresenterConst::MinStrands);
	TestEqual(TEXT("wide current is capped"), UWindPresenterSubsystem::StrandCount(5000.0f), UmbrellaWindPresenterConst::MaxStrands);
	TestTrue(TEXT("long strands get more segments"), UWindPresenterSubsystem::SegmentCount(900.0f) > UWindPresenterSubsystem::SegmentCount(300.0f));
	TestTrue(TEXT("strands are thin in the middle"), UWindPresenterSubsystem::StrandThickness(0, 0.5f) <= UmbrellaWindPresenterConst::ThickMiddle);
	TestTrue(TEXT("strands taper at the ends"), UWindPresenterSubsystem::StrandThickness(0, 0.0f) < UWindPresenterSubsystem::StrandThickness(0, 0.5f));
	const FVector2D Early = UWindPresenterSubsystem::StrandPoint(600.0f, 400.0f, 0, 3, 4, 12, 0.0f);
	const FVector2D Late = UWindPresenterSubsystem::StrandPoint(600.0f, 400.0f, 0, 3, 4, 12, 1.0f);
	TestTrue(TEXT("bends drift with game time"), !FMath::IsNearlyEqual(Early.Y, Late.Y, 0.5));
	TestTrue(TEXT("strand stays inside the current"), FMath::Abs(Early.Y) <= 200.0f && FMath::Abs(Early.X) <= 300.0f);

	UWindPresenterSubsystem* Presenter = World->GetSubsystem<UWindPresenterSubsystem>();
	AWindCurrent* Wind = World->SpawnActor<AWindCurrent>();
	if (TestNotNull(TEXT("wind presenter"), Presenter) && TestNotNull(TEXT("wind"), Wind))
	{
		Wind->SetHalfExtent(300.0f, 200.0f);
		Presenter->DrawRibbons(Wind, 0.0f);
		UStaticMeshComponent* Field = Wind->GetField();
		TestTrue(TEXT("the colour card is not rendered"), !Field->bRenderInMainPass && !Field->bRenderInDepthPass);
		TestTrue(TEXT("the card keeps its size for the field rules"), Wind->GetDrawnSize().X > 0.0);
		TestFalse(TEXT("no picture card on the field"), ArtSlot::IsDrawingArt(Field));
		const TArray<UStaticMeshComponent*> Ribbons = UWindPresenterSubsystem::RibbonsOf(Wind);
		TestEqual(TEXT("one segment per strand step"), Ribbons.Num(), UWindPresenterSubsystem::StrandCount(400.0f) * UWindPresenterSubsystem::SegmentCount(600.0f));
		const FLinearColor Ash = FLinearColor::FromSRGBColor(FColor(UmbrellaWindPresenterConst::RibbonR, UmbrellaWindPresenterConst::RibbonG, UmbrellaWindPresenterConst::RibbonB));
		bool bAllAsh = Ribbons.Num() > 0;
		bool bAllThin = Ribbons.Num() > 0;
		bool bNoCollision = true;
		for (const UStaticMeshComponent* Ribbon : Ribbons)
		{
			FLinearColor Tint = FLinearColor::Transparent;
			if (const UMaterialInstanceDynamic* Dynamic = Cast<UMaterialInstanceDynamic>(Ribbon->GetMaterial(0)))
			{
				Dynamic->GetVectorParameterValue(FMaterialParameterInfo(FName(TEXT("Tint"))), Tint);
			}
			bAllAsh &= Tint.Equals(Ash, 0.002f);
			bAllThin &= Ribbon->GetRelativeScale3D().Y * UmbrellaWindPresenterConst::PlaneEdge <= UmbrellaWindPresenterConst::ThickMiddle + KINDA_SMALL_NUMBER;
			bNoCollision &= Ribbon->GetCollisionEnabled() == ECollisionEnabled::NoCollision;
		}
		TestTrue(TEXT("every ribbon is ash blue #555e60"), bAllAsh);
		TestTrue(TEXT("every ribbon is thin (never a box)"), bAllThin);
		TestTrue(TEXT("ribbons have no collision"), bNoCollision);
		if (Ribbons.Num() > 0)
		{
			const FVector Before = Ribbons[0]->GetRelativeLocation();
			Presenter->DrawRibbons(Wind, 1.0f);
			TestTrue(TEXT("ribbons move with game time"), !Ribbons[0]->GetRelativeLocation().Equals(Before, 0.1));
			TestEqual(TEXT("moving does not add segments"), UWindPresenterSubsystem::RibbonsOf(Wind).Num(), Ribbons.Num());
			// 16:28 review: no LoadObject or component search per tick; both are cached after the first draw.
			const int32 Loads = Presenter->PlaneLoadCount();
			const int32 Searches = Presenter->RibbonSearchCount();
			Presenter->DrawRibbons(Wind, 2.0f);
			Presenter->DrawRibbons(Wind, 3.0f);
			TestEqual(TEXT("the plane mesh is not loaded again"), Presenter->PlaneLoadCount(), Loads);
			TestEqual(TEXT("the ribbons are not searched again"), Presenter->RibbonSearchCount(), Searches);
			TestTrue(TEXT("the plane was loaded at most once"), Loads <= 1);
		}
		// A resize redraws the ribbons to the new box.
		Wind->SetHalfExtent(500.0f, 200.0f);
		Presenter->DrawRibbons(Wind, 0.0f);
		TestEqual(TEXT("ribbons follow a resize"), UWindPresenterSubsystem::RibbonsOf(Wind).Num(), UWindPresenterSubsystem::StrandCount(400.0f) * UWindPresenterSubsystem::SegmentCount(1000.0f));
		TestTrue(TEXT("still not rendered after the refresh"), !Wind->GetField()->bRenderInMainPass);
	}
	// The framed wind-field picture failed stand-in admission: the game never loads its _PH.
	if (const FArtSlotRow* Row = ArtSlot::Find(UmbrellaWindPresenterConst::FieldVisual))
	{
		TestFalse(TEXT("wind field stand-in rejected"), Row->bStandInOk);
		TestEqual(TEXT("only the passed asset is tried"), ArtSlot::TexturePaths(*Row).Num(), 1);
	}
	if (const FArtSlotRow* Ella = ArtSlot::Find(TEXT("ella-state:Idle")))
	{
		TestEqual(TEXT("a keyed stand-in still loads its _PH"), ArtSlot::TexturePaths(*Ella).Num(), 2);
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
		TestEqual(TEXT("five scene slots have a consumer (bg:start-end not on the route, Josh 14 Nov)"), Visuals.Num(), 5);
		TestFalse(TEXT("no barn picture on the route"), Visuals.Contains(FName(TEXT("bg:start-end"))));
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
			const int32 Expected = 1;
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
			// A part asset that exists is drawn when the Keeper appears, unless it is an unpassed _PH stand-in and the body
			// already draws art (ShouldPartPictureYieldToBody); otherwise the transient picture is.
			const UTexture2D* Asset = ArtSlot::LoadTexture(*Row);
			const bool bAssetDraws = Asset != nullptr && !UKeeperPresenterSubsystem::ShouldPartPictureYieldToBody(Asset, Keeper);
			TestEqual(*FString::Printf(TEXT("%s drawn at spawn iff its asset exists and does not yield to the body"), *Id), UKeeperPresenterSubsystem::FindPart(Keeper, Id) != nullptr, bAssetDraws);
			if (!bAssetDraws)
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

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FArtSlotKeeperStandInHidden, "UmbrellaElla.Feedback.World.KeeperStandInHiddenUnderArt",
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::ClientContext | EAutomationTestFlags::EngineFilter)

bool FArtSlotKeeperStandInHidden::RunTest(const FString& Parameters)
{
	UWorld* World = ArtSlotTestWorld();
	if (!TestNotNull(TEXT("world"), World))
	{
		return false;
	}
	UKeeperPresenterSubsystem* Presenter = World->GetSubsystem<UKeeperPresenterSubsystem>();
	// The arena's graybox Keeper square shows while no Keeper art draws.
	AUmbrellaArena* Arena = World->SpawnActor<AUmbrellaArena>();
	if (Arena && !Arena->GetKeeperStandIn())
	{
		Arena->BuildPlaceholders();
	}
	if (TestNotNull(TEXT("arena"), Arena) && TestNotNull(TEXT("arena keeper square"), Arena->GetKeeperStandIn()) && Presenter)
	{
		Presenter->SyncArenaStandIn();
		TestTrue(TEXT("arena keeper square shows with no Keeper"), Arena->GetKeeperStandIn()->IsVisible());
	}
	AKeeperOfTime* Keeper = World->SpawnActor<AKeeperOfTime>();
	if (TestNotNull(TEXT("keeper presenter"), Presenter) && TestNotNull(TEXT("keeper"), Keeper) && Arena && Arena->GetKeeperStandIn())
	{
		const UUmbrellaTuning* Tuning = GetDefault<UUmbrellaTuning>();
		FKeeperFightModel Model;
		TArray<FKeeperCommand> Commands;
		Model.Init(Tuning->Keeper, Tuning->Encounter, FKeeperRuleSwitches());
		Model.BeginPhase(EKeeperPhase::Wings, Commands);
		const EKeeperPart BodyParts[] = {EKeeperPart::Wings, EKeeperPart::Clock, EKeeperPart::Front, EKeeperPart::Middle, EKeeperPart::Rear};
		if (!Keeper->HasActorBegunPlay())
		{
			Keeper->DispatchBeginPlay();
		}

		// The body sprite draws (at spawn when its asset exists, else a transient picture): wings, clock and the three
		// mechanism cubes hide and stay hidden across Refresh.
		Presenter->ShowStandIn(Keeper);
		const UStaticMeshComponent* Body = FindObjectFast<UStaticMeshComponent>(Keeper, FName(TEXT("KeeperStandIn")));
		if (TestNotNull(TEXT("body stand-in"), Body) && !ArtSlot::HasArt(Body))
		{
			TestTrue(TEXT("body takes a picture"), Presenter->ShowArt(Keeper, ArtSlotTestTexture()) == EArtSlotDraw::Drawn);
		}
		Keeper->Refresh(Model, 0.0f);
		for (const EKeeperPart Part : BodyParts)
		{
			TestTrue(*FString::Printf(TEXT("part %d marked as drawn by art"), static_cast<int32>(Part)), Keeper->IsPartArtDrawn(Part));
			const UStaticMeshComponent* Cube = Keeper->GetStandInVisual(Part);
			if (TestNotNull(TEXT("stand-in cube"), Cube))
			{
				TestFalse(*FString::Printf(TEXT("cube %d hidden under the body art"), static_cast<int32>(Part)), Cube->IsVisible());
			}
		}
		TestTrue(TEXT("presenter reports Keeper art"), UKeeperPresenterSubsystem::HasKeeperArt(Keeper));
		Presenter->SyncArenaStandIn();
		TestTrue(TEXT("presenter sees Keeper art"), Presenter->HasAnyKeeperArt());
		TestFalse(TEXT("arena keeper square hidden while Keeper art draws"), Arena->GetKeeperStandIn()->IsVisible());
		Presenter->Tick(0.0f);
		TestFalse(TEXT("arena keeper square stays hidden across Tick"), Arena->GetKeeperStandIn()->IsVisible());
		TestFalse(TEXT("the exposed-eye cue is not covered by the body art"), Keeper->IsPartArtDrawn(EKeeperPart::Eye));
		TestTrue(TEXT("hit regions stay"), Keeper->GetPartComponent(EKeeperPart::Wings) != nullptr);

		// No art over a part: its cube shows again on the next Refresh (a stand-in shows when no art does).
		for (const EKeeperPart Part : BodyParts)
		{
			Keeper->ClearPartArtDrawn(Part);
		}
		Keeper->Refresh(Model, 0.0f);
		for (const EKeeperPart Part : BodyParts)
		{
			TestTrue(*FString::Printf(TEXT("cube %d shows with no art"), static_cast<int32>(Part)), Keeper->GetStandInVisual(Part)->IsVisible());
		}

		// A part layer covers its own cube only (drawn now, or already at spawn when its asset exists).
		const FString FrontId = TEXT("keeper:mechanism-front");
		if (!UKeeperPresenterSubsystem::FindPart(Keeper, FrontId))
		{
			TestTrue(TEXT("front layer takes a picture"), Presenter->ShowPartArt(Keeper, FrontId, ArtSlotTestTexture()) == EArtSlotDraw::Drawn);
			Keeper->Refresh(Model, 0.0f);
			TestTrue(TEXT("front mechanism layer covers the front cube"), Keeper->IsPartArtDrawn(EKeeperPart::Front));
			TestFalse(TEXT("front cube hidden under its layer"), Keeper->GetStandInVisual(EKeeperPart::Front)->IsVisible());
			TestTrue(TEXT("rear cube still shows with no art over it"), Keeper->GetStandInVisual(EKeeperPart::Rear)->IsVisible());
		}

		// A part layer that is destroyed uncovers its cube: the presenter clears the cover on its next Tick.
		if (UStaticMeshComponent* FrontLayer = UKeeperPresenterSubsystem::FindPart(Keeper, FrontId))
		{
			UStaticMeshComponent* BodyMesh = FindObjectFast<UStaticMeshComponent>(Keeper, FName(TEXT("KeeperStandIn")));
			if (BodyMesh && ArtSlot::HasArt(BodyMesh))
			{
				ArtSlotTestClearArt(BodyMesh, Keeper);
			}
			Presenter->Tick(0.0f);
			Keeper->Refresh(Model, 0.0f);
			TestTrue(TEXT("front layer still covers the front cube"), Keeper->IsPartArtDrawn(EKeeperPart::Front));
			FrontLayer->DestroyComponent();
			Presenter->Tick(0.0f);
			Keeper->Refresh(Model, 0.0f);
			TestFalse(TEXT("destroyed front layer no longer covers the front cube"), Keeper->IsPartArtDrawn(EKeeperPart::Front));
			TestTrue(TEXT("front cube shows once its layer is destroyed"), Keeper->GetStandInVisual(EKeeperPart::Front)->IsVisible());
		}

		// The Keeper leaves: no Keeper art draws, so the arena square shows again (synced on destroy, no Tick needed).
		Keeper->Destroy();
		TestFalse(TEXT("presenter sees no Keeper art once it is gone"), Presenter->HasAnyKeeperArt());
		TestTrue(TEXT("arena keeper square shows again with no Keeper art"), Arena->GetKeeperStandIn()->IsVisible());
	}
	ArtSlotTestEnd(World);
	return true;
}


IMPLEMENT_SIMPLE_AUTOMATION_TEST(FArtSlotKeeperStateCues, "UmbrellaElla.Feedback.World.KeeperStateCuesUnderArt",
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::ClientContext | EAutomationTestFlags::EngineFilter)

bool FArtSlotKeeperStateCues::RunTest(const FString& Parameters)
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
		if (!Keeper->HasActorBegunPlay())
		{
			Keeper->DispatchBeginPlay();
		}
		Presenter->ShowStandIn(Keeper);
		const UStaticMeshComponent* Body = FindObjectFast<UStaticMeshComponent>(Keeper, FName(TEXT("KeeperStandIn")));
		if (TestNotNull(TEXT("body stand-in"), Body) && !ArtSlot::HasArt(Body))
		{
			TestTrue(TEXT("body takes a picture"), Presenter->ShowArt(Keeper, ArtSlotTestTexture()) == EArtSlotDraw::Drawn);
		}
		const UUmbrellaTuning* Tuning = GetDefault<UUmbrellaTuning>();
		FKeeperFightModel Model;
		TArray<FKeeperCommand> Commands;
		FKeeperTickInput Input;
		Input.PlayerPos = FVector2D(-500.0f, 0.0f);
		Input.PlayerRadius = 10.0f;
		Model.Init(Tuning->Keeper, Tuning->Encounter, FKeeperRuleSwitches());

		// Default states: wings alive, clock closed, mechanisms alive. The static art shows these, so the cubes hide.
		Model.BeginPhase(EKeeperPhase::Wings, Commands);
		Keeper->Refresh(Model, 0.0f);
		for (const EKeeperPart Part : {EKeeperPart::Wings, EKeeperPart::Clock, EKeeperPart::Front, EKeeperPart::Middle, EKeeperPart::Rear})
		{
			TestTrue(*FString::Printf(TEXT("part %d is under art"), static_cast<int32>(Part)), Keeper->IsPartArtDrawn(Part));
			TestFalse(*FString::Printf(TEXT("part %d cube hidden in its default state"), static_cast<int32>(Part)), Keeper->GetStandInVisual(Part)->IsVisible());
		}

		// Mechanisms phase: the wings are broken. One hit on the front mechanism opens the clock.
		Model.BeginPhase(EKeeperPhase::Mechanisms, Commands);
		for (float T = 0.0f; T < Tuning->Encounter.PhaseTransitionSeconds + 0.1f; T += 1.0f / 60.0f)
		{
			Model.Step(1.0f / 60.0f, Input, Commands);
		}
		Model.ApplyPlayerHit(EKeeperPart::Front, 1.0f, Commands);
		TestTrue(TEXT("model: wings broken"), Model.IsPartBroken(EKeeperPart::Wings));
		TestTrue(TEXT("model: clock open"), Model.IsClockOpen());
		Keeper->Refresh(Model, 0.0f);
		TestTrue(TEXT("wings still under the body art"), Keeper->IsPartArtDrawn(EKeeperPart::Wings));
		TestFalse(TEXT("broken wing draws no flat cube over the body art (no broken-state art exists)"), Keeper->GetStandInVisual(EKeeperPart::Wings)->IsVisible());
		TestTrue(TEXT("open clock shows its cue under the body art"), Keeper->GetStandInVisual(EKeeperPart::Clock)->IsVisible());
		TestFalse(TEXT("live rear mechanism stays hidden under the art"), Keeper->GetStandInVisual(EKeeperPart::Rear)->IsVisible());
		// The cue is the state colour, not the generic lilac stand-in.
		auto CueColour = [](const UStaticMeshComponent* Cube)
		{
			FLinearColor Colour = FLinearColor::Transparent;
			if (const UMaterialInstanceDynamic* Dynamic = Cube ? Cast<UMaterialInstanceDynamic>(Cube->GetMaterial(0)) : nullptr)
			{
				Dynamic->GetVectorParameterValue(FHashedMaterialParameterInfo(TEXT("Tint")), Colour);
			}
			return Colour;
		};
		TestTrue(TEXT("open clock cue is the open colour"), CueColour(Keeper->GetStandInVisual(EKeeperPart::Clock)).Equals(KeeperLook::ClockOpen));

		// A broken mechanism shows its cue too.
		Model.ApplyPlayerHit(EKeeperPart::Front, Tuning->Keeper.FrontHp * 10.0f, Commands);
		TestTrue(TEXT("model: front broken"), Model.IsPartBroken(EKeeperPart::Front));
		Keeper->Refresh(Model, 0.0f);
		TestFalse(TEXT("broken front mechanism draws no flat cube over the art"), Keeper->GetStandInVisual(EKeeperPart::Front)->IsVisible());
		Keeper->Destroy();
	}
	ArtSlotTestEnd(World);
	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FArtSlotKeeperPaperAlpha, "UmbrellaElla.Feedback.KeeperPaperStandInsHaveAlpha",
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FArtSlotKeeperPaperAlpha::RunTest(const FString& Parameters)
{
#if WITH_EDITORONLY_DATA
	// The talon, wing and front-mechanism stand-ins were ink on cream paper with no alpha, so each drew a paper box over
	// the whole Keeper. Their keyed sources must be transparent at every corner, mostly clear, and keep the drawing.
	static const TCHAR* const KeeperPaperPaths[] = {
		TEXT("/Game/UmbrellaElla/Art/Keeper/T_Keeper_Talon_PH.T_Keeper_Talon_PH"),
		TEXT("/Game/UmbrellaElla/Art/Keeper/T_Keeper_Wing_PH.T_Keeper_Wing_PH"),
		TEXT("/Game/UmbrellaElla/Art/Keeper/T_Keeper_MechFront_PH.T_Keeper_MechFront_PH"),
	};
	for (const TCHAR* Path : KeeperPaperPaths)
	{
		UTexture2D* Picture = LoadObject<UTexture2D>(nullptr, Path);
		if (!TestNotNull(*FString::Printf(TEXT("%s loads"), Path), Picture))
		{
			continue;
		}
		TestFalse(*FString::Printf(TEXT("%s keeps its alpha channel"), Path), Picture->CompressionNoAlpha);
		const ETextureSourceFormat Format = Picture->Source.GetFormat();
		const bool bEight = Format == TSF_BGRA8;
		TArray64<uint8> Mip;
		if (!TestTrue(*FString::Printf(TEXT("%s source is 8 or 16 bit RGBA"), Path), bEight || Format == TSF_RGBA16)
			|| !TestTrue(*FString::Printf(TEXT("%s source mip reads"), Path), Picture->Source.GetMipData(Mip, 0)))
		{
			continue;
		}
		const int64 W = Picture->Source.GetSizeX();
		const int64 H = Picture->Source.GetSizeY();
		const int64 Bpp = Picture->Source.GetBytesPerPixel();
		if (!TestEqual(*FString::Printf(TEXT("%s mip size"), Path), Mip.Num(), W * H * Bpp))
		{
			continue;
		}
		const auto KeeperPaperAlpha = [&](int64 X, int64 Y) -> float
		{
			const uint8* Pixel = Mip.GetData() + (Y * W + X) * Bpp;
			return bEight ? Pixel[3] / 255.0f : *reinterpret_cast<const uint16*>(Pixel + 6) / 65535.0f;
		};
		const int64 Corners[4][2] = {{0, 0}, {W - 1, 0}, {0, H - 1}, {W - 1, H - 1}};
		for (const auto& Corner : Corners)
		{
			TestTrue(*FString::Printf(TEXT("%s corner (%lld,%lld) is transparent"), Path, Corner[0], Corner[1]), KeeperPaperAlpha(Corner[0], Corner[1]) < 0.05f);
		}
		int64 Opaque = 0;
		int64 Clear = 0;
		int64 Samples = 0;
		for (int64 Y = 0; Y < H; Y += 4)
		{
			for (int64 X = 0; X < W; X += 4)
			{
				const float A = KeeperPaperAlpha(X, Y);
				Opaque += A > 0.5f ? 1 : 0;
				Clear += A < 0.05f ? 1 : 0;
				++Samples;
			}
		}
		const double OpaqueShare = static_cast<double>(Opaque) / Samples;
		const double ClearShare = static_cast<double>(Clear) / Samples;
		AddInfo(FString::Printf(TEXT("%s %lldx%lld opaque %.3f clear %.3f"), Path, W, H, OpaqueShare, ClearShare));
		TestTrue(*FString::Printf(TEXT("%s paper is keyed: over half is clear"), Path), ClearShare > 0.5);
		TestTrue(*FString::Printf(TEXT("%s drawing stays: over a tenth is opaque"), Path), OpaqueShare > 0.1);
	}
#endif
	return true;
}

#endif

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FArtSlotKeeperPartStandInsYield, "UmbrellaElla.Feedback.World.KeeperPartStandInsYieldToBody",
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::ClientContext | EAutomationTestFlags::EngineFilter)

bool FArtSlotKeeperPartStandInsYield::RunTest(const FString& Parameters)
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
		UStaticMeshComponent* Body = FindObjectFast<UStaticMeshComponent>(Keeper, FName(TEXT("KeeperStandIn")));
		if (TestNotNull(TEXT("body stand-in"), Body))
		{
			// Start from a body with no art, so the part stand-in may draw.
			ArtSlotTestClearArt(Body, Keeper);
			if (UStaticMeshComponent* Existing = UKeeperPresenterSubsystem::FindPart(Keeper, TEXT("keeper:wings-gust-wear")))
			{
				Existing->DestroyComponent();
			}
			UTexture2D* WingPh = NewObject<UTexture2D>(GetTransientPackage(), TEXT("T_Test_Wing_PH"));
			UTexture2D* WingPassed = NewObject<UTexture2D>(GetTransientPackage(), TEXT("T_Test_Wing"));
			WingPh->AddToRoot();
			WingPassed->AddToRoot();
			TestFalse(TEXT("no body art: a _PH part does not yield"), UKeeperPresenterSubsystem::ShouldPartPictureYieldToBody(WingPh, Keeper));
			TestTrue(TEXT("body draws art"), Presenter->ShowArt(Keeper, ArtSlotTestTexture()) == EArtSlotDraw::Drawn);
			TestTrue(TEXT("body art: a _PH part yields"), UKeeperPresenterSubsystem::ShouldPartPictureYieldToBody(WingPh, Keeper));
			TestFalse(TEXT("body art: a passed part still draws"), UKeeperPresenterSubsystem::ShouldPartPictureYieldToBody(WingPassed, Keeper));
			TestTrue(TEXT("a _PH wing layer is refused over the body art"),
				Presenter->ShowPartArt(Keeper, TEXT("keeper:wings-gust-wear"), WingPh) == EArtSlotDraw::NoTexture);
			TestNull(TEXT("no wing layer drawn"), UKeeperPresenterSubsystem::FindPart(Keeper, TEXT("keeper:wings-gust-wear")));
			WingPh->RemoveFromRoot();
			WingPassed->RemoveFromRoot();
		}
		Keeper->Destroy();
	}
	ArtSlotTestEnd(World);
	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FArtSlotKeeperBodyAspect, "UmbrellaElla.Feedback.World.KeeperBodyKeepsCellAspect",
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::ClientContext | EAutomationTestFlags::EngineFilter)

bool FArtSlotKeeperBodyAspect::RunTest(const FString& Parameters)
{
	const FArtSlotRow* Row = ArtSlot::Find(TEXT("keeper:body-hover-flap"));
	if (!TestNotNull(TEXT("body row"), Row))
	{
		return false;
	}
	// A sheet whose cells are twice as wide as tall: the body keeps its width and halves its height.
	UTexture2D* Wide = ArtSlotSizedTestTexture(2 * 100 * FMath::Max(1, Row->Cols), 100 * FMath::Max(1, Row->Rows));
	const FVector Scale = UKeeperPresenterSubsystem::BodyArtScaleFor(Wide, *Row);
	TestEqual(TEXT("body width kept"), Scale.X, UmbrellaKeeperPresenterConst::StandInScale.X);
	TestEqual(TEXT("height from the cell aspect"), Scale.Z, UmbrellaKeeperPresenterConst::StandInScale.X / 2.0, 1.0e-4);

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
		UStaticMeshComponent* Body = FindObjectFast<UStaticMeshComponent>(Keeper, FName(TEXT("KeeperStandIn")));
		if (TestNotNull(TEXT("body stand-in"), Body))
		{
			ArtSlotTestClearArt(Body, Keeper);
			TestTrue(TEXT("body draws the wide sheet"), Presenter->ShowArt(Keeper, Wide) == EArtSlotDraw::Drawn);
			const FVector Plane = Body->GetRelativeScale3D();
			TestEqual(TEXT("drawn picture is twice as wide as tall"), Plane.X / FMath::Max(1.0e-6, Plane.Y), 2.0, 1.0e-3);
		}
		Keeper->Destroy();
	}
	ArtSlotTestEnd(World);
	return true;
}
