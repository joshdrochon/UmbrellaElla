#pragma once

#include "CoreMinimal.h"
#include "GameFramework/GameModeBase.h"
#include "UmbrellaGameMode.generated.h"

class AUmbrellaArena;

/** Game mode (Flow, lane d). No pawn spawns until a mode is chosen on the Start screen. */
UCLASS()
class UMBRELLAELLA_API AUmbrellaGameMode : public AGameModeBase
{
	GENERATED_BODY()

public:
	AUmbrellaGameMode();

	/** Spawn the arena if the map has none, spawn and possess Ella at its start, aim the camera, start the Keeper fight. */
	void BeginFight(APlayerController* Player);

	/** Put Ella back at the arena start if she is gone (retry). */
	void EnsurePlayerPawn(APlayerController* Player);

	bool IsFightStarted() const { return bFightStarted; }

	AUmbrellaArena* GetArena() const { return Arena; }

	virtual bool PlayerCanRestart_Implementation(APlayerController* Player) override;

private:
	AUmbrellaArena* FindOrSpawnArena();

	UPROPERTY()
	TObjectPtr<AUmbrellaArena> Arena;

	bool bFightStarted = false;
};
