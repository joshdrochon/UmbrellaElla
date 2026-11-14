#include "Misc/AutomationTest.h"
#include "Progression/ProgressionDraft.h"
#include "Progression/ProgressionRules.h"
#include "Progression/ProgressionTuning.h"

#if WITH_AUTOMATION_TESTS

// Golden numbers below are printed by tools/progression_model.py (cumulative_xp, level_for_xp, run_scaling, enemy_count,
// max_track_cost, unlocked); the C++ rule functions must give the same values.

namespace
{
	FPurchaseContext Refuge()
	{
		FPurchaseContext Context;
		Context.Kind = EPurchaseContextKind::SafeRefuge;
		return Context;
	}

	FPurchaseContext RunStartContext()
	{
		FPurchaseContext Context;
		Context.Kind = EPurchaseContextKind::RunStart;
		return Context;
	}

	TArray<int32> WithRank(const FProgressionProfile& Profile, EProgressionTrack Track, int32 Rank)
	{
		TArray<int32> Ranks = Profile.Ranks;
		Ranks[static_cast<int32>(Track)] = Rank;
		return Ranks;
	}
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FProgXpCurve, "UmbrellaElla.Progression.XpCurveMatchesOracle", EAutomationTestFlags::EditorContext | EAutomationTestFlags::ClientContext | EAutomationTestFlags::EngineFilter)
bool FProgXpCurve::RunTest(const FString& Parameters)
{
	const FProgressionTuning Tuning;
	TestEqual(TEXT("level 1"), FProgressionRules::CumulativeXp(Tuning, 1), 0);
	TestEqual(TEXT("level 2"), FProgressionRules::CumulativeXp(Tuning, 2), 100);
	TestEqual(TEXT("level 3"), FProgressionRules::CumulativeXp(Tuning, 3), 200);
	TestEqual(TEXT("level 10"), FProgressionRules::CumulativeXp(Tuning, 10), 916);
	TestEqual(TEXT("level 20"), FProgressionRules::CumulativeXp(Tuning, 20), 1981);
	TestEqual(TEXT("level 30"), FProgressionRules::CumulativeXp(Tuning, 30), 3096);
	TestEqual(TEXT("level 61"), FProgressionRules::CumulativeXp(Tuning, 61), 6870);
	TestEqual(TEXT("level 62"), FProgressionRules::CumulativeXp(Tuning, 62), 7000);
	TestEqual(TEXT("cost from 3"), FProgressionRules::LevelCost(Tuning, 3), 101);
	const FLevelProgress AtTen = FProgressionRules::LevelForXp(Tuning, 916);
	TestEqual(TEXT("916 is level 10"), AtTen.Level, 10);
	TestEqual(TEXT("916 has no partial"), AtTen.PartialXp, 0);
	const FLevelProgress Carry = FProgressionRules::LevelForXp(Tuning, 150);
	TestEqual(TEXT("150 is level 2"), Carry.Level, 2);
	TestEqual(TEXT("surplus carries"), Carry.PartialXp, 50);
	const FLevelProgress Capped = FProgressionRules::LevelForXp(Tuning, 99999);
	TestEqual(TEXT("cap level"), Capped.Level, 62);
	TestTrue(TEXT("MAX at the cap"), Capped.bMax);
	TestEqual(TEXT("no partial at the cap"), Capped.PartialXp, 0);
	TestEqual(TEXT("61 earned points at the cap"), FProgressionRules::EarnedPoints(62), 61);
	TestEqual(TEXT("maxing every track costs 61"), FProgressionRules::MaxTrackCost(Tuning), 61);
	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FProgUnlocks, "UmbrellaElla.Progression.UnlockScheduleMatchesOracle", EAutomationTestFlags::EditorContext | EAutomationTestFlags::ClientContext | EAutomationTestFlags::EngineFilter)
bool FProgUnlocks::RunTest(const FString& Parameters)
{
	const FProgressionTuning Tuning;
	const int32 Levels[] = { 1, 9, 10, 19, 20, 29, 30, 62 };
	const int32 Counts[] = { 1, 1, 2, 2, 3, 3, 4, 4 };
	for (int32 Index = 0; Index < UE_ARRAY_COUNT(Levels); ++Index)
	{
		TestEqual(*FString::Printf(TEXT("unlocked at level %d"), Levels[Index]), FProgressionRules::UnlockedSpells(Tuning, Levels[Index]).Num(), Counts[Index]);
	}
	TestTrue(TEXT("small at 1"), FProgressionRules::IsSpellUnlocked(Tuning, 1, EProgressionSpell::SmallBlasts));
	TestFalse(TEXT("streamed not at 9"), FProgressionRules::IsSpellUnlocked(Tuning, 9, EProgressionSpell::StreamedBlast));
	TestTrue(TEXT("streamed at 10"), FProgressionRules::IsSpellUnlocked(Tuning, 10, EProgressionSpell::StreamedBlast));
	TestTrue(TEXT("twin at 20"), FProgressionRules::IsSpellUnlocked(Tuning, 20, EProgressionSpell::TwinStars));
	TestFalse(TEXT("needle not at 29"), FProgressionRules::IsSpellUnlocked(Tuning, 29, EProgressionSpell::NeedleSpell));
	TestTrue(TEXT("needle at 30"), FProgressionRules::IsSpellUnlocked(Tuning, 30, EProgressionSpell::NeedleSpell));
	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FProgRunScaling, "UmbrellaElla.Progression.RunScalingMatchesOracle", EAutomationTestFlags::EditorContext | EAutomationTestFlags::ClientContext | EAutomationTestFlags::EngineFilter)
