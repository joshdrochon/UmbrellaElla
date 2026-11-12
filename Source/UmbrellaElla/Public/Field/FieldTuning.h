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
};
