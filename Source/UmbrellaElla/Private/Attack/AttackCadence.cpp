#include "Attack/AttackCadence.h"

int32 AttackCadence::Step(float& Countdown, float DeltaSeconds, float ShotsPerSecond, bool bWantsFire)
{
	Countdown -= DeltaSeconds;
	if (!bWantsFire || ShotsPerSecond <= 0.0f)
	{
		Countdown = FMath::Max(Countdown, 0.0f);
		return 0;
	}
	const float Interval = 1.0f / ShotsPerSecond;
	int32 Shots = 0;
	// A shot is due when the countdown is at or below zero (a small slack absorbs float error at 1/30, 1/60, 1/120 s).
	while (Countdown <= UE_KINDA_SMALL_NUMBER)
	{
		Countdown += Interval;
		++Shots;
	}
	return Shots;
}