bool FProgRunScaling::RunTest(const FString& Parameters)
{
	const FProgressionTuning Tuning;
	struct FRow
	{
		int32 Runs;
		double Hp;
		double Cadence;
		double Count;
	};
	const FRow Rows[] = { { 0, 1.0, 1.0, 1.0 }, { 1, 1.1, 1.03, 1.1 }, { 5, 1.5, 1.15, 1.5 }, { 10, 2.0, 1.3, 2.0 }, { 20, 2.0, 1.3, 2.0 } };
	for (const FRow& Row : Rows)
	{
		const FRunScaling Scaling = FProgressionRules::RunScaling(Tuning, Row.Runs, false);
		TestEqual(*FString::Printf(TEXT("hp after %d runs"), Row.Runs), Scaling.Hp, Row.Hp, 1e-4);
		TestEqual(*FString::Printf(TEXT("cadence after %d runs"), Row.Runs), Scaling.Cadence, Row.Cadence, 1e-4);
		TestEqual(*FString::Printf(TEXT("count after %d runs"), Row.Runs), Scaling.Count, Row.Count, 1e-4);
	}
	const FRunScaling Final = FProgressionRules::RunScaling(Tuning, 3, true);
	TestEqual(TEXT("final hour hp replaces"), Final.Hp, 2.0, 1e-4);
	TestEqual(TEXT("final hour cadence replaces"), Final.Cadence, 1.35, 1e-4);
	TestEqual(TEXT("final hour count replaces"), Final.Count, 2.0, 1e-4);

	int32 Shortfall = 0;
	TestEqual(TEXT("5 base x1.3 = 7"), FProgressionRules::EnemyCount(Tuning, 5, FProgressionRules::RunScaling(Tuning, 3, false), 100, Shortfall), 7);
	TestEqual(TEXT("no shortfall"), Shortfall, 0);
	TestEqual(TEXT("7 base x2 capped at 12 slots"), FProgressionRules::EnemyCount(Tuning, 7, FProgressionRules::RunScaling(Tuning, 10, false), 12, Shortfall), 12);
	TestEqual(TEXT("shortfall recorded"), Shortfall, 2);
	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FProgFinalHourTrigger, "UmbrellaElla.Progression.AllStatsMaxedTriggersFinalHour", EAutomationTestFlags::EditorContext | EAutomationTestFlags::ClientContext | EAutomationTestFlags::EngineFilter)
bool FProgFinalHourTrigger::RunTest(const FString& Parameters)
{
	const FProgressionTuning Tuning;
	FProgressionProfile Profile = FProgressionRules::MakeEmptyProfile();
	Profile.CompletedRuns = 3;
	TestFalse(TEXT("fresh profile is not maxed"), FProgressionRules::IsAllStatsMaxed(Tuning, Profile));
	TestEqual(TEXT("ordinary scaling"), FProgressionRules::NextRunScaling(Tuning, Profile).Cadence, 1.09, 1e-4);
	for (int32 Index = 0; Index < static_cast<int32>(EProgressionTrack::Count); ++Index)
	{
		Profile.Ranks[Index] = FProgressionRules::TrackMaxRank(Tuning, static_cast<EProgressionTrack>(Index));
	}
	TestTrue(TEXT("maxed"), FProgressionRules::IsAllStatsMaxed(Tuning, Profile));
	TestEqual(TEXT("final hour replaces the ordinary scaling"), FProgressionRules::NextRunScaling(Tuning, Profile).Cadence, 1.35, 1e-4);
	TestEqual(TEXT("maxed costs 61"), FProgressionRules::SpentOnRanks(Tuning, Profile.Ranks), 61);
	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FProgKillXp, "UmbrellaElla.Progression.KillXpTable", EAutomationTestFlags::EditorContext | EAutomationTestFlags::ClientContext | EAutomationTestFlags::EngineFilter)
bool FProgKillXp::RunTest(const FString& Parameters)
{
	const FProgressionTuning Tuning;
	TestEqual(TEXT("roadwarden"), FProgressionRules::KillXp(Tuning, FName(TEXT("Roadwarden"))), 10);
	TestEqual(TEXT("floodstrider"), FProgressionRules::KillXp(Tuning, FName(TEXT("Floodstrider"))), 20);
	TestEqual(TEXT("courier"), FProgressionRules::KillXp(Tuning, FName(TEXT("Courier"))), 10);
	TestEqual(TEXT("wings"), FProgressionRules::KillXp(Tuning, FName(TEXT("Wings"))), 60);
	TestEqual(TEXT("front"), FProgressionRules::KillXp(Tuning, FName(TEXT("Front"))), 60);
	TestEqual(TEXT("middle"), FProgressionRules::KillXp(Tuning, FName(TEXT("Middle"))), 80);
	TestEqual(TEXT("rear"), FProgressionRules::KillXp(Tuning, FName(TEXT("Rear"))), 100);
	TestEqual(TEXT("clock"), FProgressionRules::KillXp(Tuning, FName(TEXT("Clock"))), 150);
	TestEqual(TEXT("courier withdrawal is not a kill"), FProgressionRules::KillXp(Tuning, FName(TEXT("CourierWithdrawal"))), 0);
	TestEqual(TEXT("absorption gives none"), FProgressionRules::KillXp(Tuning, FName(TEXT("Absorb"))), 0);
	TestEqual(TEXT("checkpoint gives none"), FProgressionRules::KillXp(Tuning, FName(TEXT("CP1"))), 0);
	TestEqual(TEXT("none gives none"), FProgressionRules::KillXp(Tuning, NAME_None), 0);
	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FProgBossRollback, "UmbrellaElla.Progression.BossCheckpointRollsBackCoherently", EAutomationTestFlags::EditorContext | EAutomationTestFlags::ClientContext | EAutomationTestFlags::EngineFilter)
