#include "Engine/Engine.h"
#include "Components/CapsuleComponent.h"
#include "Core/UmbrellaEvent.h"
#include "BrokenMill/BrokenMillRoom.h"
#include "BrokenMill/BrokenMillRules.h"
#include "BrokenMill/BrokenMillTuning.h"
#include "Core/EllaCharacter.h"
#include "Core/UmbrellaEventBus.h"
#include "Core/UmbrellaTuning.h"
#include "Field/WindCurrent.h"
#include "Input/EllaInputAdapterComponent.h"
#include "Motor/EllaMotorComponent.h"
#include "Tests/Shared/UmbrellaTestWorld.h"
#include "Umbrella/UmbrellaPlayerIds.h"
#include "Umbrella/UmbrellaStateComponent.h"
#include "Engine/StaticMeshActor.h"
#include "Engine/World.h"
#include "EngineUtils.h"
#include "Misc/AutomationTest.h"
#include "Projectile/UmbrellaProjectile.h"
#include "Trap/UmbrellaTrap.h"
#include "Tests/BrokenMill/BrokenMillTestFixture.h"

#if WITH_AUTOMATION_TESTS


namespace
{
	FMillGuardInputs ValidInputs()
	{
		FMillGuardInputs Inputs;
		Inputs.Ella = FVector(600.0, 0.0, 650.0);
		Inputs.bInActivationRegion = true;
		Inputs.bEngagementValid = true;
		Inputs.bShotGone = true;
		return Inputs;
	}

	/** Walk a guard through warning and release; returns the guard after the shot. */
	FMillGuard FireOnce(const FBrokenMillTuning& Tuning)
	{
		FMillGuard Guard;
		const FMillGuardInputs Inputs = ValidInputs();
		Guard.Advance(Tuning, 0.0f, Inputs);
		Guard.Advance(Tuning, Tuning.WarningSeconds, Inputs);
		return Guard;
	}

}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FMillGeometryEstimates, "UmbrellaElla.BrokenMill.GeometryEstimatesMatchGdd", UMBRELLAELLA_MILL_FLAGS)
bool FMillGeometryEstimates::RunTest(const FString& Parameters)
{
	const FBrokenMillTuning T;
	TestEqual(TEXT("underside clearance at root 285"), FBrokenMillRules::GetUndersideClearance(T, 285.0f), 26.0f);
	TestEqual(TEXT("floor clearance at root 185"), FBrokenMillRules::GetFloorClearance(T, 185.0f), 66.0f);
	TestEqual(TEXT("rotor clearance over the highest useful shot"), FBrokenMillRules::GetRotorClearanceAboveShots(T, 526.0f), 78.0f);
	TestTrue(TEXT("return margin about 30"), FMath::IsNearlyEqual(FBrokenMillRules::GetReturnMargin(T), 30.2f, 0.01f));
	TestEqual(TEXT("shot lifetime at most 4.167 s"), FMath::RoundToInt(FBrokenMillRules::GetGuardShotLifetime(T) * 1000.0f), 4167);
	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FMillFiringWindows, "UmbrellaElla.BrokenMill.FiringWindowsMatchGdd", UMBRELLAELLA_MILL_FLAGS)
bool FMillFiringWindows::RunTest(const FString& Parameters)
{
	const FBrokenMillTuning T;
	const FVector2D Window = FBrokenMillRules::GetFiringWindowRoot(T);
	TestEqual(TEXT("exposed band low"), static_cast<float>(Window.X), 402.0f);
	TestEqual(TEXT("exposed band high"), static_cast<float>(Window.Y), 520.0f);
	const FVector2D Comparison = FBrokenMillRules::GetComparisonWindowRoot(T, 80.0f);
	TestEqual(TEXT("80-high comparison width 92"), static_cast<float>(Comparison.Y - Comparison.X), 92.0f);
	const FVector2D Proxy = FBrokenMillRules::GetComparisonWindowRoot(T, T.TargetSize.Y);
	TestEqual(TEXT("130-high proxy low 378"), static_cast<float>(Proxy.X), 378.0f);
	TestEqual(TEXT("130-high proxy width 142"), static_cast<float>(Proxy.Y - Proxy.X), 142.0f);
	const float Fall = T.FallSpeed;
	const float Trim = T.FallTrimFraction;
	TestEqual(TEXT("118 wide at fall 264, ms"), FMath::RoundToInt(FBrokenMillRules::GetWindowSeconds(Window, Fall * (1.0f - Trim)) * 1000.0f), 447);
	TestEqual(TEXT("118 wide at fall 330, ms"), FMath::RoundToInt(FBrokenMillRules::GetWindowSeconds(Window, Fall) * 1000.0f), 358);
	TestEqual(TEXT("118 wide at fall 396, ms"), FMath::RoundToInt(FBrokenMillRules::GetWindowSeconds(Window, Fall * (1.0f + Trim)) * 1000.0f), 298);
	TestEqual(TEXT("92 wide at fall 330, ms"), FMath::RoundToInt(FBrokenMillRules::GetWindowSeconds(Comparison, Fall) * 1000.0f), 279);
	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FMillEmissionAndImpact, "UmbrellaElla.BrokenMill.EmissionCountsAndDelayedImpact", UMBRELLAELLA_MILL_FLAGS)
