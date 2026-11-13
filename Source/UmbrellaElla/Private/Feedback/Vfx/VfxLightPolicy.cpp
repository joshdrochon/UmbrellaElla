#include "Feedback/Vfx/VfxLightPolicy.h"
#include "Core/UmbrellaDrawOrder.h"
#include "Feedback/Vfx/VfxCatalog.h"

FVfxLightPlan VfxLightPolicy::PlanFor(const FVfxArtRow& Row, bool bIlluminationOn, bool bReducedFlash)
{
	FVfxLightPlan Plan;
	if (!Row.bLit || !bIlluminationOn)
	{
		return Plan;
	}
	const float Dim = (bReducedFlash && Row.bFlashing) ? ReducedFraction : 1.0f;
	Plan.bPointLight = true;
	Plan.bSpillOverlay = true;
	Plan.Intensity = PointIntensity * Dim;
	Plan.Radius = FMath::Min(Row.Size * RadiusPerSize, MaxRadius);
	Plan.SpillSize = FMath::Min(Row.Size * SpillPerSize, MaxRadius * 2.0f);
	Plan.SpillOpacity = SpillOpacity * Dim;
	Plan.Colour = VfxCatalog::LightColour(Row);
	return Plan;
}

float VfxLightPolicy::FadeAt(const FVfxArtRow& Row, float Elapsed)
{
	if (Row.bLoop)
	{
		return 1.0f;
	}
	const float Life = VfxCatalog::Duration(Row);
	return Life > 0.0f ? FMath::Clamp(1.0f - Elapsed / Life, 0.0f, 1.0f) : 0.0f;
}

float VfxLightPolicy::SpillLayerY()
{
	return UmbrellaDrawOrder::EllaY + SpillDepthOffset;
}
