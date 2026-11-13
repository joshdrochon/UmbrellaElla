#include "Motor/MotorModel.h"
#include "Core/UmbrellaSourceIds.h"
#include "Harness/UmbrellaFeatureFlags.h"
#include "Motor/MotorTuning.h"

namespace
{
	float ClampAxis(float Axis)
	{
		return FMath::Clamp(Axis, -1.0f, 1.0f);
	}

	/** Frame-rate independent blend factor for a rate in 1/s. */
	float BlendFactor(float Rate, float DeltaSeconds)
	{
		return 1.0f - FMath::Exp(-FMath::Max(Rate, 0.0f) * DeltaSeconds);
	}

	void Tick(float& Timer, float DeltaSeconds)
	{
		Timer = FMath::Max(Timer - DeltaSeconds, 0.0f);
	}

	/** Start the burst a request asks for, if it is allowed right now. */
	bool TryStart(FMotorModelState& State, EMotorRequest Request, const FMotorInput& Input, const FMotorTuning& Tuning)
	{
		if (State.Burst != EMotorBurst::None || !IsFeatureEnabled(EFeatureId::MOVE_21))
		{
			return false;
		}
		float Sign = 1.0f;
		bool bDash = UmbrellaActionRules::CanDash(Input.Action);
		if (Request == EMotorRequest::Hop)
		{
			// Hop button: overhead = hop, falling = contextual dash.
			Sign = UmbrellaActionRules::ContextDashDirection(Input.MoveAxis) == EUmbrellaDashDirection::Back ? -1.0f : 1.0f;
		}
		else
		{
			Sign = Request == EMotorRequest::DashBack ? -1.0f : 1.0f;
			if (!bDash)
			{
				return false;
			}
		}
		if (bDash)
		{
			if (State.DashCooldownLeft > 0.0f)
			{
				return false;
			}
			const float Multiplier = Input.Action == EUmbrellaAction::FreeFall ? Tuning.FreeFallDashMultiplier : 1.0f;
			State.Burst = EMotorBurst::Dash;
			State.BurstTimeLeft = Tuning.DashDurationSeconds;
			State.BurstVelocity = FVector2D(Sign * Tuning.DashDistance * Multiplier / Tuning.DashDurationSeconds, 0.0f);
			State.DashCooldownLeft = Tuning.DashCooldownSeconds;
			return true;
		}
		if (!UmbrellaActionRules::CanHop(Input.Action) || State.HopCooldownLeft > 0.0f)
		{
			return false;
		}
		State.Burst = EMotorBurst::Hop;
		State.BurstTimeLeft = Tuning.HopDurationSeconds;
		State.BurstVelocity = FVector2D(Sign * Tuning.HopDistance / Tuning.HopDurationSeconds, 0.0f);
		State.HopCooldownLeft = Tuning.HopCooldownSeconds;
		State.ProtectionLeft = Tuning.HopProtectionSeconds;
		return true;
	}
}

void MotorModel::Request(FMotorModelState& State, EMotorRequest Request, const FMotorTuning& Tuning)
{
	State.Buffered = Request;
	State.BufferLeft = Tuning.ToggleBufferSeconds;
}

float MotorModel::BaseVerticalSpeed(const FMotorInput& Input, const FMotorTuning& Tuning)
{
	const float Trim = ClampAxis(Input.TrimAxis) * Tuning.VerticalTrimPct / MotorModel::PercentScale;
	switch (Input.Action)
	{
	case EUmbrellaAction::ShootFall:
	case EUmbrellaAction::AbsorbFall:
		// Up trim reduces descent.
		return -Tuning.FallSpeed * (1.0f - Trim);
	case EUmbrellaAction::FreeFall:
		return -Tuning.FreeFallSpeed * (1.0f - Trim);
	case EUmbrellaAction::Rise:
	default:
		return Tuning.RiseSpeed * Input.LiftMultiplier * (1.0f + Trim);
	}
}

