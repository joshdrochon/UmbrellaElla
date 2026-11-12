#include "Feedback/Background/UmbrellaBackdropSubsystem.h"
#include "Components/StaticMeshComponent.h"
#include "Core/UmbrellaDrawOrder.h"
#include "Engine/StaticMesh.h"
#include "Engine/World.h"
#include "GameFramework/Actor.h"
#include "Harness/UmbrellaFeatureFlags.h"

TArray<float> UUmbrellaBackdropSubsystem::LayerDepths()
{
	return { UmbrellaDrawOrder::BackgroundFarY, UmbrellaDrawOrder::BackgroundNearY };
}

void UUmbrellaBackdropSubsystem::PostInitialize()
{
	Super::PostInitialize();
	BuildLayers();
}

int32 UUmbrellaBackdropSubsystem::BuildLayers()
{
	UWorld* World = GetWorld();
	if (!Layers.IsEmpty() || !IsValid(World) || !IsFeatureEnabled(EFeatureId::BG_05))
	{
		return Layers.Num();
	}
	UStaticMesh* Shape = LoadObject<UStaticMesh>(nullptr, TEXT("/Engine/BasicShapes/Cube.Cube"));
	for (const float Depth : LayerDepths())
	{
		AActor* Layer = World->SpawnActor<AActor>(FVector(0.0, Depth, 0.0), FRotator::ZeroRotator);
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
		Layer->SetActorLocation(FVector(0.0, Depth, 0.0));
		Layers.Add(Layer);
	}
	return Layers.Num();
}
