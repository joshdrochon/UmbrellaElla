#include "Engine/Engine.h"
#include "Core/UmbrellaEventBus.h"
#include "Engine/World.h"
#include "EngineUtils.h"
#include "Enemy/EnemyRules.h"
#include "Enemy/EnemyTuning.h"
#include "Enemy/UmbrellaEnemy.h"
#include "Engine/StaticMeshActor.h"
#include "Misc/AutomationTest.h"
#include "Projectile/UmbrellaProjectile.h"

#if WITH_AUTOMATION_TESTS

#define UMBRELLAELLA_ENEMY_FLAGS (EAutomationTestFlags::EditorContext | EAutomationTestFlags::ClientContext | EAutomationTestFlags::EngineFilter)

namespace
{
	struct FEventProbe
	{
		TArray<FUmbrellaEvent> Seen;
		void OnEvent(const FUmbrellaEvent& Event) { Seen.Add(Event); }
	};

	FUmbrellaShotSpec BlastOf(float Damage)
	{
		FUmbrellaShotSpec Spec;
		Spec.Kind = EUmbrellaShotKind::PlayerBlast;
		Spec.Damage = Damage;
		return Spec;
	}

	UWorld* MakeWorld()
	{
		UWorld* World = UWorld::CreateWorld(EWorldType::Game, false);
		FWorldContext& Context = GEngine->CreateNewWorldContext(EWorldType::Game);
		Context.SetCurrentWorld(World);
		return World;
	}

	void DropWorld(UWorld* World)
	{
		GEngine->DestroyWorldContext(World);
		World->DestroyWorld(false);
	}
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FEnemyProfilesMatchGdd, "UmbrellaElla.Enemy.ProfilesMatchGdd", UMBRELLAELLA_ENEMY_FLAGS)
bool FEnemyProfilesMatchGdd::RunTest(const FString& Parameters)
{
	const FEnemyTuning Tuning;
	const FEnemyProfile Road = FEnemyRules::MakeProfile(EEnemyType::Roadwarden, Tuning);
	const FEnemyProfile Flood = FEnemyRules::MakeProfile(EEnemyType::Floodstrider, Tuning);
	const FEnemyProfile Courier = FEnemyRules::MakeProfile(EEnemyType::SkyCourier, Tuning);
	TestEqual(TEXT("roadwarden hp"), Road.Hp, 40.0f);
	TestEqual(TEXT("roadwarden span"), Road.PatrolSpan, 300.0f);
	TestEqual(TEXT("roadwarden speed"), Road.PatrolSpeed, 90.0f);
	TestEqual(TEXT("roadwarden shot speed"), Road.ShotSpeed, 240.0f);
	TestTrue(TEXT("roadwarden cycle at least 2.5"), Road.AimSeconds + Road.GetPostFireSeconds() >= 2.5f);
	TestTrue(TEXT("roadwarden recovery at least 1"), Road.GetPostFireSeconds() >= 1.0f);
	TestEqual(TEXT("floodstrider hp"), Flood.Hp, 60.0f);
	TestEqual(TEXT("floodstrider aim"), Flood.AimSeconds, 1.1f);
	TestEqual(TEXT("floodstrider shot speed"), Flood.ShotSpeed, 220.0f);
	TestTrue(TEXT("floodstrider cycle at least 3"), Flood.AimSeconds + Flood.GetPostFireSeconds() >= 3.0f);
	TestEqual(TEXT("courier hp"), Courier.Hp, 40.0f);
	TestEqual(TEXT("courier span"), Courier.PatrolSpan, 400.0f);
	TestEqual(TEXT("courier speed"), Courier.PatrolSpeed, 100.0f);
	TestEqual(TEXT("courier shot speed"), Courier.ShotSpeed, 180.0f);
	TestTrue(TEXT("courier cycle at least 2.3"), Courier.AimSeconds + Courier.GetPostFireSeconds() >= 2.3f - UE_KINDA_SMALL_NUMBER);
	TestEqual(TEXT("courier slots"), Tuning.CourierEmissionSlots, 8);
	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FEnemyBrainCycle, "UmbrellaElla.Enemy.BrainCycle", UMBRELLAELLA_ENEMY_FLAGS)
