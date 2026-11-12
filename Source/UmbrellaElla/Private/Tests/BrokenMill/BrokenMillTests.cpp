#include "Engine/Engine.h"
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

#if WITH_AUTOMATION_TESTS

#define UMBRELLAELLA_MILL_FLAGS (EAutomationTestFlags::EditorContext | EAutomationTestFlags::ClientContext | EAutomationTestFlags::EngineFilter)

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

	/** Real Ella plus a built room at an offset; the room's target is Ella. */
	struct FMillIntegratedFixture
	{
		FUmbrellaTestWorld Test;
		AEllaCharacter* Ella = nullptr;
		ABrokenMillRoom* Room = nullptr;

		bool Setup(const FVector2D& EllaRoomPoint)
		{
			UWorld* World = Test.GetWorld();
			if (!World)
			{
				return false;
			}
			Room = World->SpawnActor<ABrokenMillRoom>(ABrokenMillRoom::StaticClass(), FTransform(FVector(10000.0, 0.0, 0.0)));
			if (!Room)
			{
				return false;
			}
			Room->BuildRoom();
			Ella = Test.SpawnElla(Room->RoomToWorld(EllaRoomPoint));
			if (Ella)
			{
				Room->SetTargetActor(Ella);
			}
			return Ella != nullptr;
		}

		/** Tick with Ella's height pinned (a held trim), so only the Motor's sideways motion moves her. */
		void TickPinnedZ(float Seconds, float Dt)
		{
			const double Z = Ella->GetActorLocation().Z;
			for (int32 Frame = 0; Frame < FMath::RoundToInt(Seconds / Dt); ++Frame)
			{
				Test.TickFrames(1, Dt);
				FVector Location = Ella->GetActorLocation();
				Location.Z = Z;
				Ella->SetActorLocation(Location);
			}
		}

		int32 CountShots() const { return Test.CountActors<AUmbrellaProjectile>(); }
		FVector2D EllaRoom() const { return Room->WorldToRoom(Ella->GetActorLocation()); }
	};
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
		FMillIntegratedFixture F;
		if (!TestTrue(TEXT("fixture"), F.Setup(FVector2D(600.0, 650.0))))
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
		FMillIntegratedFixture F;
		if (!TestTrue(TEXT("fixture"), F.Setup(FVector2D(600.0, 650.0))))
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
		FMillIntegratedFixture F;
		if (!TestTrue(TEXT("fixture"), F.Setup(FVector2D(600.0, 650.0))))
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

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FMillWorldWindPass, "UmbrellaElla.BrokenMill.World.WindCarriesEllaPastOneShotPerPass", UMBRELLAELLA_MILL_FLAGS)
bool FMillWorldWindPass::RunTest(const FString& Parameters)
{
	const float Dt = 1.0f / 60.0f;
	FMillIntegratedFixture F;
	if (!TestTrue(TEXT("fixture"), F.Setup(FVector2D(480.0, 650.0))))
	{
		return false;
	}
	AWindCurrent* Lower = F.Room->GetLowerWind();
	if (!TestNotNull(TEXT("onward wind"), Lower) || !TestNotNull(TEXT("reset wind"), F.Room->GetUpperWind()))
	{
		return false;
	}
	TestTrue(TEXT("onward wind pushes right"), Lower->GetDirection().X > 0.0);
	TestTrue(TEXT("reset wind pushes left"), F.Room->GetUpperWind()->GetDirection().X < 0.0);
	// The wind actor's overlap event names the pawn by actor name; the Motor answers to the id "Ella" (or none).
	// Until the Field lane and the Motor agree (docs/build/requests/enemies.md), put the current on the bus the way the
	// Motor reads it, with the force and direction label taken from the real wind actor.
	FUmbrellaEvent Entered;
	Entered.Type = EUmbrellaEventType::WindEntered;
	Entered.SourceId = Lower->GetFName();
	Entered.TargetId = UmbrellaPlayerIds::Ella;
	Entered.Detail = AWindCurrent::DirectionLabel(Lower->GetDirection());
	Entered.Value = Lower->GetForce();
	UUmbrellaEventBus::Get(F.Test.GetWorld())->Broadcast(Entered);
	F.Ella->GetInputAdapter()->ApplyPress(EUmbrellaInputAction::Ride);

	F.TickPinnedZ(0.5f, Dt);
	TestTrue(TEXT("the current carries Ella right"), F.Ella->GetActorLocation().X > F.Room->RoomToWorld(FVector2D(480.0, 650.0)).X + 50.0);
	TestEqual(TEXT("guard warned once on entry"), F.Room->GetEventCount(EMillGuardEvent::WarningStarted), 1);

	F.TickPinnedZ(1.5f, Dt);
	TestEqual(TEXT("one shot released for the pass"), F.Room->GetEventCount(EMillGuardEvent::ShotReleased), 1);
	TestEqual(TEXT("still one warning (no second while recovering)"), F.Room->GetEventCount(EMillGuardEvent::WarningStarted), 1);

	F.TickPinnedZ(2.0f, Dt);
	TestTrue(TEXT("Ella is carried past the guard muzzle"), F.EllaRoom().X > F.Room->GetMillTuning().GuardMuzzle.X);
	TestEqual(TEXT("passing behind started no new warning"), F.Room->GetEventCount(EMillGuardEvent::WarningStarted), 1);

	// Recovery over and the shot gone: a fresh entry from the left is a new pass and the guard warns again.
	F.TickPinnedZ(3.0f, Dt);
	TestEqual(TEXT("shot is gone"), F.CountShots(), 0);
	F.Ella->SetActorLocation(F.Room->RoomToWorld(FVector2D(480.0, 650.0)));
	F.TickPinnedZ(0.3f, Dt);
	TestEqual(TEXT("second pass rearms and warns again"), F.Room->GetEventCount(EMillGuardEvent::WarningStarted), 2);
	return true;
}

#endif
