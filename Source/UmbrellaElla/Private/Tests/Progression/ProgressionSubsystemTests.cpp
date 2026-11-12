#include "BrokenMill/BrokenMillRoom.h"
#include "Core/UmbrellaEventBus.h"
#include "Enemy/UmbrellaEnemy.h"
#include "Engine/Engine.h"
#include "Engine/GameInstance.h"
#include "Engine/World.h"
#include "Misc/AutomationTest.h"
#include "Persistence/ProgressionSaveGame.h"
#include "Progression/ProgressionSubsystem.h"
#include "UObject/StrongObjectPtr.h"

#if WITH_AUTOMATION_TESTS

namespace
{
	/** A transient world (for its event bus) and a subsystem bound to it. */
	struct FProgressionRig
	{
		UWorld* World = nullptr;
		UUmbrellaEventBus* Bus = nullptr;
		TStrongObjectPtr<UGameInstance> Instance;
		TStrongObjectPtr<UProgressionSubsystem> Progression;
		int32 XpEvents = 0;
		int32 LastXpAmount = 0;
		int32 LevelEvents = 0;
		int32 LastLevel = 0;
		FDelegateHandle XpHandle;
		FDelegateHandle LevelHandle;

		FProgressionRig()
		{
			World = UWorld::CreateWorld(EWorldType::Game, false);
			GEngine->CreateNewWorldContext(EWorldType::Game).SetCurrentWorld(World);
			Bus = UUmbrellaEventBus::Get(World);
			Instance.Reset(NewObject<UGameInstance>(GEngine));
			Progression.Reset(NewObject<UProgressionSubsystem>(Instance.Get()));
			if (Bus != nullptr)
			{
				Progression->BindToBus(Bus);
				XpHandle = Bus->On(EUmbrellaEventType::XPAwarded).AddRaw(this, &FProgressionRig::OnXp);
				LevelHandle = Bus->On(EUmbrellaEventType::LevelGained).AddRaw(this, &FProgressionRig::OnLevel);
			}
		}

		~FProgressionRig()
		{
			if (Bus != nullptr)
			{
				Bus->On(EUmbrellaEventType::XPAwarded).Remove(XpHandle);
				Bus->On(EUmbrellaEventType::LevelGained).Remove(LevelHandle);
			}
			Progression->UnbindFromBus();
			Progression.Reset();
			Instance.Reset();
			GEngine->DestroyWorldContext(World);
			World->DestroyWorld(false);
		}

		void OnXp(const FUmbrellaEvent& Event) { ++XpEvents; LastXpAmount = Event.Amount; }
		void OnLevel(const FUmbrellaEvent& Event) { ++LevelEvents; LastLevel = Event.Amount; }

		void Send(EUmbrellaEventType Type, const TCHAR* Detail)
		{
			FUmbrellaEvent Event;
			Event.Type = Type;
			Event.Detail = FName(Detail);
			Bus->Broadcast(Event);
		}

		void StartDirectorsCut() { Send(EUmbrellaEventType::ModeSelected, TEXT("DirectorsCut")); }
		void Kill(const TCHAR* Label) { Send(EUmbrellaEventType::BossPartDestroyed, Label); }
	};
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FProgWorldStartGame, "UmbrellaElla.Progression.World.StartGameGivesNoXp", EAutomationTestFlags::EditorContext | EAutomationTestFlags::ClientContext | EAutomationTestFlags::EngineFilter)
bool FProgWorldStartGame::RunTest(const FString& Parameters)
{
	FProgressionRig Rig;
	if (!TestNotNull(TEXT("bus"), Rig.Bus))
	{
		return false;
	}
	Rig.Send(EUmbrellaEventType::ModeSelected, TEXT("StartGame"));
	Rig.Kill(TEXT("Roadwarden"));
	Rig.Kill(TEXT("Clock"));
	TestEqual(TEXT("no xp"), Rig.Progression->GetXp(), 0);
	TestEqual(TEXT("level 1"), Rig.Progression->GetLevel(), 1);
	TestEqual(TEXT("no xp event"), Rig.XpEvents, 0);
	TestEqual(TEXT("three hits"), Rig.Progression->GetHitCapacity(), 3);
	TestEqual(TEXT("three lives"), Rig.Progression->GetMaxLives(), 3);
	TestEqual(TEXT("small blasts only"), Rig.Progression->GetUnlockedSpells().Num(), 1);
	TestEqual(TEXT("direct award refused"), Rig.Progression->AwardKill(FName(TEXT("Clock"))), 0);
	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FProgWorldKills, "UmbrellaElla.Progression.World.KillsAwardXpAndLevels", EAutomationTestFlags::EditorContext | EAutomationTestFlags::ClientContext | EAutomationTestFlags::EngineFilter)
