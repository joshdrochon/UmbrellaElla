#pragma once

#include "CoreMinimal.h"

/** Director's Cut chunk catalogue and nine-slot route (FLOW-24, HAZ-24..40, FLOW-27/28, FLOW-47). Plain data and rule functions; the
 *  enemies area places traps/enemies through FChunkVariant elements. Lane e. */

/** Mechanics a chunk contains; a mixed chunk may introduce at most one new one (HAZ-37). */
UENUM()
enum class EChunkMechanic : uint8
{
	Column,
	Mill,
	Warden,
	Courier,
	Stilt,
	Shutter,
	Bellows,
	BridgeTooth
};

/** One authored variant (A or B) of a catalogue chunk. */
struct UMBRELLAELLA_API FChunkVariant
{
	int32 Chunk = 0;		// 1..12
	TCHAR Variant = 'A';	// 'A' or 'B'
	TArray<EChunkMechanic> Mechanics;
	/** HAZ-24: begins/ends at interface N with persistent return flow and an optional bypass. */
	bool bInterfaceN = true;
	bool bReturnFlow = true;
	bool bBypass = true;

	FString Label() const { return FString::Printf(TEXT("%02d%c"), Chunk, Variant); }
	bool Has(EChunkMechanic M) const { return Mechanics.Contains(M); }
};

/** A generated route: nine ordered variants, three refuges (checkpoints) after slots 3, 6, 9. */
struct UMBRELLAELLA_API FRoute
{
	int64 Seed = 0;
	TArray<FChunkVariant> Slots;
	/** HAZ-40: true when the 32-attempt budget ran out and the named fallback was used. */
	bool bFromFallback = false;
	int32 Attempts = 0;

	FString Signature() const;
};

namespace LevelCatalogue
{
	/** The 12 chunks x 2 variants (24). */
	UMBRELLAELLA_API const TArray<FChunkVariant>& All();
	UMBRELLAELLA_API const FChunkVariant* Find(int32 Chunk, TCHAR Variant);

	/** HAZ-37 slot options: the chunk numbers each of the nine slots may draw from. */
	UMBRELLAELLA_API TArray<int32> SlotOptions(int32 SlotIndex);

	/** Mechanics the chunk adds beyond those already introduced. */
	UMBRELLAELLA_API int32 NewMechanicCount(const FChunkVariant& V, const TSet<EChunkMechanic>& Introduced);

	/** FLOW-47 gate: every reason the route fails (empty = valid). Checks joins, interface N, return flow, grammar, introduced-before-mixed. */
	UMBRELLAELLA_API TArray<FString> ValidateRoute(const FRoute& Route);

	/** HAZ-40: one candidate from the seed's separate layout stream (may be invalid). */
	UMBRELLAELLA_API FRoute BuildCandidate(int64 Seed, int32 Attempt);

	/** HAZ-40: first valid candidate within MaxCandidateAttempts, else the verified fallback. Same seed, same route. */
	UMBRELLAELLA_API FRoute Generate(int64 Seed);

	/** HAZ-40: the named fallback route (seed 1001 layout, verified by ValidateRoute at call time). */
	UMBRELLAELLA_API FRoute FallbackRoute();

	/** HAZ-40: different generation to avoid repeating the previous signature when another valid route exists. */
	UMBRELLAELLA_API FRoute GenerateAvoiding(int64 Seed, const FString& PreviousSignature);

	/** FLOW-24: chunk start X for a slot, including refuge lengths of earlier checkpoints. */
	UMBRELLAELLA_API float SlotStartX(int32 SlotIndex);

	/** FLOW-27: X of refuge CPn (1..3) core start, directly after slot 3n. */
	UMBRELLAELLA_API float RefugeStartX(int32 Checkpoint);

	UMBRELLAELLA_API float RouteLength();

	/** HAZ-41: a grounded footprint [Centre-Half, Centre+Half] stays on the walkable span [SupportMin, SupportMax]. */
	UMBRELLAELLA_API bool FootprintOnSupport(float Centre, float HalfWidth, float SupportMin, float SupportMax);

	/** HAZ-41: clamp a patrol centre so the whole footprint stays on the support. Support too narrow: the middle. */
	UMBRELLAELLA_API float ClampPatrolCentre(float Centre, float HalfWidth, float SupportMin, float SupportMax);
}

namespace CameraRules
{
	/** CAM-08: camera centre X following Ella, led in the travel direction (-1, 0, +1) by CameraLeadFraction of view width, clamped to the route. */
	UMBRELLAELLA_API float ScrollCentreX(float EllaX, int32 TravelDirection, float ViewWidth, float RouteMinX, float RouteMaxX);

	/** CAM-08: seconds between a hazard coming into view and reaching Ella at the given closing speed (>= AttackCueSeconds is the target). */
	UMBRELLAELLA_API float RevealLeadSeconds(float DistanceInView, float ClosingSpeed);
}
