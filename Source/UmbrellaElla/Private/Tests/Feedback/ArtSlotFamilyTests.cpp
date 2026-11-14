#include "Components/StaticMeshComponent.h"
#include "Engine/Engine.h"
#include "Engine/Texture2D.h"
#include "Engine/World.h"
#include "Feedback/Anim/EllaAnimPresenterComponent.h"
#include "Feedback/Art/ArtSlot.h"
#include "Feedback/Background/WorldArtSubsystem.h"
#include "Feedback/Ui/UiArtSubsystem.h"
#include "GameFramework/Actor.h"
#include "Level/LevelCatalogue.h"
#include "Level/UmbrellaLevelDirector.h"
#include "Misc/AutomationTest.h"

#if WITH_AUTOMATION_TESTS

namespace
{
	UTexture2D* FamilyTestTexture()
	{
		UTexture2D* Texture = UTexture2D::CreateTransient(4, 4);
		Texture->AddToRoot();
		return Texture;
	}

	UWorld* FamilyTestWorld()
	{
		UWorld* World = UWorld::CreateWorld(EWorldType::Game, false);
		if (World)
		{
			GEngine->CreateNewWorldContext(EWorldType::Game).SetCurrentWorld(World);
		}
		return World;
	}

	void FamilyTestEnd(UWorld* World)
	{
		GEngine->DestroyWorldContext(World);
		World->DestroyWorld(false);
	}
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FArtSlotEllaOverlays, "UmbrellaElla.Feedback.World.ArtSlotEllaOverlays",
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::ClientContext | EAutomationTestFlags::EngineFilter)

bool FArtSlotEllaOverlays::RunTest(const FString& Parameters)
{
	UWorld* World = FamilyTestWorld();
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
	UTexture2D* Texture = FamilyTestTexture();
	float LastDepth = -1.0e9f;
	for (const UmbrellaEllaOverlayConst::FOverlay& Layer : UmbrellaEllaOverlayConst::Overlays)
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
		const bool bAssetExists = ArtSlot::LoadTexture(*Row) != nullptr;
		TestEqual(*FString::Printf(TEXT("%s drawn at build iff its asset exists"), *Id), Presenter->FindOverlay(Id) != nullptr, bAssetExists);
		if (!bAssetExists)
		{
			TestTrue(*FString::Printf(TEXT("%s takes a picture"), *Id), Presenter->ShowOverlayArt(Id, Texture) == EArtSlotDraw::Drawn);
		}
		TestTrue(*FString::Printf(TEXT("second picture for %s refused"), *Id), Presenter->ShowOverlayArt(Id, Texture) != EArtSlotDraw::Drawn);
		const UStaticMeshComponent* Part = Presenter->FindOverlay(Id);
		if (TestNotNull(*FString::Printf(TEXT("%s overlay"), *Id), Part))
		{
			TestTrue(*FString::Printf(TEXT("%s shows art"), *Id), ArtSlot::IsDrawingArt(Part));
			TestEqual(*FString::Printf(TEXT("%s has no collision"), *Id), static_cast<int32>(Part->GetCollisionEnabled()), static_cast<int32>(ECollisionEnabled::NoCollision));
			TestEqual(*FString::Printf(TEXT("%s depth offset"), *Id), static_cast<float>(Part->GetComponentLocation().Y - Owner->GetActorLocation().Y), Layer.DepthOffset);
		}
	}
	// Each overlay shows only for its own facts.
	FEllaOverlayInput Calm;
	TestTrue(TEXT("prop always shows"), UEllaAnimPresenterComponent::ShouldShowOverlay(TEXT("umbrella:prop"), Calm));
	for (const TCHAR* Id : { TEXT("ella:condition-100-to-0"), TEXT("ella:free-fall"), TEXT("ella:hop-cartwheel-dash"), TEXT("ella:mode-transition"), TEXT("ella:living-critical"), TEXT("umbrella:repair") })
	{
		TestFalse(*FString::Printf(TEXT("%s hidden when calm"), Id), UEllaAnimPresenterComponent::ShouldShowOverlay(Id, Calm));
	}
	FEllaOverlayInput Fall;
	Fall.bFreeFall = true;
	TestTrue(TEXT("free fall shows"), UEllaAnimPresenterComponent::ShouldShowOverlay(TEXT("ella:free-fall"), Fall));
	FEllaOverlayInput Move;
	Move.bMoving = true;
	TestTrue(TEXT("hop shows motion"), UEllaAnimPresenterComponent::ShouldShowOverlay(TEXT("ella:hop-cartwheel-dash"), Move));
	FEllaOverlayInput Hurt;
	Hurt.HealthFraction = 0.5f;
	TestTrue(TEXT("hurt shows condition"), UEllaAnimPresenterComponent::ShouldShowOverlay(TEXT("ella:condition-100-to-0"), Hurt));
	TestFalse(TEXT("half health is not critical"), UEllaAnimPresenterComponent::ShouldShowOverlay(TEXT("ella:living-critical"), Hurt));
	Hurt.HealthFraction = UmbrellaEllaOverlayConst::CriticalFraction;
	TestTrue(TEXT("one hit left is critical"), UEllaAnimPresenterComponent::ShouldShowOverlay(TEXT("ella:living-critical"), Hurt));
	FEllaOverlayInput Switch;
	Switch.TransitionLeft = 0.1f;
	Switch.RepairLeft = 0.1f;
	TestTrue(TEXT("mode transition holds"), UEllaAnimPresenterComponent::ShouldShowOverlay(TEXT("ella:mode-transition"), Switch));
	TestTrue(TEXT("repair holds"), UEllaAnimPresenterComponent::ShouldShowOverlay(TEXT("umbrella:repair"), Switch));
	// Driving the facts toggles the drawn parts.
	Presenter->UpdateOverlays(Fall);
	if (const UStaticMeshComponent* FallPart = Presenter->FindOverlay(TEXT("ella:free-fall")))
	{
		TestTrue(TEXT("free-fall part visible while falling"), FallPart->IsVisible());
		Presenter->UpdateOverlays(Calm);
		TestFalse(TEXT("free-fall part hidden after"), FallPart->IsVisible());
	}
	FamilyTestEnd(World);
	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FArtSlotWorldPieces, "UmbrellaElla.Feedback.World.ArtSlotWorldPieces",
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::ClientContext | EAutomationTestFlags::EngineFilter)