bool FMillEmissionAndImpact::RunTest(const FString& Parameters)
{
	const FBrokenMillTuning T;
	const float Period = 1.0f / T.FriendlyShotsPerSecond;
	const FIntPoint Wide = FBrokenMillRules::GetEmissionCountRange(0.447f, Period);
	TestEqual(TEXT("0.447 s holds 2 to 3"), Wide, FIntPoint(2, 3));
	const FIntPoint Mid = FBrokenMillRules::GetEmissionCountRange(0.358f, Period);
	TestEqual(TEXT("0.358 s holds 1 to 2: not guaranteed two"), Mid, FIntPoint(1, 2));
	const FIntPoint Narrow = FBrokenMillRules::GetEmissionCountRange(0.298f, Period);
	TestEqual(TEXT("0.298 s holds 1 to 2"), Narrow, FIntPoint(1, 2));
	TestEqual(TEXT("first contact at root 650, ms"), FMath::RoundToInt(FBrokenMillRules::GetFirstContactSeconds(T, 650.0f, 1.0f) * 1000.0f), 1014);
	const FVector2D Big = FBrokenMillRules::GetMuzzleOffset(T, 1.3f);
	TestTrue(TEXT("HeroSize 1.3 muzzle 57.2 / 7.8"), FMath::IsNearlyEqual(static_cast<float>(Big.X), 57.2f, 0.01f) && FMath::IsNearlyEqual(static_cast<float>(Big.Y), 7.8f, 0.01f));
	TestFalse(TEXT("shadow tests never write progression"), FBrokenMillRules::IsProgressionWriteAllowed());
	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FMillActivationAndRays, "UmbrellaElla.BrokenMill.ActivationAndEngagement", UMBRELLAELLA_MILL_FLAGS)
bool FMillActivationAndRays::RunTest(const FString& Parameters)
{
	const FBrokenMillTuning T;
	TestTrue(TEXT("inside the activation region"), FBrokenMillRules::IsInActivationRegion(T, FVector(600.0, 0.0, 650.0)));
	TestFalse(TEXT("left of the region"), FBrokenMillRules::IsInActivationRegion(T, FVector(400.0, 0.0, 650.0)));
	TestFalse(TEXT("below the region"), FBrokenMillRules::IsInActivationRegion(T, FVector(600.0, 0.0, 500.0)));
	TestTrue(TEXT("ray low under the rotor is clear"), FBrokenMillRules::IsEngagementValid(T, FVector2D(650.0, 420.0), true));
	TestFalse(TEXT("ray through the rotor is blocked"), FBrokenMillRules::IsEngagementValid(T, FVector2D(800.0, 760.0), true));
	TestFalse(TEXT("ray into the island is blocked"), FBrokenMillRules::IsEngagementValid(T, FVector2D(1380.0, 300.0), true));
	TestFalse(TEXT("no engagement without a reachable descent"), FBrokenMillRules::IsEngagementValid(T, FVector2D(650.0, 420.0), false));
	TestFalse(TEXT("Ella to the right of the muzzle is behind"), FBrokenMillRules::IsEngagementValid(T, FVector2D(1500.0, 420.0), true));
	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FMillWinds, "UmbrellaElla.BrokenMill.TwoWindsNeverSteal", UMBRELLAELLA_MILL_FLAGS)
bool FMillWinds::RunTest(const FString& Parameters)
{
	const FBrokenMillTuning T;
	TestEqual(TEXT("upper centre"), FBrokenMillRules::SelectWind(T, 420.0f), EMillWind::UpperReset);
	TestEqual(TEXT("lower centre"), FBrokenMillRules::SelectWind(T, 270.0f), EMillWind::LowerOnward);
	TestEqual(TEXT("gap between them"), FBrokenMillRules::SelectWind(T, 345.0f), EMillWind::None);
	bool bOverlap = false;
	for (int32 Z = 0; Z <= 1080; ++Z)
	{
		const bool bUpper = FBrokenMillRules::SelectWind(T, static_cast<float>(Z)) == EMillWind::UpperReset;
		const bool bLower = Z >= T.LowerOnwardZ.X && Z <= T.LowerOnwardZ.Y;
		bOverlap |= bUpper && bLower;
	}
	TestFalse(TEXT("no height is in both fields"), bOverlap);
	TestTrue(TEXT("missed-current assist near x650 z150"), FBrokenMillRules::IsInMissedCurrentAssist(T, FVector2D(650.0, 150.0)));
	TestFalse(TEXT("no assist up high"), FBrokenMillRules::IsInMissedCurrentAssist(T, FVector2D(650.0, 600.0)));
	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FMillEligibleWind, "UmbrellaElla.BrokenMill.EligibleWindByRoot", UMBRELLAELLA_MILL_FLAGS)
bool FMillEligibleWind::RunTest(const FString& Parameters)
{
	const FBrokenMillTuning T;
	TestEqual(TEXT("early reopen z 420 in the column: reset"), FBrokenMillRules::GetEligibleWind(T, FVector2D(700.0, 420.0)), EMillWind::UpperReset);
	TestEqual(TEXT("late reopen z 270 in the column: onward"), FBrokenMillRules::GetEligibleWind(T, FVector2D(700.0, 270.0)), EMillWind::LowerOnward);
	TestEqual(TEXT("gap z 345: neither"), FBrokenMillRules::GetEligibleWind(T, FVector2D(700.0, 345.0)), EMillWind::None);
	TestEqual(TEXT("left of the column: neither"), FBrokenMillRules::GetEligibleWind(T, FVector2D(590.0, 420.0)), EMillWind::None);
	TestEqual(TEXT("right of the column: neither"), FBrokenMillRules::GetEligibleWind(T, FVector2D(810.0, 270.0)), EMillWind::None);
	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FMillGuardOneShot, "UmbrellaElla.BrokenMill.GuardOneShotPerPass", UMBRELLAELLA_MILL_FLAGS)