bool FProgWorldKills::RunTest(const FString& Parameters)
{
	FProgressionRig Rig;
	if (!TestNotNull(TEXT("bus"), Rig.Bus))
	{
		return false;
	}
	Rig.StartDirectorsCut();
	TestEqual(TEXT("starting the mode gives no xp"), Rig.Progression->GetXp(), 0);
	Rig.Kill(TEXT("Floodstrider"));
	TestEqual(TEXT("xp"), Rig.Progression->GetXp(), 20);
	TestEqual(TEXT("xp event amount"), Rig.LastXpAmount, 20);
	Rig.Send(EUmbrellaEventType::BossPartDestroyed, TEXT("Enemy"));
	TestEqual(TEXT("unlabelled enemy gives none"), Rig.Progression->GetXp(), 20);
	Rig.Kill(TEXT("CourierWithdrawal"));
	TestEqual(TEXT("withdrawal gives none"), Rig.Progression->GetXp(), 20);
	Rig.Send(EUmbrellaEventType::CheckpointReached, TEXT("CP1"));
	TestEqual(TEXT("checkpoint passage gives none"), Rig.Progression->GetXp(), 20);
	for (int32 Index = 0; Index < 8; ++Index)
	{
		Rig.Kill(TEXT("Clock"));
	}
	TestEqual(TEXT("1220 xp"), Rig.Progression->GetXp(), 1220);
	TestEqual(TEXT("level"), Rig.Progression->GetLevel(), 12);
	TestEqual(TEXT("level events fired once per kill that crossed"), Rig.LevelEvents > 0, true);
	TestEqual(TEXT("last level event"), Rig.LastLevel, 12);
	TestEqual(TEXT("one point per level"), Rig.Progression->GetUnspentPoints(), 11);
	TestTrue(TEXT("streamed unlocked"), Rig.Progression->IsSpellUnlocked(EProgressionSpell::StreamedBlast));
	TestFalse(TEXT("twin locked"), Rig.Progression->IsSpellUnlocked(EProgressionSpell::TwinStars));
	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FProgWorldRetry, "UmbrellaElla.Progression.World.LevelRetryKeepsXpAndRewardsAgain", EAutomationTestFlags::EditorContext | EAutomationTestFlags::ClientContext | EAutomationTestFlags::EngineFilter)
bool FProgWorldRetry::RunTest(const FString& Parameters)
{
	FProgressionRig Rig;
	if (!TestNotNull(TEXT("bus"), Rig.Bus))
	{
		return false;
	}
	Rig.StartDirectorsCut();
	Rig.Send(EUmbrellaEventType::CheckpointReached, TEXT("CP1"));
	Rig.Kill(TEXT("Roadwarden"));
	Rig.Send(EUmbrellaEventType::CheckpointRetried, TEXT("CP1"));
	TestEqual(TEXT("xp kept after a level retry"), Rig.Progression->GetXp(), 10);
	Rig.Kill(TEXT("Roadwarden"));
	TestEqual(TEXT("the same enemy pays again"), Rig.Progression->GetXp(), 20);
	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FProgWorldBossRollback, "UmbrellaElla.Progression.World.BossRetryRollsBackXpAndPartsPayAgain", EAutomationTestFlags::EditorContext | EAutomationTestFlags::ClientContext | EAutomationTestFlags::EngineFilter)