bool FEnemyBrainCycle::RunTest(const FString& Parameters)
{
	const FEnemyTuning Tuning;
	const FEnemyProfile Profile = FEnemyRules::MakeProfile(EEnemyType::Roadwarden, Tuning);
	FEnemyBrain Brain;
	Brain.Reset(Profile);
	TestEqual(TEXT("patrols first"), Brain.State, EEnemyState::Patrol);
	Brain.Advance(Profile, 0.1f, true, true);
	TestEqual(TEXT("aim begins in window"), Brain.State, EEnemyState::Aim);
	// The aim commits: leaving the window does not cancel it, and the shot is released after AimSeconds.
	TestEqual(TEXT("no shot early"), Brain.Advance(Profile, 0.5f, false, true), EEnemyBrainEvent::None);
	TestEqual(TEXT("shot at 1s"), Brain.Advance(Profile, 0.5f, false, true), EEnemyBrainEvent::ReleaseShot);
	TestEqual(TEXT("recovery after the shot"), Brain.State, EEnemyState::Recovery);
	// No new aim during recovery even with the target in the window.
	Brain.Advance(Profile, 0.9f, true, true);
	TestEqual(TEXT("still recovering"), Brain.State, EEnemyState::Recovery);
	Brain.Advance(Profile, 1.0f, true, true);
	TestEqual(TEXT("patrol after recovery"), Brain.State, EEnemyState::Patrol);
	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FEnemyPatrolSpan, "UmbrellaElla.Enemy.PatrolStaysInSpan", UMBRELLAELLA_ENEMY_FLAGS)
bool FEnemyPatrolSpan::RunTest(const FString& Parameters)
{
	const FEnemyTuning Tuning;
	const FEnemyProfile Profile = FEnemyRules::MakeProfile(EEnemyType::Roadwarden, Tuning);
	FEnemyBrain Brain;
	Brain.Reset(Profile);
	float MaxSeen = 0.0f;
	float MinSeen = 0.0f;
	for (int32 Step = 0; Step < 600; ++Step)
	{
		Brain.Advance(Profile, 0.05f, false, true);
		MaxSeen = FMath::Max(MaxSeen, Brain.PatrolOffset);
		MinSeen = FMath::Min(MinSeen, Brain.PatrolOffset);
	}
	TestTrue(TEXT("never beyond half span right"), MaxSeen <= Profile.PatrolSpan * 0.5f + UE_KINDA_SMALL_NUMBER);
	TestTrue(TEXT("never beyond half span left"), MinSeen >= -Profile.PatrolSpan * 0.5f - UE_KINDA_SMALL_NUMBER);
	TestTrue(TEXT("reaches both ends"), MaxSeen > 0.0f && MinSeen < 0.0f);
	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FEnemyFiringWindow, "UmbrellaElla.Enemy.FiringWindowIsFixedRight", UMBRELLAELLA_ENEMY_FLAGS)
bool FEnemyFiringWindow::RunTest(const FString& Parameters)
{
	const FEnemyTuning Tuning;
	const FEnemyProfile Profile = FEnemyRules::MakeProfile(EEnemyType::Roadwarden, Tuning);
	const FVector Enemy(1000.0, 0.0, 500.0);
	TestTrue(TEXT("target below-left in range"), FEnemyRules::IsTargetInFiringWindow(Enemy, FVector(700.0, 0.0, 300.0), Profile));
	TestFalse(TEXT("target to the right is behind the gun"), FEnemyRules::IsTargetInFiringWindow(Enemy, FVector(1100.0, 0.0, 300.0), Profile));
	TestFalse(TEXT("out of range"), FEnemyRules::IsTargetInFiringWindow(Enemy, FVector(-100.0, 0.0, 500.0), Profile));
	TestFalse(TEXT("well above the body"), FEnemyRules::IsTargetInFiringWindow(Enemy, FVector(900.0, 0.0, 900.0), Profile));
	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FEnemyShotIsStraight, "UmbrellaElla.Enemy.ShotIsStraightAtCapturedTarget", UMBRELLAELLA_ENEMY_FLAGS)