bool FProgBossRollback::RunTest(const FString& Parameters)
{
	const FProgressionTuning Tuning;
	FProgressionProfile Profile = FProgressionRules::MakeEmptyProfile();
	FProgressionRules::AddXp(Tuning, Profile, 250);
	TestEqual(TEXT("level 3 at the checkpoint"), FProgressionRules::LevelForXp(Tuning, Profile.Xp).Level, 3);
	TestEqual(TEXT("buy a hit"), static_cast<int32>(FProgressionRules::TryCommitRanks(Tuning, Profile, WithRank(Profile, EProgressionTrack::HitCapacity, 1), Refuge())),
		static_cast<int32>(EProgressionCommit::Ok));
	FProgressionRules::ReachCheckpoint(Profile, EProgressionCheckpointKind::Boss);
	FProgressionRules::AddXp(Tuning, Profile, 1000);
	TestTrue(TEXT("crossed levels after the checkpoint"), FProgressionRules::LevelForXp(Tuning, Profile.Xp).Level > 3);
	FProgressionRules::TryCommitRanks(Tuning, Profile, WithRank(Profile, EProgressionTrack::Lives, 4), Refuge());
	FProgressionRules::DeathRetry(Profile);
	TestEqual(TEXT("xp restored"), Profile.Xp, 250);
	TestEqual(TEXT("level restored"), FProgressionRules::LevelForXp(Tuning, Profile.Xp).Level, 3);
	TestEqual(TEXT("hit rank restored"), FProgressionRules::RankOf(Profile.Ranks, EProgressionTrack::HitCapacity), 1);
	TestEqual(TEXT("post-checkpoint lives rank gone"), FProgressionRules::RankOf(Profile.Ranks, EProgressionTrack::Lives), 0);
	TestEqual(TEXT("points coherent: 2 earned, 1 spent"), FProgressionRules::UnspentPoints(Tuning, Profile), 1);
	TestEqual(TEXT("unlocks follow the restored level"), FProgressionRules::UnlockedSpells(Tuning, FProgressionRules::LevelForXp(Tuning, Profile.Xp).Level).Num(), 1);
	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FProgBossRollbackUnlocks, "UmbrellaElla.Progression.BossRollbackRemovesUnlocksFromRolledBackXp", EAutomationTestFlags::EditorContext | EAutomationTestFlags::ClientContext | EAutomationTestFlags::EngineFilter)
bool FProgBossRollbackUnlocks::RunTest(const FString& Parameters)
{
	const FProgressionTuning Tuning;
	FProgressionProfile Profile = FProgressionRules::MakeEmptyProfile();
	FProgressionRules::ReachCheckpoint(Profile, EProgressionCheckpointKind::Boss);
	FProgressionRules::AddXp(Tuning, Profile, 1000);
	TestTrue(TEXT("streamed blast unlocked at level 10+"), FProgressionRules::IsSpellUnlocked(Tuning, FProgressionRules::LevelForXp(Tuning, Profile.Xp).Level, EProgressionSpell::StreamedBlast));
	FProgressionRules::DeathRetry(Profile);
	TestFalse(TEXT("rolled back with the XP"), FProgressionRules::IsSpellUnlocked(Tuning, FProgressionRules::LevelForXp(Tuning, Profile.Xp).Level, EProgressionSpell::StreamedBlast));
	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FProgLevelRetry, "UmbrellaElla.Progression.LevelCheckpointRetryKeepsXpAndRanks", EAutomationTestFlags::EditorContext | EAutomationTestFlags::ClientContext | EAutomationTestFlags::EngineFilter)
bool FProgLevelRetry::RunTest(const FString& Parameters)
{
	const FProgressionTuning Tuning;
	FProgressionProfile Profile = FProgressionRules::MakeEmptyProfile();
	FProgressionRules::AddXp(Tuning, Profile, 250);
	FProgressionRules::ReachCheckpoint(Profile, EProgressionCheckpointKind::Level);
	FProgressionRules::AddXp(Tuning, Profile, 300);
	FProgressionRules::TryCommitRanks(Tuning, Profile, WithRank(Profile, EProgressionTrack::Lives, 2), Refuge());
	FProgressionRules::DeathRetry(Profile);
	TestEqual(TEXT("xp kept"), Profile.Xp, 550);
	TestEqual(TEXT("ranks kept"), FProgressionRules::RankOf(Profile.Ranks, EProgressionTrack::Lives), 2);
	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FProgQuitReload, "UmbrellaElla.Progression.QuitReloadRestoresLastCheckpoint", EAutomationTestFlags::EditorContext | EAutomationTestFlags::ClientContext | EAutomationTestFlags::EngineFilter)
