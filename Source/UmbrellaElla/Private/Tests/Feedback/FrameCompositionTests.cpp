#include "Components/StaticMeshComponent.h"
#include "Engine/Engine.h"
#include "Engine/StaticMesh.h"
#include "Engine/Texture2D.h"
#include "Engine/World.h"
#include "Feedback/Art/ArtSlot.h"
#include "Feedback/Art/FrameCompositionSubsystem.h"
#include "Feedback/Vfx/VfxCatalog.h"
#include "Feedback/Vfx/VfxSheetVisual.h"
#include "GameFramework/Actor.h"
#include "Misc/AutomationTest.h"

#if WITH_AUTOMATION_TESTS

namespace
{
	UStaticMeshComponent* FrameTestMesh(AActor* Owner, const TCHAR* Name, const FVector& Location, const FLinearColor& StandIn)
	{
		UStaticMeshComponent* Mesh = NewObject<UStaticMeshComponent>(Owner, Name);
		Owner->SetRootComponent(Owner->GetRootComponent() ? Owner->GetRootComponent() : Mesh);
		if (Owner->GetRootComponent() != Mesh)
		{
			Mesh->SetupAttachment(Owner->GetRootComponent());
		}
		Mesh->SetStaticMesh(LoadObject<UStaticMesh>(nullptr, TEXT("/Engine/BasicShapes/Cube.Cube")));
		Mesh->RegisterComponent();
		Mesh->SetWorldLocation(Location);
		ArtSlot::SetFlatUnlit(Mesh, Owner, StandIn);
		return Mesh;
	}
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FFrameCompositionRules, "UmbrellaElla.Feedback.FrameComposition.Rules",
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::ClientContext | EAutomationTestFlags::EngineFilter)

bool FFrameCompositionRules::RunTest(const FString& Parameters)
{
	// Josh's 15:50 frame: a lilac route cube, cream bars, a bright paper backdrop. Pure rule table.
	const FLinearColor White = FLinearColor::White;
	TestTrue(TEXT("lilac Keeper stand-in cube is hidden"),
		UFrameCompositionSubsystem::TreatmentFor(FName(UmbrellaFrameConst::KeeperStandInName), -50.0f, false, true, UmbrellaArtSlotConst::StandInKeeperColor) == EFrameTreatment::Hide);
	TestTrue(TEXT("cream stand-in block turns island umber"),
		UFrameCompositionSubsystem::TreatmentFor(FName(TEXT("Block")), 0.0f, false, true, UmbrellaArtSlotConst::StandInDefaultColor) == EFrameTreatment::TintIsland);
	TestTrue(TEXT("backdrop art is dimmed"),
		UFrameCompositionSubsystem::TreatmentFor(FName(TEXT("Panel")), -400.0f, true, true, White) == EFrameTreatment::DimBackdropArt);
	TestTrue(TEXT("dimmed backdrop art is left alone"),
		UFrameCompositionSubsystem::TreatmentFor(FName(TEXT("Panel")), -400.0f, true, true, UmbrellaFrameConst::BackdropDim) == EFrameTreatment::Keep);
	TestTrue(TEXT("bright backdrop stand-in panel is darkened"),
		UFrameCompositionSubsystem::TreatmentFor(FName(TEXT("Panel")), -300.0f, false, true, UmbrellaArtSlotConst::StandInDefaultColor) == EFrameTreatment::DarkenBackdropPanel);
	TestTrue(TEXT("play-layer art (Ella, shots) is never touched"),
		UFrameCompositionSubsystem::TreatmentFor(FName(TEXT("Sprite")), 0.0f, true, true, White) == EFrameTreatment::Keep);
	TestTrue(TEXT("salmon enemy stand-in turns red shadow"),
		UFrameCompositionSubsystem::TreatmentFor(FName(TEXT("Placeholder")), 0.0f, false, true, UmbrellaArtSlotConst::StandInEnemyColor) == EFrameTreatment::TintEnemy);
	TestTrue(TEXT("yellow Ella stand-in is kept"),
		UFrameCompositionSubsystem::TreatmentFor(FName(TEXT("EllaStandIn")), 0.0f, false, true, UmbrellaArtSlotConst::StandInEllaColor) == EFrameTreatment::Keep);
	TestTrue(TEXT("a mesh without the slot material is kept"),
		UFrameCompositionSubsystem::TreatmentFor(FName(UmbrellaFrameConst::KeeperStandInName), 0.0f, false, false, White) == EFrameTreatment::Keep);
	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FFrameCompositionWorld, "UmbrellaElla.Feedback.FrameComposition.World",
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::ClientContext | EAutomationTestFlags::EngineFilter)

