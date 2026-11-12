#pragma once

#include "CoreMinimal.h"
#include "Projectile/UmbrellaShotSpec.h"

struct FKeeperTuning;

/** The five standard enemy types. The three Roadwarden equipment variants share every number. */
enum class EEnemyType : uint8
{
	RoadwardenSundialCaster,
	RoadwardenArmillaryLauncher,
	RoadwardenEscapementRepeater,
	Floodstrider,
	SkyCourier
};

/** Art-only variant. It changes neither mechanics nor tuning. */
enum class EEnemyVariant : uint8
{
	Male,
	Female
};

enum class EEnemyState : uint8
{
	Patrol,
	Aim,
	Recovery,
	Defeated,
	Withdrawn
};

enum class EEnemyCommandType : uint8
{
	FireShot,
	StateChanged,
	Defeated,
	Withdrawn
};

struct UMBRELLAELLA_API FEnemyCommand
{
	EEnemyCommandType Type = EEnemyCommandType::FireShot;
	EEnemyState State = EEnemyState::Patrol;
	EUmbrellaShotKind ShotKind = EUmbrellaShotKind::EnemyRed;
	FVector2D A = FVector2D::ZeroVector;
	FVector2D B = FVector2D::ZeroVector;
	int32 Slot = 0;
};

/** Numbers one enemy type runs on, read from tuning. */
struct UMBRELLAELLA_API FEnemyProfile
{
	float Hp = 0.0f;
	float PatrolSpan = 0.0f;
	float PatrolSpeed = 0.0f;
	float AimSeconds = 0.0f;
	float ShotSpeed = 0.0f;
	float RecoverySeconds = 0.0f;
	float CycleSeconds = 0.0f;
	/** 0 = unlimited (grounded types); the Sky Courier has a finite total. */
	int32 MaxEmissions = 0;
	bool bAirborne = false;
};

/**
 * One standard enemy as plain rules: patrol, stop and aim, one committed shot, recovery, repeat. No world, no UObject.
 * Contact damage is off. At zero HP it stops new and delayed fire. The Sky Courier withdraws after a finite total of
 * single emissions (red and yellow together), without kill XP, and a reset rebuilds every slot.
 */
class UMBRELLAELLA_API FEnemyModel
{
public:
	static FEnemyProfile ProfileFor(EEnemyType Type, const FKeeperTuning& Tuning);

	/** Two red-shooting enemies to one yellow across Count enemies. Indices in Reserved are yellow first (authored catch lanes). */
	static TArray<EUmbrellaShotKind> AssignShotColors(int32 Count, const TArray<int32>& ReservedYellow, int32 RedPerYellow);

	/** Fixed-point Home with a patrol span clamped to the support the enemy stands on (floating ground containment). */
	void Init(EEnemyType InType, const FEnemyProfile& InProfile, EUmbrellaShotKind InColor, const FVector2D& InHome, float SupportMinX, float SupportMaxX);

	/** Back to full HP, full slots, home position (retry). */
	void Reset();

	void Step(float DeltaSeconds, const FVector2D& PlayerPos, const FKeeperTuning& Tuning, TArray<FEnemyCommand>& Out);

	/** Take a player hit while alive. Defeat is reported through Out. */
	void ApplyHit(float Damage, TArray<FEnemyCommand>& Out);

	EEnemyType GetType() const { return Type; }
	EEnemyState GetState() const { return State; }
	EUmbrellaShotKind GetColor() const { return Color; }
	float GetHp() const { return Hp; }
	const FVector2D& GetPosition() const { return Position; }
	int32 GetEmissionsUsed() const { return EmissionsUsed; }
	int32 GetEmissionsLeft() const;
	bool IsAlive() const { return State != EEnemyState::Defeated && State != EEnemyState::Withdrawn; }
	/** True when the enemy was removed by a kill (XP-eligible), false for a Courier withdrawal. */
	bool IsKilled() const { return State == EEnemyState::Defeated; }
	const FEnemyProfile& GetProfile() const { return Profile; }
	/** Fixed right/left reach of the patrol after support clamping. */
	float GetPatrolMinX() const { return PatrolMinX; }
	float GetPatrolMaxX() const { return PatrolMaxX; }

private:
	void Enter(EEnemyState NewState, TArray<FEnemyCommand>& Out);

	EEnemyType Type = EEnemyType::RoadwardenSundialCaster;
	FEnemyProfile Profile;
	EUmbrellaShotKind Color = EUmbrellaShotKind::EnemyRed;
	FVector2D Home = FVector2D::ZeroVector;
	FVector2D Position = FVector2D::ZeroVector;
	float PatrolMinX = 0.0f;
	float PatrolMaxX = 0.0f;
	float PatrolDirection = -1.0f;
	EEnemyState State = EEnemyState::Patrol;
	float Hp = 0.0f;
	float StateTime = 0.0f;
	FVector2D LockedAim = FVector2D(-1.0f, 0.0f);
	bool bAimLocked = false;
	int32 EmissionsUsed = 0;
};
