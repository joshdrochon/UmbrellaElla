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
#include "Owl/KeeperOfTime.h"
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
	// Josh's 15:50 frame: a lilac route cube, cream bars, a bright paper backdrop. Lead 17:08: the Keeper is always seen
	// and Ella is never a bright block. Pure rule table.
	const FLinearColor White = FLinearColor::White;
	auto Facts = [](const TCHAR* Name, float Y, bool bArt, bool bSlot, const FLinearColor& Tint, bool bArena = false, bool /*bKeeperActor*/ = false)
	{
		FFrameMeshFacts F;
		F.ComponentName = FName(Name);
		F.WorldY = Y;
		F.bDrawsArt = bArt;
		F.bSlotMaterial = bSlot;
		F.Tint = Tint;
		F.bArenaOwned = bArena;
		return UFrameCompositionSubsystem::TreatmentFor(F);
	};
	const FLinearColor Lilac = UmbrellaArtSlotConst::StandInKeeperColor;
	TestTrue(TEXT("the arena's lilac Keeper square is hidden while a Keeper actor draws the Keeper"),
		Facts(UmbrellaFrameConst::KeeperStandInName, -50.0f, false, true, Lilac, true, true) == EFrameTreatment::Hide);
	TestTrue(TEXT("the Keeper actor's artless body is never hidden: gunmetal"),
		Facts(UmbrellaFrameConst::KeeperStandInName, -50.0f, false, true, Lilac, false, true) == EFrameTreatment::TintKeeper);
	TestTrue(TEXT("with no Keeper actor (Director's Cut route) the arena square is still hidden: no grey box"),
		Facts(UmbrellaFrameConst::KeeperStandInName, -50.0f, false, true, Lilac, true, false) == EFrameTreatment::Hide);
	TestTrue(TEXT("a lilac Keeper part cube turns gunmetal"),
		Facts(TEXT("WingsVisual"), -50.0f, false, true, Lilac, false, true) == EFrameTreatment::TintKeeper);
	TestTrue(TEXT("Keeper art is never touched"),
		Facts(UmbrellaFrameConst::KeeperStandInName, -50.0f, true, true, White, false, true) == EFrameTreatment::Keep);
	TestTrue(TEXT("Ella's artless stand-in reads as a dark figure"),
		Facts(UmbrellaFrameConst::EllaStandInName, 0.0f, false, true, UmbrellaArtSlotConst::StandInEllaColor) == EFrameTreatment::TintElla);
	TestTrue(TEXT("Ella art is never touched"),
		Facts(UmbrellaFrameConst::EllaStandInName, 0.0f, true, true, White) == EFrameTreatment::Keep);
	TestTrue(TEXT("Ella ink is dark (study's small dark figure)"),
		UmbrellaFrameConst::EllaInk.R + UmbrellaFrameConst::EllaInk.G + UmbrellaFrameConst::EllaInk.B < 0.2f);
	TestTrue(TEXT("Keeper metal is brighter than the backdrop, so the Keeper reads"),
		UmbrellaFrameConst::KeeperMetal.R > UmbrellaFrameConst::BackdropFlat.R * 4.0f);
	TestTrue(TEXT("cream stand-in block turns island umber"),
		Facts(TEXT("Block"), 0.0f, false, true, UmbrellaArtSlotConst::StandInDefaultColor) == EFrameTreatment::TintIsland);
	TestTrue(TEXT("backdrop art is dimmed"), Facts(TEXT("Panel"), -400.0f, true, true, White) == EFrameTreatment::DimBackdropArt);
	TestTrue(TEXT("artscene's graded backdrop layer is never dimmed (artscene request 5)"),
		Facts(TEXT("BackdropPanel"), -400.0f, true, true, White) == EFrameTreatment::Keep);
	TestTrue(TEXT("graded scene panel is never dimmed"), Facts(TEXT("ScenePanel"), -285.0f, true, true, White) == EFrameTreatment::Keep);
	TestTrue(TEXT("a flat backdrop stand-in panel is still darkened"),
		Facts(TEXT("BackdropPanel"), -400.0f, false, true, UmbrellaArtSlotConst::StandInDefaultColor) == EFrameTreatment::DarkenBackdropPanel);
	TestTrue(TEXT("enemy stand-ins are drawn small"), UFrameCompositionSubsystem::ScaleFor(EFrameTreatment::TintEnemy).X < 1.0);
	TestTrue(TEXT("the Keeper's telegraph cube is left as the Keeper draws it (thin red line, placed every tick)"),
		Facts(UmbrellaFrameConst::KeeperTelegraphName, -50.0f, false, true, UmbrellaFrameConst::TelegraphRed) == EFrameTreatment::Keep);
	TestTrue(TEXT("the Keeper's gust cube is left as the Keeper draws it (hidden)"),
		Facts(UmbrellaFrameConst::KeeperGustName, -50.0f, false, true, FLinearColor(0.7f, 0.85f, 1.0f)) == EFrameTreatment::Keep);
	TestTrue(TEXT("enemy shadow is dark, not a pink or red block"),
		UmbrellaFrameConst::EnemyShadow.R + UmbrellaFrameConst::EnemyShadow.G + UmbrellaFrameConst::EnemyShadow.B < 0.1f);
	TestTrue(TEXT("dimmed backdrop art is left alone"),
		Facts(TEXT("Panel"), -400.0f, true, true, UmbrellaFrameConst::BackdropDim) == EFrameTreatment::Keep);
	TestTrue(TEXT("bright backdrop stand-in panel is darkened"),
		Facts(TEXT("Panel"), -300.0f, false, true, UmbrellaArtSlotConst::StandInDefaultColor) == EFrameTreatment::DarkenBackdropPanel);
	TestTrue(TEXT("play-layer art (Ella, shots) is never touched"), Facts(TEXT("Sprite"), 0.0f, true, true, White) == EFrameTreatment::Keep);
	TestTrue(TEXT("salmon enemy stand-in turns red shadow"),
		Facts(TEXT("Placeholder"), 0.0f, false, true, UmbrellaArtSlotConst::StandInEnemyColor) == EFrameTreatment::TintEnemy);
	TestTrue(TEXT("a mesh without the slot material is kept"),
		Facts(UmbrellaFrameConst::KeeperStandInName, 0.0f, false, false, White) == EFrameTreatment::Keep);
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
			TestFalse(TEXT("a Keeper stand-in outside the arena is never hidden"), Keeper->bHiddenInGame);
			TestTrue(TEXT("the lilac Keeper stand-in is gunmetal"), ArtSlot::GetTint(Keeper).Equals(UmbrellaFrameConst::KeeperMetal, 0.0005f));
			if (bPanelArt)
			{
				TestTrue(TEXT("backdrop picture is dimmed toward the study's dark"), ArtSlot::GetTint(Panel).Equals(UmbrellaFrameConst::BackdropDim, 0.0005f));
			}
			TestEqual(TEXT("a second pass changes nothing"), Frame->ComposeNow(), 0);
			// A refresh that puts the cream stand-in back is caught by the next pass.
			ArtSlot::SetFlatUnlit(Block, Route, UmbrellaArtSlotConst::StandInDefaultColor);
			Frame->ComposeNow();
			TestTrue(TEXT("re-tinted after a stand-in refresh"), ArtSlot::GetTint(Block).Equals(UmbrellaFrameConst::IslandUmber, 0.0005f));
			// 16:28 review: every change is restorable.
			TestTrue(TEXT("restore puts every changed mesh back"), Frame->RestoreAll() >= 2);
			TestTrue(TEXT("cream block has its own colour again"), ArtSlot::GetTint(Block).Equals(UmbrellaArtSlotConst::StandInDefaultColor, 0.0005f));
			TestTrue(TEXT("Keeper stand-in has its own colour again"), ArtSlot::GetTint(Keeper).Equals(UmbrellaArtSlotConst::StandInKeeperColor, 0.0005f));
			TestEqual(TEXT("nothing left changed"), Frame->TouchedCount(), 0);
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
	// B11: in Director's Cut the "Director's Cut" title band (top TitleBandShare of the view) stays clear of Ella's picture.
	for (const FMarginCase& Case : Cases)
	{
		Ella->SetActorScale3D(StartScale * Case.ScaleMul);
		Ella->GetCapsuleComponent()->SetCapsuleHalfHeight(CapsuleBase * Case.CapsuleMul);
		Arena->MovePlayArea(LevelPlan::KeeperArenaOrigin());
		Frame->ApplyCameraMargin(Arena, Ella, EFrameTitleBand::Shown);
		const float Band = UmbrellaFrameConst::TitleBandShare * Camera->OrthoWidth / Aspect;
		TestTrue(FString::Printf(TEXT("Director's Cut title, %s: picture top %.1f below the title band %.1f"), Case.Name, SpriteTopAtCeiling(), FrameTop() - Band),
			SpriteTopAtCeiling() <= FrameTop() - Band + KINDA_SMALL_NUMBER);
		// Break check: the plain margin leaves the picture top inside the title band.
		Frame->ApplyCameraMargin(Arena, Ella, EFrameTitleBand::None);
		TestTrue(FString::Printf(TEXT("without the band, %s: the title covers the picture (break check)"), Case.Name),
			SpriteTopAtCeiling() > FrameTop() - UmbrellaFrameConst::TitleBandShare * Camera->OrthoWidth / Aspect);
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
	// levelchunks 16:14: the Keeper fight frame must show one continuous backdrop. Josh, 14 Nov: no barn picture on the DC
	// route at all (it read as the Start Game screen, and its edge cut the layers off before the fight). The layered
	// backdrop alone covers the widest fight frame.
	for (const FSceneArtSpec& Spec : USceneArtSubsystem::Specs())
	{
		TestFalse(TEXT("no route start/end picture"), Spec.Anchor == ESceneArtAnchor::RouteEnd || Spec.Anchor == ESceneArtAnchor::RouteStart);
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
	Ella->SetActorScale3D(Ella->GetActorScale3D() * 1.3f);
	Ella->GetCapsuleComponent()->SetCapsuleHalfHeight(Ella->GetCapsuleComponent()->GetUnscaledCapsuleHalfHeight() * 0.75f);
	Arena->MovePlayArea(LevelPlan::KeeperArenaOrigin());
	Frame->ApplyCameraMargin(Arena, Ella, EFrameTitleBand::Shown);
	const FVector View = Camera->GetComponentLocation();
	const float HalfViewW = Camera->OrthoWidth * 0.5f;
	const float HalfViewH = Camera->OrthoWidth / T.CameraAspectRatio * 0.5f;
	for (const FBackdropLayerSpec& Spec : UUmbrellaBackdropSubsystem::LayerSpecs())
	{
		const FBox2D Box = UUmbrellaBackdropSubsystem::LayerFootprint(static_cast<float>(View.X), Spec.Parallax);
		const FString Name = Spec.Name.ToString();
		TestTrue(*FString::Printf(TEXT("%s covers the fight frame's left"), *Name), Box.Min.X <= View.X - HalfViewW);
		TestTrue(*FString::Printf(TEXT("%s covers the fight frame's right"), *Name), Box.Max.X >= View.X + HalfViewW);
		TestTrue(*FString::Printf(TEXT("%s covers the fight frame's height"), *Name), Box.GetSize().Y >= 2.0f * HalfViewH);
	}
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
		// What is drawn: the picture plane's world bounds (r04: an actor-scale resize flattened the plane to 0 height).
		const FVector Half = Panel->Bounds.BoxExtent;
		return Half.X >= HalfViewW - 0.5f && Half.Z >= HalfViewH - 0.5f;
	};
	TestTrue(TEXT("gameplay frame reaches every screen edge with the margin"), FrameCovers(Camera->OrthoWidth));
	TestTrue(TEXT("the picture plane keeps its height"), Panel->Bounds.BoxExtent.Z > 1.0);
	TestEqual(TEXT("frame follows the camera"), static_cast<float>(Panel->GetOwner()->GetActorLocation().X), CameraX);
	// Break check: arena-sized (the old behaviour) sits inside the widened view.
	TestFalse(TEXT("arena-sized frame sits inside the widened view (break check)"), FrameCovers(0.0f));
	TestEqual(TEXT("not orthographic: scale 1"), USceneArtSubsystem::ViewScale(0.0f), 1.0f);
	return true;
}


