#pragma once

#include "CoreMinimal.h"
#include "HudTuning.generated.h"

/** Every number of the UI module: default, units and clamps (lane c). End a shipped default with // bake: <feature ID>.<param>. */
USTRUCT()
struct UMBRELLAELLA_API FHudTuning
{
	GENERATED_BODY()

	/** The play view is 16:9; the clock lives inside it (units: width, height). */
	UPROPERTY(Config, EditAnywhere, meta = (ClampMin = "1.0"))
	float ViewAspectWidth = 16.0f;

	UPROPERTY(Config, EditAnywhere, meta = (ClampMin = "1.0"))
	float ViewAspectHeight = 9.0f;

	/** Gap from the view's top-left corner to the clock, as a fraction of view height. */
	UPROPERTY(Config, EditAnywhere, meta = (ClampMin = "0.0", ClampMax = "0.2"))
	float MarginFraction = 0.03f;

	/** Clock radius as a fraction of view height. */
	UPROPERTY(Config, EditAnywhere, meta = (ClampMin = "0.02", ClampMax = "0.3"))
	float ClockRadiusFraction = 0.09f;

	/** Smallest text height on screen (units: px), at 720p and above. */
	UPROPERTY(Config, EditAnywhere, meta = (ClampMin = "18.0"))
	float MinTextPx = 18.0f;

	/** View height at which MinTextPx applies unscaled (units: px). */
	UPROPERTY(Config, EditAnywhere, meta = (ClampMin = "360.0"))
	float TextReferenceHeightPx = 720.0f;

	/** Health hand length, fraction of the radius. The life hand is shorter, so the two differ without color. */
	UPROPERTY(Config, EditAnywhere, meta = (ClampMin = "0.1", ClampMax = "1.0"))
	float HealthHandLength = 0.85f;

	UPROPERTY(Config, EditAnywhere, meta = (ClampMin = "0.1", ClampMax = "1.0"))
	float LifeHandLength = 0.55f;

	/** Hand thickness (units: px). The life hand is thicker and ends in a block. */
	UPROPERTY(Config, EditAnywhere, meta = (ClampMin = "1.0"))
	float HealthHandThickness = 3.0f;

	UPROPERTY(Config, EditAnywhere, meta = (ClampMin = "1.0"))
	float LifeHandThickness = 7.0f;

	/** Life hand with all lives: IX (270 degrees clockwise from XII). It runs on to XII (360) when the last life is gone.
	 *  Prototype default: the exact positions are OPEN in the GDD (docs/build/requests/health.md). */
	UPROPERTY(Config, EditAnywhere, meta = (ClampMin = "91.0", ClampMax = "359.0"))
	float LifeHandFullDegrees = 270.0f;

	/** How fast the drawn hands follow the real value (units: degrees/s). Presentation only; gameplay is immediate. */
	UPROPERTY(Config, EditAnywhere, meta = (ClampMin = "30.0"))
	float HandSpeedDegreesPerSecond = 360.0f;

	/** Segments of the rim and the gold arc. */
	UPROPERTY(Config, EditAnywhere, meta = (ClampMin = "12", ClampMax = "128"))
	int32 RimSegments = 48;

	/** Rim thickness (units: px). */
	UPROPERTY(Config, EditAnywhere, meta = (ClampMin = "1.0"))
	float RimThickness = 4.0f;

	/** Gold arc thickness (units: px). */
	UPROPERTY(Config, EditAnywhere, meta = (ClampMin = "1.0"))
	float ArcThickness = 5.0f;

	UPROPERTY(Config, EditAnywhere)
	FLinearColor FaceColor = FLinearColor(0.05f, 0.04f, 0.04f, 0.55f);

	UPROPERTY(Config, EditAnywhere)
	FLinearColor RimColor = FLinearColor(0.72f, 0.45f, 0.15f, 1.0f);

	UPROPERTY(Config, EditAnywhere)
	FLinearColor ArcColor = FLinearColor(1.0f, 0.78f, 0.25f, 1.0f);

	UPROPERTY(Config, EditAnywhere)
	FLinearColor HealthHandColor = FLinearColor(1.0f, 0.85f, 0.35f, 1.0f);

	UPROPERTY(Config, EditAnywhere)
	FLinearColor LifeHandColor = FLinearColor(0.95f, 0.95f, 0.95f, 1.0f);

	UPROPERTY(Config, EditAnywhere)
	FLinearColor NumeralColor = FLinearColor(0.95f, 0.85f, 0.65f, 1.0f);
};
