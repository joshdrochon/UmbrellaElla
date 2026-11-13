#include "BrokenMill/BrokenMillRules.h"
#include "BrokenMill/BrokenMillTuning.h"
#include "Harness/UmbrellaFeatureFlags.h"

namespace
{
	/** Closest distance from a point to a segment. */
	double DistanceToSegment(const FVector2D& Point, const FVector2D& From, const FVector2D& To)
	{
		const FVector2D Edge = To - From;
		const double Length2 = Edge.SizeSquared();
		const double Along = Length2 > 0.0 ? FMath::Clamp(FVector2D::DotProduct(Point - From, Edge) / Length2, 0.0, 1.0) : 0.0;
		return FVector2D::Distance(Point, From + Edge * Along);
	}

	/** Segment against a box (slab test). */
	bool DoesSegmentHitBox(const FVector2D& From, const FVector2D& To, const FBox2D& Box)
	{
		const FVector2D Delta = To - From;
		double Enter = 0.0;
		double Leave = 1.0;
		for (int32 Axis = 0; Axis < 2; ++Axis)
		{
			const double Origin = Axis == 0 ? From.X : From.Y;
			const double Step = Axis == 0 ? Delta.X : Delta.Y;
			const double Low = Axis == 0 ? Box.Min.X : Box.Min.Y;
			const double High = Axis == 0 ? Box.Max.X : Box.Max.Y;
			if (FMath::IsNearlyZero(Step))
			{
				if (Origin < Low || Origin > High)
				{
					return false;
				}
				continue;
			}
			double NearT = (Low - Origin) / Step;
			double FarT = (High - Origin) / Step;
			if (NearT > FarT)
			{
				Swap(NearT, FarT);
			}
			Enter = FMath::Max(Enter, NearT);
			Leave = FMath::Min(Leave, FarT);
			if (Enter > Leave)
			{
				return false;
			}
		}
		return true;
	}
}

EMillGuardEvent FMillGuard::Advance(const FBrokenMillTuning& Tuning, float DeltaTime, const FMillGuardInputs& Inputs)
{
	if (Inputs.bPaused || !IsFeatureEnabled(EFeatureId::HAZ_05))
	{
		return EMillGuardEvent::None;
	}
	if (bShotLive && Inputs.bShotGone)
	{
		bShotLive = false;
	}
	// Rearm only after the shot is gone, recovery is over and Ella has left the commit region.
	if (State == EMillGuardState::Idle && !bShotLive && !Inputs.bInActivationRegion)
	{
		bArmed = true;
	}
	switch (State)
	{
	case EMillGuardState::Idle:
		if (bEnabled && bArmed && !bShotLive && Inputs.bInActivationRegion && !Inputs.bInNoWarningPhase && Inputs.bEngagementValid)
		{
			State = EMillGuardState::Warning;
			Timer = 0.0f;
			bArmed = false;
			CapturedTarget = Inputs.Ella;
			return EMillGuardEvent::WarningStarted;
		}
		break;
	case EMillGuardState::Warning:
		Timer += DeltaTime;
		if (!bEnabled || Inputs.bPassedBehind)
		{
			State = EMillGuardState::Idle;
			Timer = 0.0f;
			return EMillGuardEvent::WarningCancelled;
		}
		if (Timer >= Tuning.WarningSeconds)
		{
			State = EMillGuardState::Recovery;
			Timer = 0.0f;
			// An invalid release lowers and aborts: quiet recovery, never a retarget.
			if (!Inputs.bEngagementValid || Inputs.bInNoWarningPhase || bShotLive)
			{
				return EMillGuardEvent::WarningAborted;
			}
			bShotLive = true;
			++ShotSerial;
			return EMillGuardEvent::ShotReleased;
		}
		break;
	case EMillGuardState::Recovery:
		Timer += DeltaTime;
		if (Timer >= Tuning.RecoverySeconds)
		{
			State = EMillGuardState::Idle;
			Timer = 0.0f;
		}
		break;
	default:
		break;
	}
	return EMillGuardEvent::None;
}

