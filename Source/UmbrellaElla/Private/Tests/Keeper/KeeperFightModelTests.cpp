#include "Misc/AutomationTest.h"

#if WITH_AUTOMATION_TESTS

#include "Encounter/EncounterTuning.h"
#include "Encounter/KeeperFightModel.h"
#include "Owl/KeeperTuning.h"

namespace
{
	constexpr EAutomationTestFlags KeeperFlags = EAutomationTestFlags::EditorContext | EAutomationTestFlags::ClientContext | EAutomationTestFlags::EngineFilter;
	constexpr float Step = 0.05f;

	struct FKeeperRig
	{
		FKeeperFightModel Model;
		TArray<FKeeperCommand> Commands;
		FKeeperTickInput Input;
		FKeeperTuning Tuning;
		FEncounterTuning Encounter;

		FKeeperRig()
		{
			Input.PlayerPos = FVector2D(-500.0f, 0.0f);
			Input.PlayerRadius = 10.0f;
		}

		void Start(EKeeperPhase Phase = EKeeperPhase::Wings, FKeeperRuleSwitches Switches = FKeeperRuleSwitches())
		{
			Model.Init(&Tuning, Encounter, Switches);
			Model.BeginPhase(Phase, Commands);
		}

		void Run(float Seconds)
		{
			for (float T = 0.0f; T < Seconds; T += Step)
			{
				Model.Step(Step, Input, Commands);
			}
		}

		int32 Count(EKeeperCommandType Type) const
		{
			int32 N = 0;
			for (const FKeeperCommand& C : Commands)
			{
				if (C.Type == Type)
				{
					++N;
				}
			}
			return N;
		}

		int32 CountShots(EUmbrellaShotKind Kind) const
		{
			int32 N = 0;
			for (const FKeeperCommand& C : Commands)
			{
				if (C.Type == EKeeperCommandType::FireShot && C.ShotKind == Kind)
				{
					++N;
				}
			}
			return N;
		}

		void SkipTransition()
		{
			Run(Encounter.PhaseTransitionSeconds + Step);
			Commands.Reset();
		}

		void BreakWings()
		{
			Model.ApplyPlayerHit(EKeeperPart::Wings, Tuning.WingsHp, Commands);
		}

		void BreakMechanism(EKeeperPart Part)
		{
			Model.ApplyPlayerHit(Part, 1000.0f, Commands);
		}
	};
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FKeeperPhaseGating, "UmbrellaElla.Keeper.PhaseGating", KeeperFlags)
bool FKeeperPhaseGating::RunTest(const FString& Parameters)
{
	FKeeperRig R;
	R.Start();
	R.SkipTransition();
	TestTrue(TEXT("wings eligible in the wings phase"), R.Model.IsPartEligible(EKeeperPart::Wings));
	TestFalse(TEXT("front rejects damage while wings live"), R.Model.IsPartEligible(EKeeperPart::Front));
	const FKeeperHitResult Blocked = R.Model.ApplyPlayerHit(EKeeperPart::Front, 10.0f, R.Commands);
	TestTrue(TEXT("front hit is consumed, not damaged"), Blocked.Outcome == EKeeperHitOutcome::Blocked);
	TestEqual(TEXT("front HP unchanged"), R.Model.GetPartHp(EKeeperPart::Front), R.Tuning.FrontHp);
	const FKeeperHitResult Blocked2 = R.Model.ApplyPlayerHit(EKeeperPart::Clock, 10.0f, R.Commands);
	TestTrue(TEXT("closed clock consumes shots"), Blocked2.Outcome == EKeeperHitOutcome::Blocked);
	const FKeeperHitResult Hit = R.Model.ApplyPlayerHit(EKeeperPart::Wings, 10.0f, R.Commands);
	TestTrue(TEXT("wing hit damages"), Hit.Outcome == EKeeperHitOutcome::Damaged);
	TestEqual(TEXT("wings lose 10 HP"), R.Model.GetPartHp(EKeeperPart::Wings), R.Tuning.WingsHp - 10.0f);
	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FKeeperBaselineHp, "UmbrellaElla.Keeper.BaselineHp", KeeperFlags)
