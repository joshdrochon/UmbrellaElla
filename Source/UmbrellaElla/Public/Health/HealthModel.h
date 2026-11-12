#pragma once

#include "CoreMinimal.h"

struct FHealthTuning;

namespace HealthConstants
{
	/** CheckpointRetried carries the lives restored in Amount (keeper request). */
	static constexpr int32 RetryLivesAmount = 3;

	/** Health numerics: below this a life counts as empty (float noise from fractional damage). */
	static constexpr float EmptyTolerance = 1.0e-4f;

	/** Face position of III, degrees clockwise from XII. */
	static constexpr float ThreeOClockDegrees = 90.0f;

	/** Capacity (hits) and lives each stop at 11 (Director's Cut tracks). */
	static constexpr int32 MaxTrackValue = 11;

	/** Shot priority of the absorb: a catch is decided before damage. */
	static constexpr int32 AbsorbShotPriority = 100;
}

/** Plain health numbers: active life, reserves, progress toward restoring a spent reserve. No UObject, tests call it directly. */
struct UMBRELLAELLA_API FHealthState
{
	/** Health of one full life (units: health). */
	float Capacity = 3.0f;

	/** Most lives the player can hold. */
	int32 MaxLives = 3;

	/** Lives left including the active one. 0 means defeated. */
	int32 Lives = 3;

	/** Health left in the active life, 0..Capacity. */
	float Active = 3.0f;

	/** Healing stored toward the next restored reserve, 0..Capacity (only grows while Active is full). */
	float ReserveProgress = 0.0f;

	bool IsDefeated() const { return Lives <= 0; }
};

struct FHealthDamageOutcome
{
	int32 LivesLost = 0;
	bool bDefeatedNow = false;
};

struct FHealthHealOutcome
{
	float ActiveGained = 0.0f;
	int32 ReservesRestored = 0;

	/** Nothing changed: full health, all lives full (a catch, not healing), or defeated. */
	bool bNothingChanged = false;
};

/** Plain rule functions of the health model (damage scale, overflow, healing, lift). */
namespace HealthRules
{
	/** A fresh state: full active life at the given capacity and lives. */
	UMBRELLAELLA_API FHealthState MakeFull(float Capacity, int32 MaxLives);

	/** Damage once, after defense: Raw x (1 - reduction). Rank is clamped to 0..MaxDefenseRank. */
	UMBRELLAELLA_API float ScaleDamage(float Raw, int32 DefenseRank, const FHealthTuning& Tuning);

	/** Apply already-scaled damage. Overflow carries into the next life's full capacity until used up or final defeat. */
	UMBRELLAELLA_API FHealthDamageOutcome ApplyDamage(FHealthState& State, float Damage);

	/** Health of one absorbed yellow: HealPerYellow + HealPerRecoveryRank x rank. */
	UMBRELLAELLA_API float HealAmount(int32 RecoveryRank, const FHealthTuning& Tuning);

	/** Heal the active life first, then fill reserve progress; one reserve per Capacity of progress, up to MaxLives. */
	UMBRELLAELLA_API FHealthHealOutcome ApplyHeal(FHealthState& State, float Amount);

	/** MinLift + (1 - MinLift) x clamp(Active / Capacity, 0, 1). Reserve count does not matter. */
	UMBRELLAELLA_API float LiftMultiplier(const FHealthState& State, float MinLift);

	/** Health hand: 90 degrees (III) when full, 0 (XII) when empty. Degrees clockwise from XII. */
	UMBRELLAELLA_API float HealthHandDegrees(const FHealthState& State);
}