IMPLEMENT_SIMPLE_AUTOMATION_TEST(FFrameCompositionKeeperAlwaysSeen, "UmbrellaElla.Feedback.FrameComposition.KeeperAlwaysSeen",
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::ClientContext | EAutomationTestFlags::EngineFilter)

bool FFrameCompositionKeeperAlwaysSeen::RunTest(const FString& Parameters)
{
	// Lead 17:08: in Start Game the Keeper was invisible (the pass hid every mesh named KeeperStandIn with no art, the
	// Keeper actor's own body too); hitbox and shots still worked. The Keeper must always be seen; Ella is a dark figure.
	FUmbrellaTestWorld Test;
	UWorld* World = Test.GetWorld();
	UFrameCompositionSubsystem* Frame = World->GetSubsystem<UFrameCompositionSubsystem>();
	AUmbrellaArena* Arena = World->SpawnActor<AUmbrellaArena>(FVector::ZeroVector, FRotator::ZeroRotator);
	if (Arena && !Arena->GetKeeperStandIn())
	{
		Arena->BuildPlaceholders();
	}
	AKeeperOfTime* Keeper = World->SpawnActor<AKeeperOfTime>(FVector(800.0, 0.0, 600.0), FRotator::ZeroRotator);
	AActor* EllaOwner = World->SpawnActor<AActor>();
	if (!TestNotNull(TEXT("frame"), Frame) || !TestNotNull(TEXT("arena"), Arena) || !TestNotNull(TEXT("keeper"), Keeper)
		|| !TestNotNull(TEXT("arena square"), Arena->GetKeeperStandIn()) || !EllaOwner)
	{
		return false;
	}
	UStaticMeshComponent* Square = Arena->GetKeeperStandIn();
	// The Keeper's own body (with its art when the asset exists), and an artless Keeper stand-in body outside the arena.
	UStaticMeshComponent* ArtBody = FindObjectFast<UStaticMeshComponent>(Keeper, FName(UmbrellaFrameConst::KeeperStandInName));
	AActor* BodyOwner = World->SpawnActor<AActor>();
	UStaticMeshComponent* Body = BodyOwner ? FrameTestMesh(BodyOwner, UmbrellaFrameConst::KeeperStandInName, FVector(800.0, -50.0, 600.0), UmbrellaArtSlotConst::StandInKeeperColor) : nullptr;
	UStaticMeshComponent* EllaFigure = FrameTestMesh(EllaOwner, UmbrellaFrameConst::EllaStandInName, FVector(0.0, 0.0, 300.0), UmbrellaArtSlotConst::StandInEllaColor);
	if (!TestNotNull(TEXT("body"), Body) || !ArtSlot::IsUnlit(Body))
	{
		AddWarning(TEXT("slot material missing: artless body not measured"));
		return true;
	}
	Frame->ComposeNow();
	TestFalse(TEXT("the artless Keeper body is drawn (never hidden)"), Body->bHiddenInGame);
	TestTrue(TEXT("the artless Keeper body reads as gunmetal"), ArtSlot::GetTint(Body).Equals(UmbrellaFrameConst::KeeperMetal, 0.0005f));
	TestTrue(TEXT("the arena's lilac square is hidden while the Keeper actor is there"), Square->bHiddenInGame);
	if (ArtBody && ArtSlot::HasArt(ArtBody))
	{
		TestFalse(TEXT("the Keeper's art body is never hidden"), ArtBody->bHiddenInGame);
	}
	TestTrue(TEXT("Ella's artless stand-in is the dark figure, not a bright block"), ArtSlot::GetTint(EllaFigure).Equals(UmbrellaFrameConst::EllaInk, 0.0005f));
	// artella r38: the pink block next to Ella was an enemy stand-in: dark and small, restorable.
	UStaticMeshComponent* EnemyBox = FrameTestMesh(EllaOwner, TEXT("Placeholder"), FVector(200.0, 0.0, 300.0), UmbrellaArtSlotConst::StandInEnemyColor);
	const FVector EnemyOwnScale(1.2, 0.2, 0.8);
	EnemyBox->SetRelativeScale3D(EnemyOwnScale);
	Frame->ComposeNow();
	TestTrue(TEXT("enemy stand-in is dark ink red"), ArtSlot::GetTint(EnemyBox).Equals(UmbrellaFrameConst::EnemyShadow, 0.0005f));
	TestTrue(TEXT("enemy stand-in is drawn small"), EnemyBox->GetRelativeScale3D().Equals(EnemyOwnScale * UmbrellaFrameConst::EnemyStandInScale, 0.001));
	TestEqual(TEXT("a second pass does not shrink it again"), Frame->ComposeNow(), 0);
	TestTrue(TEXT("still small once"), EnemyBox->GetRelativeScale3D().Equals(EnemyOwnScale * UmbrellaFrameConst::EnemyStandInScale, 0.001));
	// The Keeper's telegraph cube on the real Keeper actor: the frame pass never resizes or recolours it.
	if (UStaticMeshComponent* Telegraph = FindObjectFast<UStaticMeshComponent>(Keeper, FName(UmbrellaFrameConst::KeeperTelegraphName)))
	{
		if (!Keeper->HasActorBegunPlay())
		{
			Keeper->DispatchBeginPlay();
		}
		Frame->RestoreAll();
		const FVector Own = Telegraph->GetRelativeScale3D();
		const FLinearColor OwnTint = ArtSlot::GetTint(Telegraph);
		Telegraph->SetHiddenInGame(false);
		Frame->ComposeNow();
		TestTrue(TEXT("telegraph keeps the Keeper's size"), Telegraph->GetRelativeScale3D().Equals(Own, 0.001));
		TestTrue(TEXT("telegraph keeps the Keeper's colour"), ArtSlot::GetTint(Telegraph).Equals(OwnTint, 0.0005f));
	}
	// Quick passes look only at new actors (16:28 review: no scan of every actor every 0.2 s).
	Frame->ComposePass(EFramePass::Quick);
	TestEqual(TEXT("a quick pass with no new actor looks at none"), Frame->LastPassActorCount(), 0);
	World->SpawnActor<AActor>();
	Frame->ComposePass(EFramePass::Quick);
	TestEqual(TEXT("a quick pass looks at the new actor"), Frame->LastPassActorCount(), 1);
	// The Keeper leaves (Director's Cut route before the fight): the arena square stays hidden, never a grey box.
	Keeper->Destroy();
	Frame->ComposePass(EFramePass::Quick);
	TestTrue(TEXT("with no Keeper actor the arena square stays hidden"), Square->bHiddenInGame);
	Frame->RestoreAll();
	TestTrue(TEXT("restore gives the enemy stand-in its own size"), EnemyBox->GetRelativeScale3D().Equals(EnemyOwnScale, 0.001));
	TestFalse(TEXT("restore shows the square as its owner left it"), Square->bHiddenInGame);
	TestTrue(TEXT("restore gives the stand-in body its own lilac back"), ArtSlot::GetTint(Body).Equals(UmbrellaArtSlotConst::StandInKeeperColor, 0.0005f));
	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FFrameCompositionEnemyArtFullSize, "UmbrellaElla.Feedback.FrameComposition.EnemyArtFullSize",
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::ClientContext | EAutomationTestFlags::EngineFilter)

