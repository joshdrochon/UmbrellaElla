#include "Tests/BrokenMill/BrokenMillTestFixture.h"
#include "Attack/AttackEmitterComponent.h"
#include "BrokenMill/BrokenMillIsland.h"
#include "Components/StaticMeshComponent.h"
#include "Core/UmbrellaTuning.h"
#include "EngineUtils.h"
#include "Field/WindCurrent.h"
#include "Motor/EllaMotorComponent.h"
#include "Umbrella/UmbrellaStateComponent.h"

#if WITH_AUTOMATION_TESTS

/**
 * Broken Mill measurements in motion: the real room, the real Ella (Motor, Attack, UmbrellaState), the real winds and
 * real projectiles. Each test logs "MEASURE <row> <what>: measured <x> | GDD <y> | MATCH/GAP" lines and asserts the
 * facts the room itself must hold. GAP lines are recorded findings (docs/build/areas/enemies2-status.md), not passes.
 */
namespace
{
	const float MillMeasureDt = 1.0f / 60.0f;

	FString MillVerdict(bool bMatch)
	{
		return bMatch ? TEXT("MATCH") : TEXT("GAP");
	}

	/** Hold shoot until a fall passes below StopZ (or MaxSeconds), then let every shot resolve. */
	void MillShootFall(BrokenMillTest::FMillIntegratedFixture& F, BrokenMillTest::FMillShotTracker& Tracker, float StopZ, float MaxSeconds, double PinX)
	{
		UUmbrellaStateComponent* State = F.Ella->GetUmbrellaState();
		State->SetShootHeld(true);
		for (float Elapsed = 0.0f; Elapsed < MaxSeconds && F.EllaRoom().Y > StopZ; Elapsed += MillMeasureDt)
		{
			Tracker.Step(F, MillMeasureDt);
			FVector2D Root = F.EllaRoom();
			Root.X = PinX;
			F.Ella->SetActorLocation(F.Room->RoomToWorld(Root));
		}
		State->SetShootHeld(false);
	}

	/** Park Ella far left and high (outside every region and ray) and tick until every tracked shot is gone. */
	void MillDrainShots(BrokenMillTest::FMillIntegratedFixture& F, BrokenMillTest::FMillShotTracker& Tracker, float MaxSeconds)
	{
		const FVector2D Park(F.Room->GetMillTuning().ProtectedCoreX.X, F.Room->GetMillTuning().RoomSize.Y);
		for (float Elapsed = 0.0f; Elapsed < MaxSeconds && !Tracker.HasAllEnded(); Elapsed += MillMeasureDt)
		{
			F.Ella->SetActorLocation(F.Room->RoomToWorld(Park));
			Tracker.Step(F, MillMeasureDt);
		}
	}
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FMillGuardProfiles, "UmbrellaElla.BrokenMill.GuardProfileAndTellRules", UMBRELLAELLA_MILL_FLAGS)
bool FMillGuardProfiles::RunTest(const FString& Parameters)
{
	const FBrokenMillTuning T;
	TestEqual(TEXT("introduction 10 HP"), FBrokenMillRules::GetGuardHp(T, EMillGuardProfile::Introduction), 10.0f);
	TestEqual(TEXT("comparison 20 HP"), FBrokenMillRules::GetGuardHp(T, EMillGuardProfile::Comparison), 20.0f);
	TestEqual(TEXT("warning raises the tell"), FBrokenMillRules::GetTellPose(EMillGuardState::Warning, false, true), EMillTellPose::Raised);
	TestEqual(TEXT("abort lowers the tell for the quiet recovery"), FBrokenMillRules::GetTellPose(EMillGuardState::Recovery, true, true), EMillTellPose::Lowered);
	TestEqual(TEXT("recovery after a shot shows no tell"), FBrokenMillRules::GetTellPose(EMillGuardState::Recovery, false, true), EMillTellPose::Hidden);
	TestEqual(TEXT("idle shows no tell"), FBrokenMillRules::GetTellPose(EMillGuardState::Idle, false, true), EMillTellPose::Hidden);
	TestEqual(TEXT("a downed guard shows no tell"), FBrokenMillRules::GetTellPose(EMillGuardState::Warning, false, false), EMillTellPose::Hidden);
	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FMillWorldNaturalPass, "UmbrellaElla.BrokenMill.World.NaturalPassWarnsThenKills", UMBRELLAELLA_MILL_FLAGS)
