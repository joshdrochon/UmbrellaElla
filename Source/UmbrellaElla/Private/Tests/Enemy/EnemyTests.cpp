#include "Misc/AutomationTest.h"

#if WITH_AUTOMATION_TESTS

#include "Components/BoxComponent.h"
#include "Core/UmbrellaTuning.h"
#include "Enemy/EnemyModel.h"
#include "Enemy/UmbrellaEnemy.h"
#include "Engine/Engine.h"
#include "Engine/World.h"
#include "Owl/KeeperTuning.h"
#include "Encounter/EncounterDirectorSubsystem.h"

namespace
{
	constexpr EAutomationTestFlags EnemyFlags = EAutomationTestFlags::EditorContext | EAutomationTestFlags::ClientContext | EAutomationTestFlags::EngineFilter;
	constexpr float Step = 0.05f;

	struct FEnemyRig
	{
		FKeeperTuning Tuning;
		FEnemyModel Model;
		TArray<FEnemyCommand> Commands;
		FVector2D Player = FVector2D(-400.0f, 0.0f);

		void Start(EEnemyType Type, EUmbrellaShotKind Color = EUmbrellaShotKind::EnemyRed, float MinX = -100000.0f, float MaxX = 100000.0f)
		{
			Model.Init(Type, FEnemyModel::ProfileFor(Type, Tuning), Color, FVector2D(500.0f, 0.0f), MinX, MaxX);
		}

		void Run(float Seconds)
		{
			for (float T = 0.0f; T < Seconds; T += Step)
			{
				Model.Step(Step, Player, Tuning, Commands);
			}
		}

		int32 Shots() const
		{
			int32 N = 0;
			for (const FEnemyCommand& C : Commands)
			{
				N += (C.Type == EEnemyCommandType::FireShot) ? 1 : 0;
			}
			return N;
		}
	};
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FEnemyBaselines, "UmbrellaElla.Enemy.BaselineNumbers", EnemyFlags)
bool FEnemyBaselines::RunTest(const FString& Parameters)
{
	FEnemyRig R;
	const FEnemyProfile Warden = FEnemyModel::ProfileFor(EEnemyType::RoadwardenSundialCaster, R.Tuning);
	TestEqual(TEXT("Roadwarden HP"), Warden.Hp, 40.0f);
	TestEqual(TEXT("Roadwarden span"), Warden.PatrolSpan, 300.0f);
	TestEqual(TEXT("Roadwarden speed"), Warden.PatrolSpeed, 90.0f);
	TestEqual(TEXT("Roadwarden aim"), Warden.AimSeconds, 1.0f);
	TestEqual(TEXT("Roadwarden shot speed"), Warden.ShotSpeed, 240.0f);
	TestEqual(TEXT("Roadwarden cycle"), Warden.CycleSeconds, 2.5f);
	const FEnemyProfile Strider = FEnemyModel::ProfileFor(EEnemyType::Floodstrider, R.Tuning);
	TestEqual(TEXT("Floodstrider HP"), Strider.Hp, 60.0f);
	TestEqual(TEXT("Floodstrider speed"), Strider.PatrolSpeed, 60.0f);
	TestEqual(TEXT("Floodstrider aim"), Strider.AimSeconds, 1.1f);
	TestEqual(TEXT("Floodstrider shot"), Strider.ShotSpeed, 220.0f);
	TestEqual(TEXT("Floodstrider cycle"), Strider.CycleSeconds, 3.0f);
	const FEnemyProfile Courier = FEnemyModel::ProfileFor(EEnemyType::SkyCourier, R.Tuning);
	TestEqual(TEXT("Courier HP"), Courier.Hp, 40.0f);
	TestEqual(TEXT("Courier span"), Courier.PatrolSpan, 400.0f);
	TestEqual(TEXT("Courier speed"), Courier.PatrolSpeed, 100.0f);
	TestEqual(TEXT("Courier shot"), Courier.ShotSpeed, 180.0f);
	TestEqual(TEXT("Courier cycle"), Courier.CycleSeconds, 2.3f);
	TestTrue(TEXT("Courier is airborne"), Courier.bAirborne);
	TestEqual(TEXT("Courier emission cap"), Courier.MaxEmissions, 8);
	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FEnemyEquipmentVariants, "UmbrellaElla.Enemy.RoadwardenVariantsShareEveryNumber", EnemyFlags)
