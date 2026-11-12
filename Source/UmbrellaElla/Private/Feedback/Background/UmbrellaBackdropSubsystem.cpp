#include "Feedback/Background/UmbrellaBackdropSubsystem.h"
#include "Components/StaticMeshComponent.h"
#include "Core/UmbrellaDrawOrder.h"
#include "Engine/StaticMesh.h"
#include "Engine/World.h"
#include "GameFramework/Actor.h"
#include "GameFramework/PlayerController.h"
#include "Camera/PlayerCameraManager.h"
#include "Harness/UmbrellaFeatureFlags.h"

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

float UUmbrellaBackdropSubsystem::LoopOffset(float CameraX, float Parallax)
{
	const float Period = UmbrellaBackdropConst::LoopPeriod;
	const float Raw = FMath::Fmod(CameraX * Parallax, Period);
	return Raw < 0.0f ? Raw + Period : Raw;
}

float UUmbrellaBackdropSubsystem::LayerXForCamera(float CameraX, float Parallax)
{
	return CameraX - LoopOffset(CameraX, Parallax);
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
		const float Unit = UmbrellaBackdropConst::EngineCubeSize;
		Panel->SetRelativeScale3D(FVector(UmbrellaBackdropConst::PanelWidth / Unit, UmbrellaBackdropConst::PanelThickness, UmbrellaBackdropConst::PanelHeight / Unit));
		Layer->SetRootComponent(Panel);
		Panel->RegisterComponent();
		Layer->SetActorLocation(FVector(0.0, Spec.Depth, 0.0));
		Layers.Add(Layer);
		BuiltSpecs.Add(Spec);
	}
	return Layers.Num();
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
}

TStatId UUmbrellaBackdropSubsystem::GetStatId() const
{
	RETURN_QUICK_DECLARE_CYCLE_STAT(UUmbrellaBackdropSubsystem, STATGROUP_Tickables);
}