bool FFrameCompositionWorld::RunTest(const FString& Parameters)
{
	UWorld* World = UWorld::CreateWorld(EWorldType::Game, false);
	if (!TestNotNull(TEXT("world"), World))
	{
		return false;
	}
	GEngine->CreateNewWorldContext(EWorldType::Game).SetCurrentWorld(World);
	UFrameCompositionSubsystem* Frame = World->GetSubsystem<UFrameCompositionSubsystem>();
	AActor* Route = World->SpawnActor<AActor>();
	AActor* Arena = World->SpawnActor<AActor>();
	AActor* Backdrop = World->SpawnActor<AActor>();
	if (TestNotNull(TEXT("frame subsystem"), Frame) && Route && Arena && Backdrop)
	{
		UStaticMeshComponent* Block = FrameTestMesh(Route, TEXT("Block"), FVector(0.0, 0.0, 0.0), UmbrellaArtSlotConst::StandInDefaultColor);
		UStaticMeshComponent* Keeper = FrameTestMesh(Arena, UmbrellaFrameConst::KeeperStandInName, FVector(500.0, -50.0, 300.0), UmbrellaArtSlotConst::StandInKeeperColor);
		UStaticMeshComponent* Panel = FrameTestMesh(Backdrop, TEXT("Panel"), FVector(0.0, -400.0, 0.0), FLinearColor::White);
		UTexture2D* Picture = UTexture2D::CreateTransient(4, 4);
		Picture->AddToRoot();
		const FArtSlotRow* Row = ArtSlot::Find(TEXT("bg-layer:Base"));
		const bool bPanelArt = Row && ArtSlot::Apply(Panel, Picture, *Row, FVector(10.0, 0.01, 5.0)) == EArtSlotDraw::Drawn;
		if (ArtSlot::IsUnlit(Block))
		{
			TestTrue(TEXT("the pass changed meshes"), Frame->ComposeNow() >= 2);
			TestTrue(TEXT("cream block is island umber now"), ArtSlot::GetTint(Block).Equals(UmbrellaFrameConst::IslandUmber, 0.0005f));
			TestTrue(TEXT("lilac Keeper cube is hidden in game"), Keeper->bHiddenInGame);
			if (bPanelArt)
			{
				TestTrue(TEXT("backdrop picture is dimmed toward the study's dark"), ArtSlot::GetTint(Panel).Equals(UmbrellaFrameConst::BackdropDim, 0.0005f));
			}
			TestEqual(TEXT("a second pass changes nothing"), Frame->ComposeNow(), 0);
			// A refresh that puts the cream stand-in back is caught by the next pass.
			ArtSlot::SetFlatUnlit(Block, Route, UmbrellaArtSlotConst::StandInDefaultColor);
			Frame->ComposeNow();
			TestTrue(TEXT("re-tinted after a stand-in refresh"), ArtSlot::GetTint(Block).Equals(UmbrellaFrameConst::IslandUmber, 0.0005f));
		}
		else
		{
			AddWarning(TEXT("slot material missing in this build: world pass not measured"));
		}
		Picture->RemoveFromRoot();
	}
	GEngine->DestroyWorldContext(World);
	World->DestroyWorld(false);
	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FFrameCompositionRefusedVfx, "UmbrellaElla.Feedback.FrameComposition.RefusedVfxSheet",
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::ClientContext | EAutomationTestFlags::EngineFilter)

bool FFrameCompositionRefusedVfx::RunTest(const FString& Parameters)
{
	// The Umbra stand-in sheet is cut at its cell edges (art_slots.py: framed); it drew as a stretched dark column under Ella.
	const FVfxArtRow* Umbra = VfxCatalog::Find(FName(TEXT("Umbra")));
	const FVfxArtRow* Gold = VfxCatalog::Find(FName(TEXT("SmallBlastTravel")));
	if (!TestNotNull(TEXT("umbra row"), Umbra) || !TestNotNull(TEXT("gold row"), Gold))
	{
		return false;
	}
	TestFalse(TEXT("umbra stand-in refused"), VfxCatalog::IsStandInAdmitted(*Umbra));
	TestEqual(TEXT("only the passed umbra sheet is tried"), VfxCatalog::TexturePaths(*Umbra).Num(), 1);
	TestTrue(TEXT("a keyed sheet is admitted"), VfxCatalog::IsStandInAdmitted(*Gold));
	TestEqual(TEXT("a keyed sheet still falls back to its _PH"), VfxCatalog::TexturePaths(*Gold).Num(), 2);
	UWorld* World = UWorld::CreateWorld(EWorldType::Game, false);
	if (!TestNotNull(TEXT("world"), World))
	{
		return false;
	}
	GEngine->CreateNewWorldContext(EWorldType::Game).SetCurrentWorld(World);
	AActor* Owner = World->SpawnActor<AActor>();
	UStaticMeshComponent* Mesh = Owner ? VfxSheetVisual::Build(Owner, *Umbra, FVector2D(150.0, 420.0)) : nullptr;
	if (TestNotNull(TEXT("umbra visual"), Mesh))
	{
		const bool bHasSheet = Mesh->GetStaticMesh() && Mesh->GetStaticMesh()->GetName() == TEXT("Plane");
		TestTrue(TEXT("a refused sheet with no passed art draws nothing"), bHasSheet || (!Mesh->bRenderInMainPass && !Mesh->bRenderInDepthPass));
	}
	GEngine->DestroyWorldContext(World);
	World->DestroyWorld(false);
	return true;
}

#endif
