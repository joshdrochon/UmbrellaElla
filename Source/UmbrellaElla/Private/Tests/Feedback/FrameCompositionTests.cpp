#include "Arena/UmbrellaArena.h"
#include "Camera/CameraComponent.h"
#include "Components/CapsuleComponent.h"
#include "Components/StaticMeshComponent.h"
#include "Core/UmbrellaTuning.h"
#include "Engine/Engine.h"
#include "Engine/StaticMesh.h"
#include "Engine/Texture2D.h"
#include "Engine/World.h"
#include "Feedback/Art/ArtSlot.h"
#include "Feedback/Art/FrameCompositionSubsystem.h"
#include "Feedback/Background/SceneArtSubsystem.h"
#include "Feedback/Background/UmbrellaBackdropSubsystem.h"
#include "Feedback/Vfx/VfxCatalog.h"
#include "Feedback/Vfx/VfxSheetVisual.h"
#include "GameFramework/Actor.h"
#include "Core/EllaCharacter.h"
#include "Level/LevelCatalogue.h"
#include "Level/LevelPlan.h"
#include "Misc/AutomationTest.h"
#include "Tests/Shared/UmbrellaTestWorld.h"

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

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FFrameCompositionCameraMargin, "UmbrellaElla.Feedback.FrameComposition.CameraMargin",
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::ClientContext | EAutomationTestFlags::EngineFilter)

bool FFrameCompositionCameraMargin::RunTest(const FString& Parameters)
{
	// move's B7 captures: Ella at the ceiling (z 1036) had the top of her picture cut off by the frame edge (z 1080).
	FUmbrellaTestWorld Test;
	UFrameCompositionSubsystem* Frame = Test.GetWorld()->GetSubsystem<UFrameCompositionSubsystem>();
	AUmbrellaArena* Arena = Test.GetWorld()->SpawnActor<AUmbrellaArena>(FVector::ZeroVector, FRotator::ZeroRotator);
	AEllaCharacter* Ella = Arena ? Test.SpawnElla(Arena->GetPlayerStartLocation()) : nullptr;
	if (!TestNotNull(TEXT("frame"), Frame) || !TestNotNull(TEXT("arena"), Arena) || !TestNotNull(TEXT("ella"), Ella) || !Arena->GetPlayCamera())
	{
		return false;
	}
	UCameraComponent* Camera = Arena->GetPlayCamera();
	const float Aspect = Camera->AspectRatio;
	const FVector StartScale = Ella->GetActorScale3D();
	const float CapsuleBase = Ella->GetCapsuleComponent()->GetUnscaledCapsuleHalfHeight();
	auto SpriteTopAtCeiling = [&]()
	{
		const float Ceiling = static_cast<float>(Arena->LocalPoint(0.0f, 1.0f).Z) - Ella->GetCapsuleComponent()->GetScaledCapsuleHalfHeight();
		return Ceiling + UFrameCompositionSubsystem::SpriteHalfHeight(static_cast<float>(Ella->GetActorScale3D().Z));
	};
	auto FrameTop = [&]()
	{
		return UFrameCompositionSubsystem::FrameTopZ(static_cast<float>(Camera->GetComponentLocation().Z), Camera->OrthoWidth, Aspect);
	};
	// The spawned hero size, then the largest hero with the smallest hitbox (HeroSize 1.3, hitbox 0.75).
	struct FMarginCase { const TCHAR* Name; float ScaleMul; float CapsuleMul; };
	const FMarginCase Cases[] = { { TEXT("spawned hero size"), 1.0f, 1.0f }, { TEXT("hero size 1.3, hitbox 0.75"), 1.3f, 0.75f } };
	for (const FMarginCase& Case : Cases)
	{
		Ella->SetActorScale3D(StartScale * Case.ScaleMul);
		Ella->GetCapsuleComponent()->SetCapsuleHalfHeight(CapsuleBase * Case.CapsuleMul);
		Arena->MovePlayArea(FVector::ZeroVector);
		Frame->ApplyCameraMargin(Arena, Ella);
		TestTrue(FString::Printf(TEXT("Start Game, %s: picture top %.1f inside frame top %.1f"), Case.Name, SpriteTopAtCeiling(), FrameTop()), SpriteTopAtCeiling() <= FrameTop());
		// Director's Cut: the arena moves to the route end for the Keeper fight (B5).
		Arena->MovePlayArea(LevelPlan::KeeperArenaOrigin());
		Frame->ApplyCameraMargin(Arena, Ella);
		TestTrue(FString::Printf(TEXT("Director's Cut, %s: picture top %.1f inside frame top %.1f"), Case.Name, SpriteTopAtCeiling(), FrameTop()), SpriteTopAtCeiling() <= FrameTop());
	}
	// Break check: the arena's own camera (ortho width = arena width) cuts the picture off; the margin is what fixes it.
	Ella->SetActorScale3D(StartScale);
	Ella->GetCapsuleComponent()->SetCapsuleHalfHeight(CapsuleBase);
	Camera->SetOrthoWidth(GetDefault<UUmbrellaTuning>()->ArenaCamera.ArenaWidth);
	TestTrue(TEXT("without the margin the picture is cut (break check)"), SpriteTopAtCeiling() > FrameTop());
	Frame->ApplyCameraMargin(Arena, Ella);
	TestTrue(TEXT("the margin widens the arena camera"), Camera->OrthoWidth > GetDefault<UUmbrellaTuning>()->ArenaCamera.ArenaWidth);
	// Another system's zoom (VFX demo capture) is left alone.
	const float FrameTestForeignZoom = 600.0f;
	Camera->SetOrthoWidth(FrameTestForeignZoom);
	Frame->ApplyCameraMargin(Arena, Ella);
	TestEqual(TEXT("foreign zoom kept"), Camera->OrthoWidth, FrameTestForeignZoom);
	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FFrameCompositionKeeperBackdrop, "UmbrellaElla.Feedback.FrameComposition.KeeperBackdropContinuous",
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::ClientContext | EAutomationTestFlags::EngineFilter)

