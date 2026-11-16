#include "Misc/AutomationTest.h"

#if WITH_AUTOMATION_TESTS

#include "Attack/AttackCadence.h"
#include "Core/UmbrellaTuning.h"
#include "UObject/Package.h"
#include "Input/UmbrellaInputBindings.h"
#include "Motor/MotorModel.h"
#include "Motor/MotorTuning.h"
#include "Umbrella/UmbrellaAction.h"
#include "Umbrella/UmbrellaFlightTuning.h"
#include "Umbrella/UmbrellaStateComponent.h"

namespace
{
	const float TestDeltas[] = {1.0f / 30.0f, 1.0f / 60.0f, 1.0f / 120.0f};

	const FMotorTuning& Motor()
	{
		return GetDefault<UUmbrellaTuning>()->Motor;
	}

	/** Run the model for Seconds at Delta; returns the summed displacement. */
	FVector2D Run(FMotorModelState& State, const FMotorInput& Input, float Seconds, float Delta)
	{
		FVector2D Total = FVector2D::ZeroVector;
		const int32 Frames = FMath::RoundToInt(Seconds / Delta);
		for (int32 Frame = 0; Frame < Frames; ++Frame)
		{
			Total += MotorModel::Step(State, Input, Motor(), Delta);
		}
		return Total;
	}
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FMoveBaselineTest, "UmbrellaElla.Move.Baseline", EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FMoveBaselineTest::RunTest(const FString& Parameters)
{
	// GDD SH1.0 numbers as pinned in docs/feature-manifest.json approved_parameters.
	const FMotorTuning& M = Motor();
	TestEqual(TEXT("rise"), M.RiseSpeed, 240.0f); // D-new-move-speeds (GDD 120, felt 2x)
	TestEqual(TEXT("fall"), M.FallSpeed, 660.0f); // D-new-move-speeds (GDD 330)
	TestEqual(TEXT("free fall"), M.FreeFallSpeed, 1220.0f);
	TestEqual(TEXT("horizontal max"), M.HorizontalMaxSpeed, 580.0f);
	TestEqual(TEXT("trim"), M.VerticalTrimPct, 20.0f);
	TestEqual(TEXT("hop distance"), M.HopDistance, 80.0f);
	TestEqual(TEXT("hop duration"), M.HopDurationSeconds, 0.22f);
	TestEqual(TEXT("hop cooldown"), M.HopCooldownSeconds, 0.7f);
	TestEqual(TEXT("hop protection"), M.HopProtectionSeconds, 0.2f);
	TestEqual(TEXT("dash distance"), M.DashDistance, 170.0f); // D-new-move-speeds
	TestEqual(TEXT("dash duration"), M.DashDurationSeconds, 0.16f);
	TestEqual(TEXT("dash cooldown"), M.DashCooldownSeconds, 0.3f);
	TestEqual(TEXT("free-fall dash"), M.FreeFallDashMultiplier, 0.5f);
	TestEqual(TEXT("wind accel"), M.WindAcceleration, 3.0f);
	TestEqual(TEXT("wind open decay"), M.WindOpenDecay, 1.5f);
	TestEqual(TEXT("wind falling decay"), M.WindFallingDecay, 12.0f);
	TestEqual(TEXT("wind maximum"), M.WindMaxSpeed, 720.0f); // GDD 360 x WindScale 2 (D-new-move-speeds)
	const FUmbrellaFlightTuning& U = GetDefault<UUmbrellaTuning>()->UmbrellaFlight;
	TestEqual(TEXT("absorb range"), U.AbsorbRange, 240.0f);
	TestEqual(TEXT("absorb cone"), U.AbsorbConeDegrees, 60.0f);
	TestEqual(TEXT("pull speed"), U.PullSpeed, 700.0f);
	TestEqual(TEXT("capture distance"), U.CaptureDistance, 24.0f);
	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FMoveActionRulesTest, "UmbrellaElla.Move.ActionRules", EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FMoveActionRulesTest::RunTest(const FString& Parameters)
{
	TestEqual(TEXT("neither"), UmbrellaActionRules::ResolveAction(false, false), EUmbrellaAction::Rise);
	TestEqual(TEXT("shoot only"), UmbrellaActionRules::ResolveAction(true, false), EUmbrellaAction::ShootFall);
	TestEqual(TEXT("absorb only"), UmbrellaActionRules::ResolveAction(false, true), EUmbrellaAction::AbsorbFall);
	TestEqual(TEXT("both"), UmbrellaActionRules::ResolveAction(true, true), EUmbrellaAction::FreeFall);

	// Forbidden combinations, over every state.
	for (uint8 Index = 0; Index <= static_cast<uint8>(EUmbrellaAction::FreeFall); ++Index)
	{
		const EUmbrellaAction Action = static_cast<EUmbrellaAction>(Index);
		TestFalse(TEXT("never fire and absorb together"), UmbrellaActionRules::CanFire(Action) && UmbrellaActionRules::CanAbsorb(Action));
		TestFalse(TEXT("never hop and dash together"), UmbrellaActionRules::CanHop(Action) && UmbrellaActionRules::CanDash(Action));
		if (!UmbrellaActionRules::IsFalling(Action))
		{
			TestFalse(TEXT("no fire overhead"), UmbrellaActionRules::CanFire(Action));
			TestFalse(TEXT("no absorb overhead"), UmbrellaActionRules::CanAbsorb(Action));
		}
	}
	TestTrue(TEXT("fire in shoot-fall"), UmbrellaActionRules::CanFire(EUmbrellaAction::ShootFall));
	TestFalse(TEXT("no fire in absorb-fall"), UmbrellaActionRules::CanFire(EUmbrellaAction::AbsorbFall));
	TestFalse(TEXT("no fire in free fall"), UmbrellaActionRules::CanFire(EUmbrellaAction::FreeFall));
	TestTrue(TEXT("absorb in absorb-fall"), UmbrellaActionRules::CanAbsorb(EUmbrellaAction::AbsorbFall));
	TestFalse(TEXT("no absorb in free fall"), UmbrellaActionRules::CanAbsorb(EUmbrellaAction::FreeFall));
	TestTrue(TEXT("hop overhead"), UmbrellaActionRules::CanHop(EUmbrellaAction::Rise));
	TestTrue(TEXT("dash in free fall"), UmbrellaActionRules::CanDash(EUmbrellaAction::FreeFall));

	// Ride: overhead, held, and inside a current.
	TestTrue(TEXT("ride ok"), UmbrellaActionRules::CanRide(EUmbrellaAction::Rise, true, true));
	TestFalse(TEXT("ride needs hold"), UmbrellaActionRules::CanRide(EUmbrellaAction::Rise, false, true));
	TestFalse(TEXT("ride needs current"), UmbrellaActionRules::CanRide(EUmbrellaAction::Rise, true, false));
	TestFalse(TEXT("ride ends when falling"), UmbrellaActionRules::CanRide(EUmbrellaAction::ShootFall, true, true));

	TestEqual(TEXT("left input = back"), UmbrellaActionRules::ContextDashDirection(-0.5f), EUmbrellaDashDirection::Back);
	TestEqual(TEXT("no input = forward"), UmbrellaActionRules::ContextDashDirection(0.0f), EUmbrellaDashDirection::Forward);
	TestEqual(TEXT("right input = forward"), UmbrellaActionRules::ContextDashDirection(1.0f), EUmbrellaDashDirection::Forward);
	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FMoveSpeedsTest, "UmbrellaElla.Move.StateSpeedsAndTrim", EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FMoveSpeedsTest::RunTest(const FString& Parameters)
{
	FMotorInput Input;
	Input.Action = EUmbrellaAction::Rise;
	TestEqual(TEXT("rise"), MotorModel::BaseVerticalSpeed(Input, Motor()), 240.0f);
	Input.Action = EUmbrellaAction::ShootFall;
	TestEqual(TEXT("shoot fall"), MotorModel::BaseVerticalSpeed(Input, Motor()), -660.0f);
	Input.Action = EUmbrellaAction::AbsorbFall;
	TestEqual(TEXT("absorb fall"), MotorModel::BaseVerticalSpeed(Input, Motor()), -660.0f);
	Input.Action = EUmbrellaAction::FreeFall;
	TestEqual(TEXT("free fall"), MotorModel::BaseVerticalSpeed(Input, Motor()), -1220.0f);

	// Trim: up adds 20% of ascent and takes 20% off descent; down does the reverse.
	Input.TrimAxis = 1.0f;
	Input.Action = EUmbrellaAction::Rise;
	TestEqual(TEXT("rise + trim up"), MotorModel::BaseVerticalSpeed(Input, Motor()), 288.0f);
	Input.Action = EUmbrellaAction::ShootFall;
	TestEqual(TEXT("fall + trim up"), MotorModel::BaseVerticalSpeed(Input, Motor()), -528.0f);
	Input.TrimAxis = -1.0f;
	TestEqual(TEXT("fall + trim down"), MotorModel::BaseVerticalSpeed(Input, Motor()), -792.0f);
	Input.Action = EUmbrellaAction::Rise;
	TestEqual(TEXT("rise + trim down"), MotorModel::BaseVerticalSpeed(Input, Motor()), 192.0f);
	Input.TrimAxis = 5.0f;
	TestEqual(TEXT("trim clamps to full stick"), MotorModel::BaseVerticalSpeed(Input, Motor()), 288.0f);

	// Lift scales with active health, from MinLift to 1 (UMB-05 / SURV-05).
	TestEqual(TEXT("full health"), UmbrellaActionRules::LiftMultiplier(3.0f, 3.0f, 0.3f), 1.0f);
	TestEqual(TEXT("empty"), UmbrellaActionRules::LiftMultiplier(0.0f, 3.0f, 0.3f), 0.3f);
	TestEqual(TEXT("one of three"), UmbrellaActionRules::LiftMultiplier(1.0f, 3.0f, 0.3f), 0.3f + 0.7f / 3.0f);
	TestEqual(TEXT("over full clamps"), UmbrellaActionRules::LiftMultiplier(9.0f, 3.0f, 0.3f), 1.0f);
	Input.LiftMultiplier = 0.3f;
	Input.TrimAxis = 0.0f;
	TestEqual(TEXT("rise at min lift"), MotorModel::BaseVerticalSpeed(Input, Motor()), 72.0f);
	Input.Action = EUmbrellaAction::ShootFall;
	TestEqual(TEXT("lift does not slow a fall"), MotorModel::BaseVerticalSpeed(Input, Motor()), -660.0f);
	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FMoveHopDashTest, "UmbrellaElla.Move.HopDashTuned", EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FMoveHopDashTest::RunTest(const FString& Parameters)
{
	for (const float Delta : TestDeltas)
	{
		// Hop overhead: 40 units over 0.22 s, to the right with no input.
		{
			FMotorModelState State;
			FMotorInput Input;
			MotorModel::Request(State, EMotorRequest::Hop, Motor());
			const FVector2D First = MotorModel::Step(State, Input, Motor(), Delta);
			TestEqual(TEXT("hop speed"), static_cast<float>(State.Velocity.X), 80.0f / 0.22f, 0.01f);
			TestTrue(TEXT("hop protects"), MotorModel::IsProtected(State));
			const FVector2D Rest = Run(State, Input, 0.5f, Delta);
			TestEqual(TEXT("hop distance exact"), static_cast<float>(First.X + Rest.X), 80.0f, 0.01f);
			TestFalse(TEXT("protection ended"), MotorModel::IsProtected(State));
		}
		// Hop cooldown 0.7 s: a second press inside it does not start (and expires with the 0.1 s buffer).
		{
			FMotorModelState State;
			FMotorInput Input;
			MotorModel::Request(State, EMotorRequest::Hop, Motor());
			Run(State, Input, 0.3f, Delta);
			MotorModel::Request(State, EMotorRequest::Hop, Motor());
			const FVector2D Blocked = Run(State, Input, 0.2f, Delta);
			TestEqual(TEXT("no second hop inside cooldown"), static_cast<float>(Blocked.X), 0.0f, 0.01f);
			Run(State, Input, 0.5f, Delta);
			MotorModel::Request(State, EMotorRequest::Hop, Motor());
			const FVector2D Again = Run(State, Input, 0.5f, Delta);
			TestEqual(TEXT("hop again after cooldown"), static_cast<float>(Again.X), 80.0f, 0.01f);
		}
		// A press just before the cooldown ends still fires (toggle buffer 0.1 s).
		{
			FMotorModelState State;
			FMotorInput Input;
			MotorModel::Request(State, EMotorRequest::Hop, Motor());
			Run(State, Input, 0.65f, Delta);
			MotorModel::Request(State, EMotorRequest::Hop, Motor());
			const FVector2D Buffered = Run(State, Input, 0.4f, Delta);
			TestEqual(TEXT("buffered hop fires"), static_cast<float>(Buffered.X), 80.0f, 0.01f);
		}
		// Left input hops left.
		{
			FMotorModelState State;
			FMotorInput Input;
			Input.MoveAxis = -1.0f;
			MotorModel::Request(State, EMotorRequest::Hop, Motor());
			const FVector2D Total = Run(State, Input, 0.5f, Delta);
			TestEqual(TEXT("hop left"), static_cast<float>(Total.X), -80.0f, 0.01f);
		}
		// Dash while falling: 85 units over 0.16 s, no protection.
		{
			FMotorModelState State;
			FMotorInput Input;
			Input.Action = EUmbrellaAction::ShootFall;
			MotorModel::Request(State, EMotorRequest::DashForward, Motor());
			MotorModel::Step(State, Input, Motor(), Delta);
			TestEqual(TEXT("dash speed"), static_cast<float>(State.Velocity.X), 170.0f / 0.16f, 0.01f);
			TestFalse(TEXT("dash does not protect"), MotorModel::IsProtected(State));
			FMotorModelState Back;
			MotorModel::Request(Back, EMotorRequest::DashBack, Motor());
			const FVector2D BackTotal = Run(Back, Input, 0.5f, Delta);
			TestEqual(TEXT("dash back distance"), static_cast<float>(BackTotal.X), -170.0f, 0.01f);
		}
		// Free-fall dash is half distance.
		{
			FMotorModelState State;
			FMotorInput Input;
			Input.Action = EUmbrellaAction::FreeFall;
			MotorModel::Request(State, EMotorRequest::DashForward, Motor());
			const FVector2D Total = Run(State, Input, 0.5f, Delta);
			TestEqual(TEXT("free-fall dash half"), static_cast<float>(Total.X), 85.0f, 0.01f);
		}
		// Dash cooldown 0.3 s.
		{
			FMotorModelState State;
			FMotorInput Input;
			Input.Action = EUmbrellaAction::AbsorbFall;
			MotorModel::Request(State, EMotorRequest::DashForward, Motor());
			Run(State, Input, 0.2f, Delta);
			MotorModel::Request(State, EMotorRequest::DashForward, Motor());
			const FVector2D Blocked = Run(State, Input, 0.06f, Delta);
			TestEqual(TEXT("no dash inside cooldown"), static_cast<float>(Blocked.X), 0.0f, 0.01f);
		}
		// Hop button while falling is a context dash: left = back, none = forward.
		{
			FMotorModelState State;
			FMotorInput Input;
			Input.Action = EUmbrellaAction::ShootFall;
			Input.MoveAxis = -1.0f;
			MotorModel::Request(State, EMotorRequest::Hop, Motor());
			const FVector2D Left = Run(State, Input, 0.5f, Delta);
			TestEqual(TEXT("context dash left"), static_cast<float>(Left.X), -170.0f, 0.01f);
			FMotorModelState Fresh;
			Input.MoveAxis = 0.0f;
			MotorModel::Request(Fresh, EMotorRequest::Hop, Motor());
			const FVector2D Right = Run(Fresh, Input, 0.5f, Delta);
			TestEqual(TEXT("context dash forward"), static_cast<float>(Right.X), 170.0f, 0.01f);
		}
		// Dash needs a fall; hop needs overhead.
		{
			FMotorModelState State;
			FMotorInput Input;
			MotorModel::Request(State, EMotorRequest::DashForward, Motor());
			const FVector2D Overhead = Run(State, Input, 0.5f, Delta);
			TestEqual(TEXT("no dash overhead"), static_cast<float>(Overhead.X), 0.0f, 0.01f);
		}
	}
	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FMoveWindTest, "UmbrellaElla.Move.WindRideAndDecay", EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FMoveWindTest::RunTest(const FString& Parameters)
{
	for (const float Delta : TestDeltas)
	{
		FMotorModelState State;
		FMotorInput Input;
		Input.bRideHeld = true;
		Input.bInCurrent = true;
		Input.CurrentVelocity = FVector2D(200.0f, 0.0f);
		Run(State, Input, 3.0f, Delta);
		TestTrue(TEXT("riding"), State.bRiding);
		TestEqual(TEXT("reaches the current"), static_cast<float>(State.Wind.X), 200.0f, 1.0f);
		TestEqual(TEXT("velocity carries it"), static_cast<float>(State.Velocity.X), 200.0f, 1.0f);

		// Exponential approach: after one second about 1 - e^-3 of the way (3/s acceleration).
		FMotorModelState Fresh;
		Run(Fresh, Input, 1.0f, Delta);
		TestEqual(TEXT("acceleration 3/s"), static_cast<float>(Fresh.Wind.X), 200.0f * (1.0f - FMath::Exp(-3.0f)), 1.0f);

		// Release ride overhead: decays at 1.5/s (slow).
		FMotorModelState Open = State;
		Input.bRideHeld = false;
		Run(Open, Input, 1.0f, Delta);
		TestEqual(TEXT("open decay 1.5/s"), static_cast<float>(Open.Wind.X), 200.0f * FMath::Exp(-1.5f), 1.0f);
		TestFalse(TEXT("no longer riding"), Open.bRiding);

		// Entering a fall disengages and decays at 12/s (fast).
		FMotorModelState Falling = State;
		Input.bRideHeld = true;
		Input.Action = EUmbrellaAction::ShootFall;
		Run(Falling, Input, 0.5f, Delta);
		TestFalse(TEXT("falling disengages ride"), Falling.bRiding);
		TestTrue(TEXT("falling decays fast"), FMath::Abs(Falling.Wind.X) < 1.0f);

		// A 360 current is carried whole (GDD wind 360); only faster ones are capped, at the wind maximum.
		FMotorModelState Fast;
		Input.Action = EUmbrellaAction::Rise;
		Input.CurrentVelocity = FVector2D(360.0f, 0.0f);
		Run(Fast, Input, 5.0f, Delta);
		TestEqual(TEXT("wind 360 is not cut"), static_cast<float>(Fast.Wind.X), 360.0f, 0.5f);
		Input.CurrentVelocity = FVector2D(1800.0f, 0.0f);
		Run(Fast, Input, 5.0f, Delta);
		TestEqual(TEXT("capped at the wind maximum"), static_cast<float>(Fast.Wind.X), Motor().WindMaxSpeed, 0.01f);

		// Outside a current, holding Ride does nothing.
		FMotorModelState Outside;
		Input.bInCurrent = false;
		Run(Outside, Input, 1.0f, Delta);
		TestEqual(TEXT("no current, no ride"), static_cast<float>(Outside.Wind.X), 0.0f, 0.001f);
	}
	TestEqual(TEXT("Right"), MotorModel::ParseCurrentDirection(FName(TEXT("Right"))), FVector2D(1.0, 0.0));
	TestEqual(TEXT("left"), MotorModel::ParseCurrentDirection(FName(TEXT("left"))), FVector2D(-1.0, 0.0));
	TestEqual(TEXT("Up"), MotorModel::ParseCurrentDirection(FName(TEXT("Up"))), FVector2D(0.0, 1.0));
	TestEqual(TEXT("Down"), MotorModel::ParseCurrentDirection(FName(TEXT("Down"))), FVector2D(0.0, -1.0));
	TestEqual(TEXT("junk"), MotorModel::ParseCurrentDirection(FName(TEXT("sideways"))), FVector2D::ZeroVector);
	TestEqual(TEXT("x,z"), MotorModel::ParseCurrentDirection(FName(TEXT("0,-3"))), FVector2D(0.0, -1.0));
	TestEqual(TEXT("direction with local field"), MotorModel::ParseCurrentDirection(FName(TEXT("Right@2.4,230,-78"))), FVector2D(1.0, 0.0));
	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FMoveLocalFieldTest, "UmbrellaElla.Move.WindLocalVerticalField", EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FMoveLocalFieldTest::RunTest(const FString& Parameters)
{
	float Gain = 0.0f;
	float Centre = 0.0f;
	float Comp = 0.0f;
	TestFalse(TEXT("plain label has no field"), MotorModel::HasLocalField(FName(TEXT("Right")), Gain, Centre, Comp));
	if (!TestTrue(TEXT("field parses"), MotorModel::HasLocalField(FName(TEXT("Right@2.4,230,-78")), Gain, Centre, Comp)))
	{
		return false;
	}
	TestEqual(TEXT("gain"), Gain, 2.4f);
	TestEqual(TEXT("centre z"), Centre, 230.0f);
	TestEqual(TEXT("compensation"), Comp, -78.0f);
	// Vz term: Gain * (CentreZ - RootZ) + Compensation.
	TestEqual(TEXT("term at root 257.5 balances full lift with up trim (GDD +27.5)"), Motor().WindScale * MotorModel::LocalVerticalTerm(Gain, Centre, Comp, 257.5f) + Motor().RiseSpeed * (1.0f + Motor().VerticalTrimPct / 100.0f), 0.0f, 0.01f);
	TestEqual(TEXT("term at centre"), MotorModel::LocalVerticalTerm(Gain, Centre, Comp, 230.0f), -78.0f, 0.001f);
	for (const float Delta : TestDeltas)
	{
		FMotorModelState State;
		FMotorInput Input;
		Input.bRideHeld = true;
		Input.bInCurrent = true;
		Input.CurrentVelocity = FVector2D(360.0f, 0.0f);
		Input.LocalVerticalVelocity = -50.0f;
		const FVector2D Moved = Run(State, Input, 1.0f, Delta);
		TestEqual(TEXT("riding adds the term to Vz"), static_cast<float>(State.Velocity.Y), Motor().RiseSpeed - 50.0f, 0.01f);
		TestTrue(TEXT("displacement follows"), Moved.Y < Motor().RiseSpeed);
		FMotorModelState NotRiding;
		Input.bRideHeld = false;
		Run(NotRiding, Input, 0.5f, Delta);
		TestEqual(TEXT("not riding: no term"), static_cast<float>(NotRiding.Velocity.Y), Motor().RiseSpeed, 0.01f);
	}
	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FMoveSteeringOffTest, "UmbrellaElla.Move.NoDirectSteering", EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FMoveSteeringOffTest::RunTest(const FString& Parameters)
{
	for (const float Delta : TestDeltas)
	{
		for (uint8 Index = 0; Index <= static_cast<uint8>(EUmbrellaAction::FreeFall); ++Index)
		{
			FMotorModelState State;
			FMotorInput Input;
			Input.Action = static_cast<EUmbrellaAction>(Index);
			Input.MoveAxis = 1.0f;
			const FVector2D Total = Run(State, Input, 1.0f, Delta);
			TestEqual(TEXT("horizontal input never moves Ella sideways"), static_cast<float>(Total.X), 0.0f, 0.001f);
		}
	}
	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FMoveCadenceTest, "UmbrellaElla.Move.SmallBlastCadence", EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FMoveCadenceTest::RunTest(const FString& Parameters)
{
	for (const float Delta : TestDeltas)
	{
		float Countdown = 0.0f;
		int32 Shots = 0;
		const int32 Frames = FMath::RoundToInt(2.0f / Delta);
		for (int32 Frame = 0; Frame < Frames; ++Frame)
		{
			Shots += AttackCadence::Step(Countdown, Delta, 5.0f, true);
		}
		// 5 shots/s over 2 s: 10, plus the immediate first shot.
		TestTrue(FString::Printf(TEXT("5 shots/s at delta %f gave %d"), Delta, Shots), Shots >= 10 && Shots <= 11);

		int32 Idle = 0;
		for (int32 Frame = 0; Frame < Frames; ++Frame)
		{
			Idle += AttackCadence::Step(Countdown, Delta, 5.0f, false);
		}
		TestEqual(TEXT("no shots when not firing"), Idle, 0);
	}
	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FMoveCadenceGapsTest, "UmbrellaElla.Move.SmallBlastCadenceGaps", EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FMoveCadenceGapsTest::RunTest(const FString& Parameters)
{
	// D-new-smallblast-fixture: every gap is one interval (0.200 s at 5 shots/s), the first included.
	const float Delta = 1.0f / 60.0f;
	float Countdown = 0.0f;
	TArray<int32> ShotFrames;
	for (int32 Frame = 0; Frame < 60; ++Frame)
	{
		if (AttackCadence::Step(Countdown, Delta, 5.0f, true) > 0)
		{
			ShotFrames.Add(Frame);
		}
	}
	TestTrue(TEXT("at least 4 shots in a second"), ShotFrames.Num() >= 4);
	for (int32 Index = 1; Index < ShotFrames.Num(); ++Index)
	{
		TestEqual(*FString::Printf(TEXT("gap %d in frames"), Index), ShotFrames[Index] - ShotFrames[Index - 1], 12);
	}
	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FMoveBindingsTest, "UmbrellaElla.Move.DefaultBindings", EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FMoveBindingsTest::RunTest(const FString& Parameters)
{
	const TArray<FUmbrellaDefaultBinding> Bindings = UmbrellaInputBindings::BuildDefaults();
	auto Has = [&Bindings](EUmbrellaInputAction Action, const FKey& Key, float Scale)
	{
		for (const FUmbrellaDefaultBinding& Binding : Bindings)
		{
			if (Binding.Action == Action && Binding.Key == Key && FMath::IsNearlyEqual(Binding.Scale, Scale))
			{
				return true;
			}
		}
		return false;
	};
	TestTrue(TEXT("J shoots"), Has(EUmbrellaInputAction::Shoot, EKeys::J, 1.0f));
	TestTrue(TEXT("left mouse shoots"), Has(EUmbrellaInputAction::Shoot, EKeys::LeftMouseButton, 1.0f));
	TestTrue(TEXT("RT shoots"), Has(EUmbrellaInputAction::Shoot, EKeys::Gamepad_RightTrigger, 1.0f));
	TestTrue(TEXT("K absorbs"), Has(EUmbrellaInputAction::Absorb, EKeys::K, 1.0f));
	TestTrue(TEXT("right mouse absorbs"), Has(EUmbrellaInputAction::Absorb, EKeys::RightMouseButton, 1.0f));
	TestTrue(TEXT("LT absorbs"), Has(EUmbrellaInputAction::Absorb, EKeys::Gamepad_LeftTrigger, 1.0f));
	TestTrue(TEXT("Space hops"), Has(EUmbrellaInputAction::Hop, EKeys::SpaceBar, 1.0f));
	TestTrue(TEXT("A hops"), Has(EUmbrellaInputAction::Hop, EKeys::Gamepad_FaceButton_Bottom, 1.0f));
	TestTrue(TEXT("Q dashes back"), Has(EUmbrellaInputAction::DashBack, EKeys::Q, 1.0f));
	TestTrue(TEXT("LB dashes back"), Has(EUmbrellaInputAction::DashBack, EKeys::Gamepad_LeftShoulder, 1.0f));
	TestTrue(TEXT("E dashes forward"), Has(EUmbrellaInputAction::DashForward, EKeys::E, 1.0f));
	TestTrue(TEXT("RB dashes forward"), Has(EUmbrellaInputAction::DashForward, EKeys::Gamepad_RightShoulder, 1.0f));
	TestTrue(TEXT("Shift rides"), Has(EUmbrellaInputAction::Ride, EKeys::LeftShift, 1.0f));
	TestTrue(TEXT("Y rides"), Has(EUmbrellaInputAction::Ride, EKeys::Gamepad_FaceButton_Top, 1.0f));
	TestTrue(TEXT("W trims up"), Has(EUmbrellaInputAction::Trim, EKeys::W, 1.0f));
	TestTrue(TEXT("S trims down"), Has(EUmbrellaInputAction::Trim, EKeys::S, -1.0f));
	TestTrue(TEXT("stick trims"), Has(EUmbrellaInputAction::Trim, EKeys::Gamepad_LeftY, 1.0f));
	TestTrue(TEXT("1 selects Small"), Has(EUmbrellaInputAction::Spell1, EKeys::One, 1.0f));
	TestTrue(TEXT("4 selects Needle"), Has(EUmbrellaInputAction::Spell4, EKeys::Four, 1.0f));
	TestTrue(TEXT("] cycles on"), Has(EUmbrellaInputAction::SpellNext, EKeys::RightBracket, 1.0f));

	// Nothing steers or aims: no mouse axis, no right-stick axis, no horizontal move on the shoot/absorb keys.
	for (const FUmbrellaDefaultBinding& Binding : Bindings)
	{
		TestFalse(TEXT("no mouse aim"), Binding.Key == EKeys::MouseX || Binding.Key == EKeys::MouseY || Binding.Key == EKeys::Mouse2D);
		TestFalse(TEXT("no right-stick aim axis"), Binding.Key == EKeys::Gamepad_RightX || Binding.Key == EKeys::Gamepad_RightY);
	}
	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FMoveStateLockTest, "UmbrellaElla.Move.StateLockWaitsForNeutral", EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FMoveStateLockTest::RunTest(const FString& Parameters)
{
	UUmbrellaStateComponent* State = NewObject<UUmbrellaStateComponent>(GetTransientPackage());
	TestEqual(TEXT("starts overhead"), State->GetAction(), EUmbrellaAction::Rise);
	State->SetShootHeld(true);
	TestEqual(TEXT("shoot-fall"), State->GetAction(), EUmbrellaAction::ShootFall);
	State->SetAbsorbHeld(true);
	TestEqual(TEXT("free fall"), State->GetAction(), EUmbrellaAction::FreeFall);
	State->SetShootHeld(false);
	TestEqual(TEXT("absorb-fall"), State->GetAction(), EUmbrellaAction::AbsorbFall);
	State->SetAbsorbHeld(false);
	TestEqual(TEXT("rise"), State->GetAction(), EUmbrellaAction::Rise);

	// A lock beats the holds; after it ends a held button does not count until it is released once.
	State->SetShootHeld(true);
	State->SetLocked(true);
	TestEqual(TEXT("locked = rise"), State->GetAction(), EUmbrellaAction::Rise);
	State->SetLocked(false);
	TestEqual(TEXT("held through the lock does not fire"), State->GetAction(), EUmbrellaAction::Rise);
	State->SetShootHeld(false);
	State->SetShootHeld(true);
	TestEqual(TEXT("fresh press counts"), State->GetAction(), EUmbrellaAction::ShootFall);
	return true;
}

#endif