bool FKeeperBaselineHp::RunTest(const FString& Parameters)
{
	FKeeperRig R;
	R.Start();
	TestEqual(TEXT("wings"), R.Model.GetPartHp(EKeeperPart::Wings), 180.0f);
	TestEqual(TEXT("front"), R.Model.GetPartHp(EKeeperPart::Front), 100.0f);
	TestEqual(TEXT("middle"), R.Model.GetPartHp(EKeeperPart::Middle), 110.0f);
	TestEqual(TEXT("rear"), R.Model.GetPartHp(EKeeperPart::Rear), 120.0f);
	TestEqual(TEXT("clock"), R.Model.GetPartHp(EKeeperPart::Clock), 320.0f);
	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FKeeperWingBreakAdvances, "UmbrellaElla.Keeper.WingBreakAdvancesToMechanisms", KeeperFlags)
bool FKeeperWingBreakAdvances::RunTest(const FString& Parameters)
{
	FKeeperRig R;
	R.Start();
	R.SkipTransition();
	R.Model.ApplyPlayerHit(EKeeperPart::Wings, 179.0f, R.Commands);
	TestTrue(TEXT("still in wings"), R.Model.GetPhase() == EKeeperPhase::Wings);
	const FKeeperHitResult Result = R.Model.ApplyPlayerHit(EKeeperPart::Wings, 1.0f, R.Commands);
	TestTrue(TEXT("wings broke"), Result.bBroke);
	TestTrue(TEXT("phase advanced"), Result.bPhaseAdvanced && R.Model.GetPhase() == EKeeperPhase::Mechanisms);
	TestTrue(TEXT("transition is quiet"), R.Model.IsTransitioning());
	TestTrue(TEXT("projectiles cleared"), R.Count(EKeeperCommandType::ClearProjectiles) >= 1);
	const FKeeperHitResult Through = R.Model.ApplyPlayerHit(EKeeperPart::Wings, 10.0f, R.Commands);
	TestTrue(TEXT("depleted wings are cover only, shots pass"), Through.Outcome == EKeeperHitOutcome::PassThrough);
	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FKeeperMechanismOrder, "UmbrellaElla.Keeper.MechanismOrderAndClockOpening", KeeperFlags)
bool FKeeperMechanismOrder::RunTest(const FString& Parameters)
{
	FKeeperRig R;
	R.Start(EKeeperPhase::Mechanisms);
	R.SkipTransition();
	TestTrue(TEXT("front first"), R.Model.IsPartEligible(EKeeperPart::Front));
	TestFalse(TEXT("middle not yet"), R.Model.IsPartEligible(EKeeperPart::Middle));
	TestFalse(TEXT("rear not yet"), R.Model.IsPartEligible(EKeeperPart::Rear));
	TestFalse(TEXT("clock closed"), R.Model.IsPartEligible(EKeeperPart::Clock));
	R.Model.ApplyPlayerHit(EKeeperPart::Front, 10.0f, R.Commands);
	TestTrue(TEXT("an outer hit opens the clock"), R.Model.IsClockOpen());
	R.Commands.Reset();
	R.BreakMechanism(EKeeperPart::Front);
	TestTrue(TEXT("front broke"), R.Model.IsPartBroken(EKeeperPart::Front));
	TestTrue(TEXT("break stuns"), R.Model.IsStunned());
	TestTrue(TEXT("middle now eligible"), R.Model.IsPartEligible(EKeeperPart::Middle));
	TestFalse(TEXT("rear still not"), R.Model.IsPartEligible(EKeeperPart::Rear));
	R.BreakMechanism(EKeeperPart::Middle);
	const FKeeperHitResult Last = [&R]() { R.BreakMechanism(EKeeperPart::Rear); return FKeeperHitResult(); }();
	(void)Last;
	TestTrue(TEXT("all three broken advance to the clock"), R.Model.GetPhase() == EKeeperPhase::Clock);
	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FKeeperClockReserve, "UmbrellaElla.Keeper.ClockStopsAtReserveBeforeFinal", KeeperFlags)
bool FKeeperClockReserve::RunTest(const FString& Parameters)
{
	FKeeperRig R;
	R.Start(EKeeperPhase::Mechanisms);
	R.SkipTransition();
	R.Model.ApplyPlayerHit(EKeeperPart::Front, 10.0f, R.Commands); // opens the clock
	const FKeeperHitResult Hit = R.Model.ApplyPlayerHit(EKeeperPart::Clock, 1000.0f, R.Commands);
	TestTrue(TEXT("clock damaged"), Hit.Outcome == EKeeperHitOutcome::Damaged && Hit.bClockHpReduced);
	TestEqual(TEXT("clock stops at the 128 reserve"), R.Model.GetPartHp(EKeeperPart::Clock), R.Tuning.ClockReserveHp);
	TestFalse(TEXT("at the floor the clock takes no more"), R.Model.IsPartEligible(EKeeperPart::Clock));
	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FKeeperClockOpening, "UmbrellaElla.Keeper.ClockOpeningWindowAndRecovery", KeeperFlags)
