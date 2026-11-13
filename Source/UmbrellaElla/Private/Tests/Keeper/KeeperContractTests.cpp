#include "Misc/AutomationTest.h"

#if WITH_AUTOMATION_TESTS

#include "Core/UmbrellaSourceIds.h"
#include "Encounter/EncounterTuning.h"
#include "Encounter/KeeperFightModel.h"
#include "Owl/KeeperTuning.h"

// Clause proofs for the Keeper attack contract (GDD SH1.0 section 5): one behavior per test, each read from the model.

namespace
{
	constexpr EAutomationTestFlags KeeperContractFlags = EAutomationTestFlags::EditorContext | EAutomationTestFlags::ClientContext | EAutomationTestFlags::EngineFilter;
	constexpr float KeeperContractStep = 0.05f;

	struct FKeeperContractRig
	{
		FKeeperFightModel Model;
		TArray<FKeeperCommand> Commands;
		FKeeperTickInput Input;
		FKeeperTuning Tuning;
		FEncounterTuning Encounter;

		FKeeperContractRig()
		{
			Input.PlayerPos = FVector2D(-900.0f, 0.0f);
			Input.PlayerRadius = 10.0f;
		}

		void Start(EKeeperPhase Phase, const FKeeperRuleSwitches& Switches)
		{
			Model.Init(Tuning, Encounter, Switches);
			Model.BeginPhase(Phase, Commands);
		}

		/** One step; returns the commands it produced. */
		TArray<FKeeperCommand> StepOnce()
		{
			TArray<FKeeperCommand> Out;
			Model.Step(KeeperContractStep, Input, Out);
			Commands.Append(Out);
			return Out;
		}

		void Run(float Seconds)
		{
			for (float T = 0.0f; T < Seconds; T += KeeperContractStep)
			{
				StepOnce();
			}
		}

		static int32 CountType(const TArray<FKeeperCommand>& List, EKeeperCommandType Type)
		{
			int32 N = 0;
			for (const FKeeperCommand& C : List)
			{
				N += (C.Type == Type) ? 1 : 0;
			}
			return N;
		}

		static FKeeperRuleSwitches Quiet()
		{
			FKeeperRuleSwitches S;
			S.bRed = false;
			S.bYellow = false;
			S.bTalon = false;
			S.bGust = false;
			return S;
		}
	};
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FKeeperStunHoldsQueuedFire, "UmbrellaElla.Keeper.StunHoldsQueuedFire", KeeperContractFlags)
bool FKeeperStunHoldsQueuedFire::RunTest(const FString& Parameters)
{
	// OWL-30 / OWL-12: a mechanism break stuns for 1.2 s; new fire stops (queued emissions hold), missiles in flight continue.
	FKeeperContractRig R;
	FKeeperRuleSwitches Only = FKeeperContractRig::Quiet();
	Only.bRed = true;
	Only.bFrontCast = false;
	Only.bMiddleCast = false;
	Only.bRearCast = false;
	R.Start(EKeeperPhase::Mechanisms, Only);
	bool bQueued = false;
	for (float T = 0.0f; T < 10.0f && !bQueued; T += KeeperContractStep)
	{
		R.StepOnce();
		bQueued = R.Model.GetPendingShotCount() > 0;
	}
	TestTrue(TEXT("a red volley is mid-emission"), bQueued);
	const int32 QueuedBefore = R.Model.GetPendingShotCount();
	TArray<FKeeperCommand> BreakOut;
	R.Model.ApplyPlayerHit(EKeeperPart::Front, R.Tuning.FrontHp, BreakOut);
	TestTrue(TEXT("break stuns"), R.Model.IsStunned());
	TestEqual(TEXT("traveling missiles are not cleared by the stun"), FKeeperContractRig::CountType(BreakOut, EKeeperCommandType::ClearProjectiles), 0);
	int32 ShotsDuringStun = 0;
	int32 ShotsAfter = 0;
	while (R.Model.IsStunned())
	{
		const int32 Shots = FKeeperContractRig::CountType(R.StepOnce(), EKeeperCommandType::FireShot);
		(R.Model.IsStunned() ? ShotsDuringStun : ShotsAfter) += Shots;
		if (R.Model.IsStunned())
		{
			TestEqual(TEXT("queued emissions are held, not dropped"), R.Model.GetPendingShotCount(), QueuedBefore);
		}
	}
	TestEqual(TEXT("no new fire while stunned"), ShotsDuringStun, 0);
	for (int32 Index = 0; Index < 10; ++Index)
	{
		ShotsAfter += FKeeperContractRig::CountType(R.StepOnce(), EKeeperCommandType::FireShot);
	}
	TestTrue(TEXT("held emissions deliver after the stun"), ShotsAfter >= QueuedBefore);
	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FKeeperTalonVerticalExit, "UmbrellaElla.Keeper.TalonVerticalExitSuppressesImpossibleLaunch", KeeperContractFlags)
