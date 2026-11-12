#pragma once

#include "CoreMinimal.h"
#include "Engine/DeveloperSettings.h"
#include "Attack/AttackTuning.h"
#include "Defense/DefenseTuning.h"
#include "Encounter/EncounterTuning.h"
#include "Feedback/FeedbackTuning.h"
#include "Health/HealthTuning.h"
#include "Input/InputTuning.h"
#include "Motor/MotorTuning.h"
#include "UI/UITuning.h"
#include "Umbrella/UmbrellaFlightTuning.h"
#include "UmbrellaTuning.generated.h"

/** Project settings: one member per component tuning struct, added by the TD in card 0.3. Gameplay reads it with
 *  GetDefault<UUmbrellaTuning>(); the smoke hook reflects over it (pipeline/unreal-rules.md, Smoke hook contract). */
UCLASS(Config = Game, DefaultConfig, meta = (DisplayName = "Umbrella Tuning"))
class UMBRELLAELLA_API UUmbrellaTuning final : public UDeveloperSettings
{
	GENERATED_BODY()

public:
	UPROPERTY(Config, EditAnywhere)
	FAttackTuning Attack;

	UPROPERTY(Config, EditAnywhere)
	FDefenseTuning Defense;

	UPROPERTY(Config, EditAnywhere)
	FEncounterTuning Encounter;

	UPROPERTY(Config, EditAnywhere)
	FFeedbackTuning Feedback;

	UPROPERTY(Config, EditAnywhere)
	FHealthTuning Health;

	UPROPERTY(Config, EditAnywhere)
	FInputTuning Input;

	UPROPERTY(Config, EditAnywhere)
	FMotorTuning Motor;

	UPROPERTY(Config, EditAnywhere)
	FUITuning UI;

	UPROPERTY(Config, EditAnywhere)
	FUmbrellaFlightTuning Umbrella;
};