bool FProgWorldBossRollback::RunTest(const FString& Parameters)
{
	FProgressionRig Rig;
	if (!TestNotNull(TEXT("bus"), Rig.Bus))
	{
		return false;
	}
	Rig.StartDirectorsCut();
	Rig.Kill(TEXT("Roadwarden"));
	Rig.Send(EUmbrellaEventType::CheckpointReached, TEXT("Phase2"));
	Rig.Kill(TEXT("Front"));
	Rig.Kill(TEXT("Middle"));
	TestEqual(TEXT("xp before the loss"), Rig.Progression->GetXp(), 150);
	Rig.Send(EUmbrellaEventType::CheckpointRetried, TEXT("Phase2"));
	TestEqual(TEXT("rolled back to the boss checkpoint"), Rig.Progression->GetXp(), 10);
	Rig.Kill(TEXT("Front"));
	TestEqual(TEXT("the part pays again only when defeated again"), Rig.Progression->GetXp(), 70);
	Rig.Send(EUmbrellaEventType::CheckpointRetried, TEXT("Phase2"));
	Rig.Progression->QuitAndReload();
	TestEqual(TEXT("quit and reload: the checkpoint's xp"), Rig.Progression->GetXp(), 10);
	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FProgWorldRuns, "UmbrellaElla.Progression.World.OnlyAWonRunAdvancesScaling", EAutomationTestFlags::EditorContext | EAutomationTestFlags::ClientContext | EAutomationTestFlags::EngineFilter)
bool FProgWorldRuns::RunTest(const FString& Parameters)
{
	FProgressionRig Rig;
	if (!TestNotNull(TEXT("bus"), Rig.Bus))
	{
		return false;
	}
	Rig.StartDirectorsCut();
	Rig.Kill(TEXT("Rear"));
	Rig.Send(EUmbrellaEventType::CheckpointRetried, TEXT("CP1"));
	Rig.Progression->QuitAndReload();
	TestEqual(TEXT("loss and quit do not count"), Rig.Progression->GetCompletedRuns(), 0);
	TestEqual(TEXT("run 1 scaling"), Rig.Progression->GetRunScaling().Hp, 1.0, 1e-4);

	Rig.StartDirectorsCut();
	Rig.Kill(TEXT("Rear"));
	Rig.Send(EUmbrellaEventType::EncounterCompleted, TEXT("Win"));
	Rig.Send(EUmbrellaEventType::RunCompleted, TEXT("Win"));
	TestEqual(TEXT("a win counts once"), Rig.Progression->GetCompletedRuns(), 1);
	TestEqual(TEXT("growth kept"), Rig.Progression->GetXp(), 100);
	Rig.StartDirectorsCut();
	TestEqual(TEXT("next run hp x1.1"), Rig.Progression->GetRunScaling().Hp, 1.1, 1e-4);
	TestEqual(TEXT("next run cadence x1.03"), Rig.Progression->GetRunScaling().Cadence, 1.03, 1e-4);
	TestFalse(TEXT("not the final hour"), Rig.Progression->IsFinalHourRun());
	TestEqual(TEXT("xp survives into the next run"), Rig.Progression->GetXp(), 100);
	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FProgWorldPurchase, "UmbrellaElla.Progression.World.PurchaseNeedsContext", EAutomationTestFlags::EditorContext | EAutomationTestFlags::ClientContext | EAutomationTestFlags::EngineFilter)
bool FProgWorldPurchase::RunTest(const FString& Parameters)
{
	FProgressionRig Rig;
	if (!TestNotNull(TEXT("bus"), Rig.Bus))
	{
		return false;
	}
	Rig.StartDirectorsCut();
	Rig.Kill(TEXT("Clock"));
	Rig.Kill(TEXT("Clock"));
	TArray<int32> Want = Rig.Progression->GetEffectiveProfile().Ranks;
	Want[static_cast<int32>(EProgressionTrack::HitCapacity)] = 1;
	TestEqual(TEXT("browsing is inspection-only"), static_cast<int32>(Rig.Progression->CommitRanks(Want)), static_cast<int32>(EProgressionCommit::PurchaseNotAllowed));
	TestEqual(TEXT("hit capacity unchanged"), Rig.Progression->GetHitCapacity(), 3);
	FPurchaseContext Refuge;
	Refuge.Kind = EPurchaseContextKind::SafeRefuge;
	Rig.Progression->SetPurchaseContext(Refuge);
	TestTrue(TEXT("can purchase at a refuge"), Rig.Progression->CanPurchaseNow());
	TestEqual(TEXT("commit"), static_cast<int32>(Rig.Progression->CommitRanks(Want)), static_cast<int32>(EProgressionCommit::Ok));
	TestEqual(TEXT("four hits per life"), Rig.Progression->GetHitCapacity(), 4);
	TestEqual(TEXT("two earned, one spent"), Rig.Progression->GetUnspentPoints(), 1);
	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FProgWorldPersist, "UmbrellaElla.Progression.World.ProfileSurvivesRelaunch", EAutomationTestFlags::EditorContext | EAutomationTestFlags::ClientContext | EAutomationTestFlags::EngineFilter)
