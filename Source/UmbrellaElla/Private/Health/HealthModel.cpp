#include "Health/HealthModel.h"
#include "Health/HealthTuning.h"

FHealthState HealthRules::MakeFull(float Capacity, int32 MaxLives)
{
	FHealthState State;
	State.Capacity = FMath::Max(Capacity, 1.0f);
	State.MaxLives = FMath::Max(MaxLives, 1);
	State.Lives = State.MaxLives;
	State.Active = State.Capacity;
	State.ReserveProgress = 0.0f;
	return State;
}

float HealthRules::ScaleDamage(float Raw, int32 DefenseRank, const FHealthTuning& Tuning)
{
	const int32 Rank = FMath::Clamp(DefenseRank, 0, Tuning.MaxDefenseRank);
	return FMath::Max(Raw, 0.0f) * (1.0f - Tuning.DefenseReductionPerRank * static_cast<float>(Rank));
}

FHealthDamageOutcome HealthRules::ApplyDamage(FHealthState& State, float Damage)
{
	FHealthDamageOutcome Outcome;
	if (State.IsDefeated())
	{
		return Outcome;
	}
	float Remaining = FMath::Max(Damage, 0.0f);
	while (Remaining > 0.0f)
	{
		if (State.Active - Remaining > HealthConstants::EmptyTolerance)
		{
			State.Active -= Remaining;
			break;
		}
		Remaining = FMath::Max(Remaining - State.Active, 0.0f);
		State.Active = 0.0f;
		if (State.Lives > 1)
		{
			State.Lives -= 1;
			State.Active = State.Capacity;
			State.ReserveProgress = 0.0f;
			Outcome.LivesLost += 1;
		}
		else
		{
			State.Lives = 0;
			State.ReserveProgress = 0.0f;
			Outcome.bDefeatedNow = true;
			break;
		}
	}
	return Outcome;
}

float HealthRules::HealAmount(int32 RecoveryRank, const FHealthTuning& Tuning)
{
	const int32 Rank = FMath::Clamp(RecoveryRank, 0, Tuning.MaxRecoveryRank);
	return Tuning.HealPerYellow + Tuning.HealPerRecoveryRank * static_cast<float>(Rank);
}

FHealthHealOutcome HealthRules::ApplyHeal(FHealthState& State, float Amount)
{
	FHealthHealOutcome Outcome;
	if (State.IsDefeated() || Amount <= 0.0f)
	{
		Outcome.bNothingChanged = true;
		return Outcome;
	}
	float Remaining = Amount;
	const float Room = FMath::Max(State.Capacity - State.Active, 0.0f);
	Outcome.ActiveGained = FMath::Min(Room, Remaining);
	State.Active += Outcome.ActiveGained;
	Remaining -= Outcome.ActiveGained;

	if (State.Active >= State.Capacity - HealthConstants::EmptyTolerance)
	{
		State.Active = State.Capacity;
		while (Remaining > 0.0f && State.Lives < State.MaxLives)
		{
			const float Need = State.Capacity - State.ReserveProgress;
			if (Remaining + HealthConstants::EmptyTolerance < Need)
			{
				State.ReserveProgress += Remaining;
				Remaining = 0.0f;
				Outcome.bNothingChanged = false;
				break;
			}
			Remaining -= Need;
			State.ReserveProgress = 0.0f;
			State.Lives += 1;
			Outcome.ReservesRestored += 1;
		}
		if (State.Lives >= State.MaxLives)
		{
			State.ReserveProgress = 0.0f;
		}
	}
	const bool bProgressed = Outcome.ActiveGained > 0.0f || Outcome.ReservesRestored > 0 || Remaining < Amount;
	Outcome.bNothingChanged = !bProgressed;
	return Outcome;
}

float HealthRules::LiftMultiplier(const FHealthState& State, float MinLift)
{
	const float Fraction = State.Capacity > 0.0f ? FMath::Clamp(State.Active / State.Capacity, 0.0f, 1.0f) : 0.0f;
	return MinLift + (1.0f - MinLift) * Fraction;
}

float HealthRules::HealthHandDegrees(const FHealthState& State)
{
	const float Fraction = State.Capacity > 0.0f ? FMath::Clamp(State.Active / State.Capacity, 0.0f, 1.0f) : 0.0f;
	return HealthConstants::ThreeOClockDegrees * Fraction;
}