bool FMillWorldNaturalPass::RunTest(const FString& Parameters)
{
	// HAZ-16 / HAZ-12: Ella enters the commit region from the left at root z 680 and holds Shoot at once (neutral fire,
	// no aids). The tell is up for the whole warning, the shot comes, she falls through the exposed band. 10 HP: one
	// hit. 20 HP comparison (only HP changed): both exposed emissions must land.
	const FBrokenMillTuning& T = GetDefault<UUmbrellaTuning>()->BrokenMill;
	const FVector2D Entry(T.ActivationX.X + 10.0f, T.VerticalLiftEnd.Y);
	for (const EMillGuardProfile Profile : {EMillGuardProfile::Introduction, EMillGuardProfile::Comparison})
	{
		const TCHAR* Name = Profile == EMillGuardProfile::Introduction ? TEXT("10 HP") : TEXT("20 HP comparison");
		BrokenMillTest::FMillIntegratedFixture F;
		if (!TestNotNull(TEXT("fixture"), F.Spawn(Entry, true)))
		{
			return false;
		}
		F.Room->SetGuardProfile(Profile);
		const float StartHp = F.Room->GetGuardHp();
		BrokenMillTest::FMillShotTracker Tracker;
		UUmbrellaStateComponent* State = F.Ella->GetUmbrellaState();
		State->SetShootHeld(true);
		float TellRaisedSeconds = 0.0f;
		float FirstTellAt = -1.0f;
		float KillAt = -1.0f;
		bool bTellBeforeKill = false;
		for (float Elapsed = 0.0f; Elapsed < 4.0f && KillAt < 0.0f; Elapsed += MillMeasureDt)
		{
			Tracker.Step(F, MillMeasureDt);
			if (F.Room->GetTellVisual()->IsVisible() && F.Room->GetTellPose() == EMillTellPose::Raised)
			{
				TellRaisedSeconds += MillMeasureDt;
				FirstTellAt = FirstTellAt < 0.0f ? Elapsed : FirstTellAt;
				bTellBeforeKill = true;
			}
			if (F.Room->GetGuardHp() <= 0.0f)
			{
				KillAt = Elapsed + MillMeasureDt;
			}
			if (F.EllaRoom().Y < T.FloorTop)
			{
				State->SetShootHeld(false);
			}
		}
		State->SetShootHeld(false);
		FString Emissions;
		FString HitRoots;
		bool bOnlyExposedHit = true;
		for (const BrokenMillTest::FMillShotTrack& Track : Tracker.Tracks)
		{
			if (Track.Kind != EUmbrellaShotKind::PlayerBlast)
			{
				continue;
			}
			Emissions += FString::Printf(TEXT("%.1f "), Track.RootAtEmission.Y);
			if (Track.bHitGuard)
			{
				HitRoots += FString::Printf(TEXT("%.1f "), Track.RootAtEmission.Y);
				bOnlyExposedHit &= Track.Origin.Y - Track.Radius >= T.IslandTop - 0.5f && Track.Origin.Y - Track.Radius <= T.TargetCentre.Y + T.TargetSize.Y * 0.5f;
			}
		}
		AddInfo(FString::Printf(TEXT("MEASURE HAZ-16 %s: warned=%d tell raised %.2f s from %.2f s, red shots %d, kill at %.2f s (%.2f s after the tell), guard hits %d, emission roots [ %s], hits from roots [ %s]"),
			Name, F.Room->GetEventCount(EMillGuardEvent::WarningStarted), TellRaisedSeconds, FirstTellAt, Tracker.CountKind(EUmbrellaShotKind::EnemyRed), KillAt, KillAt - FirstTellAt, Tracker.CountGuardHits(), *Emissions, *HitRoots));
		TestEqual(TEXT("warning shown on entry"), F.Room->GetEventCount(EMillGuardEvent::WarningStarted), 1);
		TestTrue(TEXT("tell visible before the kill"), bTellBeforeKill && FirstTellAt >= 0.0f && FirstTellAt < KillAt);
		TestTrue(TEXT("tell up for the whole 1.1 s warning (within a frame)"), FMath::Abs(TellRaisedSeconds - T.WarningSeconds) <= MillMeasureDt + KINDA_SMALL_NUMBER);
		TestEqual(TEXT("the guard released its one shot"), F.Room->GetEventCount(EMillGuardEvent::ShotReleased), 1);
		TestTrue(TEXT("guard down on this pass"), KillAt > 0.0f);
		const int32 HitsNeeded = FMath::CeilToInt(StartHp / T.FriendlyDamage);
		TestEqual(FString::Printf(TEXT("%s: hits to kill"), Name), Tracker.CountGuardHits(), HitsNeeded);
		TestTrue(TEXT("only shots inside the exposed band hit (no island hit counts)"), bOnlyExposedHit);
		TestFalse(TEXT("the guard body is hidden once down"), F.Room->GetGuardVisual()->IsVisible());
		TestFalse(TEXT("no tell once down"), F.Room->GetTellVisual()->IsVisible());
	}
	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FMillWorldIslandSolid, "UmbrellaElla.BrokenMill.World.IslandStopsShotsNeverAGuardHit", UMBRELLAELLA_MILL_FLAGS)
bool FMillWorldIslandSolid::RunTest(const FString& Parameters)
{
	const FBrokenMillTuning& T = GetDefault<UUmbrellaTuning>()->BrokenMill;
	const float IslandMidZ = (T.IslandTop + T.IslandUnderside) * 0.5f;
	BrokenMillTest::FMillIntegratedFixture F;
	if (!TestNotNull(TEXT("fixture"), F.Spawn(FVector2D(650.0, IslandMidZ))))
	{
		return false;
	}
	F.Room->DisableGuard();
	TestNotNull(TEXT("island actor"), F.Room->GetIsland());
	BrokenMillTest::FMillShotTracker Tracker;
	// A real friendly shot from a root level with the island's side.
	F.Ella->GetUmbrellaState()->SetShootHeld(true);
	BrokenMillTest::MillTickPinned(F, FVector2D(650.0, IslandMidZ), 1, MillMeasureDt);
	Tracker.EndFrame(F, MillMeasureDt, F.Room->GetGuardHp());
	F.Ella->GetUmbrellaState()->SetShootHeld(false);
	// A red shot fired right into the island side.
	FUmbrellaShotSpec Red;
	Red.Kind = EUmbrellaShotKind::EnemyRed;
	Red.Origin = F.Room->RoomToWorld(FVector2D(T.IslandXRange.X - 100.0f, IslandMidZ));
	Red.Velocity = FVector(T.ShotSpeed, 0.0, 0.0);
	Red.Radius = T.ShotRadius;
	Red.Damage = T.ShotDamage;
	Red.LifetimeSeconds = FBrokenMillRules::GetGuardShotLifetime(T);
	AUmbrellaProjectile::Fire(F.Test.GetWorld(), Red);
	MillDrainShots(F, Tracker, 3.0f);
	TestEqual(TEXT("both shots seen"), Tracker.Tracks.Num(), 2);
	for (const BrokenMillTest::FMillShotTrack& Track : Tracker.Tracks)
	{
		const float Stop = T.IslandXRange.X - Track.Radius;
		AddInfo(FString::Printf(TEXT("MEASURE HAZ-14 island side: %s shot from z %.0f ended at x %.1f after %.2f s (island left %.0f)"),
			Track.Kind == EUmbrellaShotKind::PlayerBlast ? TEXT("friendly") : TEXT("red"), Track.Origin.Y, Track.Last.X, Track.EndTime - Track.EmitTime, T.IslandXRange.X));
		TestTrue(TEXT("stopped at the island side, within a frame of travel"), Track.EndTime > 0.0f && Track.Last.X <= Stop + 1.0f && Track.Last.X >= Stop - Track.Speed * MillMeasureDt - 1.0f);
		TestFalse(TEXT("not a guard hit"), Track.bHitGuard);
	}
	TestEqual(TEXT("guard HP untouched"), F.Room->GetGuardHp(), T.GuardHp);
	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FMillMeasureOnwardRide, "UmbrellaElla.BrokenMill.World.MeasureOnwardRideBends", UMBRELLAELLA_MILL_FLAGS)
