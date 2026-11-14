#include "Feedback/Background/UmbrellaBackdropSubsystem.h"
#include "Components/StaticMeshComponent.h"
#include "Core/UmbrellaDrawOrder.h"
#include "Engine/StaticMesh.h"
#include "Engine/Texture2D.h"
#include "Feedback/Art/ArtSlot.h"
#include "Engine/World.h"
#include "GameFramework/Actor.h"
#include "GameFramework/PlayerController.h"
#include "Camera/PlayerCameraManager.h"
#include "Harness/UmbrellaFeatureFlags.h"
#include "Core/UmbrellaTuning.h"
#include "Level/LevelCatalogue.h"
#include "Level/LevelPlan.h"
#include "Arena/UmbrellaArena.h"
#include "EngineUtils.h"

namespace
{
	/** Unlit stand-in colour for a backdrop layer with no art. */
	FLinearColor BackdropStandInColor(FName LayerName)
	{
		if (LayerName == TEXT("Sky"))
		{
			return UmbrellaBackdropConst::SkyStandInColor;
		}
		if (LayerName == TEXT("FarLand"))
		{
			return UmbrellaBackdropConst::FarLandStandInColor;
		}
		return UmbrellaBackdropConst::NearStandInColor;
	}
}

bool UUmbrellaBackdropSubsystem::IsLayerEnabled(FName LayerName)
{
	if (LayerName == TEXT("Sky"))
	{
		return IsFeatureEnabled(EFeatureId::BG_03);
	}
	if (LayerName == TEXT("FarLand"))
	{
		return IsFeatureEnabled(EFeatureId::BG_04);
	}
	if (LayerName == TEXT("NearArchitecture"))
	{
		return IsFeatureEnabled(EFeatureId::BG_02);
	}
	if (LayerName == TEXT("ClockWaterWind"))
	{
		return IsFeatureEnabled(EFeatureId::BG_06);
	}
	return IsFeatureEnabled(EFeatureId::BG_05);
}

TArray<FBackdropLayerSpec> UUmbrellaBackdropSubsystem::LayerSpecs()
{
	TArray<FBackdropLayerSpec> Specs;
	Specs.Add({ TEXT("Sky"), UmbrellaDrawOrder::BackgroundFarY, UmbrellaBackdropConst::SkyParallax });
	Specs.Add({ TEXT("FarLand"), UmbrellaDrawOrder::BackgroundFarY + UmbrellaBackdropConst::SameDepthStep, UmbrellaBackdropConst::FarParallax });
	Specs.Add({ TEXT("Base"), UmbrellaDrawOrder::BackgroundNearY - UmbrellaBackdropConst::SameDepthStep, UmbrellaBackdropConst::FarParallax });
	Specs.Add({ TEXT("NearArchitecture"), UmbrellaDrawOrder::BackgroundNearY, UmbrellaBackdropConst::NearParallax });
	Specs.Add({ TEXT("ClockWaterWind"), UmbrellaDrawOrder::BackgroundNearY + UmbrellaBackdropConst::SameDepthStep, UmbrellaBackdropConst::AssemblyParallax });
	return Specs;
}

TArray<float> UUmbrellaBackdropSubsystem::LayerDepths()
{
	TArray<float> Depths;
	for (const FBackdropLayerSpec& Spec : LayerSpecs())
	{
		if (IsLayerEnabled(Spec.Name))
		{
			Depths.Add(Spec.Depth);
		}
	}
	return Depths;
}

float UUmbrellaBackdropSubsystem::RouteCameraMinX()
{
	return LevelCatalogue::SlotStartX(0);
}

float UUmbrellaBackdropSubsystem::RouteCameraMaxX()
{
	return static_cast<float>(LevelPlan::KeeperArenaOrigin().X) + GetDefault<UUmbrellaTuning>()->ArenaCamera.ArenaWidth;
}

float UUmbrellaBackdropSubsystem::EffectiveParallax(float Parallax)
{
	float Fastest = 0.0f;
	for (const FBackdropLayerSpec& Spec : LayerSpecs())
	{
		Fastest = FMath::Max(Fastest, Spec.Parallax);
	}
	const float HalfTravel = FMath::Max(1.0f, (RouteCameraMaxX() - RouteCameraMinX()) * 0.5f);
	const float Scale = Fastest > 0.0f ? FMath::Min(1.0f, UmbrellaBackdropConst::SlideHeadroom / (Fastest * HalfTravel)) : 1.0f;
	return Parallax * Scale;
}

