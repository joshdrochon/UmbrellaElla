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
	/** Seconds-free loop: a layer wraps its parallax offset at this period (world units), so it never runs out. */
	static constexpr float LoopPeriod = 1200.0f;
	/** Small Y gap between layers that share one DrawOrder depth, so panels never z-fight. */
	static constexpr float SameDepthStep = 5.0f;
	/** Parallax: 0 = fixed to the camera (sky), 1 = fixed to the world. */
	static constexpr float SkyParallax = 0.05f;
	static constexpr float FarParallax = 0.2f;
	static constexpr float NearParallax = 0.5f;
	static constexpr float AssemblyParallax = 0.6f;
}

/** One backdrop layer: what it shows, where it sits, how it scrolls, and the flag that gates it. */
struct FBackdropLayerSpec
{
	FName Name;
	float Depth = 0.0f;
	float Parallax = 0.0f;
};

/**
 * Layered backdrop (sky, far skyline, near architecture) as non-colliding stand-in panels behind the play layer.
 * Art replaces the panels later; depth comes only from UmbrellaDrawOrder. Never touches collision or wind. Visuals lane.
 */
UCLASS()
class UMBRELLAELLA_API UUmbrellaBackdropSubsystem final : public UTickableWorldSubsystem
{
	GENERATED_BODY()

public:
	/** Game and PIE worlds only: an editor world would get the panels saved into the .umap. */
	virtual bool ShouldCreateSubsystem(UObject* Outer) const override;
	virtual void PostInitialize() override;

	/** Build the layers (safe to call twice). Returns the number of layers now present. */
	int32 BuildLayers();

	int32 GetLayerCount() const { return Layers.Num(); }
	const TArray<TObjectPtr<AActor>>& GetLayers() const { return Layers; }

	/** Layer Y depths back to front (enabled layers only). Pure. */
	static TArray<float> LayerDepths();

	/** True when the flag behind a layer (by name) is on. */
	static bool IsLayerEnabled(FName LayerName);

	/** Every layer in the set, back to front: sky, far land, near architecture, clock/water/wind, base. Pure. */
	static TArray<FBackdropLayerSpec> LayerSpecs();

	/** X offset (from the camera) of a looping layer: wraps in [0, LoopPeriod) so it loops forever. Pure. */
	static float LoopOffset(float CameraX, float Parallax);

	/** World X a layer panel sits at for a camera X. Pure. */
	static float LayerXForCamera(float CameraX, float Parallax);

	/** Move every layer to follow the camera X with parallax (also what Tick does). Emits nothing; no collision, no wind. */
	void ScrollTo(float CameraX);

	virtual void Tick(float DeltaTime) override;
	virtual TStatId GetStatId() const override;
	virtual bool IsTickableInEditor() const override { return false; }

	/** Specs parallel to GetLayers(). */
	const TArray<FBackdropLayerSpec>& GetBuiltSpecs() const { return BuiltSpecs; }

private:
	UPROPERTY()
	TArray<TObjectPtr<AActor>> Layers;
	TArray<FBackdropLayerSpec> BuiltSpecs;
};
