#include "BrokenMill/BrokenMillRoom.h"
#include "Core/EllaCharacter.h"
#include "Health/UmbrellaHealthComponent.h"
#include "UI/Progression/FinalHourIntroWidget.h"
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
	TestEqual(TEXT("only success completes an encounter"), Rig.Progression->GetCompletedRuns(), 0);
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

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FProgWorldRunStartRealloc, "UmbrellaElla.Progression.World.RunStartReallocationSurvivesBossRetry", EAutomationTestFlags::EditorContext | EAutomationTestFlags::ClientContext | EAutomationTestFlags::EngineFilter)
bool FProgWorldRunStartRealloc::RunTest(const FString& Parameters)
{
	FProgressionRig Rig;
	if (!TestNotNull(TEXT("bus"), Rig.Bus))
	{
		return false;
	}
	Rig.StartDirectorsCut();
	Rig.Kill(TEXT("Clock"));
	Rig.Kill(TEXT("Clock"));
	FPurchaseContext Refuge;
	Refuge.Kind = EPurchaseContextKind::SafeRefuge;
	Rig.Progression->SetPurchaseContext(Refuge);
	TArray<int32> Want = Rig.Progression->GetEffectiveProfile().Ranks;
	Want[static_cast<int32>(EProgressionTrack::HitCapacity)] = 1;
	Rig.Progression->CommitRanks(Want);
	Rig.Send(EUmbrellaEventType::EncounterCompleted, TEXT("success"));
	TestEqual(TEXT("run won"), Rig.Progression->GetCompletedRuns(), 1);

	Rig.StartDirectorsCut();
	FPurchaseContext Start;
	Start.Kind = EPurchaseContextKind::RunStart;
	Rig.Progression->SetPurchaseContext(Start);
	Want[static_cast<int32>(EProgressionTrack::HitCapacity)] = 0;
	Want[static_cast<int32>(EProgressionTrack::Lives)] = 1;
	TestEqual(TEXT("reallocate"), static_cast<int32>(Rig.Progression->CommitRanks(Want)), static_cast<int32>(EProgressionCommit::Ok));
	Rig.Send(EUmbrellaEventType::CheckpointReached, TEXT("Phase2"));
	Rig.Send(EUmbrellaEventType::CheckpointRetried, TEXT("Phase2"));
	TestEqual(TEXT("hit capacity stays reallocated"), Rig.Progression->GetHitCapacity(), 3);
	TestEqual(TEXT("lives stay reallocated"), Rig.Progression->GetRank(EProgressionTrack::Lives), 1);
	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FProgWorldQuitMidRun, "UmbrellaElla.Progression.World.RestartAfterQuitDropsUncheckpointedXp", EAutomationTestFlags::EditorContext | EAutomationTestFlags::ClientContext | EAutomationTestFlags::EngineFilter)
bool FProgWorldQuitMidRun::RunTest(const FString& Parameters)
{
	FProgressionRig Rig;
	if (!TestNotNull(TEXT("bus"), Rig.Bus))
	{
		return false;
	}
	Rig.StartDirectorsCut();
	Rig.Kill(TEXT("Roadwarden"));
	TestTrue(TEXT("xp earned"), Rig.Progression->GetXp() > 0);
	Rig.StartDirectorsCut();
	TestEqual(TEXT("back at the checkpoint"), Rig.Progression->GetXp(), 0);
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

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FProgWorldTutorialReplay, "UmbrellaElla.Progression.World.TutorialReplayUsesShadowProgress", EAutomationTestFlags::EditorContext | EAutomationTestFlags::ClientContext | EAutomationTestFlags::EngineFilter)
bool FProgWorldTutorialReplay::RunTest(const FString& Parameters)
{
	// FLOW-22: a tutorial replay plays on shadow progress; the earned profile and the save come back untouched.
	const FString Slot = TEXT("UmbrellaEllaTest_TutorialReplay");
	FProgressionStore::Delete(Slot);
	FProgressionRig Rig;
	if (!TestNotNull(TEXT("bus"), Rig.Bus))
	{
		return false;
	}
	Rig.Progression->UseSaveSlot(Slot);
	Rig.StartDirectorsCut();
	Rig.Kill(TEXT("Rear"));
	Rig.Send(EUmbrellaEventType::CheckpointReached, TEXT("CP1"));
	Rig.Send(EUmbrellaEventType::ModeSelected, TEXT("TutorialReplay"));
	TestTrue(TEXT("replay is on shadow progress"), Rig.Progression->IsShadowActive() && Rig.Progression->IsTutorialReplay());
	TestEqual(TEXT("replay plays with the earned stats"), Rig.Progression->GetXp(), 100);
	Rig.Kill(TEXT("Clock"));
	Rig.Kill(TEXT("Clock"));
	TestEqual(TEXT("the save never sees replay kills"), FProgressionStore::Load(Slot).Profile.Xp, 100);
	Rig.StartDirectorsCut();
	TestFalse(TEXT("leaving the replay ends the shadow"), Rig.Progression->IsShadowActive());
	TestEqual(TEXT("earned xp restored, no farming"), Rig.Progression->GetXp(), 100);
	TestEqual(TEXT("saved xp unchanged"), FProgressionStore::Load(Slot).Profile.Xp, 100);
	FProgressionStore::Delete(Slot);
	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FProgWorldLivesToHealth, "UmbrellaElla.Progression.World.LifePurchaseRaisesEllaLives", EAutomationTestFlags::EditorContext | EAutomationTestFlags::ClientContext | EAutomationTestFlags::EngineFilter)