bool FProgQuitReload::RunTest(const FString& Parameters)
{
	const FProgressionTuning Tuning;
	FProgressionProfile Profile = FProgressionRules::MakeEmptyProfile();
	FProgressionRules::AddXp(Tuning, Profile, 250);
	FProgressionRules::ReachCheckpoint(Profile, EProgressionCheckpointKind::Level);
	FProgressionRules::AddXp(Tuning, Profile, 300);
	FProgressionRules::QuitReload(Profile);
	TestEqual(TEXT("level checkpoint xp"), Profile.Xp, 250);
	FProgressionRules::AddXp(Tuning, Profile, 100);
	FProgressionRules::ReachCheckpoint(Profile, EProgressionCheckpointKind::Boss);
	FProgressionRules::AddXp(Tuning, Profile, 100);
	FProgressionRules::QuitReload(Profile);
	TestEqual(TEXT("boss checkpoint xp"), Profile.Xp, 350);
	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FProgCompleteRun, "UmbrellaElla.Progression.WinKeepsGrowthAndCountsOnce", EAutomationTestFlags::EditorContext | EAutomationTestFlags::ClientContext | EAutomationTestFlags::EngineFilter)
bool FProgCompleteRun::RunTest(const FString& Parameters)
{
	const FProgressionTuning Tuning;
	FProgressionProfile Profile = FProgressionRules::MakeEmptyProfile();
	FProgressionRules::AddXp(Tuning, Profile, 250);
	FProgressionRules::ReachCheckpoint(Profile, EProgressionCheckpointKind::Boss);
	FProgressionRules::CompleteRun(Profile);
	TestEqual(TEXT("completed runs"), Profile.CompletedRuns, 1);
	TestEqual(TEXT("xp kept"), Profile.Xp, 250);
	TestFalse(TEXT("checkpoint cleared"), Profile.bCheckpointValid);
	FProgressionRules::QuitReload(Profile);
	TestEqual(TEXT("reload after a win keeps the growth"), Profile.Xp, 250);
	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FProgPurchaseContext, "UmbrellaElla.Progression.PurchaseVersusReallocation", EAutomationTestFlags::EditorContext | EAutomationTestFlags::ClientContext | EAutomationTestFlags::EngineFilter)
bool FProgPurchaseContext::RunTest(const FString& Parameters)
{
	const FProgressionTuning Tuning;
	FProgressionProfile Profile = FProgressionRules::MakeEmptyProfile();
	FProgressionRules::AddXp(Tuning, Profile, 1000);

	FPurchaseContext None;
	TestFalse(TEXT("no context: inspection only"), FProgressionRules::CanPurchase(None));
	FPurchaseContext Checkpoint;
	Checkpoint.Kind = EPurchaseContextKind::Checkpoint;
	TestFalse(TEXT("a checkpoint alone is not a purchase zone"), FProgressionRules::CanPurchase(Checkpoint));
	FPurchaseContext Dead = Refuge();
	Dead.bAlive = false;
	TestFalse(TEXT("dead"), FProgressionRules::CanPurchase(Dead));
	FPurchaseContext Locked = Refuge();
	Locked.bStoryLocked = true;
	TestFalse(TEXT("story lock"), FProgressionRules::CanPurchase(Locked));
	TestTrue(TEXT("safe refuge"), FProgressionRules::CanPurchase(Refuge()));

	const TArray<int32> Bought = WithRank(Profile, EProgressionTrack::HitCapacity, 2);
	TestEqual(TEXT("denied outside a purchase context"), static_cast<int32>(FProgressionRules::TryCommitRanks(Tuning, Profile, Bought, Checkpoint)), static_cast<int32>(EProgressionCommit::PurchaseNotAllowed));
	TestEqual(TEXT("denied commit changes nothing"), FProgressionRules::RankOf(Profile.Ranks, EProgressionTrack::HitCapacity), 0);
	TestEqual(TEXT("first purchase at a refuge"), static_cast<int32>(FProgressionRules::TryCommitRanks(Tuning, Profile, Bought, Refuge())), static_cast<int32>(EProgressionCommit::Ok));

	const TArray<int32> Refunded = WithRank(Profile, EProgressionTrack::HitCapacity, 0);
	TestEqual(TEXT("no refund on run 1"), static_cast<int32>(FProgressionRules::TryCommitRanks(Tuning, Profile, Refunded, RunStartContext())), static_cast<int32>(EProgressionCommit::RefundNotAllowed));
	Profile.CompletedRuns = 1;
	TestEqual(TEXT("no refund at a refuge on run 2"), static_cast<int32>(FProgressionRules::TryCommitRanks(Tuning, Profile, Refunded, Refuge())), static_cast<int32>(EProgressionCommit::RefundNotAllowed));
	TestEqual(TEXT("refund at the start of run 2"), static_cast<int32>(FProgressionRules::TryCommitRanks(Tuning, Profile, Refunded, RunStartContext())), static_cast<int32>(EProgressionCommit::Ok));
	TestEqual(TEXT("points back"), FProgressionRules::UnspentPoints(Tuning, Profile), FProgressionRules::EarnedPoints(FProgressionRules::LevelForXp(Tuning, Profile.Xp).Level));
	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FProgUpgradeSafety, "UmbrellaElla.Progression.CommitIsAtomicAndGated", EAutomationTestFlags::EditorContext | EAutomationTestFlags::ClientContext | EAutomationTestFlags::EngineFilter)