bool FMillMeasureOnwardRide::RunTest(const FString& Parameters)
{
	// HAZ-08: Ella rides the real lower ONWARD current with Ride held, umbrella open, at trim -1/0/+1 and full/minimum
	// lift. Record the actual root path (peak, lowest, band exit, column exit) and the clearances it implies.
	const FBrokenMillTuning& T = GetDefault<UUmbrellaTuning>()->BrokenMill;
	const FMotorTuning& Motor = GetDefault<UUmbrellaTuning>()->Motor;
	const float MinLift = GetDefault<UUmbrellaTuning>()->Health.MinLift;
	const FVector2D Envelope = FBrokenMillRules::GetLoweredStepEnvelope(T);
	const FVector2D Start(T.FiringColumnX.X + 5.0f, (T.LowerOnwardZ.X + T.LowerOnwardZ.Y) * 0.5f);
	for (const bool bMinLift : {false, true})
	{
		for (const float Trim : {-1.0f, 0.0f, 1.0f})
		{
			BrokenMillTest::FMillIntegratedFixture F;
			if (!TestNotNull(TEXT("fixture"), F.Spawn(Start, true)))
			{
				return false;
			}
			BrokenMillTest::FMillEllaEventLog Log;
			Log.Attach(F.Test.GetWorld(), F.Ella->GetFName());
			const FName Upper = F.Room->GetUpperWind()->GetFName();
			if (bMinLift)
			{
				BrokenMillTest::MillSetLiftByHealth(F.Test.GetWorld(), 0.0f, 0);
			}
			F.Ella->GetUmbrellaState()->SetRideHeld(true);
			F.Ella->GetMotor()->SetTrimAxis(Trim);
			float Peak = Start.Y;
			float Lowest = Start.Y;
			float LeftBandAt = -1.0f;
			float LeftEnvelopeAt = -1.0f;
			float ColumnExitAt = -1.0f;
			float ColumnExitZ = 0.0f;
			float PeakSpeedX = 0.0f;
			bool bUpperTook = false;
			float Elapsed = 0.0f;
			for (; Elapsed < 3.0f && ColumnExitAt < 0.0f; Elapsed += MillMeasureDt)
			{
				const double XBefore = F.EllaRoom().X;
				F.Test.TickFrames(1, MillMeasureDt);
				const FVector2D Root = F.EllaRoom();
				Peak = FMath::Max(Peak, static_cast<float>(Root.Y));
				Lowest = FMath::Min(Lowest, static_cast<float>(Root.Y));
				PeakSpeedX = FMath::Max(PeakSpeedX, static_cast<float>((Root.X - XBefore) / MillMeasureDt));
				bUpperTook |= Log.IsInside(Upper);
				if (LeftBandAt < 0.0f && (Root.Y > T.LowerOnwardZ.Y || Root.Y < T.LowerOnwardZ.X))
				{
					LeftBandAt = Elapsed + MillMeasureDt;
				}
				if (LeftEnvelopeAt < 0.0f && (Root.Y > Envelope.Y || Root.Y < Envelope.X))
				{
					LeftEnvelopeAt = Elapsed + MillMeasureDt;
				}
				if (Root.X > T.FiringColumnX.Y || Root.X < T.FiringColumnX.X)
				{
					ColumnExitAt = Elapsed + MillMeasureDt;
					ColumnExitZ = Root.Y;
				}
			}
			const float Lift = bMinLift ? MinLift : 1.0f;
			const float ExpectedRise = Motor.RiseSpeed * Lift * (1.0f + Trim * Motor.VerticalTrimPct / 100.0f);
			const bool bInside = Peak <= Envelope.Y && Lowest >= Envelope.X;
			AddInfo(FString::Printf(TEXT("MEASURE HAZ-08 onward ride lift %.1f trim %+.0f: rise %.1f/s, peak root %.1f, lowest %.1f, left the band (210-330) at %.2f s, left envelope 185-285 at %.2f s, upper reset took her %d, column exit at %.2f s z %.1f (x %.1f), peak carry %.1f/s; projected underside clearance %.1f (GDD 26 at root 285), floor clearance %.1f (GDD 66 at root 185) | GDD envelope 185-285 | %s"),
				Lift, Trim, ExpectedRise, Peak, Lowest, LeftBandAt, LeftEnvelopeAt, bUpperTook ? 1 : 0, ColumnExitAt, ColumnExitZ, F.EllaRoom().X, PeakSpeedX,
				FBrokenMillRules::GetUndersideClearance(T, Peak), FBrokenMillRules::GetFloorClearance(T, Lowest), *MillVerdict(bInside && !bUpperTook)));
			TestTrue(TEXT("the ride was measured (Motor rode the real current)"), PeakSpeedX > 0.0f);
			TestTrue(TEXT("the local restoring field keeps the root inside the required envelope 185-285 and the upper reset never takes her"), bInside && !bUpperTook);
		}
	}
	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FMillMeasureRedRays, "UmbrellaElla.BrokenMill.World.MeasureRedRayPaths", UMBRELLAELLA_MILL_FLAGS)