void FMillGuard::SetGuardEnabled(bool bNewEnabled)
{
	bEnabled = bNewEnabled;
}

void FMillGuard::Reset()
{
	State = EMillGuardState::Idle;
	Timer = 0.0f;
	bArmed = true;
	bShotLive = false;
}

void FMillShotLog::RecordEmission(int32 Serial, float Time, const FVector& Position)
{
	FMillShotLogEntry& Entry = Entries.AddDefaulted_GetRef();
	Entry.Serial = Serial;
	Entry.EmissionTime = Time;
	Entry.EmissionPosition = Position;
}

void FMillShotLog::RecordFirstContact(int32 Serial, FName Contact, float Time)
{
	for (FMillShotLogEntry& Entry : Entries)
	{
		if (Entry.Serial == Serial && Entry.FirstContact.IsNone())
		{
			Entry.FirstContact = Contact;
			Entry.ImpactTime = Time;
		}
	}
}

bool FBrokenMillRules::IsInActivationRegion(const FBrokenMillTuning& Tuning, const FVector& Ella)
{
	return IsFeatureEnabled(EFeatureId::HAZ_04) && Ella.X >= Tuning.ActivationX.X && Ella.X <= Tuning.ActivationX.Y && Ella.Z >= Tuning.ActivationZ.X && Ella.Z <= Tuning.ActivationZ.Y;
}

bool FBrokenMillRules::IsRayClearOfRotor(const FBrokenMillTuning& Tuning, const FVector2D& From, const FVector2D& To)
{
	return DistanceToSegment(Tuning.RotorCentre, From, To) > Tuning.RotorRadius + Tuning.ShotRadius;
}

bool FBrokenMillRules::IsRayClearOfIsland(const FBrokenMillTuning& Tuning, const FVector2D& From, const FVector2D& To)
{
	const FBox2D Island(FVector2D(Tuning.IslandXRange.X, Tuning.IslandUnderside), FVector2D(Tuning.IslandXRange.Y, Tuning.IslandTop + Tuning.ShotRadius));
	return !DoesSegmentHitBox(From, To, Island);
}

bool FBrokenMillRules::IsEngagementValid(const FBrokenMillTuning& Tuning, const FVector2D& Ella, bool bDescentReachable)
{
	if (!bDescentReachable || Tuning.GuardMuzzle.X <= Ella.X)
	{
		return false;
	}
	return FVector2D::Distance(Tuning.GuardMuzzle, Ella) <= Tuning.ShotRange && IsRayClearOfRotor(Tuning, Tuning.GuardMuzzle, Ella) && IsRayClearOfIsland(Tuning, Tuning.GuardMuzzle, Ella);
}

float FBrokenMillRules::GetGuardHp(const FBrokenMillTuning& Tuning, EMillGuardProfile Profile)
{
	return Profile == EMillGuardProfile::Comparison && IsFeatureEnabled(EFeatureId::HAZ_16) ? Tuning.GuardHpComparison : Tuning.GuardHp;
}

EMillTellPose FBrokenMillRules::GetTellPose(EMillGuardState State, bool bLastReleaseAborted, bool bGuardAlive)
{
	if (!IsFeatureEnabled(EFeatureId::HAZ_04) || !bGuardAlive)
	{
		return EMillTellPose::Hidden;
	}
	if (State == EMillGuardState::Warning)
	{
		return EMillTellPose::Raised;
	}
	return State == EMillGuardState::Recovery && bLastReleaseAborted ? EMillTellPose::Lowered : EMillTellPose::Hidden;
}

float FBrokenMillRules::GetGuardShotLifetime(const FBrokenMillTuning& Tuning)
{
	return Tuning.ShotSpeed > 0.0f ? Tuning.ShotRange / Tuning.ShotSpeed : 0.0f;
}

