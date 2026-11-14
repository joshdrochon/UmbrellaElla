#pragma once

#include "CoreMinimal.h"
#include "ProgressionTuning.generated.h"

/**
 * Every number of the Progression module (GDD SH1.0 section 4, adjustable prototype values, not final balance).
 * Not yet a member of UUmbrellaTuning (Core): see docs/build/requests/progression.md. Rule functions take a const
 * reference, so tests pass their own copy and the subsystem uses a default-constructed one until the member exists.
 * End a shipped default with // bake: <feature ID>.<param>.
 */
USTRUCT()
struct UMBRELLAELLA_API FProgressionTuning
{
	GENERATED_BODY()

	/** Advancing from level L costs XpCurveBase + floor((L - 1) / 2) XP. */
	UPROPERTY(EditAnywhere, Category = "Curve", meta = (ClampMin = "1"))
	int32 XpCurveBase = 100; // bake: FLOW-15.xp_curve_base

	UPROPERTY(EditAnywhere, Category = "Curve", meta = (ClampMin = "2"))
	int32 LevelCap = 62; // bake: FLOW-15.level_cap

	UPROPERTY(EditAnywhere, Category = "Curve")
	int32 TargetXpPerRun = 700; // bake: FLOW-15.target_xp_per_run

	UPROPERTY(EditAnywhere, Category = "Health tracks")
	int32 StartHitsPerLife = 3; // bake: FLOW-15.start_hits_per_life

	UPROPERTY(EditAnywhere, Category = "Health tracks")
	int32 StartLives = 3; // bake: FLOW-15.start_lives

	UPROPERTY(EditAnywhere, Category = "Health tracks")
	int32 MaxHitsPerLife = 11; // bake: FLOW-15.max_hits_per_life

	UPROPERTY(EditAnywhere, Category = "Health tracks")
	int32 MaxLivesCap = 11; // bake: FLOW-15.max_lives

	UPROPERTY(EditAnywhere, Category = "Health tracks")
	int32 RecoveryRanks = 3; // three successive one-point ranks

	UPROPERTY(EditAnywhere, Category = "Health tracks")
	float HealPerYellow = 0.5f; // base value; the Health tuning owns the bake key for this number

	UPROPERTY(EditAnywhere, Category = "Health tracks")
	float HealPerRecoveryRank = 0.3f; // base value; the Health tuning owns the bake key for this number

	/** Unlock levels (Small Blasts is level 1, always). */
	UPROPERTY(EditAnywhere, Category = "Unlocks")
	int32 UnlockLevelSmall = 1; // Small Blasts is always unlocked

	UPROPERTY(EditAnywhere, Category = "Unlocks")
	int32 UnlockLevelStreamed = 10; // bake: FLOW-16.unlock_level_streamed

	UPROPERTY(EditAnywhere, Category = "Unlocks")
	int32 UnlockLevelTwin = 20; // bake: FLOW-16.unlock_level_twin

	UPROPERTY(EditAnywhere, Category = "Unlocks")
	int32 UnlockLevelNeedle = 30; // bake: FLOW-16.unlock_level_needle

	/** Level gates of ranks I / II / III of the seven three-rank tracks (levels 1 / 8 / 18). */
	UPROPERTY(EditAnywhere, Category = "Ranks")
	int32 RankGateLevelI = 1;

	UPROPERTY(EditAnywhere, Category = "Ranks")
	int32 RankGateLevelII = 8;

	UPROPERTY(EditAnywhere, Category = "Ranks")
	int32 RankGateLevelIII = 18;

	/** Point cost of rank I / II / III of the seven three-rank tracks (1 / 2 / 3). */
	UPROPERTY(EditAnywhere, Category = "Ranks")
	int32 RankCostI = 1;

	UPROPERTY(EditAnywhere, Category = "Ranks")
	int32 RankCostII = 2;

	UPROPERTY(EditAnywhere, Category = "Ranks")
	int32 RankCostIII = 3;

	/** Run scaling, completed Director's Cut runs only. */
	UPROPERTY(EditAnywhere, Category = "Run scaling")
	float HpMultiplierCap = 2.0f; // bake: FLOW-05.hp_multiplier_cap

	UPROPERTY(EditAnywhere, Category = "Run scaling")
	float HpMultiplierStep = 0.1f; // bake: FLOW-05.hp_multiplier_step

	UPROPERTY(EditAnywhere, Category = "Run scaling")
	float CadenceMultiplierCap = 1.3f; // bake: FLOW-05.cadence_multiplier_cap

	UPROPERTY(EditAnywhere, Category = "Run scaling")
	float CadenceMultiplierStep = 0.03f; // bake: FLOW-05.cadence_multiplier_step

	UPROPERTY(EditAnywhere, Category = "Run scaling")
	float CountMultiplierCap = 2.0f; // bake: FLOW-05.count_multiplier_cap

	UPROPERTY(EditAnywhere, Category = "Run scaling")
	float CountMultiplierStep = 0.1f; // bake: FLOW-05.count_multiplier_step

	UPROPERTY(EditAnywhere, Category = "Final Hour")
	float FinalHourHpMultiplier = 2.0f; // bake: FLOW-06.final_hour_hp_multiplier

	UPROPERTY(EditAnywhere, Category = "Final Hour")
	float FinalHourCadenceMultiplier = 1.35f; // bake: FLOW-06.final_hour_cadence_multiplier

