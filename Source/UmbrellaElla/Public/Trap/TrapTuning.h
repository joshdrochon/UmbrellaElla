#pragma once

#include "CoreMinimal.h"
#include "TrapTuning.generated.h"

namespace TrapConst
{
	static constexpr float FullTurnDegrees = 360.0f;
	/** Engine cube edge length in units. */
	static constexpr float CubeSize = 100.0f;
}

/**
 * Every number of the Trap module (lane enemies): GDD SH1.0 baselines, adjustable. Gust length, gust speed, blade
 * count, spin and tooth size are not printed in the GDD: prototype starts, marked adjustable.
 * Not a member of UUmbrellaTuning yet (see docs/build/requests/enemies.md): read as FTrapTuning().
 */
USTRUCT()
struct UMBRELLAELLA_API FTrapTuning
{
	GENERATED_BODY()

	/** Physical hits deal this much health (ordinary trap-wide baseline). */
	UPROPERTY(EditAnywhere, Category = "Trap")
	float ContactDamage = 1.0f;

	/** Post-hit protection per victim, so a persistent overlap cannot repeat damage per frame. */
	UPROPERTY(EditAnywhere, Category = "Trap")
	float PostHitProtectionSeconds = 0.65f;

	UPROPERTY(EditAnywhere, Category = "AirMill")
	float RotorSweptRadius = 150.0f;

	UPROPERTY(EditAnywhere, Category = "AirMill")
	int32 BladeCount = 4;

	UPROPERTY(EditAnywhere, Category = "AirMill")
	float SpinDegreesPerSecond = 90.0f;

	/** Visible crank/tension warning, at least 1 s. */
	UPROPERTY(EditAnywhere, Category = "Shutter")
	float ShutterWarningSeconds = 1.0f;

	/** Closing and closed strike. */
	UPROPERTY(EditAnywhere, Category = "Shutter")
	float ShutterStrikeSeconds = 0.6f;

	/** Clearly open recovery, at least 1.4 s. */
	UPROPERTY(EditAnywhere, Category = "Shutter")
	float ShutterRecoverySeconds = 1.4f;

	/** Nozzle warning that locks one lane, at least 1 s. */
	UPROPERTY(EditAnywhere, Category = "Bellows")
	float BellowsWarningSeconds = 1.0f;

	/** Finite advancing gust. */
	UPROPERTY(EditAnywhere, Category = "Bellows")
	float BellowsGustSeconds = 1.0f;

	/** No-fire recovery, at least 1.5 s. */
	UPROPERTY(EditAnywhere, Category = "Bellows")
	float BellowsRecoverySeconds = 1.5f;

	/** Bounded push on a gust hit, units/s, toward safe catch space (down and left). */
	UPROPERTY(EditAnywhere, Category = "Bellows")
	float BellowsPushSpeed = 150.0f;

	UPROPERTY(EditAnywhere, Category = "RoofTeeth")
	FVector2D TeethSize = FVector2D(160.0, 40.0);

	/** Hit-box half depth (Y) and placeholder depth scale for trap actors. */
	UPROPERTY(EditAnywhere, Category = "Placeholder")
	float DepthHalfExtent = 50.0f;

	UPROPERTY(EditAnywhere, Category = "Placeholder")
	float PlaceholderDepthScale = 0.1f;
};
