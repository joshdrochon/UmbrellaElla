#include "Umbrella/UmbrellaAction.h"
#include "Harness/UmbrellaFeatureFlags.h"

EUmbrellaAction UmbrellaActionRules::ResolveAction(bool bShootHeld, bool bAbsorbHeld)
{
	if (bShootHeld && bAbsorbHeld)
	{
		return EUmbrellaAction::FreeFall;
	}
	if (bShootHeld)
	{
		return EUmbrellaAction::ShootFall;
	}
	if (bAbsorbHeld)
	{
		return EUmbrellaAction::AbsorbFall;
	}
	return EUmbrellaAction::Rise;
}

bool UmbrellaActionRules::CanFire(EUmbrellaAction Action)
{
	// MOVE-14: unlimited basic fire only while dropping, and only the shooting fall.
	return IsFeatureEnabled(EFeatureId::MOVE_14) && Action == EUmbrellaAction::ShootFall;
}

bool UmbrellaActionRules::CanAbsorb(EUmbrellaAction Action)
{
	return IsFeatureEnabled(EFeatureId::MOVE_14) && Action == EUmbrellaAction::AbsorbFall;
}

bool UmbrellaActionRules::IsFalling(EUmbrellaAction Action)
{
	return Action != EUmbrellaAction::Rise;
}

bool UmbrellaActionRules::CanHop(EUmbrellaAction Action)
{
	return Action == EUmbrellaAction::Rise;
}

bool UmbrellaActionRules::CanDash(EUmbrellaAction Action)
{
	return IsFalling(Action);
}

bool UmbrellaActionRules::CanRide(EUmbrellaAction Action, bool bRideHeld, bool bInCurrent)
{
	// MOVE-20: Ride needs overhead mode, held Ride and overlap with a live voluntary current.
	return IsFeatureEnabled(EFeatureId::MOVE_20) && Action == EUmbrellaAction::Rise && bRideHeld && bInCurrent;
}

EUmbrellaDashDirection UmbrellaActionRules::ContextDashDirection(float MoveAxis)
{
	return MoveAxis < 0.0f ? EUmbrellaDashDirection::Back : EUmbrellaDashDirection::Forward;
}

float UmbrellaActionRules::LiftMultiplier(float ActiveHealth, float Capacity, float MinLift)
{
	// UMB-05: lift falls with active health toward MinLift, independent of reserve lives.
	if (!IsFeatureEnabled(EFeatureId::UMB_05) || Capacity <= 0.0f)
	{
		return 1.0f;
	}
	return MinLift + (1.0f - MinLift) * FMath::Clamp(ActiveHealth / Capacity, 0.0f, 1.0f);
}

FName UmbrellaActionRules::ActionName(EUmbrellaAction Action)
{
	switch (Action)
	{
	case EUmbrellaAction::ShootFall:
		return FName(TEXT("ShootFall"));
	case EUmbrellaAction::AbsorbFall:
		return FName(TEXT("AbsorbFall"));
	case EUmbrellaAction::FreeFall:
		return FName(TEXT("FreeFall"));
	case EUmbrellaAction::Rise:
	default:
		return FName(TEXT("Rise"));
	}
}
