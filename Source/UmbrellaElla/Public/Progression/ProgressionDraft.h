#pragma once

#include "CoreMinimal.h"
#include "Progression/ProgressionTypes.h"

struct FProgressionTuning;

/** One staged change on the review step: the rank move, its point cost and the value it changes. */
struct UMBRELLAELLA_API FProgressionReviewLine
{
	EProgressionTrack Track = EProgressionTrack::HitCapacity;
	int32 FromRank = 0;
	int32 ToRank = 0;
	/** Points this line spends (negative = refunded). */
	int32 Cost = 0;
	float ValueBefore = 0.0f;
	float ValueAfter = 0.0f;
};

/**
 * A staged, unconfirmed set of ranks (purchase screen). Browsing and previewing never touch live values: only
 * Commit on the subsystem applies a draft, atomically. Cancel, closing or a context change discards it.
 */
struct UMBRELLAELLA_API FProgressionDraft
{
	TArray<int32> Ranks;

	static FProgressionDraft Begin(const FProgressionProfile& Real);
	/** Stages one more (+1) or one fewer (-1) rank on a track if the result is a legal commit; otherwise leaves the draft. */
	EProgressionCommit Stage(const FProgressionTuning& Tuning, const FProgressionProfile& Real, const FPurchaseContext& Context,
		EProgressionTrack Track, int32 Delta);
	bool IsDirty(const FProgressionProfile& Real) const;
	/** Points the draft would spend beyond the real profile (negative = a net refund). */
	int32 NetCost(const FProgressionTuning& Tuning, const FProgressionProfile& Real) const;
	void Discard(const FProgressionProfile& Real);
	/** Every staged change with its cost and effect, in track order; the costs add up to NetCost. */
	TArray<FProgressionReviewLine> Review(const FProgressionTuning& Tuning, const FProgressionProfile& Real) const;
};
