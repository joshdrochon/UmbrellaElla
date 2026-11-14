#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "Level/LevelCatalogue.h"
#include "Core/UmbrellaEvent.h"
#include "Level/LevelPlan.h"
#include "UmbrellaLevelDirector.generated.h"

namespace UmbrellaCameraFollowConst
{
	/**
	 * Camera follow smoothing (critically damped spring, seconds). dcseamless, Nov 14: the camera centre was Ella's X plus a
	 * lead of +-CameraLeadFraction x view width chosen by the SIGN of her X velocity, set instantly: every time she stopped
	 * (a Space flap, a key release) the view jumped 480 units back, and 480 forward when she moved again (measured with
	 * real input: per-frame camera steps -480..+960 at 30 fps). 0.25 s keeps her near the lead point while flying.
	 */
	static constexpr float SmoothSeconds = 0.25f;
	/** The lead turns at most this fast (units/s): a reversal swings it 960 units, which a spring alone ran at 94 units a frame. */
	static constexpr float LeadSpeed = 300.0f;
	/** A target this far from the camera (a checkpoint place, a respawn, the handoff) is a cut: the camera snaps. */
	static constexpr float SnapDistance = 3840.0f;
}

/** Camera follow state: smoothed centre X, its rate, and the lead kept while Ella is not moving sideways. */
struct FCameraFollowState
{
	float X = 0.0f;
	float Rate = 0.0f;
	float Lead = 0.0f;
	float LeadTarget = 0.0f;
	bool bStarted = false;
};

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

	/** Follow Ella's X: scrolls the camera, notes checkpoints, fires the Keeper handoff once. Tests call this directly.
	 *  DeltaSeconds 0 (tests, scripted runs) places the camera at once; the game's Tick passes its frame time (smoothed). */
	void StepFollow(float EllaX, int32 TravelDirection, float DeltaSeconds = 0.0f);

	/**
	 * Next camera centre target (before the route clamp) for Ella at EllaX moving in TravelDirection (-1, 0, +1): the lead
	 * turns to the travel side and stays when she stops (no snap back), and the centre follows Ella + lead on a critically
	 * damped spring, so neither position nor speed jumps. DeltaSeconds <= 0, the first call, or a cut (SnapDistance) snap. Pure.
	 */
	static float StepCameraFollow(FCameraFollowState& State, float EllaX, int32 TravelDirection, float DeltaSeconds, float LeadDistance);

	virtual void Tick(float DeltaSeconds) override;

	const FRoute& GetRoute() const { return Route; }
	const TArray<FLevelPlacement>& GetPlan() const { return Plan; }
	const TArray<TObjectPtr<AActor>>& GetSpawned() const { return Spawned; }
	int32 GetSlotsSpawned() const { return SlotsSpawned; }
	int32 GetCheckpointReached() const { return CheckpointReached; }
	bool HasHandedOff() const { return bHandedOff; }
	/** Set (or found on first use) the arena whose camera scrolls. With a route built and not handed off, its right
	 *  wall moves to the route end (B12). */
	void SetArena(AUmbrellaArena* InArena);

	/** Last camera X written by StepFollow (tests read it). */
	float GetLastCameraX() const { return LastCameraX; }

private:
	AActor* SpawnBlock(const FLevelPlacement& Placement);
	void SpawnMechanic(const FLevelPlacement& Placement);
	void BroadcastRouteEvent(EUmbrellaEventType EventType, FName Detail, float Value) const;
	/** The arena (set, or the world's first one); null when the world has none. */
	AUmbrellaArena* FindArena();
	/** B12: on a built route before the handoff, the arena's right wall stands at the route end. */
	void ApplyRouteRightWall();

	UPROPERTY()
	TArray<TObjectPtr<AActor>> Spawned;

	UPROPERTY()
	TObjectPtr<AUmbrellaArena> Arena;

	/** Where the arena stood before the handoff moved it to the route end; ClearRoute puts it back. */
	FVector ArenaHome = FVector::ZeroVector;
	bool bArenaMoved = false;
	/** The route moved the arena's right wall to the route end (B12); ClearRoute puts it back. */
	bool bRightWallMoved = false;

	FRoute Route;
	TArray<FLevelPlacement> Plan;
	int32 SlotsSpawned = 0;
	int32 CheckpointReached = 0;
	bool bHandedOff = false;
	float LastCameraX = 0.0f;
	FCameraFollowState Follow;
};
