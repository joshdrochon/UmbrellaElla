#pragma once

#include "CoreMinimal.h"
#include "Enemy/EnemyTypes.h"
#include "Projectile/UmbrellaShotSpec.h"

struct FEnemyTuning;

/** One enemy type's numbers, copied out of FEnemyTuning so rule functions take plain values. */
struct UMBRELLAELLA_API FEnemyProfile
{
	float Hp = 0.0f;
	float PatrolSpan = 0.0f;
	float PatrolSpeed = 0.0f;
	float AimSeconds = 0.0f;
	float ShotSpeed = 0.0f;
	float RecoverySeconds = 0.0f;
	float CycleSeconds = 0.0f;
	float Damage = 0.0f;
	float ShotRadius = 0.0f;
	float Range = 0.0f;
	FVector2D Body = FVector2D::ZeroVector;

	/** Time from the shot release to the next aim start: the longer of the recovery and the rest of the cycle. */
	float GetPostFireSeconds() const;

	float GetShotLifetime() const;
};

/** Pure state machine of one enemy: patrol, stop and aim, one committed shot, recovery. No engine calls. */
struct UMBRELLAELLA_API FEnemyBrain
{
	EEnemyState State = EEnemyState::Patrol;
	float StateTime = 0.0f;
	float PatrolOffset = 0.0f;
	float PatrolDirection = 1.0f;
	float Hp = 0.0f;

	void Reset(const FEnemyProfile& Profile);

	/** Step by DeltaTime. A target in the window starts an aim; the aim always commits to its shot (no retarget). */
	EEnemyBrainEvent Advance(const FEnemyProfile& Profile, float DeltaTime, bool bTargetInWindow, bool bHasEmissionsLeft);

	/** Subtract damage; true-like result is the HP left. At 0 HP the state is Defeated and nothing more fires. */
	float ApplyDamage(float Damage);
};

/** Courier emission slots: stable identities, finite, rebuilt on retry, duplicate callbacks rejected. */
struct UMBRELLAELLA_API FCourierPackets
{
	void Reset(int32 SlotCount);

	/** Take the next unused slot; INDEX_NONE when all are spent. */
	int32 TakeNextSlot();

	int32 GetRemaining() const;
	bool IsExhausted() const;

	/** Records a shot callback serial and returns how many times it has now been seen; a caller acts only on 1. */
	int32 RecordCallback(int32 Serial);

private:
	int32 SlotTotal = 0;
	int32 NextSlot = 0;
	TMap<int32, int32> SeenCallbacks;
};

/** Plain rule functions (tests call these directly). */
struct UMBRELLAELLA_API FEnemyRules
{
	static FEnemyProfile MakeProfile(EEnemyType Type, const FEnemyTuning& Tuning);

	/** Fixed-right fire: the target must be to the left of the enemy, in range, and not above its body. */
	static bool IsTargetInFiringWindow(const FVector& Enemy, const FVector& Target, const FEnemyProfile& Profile);

	/** Straight, non-homing velocity in X/Z from the muzzle to the captured target point. */
	static FVector AimVelocity(const FVector& Muzzle, const FVector& Target, float Speed);

	/** Whole shot spec for one release. */
	static FUmbrellaShotSpec MakeShot(const FEnemyProfile& Profile, EUmbrellaShotKind Kind, const FVector& Muzzle, const FVector& Target, FName SourceId);

	/**
	 * Seeded colour assignment for Count placed enemies: the first Reserved are yellow (early healing and tutorial
	 * lanes), the rest reach the red:yellow target with the same seed giving the same list. Only Red and Yellow come back.
	 */
	static TArray<EUmbrellaShotKind> AssignShotColors(int32 Count, int32 Reserved, int32 RedPerYellow, FRandomStream& Stream);

	/** Only a player blast hurts an enemy; enemy shots pass through. */
	static bool IsDamagingShot(const FUmbrellaShotSpec& Shot);
};
