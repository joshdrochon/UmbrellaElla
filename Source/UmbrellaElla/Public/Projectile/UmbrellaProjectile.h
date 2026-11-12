#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "Projectile/UmbrellaShotSpec.h"
#include "UmbrellaProjectile.generated.h"

/** Projectile Service actor (lane c): spawn, motion, collision report, lifetime. */
UCLASS()
class UMBRELLAELLA_API AUmbrellaProjectile : public AActor
{
	GENERATED_BODY()

public:
	AUmbrellaProjectile();

	/** The one way to fire a shot. Returns nullptr when the world refuses the spawn. */
	static AUmbrellaProjectile* Fire(UWorld* World, const FUmbrellaShotSpec& Spec);

	const FUmbrellaShotSpec& GetSpec() const { return Spec; }

private:
	UPROPERTY()
	FUmbrellaShotSpec Spec;
};