bool FProgWorldPersist::RunTest(const FString& Parameters)
{
	const FString Slot = TEXT("UmbrellaEllaTest_Subsystem");
	FProgressionStore::Delete(Slot);
	{
		FProgressionRig First;
		if (!TestNotNull(TEXT("bus"), First.Bus))
		{
			return false;
		}
		First.Progression->UseSaveSlot(Slot);
		First.StartDirectorsCut();
		First.Send(EUmbrellaEventType::CheckpointReached, TEXT("CP1"));
		First.Kill(TEXT("Rear"));
		First.Kill(TEXT("Rear"));
		First.Send(EUmbrellaEventType::CheckpointReached, TEXT("CP2"));
		First.Kill(TEXT("Floodstrider"));
	}
	{
		FProgressionRig Second;
		Second.Progression->UseSaveSlot(Slot);
		Second.Progression->SetPlayMode(EUmbrellaPlayMode::DirectorsCut);
		TestEqual(TEXT("a relaunch restores the last checkpoint, not the XP after it"), Second.Progression->GetXp(), 200);
		TestEqual(TEXT("status"), static_cast<int32>(Second.Progression->GetLoadStatus()), static_cast<int32>(EProgressionLoadStatus::Loaded));
	}
	FProgressionStore::Delete(Slot);
	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FProgWorldShadow, "UmbrellaElla.Progression.World.ShadowProgressNeverTouchesTheProfile", EAutomationTestFlags::EditorContext | EAutomationTestFlags::ClientContext | EAutomationTestFlags::EngineFilter)
bool FProgWorldShadow::RunTest(const FString& Parameters)
{
	const FString Slot = TEXT("UmbrellaEllaTest_Shadow");
	FProgressionStore::Delete(Slot);
	FProgressionRig Rig;
	if (!TestNotNull(TEXT("bus"), Rig.Bus))
	{
		return false;
	}
	Rig.Progression->UseSaveSlot(Slot);
	Rig.StartDirectorsCut();
	Rig.Kill(TEXT("Rear"));
	Rig.Progression->BeginShadowProgress(30);
	TestTrue(TEXT("shadow on"), Rig.Progression->IsShadowActive());
	TestEqual(TEXT("fixture level"), Rig.Progression->GetLevel(), 30);
	TestEqual(TEXT("29 points"), Rig.Progression->GetUnspentPoints(), 29);
	TestTrue(TEXT("needle unlocked"), Rig.Progression->IsSpellUnlocked(EProgressionSpell::NeedleSpell));
	Rig.Kill(TEXT("Rear"));
	Rig.Progression->EndShadowProgress();
	TestEqual(TEXT("real xp restored"), Rig.Progression->GetXp(), 100);
	TestEqual(TEXT("the saved copy never saw the shadow"), FProgressionStore::Load(Slot).Profile.Xp, 100);
	FProgressionStore::Delete(Slot);
	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FProgWorldRealEnemies, "UmbrellaElla.Progression.World.RealEnemyAndMillKillsPayXp", EAutomationTestFlags::EditorContext | EAutomationTestFlags::ClientContext | EAutomationTestFlags::EngineFilter)