bool FFrameCompositionKeeperBackdrop::RunTest(const FString& Parameters)
{
	// levelchunks 16:14: at the Director's Cut Keeper handoff the route-end picture stopped at the route end, so the left
	// ~40% of the fight screen showed it and the rest a different backdrop. The picture must cover the whole fight frame.
	FSceneArtSpec RouteEnd;
	for (const FSceneArtSpec& Spec : USceneArtSubsystem::Specs())
	{
		if (Spec.Anchor == ESceneArtAnchor::RouteEnd)
		{
			RouteEnd = Spec;
		}
	}
	if (!TestTrue(TEXT("route end spec"), RouteEnd.Anchor == ESceneArtAnchor::RouteEnd))
	{
		return false;
	}
	FUmbrellaTestWorld Test;
	UFrameCompositionSubsystem* Frame = Test.GetWorld()->GetSubsystem<UFrameCompositionSubsystem>();
	AUmbrellaArena* Arena = Test.GetWorld()->SpawnActor<AUmbrellaArena>(FVector::ZeroVector, FRotator::ZeroRotator);
	AEllaCharacter* Ella = Arena ? Test.SpawnElla(Arena->GetPlayerStartLocation()) : nullptr;
	if (!TestNotNull(TEXT("frame"), Frame) || !TestNotNull(TEXT("arena"), Arena) || !TestNotNull(TEXT("ella"), Ella) || !Arena->GetPlayCamera())
	{
		return false;
	}
	UCameraComponent* Camera = Arena->GetPlayCamera();
	const FArenaCameraTuning& T = GetDefault<UUmbrellaTuning>()->ArenaCamera;
	// Widest view: the largest hero with the smallest hitbox gets the biggest camera margin.
	Ella->SetActorScale3D(Ella->GetActorScale3D() * 1.3f);
	Ella->GetCapsuleComponent()->SetCapsuleHalfHeight(Ella->GetCapsuleComponent()->GetUnscaledCapsuleHalfHeight() * 0.75f);
	Arena->MovePlayArea(LevelPlan::KeeperArenaOrigin());
	Frame->ApplyCameraMargin(Arena, Ella);
	const FVector View = Camera->GetComponentLocation();
	const float HalfViewW = Camera->OrthoWidth * 0.5f;
	const float HalfViewH = Camera->OrthoWidth / T.CameraAspectRatio * 0.5f;
	const FVector2D Size = USceneArtSubsystem::PanelSize(RouteEnd);
	const float PanelX = USceneArtSubsystem::PanelX(RouteEnd, static_cast<float>(View.X));
	const float PanelZ = T.ArenaHeight * 0.5f;
	TestTrue(TEXT("route end picture reaches the fight frame's left edge"), PanelX - Size.X * 0.5f <= View.X - HalfViewW);
	TestTrue(TEXT("route end picture reaches the fight frame's right edge"), PanelX + Size.X * 0.5f >= View.X + HalfViewW);
	TestTrue(TEXT("route end picture reaches the fight frame's top"), PanelZ + Size.Y * 0.5f >= View.Z + HalfViewH);
	TestTrue(TEXT("route end picture reaches the fight frame's bottom"), PanelZ - Size.Y * 0.5f <= View.Z - HalfViewH);
	// Break check: the old placement (last arena width of the route) leaves the right of the fight frame uncovered.
	const float OldRight = LevelCatalogue::RouteLength();
	TestTrue(TEXT("old placement stopped inside the fight frame (break check)"), OldRight < View.X + HalfViewW);
	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FFrameCompositionGameplayFrameFillsView, "UmbrellaElla.Feedback.FrameComposition.GameplayFrameFillsView",
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::ClientContext | EAutomationTestFlags::EngineFilter)