bool FArtSlotWorldPieces::RunTest(const FString& Parameters)
{
	UWorld* World = FamilyTestWorld();
	if (!TestNotNull(TEXT("world"), World))
	{
		return false;
	}
	UWorldArtSubsystem* WorldArt = World->GetSubsystem<UWorldArtSubsystem>();
	AUmbrellaLevelDirector* Director = World->SpawnActor<AUmbrellaLevelDirector>();
	if (TestNotNull(TEXT("world art subsystem"), WorldArt) && TestNotNull(TEXT("director"), Director))
	{
		TestTrue(TEXT("route built"), Director->BuildRoute(1) > 0);
		for (const FString Id : { FString(TEXT("world:solids")), FString(TEXT("world:solids-block")), FString(TEXT("world:refuge-and-yellow-bay")), FString(TEXT("world:mill-and-traps")) })
		{
			const FArtSlotRow* Row = ArtSlot::Find(*Id);
			if (TestNotNull(*FString::Printf(TEXT("%s has a slot row"), *Id), Row))
			{
				TestFalse(*FString::Printf(TEXT("%s names a consumer"), *Id), FString(Row->DrawnBy) == TEXT("-"));
			}
		}
		// Count what the plan holds, then draw with a transient picture and compare.
		int32 Solids = 0;
		int32 Blocks = 0;
		int32 Refuges = 0;
		for (const FLevelPlacement& Placement : Director->GetPlan())
		{
			const FString Visual = UWorldArtSubsystem::VisualFor(Placement.Kind, Placement.Size);
			Solids += Visual == TEXT("world:solids") ? 1 : 0;
			Blocks += Visual == TEXT("world:solids-block") ? 1 : 0;
			Refuges += Visual == TEXT("world:refuge-and-yellow-bay") ? 1 : 0;
		}
		TestTrue(TEXT("the route has land and refuges"), Solids > 0 && Refuges > 0);
		TestEqual(TEXT("the floor draws the island slab, never a flat bar (artscene request 4)"), UWorldArtSubsystem::VisualFor(ELevelPlacementKind::Floor), FString(TEXT("world:solids")));
		// artscene request 6: blocks and columns get their own picture; ledges, the floor and other kinds keep theirs.
		TestEqual(TEXT("a 192x259 column draws the block picture"), UWorldArtSubsystem::VisualFor(ELevelPlacementKind::Solid, FVector(192.0f, 100.0f, 259.0f)), FString(TEXT("world:solids-block")));
		TestEqual(TEXT("a 576x43 ledge draws the ledge picture"), UWorldArtSubsystem::VisualFor(ELevelPlacementKind::Solid, FVector(576.0f, 100.0f, 43.0f)), FString(TEXT("world:solids")));
		TestEqual(TEXT("a 4.27:1 piece is a ledge by the 4:1 line"), UWorldArtSubsystem::VisualFor(ELevelPlacementKind::Solid, FVector(461.0f, 100.0f, 108.0f)), FString(TEXT("world:solids")));
		TestEqual(TEXT("a tall floor stays the island slab"), UWorldArtSubsystem::VisualFor(ELevelPlacementKind::Floor, FVector(192.0f, 100.0f, 259.0f)), FString(TEXT("world:solids")));
		TestEqual(TEXT("a block with no imported picture falls back to the ledge picture, never a bare box"), UWorldArtSubsystem::FallbackVisual(TEXT("world:solids-block")), FString(TEXT("world:solids")));
		TestTrue(TEXT("other slots have no fallback"), UWorldArtSubsystem::FallbackVisual(TEXT("world:solids")).IsEmpty());
		TestEqual(TEXT("a zero-height solid is a ledge, not a divide by zero"), UWorldArtSubsystem::VisualFor(ELevelPlacementKind::Solid, FVector(100.0f, 100.0f, 0.0f)), FString(TEXT("world:solids")));
		// Every land block that collides before drawing (the solids Ella meets), measured before the pictures go on.
		TArray<UStaticMeshComponent*> Colliding;
		for (const TObjectPtr<AActor>& Piece : Director->GetSpawned())
		{
			UStaticMeshComponent* Block = IsValid(Piece) ? FindObjectFast<UStaticMeshComponent>(Piece, TEXT("Block")) : nullptr;
			if (Block && Block->GetCollisionEnabled() == ECollisionEnabled::QueryAndPhysics)
			{
				Colliding.Add(Block);
			}
		}
		TestTrue(TEXT("the route has colliding land blocks"), Colliding.Num() > 0);
		UTexture2D* Texture = FamilyTestTexture();
		const int32 Drawn = WorldArt->Refresh(Texture);
		TestEqual(TEXT("every ledge is drawn"), WorldArt->DrawnCount(TEXT("world:solids")), Solids);
		TestEqual(TEXT("every block and column is drawn with the block picture"), WorldArt->DrawnCount(TEXT("world:solids-block")), Blocks);
		TestEqual(TEXT("every refuge piece is drawn"), WorldArt->DrawnCount(TEXT("world:refuge-and-yellow-bay")), Refuges);
		TestEqual(TEXT("drawn total is the four slots"), Drawn, Solids + Blocks + Refuges + WorldArt->DrawnCount(TEXT("world:mill-and-traps")));
		TestEqual(TEXT("a second pass draws nothing new"), WorldArt->Refresh(Texture), 0);
		// main 991b3eb7: drawing turned each block's own mesh into a NoCollision plane, so Ella flew through every solid.
		// Every block that collided before still collides, keeps its box size, and its picture is on a non-colliding plane.
		int32 StillColliding = 0;
		int32 PicturedApart = 0;
		for (UStaticMeshComponent* Block : Colliding)
		{
			StillColliding += Block->GetCollisionEnabled() == ECollisionEnabled::QueryAndPhysics ? 1 : 0;
			const UStaticMeshComponent* Picture = FindObjectFast<UStaticMeshComponent>(Block->GetOwner(), TEXT("BlockArt"));
			PicturedApart += Picture && ArtSlot::HasArt(Picture) && Picture->GetCollisionEnabled() == ECollisionEnabled::NoCollision
				&& Picture->IsVisible() && !Block->IsVisible() && !ArtSlot::HasArt(Block) ? 1 : 0;
		}
		TestEqual(TEXT("every drawn land block still collides"), StillColliding, Colliding.Num());
		TestEqual(TEXT("every drawn land block shows its picture on a separate non-colliding plane"), PicturedApart, Colliding.Num());
	}
	FamilyTestEnd(World);
	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FArtSlotUiPieces, "UmbrellaElla.Feedback.World.ArtSlotUiPieces",
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::ClientContext | EAutomationTestFlags::EngineFilter)

