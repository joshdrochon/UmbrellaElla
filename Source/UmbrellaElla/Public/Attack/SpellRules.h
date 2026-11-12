#pragma once

#include "CoreMinimal.h"
#include "Core/UmbrellaPlayMode.h"
#include "Projectile/UmbrellaShotSpec.h"
#include "SpellRules.generated.h"

struct FAttackTuning;

/** The four weapon families, exactly. There is no fifth. Order = keys 1..4 = right-stick up/right/down/left. */
UENUM()
enum class EUmbrellaSpell : uint8
{
	SmallBlasts,
	StreamedBlast,
	TwinStars,
	Needle,
	Count UMETA(Hidden)
};

/** Plain numbers of one spell, read from tuning. */
struct UMBRELLAELLA_API FSpellProfile
{
	float ShotsPerSecond = 0.0f;
	float Damage = 0.0f;
	float Speed = 0.0f;
	float Range = 0.0f;
	float RadiusScale = 1.0f;
	/** Shots per volley (Twin Stars = 2). */
	int32 ShotsPerVolley = 1;
	/** Vertical gap between the shots of a volley. */
	float Separation = 0.0f;
};

/** Plain rule functions for spells: availability, cycling, and the shots a spell fires. */
namespace SpellRules
{
	static constexpr int32 SpellCount = static_cast<int32>(EUmbrellaSpell::Count);

	UMBRELLAELLA_API int32 UnlockLevel(EUmbrellaSpell Spell, const FAttackTuning& Tuning);

	/** Start Game: only Small Blasts. Director's Cut: a spell is available once the level reaches its unlock level. */
	UMBRELLAELLA_API bool IsAvailable(EUmbrellaSpell Spell, EUmbrellaPlayMode Mode, int32 DirectorLevel, const FAttackTuning& Tuning);

	/** Next available spell in Direction (+1 / -1), wrapping; Current when it is the only one. */
	UMBRELLAELLA_API EUmbrellaSpell Cycle(EUmbrellaSpell Current, int32 Direction, EUmbrellaPlayMode Mode, int32 DirectorLevel, const FAttackTuning& Tuning);

	UMBRELLAELLA_API FSpellProfile GetProfile(EUmbrellaSpell Spell, const FAttackTuning& Tuning);

	/** The shots one volley of a spell fires from Muzzle (Streamed Blast: one damage pulse per tick). All go to +X. */
	UMBRELLAELLA_API TArray<FUmbrellaShotSpec> BuildVolley(EUmbrellaSpell Spell, const FVector& Muzzle, const FAttackTuning& Tuning);

	/** Streamed Blast beam length after being held HeldSeconds: grows at the growth speed up to the maximum range. */
	UMBRELLAELLA_API float StreamLength(float HeldSeconds, const FAttackTuning& Tuning);

	UMBRELLAELLA_API FName SpellName(EUmbrellaSpell Spell);
}