bool FProgUpgradeSafety::RunTest(const FString& Parameters)
{
	const FProgressionTuning Tuning;
	FProgressionProfile Profile = FProgressionRules::MakeEmptyProfile();
	FProgressionRules::AddXp(Tuning, Profile, 250);
	const FProgressionProfile Before = Profile;

	TestEqual(TEXT("rank II of a three-rank track is gated by level 8"),
		static_cast<int32>(FProgressionRules::TryCommitRanks(Tuning, Profile, WithRank(Profile, EProgressionTrack::SuctionRange, 2), Refuge())), static_cast<int32>(EProgressionCommit::RankGateClosed));
	TestTrue(TEXT("gate failure changed nothing"), Profile == Before);
	TestEqual(TEXT("capacity rank 3 costs 3 points but only 2 are earned"),
		static_cast<int32>(FProgressionRules::TryCommitRanks(Tuning, Profile, WithRank(Profile, EProgressionTrack::HitCapacity, 3), Refuge())), static_cast<int32>(EProgressionCommit::NotEnoughPoints));
	TestEqual(TEXT("rank above the maximum"),
		static_cast<int32>(FProgressionRules::TryCommitRanks(Tuning, Profile, WithRank(Profile, EProgressionTrack::Recovery, 4), Refuge())), static_cast<int32>(EProgressionCommit::InvalidRanks));
	TestTrue(TEXT("still unchanged"), Profile == Before);

	// A mixed stage: one valid track plus one invalid track commits nothing.
	TArray<int32> Mixed = WithRank(Profile, EProgressionTrack::Lives, 1);
	Mixed[static_cast<int32>(EProgressionTrack::DamageNeedle)] = 3;
	TestNotEqual(TEXT("mixed stage refused"), static_cast<int32>(FProgressionRules::TryCommitRanks(Tuning, Profile, Mixed, Refuge())), static_cast<int32>(EProgressionCommit::Ok));
	TestTrue(TEXT("mixed stage changed nothing"), Profile == Before);

	// INV-2: earned equals spent plus unspent after any legal sequence.
	FProgressionRules::TryCommitRanks(Tuning, Profile, WithRank(Profile, EProgressionTrack::Lives, 2), Refuge());
	const int32 Earned = FProgressionRules::EarnedPoints(FProgressionRules::LevelForXp(Tuning, Profile.Xp).Level);
	TestEqual(TEXT("earned = spent + unspent"), Earned, FProgressionRules::SpentOnRanks(Tuning, Profile.Ranks) + FProgressionRules::UnspentPoints(Tuning, Profile));
	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FProgRankValues, "UmbrellaElla.Progression.RankValues", EAutomationTestFlags::EditorContext | EAutomationTestFlags::ClientContext | EAutomationTestFlags::EngineFilter)
bool FProgRankValues::RunTest(const FString& Parameters)
{
	const FProgressionTuning Tuning;
	FProgressionProfile Profile = FProgressionRules::MakeEmptyProfile();
	TestEqual(TEXT("start capacity"), FProgressionRules::HitCapacity(Tuning, Profile.Ranks), 3);
	TestEqual(TEXT("start lives"), FProgressionRules::MaxLives(Tuning, Profile.Ranks), 3);
	const float Heals[] = { 0.5f, 0.8f, 1.1f, 1.4f };
	const float Reductions[] = { 0.0f, 0.1f, 0.2f, 0.3f };
	const float Ranges[] = { 240.0f, 270.0f, 300.0f, 330.0f };
	const float Cones[] = { 60.0f, 70.0f, 80.0f, 90.0f };
	const float Damages[] = { 1.0f, 1.25f, 1.65f, 2.25f };
	for (int32 Rank = 0; Rank <= 3; ++Rank)
	{
		Profile.Ranks[static_cast<int32>(EProgressionTrack::Recovery)] = Rank;
		Profile.Ranks[static_cast<int32>(EProgressionTrack::DamageReduction)] = Rank;
		Profile.Ranks[static_cast<int32>(EProgressionTrack::SuctionRange)] = Rank;
		Profile.Ranks[static_cast<int32>(EProgressionTrack::SuctionCone)] = Rank;
		Profile.Ranks[static_cast<int32>(EProgressionTrack::DamageTwin)] = Rank;
		TestEqual(TEXT("heal per yellow"), FProgressionRules::YellowHealFor(Tuning, Profile.Ranks), Heals[Rank], 1e-4f);
		TestEqual(TEXT("damage reduction"), FProgressionRules::DamageReduction(Tuning, Profile.Ranks), Reductions[Rank], 1e-4f);
		TestEqual(TEXT("suction range"), FProgressionRules::SuctionRange(Tuning, Profile.Ranks), Ranges[Rank], 1e-3f);
		TestEqual(TEXT("suction cone"), FProgressionRules::SuctionConeDegrees(Tuning, Profile.Ranks), Cones[Rank], 1e-3f);
		TestEqual(TEXT("twin damage"), FProgressionRules::SpellDamageMultiplier(Tuning, Profile.Ranks, EProgressionSpell::TwinStars), Damages[Rank], 1e-4f);
		TestEqual(TEXT("small damage untouched"), FProgressionRules::SpellDamageMultiplier(Tuning, Profile.Ranks, EProgressionSpell::SmallBlasts), 1.0f, 1e-4f);
	}
	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FProgFixture, "UmbrellaElla.Progression.DeveloperFixtureLevels", EAutomationTestFlags::EditorContext | EAutomationTestFlags::ClientContext | EAutomationTestFlags::EngineFilter)
