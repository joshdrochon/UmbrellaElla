#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "UmbrellaArena.generated.h"

/** The Keeper arena: bounds, play camera (fixed 16:9), Ella start and Keeper anchor (CAM, WIND, HAZ, BG). Flow spawns one if the map has none. Lane e. */
UCLASS()
class UMBRELLAELLA_API AUmbrellaArena : public AActor
{
	GENERATED_BODY()

public:
	FVector GetPlayerStartLocation() const { return FVector::ZeroVector; }
	FVector GetKeeperAnchorLocation() const { return FVector::ZeroVector; }
};
