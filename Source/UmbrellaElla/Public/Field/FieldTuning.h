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

	/** initial margin: fraction of arena height. // bake: CAM-06.margin_height_fraction */
	UPROPERTY(EditAnywhere, meta = (ClampMin = "0"))
	float ClearanceMarginHeightFraction = 0.03f;

	/** initial margin: fraction of the hurtbox diameter. // bake: CAM-06.margin_diameter_fraction */
	UPROPERTY(EditAnywhere, meta = (ClampMin = "0"))
	float ClearanceMarginDiameterFraction = 0.25f;

	/** entrance/exit height as a fraction of H. // bake: CAM-05.interface_height_fraction */
	UPROPERTY(EditAnywhere, meta = (ClampMin = "0", ClampMax = "1"))
	float InterfaceHeightFraction = 0.5f;

	/** vestibule length as a fraction of W. // bake: CAM-05.vestibule_fraction */
	UPROPERTY(EditAnywhere, meta = (ClampMin = "0", ClampMax = "1"))
	float VestibuleFraction = 0.2f;

	/** minimum vertical clearance as a fraction of H. // bake: CAM-05.min_clearance_fraction */
	UPROPERTY(EditAnywhere, meta = (ClampMin = "0", ClampMax = "1"))
	float MinClearanceHeightFraction = 0.3f;

	/** Chunk length in units. // bake: FLOW-24.chunk_length */
	UPROPERTY(EditAnywhere, meta = (ClampMin = "1"))
	float ChunkLength = 1920.0f;

	/** Chunks per Director's Cut route (nine-slot grammar). */
	UPROPERTY(EditAnywhere, meta = (ClampMin = "1"))
	int32 RouteSlotCount = 9;

	/** Chunks between refuges (a refuge follows every third chunk). */
	UPROPERTY(EditAnywhere, meta = (ClampMin = "1"))
	int32 SlotsPerCheckpoint = 3;

	/** Seed of the named fallback layout. */
	UPROPERTY(EditAnywhere)
	int32 FallbackSeed = 1001;

	/** Candidate attempts before the named verified fallback. // bake: HAZ-40.max_attempts */
	UPROPERTY(EditAnywhere, meta = (ClampMin = "1"))
	int32 MaxCandidateAttempts = 32;

	/** Refuge core length as a fraction of a chunk (not set by the GDD; adjustable). */
	UPROPERTY(EditAnywhere, meta = (ClampMin = "0"))
	float RefugeLengthFraction = 0.5f;

	/** new-attack cue target in seconds (proposed, not universal proof). // bake: CAM-08.cue_seconds */
	UPROPERTY(EditAnywhere, meta = (ClampMin = "0"))
	float AttackCueSeconds = 1.0f;

	/** camera lead as a fraction of view width, in the travel direction. */
	UPROPERTY(EditAnywhere, meta = (ClampMin = "0", ClampMax = "0.5"))
	float CameraLeadFraction = 0.25f;

	/** margin inside the view a hazard must clear to count as revealed, fraction of view width. */
	UPROPERTY(EditAnywhere, meta = (ClampMin = "0", ClampMax = "0.5"))
	float RevealEdgeFraction = 0.03f;

	/** Drawn wind field stand-in colours by what the current does (art replaces them; readability, not final look). */
	UPROPERTY(EditAnywhere, Category = "Readability")
	FLinearColor TransportFieldColour = FLinearColor(0.55f, 0.78f, 0.95f);

	UPROPERTY(EditAnywhere, Category = "Readability")
	FLinearColor DescentFieldColour = FLinearColor(0.62f, 0.52f, 0.90f);

	/** Lift / rescue / reacquisition currents. */
	UPROPERTY(EditAnywhere, Category = "Readability")
	FLinearColor LiftFieldColour = FLinearColor(0.55f, 0.92f, 0.62f);

	/** Leftward return / reset currents. */
	UPROPERTY(EditAnywhere, Category = "Readability")
	FLinearColor ReturnFieldColour = FLinearColor(0.98f, 0.80f, 0.45f);

	/** Depth scale of the drawn field plane (a thin card behind Ella). */
	UPROPERTY(EditAnywhere, Category = "Readability", meta = (ClampMin = "0"))
	float FieldDepthScale = 0.01f;
};