bool FFrameCompositionEnemyArtFullSize::RunTest(const FString& Parameters)
{
	// Review 18:08: a 0.6x enemy stand-in that gets art mid-run drew at 0.6x, and shrank to 0.36x when the art went away.
	FUmbrellaTestWorld Test;
	UWorld* World = Test.GetWorld();
	UFrameCompositionSubsystem* Frame = World->GetSubsystem<UFrameCompositionSubsystem>();
	AActor* Enemy = World->SpawnActor<AActor>();
	if (!TestNotNull(TEXT("frame"), Frame) || !TestNotNull(TEXT("enemy"), Enemy))
	{
		return false;
	}
	FrameTestMesh(Enemy, TEXT("Root"), FVector(0.0, 0.0, 0.0), FLinearColor::Black);
	UStaticMeshComponent* Box = FrameTestMesh(Enemy, TEXT("Placeholder"), FVector(0.0, 0.0, 0.0), UmbrellaArtSlotConst::StandInEnemyColor);
	if (!ArtSlot::IsUnlit(Box))
	{
		AddWarning(TEXT("slot material missing in this build: enemy art flip not measured"));
		return true;
	}
	const FVector Own = Box->GetRelativeScale3D();
	Frame->ComposeNow();
	TestTrue(TEXT("enemy stand-in is drawn small"), Box->GetRelativeScale3D().Equals(Own * UmbrellaFrameConst::EnemyStandInScale, 0.001));
	// Art lands; its owner keeps the box it had (no resize of its own).
	UTexture2D* Picture = UTexture2D::CreateTransient(4, 4);
	Picture->AddToRoot();
	const FArtSlotRow* Row = ArtSlot::Find(TEXT("bg-layer:Base"));
	const FVector Shrunk = Box->GetRelativeScale3D();
	if (TestNotNull(TEXT("art row"), Row) && ArtSlot::Apply(Box, Picture, *Row, FVector::OneVector) == EArtSlotDraw::Drawn)
	{
		Box->SetRelativeScale3D(Shrunk);
		Frame->ComposeNow();
		TestTrue(TEXT("the enemy's art draws at scale 1"), Box->GetRelativeScale3D().Equals(Own, 0.001));
		TestEqual(TEXT("an art mesh is not tracked"), Frame->TouchedCount(), 0);
		// Art goes away again: shrunk once from its own size, never 0.36x.
		ArtSlot::SetFlatUnlit(Box, Enemy, UmbrellaArtSlotConst::StandInEnemyColor);
		Frame->ComposeNow();
		TestTrue(TEXT("back to a stand-in: 0.6x, not 0.36x"), Box->GetRelativeScale3D().Equals(Own * UmbrellaFrameConst::EnemyStandInScale, 0.001));
	}
	Picture->RemoveFromRoot();
	return true;
}

#endif