bool FMillMeasureRedRays::RunTest(const FString& Parameters)
{
	// HAZ-09: every admissible red ray across the commit region, flown by the real projectile to its end. Closest
	// approach to the rotor, where the leftmost ray ends and how close any ray comes to the protected core.
	const FBrokenMillTuning& T = GetDefault<UUmbrellaTuning>()->BrokenMill;
	BrokenMillTest::FMillIntegratedFixture F;
	if (!TestNotNull(TEXT("fixture"), F.Spawn(FVector2D(T.ActivationX.X, T.ActivationZ.X))))
	{
		return false;
	}
	float MinRotorClearance = TNumericLimits<float>::Max();
	float LeftmostEnd = TNumericLimits<float>::Max();
	int32 Rays = 0;
	int32 Aborts = 0;
	const int32 Columns = 5;
	const int32 Rows = 3;
	for (int32 Column = 0; Column < Columns; ++Column)
	{
		for (int32 Row = 0; Row < Rows; ++Row)
		{
			const FVector2D Point(FMath::Lerp(T.ActivationX.X, T.ActivationX.Y, Column / float(Columns - 1)), FMath::Lerp(T.ActivationZ.X, T.ActivationZ.Y, Row / float(Rows - 1)));
			F.Room->ResetForRestart();
			BrokenMillTest::FMillShotTracker Tracker;
			Tracker.PointOfInterest = T.RotorCentre;
			const int32 WarningFrames = FMath::CeilToInt(T.WarningSeconds / MillMeasureDt) + 2;
			for (int32 Frame = 0; Frame < WarningFrames && Tracker.CountKind(EUmbrellaShotKind::EnemyRed) == 0; ++Frame)
			{
				F.Ella->SetActorLocation(F.Room->RoomToWorld(Point));
				Tracker.Step(F, MillMeasureDt);
			}
			if (Tracker.CountKind(EUmbrellaShotKind::EnemyRed) == 0)
			{
				++Aborts;
				AddInfo(FString::Printf(TEXT("ray to (%.0f, %.0f): no release (aborts %d, warnings %d)"), Point.X, Point.Y, F.Room->GetEventCount(EMillGuardEvent::WarningAborted), F.Room->GetEventCount(EMillGuardEvent::WarningStarted)));
				continue;
			}
			MillDrainShots(F, Tracker, FBrokenMillRules::GetGuardShotLifetime(T) + 0.5f);
			for (const BrokenMillTest::FMillShotTrack& Track : Tracker.Tracks)
			{
				if (Track.Kind != EUmbrellaShotKind::EnemyRed)
				{
					continue;
				}
				++Rays;
				const float Clearance = Track.MinDistanceToPoint - T.RotorRadius - Track.Radius;
				MinRotorClearance = FMath::Min(MinRotorClearance, Clearance);
				LeftmostEnd = FMath::Min(LeftmostEnd, Track.MinX);
				AddInfo(FString::Printf(TEXT("ray to (%.0f, %.0f): rotor centre distance %.1f (clearance %.1f), ended at (%.1f, %.1f) after %.2f s"),
					Point.X, Point.Y, Track.MinDistanceToPoint, Clearance, Track.Last.X, Track.Last.Y, Track.EndTime - Track.EmitTime));
			}
		}
	}
	const float CoreEdge = T.ProtectedCoreX.Y + T.MaxHalfWidth + T.ShotRadius;
	AddInfo(FString::Printf(TEXT("MEASURE HAZ-09 rays: %d flown, %d no release; least rotor clearance %.1f | GDD about 25 | %s"), Rays, Aborts, MinRotorClearance, *MillVerdict(MinRotorClearance >= 20.0f)));
	AddInfo(FString::Printf(TEXT("MEASURE HAZ-09 leftmost ray end x %.1f | GDD 421.6 | %s"), LeftmostEnd, *MillVerdict(FMath::Abs(LeftmostEnd - T.RayEndX) <= 5.0f)));
	AddInfo(FString::Printf(TEXT("MEASURE HAZ-09 margin to core edge %.1f: %.1f | GDD about 30 | %s"), CoreEdge, LeftmostEnd - CoreEdge, *MillVerdict(LeftmostEnd - CoreEdge >= 25.0f)));
	TestTrue(TEXT("rays were flown"), Rays > 0);
	TestTrue(TEXT("no flown ray touched the rotor"), MinRotorClearance > 0.0f);
	TestTrue(TEXT("no ray reaches the protected core"), LeftmostEnd > CoreEdge);
	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FMillMeasureFixture, "UmbrellaElla.BrokenMill.World.MeasureFiringFixture", UMBRELLAELLA_MILL_FLAGS)