FVector2D MotorModel::Step(FMotorModelState& State, const FMotorInput& Input, const FMotorTuning& Tuning, float DeltaSeconds)
{
	Tick(State.HopCooldownLeft, DeltaSeconds);
	Tick(State.DashCooldownLeft, DeltaSeconds);
	Tick(State.ProtectionLeft, DeltaSeconds);

	if (State.Buffered != EMotorRequest::None)
	{
		if (TryStart(State, State.Buffered, Input, Tuning))
		{
			State.Buffered = EMotorRequest::None;
			State.BufferLeft = 0.0f;
		}
		else
		{
			State.BufferLeft -= DeltaSeconds;
			if (State.BufferLeft <= 0.0f)
			{
				State.Buffered = EMotorRequest::None;
			}
		}
	}

	// Wind: ride a current to reach its velocity; otherwise momentum decays (fast when falling).
	FVector2D WindNow = State.Wind;
	if (IsFeatureEnabled(EFeatureId::MOVE_22))
	{
		State.bRiding = UmbrellaActionRules::CanRide(Input.Action, Input.bRideHeld, Input.bInCurrent);
		if (State.bRiding)
		{
			State.Wind += (Input.CurrentVelocity - State.Wind) * BlendFactor(Tuning.WindAcceleration, DeltaSeconds);
		}
		else
		{
			const float Decay = UmbrellaActionRules::IsFalling(Input.Action) ? Tuning.WindFallingDecay : Tuning.WindOpenDecay;
			State.Wind *= 1.0f - BlendFactor(Decay, DeltaSeconds);
		}
		State.Wind.X = FMath::Clamp<double>(State.Wind.X, -Tuning.HorizontalMaxSpeed, Tuning.HorizontalMaxSpeed);
		State.Wind.Y = FMath::Clamp<double>(State.Wind.Y, -Tuning.HorizontalMaxSpeed, Tuning.HorizontalMaxSpeed);
		WindNow = State.Wind;
	}
	else
	{
		State.bRiding = false;
		State.Wind = FVector2D::ZeroVector;
		WindNow = FVector2D::ZeroVector;
	}

	// Burst: spend at most the time left, so the distance is exact at any delta.
	FVector2D BurstNow = FVector2D::ZeroVector;
	float BurstSeconds = 0.0f;
	if (State.Burst != EMotorBurst::None)
	{
		BurstNow = State.BurstVelocity;
		BurstSeconds = FMath::Min(DeltaSeconds, State.BurstTimeLeft);
		State.BurstTimeLeft -= BurstSeconds;
		if (State.BurstTimeLeft <= 0.0f)
		{
			State.Burst = EMotorBurst::None;
			State.BurstVelocity = FVector2D::ZeroVector;
		}
	}

	const FVector2D Base(0.0f, BaseVerticalSpeed(Input, Tuning));
	// Hostile forced push: no ride blend, no decay, not cancelled by action or defense.
	const FVector2D Forced = Input.ForcedVelocity;
	State.Velocity = Base + WindNow + BurstNow + Forced;
	return (Base + WindNow + Forced) * DeltaSeconds + BurstNow * BurstSeconds;
}

bool MotorModel::IsProtected(const FMotorModelState& State)
{
	return State.ProtectionLeft > 0.0f;
}

bool MotorModel::IsForcedSource(FName SourceId)
{
	return SourceId == UmbrellaSourceIds::GustBand();
}

FVector2D MotorModel::ParseCurrentDirection(FName Detail)
{
	const FString Text = Detail.ToString().TrimStartAndEnd();
	if (Text.Equals(TEXT("Right"), ESearchCase::IgnoreCase))
	{
		return FVector2D(1.0f, 0.0f);
	}
	if (Text.Equals(TEXT("Left"), ESearchCase::IgnoreCase))
	{
		return FVector2D(-1.0f, 0.0f);
	}
	if (Text.Equals(TEXT("Up"), ESearchCase::IgnoreCase))
	{
		return FVector2D(0.0f, 1.0f);
	}
	if (Text.Equals(TEXT("Down"), ESearchCase::IgnoreCase))
	{
		return FVector2D(0.0f, -1.0f);
	}
	FString XText;
	FString ZText;
	if (Text.Split(TEXT(","), &XText, &ZText))
	{
		FVector2D Direction(FCString::Atof(*XText), FCString::Atof(*ZText));
		return Direction.GetSafeNormal();
	}
	return FVector2D::ZeroVector;
}
