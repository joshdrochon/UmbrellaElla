#pragma once

#include "CoreMinimal.h"
#include "UmbrellaFlightTuning.generated.h"

/** Every number of the Umbrella module: default, units and clamps (lane a). End a shipped default with // bake: <feature ID>.<param>.
 *  The absorb numbers are read by the Absorb receiver (health lane): GetDefault<UUmbrellaTuning>()->UmbrellaFlight.AbsorbRange. */
USTRUCT()
struct UMBRELLAELLA_API FUmbrellaFlightTuning
{
	GENERATED_BODY()

	/** Lift multiplier at zero active health (lift = min + (1 - min) * active/capacity). */
	UPROPERTY(Config, EditAnywhere, Category = "Umbrella", meta = (ClampMin = "0", ClampMax = "1"))
	float MinLift = 0.3f; // bake: SURV-05.min_lift

	/** Hits in one active life (a full health hand), used when PlayerHealthChanged does not carry a capacity. */
	UPROPERTY(Config, EditAnywhere, Category = "Umbrella", meta = (ClampMin = "1"))
	float DefaultLifeCapacityHits = 3.0f;

	UPROPERTY(Config, EditAnywhere, Category = "Umbrella", meta = (ClampMin = "0"))
	float AbsorbRange = 240.0f; // bake: UMB-05.absorb_range

	/** Full cone angle, degrees. */
	UPROPERTY(Config, EditAnywhere, Category = "Umbrella", meta = (ClampMin = "0", ClampMax = "360"))
	float AbsorbConeDegrees = 60.0f; // bake: UMB-05.absorb_cone_deg

	UPROPERTY(Config, EditAnywhere, Category = "Umbrella", meta = (ClampMin = "0"))
	float PullSpeed = 700.0f; // bake: UMB-05.pull_speed

	UPROPERTY(Config, EditAnywhere, Category = "Umbrella", meta = (ClampMin = "0"))
	float CaptureDistance = 24.0f; // bake: UMB-05.capture_distance

	UPROPERTY(Config, EditAnywhere, Category = "Umbrella", meta = (ClampMin = "0"))
	float HealPerYellow = 0.5f; // bake: UMB-05.heal_per_yellow

	UPROPERTY(Config, EditAnywhere, Category = "Umbrella", meta = (ClampMin = "0"))
	float HealPerRecoveryRank = 0.3f; // bake: UMB-05.heal_per_recovery_rank
};