bool FProgFixture::RunTest(const FString& Parameters)
{
	const FProgressionTuning Tuning;
	for (int32 Level = 1; Level <= Tuning.LevelCap; ++Level)
	{
		const FProgressionProfile Fixture = FProgressionRules::MakeFixture(Tuning, Level);
		const FLevelProgress Progress = FProgressionRules::LevelForXp(Tuning, Fixture.Xp);
		if (Progress.Level != Level || Progress.PartialXp != 0 || FProgressionRules::UnspentPoints(Tuning, Fixture) != Level - 1
			|| FProgressionRules::SpentOnRanks(Tuning, Fixture.Ranks) != 0)
		{
			AddError(FString::Printf(TEXT("fixture level %d is not level %d / zero partial / %d points / no ranks"), Level, Level, Level - 1));
			return false;
		}
	}
	TestEqual(TEXT("level 62 has 61 points"), FProgressionRules::UnspentPoints(Tuning, FProgressionRules::MakeFixture(Tuning, 62)), 61);
	TestEqual(TEXT("level 30 unlocks all four"), FProgressionRules::UnlockedSpells(Tuning, FProgressionRules::LevelForXp(Tuning, FProgressionRules::MakeFixture(Tuning, 30).Xp).Level).Num(), 4);
	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FProgRingFill, "UmbrellaElla.Progression.RingFillAndMax", EAutomationTestFlags::EditorContext | EAutomationTestFlags::ClientContext | EAutomationTestFlags::EngineFilter)
bool FProgRingFill::RunTest(const FString& Parameters)
{
	const FProgressionTuning Tuning;
	TestEqual(TEXT("empty ring"), FProgressionRules::RingFill(FProgressionRules::LevelForXp(Tuning, 0)), 0.0f, 1e-4f);
	TestEqual(TEXT("half a level"), FProgressionRules::RingFill(FProgressionRules::LevelForXp(Tuning, 50)), 0.5f, 1e-4f);
	TestEqual(TEXT("overflow carries into the next level"), FProgressionRules::RingFill(FProgressionRules::LevelForXp(Tuning, 150)), 0.5f, 1e-4f);
	const FLevelProgress Max = FProgressionRules::LevelForXp(Tuning, 7000);
	TestTrue(TEXT("MAX at 7000"), Max.bMax);
	TestEqual(TEXT("full ring at the cap, no false next-level fill"), FProgressionRules::RingFill(Max), 1.0f, 1e-4f);
	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FProgDraft, "UmbrellaElla.Progression.DraftStagesWithoutChangingLiveValues", EAutomationTestFlags::EditorContext | EAutomationTestFlags::ClientContext | EAutomationTestFlags::EngineFilter)
bool FProgDraft::RunTest(const FString& Parameters)
{
	const FProgressionTuning Tuning;
	FProgressionProfile Real = FProgressionRules::MakeEmptyProfile();
	FProgressionRules::AddXp(Tuning, Real, 250);
	const FProgressionProfile Before = Real;
	FProgressionDraft Draft = FProgressionDraft::Begin(Real);
	TestFalse(TEXT("clean draft"), Draft.IsDirty(Real));
	TestEqual(TEXT("stage a hit"), static_cast<int32>(Draft.Stage(Tuning, Real, Refuge(), EProgressionTrack::HitCapacity, 1)), static_cast<int32>(EProgressionCommit::Ok));
	TestEqual(TEXT("stage a life"), static_cast<int32>(Draft.Stage(Tuning, Real, Refuge(), EProgressionTrack::Lives, 1)), static_cast<int32>(EProgressionCommit::Ok));
	TestEqual(TEXT("a third point is not there"), static_cast<int32>(Draft.Stage(Tuning, Real, Refuge(), EProgressionTrack::Recovery, 1)), static_cast<int32>(EProgressionCommit::NotEnoughPoints));
	TestEqual(TEXT("cost of the draft"), Draft.NetCost(Tuning, Real), 2);
	TestTrue(TEXT("dirty"), Draft.IsDirty(Real));
	TestTrue(TEXT("live profile untouched while staging"), Real == Before);
	TestEqual(TEXT("cannot stage outside a purchase context"), static_cast<int32>(Draft.Stage(Tuning, Real, FPurchaseContext(), EProgressionTrack::Recovery, 1)), static_cast<int32>(EProgressionCommit::PurchaseNotAllowed));
	Draft.Discard(Real);
	TestFalse(TEXT("discard returns to live"), Draft.IsDirty(Real));
	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FProgLevelAfterBoss, "UmbrellaElla.Progression.LevelCheckpointAfterBossCheckpointKeepsRollback", EAutomationTestFlags::EditorContext | EAutomationTestFlags::ClientContext | EAutomationTestFlags::EngineFilter)
bool FProgLevelAfterBoss::RunTest(const FString& Parameters)
{
	// FLOW-13: a level checkpoint reached after a boss checkpoint does not exempt the post-boss gains from rollback.
	const FProgressionTuning Tuning;
	FProgressionProfile Profile = FProgressionRules::MakeEmptyProfile();
	FProgressionRules::AddXp(Tuning, Profile, 250);
	FProgressionRules::ReachCheckpoint(Profile, EProgressionCheckpointKind::Boss);
	FProgressionRules::AddXp(Tuning, Profile, 400);
	FProgressionRules::TryCommitRanks(Tuning, Profile, WithRank(Profile, EProgressionTrack::Lives, 2), Refuge());
	FProgressionRules::ReachCheckpoint(Profile, EProgressionCheckpointKind::Level);
	FProgressionRules::AddXp(Tuning, Profile, 100);
	FProgressionRules::DeathRetry(Profile);
	TestEqual(TEXT("xp back to the boss checkpoint, not the later level checkpoint"), Profile.Xp, 250);
	TestEqual(TEXT("post-boss lives ranks gone"), FProgressionRules::RankOf(Profile.Ranks, EProgressionTrack::Lives), 0);
	TestEqual(TEXT("level coherent"), FProgressionRules::LevelForXp(Tuning, Profile.Xp).Level, 3);
	TestEqual(TEXT("points coherent"), FProgressionRules::UnspentPoints(Tuning, Profile), 2);
	FProgressionRules::ReachCheckpoint(Profile, EProgressionCheckpointKind::Boss);
	TestEqual(TEXT("a new boss checkpoint still replaces the old one"), Profile.CheckpointXp, 250);
	FProgressionRules::CompleteRun(Profile);
	FProgressionRules::ReachCheckpoint(Profile, EProgressionCheckpointKind::Level);
	TestEqual(TEXT("after a won run a level checkpoint is a level checkpoint again"), static_cast<int32>(Profile.CheckpointKind),
		static_cast<int32>(EProgressionCheckpointKind::Level));
	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FProgEffectsOnce, "UmbrellaElla.Progression.EffectsDerivedFromBaselineOnce", EAutomationTestFlags::EditorContext | EAutomationTestFlags::ClientContext | EAutomationTestFlags::EngineFilter)
