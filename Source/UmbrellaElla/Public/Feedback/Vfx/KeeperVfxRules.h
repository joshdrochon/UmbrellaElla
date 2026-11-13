#pragma once

#include "CoreMinimal.h"
#include "Encounter/KeeperFightModel.h"

/** What the Keeper effects need to know about the fight, copied from the model's public readers each step. */
struct FKeeperVfxSnapshot
{
	bool bFightActive = false;
	EKeeperPhysical Physical = EKeeperPhysical::None;
	EKeeperStage Stage = EKeeperStage::Idle;
	bool bClockOpen = false;
	bool bEyeExposed = false;
	bool bSlowed = false;
	bool bStunned = false;
	bool bBlackedOut = false;
	bool bDeparting = false;
};

/** Where a Keeper effect is placed. Every anchor is read from the model, so effect, head and target stay registered. */
enum class EKeeperVfxAnchor : uint8
{
	Body,
	Head,
	Claw,
	GustFront,
	Clock,
	Screen
};

/** One change the effects must make: start a one-shot or a held loop, or stop a held loop. */
struct FKeeperVfxCue
{
	FName Key;
	bool bStart = true;
	EKeeperVfxAnchor Anchor = EKeeperVfxAnchor::Body;
};

/** Plain rules: which Keeper effect belongs to which state change. The model is the authority; nothing here keeps time. */
namespace KeeperVfxRules
{
	UMBRELLAELLA_API FKeeperVfxSnapshot Read(const FKeeperFightModel& Model, bool bFightActive, bool bDeparting);

	/** Effect keys of a physical attack, or NAME_None. */
	UMBRELLAELLA_API FName WarningKey(EKeeperPhysical Physical);
	UMBRELLAELLA_API FName StrikeKey(EKeeperPhysical Physical);
	UMBRELLAELLA_API FName RecoveryKey(EKeeperPhysical Physical);

	/** The physical attack a telegraph event names (its Detail), or None. */
	UMBRELLAELLA_API EKeeperPhysical PhysicalForAttack(FName AttackName);

	UMBRELLAELLA_API EKeeperVfxAnchor AnchorFor(EKeeperPhysical Physical);

	/** The cues for one step. A stage that deals no damage (pause, return, recovery) never starts a strike effect. */
	UMBRELLAELLA_API void Diff(const FKeeperVfxSnapshot& Before, const FKeeperVfxSnapshot& After, TArray<FKeeperVfxCue>& Out);

	/** Every held (looping) Keeper effect: what a reset must stop. */
	UMBRELLAELLA_API TArray<FName> HeldKeys();

	/** True when a clock double-beat shot starts a new beat (not another shot of the same beat). */
	UMBRELLAELLA_API bool IsNewBeat(float SecondsSinceLastBeatShot, float ShotSpacingSeconds, float RepeatWaitSeconds);
}