bool FMillMeasureFixture::RunTest(const FString& Parameters)
{
	// HAZ-10: the friendly-fire fixture as the real Attack and Motor deliver it: cadence, speed, radius, damage, range,
	// burst, muzzle offset, fall speeds at trim and the rise. Cadence and movement are the shared tuning, not room tuning.
	const FBrokenMillTuning& T = GetDefault<UUmbrellaTuning>()->BrokenMill;
	const FMotorTuning& Motor = GetDefault<UUmbrellaTuning>()->Motor;
	BrokenMillTest::FMillIntegratedFixture F;
	const FVector2D Start(650.0, 640.0);
	if (!TestNotNull(TEXT("fixture"), F.Spawn(Start)))
	{
		return false;
	}
	F.Room->DisableGuard();
	BrokenMillTest::FMillShotTracker Tracker;
	F.Ella->GetUmbrellaState()->SetShootHeld(true);
	const float Window = 1.0f;
	const double StartZ = F.EllaRoom().Y;
	for (float Elapsed = 0.0f; Elapsed < Window - KINDA_SMALL_NUMBER; Elapsed += MillMeasureDt)
	{
		Tracker.Step(F, MillMeasureDt);
	}
	const float FallNeutral = static_cast<float>((StartZ - F.EllaRoom().Y) / Window);
	F.Ella->GetUmbrellaState()->SetShootHeld(false);
	TArray<float> Times;
	float MinGap = TNumericLimits<float>::Max();
	float MaxGap = 0.0f;
	int32 SameInstant = 1;
	const BrokenMillTest::FMillShotTrack* First = Tracker.Tracks.Num() > 0 ? &Tracker.Tracks[0] : nullptr;
	for (int32 Index = 1; Index < Tracker.Tracks.Num(); ++Index)
	{
		const float Gap = Tracker.Tracks[Index].EmitTime - Tracker.Tracks[Index - 1].EmitTime;
		if (Gap < KINDA_SMALL_NUMBER)
		{
			++SameInstant;
			continue;
		}
		MinGap = FMath::Min(MinGap, Gap);
		MaxGap = FMath::Max(MaxGap, Gap);
	}
	if (!TestNotNull(TEXT("shots fired"), First))
	{
		return false;
	}
	const FVector2D OffsetBefore = First->Origin - First->RootBeforeEmission;
	const FVector2D OffsetAfter = First->Origin - First->RootAtEmission;
	AddInfo(FString::Printf(TEXT("MEASURE HAZ-10 cadence: %d shots in %.1f s, first gap %.3f s, gaps %.3f-%.3f s | GDD 5/s (0.200 s) | %s"), Tracker.Tracks.Num(), Window, Tracker.Tracks.Num() > 1 ? Tracker.Tracks[1].EmitTime - Tracker.Tracks[0].EmitTime : 0.0f, MinGap, MaxGap, *MillVerdict(FMath::IsNearlyEqual(MinGap, 1.0f / T.FriendlyShotsPerSecond, 0.002f) && FMath::IsNearlyEqual(MaxGap, 1.0f / T.FriendlyShotsPerSecond, 0.002f))));
	AddInfo(FString::Printf(TEXT("MEASURE HAZ-10 speed %.1f | GDD %.0f | %s"), First->Speed, T.FriendlyShotSpeed, *MillVerdict(FMath::IsNearlyEqual(First->Speed, T.FriendlyShotSpeed, 0.5f))));
	AddInfo(FString::Printf(TEXT("MEASURE HAZ-10 radius %.1f | GDD %.0f | %s"), First->Radius, T.FriendlyShotRadius, *MillVerdict(FMath::IsNearlyEqual(First->Radius, T.FriendlyShotRadius, 0.1f))));
	AddInfo(FString::Printf(TEXT("MEASURE HAZ-10 damage %.1f | GDD %.0f | %s"), First->Damage, T.FriendlyDamage, *MillVerdict(FMath::IsNearlyEqual(First->Damage, T.FriendlyDamage, 0.01f))));
	AddInfo(FString::Printf(TEXT("MEASURE HAZ-10 range %.1f | GDD %.0f | %s"), First->Speed * First->Lifetime, T.FriendlyRange, *MillVerdict(FMath::IsNearlyEqual(First->Speed * First->Lifetime, T.FriendlyRange, 1.0f))));
	AddInfo(FString::Printf(TEXT("MEASURE HAZ-10 burst %d per emission | GDD 1 | %s"), SameInstant, *MillVerdict(SameInstant == 1)));
	AddInfo(FString::Printf(TEXT("MEASURE HAZ-10 muzzle offset from root (start of frame) X %+.1f Z %+.1f, (end of frame) X %+.1f Z %+.1f | GDD +%.0f / +%.0f at HeroSize 1 | %s"),
		OffsetBefore.X, OffsetBefore.Y, OffsetAfter.X, OffsetAfter.Y, T.MuzzleOffset.X, T.MuzzleOffset.Y,
		*MillVerdict(FMath::IsNearlyEqual(OffsetBefore.X, T.MuzzleOffset.X, 1.0f) && FMath::IsNearlyEqual(OffsetBefore.Y, T.MuzzleOffset.Y, 1.0f))));
	TestEqual(TEXT("the first emission is immediate (first frame)"), First->EmitTime, 0.0f);

	// Fall speeds at trim -1/0/+1 while shooting, and the rise at full lift.
	FString Falls;
	bool bFallsMatch = true;
	for (const float Trim : {1.0f, 0.0f, -1.0f})
	{
		BrokenMillTest::FMillIntegratedFixture G;
		if (!TestNotNull(TEXT("fixture"), G.Spawn(Start)))
		{
			return false;
		}
		G.Room->DisableGuard();
		G.Ella->GetMotor()->SetTrimAxis(Trim);
		G.Ella->GetUmbrellaState()->SetShootHeld(true);
		const double Z0 = G.EllaRoom().Y;
		G.Test.TickSeconds(0.5f, MillMeasureDt);
		const float Speed = static_cast<float>((Z0 - G.EllaRoom().Y) / 0.5f);
		const float Gdd = T.FallSpeed * (1.0f - Trim * T.FallTrimFraction);
		bFallsMatch &= FMath::IsNearlyEqual(Speed, Gdd, 1.0f);
		Falls += FString::Printf(TEXT("trim %+.0f %.1f/s (GDD %.0f) "), Trim, Speed, Gdd);
	}
	AddInfo(FString::Printf(TEXT("MEASURE HAZ-10 shoot-fall %s| %s"), *Falls, *MillVerdict(bFallsMatch)));
	{
		BrokenMillTest::FMillIntegratedFixture G;
		if (!TestNotNull(TEXT("fixture"), G.Spawn(FVector2D(300.0, 200.0))))
		{
			return false;
		}
		const double Z0 = G.EllaRoom().Y;
		G.Test.TickSeconds(0.5f, MillMeasureDt);
		const float Rise = static_cast<float>((G.EllaRoom().Y - Z0) / 0.5f);
		AddInfo(FString::Printf(TEXT("MEASURE HAZ-10 rise %.1f/s | GDD 120 | %s"), Rise, *MillVerdict(FMath::IsNearlyEqual(Rise, Motor.RiseSpeed, 1.0f))));
	}
	AddInfo(TEXT("MEASURE HAZ-10 HeroSize 0.75/1.3 and actor scale 0.5 x HeroSize: not built in the game (no HeroSize anywhere outside this room's estimate) | GAP"));
	TestTrue(TEXT("shoot-fall at trim 0 is the shared fall speed"), FMath::IsNearlyEqual(FallNeutral, Motor.FallSpeed, 2.0f));
	TestFalse(TEXT("shadow tests never write progression"), FBrokenMillRules::IsProgressionWriteAllowed());
	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FMillMeasureWindow, "UmbrellaElla.BrokenMill.World.MeasureFiringWindow", UMBRELLAELLA_MILL_FLAGS)
