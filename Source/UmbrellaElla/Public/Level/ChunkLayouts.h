#pragma once

#include "CoreMinimal.h"
#include "Level/LevelCatalogue.h"

/** What one authored piece of a chunk variant is. */
enum class EChunkPieceKind : uint8
{
	Solid,	// harmless land: roof, bridge, shelf, eave (blocks, never damages)
	Wind,	// a harmless current (AWindCurrent)
	Trap,	// a trap through the enemies lane (mill, shutter, bellows, teeth)
	Enemy	// an enemy through the enemies lane (Warden, Floodstrider, Courier)
};

/** What a wind piece does for the player; FLOW readability draws each role differently. */
enum class EWindRole : uint8
{
	Transport,	// carries onward (mostly right)
	Descent,	// carries down (a catch or descent column)
	Lift,		// carries up (rescue / reacquisition / assisted rise)
	Return		// carries left (the persistent return flow / reset current)
};

/** Placed shot colour of an enemy piece: forced by the chunk's design, or left to the level-wide 2:1 assignment. */
enum class EChunkShotColour : uint8
{
	Any,
	Yellow,
	Red
};

/**
 * One piece in chunk-local fractions: X of the chunk length (0 = entrance, 1 = exit), Z of the arena height
 * (0 = bottom). Solid and Wind use Rect; Trap and Enemy use the Rect centre (their size comes from their own tuning).
 */
struct UMBRELLAELLA_API FChunkPiece
{
	EChunkPieceKind Kind = EChunkPieceKind::Solid;
	FBox2D Rect = FBox2D(FVector2D::ZeroVector, FVector2D::ZeroVector);
	EChunkMechanic Mechanic = EChunkMechanic::Column;
	/** Wind only: unit direction in X/Z and its role. */
	FVector2D Direction = FVector2D::ZeroVector;
	EWindRole Role = EWindRole::Transport;
	/** Wind only: part of the optional safer bypass (an extra transfer, never the whole chunk). */
	bool bBypass = false;
	/** Enemy only. */
	EChunkShotColour Colour = EChunkShotColour::Any;

	FVector2D Centre() const { return Rect.GetCenter(); }
};

/** The authored arrangement of one variant: its pieces and a short design note. */
struct UMBRELLAELLA_API FChunkLayout
{
	int32 Chunk = 0;
	TCHAR Variant = 'A';
	TArray<FChunkPiece> Pieces;

	TArray<const FChunkPiece*> Of(EChunkPieceKind Kind) const;
	TArray<const FChunkPiece*> Winds(EWindRole Role) const;
	TArray<const FChunkPiece*> Bypass() const;
	/** a stable text form of the pieces (tests compare A against B). */
	FString Signature() const;
};

/** True constants of the chunk interface (shared by every variant). */
namespace ChunkLayoutConst
{
	/** Interface N: the entrance and exit band in Z fractions (centre 0.5 H, clearance 0.3 H). */
	static constexpr float InterfaceLow = 0.35f;
	static constexpr float InterfaceHigh = 0.65f;
	/** The exit corridor starts here (fraction of chunk length); a bypass rejoins N inside it or on a main current. */
	static constexpr float ExitCorridorStart = 0.8f;
	/** A bypass is a transfer, not a skip: at most this much of the chunk length. */
	static constexpr float MaxBypassLength = 0.7f;
	/** Look-ahead used to test that a bypass end hands over to the next piece. */
	static constexpr float RejoinProbe = 0.01f;
	/** Floor top as a fraction of H (LevelPlanConst::FloorThicknessFraction reads it). */
	static constexpr float FloorTop = 0.04f;
	/** Check tolerances (chunk fractions): overlap below this is touching; an enemy stands within StandTolerance of land. */
	static constexpr float OverlapEpsilon = 1.0e-3f;
	static constexpr float StandTolerance = 5.0e-3f;
	/** A column current: at least this tall, at most this wide. */
	static constexpr float ColumnMinHeight = 0.3f;
	static constexpr float ColumnMaxWidth = 0.25f;
	/** Width of the entrance / exit band checked for interface N. */
	static constexpr float EdgeBand = 0.05f;
	/** An air-only enemy closer than this above land counts as resting on it. */
	static constexpr float CourierClearance = 0.02f;
}

namespace ChunkLayouts
{
	/** The authored layout of a variant; empty pieces when its chunk flag is off or it does not exist. */
	UMBRELLAELLA_API FChunkLayout Get(int32 Chunk, TCHAR Variant);

	/** true when the chunk's own feature flag is on (each authored chunk has one). */
	UMBRELLAELLA_API bool IsChunkEnabled(int32 Chunk);

	/** Hazard rect of a trap or enemy piece in chunk fractions, from its kind's real size (enemy: body + patrol span). */
	UMBRELLAELLA_API FBox2D HazardRect(const FChunkPiece& Piece);

	/** Every reason the layout breaks the shared rules (empty = fine): interface N open at both ends, a return
	 *  current, the variant's mechanics present, no overlapping currents, enemies standing on land or in the air as their type allows. */
	UMBRELLAELLA_API TArray<FString> Validate(const FChunkLayout& Layout);

	/** Every reason the layout's bypass breaks the safer-bypass rule (empty = fine). */
	UMBRELLAELLA_API TArray<FString> ValidateBypass(const FChunkLayout& Layout);
}
