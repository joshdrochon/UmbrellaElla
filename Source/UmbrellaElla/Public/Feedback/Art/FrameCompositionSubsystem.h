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
}

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

private:
	float SinceLastPass = 0.0f;
	float SinceLastDump = 0.0f;
};
