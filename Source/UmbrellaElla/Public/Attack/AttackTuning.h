#pragma once

#include "CoreMinimal.h"
#include "AttackTuning.generated.h"

/** Every number of the Attack module: default, units and clamps (lane a). Units: GDD world units = Unreal cm. End a shipped default with // bake: <feature ID>.<param>. */
USTRUCT()
struct UMBRELLAELLA_API FAttackTuning
{
	GENERATED_BODY()

	/** Small Blasts cadence, shots/s. */
	UPROPERTY(Config, EditAnywhere, Category = "Attack", meta = (ClampMin = "0.1"))
	float SmallShotsPerSecond = 5.0f; // bake: COM-06.shots_per_s

	UPROPERTY(Config, EditAnywhere, Category = "Attack", meta = (ClampMin = "0"))
	float SmallDamage = 10.0f; // bake: COM-06.damage

	UPROPERTY(Config, EditAnywhere, Category = "Attack", meta = (ClampMin = "1"))
	float SmallSpeed = 700.0f; // bake: COM-06.speed

	UPROPERTY(Config, EditAnywhere, Category = "Attack", meta = (ClampMin = "1"))
	float SmallRange = 1500.0f; // bake: COM-06.range

	/** Player blast collision radius, units (fixed collider data, never read from art). */
	UPROPERTY(Config, EditAnywhere, Category = "Attack", meta = (ClampMin = "0"))
	float BlastRadius = 12.0f;

	/** Fixed muzzle anchor relative to Ella's origin (X right, Z up). Stable: never read from the sprite. */
	UPROPERTY(Config, EditAnywhere, Category = "Attack")
	FVector MuzzleOffset = FVector(60.0, 0.0, 0.0);
};
