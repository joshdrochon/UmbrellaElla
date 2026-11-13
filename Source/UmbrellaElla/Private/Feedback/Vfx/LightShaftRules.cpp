#include "Feedback/Vfx/LightShaftRules.h"

bool LightShaftRules::IsUmbrellaOpen(EUmbrellaAction Action)
{
	return Action == EUmbrellaAction::Rise;
}

float LightShaftRules::StepOpenness(float Current, bool bOpen, float DeltaSeconds)
{
	const float Rate = 1.0f / (bOpen ? OpenSeconds : CloseSeconds);
	const float Moved = Current + (bOpen ? Rate : -Rate) * FMath::Max(DeltaSeconds, 0.0f);
	return FMath::Clamp(Moved, 0.0f, 1.0f);
}

float LightShaftRules::UmbraWidthAt(float Openness)
{
	return UmbraWidth * FMath::Clamp(Openness, 0.0f, 1.0f);
}

float LightShaftRules::LightBelowAt(float Openness)
{
	return 1.0f - FMath::Clamp(Openness, 0.0f, 1.0f);
}

FVector LightShaftRules::ShaftAboveCentre(const FVector& Ella)
{
	return FVector(Ella.X, 0.0, Ella.Z + CanopyHeight + ShaftLength * 0.5f);
}

FVector LightShaftRules::ShaftBelowCentre(const FVector& Ella)
{
	return FVector(Ella.X, 0.0, Ella.Z + CanopyHeight - ShaftLength * 0.5f);
}

FVector LightShaftRules::UmbraCentre(const FVector& Ella)
{
	return FVector(Ella.X, 0.0, Ella.Z + CanopyHeight - UmbraLength * 0.5f);
}
