#pragma once

#include "CoreMinimal.h"
#include "Engine/DeveloperSettings.h"
#include "Motor/MotorTuning.h"
#include "Umbrella/UmbrellaFlightTuning.h"
#include "Attack/AttackTuning.h"
#include "Health/HealthTuning.h"
#include "Projectile/ProjectileTuning.h"
#include "UI/HudTuning.h"
#include "Owl/KeeperTuning.h"
#include "Encounter/EncounterTuning.h"
#include "Flow/FlowTuning.h"
#include "Arena/ArenaCameraTuning.h"
#include "Field/FieldTuning.h"
#include "UmbrellaTuning.generated.h"

/**
 * All gameplay tuning, one member per module struct (Core, TD-owned). Read with GetDefault<UUmbrellaTuning>() at the point of use.
 * Lanes add fields inside their own struct header, never here. Never edit in Project Settings (no ini section).
 */
UCLASS(Config = Game, defaultconfig, meta = (DisplayName = "Umbrella Tuning"))
class UMBRELLAELLA_API UUmbrellaTuning final : public UDeveloperSettings
{
	GENERATED_BODY()

public:
	UPROPERTY(Config, EditAnywhere, Category = "Motor")
	FMotorTuning Motor;

	UPROPERTY(Config, EditAnywhere, Category = "Umbrella")
	FUmbrellaFlightTuning UmbrellaFlight;

	UPROPERTY(Config, EditAnywhere, Category = "Attack")
	FAttackTuning Attack;

	UPROPERTY(Config, EditAnywhere, Category = "Health")
	FHealthTuning Health;

	UPROPERTY(Config, EditAnywhere, Category = "Projectile")
	FProjectileTuning Projectile;

	UPROPERTY(Config, EditAnywhere, Category = "UI")
	FHudTuning Hud;

	UPROPERTY(Config, EditAnywhere, Category = "Owl")
	FKeeperTuning Keeper;

	UPROPERTY(Config, EditAnywhere, Category = "Encounter")
	FEncounterTuning Encounter;

	UPROPERTY(Config, EditAnywhere, Category = "Flow")
	FFlowTuning Flow;

	UPROPERTY(Config, EditAnywhere, Category = "Arena")
	FArenaCameraTuning ArenaCamera;

	UPROPERTY(Config, EditAnywhere, Category = "Field")
	FFieldTuning Field;
};
