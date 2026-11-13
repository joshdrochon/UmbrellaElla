#include "Arena/UmbrellaArena.h"
#include "Camera/CameraComponent.h"
#include "Components/StaticMeshComponent.h"
#include "Core/UmbrellaDrawOrder.h"
#include "Engine/Engine.h"
#include "Engine/StaticMesh.h"
#include "Engine/World.h"
#include "Feedback/Art/ArtSlot.h"
#include "Feedback/Background/UmbrellaBackdropSubsystem.h"
#include "Feedback/Ui/UiArtSubsystem.h"
#include "Flow/FlowRules.h"
#include "Algo/Find.h"
#include "Engine/Texture2D.h"
#include "GameFramework/Actor.h"
#include "Materials/MaterialInstanceDynamic.h"
#include "Misc/AutomationTest.h"

#if WITH_AUTOMATION_TESTS

namespace
{
	UWorld* ScreenFixTestWorld()
	{
		UWorld* World = UWorld::CreateWorld(EWorldType::Game, false);
		if (World)
		{
			GEngine->CreateNewWorldContext(EWorldType::Game).SetCurrentWorld(World);
		}
		return World;
	}

	void ScreenFixTestEnd(UWorld* World)
	{
		GEngine->DestroyWorldContext(World);
		World->DestroyWorld(false);
	}
}

// The ortho play camera must render the view it reports. With auto-calculated ortho planes on, the engine drew the
// frame centred on world (0, 0) instead of the arena middle, so Ella, the guard and the Keeper fell off screen.
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FScreenFixCamera, "UmbrellaElla.ScreenFix.CameraRendersItsOwnView",
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::ClientContext | EAutomationTestFlags::EngineFilter)

bool FScreenFixCamera::RunTest(const FString& Parameters)
{
	const UCameraComponent* Camera = GetDefault<AUmbrellaArena>()->GetPlayCamera();
	if (!TestNotNull(TEXT("play camera"), Camera))
	{
		return false;
	}
	TestEqual(TEXT("orthographic"), static_cast<int32>(Camera->ProjectionMode), static_cast<int32>(ECameraProjectionMode::Orthographic));
	TestFalse(TEXT("no auto ortho planes (they re-centre the view on the world origin)"), Camera->bAutoCalculateOrthoPlanes);
	FPostProcessSettings Settings;
	AUmbrellaArena::ApplyFlatLookPostProcess(Settings);
	TestEqual(TEXT("exposure is fixed"), Settings.AutoExposureMinBrightness, Settings.AutoExposureMaxBrightness);
	TestEqual(TEXT("no bloom"), Settings.BloomIntensity, 0.0f);
	return true;
}

// Every backdrop layer sits behind every gameplay depth, so nothing paper-like can cover Ella, the guard or a shot.
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FScreenFixDepth, "UmbrellaElla.ScreenFix.World.GameplayInFrontOfEveryBackdropLayer",
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::ClientContext | EAutomationTestFlags::EngineFilter)

bool FScreenFixDepth::RunTest(const FString& Parameters)
{
	UWorld* World = ScreenFixTestWorld();
	if (!TestNotNull(TEXT("world"), World))
	{
		return false;
	}
	UUmbrellaBackdropSubsystem* Backdrop = World->GetSubsystem<UUmbrellaBackdropSubsystem>();
	if (TestNotNull(TEXT("backdrop"), Backdrop) && TestTrue(TEXT("layers built"), Backdrop->BuildLayers() > 0))
	{
		const float Gameplay[] = { UmbrellaDrawOrder::ArenaY, UmbrellaDrawOrder::HazardY, UmbrellaDrawOrder::KeeperY, UmbrellaDrawOrder::EllaY, UmbrellaDrawOrder::ProjectileY, UmbrellaDrawOrder::VfxY };
		for (const AActor* Layer : Backdrop->GetLayers())
		{
			const UStaticMeshComponent* Panel = Cast<UStaticMeshComponent>(Layer->GetRootComponent());
			TestTrue(TEXT("backdrop panel is flat unlit"), ArtSlot::IsUnlit(Panel));
			// Nearest face of the panel (centre plus half its thickness) still behind the farthest gameplay depth.
			const float Front = static_cast<float>(Layer->GetActorLocation().Y) + UmbrellaBackdropConst::PanelThickness * UmbrellaArtSlotConst::PlaneEdge * 0.5f;
			for (const float Depth : Gameplay)
			{
				TestTrue(TEXT("every gameplay depth is in front of this backdrop layer"), Front < Depth);
			}
		}
	}
	ScreenFixTestEnd(World);
	return true;
}

