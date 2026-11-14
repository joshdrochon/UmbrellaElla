#include "Feedback/Background/SceneArtSubsystem.h"
#include "Camera/PlayerCameraManager.h"
#include "Components/StaticMeshComponent.h"
#include "Core/UmbrellaDrawOrder.h"
#include "Core/UmbrellaTuning.h"
#include "Engine/StaticMesh.h"
#include "Engine/Texture2D.h"
#include "Engine/World.h"
#include "Feedback/Art/ArtSlot.h"
#include "Feedback/Background/UmbrellaBackdropSubsystem.h"
#include "GameFramework/Actor.h"
#include "GameFramework/PlayerController.h"
#include "Harness/UmbrellaFeatureFlags.h"
#include "Level/LevelCatalogue.h"
#include "Level/LevelPlan.h"

namespace
{
	/** World Z of a panel centre: backdrop layers centre on 0, view-sized panels on the middle of the camera view. */
	float ScenePanelZ(const FSceneArtSpec& Spec)
	{
		return Spec.Anchor == ESceneArtAnchor::Layer ? 0.0f : GetDefault<UUmbrellaTuning>()->ArenaCamera.ArenaHeight * 0.5f;
	}
}

FVector2D USceneArtSubsystem::PanelSize(const FSceneArtSpec& Spec)
{
	if (Spec.Anchor == ESceneArtAnchor::Layer)
	{
		return FVector2D(UmbrellaBackdropConst::PanelWidth, UmbrellaBackdropConst::PanelHeight);
	}
	const FArenaCameraTuning& Camera = GetDefault<UUmbrellaTuning>()->ArenaCamera;
	const float Fill = Spec.Anchor == ESceneArtAnchor::View ? 1.0f : UmbrellaSceneArtConst::RouteEndFill;
	return FVector2D(Camera.ArenaWidth, Camera.ArenaHeight) * Fill;
}

TArray<FSceneArtSpec> USceneArtSubsystem::Specs()
{
	TArray<FSceneArtSpec> Out;
	Out.Add({ TEXT("bg:atmosphere"), UmbrellaDrawOrder::BackgroundFarY + UmbrellaSceneArtConst::AtmosphereStep, UmbrellaBackdropConst::SkyParallax, ESceneArtAnchor::Layer });
	Out.Add({ TEXT("bg:land"), UmbrellaDrawOrder::BackgroundFarY + UmbrellaSceneArtConst::LandStep, UmbrellaBackdropConst::FarParallax, ESceneArtAnchor::Layer });
	Out.Add({ TEXT("bg:water"), UmbrellaDrawOrder::BackgroundFarY + UmbrellaSceneArtConst::WaterStep, UmbrellaBackdropConst::FarParallax, ESceneArtAnchor::Layer });
	Out.Add({ TEXT("bg:clocks"), UmbrellaDrawOrder::BackgroundNearY + UmbrellaSceneArtConst::ClocksStep, UmbrellaBackdropConst::NearParallax, ESceneArtAnchor::Layer });
	Out.Add({ TEXT("bg:start-end"), UmbrellaDrawOrder::BackgroundNearY + UmbrellaSceneArtConst::StartEndStep, 1.0f, ESceneArtAnchor::RouteStart });
	Out.Add({ TEXT("bg:start-end"), UmbrellaDrawOrder::BackgroundNearY + UmbrellaSceneArtConst::StartEndStep, 1.0f, ESceneArtAnchor::RouteEnd });
	Out.Add({ TEXT("scene:gameplay-frame"), UmbrellaDrawOrder::ForegroundY + UmbrellaSceneArtConst::FrameLift, 0.0f, ESceneArtAnchor::View });
	return Out;
}

bool USceneArtSubsystem::IsVisualEnabled(const FString& Visual)
{
	if (Visual == TEXT("bg:land"))
	{
		return IsFeatureEnabled(EFeatureId::BG_04);
	}
	if (Visual == TEXT("bg:atmosphere") || Visual == TEXT("bg:water") || Visual == TEXT("bg:clocks"))
	{
		return IsFeatureEnabled(EFeatureId::BG_03);
	}
	return IsFeatureEnabled(EFeatureId::FLOW_25);
}

float USceneArtSubsystem::PanelX(const FSceneArtSpec& Spec, float CameraX)
{
	switch (Spec.Anchor)
	{
	case ESceneArtAnchor::View:
		return CameraX;
	case ESceneArtAnchor::RouteStart:
		return LevelCatalogue::SlotStartX(0) + GetDefault<UUmbrellaTuning>()->ArenaCamera.ArenaWidth * 0.5f;
	case ESceneArtAnchor::RouteEnd:
		// Centred on the Keeper fight frame (B5 moves the arena there at the handoff), so the route's end picture fills
		// the whole fight screen instead of stopping at the route end 40% across it (levelchunks 16:14 seam).
		return static_cast<float>(LevelPlan::KeeperArenaOrigin().X) + GetDefault<UUmbrellaTuning>()->ArenaCamera.ArenaWidth * 0.5f;
	default:
		return UUmbrellaBackdropSubsystem::LayerXForCamera(CameraX, Spec.Parallax);
	}
}

