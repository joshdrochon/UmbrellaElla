#pragma once

#include "CoreMinimal.h"
#include "EncounterTuning.generated.h"

/** Every number of the Encounter module: default, units and clamps (lane b). End a shipped default with // bake: <feature ID>.<param>. */
USTRUCT()
struct UMBRELLAELLA_API FEncounterTuning
{
	GENERATED_BODY()

	/** Quiet time at the start of every phase: no new attacks start (encounter.json transition_in.sec). */
	UPROPERTY(EditAnywhere, Category = "Phases", meta = (ClampMin = "0"))
	float PhaseTransitionSeconds = 2.0f;

	/** Lives Ella has after a checkpoint retry (one active plus two reserves). The Health lane restores them. */
	UPROPERTY(EditAnywhere, Category = "Retry", meta = (ClampMin = "1"))
	int32 RetryLives = 3;

	/** True: ResetForRestart re-enters the checkpoint phase by itself. False: the caller invokes BeginKeeperFight. */
	UPROPERTY(EditAnywhere, Category = "Retry")
	bool bResumeAfterReset = true;

	/** Half the arena play height Ella is clamped to when the Keeper picks a gust band (cm). */
	UPROPERTY(EditAnywhere, Category = "Arena")
	float ArenaHeight = 1080.0f;

	/** Ella's radius for Keeper attacks when no collider can be read (cm). */
	UPROPERTY(EditAnywhere, Category = "Arena")
	float PlayerRadius = 28.0f;
};