bool FKeeperTalonVerticalExit::RunTest(const FString& Parameters)
{
	// OWL-19: a conservative vertical-exit check suppresses a talon launch Ella could not rise or fall out of.
	FKeeperContractRig R;
	FKeeperRuleSwitches Only = FKeeperContractRig::Quiet();
	Only.bTalon = true;
	R.Start(EKeeperPhase::Wings, Only);
	R.Input.PlayerPos = R.Model.GetClaw() + FVector2D(-150.0f, 0.0f);
	R.Input.bHasVerticalBounds = true;
	R.Input.EllaClimbRate = 96.0f;
	R.Input.EllaDropRate = 264.0f;
	// Pinned: floor and ceiling hug Ella, no room to leave the 48-wide tip band.
	R.Input.FloorZ = R.Input.PlayerPos.Y - R.Input.PlayerRadius - 5.0f;
	R.Input.CeilingZ = R.Input.PlayerPos.Y + R.Input.PlayerRadius + 5.0f;
	R.Run(R.Encounter.PhaseTransitionSeconds + R.Tuning.TalonFirstAtSeconds + 2.0f);
	TestTrue(TEXT("no talon when Ella cannot exit vertically"), R.Model.GetPhysical() == EKeeperPhysical::None);
	TestFalse(TEXT("the static rule agrees"), FKeeperFightModel::CanExitVertically(R.Input, R.Tuning.TalonTipWidth * 0.5f, R.Tuning.TalonWarningSeconds));
	// Too slow to clear in the warning, even with room.
	R.Input.FloorZ = R.Input.PlayerPos.Y - 1000.0f;
	R.Input.CeilingZ = R.Input.PlayerPos.Y + 1000.0f;
	FKeeperTickInput Slow = R.Input;
	Slow.EllaClimbRate = 1.0f;
	Slow.EllaDropRate = 1.0f;
	TestFalse(TEXT("too slow to clear in the warning"), FKeeperFightModel::CanExitVertically(Slow, R.Tuning.TalonTipWidth * 0.5f, R.Tuning.TalonWarningSeconds));
	// Room above: the talon launches.
	R.Run(KeeperContractStep * 2.0f);
	TestTrue(TEXT("talon launches once an exit exists"), R.Model.GetPhysical() == EKeeperPhysical::Talon);
	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FKeeperMiddleWarningCurve, "UmbrellaElla.Keeper.MiddleWarningShowsTheCurve", KeeperContractFlags)
bool FKeeperMiddleWarningCurve::RunTest(const FString& Parameters)
{
	// OWL-25: the middle warning telegraphs the same curve (sign and 80-unit amplitude) the stroke then takes.
	FKeeperContractRig R;
	FKeeperRuleSwitches Only = FKeeperContractRig::Quiet();
	Only.bFrontCast = false;
	Only.bRearCast = false;
	R.Start(EKeeperPhase::Mechanisms, Only);
	FKeeperCommand Warning;
	bool bWarned = false;
	for (float T = 0.0f; T < 10.0f && !bWarned; T += KeeperContractStep)
	{
		for (const FKeeperCommand& C : R.StepOnce())
		{
			if (C.Type == EKeeperCommandType::PhysicalWarning && C.Physical == EKeeperPhysical::MiddleCurve)
			{
				Warning = C;
				bWarned = true;
			}
		}
	}
	TestTrue(TEXT("middle warning seen"), bWarned);
	TestEqual(TEXT("warning curve = serial sign x 80"), Warning.Curve, FKeeperFightModel::MiddleSignForSerial(Warning.Serial) * R.Tuning.MiddleOffset);
	TestTrue(TEXT("warning stage"), Warning.Stage == EKeeperStage::Warning);
	// Mid-stroke the head sits on the warned side of the straight line.
	while (R.Model.GetStage() != EKeeperStage::Stroke)
	{
		R.StepOnce();
	}
	const float HalfStroke = 0.5f * R.Tuning.ChainReach / R.Tuning.ChainSpeed;
	R.Run(HalfStroke - KeeperContractStep);
	const FVector2D Axis = (Warning.B - Warning.A).GetSafeNormal();
	const FVector2D Normal(-Axis.Y, Axis.X);
	const float Side = FVector2D::DotProduct(R.Model.GetHeadPosition() - Warning.A, Normal);
	TestTrue(TEXT("head bends to the warned side"), Side * Warning.Curve > 0.0f);
	TestTrue(TEXT("bend near the warned amplitude"), FMath::Abs(Side) >= 0.8f * R.Tuning.MiddleOffset);
	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FKeeperRearSecondClack, "UmbrellaElla.Keeper.RearPauseSignalsUnfinishedStroke", KeeperContractFlags)
