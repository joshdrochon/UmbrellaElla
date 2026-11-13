#pragma once

#include "CoreMinimal.h"

class AEllaCharacter;
class ABrokenMillRoom;
class UWorld;

/**
 * The scripted playtest run behind -SmokePlaytest (lane playtest). It drives Ella through the measured scenarios with the
 * Motor, Health and Attack components of the live game and logs one PLAYTEST_* line per scenario for
 * tools/build/playtest_check.py. Plain rule functions below are the testable part; the scenarios need a running world.
 */
class UMBRELLAELLA_API FPlaytestRun
{
public:
	/** Hold time of the HAZ run in real seconds (Broken Mill room, natural attempts, no aids). */
	static constexpr float HazRunSeconds = 25.0f;
	/** Extra wait past the hook grace for the synchronous scenarios and the flow check, seconds. */
	static constexpr float PlaytestSetupGraceSeconds = 10.0f;
	/** Fixed step of the synchronous scenarios, seconds. */
	static constexpr float StepSeconds = 1.0f / 60.0f;
	/** Length of one CAM measurement, seconds. */
	static constexpr float CamSeconds = 2.0f;
	/** A run counts as boring (no useful action) when idle share of the HAZ run is above this. */
	static constexpr float BoringIdleShare = 0.5f;
	/** Drawn-width tolerance, world units. */
	static constexpr float DrawnWidthTolerance = 4.0f;
	/** World X offset of the scratch room, far from the level. */
	static constexpr double ScratchRoomX = 60000.0;

	/** Vertical displacement envelope [Min, Max] over Seconds from the motor tuning: fall and rise speed, plus the trim share. */
	static void VerticalEnvelope(float Seconds, float& OutMin, float& OutMax);

	/** Share of Seconds spent with no useful action. 1 when Seconds is not positive. */
	static float IdleShare(float IdleSeconds, float Seconds);

	/** Format the key=value tail of a line: PLAYTEST_<Key> then the pairs. */
	static FString FormatLine(const TCHAR* Key, const TArray<TPair<FString, FString>>& Pairs);

	/** Run the synchronous scenarios (CAM-04, CAM-07, FLOW-25, FLOW-28) and start the HAZ run. Returns false when Ella is missing. */
	bool Begin(UWorld* World);

	/** Advance the real-time HAZ run. Returns true once it has logged its line. */
	bool Tick(float DeltaSeconds);

	bool IsDone() const { return bDone; }

private:
	void MeasureCam04(AEllaCharacter* Ella);
	void MeasureCam07(AEllaCharacter* Ella);
	void MeasureFlow25();
	void MeasureFlow28(AEllaCharacter* Ella);
	void FinishHaz();

	TWeakObjectPtr<UWorld> WorldPtr;
	TWeakObjectPtr<AEllaCharacter> EllaPtr;
	TWeakObjectPtr<ABrokenMillRoom> Room;
	float HazElapsed = 0.0f;
	float IdleSeconds = 0.0f;
	float DamageTaken = 0.0f;
	float HealthAtStart = 0.0f;
	float StartGuardHp = 0.0f;
	FVector EllaHome = FVector::ZeroVector;
	bool bDone = false;
};
