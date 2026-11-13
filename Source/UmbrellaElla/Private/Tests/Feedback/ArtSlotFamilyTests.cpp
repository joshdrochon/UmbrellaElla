#include "Components/StaticMeshComponent.h"
#include "Engine/Engine.h"
#include "Engine/Texture2D.h"
#include "Engine/World.h"
#include "Feedback/Anim/EllaAnimPresenterComponent.h"
#include "Feedback/Art/ArtSlot.h"
#include "GameFramework/Actor.h"
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

#endif