EMillWind FBrokenMillRules::SelectWind(const FBrokenMillTuning& Tuning, float EllaZ)
{
	if (!IsFeatureEnabled(EFeatureId::HAZ_06))
	{
		return EMillWind::None;
	}
	if (EllaZ >= Tuning.UpperResetZ.X && EllaZ <= Tuning.UpperResetZ.Y)
	{
		return EMillWind::UpperReset;
	}
	if (EllaZ >= Tuning.LowerOnwardZ.X && EllaZ <= Tuning.LowerOnwardZ.Y)
	{
		return EMillWind::LowerOnward;
	}
	return EMillWind::None;
}

EMillWind FBrokenMillRules::GetEligibleWind(const FBrokenMillTuning& Tuning, const FVector2D& Ella)
{
	if (!IsFeatureEnabled(EFeatureId::HAZ_07) || Ella.X < Tuning.FiringColumnX.X || Ella.X > Tuning.FiringColumnX.Y)
	{
		return EMillWind::None;
	}
	return SelectWind(Tuning, Ella.Y);
}

bool FBrokenMillRules::IsInMissedCurrentAssist(const FBrokenMillTuning& Tuning, const FVector2D& Ella)
{
	return IsFeatureEnabled(EFeatureId::HAZ_07) && FVector2D::Distance(Ella, Tuning.MissedCurrentAssistPoint) <= Tuning.MissedCurrentAssistRadius;
}

float FBrokenMillRules::GetUndersideClearance(const FBrokenMillTuning& Tuning, float Root)
{
	return Tuning.IslandUnderside - (Root + Tuning.MaxHalfHeight);
}

float FBrokenMillRules::GetFloorClearance(const FBrokenMillTuning& Tuning, float Root)
{
	return (Root - Tuning.MaxHalfHeight) - Tuning.FloorTop;
}

float FBrokenMillRules::GetRotorClearanceAboveShots(const FBrokenMillTuning& Tuning, float HighestShotCentre)
{
	return (Tuning.RotorCentre.Y - Tuning.RotorRadius) - (HighestShotCentre + Tuning.FriendlyShotRadius);
}

float FBrokenMillRules::GetReturnMargin(const FBrokenMillTuning& Tuning)
{
	return Tuning.RayEndX - (Tuning.ProtectedCoreX.Y + Tuning.MaxHalfWidth + Tuning.ShotRadius);
}

FVector2D FBrokenMillRules::GetGuardFeet(const FBrokenMillTuning& Tuning)
{
	return FVector2D(Tuning.GuardFeetX, Tuning.TargetCentre.Y - Tuning.TargetSize.Y * 0.5f);
}

FVector2D FBrokenMillRules::GetLoweredStepEnvelope(const FBrokenMillTuning& Tuning)
{
	return Tuning.LoweredStepEnvelope;
}

bool FBrokenMillRules::IsInAscent(const FBrokenMillTuning& Tuning, const FVector2D& Ella)
{
	return Ella.X >= Tuning.AscentStartX;
}

bool FBrokenMillRules::IsAscentStartClear(const FBrokenMillTuning& Tuning)
{
	return Tuning.AscentStartX >= Tuning.IslandXRange.Y + Tuning.MaxHalfWidth + Tuning.AscentStartMargin;
}

bool FBrokenMillRules::IsInProtectedCore(const FBrokenMillTuning& Tuning, const FVector2D& Root)
{
	return Root.X >= Tuning.ProtectedCoreX.X && Root.X <= Tuning.ProtectedCoreX.Y && Root.Y >= Tuning.ProtectedCoreZ.X && Root.Y <= Tuning.ProtectedCoreZ.Y;
}

bool FBrokenMillRules::IsInVerticalLift(const FBrokenMillTuning& Tuning, const FVector2D& Root)
{
	return FMath::Abs(Root.X - Tuning.VerticalLiftEnd.X) <= Tuning.VerticalLiftHalfWidth && Root.Y <= Tuning.VerticalLiftEnd.Y;
}

