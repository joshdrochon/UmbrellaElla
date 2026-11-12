#include "Progression/ProgressionRules.h"
#include "Harness/UmbrellaFeatureFlags.h"
#include "Progression/ProgressionTuning.h"

// Each gated rule function checks its flag; with a flag off it falls back to the Start Game behaviour (no growth, no
// scaling, no rewards). The curve, ranks and fixture are the shared base and have no switch of their own.

namespace
{
	/** Three-rank tracks (everything except hit capacity, lives and recovery). */
	bool IsThreeRankTrack(EProgressionTrack Track)
	{
		return Track != EProgressionTrack::HitCapacity && Track != EProgressionTrack::Lives && Track != EProgressionTrack::Recovery;
	}

	int32 TrackIndex(EProgressionTrack Track)
	{
		return static_cast<int32>(Track);
	}

	int32 TrackCount()
	{
		return static_cast<int32>(EProgressionTrack::Count);
	}

	bool ContainsNoCase(const FString& Haystack, const TCHAR* Needle)
	{
		return Haystack.Contains(Needle, ESearchCase::IgnoreCase);
	}

	int32 CostForThreeRank(const FProgressionTuning& Tuning, int32 Rank)
	{
		const int32 Costs[] = { Tuning.RankCostI, Tuning.RankCostII, Tuning.RankCostIII };
		const int32 Index = FMath::Clamp(Rank, 1, UE_ARRAY_COUNT(Costs)) - 1;
		return Costs[Index];
	}

	float ThreeRankValue(const float Base, const float Step, int32 Rank)
	{
		return Base + Step * static_cast<float>(Rank);
	}
}

// ---------------------------------------------------------------- XP curve and levels
int32 FProgressionRules::LevelCost(const FProgressionTuning& Tuning, int32 Level)
{
	return Tuning.XpCurveBase + (FMath::Max(Level, 1) - 1) / 2;
}

int32 FProgressionRules::CumulativeXp(const FProgressionTuning& Tuning, int32 Level)
{
	int32 Total = 0;
	for (int32 From = 1; From < Level; ++From)
	{
		Total += LevelCost(Tuning, From);
	}
	return Total;
}

FLevelProgress FProgressionRules::LevelForXp(const FProgressionTuning& Tuning, int32 Xp)
{
	FLevelProgress Result;
	int32 Left = FMath::Max(Xp, 0);
	while (Result.Level < Tuning.LevelCap && Left >= LevelCost(Tuning, Result.Level))
	{
		Left -= LevelCost(Tuning, Result.Level);
		++Result.Level;
	}
	Result.bMax = Result.Level >= Tuning.LevelCap;
	Result.PartialXp = Result.bMax ? 0 : Left;
	Result.CostToNext = Result.bMax ? 0 : LevelCost(Tuning, Result.Level);
	return Result;
}

int32 FProgressionRules::EarnedPoints(int32 Level)
{
	return FMath::Max(Level, 1) - 1;
}

// ---------------------------------------------------------------- unlocks
int32 FProgressionRules::SpellUnlockLevel(const FProgressionTuning& Tuning, EProgressionSpell Spell)
{
	switch (Spell)
	{
	case EProgressionSpell::SmallBlasts:
		return Tuning.UnlockLevelSmall;
	case EProgressionSpell::StreamedBlast:
		return Tuning.UnlockLevelStreamed;
	case EProgressionSpell::TwinStars:
		return Tuning.UnlockLevelTwin;
	case EProgressionSpell::NeedleSpell:
		return Tuning.UnlockLevelNeedle;
	default:
		return Tuning.LevelCap + 1;
	}
}

bool FProgressionRules::IsSpellUnlocked(const FProgressionTuning& Tuning, int32 Level, EProgressionSpell Spell)
{
	return IsFeatureEnabled(EFeatureId::FLOW_16) ? Level >= SpellUnlockLevel(Tuning, Spell) : Spell == EProgressionSpell::SmallBlasts;
}

