#pragma once

#include "CoreMinimal.h"
#include "GameFramework/GameModeBase.h"
#include "UmbrellaGameMode.generated.h"

class AUmbrellaArena;
class AUmbrellaLevelDirector;

/** Game mode (Flow, lane d). No pawn spawns until a mode is chosen on the Start screen. */
UCLASS()
class UMBRELLAELLA_API AUmbrellaGameMode : public AGameModeBase
{
	GENERATED_BODY()

public:
	AUmbrellaGameMode();

	/** Spawn the arena if the map has none, spawn and possess Ella at its start, aim the camera, start the Keeper fight. */
	void BeginFight(APlayerController* Player);

	/**
	 * Director's Cut start: arena, Ella, the level director with its built route, Ella placed at the first checkpoint.
	 * The Keeper fight begins at the route end (the director hands off). When the route could not be built nothing starts;
	 * HasRoute() is false and the caller falls back to BeginFight.
	 */
	void BeginRoute(APlayerController* Player, int64 Seed);

	/** Retry in the route: Ella back at the last checkpoint reached (the first one before any). */
	void PlaceAtLastCheckpoint(APlayerController* Player);

	bool HasRoute() const;

	AUmbrellaLevelDirector* GetLevelDirector() const { return LevelDirector; }

	/** Put Ella back at the arena start if she is gone (retry). */
	void EnsurePlayerPawn(APlayerController* Player);

	bool IsFightStarted() const { return bFightStarted; }

	AUmbrellaArena* GetArena() const { return Arena; }

	virtual bool PlayerCanRestart_Implementation(APlayerController* Player) override;

private:
	AUmbrellaArena* FindOrSpawnArena();

	UPROPERTY()
	TObjectPtr<AUmbrellaArena> Arena;

	UPROPERTY()
	TObjectPtr<AUmbrellaLevelDirector> LevelDirector;

	bool bFightStarted = false;
};