bool FMillGuardOneShot::RunTest(const FString& Parameters)
{
	const FBrokenMillTuning T;
	FMillGuard Guard;
	FMillGuardInputs Inputs = ValidInputs();
	TestEqual(TEXT("warning starts"), Guard.Advance(T, 0.0f, Inputs), EMillGuardEvent::WarningStarted);
	TestEqual(TEXT("no shot before 1.1 s"), Guard.Advance(T, 1.0f, Inputs), EMillGuardEvent::None);
	TestEqual(TEXT("shot at 1.1 s"), Guard.Advance(T, 0.1f, Inputs), EMillGuardEvent::ShotReleased);
	TestTrue(TEXT("a shot is live"), Guard.bShotLive);
	Inputs.bShotGone = false;
	// Staying in the region never rearms: no second warning during recovery or while the shot lives.
	for (int32 Step = 0; Step < 100; ++Step)
	{
		TestNotEqual(TEXT("no new warning"), Guard.Advance(T, 0.1f, Inputs), EMillGuardEvent::WarningStarted);
	}
	Inputs.bShotGone = true;
	TestNotEqual(TEXT("shot gone but still in the region: no warning"), Guard.Advance(T, 0.1f, Inputs), EMillGuardEvent::WarningStarted);
	Inputs.bInActivationRegion = false;
	Guard.Advance(T, 0.1f, Inputs);
	Inputs.bInActivationRegion = true;
	TestEqual(TEXT("fresh exit and re-entry rearms"), Guard.Advance(T, 0.1f, Inputs), EMillGuardEvent::WarningStarted);
	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FMillGuardCancels, "UmbrellaElla.BrokenMill.GuardCancelAbortPausePassBehind", UMBRELLAELLA_MILL_FLAGS)
bool FMillGuardCancels::RunTest(const FString& Parameters)
{
	const FBrokenMillTuning T;
	FMillGuardInputs Inputs = ValidInputs();

	FMillGuard Paused;
	Paused.Advance(T, 0.0f, Inputs);
	FMillGuardInputs PausedInputs = Inputs;
	PausedInputs.bPaused = true;
	TestEqual(TEXT("pause freezes the warning clock"), Paused.Advance(T, 5.0f, PausedInputs), EMillGuardEvent::None);
	TestEqual(TEXT("clock did not move"), Paused.Timer, 0.0f);

	FMillGuard Behind;
	Behind.Advance(T, 0.0f, Inputs);
	FMillGuardInputs BehindInputs = Inputs;
	BehindInputs.bPassedBehind = true;
	TestEqual(TEXT("passing behind cancels"), Behind.Advance(T, 0.2f, BehindInputs), EMillGuardEvent::WarningCancelled);

	FMillGuard Disabled;
	Disabled.Advance(T, 0.0f, Inputs);
	Disabled.SetGuardEnabled(false);
	TestEqual(TEXT("disabling cancels the pending fire"), Disabled.Advance(T, 2.0f, Inputs), EMillGuardEvent::WarningCancelled);
	TestFalse(TEXT("nothing launched"), Disabled.bShotLive);

	FMillGuard Aborted;
	Aborted.Advance(T, 0.0f, Inputs);
	FMillGuardInputs LostInputs = Inputs;
	LostInputs.bEngagementValid = false;
	TestEqual(TEXT("invalid at release aborts, no shot"), Aborted.Advance(T, T.WarningSeconds, LostInputs), EMillGuardEvent::WarningAborted);
	TestFalse(TEXT("no shot launched on abort"), Aborted.bShotLive);
	TestEqual(TEXT("quiet recovery follows"), Aborted.State, EMillGuardState::Recovery);

	FMillGuard NoWarn;
	FMillGuardInputs NoWarnInputs = Inputs;
	NoWarnInputs.bInNoWarningPhase = true;
	TestNotEqual(TEXT("no warning in reset or exit"), NoWarn.Advance(T, 0.0f, NoWarnInputs), EMillGuardEvent::WarningStarted);

	FMillGuard Launched = FireOnce(T);
	Launched.SetGuardEnabled(false);
	TestTrue(TEXT("a launched shot survives disabling"), Launched.bShotLive);
	Launched.Reset();
	TestFalse(TEXT("retry clears the live shot"), Launched.bShotLive);
	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FMillLogAndPool, "UmbrellaElla.BrokenMill.ShotLogAndPoolGate", UMBRELLAELLA_MILL_FLAGS)
