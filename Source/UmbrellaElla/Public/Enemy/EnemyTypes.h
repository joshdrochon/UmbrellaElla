#pragma once

#include "CoreMinimal.h"
#include "EnemyTypes.generated.h"

/** The three regular enemy families (Director's Cut). Lane enemies. */
UENUM()
enum class EEnemyType : uint8
{
	Roadwarden,
	Floodstrider,
	SkyCourier
};

/** Presentation variant only: gender changes neither mechanics nor tuning. */
UENUM()
enum class EEnemyGender : uint8
{
	Male,
	Female
};

/** Roadwarden equipment variant. Cosmetic: no new burst or cadence. */
UENUM()
enum class ERoadwardenEquipment : uint8
{
	SundialCaster,
	ArmillaryLauncher,
	EscapementRepeater
};

/** Art-facing state names (GDD production state coverage). */
UENUM()
enum class EEnemyState : uint8
{
	Patrol,
	Aim,
	Recovery,
	Defeated,
	Withdrawn
};

/** What a brain step asks the actor to do. */
UENUM()
enum class EEnemyBrainEvent : uint8
{
	None,
	ReleaseShot,
	Withdraw
};