bool FProgWorldLivesToHealth::RunTest(const FString& Parameters)
{
	// SURV-06: one point buys +1 life (and +1 hit per life); Ella's health reads the new values after the purchase.
	FProgressionRig Rig;
	if (!TestNotNull(TEXT("bus"), Rig.Bus))
	{
		return false;
	}
	FActorSpawnParameters Params;
	Params.SpawnCollisionHandlingOverride = ESpawnActorCollisionHandlingMethod::AlwaysSpawn;
	AEllaCharacter* Ella = Rig.World->SpawnActor<AEllaCharacter>(AEllaCharacter::StaticClass(), FTransform(FVector::ZeroVector), Params);
	if (!TestNotNull(TEXT("ella"), Ella) || !TestNotNull(TEXT("health"), Ella->GetHealth()))
	{
		return false;
	}
	Rig.StartDirectorsCut();
	TestEqual(TEXT("three lives to start"), Ella->GetHealth()->GetState().MaxLives, 3);
	Rig.Kill(TEXT("Clock"));
	Rig.Kill(TEXT("Clock"));
	FPurchaseContext Refuge;
	Refuge.Kind = EPurchaseContextKind::SafeRefuge;
	Rig.Progression->SetPurchaseContext(Refuge);
	TArray<int32> Want = Rig.Progression->GetEffectiveProfile().Ranks;
	Want[static_cast<int32>(EProgressionTrack::Lives)] = 1;
	TestEqual(TEXT("buy a life"), static_cast<int32>(Rig.Progression->CommitRanks(Want)), static_cast<int32>(EProgressionCommit::Ok));
	TestEqual(TEXT("progression says four lives"), Rig.Progression->GetMaxLives(), 4);
	TestEqual(TEXT("ella has four lives"), Ella->GetHealth()->GetState().MaxLives, 4);
	TestEqual(TEXT("hits per life still three"), Ella->GetHealth()->GetState().Capacity, 3.0f, 1e-4f);
	Want[static_cast<int32>(EProgressionTrack::HitCapacity)] = 1;
	TestEqual(TEXT("buy a hit"), static_cast<int32>(Rig.Progression->CommitRanks(Want)), static_cast<int32>(EProgressionCommit::Ok));
	TestEqual(TEXT("ella has four hits per life"), Ella->GetHealth()->GetState().Capacity, 4.0f, 1e-4f);
	Rig.Send(EUmbrellaEventType::ModeSelected, TEXT("StartGame"));
	TestEqual(TEXT("start game puts ella back to three lives"), Ella->GetHealth()->GetState().MaxLives, 3);
	Ella->Destroy();
	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FProgWorldRetryCapacity, "UmbrellaElla.Progression.World.KeeperRetryRestoresEllaCapacity", EAutomationTestFlags::EditorContext | EAutomationTestFlags::ClientContext | EAutomationTestFlags::EngineFilter)