bool FMillLogAndPool::RunTest(const FString& Parameters)
{
	FMillShotLog Log;
	Log.RecordEmission(1, 2.5f, FVector(1410.0, 25.0, 480.0));
	Log.RecordFirstContact(1, FName(TEXT("Terrain")), 6.0f);
	Log.RecordFirstContact(1, FName(TEXT("Target")), 7.0f);
	TestEqual(TEXT("one entry"), Log.Entries.Num(), 1);
	TestEqual(TEXT("first contact kept"), Log.Entries[0].FirstContact, FName(TEXT("Terrain")));
	TestEqual(TEXT("impact time kept"), Log.Entries[0].ImpactTime, 6.0f);

	const FBrokenMillTuning T;
	FMillPoolState Clean;
	TestEqual(TEXT("clean candidate passes"), FBrokenMillRules::GetPoolGateFailures(T, Clean).Num(), 0);
	FMillPoolState Dirty;
	Dirty.bLiveShot = true;
	Dirty.bMirrored = true;
	Dirty.ActiveEnemyBullets = 2;
	TestEqual(TEXT("live shot, mirror and two bullets fail"), FBrokenMillRules::GetPoolGateFailures(T, Dirty).Num(), 3);
	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FMillRoomWorld, "UmbrellaElla.BrokenMill.World.RoomFiresOneShotAndDies", UMBRELLAELLA_MILL_FLAGS)
bool FMillRoomWorld::RunTest(const FString& Parameters)
{
	UWorld* World = UWorld::CreateWorld(EWorldType::Game, false);
	FWorldContext& Context = GEngine->CreateNewWorldContext(EWorldType::Game);
	Context.SetCurrentWorld(World);
	ABrokenMillRoom* Room = World->SpawnActor<ABrokenMillRoom>(ABrokenMillRoom::StaticClass(), FTransform(FVector(10000.0, 0.0, 0.0)));
	Room->BuildRoom();
	TestNotNull(TEXT("rotor trap spawned"), Room->GetRotor());
	AStaticMeshActor* Ella = World->SpawnActor<AStaticMeshActor>(AStaticMeshActor::StaticClass(), FTransform(Room->RoomToWorld(FVector2D(600.0, 650.0))));
	Room->SetTargetActor(Ella);
	TestEqual(TEXT("warning starts"), Room->StepSeconds(0.1f), EMillGuardEvent::WarningStarted);
	TestEqual(TEXT("shot after the warning"), Room->StepSeconds(Room->GetMillTuning().WarningSeconds), EMillGuardEvent::ShotReleased);
	int32 Shots = 0;
	for (TActorIterator<AUmbrellaProjectile> It(World); It; ++It)
	{
		++Shots;
		TestEqual(TEXT("red"), It->GetSpec().Kind, EUmbrellaShotKind::EnemyRed);
		TestEqual(TEXT("speed 240"), static_cast<float>(It->GetSpec().Velocity.Size()), 240.0f);
		TestEqual(TEXT("one health"), It->GetSpec().Damage, 1.0f);
		TestTrue(TEXT("flies left"), It->GetSpec().Velocity.X < 0.0);
	}
	TestEqual(TEXT("exactly one enemy bullet"), Shots, 1);
	TestEqual(TEXT("one logged emission"), Room->GetShotLog().Entries.Num(), 1);

	FUmbrellaShotSpec Blast;
	Blast.Kind = EUmbrellaShotKind::PlayerBlast;
	Blast.Damage = 10.0f;
	TestEqual(TEXT("one blast kills the 10 HP guard"), Room->ReceiveShot(Blast, FVector::ZeroVector), EUmbrellaShotResult::Consumed);
	TestEqual(TEXT("hp zero"), Room->GetGuardHp(), 0.0f);
	TestFalse(TEXT("guard disabled"), Room->GetGuard().bEnabled);
	TestEqual(TEXT("dead guard ignores shots"), Room->ReceiveShot(Blast, FVector::ZeroVector), EUmbrellaShotResult::Ignored);
	Room->ResetForRestart();
	TestEqual(TEXT("retry restores hp"), Room->GetGuardHp(), Room->GetMillTuning().GuardHp);
	TestTrue(TEXT("retry re-enables the guard"), Room->GetGuard().bEnabled);
	GEngine->DestroyWorldContext(World);
	World->DestroyWorld(false);
	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FMillWorldCancelAbortPause, "UmbrellaElla.BrokenMill.World.GuardChecksWithRealElla", UMBRELLAELLA_MILL_FLAGS)