bool FEnemyEquipmentVariants::RunTest(const FString& Parameters)
{
	FEnemyRig R;
	const FEnemyProfile A = FEnemyModel::ProfileFor(EEnemyType::RoadwardenSundialCaster, R.Tuning);
	const FEnemyProfile B = FEnemyModel::ProfileFor(EEnemyType::RoadwardenArmillaryLauncher, R.Tuning);
	const FEnemyProfile C = FEnemyModel::ProfileFor(EEnemyType::RoadwardenEscapementRepeater, R.Tuning);
	const auto Same = [](const FEnemyProfile& X, const FEnemyProfile& Y)
	{
		return X.Hp == Y.Hp && X.PatrolSpan == Y.PatrolSpan && X.PatrolSpeed == Y.PatrolSpeed && X.AimSeconds == Y.AimSeconds
			&& X.ShotSpeed == Y.ShotSpeed && X.RecoverySeconds == Y.RecoverySeconds && X.CycleSeconds == Y.CycleSeconds
			&& X.MaxEmissions == Y.MaxEmissions && X.bAirborne == Y.bAirborne;
	};
	TestTrue(TEXT("Armillary equals Sundial"), Same(A, B));
	TestTrue(TEXT("Escapement equals Sundial"), Same(A, C));
	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FEnemyCycle, "UmbrellaElla.Enemy.RoadwardenPatrolAimOneShotRecovery", EnemyFlags)
bool FEnemyCycle::RunTest(const FString& Parameters)
{
	FEnemyRig R;
	R.Start(EEnemyType::RoadwardenSundialCaster);
	R.Run(0.4f);
	TestTrue(TEXT("patrols first"), R.Model.GetState() == EEnemyState::Patrol);
	R.Run(0.2f);
	TestTrue(TEXT("stops and aims after the patrol part of the cycle"), R.Model.GetState() == EEnemyState::Aim);
	const FVector2D AimPos = R.Model.GetPosition();
	R.Run(0.5f);
	TestEqual(TEXT("holds still while aiming"), static_cast<float>(R.Model.GetPosition().X), static_cast<float>(AimPos.X));
	TestEqual(TEXT("no shot during the aim"), R.Shots(), 0);
	R.Run(0.6f);
	TestEqual(TEXT("exactly one committed shot"), R.Shots(), 1);
	TestTrue(TEXT("recovering"), R.Model.GetState() == EEnemyState::Recovery);
	for (const FEnemyCommand& C : R.Commands)
	{
		if (C.Type == EEnemyCommandType::FireShot)
		{
			TestTrue(TEXT("flies left toward Ella at 240"), FMath::IsNearlyEqual(static_cast<float>(C.B.Size()), 240.0f, 0.5f) && C.B.X < 0.0f);
		}
	}
	R.Commands.Reset();
	R.Run(1.0f);
	TestEqual(TEXT("no second shot in the recovery"), R.Shots(), 0);
	R.Run(2.5f);
	TestEqual(TEXT("the cycle is at least 2.5 s: one more shot"), R.Shots(), 1);
	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FEnemyCommit, "UmbrellaElla.Enemy.ShotDirectionIsCommittedAtAimStart", EnemyFlags)
bool FEnemyCommit::RunTest(const FString& Parameters)
{
	FEnemyRig R;
	R.Start(EEnemyType::RoadwardenSundialCaster);
	R.Player = FVector2D(-400.0f, 0.0f);
	R.Run(0.6f); // aim has started
	R.Player = FVector2D(-400.0f, 900.0f); // Ella moves away
	R.Run(1.2f);
	for (const FEnemyCommand& C : R.Commands)
	{
		if (C.Type == EEnemyCommandType::FireShot)
		{
			TestTrue(TEXT("the shot still flies along the locked line (near level)"), FMath::Abs(C.B.Y) < FMath::Abs(C.B.X) * 0.1f);
		}
	}
	TestEqual(TEXT("one shot"), R.Shots(), 1);
	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FEnemyNoFireBehind, "UmbrellaElla.Enemy.NoFireWhenEllaIsBehind", EnemyFlags)
