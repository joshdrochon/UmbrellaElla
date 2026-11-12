#pragma once

#include "CoreMinimal.h"
#include "ArenaCameraTuning.generated.h"

/** Every number of the Arena module: default, units and clamps (lane e). End a shipped default with // bake: <feature ID>.<param>. */
USTRUCT()
struct UMBRELLAELLA_API FArenaCameraTuning
{
	GENERATED_BODY()

	/** Arena width in world units (1 unit = 1 cm), GDD SH1.0 section 5. */
	UPROPERTY(EditAnywhere, meta = (ClampMin = "1"))
	float ArenaWidth = 1920.0f;

	/** Arena height in world units. */
	UPROPERTY(EditAnywhere, meta = (ClampMin = "1"))
	float ArenaHeight = 1080.0f;

	/** Fixed play camera aspect ratio, 16:9 . */
	UPROPERTY(EditAnywhere, meta = (ClampMin = "0.1"))
	float CameraAspectRatio = 1.777778f;

	/** Camera distance from the play plane along Y (depth only; orthographic). */
	UPROPERTY(EditAnywhere, meta = (ClampMin = "1"))
	float CameraDistance = 1000.0f;

	/** Thickness of the invisible wall and ceiling boxes. */
	UPROPERTY(EditAnywhere, meta = (ClampMin = "1"))
	float WallThickness = 100.0f;

	/** Ella start, as a fraction of arena width from the left edge. */
	UPROPERTY(EditAnywhere, meta = (ClampMin = "0", ClampMax = "1"))
	float PlayerStartXFraction = 0.2f;

	/** Ella start, as a fraction of arena height from the bottom. */
	UPROPERTY(EditAnywhere, meta = (ClampMin = "0", ClampMax = "1"))
	float PlayerStartZFraction = 0.5f;

	/** Keeper anchor, as a fraction of arena width from the left edge. */
	UPROPERTY(EditAnywhere, meta = (ClampMin = "0", ClampMax = "1"))
	float KeeperAnchorXFraction = 0.75f;

	/** Keeper anchor, as a fraction of arena height from the bottom. */
	UPROPERTY(EditAnywhere, meta = (ClampMin = "0", ClampMax = "1"))
	float KeeperAnchorZFraction = 0.6f;

	/** Far background scroll speed, units per second. */
	UPROPERTY(EditAnywhere, meta = (ClampMin = "0"))
	float BackgroundFarSpeed = 20.0f;

	/** Near background scroll speed, units per second. */
	UPROPERTY(EditAnywhere, meta = (ClampMin = "0"))
	float BackgroundNearSpeed = 60.0f;
};