bool FKeeperClockOpening::RunTest(const FString& Parameters)
{
	FKeeperRig R;
	R.Start(EKeeperPhase::Mechanisms);
	R.SkipTransition();
	R.Model.ApplyPlayerHit(EKeeperPart::Front, 1.0f, R.Commands);
	TestTrue(TEXT("open"), R.Model.IsClockOpen());
	R.Run(R.Tuning.ClockOpenSeconds - 0.3f);
	R.Model.ApplyPlayerHit(EKeeperPart::Front, 1.0f, R.Commands);
	R.Run(0.5f);
	TestFalse(TEXT("repeated hits do not extend the opening"), R.Model.IsClockOpen());
	R.Model.ApplyPlayerHit(EKeeperPart::Front, 1.0f, R.Commands);
	TestFalse(TEXT("no reopening inside the 1.3 s protection recovery"), R.Model.IsClockOpen());
	R.Run(R.Tuning.ClockProtectRecoverySeconds + 0.2f);
	R.Model.ApplyPlayerHit(EKeeperPart::Front, 1.0f, R.Commands);
	TestTrue(TEXT("opens again after the recovery"), R.Model.IsClockOpen());
	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FKeeperFinalCycle, "UmbrellaElla.Keeper.FinalExposureCycle", KeeperFlags)
bool FKeeperFinalCycle::RunTest(const FString& Parameters)
{
	FKeeperRig R;
	R.Start(EKeeperPhase::Clock);
	R.Run(R.Encounter.PhaseTransitionSeconds + Step);
	TestTrue(TEXT("exposed at the finale start"), R.Model.IsClockOpen());
	R.Run(R.Tuning.FinalExposureSeconds + 0.1f);
	TestFalse(TEXT("closed after 1.9 s"), R.Model.IsClockOpen());
	R.Run(R.Tuning.FinalExposureCycleSeconds - R.Tuning.FinalExposureSeconds);
	TestTrue(TEXT("exposed again on the 4.8 s cycle"), R.Model.IsClockOpen());
	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FKeeperFinalHitWins, "UmbrellaElla.Keeper.FinalClockHitEndsFight", KeeperFlags)
bool FKeeperFinalHitWins::RunTest(const FString& Parameters)
{
	FKeeperRig R;
	R.Start(EKeeperPhase::Clock);
	R.Run(R.Encounter.PhaseTransitionSeconds + Step);
	R.Commands.Reset();
	const FKeeperHitResult Result = R.Model.ApplyPlayerHit(EKeeperPart::Clock, 10000.0f, R.Commands);
	TestTrue(TEXT("lethal"), Result.bFightWon);
	TestEqual(TEXT("exactly one FightWon"), R.Count(EKeeperCommandType::FightWon), 1);
	TestTrue(TEXT("model ended"), R.Model.IsEnded());
	TestTrue(TEXT("every threat is cleared"), R.Count(EKeeperCommandType::ClearProjectiles) >= 1 && R.Count(EKeeperCommandType::ClearGusts) >= 1);
	R.Commands.Reset();
	R.Run(5.0f);
	TestEqual(TEXT("nothing fires after the win"), R.Commands.Num(), 0);
	TestTrue(TEXT("defeat wins a same-frame tie"), FKeeperFightModel::ShouldDefeatWin(true, true));
	TestFalse(TEXT("no defeat, no tie"), FKeeperFightModel::ShouldDefeatWin(false, true));
	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FKeeperRedPressure, "UmbrellaElla.Keeper.RedPressure", KeeperFlags)
bool FKeeperRedPressure::RunTest(const FString& Parameters)
{
	FKeeperRig R;
	FKeeperRuleSwitches Only;
	Only.bYellow = false;
	Only.bGust = false;
	Only.bTalon = false;
	R.Start(EKeeperPhase::Wings, Only);
	R.Run(R.Encounter.PhaseTransitionSeconds + R.Tuning.RedFirstAtSeconds + 0.5f);
	TestEqual(TEXT("first volley is four reds"), R.CountShots(EUmbrellaShotKind::EnemyRed), R.Tuning.RedShotCount);
	TestEqual(TEXT("no yellow when off"), R.CountShots(EUmbrellaShotKind::EnemyYellow), 0);
	for (const FKeeperCommand& C : R.Commands)
	{
		if (C.Type == EKeeperCommandType::FireShot)
		{
			TestEqual(TEXT("wings red speed 240"), static_cast<float>(C.B.Size()), R.Tuning.RedSpeedWings);
			TestEqual(TEXT("damage 1"), C.Damage, 1.0f);
			break;
		}
	}
	TestEqual(TEXT("spread angles"), FKeeperFightModel::FanAngleDeg(0.0f, 36.0f, 0, 4), -18.0f);
	TestEqual(TEXT("spread angles end"), FKeeperFightModel::FanAngleDeg(0.0f, 36.0f, 3, 4), 18.0f);
	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FKeeperYellowPacket, "UmbrellaElla.Keeper.YellowPackets", KeeperFlags)
