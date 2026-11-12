#pragma once

#include "CoreMinimal.h"
#include "EnemyTuning.generated.h"

namespace EnemyConst
{
	/** Engine cube edge length in units. */
	static constexpr float CubeSize = 100.0f;
}

/**
 * Every number of the Enemy module (lane enemies): GDD SH1.0 baselines, adjustable, units in world units and seconds.
 * Not a member of UUmbrellaTuning yet (Core is TD-owned, see docs/build/requests/enemies.md): read it as
 * FEnemyTuning() until the member lands. End a shipped default with // bake: <feature ID>.<param>.
 */
USTRUCT()
struct UMBRELLAELLA_API FEnemyTuning
{
	GENERATED_BODY()

	UPROPERTY(EditAnywhere, Category = "Roadwarden")
	float RoadwardenHp = 40.0f; // bake: COM-14.roadwarden_hp

	UPROPERTY(EditAnywhere, Category = "Roadwarden")
	float RoadwardenPatrolSpan = 300.0f;

	UPROPERTY(EditAnywhere, Category = "Roadwarden")
	float RoadwardenPatrolSpeed = 90.0f;

	UPROPERTY(EditAnywhere, Category = "Roadwarden")
	float RoadwardenAimSeconds = 1.0f;

	UPROPERTY(EditAnywhere, Category = "Roadwarden")
	float RoadwardenShotSpeed = 240.0f;

	UPROPERTY(EditAnywhere, Category = "Roadwarden")
	float RoadwardenRecoverySeconds = 1.0f;

	UPROPERTY(EditAnywhere, Category = "Roadwarden")
	float RoadwardenCycleSeconds = 2.5f;

	UPROPERTY(EditAnywhere, Category = "Roadwarden")
	FVector2D RoadwardenTorso = FVector2D(40.0, 80.0);

	UPROPERTY(EditAnywhere, Category = "Floodstrider")
	float FloodstriderHp = 60.0f; // bake: COM-15.floodstrider_hp

	UPROPERTY(EditAnywhere, Category = "Floodstrider")
	float FloodstriderPatrolSpan = 300.0f;

	UPROPERTY(EditAnywhere, Category = "Floodstrider")
	float FloodstriderPatrolSpeed = 60.0f;

	UPROPERTY(EditAnywhere, Category = "Floodstrider")
	float FloodstriderAimSeconds = 1.1f;

	UPROPERTY(EditAnywhere, Category = "Floodstrider")
	float FloodstriderShotSpeed = 220.0f;

	UPROPERTY(EditAnywhere, Category = "Floodstrider")
	float FloodstriderRecoverySeconds = 1.0f;

	UPROPERTY(EditAnywhere, Category = "Floodstrider")
	float FloodstriderCycleSeconds = 3.0f;

	UPROPERTY(EditAnywhere, Category = "Floodstrider")
	FVector2D FloodstriderTorso = FVector2D(40.0, 80.0);

	/** Adjustable starting example, not a fixed height (a short stilt is allowed). */
	UPROPERTY(EditAnywhere, Category = "Floodstrider")
	float FloodstriderStiltHeight = 160.0f;

	UPROPERTY(EditAnywhere, Category = "SkyCourier")
	float CourierHp = 40.0f; // bake: COM-16.courier_hp

	UPROPERTY(EditAnywhere, Category = "SkyCourier")
	float CourierPatrolSpan = 400.0f;

	UPROPERTY(EditAnywhere, Category = "SkyCourier")
	float CourierPatrolSpeed = 100.0f;

	UPROPERTY(EditAnywhere, Category = "SkyCourier")
	float CourierAimSeconds = 1.1f;

	UPROPERTY(EditAnywhere, Category = "SkyCourier")
	float CourierShotSpeed = 180.0f;

	UPROPERTY(EditAnywhere, Category = "SkyCourier")
	float CourierRecoverySeconds = 1.0f;

	UPROPERTY(EditAnywhere, Category = "SkyCourier")
	float CourierCycleSeconds = 2.3f;

	UPROPERTY(EditAnywhere, Category = "SkyCourier")
	FVector2D CourierBody = FVector2D(48.0, 88.0);

	/** Single emissions in total across red and yellow, stable slots 0..N-1. */
	UPROPERTY(EditAnywhere, Category = "SkyCourier")
	int32 CourierEmissionSlots = 8;

	/** Shared by all enemies (adjustable prototype values). */
	UPROPERTY(EditAnywhere, Category = "Shot")
	float IncomingDamage = 1.0f;

	UPROPERTY(EditAnywhere, Category = "Shot")
	float ShotRadius = 8.0f;

	UPROPERTY(EditAnywhere, Category = "Shot")
	float ShotRange = 1000.0f;

	/** Level-wide placement target: this many red shooters per yellow shooter. */
	UPROPERTY(EditAnywhere, Category = "Placement")
	int32 RedPerYellow = 2;

	/** Chunk limits (pressure contract): enemies of one type in an introduction, kinds in a mixed chunk. */
	UPROPERTY(EditAnywhere, Category = "Pressure")
	int32 MaxMixedEnemyKinds = 2;

	UPROPERTY(EditAnywhere, Category = "Pressure")
	int32 MaxTimingDemandsInCrossing = 1;

	/** Minimum clear distance between a spawn and Ella. */
	UPROPERTY(EditAnywhere, Category = "Pressure")
	float MinSpawnDistanceFromPlayer = 200.0f;

	/** Half thickness of the hit box and placeholder depth scale (Y is depth; play is in X/Z). */
	UPROPERTY(EditAnywhere, Category = "Placeholder")
	float DepthHalfExtent = 50.0f;

	UPROPERTY(EditAnywhere, Category = "Placeholder")
	float PlaceholderDepthScale = 0.1f;
};
