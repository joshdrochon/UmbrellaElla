#pragma once

#include "CoreMinimal.h"
#include "ProjectileTuning.generated.h"

/** Every number of the Projectile module: default, units and clamps (lane c). End a shipped default with // bake: <feature ID>.<param>. */
USTRUCT()
struct UMBRELLAELLA_API FProjectileTuning
{
	GENERATED_BODY()

	/** Lifetime when a spec leaves it at zero (units: s). A safety net, not a GDD value. */
	UPROPERTY(Config, EditAnywhere, meta = (ClampMin = "0.1", ClampMax = "30.0"))
	float DefaultLifetimeSeconds = 4.0f;

	/** Radius when a spec leaves it at zero (units: world units). */
	UPROPERTY(Config, EditAnywhere, meta = (ClampMin = "1.0", ClampMax = "200.0"))
	float DefaultRadius = 8.0f;

	/** Radius of the engine sphere mesh the placeholder scales (units: world units; the engine sphere is 100 across). */
	UPROPERTY(Config, EditAnywhere, meta = (ClampMin = "1.0"))
	float PlaceholderMeshRadius = 50.0f;

	/** Placeholder tint of Ella's shots. */
	UPROPERTY(Config, EditAnywhere)
	FLinearColor PlayerColor = FLinearColor(0.3f, 0.8f, 1.0f, 1.0f);

	/** Placeholder tint of red (harmful) enemy shots. */
	UPROPERTY(Config, EditAnywhere)
	FLinearColor RedColor = FLinearColor(0.9f, 0.1f, 0.1f, 1.0f);

	/** Placeholder tint of yellow (absorbable) enemy shots. */
	UPROPERTY(Config, EditAnywhere)
	FLinearColor YellowColor = FLinearColor(1.0f, 0.85f, 0.1f, 1.0f);
};