bool FFrameCompositionGameplayFrameFillsView::RunTest(const FString& Parameters)
{
	// visualqa r03: with the camera margin the view-sized scene:gameplay-frame stayed arena-sized and sat 1-2% inside
	// the screen edge. It must size to the camera's ortho width and reach every edge.
	FUmbrellaTestWorld Test;
	UWorld* World = Test.GetWorld();
	UFrameCompositionSubsystem* Frame = World->GetSubsystem<UFrameCompositionSubsystem>();
	USceneArtSubsystem* Scene = World->GetSubsystem<USceneArtSubsystem>();
	AUmbrellaArena* Arena = World->SpawnActor<AUmbrellaArena>(FVector::ZeroVector, FRotator::ZeroRotator);
	AEllaCharacter* Ella = Arena ? Test.SpawnElla(Arena->GetPlayerStartLocation()) : nullptr;
	if (!TestNotNull(TEXT("frame"), Frame) || !TestNotNull(TEXT("scene"), Scene) || !TestNotNull(TEXT("arena"), Arena)
		|| !TestNotNull(TEXT("ella"), Ella) || !Arena->GetPlayCamera())
	{
		return false;
	}
	if (!Scene->FindPanel(TEXT("scene:gameplay-frame")))
	{
		UTexture2D* Stand = UTexture2D::CreateTransient(8, 8, PF_B8G8R8A8);
		Scene->ShowArt(TEXT("scene:gameplay-frame"), Stand);
	}
	const UStaticMeshComponent* Panel = Scene->FindPanel(TEXT("scene:gameplay-frame"));
	if (!TestNotNull(TEXT("gameplay frame panel"), Panel))
	{
		return false;
	}
	UCameraComponent* Camera = Arena->GetPlayCamera();
	const FArenaCameraTuning& T = GetDefault<UUmbrellaTuning>()->ArenaCamera;
	Ella->SetActorScale3D(Ella->GetActorScale3D() * 1.3f);
	Ella->GetCapsuleComponent()->SetCapsuleHalfHeight(Ella->GetCapsuleComponent()->GetUnscaledCapsuleHalfHeight() * 0.75f);
	Frame->ApplyCameraMargin(Arena, Ella);
	TestTrue(TEXT("camera margin widened the view"), Camera->OrthoWidth > T.ArenaWidth);
	const float CameraX = static_cast<float>(Camera->GetComponentLocation().X);
	const float HalfViewW = Camera->OrthoWidth * 0.5f;
	const float HalfViewH = Camera->OrthoWidth / T.CameraAspectRatio * 0.5f;
	auto FrameCovers = [&](float OrthoWidth)
	{
		Scene->ScrollTo(CameraX, OrthoWidth);
		const FVector Scale = Panel->GetOwner()->GetActorScale3D();
		const float HalfW = static_cast<float>(Scale.X) * UmbrellaBackdropConst::EngineCubeSize * 0.5f;
		const float HalfH = static_cast<float>(Scale.Z) * UmbrellaBackdropConst::EngineCubeSize * 0.5f;
		return HalfW >= HalfViewW - 0.5f && HalfH >= HalfViewH - 0.5f;
	};
	TestTrue(TEXT("gameplay frame reaches every screen edge with the margin"), FrameCovers(Camera->OrthoWidth));
	TestEqual(TEXT("frame keeps its depth thickness"), static_cast<float>(Panel->GetOwner()->GetActorScale3D().Y), UmbrellaBackdropConst::PanelThickness);
	TestEqual(TEXT("frame follows the camera"), static_cast<float>(Panel->GetOwner()->GetActorLocation().X), CameraX);
	// Break check: arena-sized (the old behaviour) sits inside the widened view.
	TestFalse(TEXT("arena-sized frame sits inside the widened view (break check)"), FrameCovers(0.0f));
	TestEqual(TEXT("not orthographic: scale 1"), USceneArtSubsystem::ViewScale(0.0f), 1.0f);
	return true;
}

#endif