// A stand-in cube never depends on level lights: the flat slot material is unlit.
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FScreenFixUnlit, "UmbrellaElla.ScreenFix.World.StandInsAreUnlit",
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::ClientContext | EAutomationTestFlags::EngineFilter)

bool FScreenFixUnlit::RunTest(const FString& Parameters)
{
	UWorld* World = ScreenFixTestWorld();
	if (!TestNotNull(TEXT("world"), World))
	{
		return false;
	}
	AActor* Owner = World->SpawnActor<AActor>();
	UStaticMeshComponent* Mesh = NewObject<UStaticMeshComponent>(Owner, TEXT("StandIn"));
	Mesh->SetStaticMesh(LoadObject<UStaticMesh>(nullptr, TEXT("/Engine/BasicShapes/Cube.Cube")));
	TestFalse(TEXT("the engine cube starts lit"), ArtSlot::IsUnlit(Mesh));
	ArtSlot::SetFlatUnlit(Mesh, Owner, UmbrellaArtSlotConst::StandInEllaColor);
	TestTrue(TEXT("flat unlit after SetFlatUnlit"), ArtSlot::IsUnlit(Mesh));
	if (const UMaterialInstanceDynamic* Dynamic = Cast<UMaterialInstanceDynamic>(Mesh->GetMaterial(0)))
	{
		FLinearColor Tint;
		TestTrue(TEXT("tint set"), Dynamic->GetVectorParameterValue(FName(TEXT("Tint")), Tint));
		TestEqual(TEXT("tint is the stand-in colour"), Tint, UmbrellaArtSlotConst::StandInEllaColor);
	}
	ScreenFixTestEnd(World);
	return true;
}

// B2 (Nov 13): the screen:Playing stand-in was a screenshot of a black frame, drawn full-screen above the game, so
// gameplay was black with only a clock. No full-frame screen picture may sit over the played world.
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FScreenFixNoScreenArtOverGameplay, "UmbrellaElla.ScreenFix.World.NoScreenArtOverGameplay",
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::ClientContext | EAutomationTestFlags::EngineFilter)

bool FScreenFixNoScreenArtOverGameplay::RunTest(const FString& Parameters)
{
	UWorld* World = ScreenFixTestWorld();
	if (!TestNotNull(TEXT("world"), World))
	{
		return false;
	}
	UUiArtSubsystem* Ui = World->GetSubsystem<UUiArtSubsystem>();
	if (TestNotNull(TEXT("ui art subsystem"), Ui))
	{
		UTexture2D* Texture = UTexture2D::CreateTransient(4, 4);
		Texture->AddToRoot();
		const EFlowScreen Gameplay[] = { EFlowScreen::Playing, EFlowScreen::Resuming, EFlowScreen::Tutorial };
		for (int32 Value = 0; Value <= static_cast<int32>(EFlowScreen::Statistics); ++Value)
		{
			const EFlowScreen Screen = static_cast<EFlowScreen>(Value);
			const bool bGameplay = Algo::Find(Gameplay, Screen) != nullptr;
			Ui->ShowScreenArt(Screen, Texture);
			const FString What = UUiArtSubsystem::VisualIdFor(Screen);
			if (bGameplay)
			{
				TestFalse(*FString::Printf(TEXT("%s never covers the played world"), *What), Ui->IsShowingArt());
			}
			else
			{
				TestTrue(*FString::Printf(TEXT("%s shows on a menu screen"), *What), Ui->IsShowingArt());
			}
		}
		Ui->ClearScreenArt();
		Texture->RemoveFromRoot();
	}
	ScreenFixTestEnd(World);
	return true;
}

#endif
