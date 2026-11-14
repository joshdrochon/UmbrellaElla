#pragma once

#include "CoreMinimal.h"
#include "Level/LevelPlan.h"
#include "Subsystems/WorldSubsystem.h"
#include "WorldArtSubsystem.generated.h"

class AActor;
class UStaticMeshComponent;
class UTexture2D;

namespace UmbrellaWorldArtConst
{
	static constexpr float RefreshSeconds = 0.5f;
	/** A Solid narrower than this many times its height is a block or column, not a ledge (artscene request 6:
	 *  ChunkCatalogueData ledges are 7:1 to 15:1, blocks and columns 0.7:1 to 2.7:1). */
	static constexpr float BlockMaxAspect = 4.0f;
}

/**
 * Draws the world slots (world:solids, world:solids-block, world:refuge-and-yellow-bay, world:mill-and-traps) onto the pieces the level
 * director already placed: land blocks, refuge and checkpoint blocks, and traps keep their stand-in box and shape, and
 * their picture replaces the flat colour when the slot asset exists. Collision is never touched. Visuals lane.
 */
UCLASS()
class UMBRELLAELLA_API UWorldArtSubsystem final : public UTickableWorldSubsystem
{
	GENERATED_BODY()

public:
	virtual bool ShouldCreateSubsystem(UObject* Outer) const override;
	virtual void Tick(float DeltaTime) override;
	virtual TStatId GetStatId() const override;

	/** The slot a placement kind draws, or an empty string (wind, enemies have none). Pure. */
	static FString VisualFor(ELevelPlacementKind Kind);

	/** As above, with the placement's full extents (X wide, Z tall): a Solid under BlockMaxAspect draws
	 *  world:solids-block, so a column is not a squashed ledge picture. Floor and ledges keep world:solids. Pure. */
	static FString VisualFor(ELevelPlacementKind Kind, const FVector& Size);

	/** The slot drawn instead when Visual's own picture is not imported (block -> ledge picture), or empty. Pure. */
	static FString FallbackVisual(const FString& Visual);

	/** Draw every director piece not drawn yet (Texture null = load each slot's asset). Returns pieces drawn this call. */
	int32 Refresh(UTexture2D* Texture);

	/** Pieces drawn so far for a slot. */
	int32 DrawnCount(const FString& Visual) const;

private:
	TSet<TWeakObjectPtr<AActor>> Done;
	TMap<FString, int32> Counts;
	float Since = 0.0f;
};