bool FKeeperYellowPacket::RunTest(const FString& Parameters)
{
	FKeeperRig R;
	FKeeperRuleSwitches Only;
	Only.bRed = false;
	Only.bGust = false;
	Only.bTalon = false;
	R.Start(EKeeperPhase::Wings, Only);
	R.Run(R.Encounter.PhaseTransitionSeconds + R.Tuning.YellowFirstAtSeconds + 0.5f);
	TestEqual(TEXT("two yellow packets"), R.CountShots(EUmbrellaShotKind::EnemyYellow), 2);
	for (const FKeeperCommand& C : R.Commands)
	{
		if (C.Type == EKeeperCommandType::FireShot)
		{
			TestEqual(TEXT("wings yellow speed 180"), static_cast<float>(C.B.Size()), R.Tuning.YellowSpeedWings);
			TestTrue(TEXT("size 1.2x"), FMath::IsNearlyEqual(C.Value, R.Tuning.RedBaseRadius * 1.2f, 0.01f));
			break;
		}
	}
	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FKeeperDoubleBeat, "UmbrellaElla.Keeper.ClockDoubleBeatRepeatsPaths", KeeperFlags)
bool FKeeperDoubleBeat::RunTest(const FString& Parameters)
{
	FKeeperRig R;
	FKeeperRuleSwitches Only;
	Only.bYellow = false;
	Only.bTalon = false;
	R.Start(EKeeperPhase::Clock, Only);
	R.Run(R.Encounter.PhaseTransitionSeconds + R.Tuning.BeatFirstAtSeconds + 2.5f);
	TArray<FVector2D> Velocities;
	for (const FKeeperCommand& C : R.Commands)
	{
		if (C.Type == EKeeperCommandType::FireShot)
		{
			Velocities.Add(C.B);
		}
	}
	TestEqual(TEXT("eight shots in one double beat"), Velocities.Num(), R.Tuning.RedShotCount * 2);
	if (Velocities.Num() == R.Tuning.RedShotCount * 2)
	{
		for (int32 Index = 0; Index < R.Tuning.RedShotCount; ++Index)
		{
			TestTrue(TEXT("repeat flies the same path"), Velocities[Index].Equals(Velocities[Index + R.Tuning.RedShotCount], 0.01f));
		}
	}
	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FKeeperSchedulerSerial, "UmbrellaElla.Keeper.PhysicalSchedulerSerialisesMoves", KeeperFlags)
bool FKeeperSchedulerSerial::RunTest(const FString& Parameters)
{
	FKeeperRig R;
	FKeeperRuleSwitches Only;
	Only.bRed = false;
	Only.bYellow = false;
	Only.bTalon = false;
	R.Start(EKeeperPhase::Mechanisms, Only);
	R.Input.PlayerPos = FVector2D(-900.0f, 0.0f);
	R.Run(R.Encounter.PhaseTransitionSeconds + R.Tuning.CastFirstAtSeconds + 0.2f);
	TestEqual(TEXT("front cast first"), static_cast<int32>(R.Model.GetPhysical()), static_cast<int32>(EKeeperPhysical::FrontCast));
	TestTrue(TEXT("warning first"), R.Model.GetStage() == EKeeperStage::Warning);
	// Never two physical moves at once: warnings only come after the previous one went idle.
	int32 MaxActive = 0;
	int32 Warnings = 0;
	int32 Done = 0;
	for (float T = 0.0f; T < 30.0f; T += Step)
	{
		R.Commands.Reset();
		R.Model.Step(Step, R.Input, R.Commands);
		Warnings += R.Count(EKeeperCommandType::PhysicalWarning);
		Done += R.Count(EKeeperCommandType::PhysicalRecovery);
		MaxActive = FMath::Max(MaxActive, Warnings - Done);
	}
	TestTrue(TEXT("at most one move in flight"), MaxActive <= 1);
	TestTrue(TEXT("middle and rear follow in order"), R.Model.GetCastSerial() >= 3);
	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FKeeperMiddleParity, "UmbrellaElla.Keeper.MiddleCurveSignFollowsSerial", KeeperFlags)
