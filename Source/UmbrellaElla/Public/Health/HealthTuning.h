#pragma once

#include "CoreMinimal.h"
#include "HealthTuning.generated.h"

/** Every number of the Health module: default, units and clamps (lane c). End a shipped default with // bake: <feature ID>.<param>. */
USTRUCT()
struct UMBRELLAELLA_API FHealthTuning
{
	GENERATED_BODY()

	/** Health per life, in ordinary hits (one active life holds three one-health hits). */
	UPROPERTY(Config, EditAnywhere, meta = (ClampMin = "1.0", ClampMax = "11.0"))
	float HitsPerLife = 3.0f;

	/** Lives total: the active life plus the reserves. */
	UPROPERTY(Config, EditAnywhere, meta = (ClampMin = "1", ClampMax = "11"))
	int32 MaxLives = 3;

	/** Lift multiplier at zero active health (units: x). */
	UPROPERTY(Config, EditAnywhere, meta = (ClampMin = "0.0", ClampMax = "1.0"))
	float MinLift = 0.3f; // bake: SURV-05.min_lift

	/** Protection after a hit (units: s). */
	UPROPERTY(Config, EditAnywhere, meta = (ClampMin = "0.0", ClampMax = "5.0"))
	float PostHitProtectionSeconds = 0.65f; // bake: SURV-05.post_hit_protection_s

	/** Physical trap hit damage (units: health). */
	UPROPERTY(Config, EditAnywhere, meta = (ClampMin = "0.0"))
	float TrapDamage = 1.0f; // bake: FLOW-33.trap_damage

	/** Former incoming values were divided by this (documentation of the migration; outgoing damage is untouched). */
	UPROPERTY(Config, EditAnywhere, meta = (ClampMin = "1.0"))
	float OldDamageDivisor = 8.0f; // bake: FLOW-33.old_damage_divisor

	/** Healing for one absorbed yellow at recovery rank 0 (units: health). */
	UPROPERTY(Config, EditAnywhere, meta = (ClampMin = "0.0"))
	float HealPerYellow = 0.5f; // bake: UMB-05.heal_per_yellow

	/** Extra healing per recovery rank (units: health). */
	UPROPERTY(Config, EditAnywhere, meta = (ClampMin = "0.0"))
	float HealPerRecoveryRank = 0.3f; // bake: UMB-05.heal_per_recovery_rank

	/** Highest recovery rank (0, I, II, III: no fourth rank). */
	UPROPERTY(Config, EditAnywhere, meta = (ClampMin = "0", ClampMax = "3"))
	int32 MaxRecoveryRank = 3;

	/** Ordinary damage reduction per defense rank (units: fraction; 0 / 10 / 20 / 30 %). */
	UPROPERTY(Config, EditAnywhere, meta = (ClampMin = "0.0", ClampMax = "0.5"))
	float DefenseReductionPerRank = 0.1f;

	/** Highest defense rank. */
	UPROPERTY(Config, EditAnywhere, meta = (ClampMin = "0", ClampMax = "3"))
	int32 MaxDefenseRank = 3;
};
