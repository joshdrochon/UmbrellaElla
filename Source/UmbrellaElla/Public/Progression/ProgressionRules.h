#pragma once

#include "CoreMinimal.h"
#include "Progression/ProgressionTypes.h"

struct FProgressionTuning;

/** Level and partial XP for an XP total; bMax at the cap (the HUD shows MAX, never a false next-level fill). */
struct UMBRELLAELLA_API FLevelProgress
{
	int32 Level = 1;
	int32 PartialXp = 0;
	int32 CostToNext = 0;
	bool bMax = false;
};

/** Multipliers for the next run. */
struct UMBRELLAELLA_API FRunScaling
{
	double Hp = 1.0;
	double Cadence = 1.0;
	double Count = 1.0;
};

/**
 * Plain rule functions for Director's Cut progression (Director's Cut, GDD section 4). They mirror tools/progression_model.py;
 * tests compare the numbers. Nothing here touches the world, the event bus or the disk.
 * INV-1: level, points and unlocks are derived from Xp and Ranks, never stored.
 * INV-2: earned points (Level - 1) equal spent costs plus unspent points.
 * INV-3: Start Game has no progression (the subsystem returns a zero profile in that mode).
 */
struct UMBRELLAELLA_API FProgressionRules
{
	/** Ranks on each of the seven three-rank tracks (costs 1 / 2 / 3). */
	static constexpr int32 ThreeRankMax = 3;
	/** Float tuning like 0.1 is not exact; this keeps round(5 x 1.3) = 7 on the .5 edge. */
	static constexpr double CountRoundingEpsilon = 1e-6;

	// ---- XP curve and levels
	static int32 LevelCost(const FProgressionTuning& Tuning, int32 Level);
	static int32 CumulativeXp(const FProgressionTuning& Tuning, int32 Level);
	static FLevelProgress LevelForXp(const FProgressionTuning& Tuning, int32 Xp);
	static int32 EarnedPoints(int32 Level);

	// ---- Unlocks
	static int32 SpellUnlockLevel(const FProgressionTuning& Tuning, EProgressionSpell Spell);
	static bool IsSpellUnlocked(const FProgressionTuning& Tuning, int32 Level, EProgressionSpell Spell);
	static TArray<EProgressionSpell> UnlockedSpells(const FProgressionTuning& Tuning, int32 Level);

	// ---- Tracks and ranks
	static FProgressionProfile MakeEmptyProfile();
	static int32 RankOf(const TArray<int32>& Ranks, EProgressionTrack Track);
	static int32 TrackMaxRank(const FProgressionTuning& Tuning, EProgressionTrack Track);
	/** Cost of buying the given 1-based rank on a track. */
	static int32 RankCost(const FProgressionTuning& Tuning, EProgressionTrack Track, int32 Rank);
	static int32 RankGateLevel(const FProgressionTuning& Tuning, EProgressionTrack Track, int32 Rank);
	static int32 SpentOnRanks(const FProgressionTuning& Tuning, const TArray<int32>& Ranks);
	static int32 UnspentPoints(const FProgressionTuning& Tuning, const FProgressionProfile& Profile);
	static int32 MaxTrackCost(const FProgressionTuning& Tuning);
	static bool IsAllStatsMaxed(const FProgressionTuning& Tuning, const FProgressionProfile& Profile);

	// ---- Rank values other modules read
	static int32 HitCapacity(const FProgressionTuning& Tuning, const TArray<int32>& Ranks);
	static int32 MaxLives(const FProgressionTuning& Tuning, const TArray<int32>& Ranks);
	static float HealPerYellow(const FProgressionTuning& Tuning, const TArray<int32>& Ranks);
	static float DamageReduction(const FProgressionTuning& Tuning, const TArray<int32>& Ranks);
	static float SuctionRange(const FProgressionTuning& Tuning, const TArray<int32>& Ranks);
	static float SuctionConeDegrees(const FProgressionTuning& Tuning, const TArray<int32>& Ranks);
	static float SpellDamageMultiplier(const FProgressionTuning& Tuning, const TArray<int32>& Ranks, EProgressionSpell Spell);

	// ---- Run scaling
	static FRunScaling RunScaling(const FProgressionTuning& Tuning, int32 CompletedRuns, bool bFinalHour);
	/** Final Hour replaces the ordinary scaling when every stat is at maximum, evaluated when the run starts. */
	static FRunScaling NextRunScaling(const FProgressionTuning& Tuning, const FProgressionProfile& Profile);
	/** round(base x count multiplier), never above the legal slots; OutShortfall is the recorded shortfall. */
	static int32 EnemyCount(const FProgressionTuning& Tuning, int32 BaseCount, const FRunScaling& Scaling, int32 LegalSlots, int32& OutShortfall);

	// ---- Kill XP. A label that is not a rewardable kill gives 0 (Courier withdrawal, absorption, checkpoints).
	static int32 KillXp(const FProgressionTuning& Tuning, FName Label);

	// ---- Profile changes
	/** Adds XP; returns the number of levels gained. Does nothing for Amount <= 0. */
	static int32 AddXp(const FProgressionTuning& Tuning, FProgressionProfile& Profile, int32 Amount);
	static void ReachCheckpoint(FProgressionProfile& Profile, EProgressionCheckpointKind Kind);
	/** Level checkpoint keeps XP and ranks; boss checkpoint restores the checkpoint's XP and ranks together. */
	static void DeathRetry(FProgressionProfile& Profile);
	/** Quit and reload: the last checkpoint's XP and ranks, whatever its kind. */
	static void QuitReload(FProgressionProfile& Profile);
	/** A won run: keeps growth, advances the completed-run count, drops the checkpoint. */
	static void CompleteRun(FProgressionProfile& Profile);

	// ---- Purchases
	static bool CanPurchase(const FPurchaseContext& Context);
	static bool CanReallocate(const FPurchaseContext& Context, const FProgressionProfile& Profile);
	/** Applies a staged set of ranks atomically, or changes nothing. */
	static EProgressionCommit TryCommitRanks(const FProgressionTuning& Tuning, FProgressionProfile& Profile,
		const TArray<int32>& NewRanks, const FPurchaseContext& Context);

	// ---- XP ring: 0..1 fill toward the next level; full (with MAX shown) at the cap, never a false next-level fill.
	static float RingFill(const FLevelProgress& Progress);

	// ---- Developer fixture: level L, zero partial XP, no ranks.
	static FProgressionProfile MakeFixture(const FProgressionTuning& Tuning, int32 Level);
};
