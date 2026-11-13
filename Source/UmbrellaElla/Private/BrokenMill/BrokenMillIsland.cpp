#include "BrokenMill/BrokenMillIsland.h"
#include "BrokenMill/BrokenMillPlaceholder.h"
#include "Components/BoxComponent.h"
#include "Components/StaticMeshComponent.h"
#include "Core/UmbrellaCollision.h"

ABrokenMillIsland::ABrokenMillIsland()
{
	Box = CreateDefaultSubobject<UBoxComponent>(TEXT("Box"));
	RootComponent = Box;
	Box->SetCollisionProfileName(TEXT("BlockAllDynamic"));
	Box->SetCollisionResponseToChannel(UmbrellaCollision::PlayerShot, ECR_Block);
	Box->SetCollisionResponseToChannel(UmbrellaCollision::EnemyShot, ECR_Block);
	Visual = CreateDefaultSubobject<UStaticMeshComponent>(TEXT("Visual"));
	Visual->SetupAttachment(Box);
	Visual->SetCollisionEnabled(ECollisionEnabled::NoCollision);
}

void ABrokenMillIsland::ConfigureBox(const FVector& HalfExtent, const FLinearColor& Color, float CubeSize, float DepthScale)
{
	Box->SetBoxExtent(HalfExtent);
	BrokenMillPlaceholder::ApplyCube(Visual, this, FVector2D(HalfExtent.X * 2.0, HalfExtent.Z * 2.0), Color, CubeSize, DepthScale);
}
