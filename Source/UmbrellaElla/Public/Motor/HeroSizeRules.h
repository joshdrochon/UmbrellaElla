#pragma once

#include "CoreMinimal.h"

struct FMotorTuning;

/** Plain HeroSize rules: clamped size, applied actor scale, hitbox scale. Muzzle offset follows HeroSize; blast radius does not (radius stays 6). */
namespace HeroSizeRules
{
	UMBRELLAELLA_API float ClampedHeroSize(const FMotorTuning& Tuning);

	UMBRELLAELLA_API float ClampedHitboxScale(const FMotorTuning& Tuning);

	/** Uniform actor scale: 0.5 at HeroSize 1. */
	UMBRELLAELLA_API float ActorScale(const FMotorTuning& Tuning);

	/** Muzzle offset from Ella's origin: the reference offset (+44/+6 at HeroSize 1) times HeroSize. */
	UMBRELLAELLA_API FVector MuzzleOffset(const FVector& ReferenceOffset, const FMotorTuning& Tuning);
}
