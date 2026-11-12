#pragma once

#include "CoreMinimal.h"
#include "Subsystems/WorldSubsystem.h"
#include "UmbrellaBackdropSubsystem.generated.h"

namespace UmbrellaBackdropConst
{
	/** Layer width and height in world units (placeholder panels behind the play camera). */
	static constexpr float PanelWidth = 4800.0f;
	static constexpr float PanelHeight = 2400.0f;
	/** Thin depth so the panel is a flat card. */
	static constexpr float PanelThickness = 0.01f;
	/** Cube base size in engine units. */
	static constexpr float EngineCubeSize = 100.0f;
}

/**
 * Layered backdrop (sky, far skyline, near architecture) as non-colliding stand-in panels behind the play layer.
 * Art replaces the panels later; depth comes only from UmbrellaDrawOrder. Never touches collision or wind. Visuals lane.
 */
UCLASS()
class UMBRELLAELLA_API UUmbrellaBackdropSubsystem final : public UWorldSubsystem
{
	GENERATED_BODY()

public:
	virtual void PostInitialize() override;

	/** Build the layers (safe to call twice). Returns the number of layers now present. */
	int32 BuildLayers();

	int32 GetLayerCount() const { return Layers.Num(); }
	const TArray<TObjectPtr<AActor>>& GetLayers() const { return Layers; }

	/** Layer Y depths back to front. Pure. */
	static TArray<float> LayerDepths();

private:
	UPROPERTY()
	TArray<TObjectPtr<AActor>> Layers;
};