bool FBrokenMillRules::IsRootAtReopen(const FBrokenMillTuning& Tuning, float RootZ)
{
	return RootZ <= Tuning.RootReopenZ;
}

FVector2D FBrokenMillRules::GetFiringWindowRoot(const FBrokenMillTuning& Tuning)
{
	const float TargetBottom = Tuning.TargetCentre.Y - Tuning.TargetSize.Y * 0.5f;
	const float TargetTop = Tuning.TargetCentre.Y + Tuning.TargetSize.Y * 0.5f;
	const float MuzzleZ = Tuning.MuzzleOffset.Y;
	const float Radius = Tuning.FriendlyShotRadius;
	const float Low = FMath::Max(TargetBottom - Radius - MuzzleZ, Tuning.IslandTop + Tuning.IslandShotMargin + Radius - MuzzleZ);
	return FVector2D(Low, TargetTop + Radius - MuzzleZ);
}

FVector2D FBrokenMillRules::GetComparisonWindowRoot(const FBrokenMillTuning& Tuning, float TargetHeight)
{
	const float TargetZ = Tuning.TargetCentre.Y;
	const float Reach = TargetHeight * 0.5f + Tuning.FriendlyShotRadius;
	return FVector2D(TargetZ - Reach - Tuning.MuzzleOffset.Y, TargetZ + Reach - Tuning.MuzzleOffset.Y);
}

float FBrokenMillRules::GetWindowSeconds(const FVector2D& Window, float FallSpeed)
{
	return FallSpeed > 0.0f ? (Window.Y - Window.X) / FallSpeed : 0.0f;
}

FIntPoint FBrokenMillRules::GetEmissionCountRange(float WindowSeconds, float PeriodSeconds)
{
	if (PeriodSeconds <= 0.0f)
	{
		return FIntPoint(0, 0);
	}
	const float Ratio = WindowSeconds / PeriodSeconds;
	return FIntPoint(FMath::FloorToInt(Ratio), FMath::CeilToInt(Ratio));
}

float FBrokenMillRules::GetFirstContactSeconds(const FBrokenMillTuning& Tuning, float RootX, float HeroSize)
{
	const float MuzzleX = RootX + GetMuzzleOffset(Tuning, HeroSize).X;
	const float TargetLeft = Tuning.TargetCentre.X - Tuning.TargetSize.X * 0.5f;
	return (TargetLeft - Tuning.FriendlyShotRadius - MuzzleX) / Tuning.FriendlyShotSpeed;
}

FVector2D FBrokenMillRules::GetMuzzleOffset(const FBrokenMillTuning& Tuning, float HeroSize)
{
	return Tuning.MuzzleOffset * HeroSize;
}

bool FBrokenMillRules::IsProgressionWriteAllowed()
{
	return false;
}

TArray<FName> FBrokenMillRules::GetPoolGateFailures(const FBrokenMillTuning& Tuning, const FMillPoolState& State)
{
	TArray<FName> Failures;
	if (!IsFeatureEnabled(EFeatureId::HAZ_17))
	{
		return Failures;
	}
	if (State.bPendingWarning)
	{
		Failures.Add(FName(TEXT("PendingWarning")));
	}
	if (State.bLiveShot)
	{
		Failures.Add(FName(TEXT("LiveShot")));
	}
	if (State.bDelayedImpact)
	{
		Failures.Add(FName(TEXT("DelayedImpact")));
	}
	if (State.bMirrored)
	{
		Failures.Add(FName(TEXT("HorizontalMirror")));
	}
	if (State.ActiveOwners > 1)
	{
		Failures.Add(FName(TEXT("MoreThanOneOwner")));
	}
	if (State.ActiveEnemyBullets > Tuning.MaxActiveEnemyBullets)
	{
		Failures.Add(FName(TEXT("TooManyEnemyBullets")));
	}
	if (State.bNewSimultaneousTiming)
	{
		Failures.Add(FName(TEXT("NewSimultaneousTiming")));
	}
	return Failures;
}