bool FMillWorldCancelAbortPause::RunTest(const FString& Parameters)
{
	const float Dt = 1.0f / 60.0f;
	{
		// Pause: the warning clock stands still, then resumes and the single shot comes.
		BrokenMillTest::FMillIntegratedFixture F;
		if (!TestNotNull(TEXT("fixture"), F.Spawn(FVector2D(600.0, 650.0))))
		{
			return false;
		}
		F.TickPinnedZ(0.1f, Dt);
		TestEqual(TEXT("warning started"), F.Room->GetEventCount(EMillGuardEvent::WarningStarted), 1);
		F.Room->SetSimulationPaused(true);
		const float TimerBefore = F.Room->GetGuard().Timer;
		F.TickPinnedZ(3.0f, Dt);
		TestEqual(TEXT("pause froze the warning clock"), F.Room->GetGuard().Timer, TimerBefore);
		TestEqual(TEXT("no shot while paused"), F.Room->GetEventCount(EMillGuardEvent::ShotReleased), 0);
		F.Room->SetSimulationPaused(false);
		F.TickPinnedZ(1.2f, Dt);
		TestEqual(TEXT("one shot after resume"), F.Room->GetEventCount(EMillGuardEvent::ShotReleased), 1);
		TestEqual(TEXT("one live enemy bullet"), F.CountShots(), 1);
	}
	{
		// Cancel: Ella passes behind the guard during the warning. POSITION-DRIVEN: this proves the room reacts to Ella's
		// X crossing the muzzle, not that the Motor can carry her there (dashes reach ~85 units per 0.3 s, so no dash chain
		// covers the ~700 units from the activation region to the muzzle inside the 1.1 s warning).
		BrokenMillTest::FMillIntegratedFixture F;
		if (!TestNotNull(TEXT("fixture"), F.Spawn(FVector2D(600.0, 650.0))))
		{
			return false;
		}
		F.Test.TickFrames(6, Dt);
		TestEqual(TEXT("warning started"), F.Room->GetEventCount(EMillGuardEvent::WarningStarted), 1);
		F.Ella->SetActorLocation(F.Room->RoomToWorld(FVector2D(F.Room->GetMillTuning().GuardMuzzle.X + 40.0, 650.0)));
		F.Test.TickSeconds(2.0f, Dt);
		TestEqual(TEXT("cancelled"), F.Room->GetEventCount(EMillGuardEvent::WarningCancelled), 1);
		TestEqual(TEXT("no shot released"), F.Room->GetEventCount(EMillGuardEvent::ShotReleased), 0);
		TestEqual(TEXT("no bullet exists"), F.CountShots(), 0);
	}
	{
		// Abort: the real Motor dashes Ella back (RequestDash) out of shot range before the release; quiet recovery, no shot.
		BrokenMillTest::FMillIntegratedFixture F;
		if (!TestNotNull(TEXT("fixture"), F.Spawn(FVector2D(600.0, 650.0))))
		{
			return false;
		}
		F.Test.TickFrames(6, Dt);
		TestEqual(TEXT("warning started"), F.Room->GetEventCount(EMillGuardEvent::WarningStarted), 1);
		const float StartX = F.EllaRoom().X;
		const float DashGap = GetDefault<UUmbrellaTuning>()->Motor.DashCooldownSeconds + 0.02f;
		F.Ella->GetUmbrellaState()->SetAbsorbHeld(true); // a dash needs a falling action; height is pinned below
		for (int32 DashIndex = 0; DashIndex < 3; ++DashIndex)
		{
			F.Ella->GetMotor()->RequestDash(EUmbrellaDashDirection::Back);
			F.TickPinnedZ(DashGap, Dt);
		}
		TestTrue(TEXT("the Motor moved her back"), F.EllaRoom().X < StartX - 200.0f);
		F.Test.TickSeconds(1.5f, Dt);
		TestEqual(TEXT("aborted"), F.Room->GetEventCount(EMillGuardEvent::WarningAborted), 1);
		TestEqual(TEXT("no shot"), F.Room->GetEventCount(EMillGuardEvent::ShotReleased), 0);
		TestEqual(TEXT("no bullet"), F.CountShots(), 0);
	}
	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FMillWorldRealWinds, "UmbrellaElla.BrokenMill.World.RealWindsPickedByReopenHeight", UMBRELLAELLA_MILL_FLAGS)
