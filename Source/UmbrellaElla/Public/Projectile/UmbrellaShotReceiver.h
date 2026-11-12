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
 * The Projectile Service calls it on the hit actor, then on its components, highest priority first.
 * Consumed removes the shot and stops the call chain.
 */
class UMBRELLAELLA_API IUmbrellaShotReceiver
{
	GENERATED_BODY()

public:
	virtual EUmbrellaShotResult ReceiveShot(const FUmbrellaShotSpec& Shot, const FVector& HitLocation) = 0;

	/** Higher goes first. Default 0; Ella's absorb answers at 100 so a catch is decided before damage. */
	virtual int32 GetShotPriority() const { return 0; }
};