bool FEnemyNoFireBehind::RunTest(const FString& Parameters)
{
	FEnemyRig R;
	R.Start(EEnemyType::RoadwardenSundialCaster);
	R.Player = FVector2D(2000.0f, 0.0f);
	R.Run(8.0f);
	TestEqual(TEXT("no shot at a target that is not ahead"), R.Shots(), 0);
	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FEnemyDefeat, "UmbrellaElla.Enemy.ZeroHpStopsFire", EnemyFlags)
bool FEnemyDefeat::RunTest(const FString& Parameters)
{
	FEnemyRig R;
	R.Start(EEnemyType::RoadwardenSundialCaster);
	R.Run(0.7f);
	TestTrue(TEXT("aiming"), R.Model.GetState() == EEnemyState::Aim);
	R.Model.ApplyHit(30.0f, R.Commands);
	TestEqual(TEXT("30 damage leaves 10 HP"), R.Model.GetHp(), 10.0f);
	R.Model.ApplyHit(10.0f, R.Commands);
	TestTrue(TEXT("defeated at zero HP"), R.Model.GetState() == EEnemyState::Defeated);
	TestTrue(TEXT("a kill is XP-eligible"), R.Model.IsKilled());
	R.Commands.Reset();
	R.Run(6.0f);
	TestEqual(TEXT("no new or delayed fire after defeat"), R.Shots(), 0);
	R.Model.ApplyHit(10.0f, R.Commands);
	TestEqual(TEXT("further hits change nothing"), R.Model.GetHp(), 0.0f);
	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FEnemyColours, "UmbrellaElla.Enemy.BothShotColoursOnEveryType", EnemyFlags)
bool FEnemyColours::RunTest(const FString& Parameters)
{
	const EEnemyType Types[] = {EEnemyType::RoadwardenSundialCaster, EEnemyType::RoadwardenArmillaryLauncher, EEnemyType::RoadwardenEscapementRepeater,
		EEnemyType::Floodstrider, EEnemyType::SkyCourier};
	const EUmbrellaShotKind Colours[] = {EUmbrellaShotKind::EnemyRed, EUmbrellaShotKind::EnemyYellow};
	for (EEnemyType Type : Types)
	{
		for (EUmbrellaShotKind Colour : Colours)
		{
			FEnemyRig R;
			R.Start(Type, Colour);
			R.Run(4.0f);
			bool bSawShot = false;
			for (const FEnemyCommand& C : R.Commands)
			{
				if (C.Type == EEnemyCommandType::FireShot)
				{
					bSawShot = true;
					TestTrue(TEXT("the shot carries the configured colour"), C.ShotKind == Colour);
				}
			}
			TestTrue(TEXT("every type fires in both colours"), bSawShot);
		}
	}
	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FEnemyColourPlan, "UmbrellaElla.Enemy.ColourAllocationIsTwoRedToOneYellow", EnemyFlags)
bool FEnemyColourPlan::RunTest(const FString& Parameters)
{
	const TArray<EUmbrellaShotKind> Colours = FEnemyModel::AssignShotColors(9, TArray<int32>(), 2);
	int32 Yellow = 0;
	for (EUmbrellaShotKind Colour : Colours)
	{
		Yellow += (Colour == EUmbrellaShotKind::EnemyYellow) ? 1 : 0;
	}
	TestEqual(TEXT("nine enemies: six red, three yellow"), Yellow, 3);
	const TArray<int32> Reserved = {0};
	const TArray<EUmbrellaShotKind> WithReserved = FEnemyModel::AssignShotColors(9, Reserved, 2);
	TestTrue(TEXT("the reserved catch lane is yellow"), WithReserved[0] == EUmbrellaShotKind::EnemyYellow);
	int32 Yellow2 = 0;
	for (EUmbrellaShotKind Colour : WithReserved)
	{
		Yellow2 += (Colour == EUmbrellaShotKind::EnemyYellow) ? 1 : 0;
	}
	TestEqual(TEXT("the reservation counts toward the same level-wide total"), Yellow2, 3);
	TestEqual(TEXT("zero enemies"), FEnemyModel::AssignShotColors(0, TArray<int32>(), 2).Num(), static_cast<int32>(0));
	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FEnemyCourierSlots, "UmbrellaElla.Enemy.CourierEightEmissionsThenWithdraws", EnemyFlags)