TArray<EProgressionSpell> FProgressionRules::UnlockedSpells(const FProgressionTuning& Tuning, int32 Level)
{
	TArray<EProgressionSpell> Result;
	for (int32 Index = 0; Index < static_cast<int32>(EProgressionSpell::Count); ++Index)
	{
		const EProgressionSpell Spell = static_cast<EProgressionSpell>(Index);
		if (IsSpellUnlocked(Tuning, Level, Spell))
		{
			Result.Add(Spell);
		}
	}
	return Result;
}

// ---------------------------------------------------------------- tracks and ranks
FProgressionProfile FProgressionRules::MakeEmptyProfile()
{
	FProgressionProfile Profile;
	Profile.Ranks.Init(0, TrackCount());
	Profile.CheckpointRanks.Init(0, TrackCount());
	return Profile;
}

int32 FProgressionRules::RankOf(const TArray<int32>& Ranks, EProgressionTrack Track)
{
	return Ranks.IsValidIndex(TrackIndex(Track)) ? Ranks[TrackIndex(Track)] : 0;
}

int32 FProgressionRules::TrackMaxRank(const FProgressionTuning& Tuning, EProgressionTrack Track)
{
	switch (Track)
	{
	case EProgressionTrack::HitCapacity:
		return Tuning.MaxHitsPerLife - Tuning.StartHitsPerLife;
	case EProgressionTrack::Lives:
		return Tuning.MaxLivesCap - Tuning.StartLives;
	case EProgressionTrack::Recovery:
		return Tuning.RecoveryRanks;
	default:
		return ThreeRankMax;
	}
}

int32 FProgressionRules::RankCost(const FProgressionTuning& Tuning, EProgressionTrack Track, int32 Rank)
{
	return IsThreeRankTrack(Track) ? CostForThreeRank(Tuning, Rank) : 1;
}

int32 FProgressionRules::RankGateLevel(const FProgressionTuning& Tuning, EProgressionTrack Track, int32 Rank)
{
	if (!IsThreeRankTrack(Track))
	{
		return 1;
	}
	const int32 Gates[] = { Tuning.RankGateLevelI, Tuning.RankGateLevelII, Tuning.RankGateLevelIII };
	return Gates[FMath::Clamp(Rank, 1, UE_ARRAY_COUNT(Gates)) - 1];
}

int32 FProgressionRules::SpentOnRanks(const FProgressionTuning& Tuning, const TArray<int32>& Ranks)
{
	int32 Total = 0;
	for (int32 Index = 0; Index < TrackCount(); ++Index)
	{
		const EProgressionTrack Track = static_cast<EProgressionTrack>(Index);
		const int32 Rank = RankOf(Ranks, Track);
		for (int32 Step = 1; Step <= Rank; ++Step)
		{
			Total += RankCost(Tuning, Track, Step);
		}
	}
	return Total;
}

int32 FProgressionRules::UnspentPoints(const FProgressionTuning& Tuning, const FProgressionProfile& Profile)
{
	return EarnedPoints(LevelForXp(Tuning, Profile.Xp).Level) - SpentOnRanks(Tuning, Profile.Ranks);
}

int32 FProgressionRules::MaxTrackCost(const FProgressionTuning& Tuning)
{
	TArray<int32> Maxed;
	for (int32 Index = 0; Index < TrackCount(); ++Index)
	{
		Maxed.Add(TrackMaxRank(Tuning, static_cast<EProgressionTrack>(Index)));
	}
	return SpentOnRanks(Tuning, Maxed);
}

bool FProgressionRules::IsAllStatsMaxed(const FProgressionTuning& Tuning, const FProgressionProfile& Profile)
{
	for (int32 Index = 0; Index < TrackCount(); ++Index)
	{
		const EProgressionTrack Track = static_cast<EProgressionTrack>(Index);
		if (RankOf(Profile.Ranks, Track) < TrackMaxRank(Tuning, Track))
		{
			return false;
		}
	}
	return true;
}