bool FMillWorldRealWinds::RunTest(const FString& Parameters)
{
	// HAZ-14: early/late reopening selects each wind without theft, through the REAL wind volumes' overlap events.
	const float Dt = 1.0f / 60.0f;
	const float MeasureSeconds = 0.4f;
	const float MinCarry = 20.0f;
	struct FMillReopenCase
	{
		float ReopenZ;
		int32 ExpectedSign;
		const TCHAR* Label;
	};
	const FMillReopenCase Cases[] = {{420.0f, -1, TEXT("early reopen z 420")}, {270.0f, 1, TEXT("late reopen z 270")}, {345.0f, 0, TEXT("gap reopen z 345")}};
	for (const FMillReopenCase& Case : Cases)
	{
		BrokenMillTest::FMillIntegratedFixture F;
		if (!TestNotNull(TEXT("fixture"), F.Spawn(FVector2D(700.0, 600.0), true)) || !TestNotNull(TEXT("reset wind"), F.Room->GetUpperWind()) || !TestNotNull(TEXT("onward wind"), F.Room->GetLowerWind()))
		{
			return false;
		}
		TestEqual(TEXT("Ella answers to the bus id"), F.Ella->GetFName(), UmbrellaPlayerIds::Ella);
		BrokenMillTest::FMillEllaEventLog Log;
		Log.Attach(F.Test.GetWorld(), F.Ella->GetFName());
		const FName Upper = F.Room->GetUpperWind()->GetFName();
		const FName Lower = F.Room->GetLowerWind()->GetFName();
		F.Test.TickFrames(2, Dt);
		UUmbrellaStateComponent* State = F.Ella->GetUmbrellaState();
		State->SetRideHeld(true);
		State->SetAbsorbHeld(true);
		const double StartX = F.EllaRoom().X;
		F.TickUntilRootBelow(Case.ReopenZ, 3.0f, Dt);
		const FVector2D AtReopen = F.EllaRoom();
		TestTrue(FString::Printf(TEXT("%s: falling through the reset band never rode it"), Case.Label), FMath::Abs(AtReopen.X - StartX) < 1.0);
		State->SetAbsorbHeld(false);
		F.Test.TickFrames(1, Dt);
		const bool bInUpper = Log.IsInside(Upper);
		const bool bInLower = Log.IsInside(Lower);
		AddInfo(FString::Printf(TEXT("%s: actual reopen root z %.1f; inside reset=%d onward=%d; capsule half height %.1f"), Case.Label, AtReopen.Y, bInUpper ? 1 : 0, bInLower ? 1 : 0,
			F.Ella->GetCapsuleComponent()->GetScaledCapsuleHalfHeight()));
		TestEqual(FString::Printf(TEXT("%s: reset band touching Ella"), Case.Label), bInUpper, Case.ExpectedSign < 0);
		TestEqual(FString::Printf(TEXT("%s: onward band touching Ella"), Case.Label), bInLower, Case.ExpectedSign > 0);
		if (Case.ExpectedSign == 0)
		{
			// Rising 120/s from the gap reaches the reset band (z 360) in about 0.1 s; before that nothing carries her.
			F.Test.TickSeconds(0.05f, Dt);
			TestTrue(TEXT("gap: no current moved her"), FMath::Abs(F.EllaRoom().X - AtReopen.X) < 1.0);
			continue;
		}
		F.Test.TickSeconds(MeasureSeconds, Dt);
		const double Carried = F.EllaRoom().X - AtReopen.X;
		AddInfo(FString::Printf(TEXT("%s: carried %.1f units in %.1f s"), Case.Label, Carried, MeasureSeconds));
		TestTrue(FString::Printf(TEXT("%s: the Motor rides the real current"), Case.Label), F.Ella->GetMotor()->IsRiding());
		TestTrue(FString::Printf(TEXT("%s: carried the chosen way"), Case.Label), Carried * Case.ExpectedSign > MinCarry);
		// Transient after the measurement: record where free rising takes her (the local restoring field is not built).
		float StolenAt = -1.0f;
		for (float Elapsed = 0.0f; Elapsed < 1.5f; Elapsed += Dt)
		{
			F.Test.TickFrames(1, Dt);
			if (StolenAt < 0.0f && Case.ExpectedSign > 0 && Log.IsInside(Upper))
			{
				StolenAt = MeasureSeconds + Elapsed;
			}
		}
		AddInfo(FString::Printf(TEXT("%s: 1.9 s after reopen root (%.1f, %.1f); reached reset band after %.2f s (-1 = never)"), Case.Label, F.EllaRoom().X, F.EllaRoom().Y, StolenAt));
	}
	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FMillWorldFallingPass, "UmbrellaElla.BrokenMill.World.FallingPassRidesOnwardOneShot", UMBRELLAELLA_MILL_FLAGS)
bool FMillWorldFallingPass::RunTest(const FString& Parameters)
{
	// HAZ-14/15: warned in the commit region, Ella falls through the firing column and reopens late; the real onward
	// current carries her right while the single snapshot shot flies at where she was and misses.
	const float Dt = 1.0f / 60.0f;
	const FVector2D Entry(600.0, 650.0);
	BrokenMillTest::FMillIntegratedFixture F;
	if (!TestNotNull(TEXT("fixture"), F.Spawn(Entry, true)))
	{
		return false;
	}
	BrokenMillTest::FMillEllaEventLog Log;
	Log.Attach(F.Test.GetWorld(), F.Ella->GetFName());
	F.Test.TickFrames(2, Dt);
	TestEqual(TEXT("warning on entry"), F.Room->GetEventCount(EMillGuardEvent::WarningStarted), 1);
	const FVector Captured = F.Room->GetGuard().CapturedTarget;
	UUmbrellaStateComponent* State = F.Ella->GetUmbrellaState();
	State->SetRideHeld(true);
	State->SetAbsorbHeld(true);
	F.TickUntilRootBelow(270.0f, 3.0f, Dt);
	State->SetAbsorbHeld(false);
	const FVector2D AtReopen = F.EllaRoom();
	TestEqual(TEXT("one shot released during the fall"), F.Room->GetEventCount(EMillGuardEvent::ShotReleased), 1);
	AUmbrellaProjectile* Shot = nullptr;
	for (TActorIterator<AUmbrellaProjectile> It(F.Test.GetWorld()); It; ++It)
	{
		Shot = *It;
	}
	if (TestNotNull(TEXT("the shot is live"), Shot))
	{
		const FVector2D Aim = (FVector2D(Captured.X, Captured.Z) - F.Room->GetMillTuning().GuardMuzzle).GetSafeNormal();
		const FVector2D Flight = FVector2D(Shot->GetSpec().Velocity.X, Shot->GetSpec().Velocity.Z).GetSafeNormal();
		TestTrue(TEXT("aimed at the target captured at warning start, never retargeted"), FVector2D::DotProduct(Aim, Flight) > 0.999);
	}
	F.Test.TickSeconds(0.4f, Dt);
	TestTrue(TEXT("the real onward current carries her right"), F.EllaRoom().X - AtReopen.X > 20.0);
	// Fall away below the room so she cannot re-enter the commit region while the shot lives.
	State->SetAbsorbHeld(true);
	F.Test.TickSeconds(F.Room->GetMillTuning().ShotRange / F.Room->GetMillTuning().ShotSpeed + 0.2f, Dt);
	TestEqual(TEXT("shot gone"), F.CountShots(), 0);
	TestEqual(TEXT("the snapshot shot never touched Ella"), Log.ShotContactsOnElla(), 0);
	TestEqual(TEXT("one warning for the whole pass"), F.Room->GetEventCount(EMillGuardEvent::WarningStarted), 1);
	// Fresh entry (position-driven: no current in the room carries her back up to z 650).
	State->SetAbsorbHeld(false);
	F.Ella->SetActorLocation(F.Room->RoomToWorld(Entry));
	F.Test.TickSeconds(0.1f, Dt);
	TestEqual(TEXT("a fresh entry rearms and warns again"), F.Room->GetEventCount(EMillGuardEvent::WarningStarted), 2);
	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FMillWorldFreeRise, "UmbrellaElla.BrokenMill.World.FreeRiseLeavesRegionShotMisses", UMBRELLAELLA_MILL_FLAGS)