bool FEnemyCourierSlots::RunTest(const FString& Parameters)
{
	FEnemyRig R;
	R.Start(EEnemyType::SkyCourier, EUmbrellaShotKind::EnemyYellow);
	R.Run(60.0f);
	TestEqual(TEXT("eight single emissions in total"), R.Shots(), 8);
	TestTrue(TEXT("then it withdraws"), R.Model.GetState() == EEnemyState::Withdrawn);
	TestFalse(TEXT("a withdrawal is not a kill (no XP)"), R.Model.IsKilled());
	TArray<int32> Slots;
	for (const FEnemyCommand& C : R.Commands)
	{
		if (C.Type == EEnemyCommandType::FireShot)
		{
			Slots.Add(C.Slot);
		}
	}
	TestTrue(TEXT("stable slots 0 to 7"), Slots == TArray<int32>({0, 1, 2, 3, 4, 5, 6, 7}));
	R.Model.Reset();
	TestEqual(TEXT("retry rebuilds all eight slots"), R.Model.GetEmissionsLeft(), 8);
	TestTrue(TEXT("and the Courier is alive again"), R.Model.IsAlive());
	R.Commands.Reset();
	R.Run(5.0f);
	TestTrue(TEXT("it fires again after the retry"), R.Shots() >= 1);
	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FEnemyKillBeatsWithdraw, "UmbrellaElla.Enemy.KillingACourierDiffersFromWithdrawal", EnemyFlags)
bool FEnemyKillBeatsWithdraw::RunTest(const FString& Parameters)
{
	FEnemyRig R;
	R.Start(EEnemyType::SkyCourier);
	R.Model.ApplyHit(1000.0f, R.Commands);
	TestTrue(TEXT("killed"), R.Model.IsKilled());
	TestTrue(TEXT("not withdrawn"), R.Model.GetState() == EEnemyState::Defeated);
	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FEnemyContainment, "UmbrellaElla.Enemy.PatrolStaysOnItsSupport", EnemyFlags)
bool FEnemyContainment::RunTest(const FString& Parameters)
{
	FEnemyRig R;
	R.Start(EEnemyType::RoadwardenSundialCaster, EUmbrellaShotKind::EnemyRed, 450.0f, 520.0f);
	R.Player = FVector2D(5000.0f, 0.0f); // never aims, only patrols
	float MinX = 100000.0f;
	float MaxX = -100000.0f;
	for (float T = 0.0f; T < 20.0f; T += Step)
	{
		R.Model.Step(Step, R.Player, R.Tuning, R.Commands);
		MinX = FMath::Min(MinX, R.Model.GetPosition().X);
		MaxX = FMath::Max(MaxX, R.Model.GetPosition().X);
	}
	TestTrue(TEXT("never left the support"), MinX >= 450.0f - 0.01f && MaxX <= 520.0f + 0.01f);
	TestTrue(TEXT("the patrol span is limited to the surface (70 of 300)"), R.Model.GetPatrolMaxX() - R.Model.GetPatrolMinX() <= 70.01f);
	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FEnemyAirborne, "UmbrellaElla.Enemy.CourierPatrolsInTheAir", EnemyFlags)
bool FEnemyAirborne::RunTest(const FString& Parameters)
{
	FEnemyRig R;
	R.Start(EEnemyType::SkyCourier);
	R.Player = FVector2D(5000.0f, 0.0f);
	R.Run(10.0f);
	TestEqual(TEXT("height never changes"), static_cast<float>(R.Model.GetPosition().Y), 0.0f);
	TestEqual(TEXT("air span 400"), R.Model.GetPatrolMaxX() - R.Model.GetPatrolMinX(), 400.0f);
	return true;
}

namespace
{
	struct FEnemyWorld
	{
		UWorld* World = nullptr;

		FEnemyWorld()
		{
			World = UWorld::CreateWorld(EWorldType::Game, false, FName(TEXT("EnemyTestWorld")));
			FWorldContext& Context = GEngine->CreateNewWorldContext(EWorldType::Game);
			Context.SetCurrentWorld(World);
			World->InitializeActorsForPlay(FURL());
			World->BeginPlay();
		}