float UUmbrellaBackdropSubsystem::LayerOffset(float CameraX, float Parallax)
{
	const float Centre = (RouteCameraMinX() + RouteCameraMaxX()) * 0.5f;
	const float Headroom = UmbrellaBackdropConst::SlideHeadroom;
	return FMath::Clamp(-EffectiveParallax(Parallax) * (CameraX - Centre), -Headroom, Headroom);
}

float UUmbrellaBackdropSubsystem::LayerXForCamera(float CameraX, float Parallax)
{
	return CameraX + LayerOffset(CameraX, Parallax);
}

int32 UUmbrellaBackdropSubsystem::HideArenaStandIns()
{
	UWorld* World = GetWorld();
	bool bAnyArt = false;
	for (int32 Index = 0; Index < Layers.Num(); ++Index)
	{
		bAnyArt = bAnyArt || IsLayerDrawnWithArt(Index);
	}
	if (!bAnyArt || !IsValid(World))
	{
		return 0;
	}
	int32 Hidden = 0;
	for (TActorIterator<AUmbrellaArena> It(World); It; ++It)
	{
		for (UStaticMeshComponent* Plane : { It->GetBackgroundFar(), It->GetBackgroundNear() })
		{
			if (IsValid(Plane))
			{
				if (!Plane->bHiddenInGame)
				{
					Plane->SetHiddenInGame(true);
				}
				++Hidden;
			}
		}
	}
	return Hidden;
}

bool UUmbrellaBackdropSubsystem::ShouldCreateSubsystem(UObject* Outer) const
{
	const UWorld* World = Cast<UWorld>(Outer);
	return World && World->IsGameWorld() && Super::ShouldCreateSubsystem(Outer);
}

void UUmbrellaBackdropSubsystem::PostInitialize()
{
	Super::PostInitialize();
	BuildLayers();
}

int32 UUmbrellaBackdropSubsystem::BuildLayers()
{
	UWorld* World = GetWorld();
	if (!Layers.IsEmpty() || !IsValid(World))
	{
		return Layers.Num();
	}
	UStaticMesh* Shape = LoadObject<UStaticMesh>(nullptr, TEXT("/Engine/BasicShapes/Cube.Cube"));
	for (const FBackdropLayerSpec& Spec : LayerSpecs())
	{
		if (!IsLayerEnabled(Spec.Name))
		{
			continue;
		}
		AActor* Layer = World->SpawnActor<AActor>(FVector(0.0, Spec.Depth, 0.0), FRotator::ZeroRotator);
		if (!IsValid(Layer))
		{
			continue;
		}
		UStaticMeshComponent* Panel = NewObject<UStaticMeshComponent>(Layer, TEXT("BackdropPanel"));
		if (IsValid(Shape))
		{
			Panel->SetStaticMesh(Shape);
		}
		Panel->SetCollisionEnabled(ECollisionEnabled::NoCollision);
		Panel->SetGenerateOverlapEvents(false);
		ArtSlot::SetFlatUnlit(Panel, Layer, BackdropStandInColor(Spec.Name));
		const float Unit = UmbrellaBackdropConst::EngineCubeSize;
		Panel->SetRelativeScale3D(FVector(UmbrellaBackdropConst::PanelWidth / Unit, UmbrellaBackdropConst::PanelThickness, UmbrellaBackdropConst::PanelHeight / Unit));
		Layer->SetRootComponent(Panel);
		Panel->RegisterComponent();
		Layer->SetActorLocation(FVector(0.0, Spec.Depth, 0.0));
		Layers.Add(Layer);
		BuiltSpecs.Add(Spec);
		// Art slot: the layer's picture when its asset exists; the stand-in panel otherwise.
		ApplyLayerArt(Layers.Num() - 1, nullptr);
	}
	return Layers.Num();
}

FString UUmbrellaBackdropSubsystem::LayerVisualId(FName LayerName)
{
	return FString::Printf(TEXT("bg-layer:%s"), *LayerName.ToString());
}

EArtSlotDraw UUmbrellaBackdropSubsystem::ApplyLayerArt(int32 Index, UTexture2D* Texture)
{
	if (!Layers.IsValidIndex(Index) || !IsValid(Layers[Index]))
	{
		return EArtSlotDraw::NoTexture;
	}
	UStaticMeshComponent* Panel = Cast<UStaticMeshComponent>(Layers[Index]->GetRootComponent());
	const FString Visual = LayerVisualId(BuiltSpecs[Index].Name);
	const FArtSlotRow* Row = ArtSlot::Find(*Visual);
	if (!Panel || !Row)
	{
		return EArtSlotDraw::NoTexture;
	}
	const float Unit = UmbrellaBackdropConst::EngineCubeSize;
	const FVector Box(UmbrellaBackdropConst::PanelWidth / Unit, UmbrellaBackdropConst::PanelThickness, UmbrellaBackdropConst::PanelHeight / Unit);
	return ArtSlot::Apply(Panel, Texture ? Texture : ArtSlot::LoadTexture(*Row), *Row, Box);
}

