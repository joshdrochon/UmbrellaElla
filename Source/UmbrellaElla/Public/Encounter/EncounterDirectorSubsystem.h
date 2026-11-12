#pragma once

#include "CoreMinimal.h"
#include "Subsystems/WorldSubsystem.h"
#include "EncounterDirectorSubsystem.generated.h"

/** Encounter Director: owns the encounter state, phases, checkpoints, retry and the win. Lane b. */
UCLASS()
class UMBRELLAELLA_API UEncounterDirectorSubsystem : public UWorldSubsystem
{
	GENERATED_BODY()

public:
	/** Flow (lane d) calls this when a mode reaches the Keeper. Spawns the Keeper at the arena anchor. */
	void BeginKeeperFight();

	/** Clears every projectile, timer and module state and returns to READY. */
	void ResetForRestart();
};
