#pragma once

#include "CoreMinimal.h"
#include "FieldTuning.generated.h"

/** Every number of the Field module: default, units and clamps (lane e). End a shipped default with // bake: <feature ID>.<param>. */
USTRUCT()
struct UMBRELLAELLA_API FFieldTuning
{
	GENERATED_BODY()

	/** Default wind current force in units per second (the Motor applies it; currents never deal damage). */
	UPROPERTY(EditAnywhere, meta = (ClampMin = "0"))
	float DefaultWindForce = 300.0f;

	/** CAM-06 initial margin: fraction of arena height. // bake: CAM-06.margin_height_fraction */
	UPROPERTY(EditAnywhere, meta = (ClampMin = "0"))
	float ClearanceMarginHeightFraction = 0.03f;

	/** CAM-06 initial margin: fraction of the hurtbox diameter. // bake: CAM-06.margin_diameter_fraction */
	UPROPERTY(EditAnywhere, meta = (ClampMin = "0"))
	float ClearanceMarginDiameterFraction = 0.25f;

	/** CAM-05 entrance/exit height as a fraction of H. // bake: CAM-05.interface_height_fraction */
	UPROPERTY(EditAnywhere, meta = (ClampMin = "0", ClampMax = "1"))
	float InterfaceHeightFraction = 0.5f;

	/** CAM-05 vestibule length as a fraction of W. // bake: CAM-05.vestibule_fraction */
	UPROPERTY(EditAnywhere, meta = (ClampMin = "0", ClampMax = "1"))
	float VestibuleFraction = 0.2f;

	/** CAM-05 minimum vertical clearance as a fraction of H. // bake: CAM-05.min_clearance_fraction */
	UPROPERTY(EditAnywhere, meta = (ClampMin = "0", ClampMax = "1"))
	float MinClearanceHeightFraction = 0.3f;

	/** Chunk length in units. // bake: FLOW-24.chunk_length */
	UPROPERTY(EditAnywhere, meta = (ClampMin = "1"))
	float ChunkLength = 1920.0f;

	/** Chunks per Director's Cut route (HAZ-37 nine-slot grammar). */
	UPROPERTY(EditAnywhere, meta = (ClampMin = "1"))
	int32 RouteSlotCount = 9;

	/** Candidate attempts before the named verified fallback. // bake: HAZ-40.max_attempts */
	UPROPERTY(EditAnywhere, meta = (ClampMin = "1"))
	int32 MaxCandidateAttempts = 32;

	/** Refuge core length as a fraction of a chunk (not set by the GDD; adjustable). */
	UPROPERTY(EditAnywhere, meta = (ClampMin = "0"))
	float RefugeLengthFraction = 0.5f;

	/** CAM-08 new-attack cue target in seconds (proposed, not universal proof). // bake: CAM-08.cue_seconds */
	UPROPERTY(EditAnywhere, meta = (ClampMin = "0"))
	float AttackCueSeconds = 1.0f;

	/** CAM-08 camera lead as a fraction of view width, in the travel direction. */
	UPROPERTY(EditAnywhere, meta = (ClampMin = "0", ClampMax = "0.5"))
	float CameraLeadFraction = 0.25f;

	/** CAM-08 margin inside the view a hazard must clear to count as revealed, fraction of view width. */
	UPROPERTY(EditAnywhere, meta = (ClampMin = "0", ClampMax = "0.5"))
	float RevealEdgeFraction = 0.03f;
};
