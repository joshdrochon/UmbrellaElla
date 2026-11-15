#pragma once

#include "CoreMinimal.h"
#include "Level/ChunkLayouts.h"
#include "Level/LevelCatalogue.h"

/** What the level director places for a route. Plain data so tests read it without a world. Lane e. */
UENUM()
enum class ELevelPlacementKind : uint8
{
	Floor,
	Solid,
	Wind,
	Refuge,
	Checkpoint,
	Trap,
	Enemy
};

/** True constants of the placeholder layout, as fractions of the arena height or chunk length (art replaces the boxes). */
namespace LevelPlanConst
{
	static constexpr float FloorThicknessFraction = ChunkLayoutConst::FloorTop;
	static constexpr float CheckpointSizeFraction = 0.06f;
	static constexpr float CheckpointStandFraction = 0.1f;
	static constexpr float StandInsetFraction = 0.25f;
	/** Land is this deep in Y around the play plane, so Ella (at EllaY) collides with it. */
	static constexpr float SolidDepth = 100.0f;
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
	bool bYellowShot = false;				// Enemy only: forced by the chunk or the seeded 2:1 assignment
	FVector2D WindDirection = FVector2D::ZeroVector;	// Wind only, unit X/Z
	EWindRole WindRole = EWindRole::Transport;		// Wind only
	bool bBypass = false;					// Wind only: part of the safer bypass
};

namespace LevelPlan
{
	/** Placements for the whole route: per slot the variant's authored land, currents, traps and enemies
	 *  (ChunkLayouts), then refuges with checkpoint markers. Same route, same list. */
	UMBRELLAELLA_API TArray<FLevelPlacement> Build(const FRoute& Route);

	/** A mostly vertical current (|Z| > |X|). The route places none (D-new-no-vertical-wind, Josh 14 Nov). */
	UMBRELLAELLA_API bool IsVerticalWind(const FVector2D& Direction);

	/** Where Ella stands at checkpoint 1..3 (just inside the refuge, on the floor). Checkpoint 0 is the route start:
	 *  there is no refuge before slot 0, so she stands the same inset into slot 0's floor, inside the first camera view (B6). */
	UMBRELLAELLA_API FVector CheckpointStandLocation(int32 Checkpoint);

	/** The checkpoint (0 = none) Ella has reached at X: the last refuge start at or before X. */
	UMBRELLAELLA_API int32 CheckpointReachedAt(float EllaX);

	/** X where the Keeper handoff begins: the last refuge's far end less the vestibule. */
	UMBRELLAELLA_API float KeeperHandoffX();

	/** Bottom-left corner of the Keeper arena for the Director's Cut fight (B5): the arena moves here at the handoff, so
	 *  Ella at the handoff line stands at the arena's own player-start fraction, as in Start Game, and the Keeper anchor
	 *  and fixed camera frame the fight where she is. */
	UMBRELLAELLA_API FVector KeeperArenaOrigin();
}
