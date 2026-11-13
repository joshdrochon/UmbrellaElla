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
}

/**
 * Draws the world slots (world:solids, world:refuge-and-yellow-bay, world:mill-and-traps) onto the pieces the level
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

	/** The slot a placement kind draws, or an empty string (floor, wind, enemies have none). Pure. */
	static FString VisualFor(ELevelPlacementKind Kind);

	/** Draw every director piece not drawn yet (Texture null = load each slot's asset). Returns pieces drawn this call. */
	int32 Refresh(UTexture2D* Texture);

	/** Pieces drawn so far for a slot. */
	int32 DrawnCount(const FString& Visual) const;

private:
	TSet<TWeakObjectPtr<AActor>> Done;
	TMap<FString, int32> Counts;
	float Since = 0.0f;
};