// ---------------------------------------------------------------- rank values
int32 FProgressionRules::HitCapacity(const FProgressionTuning& Tuning, const TArray<int32>& Ranks)
{
	return Tuning.StartHitsPerLife + RankOf(Ranks, EProgressionTrack::HitCapacity);
}

int32 FProgressionRules::MaxLives(const FProgressionTuning& Tuning, const TArray<int32>& Ranks)
{
	return Tuning.StartLives + RankOf(Ranks, EProgressionTrack::Lives);
}

float FProgressionRules::HealPerYellow(const FProgressionTuning& Tuning, const TArray<int32>& Ranks)
{
	return Tuning.HealPerYellow + Tuning.HealPerRecoveryRank * static_cast<float>(RankOf(Ranks, EProgressionTrack::Recovery));
}

float FProgressionRules::DamageReduction(const FProgressionTuning& Tuning, const TArray<int32>& Ranks)
{
	const float Values[] = { 0.0f, Tuning.DamageReductionRankI, Tuning.DamageReductionRankII, Tuning.DamageReductionRankIII };
	return Values[FMath::Clamp(RankOf(Ranks, EProgressionTrack::DamageReduction), 0, static_cast<int32>(UE_ARRAY_COUNT(Values)) - 1)];
}

float FProgressionRules::SuctionRange(const FProgressionTuning& Tuning, const TArray<int32>& Ranks)
{
	return ThreeRankValue(Tuning.SuctionRangeBase, Tuning.SuctionRangePerRank, RankOf(Ranks, EProgressionTrack::SuctionRange));
}

float FProgressionRules::SuctionConeDegrees(const FProgressionTuning& Tuning, const TArray<int32>& Ranks)
{
	return ThreeRankValue(Tuning.SuctionConeBaseDegrees, Tuning.SuctionConePerRankDegrees, RankOf(Ranks, EProgressionTrack::SuctionCone));
}

float FProgressionRules::SpellDamageMultiplier(const FProgressionTuning& Tuning, const TArray<int32>& Ranks, EProgressionSpell Spell)
{
	const float Values[] = { 1.0f, Tuning.SpellDamageRankI, Tuning.SpellDamageRankII, Tuning.SpellDamageRankIII };
	int32 Rank = 0;
	switch (Spell)
	{
	case EProgressionSpell::SmallBlasts:
		Rank = RankOf(Ranks, EProgressionTrack::DamageSmall);
		break;
	case EProgressionSpell::StreamedBlast:
		Rank = RankOf(Ranks, EProgressionTrack::DamageStreamed);
		break;
	case EProgressionSpell::TwinStars:
		Rank = RankOf(Ranks, EProgressionTrack::DamageTwin);
		break;
	default:
		Rank = RankOf(Ranks, EProgressionTrack::DamageNeedle);
		break;
	}
	return Values[FMath::Clamp(Rank, 0, static_cast<int32>(UE_ARRAY_COUNT(Values)) - 1)];
}

// ---------------------------------------------------------------- run scaling (FLOW-05, FLOW-06)
FRunScaling FProgressionRules::RunScaling(const FProgressionTuning& Tuning, int32 CompletedRuns, bool bFinalHour)
{
	FRunScaling Result;
	if (bFinalHour && IsFeatureEnabled(EFeatureId::FLOW_06))
	{
		Result.Hp = static_cast<double>(Tuning.FinalHourHpMultiplier);
		Result.Cadence = static_cast<double>(Tuning.FinalHourCadenceMultiplier);
		Result.Count = static_cast<double>(Tuning.FinalHourCountMultiplier);
		return Result;
	}
	if (!IsFeatureEnabled(EFeatureId::FLOW_05))
	{
		return Result;
	}
	const double Runs = static_cast<double>(FMath::Max(CompletedRuns, 0));
	Result.Hp = FMath::Min(static_cast<double>(Tuning.HpMultiplierCap), 1.0 + static_cast<double>(Tuning.HpMultiplierStep) * Runs);
	Result.Cadence = FMath::Min(static_cast<double>(Tuning.CadenceMultiplierCap), 1.0 + static_cast<double>(Tuning.CadenceMultiplierStep) * Runs);
	Result.Count = FMath::Min(static_cast<double>(Tuning.CountMultiplierCap), 1.0 + static_cast<double>(Tuning.CountMultiplierStep) * Runs);
	return Result;
}