bool FProgWorldRealEnemies::RunTest(const FString& Parameters)
{
	FProgressionRig Rig;
	if (!TestNotNull(TEXT("bus"), Rig.Bus))
	{
		return false;
	}
	Rig.StartDirectorsCut();
	FUmbrellaShotSpec Blast;
	Blast.Kind = EUmbrellaShotKind::PlayerBlast;
	Blast.Damage = 1000.0f;
	const struct { EEnemyType Type; int32 Xp; } Cases[] = {
		{ EEnemyType::Roadwarden, 10 }, { EEnemyType::Floodstrider, 20 }, { EEnemyType::SkyCourier, 10 } };
	int32 Expected = 0;
	for (const auto& Case : Cases)
	{
		AUmbrellaEnemy* Enemy = Rig.World->SpawnActor<AUmbrellaEnemy>();
		if (!TestNotNull(TEXT("enemy"), Enemy))
		{
			return false;
		}
		Enemy->Configure(Case.Type, EEnemyGender::Male, EUmbrellaShotKind::EnemyRed);
		Enemy->ReceiveShot(Blast, FVector::ZeroVector);
		Expected += Case.Xp;
		TestEqual(*FString::Printf(TEXT("xp after %s"), *Enemy->GetName()), Rig.Progression->GetXp(), Expected);
		Enemy->ReceiveShot(Blast, FVector::ZeroVector);
		TestEqual(TEXT("a defeated enemy pays once"), Rig.Progression->GetXp(), Expected);
	}
	ABrokenMillRoom* Room = Rig.World->SpawnActor<ABrokenMillRoom>();
	if (TestNotNull(TEXT("room"), Room))
	{
		Room->ReceiveShot(Blast, FVector::ZeroVector);
		TestEqual(TEXT("mill guard pays Roadwarden xp"), Rig.Progression->GetXp(), Expected + 10);
	}
	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FProgWorldKeeperEvents, "UmbrellaElla.Progression.World.KeeperEventStringsDriveXpAndCheckpoints", EAutomationTestFlags::EditorContext | EAutomationTestFlags::ClientContext | EAutomationTestFlags::EngineFilter)
bool FProgWorldKeeperEvents::RunTest(const FString& Parameters)
{
	FProgressionRig Rig;
	if (!TestNotNull(TEXT("bus"), Rig.Bus))
	{
		return false;
	}
	Rig.StartDirectorsCut();
	auto Keeper = [&Rig](EUmbrellaEventType Type, const TCHAR* Detail, const TCHAR* Target)
	{
		FUmbrellaEvent Event;
		Event.Type = Type;
		Event.SourceId = FName(TEXT("KeeperOfTime"));
		Event.TargetId = FName(Target);
		Event.Detail = FName(Detail);
		Rig.Bus->Broadcast(Event);
	};
	Keeper(EUmbrellaEventType::PhaseStarted, TEXT("wings"), TEXT("KeeperOfTime"));
	Keeper(EUmbrellaEventType::CheckpointReached, TEXT("wings"), TEXT("KeeperOfTime"));
	Keeper(EUmbrellaEventType::BossPartDestroyed, TEXT("wings"), TEXT("WINGS"));
	TestEqual(TEXT("wings"), Rig.Progression->GetXp(), 60);
	Keeper(EUmbrellaEventType::BossPartDestroyed, TEXT("mechanisms"), TEXT("MECH_FRONT"));
	Keeper(EUmbrellaEventType::BossPartDestroyed, TEXT("mechanisms"), TEXT("MECH_MIDDLE"));
	Keeper(EUmbrellaEventType::BossPartDestroyed, TEXT("mechanisms"), TEXT("MECH_REAR"));
	TestEqual(TEXT("mechanisms 60+80+100"), Rig.Progression->GetXp(), 300);
	Keeper(EUmbrellaEventType::BossPartDestroyed, TEXT("clock"), TEXT("EYE"));
	TestEqual(TEXT("the eye pays nothing"), Rig.Progression->GetXp(), 300);
	Keeper(EUmbrellaEventType::CheckpointRetried, TEXT("mechanisms"), TEXT("Player"));
	TestEqual(TEXT("keeper phase checkpoint is a boss checkpoint: retry rolls xp back to it"), Rig.Progression->GetXp(), 0);
	Keeper(EUmbrellaEventType::BossPartDestroyed, TEXT("clock"), TEXT("CLOCK"));
	TestEqual(TEXT("clock"), Rig.Progression->GetXp(), 150);
	Keeper(EUmbrellaEventType::EncounterCompleted, TEXT("success"), TEXT("KeeperOfTime"));
	TestEqual(TEXT("win keeps xp"), Rig.Progression->GetXp(), 150);
	return true;
}

#endif
