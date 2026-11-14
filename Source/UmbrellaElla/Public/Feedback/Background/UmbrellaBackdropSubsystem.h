#pragma once

#include "CoreMinimal.h"
#include "Subsystems/WorldSubsystem.h"
#include "UmbrellaBackdropSubsystem.generated.h"

class UTexture2D;
enum class EArtSlotDraw : uint8;

namespace UmbrellaBackdropConst
{
	/** Layer width and height in world units (placeholder panels behind the play camera). */
	static constexpr float PanelWidth = 4800.0f;
	static constexpr float PanelHeight = 2400.0f;
	/** Thin depth so the panel is a flat card. */
	static constexpr float PanelThickness = 0.01f;
	/** Unlit stand-in colours, darker the farther back, so gameplay reads in front. */
	static const FLinearColor SkyStandInColor(0.20f, 0.19f, 0.17f, 1.0f);
	static const FLinearColor FarLandStandInColor(0.16f, 0.15f, 0.14f, 1.0f);
	static const FLinearColor NearStandInColor(0.12f, 0.11f, 0.10f, 1.0f);
	/** Cube base size in engine units. */
	static constexpr float EngineCubeSize = 100.0f;
	/**
	 * Widest half-view (world units) the backdrop must cover around the camera. Measured on the DC route (dcseamless, Nov 13):
	 * the camera margin and title band widen the ortho view to 2255 (half 1128); 1300 keeps a margin over that.
	 */
	static constexpr float MaxViewHalfWidth = 1300.0f;
	/**
	 * How far (world units) a layer panel may slide from the camera before its edge would show: half the panel minus the
	 * widest half-view. Layers no longer wrap (the old 1200-unit wrap made each layer jump a quarter picture in one frame,
	 * so the route showed the same island and arch again and again); each picture is crossed once, start to Keeper.
	 */
	static constexpr float SlideHeadroom = PanelWidth * 0.5f - MaxViewHalfWidth;
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

	/** Camera X range the backdrop is built for: the route start to the right edge of the Keeper fight frame. Pure. */
	static float RouteCameraMinX();
	static float RouteCameraMaxX();

	/**
	 * Parallax a layer really scrolls at: its spec parallax scaled down (same factor for every layer, so their depth order
	 * and ratios stay) until the fastest layer crosses its picture once over the whole camera range without an edge showing. Pure.
	 */
	static float EffectiveParallax(float Parallax);

	/** Signed X offset of a layer panel from the camera: continuous in CameraX, never beyond +-SlideHeadroom. Pure. */
	static float LayerOffset(float CameraX, float Parallax);

	/** World X a layer panel sits at for a camera X. Pure. */
	static float LayerXForCamera(float CameraX, float Parallax);

	/** Move every layer to follow the camera X with parallax (also what Tick does). Emits nothing; no collision, no wind. */
	void ScrollTo(float CameraX);

	virtual void Tick(float DeltaTime) override;
	virtual TStatId GetStatId() const override;
	virtual bool IsTickableInEditor() const override { return false; }

	/** Art slot id of a layer ("bg-layer:Sky"). Pure. */
	static FString LayerVisualId(FName LayerName);

	/** Draw layer Index with Texture (null = load the layer's slot asset). Anything but Drawn keeps the stand-in. */
	EArtSlotDraw ApplyLayerArt(int32 Index, UTexture2D* Texture);

	/** True when the layer shows art, not the stand-in panel. */
	bool IsLayerDrawnWithArt(int32 Index) const;

	/** World-space (X, Z) box a layer panel covers when the camera is at CameraX. Pure; independent of the mesh, so art does not change it. */
	static FBox2D LayerFootprint(float CameraX, float Parallax);

	/** Camera X at the middle of route stage Slot (0..8): the span the LevelDirector gives that stage. Pure. */
	static float StageCameraX(int32 Slot);

	/** True when the built layers together cover the whole camera view (width ArenaWidth, height 0..ArenaHeight) with the camera at the middle of route stage Slot. */
	bool IsRouteStageCovered(int32 Slot) const;

	/** Number of route stages (of RouteSlotCount) the backdrop covers. Route-stage backdrop coverage. */
	int32 CountCoveredStages() const;

	/**
	 * Hide the arena's flat stand-in background planes (BackgroundFar/Near) once a backdrop layer draws art: they sat at the
	 * backdrop's own depths as darkened 3840 x 1080 boxes and showed as hard-edged "screens" across the route. Returns how many
	 * planes are hidden now.
	 */
	int32 HideArenaStandIns();

	/** Specs parallel to GetLayers(). */
	const TArray<FBackdropLayerSpec>& GetBuiltSpecs() const { return BuiltSpecs; }

private:
	UPROPERTY()
	TArray<TObjectPtr<AActor>> Layers;
	TArray<FBackdropLayerSpec> BuiltSpecs;
};