bool FProgEffectsOnce::RunTest(const FString& Parameters)
{
	// FLOW-17: every value comes from the baseline plus the rank, once; re-deriving or re-committing never compounds.
	const FProgressionTuning Tuning;
	FProgressionProfile Profile = FProgressionRules::MakeEmptyProfile();
	FProgressionRules::AddXp(Tuning, Profile, FProgressionRules::CumulativeXp(Tuning, 30));
	TArray<int32> Ranks = Profile.Ranks;
	Ranks[static_cast<int32>(EProgressionTrack::HitCapacity)] = 2;
	Ranks[static_cast<int32>(EProgressionTrack::Recovery)] = 2;
	Ranks[static_cast<int32>(EProgressionTrack::DamageReduction)] = 2;
	Ranks[static_cast<int32>(EProgressionTrack::SuctionRange)] = 2;
	Ranks[static_cast<int32>(EProgressionTrack::DamageSmall)] = 2;
	TestEqual(TEXT("commit"), static_cast<int32>(FProgressionRules::TryCommitRanks(Tuning, Profile, Ranks, Refuge())), static_cast<int32>(EProgressionCommit::Ok));
	const FProgressionEffects First = FProgressionRules::DeriveEffects(Tuning, Profile.Ranks);
	TestEqual(TEXT("re-commit of the same ranks"), static_cast<int32>(FProgressionRules::TryCommitRanks(Tuning, Profile, Ranks, Refuge())), static_cast<int32>(EProgressionCommit::Ok));
	const FProgressionEffects Second = FProgressionRules::DeriveEffects(Tuning, Profile.Ranks);
	TestTrue(TEXT("deriving again gives the same values"), First == Second);
	TestEqual(TEXT("hits = 3 + 2"), First.HitCapacity, 5);
	TestEqual(TEXT("heal = 0.5 + 2 x 0.3, not compounded"), First.YellowHeal, 1.1f, 1e-4f);
	TestEqual(TEXT("reduction rank II = 0.20 from baseline, not 0.10 + 0.20"), First.DamageReduction, 0.20f, 1e-4f);
	TestEqual(TEXT("suction range = 240 + 2 x 30"), First.SuctionRange, 300.0f, 1e-3f);
	TestEqual(TEXT("small damage rank II = 1.65, not 1.25 x 1.65"), First.SpellDamage[static_cast<int32>(EProgressionSpell::SmallBlasts)], 1.65f, 1e-4f);
	TestEqual(TEXT("lives untouched"), First.MaxLives, 3);
	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FProgDamageOnly, "UmbrellaElla.Progression.DamageRanksChangeOnlyDamage", EAutomationTestFlags::EditorContext | EAutomationTestFlags::ClientContext | EAutomationTestFlags::EngineFilter)
bool FProgDamageOnly::RunTest(const FString& Parameters)
{
	// FLOW-17: a damage rank changes that spell's damage and nothing else progression hands out (rate, geometry,
	// protection, penetration and aim are not progression outputs; no other value may move).
	const FProgressionTuning Tuning;
	const TArray<int32> Base = FProgressionRules::MakeEmptyProfile().Ranks;
	const FProgressionEffects Before = FProgressionRules::DeriveEffects(Tuning, Base);
	const EProgressionTrack DamageTracks[] = { EProgressionTrack::DamageSmall, EProgressionTrack::DamageStreamed, EProgressionTrack::DamageTwin, EProgressionTrack::DamageNeedle };
	for (int32 Index = 0; Index < static_cast<int32>(UE_ARRAY_COUNT(DamageTracks)); ++Index)
	{
		TArray<int32> Ranks = Base;
		Ranks[static_cast<int32>(DamageTracks[Index])] = FProgressionRules::ThreeRankMax;
		FProgressionEffects After = FProgressionRules::DeriveEffects(Tuning, Ranks);
		TestEqual(FString::Printf(TEXT("track %d raises its own spell"), Index), After.SpellDamage[Index], Tuning.SpellDamageRankIII, 1e-4f);
		After.SpellDamage[Index] = Before.SpellDamage[Index];
		TestTrue(FString::Printf(TEXT("track %d moves nothing else"), Index), After == Before);
	}
	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FProgHealthFraction, "UmbrellaElla.Progression.HealthFractionKeptOnCapacityChange", EAutomationTestFlags::EditorContext | EAutomationTestFlags::ClientContext | EAutomationTestFlags::EngineFilter)