bool FKeeperMiddleParity::RunTest(const FString& Parameters)
{
	TestEqual(TEXT("serial 0"), FKeeperFightModel::MiddleSignForSerial(0), 1.0f);
	TestEqual(TEXT("serial 1"), FKeeperFightModel::MiddleSignForSerial(1), -1.0f);
	TestEqual(TEXT("serial 2"), FKeeperFightModel::MiddleSignForSerial(2), 1.0f);
	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FKeeperRearPause, "UmbrellaElla.Keeper.RearTwoStageHasSafePause", KeeperFlags)
bool FKeeperRearPause::RunTest(const FString& Parameters)
{
	FKeeperRig R;
	FKeeperRuleSwitches Only;
	Only.bRed = false;
	Only.bYellow = false;
	Only.bTalon = false;
	Only.bFrontCast = false;
	Only.bMiddleCast = false;
	R.Start(EKeeperPhase::Mechanisms, Only);
	R.Input.PlayerPos = FVector2D(-900.0f, 0.0f);
	bool bSawPause = false;
	bool bSawSecond = false;
	float PauseSeconds = 0.0f;
	for (float T = 0.0f; T < 12.0f; T += Step)
	{
		R.Model.Step(Step, R.Input, R.Commands);
		if (R.Model.GetStage() == EKeeperStage::Pause)
		{
			bSawPause = true;
			PauseSeconds += Step;
			TestFalse(TEXT("the pause is harmless"), R.Model.IsHeadHurting());
		}
		if (R.Model.GetStage() == EKeeperStage::SecondStroke)
		{
			bSawSecond = true;
			TestTrue(TEXT("second stroke hurts"), R.Model.IsHeadHurting());
		}
	}
	TestTrue(TEXT("pause seen"), bSawPause);
	TestTrue(TEXT("second stroke seen"), bSawSecond);
	TestTrue(TEXT("pause lasts about 0.65 s"), FMath::Abs(PauseSeconds - R.Tuning.RearPauseSeconds) <= 2.0f * Step);
	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FKeeperChainDamageOnce, "UmbrellaElla.Keeper.ChainHeadDamagesOncePerCast", KeeperFlags)
bool FKeeperChainDamageOnce::RunTest(const FString& Parameters)
{
	FKeeperRig R;
	FKeeperRuleSwitches Only;
	Only.bRed = false;
	Only.bYellow = false;
	Only.bTalon = false;
	Only.bMiddleCast = false;
	Only.bRearCast = false;
	R.Start(EKeeperPhase::Mechanisms, Only);
	// Ella sits in the lane the cast locks: straight left of the front mechanism.
	R.Input.PlayerPos = R.Model.GetMechanismHome(EKeeperPart::Front) + FVector2D(-400.0f, 0.0f);
	R.Input.PlayerRadius = 20.0f;
	R.Run(R.Encounter.PhaseTransitionSeconds + 8.0f);
	int32 Hits = 0;
	for (const FKeeperCommand& C : R.Commands)
	{
		if (C.Type == EKeeperCommandType::DamagePlayer && C.Name == FName(TEXT("MECH_Front_Cast")))
		{
			++Hits;
			TestEqual(TEXT("chain damage 1.25"), C.Damage, 1.25f);
		}
	}
	TestEqual(TEXT("exactly one hit for the cast"), Hits, 1);
	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FKeeperTalon, "UmbrellaElla.Keeper.TalonWarnsStrikesAndRearms", KeeperFlags)