bool FKeeperRearSecondClack::RunTest(const FString& Parameters)
{
	// OWL-27: the midpoint stop is announced as a pause (second clack) at the stopped head, not as recovery.
	FKeeperContractRig R;
	FKeeperRuleSwitches Only = FKeeperContractRig::Quiet();
	Only.bFrontCast = false;
	Only.bMiddleCast = false;
	R.Start(EKeeperPhase::Mechanisms, Only);
	FKeeperCommand Clack;
	FKeeperCommand Warning;
	bool bClack = false;
	bool bRecoveryBeforeClack = false;
	for (float T = 0.0f; T < 10.0f && !bClack; T += KeeperContractStep)
	{
		for (const FKeeperCommand& C : R.StepOnce())
		{
			if (C.Type == EKeeperCommandType::PhysicalWarning)
			{
				Warning = C;
			}
			bRecoveryBeforeClack |= (C.Type == EKeeperCommandType::PhysicalRecovery);
			if (C.Type == EKeeperCommandType::PhysicalStrike && C.Stage == EKeeperStage::Pause)
			{
				Clack = C;
				bClack = true;
			}
		}
	}
	TestTrue(TEXT("second clack announced"), bClack);
	TestFalse(TEXT("no recovery before the clack"), bRecoveryBeforeClack);
	TestEqual(TEXT("clack lasts the safe pause"), Clack.Value, R.Tuning.RearPauseSeconds);
	TestTrue(TEXT("clack marks the stopped head at the midpoint"), Clack.A.Equals((Warning.A + Warning.B) * 0.5f, 1.0f));
	TestTrue(TEXT("the stroke is still unfinished"), R.Model.IsPhysicalThreatening());
	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FKeeperBeatRepriseCue, "UmbrellaElla.Keeper.DoubleBeatRepriseCue", KeeperContractFlags)
bool FKeeperBeatRepriseCue::RunTest(const FString& Parameters)
{
	// OWL-28: a reprise cue marks the repeat, landing with its first shot on the original path.
	FKeeperContractRig R;
	FKeeperRuleSwitches Only = FKeeperContractRig::Quiet();
	R.Start(EKeeperPhase::Clock, Only);
	TArray<FKeeperCommand> Beats;
	int32 CueAtShot = INDEX_NONE;
	FKeeperCommand Cue;
	for (float T = 0.0f; T < 10.0f && Beats.Num() < 2 * R.Tuning.RedShotCount; T += KeeperContractStep)
	{
		for (const FKeeperCommand& C : R.StepOnce())
		{
			if (C.Type == EKeeperCommandType::BeatReprise && CueAtShot == INDEX_NONE)
			{
				CueAtShot = Beats.Num();
				Cue = C;
			}
			if (C.Type == EKeeperCommandType::FireShot)
			{
				Beats.Add(C);
			}
		}
	}
	TestEqual(TEXT("one cue, right before the repeat's first shot"), CueAtShot, R.Tuning.RedShotCount);
	TestTrue(TEXT("cue names the double beat"), Cue.Name == UmbrellaSourceIds::ClockDoubleBeat());
	if (Beats.Num() > R.Tuning.RedShotCount)
	{
		TestTrue(TEXT("cue sits on the original path origin"), Cue.A.Equals(Beats[R.Tuning.RedShotCount].A, 0.01f));
	}
	return true;
}

#endif