bool FEnemyShotIsStraight::RunTest(const FString& Parameters)
{
	const FEnemyTuning Tuning;
	const FEnemyProfile Profile = FEnemyRules::MakeProfile(EEnemyType::Roadwarden, Tuning);
	const FUmbrellaShotSpec Spec = FEnemyRules::MakeShot(Profile, EUmbrellaShotKind::EnemyYellow, FVector(100.0, 25.0, 300.0), FVector(0.0, 0.0, 100.0), FName(TEXT("E")));
	TestEqual(TEXT("kind"), Spec.Kind, EUmbrellaShotKind::EnemyYellow);
	TestEqual(TEXT("speed"), static_cast<float>(Spec.Velocity.Size()), 240.0f);
	TestEqual(TEXT("no depth motion"), Spec.Velocity.Y, 0.0);
	TestTrue(TEXT("heads left and down"), Spec.Velocity.X < 0.0 && Spec.Velocity.Z < 0.0);
	TestEqual(TEXT("damage is incoming health"), Spec.Damage, 1.0f);
	TestEqual(TEXT("lifetime is range over speed"), Spec.LifetimeSeconds, 1000.0f / 240.0f);
	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FEnemyColorRatio, "UmbrellaElla.Enemy.ColorRatioTwoRedToOneYellow", UMBRELLAELLA_ENEMY_FLAGS)
bool FEnemyColorRatio::RunTest(const FString& Parameters)
{
	FRandomStream Stream(20261110);
	const TArray<EUmbrellaShotKind> Colors = FEnemyRules::AssignShotColors(12, 0, 2, Stream);
	int32 Yellow = 0;
	for (const EUmbrellaShotKind Kind : Colors)
	{
		Yellow += Kind == EUmbrellaShotKind::EnemyYellow ? 1 : 0;
		TestTrue(TEXT("only red or yellow"), Kind == EUmbrellaShotKind::EnemyYellow || Kind == EUmbrellaShotKind::EnemyRed);
	}
	TestEqual(TEXT("12 enemies"), Colors.Num(), 12);
	TestEqual(TEXT("4 yellow, 8 red"), Yellow, 4);

	FRandomStream StreamA(7);
	FRandomStream StreamB(7);
	TestTrue(TEXT("same seed, same colours"), FEnemyRules::AssignShotColors(9, 0, 2, StreamA) == FEnemyRules::AssignShotColors(9, 0, 2, StreamB));

	FRandomStream StreamC(7);
	const TArray<EUmbrellaShotKind> Reserved = FEnemyRules::AssignShotColors(6, 3, 2, StreamC);
	TestTrue(TEXT("reserved early yellows come first"), Reserved[0] == EUmbrellaShotKind::EnemyYellow && Reserved[1] == EUmbrellaShotKind::EnemyYellow && Reserved[2] == EUmbrellaShotKind::EnemyYellow);
	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FCourierPacketLifecycle, "UmbrellaElla.Enemy.CourierPacketLifecycle", UMBRELLAELLA_ENEMY_FLAGS)
bool FCourierPacketLifecycle::RunTest(const FString& Parameters)
{
	FCourierPackets Packets;
	Packets.Reset(8);
	for (int32 Slot = 0; Slot < 8; ++Slot)
	{
		TestEqual(TEXT("stable slot identity"), Packets.TakeNextSlot(), Slot);
	}
	TestTrue(TEXT("exhausted after eight"), Packets.IsExhausted());
	TestEqual(TEXT("ninth is refused"), Packets.TakeNextSlot(), static_cast<int32>(INDEX_NONE));
	Packets.Reset(8);
	TestEqual(TEXT("retry rebuilds eight"), Packets.GetRemaining(), 8);
	TestEqual(TEXT("first callback is the first"), Packets.RecordCallback(3), 1);
	TestEqual(TEXT("duplicate callback is seen twice, so the caller rejects it"), Packets.RecordCallback(3), 2);
	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FEnemyGenderChangesNothing, "UmbrellaElla.Enemy.World.GenderChangesNoMechanics", UMBRELLAELLA_ENEMY_FLAGS)
