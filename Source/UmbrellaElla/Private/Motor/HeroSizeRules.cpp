#include "Motor/HeroSizeRules.h"

#include "Motor/MotorTuning.h"

float HeroSizeRules::ClampedHeroSize(const FMotorTuning& Tuning)
{
	return FMath::Clamp(Tuning.HeroSize, Tuning.HeroSizeMin, Tuning.HeroSizeMax);
}

float HeroSizeRules::ClampedHitboxScale(const FMotorTuning& Tuning)
{
	return FMath::Clamp(Tuning.HitboxScale, Tuning.HitboxScaleMin, Tuning.HitboxScaleMax);
}

float HeroSizeRules::ActorScale(const FMotorTuning& Tuning)
{
	return Tuning.ActorScaleAtReference * ClampedHeroSize(Tuning);
}

FVector HeroSizeRules::MuzzleOffset(const FVector& ReferenceOffset, const FMotorTuning& Tuning)
{
	return ReferenceOffset * ClampedHeroSize(Tuning);
}