bool FArtSlotUiPieces::RunTest(const FString& Parameters)
{
	// Every ui piece and menu backdrop has a row naming a consumer and a place in the table; a piece shows only on its screens.
	for (const UmbrellaUiPieceConst::FUiPiece& Piece : UmbrellaUiPieceConst::Pieces)
	{
		const FArtSlotRow* Row = ArtSlot::Find(Piece.Visual);
		if (TestNotNull(Piece.Visual, Row))
		{
			TestFalse(*FString::Printf(TEXT("%s names a consumer"), Piece.Visual), FString(Row->DrawnBy) == TEXT("-"));
		}
		TestTrue(*FString::Printf(TEXT("%s is on at least one screen"), Piece.Visual), Piece.Screens != 0);
	}
	UWorld* World = FamilyTestWorld();
	if (!TestNotNull(TEXT("world"), World))
	{
		return false;
	}
	UUiArtSubsystem* Ui = World->GetSubsystem<UUiArtSubsystem>();
	if (TestNotNull(TEXT("ui art subsystem"), Ui))
	{
		UTexture2D* Texture = FamilyTestTexture();
		TestFalse(TEXT("nothing without a picture"), Ui->DrawPiece(TEXT("ui:title-lockup"), EFlowScreen::Title, nullptr) == EArtSlotDraw::Drawn);
		TestTrue(TEXT("lockup shows on Title"), Ui->DrawPiece(TEXT("ui:title-lockup"), EFlowScreen::Title, Texture) == EArtSlotDraw::Drawn);
		TestTrue(TEXT("lockup is tracked"), Ui->IsShowingPiece(TEXT("ui:title-lockup")));
		TestFalse(TEXT("a second lockup is refused"), Ui->DrawPiece(TEXT("ui:title-lockup"), EFlowScreen::Title, Texture) == EArtSlotDraw::Drawn);
		TestFalse(TEXT("lockup is not drawn on Settings"), Ui->DrawPiece(TEXT("ui:title-lockup"), EFlowScreen::Settings, Texture) == EArtSlotDraw::Drawn);
		TestTrue(TEXT("settings head shows on Settings"), Ui->DrawPiece(TEXT("ui:head-Settings"), EFlowScreen::Settings, Texture) == EArtSlotDraw::Drawn);
		TestFalse(TEXT("settings head is not drawn on Paused"), Ui->DrawPiece(TEXT("ui:head-Paused"), EFlowScreen::Settings, Texture) == EArtSlotDraw::Drawn);
		TestEqual(TEXT("two pieces up"), Ui->PieceCount(), 2);
		Ui->ClearPieces();
		TestEqual(TEXT("cleared"), Ui->PieceCount(), 0);
		TestFalse(TEXT("unknown piece refused"), Ui->DrawPiece(TEXT("ui:nothing"), EFlowScreen::Title, Texture) == EArtSlotDraw::Drawn);
	}
	FamilyTestEnd(World);
	return true;
}

#endif