bool FMillWorldFreeRise::RunTest(const FString& Parameters)
{
	// HAZ-15: the 1.1 s tell is a snapshot. Rising freely at 120/s Ella leaves the 70-tall commit region before the
	// release; the guard still fires once, straight at the captured point, and the shot misses.
	const float Dt = 1.0f / 60.0f;
	const FBrokenMillTuning& T = GetDefault<UUmbrellaTuning>()->BrokenMill;
	BrokenMillTest::FMillIntegratedFixture F;
	if (!TestNotNull(TEXT("fixture"), F.Spawn(FVector2D(600.0, T.ActivationZ.X + 10.0f))))
	{
		return false;
	}
	BrokenMillTest::FMillEllaEventLog Log;
	Log.Attach(F.Test.GetWorld(), F.Ella->GetFName());
	F.Test.TickFrames(1, Dt);
	TestEqual(TEXT("warning on entry"), F.Room->GetEventCount(EMillGuardEvent::WarningStarted), 1);
	const FVector Captured = F.Room->GetGuard().CapturedTarget;
	float LeftRegionAt = -1.0f;
	float Elapsed = 0.0f;
	FVector2D AtRelease = FVector2D::ZeroVector;
	while (F.Room->GetEventCount(EMillGuardEvent::ShotReleased) + F.Room->GetEventCount(EMillGuardEvent::WarningAborted) == 0 && Elapsed < 2.0f)
	{
		F.Test.TickFrames(1, Dt);
		Elapsed += Dt;
		if (LeftRegionAt < 0.0f && F.EllaRoom().Y > T.ActivationZ.Y)
		{
			LeftRegionAt = Elapsed;
		}
		AtRelease = F.EllaRoom();
	}
	AddInfo(FString::Printf(TEXT("left the region after %.2f s; root at release (%.1f, %.1f)"), LeftRegionAt, AtRelease.X, AtRelease.Y));
	TestTrue(TEXT("free rise left the region before the release"), LeftRegionAt > 0.0f && LeftRegionAt < T.WarningSeconds);
	TestTrue(TEXT("engagement is still valid where she rose to"), FBrokenMillRules::IsEngagementValid(T, AtRelease, true));
	TestEqual(TEXT("one shot released (leaving the region does not abort)"), F.Room->GetEventCount(EMillGuardEvent::ShotReleased), 1);
	for (TActorIterator<AUmbrellaProjectile> It(F.Test.GetWorld()); It; ++It)
	{
		const FVector2D Aim = (FVector2D(Captured.X, Captured.Z) - T.GuardMuzzle).GetSafeNormal();
		const FVector2D Flight = FVector2D(It->GetSpec().Velocity.X, It->GetSpec().Velocity.Z).GetSafeNormal();
		TestTrue(TEXT("straight at the captured point"), FVector2D::DotProduct(Aim, Flight) > 0.999);
	}
	F.Test.TickSeconds(FBrokenMillRules::GetGuardShotLifetime(T) + 0.2f, Dt);
	TestEqual(TEXT("shot gone"), F.CountShots(), 0);
	TestEqual(TEXT("the shot missed the risen Ella"), Log.ShotContactsOnElla(), 0);
	TestEqual(TEXT("no second warning"), F.Room->GetEventCount(EMillGuardEvent::WarningStarted), 1);
	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FMillWorldMissedCurrent, "UmbrellaElla.BrokenMill.World.MissedCurrentFallsAndMinimumLiftRescue", UMBRELLAELLA_MILL_FLAGS)