bool UUmbrellaBackdropSubsystem::IsLayerDrawnWithArt(int32 Index) const
{
	return Layers.IsValidIndex(Index) && IsValid(Layers[Index]) && ArtSlot::HasArt(Cast<UStaticMeshComponent>(Layers[Index]->GetRootComponent()));
}

FBox2D UUmbrellaBackdropSubsystem::LayerFootprint(float CameraX, float Parallax)
{
	const float X = LayerXForCamera(CameraX, Parallax);
	const float HalfWidth = UmbrellaBackdropConst::PanelWidth * 0.5f;
	const float HalfHeight = UmbrellaBackdropConst::PanelHeight * 0.5f;
	return FBox2D(FVector2D(X - HalfWidth, -HalfHeight), FVector2D(X + HalfWidth, HalfHeight));
}

float UUmbrellaBackdropSubsystem::StageCameraX(int32 Slot)
{
	const int32 Count = GetDefault<UUmbrellaTuning>()->Field.RouteSlotCount;
	const float Start = LevelCatalogue::SlotStartX(Slot);
	const float End = Slot + 1 < Count ? LevelCatalogue::SlotStartX(Slot + 1) : LevelCatalogue::RouteLength();
	return (Start + End) * 0.5f;
}

bool UUmbrellaBackdropSubsystem::IsRouteStageCovered(int32 Slot) const
{
	const FArenaCameraTuning& Camera = GetDefault<UUmbrellaTuning>()->ArenaCamera;
	const float CameraX = StageCameraX(Slot);
	const float ViewMinX = CameraX - Camera.ArenaWidth * 0.5f;
	const float ViewMaxX = CameraX + Camera.ArenaWidth * 0.5f;
	TArray<FBox2D> Usable;
	for (int32 Index = 0; Index < Layers.Num() && Index < BuiltSpecs.Num(); ++Index)
	{
		const FBox2D Box = LayerFootprint(CameraX, BuiltSpecs[Index].Parallax);
		if (IsValid(Layers[Index]) && Box.Min.Y <= 0.0 && Box.Max.Y >= Camera.ArenaHeight)
		{
			Usable.Add(Box);
		}
	}
	Usable.Sort([](const FBox2D& A, const FBox2D& B) { return A.Min.X < B.Min.X; });
	double Reach = ViewMinX;
	for (const FBox2D& Box : Usable)
	{
		if (Box.Min.X > Reach)
		{
			break;
		}
		Reach = FMath::Max(Reach, Box.Max.X);
	}
	return Reach >= ViewMaxX;
}

int32 UUmbrellaBackdropSubsystem::CountCoveredStages() const
{
	int32 Covered = 0;
	for (int32 Slot = 0; Slot < GetDefault<UUmbrellaTuning>()->Field.RouteSlotCount; ++Slot)
	{
		Covered += IsRouteStageCovered(Slot) ? 1 : 0;
	}
	return Covered;
}

void UUmbrellaBackdropSubsystem::ScrollTo(float CameraX)
{
	for (int32 Index = 0; Index < Layers.Num(); ++Index)
	{
		if (IsValid(Layers[Index]))
		{
			FVector Location = Layers[Index]->GetActorLocation();
			Location.X = LayerXForCamera(CameraX, BuiltSpecs[Index].Parallax);
			Layers[Index]->SetActorLocation(Location);
		}
	}
}

void UUmbrellaBackdropSubsystem::Tick(float DeltaTime)
{
	const UWorld* World = GetWorld();
	const APlayerController* Controller = IsValid(World) ? World->GetFirstPlayerController() : nullptr;
	if (IsValid(Controller) && IsValid(Controller->PlayerCameraManager) && !Layers.IsEmpty())
	{
		ScrollTo(static_cast<float>(Controller->PlayerCameraManager->GetCameraLocation().X));
	}
	// Every tick, not once: the Keeper handoff rebuilds the arena's planes (BuildPlaceholders makes new components), and
	// a one-shot hide left them showing as a dark rectangle behind the faded end picture (visual_qa keeper, dcs-r1).
	HideArenaStandIns();
}

TStatId UUmbrellaBackdropSubsystem::GetStatId() const
{
	RETURN_QUICK_DECLARE_CYCLE_STAT(UUmbrellaBackdropSubsystem, STATGROUP_Tickables);
}
