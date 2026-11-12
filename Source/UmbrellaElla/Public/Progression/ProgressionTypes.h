#pragma once

#include "CoreMinimal.h"
#include "ProgressionTypes.generated.h"

/** Director's Cut stat tracks . Hit capacity and lives cost one point per +1; the seven others cost 1 / 2 / 3. */
UENUM()
enum class EProgressionTrack : uint8
{
	HitCapacity,
	Lives,
	Recovery,
	DamageReduction,
	SuctionRange,
	SuctionCone,
	DamageSmall,
	DamageStreamed,
	DamageTwin,
	DamageNeedle,
	Count UMETA(Hidden)
};

/** The four spells of the unlock schedule . */
UENUM()
enum class EProgressionSpell : uint8
{
	SmallBlasts,
	StreamedBlast,
	TwinStars,
	NeedleSpell,
	Count UMETA(Hidden)
};

/** A level checkpoint keeps XP on a death retry; a boss checkpoint rolls it back . Both are quit/reload targets. */
UENUM()
enum class EProgressionCheckpointKind : uint8
{
	Level,
	Boss
};

/** Where the player stands when browsing the upgrade screen . */
UENUM()
enum class EPurchaseContextKind : uint8
{
	None,
	SafeRefuge,
	BetweenRuns,
	RunStart,
	Checkpoint
};

UENUM()
enum class EProgressionCommit : uint8
{
	Ok,
	InvalidRanks,
	PurchaseNotAllowed,
	RefundNotAllowed,
	RankGateClosed,
	NotEnoughPoints
};

/** The eligible-state half of the purchase context: active, alive and outside a story lock. */
USTRUCT()
struct UMBRELLAELLA_API FPurchaseContext
{
	GENERATED_BODY()

	UPROPERTY()
	EPurchaseContextKind Kind = EPurchaseContextKind::None;

	UPROPERTY()
	bool bAlive = true;

	UPROPERTY()
	bool bStoryLocked = false;
};

/** Earned character data : XP, completed runs, ranks, and the last checkpoint's copy of the same. Level, points and unlocks are derived, so they can never disagree. */
USTRUCT()
struct UMBRELLAELLA_API FProgressionProfile
{
	GENERATED_BODY()

	UPROPERTY(SaveGame)
	int32 Xp = 0;

	UPROPERTY(SaveGame)
	int32 CompletedRuns = 0;

	/** One entry per EProgressionTrack; the rank bought on that track. */
	UPROPERTY(SaveGame)
	TArray<int32> Ranks;

	UPROPERTY(SaveGame)
	bool bCheckpointValid = false;

	UPROPERTY(SaveGame)
	EProgressionCheckpointKind CheckpointKind = EProgressionCheckpointKind::Level;

	UPROPERTY(SaveGame)
	int32 CheckpointXp = 0;

	UPROPERTY(SaveGame)
	TArray<int32> CheckpointRanks;

	bool operator==(const FProgressionProfile& Other) const
	{
		return Xp == Other.Xp && CompletedRuns == Other.CompletedRuns && Ranks == Other.Ranks
			&& bCheckpointValid == Other.bCheckpointValid && CheckpointKind == Other.CheckpointKind
			&& CheckpointXp == Other.CheckpointXp && CheckpointRanks == Other.CheckpointRanks;
	}
};
