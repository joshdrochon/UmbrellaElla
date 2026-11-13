#pragma once

#include "CoreMinimal.h"
#include "Attack/AttackTuning.h"
#include "Encounter/EncounterTuning.h"
#include "Field/FieldTuning.h"
#include "Flow/FlowTuning.h"
#include "Health/HealthTuning.h"
#include "Motor/MotorTuning.h"
#include "Owl/KeeperTuning.h"
#include "Progression/ProgressionTuning.h"
#include "Umbrella/UmbrellaFlightTuning.h"

class UUmbrellaTuning;

#if UMBRELLAELLA_WORKBENCH
/**
 * A copy of the module tuning structs the settings can change at runtime: the Director's Cut developer options and the
 * reduced-motion presentation. Readers keep reading GetDefault<UUmbrellaTuning>() at the point of use; the settings
 * subsystem writes a composed copy into it while an option is active and writes the captured baseline back after.
 * Nothing here is saved to an ini file. Compiled only in workbench builds: the submission never writes the tuning
 * class default (pipeline/unreal-rules.md), so there the developer options stay read-only.
 */
struct UMBRELLAELLA_API FSettingsLiveTuning
{
	FMotorTuning Motor;
	FFieldTuning Field;
	FKeeperTuning Keeper;
	FHealthTuning Health;
	FAttackTuning Attack;
	FProgressionTuning Progression;
	FFlowTuning Flow;
	FEncounterTuning Encounter;
	FUmbrellaFlightTuning UmbrellaFlight;

	/** Copy the structs out of a tuning object. */
	static FSettingsLiveTuning ReadFrom(const UUmbrellaTuning* Tuning);

	/** Write the structs into a tuning object (the live defaults every reader sees). */
	void WriteTo(UUmbrellaTuning* Tuning) const;
};
#endif // UMBRELLAELLA_WORKBENCH
