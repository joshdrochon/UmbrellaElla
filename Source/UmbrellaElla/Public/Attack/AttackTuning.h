#pragma once

#include "CoreMinimal.h"
#include "AttackTuning.generated.h"

/** Every number of the Attack module: default, units and clamps (lane a). Units: GDD world units = Unreal cm. End a shipped default with // bake: <feature ID>.<param>. */
USTRUCT()
struct UMBRELLAELLA_API FAttackTuning
{
	GENERATED_BODY()

	/** Small Blasts cadence, shots/s. */
	UPROPERTY(Config, EditAnywhere, Category = "Attack", meta = (ClampMin = "0.1"))
	float SmallShotsPerSecond = 5.0f; // bake: COM-06.shots_per_s

	UPROPERTY(Config, EditAnywhere, Category = "Attack", meta = (ClampMin = "0"))
	float SmallDamage = 10.0f; // bake: COM-06.damage

	UPROPERTY(Config, EditAnywhere, Category = "Attack", meta = (ClampMin = "1"))
	float SmallSpeed = 700.0f; // bake: COM-06.speed

	UPROPERTY(Config, EditAnywhere, Category = "Attack", meta = (ClampMin = "1"))
	float SmallRange = 1500.0f; // bake: COM-06.range

	/** Small Blasts burst option: shots per trigger, 1 to SmallBurstMax. Default one (GDD Small Blasts row). */
	UPROPERTY(Config, EditAnywhere, Category = "Attack", meta = (ClampMin = "1"))
	int32 SmallBurstCount = 1;

	/** Largest burst the option allows (GDD: 1 to 5). */
	UPROPERTY(Config, EditAnywhere, Category = "Attack", meta = (ClampMin = "1"))
	int32 SmallBurstMax = 5;

	/** Seconds between the shots of a burst (GDD: 0.08). */
	UPROPERTY(Config, EditAnywhere, Category = "Attack", meta = (ClampMin = "0.01"))
	float SmallBurstSpacing = 0.08f;

	/** Streamed Blast damage ticks per second. */
	UPROPERTY(Config, EditAnywhere, Category = "Attack", meta = (ClampMin = "0.1"))
	float StreamTicksPerSecond = 10.0f; // bake: COM-07.ticks_per_s

	UPROPERTY(Config, EditAnywhere, Category = "Attack", meta = (ClampMin = "0"))
	float StreamTickDamage = 4.0f; // bake: COM-07.tick_damage

	/** How fast the beam grows from the muzzle, units/s. */
	UPROPERTY(Config, EditAnywhere, Category = "Attack", meta = (ClampMin = "1"))
	float StreamGrowthSpeed = 1200.0f; // bake: COM-07.growth_speed

	UPROPERTY(Config, EditAnywhere, Category = "Attack", meta = (ClampMin = "1"))
	float StreamMaxRange = 1400.0f; // bake: COM-07.max_range

	UPROPERTY(Config, EditAnywhere, Category = "Attack", meta = (ClampMin = "0"))
	float StreamWidth = 14.0f; // bake: COM-07.width

	/** Twin Stars: vertical gap between the two shots of a volley. */
	UPROPERTY(Config, EditAnywhere, Category = "Attack", meta = (ClampMin = "0"))
	float TwinSeparation = 44.0f; // bake: COM-08.separation

	UPROPERTY(Config, EditAnywhere, Category = "Attack", meta = (ClampMin = "0.1"))
	float TwinVolleysPerSecond = 5.0f; // bake: COM-08.volleys_per_s

	UPROPERTY(Config, EditAnywhere, Category = "Attack", meta = (ClampMin = "0"))
	float TwinDamage = 7.0f; // bake: COM-08.damage

	UPROPERTY(Config, EditAnywhere, Category = "Attack", meta = (ClampMin = "1"))
	float TwinSpeed = 700.0f; // bake: COM-08.speed

	UPROPERTY(Config, EditAnywhere, Category = "Attack", meta = (ClampMin = "1"))
	float TwinRange = 1500.0f; // bake: COM-08.range

	UPROPERTY(Config, EditAnywhere, Category = "Attack", meta = (ClampMin = "0.1"))
	float NeedleShotsPerSecond = 3.0f; // bake: COM-09.shots_per_s

	UPROPERTY(Config, EditAnywhere, Category = "Attack", meta = (ClampMin = "0"))
	float NeedleDamage = 14.0f; // bake: COM-09.damage

