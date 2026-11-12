#pragma once

#include "CoreMinimal.h"
#include "UObject/Interface.h"
#include "UmbrellaShotReceiver.generated.h"

struct FUmbrellaShotSpec;

/** What a receiver did with a shot. */
UENUM()
enum class EUmbrellaShotResult : uint8
{
	Ignored,
	Consumed
};

UINTERFACE(MinimalAPI)
class UUmbrellaShotReceiver : public UInterface
{
	GENERATED_BODY()
};

/**
 * Implemented by anything a shot can hit: Ella's health/absorb components, Keeper parts, enemies.
 * The Projectile Service calls it on the hit actor, then on its components. Consumed removes the shot.
 */
class UMBRELLAELLA_API IUmbrellaShotReceiver
{
	GENERATED_BODY()

public:
	virtual EUmbrellaShotResult ReceiveShot(const FUmbrellaShotSpec& Shot, const FVector& HitLocation) = 0;
};