bool FProgHealthFraction::RunTest(const FString& Parameters)
{
	// FLOW-17 rule: a capacity purchase or refund keeps the active fraction, unrounded, and never revives an empty life.
	TestEqual(TEXT("full stays full on a buy"), FProgressionRules::ActiveHealthAfterCapacityChange(3.0f, 3.0f, 4.0f), 4.0f, 1e-4f);
	TestEqual(TEXT("two thirds of 3 -> two thirds of 4, no rounding"), FProgressionRules::ActiveHealthAfterCapacityChange(2.0f, 3.0f, 4.0f), 8.0f / 3.0f, 1e-4f);
	TestEqual(TEXT("half of 4 -> half of 3 on a refund"), FProgressionRules::ActiveHealthAfterCapacityChange(2.0f, 4.0f, 3.0f), 1.5f, 1e-4f);
	TestEqual(TEXT("empty stays empty (no resurrection)"), FProgressionRules::ActiveHealthAfterCapacityChange(0.0f, 3.0f, 11.0f), 0.0f, 1e-6f);
	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FProgScaledTimings, "UmbrellaElla.Progression.RunScalingTouchesOnlyCooldownAndHp", EAutomationTestFlags::EditorContext | EAutomationTestFlags::ClientContext | EAutomationTestFlags::EngineFilter)
bool FProgScaledTimings::RunTest(const FString& Parameters)
{
	// FLOW-05/06 rule layer: an ordinary firing cooldown is divided by the cadence multiplier and HP multiplied; nothing else.
	const FProgressionTuning Tuning;
	const FRunScaling Runs10 = FProgressionRules::RunScaling(Tuning, 10, false);
	TestEqual(TEXT("cooldown 2.6 / 1.3"), FProgressionRules::ScaledFiringCooldown(2.6f, Runs10), 2.0f, 1e-4f);
	TestEqual(TEXT("hp 5 x 2"), FProgressionRules::ScaledHp(5.0f, Runs10), 10.0f, 1e-4f);
	const FRunScaling Final = FProgressionRules::RunScaling(Tuning, 1, true);
	TestEqual(TEXT("final hour cooldown 2.7 / 1.35"), FProgressionRules::ScaledFiringCooldown(2.7f, Final), 2.0f, 1e-4f);
	TestEqual(TEXT("final hour hp x2 (replaces, not compounds)"), FProgressionRules::ScaledHp(5.0f, Final), 10.0f, 1e-4f);
	const FRunScaling None = FProgressionRules::RunScaling(Tuning, 0, false);
	TestEqual(TEXT("first run unchanged"), FProgressionRules::ScaledFiringCooldown(2.6f, None), 2.6f, 1e-6f);
	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FProgReview, "UmbrellaElla.Progression.ReviewListsCompleteCostsAndEffects", EAutomationTestFlags::EditorContext | EAutomationTestFlags::ClientContext | EAutomationTestFlags::EngineFilter)
bool FProgReview::RunTest(const FString& Parameters)
{
	// FLOW-42: the review step lists every staged change with its cost and its effect, and the costs add up to the total.
	const FProgressionTuning Tuning;
	FProgressionProfile Real = FProgressionRules::MakeEmptyProfile();
	FProgressionRules::AddXp(Tuning, Real, FProgressionRules::CumulativeXp(Tuning, 10));
	FProgressionDraft Draft = FProgressionDraft::Begin(Real);
	Draft.Stage(Tuning, Real, Refuge(), EProgressionTrack::HitCapacity, 1);
	Draft.Stage(Tuning, Real, Refuge(), EProgressionTrack::Recovery, 1);
	Draft.Stage(Tuning, Real, Refuge(), EProgressionTrack::SuctionRange, 1);
	Draft.Stage(Tuning, Real, Refuge(), EProgressionTrack::SuctionRange, 1);
	const TArray<FProgressionReviewLine> Lines = Draft.Review(Tuning, Real);
	if (!TestEqual(TEXT("three staged tracks, three lines"), Lines.Num(), 3))
	{
		return false;
	}
	int32 Total = 0;
	for (const FProgressionReviewLine& Line : Lines)
	{
		Total += Line.Cost;
	}
	TestEqual(TEXT("costs add up to the draft total"), Total, Draft.NetCost(Tuning, Real));
	TestEqual(TEXT("hits line"), static_cast<int32>(Lines[0].Track), static_cast<int32>(EProgressionTrack::HitCapacity));
	TestEqual(TEXT("hits cost"), Lines[0].Cost, 1);
	TestEqual(TEXT("hits effect before"), Lines[0].ValueBefore, 3.0f, 1e-4f);
	TestEqual(TEXT("hits effect after"), Lines[0].ValueAfter, 4.0f, 1e-4f);
	TestEqual(TEXT("recovery 0.5 -> 0.8"), Lines[1].ValueAfter, 0.8f, 1e-4f);
	TestEqual(TEXT("suction two ranks cost 1 + 2"), Lines[2].Cost, 3);
	TestEqual(TEXT("suction rank 0 -> 2"), Lines[2].ToRank, 2);
	TestEqual(TEXT("suction range 240 -> 300"), Lines[2].ValueAfter, 300.0f, 1e-3f);
	Draft.Stage(Tuning, Real, Refuge(), EProgressionTrack::Recovery, -1);
	TestEqual(TEXT("unstaging removes its line"), Draft.Review(Tuning, Real).Num(), 2);
	return true;
}

#endif