FRunScaling FProgressionRules::NextRunScaling(const FProgressionTuning& Tuning, const FProgressionProfile& Profile)
{
	return RunScaling(Tuning, Profile.CompletedRuns, IsAllStatsMaxed(Tuning, Profile));
}

int32 FProgressionRules::EnemyCount(const FProgressionTuning& Tuning, int32 BaseCount, const FRunScaling& Scaling, int32 LegalSlots, int32& OutShortfall)
{
	const int32 Wanted = FMath::FloorToInt(static_cast<double>(BaseCount) * Scaling.Count + 0.5 + CountRoundingEpsilon);
	const int32 Placed = FMath::Min(Wanted, LegalSlots);
	OutShortfall = FMath::Max(0, Wanted - LegalSlots);
	return Placed;
}

// ---------------------------------------------------------------- kill XP
int32 FProgressionRules::KillXp(const FProgressionTuning& Tuning, FName Label)
{
	if (!IsFeatureEnabled(EFeatureId::FLOW_19) || Label.IsNone())
	{
		return 0;
	}
	const FString Text = Label.ToString();
	if (ContainsNoCase(Text, TEXT("withdraw")))
	{
		return 0;
	}
	struct FKillLabel
	{
		const TCHAR* Needle;
		int32 Xp;
	};
	const FKillLabel Table[] = {
		{ TEXT("roadwarden"), Tuning.XpRoadwarden },
		{ TEXT("floodstrider"), Tuning.XpFloodstrider },
		{ TEXT("courier"), Tuning.XpCourier },
		{ TEXT("wing"), Tuning.XpWings },
		{ TEXT("front"), Tuning.XpFront },
		{ TEXT("middle"), Tuning.XpMiddle },
		{ TEXT("rear"), Tuning.XpRear },
		{ TEXT("clock"), Tuning.XpClock },
	};
	for (const FKillLabel& Entry : Table)
	{
		if (ContainsNoCase(Text, Entry.Needle))
		{
			return Entry.Xp;
		}
	}
	return 0;
}

// ---------------------------------------------------------------- profile changes
int32 FProgressionRules::AddXp(const FProgressionTuning& Tuning, FProgressionProfile& Profile, int32 Amount)
{
	if (Amount <= 0)
	{
		return 0;
	}
	const int32 Before = LevelForXp(Tuning, Profile.Xp).Level;
	const int32 Ceiling = CumulativeXp(Tuning, Tuning.LevelCap);
	Profile.Xp = FMath::Min(Profile.Xp + Amount, Ceiling);
	return LevelForXp(Tuning, Profile.Xp).Level - Before;
}

void FProgressionRules::ReachCheckpoint(FProgressionProfile& Profile, EProgressionCheckpointKind Kind)
{
	Profile.bCheckpointValid = true;
	Profile.CheckpointKind = Kind;
	Profile.CheckpointXp = Profile.Xp;
	Profile.CheckpointRanks = Profile.Ranks;
}

void FProgressionRules::DeathRetry(FProgressionProfile& Profile)
{
	if (IsFeatureEnabled(EFeatureId::FLOW_07) && Profile.bCheckpointValid && Profile.CheckpointKind == EProgressionCheckpointKind::Boss)
	{
		Profile.Xp = Profile.CheckpointXp;
		Profile.Ranks = Profile.CheckpointRanks;
	}
}

void FProgressionRules::QuitReload(FProgressionProfile& Profile)
{
	if (IsFeatureEnabled(EFeatureId::FLOW_08) && Profile.bCheckpointValid)
	{
		Profile.Xp = Profile.CheckpointXp;
		Profile.Ranks = Profile.CheckpointRanks;
	}
}

