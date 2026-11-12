#pragma once

#include "CoreMinimal.h"
#include "Level/LevelCatalogue.h"

/** What the level director places for a route. Plain data so tests read it without a world. Lane e. */
UENUM()
enum class ELevelPlacementKind : uint8
{
	Floor,
	Column,
	Refuge,
	Checkpoint,
	Trap,
	Enemy
};

/** True constants of the placeholder layout, as fractions of the arena height or chunk length (art replaces the boxes). */
namespace LevelPlanConst
{
	static constexpr float FloorThicknessFraction = 0.04f;
	static constexpr float ColumnWidthFraction = 0.08f;
	static constexpr float ColumnHeightFraction = 0.45f;
	static constexpr float MidHeightFraction = 0.5f;
	static constexpr float HighFraction = 0.75f;
	static constexpr float CheckpointSizeFraction = 0.06f;
	static constexpr float TrapSizeFraction = 0.12f;
	static constexpr float EnemySizeFraction = 0.1f;
	static constexpr float StandInsetFraction = 0.25f;
	static constexpr float VariantShiftFraction = 0.15f;
	static constexpr float MechanicSpacingFraction = 0.3f;
	static constexpr float DepthSize = 10.0f;
	static constexpr int64 SeedMask = 0x7fffffffLL;
	static constexpr int32 MaxCheckpoint = 3;
	static constexpr float CubeSize = 100.0f;
}

struct UMBRELLAELLA_API FLevelPlacement
{
	ELevelPlacementKind Kind = ELevelPlacementKind::Floor;
	int32 Slot = 0;					// 0..8, or checkpoint index 1..3 for Refuge/Checkpoint
	EChunkMechanic Mechanic = EChunkMechanic::Column;
	FVector Location = FVector::ZeroVector;	// centre, world units
	FVector Size = FVector::ZeroVector;		// full extents, world units
	bool bYellowShot = false;				// Enemy only, seeded from the route seed
};

namespace LevelPlan
{
	/** Placements for the whole route: floors, refuges with checkpoint markers, one set of mechanic placements per slot. Same route, same list. */
	UMBRELLAELLA_API TArray<FLevelPlacement> Build(const FRoute& Route);

	/** Where Ella stands at checkpoint 1..3 (just inside the refuge, on the floor). */
	UMBRELLAELLA_API FVector CheckpointStandLocation(int32 Checkpoint);

	/** The checkpoint (0 = none) Ella has reached at X: the last refuge start at or before X. */
	UMBRELLAELLA_API int32 CheckpointReachedAt(float EllaX);

	/** X where the Keeper handoff begins: the last refuge's far end less the vestibule. */
	UMBRELLAELLA_API float KeeperHandoffX();
}
