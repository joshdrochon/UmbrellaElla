#pragma once

#include "CoreMinimal.h"
#include "GameFramework/HUD.h"
#include "UI/ClockHudModel.h"
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

	/** Absorbed energy on its way into the clock (one mote per real heal). */
	const TArray<FClockEnergyMote>& GetEnergyMotes() const { return EnergyMotes; }

	/** Motes that reached the clock so far. */
	int32 GetEnergyArrived() const { return EnergyArrived; }

	/** Test seam: advance the energy flow without drawing. */
	void StepEnergyFlow(float DeltaSeconds);

protected:
	virtual void BeginPlay() override;
	virtual void EndPlay(const EEndPlayReason::Type Reason) override;

private:
	void OnHealthChanged(const struct FUmbrellaEvent& Event);
	FVector2D EllaScreenPoint() const;
	void DrawDial(const FClockLayout& Layout, const struct FHudTuning& Tuning);
	void DrawEnergy(const FClockLayout& Layout, const struct FHudTuning& Tuning);
	void DrawSpellWheel(const FClockLayout& Layout, const struct FHudTuning& Tuning, class UFont* Font);
	void DrawHandBlade(const FVector2D& Center, const FVector2D& Tip, float Width, const FLinearColor& Color);
	void DrawCircleOutline(const FVector2D& Center, float Radius, int32 Segments, float Thickness, const FLinearColor& Color);
	void DrawArc(const FVector2D& Center, float Radius, float FromDegrees, float ToDegrees, int32 Segments, float Thickness, const FLinearColor& Color);

	float DrawnHealthDegrees = -1.0f;
	float DrawnLifeDegrees = -1.0f;
	TArray<FClockEnergyMote> EnergyMotes;
	int32 EnergyArrived = 0;
	FClockLayout LastLayout;
	FDelegateHandle HealthHandle;
};