bool FProgWorldRetryCapacity::RunTest(const FString& Parameters)
{
	// OWL-06 / OWL-10: a Keeper retry uses the checkpoint-restored capacity and max lives (boss checkpoint rolls a later
	// purchase back); a level checkpoint retains it. Progression pushes the result to Ella before she is healed.
	FProgressionRig Rig;
	if (!TestNotNull(TEXT("bus"), Rig.Bus))
	{
		return false;
	}
	FActorSpawnParameters Params;
	Params.SpawnCollisionHandlingOverride = ESpawnActorCollisionHandlingMethod::AlwaysSpawn;
	AEllaCharacter* Ella = Rig.World->SpawnActor<AEllaCharacter>(AEllaCharacter::StaticClass(), FTransform(FVector::ZeroVector), Params);
	if (!TestNotNull(TEXT("ella"), Ella) || !TestNotNull(TEXT("health"), Ella->GetHealth()))
	{
		return false;
	}
	Rig.StartDirectorsCut();
	Rig.Kill(TEXT("Clock"));
	Rig.Kill(TEXT("Clock"));
	FPurchaseContext Refuge;
	Refuge.Kind = EPurchaseContextKind::SafeRefuge;
	Rig.Progression->SetPurchaseContext(Refuge);
	const int32 LivesTrack = static_cast<int32>(EProgressionTrack::Lives);
	const int32 HitsTrack = static_cast<int32>(EProgressionTrack::HitCapacity);
	TArray<int32> Want = Rig.Progression->GetEffectiveProfile().Ranks;
	Rig.Send(EUmbrellaEventType::CheckpointReached, TEXT("Phase2"));
	Want[LivesTrack] = 1;
	Want[HitsTrack] = 1;
	TestEqual(TEXT("buy after the boss checkpoint"), static_cast<int32>(Rig.Progression->CommitRanks(Want)), static_cast<int32>(EProgressionCommit::Ok));
	TestEqual(TEXT("four lives before the loss"), Ella->GetHealth()->GetState().MaxLives, 4);
	TestEqual(TEXT("four hits before the loss"), Ella->GetHealth()->GetState().Capacity, 4.0f, 1e-4f);
	Rig.Send(EUmbrellaEventType::CheckpointRetried, TEXT("Phase2"));
	TestEqual(TEXT("keeper retry restores the checkpoint's max lives"), Ella->GetHealth()->GetState().MaxLives, 3);
	TestEqual(TEXT("keeper retry restores the checkpoint's capacity"), Ella->GetHealth()->GetState().Capacity, 3.0f, 1e-4f);

	// Retained: a purchase made before a level checkpoint is kept by a level retry.
	Rig.StartDirectorsCut();
	TestEqual(TEXT("buy before a level checkpoint"), static_cast<int32>(Rig.Progression->CommitRanks(Want)), static_cast<int32>(EProgressionCommit::Ok));
	Rig.Send(EUmbrellaEventType::CheckpointReached, TEXT("CP1"));
	Rig.Send(EUmbrellaEventType::CheckpointRetried, TEXT("CP1"));
	TestEqual(TEXT("level retry keeps the max lives"), Ella->GetHealth()->GetState().MaxLives, 4);
	TestEqual(TEXT("level retry keeps the capacity"), Ella->GetHealth()->GetState().Capacity, 4.0f, 1e-4f);
	Ella->Destroy();
	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FProgWorldFinalHourIntro, "UmbrellaElla.Progression.World.FinalHourIntroBeforeExtremeRun", EAutomationTestFlags::EditorContext | EAutomationTestFlags::ClientContext | EAutomationTestFlags::EngineFilter)
bool FProgWorldFinalHourIntro::RunTest(const FString& Parameters)
{
	// FLOW-06: when every stat is maxed, the next Director's Cut run shows the Final Hour intro (exact text) as it starts.
	FProgressionRig Rig;
	if (!TestNotNull(TEXT("bus"), Rig.Bus))
	{
		return false;
	}
	TestEqual(TEXT("approved exact text"), UFinalHourIntroWidget::IntroText().ToString(),
		FString(TEXT("Her time has run its course. The owl is coming.")));
	const TSharedRef<bool> RunWasExtremeWhenShown = MakeShared<bool>(false);
	UProgressionSubsystem* Progression = Rig.Progression.Get();
	const FDelegateHandle Handle = Rig.Progression->OnFinalHourIntro().AddLambda([Progression, RunWasExtremeWhenShown]()
	{
		*RunWasExtremeWhenShown = Progression->IsFinalHourRun() && Progression->GetRunScaling().Hp > 1.0;
	});
	Rig.StartDirectorsCut();
	TestEqual(TEXT("no intro on an ordinary run"), Rig.Progression->GetFinalHourIntroCount(), 0);
	const FProgressionTuning& Tuning = Rig.Progression->GetTuning();
	while (Rig.Progression->GetLevel() < Tuning.LevelCap)
	{
		Rig.Kill(TEXT("Clock"));
	}
	FPurchaseContext Refuge;
	Refuge.Kind = EPurchaseContextKind::SafeRefuge;
	Rig.Progression->SetPurchaseContext(Refuge);
	TArray<int32> Max = Rig.Progression->GetEffectiveProfile().Ranks;
	for (int32 Index = 0; Index < Max.Num(); ++Index)
	{
		Max[Index] = FProgressionRules::TrackMaxRank(Tuning, static_cast<EProgressionTrack>(Index));
	}
	TestEqual(TEXT("max every stat"), static_cast<int32>(Rig.Progression->CommitRanks(Max)), static_cast<int32>(EProgressionCommit::Ok));
	TestEqual(TEXT("still no intro mid-run"), Rig.Progression->GetFinalHourIntroCount(), 0);
	Rig.Send(EUmbrellaEventType::RunCompleted, TEXT("success"));
	Rig.StartDirectorsCut();
	TestEqual(TEXT("intro shown once at the Extreme run start"), Rig.Progression->GetFinalHourIntroCount(), 1);
	TestTrue(TEXT("the run it announces is the Extreme run"), *RunWasExtremeWhenShown);
	TestEqual(TEXT("final hour hp x2"), Rig.Progression->GetRunScaling().Hp, 2.0, 1e-6);
	Rig.Progression->OnFinalHourIntro().Remove(Handle);
	return true;
}

#endif