bool FKeeperTalon::RunTest(const FString& Parameters)
{
	FKeeperRig R;
	FKeeperRuleSwitches Only;
	Only.bRed = false;
	Only.bYellow = false;
	Only.bGust = false;
	R.Start(EKeeperPhase::Wings, Only);
	R.Input.PlayerPos = R.Model.GetClaw() + FVector2D(-200.0f, 0.0f);
	R.Input.PlayerRadius = 30.0f;
	R.Run(R.Encounter.PhaseTransitionSeconds + R.Tuning.TalonFirstAtSeconds + 0.2f);
	TestEqual(TEXT("talon warning started"), static_cast<int32>(R.Model.GetPhysical()), static_cast<int32>(EKeeperPhysical::Talon));
	TestFalse(TEXT("not armed after committing"), R.Model.IsTalonArmed());
	R.Run(R.Tuning.TalonWarningSeconds + R.Tuning.TalonStrikeSeconds + 0.1f);
	int32 Hits = 0;
	float Damage = 0.0f;
	for (const FKeeperCommand& C : R.Commands)
	{
		if (C.Type == EKeeperCommandType::DamagePlayer)
		{
			++Hits;
			Damage = C.Damage;
		}
	}
	TestEqual(TEXT("one talon hit"), Hits, 1);
	TestEqual(TEXT("talon damage 1.5"), Damage, 1.5f);
	// Staying inside 270 never re-arms; leaving beyond 370 does.
	R.Run(R.Tuning.TalonCooldownSeconds + 1.0f);
	TestFalse(TEXT("still not armed inside reach"), R.Model.IsTalonArmed());
	R.Input.PlayerPos = R.Model.GetClaw() + FVector2D(-(R.Tuning.TalonRearmExit + 20.0f), 0.0f);
	R.Run(Step * 2.0f);
	TestTrue(TEXT("armed after leaving beyond 370"), R.Model.IsTalonArmed());
	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FKeeperTalonNoDamageInWarning, "UmbrellaElla.Keeper.TalonWarningDoesNoDamage", KeeperFlags)
bool FKeeperTalonNoDamageInWarning::RunTest(const FString& Parameters)
{
	FKeeperRig R;
	FKeeperRuleSwitches Only;
	Only.bRed = false;
	Only.bYellow = false;
	Only.bGust = false;
	R.Start(EKeeperPhase::Wings, Only);
	R.Input.PlayerPos = R.Model.GetClaw() + FVector2D(-100.0f, 0.0f);
	R.Run(R.Encounter.PhaseTransitionSeconds + R.Tuning.TalonFirstAtSeconds + 0.2f + R.Tuning.TalonWarningSeconds - 0.2f);
	TestTrue(TEXT("still warning"), R.Model.GetStage() == EKeeperStage::Warning);
	TestEqual(TEXT("no damage during the warning"), R.Count(EKeeperCommandType::DamagePlayer), 0);
	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FKeeperGust, "UmbrellaElla.Keeper.GustLocksBandAndStopsWithWings", KeeperFlags)
bool FKeeperGust::RunTest(const FString& Parameters)
{
	FKeeperRig R;
	FKeeperRuleSwitches Only;
	Only.bRed = false;
	Only.bYellow = false;
	Only.bTalon = false;
	R.Start(EKeeperPhase::Wings, Only);
	R.Input.PlayerPos = FVector2D(-600.0f, 300.0f);
	R.Run(R.Encounter.PhaseTransitionSeconds + R.Tuning.GustFirstAtSeconds + 0.2f);
	TestEqual(TEXT("gust warning"), static_cast<int32>(R.Model.GetPhysical()), static_cast<int32>(EKeeperPhysical::Gust));
	TestEqual(TEXT("band locked at Ella's altitude"), R.Model.GetGustBandZ(), 300.0f);
	R.Input.PlayerPos.Y = 900.0f; // moving away does not move the band
	R.Run(R.Tuning.GustWarningSeconds);
	TestTrue(TEXT("front travelling"), R.Model.IsGustTravelling());
	TestEqual(TEXT("band stays locked"), R.Model.GetGustBandZ(), 300.0f);
	R.BreakWings();
	TestTrue(TEXT("breaking the wings removes the gust"), R.Model.GetPhysical() == EKeeperPhysical::None);
	TestTrue(TEXT("gusts cleared"), R.Count(EKeeperCommandType::ClearGusts) >= 1);
	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FKeeperGustPush, "UmbrellaElla.Keeper.GustDamagesAndPushesOnce", KeeperFlags)
bool FKeeperGustPush::RunTest(const FString& Parameters)
{
	FKeeperRig R;
	FKeeperRuleSwitches Only;
	Only.bRed = false;
	Only.bYellow = false;
	Only.bTalon = false;
	R.Start(EKeeperPhase::Wings, Only);
	R.Input.PlayerPos = FVector2D(R.Model.GetMuzzle().X - 400.0f, 300.0f);
	R.Run(R.Encounter.PhaseTransitionSeconds + R.Tuning.GustFirstAtSeconds + R.Tuning.GustWarningSeconds + 3.0f);
	int32 Damage = 0;
	int32 Pushes = 0;
	for (const FKeeperCommand& C : R.Commands)
	{
		Damage += (C.Type == EKeeperCommandType::DamagePlayer) ? 1 : 0;
		Pushes += (C.Type == EKeeperCommandType::PushPlayer) ? 1 : 0;
	}
	TestEqual(TEXT("one damage per gust"), Damage, 1);
	TestTrue(TEXT("pushed while inside the front"), Pushes >= 1);
	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FKeeperReducedPressure, "UmbrellaElla.Keeper.RedIsReducedDuringPhysicalActivity", KeeperFlags)