bool FEnemyGenderChangesNothing::RunTest(const FString& Parameters)
{
	UWorld* World = MakeWorld();
	AUmbrellaEnemy* Male = World->SpawnActor<AUmbrellaEnemy>();
	AUmbrellaEnemy* Female = World->SpawnActor<AUmbrellaEnemy>();
	Male->Configure(EEnemyType::Roadwarden, EEnemyGender::Male, EUmbrellaShotKind::EnemyRed);
	Female->Configure(EEnemyType::Roadwarden, EEnemyGender::Female, EUmbrellaShotKind::EnemyRed);
	TestEqual(TEXT("female kept"), Female->GetGender(), EEnemyGender::Female);
	TestEqual(TEXT("same hp"), Male->GetMaxHp(), Female->GetMaxHp());
	TestEqual(TEXT("same shot speed"), Male->GetProfile().ShotSpeed, Female->GetProfile().ShotSpeed);
	TestEqual(TEXT("same aim time"), Male->GetProfile().AimSeconds, Female->GetProfile().AimSeconds);
	DropWorld(World);
	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FEnemyTakesDamageAndDies, "UmbrellaElla.Enemy.World.DiesAtZeroHp", UMBRELLAELLA_ENEMY_FLAGS)
bool FEnemyTakesDamageAndDies::RunTest(const FString& Parameters)
{
	UWorld* World = MakeWorld();
	UUmbrellaEventBus* Bus = UUmbrellaEventBus::Get(World);
	const TSharedRef<FEventProbe> Probe = MakeShared<FEventProbe>();
	const FDelegateHandle Handle = Bus->On(EUmbrellaEventType::BossPartDestroyed).AddSP(Probe, &FEventProbe::OnEvent);
	const EEnemyType Types[] = { EEnemyType::Roadwarden, EEnemyType::Floodstrider, EEnemyType::SkyCourier };
	for (const EEnemyType Type : Types)
	{
		AUmbrellaEnemy* Enemy = World->SpawnActor<AUmbrellaEnemy>();
		Enemy->Configure(Type, EEnemyGender::Female, EUmbrellaShotKind::EnemyRed);
		const float Hp = Enemy->GetMaxHp();
		TestEqual(TEXT("blast consumed"), Enemy->ReceiveShot(BlastOf(10.0f), FVector::ZeroVector), EUmbrellaShotResult::Consumed);
		TestEqual(TEXT("hp drops by damage"), Enemy->GetHp(), Hp - 10.0f);
		FUmbrellaShotSpec EnemyShot;
		EnemyShot.Kind = EUmbrellaShotKind::EnemyRed;
		EnemyShot.Damage = 10.0f;
		TestEqual(TEXT("enemy shots pass through"), Enemy->ReceiveShot(EnemyShot, FVector::ZeroVector), EUmbrellaShotResult::Ignored);
		int32 Hits = 1;
		while (Enemy->GetEnemyState() != EEnemyState::Defeated && Hits < 100)
		{
			Enemy->ReceiveShot(BlastOf(10.0f), FVector::ZeroVector);
			++Hits;
		}
		TestEqual(TEXT("hits to kill"), Hits, FMath::CeilToInt(Hp / 10.0f));
		TestEqual(TEXT("dead at zero"), Enemy->GetHp(), 0.0f);
		TestEqual(TEXT("defeated"), Enemy->GetEnemyState(), EEnemyState::Defeated);
		TestEqual(TEXT("dead enemy ignores shots"), Enemy->ReceiveShot(BlastOf(10.0f), FVector::ZeroVector), EUmbrellaShotResult::Ignored);
	}
	TestEqual(TEXT("one part-destroyed per kill"), Probe->Seen.Num(), 3);
	TestEqual(TEXT("detail is Enemy"), Probe->Seen[0].Detail, FName(TEXT("Enemy")));
	Bus->On(EUmbrellaEventType::BossPartDestroyed).Remove(Handle);
	DropWorld(World);
	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FEnemyFiresRightColor, "UmbrellaElla.Enemy.World.FiresConfiguredColour", UMBRELLAELLA_ENEMY_FLAGS)