		~FEnemyWorld()
		{
			if (GEngine)
			{
				GEngine->DestroyWorldContext(World);
			}
			if (World)
			{
				World->DestroyWorld(false);
			}
		}
	};
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FEnemyWorldHit, "UmbrellaElla.Enemy.World.PlayerShotsReduceHpAndDefeat", EnemyFlags)
bool FEnemyWorldHit::RunTest(const FString& Parameters)
{
	FEnemyWorld W;
	AUmbrellaEnemy* Enemy = AUmbrellaEnemy::SpawnEnemy(W.World, EEnemyType::RoadwardenSundialCaster, EEnemyVariant::Female, EUmbrellaShotKind::EnemyRed,
		FVector(500.0f, 0.0f, 0.0f), -100000.0f, 100000.0f);
	if (!TestNotNull(TEXT("enemy spawned"), Enemy))
	{
		return false;
	}
	FUmbrellaShotSpec Shot;
	Shot.Kind = EUmbrellaShotKind::PlayerBlast;
	Shot.Damage = 10.0f;
	TestTrue(TEXT("player shot consumed"), Enemy->ReceiveShot(Shot, FVector::ZeroVector) == EUmbrellaShotResult::Consumed);
	TestEqual(TEXT("40 HP minus 10"), Enemy->GetModel().GetHp(), 30.0f);
	Shot.Kind = EUmbrellaShotKind::EnemyRed;
	TestTrue(TEXT("enemy shots never hurt enemies"), Enemy->ReceiveShot(Shot, FVector::ZeroVector) == EUmbrellaShotResult::Ignored);
	Shot.Kind = EUmbrellaShotKind::PlayerBlast;
	Shot.Damage = 100.0f;
	Enemy->ReceiveShot(Shot, FVector::ZeroVector);
	TestTrue(TEXT("defeated"), Enemy->GetModel().GetState() == EEnemyState::Defeated);
	TestTrue(TEXT("a defeated enemy ignores shots (they pass through)"), Enemy->ReceiveShot(Shot, FVector::ZeroVector) == EUmbrellaShotResult::Ignored);
	TestTrue(TEXT("hit box is off"), Enemy->FindComponentByClass<UBoxComponent>()->GetCollisionEnabled() == ECollisionEnabled::NoCollision);
	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FEnemyWorldRetry, "UmbrellaElla.Enemy.World.DirectorRetryRebuildsEnemies", EnemyFlags)
bool FEnemyWorldRetry::RunTest(const FString& Parameters)
{
	FEnemyWorld W;
	AddExpectedError(TEXT("no arena in the world"), EAutomationExpectedErrorFlags::Contains, 0);
	UEncounterDirectorSubsystem* Director = W.World->GetSubsystem<UEncounterDirectorSubsystem>();
	if (!TestNotNull(TEXT("director"), Director))
	{
		return false;
	}
	Director->SetManualStepping(true);
	AUmbrellaEnemy* Courier = AUmbrellaEnemy::SpawnEnemy(W.World, EEnemyType::SkyCourier, EEnemyVariant::Male, EUmbrellaShotKind::EnemyYellow,
		FVector(500.0f, 0.0f, 200.0f), -100000.0f, 100000.0f);
	AUmbrellaEnemy* Warden = AUmbrellaEnemy::SpawnEnemy(W.World, EEnemyType::RoadwardenArmillaryLauncher, EEnemyVariant::Male, EUmbrellaShotKind::EnemyRed,
		FVector(800.0f, 0.0f, 0.0f), -100000.0f, 100000.0f);
	if (!TestNotNull(TEXT("courier"), Courier) || !TestNotNull(TEXT("warden"), Warden))
	{
		return false;
	}
	for (int32 Index = 0; Index < 1200; ++Index)
	{
		Courier->StepBy(0.05f, FVector2D(-400.0f, 0.0f));
	}
	FUmbrellaShotSpec Shot;
	Shot.Kind = EUmbrellaShotKind::PlayerBlast;
	Shot.Damage = 1000.0f;
	Warden->ReceiveShot(Shot, FVector::ZeroVector);
	TestTrue(TEXT("courier withdrew"), Courier->GetModel().GetState() == EEnemyState::Withdrawn);
	TestTrue(TEXT("warden killed"), Warden->GetModel().GetState() == EEnemyState::Defeated);
	Director->BeginKeeperFight();
	Director->ResetForRestart();
	TestEqual(TEXT("courier has eight slots again"), Courier->GetModel().GetEmissionsLeft(), 8);
	TestTrue(TEXT("courier alive"), Courier->GetModel().IsAlive());
	TestEqual(TEXT("warden back to full HP"), Warden->GetModel().GetHp(), 40.0f);
	return true;
}

#endif
