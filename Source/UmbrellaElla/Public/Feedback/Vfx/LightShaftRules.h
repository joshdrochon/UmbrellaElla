#pragma once

#include "CoreMinimal.h"
#include "Umbrella/UmbrellaAction.h"

/**
 * The light and the shadow: a thin shaft of light falls into the abyss through Ella's position. While the umbrella is
 * open overhead its dark umbra hangs below her and the shaft stops at the canopy; when she folds it to descend, the
 * gap closes and the light passes through. Looks only: nothing here changes forces, health, targets or controls.
 */
namespace LightShaftRules
{
	/**
	 * A hairline of light (about 2 px at 1280 wide), never a bar: at 28 the sheet's cream paper read as a solid cream bar
	 * on the dark frame (lead 17:08; measured 150/255 at opacity 0.3, the sheet material ignores Opacity and Tint).
	 */
	static constexpr float ShaftWidth = 6.0f;
	/** Length of each shaft part (above and below Ella): longer than the view is tall. */
	static constexpr float ShaftLength = 2400.0f;
	static constexpr float UmbraWidth = 150.0f;
	static constexpr float UmbraLength = 420.0f;
	/** Seconds the umbra takes to open and to close. */
	static constexpr float OpenSeconds = 0.2f;
	static constexpr float CloseSeconds = 0.15f;
	/** The canopy sits this far above Ella's origin. */
	static constexpr float CanopyHeight = 70.0f;

	/** The umbrella is open overhead only while rising. Every falling state folds it. */
	UMBRELLAELLA_API bool IsUmbrellaOpen(EUmbrellaAction Action);

	/** Openness 0 (folded, light passes) to 1 (open, full umbra), moved toward its target over game time. */
	UMBRELLAELLA_API float StepOpenness(float Current, bool bOpen, float DeltaSeconds);

	UMBRELLAELLA_API float UmbraWidthAt(float Openness);

	/** How much of the shaft shows below Ella: all of it when folded, none under an open canopy. */
	UMBRELLAELLA_API float LightBelowAt(float Openness);

	/** Centres of the three parts for Ella's position (X and Z; depth comes from each part's layer). */
	UMBRELLAELLA_API FVector ShaftAboveCentre(const FVector& Ella);
	UMBRELLAELLA_API FVector ShaftBelowCentre(const FVector& Ella);
	UMBRELLAELLA_API FVector UmbraCentre(const FVector& Ella);
}
