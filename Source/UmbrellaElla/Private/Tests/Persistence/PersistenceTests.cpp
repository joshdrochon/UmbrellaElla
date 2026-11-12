#include "Misc/AutomationTest.h"
#include "Persistence/ProgressionSaveGame.h"
#include "Progression/ProgressionRules.h"
#include "Progression/ProgressionTuning.h"

#if WITH_AUTOMATION_TESTS

namespace
{
	/** A save slot used by one test only, deleted when the test ends so Saved/SaveGames is unchanged. */
	struct FTestSlot
	{
		FString Name;
		explicit FTestSlot(const TCHAR* Suffix) : Name(FString(TEXT("UmbrellaEllaTest_")) + Suffix) { FProgressionStore::Delete(Name); }
		~FTestSlot() { FProgressionStore::Delete(Name); }
	};

	FProgressionProfile SampleProfile(int32 Xp)
	{
		const FProgressionTuning Tuning;
		FProgressionProfile Profile = FProgressionRules::MakeEmptyProfile();
		FProgressionRules::AddXp(Tuning, Profile, Xp);
		Profile.Ranks[static_cast<int32>(EProgressionTrack::Lives)] = 2;
		Profile.CompletedRuns = 2;
		FProgressionRules::ReachCheckpoint(Profile, EProgressionCheckpointKind::Boss);
		return Profile;
	}
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FPersistRoundTrip, "UmbrellaElla.Persistence.RoundTrip",
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::ClientContext | EAutomationTestFlags::EngineFilter)
bool FPersistRoundTrip::RunTest(const FString& Parameters)
{
	const FTestSlot Slot(TEXT("RoundTrip"));
	TestEqual(TEXT("fresh when empty"), static_cast<int32>(FProgressionStore::Load(Slot.Name).Status), static_cast<int32>(EProgressionLoadStatus::Fresh));
	const FProgressionProfile Saved = SampleProfile(777);
	FProgressionStore::Save(Slot.Name, Saved);
	const FProgressionLoadResult Loaded = FProgressionStore::Load(Slot.Name);
	TestEqual(TEXT("loaded"), static_cast<int32>(Loaded.Status), static_cast<int32>(EProgressionLoadStatus::Loaded));
	TestTrue(TEXT("every field survives"), Loaded.Profile == Saved);
	TestEqual(TEXT("xp"), Loaded.Profile.Xp, 777);
	TestEqual(TEXT("lives rank"), FProgressionRules::RankOf(Loaded.Profile.Ranks, EProgressionTrack::Lives), 2);
	TestEqual(TEXT("checkpoint xp"), Loaded.Profile.CheckpointXp, 777);
	TestTrue(TEXT("checkpoint valid"), Loaded.Profile.bCheckpointValid);
	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FPersistBackup, "UmbrellaElla.Persistence.CorruptMainFallsBackToBackup",
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::ClientContext | EAutomationTestFlags::EngineFilter)
bool FPersistBackup::RunTest(const FString& Parameters)
{
	const FTestSlot Slot(TEXT("Backup"));
	const FProgressionProfile First = SampleProfile(300);
	const FProgressionProfile Second = SampleProfile(900);
	FProgressionStore::Save(Slot.Name, First);
	TestEqual(TEXT("second save also writes the backup"), FProgressionStore::Save(Slot.Name, Second), 2);
	FProgressionStore::WriteSlot(Slot.Name, Second, FProgressionStore::ComputeChecksum(Second) + 1);
	const FProgressionLoadResult Loaded = FProgressionStore::Load(Slot.Name);
	TestEqual(TEXT("backup used"), static_cast<int32>(Loaded.Status), static_cast<int32>(EProgressionLoadStatus::LoadedFromBackup));
	TestEqual(TEXT("backup holds the previous good copy"), Loaded.Profile.Xp, 300);
	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FPersistBlocked, "UmbrellaElla.Persistence.TwoCorruptCopiesBlock",
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::ClientContext | EAutomationTestFlags::EngineFilter)
bool FPersistBlocked::RunTest(const FString& Parameters)
{
	const FTestSlot Slot(TEXT("Blocked"));
	const FProgressionProfile Profile = SampleProfile(300);
	FProgressionStore::WriteSlot(Slot.Name, Profile, FProgressionStore::ComputeChecksum(Profile) + 1);
	FProgressionStore::WriteSlot(FProgressionStore::BackupSlotName(Slot.Name), Profile, FProgressionStore::ComputeChecksum(Profile) + 2);
	const FProgressionLoadResult Loaded = FProgressionStore::Load(Slot.Name);
	TestEqual(TEXT("blocked, not silently erased"), static_cast<int32>(Loaded.Status), static_cast<int32>(EProgressionLoadStatus::BlockedCorrupt));
	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FPersistChecksum, "UmbrellaElla.Persistence.ChecksumSeesEveryField",
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::ClientContext | EAutomationTestFlags::EngineFilter)
bool FPersistChecksum::RunTest(const FString& Parameters)
{
	const FProgressionProfile Base = SampleProfile(300);
	const int32 Sum = FProgressionStore::ComputeChecksum(Base);
	TestEqual(TEXT("stable"), FProgressionStore::ComputeChecksum(Base), Sum);
	FProgressionProfile Changed = Base;
	Changed.Xp += 1;
	TestNotEqual(TEXT("xp"), FProgressionStore::ComputeChecksum(Changed), Sum);
	Changed = Base;
	Changed.Ranks[0] += 1;
	TestNotEqual(TEXT("rank"), FProgressionStore::ComputeChecksum(Changed), Sum);
	Changed = Base;
	Changed.CheckpointRanks[1] += 1;
	TestNotEqual(TEXT("checkpoint rank"), FProgressionStore::ComputeChecksum(Changed), Sum);
	Changed = Base;
	Changed.CompletedRuns += 1;
	TestNotEqual(TEXT("runs"), FProgressionStore::ComputeChecksum(Changed), Sum);
	return true;
}

#endif
