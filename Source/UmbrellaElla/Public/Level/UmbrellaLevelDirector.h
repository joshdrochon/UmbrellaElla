#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "Level/LevelCatalogue.h"
#include "Core/UmbrellaEvent.h"
#include "Level/LevelPlan.h"
#include "UmbrellaLevelDirector.generated.h"

class AUmbrellaArena;

/**
 * Director's Cut level director: spawns the nine-chunk route as placeholder geometry (engine cubes), places traps and
 * enemies through the enemies lane's public Configure functions, tracks checkpoints, drives the scrolling camera and
 * hands off to the Keeper at the route end. Lane e.
 */
UCLASS()
class UMBRELLAELLA_API AUmbrellaLevelDirector : public AActor
{
	GENERATED_BODY()

public:
	AUmbrellaLevelDirector();

	/** Generate the route from Seed and spawn everything. Replaces a previous build. Returns the number of chunks spawned (0 when the level flags are off). */
	int32 BuildRoute(int64 Seed);

	/** Spawn an explicit route (tests build one variant at a time). Same flags and return value as BuildRoute. */
	int32 BuildRouteFrom(const FRoute& InRoute);

	/** Destroy everything this director spawned. */
	void ClearRoute();

	/** Move Actor to the stand position of checkpoint 1..3. Returns the checkpoint placed at, 0 when refused. */
	int32 PlaceAtCheckpoint(AActor* Actor, int32 Checkpoint) const;

	/** Follow Ella's X: scrolls the camera, notes checkpoints, fires the Keeper handoff once. Tests call this directly. */
	void StepFollow(float EllaX, int32 TravelDirection);

	virtual void Tick(float DeltaSeconds) override;

	const FRoute& GetRoute() const { return Route; }
	const TArray<FLevelPlacement>& GetPlan() const { return Plan; }
	const TArray<TObjectPtr<AActor>>& GetSpawned() const { return Spawned; }
	int32 GetSlotsSpawned() const { return SlotsSpawned; }
	int32 GetCheckpointReached() const { return CheckpointReached; }
	bool HasHandedOff() const { return bHandedOff; }
	/** Set (or found on first use) the arena whose camera scrolls. */
	void SetArena(AUmbrellaArena* InArena) { Arena = InArena; }

	/** Last camera X written by StepFollow (tests read it). */
	float GetLastCameraX() const { return LastCameraX; }

private:
	AActor* SpawnBlock(const FLevelPlacement& Placement);
	void SpawnMechanic(const FLevelPlacement& Placement);
	void BroadcastRouteEvent(EUmbrellaEventType EventType, FName Detail, float Value) const;

	UPROPERTY()
	TArray<TObjectPtr<AActor>> Spawned;

	UPROPERTY()
	TObjectPtr<AUmbrellaArena> Arena;

	/** Where the arena stood before the handoff moved it to the route end; ClearRoute puts it back. */
	FVector ArenaHome = FVector::ZeroVector;
	bool bArenaMoved = false;

	FRoute Route;
	TArray<FLevelPlacement> Plan;
	int32 SlotsSpawned = 0;
	int32 CheckpointReached = 0;
	bool bHandedOff = false;
	float LastCameraX = 0.0f;
};