bool FKeeperReducedPressure::RunTest(const FString& Parameters)
{
	FKeeperRig R;
	FKeeperRuleSwitches Only;
	Only.bYellow = false;
	Only.bTalon = false;
	Only.bGust = false;
	Only.bMiddleCast = false;
	Only.bRearCast = false;
	R.Start(EKeeperPhase::Mechanisms, Only);
	R.Input.PlayerPos = FVector2D(-900.0f, 0.0f);
	// Run into the front cast warning, then watch volleys that start while it is active.
	R.Run(R.Encounter.PhaseTransitionSeconds + R.Tuning.CastFirstAtSeconds + 0.1f);
	TestTrue(TEXT("physical threatening"), R.Model.IsPhysicalThreatening());
	R.Commands.Reset();
	const float Cutoff = R.Model.GetRedCountdown();
	R.Run(Cutoff + 0.3f);
	TestTrue(TEXT("the new volley is one shot"), R.CountShots(EUmbrellaShotKind::EnemyRed) == 1 || !R.Model.IsPhysicalThreatening());
	TestEqual(TEXT("reduced interval is 2.16 s"), R.Tuning.ReducedIntervalSeconds, 2.16f);
	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FKeeperSlowEye, "UmbrellaElla.Keeper.ClockHitStartsSlowAndEyeThenBlackout", KeeperFlags)
bool FKeeperSlowEye::RunTest(const FString& Parameters)
{
	FKeeperRig R;
	R.Start(EKeeperPhase::Mechanisms);
	R.SkipTransition();
	R.Model.ApplyPlayerHit(EKeeperPart::Front, 1.0f, R.Commands); // opens the clock
	R.Model.ApplyPlayerHit(EKeeperPart::Clock, 5.0f, R.Commands);
	TestTrue(TEXT("slow on the qualifying hit"), R.Model.IsSlowed());
	TestEqual(TEXT("world scale 0.35"), R.Model.GetWorldScale(), 0.35f);
	TestTrue(TEXT("eye exposed by the same hit"), R.Model.IsEyeExposed());
	R.Model.ApplyPlayerHit(EKeeperPart::Clock, 5.0f, R.Commands);
	TestEqual(TEXT("one slow start per opening"), R.Count(EKeeperCommandType::SlowStarted), 1);
	const FKeeperHitResult Eye = R.Model.ApplyPlayerHit(EKeeperPart::Eye, 1.0f, R.Commands);
	TestTrue(TEXT("eye hit consumed"), Eye.Outcome == EKeeperHitOutcome::Blocked);
	TestTrue(TEXT("blackout starts"), R.Model.IsBlackedOut());
	TestFalse(TEXT("blackout replaces the slow"), R.Model.IsSlowed());
	TestFalse(TEXT("eye window consumed"), R.Model.IsEyeExposed());
	TestTrue(TEXT("pending shots and projectiles cleared"), R.Model.GetPendingShotCount() == 0 && R.Count(EKeeperCommandType::ClearProjectiles) >= 1);
	R.Run(R.Tuning.BlackoutSeconds + 0.2f);
	TestFalse(TEXT("blackout ends"), R.Model.IsBlackedOut());
	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FKeeperSlowStretchesTime, "UmbrellaElla.Keeper.SlowStretchesWorldTimersNotClockTimers", KeeperFlags)
bool FKeeperSlowStretchesTime::RunTest(const FString& Parameters)
{
	FKeeperRig R;
	FKeeperRuleSwitches Only;
	Only.bGust = false;
	Only.bTalon = false;
	Only.bYellow = false;
	R.Start(EKeeperPhase::Mechanisms, Only);
	R.SkipTransition();
	R.Model.ApplyPlayerHit(EKeeperPart::Front, 1.0f, R.Commands);
	R.Model.ApplyPlayerHit(EKeeperPart::Clock, 5.0f, R.Commands);
	TestTrue(TEXT("slowed"), R.Model.IsSlowed());
	const float RedBefore = R.Model.GetRedCountdown();
	TestTrue(TEXT("opening starts the fire pause"), R.Model.IsFirePaused());
	R.Run(0.3f);
	TestTrue(TEXT("fire pause froze the countdown"), FMath::IsNearlyEqual(RedBefore, R.Model.GetRedCountdown(), 0.001f));
	R.Run(R.Tuning.FirePauseSeconds);
	TestFalse(TEXT("pause is over"), R.Model.IsFirePaused());
	const float RedMid = R.Model.GetRedCountdown();
	R.Run(0.5f);
	const float RedAfter = R.Model.GetRedCountdown();
	TestTrue(TEXT("0.5 s of gameplay time is about 0.175 s of world time while slowed"),
		FMath::IsNearlyEqual(RedMid - RedAfter, 0.5f * R.Tuning.SlowWorldScale, 0.06f));
	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FKeeperStun, "UmbrellaElla.Keeper.BreakStunCancelsPhysicalMove", KeeperFlags)
