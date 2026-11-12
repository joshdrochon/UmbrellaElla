#pragma once

#include "CoreMinimal.h"
#include "InputCoreTypes.h"

/** Every logical player action the adapter owns (IA_* names in the GDD). */
enum class EUmbrellaInputAction : uint8
{
	Shoot,
	Absorb,
	Hop,
	DashBack,
	DashForward,
	Ride,
	Trim,
	MoveX,
	Spell1,
	Spell2,
	Spell3,
	Spell4,
	SpellNext,
	SpellPrevious,
	Count
};

/** One default key for one action. Axis keys carry a scale (+1 or -1). */
struct UMBRELLAELLA_API FUmbrellaDefaultBinding
{
	EUmbrellaInputAction Action = EUmbrellaInputAction::Shoot;
	FKey Key;
	float Scale = 1.0f;
};

/** The default keyboard + mouse + gamepad bindings (GDD default controls). Plain data so tests read it. */
namespace UmbrellaInputBindings
{
	UMBRELLAELLA_API TArray<FUmbrellaDefaultBinding> BuildDefaults();

	/** IA_* asset-style name, e.g. IA_Shoot. */
	UMBRELLAELLA_API FName ActionName(EUmbrellaInputAction Action);

	/** True for the axis actions (Trim, MoveX); the rest are buttons. */
	UMBRELLAELLA_API bool IsAxisAction(EUmbrellaInputAction Action);
}