void FProgressionRules::CompleteRun(FProgressionProfile& Profile)
{
	if (!IsFeatureEnabled(EFeatureId::FLOW_10))
	{
		return;
	}
	++Profile.CompletedRuns;
	Profile.bCheckpointValid = false;
	Profile.CheckpointXp = Profile.Xp;
	Profile.CheckpointRanks = Profile.Ranks;
}

// ---------------------------------------------------------------- purchases
bool FProgressionRules::CanPurchase(const FPurchaseContext& Context)
{
	if (!IsFeatureEnabled(EFeatureId::FLOW_18) || !Context.bAlive || Context.bStoryLocked)
	{
		return false;
	}
	return Context.Kind == EPurchaseContextKind::SafeRefuge || Context.Kind == EPurchaseContextKind::BetweenRuns
		|| Context.Kind == EPurchaseContextKind::RunStart;
}

bool FProgressionRules::CanReallocate(const FPurchaseContext& Context, const FProgressionProfile& Profile)
{
	return IsFeatureEnabled(EFeatureId::FLOW_11) && CanPurchase(Context) && Context.Kind == EPurchaseContextKind::RunStart
		&& Profile.CompletedRuns >= 1;
}

EProgressionCommit FProgressionRules::TryCommitRanks(const FProgressionTuning& Tuning, FProgressionProfile& Profile,
	const TArray<int32>& NewRanks, const FPurchaseContext& Context)
{
	if (NewRanks.Num() != TrackCount() || Profile.Ranks.Num() != TrackCount())
	{
		return EProgressionCommit::InvalidRanks;
	}
	const int32 Level = LevelForXp(Tuning, Profile.Xp).Level;
	bool bBuys = false;
	bool bRefunds = false;
	for (int32 Index = 0; Index < TrackCount(); ++Index)
	{
		const EProgressionTrack Track = static_cast<EProgressionTrack>(Index);
		if (NewRanks[Index] < 0 || NewRanks[Index] > TrackMaxRank(Tuning, Track))
		{
			return EProgressionCommit::InvalidRanks;
		}
		bBuys |= NewRanks[Index] > Profile.Ranks[Index];
		bRefunds |= NewRanks[Index] < Profile.Ranks[Index];
	}
	if (bRefunds && !CanReallocate(Context, Profile))
	{
		return EProgressionCommit::RefundNotAllowed;
	}
	if (bBuys && !CanPurchase(Context))
	{
		return EProgressionCommit::PurchaseNotAllowed;
	}
	for (int32 Index = 0; Index < TrackCount(); ++Index)
	{
		const EProgressionTrack Track = static_cast<EProgressionTrack>(Index);
		for (int32 Rank = Profile.Ranks[Index] + 1; Rank <= NewRanks[Index]; ++Rank)
		{
			if (Level < RankGateLevel(Tuning, Track, Rank))
			{
				return EProgressionCommit::RankGateClosed;
			}
		}
	}
	if (SpentOnRanks(Tuning, NewRanks) > EarnedPoints(Level))
	{
		return EProgressionCommit::NotEnoughPoints;
	}
	Profile.Ranks = NewRanks;
	return EProgressionCommit::Ok;
}

float FProgressionRules::RingFill(const FLevelProgress& Progress)
{
	if (Progress.bMax)
	{
		return 1.0f;
	}
	return Progress.CostToNext > 0 ? static_cast<float>(Progress.PartialXp) / static_cast<float>(Progress.CostToNext) : 0.0f;
}

// ---------------------------------------------------------------- developer fixture
FProgressionProfile FProgressionRules::MakeFixture(const FProgressionTuning& Tuning, int32 Level)
{
	FProgressionProfile Profile = MakeEmptyProfile();
	Profile.Xp = CumulativeXp(Tuning, FMath::Clamp(Level, 1, Tuning.LevelCap));
	return Profile;
}