bool FMillWorldMissedCurrent::RunTest(const FString& Parameters)
{
	// HAZ-15: ordinary-fall and optional-freefall misses of the onward current, the actual reopening heights, and the
	// rescue envelope at minimum lift with no dash or hop ever requested.
	const float Dt = 1.0f / 60.0f;
	const FBrokenMillTuning& T = GetDefault<UUmbrellaTuning>()->BrokenMill;
	const FMotorTuning& Motor = GetDefault<UUmbrellaTuning>()->Motor;
	const float MinLift = GetDefault<UUmbrellaTuning>()->Health.MinLift;
	const FVector2D Start(650.0, 300.0);
	const float MissTop = 270.0f;
	const float MissLow = 150.0f;

	// 1. Fall times 270 -> 150 (GDD: 0.364 s ordinary, 0.197 s free fall; nominal, not a recovery guarantee).
	for (const bool bFreeFall : {false, true})
	{
		BrokenMillTest::FMillIntegratedFixture F;
		if (!TestNotNull(TEXT("fixture"), F.Spawn(Start, true)))
		{
			return false;
		}
		UUmbrellaStateComponent* State = F.Ella->GetUmbrellaState();
		State->SetRideHeld(true);
		State->SetAbsorbHeld(true);
		State->SetShootHeld(bFreeFall);
		F.TickUntilRootBelow(MissTop, 2.0f, Dt);
		const float FromZ = F.EllaRoom().Y;
		const float Seconds = F.TickUntilRootBelow(MissLow, 2.0f, Dt);
		const float Speed = bFreeFall ? Motor.FreeFallSpeed : Motor.FallSpeed;
		const float Expected = (MissTop - MissLow) / Speed;
		AddInfo(FString::Printf(TEXT("%s miss: z %.1f -> %.1f in %.3f s (nominal %.3f s)"), bFreeFall ? TEXT("free-fall") : TEXT("ordinary"), FromZ, F.EllaRoom().Y, Seconds, Expected));
		TestTrue(FString::Printf(TEXT("%s fall 270->150 within a frame of nominal"), bFreeFall ? TEXT("free-fall") : TEXT("ordinary")), FMath::Abs(Seconds - Expected) <= Dt + KINDA_SMALL_NUMBER);
		TestTrue(TEXT("falling never rode the onward current"), FMath::Abs(F.EllaRoom().X - Start.X) < 1.0);
	}

	// 2. Rescue envelope at minimum lift: reopen at each height, rise at 0.3 x 120 = 36/s back into the onward band.
	const float FloorContactRoot = T.FloorTop + T.MaxHalfHeight;
	for (const float ReopenZ : {200.0f, 170.0f, 150.0f, 130.0f})
	{
		BrokenMillTest::FMillIntegratedFixture F;
		if (!TestNotNull(TEXT("fixture"), F.Spawn(Start, true)))
		{
			return false;
		}
		BrokenMillTest::FMillEllaEventLog Log;
		Log.Attach(F.Test.GetWorld(), F.Ella->GetFName());
		const FName Lower = F.Room->GetLowerWind()->GetFName();
		BrokenMillTest::MillSetLiftByHealth(F.Test.GetWorld(), 0.0f, 0);
		F.Test.TickFrames(1, Dt);
		TestTrue(TEXT("Motor at minimum lift"), FMath::IsNearlyEqual(F.Ella->GetMotor()->GetLiftMultiplier(), MinLift, 0.001f));
		UUmbrellaStateComponent* State = F.Ella->GetUmbrellaState();
		State->SetRideHeld(true);
		State->SetAbsorbHeld(true);
		F.TickUntilRootBelow(ReopenZ, 2.0f, Dt);
		const float ReopenRoot = F.EllaRoom().Y;
		State->SetAbsorbHeld(false);
		float MinRoot = ReopenRoot;
		float RescuedAt = -1.0f;
		float SpeedSample = -1.0f;
		const float MaxRescueSeconds = (T.LowerOnwardZ.X - ReopenRoot) / (Motor.RiseSpeed * MinLift) + 0.5f;
		for (float Elapsed = 0.0f; Elapsed < MaxRescueSeconds && RescuedAt < 0.0f; Elapsed += Dt)
		{
			F.Test.TickFrames(1, Dt);
			MinRoot = FMath::Min(MinRoot, static_cast<float>(F.EllaRoom().Y));
			if (SpeedSample < 0.0f && Elapsed >= 1.0f - KINDA_SMALL_NUMBER)
			{
				SpeedSample = (F.EllaRoom().Y - ReopenRoot) / (Elapsed + Dt);
			}
			if (Log.IsInside(Lower))
			{
				RescuedAt = Elapsed + Dt;
			}
		}
		TestTrue(TEXT("no sideways motion before the rescue (no dash, no hop, no assist push)"), FMath::Abs(F.EllaRoom().X - Start.X) < 1.0);
		const double BandX = F.EllaRoom().X;
		F.Test.TickSeconds(0.5f, Dt);
		const double Carried = F.EllaRoom().X - BandX;
		const float RealHalfHeight = F.Ella->GetCapsuleComponent()->GetScaledCapsuleHalfHeight();
		AddInfo(FString::Printf(TEXT("reopen at %.0f: actual root %.1f, lowest %.1f, floor clearance %.1f (GDD half height %.0f) / %.1f (real capsule %.0f), rise %.1f/s, back in onward band after %.2f s, carried %.1f in 0.5 s"),
			ReopenZ, ReopenRoot, MinRoot, MinRoot - FloorContactRoot, T.MaxHalfHeight, MinRoot - T.FloorTop - RealHalfHeight, RealHalfHeight, SpeedSample, RescuedAt, Carried));
		TestTrue(TEXT("reopening is immediate (no hidden sink)"), MinRoot >= ReopenRoot - KINDA_SMALL_NUMBER);
		TestTrue(TEXT("actual reopen within one ordinary-fall frame of the decision height"), ReopenZ - ReopenRoot <= Motor.FallSpeed * Dt + KINDA_SMALL_NUMBER);
		TestTrue(TEXT("clear of the floor with the GDD hurtbox"), MinRoot >= FloorContactRoot);
		if (SpeedSample > 0.0f)
		{
			TestTrue(TEXT("minimum-lift rise about 36/s"), FMath::IsNearlyEqual(SpeedSample, Motor.RiseSpeed * MinLift, 1.0f));
		}
		TestTrue(TEXT("rescued: back in the real onward current"), RescuedAt > 0.0f);
		TestTrue(TEXT("rescued: the current carries her onward"), Carried > 10.0);
	}
	return true;
}

#endif