bool FMillMeasureWindow::RunTest(const FString& Parameters)
{
	// HAZ-11: which ROOT heights let a real friendly shot hit the real target (island in front), swept one unit at a
	// time near both edges. The window seconds follow at the three real fall speeds.
	const FBrokenMillTuning& T = GetDefault<UUmbrellaTuning>()->BrokenMill;
	const FMotorTuning& Motor = GetDefault<UUmbrellaTuning>()->Motor;
	const float RootX = 650.0f;
	BrokenMillTest::FMillIntegratedFixture F;
	if (!TestNotNull(TEXT("fixture"), F.Spawn(FVector2D(RootX, 300.0))))
	{
		return false;
	}
	TArray<float> Heights;
	for (float Z = T.IslandTop - 20.0f; Z <= T.IslandTop + 40.0f; Z += 1.0f)
	{
		Heights.Add(Z);
	}
	const float TargetTop = T.TargetCentre.Y + T.TargetSize.Y * 0.5f;
	for (float Z = TargetTop - 10.0f; Z <= TargetTop + 30.0f; Z += 1.0f)
	{
		Heights.Add(Z);
	}
	float Low = TNumericLimits<float>::Max();
	float High = -TNumericLimits<float>::Max();
	float HighestCentre = -TNumericLimits<float>::Max();
	float HitRadius = 0.0f;
	int32 Holes = 0;
	BrokenMillTest::FMillShotTracker Tracker;
	UUmbrellaStateComponent* State = F.Ella->GetUmbrellaState();
	const int32 GapFrames = FMath::CeilToInt(1.0f / GetDefault<UUmbrellaTuning>()->Attack.SmallShotsPerSecond / MillMeasureDt) + 1;
	for (const float Z : Heights)
	{
		F.Room->ResetForRestart();
		F.Room->SetGuardProfile(EMillGuardProfile::Comparison);
		F.Room->DisableGuard();
		const int32 Before = Tracker.Tracks.Num();
		State->SetShootHeld(true);
		for (int32 Frame = 0; Frame < GapFrames && Tracker.Tracks.Num() == Before; ++Frame)
		{
			F.Ella->SetActorLocation(F.Room->RoomToWorld(FVector2D(RootX, Z)));
			Tracker.Step(F, MillMeasureDt);
		}
		State->SetShootHeld(false);
		const float HpBeforeFlight = F.Room->GetGuardHp();
		for (int32 Frame = 0; Frame < 200 && !Tracker.HasAllEnded(); ++Frame)
		{
			F.Ella->SetActorLocation(F.Room->RoomToWorld(FVector2D(RootX, Z)));
			Tracker.Step(F, MillMeasureDt);
		}
		// Wait out the cadence so the next height fires on its first frame.
		BrokenMillTest::MillTickPinned(F, FVector2D(RootX, Z), GapFrames, MillMeasureDt);
		if (Tracker.Tracks.Num() <= Before)
		{
			continue;
		}
		const BrokenMillTest::FMillShotTrack& Track = Tracker.Tracks.Last();
		const bool bHit = Track.bHitGuard || F.Room->GetGuardHp() < HpBeforeFlight;
		// The root when the shot left (the Motor moves her before the Attack fires in the same frame).
		const float Root = static_cast<float>(Track.RootAtEmission.Y);
		if (bHit)
		{
			Low = FMath::Min(Low, Root);
			High = FMath::Max(High, Root);
			HighestCentre = FMath::Max(HighestCentre, static_cast<float>(Track.Origin.Y));
			HitRadius = Track.Radius;
		}
		else if (Root > Low && Root < High)
		{
			++Holes;
		}
	}
	const FVector2D Gdd = FBrokenMillRules::GetFiringWindowRoot(T);
	const float Width = High - Low;
	AddInfo(FString::Printf(TEXT("MEASURE HAZ-11 exposed root band (root at emission) %.1f-%.1f width %.1f (holes %d) | GDD %.0f-%.0f width %.0f | %s"),
		Low, High, Width, Holes, Gdd.X, Gdd.Y, Gdd.Y - Gdd.X, *MillVerdict(FMath::Abs(Low - Gdd.X) <= 1.0f && FMath::Abs(High - Gdd.Y) <= 1.0f)));
	FString Seconds;
	bool bSecondsMatch = true;
	for (const float Trim : {1.0f, 0.0f, -1.0f})
	{
		const float Fall = Motor.FallSpeed * (1.0f - Trim * Motor.VerticalTrimPct / 100.0f);
		const float Measured = Width / Fall;
		const float GddSeconds = FBrokenMillRules::GetWindowSeconds(Gdd, Fall);
		bSecondsMatch &= FMath::Abs(Measured - GddSeconds) <= 0.005f;
		Seconds += FString::Printf(TEXT("fall %.0f: %.3f s (GDD %.3f) "), Fall, Measured, GddSeconds);
	}
	AddInfo(FString::Printf(TEXT("MEASURE HAZ-11 window seconds %s| %s"), *Seconds, *MillVerdict(bSecondsMatch)));
	const float RotorLow = T.RotorCentre.Y - T.RotorRadius;
	const float RotorGap = RotorLow - (HighestCentre + HitRadius);
	AddInfo(FString::Printf(TEXT("MEASURE HAZ-09 highest useful friendly-shot centre %.0f + radius %.0f, rotor low %.0f leaves %.0f | GDD 526 + 6, 78 | %s"),
		HighestCentre, HitRadius, RotorLow, RotorGap, *MillVerdict(FMath::Abs(RotorGap - 78.0f) <= 1.0f)));
	TestTrue(TEXT("a window was found"), Width > 0.0f);
	TestEqual(TEXT("the window has no holes"), Holes, 0);
	TestTrue(TEXT("the island blocks every low line: lowest hitting shot's lower edge clears the island top"), Low - HitRadius + (HighestCentre - High) >= T.IslandTop - 0.5f);
	TestTrue(TEXT("useful shots stay under the rotor"), RotorGap > 0.0f);
	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FMillMeasureEmissions, "UmbrellaElla.BrokenMill.World.MeasureEmissionsPerPass", UMBRELLAELLA_MILL_FLAGS)
