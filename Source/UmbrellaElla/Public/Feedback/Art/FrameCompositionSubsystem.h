#pragma once

#include "CoreMinimal.h"
#include "Subsystems/WorldSubsystem.h"
#include "FrameCompositionSubsystem.generated.h"

class UStaticMeshComponent;

namespace UmbrellaFrameConst
{
	/**
	 * Everything drawn behind the play layer (world Y below this) is dimmed toward the Other Realm study's dark
	 * backdrop (visualqa, Josh 16:05). Between the arena depth and the hazard depth (UmbrellaDrawOrder).
	 */
	static constexpr float BehindPlayY = -150.0f;
	/** Multiply on backdrop art: the study's near-black, warm ground (#1c1a18 range), the picture's detail kept faint. */
	static const FLinearColor BackdropDim(0.055f, 0.048f, 0.042f, 1.0f);
	/** A flat stand-in panel behind play is never brighter than this (sRGB about #1c1a18). */
	static const FLinearColor BackdropFlat(0.012f, 0.011f, 0.010f, 1.0f);
	/** Cream route blocks become the study's floating-island umber (sRGB about #3a2a1c). */
	static const FLinearColor IslandUmber(0.042f, 0.023f, 0.012f, 1.0f);
	/** Salmon enemy stand-in boxes become the art bible's red shadow #8f173c (shot-red family), a dark silhouette. */
	static const FLinearColor EnemyShadow(0.275f, 0.009f, 0.045f, 1.0f);
	/** Name of the arena's lilac Keeper stand-in cube: never drawn on a gameplay screen. */
	static const TCHAR* const KeeperStandInName = TEXT("KeeperStandIn");
	/** Colour match tolerances: a tint already applied, and a stand-in role colour. */
	static constexpr float AppliedTolerance = 0.0005f;
	static constexpr float RoleTolerance = 0.002f;
	/** With -VisualQADump on the command line, every visible mesh is logged (LogUmbrellaFrame) this often, in seconds. */
	static constexpr float DumpInterval = 5.0f;
	/** Seconds between passes over the world's meshes. */
	static constexpr float PassInterval = 0.2f;
	/**
	 * Camera margin (coordinator 16:20): world units shown above the top of Ella's picture cell when she is at the play
	 * ceiling (arena top minus capsule half-height, z 1036 at HeroSize 1). The ceiling itself is unchanged.
	 */
	static constexpr float CeilingSpritePad = 8.0f;
	/** Side of the engine cube/plane the art boxes scale (ArtSlot), world units. */
	static constexpr float UnitBoxSize = 100.0f;
	/** An orthographic width within this of the expected one counts as unchanged (another system's zoom is left alone). */
	static constexpr float OrthoMatchTolerance = 0.5f;
}

class ACharacter;
class AUmbrellaArena;

/** What the frame pass does to one mesh. */
enum class EFrameTreatment : uint8
{
	Keep,
	DimBackdropArt,
	DarkenBackdropPanel,
	TintIsland,
	TintEnemy,
	Hide
};

/**
 * Composes the gameplay frame toward the Other Realm study: dims the backdrop, turns cream stand-in blocks into
 * dark island umber and hides lilac Keeper stand-in cubes, so no bright placeholder box or bar is ever on a gameplay
 * screen. Visual only (tint and hidden-in-game); never collision, size or game state. visualqa lane.
 */
UCLASS()
class UMBRELLAELLA_API UFrameCompositionSubsystem final : public UTickableWorldSubsystem
{
	GENERATED_BODY()

public:
	virtual void Tick(float DeltaTime) override;
	virtual TStatId GetStatId() const override;

	/** The treatment for a mesh at world depth Y with these properties. Pure. */
	static EFrameTreatment TreatmentFor(FName ComponentName, float WorldY, bool bDrawsArt, bool bSlotMaterial, const FLinearColor& Tint);

	/** Apply the treatment to every mesh in the world now; returns how many meshes changed. */
	int32 ComposeNow();

	/** Log every rendered mesh: owner, component, world box, art or stand-in tint (finds the boxes on a capture). */
	int32 DumpVisibleMeshes() const;

	/** Half-height of Ella's drawn picture cell for an actor scale (UmbrellaPresenterConst::ArtCellHeight). Pure. */
	static float SpriteHalfHeight(float ActorScaleZ);

	/** Orthographic width that keeps the arena's full height plus Overhang above and below on screen. Pure. */
	static float MarginOrthoWidth(float ArenaHeight, float AspectRatio, float SpriteHalf, float CapsuleHalf);

	/** World Z of the top edge of an orthographic view. Pure. */
	static float FrameTopZ(float CameraZ, float OrthoWidth, float AspectRatio);

	/**
	 * Widen the arena camera so Ella's whole picture stays in frame at the play ceiling, in Start Game and Director's
	 * Cut. Leaves a camera another system zoomed (VFX demo capture) alone.
	 */
	void ApplyCameraMargin(AUmbrellaArena* Arena, const ACharacter* Ella);

private:
	float LastMarginOrthoWidth = 0.0f;
	float SinceLastPass = 0.0f;
	float SinceLastDump = 0.0f;
};
