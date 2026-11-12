#include "Projectile/UmbrellaProjectile.h"
#include "Engine/World.h"

AUmbrellaProjectile::AUmbrellaProjectile()
{
	PrimaryActorTick.bCanEverTick = false;
}

AUmbrellaProjectile* AUmbrellaProjectile::Fire(UWorld* World, const FUmbrellaShotSpec& Spec)
{
	if (!World)
	{
		return nullptr;
	}
	FActorSpawnParameters Params;
	Params.SpawnCollisionHandlingOverride = ESpawnActorCollisionHandlingMethod::AlwaysSpawn;
	AUmbrellaProjectile* Shot = World->SpawnActor<AUmbrellaProjectile>(AUmbrellaProjectile::StaticClass(), FTransform(Spec.Origin), Params);
	if (Shot)
	{
		Shot->Spec = Spec;
	}
	return Shot;
}
