#pragma once

#include "CoreMinimal.h"
#include "Attack/SpellRules.h"
#include "SpellPresentation.generated.h"

struct FAttackTuning;

/** Which body family Ella's falling attack uses. Presentation only: it never changes damage, aim or timing. */
UENUM()
enum class EUmbrellaBodyPose : uint8
{
	RegularFall,
	ShoulderFall
};

/**
 * The Small Blasts canopy cycle: folded-ready, snapped open with a pulse on an actual emission, then closing and
 * cocking back to ready. Only Small Blasts fold; the other spells hold the canopy open and steady (Steady).
 */
UENUM()
enum class EUmbrellaCanopyPhase : uint8
{
	Steady,
	FoldedReady,
	SnapOpen,
	Cock
};

struct FCanopyCycleState
{
	EUmbrellaCanopyPhase Phase = EUmbrellaCanopyPhase::FoldedReady;
	float PhaseLeft = 0.0f;
	/** Emissions seen since the last read (each one restarts the cycle). */
	int32 Pulses = 0;
};

/** One entry of the spell wheel / locked-weapon display. */
struct FSpellWheelEntry
{
	EUmbrellaSpell Spell = EUmbrellaSpell::SmallBlasts;
	bool bLocked = false;
	/** The Director's Cut level that unlocks it (1/10/20/30 by default). */
	int32 UnlockLevel = 1;
	/** What the wheel shows under the spell name: the unlock level while locked, empty once unlocked. */
	FString LockLabel;
};

/** One stand-in strand of the Streamed Blast: start and end in beam space (X forward from the muzzle, Z up). */
struct FBeamStrand
{
	FVector2D Start = FVector2D::ZeroVector;
	FVector2D Converge = FVector2D::ZeroVector;
	FVector2D End = FVector2D::ZeroVector;
};

/** Plain presentation rules of the four spells. Tests call them; the emitter, beam and HUD draw from them. */
namespace SpellPresentationRules
{
	/** RegularFall serves Small/Twin/Needle; ShoulderFall (shoulder-braced) serves the Streamed Blast. */
	UMBRELLAELLA_API EUmbrellaBodyPose BodyPoseFor(EUmbrellaSpell Spell);

	/** True only for Small Blasts: the one spell that folds, snaps open and cocks. */
	UMBRELLAELLA_API bool HasCanopyCycle(EUmbrellaSpell Spell);

	/** Phase to show while Spell is equipped and nothing has been emitted. */
	UMBRELLAELLA_API FCanopyCycleState RestingCycle(EUmbrellaSpell Spell);

	/** An actual emission of Spell: Small snaps open (and pulses); others stay steady. */
	UMBRELLAELLA_API void OnEmission(FCanopyCycleState& Cycle, EUmbrellaSpell Spell, const FAttackTuning& Tuning);

	/** Advance the cycle by time alone: SnapOpen -> Cock -> FoldedReady. Never starts a cycle by itself. */
	UMBRELLAELLA_API void Step(FCanopyCycleState& Cycle, float DeltaSeconds, const FAttackTuning& Tuning);

	/** The spell's name as the wheel shows it. */
	UMBRELLAELLA_API FString DisplayName(EUmbrellaSpell Spell);

	/** The four wheel entries in key order, with their lock state and unlock-level label for this mode and level. */
	UMBRELLAELLA_API TArray<FSpellWheelEntry> WheelEntries(EUmbrellaPlayMode Mode, int32 DirectorLevel, const FAttackTuning& Tuning);

	/** The stand-in strands for a beam of Length and full Width: they leave the canopy interior spread out and converge
	 *  forward onto the edges of the dark body, half above and half below it. */
	UMBRELLAELLA_API TArray<FBeamStrand> BeamStrands(float Length, float Width, const FAttackTuning& Tuning);
}
