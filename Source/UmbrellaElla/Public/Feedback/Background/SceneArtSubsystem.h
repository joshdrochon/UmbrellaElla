#pragma once

#include "CoreMinimal.h"
#include "Subsystems/WorldSubsystem.h"
#include "SceneArtSubsystem.generated.h"

class UStaticMeshComponent;
class UTexture2D;
enum class EArtSlotDraw : uint8;

namespace UmbrellaSceneArtConst
{
	/** Depth steps (Y units) between the scene pictures and the stand-in backdrop layers they sit among. */
	static constexpr float AtmosphereStep = 2.0f;
	static constexpr float LandStep = 10.0f;
	static constexpr float WaterStep = 15.0f;
	static constexpr float ClocksStep = 10.0f;
	static constexpr float StartEndStep = 15.0f;
	/**
	 * Route start/end pictures are this much larger than the arena view, so the widest camera margin (visualqa: HeroSize
	 * 1.3, hitbox 0.75 shows about 7% more) never opens a strip of another backdrop at their edges.
	 */
	static constexpr float RouteEndFill = 1.08f;
	/** Frame sits in front of everything the camera sees; parallax 0 keeps it on the camera. */
	static constexpr float FrameLift = 0.0f;
}

/** How a scene picture is placed: fixed to the camera or scrolling as a parallax layer, or pinned to the route start or end. */
enum class ESceneArtAnchor : uint8
{
	Layer,
	View,
	RouteStart,
	RouteEnd
};

/** One scene picture: its slot, depth, parallax and how it is placed. */
struct FSceneArtSpec
{
	FName Visual;
	float Depth = 0.0f;
	float Parallax = 0.0f;
	ESceneArtAnchor Anchor = ESceneArtAnchor::Layer;
};

/**
 * Draws the scene slots that have no stand-in panel: bg:atmosphere, bg:land, bg:water, bg:clocks, bg:start-end and
 * scene:gameplay-frame. A picture exists only when its asset does, so the stand-in backdrop stays as the fallback. Pictures
 * share the backdrop's panel size and parallax; the frame and the start and end pictures are one view big. No collision, no wind. Visuals lane.
 */
UCLASS()
class UMBRELLAELLA_API USceneArtSubsystem final : public UTickableWorldSubsystem
{
	GENERATED_BODY()

public:
	virtual bool ShouldCreateSubsystem(UObject* Outer) const override;
	virtual void PostInitialize() override;
	virtual void Tick(float DeltaTime) override;
	virtual TStatId GetStatId() const override;
	virtual bool IsTickableInEditor() const override { return false; }

	/** Every scene picture, back to front within the backdrop. Pure. */
	static TArray<FSceneArtSpec> Specs();

	/** Draw Texture for a slot (null = load the slot's asset): one panel per anchor of the slot. Refuses a slot already drawn. */
	EArtSlotDraw ShowArt(const FString& Visual, UTexture2D* Texture);

	/** Panels drawn for a slot (start-end has two). */
	int32 PanelCount(const FString& Visual) const;

	/** First panel of a slot, or null. */
	UStaticMeshComponent* FindPanel(const FString& Visual, int32 Index = 0) const;

	/** True when the flag a visual is built behind is on (sky, water and clocks; land; frame and route ends each have their own). */
	static bool IsVisualEnabled(const FString& Visual);

	/** Width and height of a panel: backdrop-sized for layers, view-sized for the frame, view plus fill for route ends. Pure. */
	static FVector2D PanelSize(const FSceneArtSpec& Spec);

	/** World X a panel sits at for a camera X. Pure. */
	static float PanelX(const FSceneArtSpec& Spec, float CameraX);

	/**
	 * How much larger than the arena view the camera shows: OrthoWidth / ArenaWidth, 1 when not orthographic (0). The
	 * camera margin (visualqa) widens the view, so the view-sized frame scales by this to keep reaching the screen edge. Pure.
	 */
	static float ViewScale(float OrthoWidth);

	/** Move every panel for a camera X and size view panels to the camera's ortho width (0 = arena width; also what Tick does). */
	void ScrollTo(float CameraX, float OrthoWidth = 0.0f);

	virtual void Deinitialize() override;

private:
	struct FPanel
	{
		FSceneArtSpec Spec;
		TWeakObjectPtr<AActor> Actor;
	};
	TArray<FPanel> Panels;
};
