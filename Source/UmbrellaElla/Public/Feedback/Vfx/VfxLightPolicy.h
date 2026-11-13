#pragma once

#include "CoreMinimal.h"

struct FVfxArtRow;

/** What one effect adds to light nearby surfaces. Both parts are local, belong to the effect and leave with it. */
struct FVfxLightPlan
{
	/** A small unshadowed point light: lights surfaces that use a lit material (stand-ins, lit sprites). */
	bool bPointLight = false;
	/** An additive soft overlay just in front of the characters and scenery: lights unlit sprites without changing their material. */
	bool bSpillOverlay = false;
	float Intensity = 0.0f;
	float Radius = 0.0f;
	float SpillSize = 0.0f;
	float SpillOpacity = 0.0f;
	FLinearColor Colour = FLinearColor::Black;
};

/**
 * Nearby-surface illumination: the method this build uses. Sprites stay unlit (the art import policy is unchanged);
 * an effect that carries light adds a registered additive overlay at its own position, plus a point light for lit
 * surfaces. The choice is recorded as an open decision in docs/build/requests/artfx.md.
 */
namespace VfxLightPolicy
{
	static constexpr float PointIntensity = 3000.0f;
	/** Light reach as a multiple of the effect size, capped so the influence stays local. */
	static constexpr float RadiusPerSize = 3.0f;
	static constexpr float MaxRadius = 420.0f;
	/** Overlay size as a multiple of the effect size. */
	static constexpr float SpillPerSize = 2.5f;
	static constexpr float SpillOpacity = 0.35f;
	/** Reduced-flash mode keeps the light but dims it to this fraction. */
	static constexpr float ReducedFraction = 0.4f;
	/** The overlay sits this far in front of Ella's layer: above characters and scenery, below shots and effects. */
	static constexpr float SpillDepthOffset = 10.0f;

	/** The light an effect throws. Nothing when the effect carries no light or illumination is switched off. */
	UMBRELLAELLA_API FVfxLightPlan PlanFor(const FVfxArtRow& Row, bool bIlluminationOn, bool bReducedFlash);

	/** Brightness over the effect's life, 1 to 0: a one-shot's light fades out with it, so surfaces return to normal. */
	UMBRELLAELLA_API float FadeAt(const FVfxArtRow& Row, float Elapsed);

	/** Depth (Y) of the overlay. */
	UMBRELLAELLA_API float SpillLayerY();
}
