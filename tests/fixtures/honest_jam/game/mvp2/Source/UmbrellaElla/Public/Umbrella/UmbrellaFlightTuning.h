#pragma once

#include "CoreMinimal.h"
#include "UmbrellaFlightTuning.generated.h"

/** The umbrella's tuning (pipeline/unreal/gameplay-code.md: FUmbrellaFlightTuning, not FUmbrellaTuning). MVP 2: UP_OPEN
 *  lift (GDD SH1.0 movement starts). Read with GetDefault<UUmbrellaTuning>()->Umbrella.AscentSpeed. */
USTRUCT()
struct FUmbrellaFlightTuning
{
	GENERATED_BODY()

	UPROPERTY(EditAnywhere, meta = (Units = "CentimetersPerSecond", ClampMin = "120", ClampMax = "550"))
	float AscentSpeed = 120.0f;   // bake: MOVE-21.rise_speed

	UPROPERTY(EditAnywhere, meta = (ToolTip = "cm/s^2", ClampMin = "400", ClampMax = "2600"))
	float FallSpeed = 330.0f;   // bake: MOVE-21.fall_speed
};