bool USceneArtSubsystem::ShouldCreateSubsystem(UObject* Outer) const
{
	const UWorld* World = Cast<UWorld>(Outer);
	return World && World->IsGameWorld() && Super::ShouldCreateSubsystem(Outer);
}

void USceneArtSubsystem::PostInitialize()
{
	Super::PostInitialize();
	TSet<FName> Seen;
	for (const FSceneArtSpec& Spec : Specs())
	{
		bool bAlready = false;
		Seen.Add(Spec.Visual, &bAlready);
		if (!bAlready)
		{
			ShowArt(Spec.Visual.ToString(), nullptr);
		}
	}
}

void USceneArtSubsystem::Deinitialize()
{
	Panels.Reset();
	Super::Deinitialize();
}

EArtSlotDraw USceneArtSubsystem::ShowArt(const FString& Visual, UTexture2D* Texture)
{
	UWorld* World = GetWorld();
	const FArtSlotRow* Row = ArtSlot::Find(*Visual);
	if (!IsValid(World) || !Row || !IsFeatureEnabled(EFeatureId::ART_05) || !IsVisualEnabled(Visual) || PanelCount(Visual) > 0)
	{
		return EArtSlotDraw::NoTexture;
	}
	UTexture2D* Picture = Texture ? Texture : ArtSlot::LoadTexture(*Row);
	if (!IsValid(Picture))
	{
		return EArtSlotDraw::NoTexture;
	}
	UStaticMesh* Shape = LoadObject<UStaticMesh>(nullptr, TEXT("/Engine/BasicShapes/Cube.Cube"));
	EArtSlotDraw Result = EArtSlotDraw::NoTexture;
	for (const FSceneArtSpec& Spec : Specs())
	{
		if (Spec.Visual != FName(*Visual))
		{
			continue;
		}
		AActor* Actor = World->SpawnActor<AActor>(FVector(PanelX(Spec, 0.0f), Spec.Depth, ScenePanelZ(Spec)), FRotator::ZeroRotator);
		if (!IsValid(Actor))
		{
			continue;
		}
		UStaticMeshComponent* Panel = NewObject<UStaticMeshComponent>(Actor, TEXT("ScenePanel"));
		if (IsValid(Shape))
		{
			Panel->SetStaticMesh(Shape);
		}
		Panel->SetCollisionEnabled(ECollisionEnabled::NoCollision);
		Panel->SetGenerateOverlapEvents(false);
		const FVector2D Size = USceneArtSubsystem::PanelSize(Spec);
		const float Unit = UmbrellaBackdropConst::EngineCubeSize;
		const FVector Box(Size.X / Unit, UmbrellaBackdropConst::PanelThickness, Size.Y / Unit);
		Panel->SetRelativeScale3D(Box);
		Actor->SetRootComponent(Panel);
		Panel->RegisterComponent();
		Actor->SetActorLocation(FVector(PanelX(Spec, 0.0f), Spec.Depth, ScenePanelZ(Spec)));
		Result = ArtSlot::Apply(Panel, Picture, *Row, Box);
		if (Result != EArtSlotDraw::Drawn)
		{
			Actor->Destroy();
			return Result;
		}
		FPanel& Entry = Panels.AddDefaulted_GetRef();
		Entry.Spec = Spec;
		Entry.Actor = Actor;
	}
	return Result;
}

int32 USceneArtSubsystem::PanelCount(const FString& Visual) const
{
	int32 Count = 0;
	for (const FPanel& Entry : Panels)
	{
		Count += (Entry.Spec.Visual == FName(*Visual) && Entry.Actor.IsValid()) ? 1 : 0;
	}
	return Count;
}

UStaticMeshComponent* USceneArtSubsystem::FindPanel(const FString& Visual, int32 Index) const
{
	int32 Seen = 0;
	for (const FPanel& Entry : Panels)
	{
		if (Entry.Spec.Visual == FName(*Visual) && Entry.Actor.IsValid() && Seen++ == Index)
		{
			return Cast<UStaticMeshComponent>(Entry.Actor->GetRootComponent());
		}
	}
	return nullptr;
}

void USceneArtSubsystem::ScrollTo(float CameraX)
{
	for (const FPanel& Entry : Panels)
	{
		if (AActor* Actor = Entry.Actor.Get())
		{
			FVector Location = Actor->GetActorLocation();
			Location.X = PanelX(Entry.Spec, CameraX);
			Actor->SetActorLocation(Location);
		}
	}
}

void USceneArtSubsystem::Tick(float DeltaTime)
{
	const UWorld* World = GetWorld();
	const APlayerController* Controller = IsValid(World) ? World->GetFirstPlayerController() : nullptr;
	if (IsValid(Controller) && IsValid(Controller->PlayerCameraManager) && !Panels.IsEmpty())
	{
		ScrollTo(static_cast<float>(Controller->PlayerCameraManager->GetCameraLocation().X));
	}
}

TStatId USceneArtSubsystem::GetStatId() const
{
	RETURN_QUICK_DECLARE_CYCLE_STAT(USceneArtSubsystem, STATGROUP_Tickables);
}