bool FMillMeasureEmissions::RunTest(const FString& Parameters)
{
	// HAZ-12: real shoot-falls through the real target at trim +1/0/-1 (fall 264/330/396) and six cadence phases each:
	// how many emissions actually hit per pass. Plus the GDD's worked case from root z 680.
	const FBrokenMillTuning& T = GetDefault<UUmbrellaTuning>()->BrokenMill;
	const FMotorTuning& Motor = GetDefault<UUmbrellaTuning>()->Motor;
	const float Period = 1.0f / GetDefault<UUmbrellaTuning>()->Attack.SmallShotsPerSecond;
	const float RootX = 650.0f;
	const int32 Phases = 10;
	const TCHAR* GddRange[] = {TEXT("2-3"), TEXT("1-2"), TEXT("1-2")};
	const FIntPoint GddCounts[] = {FIntPoint(2, 3), FIntPoint(1, 2), FIntPoint(1, 2)};
	int32 TrimIndex = 0;
	for (const float Trim : {1.0f, 0.0f, -1.0f})
	{
		const float Fall = Motor.FallSpeed * (1.0f - Trim * Motor.VerticalTrimPct / 100.0f);
		int32 MinHits = TNumericLimits<int32>::Max();
		int32 MaxHits = 0;
		FString PerPhase;
		for (int32 Phase = 0; Phase < Phases; ++Phase)
		{
			const float StartZ = 680.0f - Fall * Period * Phase / Phases;
			BrokenMillTest::FMillIntegratedFixture F;
			if (!TestNotNull(TEXT("fixture"), F.Spawn(FVector2D(RootX, StartZ))))
			{
				return false;
			}
			F.Room->SetGuardProfile(EMillGuardProfile::Comparison);
			F.Room->DisableGuard();
			F.Ella->GetMotor()->SetTrimAxis(Trim);
			BrokenMillTest::FMillShotTracker Tracker;
			Tracker.bReviveGuard = true;
			MillShootFall(F, Tracker, T.IslandUnderside - 40.0f, 2.0f, RootX);
			MillDrainShots(F, Tracker, 2.5f);
			int32 Hits = Tracker.CountGuardHits();
			MinHits = FMath::Min(MinHits, Hits);
			MaxHits = FMath::Max(MaxHits, Hits);
			FString Roots;
			for (const BrokenMillTest::FMillShotTrack& Track : Tracker.Tracks)
			{
				Roots += FString::Printf(TEXT("%.1f%s "), Track.RootAtEmission.Y, Track.bHitGuard ? TEXT("*") : TEXT(""));
			}
			PerPhase += FString::Printf(TEXT("[start %.0f: %d hits; %s] "), StartZ, Hits, *Roots);
			if (Trim == 0.0f && Phase == 0)
			{
				AddInfo(FString::Printf(TEXT("MEASURE HAZ-12 from root 680, immediate neutral fire: emission roots (* = hit) %s | GDD 680/614/548/482/416/350, only 482/416 exposed"), *Roots));
			}
		}
		const bool bMatch = MinHits == GddCounts[TrimIndex].X && MaxHits == GddCounts[TrimIndex].Y;
		AddInfo(FString::Printf(TEXT("MEASURE HAZ-12 fall %.0f: hits per pass %d-%d over %d phases | GDD %s | %s"), Fall, MinHits, MaxHits, Phases, GddRange[TrimIndex], *MillVerdict(bMatch)));
		AddInfo(FString::Printf(TEXT("  fall %.0f detail: %s"), Fall, *PerPhase));
		TestTrue(TEXT("every pass lands at least one hit (the 10 HP introduction is winnable in one pass)"), MinHits >= 1);
		++TrimIndex;
	}
	AddInfo(FString::Printf(TEXT("MEASURE HAZ-12 four hits need >= %.1f s between first and fourth emission | GDD >= 0.6 s"), 3.0f * Period));
	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FMillMeasureDelayedImpact, "UmbrellaElla.BrokenMill.World.MeasureDelayedImpact", UMBRELLAELLA_MILL_FLAGS)