	UPROPERTY(Config, EditAnywhere, Category = "Attack", meta = (ClampMin = "1"))
	float NeedleSpeed = 1000.0f; // bake: COM-09.speed

	UPROPERTY(Config, EditAnywhere, Category = "Attack", meta = (ClampMin = "1"))
	float NeedleRange = 1700.0f; // bake: COM-09.range

	/** Needle size relative to a Small Blast. */
	UPROPERTY(Config, EditAnywhere, Category = "Attack", meta = (ClampMin = "0.1"))
	float NeedleSizeMultiplier = 0.7f; // bake: COM-09.size_multiplier

	/** Streamed Blast beam box half depth (Y, the projectile plane thickness), units. */
	UPROPERTY(Config, EditAnywhere, Category = "Attack", meta = (ClampMin = "0"))
	float StreamDepthHalfExtent = 12.0f;

	/** Player blast collision radius, units (fixed collider data, never read from art). */
	UPROPERTY(Config, EditAnywhere, Category = "Attack", meta = (ClampMin = "0"))
	float BlastRadius = 6.0f; // GDD fixture (D-new-smallblast-fixture)

	/** Fixed muzzle anchor relative to Ella's origin (X right, Z up). Stable: never read from the sprite. */
	UPROPERTY(Config, EditAnywhere, Category = "Attack")
	FVector MuzzleOffset = FVector(44.0, 0.0, 6.0); // GDD fixture +44/+6 at HeroSize 1 (D-new-smallblast-fixture)

	/** Director's Cut level that unlocks each spell (Small, Stream, Twin, Needle). */
	UPROPERTY(Config, EditAnywhere, Category = "Attack", meta = (ClampMin = "1"))
	int32 SmallUnlockLevel = 1;

	UPROPERTY(Config, EditAnywhere, Category = "Attack", meta = (ClampMin = "1"))
	int32 StreamUnlockLevel = 10;

	UPROPERTY(Config, EditAnywhere, Category = "Attack", meta = (ClampMin = "1"))
	int32 TwinUnlockLevel = 20;

	UPROPERTY(Config, EditAnywhere, Category = "Attack", meta = (ClampMin = "1"))
	int32 NeedleUnlockLevel = 30;

	/** Holding a spell key this long opens the wheel (flick selects at once). */
	UPROPERTY(Config, EditAnywhere, Category = "Attack", meta = (ClampMin = "0"))
	float WheelHoldSeconds = 0.3f;

	/** Small Blasts canopy cycle, presentation only: seconds the canopy shows snapped open and pulsing after an emission,
	 *  then seconds it closes and cocks back to folded-ready. Together under the 0.2 s shot interval, so it is ready again
	 *  before the next shot; it never delays or gates a shot. No GDD number (prototype default). */
	UPROPERTY(Config, EditAnywhere, Category = "Attack", meta = (ClampMin = "0.01"))
	float SmallCanopyOpenSeconds = 0.06f;

	UPROPERTY(Config, EditAnywhere, Category = "Attack", meta = (ClampMin = "0.01"))
	float SmallCanopyCockSeconds = 0.08f;

	/** Streamed Blast stand-in strands: how many canopy-interior strands run beside the dark beam body. */
	UPROPERTY(Config, EditAnywhere, Category = "Attack", meta = (ClampMin = "2", ClampMax = "8"))
	int32 StreamStrandCount = 4;

	/** Strand spread at the muzzle (half height, units: the canopy interior) and the share of the beam length over
	 *  which they converge onto the body edge. Looks only: the beam box stays the hitbox. */
	UPROPERTY(Config, EditAnywhere, Category = "Attack", meta = (ClampMin = "0"))
	float StreamStrandCanopySpread = 28.0f;

	UPROPERTY(Config, EditAnywhere, Category = "Attack", meta = (ClampMin = "0.05", ClampMax = "1.0"))
	float StreamStrandConvergeShare = 0.35f;

	/** Strand thickness (units). */
	UPROPERTY(Config, EditAnywhere, Category = "Attack", meta = (ClampMin = "0.5"))
	float StreamStrandThickness = 3.0f;

	/** The beam body is dark; the strands around it carry the light. */
	UPROPERTY(Config, EditAnywhere, Category = "Attack")
	FLinearColor StreamBodyColor = FLinearColor(0.05f, 0.06f, 0.09f);

	UPROPERTY(Config, EditAnywhere, Category = "Attack")
	FLinearColor StreamStrandColor = FLinearColor(0.55f, 0.85f, 1.0f);
};