	UPROPERTY(EditAnywhere, Category = "Final Hour")
	float FinalHourCountMultiplier = 2.0f; // bake: FLOW-06.final_hour_count_multiplier

	/** Seconds the Final Hour intro stays up before the Extreme run plays. GDD: duration, skip and repeat policy are OPEN; provisional. */
	UPROPERTY(EditAnywhere, Category = "Final Hour", meta = (ClampMin = "0"))
	float FinalHourIntroSeconds = 4.0f;

	/** Final Hour intro text size (pixels). */
	UPROPERTY(EditAnywhere, Category = "Final Hour", meta = (ClampMin = "8"))
	int32 FinalHourIntroTextSize = 40;

	/** Kill XP. */
	UPROPERTY(EditAnywhere, Category = "Kill XP")
	int32 XpRoadwarden = 10; // bake: FLOW-19.xp_roadwarden

	UPROPERTY(EditAnywhere, Category = "Kill XP")
	int32 XpFloodstrider = 20; // bake: FLOW-19.xp_floodstrider

	UPROPERTY(EditAnywhere, Category = "Kill XP")
	int32 XpCourier = 10; // bake: FLOW-19.xp_courier

	UPROPERTY(EditAnywhere, Category = "Kill XP")
	int32 XpWings = 60; // bake: FLOW-19.xp_wings

	UPROPERTY(EditAnywhere, Category = "Kill XP")
	int32 XpFront = 60; // bake: FLOW-19.xp_front

	UPROPERTY(EditAnywhere, Category = "Kill XP")
	int32 XpMiddle = 80; // bake: FLOW-19.xp_middle

	UPROPERTY(EditAnywhere, Category = "Kill XP")
	int32 XpRear = 100; // bake: FLOW-19.xp_rear

	UPROPERTY(EditAnywhere, Category = "Kill XP")
	int32 XpClock = 150; // bake: FLOW-19.xp_clock

	/** Ordinary damage reduction, suction range, suction cone, spell damage per rank 0 / I / II / III . */
	UPROPERTY(EditAnywhere, Category = "Rank values")
	float DamageReductionRankI = 0.10f;

	UPROPERTY(EditAnywhere, Category = "Rank values")
	float DamageReductionRankII = 0.20f;

	UPROPERTY(EditAnywhere, Category = "Rank values")
	float DamageReductionRankIII = 0.30f;

	UPROPERTY(EditAnywhere, Category = "Rank values")
	float SuctionRangeBase = 240.0f; // base value; the UmbrellaFlight tuning owns the bake key for this number

	UPROPERTY(EditAnywhere, Category = "Rank values")
	float SuctionRangePerRank = 30.0f;

	UPROPERTY(EditAnywhere, Category = "Rank values")
	float SuctionConeBaseDegrees = 60.0f; // base value; the UmbrellaFlight tuning owns the bake key for this number

	UPROPERTY(EditAnywhere, Category = "Rank values")
	float SuctionConePerRankDegrees = 10.0f;

	UPROPERTY(EditAnywhere, Category = "Rank values")
	float SpellDamageRankI = 1.25f;

	UPROPERTY(EditAnywhere, Category = "Rank values")
	float SpellDamageRankII = 1.65f;

	UPROPERTY(EditAnywhere, Category = "Rank values")
	float SpellDamageRankIII = 2.25f;

	/** Save slots (profile and its backup). */
	UPROPERTY(EditAnywhere, Category = "Persistence")
	FString SaveSlotName = TEXT("UmbrellaEllaProgress");

	/** HUD ring: seconds of the level-up pulse. */
	UPROPERTY(EditAnywhere, Category = "XP ring", meta = (ClampMin = "0"))
	float LevelUpPulseSeconds = 0.8f;

	/** XP ring look (pixels and colours); the ring is a separate layer around the clock. */
	UPROPERTY(EditAnywhere, Category = "XP ring", meta = (ClampMin = "1"))
	float RingThickness = 3.0f;

	UPROPERTY(EditAnywhere, Category = "XP ring", meta = (ClampMin = "0"))
	float RingPulseExtraThickness = 4.0f;

	UPROPERTY(EditAnywhere, Category = "XP ring", meta = (ClampMin = "8"))
	int32 RingSegments = 64;

	UPROPERTY(EditAnywhere, Category = "XP ring")
	float RingSizePixels = 140.0f;

	UPROPERTY(EditAnywhere, Category = "XP ring")
	FVector2D RingViewportPosition = FVector2D(16.0, 16.0);

	UPROPERTY(EditAnywhere, Category = "XP ring")
	FLinearColor RingTrackColor = FLinearColor(0.15f, 0.15f, 0.2f, 0.45f);

	UPROPERTY(EditAnywhere, Category = "XP ring")
	FLinearColor RingFillColor = FLinearColor(0.45f, 0.85f, 1.0f, 0.95f);

	UPROPERTY(EditAnywhere, Category = "XP ring")
	FLinearColor RingMaxColor = FLinearColor(1.0f, 0.85f, 0.35f, 0.95f);

	UPROPERTY(EditAnywhere, Category = "XP ring")
	FLinearColor RingLevelUpColor = FLinearColor(1.0f, 1.0f, 1.0f, 1.0f);
};
