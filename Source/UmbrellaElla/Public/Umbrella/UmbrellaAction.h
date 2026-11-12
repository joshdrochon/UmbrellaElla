#pragma once

#include "CoreMinimal.h"
#include "UmbrellaAction.generated.h"

/** Ella's four-state action model: which of Shoot and Absorb are held decides it. */
UENUM()
enum class EUmbrellaAction : uint8
{
	Rise,
	ShootFall,
	AbsorbFall,
	FreeFall
};

/** Dash direction. Fire never follows it: shots always go to +X. */
UENUM()
enum class EUmbrellaDashDirection : uint8
{
	Back,
	Forward
};

/** Plain rule functions (no state, no engine objects) so tests and components share one source of truth. */
namespace UmbrellaActionRules
{
	/** Neither held = Rise; Shoot only = ShootFall; Absorb only = AbsorbFall; both = FreeFall. */
	UMBRELLAELLA_API EUmbrellaAction ResolveAction(bool bShootHeld, bool bAbsorbHeld);

	/** Only the shooting fall fires. */
	UMBRELLAELLA_API bool CanFire(EUmbrellaAction Action);

	/** Only the absorbing fall absorbs and heals. */
	UMBRELLAELLA_API bool CanAbsorb(EUmbrellaAction Action);

	UMBRELLAELLA_API bool IsFalling(EUmbrellaAction Action);

	/** Hop is overhead only. */
	UMBRELLAELLA_API bool CanHop(EUmbrellaAction Action);

	/** Dash is falling only (free fall included, at reduced distance). */
	UMBRELLAELLA_API bool CanDash(EUmbrellaAction Action);

	/** Ride needs overhead, Ride held and overlap with a live current. */
	UMBRELLAELLA_API bool CanRide(EUmbrellaAction Action, bool bRideHeld, bool bInCurrent);

	/** Context dash (Hop button while falling): left input = Back, otherwise Forward. */
	UMBRELLAELLA_API EUmbrellaDashDirection ContextDashDirection(float MoveAxis);

	/** Lift multiplier: MinLift + (1 - MinLift) * clamp(ActiveHealth / Capacity, 0, 1). */
	UMBRELLAELLA_API float LiftMultiplier(float ActiveHealth, float Capacity, float MinLift);

	/** Short stable name for events and logs. */
	UMBRELLAELLA_API FName ActionName(EUmbrellaAction Action);
}