bool FKeeperStun::RunTest(const FString& Parameters)
{
	FKeeperRig R;
	FKeeperRuleSwitches Only;
	Only.bRed = false;
	Only.bYellow = false;
	Only.bTalon = false;
	R.Start(EKeeperPhase::Mechanisms, Only);
	R.Input.PlayerPos = FVector2D(-900.0f, 0.0f);
	R.Run(R.Encounter.PhaseTransitionSeconds + R.Tuning.CastFirstAtSeconds + 0.2f);
	TestTrue(TEXT("front cast running"), R.Model.GetPhysical() == EKeeperPhysical::FrontCast);
	R.BreakMechanism(EKeeperPart::Front);
	TestTrue(TEXT("cast cancelled at once"), R.Model.GetPhysical() == EKeeperPhysical::None);
	TestEqual(TEXT("cancel command sent"), R.Count(EKeeperCommandType::PhysicalCancelled), 1);
	TestTrue(TEXT("stunned"), R.Model.IsStunned());
	R.Run(R.Tuning.BreakStunSeconds + 0.2f);
	TestFalse(TEXT("stun ends"), R.Model.IsStunned());
	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FKeeperRetry, "UmbrellaElla.Keeper.RetryRestoresPhaseCheckpoint", KeeperFlags)
bool FKeeperRetry::RunTest(const FString& Parameters)
{
	FKeeperRig R;
	R.Start();
	R.SkipTransition();
	R.BreakWings();
	R.Run(R.Encounter.PhaseTransitionSeconds + Step);
	R.Model.ApplyPlayerHit(EKeeperPart::Front, 50.0f, R.Commands);
	TestEqual(TEXT("front damaged"), R.Model.GetPartHp(EKeeperPart::Front), 50.0f);
	R.Commands.Reset();
	R.Model.RetryCheckpoint(R.Commands);
	TestTrue(TEXT("back in the mechanisms phase"), R.Model.GetPhase() == EKeeperPhase::Mechanisms);
	TestEqual(TEXT("front restored to full"), R.Model.GetPartHp(EKeeperPart::Front), R.Tuning.FrontHp);
	TestTrue(TEXT("wings stay broken (earlier phase)"), R.Model.IsPartBroken(EKeeperPart::Wings));
	TestTrue(TEXT("quiet transition again"), R.Model.IsTransitioning());
	TestEqual(TEXT("no leftover queued shots"), R.Model.GetPendingShotCount(), 0);
	TestTrue(TEXT("hazards cleared"), R.Count(EKeeperCommandType::ClearProjectiles) >= 1);
	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FKeeperCheckpointCarriesClock, "UmbrellaElla.Keeper.ClockDamageCarriesIntoCheckpoint", KeeperFlags)
bool FKeeperCheckpointCarriesClock::RunTest(const FString& Parameters)
{
	FKeeperRig R;
	R.Start(EKeeperPhase::Mechanisms);
	R.SkipTransition();
	R.Model.ApplyPlayerHit(EKeeperPart::Front, 1.0f, R.Commands);
	R.Model.ApplyPlayerHit(EKeeperPart::Clock, 100.0f, R.Commands);
	R.BreakMechanism(EKeeperPart::Front);
	R.BreakMechanism(EKeeperPart::Middle);
	R.BreakMechanism(EKeeperPart::Rear);
	TestTrue(TEXT("clock phase"), R.Model.GetPhase() == EKeeperPhase::Clock);
	const float Carried = R.Model.GetPartHp(EKeeperPart::Clock);
	TestEqual(TEXT("clock lost 100"), Carried, R.Tuning.ClockHp - 100.0f);
	R.Run(R.Encounter.PhaseTransitionSeconds + Step);
	R.Model.ApplyPlayerHit(EKeeperPart::Clock, 20.0f, R.Commands);
	R.Model.RetryCheckpoint(R.Commands);
	TestEqual(TEXT("retry restores the clock to its checkpoint HP"), R.Model.GetPartHp(EKeeperPart::Clock), Carried);
	return true;
}

#endif
