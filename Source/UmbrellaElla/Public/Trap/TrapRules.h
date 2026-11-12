#pragma once

#include "CoreMinimal.h"
#include "Enemy/EnemyTypes.h"
#include "TrapRules.generated.h"

struct FEnemyTuning;
struct FTrapTuning;

UENUM()
enum class ETrapKind : uint8
{
	AirMill,
	TimedShutter,
	HostileBellows,
	RoofTeeth
};

/** Where a timed trap is in its cycle. */
UENUM()
enum class ETrapPhase : uint8
{
	Warning,
	Active,
	Recovery
};

/** Warning, active, recovery lengths of one timed trap. */
struct UMBRELLAELLA_API FTrapCycle
{
	float WarningSeconds = 0.0f;
	float ActiveSeconds = 0.0f;
	float RecoverySeconds = 0.0f;

	float GetCycleSeconds() const;

	/** Phase at Time seconds into the (looping) cycle. */
	ETrapPhase PhaseAt(float Time) const;
};

/** Per-victim post-hit protection: a persistent overlap deals damage once per window, never per frame. */
struct UMBRELLAELLA_API FContactGate
{
	TMap<FName, float> Remaining;

	void Advance(float DeltaTime);

	/** Damage dealt now: Damage, or 0 while the victim is protected. Starts the protection when it deals damage. */
	float ConsumeHit(FName Victim, float Damage, float ProtectionSeconds);
};

/** Plain trap rules (tests call these). */
struct UMBRELLAELLA_API FTrapRules
{
	static FTrapCycle MakeCycle(ETrapKind Kind, const FTrapTuning& Tuning);

	/** True only in the phase that hurts: shutter and bellows when Active; mill and teeth always (static or spinning). */
	static bool IsPhaseDamaging(ETrapKind Kind, ETrapPhase Phase);

	/** The whole swept disk is blocked, not just the blade tips. */
	static bool IsInsideSweptDisk(const FVector& Point, const FVector& Centre, float Radius);

	/** Blade angle in degrees at Time seconds. */
	static float BladeAngle(float Time, float DegreesPerSecond);

	/** Gust push in X/Z toward safe catch space (down and left), bounded by PushSpeed. */
	static FVector BellowsPush(float PushSpeed);

	static FName KindName(ETrapKind Kind);
};

/** What breaks the pressure contract. */
UENUM()
enum class EPressureViolation : uint8
{
	TooManyProblemsEarly,
	TooManyTimingDemands,
	IntroductionNotSingleEnemy,
	MixedChunkTooManyKinds,
	UntaughtEnemy,
	SpawnOnPlayer,
	AttackFromOffscreen,
	AttackFromClearedNeighbor,
	FireSealsEscape
};

UENUM()
enum class EPressureStage : uint8
{
	Early,
	Later
};

struct UMBRELLAELLA_API FPressureEnemy
{
	EEnemyType Type = EEnemyType::Roadwarden;
	FVector Location = FVector::ZeroVector;
	bool bOnscreen = true;
	bool bFromClearedNeighbor = false;
};

/** One chunk as the contract sees it. */
struct UMBRELLAELLA_API FPressureChunk
{
	EPressureStage Stage = EPressureStage::Later;
	bool bIsIntroduction = false;
	TArray<FPressureEnemy> Enemies;
	int32 TrapCount = 0;
	/** Threatening timing demands occupying the mandatory crossing (an enemy cycle or a trap cycle each count one). */
	int32 TimingDemandsInCrossing = 0;
	TArray<EEnemyType> TaughtTypes;
	FVector PlayerLocation = FVector::ZeroVector;
	bool bFireSealsEscape = false;
};

/** The pressure contract: retime or reject the chunk, never freeze visible geometry. Empty result = chunk passes. */
struct UMBRELLAELLA_API FPressureContract
{
	static TArray<EPressureViolation> Evaluate(const FPressureChunk& Chunk, const FEnemyTuning& Tuning);
};