bool FMillMeasureDelayedImpact::RunTest(const FString& Parameters)
{
	// HAZ-13: first contact from root x 650 on the line; forward drift after closing out of the real onward current
	// and the contact time it gives; a shot still in flight lands after Ella reopens, the target still there.
	const FBrokenMillTuning& T = GetDefault<UUmbrellaTuning>()->BrokenMill;
	const FMotorTuning& Motor = GetDefault<UUmbrellaTuning>()->Motor;
	const float LineZ = T.TargetCentre.Y;
	{
		BrokenMillTest::FMillIntegratedFixture F;
		if (!TestNotNull(TEXT("fixture"), F.Spawn(FVector2D(650.0, LineZ))))
		{
			return false;
		}
		F.Room->DisableGuard();
		BrokenMillTest::FMillShotTracker Tracker;
		F.Ella->GetUmbrellaState()->SetShootHeld(true);
		BrokenMillTest::MillTickPinned(F, FVector2D(650.0, LineZ), 0, MillMeasureDt);
		Tracker.Step(F, MillMeasureDt);
		F.Ella->GetUmbrellaState()->SetShootHeld(false);
		MillDrainShots(F, Tracker, 3.0f);
		const BrokenMillTest::FMillShotTrack* Shot = Tracker.Tracks.Num() > 0 ? &Tracker.Tracks[0] : nullptr;
		if (!TestNotNull(TEXT("shot"), Shot))
		{
			return false;
		}
		const float Contact = Shot->EndTime - Shot->EmitTime;
		const float Gdd = FBrokenMillRules::GetFirstContactSeconds(T, 650.0f, 1.0f);
		AddInfo(FString::Printf(TEXT("MEASURE HAZ-13 first contact from root x 650: muzzle x %.1f, contact after %.3f s (frame-quantised, %.3f s analytic for this muzzle/radius) | GDD 1.014 s (muzzle 694) | %s"),
			Shot->Origin.X, Contact, (T.TargetCentre.X - T.TargetSize.X * 0.5f - Shot->Radius - Shot->Origin.X) / Shot->Speed, *MillVerdict(FMath::Abs(Contact - Gdd) <= MillMeasureDt)));
		TestTrue(TEXT("hit the guard"), Shot->bHitGuard);
	}
	{
		// Ride the onward current at the band centre (height held: the ride alone rises out of the band, see
		// MeasureOnwardRideBends), close the umbrella to shoot, measure the residual forward drift.
		const FVector2D Start(T.FiringColumnX.X + 5.0f, (T.LowerOnwardZ.X + T.LowerOnwardZ.Y) * 0.5f);
		BrokenMillTest::FMillIntegratedFixture F;
		if (!TestNotNull(TEXT("fixture"), F.Spawn(Start, true)))
		{
			return false;
		}
		F.Room->DisableGuard();
		F.Ella->GetUmbrellaState()->SetRideHeld(true);
		float RideSeconds = 0.0f;
		while (F.EllaRoom().X < T.FiringColumnX.Y - 60.0f && RideSeconds < 3.0f)
		{
			F.TickPinnedZ(MillMeasureDt, MillMeasureDt);
			RideSeconds += MillMeasureDt;
		}
		const double CloseX = F.EllaRoom().X;
		const double SpeedAtClose = F.Ella->GetMotor()->GetVelocity().X;
		F.Ella->GetUmbrellaState()->SetShootHeld(true);
		float Settle = 0.0f;
		while (Settle < 1.5f)
		{
			F.TickPinnedZ(MillMeasureDt, MillMeasureDt);
			Settle += MillMeasureDt;
		}
		const double Drift = F.EllaRoom().X - CloseX;
		const float GddDrift = 30.0f;
		const float DriftContact = FBrokenMillRules::GetFirstContactSeconds(T, 650.0f + static_cast<float>(Drift), 1.0f);
		AddInfo(FString::Printf(TEXT("MEASURE HAZ-13 drift: carried at %.1f/s after %.2f s riding (room wind %.0f, Motor clamp %.0f), residual drift after closing %.1f units, GDD-muzzle contact from 650 + drift %.3f s | GDD wind 360 / decay 12: about 30 units, 0.971 s | %s"),
			SpeedAtClose, RideSeconds, T.WindSpeed, Motor.WindMaxSpeed, Drift, DriftContact, *MillVerdict(FMath::Abs(Drift - GddDrift) <= 3.0f)));
		TestTrue(TEXT("closing kept some forward drift"), Drift > 0.0);
		TestTrue(TEXT("drift is the falling decay of the carried speed (speed / decay, within 15%)"), FMath::IsNearlyEqual(static_cast<float>(Drift), static_cast<float>(SpeedAtClose) / Motor.WindFallingDecay, static_cast<float>(SpeedAtClose) / Motor.WindFallingDecay * 0.15f));
	}
	{
		// Delayed impact: one shot on the line, then Ella reopens (Shoot released) and rises before it lands.
		BrokenMillTest::FMillIntegratedFixture F;
		if (!TestNotNull(TEXT("fixture"), F.Spawn(FVector2D(650.0, LineZ))))
		{
			return false;
		}
		F.Room->DisableGuard();
		BrokenMillTest::FMillShotTracker Tracker;
		F.Ella->GetUmbrellaState()->SetShootHeld(true);
		Tracker.Step(F, MillMeasureDt);
		F.Ella->GetUmbrellaState()->SetShootHeld(false);
		const float ReopenedAt = Tracker.Clock;
		bool bVisibleAtImpact = false;
		float HitAt = -1.0f;
		for (float Elapsed = 0.0f; Elapsed < 2.0f && HitAt < 0.0f; Elapsed += MillMeasureDt)
		{
			const bool bVisible = F.Room->GetGuardVisual()->IsVisible();
			Tracker.Step(F, MillMeasureDt);
			if (Tracker.CountGuardHits() > 0)
			{
				HitAt = Tracker.Clock;
				bVisibleAtImpact = bVisible;
			}
		}
		AddInfo(FString::Printf(TEXT("MEASURE HAZ-13 delayed impact: reopened at %.3f s, Ella rose to z %.1f, hit landed at %.3f s, target visible until impact %d | GDD target stays alive/visible | %s"),
			ReopenedAt, F.EllaRoom().Y, HitAt, bVisibleAtImpact ? 1 : 0, *MillVerdict(HitAt > ReopenedAt && bVisibleAtImpact)));
		TestTrue(TEXT("the shot landed after she reopened"), HitAt > ReopenedAt);
		TestTrue(TEXT("the target was still visible when it landed"), bVisibleAtImpact);
		TestTrue(TEXT("she was rising (reopened) by then"), F.EllaRoom().Y > LineZ);
	}
	AddInfo(TEXT("MEASURE HAZ-13 HeroSize 1.3 (muzzle 57.2 / 7.8, band 1.8 lower): HeroSize not built | GAP"));
	return true;
}

#endif
