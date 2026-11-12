#pragma once

#include "CoreMinimal.h"
#include "GameFramework/HUD.h"
#include "UmbrellaHUD.generated.h"

/**
 * Gameplay HUD host: the clock HUD with health and life hands. Lane c.
 * One clock, two hands, no other HUD element. It only reads health; it never changes it.
 */
UCLASS()
class UMBRELLAELLA_API AUmbrellaHUD : public AHUD
{
	GENERATED_BODY()

public:
	virtual void DrawHUD() override;

	/** Hand angles as drawn this frame (they follow the real values at a capped speed). */
	float GetDrawnHealthDegrees() const { return DrawnHealthDegrees; }
	float GetDrawnLifeDegrees() const { return DrawnLifeDegrees; }

private:
	void DrawCircleOutline(const FVector2D& Center, float Radius, int32 Segments, float Thickness, const FLinearColor& Color);
	void DrawArc(const FVector2D& Center, float Radius, float FromDegrees, float ToDegrees, int32 Segments, float Thickness, const FLinearColor& Color);

	float DrawnHealthDegrees = -1.0f;
	float DrawnLifeDegrees = -1.0f;
};