bool FEnemyFiresRightColor::RunTest(const FString& Parameters)
{
	UWorld* World = MakeWorld();
	AStaticMeshActor* Ella = World->SpawnActor<AStaticMeshActor>(AStaticMeshActor::StaticClass(), FTransform(FVector(700.0, 0.0, 300.0)));
	const EUmbrellaShotKind Colours[] = { EUmbrellaShotKind::EnemyRed, EUmbrellaShotKind::EnemyYellow };
	for (const EUmbrellaShotKind Colour : Colours)
	{
		AUmbrellaEnemy* Enemy = World->SpawnActor<AUmbrellaEnemy>(AUmbrellaEnemy::StaticClass(), FTransform(FVector(1000.0, 0.0, 500.0)));
		Enemy->Configure(EEnemyType::Roadwarden, EEnemyGender::Male, Colour);
		Enemy->SetTargetActor(Ella);
		Enemy->StepSeconds(0.1f);
		TestEqual(TEXT("aiming"), Enemy->GetEnemyState(), EEnemyState::Aim);
		TestEqual(TEXT("nothing fired during the warning"), Enemy->GetShotsFired(), 0);
		const EEnemyBrainEvent Event = Enemy->StepSeconds(Enemy->GetProfile().AimSeconds);
		TestEqual(TEXT("released"), Event, EEnemyBrainEvent::ReleaseShot);
		TestEqual(TEXT("one shot"), Enemy->GetShotsFired(), 1);
		int32 Matching = 0;
		for (TActorIterator<AUmbrellaProjectile> It(World); It; ++It)
		{
			Matching += (It->GetSpec().Kind == Colour && It->GetSpec().SourceId == Enemy->GetFName()) ? 1 : 0;
		}
		TestEqual(TEXT("projectile of the placed colour"), Matching, 1);
	}
	DropWorld(World);
	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FCourierWithdrawsAfterEight, "UmbrellaElla.Enemy.World.CourierWithdrawsAndRetryRestores", UMBRELLAELLA_ENEMY_FLAGS)
bool FCourierWithdrawsAfterEight::RunTest(const FString& Parameters)
{
	UWorld* World = MakeWorld();
	AStaticMeshActor* Ella = World->SpawnActor<AStaticMeshActor>(AStaticMeshActor::StaticClass(), FTransform(FVector(700.0, 0.0, 300.0)));
	AUmbrellaEnemy* Courier = World->SpawnActor<AUmbrellaEnemy>(AUmbrellaEnemy::StaticClass(), FTransform(FVector(1000.0, 0.0, 500.0)));
	Courier->Configure(EEnemyType::SkyCourier, EEnemyGender::Female, EUmbrellaShotKind::EnemyYellow);
	Courier->SetTargetActor(Ella);
	for (int32 Step = 0; Step < 400 && Courier->GetEnemyState() != EEnemyState::Withdrawn; ++Step)
	{
		Courier->StepSeconds(0.25f);
	}
	TestEqual(TEXT("eight shots in total"), Courier->GetShotsFired(), 8);
	TestEqual(TEXT("withdrawn, not defeated"), Courier->GetEnemyState(), EEnemyState::Withdrawn);
	Courier->ResetForRestart();
	TestEqual(TEXT("retry restores eight slots"), Courier->GetCourierSlotsRemaining(), 8);
	TestEqual(TEXT("retry back on patrol"), Courier->GetEnemyState(), EEnemyState::Patrol);
	DropWorld(World);
	return true;
}

#endif
